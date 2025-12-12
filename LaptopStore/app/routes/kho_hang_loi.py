from flask import Blueprint, request, jsonify
from app.config import Config
import pyodbc
from datetime import datetime

def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)

kho_hang_loi_routes = Blueprint('kho_hang_loi_routes', __name__)

@kho_hang_loi_routes.route('/api/get_kho_hang_loi', methods=['POST'])
def get_kho_hang_loi():
    data = request.json
    search_string = data.get("SearchString", None)
    page = data.get("Page", 1)
    page_size = data.get("PageSize", 10)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    offset = (page - 1) * page_size
    
    # Truy vấn từ SanPhamSerial với trạng thái Lỗi
    if search_string:
        query = """
            SELECT ss.MaSerial, ss.MaSanPham, s.TenSanPham, ss.SerialNumber, ss.TrangThai, ss.NgayBan
            FROM SanPhamSerial ss
            INNER JOIN SanPham s ON ss.MaSanPham = s.MaSanPham
            WHERE ss.TrangThai = N'Lỗi' AND (s.TenSanPham LIKE ? OR ss.SerialNumber LIKE ?)
            ORDER BY ss.MaSerial DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        search_param = f"%{search_string}%"
        cursor.execute(query, (search_param, search_param, offset, page_size))
    else:
        query = """
            SELECT ss.MaSerial, ss.MaSanPham, s.TenSanPham, ss.SerialNumber, ss.TrangThai, ss.NgayBan
            FROM SanPhamSerial ss
            INNER JOIN SanPham s ON ss.MaSanPham = s.MaSanPham
            WHERE ss.TrangThai = N'Lỗi'
            ORDER BY ss.MaSerial DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        cursor.execute(query, (offset, page_size))
    
    rows = cursor.fetchall()
    
    # Format dữ liệu trả về
    kho_hang_loi_list = [
        {
            "MaKhoLoi": row[0], # Using MaSerial as ID
            "MaSanPham": row[1],
            "TenSanPham": row[2],
            "SerialNumber": row[3], # New field
            "TrangThai": row[4],  # New field
            "NgayNhap": row[5].strftime("%Y-%m-%d %H:%M:%S") if row[5] else None # Using NgayBan as approx timestamp
        }
        for row in rows
    ]
    
    # Đếm tổng số bản ghi
    if search_string:
        count_query = """
            SELECT COUNT(*) 
            FROM SanPhamSerial ss
            INNER JOIN SanPham s ON ss.MaSanPham = s.MaSanPham
            WHERE ss.TrangThai = N'Lỗi' AND (s.TenSanPham LIKE ? OR ss.SerialNumber LIKE ?)
        """
        cursor.execute(count_query, (search_param, search_param))
    else:
        count_query = "SELECT COUNT(*) FROM SanPhamSerial WHERE TrangThai = N'Lỗi'"
        cursor.execute(count_query)
    
    total_count = cursor.fetchone()[0]
    total_pages = (total_count // page_size) + (1 if total_count % page_size > 0 else 0)
    
    conn.close()
    
    return jsonify({
        "success": True,
        "khoHangLoi": kho_hang_loi_list,
        "totalPages": total_pages,
        "totalCount": total_count
    })

@kho_hang_loi_routes.route('/api/them_kho_hang_loi', methods=['POST'])
def them_kho_hang_loi():
    data = request.json
    ma_san_pham = data.get("MaSanPham")
    so_luong = data.get("SoLuong")
    ly_do = data.get("LyDo", "")
    
    if not ma_san_pham or not so_luong:
        return jsonify({"success": False, "message": "Thiếu thông tin sản phẩm hoặc số lượng"}), 400
    
    if so_luong <= 0:
        return jsonify({"success": False, "message": "Số lượng phải lớn hơn 0"}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Kiểm tra sản phẩm có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM SanPham WHERE MaSanPham = ?", (ma_san_pham,))
        if cursor.fetchone()[0] == 0:
            return jsonify({"success": False, "message": "Sản phẩm không tồn tại"}), 404
        
        # Thêm vào kho hàng lỗi
        insert_query = """
            INSERT INTO KhoHangLoi (MaSanPham, SoLuong, LyDo, NgayNhap)
            VALUES (?, ?, ?, ?)
        """
        ngay_nhap = datetime.now()
        cursor.execute(insert_query, (ma_san_pham, so_luong, ly_do, ngay_nhap))
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Thêm sản phẩm vào kho hàng lỗi thành công"
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@kho_hang_loi_routes.route('/api/xoa_kho_hang_loi', methods=['POST'])
def xoa_kho_hang_loi():
    data = request.json
    ma_kho_loi = data.get("MaKhoLoi")
    
    if not ma_kho_loi:
        return jsonify({"success": False, "message": "Thiếu mã kho lỗi"}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Kiểm tra bản ghi có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM KhoHangLoi WHERE MaKhoLoi = ?", (ma_kho_loi,))
        if cursor.fetchone()[0] == 0:
            return jsonify({"success": False, "message": "Không tìm thấy bản ghi"}), 404
        
        # Xóa bản ghi
        cursor.execute("DELETE FROM KhoHangLoi WHERE MaKhoLoi = ?", (ma_kho_loi,))
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Xóa bản ghi thành công"
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@kho_hang_loi_routes.route('/api/cap_nhat_kho_hang_loi', methods=['POST'])
def cap_nhat_kho_hang_loi():
    data = request.json
    ma_kho_loi = data.get("MaKhoLoi")
    so_luong = data.get("SoLuong")
    ly_do = data.get("LyDo")
    
    if not ma_kho_loi:
        return jsonify({"success": False, "message": "Thiếu mã kho lỗi"}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Kiểm tra bản ghi có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM KhoHangLoi WHERE MaKhoLoi = ?", (ma_kho_loi,))
        if cursor.fetchone()[0] == 0:
            return jsonify({"success": False, "message": "Không tìm thấy bản ghi"}), 404
        
        # Cập nhật thông tin
        update_query = """
            UPDATE KhoHangLoi 
            SET SoLuong = ?, LyDo = ?
            WHERE MaKhoLoi = ?
        """
        cursor.execute(update_query, (so_luong, ly_do, ma_kho_loi))
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Cập nhật thành công"
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@kho_hang_loi_routes.route('/api/thong_ke_kho_hang_loi', methods=['GET'])
def thong_ke_kho_hang_loi():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Thống kê tổng số sản phẩm lỗi
        cursor.execute("SELECT COUNT(*), SUM(SoLuong) FROM KhoHangLoi")
        tong_san_pham, tong_so_luong = cursor.fetchone()
        
        # Thống kê theo sản phẩm
        cursor.execute("""
            SELECT s.TenSanPham, SUM(k.SoLuong) as TongSoLuong, COUNT(*) as SoLanNhap
            FROM KhoHangLoi k
            INNER JOIN SanPham s ON k.MaSanPham = s.MaSanPham
            GROUP BY s.MaSanPham, s.TenSanPham
            ORDER BY TongSoLuong DESC
        """)
        thong_ke_san_pham = [
            {
                "TenSanPham": row[0],
                "TongSoLuong": row[1],
                "SoLanNhap": row[2]
            }
            for row in cursor.fetchall()
        ]
        
        return jsonify({
            "success": True,
            "tongSanPham": tong_san_pham or 0,
            "tongSoLuong": tong_so_luong or 0,
            "thongKeSanPham": thong_ke_san_pham
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()