import logging
from flask import Flask, render_template, request, jsonify
from modules.rag_core import RAGCore

# Cấu hình logging để xem thông tin chi tiết hơn
logging.basicConfig(level=logging.INFO)

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# Khởi tạo hệ thống RAG một lần duy nhất khi ứng dụng khởi động
# Điều này giúp không phải tải lại model mỗi khi có request
try:
    rag_system = RAGCore()
except Exception as e:
    logging.error(f"Không thể khởi tạo RAGCore: {e}")
    rag_system = None

@app.route('/')
def index():
    """
    Hàm này phục vụ file index.html làm giao diện chính.
    """
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """
    API endpoint để nhận câu hỏi từ giao diện và trả lời.
    """
    if not rag_system:
        return jsonify({'error': 'Hệ thống RAG chưa sẵn sàng. Vui lòng kiểm tra log server.'}), 500

    # Lấy câu hỏi từ dữ liệu JSON mà frontend gửi lên
    data = request.get_json()
    question = data.get('question', '')

    logging.info(f"Flask nhận câu hỏi: {question}")

    if not question:
        return jsonify({'answer': 'Vui lòng đặt câu hỏi.'})

    try:
        # Gọi đến RAGCore để xử lý và lấy câu trả lời
        real_answer = rag_system.answer(question)
        logging.info(f"Gemini trả lời: {real_answer}")
        return jsonify({'answer': real_answer})
    except Exception as e:
        logging.error(f"Lỗi khi xử lý câu hỏi: {e}")
        return jsonify({'answer': 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.'}), 500

if __name__ == '__main__':
    # Chạy ứng dụng Flask
    # Thêm use_reloader=False để tránh server khởi động lại 2 lần khi ở debug mode
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)

