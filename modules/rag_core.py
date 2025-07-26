import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Tải các biến môi trường từ file .env
load_dotenv()

# --- Các hằng số cấu hình ---
DB_FAISS_PATH = "vectorstore/db_faiss"

class RAGCore:
    def __init__(self):
        print("Đang khởi tạo RAGCore, vui lòng chờ...")
        
        # 1. Tải mô hình embedding
        #    Sử dụng cùng một mô hình như khi tạo vector store
        self.embedding_model = SentenceTransformerEmbeddings(
            model_name="keepitreal/vietnamese-sbert"
        )
        print("-> Tải xong embedding model.")

        # 2. Tải mô hình sinh ngôn ngữ (LLM) từ Gemini
        #    Đảm bảo GOOGLE_API_KEY đã được đặt trong file .env
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest", 
            temperature=0.3,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        print("-> Kết nối tới Gemini API thành công.")
        
        # *** NÂNG CẤP LỚN Ở ĐÂY ***
        # 3. Tải cơ sở dữ liệu vector đã được tạo sẵn
        try:
            self.db = FAISS.load_local(
                DB_FAISS_PATH, 
                self.embedding_model, 
                allow_dangerous_deserialization=True # Cần thiết cho FAISS
            )
            print("-> Tải thành công cơ sở dữ liệu vector đã lưu.")
        except Exception as e:
            print(f"LỖI: Không thể tải cơ sở dữ liệu vector từ '{DB_FAISS_PATH}'.")
            print("Vui lòng chạy kịch bản 'scripts/process_docs.py' trước.")
            print(f"Chi tiết lỗi: {e}")
            self.db = None # Đặt là None nếu không tải được
        
        # Tạo retriever từ cơ sở dữ liệu vector
        self.retriever = self.db.as_retriever(search_kwargs={'k': 3}) if self.db else None
        
        # 4. Tạo chuỗi xử lý (RAG Chain)
        self.rag_chain = self._create_rag_chain()
        
        print("RAGCore đã sẵn sàng!")

    def _create_rag_chain(self):
        """Tạo chuỗi xử lý LangChain."""
        
        # Định nghĩa mẫu prompt tiếng Việt
        custom_rag_prompt = PromptTemplate(
            template="""Dựa vào những thông tin được cung cấp dưới đây để trả lời câu hỏi. Nếu không tìm thấy thông tin, hãy trả lời một cách lịch sự rằng bạn không biết câu trả lời. Đừng cố bịa ra câu trả lời.

Bối cảnh: {context}

Câu hỏi: {question}

Câu trả lời hữu ích:""",
            input_variables=["context", "question"],
        )

        # Tạo chuỗi xử lý
        chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | custom_rag_prompt
            | self.llm
            | StrOutputParser()
        )
        return chain

    def answer(self, question: str):
        """Nhận câu hỏi và trả về câu trả lời từ RAG chain."""
        if not self.retriever:
            return "Lỗi: Cơ sở dữ liệu vector chưa được tải. Vui lòng kiểm tra lại."
            
        print(f"Chain đang xử lý câu hỏi: '{question}'")
        response = self.rag_chain.invoke(question)
        return response


# Dành cho việc kiểm tra nhanh
if __name__ == '__main__':
    rag_system = RAGCore()
    # Ví dụ câu hỏi, bạn có thể thay đổi để kiểm tra
    test_question = "Xe ô tô con được sử dụng cho mục đích gì?" 
    print(f"\nĐang hỏi thử: {test_question}")
    answer = rag_system.answer(test_question)
    print("\nCâu trả lời từ Bot:")
    print(answer)
