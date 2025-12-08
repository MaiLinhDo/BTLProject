from flask import Blueprint, request, jsonify
from app.config import Config
import pyodbc

def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)

def serialize_supplier(row):
    return {
        "MaNhaCungCap": row.MaNhaCungCap,
        "TenNhaCungCap": row.TenNhaCungCap,
        "MaSoThue": row.MaSoThue,
        "Email": row.Email,
        "SoDienThoai": row.SoDienThoai,
        "DiaChi": row.DiaChi,
        "TrangThai": row.TrangThai,
        "NgayTao": row.NgayTao.strftime("%Y-%m-%d") if row.NgayTao else None,
        "GhiChu": row.GhiChu
    }

supplier_routes = Blueprint("supplier_routes", __name__)

@supplier_routes.route('/api/suppliers', methods=['GET'])
def list_suppliers():
    search = request.args.get('search', "")
    status = request.args.get('status', type=str)
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('pageSize', default=10, type=int)

    conn = get_connection()
    cursor = conn.cursor()

    where_clause = "WHERE 1=1"
    params = []

    if search:
        like_value = f"%{search}%"
        where_clause += " AND (TenNhaCungCap LIKE ? OR SoDienThoai LIKE ? OR Email LIKE ?)"
        params.extend([like_value, like_value, like_value])

    if status in ("0", "1"):
        where_clause += " AND TrangThai = ?"
        params.append(int(status))

    query = f"""
        SELECT MaNhaCungCap, TenNhaCungCap, MaSoThue, Email, SoDienThoai, DiaChi, TrangThai, NgayTao, GhiChu
        FROM NhaCungCap
        {where_clause}
        ORDER BY NgayTao DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    cursor.execute(query, params + [(page - 1) * page_size, page_size])
    rows = cursor.fetchall()

    count_query = f"SELECT COUNT(*) FROM NhaCungCap {where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "success": True,
        "suppliers": [serialize_supplier(row) for row in rows],
        "totalPages": (total_count + page_size - 1) // page_size
    })

@supplier_routes.route('/api/suppliers/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MaNhaCungCap, TenNhaCungCap, MaSoThue, Email, SoDienThoai, DiaChi, TrangThai, NgayTao, GhiChu
        FROM NhaCungCap
        WHERE MaNhaCungCap = ?
    """, (supplier_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"success": False, "message": "Không tìm thấy nhà cung cấp"}), 404

    return jsonify({"success": True, "supplier": serialize_supplier(row)})

@supplier_routes.route('/api/suppliers', methods=['POST'])
def create_supplier():
    data = request.json
    ten = data.get("TenNhaCungCap")
    if not ten:
        return jsonify({"success": False, "message": "Tên nhà cung cấp không được để trống"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO NhaCungCap (TenNhaCungCap, MaSoThue, Email, SoDienThoai, DiaChi, TrangThai, NgayTao, GhiChu)
        VALUES (?, ?, ?, ?, ?, ?, GETDATE(), ?)
    """, (
        ten,
        data.get("MaSoThue"),
        data.get("Email"),
        data.get("SoDienThoai"),
        data.get("DiaChi"),
        data.get("TrangThai", 1),
        data.get("GhiChu")
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@supplier_routes.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    data = request.json
    ten = data.get("TenNhaCungCap")
    if not ten:
        return jsonify({"success": False, "message": "Tên nhà cung cấp không được để trống"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE NhaCungCap
        SET TenNhaCungCap = ?, MaSoThue = ?, Email = ?, SoDienThoai = ?, DiaChi = ?, TrangThai = ?, GhiChu = ?
        WHERE MaNhaCungCap = ?
    """, (
        ten,
        data.get("MaSoThue"),
        data.get("Email"),
        data.get("SoDienThoai"),
        data.get("DiaChi"),
        data.get("TrangThai", 1),
        data.get("GhiChu"),
        supplier_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@supplier_routes.route('/api/suppliers/<int:supplier_id>/toggle', methods=['PATCH'])
def toggle_supplier_status(supplier_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TrangThai FROM NhaCungCap WHERE MaNhaCungCap = ?", (supplier_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "message": "Không tìm thấy nhà cung cấp"}), 404

    new_status = 0 if row.TrangThai else 1
    cursor.execute("UPDATE NhaCungCap SET TrangThai = ? WHERE MaNhaCungCap = ?", (new_status, supplier_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "TrangThai": new_status})

