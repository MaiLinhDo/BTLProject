import pyodbc
from flask import request, jsonify

from app.config import Config
from datetime import datetime, timedelta


def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)

def get_revenue_by_product_and_category():
    conn = get_connection()
    cursor = conn.cursor()
    current_date = datetime.now().date()

    # Doanh thu theo sản phẩm
    cursor.execute("""
        SELECT CT.MaSanPham, SUM(CT.Gia) AS DoanhThu
        FROM ChiTietDonHang CT
        JOIN DonHang DH ON CT.MaDonHang = DH.MaDonHang
        WHERE CONVERT(date, DH.NgayDatHang) = ?
        GROUP BY CT.MaSanPham
    """, (current_date,))
    product_rows = cursor.fetchall()

    revenue_by_product = []
    for row in product_rows:
        cursor.execute("SELECT TenSanPham FROM SanPham WHERE MaSanPham = ?", (row.MaSanPham,))
        product = cursor.fetchone()
        revenue_by_product.append({
            "TenSanPham": product.TenSanPham if product else "Không xác định",
            "DoanhThu": float(row.DoanhThu or 0)
        })

    # Doanh thu theo danh mục
    cursor.execute("""
        SELECT SP.MaDanhMuc, SUM(CT.Gia) AS DoanhThu
        FROM ChiTietDonHang CT
        JOIN DonHang DH ON CT.MaDonHang = DH.MaDonHang
        JOIN SanPham SP ON CT.MaSanPham = SP.MaSanPham
        WHERE CONVERT(date, DH.NgayDatHang) = ?
        GROUP BY SP.MaDanhMuc
    """, (current_date,))
    category_rows = cursor.fetchall()

    revenue_by_category = []
    for row in category_rows:
        cursor.execute("SELECT TenDanhMuc FROM DanhMucSanPham WHERE MaDanhMuc = ?", (row.MaDanhMuc,))
        category = cursor.fetchone()
        revenue_by_category.append({
            "TenDanhMuc": category.TenDanhMuc if category else "Không xác định",
            "DoanhThu": float(row.DoanhThu or 0)
        })

    conn.close()

    return {
        "revenueByProduct": revenue_by_product,
        "revenueByCategory": revenue_by_category
    }

def thong_ke_theo_thang():
    conn = get_connection()
    cursor = conn.cursor()

    # ================================
    #      TÍNH NGÀY TRONG THÁNG
    # ================================
    now = datetime.now()
    first_day = datetime(now.year, now.month, 1).date()
    if now.month == 12:
        last_day = datetime(now.year, 12, 31).date()
    else:
        last_day = (datetime(now.year, now.month + 1, 1) - timedelta(days=1)).date()

    # ================================
    #      1. TỔNG ĐƠN HÀNG
    # ================================
    cursor.execute("""
            SELECT COUNT(*)
            FROM DonHang
            WHERE CONVERT(date, NgayDatHang) BETWEEN ? AND ?
        """, (first_day, last_day))
    totalOrders = cursor.fetchone()[0]

    # ================================
    #      2. ĐƠN THEO TRẠNG THÁI
    # ================================
    def get_count(status):
        cursor.execute("""
                SELECT COUNT(*)
                FROM DonHang
                WHERE TrangThai = ? 
                  AND CONVERT(date, NgayDatHang) BETWEEN ? AND ?
            """, (status, first_day, last_day))
        return cursor.fetchone()[0]

    pendingOrders = get_count(0)
    approvedOrders = get_count(1)
    deliveredOrders = get_count(2)
    cancelledOrders = get_count(3)

    # ================================
    #      3. DOANH THU THEO TRẠNG THÁI
    # ================================
    def get_revenue(status):
        cursor.execute("""
                SELECT SUM(TongTien)
                FROM DonHang
                WHERE TrangThai = ?
                  AND CONVERT(date, NgayDatHang) BETWEEN ? AND ?
            """, (status, first_day, last_day))

        val = cursor.fetchone()[0]
        return float(val or 0)

    revenuePending = get_revenue(0)
    revenueApproved = get_revenue(1)
    revenueDelivered = get_revenue(2)
    revenueCancelled = get_revenue(3)

    totalRevenue = revenuePending + revenueApproved + revenueDelivered

    # ================================
    #      4. TOP 5 SẢN PHẨM BÁN CHẠY
    # ================================
    cursor.execute("""
            SELECT TOP 5 
                CT.MaSanPham,
                SUM(CT.SoLuong) AS SoLuongBan
            FROM ChiTietDonHang CT
            JOIN DonHang DH ON CT.MaDonHang = DH.MaDonHang
            WHERE DH.TrangThai = 2
              AND CONVERT(date, DH.NgayDatHang) BETWEEN ? AND ?
            GROUP BY CT.MaSanPham
            ORDER BY SUM(CT.SoLuong) DESC
        """, (first_day, last_day))

    rows = cursor.fetchall()
    bestSellingProducts = []

    for row in rows:
        cursor.execute("SELECT TenSanPham FROM SanPham WHERE MaSanPham = ?", (row.MaSanPham,))
        product = cursor.fetchone()

        bestSellingProducts.append({
            "tenSanPham": product.TenSanPham if product else "Không xác định",
            "soLuong": int(row.SoLuongBan or 0)
        })

    conn.close()

    return jsonify({
        "totalOrders": totalOrders,
        "pendingOrders": pendingOrders,
        "approvedOrders": approvedOrders,
        "deliveredOrders": deliveredOrders,
        "cancelledOrders": cancelledOrders,

        "revenuePending": revenuePending,
        "revenueApproved": revenueApproved,
        "revenueDelivered": revenueDelivered,
        "revenueCancelled": revenueCancelled,
        "totalRevenue": totalRevenue,

        "bestSellingProducts": bestSellingProducts
    })
