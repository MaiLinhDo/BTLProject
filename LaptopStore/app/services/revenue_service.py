import pyodbc
from app.config import Config
from datetime import datetime

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
