from flask import Flask, request, jsonify, Blueprint
import google.generativeai as genai
import pyodbc
import sys
from flask_cors import CORS
from app.config import Config

# pip install flask google-generativeai pyodbc flask-cors

# Đảm bảo UTF-8 là mã hóa mặc định
sys.stdout.reconfigure(encoding='utf-8')

# Cấu hình API Key Gemini
API_KEY = "AIzaSyD84nqYxXX1Nfm1pBgF_IE0TUwuMIp1DU0"
genai.configure(api_key=API_KEY)

# Chọn model Gemini
model = genai.GenerativeModel("gemini-2.0-flash")


# Cấu hình kết nối SQL Server
def get_db_connection():
    try:
        conn = pyodbc.connect(Config.SQL_SERVER_CONN + "TrustServerCertificate=yes;")
        return conn
    except Exception as e:
        print(f"❌ Lỗi kết nối SQL Server: {str(e)}")
        raise


def get_support_staff_info():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT TOP 3 tk.HoTen, ISNULL(tk.SoDienThoai, ''), ISNULL(tk.Email, ''), ISNULL(q.TenQuyen, N'Nhân viên')
        FROM TaiKhoan tk
        LEFT JOIN Quyen q ON tk.MaQuyen = q.MaQuyen
        WHERE tk.TrangThai = 1 AND (q.TenQuyen IS NULL OR q.TenQuyen <> N'Khách hàng')
        ORDER BY tk.NgayTao DESC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return ("Hiện tại chatbot chỉ hỗ trợ kiểm tra tồn kho. "
                "Vui lòng liên hệ hotline 1900.999.888 để được nhân viên hỗ trợ chi tiết.")

    message_lines = [
        "Xin lỗi! Câu hỏi này nằm ngoài phạm vi hỗ trợ tự động.",
        "Bạn có thể liên hệ đội ngũ nhân viên của chúng tôi để được tư vấn ngay:"
    ]

    for row in rows:
        ho_ten = row[0]
        so_dien_thoai = row[1] or "Chưa cập nhật"
        email = row[2] or "support@laptopstore.vn"
        chuc_vu = row[3] or "Nhân viên"
        message_lines.append(f"• {ho_ten} ({chuc_vu}) - SĐT: {so_dien_thoai} - Email: {email}")

    message_lines.append("Nhân viên luôn sẵn sàng hỗ trợ 24/7 ❤️")
    return "\n".join(message_lines)


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
    Trước tiên thử tìm kiếm đơn giản trong database, nếu không tìm thấy mới dùng AI.
    """
    # Tìm kiếm đơn giản: lấy các từ khóa từ câu hỏi
    keywords = []
    words = user_message.split()
    for word in words:
        # Loại bỏ các từ không quan trọng
        word_clean = word.strip().lower()
        if len(word_clean) > 2 and word_clean not in ['laptop', 'máy', 'tính', 'có', 'không', 'còn', 'hàng', 'giá', 'bao', 'nhiêu']:
            keywords.append(word_clean)
    
    # Nếu có từ khóa, thử tìm trong database trước
    if keywords:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            found_products = []
            # Tìm sản phẩm có chứa bất kỳ từ khóa nào
            for keyword in keywords:
                query = """
                SELECT DISTINCT TenSanPham 
                FROM SanPham 
                WHERE LOWER(TenSanPham) LIKE ? AND TrangThai = 1
                """
                cursor.execute(query, (f"%{keyword}%",))
                products = cursor.fetchall()
                for product in products:
                    if product[0] not in found_products:
                        found_products.append(product[0])
            
            cursor.close()
            conn.close()
            
            if found_products:
                print(f"🔍 Tìm thấy {len(found_products)} sản phẩm bằng từ khóa: {found_products}")
                return found_products  # Trả về danh sách tên sản phẩm
        except Exception as e:
            print(f"❌ Lỗi khi tìm kiếm đơn giản: {str(e)}")
    
    
    # Nếu không tìm thấy bằng từ khóa, dùng AI để trích xuất
    prompt = f"""Bạn hãy xác định tên sản phẩm laptop trong câu sau:
    '{user_message}'
    Chỉ trả về tên sản phẩm, không giải thích thêm. Nếu có nhiều sản phẩm, phân cách bởi dấu phẩy.
    Nếu không có sản phẩm, trả lời 'Không có sản phẩm'."""

    try:
        response = model.generate_content(prompt)
        product_names = response.text.strip()
        print(f"🔍 AI trích xuất: {product_names}")
    except Exception as e:
        print("❌ Lỗi khi gọi API Gemini:", str(e))
        return []

    if product_names.lower() == "không có sản phẩm" or not product_names:
        return []

    return [name.strip() for name in product_names.split(",")]


# Kiểm tra danh sách sản phẩm còn hàng
def check_products_availability(product_names):
    conn = get_db_connection()
    cursor = conn.cursor()

    results = []
    found_product_ids = set()  # Để tránh trùng lặp
    
    for product_name in product_names:
        # Thử tìm chính xác trước
        query_exact = """
        SELECT MaSanPham, TenSanPham, SoLuong, Gia, GiaMoi 
        FROM SanPham 
        WHERE TenSanPham = ? AND TrangThai = 1 
        """
        cursor.execute(query_exact, (product_name,))
        product = cursor.fetchone()
        
        # Nếu không tìm thấy chính xác, thử tìm với LIKE
        if not product:
            query_like = """
            SELECT TOP 1 MaSanPham, TenSanPham, SoLuong, Gia, GiaMoi 
            FROM SanPham 
            WHERE LOWER(TenSanPham) LIKE ? AND TrangThai = 1 
            """
            cursor.execute(query_like, (f"%{product_name.lower()}%",))
            product = cursor.fetchone()

        if product and product[0] not in found_product_ids:
            found_product_ids.add(product[0])
            product_link = f"http://localhost:59774/Home/ChiTietSanPham/{product[0]}"
            if product[2] > 0:
                if product[4] is not None and product[4] > 0:
                    results.append(
                        f"✅ Sản phẩm '{product[1]}' còn {product[2]} cái. Đang được bán với giá {product[4]:,}đ sau khi giảm (Giá gốc: {product[3]:,}đ). <a style='color:blue;' href='{product_link}'>Bấm vào đây để xem</a>")
                else:
                    results.append(
                        f"✅ Sản phẩm '{product[1]}' còn {product[2]} cái. Giá bán: {product[3]:,}đ. <a style='color:blue;' href='{product_link}'>Bấm vào đây để xem</a>")
            else:
                results.append(f"❌ Sản phẩm '{product[1]}' hiện đã hết hàng.")
        elif not product:
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

        # Nếu có sản phẩm được trích xuất, luôn kiểm tra và trả về thông tin sản phẩm
        if product_names:
            stock_responses = check_products_availability(product_names)
            print(f"🔍 Kết quả kiểm tra kho: {stock_responses}")
            return jsonify({"response": "\n".join(stock_responses)})

        # Nếu không có sản phẩm được trích xuất, trả về thông tin nhân viên hỗ trợ
        staff_message = get_support_staff_info()
        return jsonify({"response": staff_message})

    except Exception as e:
        print(f"❌ Lỗi khi xử lý tin nhắn: {str(e)}")
        return jsonify({"error": f"Lỗi máy chủ: {str(e)}"}), 500

