import os
import docx2txt
from pypdf import PdfReader
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_documents_from_directory(directory_path):
    """
    Tải và đọc nội dung từ tất cả các file .txt, .pdf, .docx trong một thư mục
    và các thư mục con của nó. Tự động bỏ qua các file tạm của Office.
    """
    all_docs = []
    print("Bắt đầu quy trình xử lý tài liệu với các loader chuyên dụng...")
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            # *** CẢI TIẾN: Bỏ qua các file tạm của Office ***
            if file.startswith('~$'):
                print(f"  -> Bỏ qua file tạm: {file}")
                continue

            file_path = os.path.join(root, file)
            print(f"  -> Đang xử lý file: {os.path.basename(file_path)}")
            
            try:
                if file.endswith(".pdf"):
                    reader = PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    all_docs.append({'source': file, 'content': text})
                elif file.endswith(".docx"):
                    text = docx2txt.process(file_path)
                    all_docs.append({'source': file, 'content': text})
                elif file.endswith(".txt"):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    all_docs.append({'source': file, 'content': text})
            except Exception as e:
                print(f"      LỖI: Không thể đọc file {os.path.basename(file_path)}. Lỗi: {e}")

    print("Đã tải thành công nội dung từ các tài liệu.")
    return all_docs

def create_vector_db():
    """
    Tạo cơ sở dữ liệu vector từ các tài liệu trong thư mục 'data'.
    """
    # Tải tài liệu
    documents = load_documents_from_directory('data')
    
    if not documents:
        print("Không tìm thấy tài liệu nào trong thư mục 'data'. Vui lòng thêm tài liệu và thử lại.")
        return

    # Chuẩn bị nội dung và metadata để xử lý
    docs_content = [doc['content'] for doc in documents]
    docs_metadata = [{'source': doc['source']} for doc in documents]

    # Chia nhỏ văn bản
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.create_documents(docs_content, metadatas=docs_metadata)
    print(f"Đã chia tài liệu thành {len(texts)} đoạn văn bản.")

    # Tải mô hình embedding
    embedding_model = SentenceTransformerEmbeddings(model_name="keepitreal/vietnamese-sbert")
    print("Đã tải xong mô hình embedding.")

    # Tạo và lưu trữ cơ sở dữ liệu vector
    print("Đang tạo cơ sở dữ liệu vector... Quá trình này có thể mất một lúc.")
    vector_store = FAISS.from_documents(texts, embedding_model)
    vector_store.save_local("vectorstore")
    print("==================================================")
    print("ĐÃ TẠO VÀ LƯU VECTOR STORE THÀNH CÔNG!")
    print("==================================================")
