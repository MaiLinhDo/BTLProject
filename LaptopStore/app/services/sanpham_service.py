import pyodbc
from app.config import Config
from datetime import datetime
from flask import request
def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)
def get_product_by_id(product_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MaSanPham,MoTa,MaHang,MaDanhMuc,NgayTao, TenSanPham, SoLuong, Gia, GiaMoi, HinhAnh,TrangThai
        FROM SanPham
        WHERE MaSanPham = ?
    """, (product_id,))
    
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    cursor.execute("""
        SELECT ts.MaThongSo, ts.TenThongSo, ts.DonVi, ts.MoTa, ts.ThuTu, sps.GiaTri
        FROM SanPhamThongSo sps
        INNER JOIN ThongSoKyThuat ts ON sps.MaThongSo = ts.MaThongSo
        WHERE sps.MaSanPham = ?
        ORDER BY ISNULL(ts.ThuTu, ts.MaThongSo)
    """, (product_id,))
    spec_rows = cursor.fetchall()

    cursor.execute("""
        SELECT MaSerial, SerialNumber, TrangThai, NgayNhap, NgayBan
        FROM SanPhamSerial
        WHERE MaSanPham = ?
        ORDER BY MaSerial DESC
    """, (product_id,))
    serial_rows = cursor.fetchall()
    conn.close()

    specs = [{
        "MaThongSo": spec[0],
        "TenThongSo": spec[1],
        "DonVi": spec[2],
        "MoTa": spec[3],
        "ThuTu": spec[4],
        "GiaTri": spec[5]
    } for spec in spec_rows]

    serials = [{
        "MaSerial": serial[0],
        "SerialNumber": serial[1],
        "TrangThai": serial[2],
        "NgayNhap": serial[3].strftime("%Y-%m-%d %H:%M:%S") if serial[3] else None,
        "NgayBan": serial[4].strftime("%Y-%m-%d %H:%M:%S") if serial[4] else None
    } for serial in serial_rows]

    return {
        "MaSanPham": row.MaSanPham,
        "TenSanPham": row.TenSanPham,
        "SoLuong": row.SoLuong,
        "Gia": float(row.Gia) if row.Gia else 0,
        "GiaMoi": float(row.GiaMoi) if row.GiaMoi else None,
        "HinhAnh": row.HinhAnh,
        "MoTa": row.MoTa,
        "MaHang": row.MaHang,
        "MaDanhMuc": row.MaDanhMuc,
        "NgayTao": row.NgayTao.strftime("%Y-%m-%d"),
        "TrangThai": row.TrangThai,
        "ThongSoKyThuat": specs,
        "SerialNumbers": serials,
        "SerialCount": len(serials)
    }
    # Sửa service để lấy sản phẩm cùng giá
def get_similar_price_products(price, product_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Truy vấn các sản phẩm có giá trong khoảng +/- 5 triệu của sản phẩm hiện tại
    cursor.execute("""
        SELECT MaSanPham, TenSanPham, Gia, GiaMoi, HinhAnh, MoTa, MaHang, MaDanhMuc, NgayTao, TrangThai
        FROM SanPham
        WHERE Gia >= ? - 5000000 AND Gia <= ? + 5000000 AND MaSanPham != ? AND TrangThai = 1
        ORDER BY Gia
    """, (price, price, product_id))
    
    products = cursor.fetchall()
    conn.close()

    # Xử lý và trả về danh sách sản phẩm
    similar_products = [{
        "MaSanPham": product[0],
        "TenSanPham": product[1],
        "Gia": float(product[2]),
        "GiaMoi": float(product[3]) if product[3] else None,
        "HinhAnh": product[4],
        "MoTa": product[5],
        "MaHang": product[6],
        "MaDanhMuc": product[7],
        "NgayTao": product[8].strftime("%Y-%m-%d"),
        "TrangThai": product[9],
    } for product in products]

    return similar_products

def get_products_user(category_id, search="", min_price=None, max_price=None, brand=None, page=1, page_size=8, spec_filters=None):
    conn = get_connection()
    cursor = conn.cursor()
    spec_filters = spec_filters or []
    
    # SQL cơ bản để truy vấn sản phẩm (dựa trên code cũ)
    query = """
    SELECT MaSanPham, TenSanPham, Gia, HinhAnh, MoTa, GiaMoi, MaHang, MaDanhMuc, NgayTao, TrangThai, SoLuong
    FROM SanPham 
    WHERE TrangThai = 1
    """
    
    params = []
    
    # Thêm điều kiện danh mục (chỉ khi có category_id hợp lệ)
    if category_id and category_id != "0" and category_id != "" and category_id != "None":
        query += " AND MaDanhMuc = ?"
        params.append(int(category_id))
    
    # Thêm các điều kiện tìm kiếm (giống code cũ)
    if search and search.strip():
        query += " AND TenSanPham LIKE ?"
        params.append(f"%{search.strip()}%")
        
    if min_price is not None:
        query += " AND (CASE WHEN GiaMoi IS NOT NULL THEN GiaMoi ELSE Gia END) >= ?"
        params.append(min_price)
        
    if max_price is not None:
        query += " AND (CASE WHEN GiaMoi IS NOT NULL THEN GiaMoi ELSE Gia END) <= ?"
        params.append(max_price)
        
    if brand is not None:
        query += " AND MaHang = ?"
        params.append(brand)

    for spec in spec_filters:
        query += """
        AND EXISTS (
            SELECT 1 FROM SanPhamThongSo sps
            WHERE sps.MaSanPham = SanPham.MaSanPham
              AND sps.MaThongSo = ?
              AND sps.GiaTri LIKE ?
        )
        """
        params.append(spec["MaThongSo"])
        params.append(f"%{spec['GiaTri']}%")
    
    query += " ORDER BY MaSanPham DESC"
    
    # Pagination (giống code cũ)
    query += " OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
    params.append((page - 1) * page_size)
    params.append(page_size)
    
    print(f"Main query: {query}")
    print(f"Main params: {params}")
    
    # Thực thi query chính
    cursor.execute(query, tuple(params))
    products = cursor.fetchall()
    
    # Lấy tổng số sản phẩm để tính toán trang (dựa trên code cũ, nhưng cải tiến)
    count_query = """
    SELECT COUNT(*) 
    FROM SanPham 
    WHERE TrangThai = 1
    """
    
    count_params = []
    
    # Thêm lại các điều kiện cho count query (không bao gồm pagination)
    if category_id and category_id != "0" and category_id != "" and category_id != "None":
        count_query += " AND MaDanhMuc = ?"
        count_params.append(int(category_id))
    
    if search and search.strip():
        count_query += " AND TenSanPham LIKE ?"
        count_params.append(f"%{search.strip()}%")
        
    if min_price is not None:
        count_query += " AND (CASE WHEN GiaMoi IS NOT NULL THEN GiaMoi ELSE Gia END) >= ?"
        count_params.append(min_price)
        
    if max_price is not None:
        count_query += " AND (CASE WHEN GiaMoi IS NOT NULL THEN GiaMoi ELSE Gia END) <= ?"
        count_params.append(max_price)
        
    if brand is not None:
        count_query += " AND MaHang = ?"
        count_params.append(brand)

    for spec in spec_filters:
        count_query += """
        AND EXISTS (
            SELECT 1 FROM SanPhamThongSo sps
            WHERE sps.MaSanPham = SanPham.MaSanPham
              AND sps.MaThongSo = ?
              AND sps.GiaTri LIKE ?
        )
        """
        count_params.append(spec["MaThongSo"])
        count_params.append(f"%{spec['GiaTri']}%")
    
    print(f"Count query: {count_query}")
    print(f"Count params: {count_params}")
    
    cursor.execute(count_query, tuple(count_params))
    total_products = cursor.fetchone()[0]
    total_pages = (total_products + page_size - 1) // page_size
    
    # Lấy thông tin rating cho các sản phẩm đã lấy được
    if products:
        product_ids = [str(product[0]) for product in products]
        placeholders = ','.join(['?' for _ in product_ids])
        
        rating_query = f"""
        SELECT 
            sp.MaSanPham,
            ISNULL(AVG(CAST(dg.DiemDanhGia AS FLOAT)), 0) as TrungBinhSao,
            COUNT(dg.MaDanhGia) as SoLuongDanhGia
        FROM SanPham sp
        LEFT JOIN DanhGiaSanPham dg ON sp.MaSanPham = dg.MaSanPham
        WHERE sp.MaSanPham IN ({placeholders})
        GROUP BY sp.MaSanPham
        """
        
        cursor.execute(rating_query, product_ids)
        ratings = cursor.fetchall()
        
        # Tạo dictionary để map rating với product ID
        rating_dict = {rating[0]: {"TrungBinhSao": round(rating[1], 1), "SoLuongDanhGia": rating[2]} for rating in ratings}
    else:
        rating_dict = {}
    
    # Xử lý dữ liệu trả về (kết hợp code cũ với rating)
    product_data = []
    for product in products:
        product_id = product[0]
        rating_info = rating_dict.get(product_id, {"TrungBinhSao": 0.0, "SoLuongDanhGia": 0})
        
        product_data.append({
            "MaSanPham": product[0],
            "TenSanPham": product[1],
            "Gia": float(product[2]) if product[2] else 0,
            "HinhAnh": product[3],
            "MoTa": product[4],
            "GiaMoi": float(product[5]) if product[5] else None,
            "MaHang": product[6],
            "MaDanhMuc": product[7],
            "NgayTao": product[8].strftime("%Y-%m-%d") if product[8] else "",
            "TrangThai": product[9],
            "SoLuong": product[10],
            # Thêm thông tin rating
            "TrungBinhSao": rating_info["TrungBinhSao"],
            "SoLuongDanhGia": rating_info["SoLuongDanhGia"]
        })
    
    conn.close()
    
    print(f"Total products: {total_products}, Total pages: {total_pages}, Current page: {page}")
    
    return {
        "products": product_data,
        "totalPages": total_pages,
        "currentPage": page,
        "totalProducts": total_products
    }

   