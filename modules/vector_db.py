import os
import io
from dotenv import load_dotenv
import docx2txt
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# Thêm các thư viện của Google
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import json # Thêm dòng này để import thư viện json

# Tải các biến môi trường từ file .env
load_dotenv()

# ... (các hàm get_files_recursively và load_documents_from_google_drive_old_version nếu có)

def load_documents_from_google_drive():
    """
    Kết nối tới Google Drive, tải và đọc nội dung từ tất cả các file
    trong thư mục được chỉ định và các thư mục con của nó.
    """
    # Lấy thông tin từ biến môi trường
    # SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS') # Xóa hoặc comment dòng này
    
    # Lấy nội dung JSON của credentials từ biến môi trường
    GOOGLE_CREDENTIALS_JSON_CONTENT = os.getenv('GOOGLE_CREDENTIALS_JSON') 
    FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    # Kiểm tra xem các biến môi trường đã được thiết lập chưa
    if not GOOGLE_CREDENTIALS_JSON_CONTENT or not FOLDER_ID:
        raise ValueError("Lỗi: Vui lòng đặt GOOGLE_CREDENTIALS_JSON và GOOGLE_DRIVE_FOLDER_ID trong biến môi trường.")

    # Xác thực với Google Drive bằng tài khoản dịch vụ từ nội dung JSON
    try:
        # Chuyển đổi chuỗi JSON thành dictionary
        info = json.loads(GOOGLE_CREDENTIALS_JSON_CONTENT)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
    except Exception as e:
        # Cập nhật thông báo lỗi để phản ánh nguyên nhân mới
        raise ConnectionError(f"Không thể xác thực với Google Drive. Hãy chắc chắn nội dung JSON của biến môi trường 'GOOGLE_CREDENTIALS_JSON' là chính xác. Lỗi: {e}")

    print("Bắt đầu quét đệ quy các file từ Google Drive...")
    try:
        items = get_files_recursively(service, FOLDER_ID)
    except Exception as e:
        raise ConnectionError(f"Không thể lấy danh sách file từ Google Drive. Hãy kiểm tra lại FOLDER_ID và quyền chia sẻ. Lỗi: {e}")

    if not items:
        print("Không tìm thấy file nào trong thư mục Google Drive được chỉ định (bao gồm cả các thư mục con).")
        return []

    all_docs = []
    print(f"Tìm thấy tổng cộng {len(items)} file. Bắt đầu tải và xử lý...")

    # Duyệt qua từng file để tải và đọc nội dung
    for item in items:
        file_id = item.get('id')
        file_name = item.get('name')
        mime_type = item.get('mimeType')
        
        # Bỏ qua các file tạm của Microsoft Office
        if file_name.startswith('~$'):
            print(f"  -> Bỏ qua file tạm: {file_name}")
            continue

        print(f"  -> Đang xử lý file: {file_name} ({mime_type})")

        try:
            # Tải file về bộ nhớ tạm (in-memory)
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            fh.seek(0)

            # Đọc nội dung file tùy theo định dạng
            text = ""
            if mime_type == 'application/pdf':
                reader = PdfReader(fh)
                for page in reader.pages:
                    text += page.extract_text() or ""
            elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                text = docx2txt.process(fh)
            elif mime_type == 'text/plain':
                text = fh.read().decode('utf-8')
            else:
                print(f"      -> Bỏ qua file không hỗ trợ: {file_name} ({mime_type})")
                continue
            
            # Chỉ thêm vào danh sách nếu file có nội dung
            if text.strip():
                all_docs.append({'source': file_name, 'content': text})

        except Exception as e:
            print(f"      LỖI: Không thể đọc file {file_name}. Lỗi: {e}")

    print(f"Đã tải và xử lý thành công nội dung từ {len(all_docs)} tài liệu trên Google Drive.")
    return all_docs

# ... (hàm create_vector_db)
def create_vector_db():
    """
    Tạo và đẩy dữ liệu vector lên Pinecone từ các tài liệu trên Google Drive.
    """
    index_name = os.getenv("PINECONE_INDEX_NAME")
    if not index_name:
        raise ValueError("LỖI: Vui lòng đặt PINECONE_INDEX_NAME trong file .env")

    # Lấy tài liệu từ Google Drive
    documents = load_documents_from_google_drive()
    
    if not documents:
        print("Không có tài liệu nào từ Google Drive để xử lý. Quy trình kết thúc.")
        return

    # Các bước tiếp theo giữ nguyên
    docs_content = [doc['content'] for doc in documents]
    docs_metadata = [{'source': doc['source']} for doc in documents]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.create_documents(docs_content, metadatas=docs_metadata)
    print(f"Đã chia tài liệu thành {len(texts)} đoạn văn bản.")

    print("Sử dụng mô hình embedding của Google qua API...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    print(f"Đang đẩy {len(texts)} đoạn văn bản lên Pinecone index '{index_name}'...")
    PineconeVectorStore.from_documents(texts, embeddings, index_name=index_name)
    
    print("==========================================================")
    print("ĐÃ ĐẨY DỮ LIỆU TỪ GOOGLE DRIVE LÊN PINECONE THÀNH CÔNG!")
    print("==========================================================")
