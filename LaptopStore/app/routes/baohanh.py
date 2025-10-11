from flask import Blueprint, request, jsonify
from app.config import Config
import pyodbc
from datetime import datetime, timedelta
import json
from datetime import datetime
def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)

warranty_routes = Blueprint('warranty_routes', __name__)
# 1. Tạo phiếu bảo hành (FIXED)
@warranty_routes.route('/api/tao_phieu_bao_hanh', methods=['POST'])
def tao_phieu_bao_hanh():
    data = request.json
    ma_don_hang = data.get("MaDonHang")
    ma_san_pham = data.get("MaSanPham")
    so_luong_bh = data.get("SoLuongBH", 1)
    mo_ta_loi = data.get("MoTaLoi")
    hinh_anh_loi = data.get("HinhAnhLoi", [])  # Danh sách tên file từ C#
    
    if not all([ma_don_hang, ma_san_pham, mo_ta_loi]):
        return jsonify({"success": False, "message": "Thiếu thông tin bắt buộc"}), 400
    
    # CONVERT SANG INTEGER VÀ VALIDATE
    try:
        ma_don_hang = int(ma_don_hang)
        ma_san_pham = int(ma_san_pham)
        so_luong_bh = int(so_luong_bh)
        
        if so_luong_bh <= 0:
            return jsonify({"success": False, "message": "Số lượng bảo hành phải lớn hơn 0"}), 400
            
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Dữ liệu đầu vào không hợp lệ"}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Kiểm tra đơn hàng và sản phẩm
        cursor.execute("""
            SELECT DH.MaTaiKhoan, DH.NgayDatHang, DH.TrangThai, CT.SoLuong
            FROM DonHang DH
            INNER JOIN ChiTietDonHang CT ON DH.MaDonHang = CT.MaDonHang
            WHERE DH.MaDonHang = ? AND CT.MaSanPham = ?
        """, (ma_don_hang, ma_san_pham))
        
        don_hang_info = cursor.fetchone()
        if not don_hang_info:
            return jsonify({"success": False, "message": "Không tìm thấy đơn hàng hoặc sản phẩm"}), 404
        
        ma_tai_khoan, ngay_dat_hang, trang_thai_dh, so_luong_mua = don_hang_info
        
        # CONVERT so_luong_mua SANG INT NẾU CẦN
        so_luong_mua = int(so_luong_mua) if so_luong_mua else 0
        
        # Kiểm tra đơn hàng đã giao
        if trang_thai_dh != "Đã giao":
            return jsonify({"success": False, "message": "Đơn hàng chưa được giao, không thể tạo phiếu bảo hành"}), 400
        
        # XỬ LÝ NGÀY THÁNG AN TOÀN HƠN
        try:
            if isinstance(ngay_dat_hang, str):
                ngay_dat_hang = datetime.strptime(ngay_dat_hang, "%Y-%m-%d")
            elif not isinstance(ngay_dat_hang, datetime):
                ngay_dat_hang = datetime.now()
        except:
            ngay_dat_hang = datetime.now()
        
        # Kiểm tra còn trong thời hạn bảo hành (1 năm)
        ngay_het_han = ngay_dat_hang + timedelta(days=365)
        if datetime.now() > ngay_het_han:
            return jsonify({"success": False, "message": "Sản phẩm đã hết hạn bảo hành"}), 400
        
        # Kiểm tra số lượng hợp lệ - SAFE COMPARISON
        if so_luong_bh > so_luong_mua:
            return jsonify({
                "success": False, 
                "message": f"Số lượng bảo hành ({so_luong_bh}) không được vượt quá số lượng đã mua ({so_luong_mua})"
            }), 400
        
        # Kiểm tra đã tạo phiếu bảo hành chưa
        cursor.execute("""
            SELECT COUNT(*) FROM PhieuBaoHanh 
            WHERE MaDonHang = ? AND MaSanPham = ? AND TrangThai NOT IN (N'Từ chối', N'Hoàn tất')
        """, (ma_don_hang, ma_san_pham))
        
        if cursor.fetchone()[0] > 0:
            return jsonify({"success": False, "message": "Đã có phiếu bảo hành đang xử lý cho sản phẩm này"}), 400
        
        # XỬ LÝ HÌNH ẢNH AN TOÀN HƠN
        hinh_anh_json = None
        if hinh_anh_loi and isinstance(hinh_anh_loi, list) and len(hinh_anh_loi) > 0:
            # Lọc bỏ các giá trị không hợp lệ
            hinh_anh_filtered = [img for img in hinh_anh_loi if img and isinstance(img, str) and img.strip()]
            if hinh_anh_filtered:
                hinh_anh_json = json.dumps(hinh_anh_filtered)
        
        # Tạo phiếu bảo hành
        cursor.execute("""
            INSERT INTO PhieuBaoHanh (MaDonHang, MaTaiKhoan, MaSanPham, SoLuongBH, MoTaLoi, 
                                     HinhAnhLoi, NgayBatDauBH, NgayKetThucBH, TrangThai)
            OUTPUT INSERTED.MaPhieuBH
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, N'Chờ xử lý')
        """, (ma_don_hang, ma_tai_khoan, ma_san_pham, so_luong_bh, mo_ta_loi, 
              hinh_anh_json, ngay_dat_hang, ngay_het_han))
        
        ma_phieu_bh = cursor.fetchone()[0]
        
        # THÊM LỊCH SỬ XỬ LÝ
        cursor.execute("""
            INSERT INTO LichSuBaoHanh (MaPhieuBH, TrangThaiCu, TrangThaiMoi, MoTa, NgayCapNhat)
            VALUES (?, NULL, N'Chờ xử lý', N'Phiếu bảo hành được tạo bởi khách hàng', GETDATE())
        """, (ma_phieu_bh,))
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Tạo phiếu bảo hành thành công",
            "maPhieuBH": ma_phieu_bh,
            "ngayHetHan": ngay_het_han.strftime("%Y-%m-%d"),
            "soHinhAnh": len(hinh_anh_loi) if hinh_anh_loi else 0
        })
        
    except Exception as e:
        conn.rollback()
        print(f"Error in tao_phieu_bao_hanh: {str(e)}")
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500
    finally:
        conn.close()
