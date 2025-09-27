import pyodbc
from app.config import Config
from datetime import datetime
from flask import request

def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)
# Hàm lấy tất cả danh mục sản phẩm
def get_all_categories():
    try:
        conn = get_connection()  # Kết nối đến cơ sở dữ liệu
        cursor = conn.cursor()

        # Truy vấn lấy tất cả các danh mục sản phẩm
        cursor.execute("""
            SELECT MaHang, TenHang, TrangThai, NgayTao
            FROM HangSanPham
        """)
        
        rows = cursor.fetchall()  # Lấy tất cả kết quả trả về
        conn.close()

        if not rows:
            return {"success": False, "message": "Không tìm thấy danh mục nào."}

        # Chuyển kết quả từ rows thành danh sách các dictionary
        categories = [
            {
                "MaHang": row[0],
                "TenHang": row[1],
                "TrangThai": row[2],
                "NgayTao": row[3].strftime("%Y-%m-%d") if row[3] else None
            }
            for row in rows
        ]

        return {"success": True, "categories": categories}
    
    except Exception as e:
        return {"success": False, "message": str(e)}
def get_categories(page=1, page_size=5, search=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        base_query = "SELECT MaHang, TenHang, TrangThai, NgayTao FROM HangSanPham"
        count_query = "SELECT COUNT(*) FROM HangSanPham"
        params = []

        if search:
            base_query += " WHERE TenHang LIKE ?"
            count_query += " WHERE TenHang LIKE ?"
            params.append(f"%{search}%")

        base_query += " ORDER BY MaHang OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([(page - 1) * page_size, page_size])

        cursor.execute(count_query, *(params[:-2] if search else []))
        total = cursor.fetchone()[0]

        cursor.execute(base_query, *params)
        rows = cursor.fetchall()
        conn.close()

        categories = [
            {
                "MaHang": row[0],
                "TenHang": row[1],
                "TrangThai": row[2],
                "NgayTao": row[3].strftime("%Y-%m-%d") if row[3] else None
            } for row in rows
        ]

        return {"success": True, "total": total, "categories": categories}
    except Exception as e:
        return {"success": False, "message": str(e)}

def add_category(data):
    try:
        ten_hang = data.get("TenHang")
        if not ten_hang:
            return {"success": False, "message": "Tên danh mục không được để trống"}

        conn = get_connection()
        cursor = conn.cursor()

        # Kiểm tra trùng tên
        cursor.execute("SELECT COUNT(*) FROM HangSanPham WHERE TenHang = ?", ten_hang)
        if cursor.fetchone()[0] > 0:
            return {"success": False, "message": "Tên danh mục đã tồn tại"}

        cursor.execute("""
            INSERT INTO HangSanPham (TenHang, TrangThai, NgayTao)
            VALUES (?, ?, ?)
        """, ten_hang, True, datetime.now())
        conn.commit()
        conn.close()
        return {"success": True, "message": "Thêm danh mục thành công"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def update_category(data):
    try:
        ma_hang = data.get("MaHang")
        ten_hang = data.get("TenHang")

        if not ten_hang:
            return {"success": False, "message": "Tên danh mục không được để trống"}

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM HangSanPham WHERE TenHang = ? AND MaHang != ?", ten_hang, ma_hang)
        if cursor.fetchone()[0] > 0:
            return {"success": False, "message": "Tên danh mục đã tồn tại"}

        cursor.execute("UPDATE HangSanPham SET TenHang = ? WHERE MaHang = ?", ten_hang, ma_hang)
        conn.commit()
        conn.close()
        return {"success": True, "message": "Cập nhật danh mục thành công"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def toggle_status(ma_hang):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT TrangThai FROM HangSanPham WHERE MaHang = ?", ma_hang)
        current_status = cursor.fetchone()
        if not current_status:
            return {"success": False, "message": "Không tìm thấy danh mục"}

        new_status = not current_status[0]
        cursor.execute("UPDATE HangSanPham SET TrangThai = ? WHERE MaHang = ?", new_status, ma_hang)
        conn.commit()
        conn.close()
        return {"success": True, "message": "Cập nhật trạng thái thành công"}
    except Exception as e:
        return {"success": False, "message": str(e)}
def get_category_by_id(ma_hang):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM HangSanPham WHERE MaHang = ?", ma_hang)
        category = cursor.fetchone()
        conn.close()

        if not category:
            return {"success": False, "message": "Không tìm thấy danh mục"}

        # Chuyển đổi Row thành dictionary
        columns = [column[0] for column in cursor.description]  # Lấy tên cột
        category_dict = dict(zip(columns, category))  # Kết hợp tên cột với giá trị

        # Trả về thông tin danh mục dưới dạng dictionary
        return {"success": True, "category": category_dict}
    except Exception as e:
        # Ghi lại lỗi
        print(f"Error: {str(e)}")
        return {"success": False, "message": str(e)}

def get_danhmuc(page=1, page_size=5, search=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        base_query = "SELECT MaDanhMuc, TenDanhMuc, TrangThai, NgayTao FROM DanhMucSanPham"
        count_query = "SELECT COUNT(*) FROM DanhMucSanPham"
        params = []

        if search:
            base_query += " WHERE TenDanhMuc LIKE ?"
            count_query += " WHERE TenDanhMuc LIKE ?"
            params.append(f"%{search}%")

        base_query += " ORDER BY MaDanhMuc OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([(page - 1) * page_size, page_size])

        cursor.execute(count_query, *(params[:-2] if search else []))
        total = cursor.fetchone()[0]

        cursor.execute(base_query, *params)
        rows = cursor.fetchall()
        conn.close()

        categories = [
            {
                "MaDanhMuc": row[0],
                "TenDanhMuc": row[1],
                "TrangThai": row[2],
                "NgayTao": row[3].strftime("%Y-%m-%d") if row[3] else None
            } for row in rows
        ]

        return {"success": True, "total": total, "categories": categories}
    except Exception as e:
        return {"success": False, "message": str(e)}

def add_danhmuc(data):
    try:
        ten_hang = data.get("TenDanhMuc")
        if not ten_hang:
            return {"success": False, "message": "Tên danh mục không được để trống"}

        conn = get_connection()
        cursor = conn.cursor()

        # Kiểm tra trùng tên
        cursor.execute("SELECT COUNT(*) FROM DanhMucSanPham WHERE TenDanhMuc = ?", ten_hang)
        if cursor.fetchone()[0] > 0:
            return {"success": False, "message": "Tên danh mục đã tồn tại"}

        cursor.execute("""
            INSERT INTO DanhMucSanPham (TenDanhMuc, TrangThai, NgayTao)
            VALUES (?, ?, ?)
        """, ten_hang, True, datetime.now())
        conn.commit()
        conn.close()
        return {"success": True, "message": "Thêm danh mục thành công"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def update_danhmuc(data):
    try:
        ma_hang = data.get("MaDanhMuc")
        ten_hang = data.get("TenDanhMuc")

        if not ten_hang:
            return {"success": False, "message": "Tên danh mục không được để trống"}

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM DanhMucSanPham WHERE TenDanhMuc = ? AND MaDanhMuc != ?", ten_hang, ma_hang)
        if cursor.fetchone()[0] > 0:
            return {"success": False, "message": "Tên danh mục đã tồn tại"}

        cursor.execute("UPDATE DanhMucSanPham SET TenDanhMuc = ? WHERE MaDanhMuc = ?", ten_hang, ma_hang)
        conn.commit()
        conn.close()
        return {"success": True, "message": "Cập nhật danh mục thành công"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def toggle_status_danhmuc(ma_hang):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT TrangThai FROM DanhMucSanPham WHERE MaDanhMuc = ?", ma_hang)
        current_status = cursor.fetchone()
        if not current_status:
            return {"success": False, "message": "Không tìm thấy danh mục"}

        new_status = not current_status[0]
        cursor.execute("UPDATE DanhMucSanPham SET TrangThai = ? WHERE MaDanhMuc = ?", new_status, ma_hang)
        conn.commit()
        conn.close()
        return {"success": True, "message": "Cập nhật trạng thái thành công"}
    except Exception as e:
        return {"success": False, "message": str(e)}
def get_danhmuc_by_id(ma_hang):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM DanhMucSanPham WHERE MaDanhMuc = ?", ma_hang)
        category = cursor.fetchone()
        conn.close()

        if not category:
            return {"success": False, "message": "Không tìm thấy danh mục"}

        # Chuyển đổi Row thành dictionary
        columns = [column[0] for column in cursor.description]  # Lấy tên cột
        category_dict = dict(zip(columns, category))  # Kết hợp tên cột với giá trị

        # Trả về thông tin danh mục dưới dạng dictionary
        return {"success": True, "category": category_dict}
    except Exception as e:
        # Ghi lại lỗi
        print(f"Error: {str(e)}")
        return {"success": False, "message": str(e)}


