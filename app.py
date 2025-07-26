import os
import nest_asyncio
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

nest_asyncio.apply()
load_dotenv()

from modules.rag_core import RAGCore
from modules.vector_db import create_vector_db

app = Flask(__name__)

# --- TỐI ƯU HÓA: KHỞI TẠO "LƯỜI BIẾNG" ---
rag_system = None  # Ban đầu, không khởi tạo gì cả

def get_rag_system():
    """
    Hàm này sẽ kiểm tra và khởi tạo RAGCore chỉ khi cần thiết.
    Nó đảm bảo RAGCore chỉ được tạo một lần duy nhất.
    """
    global rag_system
    if rag_system is None:
        print("Lazy Initializing RAG Core for the first time...")
        try:
            rag_system = RAGCore()
            print("RAG Core initialized successfully.")
        except Exception as e:
            print(f"FATAL: Could not initialize RAGCore. Error: {e}")
            # Trả về lỗi nếu không khởi tạo được
            return None 
    return rag_system

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    # Lấy hệ thống RAG, sẽ khởi tạo nếu đây là lần đầu
    current_rag_system = get_rag_system()
    
    if not current_rag_system:
        return jsonify({'answer': 'Lỗi hệ thống: RAG Core chưa được khởi tạo. Vui lòng kiểm tra logs.'}), 500

    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    try:
        answer = current_rag_system.answer(question)
        return jsonify({'answer': answer})
    except Exception as e:
        print(f"Error during answer generation: {e}")
        return jsonify({'answer': 'Xin lỗi, đã có lỗi xảy ra trong quá trình xử lý câu hỏi.'}), 500

@app.route('/admin/process-data')
def process_data_route():
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
