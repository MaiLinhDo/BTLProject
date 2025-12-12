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
            SELECT pn.MaPhieuNhap, pn.NgayNhap, pn.TongTien, pn.GhiChu,
                   pn.MaNhaCungCap, ISNULL(ncc.TenNhaCungCap, N'') AS TenNhaCungCap,
                   pn.NguoiTao, pn.TrangThai, pn.SoPhieuNhap, pn.NgayCapNhat
            FROM PhieuNhapKho pn
            LEFT JOIN NhaCungCap ncc ON pn.MaNhaCungCap = ncc.MaNhaCungCap
            WHERE pn.MaPhieuNhap = ?
            ORDER BY pn.NgayNhap DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        cursor.execute(query, (search_string, offset, page_size))
    else:
        query = """
            SELECT pn.MaPhieuNhap, pn.NgayNhap, pn.TongTien, pn.GhiChu,
                   pn.MaNhaCungCap, ISNULL(ncc.TenNhaCungCap, N'') AS TenNhaCungCap,
                   pn.NguoiTao, pn.TrangThai, pn.SoPhieuNhap, pn.NgayCapNhat
            FROM PhieuNhapKho pn
            LEFT JOIN NhaCungCap ncc ON pn.MaNhaCungCap = ncc.MaNhaCungCap
            ORDER BY pn.NgayNhap DESC
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
            "GhiChu": row[3],
            "MaNhaCungCap": row[4],
            "TenNhaCungCap": row[5],
            "NguoiTao": row[6],
            "TrangThai": row[7],
            "SoPhieuNhap": row[8],
            "NgayCapNhat": row[9] if len(row) > 9 else None
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
        SELECT pn.MaPhieuNhap, pn.NgayNhap, pn.TongTien, pn.GhiChu,
               pn.MaNhaCungCap, ISNULL(ncc.TenNhaCungCap, N''), ISNULL(ncc.SoDienThoai, N''), ISNULL(ncc.Email, N''),
               pn.NguoiTao, pn.TrangThai, pn.SoPhieuNhap, pn.NgayCapNhat
        FROM PhieuNhapKho pn
        LEFT JOIN NhaCungCap ncc ON pn.MaNhaCungCap = ncc.MaNhaCungCap
        WHERE pn.MaPhieuNhap = ?
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
        "GhiChu": row[3],
        "MaNhaCungCap": row[4],
        "TenNhaCungCap": row[5],
        "SoDienThoaiNCC": row[6],
        "EmailNCC": row[7],
        "NguoiTao": row[8] if len(row) > 8 else None,
        "TrangThai": row[9] if len(row) > 9 else None,
        "SoPhieuNhap": row[10] if len(row) > 10 else None,
        "NgayCapNhat": row[11] if len(row) > 11 else None
    }

    # Truy vấn chi tiết phiếu nhập kho
    query_chitiet = """
      SELECT ctpn.MaChiTiet, ctpn.MaPhieuNhap, ctpn.MaSanPham, ctpn.SoLuong, ctpn.GiaNhap, ctpn.TongTien, sp.TenSanPham
        FROM ChiTietPhieuNhapKho ctpn
        INNER JOIN SanPham sp ON ctpn.MaSanPham = sp.MaSanPham
        WHERE ctpn.MaPhieuNhap = ?
        ORDER BY ctpn.MaChiTiet
    """
    cursor.execute(query_chitiet, (ma_phieu,))
    chitiet_rows = cursor.fetchall()

    detail_ids = [row[0] for row in chitiet_rows]
    serial_map = {}
    if detail_ids:
        placeholders = ",".join(['?'] * len(detail_ids))
        cursor.execute(f"""
            SELECT MaChiTietPhieuNhap, SerialNumber
            FROM SanPhamSerial
            WHERE MaChiTietPhieuNhap IN ({placeholders})
            ORDER BY SerialNumber
        """, detail_ids)
        for detail_id, serial in cursor.fetchall():
            serial_map.setdefault(detail_id, []).append(serial)

    chi_tiet_list = [
        {
            "MaChiTiet": row[0],
            "MaPhieuNhap": row[1],
            "MaSanPham": row[2],
            "SoLuong": row[3],
            "GiaNhap": row[4],
            "TongTien": row[5],
            "TenSanPham": row[6],
            "SerialNumbers": serial_map.get(row[0], [])
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
        supplier_id = phieu_nhap.get("MaNhaCungCap")
        if not supplier_id:
            return jsonify({"success": False, "message": "Vui lòng chọn nhà cung cấp"}), 400

        cursor.execute("SELECT COUNT(*) FROM NhaCungCap WHERE MaNhaCungCap = ?", (supplier_id,))
        if cursor.fetchone()[0] == 0:
            return jsonify({"success": False, "message": "Nhà cung cấp không tồn tại"}), 400

        # Tạo phiếu nhập kho mới
        insert_phieu = """
            INSERT INTO PhieuNhapKho (NgayNhap, TongTien, GhiChu, MaNhaCungCap, NguoiTao, TrangThai, SoPhieuNhap, NgayCapNhat)
            OUTPUT INSERTED.MaPhieuNhap
            VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
        """
        ngay_nhap = datetime.now()
        nguoi_tao = phieu_nhap.get("NguoiTao")
        trang_thai = phieu_nhap.get("TrangThai", "Đã nhập")
        so_phieu_nhap = phieu_nhap.get("SoPhieuNhap")
        cursor.execute(insert_phieu, (ngay_nhap, 0, phieu_nhap.get("GhiChu", ""), supplier_id, nguoi_tao, trang_thai, so_phieu_nhap))
        ma_phieu = cursor.fetchone()[0]

        tong_tien = 0

        for chi_tiet in chi_tiets:
            ma_san_pham = chi_tiet["MaSanPham"]
            so_luong = chi_tiet["SoLuong"]
            gia_nhap = chi_tiet["GiaNhap"]
            thanh_tien = so_luong * gia_nhap
            serial_values = chi_tiet.get("SerialNumbers", [])

            if isinstance(serial_values, str):
                serial_values = [serial.strip() for serial in serial_values.replace(",", "\n").splitlines() if serial.strip()]
            elif isinstance(serial_values, list):
                serial_values = [str(serial).strip() for serial in serial_values if str(serial).strip()]
            else:
                serial_values = []

            if len(serial_values) != so_luong:
                conn.rollback()
                return jsonify({
                    "success": False,
                    "message": f"Số lượng serial của sản phẩm {ma_san_pham} không khớp với số lượng nhập."
                }), 400

            insert_detail = """
                INSERT INTO ChiTietPhieuNhapKho (MaPhieuNhap, MaSanPham, SoLuong, GiaNhap)
                OUTPUT INSERTED.MaChiTiet
                VALUES (?, ?, ?, ?)
            """
            cursor.execute(insert_detail, (ma_phieu, ma_san_pham, so_luong, gia_nhap))
            ma_chi_tiet = cursor.fetchone()[0]

            for serial in serial_values:
                cursor.execute("""
                    INSERT INTO SanPhamSerial (MaSanPham, MaChiTietPhieuNhap, MaPhieuNhap, SerialNumber, TrangThai)
                    VALUES (?, ?, ?, ?, N'Trong kho')
                """, (ma_san_pham, ma_chi_tiet, ma_phieu, serial))

            # Cập nhật SoLuong = số serial "Trong kho" (tồn dư) sau khi nhập kho
            cursor.execute("""
                UPDATE SanPham
                SET SoLuong = (
                    SELECT COUNT(*) 
                    FROM SanPhamSerial 
                    WHERE MaSanPham = ? AND TrangThai = N'Trong kho'
                )
                WHERE MaSanPham = ?
            """, (ma_san_pham, ma_san_pham))

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

