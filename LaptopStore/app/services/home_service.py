import pyodbc
from app.config import Config
from datetime import datetime
from flask import request

def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)

def get_valid_vouchers():
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT * FROM Voucher
    WHERE TrangThai = 1
      AND NgayBatDau <= GETDATE()
      AND NgayKetThuc >= GETDATE()
      AND SoLuongSuDung < SoLuongSuDungToiDa
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    vouchers = []
    for row in rows:
        vouchers.append({
            "MaVoucher": row.MaVoucher,
            "Code": row.Code,
            "SoLuongSuDung": row.SoLuongSuDung,
            "SoLuongSuDungToiDa": row.SoLuongSuDungToiDa,
            "NgayBatDau": row.NgayBatDau.strftime("%Y-%m-%d"),
            "NgayKetThuc": row.NgayKetThuc.strftime("%Y-%m-%d"),
            "TrangThai": row.TrangThai,
            "MoTa": row.MoTa,
            "GiamGia": row.GiamGia, 
        })
    conn.close()
    return vouchers

def get_banners():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Banner")
    rows = cursor.fetchall()
    banners = []
    for row in rows:
        banners.append({
            "MaBanner": row.MaBanner,
            "MoTa": row.MoTa,
            "HinhAnh": row.HinhAnh
        })
    conn.close()
    return banners
def get_products():
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT TOP 12 
        sp.MaSanPham,
        sp.TenSanPham,
        sp.Gia,
        sp.GiaMoi,
        sp.HinhAnh,
        ISNULL(AVG(CAST(dg.DiemDanhGia AS FLOAT)), 0) as TrungBinhSao,
        COUNT(dg.MaDanhGia) as SoLuongDanhGia
    FROM SanPham sp
    LEFT JOIN DanhGiaSanPham dg ON sp.MaSanPham = dg.MaSanPham
    WHERE sp.TrangThai = 1
    GROUP BY sp.MaSanPham, sp.TenSanPham, sp.Gia, sp.GiaMoi, sp.HinhAnh
    ORDER BY sp.MaSanPham DESC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    products = []
    for row in rows:
        products.append({
            "MaSanPham": row[0],
            "TenSanPham": row[1],
            "Gia": row[2],
            "GiaMoi": row[3],
            "HinhAnh": row[4],
            "TrungBinhSao": round(row[5], 1) if row[5] else 0,
            "SoLuongDanhGia": row[6] if row[6] else 0
        })
    conn.close()
    return products

def get_categories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM DanhMucSanPham WHERE TrangThai = 1")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "MaDanhMuc": row.MaDanhMuc,
            "TenDanhMuc": row.TenDanhMuc,
            "TrangThai": row.TrangThai
        }
        for row in rows
    ]
def get_hang():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM HangSanPham WHERE TrangThai = 1")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "MaHang": row.MaHang,
            "TenHang": row.TenHang,
            "TrangThai": row.TrangThai
        }
        for row in rows
    ]
def dang_ky_tai_khoan(data):
    conn = get_connection()
    cursor = conn.cursor()

    username = data.get("Username")
    email = data.get("Email")
    password = data.get("Password")
    xac_nhan_mat_khau = data.get("XacNhanMatKhau")
    HoTen = data.get("HoTen")
    SoDienThoai = data.get("SoDienThoai")
    DiaChi = data.get("DiaChi")
    # 1. Kiểm tra mật khẩu xác nhận
    if password != xac_nhan_mat_khau:
        return {"success": False, "message": "Mật khẩu xác nhận không khớp."}

    # 2. Kiểm tra Username tồn tại
    cursor.execute("SELECT * FROM TaiKhoan WHERE Username = ?", username)
    if cursor.fetchone():
        return {"success": False, "message": "Tên đăng nhập đã tồn tại."}

    # 3. Kiểm tra Email tồn tại
    cursor.execute("SELECT * FROM TaiKhoan WHERE Email = ?", email)
    if cursor.fetchone():
        return {"success": False, "message": "Email đã tồn tại trong hệ thống."}

    # 4. Tạo tài khoản
    now = datetime.now()
    cursor.execute("""
        INSERT INTO TaiKhoan (Username, Password,SoDienThoai,DiaChi,HoTen, Email, NgayTao, TrangThai, MaQuyen)
        VALUES (?, ?, ?, ?, ?, ?,?,?,?)
    """, (username, password,SoDienThoai,DiaChi,HoTen, email, now, 1, 3))

    conn.commit()

    # Lấy lại ID tài khoản vừa tạo
    cursor.execute("SELECT MaTaiKhoan FROM TaiKhoan WHERE Username = ?", username)
    tai_khoan = cursor.fetchone()
    if not tai_khoan:
        return {"success": False, "message": "Không lấy được ID tài khoản."}

    ma_tai_khoan = tai_khoan.MaTaiKhoan

    # 5. Tạo giỏ hàng
    cursor.execute("INSERT INTO GioHang (MaTaiKhoan, TongTien) VALUES (?, ?)", (ma_tai_khoan, 0))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Đăng ký thành công."}
