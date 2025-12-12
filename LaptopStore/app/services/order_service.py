import pyodbc
from app.config import Config

def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)

def create_order(data):
    conn = get_connection()
    cursor = conn.cursor()

    # Lấy hình thức thanh toán, mặc định là COD
    hinh_thuc_thanh_toan = data.get("HinhThucThanhToan", "COD")
    
    cursor.execute("""
        INSERT INTO DonHang (MaTaiKhoan, NgayDatHang, TongTien, DiaChiGiaoHang, SoDienThoai, TrangThai, MaVoucher, HinhThucThanhToan)
        OUTPUT INSERTED.MaDonHang
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["MaTaiKhoan"],
        data["NgayDatHang"],
        data["TongTien"],
        data["DiaChiGiaoHang"],
        data["SoDienThoai"],
        data["TrangThai"],
        data["MaVoucher"],
        hinh_thuc_thanh_toan
    ))
    don_hang_id = cursor.fetchone()[0]

    for item in data["ChiTietDonHang"]:
        cursor.execute("""
            INSERT INTO ChiTietDonHang (MaDonHang, MaSanPham, SoLuong, Gia)
            VALUES (?, ?, ?, ?)
        """, (don_hang_id, item["MaSanPham"], item["SoLuong"], item["Gia"]))

    cursor.execute("SELECT * FROM DonHang WHERE MaDonHang = ?", (don_hang_id,))
    order_row = cursor.fetchone()

    cursor.execute("""
        SELECT CT.MaDonHang, CT.MaSanPham, CT.SoLuong, CT.Gia, SP.TenSanPham
        FROM ChiTietDonHang CT
        JOIN SanPham SP ON CT.MaSanPham = SP.MaSanPham
        WHERE CT.MaDonHang = ?
    """, (don_hang_id,))
    details_rows = cursor.fetchall()

    cursor.execute("SELECT * FROM TaiKhoan WHERE MaTaiKhoan = ?", (order_row.MaTaiKhoan,))
    user_row = cursor.fetchone()

    cursor.execute("SELECT GiamGia FROM Voucher WHERE MaVoucher = ?", (order_row.MaVoucher,))
    voucher_row = cursor.fetchone()

    conn.commit()
    conn.close()

    return {
        "order_row": order_row,
        "details_rows": details_rows,
        "user_row": user_row,
        "voucher_row": voucher_row
    }

def get_order_detail_by_id(order_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM DonHang WHERE MaDonHang = ?", (order_id,))
    order_row = cursor.fetchone()

    if not order_row:
        conn.close()
        return None

    cursor.execute("""
        SELECT CT.MaDonHang, CT.MaSanPham, CT.SoLuong, CT.Gia, SP.TenSanPham
        FROM ChiTietDonHang CT
        JOIN SanPham SP ON CT.MaSanPham = SP.MaSanPham
        WHERE CT.MaDonHang = ?
    """, (order_id,))
    details_rows = cursor.fetchall()

    # Lấy serial numbers cho từng sản phẩm trong đơn hàng (theo MaDonHang)
    serial_map = {}
    for detail_row in details_rows:
        ma_san_pham = detail_row.MaSanPham
        
        # Lấy serial numbers của đơn hàng này (theo MaDonHang)
        cursor.execute("""
            SELECT SerialNumber
            FROM SanPhamSerial
            WHERE MaSanPham = ? AND MaDonHang = ? AND TrangThai = N'Đã bán'
            ORDER BY NgayBan DESC
        """, (ma_san_pham, order_id))
        
        serials = [row[0] for row in cursor.fetchall()]
        serial_map[ma_san_pham] = serials

    # Lấy MaVoucher từ order_row (có thể là object hoặc tuple)
    ma_voucher = None
    if hasattr(order_row, 'MaVoucher'):
        ma_voucher = order_row.MaVoucher
    elif isinstance(order_row, tuple) and len(order_row) > 4:
        ma_voucher = order_row[4]
    
    voucher_row = None
    if ma_voucher:
        cursor.execute("SELECT GiamGia, Code FROM Voucher WHERE MaVoucher = ?", (ma_voucher,))
        voucher_row = cursor.fetchone()

    # Lấy MaTaiKhoan từ order_row
    ma_tai_khoan = None
    if hasattr(order_row, 'MaTaiKhoan'):
        ma_tai_khoan = order_row.MaTaiKhoan
    elif isinstance(order_row, tuple) and len(order_row) > 1:
        ma_tai_khoan = order_row[1]
    
    user_row = None
    if ma_tai_khoan:
        cursor.execute("SELECT * FROM TaiKhoan WHERE MaTaiKhoan = ?", (ma_tai_khoan,))
        user_row = cursor.fetchone()

    conn.close()

    return {
        "order_row": order_row,
        "details_rows": details_rows,
        "user_row": user_row,
        "voucher_row": voucher_row,
        "serial_map": serial_map
    }
def update_order_status(order_id, status):
    conn = get_connection()
    cursor = conn.cursor()

    # Kiểm tra đơn hàng có tồn tại không
    cursor.execute("SELECT * FROM DonHang WHERE MaDonHang = ?", (order_id,))
    order_row = cursor.fetchone()

    if not order_row:
        conn.close()
        return None

    # Cập nhật trạng thái
    cursor.execute("""
        UPDATE DonHang SET TrangThai = ?
        WHERE MaDonHang = ?
    """, (status, order_id))

    conn.commit()
    conn.close()
    return True 
