from flask import Blueprint, request, jsonify
from app.config import Config
import pyodbc

def get_connection():
    return pyodbc.connect(Config.SQL_SERVER_CONN)

def serialize_spec(row):
    return {
        "MaThongSo": row.MaThongSo,
        "TenThongSo": row.TenThongSo,
        "DonVi": row.DonVi,
        "MoTa": row.MoTa,
        "ThuTu": row.ThuTu,
        "TrangThai": row.TrangThai
    }

spec_routes = Blueprint("spec_routes", __name__)

@spec_routes.route('/api/spec-definitions', methods=['GET'])
def list_specs():
    search = request.args.get('search', "")
    status = request.args.get('status')
    active_only = request.args.get('active')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('pageSize', default=20, type=int)

    conn = get_connection()
    cursor = conn.cursor()

    where_clause = "WHERE 1=1"
    params = []

    if search:
        where_clause += " AND TenThongSo LIKE ?"
        params.append(f"%{search}%")

    if status in ("0", "1"):
        where_clause += " AND TrangThai = ?"
        params.append(int(status))
    elif active_only == "1":
        where_clause += " AND TrangThai = 1"

    query = f"""
        SELECT MaThongSo, TenThongSo, DonVi, MoTa, ThuTu, TrangThai
        FROM ThongSoKyThuat
        {where_clause}
        ORDER BY ISNULL(ThuTu, MaThongSo)
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    cursor.execute(query, params + [(page - 1) * page_size, page_size])
    rows = cursor.fetchall()
    
    # Lấy danh sách giá trị cho từng thông số
    specs = []
    for row in rows:
        spec = serialize_spec(row)
        
        # Chỉ lấy giá trị nếu active=1 (đây là API dùng cho client)
        if active_only == "1":
            cursor.execute("""
                SELECT DISTINCT GiaTri 
                FROM SanPhamThongSo 
                WHERE MaThongSo = ? AND LTRIM(RTRIM(GiaTri)) <> ''
                ORDER BY GiaTri
            """, (row.MaThongSo,))
            values = [r[0] for r in cursor.fetchall()]
            spec["Values"] = values
        else:
            spec["Values"] = []
            
        specs.append(spec)

    count_query = f"SELECT COUNT(*) FROM ThongSoKyThuat {where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "success": True,
        "specs": specs,
        "totalPages": (total_count + page_size - 1) // page_size
    })

@spec_routes.route('/api/spec-definitions/<int:spec_id>', methods=['GET'])
def get_spec(spec_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MaThongSo, TenThongSo, DonVi, MoTa, ThuTu, TrangThai
        FROM ThongSoKyThuat
        WHERE MaThongSo = ?
    """, (spec_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"success": False, "message": "Không tìm thấy thông số"}), 404

    return jsonify({"success": True, "spec": serialize_spec(row)})

@spec_routes.route('/api/spec-definitions', methods=['POST'])
def create_spec():
    data = request.json
    name = data.get("TenThongSo")
    if not name:
        return jsonify({"success": False, "message": "Tên thông số không được để trống"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ThongSoKyThuat (TenThongSo, DonVi, MoTa, ThuTu, TrangThai)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        data.get("DonVi"),
        data.get("MoTa"),
        data.get("ThuTu"),
        data.get("TrangThai", 1)
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@spec_routes.route('/api/spec-definitions/<int:spec_id>', methods=['PUT'])
def update_spec(spec_id):
    data = request.json
    name = data.get("TenThongSo")
    if not name:
        return jsonify({"success": False, "message": "Tên thông số không được để trống"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE ThongSoKyThuat
        SET TenThongSo = ?, DonVi = ?, MoTa = ?, ThuTu = ?, TrangThai = ?
        WHERE MaThongSo = ?
    """, (
        name,
        data.get("DonVi"),
        data.get("MoTa"),
        data.get("ThuTu"),
        data.get("TrangThai", 1),
        spec_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@spec_routes.route('/api/spec-definitions/<int:spec_id>/toggle', methods=['PATCH'])
def toggle_spec(spec_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TrangThai FROM ThongSoKyThuat WHERE MaThongSo = ?", (spec_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "message": "Không tìm thấy thông số"}), 404

    new_status = 0 if row.TrangThai else 1
    cursor.execute("UPDATE ThongSoKyThuat SET TrangThai = ? WHERE MaThongSo = ?", (new_status, spec_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "TrangThai": new_status})

