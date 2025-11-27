from flask import Blueprint, request, jsonify
from app.config import Config
import pyodbc
from app.services.order_service import create_order, get_order_detail_by_id, update_order_status
from app.services.sanpham_service import get_product_by_id
from datetime import datetime, timedelta
import json
import os

def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)
order_routes = Blueprint("order_routes", __name__)


def create_auto_warranty(ma_don_hang):
    """Tạo bảo hành tự động cho đơn hàng khi giao thành công"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Lấy thông tin đơn hàng
        cursor.execute("SELECT MaTaiKhoan FROM DonHang WHERE MaDonHang = ?", (ma_don_hang,))
        don_hang = cursor.fetchone()

        if not don_hang:
            return False

        ma_tai_khoan = don_hang[0]
        ngay_giao = datetime.now()
        ngay_het_han = ngay_giao + timedelta(days=365)  # 1 năm bảo hành

        # Lấy chi tiết sản phẩm trong đơn hàng
        cursor.execute("""
            SELECT MaSanPham, SoLuong 
            FROM ChiTietDonHang 
            WHERE MaDonHang = ?
        """, (ma_don_hang,))

        chi_tiet = cursor.fetchall()

        # Tạo bảo hành cho từng sản phẩm
        for item in chi_tiet:
            ma_san_pham, so_luong = item

            # Kiểm tra đã tạo bảo hành chưa
            cursor.execute("""
                SELECT COUNT(*) FROM BaoHanhTuDong 
                WHERE MaDonHang = ? AND MaSanPham = ?
            """, (ma_don_hang, ma_san_pham))

            if cursor.fetchone()[0] == 0:
                # Tạo bảo hành tự động
                cursor.execute("""
                    INSERT INTO BaoHanhTuDong (MaDonHang, MaSanPham, MaTaiKhoan, SoLuong, NgayBatDau, NgayKetThuc, TrangThai)
                    VALUES (?, ?, ?, ?, ?, ?, N'Hoạt động')
                """, (ma_don_hang, ma_san_pham, ma_tai_khoan, so_luong, ngay_giao, ngay_het_han))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"Lỗi tạo bảo hành tự động: {str(e)}")
        return False

@order_routes.route("/api/get_order_detail", methods=["POST"])
def get_order_detail():
    data = request.json
    order_id = data.get("orderId")

    if not order_id:
        return jsonify({"success": False, "message": "Thiếu orderId"}), 400

    result = get_order_detail_by_id(order_id)
    if not result:
        return jsonify({"success": False, "message": "Không tìm thấy đơn hàng."}), 404

    order_row = result["order_row"]
    details_rows = result["details_rows"]
    user_row = result["user_row"]
    voucher_row = result["voucher_row"]

    order = {
        "MaDonHang": order_row.MaDonHang,
        "MaTaiKhoan": order_row.MaTaiKhoan,
        "HoTen": user_row.HoTen,
        "NgayDatHang": order_row.NgayDatHang.strftime("%Y-%m-%d"),
        "TongTien": float(order_row.TongTien),
        "MaVoucher": order_row.MaVoucher,
        "DiaChiGiaoHang": order_row.DiaChiGiaoHang,
        "SoDienThoai": order_row.SoDienThoai,
        "TrangThai": order_row.TrangThai
    }

    details = [{
        "MaDonHang": row.MaDonHang,
        "MaSanPham": row.MaSanPham,
        "TenSanPham": row.TenSanPham,
        "SoLuong": row.SoLuong,
        "Gia": float(row.Gia)
    } for row in details_rows]

    return jsonify({
        "success": True,
        "order": order,
        "details": details,
        "giamGia": float(voucher_row.GiamGia)if voucher_row and voucher_row.GiamGia is not None else None,
        "code": voucher_row.Code if voucher_row else None
    })
@order_routes.route('/api/update_order_status', methods=['PUT'])
def update_order_status_route():
    data = request.json
    order_id = data.get("MaDonHang")
    status = data.get("TrangThai")

    if not order_id or not status:
        return jsonify({"success": False, "message": "Thiếu dữ liệu."}), 400

    result = update_order_status(order_id, status)
    if not result:
        return jsonify({"success": False, "message": "Không tìm thấy đơn hàng."}), 404
    # TẠO BẢO HÀNH TỰ ĐỘNG KHI ĐƠN HÀNG ĐƯỢC GIAO THÀNH CÔNG
    if status == "Đã giao":
        create_auto_warranty(order_id)
        print(f"Đã tạo bảo hành tự động cho đơn hàng {order_id}")
    return jsonify({"success": True, "message": "Cập nhật trạng thái thành công."})
@order_routes.route('/api/them_donhang', methods=['POST'])
def them_donhang():
    data = request.json
    result = create_order(data)

    order_row = result["order_row"]
    details_rows = result["details_rows"]
    user_row = result["user_row"]
    voucher_row = result["voucher_row"]

    order = {
        "MaDonHang": order_row.MaDonHang,
        "MaTaiKhoan": order_row.MaTaiKhoan,
        "HoTen": user_row.HoTen,
        "NgayDatHang": order_row.NgayDatHang.strftime("%Y-%m-%d"),
        "TongTien": float(order_row.TongTien),
        "MaVoucher": order_row.MaVoucher,
        "DiaChiGiaoHang": order_row.DiaChiGiaoHang,
        "SoDienThoai": order_row.SoDienThoai,
        "TrangThai": order_row.TrangThai
    }

    details = [{
        "MaDonHang": row.MaDonHang,
        "MaSanPham": row.MaSanPham,
        "TenSanPham": row.TenSanPham,
        "SoLuong": row.SoLuong,
        "Gia": float(row.Gia)
    } for row in details_rows]
   # Giảm số lượng trong kho khi đặt hàng
    for row in details_rows:
        product = get_product_by_id(row.MaSanPham)  # Lấy sản phẩm từ cơ sở dữ liệu
        if product:
            # Cập nhật số lượng tồn kho
            product["SoLuong"] -= row.SoLuong
            if product["SoLuong"] < 0:
                return jsonify({"success": False, "message": "Số lượng sản phẩm không đủ."})

            # Lưu lại thay đổi số lượng sản phẩm
            conn = get_connection()
            cursor = conn.cursor()
            query = "Update SanPham Set SoLuong = ? where MaSanPham = ?"
            cursor.execute(query, (product["SoLuong"], row.MaSanPham))
            conn.commit()
            conn.close()
        #    update_product_quantity(product)
    giam_gia = float(voucher_row.GiamGia) if voucher_row else None

    return jsonify({
        "success": True,
        "order": order,
        "details": details,
        "giamGia": giam_gia
    })
@order_routes.route('/api/get_orders', methods=['POST'])
def get_orders():
    data = request.json
    page = data.get("page", 1)
    pageSize = data.get("pageSize", 5)
    searchTerm = data.get("searchTerm")
    status = data.get("status")
    
    conn = get_connection()
    cursor = conn.cursor()
    params = []
    query = "SELECT DonHang.*, TaiKhoan.HoTen FROM DonHang JOIN TaiKhoan ON DonHang.MaTaiKhoan = TaiKhoan.MaTaiKhoan"
    
    if (status and searchTerm):
        query += " WHERE TaiKhoan.HoTen LIKE ? AND DonHang.TrangThai LIKE ?"
        params.append(f"%{searchTerm}%")
        params.append(f"%{status}%")
    elif(searchTerm and not status):
        query += " WHERE TaiKhoan.HoTen LIKE ?"
        params.append(f"%{searchTerm}%")
    elif ( status and not searchTerm):
        query += " WHERE DonHang.TrangThai LIKE ?"
        params.append(f"%{status}%")
    
    cursor.execute(query,params)
    all_orders = cursor.fetchall()
    total = len(all_orders)
    
    # Phân trang
    query += " ORDER BY NgayDatHang DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
    params.extend([(page - 1) * pageSize, pageSize])
    cursor.execute(query, params)
    paged_orders = cursor.fetchall()
    
    result = []
    for row in paged_orders:
        result.append({
            "MaDonHang": row.MaDonHang,
            "HoTen": row.HoTen or "N/A",
            "NgayDatHang": row.NgayDatHang.strftime("%Y-%m-%d") if row.NgayDatHang else "N/A",  # Format datetime
            "TongTien": float(row.TongTien) if row.TongTien else 0.0,  # Convert to float
            "DiaChiGiaoHang": row.DiaChiGiaoHang or "",
            "SoDienThoai": row.SoDienThoai or "",
            "TrangThai": row.TrangThai or "N/A",  # Ensure string
            "MaVoucher": row.MaVoucher
        })
    
    conn.close()
    return jsonify({"orders": result, "total": total})
@order_routes.route('/api/cancel_order', methods=['POST'])
def cancel_order():
    data = request.json
    order_id = data["order_id"]

    conn = get_connection()
    cursor = conn.cursor()

    # Kiểm tra đơn hàng
    cursor.execute("SELECT * FROM DonHang WHERE MaDonHang = ?", (order_id,))
    order_row = cursor.fetchone()
    if not order_row:
        conn.close()
        return jsonify({"success": False})

    # Lấy chi tiết
    cursor.execute("SELECT MaSanPham, SoLuong FROM ChiTietDonHang WHERE MaDonHang = ?", (order_id,))
    details = cursor.fetchall()

    # Cập nhật số lượng sản phẩm
    for item in details:
        cursor.execute("UPDATE SanPham SET SoLuong = SoLuong + ? WHERE MaSanPham = ?", (item.SoLuong, item.MaSanPham))

    # Cập nhật trạng thái
    cursor.execute("UPDATE DonHang SET TrangThai = ? WHERE MaDonHang = ?", ("Đã Hủy", order_id))

    conn.commit()
    conn.close()
    return jsonify({"success": True})

# 1. Cập nhật trạng thái đơn hàng theo luồng mới
@order_routes.route('/api/update_order_status_new', methods=['PUT'])
def update_order_status_new():
    data = request.json
    order_id = data.get("MaDonHang")
    new_status = data.get("TrangThai")
    
    if not order_id or not new_status:
        return jsonify({"success": False, "message": "Thiếu thông tin"}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Cập nhật trạng thái
    cursor.execute("UPDATE DonHang SET TrangThai = ? WHERE MaDonHang = ?", 
                   (new_status, order_id))
    conn.commit()
    conn.close()
    if new_status == "Đã giao":
        create_auto_warranty(order_id)
        print(f"Đã tạo bảo hành tự động cho đơn hàng {order_id}")
    return jsonify({"success": True, "message": "Cập nhật thành công"})


@order_routes.route("/api/thong_ke", methods=["POST"])
def thong_ke():
    data = request.get_json()
    start_date = data.get("startDate")
    end_date = data.get("endDate")

    if not start_date or not end_date:
        return jsonify({"success": False, "message": "Thiếu ngày bắt đầu hoặc kết thúc."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Tổng đơn hàng
    cursor.execute("""
        SELECT COUNT(*) FROM DonHang 
        WHERE NgayDatHang BETWEEN ? AND ?
    """, (start_date, end_date))
    total_orders = cursor.fetchone()[0]

    # Đếm theo trạng thái
    def count_by_status(status):
        cursor.execute("""
            SELECT COUNT(*) FROM DonHang 
            WHERE TrangThai = ? AND NgayDatHang BETWEEN ? AND ?
        """, (status, start_date, end_date))
        return cursor.fetchone()[0]

    pending = count_by_status("Đang chờ xử lý")
    approved = count_by_status("Đã duyệt")
    delivered = count_by_status("Đã giao")
    cancelled = count_by_status("Đã hủy")

    # Doanh thu theo trạng thái
    def sum_revenue(status):
        cursor.execute("""
            SELECT SUM(TongTien) FROM DonHang 
            WHERE TrangThai = ? AND NgayDatHang BETWEEN ? AND ?
        """, (status, start_date, end_date))
        result = cursor.fetchone()[0]
        return result or 0

    revenue_pending = sum_revenue("Đang chờ xử lý")
    revenue_approved = sum_revenue("Đã duyệt")
    revenue_delivered = sum_revenue("Đã giao")
    revenue_cancelled = sum_revenue("Đã hủy")

    total_revenue = revenue_pending + revenue_approved + revenue_delivered + revenue_cancelled

    # Sản phẩm bán chạy
    cursor.execute("""
        SELECT TOP 5 c.MaSanPham, p.TenSanPham, SUM(c.SoLuong) as SoLuong
        FROM ChiTietDonHang c
        JOIN DonHang d ON c.MaDonHang = d.MaDonHang
        JOIN SanPham p ON c.MaSanPham = p.MaSanPham
        WHERE d.NgayDatHang BETWEEN ? AND ?
        GROUP BY c.MaSanPham, p.TenSanPham
        ORDER BY SoLuong DESC
    """, (start_date, end_date))

    best_selling = [{"TenSanPham": row[1], "SoLuong": row[2]} for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "success": True,
        "totalOrders": total_orders,
        "pendingOrders": pending,
        "approvedOrders": approved,
        "deliveredOrders": delivered,
        "cancelledOrders": cancelled,
        "revenuePending": f"{revenue_pending:,.0f} đ",
        "revenueApproved": f"{revenue_approved:,.0f} đ",
        "revenueDelivered": f"{revenue_delivered:,.0f} đ",
        "revenueCancelled": f"{revenue_cancelled:,.0f} đ",
        "totalRevenue": total_revenue,
        "bestSellingProducts": best_selling
    })


# 2. Xác nhận đã nhận hàng
@order_routes.route('/api/confirm_received', methods=['POST'])
def confirm_received():
    data = request.json
    order_id = data.get("MaDonHang")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE DonHang 
        SET TrangThai = 'Đã giao' 
        WHERE MaDonHang = ?
    """, (order_id,))

    conn.commit()
    conn.close()
    create_auto_warranty(order_id)
    print(f"Đã tạo bảo hành tự động cho đơn hàng {order_id}")
    return jsonify({"success": True, "message": "Xác nhận thành công"})


