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


    

        
