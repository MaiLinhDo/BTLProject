from flask import Blueprint, request, jsonify
from app.config import Config
import pyodbc
from datetime import datetime, timedelta
import json
from datetime import datetime
def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)

warranty_routes = Blueprint('warranty_routes', __name__)

# 2. Lấy danh sách phiếu bảo hành
@warranty_routes.route('/api/get_phieu_bao_hanh', methods=['POST'])
def get_phieu_bao_hanh():
    data = request.json
    search_string = data.get("SearchString", "")
    trang_thai = data.get("TrangThai", "")
    page = data.get("Page", 1)
    page_size = data.get("PageSize", 10)
    ma_tai_khoan = data.get("MaTaiKhoan")  # Nếu lấy theo user
    
    conn = get_connection()
    cursor = conn.cursor()
    
    offset = (page - 1) * page_size
    
    # Base query
    base_query = """
        SELECT PBH.MaPhieuBH, PBH.MaDonHang, PBH.SoLuongBH, PBH.MoTaLoi, 
               PBH.NgayTao, PBH.NgayBatDauBH, PBH.NgayKetThucBH, PBH.TrangThai,
               PBH.LyDoTuChoi, SP.TenSanPham, SP.HinhAnh, TK.HoTen,
               CASE WHEN PBH.NgayKetThucBH > GETDATE() THEN 1 ELSE 0 END as ConBaoHanh,
               DATEDIFF(day, GETDATE(), PBH.NgayKetThucBH) as SoNgayConLai,SP.MaSanPham
        FROM PhieuBaoHanh PBH
        INNER JOIN SanPham SP ON PBH.MaSanPham = SP.MaSanPham
        INNER JOIN TaiKhoan TK ON PBH.MaTaiKhoan = TK.MaTaiKhoan
        WHERE 1=1
    """
    
    params = []
    
    # Filters
    if ma_tai_khoan:
        base_query += " AND PBH.MaTaiKhoan = ?"
        params.append(ma_tai_khoan)
    
    if search_string:
        base_query += " AND (SP.TenSanPham LIKE ? OR TK.HoTen LIKE ? OR PBH.MoTaLoi LIKE ?)"
        search_param = f"%{search_string}%"
        params.extend([search_param, search_param, search_param])
    
    if trang_thai:
        base_query += " AND PBH.TrangThai = ?"
        params.append(trang_thai)
    
    # Count total
    count_query = f"SELECT COUNT(*) FROM ({base_query}) as CountQuery"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]
    
    # Get paginated data
    base_query += " ORDER BY PBH.NgayTao DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
    params.extend([offset, page_size])
    
    cursor.execute(base_query, params)
    rows = cursor.fetchall()
    
    phieu_bao_hanh_list = []
    for row in rows:
        phieu_bao_hanh_list.append({
            "MaPhieuBH": row[0],
            "MaDonHang": row[1],
            "SoLuongBH": row[2],
            "MoTaLoi": row[3],
            "NgayTao": row[4].strftime("%Y-%m-%d %H:%M:%S") if row[4] else None,
            "NgayBatDauBH": row[5].strftime("%Y-%m-%d") if row[5] else None,
            "NgayKetThucBH": row[6].strftime("%Y-%m-%d") if row[6] else None,
            "TrangThai": row[7],
            "LyDoTuChoi": row[8],
            "TenSanPham": row[9],
            "HinhAnhSP": row[10],
            "TenKhachHang": row[11],
            "ConBaoHanh": bool(row[12]),
            "SoNgayConLai": max(0, row[13]) if row[13] else 0,
            "MaSanPham": row[14]
        })
    
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    
    conn.close()
    
    return jsonify({
        "success": True,
        "phieuBaoHanh": phieu_bao_hanh_list,
        "totalPages": total_pages,
        "totalCount": total_count,
        "currentPage": page
    })

