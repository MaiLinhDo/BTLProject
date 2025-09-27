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


    

        