# API lấy bảo hành tự động của khách hàng
@order_routes.route('/api/get_bao_hanh_tu_dong', methods=['POST'])
def get_bao_hanh_tu_dong():
    data = request.json
    ma_tai_khoan = data.get('maTaiKhoan')
    page = data.get('page', 1)
    page_size = data.get('pageSize', 10)

    if not ma_tai_khoan:
        return jsonify({"success": False, "message": "Thiếu mã tài khoản"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Đếm tổng số
    cursor.execute("""
        SELECT COUNT(*) FROM BaoHanhTuDong 
        WHERE MaTaiKhoan = ?
    """, (ma_tai_khoan,))
    total_count = cursor.fetchone()[0]

    # Lấy dữ liệu phân trang
    offset = (page - 1) * page_size
    cursor.execute("""
        SELECT BH.MaBaoHanh, BH.MaDonHang, BH.MaSanPham, SP.TenSanPham, SP.HinhAnh,
               BH.SoLuong, BH.NgayBatDau, BH.NgayKetThuc, BH.TrangThai,
               DATEDIFF(DAY, GETDATE(), BH.NgayKetThuc) AS SoNgayConLai,
               CASE WHEN BH.NgayKetThuc > GETDATE() THEN 1 ELSE 0 END AS ConBaoHanh
        FROM BaoHanhTuDong BH
        INNER JOIN SanPham SP ON BH.MaSanPham = SP.MaSanPham
        WHERE BH.MaTaiKhoan = ?
        ORDER BY BH.NgayBatDau DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """, (ma_tai_khoan, offset, page_size))

    bao_hanh_list = []
    for row in cursor.fetchall():
        bao_hanh_list.append({
            "MaBaoHanh": row[0],
            "MaDonHang": row[1],
            "MaSanPham": row[2],
            "TenSanPham": row[3],
            "HinhAnh": row[4],
            "SoLuong": row[5],
            "NgayBatDau": row[6].strftime("%Y-%m-%d") if row[6] else None,
            "NgayKetThuc": row[7].strftime("%Y-%m-%d") if row[7] else None,
            "TrangThai": row[8],
            "SoNgayConLai": max(0, row[9]) if row[9] else 0,
            "ConBaoHanh": bool(row[10])
        })

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    conn.close()

    return jsonify({
        "success": True,
        "baoHanhList": bao_hanh_list,
        "totalPages": total_pages,
        "totalCount": total_count,
        "currentPage": page
    })


# 3. Tạo yêu cầu đổi trả đơn giản
@order_routes.route('/api/create_return', methods=['POST'])
def create_return():
    data = request.json

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO DonDoiTra (MaDonHang, LoaiYeuCau, LyDo, MoTa, NgayTao, TrangThai)
        VALUES (?, ?, ?, ?, GETDATE(), N'Chờ xử lý')
    """, (data["MaDonHang"], data["LoaiYeuCau"], data["LyDo"], data["MoTa"]))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Tạo yêu cầu đổi trả thành công"})


# 4. Tạo đánh giá sản phẩm
@order_routes.route('/api/create_review', methods=['POST'])
def create_review():
    data = request.json

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO DanhGiaSanPham (MaTaiKhoan, MaSanPham, DiemDanhGia, BinhLuan, NgayDanhGia)
        VALUES (?, ?, ?, ?, GETDATE())
    """, (data["MaTaiKhoan"], data["MaSanPham"], data["DiemDanhGia"], data["BinhLuan"]))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Đánh giá thành công"})


# 5. Lấy đánh giá sản phẩm
@order_routes.route('/api/get_reviews/<int:product_id>', methods=['GET'])
def get_reviews(product_id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)

    conn = get_connection()
    cursor = conn.cursor()

    # Lấy tất cả đánh giá để tính thống kê
    cursor.execute("""
        SELECT DG.DiemDanhGia, DG.BinhLuan, DG.NgayDanhGia, TK.HoTen
        FROM DanhGiaSanPham DG
        JOIN TaiKhoan TK ON DG.MaTaiKhoan = TK.MaTaiKhoan
        WHERE DG.MaSanPham = ?
        ORDER BY DG.NgayDanhGia DESC
    """, (product_id,))

    all_reviews = cursor.fetchall()
    total_reviews = len(all_reviews)

    # Tính rating trung bình
    if total_reviews > 0:
        average_rating = sum(row[0] for row in all_reviews) / total_reviews
        average_rating = round(average_rating, 1)
    else:
        average_rating = 0

    # Tính phân bố rating
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for row in all_reviews:
        rating = row[0]
        if rating in rating_counts:
            rating_counts[rating] += 1

    rating_distribution = []
    for stars in range(1, 6):
        rating_distribution.append({
            "Stars": stars,
            "Count": rating_counts[stars]
        })

    # Phân trang cho reviews
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_reviews = all_reviews[start_idx:end_idx]

    reviews = []
    for row in paged_reviews:
        reviews.append({
            "DiemDanhGia": row[0],
            "BinhLuan": row[1],
            "NgayDanhGia": row[2].strftime("%Y-%m-%d") if row[2] else "",
            "HoTen": row[3]
        })

    conn.close()

    return jsonify({
        "success": True,
        "reviews": reviews,
        "totalReviews": total_reviews,
        "averageRating": average_rating,
        "ratingDistribution": rating_distribution,
        "currentPage": page,
        "totalPages": (total_reviews + page_size - 1) // page_size if total_reviews > 0 else 1
    })
# 6. Lấy đơn hàng với thông tin có thể đổi trả/đánh giá
@order_routes.route('/api/get_user_orders_paginated', methods=['POST'])
def get_user_orders_paginated():
    data = request.json
    ma_tai_khoan = data.get('maTaiKhoan')
    page = data.get('page', 1)
    page_size = data.get('pageSize', 6)

    if not ma_tai_khoan:
        return jsonify({"success": False, "message": "Thiếu mã tài khoản"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Đếm tổng số đơn hàng
    cursor.execute("""
        SELECT COUNT(*) FROM DonHang 
        WHERE MaTaiKhoan = ?
    """, (ma_tai_khoan,))
    total_orders = cursor.fetchone()[0]

    # Tính tổng số trang
    total_pages = (total_orders + page_size - 1) // page_size if total_orders > 0 else 1

    # Lấy đơn hàng với phân trang
    cursor.execute("""
        SELECT MaDonHang, NgayDatHang, TongTien, TrangThai, 
               DATEDIFF(day, NgayDatHang, GETDATE()) as SoNgay
        FROM DonHang 
        WHERE MaTaiKhoan = ?
        ORDER BY NgayDatHang DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """, (ma_tai_khoan, (page - 1) * page_size, page_size))

    orders = []
    for row in cursor.fetchall():
        ma_don_hang, ngay_dat, tong_tien, trang_thai, so_ngay = row

        # Xác định hành động có thể thực hiện
        can_cancel = trang_thai in ["Đặt hàng thành công", "Đang chuẩn bị hàng"]
        can_return = trang_thai == "Đã giao" and so_ngay <= 7
        can_review = trang_thai == "Đã giao"
        can_confirm = trang_thai == "Đơn hàng sẽ sớm được giao đến bạn"

        # Lấy chi tiết sản phẩm trong đơn hàng
        cursor.execute("""
            SELECT CT.MaSanPham, SP.TenSanPham, CT.SoLuong, CT.Gia, SP.HinhAnh
            FROM ChiTietDonHang CT
            JOIN SanPham SP ON CT.MaSanPham = SP.MaSanPham
            WHERE CT.MaDonHang = ?
        """, (ma_don_hang,))

        products = []
        for product_row in cursor.fetchall():
            products.append({
                "MaSanPham": product_row[0],
                "TenSanPham": product_row[1],
                "SoLuong": product_row[2],
                "Gia": float(product_row[3]),
                "HinhAnh": product_row[4]
            })

        orders.append({
            "MaDonHang": ma_don_hang,
            "NgayDatHang": ngay_dat.strftime("%Y-%m-%d") if ngay_dat else "",
            "TongTien": float(tong_tien) if tong_tien else 0,
            "TrangThai": trang_thai,
            "CanCancel": can_cancel,
            "CanReturn": can_return,
            "CanReview": can_review,
            "CanConfirm": can_confirm,
            "Products": products
        })

    conn.close()

    return jsonify({
        "success": True,
        "orders": orders,
        "currentPage": page,
        "totalPages": total_pages,
        "total": total_orders,
        "hasNext": page < total_pages,
        "hasPrev": page > 1
    })


@order_routes.route('/api/get_all_reviews', methods=['GET'])
def get_all_reviews():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    product_id = request.args.get('productId', type=int)
    rating = request.args.get('rating', type=int)

    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT DG.MaDanhGia, DG.DiemDanhGia, DG.BinhLuan, DG.NgayDanhGia,
               TK.HoTen, SP.TenSanPham, SP.MaSanPham, SP.HinhAnh
        FROM DanhGiaSanPham DG
        JOIN TaiKhoan TK ON DG.MaTaiKhoan = TK.MaTaiKhoan
        JOIN SanPham SP ON DG.MaSanPham = SP.MaSanPham
        WHERE 1=1
    """
    params = []

    if product_id:
        base_query += " AND DG.MaSanPham = ?"
        params.append(product_id)

    if rating:
        base_query += " AND DG.DiemDanhGia = ?"
        params.append(rating)

    # Đếm tổng số
    count_query = f"SELECT COUNT(*) FROM ({base_query}) as CountQuery"
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # Phân trang
    base_query += " ORDER BY DG.NgayDanhGia DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
    params.extend([(page - 1) * page_size, page_size])

    cursor.execute(base_query, params)

    reviews = []
    for row in cursor.fetchall():
        reviews.append({
            "MaDanhGia": row[0],
            "DiemDanhGia": row[1],
            "BinhLuan": row[2],
            "NgayDanhGia": row[3].strftime("%Y-%m-%d"),
            "HoTen": row[4],
            "TenSanPham": row[5],
            "MaSanPham": row[6],
            "HinhAnh": row[7]
        })

    conn.close()

    return jsonify({
        "success": True,
        "reviews": reviews,
        "totalPages": (total + page_size - 1) // page_size,
        "currentPage": page,
        "total": total
    })


# Lấy chi tiết đánh giá
@order_routes.route('/api/get_review_detail/<int:review_id>', methods=['GET'])
def get_review_detail(review_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DG.MaDanhGia, DG.DiemDanhGia, DG.BinhLuan, DG.NgayDanhGia,
               TK.HoTen, SP.TenSanPham, SP.MaSanPham, SP.HinhAnh
        FROM DanhGiaSanPham DG
        JOIN TaiKhoan TK ON DG.MaTaiKhoan = TK.MaTaiKhoan
        JOIN SanPham SP ON DG.MaSanPham = SP.MaSanPham
        WHERE DG.MaDanhGia = ?
    """, (review_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        review = {
            "MaDanhGia": row[0],
            "DiemDanhGia": row[1],
            "BinhLuan": row[2],
            "NgayDanhGia": row[3].strftime("%Y-%m-%d"),
            "HoTen": row[4],
            "TenSanPham": row[5],
            "MaSanPham": row[6],
            "HinhAnh": row[7]
        }
        return jsonify({"success": True, "review": review})

    return jsonify({"success": False, "message": "Không tìm thấy đánh giá"})


# Xóa đánh giá
@order_routes.route('/api/delete_review/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM DanhGiaSanPham WHERE MaDanhGia = ?", (review_id,))

        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return jsonify({"success": True, "message": "Xóa đánh giá thành công"})
        else:
            conn.close()
            return jsonify({"success": False, "message": "Không tìm thấy đánh giá"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# Thống kê đánh giá
@order_routes.route('/api/review_statistics', methods=['GET'])
def review_statistics():
    conn = get_connection()
    cursor = conn.cursor()

    # Tổng số đánh giá
    cursor.execute("SELECT COUNT(*) FROM DanhGiaSanPham")
    total_reviews = cursor.fetchone()[0]

    # Rating trung bình
    cursor.execute("SELECT AVG(CAST(DiemDanhGia as FLOAT)) FROM DanhGiaSanPham")
    avg_rating = cursor.fetchone()[0] or 0

    # Phần trăm 5 sao
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN DiemDanhGia = 5 THEN 1 END) * 100.0 / COUNT(*) as FiveStarPercent
        FROM DanhGiaSanPham
    """)
    five_star_percent = cursor.fetchone()[0] or 0

    # Đánh giá tháng này
    cursor.execute("""
        SELECT COUNT(*) FROM DanhGiaSanPham 
         WHERE MONTH(NgayDanhGia) = MONTH(GETDATE()) 
         AND YEAR(NgayDanhGia) = YEAR(GETDATE())
     """)
    this_month_reviews = cursor.fetchone()[0]

    # Phân bố rating
    rating_distribution = []
    for i in range(1, 6):
        cursor.execute("""
            SELECT COUNT(*) FROM DanhGiaSanPham WHERE DiemDanhGia = ?
        """, (i,))
        count = cursor.fetchone()[0]
        percentage = (count * 100.0 / total_reviews) if total_reviews > 0 else 0
        rating_distribution.append({
            "Stars": i,
            "Count": count,
            "Percentage": round(percentage, 1)
        })
    # Top sản phẩm được đánh giá cao
    cursor.execute("""
            SELECT TOP 5 SP.MaSanPham, SP.TenSanPham, SP.HinhAnh,
               AVG(CAST(DG.DiemDanhGia as FLOAT)) as AvgRating,
               COUNT(DG.MaDanhGia) as TotalReviews
        FROM SanPham SP
        JOIN DanhGiaSanPham DG ON SP.MaSanPham = DG.MaSanPham
            GROUP BY SP.MaSanPham, SP.TenSanPham, SP.HinhAnh
            HAVING COUNT(DG.MaDanhGia) >= 3
            ORDER BY AVG(CAST(DG.DiemDanhGia as FLOAT)) DESC
    """)

    top_rated = []
    for row in cursor.fetchall():
        top_rated.append({
            "MaSanPham": row[0],
            "TenSanPham": row[1],
            "HinhAnh": row[2],
            "AverageRating": round(row[3], 1),
            "TotalReviews": row[4]
        })

    # Đánh giá gần đây
    cursor.execute("""
            SELECT TOP 5 DG.DiemDanhGia, DG.BinhLuan, DG.NgayDanhGia,
                   TK.HoTen, SP.TenSanPham, SP.MaSanPham, SP.HinhAnh
            FROM DanhGiaSanPham DG
            JOIN TaiKhoan TK ON DG.MaTaiKhoan = TK.MaTaiKhoan
            JOIN SanPham SP ON DG.MaSanPham = SP.MaSanPham
            ORDER BY DG.NgayDanhGia DESC
    """)

    recent_reviews = []
    for row in cursor.fetchall():
        recent_reviews.append({
            "DiemDanhGia": row[0],
            "BinhLuan": row[1],
            "NgayDanhGia": row[2].strftime("%Y-%m-%d"),
            "HoTen": row[3],
            "TenSanPham": row[4],
            "MaSanPham": row[5],
            "HinhAnh": row[6]
        })

    conn.close()

    return jsonify({
        "success": True,
        "totalReviews": total_reviews,
        "averageRating": round(avg_rating, 1),
        "fiveStarPercentage": round(five_star_percent, 1),
        "thisMonthReviews": this_month_reviews,
        "ratingDistribution": rating_distribution,
        "topRatedProducts": top_rated,
        "recentReviews": recent_reviews
    })


@order_routes.route('/api/get_return_requests', methods=['GET'])
def get_return_requests():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    status = request.args.get('status', '')

    conn = get_connection()
    cursor = conn.cursor()

    # Base query - sử dụng đúng tên cột từ schema
    base_query = """
        SELECT DT.MaDoiTra, DT.MaDonHang, DT.LoaiYeuCau, DT.LyDo, 
               DT.MoTa, DT.NgayTao, DT.TrangThai,
               TK.HoTen, DH.TongTien
        FROM DonDoiTra DT
        JOIN DonHang DH ON DT.MaDonHang = DH.MaDonHang
        JOIN TaiKhoan TK ON DH.MaTaiKhoan = TK.MaTaiKhoan
        WHERE 1=1
    """
    params = []

    # Filter by status if provided
    if status:
        base_query += " AND DT.TrangThai = ?"
        params.append(status)

    # Count total records
    count_query = f"SELECT COUNT(*) FROM ({base_query}) as CountQuery"
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # Add pagination
    base_query += " ORDER BY DT.NgayTao DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
    params.extend([(page - 1) * page_size, page_size])

    cursor.execute(base_query, params)

    returns = []
    for row in cursor.fetchall():
        returns.append({
            "MaDoiTra": row[0],
            "MaDonHang": row[1],
            "LoaiYeuCau": row[2],
            "LyDo": row[3],
            "MoTa": row[4],
            "NgayTao": row[5].strftime("%Y-%m-%d") if row[5] else "",
            "TrangThai": row[6],
            "HoTen": row[7],
            "TongTien": float(row[8]) if row[8] else 0
        })

    conn.close()

    return jsonify({
        "success": True,
        "returns": returns,
        "total": total,
        "currentPage": page,
        "totalPages": (total + page_size - 1) // page_size if total > 0 else 1
    })


@order_routes.route('/api/get_return_detail/<int:return_id>', methods=['GET'])
def get_return_detail(return_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DT.MaDoiTra, DT.MaDonHang, DT.LoaiYeuCau, DT.LyDo, 
               DT.MoTa, DT.NgayTao, DT.TrangThai, DT.HinhAnhLoi,
               TK.HoTen, TK.SoDienThoai, TK.Email,
               DH.TongTien, DH.DiaChiGiaoHang, DH.NgayDatHang
        FROM DonDoiTra DT
        JOIN DonHang DH ON DT.MaDonHang = DH.MaDonHang
        JOIN TaiKhoan TK ON DH.MaTaiKhoan = TK.MaTaiKhoan
        WHERE DT.MaDoiTra = ?
    """, (return_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "message": "Không tìm thấy yêu cầu đổi trả"})

    # Lấy chi tiết sản phẩm trong đơn hàng
    cursor.execute("""
        SELECT CT.MaSanPham, SP.TenSanPham, CT.SoLuong, CT.Gia, SP.HinhAnh
        FROM ChiTietDonHang CT
        JOIN SanPham SP ON CT.MaSanPham = SP.MaSanPham
        WHERE CT.MaDonHang = ?
    """, (row[1],))

    products = []
    for product_row in cursor.fetchall():
        products.append({
            "MaSanPham": product_row[0],
            "TenSanPham": product_row[1],
            "SoLuong": product_row[2],
            "Gia": float(product_row[3]),
            "HinhAnh": product_row[4]
        })

    # Parse hình ảnh lỗi
    hinh_anh_loi = []
    if row[7]:  # HinhAnhLoi
        try:
            hinh_anh_loi = json.loads(row[7])
        except:
            hinh_anh_loi = []

    return_detail = {
        "MaDoiTra": row[0],
        "MaDonHang": row[1],
        "LoaiYeuCau": row[2],
        "LyDo": row[3],
        "MoTa": row[4],
        "NgayTao": row[5].strftime("%Y-%m-%d %H:%M:%S") if row[5] else "",
        "TrangThai": row[6],
        "HinhAnhLoi": hinh_anh_loi,  # THÊM TRƯỜNG NÀY
        "HoTen": row[8],
        "SoDienThoai": row[9],
        "Email": row[10],
        "TongTien": float(row[11]) if row[11] else 0,
        "DiaChiGiaoHang": row[12],
        "NgayDatHang": row[13].strftime("%Y-%m-%d") if row[13] else "",
        "Products": products
    }

    conn.close()

    return jsonify({
        "success": True,
        "returnDetail": return_detail
    })


@order_routes.route('/api/update_return_status', methods=['PUT'])
def update_return_status():
    data = request.json
    return_id = data.get("maDoiTra")
    new_status = data.get("trangThai")

    if not return_id or not new_status:
        return jsonify({"success": False, "message": "Thiếu thông tin cần thiết"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Cập nhật trạng thái (không có GhiChu trong schema)
    cursor.execute("""
        UPDATE DonDoiTra 
        SET TrangThai = ?
        WHERE MaDoiTra = ?
    """, (new_status, return_id))

    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Cập nhật trạng thái thành công"})
    else:
        conn.close()
        return jsonify({"success": False, "message": "Không tìm thấy yêu cầu đổi trả"})


# API lấy danh sách đổi trả của khách hàng
@order_routes.route('/api/get_user_returns', methods=['POST'])
def get_user_returns():
    data = request.json
    ma_tai_khoan = data.get('maTaiKhoan')
    page = data.get('page', 1)
    page_size = data.get('pageSize', 10)

    if not ma_tai_khoan:
        return jsonify({"success": False, "message": "Thiếu mã tài khoản"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Đếm tổng số
        cursor.execute("""
            SELECT COUNT(*) FROM DonDoiTra DT
            INNER JOIN DonHang DH ON DT.MaDonHang = DH.MaDonHang
            WHERE DH.MaTaiKhoan = ?
        """, (ma_tai_khoan,))
        total_count = cursor.fetchone()[0]

        # Lấy dữ liệu phân trang
        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT DT.MaDoiTra, DT.MaDonHang, DT.LoaiYeuCau, DT.LyDo, 
                   DT.MoTa, DT.NgayTao, DT.TrangThai, DT.HinhAnhLoi,
                   DH.TongTien, DH.NgayDatHang,
                   DATEDIFF(day, DH.NgayDatHang, GETDATE()) as SoNgayTuGiao
            FROM DonDoiTra DT
            INNER JOIN DonHang DH ON DT.MaDonHang = DH.MaDonHang
            WHERE DH.MaTaiKhoan = ?
            ORDER BY DT.NgayTao DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (ma_tai_khoan, offset, page_size))

        returns_list = []
        for row in cursor.fetchall():
            # Parse hình ảnh
            hinh_anh_loi = []
            if row[7]:  # HinhAnhLoi
                try:
                    hinh_anh_loi = json.loads(row[7])
                except:
                    hinh_anh_loi = []

            returns_list.append({
                "MaDoiTra": row[0],
                "MaDonHang": row[1],
                "LoaiYeuCau": row[2],
                "LyDo": row[3],
                "MoTa": row[4],
                "NgayTao": row[5].strftime("%Y-%m-%d %H:%M:%S") if row[5] else None,
                "TrangThai": row[6],
                "HinhAnhLoi": hinh_anh_loi,
                "TongTien": float(row[8]) if row[8] else 0,
                "NgayDatHang": row[9].strftime("%Y-%m-%d") if row[9] else None,
                "SoNgayTuGiao": row[10] if row[10] else 0
            })

        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

        conn.close()

        return jsonify({
            "success": True,
            "returns": returns_list,
            "totalPages": total_pages,
            "totalCount": total_count,
            "currentPage": page
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# API tạo đổi trả với hình ảnh
@order_routes.route('/api/create_return_with_images', methods=['POST'])
def create_return_with_images():
    data = request.json
    ma_don_hang = data.get("MaDonHang")
    loai_yeu_cau = data.get("LoaiYeuCau")
    ly_do = data.get("LyDo")
    mo_ta = data.get("MoTa")
    hinh_anh_loi = data.get("HinhAnhLoi", [])  # Danh sách tên file từ C#

    if not all([ma_don_hang, loai_yeu_cau, ly_do, mo_ta]):
        return jsonify({"success": False, "message": "Thiếu thông tin bắt buộc"}), 400

    # Validate dữ liệu
    try:
        ma_don_hang = int(ma_don_hang)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Mã đơn hàng không hợp lệ"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Kiểm tra đơn hàng
        cursor.execute("""
            SELECT MaTaiKhoan, TrangThai, NgayDatHang 
            FROM DonHang 
            WHERE MaDonHang = ?
        """, (ma_don_hang,))

        don_hang_info = cursor.fetchone()
        if not don_hang_info:
            return jsonify({"success": False, "message": "Không tìm thấy đơn hàng"}), 404

        ma_tai_khoan, trang_thai, ngay_dat_hang = don_hang_info

        # Kiểm tra đơn hàng đã giao
        if trang_thai != "Đã giao":
            return jsonify({"success": False, "message": "Đơn hàng chưa được giao, không thể tạo yêu cầu đổi trả"}), 400

        # Kiểm tra thời hạn 7 ngày
        from datetime import datetime, timedelta
        if isinstance(ngay_dat_hang, str):
            ngay_dat_hang = datetime.strptime(ngay_dat_hang, "%Y-%m-%d")

        ngay_het_han = ngay_dat_hang + timedelta(days=7)
        if datetime.now() > ngay_het_han:
            return jsonify({"success": False, "message": "Đã quá thời hạn 7 ngày để tạo yêu cầu đổi trả"}), 400

        # Kiểm tra đã tạo yêu cầu chưa
        cursor.execute("""
            SELECT COUNT(*) FROM DonDoiTra 
            WHERE MaDonHang = ? AND TrangThai NOT IN (N'Từ chối', N'Đã xử lý')
        """, (ma_don_hang,))

        if cursor.fetchone()[0] > 0:
            return jsonify({"success": False, "message": "Đã có yêu cầu đổi trả đang xử lý cho đơn hàng này"}), 400

        # Xử lý hình ảnh
        hinh_anh_json = None
        if hinh_anh_loi and isinstance(hinh_anh_loi, list) and len(hinh_anh_loi) > 0:
            # Lọc bỏ các giá trị không hợp lệ
            hinh_anh_filtered = [img for img in hinh_anh_loi if img and isinstance(img, str) and img.strip()]
            if hinh_anh_filtered:
                hinh_anh_json = json.dumps(hinh_anh_filtered)

        # Tạo yêu cầu đổi trả
        cursor.execute("""
            INSERT INTO DonDoiTra (MaDonHang, LoaiYeuCau, LyDo, MoTa, HinhAnhLoi, NgayTao, TrangThai)
            OUTPUT INSERTED.MaDoiTra
            VALUES (?, ?, ?, ?, ?, GETDATE(), N'Chờ xử lý')
        """, (ma_don_hang, loai_yeu_cau, ly_do, mo_ta, hinh_anh_json))

        ma_doi_tra = cursor.fetchone()[0]

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Tạo yêu cầu đổi trả thành công",
            "maDoiTra": ma_doi_tra,
            "soHinhAnh": len(hinh_anh_loi) if hinh_anh_loi else 0
        })

    except Exception as e:
        conn.rollback()
        print(f"Error in create_return_with_images: {str(e)}")
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500
    finally:
        conn.close()


# API cập nhật hình ảnh đổi trả
@order_routes.route('/api/cap_nhat_hinh_anh_doi_tra', methods=['POST'])
def cap_nhat_hinh_anh_doi_tra():
    data = request.json
    ma_doi_tra = data.get("MaDoiTra")
    hinh_anh_loi = data.get("HinhAnhLoi", [])

    if not ma_doi_tra:
        return jsonify({"success": False, "message": "Thiếu mã đổi trả"}), 400

    try:
        ma_doi_tra = int(ma_doi_tra)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Mã đổi trả không hợp lệ"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Kiểm tra đổi trả tồn tại
        cursor.execute("SELECT MaDoiTra FROM DonDoiTra WHERE MaDoiTra = ?", (ma_doi_tra,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Không tìm thấy yêu cầu đổi trả"}), 404

        # Xử lý hình ảnh
        hinh_anh_json = None
        if hinh_anh_loi and isinstance(hinh_anh_loi, list):
            hinh_anh_filtered = [img for img in hinh_anh_loi if img and isinstance(img, str) and img.strip()]
            if hinh_anh_filtered:
                hinh_anh_json = json.dumps(hinh_anh_filtered)

        # Cập nhật hình ảnh
        cursor.execute("""
            UPDATE DonDoiTra 
            SET HinhAnhLoi = ?
            WHERE MaDoiTra = ?
        """, (hinh_anh_json, ma_doi_tra))

        conn.commit()

        return jsonify({
            "success": True,
            "message": f"Cập nhật {len(hinh_anh_loi) if hinh_anh_loi else 0} hình ảnh thành công"
        })

    except Exception as e:
        conn.rollback()
        print(f"Error in cap_nhat_hinh_anh_doi_tra: {str(e)}")
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500
    finally:
        conn.close()


# API lấy chi tiết đổi trả của user
@order_routes.route('/api/get_user_return_detail', methods=['POST'])
def get_user_return_detail():
    data = request.json
    ma_doi_tra = data.get("MaDoiTra")
    ma_tai_khoan = data.get("MaTaiKhoan")  # Để đảm bảo user chỉ xem được đổi trả của mình

    if not ma_doi_tra:
        return jsonify({"success": False, "message": "Thiếu mã đổi trả"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Lấy chi tiết đổi trả với kiểm tra quyền
        query = """
            SELECT DT.MaDoiTra, DT.MaDonHang, DT.LoaiYeuCau, DT.LyDo, 
                   DT.MoTa, DT.NgayTao, DT.TrangThai, DT.HinhAnhLoi,
                   DH.TongTien, DH.NgayDatHang, DH.DiaChiGiaoHang,
                   TK.HoTen, TK.SoDienThoai, TK.Email
            FROM DonDoiTra DT
            INNER JOIN DonHang DH ON DT.MaDonHang = DH.MaDonHang
            INNER JOIN TaiKhoan TK ON DH.MaTaiKhoan = TK.MaTaiKhoan
            WHERE DT.MaDoiTra = ?
        """
        params = [ma_doi_tra]

        if ma_tai_khoan:
            query += " AND DH.MaTaiKhoan = ?"
            params.append(ma_tai_khoan)

        cursor.execute(query, params)
        row = cursor.fetchone()

        if not row:
            return jsonify({"success": False, "message": "Không tìm thấy yêu cầu đổi trả"}), 404

        # Lấy chi tiết sản phẩm
        cursor.execute("""
            SELECT CT.MaSanPham, SP.TenSanPham, CT.SoLuong, CT.Gia, SP.HinhAnh
            FROM ChiTietDonHang CT
            INNER JOIN SanPham SP ON CT.MaSanPham = SP.MaSanPham
            WHERE CT.MaDonHang = ?
        """, (row[1],))  # MaDonHang

        products = []
        for product_row in cursor.fetchall():
            products.append({
                "MaSanPham": product_row[0],
                "TenSanPham": product_row[1],
                "SoLuong": product_row[2],
                "Gia": float(product_row[3]),
                "HinhAnh": product_row[4]
            })

        # Parse hình ảnh lỗi
        hinh_anh_loi = []
        if row[7]:  # HinhAnhLoi
            try:
                hinh_anh_loi = json.loads(row[7])
            except:
                hinh_anh_loi = []

        chi_tiet = {
            "MaDoiTra": row[0],
            "MaDonHang": row[1],
            "LoaiYeuCau": row[2],
            "LyDo": row[3],
            "MoTa": row[4],
            "NgayTao": row[5].strftime("%Y-%m-%d %H:%M:%S") if row[5] else None,
            "TrangThai": row[6],
            "HinhAnhLoi": hinh_anh_loi,
            "TongTien": float(row[8]) if row[8] else 0,
            "NgayDatHang": row[9].strftime("%Y-%m-%d") if row[9] else None,
            "DiaChiGiaoHang": row[10],
            "TenKhachHang": row[11],
            "SoDienThoai": row[12],
            "Email": row[13],
            "Products": products
        }

        conn.close()

        return jsonify({"success": True, "chiTiet": chi_tiet})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

        
