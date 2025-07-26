import os
import nest_asyncio  # <-- THÊM DÒNG NÀY
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

nest_asyncio.apply()  # <-- VÀ THÊM DÒNG NÀY

load_dotenv()

# --- Phần còn lại của file giữ nguyên ---
from modules.rag_core import RAGCore
from modules.vector_db import create_vector_db

app = Flask(__name__)

# Khởi tạo RAG Core ngay khi bắt đầu. An toàn vì chỉ kết nối API.
try:
    print("Initializing RAG Core...")
    rag_system = RAGCore()
    print("RAG Core initialized successfully.")
except Exception as e:
    print(f"FATAL: Could not initialize RAGCore. Error: {e}")
    rag_system = None

@app.route('/')
def index():
    """Phục vụ trang chat chính."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """Xử lý câu hỏi chat từ người dùng."""
    if not rag_system:
        return jsonify({'answer': 'Lỗi hệ thống: RAG Core chưa được khởi tạo. Vui lòng kiểm tra logs.'}), 500

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
    """Endpoint bí mật để kích hoạt xử lý tài liệu."""
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
