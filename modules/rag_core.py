import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.chains.llm import LLMChain

load_dotenv()

# --- **TỐI ƯU HÓA**: Rút gọn prompt để tăng tốc độ phản hồi của LLM ---
# Chúng ta yêu cầu ít câu hỏi hơn (2 thay vì 3) và đưa ra chỉ dẫn ngắn gọn.
MULTI_QUERY_PROMPT_TEMPLATE = """Bạn là một trợ lý AI. Dựa vào câu hỏi của người dùng, hãy tạo ra 2 phiên bản câu hỏi khác có cùng ý nghĩa, sử dụng các từ đồng nghĩa.
Mỗi câu hỏi trên một dòng riêng biệt.

Câu hỏi gốc: {question}
"""

class RAGCore:
    def __init__(self):
        print("Đang khởi tạo RAGCore (phiên bản TỐI ƯU HÓA TỐC ĐỘ)...")
        
        index_name = os.getenv("PINECONE_INDEX_NAME")
        google_api_key = os.getenv("GOOGLE_API_KEY")

        if not index_name or not google_api_key:
            raise ValueError("Vui lòng đặt GOOGLE_API_KEY và PINECONE_INDEX_NAME trong file .env")

        # Khởi tạo mô hình embedding của Google
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key,
            transport='rest'
        )
        print("-> Đã kết nối tới Google Embedding API.")

        # Khởi tạo mô hình ngôn ngữ (LLM) của Google
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest", 
            temperature=0.3,
            google_api_key=google_api_key,
            transport='rest'
        )
        print("-> Đã kết nối tới Gemini API.")
        
        print(f"-> Đang kết nối tới Pinecone index '{index_name}'...")
        vector_store = PineconeVectorStore.from_existing_index(
            index_name=index_name,
            embedding=self.embedding_model
        )
        print("-> Kết nối tới Pinecone thành công.")

        # --- Cấu hình bộ truy vấn thông minh với prompt đã được tối ưu hóa ---
        query_prompt = PromptTemplate(
            input_variables=["question"],
            template=MULTI_QUERY_PROMPT_TEMPLATE
        )
        llm_chain = LLMChain(llm=self.llm, prompt=query_prompt, verbose=False) # Tắt verbose để log gọn hơn

        print("-> Đang cấu hình bộ truy vấn đã được tối ưu hóa...")
        self.retriever = MultiQueryRetriever(
            retriever=vector_store.as_retriever(search_kwargs={'k': 5}),
            llm_chain=llm_chain,
        )
        print("-> Bộ truy vấn đã sẵn sàng.")
        
        self.rag_chain = self._create_rag_chain()
        print("RAGCore (phiên bản TỐI ƯU HÓA TỐC ĐỘ) đã sẵn sàng!")

    def _create_rag_chain(self):
        # Prompt trả lời cuối cùng vẫn giữ nguyên
        custom_rag_prompt = PromptTemplate(
            template="""Dựa vào những thông tin được cung cấp dưới đây để trả lời câu hỏi một cách chi tiết và đầy đủ nhất có thể. Nếu không tìm thấy thông tin, hãy trả lời một cách lịch sự rằng bạn không có đủ thông tin để trả lời. Đừng cố bịa ra câu trả lời.

Bối cảnh: {context}

Câu hỏi: {question}

Câu trả lời hữu ích:""",
            input_variables=["context", "question"],
        )
        chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | custom_rag_prompt
            | self.llm
            | StrOutputParser()
        )
        return chain

    def answer(self, question: str):
        if not self.retriever:
            return "Lỗi: Hệ thống không thể kết nối đến cơ sở dữ liệu kiến thức (Pinecone)."
        
        print(f"Chain đang xử lý câu hỏi (sử dụng MultiQuery đã tối ưu): '{question}'")
        response = self.rag_chain.invoke(question)
        return response