# 3. Cập nhật trạng thái phiếu bảo hành
@warranty_routes.route('/api/cap_nhat_trang_thai_bao_hanh', methods=['POST'])
def cap_nhat_trang_thai_bao_hanh():
    data = request.json
    ma_phieu_bh = data.get("MaPhieuBH")
    trang_thai_moi = data.get("TrangThai")
    ly_do_tu_choi = data.get("LyDoTuChoi")
    ghi_chu = data.get("GhiChu")
    nhan_vien_xu_ly = data.get("NhanVienXuLy")
    
    if not ma_phieu_bh or not trang_thai_moi:
        return jsonify({"success": False, "message": "Thiếu thông tin bắt buộc"}), 400
    
    # Validate trạng thái
    valid_states = ["Chờ xử lý", "Đã duyệt", "Chờ lấy hàng bảo hành", "Đang vận chuyển", 
                   "Đang bảo hành", "Bảo hành hoàn tất", "Chờ trả hàng", "Đã trả hàng", 
                   "Hoàn tất", "Từ chối"]
    
    if trang_thai_moi not in valid_states:
        return jsonify({"success": False, "message": "Trạng thái không hợp lệ"}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Kiểm tra phiếu tồn tại
        cursor.execute("SELECT TrangThai FROM PhieuBaoHanh WHERE MaPhieuBH = ?", (ma_phieu_bh,))
        current_record = cursor.fetchone()
        if not current_record:
            return jsonify({"success": False, "message": "Không tìm thấy phiếu bảo hành"}), 404
        
        trang_thai_cu = current_record[0]
        
        # Cập nhật trạng thái
        update_query = """
            UPDATE PhieuBaoHanh 
            SET TrangThai = ?, NgayCapNhat = GETDATE()
        """
        update_params = [trang_thai_moi]
        
        if ly_do_tu_choi:
            update_query += ", LyDoTuChoi = ?"
            update_params.append(ly_do_tu_choi)
        
        if nhan_vien_xu_ly:
            update_query += ", NhanVienXuLy = ?"
            update_params.append(nhan_vien_xu_ly)
        
        update_query += " WHERE MaPhieuBH = ?"
        update_params.append(ma_phieu_bh)
        
        cursor.execute(update_query, update_params)
        
        # Lưu lịch sử (trigger sẽ tự động thực hiện)
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": f"Cập nhật trạng thái từ '{trang_thai_cu}' sang '{trang_thai_moi}' thành công"
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# 4. Lấy chi tiết phiếu bảo hành
def safe_strftime(value, fmt="%Y-%m-%d %H:%M:%S"):
    """Định dạng ngày giờ an toàn từ datetime hoặc string"""
    if not value:
        return None
    if isinstance(value, str):
        try:
            # Thử parse string về datetime
            dt = datetime.fromisoformat(value.replace("Z", "").strip())
            return dt.strftime(fmt)
        except Exception:
            return value  # Nếu parse fail thì trả lại string
    return value.strftime(fmt)


# 4. Lấy chi tiết phiếu bảo hành - FIXED
@warranty_routes.route('/api/get_chi_tiet_bao_hanh', methods=['POST'])
def get_chi_tiet_bao_hanh():
    data = request.json
    ma_phieu_bh = data.get("MaPhieuBH")
    if not ma_phieu_bh:
        return jsonify({"success": False, "message": "Thiếu mã phiếu bảo hành"}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Lấy thông tin phiếu bảo hành với thứ tự rõ ràng
        cursor.execute("""
            SELECT 
                PBH.MaPhieuBH,          -- 0
                PBH.MaDonHang,          -- 1  
                PBH.MaTaiKhoan,         -- 2
                PBH.MaSanPham,          -- 3
                PBH.SoLuongBH,          -- 4
                PBH.MoTaLoi,            -- 5
                PBH.HinhAnhLoi,         -- 6
                PBH.NgayTao,            -- 7
                PBH.NgayBatDauBH,       -- 8
                PBH.NgayKetThucBH,      -- 9
                PBH.TrangThai,          -- 10
                PBH.LyDoTuChoi,         -- 11
                PBH.NhanVienXuLy,       -- 12
                SP.TenSanPham,          -- 13
                SP.HinhAnh,             -- 14
                TK.HoTen,               -- 15
                TK.SoDienThoai,         -- 16
                TK.Email,               -- 17
                DH.DiaChiGiaoHang,      -- 18
                DH.NgayDatHang,         -- 19
                CASE WHEN PBH.NgayKetThucBH > GETDATE() THEN 1 ELSE 0 END as ConBaoHanh,     -- 20
                DATEDIFF(day, GETDATE(), PBH.NgayKetThucBH) as SoNgayConLai                  -- 21
            FROM PhieuBaoHanh PBH
            INNER JOIN SanPham SP ON PBH.MaSanPham = SP.MaSanPham
            INNER JOIN TaiKhoan TK ON PBH.MaTaiKhoan = TK.MaTaiKhoan
            INNER JOIN DonHang DH ON PBH.MaDonHang = DH.MaDonHang
            WHERE PBH.MaPhieuBH = ?
        """, (ma_phieu_bh,))
        
        phieu_row = cursor.fetchone()
        if not phieu_row:
            return jsonify({"success": False, "message": "Không tìm thấy phiếu bảo hành"}), 404
        
        # Lịch sử xử lý
        cursor.execute("""
            SELECT TrangThaiCu, TrangThaiMoi, MoTa, NgayCapNhat, NguoiCapNhat
            FROM LichSuBaoHanh
            WHERE MaPhieuBH = ?
            ORDER BY NgayCapNhat DESC
        """, (ma_phieu_bh,))
        
        lich_su = []
        for row in cursor.fetchall():
            lich_su.append({
                "TrangThaiCu": row[0],
                "TrangThaiMoi": row[1], 
                "MoTa": row[2],
                "NgayCapNhat": safe_strftime(row[3], "%Y-%m-%d %H:%M:%S"),
                "NguoiCapNhat": row[4]
            })
        
        # Vận chuyển
        cursor.execute("""
            SELECT LoaiVanChuyen, DonViVanChuyen, MaVanDon, NgayLayHang, NgayGiaoHang, 
                   TrangThaiVanChuyen, GhiChu
            FROM VanChuyenBaoHanh
            WHERE MaPhieuBH = ?
            ORDER BY NgayLayHang DESC
        """, (ma_phieu_bh,))
        
        van_chuyen = []
        for row in cursor.fetchall():
            van_chuyen.append({
                "LoaiVanChuyen": row[0],
                "DonViVanChuyen": row[1],
                "MaVanDon": row[2],
                "NgayLayHang": safe_strftime(row[3], "%Y-%m-%d %H:%M:%S"),
                "NgayGiaoHang": safe_strftime(row[4], "%Y-%m-%d %H:%M:%S"),
                "TrangThaiVanChuyen": row[5],
                "GhiChu": row[6]
            })
        
        # Xử lý từ nhà sản xuất
        cursor.execute("""
            SELECT TenNhaSanXuat, MaPhieuNSX, NgayGui, NgayNhan, NgayHoanTat,
                   HinhThucXuLy, MoTaXuLy, ChiPhi, TrangThai
            FROM XuLyNhaSanXuat
            WHERE MaPhieuBH = ?
        """, (ma_phieu_bh,))
        
        xu_ly_nsx = []
        for row in cursor.fetchall():
            xu_ly_nsx.append({
                "TenNhaSanXuat": row[0],
                "MaPhieuNSX": row[1],
                "NgayGui": safe_strftime(row[2], "%Y-%m-%d"),
                "NgayNhan": safe_strftime(row[3], "%Y-%m-%d"),
                "NgayHoanTat": safe_strftime(row[4], "%Y-%m-%d"),
                "HinhThucXuLy": row[5],
                "MoTaXuLy": row[6],
                "ChiPhi": float(row[7]) if row[7] else 0,
                "TrangThai": row[8]
            })
        
        # Parse hình ảnh lỗi
        hinh_anh_loi = []
        if phieu_row[6]:  # HinhAnhLoi
            try:
                hinh_anh_loi = json.loads(phieu_row[6])
                if not isinstance(hinh_anh_loi, list):
                    hinh_anh_loi = []
            except:
                hinh_anh_loi = []
        
        # Mapping đúng thứ tự các trường
        chi_tiet = {
            "MaPhieuBH": phieu_row[0],
            "MaDonHang": phieu_row[1],
            "MaTaiKhoan": phieu_row[2],
            "MaSanPham": phieu_row[3],
            "SoLuongBH": phieu_row[4],
            "MoTaLoi": phieu_row[5],
            "HinhAnhLoi": hinh_anh_loi,
            "NgayTao": safe_strftime(phieu_row[7], "%Y-%m-%d %H:%M:%S"),
            "NgayBatDauBH": safe_strftime(phieu_row[8], "%Y-%m-%d"),
            "NgayKetThucBH": safe_strftime(phieu_row[9], "%Y-%m-%d"),
            "TrangThai": phieu_row[10],
            "LyDoTuChoi": phieu_row[11],
            "NhanVienXuLy": phieu_row[12],
            "TenSanPham": phieu_row[13],
            "HinhAnhSP": phieu_row[14],
            "TenKhachHang": phieu_row[15],
            "SoDienThoai": phieu_row[16],
            "Email": phieu_row[17],
            "DiaChiGiaoHang": phieu_row[18],
            "NgayMua": safe_strftime(phieu_row[19], "%Y-%m-%d"),
            "ConBaoHanh": bool(phieu_row[20]),
            "SoNgayConLai": max(0, phieu_row[21]) if phieu_row[21] else 0,
            "LichSu": lich_su,
            "VanChuyen": van_chuyen,
            "XuLyNhaSanXuat": xu_ly_nsx
        }
        
        conn.close()
        return jsonify({"success": True, "chiTiet": chi_tiet})
        
    except Exception as e:
        conn.close()
        print(f"Error in get_chi_tiet_bao_hanh: {str(e)}")
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500

# 7. Thống kê bảo hành
@warranty_routes.route('/api/thong_ke_bao_hanh', methods=['POST'])
def thong_ke_bao_hanh():
    data = request.json
    start_date = data.get("startDate")
    end_date = data.get("endDate")
    
    if not start_date or not end_date:
        return jsonify({"success": False, "message": "Thiếu ngày bắt đầu hoặc kết thúc"}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Thống kê tổng quan
        cursor.execute("""
            SELECT 
                COUNT(*) as TongPhieu,
                SUM(CASE WHEN TrangThai = N'Chờ xử lý' THEN 1 ELSE 0 END) as ChoXuLy,
                SUM(CASE WHEN TrangThai IN (N'Đang bảo hành', N'Chờ lấy hàng bảo hành') THEN 1 ELSE 0 END) as DangBaoHanh,
                SUM(CASE WHEN TrangThai = N'Hoàn tất' THEN 1 ELSE 0 END) as HoanTat,
                SUM(CASE WHEN TrangThai = N'Từ chối' THEN 1 ELSE 0 END) as TuChoi
            FROM PhieuBaoHanh
            WHERE NgayTao BETWEEN ? AND ?
        """, (start_date, end_date))
        
        thong_ke_tong = cursor.fetchone()
        
        # Thống kê chi phí
        cursor.execute("""
            SELECT ISNULL(SUM(NSX.ChiPhi), 0) as TongChiPhi
            FROM PhieuBaoHanh PBH
            LEFT JOIN XuLyNhaSanXuat NSX ON PBH.MaPhieuBH = NSX.MaPhieuBH
            WHERE PBH.NgayTao BETWEEN ? AND ?
        """, (start_date, end_date))
        
        tong_chi_phi = cursor.fetchone()[0] or 0
        
        # Top sản phẩm bảo hành nhiều nhất
        cursor.execute("""
            SELECT TOP 5
                SP.TenSanPham,
                COUNT(*) as SoLuongBH,
                CAST(COUNT(*) * 100.0 / (
                    SELECT COUNT(*) 
                    FROM ChiTietDonHang CT2
                    INNER JOIN DonHang DH2 ON CT2.MaDonHang = DH2.MaDonHang
                    WHERE CT2.MaSanPham = PBH.MaSanPham 
                    AND DH2.NgayDatHang <= GETDATE()
                ) as DECIMAL(5,2)) as TiLeBaoHanh
            FROM PhieuBaoHanh PBH
            INNER JOIN SanPham SP ON PBH.MaSanPham = SP.MaSanPham
            WHERE PBH.NgayTao BETWEEN ? AND ?
            GROUP BY PBH.MaSanPham, SP.TenSanPham
            ORDER BY SoLuongBH DESC
        """, (start_date, end_date))
        
        top_san_pham = []
        for row in cursor.fetchall():
            top_san_pham.append({
                "TenSanPham": row[0],
                "SoLuongBH": row[1],
                "TiLeBaoHanh": float(row[2]) if row[2] else 0
            })
        
        # Biểu đồ theo tháng
        cursor.execute("""
            SELECT 
                MONTH(PBH.NgayTao) as Thang,
                YEAR(PBH.NgayTao) as Nam,
                COUNT(*) as SoLuongBH,
                ISNULL(SUM(NSX.ChiPhi), 0) as ChiPhi
            FROM PhieuBaoHanh PBH
            LEFT JOIN XuLyNhaSanXuat NSX ON PBH.MaPhieuBH = NSX.MaPhieuBH
            WHERE PBH.NgayTao BETWEEN ? AND ?
            GROUP BY YEAR(PBH.NgayTao), MONTH(PBH.NgayTao)
            ORDER BY Nam, Thang
        """, (start_date, end_date))
        
        bieu_do_thang = []
        for row in cursor.fetchall():
            bieu_do_thang.append({
                "Thang": row[0],
                "Nam": row[1],
                "SoLuongBH": row[2],
                "ChiPhi": float(row[3]) if row[3] else 0
            })
        
        conn.close()
        
        return jsonify({
            "success": True,
            "tongPhieuBH": thong_ke_tong[0] or 0,
            "choXuLy": thong_ke_tong[1] or 0,
            "dangBaoHanh": thong_ke_tong[2] or 0,
            "hoanTat": thong_ke_tong[3] or 0,
            "tuChoi": thong_ke_tong[4] or 0,
            "tongChiPhi": float(tong_chi_phi),
            "topSanPhamLoi": top_san_pham,
            "bieuDoThang": bieu_do_thang
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

