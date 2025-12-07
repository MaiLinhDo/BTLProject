from flask import Blueprint, request, jsonify
import json
import app.services.sanpham_service as sanpham_service
from app.config import Config
import pyodbc

def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)

def normalize_spec_filters(raw_filters):
    if not raw_filters:
        return []

    parsed = raw_filters
    if isinstance(raw_filters, str):
        try:
            parsed = json.loads(raw_filters)
        except (ValueError, TypeError):
            return []

    normalized = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        spec_id = item.get("MaThongSo") or item.get("maThongSo")
        value = item.get("GiaTri") or item.get("giaTri")
        if not spec_id or value is None:
            continue
        try:
            normalized.append({
                "MaThongSo": int(spec_id),
                "GiaTri": str(value).strip()
            })
        except (ValueError, TypeError):
            continue
    return normalized

def normalize_spec_values(raw_value):
    normalized = []
    if not raw_value:
        return normalized
    specs = normalize_spec_filters(raw_value)
    for spec in specs:
        if spec["GiaTri"]:
            normalized.append((spec["MaThongSo"], spec["GiaTri"]))
    return normalized

def save_product_specs(cursor, product_id, specs, replace=False):
    if replace:
        cursor.execute("DELETE FROM SanPhamThongSo WHERE MaSanPham = ?", (product_id,))
    for spec_id, value in specs:
        cursor.execute("""
            INSERT INTO SanPhamThongSo (MaSanPham, MaThongSo, GiaTri)
            VALUES (?, ?, ?)
        """, (product_id, spec_id, value))

product_routes = Blueprint("product_routes", __name__)
# API lấy thông tin sản phẩm theo ID
@product_routes.route("/api/get_detail_product", methods=["POST"])
def get_detail_product():
    data = request.json
    product_id = data.get("productId")

    if not product_id:
        return jsonify({"success": False, "message": "Thiếu productId"}), 400

    # Gọi service để lấy thông tin sản phẩm
    product = sanpham_service.get_product_by_id(product_id)

    if not product:
        return jsonify({"success": False, "message": "Không tìm thấy sản phẩm."}), 404
    
    # Lấy sản phẩm cùng giá
    sanpham_cung_gia = sanpham_service.get_similar_price_products(product["Gia"], product["MaSanPham"])

    return jsonify({
        "success": True,
        "product": product,
        "similarProducts": sanpham_cung_gia
    })
@product_routes.route("/api/get_product", methods=["POST"])
def get_product():
    data = request.json
    product_id = data.get("productId")

    if not product_id:
        return jsonify({"success": False, "message": "Thiếu productId"}), 400

    product = sanpham_service.get_product_by_id(product_id)

    if not product:
        return jsonify({"success": False, "message": "Không tìm thấy sản phẩm."}), 404
    print(product)
    return jsonify({"success": True, "product": product})
@product_routes.route('/api/products_user', methods=['GET'])
def api_products():
    # Lấy các tham số từ request
    category_id = request.args.get('id')
    search = request.args.get('search', "")
    min_price = request.args.get('minPrice', type=float)
    max_price = request.args.get('maxPrice', type=float)
    brand = request.args.get('brand', type=int)
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('pageSize', default=8, type=int)
    spec_filters_raw = request.args.get('specFilters')
    spec_filters = normalize_spec_filters(spec_filters_raw)

    # Gọi đến service để lấy danh sách sản phẩm
    result = sanpham_service.get_products_user(
        category_id,
        search,
        min_price,
        max_price,
        brand,
        page,
        page_size,
        spec_filters=spec_filters
    )

    return jsonify(result)
