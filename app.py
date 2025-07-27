import os
import nest_asyncio
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Áp dụng nest_asyncio để xử lý các vấn đề về event loop
nest_asyncio.apply()
# Tải các biến môi trường từ file .env
load_dotenv()

# Import các module tùy chỉnh
from modules.rag_core import RAGCore
from modules.vector_db import create_vector_db

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# --- **KIẾN TRÚC CUỐI CÙNG: KHỞI TẠO LƯỜI BIẾNG ĐỂ CHỐNG SẬP** ---
rag_system = None

def get_rag_system():
    """
    Hàm này sẽ kiểm tra và khởi tạo RAGCore chỉ khi cần thiết.
    Đây là phương pháp tối ưu nhất cho môi trường có tài nguyên hạn chế.
    """
    global rag_system
    if rag_system is None:
        print("LAZY_INIT: First request received. Starting RAG Core initialization...")
        try:
            rag_system = RAGCore()
            print("LAZY_INIT: RAG Core initialized successfully.")
        except Exception as e:
            print(f"LAZY_INIT: FATAL - Could not initialize RAGCore. Error: {e}")
            rag_system = "initialization_failed"
    return rag_system

# --- CÁC ROUTE CỦA ỨNG DỤNG ---

@app.route('/')
def index():
    """Route để hiển thị giao diện web chính."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """API endpoint để nhận câu hỏi và trả về câu trả lời từ RAG."""
    current_rag_system = get_rag_system()
    
    if current_rag_system == "initialization_failed":
        return jsonify({'answer': 'Lỗi hệ thống: Không thể khởi tạo RAG Core. Vui lòng kiểm tra logs server.'}), 500
    if not isinstance(current_rag_system, RAGCore):
        # Đây là trường hợp hệ thống đang trong quá trình khởi tạo ở lần gọi đầu tiên
        # Trả về mã lỗi 503 để JS biết và thử lại sau.
        return jsonify({'answer': 'Hệ thống đang khởi tạo, vui lòng thử lại sau giây lát.'}), 503 

    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    # Xử lý yêu cầu "ping" đặc biệt từ giao diện để xác nhận sẵn sàng
    if question == "__WARM_UP_PING__":
        return jsonify({'answer': 'pong', 'status': 'ready'})

    try:
        answer = current_rag_system.answer(question)
        return jsonify({'answer': answer})
    except Exception as e:
        print(f"Error during answer generation: {e}")
        return jsonify({'answer': 'Xin lỗi, đã có lỗi xảy ra trong quá trình xử lý câu hỏi.'}), 500

@app.route('/admin/process-data')
def process_data_route():
    """Route quản trị để kích hoạt việc xử lý và nạp dữ liệu từ Google Drive."""
    secret_key = os.getenv("APP_SECRET_KEY")
    provided_key = request.args.get('key')

    if not secret_key or provided_key != secret_key:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        print("ADMIN: Starting data processing task...")
        create_vector_db() 
        print("ADMIN: Data processing task finished successfully.")
        return jsonify({"status": "success", "message": "Đã xử lý và đẩy dữ liệu lên Pinecone thành công."})
    except Exception as e:
        print(f"ADMIN ERROR: Failed to process data. Error: {e}")
        return jsonify({"status": "error", "message": f"An error occurred: {e}"}), 500

# Đoạn mã để chạy thử cục bộ
if __name__ == '__main__':
    # Chạy với debug=False để tránh khởi động 2 lần và mô phỏng chính xác môi trường trên Render
    app.run(host='0.0.0.0', port=5000, debug=False)