# API để cập nhật hình ảnh sau khi C# đã lưu file (IMPROVED)
@warranty_routes.route('/api/cap_nhat_hinh_anh_bao_hanh', methods=['POST'])
def cap_nhat_hinh_anh_bao_hanh():
    data = request.json
    ma_phieu_bh = data.get("MaPhieuBH")
    hinh_anh_loi = data.get("HinhAnhLoi", [])
    
    if not ma_phieu_bh:
        return jsonify({"success": False, "message": "Thiếu mã phiếu bảo hành"}), 400
    
    # VALIDATE MA_PHIEU_BH
    try:
        ma_phieu_bh = int(ma_phieu_bh)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Mã phiếu bảo hành không hợp lệ"}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # KIỂM TRA PHIẾU BẢO HÀNH TỒN TẠI
        cursor.execute("SELECT MaPhieuBH FROM PhieuBaoHanh WHERE MaPhieuBH = ?", (ma_phieu_bh,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Không tìm thấy phiếu bảo hành"}), 404
        
        # XỬ LÝ HÌNH ẢNH AN TOÀN
        hinh_anh_json = None
        if hinh_anh_loi and isinstance(hinh_anh_loi, list):
            # Lọc bỏ các giá trị không hợp lệ+-
            hinh_anh_filtered = [img for img in hinh_anh_loi if img and isinstance(img, str) and img.strip()]
            if hinh_anh_filtered:
                hinh_anh_json = json.dumps(hinh_anh_filtered)
        
        # Cập nhật hình ảnh vào database
        cursor.execute("""
            UPDATE PhieuBaoHanh 
            SET HinhAnhLoi = ?
            WHERE MaPhieuBH = ?
        """, (hinh_anh_json, ma_phieu_bh))
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": f"Cập nhật {len(hinh_anh_loi) if hinh_anh_loi else 0} hình ảnh thành công"
        })
        
    except Exception as e:
        conn.rollback()
        print(f"Error in cap_nhat_hinh_anh_bao_hanh: {str(e)}")
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500
    finally:
        conn.close()
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
    # 8. Kiểm tra điều kiện bảo hành