def add_user_to_db(email, full_name):
    conn = get_connection()
    cursor = conn.cursor()

    # Kiểm tra xem email đã tồn tại trong bảng TaiKhoan chưa
    cursor.execute("SELECT * FROM TaiKhoan WHERE Email = ?", (email,))
    user = cursor.fetchone()

    if user is None:
        cursor.execute("""
            INSERT INTO TaiKhoan (Username, Email, Password, HoTen, NgayTao, TrangThai, MaQuyen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (email, email, '', full_name, '2025-04-14', True, 3))
        conn.commit()

    conn.close()

def dang_nhap_tai_khoan(username, password):
    if not username or not password:
        return {"success": False, "message": "Tên đăng nhập và mật khẩu là bắt buộc."}

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM TaiKhoan WHERE Username = ?", username)
    user = cursor.fetchone()

    if not user:
        conn.close()
        print("Tên đăng nhập không tồn tại.")
        return {"success": False, "message": "Tên đăng nhập không tồn tại."}

    if user.Password != password:
        conn.close()
        return {"success": False, "message": "Mật khẩu không đúng."}

    if not user.TrangThai:
        conn.close()
        return {"success": False, "message": "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên để mở khóa."}

    # Đăng nhập thành công
    user_info = {
        "Username": user.Username,
        "HoTen": user.HoTen,
        "Quyen": user.MaQuyen,
        "TrangThai": user.TrangThai,
    }

    conn.close()
    return {"success": True, "message": "Đăng nhập thành công.", "user": user_info}
def capnhat_thong_tin_service(data):
    username = data.get("Username")
    hoten = data.get("HoTen")
    sodienthoai = data.get("SoDienThoai")
    diachi = data.get("DiaChi")
    matkhauhientai = data.get("MatKhauHienTai")
    matkhaumoi = data.get("MatKhauMoi")
    xacnhanmatkhaumoi = data.get("XacNhanMatKhauMoi")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM TaiKhoan WHERE Username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return {"success": False, "message": "Tài khoản không tồn tại."}

    if matkhauhientai:
        if user.Password != matkhauhientai:
            conn.close()
            return {"success": False, "message": "Mật khẩu hiện tại không đúng."}
        if matkhaumoi != xacnhanmatkhaumoi:
            conn.close()
            return {"success": False, "message": "Xác nhận mật khẩu mới không khớp."}
        cursor.execute("UPDATE TaiKhoan SET Password = ? WHERE Username = ?", (matkhaumoi, username))

    cursor.execute("""
        UPDATE TaiKhoan SET HoTen = ?, SoDienThoai = ?, DiaChi = ?
        WHERE Username = ?
    """, (hoten, sodienthoai, diachi, username))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Cập nhật thông tin thành công."}
def get_user_profile(username):
    conn = get_connection()
    cursor = conn.cursor()

    # Lấy thông tin người dùng
    cursor.execute("SELECT * FROM TaiKhoan WHERE Username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return {"success": False, "message": "Tài khoản không tồn tại."}

    user_info = {
        "Username": user.Username,
        "HoTen": user.HoTen,
        "SoDienThoai": user.SoDienThoai,
        "DiaChi": user.DiaChi,
        "Email": user.Email,
        "TrangThai": user.TrangThai,
        "MaTaiKhoan": user.MaTaiKhoan,
        "Password": user.Password,
        "MaQuyen": user.MaQuyen,
        "NgayTao": user.NgayTao.strftime("%Y-%m-%d"),
    }

    # Lấy danh sách đơn hàng
    cursor.execute("SELECT * FROM DonHang WHERE MaTaiKhoan = ?", (user.MaTaiKhoan,))
    orders = cursor.fetchall()

    orders_data = []
    for order in orders:
        orders_data.append({
            "MaDonHang": order.MaDonHang,
            "MaTaiKhoan": order.MaTaiKhoan,
            "TongTien": order.TongTien,
            "DiaChiGiaoHang": order.DiaChiGiaoHang,
            "SoDienThoai": order.SoDienThoai,
            "MaVoucher": order.MaVoucher,
            "NgayDatHang": order.NgayDatHang.strftime("%Y-%m-%d"),
            "TrangThai": order.TrangThai
        })

    conn.close()

    return {
        "success": True,
        "user": user_info,
        "orders": orders_data
    }
def dang_xuat(username):
    conn = get_connection()
    cursor = conn.cursor()

    # Lấy thông tin người dùng
    cursor.execute("SELECT * FROM TaiKhoan WHERE Username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return {"success": False, "message": "Tài khoản không tồn tại."}

    user_info = {
        "Username": user.Username,
        "MaTaiKhoan": user.MaTaiKhoan
    }
    print(user_info)
    # Kiểm tra và tạo giỏ hàng nếu chưa có
    cursor.execute("SELECT * FROM GioHang WHERE MaTaiKhoan = ?", (user.MaTaiKhoan,))
    giohang = cursor.fetchone()

    if not giohang:
        cursor.execute("INSERT INTO GioHang (MaTaiKhoan, TongTien) VALUES (?, ?)", (user.MaTaiKhoan, 0))
        conn.commit()

    # Lấy giỏ hàng từ session giả sử gửi từ C# trong body
    cart_items = request.json.get('cart')  # Giỏ hàng từ C# session

    if cart_items:
        for item in cart_items:
            cursor.execute("SELECT * FROM ChiTietGioHang WHERE MaGioHang = ? AND MaSanPham = ?", 
                           (giohang.MaGioHang, item['MaSanPham']))
            existing_item = cursor.fetchone()

            if existing_item:
                # Cập nhật số lượng nếu đã tồn tại
                cursor.execute("UPDATE ChiTietGioHang SET SoLuong = SoLuong + ? WHERE MaGioHang = ? AND MaSanPham = ?",
                               (item['SoLuong'], giohang.MaGioHang, item['MaSanPham']))
            else:
                # Thêm sản phẩm mới vào giỏ hàng
                cursor.execute("INSERT INTO ChiTietGioHang (MaGioHang, MaSanPham, SoLuong, Gia) VALUES (?, ?, ?, ?)",
                               (giohang.MaGioHang, item['MaSanPham'], item['SoLuong'], item['Gia']))

        conn.commit()

    conn.close()

    return {"success": True, "message": "Đăng xuất và đồng bộ giỏ hàng thành công."}
def get_user_cart(username):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Lấy thông tin người dùng
    cursor.execute("SELECT * FROM TaiKhoan WHERE Username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return []
    
    # Lấy giỏ hàng của người dùng
    cursor.execute("""
        SELECT ctgh.MaChiTiet, ctgh.MaGioHang, ctgh.MaSanPham, ctgh.SoLuong, ctgh.Gia, ctgh.GiaMoi, sp.TenSanPham,sp.HinhAnh
        FROM ChiTietGioHang ctgh
        JOIN GioHang gh ON ctgh.MaGioHang = gh.MaGioHang
        JOIN SanPham sp ON ctgh.MaSanPham = sp.MaSanPham
        WHERE gh.MaTaiKhoan = ?
    """, (user.MaTaiKhoan,))
    
    cart_items = []
    for row in cursor.fetchall():
        cart_items.append({
            "MaChiTiet": row.MaChiTiet,
            "MaGioHang": row.MaGioHang,
            "MaSanPham": row.MaSanPham,
            "HinhAnh": row.HinhAnh,
            "SoLuong": row.SoLuong,
            "Gia": float(row.Gia) if row.Gia else 0,
            "GiaMoi": float(row.GiaMoi) if row.GiaMoi else None,
            "TenSanPham": row.TenSanPham
        })
    print(cart_items)
    cursor.execute("""
        DELETE FROM ChiTietGioHang
        WHERE MaGioHang IN (
            SELECT MaGioHang FROM GioHang WHERE MaTaiKhoan = ?
        )
    """, (user.MaTaiKhoan,))
    conn.commit()  
    conn.close()
    return cart_items

def check_coupon(code):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM Voucher 
        WHERE Code = ? AND SoLuongSuDung < SoLuongSuDungToiDa 
        AND NgayBatDau <= ? AND NgayKetThuc >= ? AND TrangThai = 1
    """, (code, datetime.now(), datetime.now()))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "MaVoucher": row.MaVoucher,
        "Code": row.Code,
        "SoLuongSuDung": row.SoLuongSuDung,
        "SoLuongSuDungToiDa": row.SoLuongSuDungToiDa,
        "NgayBatDau": row.NgayBatDau,
        "NgayKetThuc": row.NgayKetThuc,
        "TrangThai": row.TrangThai,
        "GiamGia": row.GiamGia
    }