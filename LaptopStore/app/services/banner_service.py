from datetime import datetime
import pyodbc
from app.config import Config
from flask import request

def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)
def get_all_banners(page=1, page_size=5, search=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        base_query = "SELECT MaBanner, HinhAnh, LienKet, MoTa FROM Banner"
        count_query = "SELECT COUNT(*) FROM Banner"
        params = []

        if search:
            base_query += " WHERE MoTa LIKE ?"
            count_query += " WHERE MoTa LIKE ?"
            params.append(f"%{search}%")

        base_query += " ORDER BY MaBanner OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([(page - 1) * page_size, page_size])

        cursor.execute(count_query, *(params[:-2] if search else []))
        total = cursor.fetchone()[0]

        cursor.execute(base_query, *params)
        rows = cursor.fetchall()
        conn.close()

        banners = [
            {
                "MaBanner": row[0],
                "MoTa": row[3],
                "HinhAnh": row[1],
                "LienKet": row[2],
            } for row in rows
        ]

        return {"success": True, "total": total, "banners": banners}
    except Exception as e:
        return {"success": False, "message": str(e)}

def add_banner(data):
    try:
        tieude = data.get("MoTa")
        hinhanh = data.get("HinhAnh")
        lienket = data.get("LienKet")
        if not tieude or not hinhanh:
            return {"success": False, "message": "Tiêu đề và hình ảnh không được để trống"}

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Banner (MoTa, HinhAnh, LienKet)
            VALUES (?, ?, ?)
        """, tieude, hinhanh, lienket)

        conn.commit()
        conn.close()
        return {"success": True, "message": "Thêm banner thành công"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def update_banner(data):
    try:
        ma_banner = data.get("MaBanner")
        tieude = data.get("MoTa")
        hinhanh = data.get("HinhAnh")
        lienket = data.get("LienKet")
        if not tieude:
            return {"success": False, "message": "Tiêu đề không được để trống"}

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE Banner SET MoTa = ?, HinhAnh = ?
            WHERE MaBanner = ?
        """, tieude, hinhanh, ma_banner)

        conn.commit()
        conn.close()
        return {"success": True, "message": "Cập nhật banner thành công"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_banner_by_id(ma_banner):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Banner WHERE MaBanner = ?", ma_banner)
        banner = cursor.fetchone()

        if not banner:
            return {"success": False, "message": "Không tìm thấy banner"}

        columns = [column[0] for column in cursor.description]
        banner_dict = dict(zip(columns, banner))

        conn.close()
        return {"success": True, "banner": banner_dict}
    except Exception as e:
        return {"success": False, "message": str(e)}
def delete_banner(ma_banner):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Banner WHERE MaBanner = ?", ma_banner)
        conn.commit()
        conn.close()
        return {"success": True, "message": "Xóa banner thành công"}
    except Exception as e:
        return {"success": False, "message": str(e)}