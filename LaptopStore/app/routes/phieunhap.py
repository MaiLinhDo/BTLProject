from flask import Blueprint, request, jsonify
from app.config import Config
import pyodbc
from datetime import datetime
def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)

phieunhap_routes = Blueprint('phieunhap_routes', __name__)

@phieunhap_routes.route('/api/get_phieunhapkho', methods=['POST'])
def get_phieunhapkho():
    data = request.json
    search_string = data.get("SearchString", None)
    page = data.get("Page", 1)
    page_size = data.get("PageSize", 10)

    conn = get_connection()
    cursor = conn.cursor()

    offset = (page - 1) * page_size

    # Truy vấn chính
    if search_string:
        query = """
            SELECT MaPhieuNhap, NgayNhap, TongTien,GhiChu
            FROM PhieuNhapKho
            WHERE MaPhieuNhap = ?
            ORDER BY NgayNhap DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        cursor.execute(query, (search_string, offset, page_size))
    else:
        query = """
            SELECT MaPhieuNhap, NgayNhap ,TongTien,GhiChu
            FROM PhieuNhapKho
            ORDER BY NgayNhap DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        cursor.execute(query, (offset, page_size))

    rows = cursor.fetchall()

    # Format dữ liệu trả về
    phieu_nhap_list = [
        {
            "MaPhieuNhap": row[0],
            "NgayNhap": row[1],
            "TongTien": row[2],
            "GhiChu": row[3]
        }
        for row in rows
    ]

    # Đếm tổng số phiếu nhập để tính số trang
    if search_string:
        count_query = "SELECT COUNT(*) FROM PhieuNhapKho WHERE MaPhieuNhap = ?"
        cursor.execute(count_query, (search_string,))
    else:
        count_query = "SELECT COUNT(*) FROM PhieuNhapKho"
        cursor.execute(count_query)

    total_count = cursor.fetchone()[0]
    total_pages = (total_count // page_size) + (1 if total_count % page_size > 0 else 0)

    conn.close()

    return jsonify({
        "success": True,
        "phieuNhaps": phieu_nhap_list,
        "totalPages": total_pages
    })
@phieunhap_routes.route('/api/get_chitietphieunhap', methods=['POST'])
def get_chitiet_phieunhap():
    data = request.json
    ma_phieu = data.get("MaPhieuNhap", None)

    if not ma_phieu:
        return jsonify({"success": False, "message": "Thiếu mã phiếu nhập"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Truy vấn phiếu nhập kho
    query_phieu = """
        SELECT MaPhieuNhap,NgayNhap,TongTien, GhiChu
        FROM PhieuNhapKho
        WHERE MaPhieuNhap = ?
    """
    cursor.execute(query_phieu, (ma_phieu,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "message": "Không tìm thấy phiếu nhập"}), 404

    phieu_nhap = {
        "MaPhieuNhap": row[0],
        "NgayNhap": row[1],
        "TongTien": row[2],
        "GhiChu": row[3]
    }

    # Truy vấn chi tiết phiếu nhập kho
    query_chitiet = """
      SELECT MaChiTiet, MaPhieuNhap,ChiTietPhieuNhapKho.MaSanPham,ChiTietPhieuNhapKho.SoLuong,GiaNhap, TongTien, TenSanPham
        FROM ChiTietPhieuNhapKho, SanPham
        WHERE MaPhieuNhap = ? AND ChiTietPhieuNhapKho.MaSanPham = SanPham.MaSanPham
    """
    cursor.execute(query_chitiet, (ma_phieu,))
    chitiet_rows = cursor.fetchall()

    chi_tiet_list = [
        {
            "MaPhieuNhap": row[0],
            "MaChiTiet": row[1],
            "MaSanPham": row[2],
            "SoLuong": row[3],
            "GiaNhap": row[4],
            "TongTien": row[5],
            "TenSanPham": row[6]
        }
        for row in chitiet_rows
    ]

    conn.close()

    return jsonify({
        "success": True,
        "phieuNhap": phieu_nhap,
        "chiTiet": chi_tiet_list
    })
@phieunhap_routes.route('/api/create_phieunhap', methods=['POST'])
def create_phieunhap():
    data = request.json
    phieu_nhap = data.get("phieuNhapKho")
    chi_tiets = data.get("ChiTietPhieuNhaps", [])

    if not phieu_nhap or not chi_tiets:
        return jsonify({"success": False, "message": "Thiếu dữ liệu phiếu nhập hoặc chi tiết"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Tạo phiếu nhập kho mới
        insert_phieu = """
            INSERT INTO PhieuNhapKho (NgayNhap, TongTien, GhiChu)
            OUTPUT INSERTED.MaPhieuNhap
            VALUES (?, ?, ?)
        """
        ngay_nhap = datetime.now()
        cursor.execute(insert_phieu, (ngay_nhap, 0, phieu_nhap.get("GhiChu", "")))
        ma_phieu = cursor.fetchone()[0]

        tong_tien = 0

        for chi_tiet in chi_tiets:
            ma_san_pham = chi_tiet["MaSanPham"]
            so_luong = chi_tiet["SoLuong"]
            gia_nhap = chi_tiet["GiaNhap"]
            thanh_tien = so_luong * gia_nhap

            # Kiểm tra chi tiết đã tồn tại chưa
            cursor.execute("""
                SELECT SoLuong, GiaNhap FROM ChiTietPhieuNhapKho
                WHERE MaPhieuNhap = ? AND MaSanPham = ?
            """, (ma_phieu, ma_san_pham))
            existing = cursor.fetchone()

            if existing:
                # Nếu giá nhập không trùng thì báo lỗi
                if existing[1] != gia_nhap:
                    conn.rollback()
                    return jsonify({
                        "success": False,
                        "message": f"Sản phẩm {ma_san_pham} đã tồn tại với giá khác."
                    }), 400

                # Cập nhật số lượng trong chi tiết phiếu
                cursor.execute("""
                    UPDATE ChiTietPhieuNhapKho
                    SET SoLuong = SoLuong + ?
                    WHERE MaPhieuNhap = ? AND MaSanPham = ?
                """, (so_luong, ma_phieu, ma_san_pham))
            else:
                # Thêm mới chi tiết phiếu
                cursor.execute("""
                    INSERT INTO ChiTietPhieuNhapKho (MaPhieuNhap, MaSanPham, SoLuong, GiaNhap)
                    VALUES (?, ?, ?, ?)
                """, (ma_phieu, ma_san_pham, so_luong, gia_nhap))

            # Cập nhật số lượng tồn kho sản phẩm
            cursor.execute("""
                UPDATE SanPham
                SET SoLuong = SoLuong + ?
                WHERE MaSanPham = ?
            """, (so_luong, ma_san_pham))

            tong_tien += thanh_tien

        # Cập nhật tổng tiền
        cursor.execute("""
            UPDATE PhieuNhapKho
            SET TongTien = ?
            WHERE MaPhieuNhap = ?
        """, (tong_tien, ma_phieu))

        conn.commit()
        return jsonify({"success": True, "MaPhieuNhap": ma_phieu})

    except Exception as e:
        print(e)
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        conn.close()

