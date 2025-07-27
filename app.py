import os
import nest_asyncio
import threading # Thêm thư viện để xử lý luồng nền
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

# --- **KIẾN TRÚC CUỐI CÙNG: KHỞI ĐỘNG NỀN CHO GIAO DIỆN WEB** ---
rag_system = None
# Sử dụng một biến để theo dõi trạng thái của hệ thống AI
# Các trạng thái: "initializing", "ready", "error"
rag_system_status = "initializing" 

def initialize_rag_in_background():
    """
    Hàm này sẽ được chạy trong một luồng nền để khởi tạo RAGCore
    mà không làm chặn ứng dụng chính.
    """
    global rag_system, rag_system_status
    print("BACKGROUND_TASK: Starting RAG Core initialization...")
    try:
        rag_system = RAGCore()
        rag_system_status = "ready"
        print("BACKGROUND_TASK: RAG Core is now ready.")
    except Exception as e:
        rag_system_status = "error"
        print(f"BACKGROUND_TASK: FATAL - Could not initialize RAGCore. Error: {e}")

# --- CÁC ROUTE CỦA ỨNG DỤNG ---

@app.route('/')
def index():
    """Route để hiển thị giao diện web chính."""
    return render_template('index.html')

@app.route('/status')
def status():
    """
    API endpoint đơn giản để giao diện web kiểm tra trạng thái
    của hệ thống AI.
    """
    global rag_system_status
    return jsonify({"status": rag_system_status})

@app.route('/ask', methods=['POST'])
def ask():
    """API endpoint để nhận câu hỏi và trả về câu trả lời."""
    global rag_system_status, rag_system

    # Chỉ xử lý câu hỏi nếu hệ thống đã sẵn sàng
    if rag_system_status != "ready" or rag_system is None:
        return jsonify({'answer': 'Lỗi: Hệ thống chưa sẵn sàng hoặc đang khởi tạo. Vui lòng thử lại sau.'}), 503

    # Nếu hệ thống đã sẵn sàng, tiếp tục xử lý
    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    try:
        answer = rag_system.answer(question)
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

# --- KHỞI ĐỘNG LUỒNG NỀN ---
# Bắt đầu quá trình khởi tạo RAGCore ngay khi ứng dụng chạy
threading.Thread(target=initialize_rag_in_background, daemon=True).start()

# Đoạn mã để chạy thử cục bộ
if __name__ == '__main__':
    # Chạy với debug=False để tránh khởi động 2 lần và mô phỏng chính xác môi trường trên Render
    app.run(host='0.0.0.0', port=5000, debug=False)
