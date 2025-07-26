import os
from dotenv import load_dotenv
import docx2txt
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# Tải các biến môi trường từ file .env
load_dotenv()

def load_documents_from_directory(directory_path):
    """
    Tải và đọc nội dung từ tất cả các file .txt, .pdf, .docx trong một thư mục.
    """
    all_docs = []
    print("Bắt đầu quy trình xử lý tài liệu với các loader chuyên dụng...")
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.startswith('~$'):
                print(f"  -> Bỏ qua file tạm: {file}")
                continue

            file_path = os.path.join(root, file)
            print(f"  -> Đang xử lý file: {os.path.basename(file_path)}")
            
            try:
                text = ""
                if file.endswith(".pdf"):
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        text += page.extract_text() or ""
                elif file.endswith(".docx"):
                    text = docx2txt.process(file_path)
                elif file.endswith(".txt"):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                
                if text.strip(): # Chỉ thêm nếu có nội dung
                    all_docs.append({'source': file, 'content': text})

            except Exception as e:
                print(f"      LỖI: Không thể đọc file {os.path.basename(file_path)}. Lỗi: {e}")

    print(f"Đã tải thành công nội dung từ {len(all_docs)} tài liệu.")
    return all_docs

def create_vector_db():
    """
    Tạo và đẩy dữ liệu vector lên Pinecone từ thư mục 'data'.
    """
    index_name = os.getenv("PINECONE_INDEX_NAME")
    if not index_name:
        raise ValueError("LỖI: Vui lòng đặt PINECONE_INDEX_NAME trong file .env")

    documents = load_documents_from_directory('data')
    if not documents:
        print("Không tìm thấy tài liệu nào trong thư mục 'data'. Vui lòng thêm tài liệu và thử lại.")
        return

    docs_content = [doc['content'] for doc in documents]
    docs_metadata = [{'source': doc['source']} for doc in documents]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.create_documents(docs_content, metadatas=docs_metadata)
    print(f"Đã chia tài liệu thành {len(texts)} đoạn văn bản.")

    print("Sử dụng mô hình embedding của Google qua API...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    print(f"Đang đẩy {len(texts)} đoạn văn bản lên Pinecone index '{index_name}'...")
    PineconeVectorStore.from_documents(texts, embeddings, index_name=index_name)
    
    print("==================================================")
    print("ĐÃ ĐẨY DỮ LIỆU LÊN PINECONE THÀNH CÔNG!")
    print("==================================================")
