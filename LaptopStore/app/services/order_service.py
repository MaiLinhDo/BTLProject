import pyodbc
from app.config import Config

def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)

def create_order(data):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO DonHang (MaTaiKhoan, NgayDatHang, TongTien, DiaChiGiaoHang, SoDienThoai, TrangThai, MaVoucher)
        OUTPUT INSERTED.MaDonHang
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["MaTaiKhoan"],
        data["NgayDatHang"],
        data["TongTien"],
        data["DiaChiGiaoHang"],
        data["SoDienThoai"],
        data["TrangThai"],
        data["MaVoucher"]
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

    cursor.execute("SELECT GiamGia, Code FROM Voucher WHERE MaVoucher = ?", (order_row.MaVoucher,))
    voucher_row = cursor.fetchone()

    cursor.execute("SELECT * FROM TaiKhoan WHERE MaTaiKhoan = ?", (order_row.MaTaiKhoan,))
    user_row = cursor.fetchone()

    conn.close()

    return {
        "order_row": order_row,
        "details_rows": details_rows,
        "user_row": user_row,
        "voucher_row": voucher_row
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