@product_routes.route('/api/get_products', methods=['POST'])
def get_products():
    data = request.json
    search_string = data.get("SearchString", "")
    page = data.get("Page", 1)
    page_size = data.get("PageSize", 10)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Xử lý chuỗi tìm kiếm
    search_pattern = f"%{search_string}%" if search_string else "%"
    
    # Tính toán phân trang
    offset = (page - 1) * page_size
    
    # Truy vấn lấy tên sản phẩm và số lượng
    query = """
        SELECT TenSanPham, SoLuong 
        FROM SanPham 
        WHERE TenSanPham LIKE ? 
        ORDER BY TenSanPham 
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    
    # Truyền tham số đúng cách
    cursor.execute(query, (search_pattern, offset, page_size))
    products = cursor.fetchall()

    # Chuyển đổi dữ liệu thành một danh sách từ điển chỉ chứa tên sản phẩm và số lượng
    product_list = [{"TenSanPham": row[0], "SoLuong": row[1]} for row in products]
    
    # Đếm tổng số sản phẩm
    count_query = "SELECT COUNT(*) FROM SanPham WHERE TenSanPham LIKE ?"
    cursor.execute(count_query, (search_pattern,))
    total_count = cursor.fetchone()[0]
    
    conn.close()
    
    # Trả về kết quả
    return jsonify({
        "success": True,
        "products": product_list,
        "totalPages": (total_count // page_size) + (1 if total_count % page_size > 0 else 0)
    })
@product_routes.route('/api/get_sanpham', methods=['GET'])
def get_sanpham():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MaSanPham, TenSanPham, SoLuong FROM SanPham")
    rows = cursor.fetchall()
    conn.close()

    san_phams = [
        {"MaSanPham": row[0], "TenSanPham": row[1], "SoLuong": row[2]}
        for row in rows
    ]

    return jsonify({
        "success": True,
        "sanPhams": san_phams
    })
@product_routes.route('/api/get_sanpham_admin', methods=['POST'])
def get_sanpham_admin():
    data = request.json
    search_term = data.get("SearchTerm", "")
    page = data.get("Page", 1)
    page_size = data.get("PageSize", 10)
    spec_filters = normalize_spec_filters(data.get("SpecFilters"))

    offset = (page - 1) * page_size

    conn = get_connection()
    cursor = conn.cursor()

    where_clause = "WHERE TenSanPham LIKE ?"
    params = [f"%{search_term}%"]

    for spec in spec_filters:
        where_clause += """
            AND EXISTS (
                SELECT 1 FROM SanPhamThongSo sps
                WHERE sps.MaSanPham = SanPham.MaSanPham
                AND sps.MaThongSo = ?
                AND sps.GiaTri LIKE ?
            )
        """
        params.extend([spec["MaThongSo"], f"%{spec['GiaTri']}%"])

    query = f"""
        SELECT MaSanPham, TenSanPham, MoTa, Gia, GiaMoi, TrangThai, HinhAnh, MaDanhMuc, MaHang
        FROM SanPham
        {where_clause}
        ORDER BY MaSanPham DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    cursor.execute(query, params + [offset, page_size])
    rows = cursor.fetchall()

    # Đếm tổng số sản phẩm
    count_query = f"SELECT COUNT(*) FROM SanPham {where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]

    conn.close()

    products = []
    for row in rows:
        products.append({
            "MaSanPham": row[0],
            "TenSanPham": row[1],
            "MoTa": row[2],
            "Gia": row[3],
            "GiaMoi": row[4],
            "TrangThai": row[5],
            "HinhAnh": row[6],
            "MaDanhMuc": row[7],
            "MaHang": row[8]
        })

    return jsonify({
        "success": True,
        "sanPhams": products,
        "totalPages": (total_count // page_size) + (1 if total_count % page_size > 0 else 0)
    })
@product_routes.route('/api/create_sanpham', methods=['POST'])
def create_sanpham():
    data = request.form
    hinh_dai_dien = request.files.get('HinhDaiDien')
    hinh_kem_theo = request.files.getlist('HinhKemTheo')

    ten_san_pham = data.get('TenSanPham')
    mo_ta = data.get('MoTa')
    gia = data.get('Gia')
    ma_danh_muc = data.get('MaDanhMuc')
    ma_hang = data.get('MaHang')
    so_luong = data.get('SoLuong')
    spec_values = normalize_spec_values(data.get('ThongSoKyThuat'))
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO SanPham (TenSanPham, MoTa, Gia, MaDanhMuc, MaHang, TrangThai, NgayTao, HinhAnh, SoLuong)
        OUTPUT INSERTED.MaSanPham
        VALUES (?, ?, ?, ?, ?, 1, GETDATE(), ?,?)
    """

    hinh_anh = (hinh_dai_dien.filename) if hinh_dai_dien else None

    cursor.execute(query, (ten_san_pham, mo_ta, gia, ma_danh_muc, ma_hang, hinh_anh, so_luong))
    ma_san_pham = cursor.fetchone()[0]

    if spec_values:
        save_product_specs(cursor, ma_san_pham, spec_values)

    conn.commit()

    conn.close()
    return jsonify({"success": True, "MaSanPham": ma_san_pham})
@product_routes.route('/api/update_sanpham/<int:id>', methods=['POST'])
def update_sanpham(id):
    data = request.form
    hinh_dai_dien = request.files.get('HinhDaiDien')
    hinh_kem_theo = request.files.getlist('HinhKemTheo')

    ten_san_pham = data.get('TenSanPham')
    mo_ta = data.get('MoTa')
    gia = data.get('Gia')
    ma_danh_muc = data.get('MaDanhMuc')
    ma_hang = data.get('MaHang')
    spec_values = normalize_spec_values(data.get('ThongSoKyThuat'))

    conn = get_connection()
    cursor = conn.cursor()

    # Cập nhật sản phẩm
    query = """
        UPDATE SanPham
        SET TenSanPham = ?, MoTa = ?, Gia = ?, MaDanhMuc = ?, MaHang = ?, NgayTao = GETDATE()
        WHERE MaSanPham = ?
    """
    cursor.execute(query, (ten_san_pham, mo_ta, gia, ma_danh_muc, ma_hang, id))

    # Cập nhật ảnh đại diện nếu có
    if hinh_dai_dien:
        hinh_anh = (hinh_dai_dien.filename)
        update_image_query = "UPDATE SanPham SET HinhAnh = ? WHERE MaSanPham = ?"
        cursor.execute(update_image_query, (hinh_anh, id))

    save_product_specs(cursor, id, spec_values, replace=True)

    conn.commit()

    conn.close()
    return jsonify({"success": True})
@product_routes.route('/api/giamgia', methods=['POST'])
def giamgia():
    data = request.json
    ma_san_pham = data.get("MaSanPham")
    gia_moi = data.get("GiaMoi")

    conn = get_connection()
    cursor = conn.cursor()

    query = "UPDATE SanPham SET GiaMoi = ? WHERE MaSanPham = ?"
    cursor.execute(query, (gia_moi, ma_san_pham))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@product_routes.route('/api/ngunggiamgia', methods=['POST'])
def ngunggiamgia():
    data = request.json
    ma_san_pham = data.get("MaSanPham")

    conn = get_connection()
    cursor = conn.cursor()

    query = "UPDATE SanPham SET GiaMoi = NULL WHERE MaSanPham = ?"
    cursor.execute(query, (ma_san_pham,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})
@product_routes.route('/api/ngung_ban', methods=['POST'])
def ngung_ban():
    data = request.json
    ma_san_pham = data.get("MaSanPham")
    TrangThai = data.get("TrangThai")

    conn = get_connection()
    cursor = conn.cursor()

    query = "UPDATE SanPham SET TrangThai = ? WHERE MaSanPham = ?"
    cursor.execute(query, (TrangThai, ma_san_pham))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