@warranty_routes.route('/api/kiem_tra_dieu_kien_bao_hanh', methods=['POST'])
def kiem_tra_dieu_kien_bao_hanh():
    data = request.json
    ma_don_hang = data.get("MaDonHang")
    ma_san_pham = data.get("MaSanPham")
    
    if not ma_don_hang or not ma_san_pham:
        return jsonify({"success": False, "message": "Thiếu thông tin đơn hàng hoặc sản phẩm"}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Kiểm tra thông tin đơn hàng
        cursor.execute("""
            SELECT DH.NgayDatHang, DH.TrangThai, CT.SoLuong, SP.TenSanPham
            FROM DonHang DH
            INNER JOIN ChiTietDonHang CT ON DH.MaDonHang = CT.MaDonHang
            INNER JOIN SanPham SP ON CT.MaSanPham = SP.MaSanPham
            WHERE DH.MaDonHang = ? AND CT.MaSanPham = ?
        """, (ma_don_hang, ma_san_pham))
        
        don_hang_info = cursor.fetchone()
        if not don_hang_info:
            return jsonify({
                "success": True,
                "coTheBaoHanh": False,
                "lyDo": "Không tìm thấy đơn hàng hoặc sản phẩm"
            })
        
        ngay_dat_hang, trang_thai, so_luong_mua, ten_san_pham = don_hang_info
        
        # Kiểm tra đã giao hàng
        if trang_thai != "Đã giao":
            return jsonify({
                "success": True,
                "coTheBaoHanh": False,
                "lyDo": "Đơn hàng chưa được giao"
            })
        
        # Kiểm tra thời hạn bảo hành
        ngay_het_han = ngay_dat_hang + timedelta(days=365)  # 1 năm
        con_bao_hanh = datetime.now() <= ngay_het_han
        so_ngay_con_lai = (ngay_het_han - datetime.now()).days if con_bao_hanh else 0
        
        if not con_bao_hanh:
            return jsonify({
                "success": True,
                "coTheBaoHanh": False,
                "lyDo": f"Sản phẩm đã hết hạn bảo hành ({ngay_het_han.strftime('%d/%m/%Y')})",
                "ngayHetHan": ngay_het_han.strftime("%Y-%m-%d")
            })
        
        # Kiểm tra đã có phiếu bảo hành chưa
        cursor.execute("""
            SELECT COUNT(*) FROM PhieuBaoHanh 
            WHERE MaDonHang = ? AND MaSanPham = ? AND TrangThai NOT IN (N'Từ chối', N'Hoàn tất')
        """, (ma_don_hang, ma_san_pham))
        
        da_co_phieu = cursor.fetchone()[0] > 0
        
        if da_co_phieu:
            return jsonify({
                "success": True,
                "coTheBaoHanh": False,
                "lyDo": "Đã có phiếu bảo hành đang xử lý cho sản phẩm này"
            })
        
        conn.close()
        
        return jsonify({
            "success": True,
            "coTheBaoHanh": True,
            "tenSanPham": ten_san_pham,
            "soLuongMua": so_luong_mua,
            "ngayMua": ngay_dat_hang.strftime("%Y-%m-%d"),
            "ngayHetHan": ngay_het_han.strftime("%Y-%m-%d"),
            "soNgayConLai": max(0, so_ngay_con_lai)
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

