from flask import Flask, request, jsonify,Blueprint
import google.generativeai as genai
import pyodbc
import sys
from flask_cors import CORS
#pip install flask google-generativeai pyodbc flask-cors

# Đảm bảo UTF-8 là mã hóa mặc định
sys.stdout.reconfigure(encoding='utf-8')

# Cấu hình API Key Gemini
API_KEY = "AIzaSyCeGZiWJ6_Ynysbwt5-32VRStPTGs1Iwyw"
genai.configure(api_key=API_KEY)

# Chọn model Gemini
model = genai.GenerativeModel("gemini-2.0-flash")

# Cấu hình kết nối SQL Server
def get_db_connection():
    conn = pyodbc.connect(
        "DRIVER={SQL Server};"
        "SERVER=DESKTOP-A9RVON6\\SQLEXPRESS;"
        "DATABASE=LaptopStore;"
        "Trusted_Connection=yes;" 
        "TrustServerCertificate=yes;"  
    )
    return conn

def is_stock_inquiry(user_message):
    prompt = f"""Bạn chỉ cần trả lời một từ duy nhất: 'Có' hoặc 'Không'.  
    Không được giải thích, không được thêm bất kỳ thông tin nào khác.  
    Nếu câu hỏi sau liên quan đến số lượng hàng tồn kho hoặc tình trạng còn hàng, trả lời 'Có'.  
    Nếu không, trả lời 'Không'.  

    Câu hỏi: '{user_message}'  
    **Đáp án**:"""

    try:
        response = model.generate_content(prompt)
        clean_response = response.text.strip().lower()

        # Chỉ giữ lại "có" hoặc "không", loại bỏ phần giải thích
        if "có" in clean_response:
            return True
        if "không" in clean_response:
            return False

        return False  # Nếu không xác định được, mặc định là "Không"
    except Exception as e:
        print("❌ Lỗi khi gọi API Gemini:", str(e))
        return False 

# Trích xuất tất cả sản phẩm từ câu hỏi
def extract_product_names(user_message):
    """
    Trích xuất tất cả sản phẩm từ tin nhắn của người dùng.
    """
    prompt = f"""Bạn hãy xác định tất cả các tên sản phẩm trong câu sau:
    '{user_message}'
    Nếu có nhiều sản phẩm, hãy liệt kê tất cả các sản phẩm, phân cách bởi dấu phẩy.
    Nếu không có sản phẩm, trả lời 'Không có sản phẩm'."""
   
    try:
        response = model.generate_content(prompt)
        product_names = response.text.strip()
    except Exception as e:
        print("❌ Lỗi khi gọi API Gemini:", str(e))
        return []

    if product_names.lower() == "không có sản phẩm":
        return []
    
    return [name.strip() for name in product_names.split(",")]

# Kiểm tra danh sách sản phẩm còn hàng
def check_products_availability(product_names):
    conn = get_db_connection()
    cursor = conn.cursor()

    results = []
    for product_name in product_names:
        query = """
        SELECT TOP 1 MaSanPham, TenSanPham, SoLuong, Gia, GiaMoi 
        FROM SanPham 
        WHERE TenSanPham LIKE ? AND TrangThai = 1 
        """
        cursor.execute(query, (f"%{product_name}%",))
        product = cursor.fetchone()

        if product:
  
            product_link = f"https://localhost:44373/Home/ChiTietSanPham/{product[0]}"
            if product[2] > 0:
                if product[4] is not None and product[4] > 0:
                    results.append(f"✅ Sản phẩm '{product[1]}' còn {product[2]} cái. Đang được bán với giá {product[4]:,}đ sau khi giảm (Giá gốc: {product[3]:,}đ). <a style='color:blue;' href='{product_link}'>Bấm vào đây để xem</a>")
                else:
                    results.append(f"✅ Sản phẩm '{product[1]}' còn {product[2]} cái. Giá bán: {product[3]:,}đ. <a style='color:blue;' href='{product_link}'>Bấm vào đây để xem</a>")
            else:
                results.append(f"❌ Sản phẩm '{product[1]}' hiện đã hết hàng.")
        else:
            results.append(f"❓ Không tìm thấy sản phẩm '{product_name}' trong kho.")

    cursor.close()
    conn.close()

    return results

# Tạo Flask API
apichat = Blueprint('apichat', __name__)
CORS(apichat)  # Cấu hình CORS

@apichat.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("mess", "")
      
        if not user_message:
            return jsonify({"error": "Tin nhắn không được để trống"}), 400

        # Trích xuất danh sách sản phẩm
        product_names = extract_product_names(user_message)
        print(f"🔍 Sản phẩm được trích xuất: {product_names}") 

        # Nếu có sản phẩm và người dùng hỏi về hàng tồn, kiểm tra kho
        if product_names and is_stock_inquiry(user_message):
            stock_responses = check_products_availability(product_names)
            print(f"🔍 Kết quả kiểm tra kho: {stock_responses}")  
            return jsonify({"response": "\n".join(stock_responses)})

        # Nếu không có sản phẩm hoặc không hỏi về hàng tồn, hỏi Gemini như bình thường
        response = model.generate_content(user_message)
        return jsonify({"response": response.text})

    except Exception as e:
        print(f"❌ Lỗi khi xử lý tin nhắn: {str(e)}")
        return jsonify({"error": f"Lỗi máy chủ: {str(e)}"}), 500

