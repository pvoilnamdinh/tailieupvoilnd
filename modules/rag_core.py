import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

class RAGCore:
    def __init__(self):
        print("Đang khởi tạo RAGCore (phiên bản Cloud)...")
        
        index_name = os.getenv("PINECONE_INDEX_NAME")
        google_api_key = os.getenv("GOOGLE_API_KEY")

        if not index_name or not google_api_key:
            raise ValueError("Vui lòng đặt GOOGLE_API_KEY và PINECONE_INDEX_NAME trong file .env")

        # *** SỬA LỖI: Chuyển sang giao thức REST ổn định hơn ***
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key,
            transport='rest'  # Thêm dòng này
        )
        print("-> Đã kết nối tới Google Embedding API (qua REST).")

        # *** SỬA LỖI: Chuyển sang giao thức REST ổn định hơn ***
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest", 
            temperature=0.3,
            google_api_key=google_api_key,
            transport='rest'  # Thêm dòng này
        )
        print("-> Đã kết nối tới Gemini API (qua REST).")
        
        print(f"-> Đang kết nối tới Pinecone index '{index_name}'...")
        vector_store = PineconeVectorStore.from_existing_index(
            index_name=index_name,
            embedding=self.embedding_model
        )
        self.retriever = vector_store.as_retriever(search_kwargs={'k': 5})
        print("-> Kết nối tới Pinecone thành công.")
        
        self.rag_chain = self._create_rag_chain()
        print("RAGCore (phiên bản Cloud) đã sẵn sàng!")

    def _create_rag_chain(self):
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
        print(f"Chain đang xử lý câu hỏi: '{question}'")
        response = self.rag_chain.invoke(question)
        return response
