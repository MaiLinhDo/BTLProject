import pyodbc
from app.config import Config

def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM TaiKhoan WHERE Username = ? ", (username,))
    user = cursor.fetchone()
    conn.close()
    return user
def get_khachhang(page=1, page_size=5, search=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        base_query = "SELECT MaTaiKhoan, Username, HoTen, Email, TrangThai,DiaChi,SoDienThoai,NgayTao FROM TaiKhoan WHERE MaQuyen = 3"
        count_query = "SELECT COUNT(*) FROM TaiKhoan WHERE MaQuyen = 3"
        params = []

        if search:
            base_query += " AND (Username LIKE ? OR HoTen LIKE ? OR Email LIKE ?)"
            count_query += " AND (Username LIKE ? OR HoTen LIKE ? OR Email LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        base_query += " ORDER BY MaTaiKhoan OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([(page - 1) * page_size, page_size])

        cursor.execute(count_query, *(params[:-2] if search else []))
        total = cursor.fetchone()[0]

        cursor.execute(base_query, *params)
        rows = cursor.fetchall()
        conn.close()

        khachhang_list = [
            {
                "MaTaiKhoan": row[0],
                "Username": row[1],
                "HoTen": row[2],
                "Email": row[3],
                "TrangThai": row[4],
                "DiaChi": row[5],
                "SoDienThoai": row[6],
                "NgayTao": row[7].strftime("%Y-%m-%d") if row[7] else None,
            } for row in rows
        ]

        return {"success": True, "total": total, "khachhang": khachhang_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

def toggle_trangthai_khachhang(ma_tai_khoan):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT TrangThai FROM TaiKhoan WHERE MaTaiKhoan = ?", ma_tai_khoan)
        current_status = cursor.fetchone()
        if not current_status:
            return {"success": False, "message": "Không tìm thấy khách hàng"}

        new_status = not current_status[0]
        cursor.execute("UPDATE TaiKhoan SET TrangThai = ? WHERE MaTaiKhoan = ?", new_status, ma_tai_khoan)
        conn.commit()
        conn.close()
        return {"success": True, "message": "Cập nhật trạng thái thành công"}
    except Exception as e:
        return {"success": False, "message": str(e)}
def doi_mat_khau_service(username, matkhau_cu, matkhau_moi, xacnhan_mk):
    if not all([username, matkhau_cu, matkhau_moi, xacnhan_mk]):
        return {"success": False, "message": "Thiếu thông tin đầu vào"}

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Password FROM TaiKhoan WHERE Username = ?", (username,))
        row = cursor.fetchone()

        if not row:
            return {"success": False, "message": "Không tìm thấy tài khoản"}

        if row[0] != matkhau_cu:
            return {"success": False, "message": "Mật khẩu cũ không chính xác"}

        if matkhau_moi != xacnhan_mk:
            return {"success": False, "message": "Xác nhận mật khẩu không khớp"}

        cursor.execute("UPDATE TaiKhoan SET Password = ? WHERE Username = ?", (matkhau_moi, username))
        conn.commit()
        conn.close()

        return {"success": True, "message": "Đổi mật khẩu thành công"}

    except Exception as e:
        return {"success": False, "message": str(e)}
def update_trang_thai_tai_khoan(ma_tai_khoan, trang_thai):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM TaiKhoan WHERE MaTaiKhoan = ?", (ma_tai_khoan,))
        tai_khoan = cursor.fetchone()
        if not tai_khoan:
            return {"success": False, "message": "Không tìm thấy tài khoản"}

        cursor.execute("UPDATE TaiKhoan SET TrangThai = ? WHERE MaTaiKhoan = ?", (trang_thai, ma_tai_khoan))
        conn.commit()
        conn.close()

        status_text = "Mở khóa" if trang_thai else "Khóa"
        return {"success": True, "message": f"{status_text} tài khoản thành công"}
    except Exception as e:
        return {"success": False, "message": str(e)}



