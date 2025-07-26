import sys
import os

# Thêm thư mục gốc của dự án vào Python Path
# Điều này cần thiết để import các module từ thư mục 'modules'
# khi chạy file này trực tiếp từ thư mục 'scripts'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.vector_db import create_vector_db

if __name__ == "__main__":
    print("="*50)
    print("BẮT ĐẦU KỊCH BẢN XỬ LÝ TÀI LIỆU")
    print("="*50)
    
    # Gọi hàm chính để tạo cơ sở dữ liệu
    create_vector_db()
    
    print("\n" + "="*50)
    print("KỊCH BẢN ĐÃ HOÀN TẤT.")
    print("Cơ sở dữ liệu vector đã được tạo/cập nhật trong thư mục 'vectorstore'.")
    print("="*50)

