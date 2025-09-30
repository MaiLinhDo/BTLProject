from flask import Blueprint, request, jsonify
from app.services.voucher_service import get_voucher_by_code, update_voucher_usage,get_vouchers, get_voucher_by_id, create_voucher, update_voucher_admin, toggle_voucher_status

voucher_routes = Blueprint('voucher_routes', __name__)

@voucher_routes.route('/api/voucher', methods=['GET'])
def get_voucher():
    code = request.args.get('code')
    voucher = get_voucher_by_code(code)
    if voucher:
        return jsonify({
            "Code": voucher.Code,
            "GiamGia": voucher.GiamGia,
            "MaVoucher": voucher.MaVoucher
        })
    return jsonify({"error": "Voucher not found"}), 404

@voucher_routes.route('/api/voucher/update', methods=['POST'])
def update_voucher():
    data = request.json
    code = data.get('code')
    update_voucher_usage(code)
    return jsonify({"success": True})
# GET: Lấy danh sách voucher với phân trang và tìm kiếm
@voucher_routes.route('/api/get_all_voucher', methods=['GET'])
def get_all_voucher():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 5))
    search_term = request.args.get('search', '')

    vouchers, total = get_vouchers(page, page_size, search_term)
    if vouchers:
        return jsonify({
            "success": True,
            "vouchers": vouchers,
            "total": total
        })
    return jsonify({"success": False, "message": "No vouchers found"}), 404

# POST: Thêm voucher mới
@voucher_routes.route('/api/voucher', methods=['POST'])
def add_voucher():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    result = create_voucher(data)
    if result:
        return jsonify({"success": True, "message": "Voucher created successfully"})
    return jsonify({"success": False, "message": "Failed to create voucher"}), 500

# GET: Lấy chi tiết voucher theo ID
@voucher_routes.route('/api/voucher/<int:id>', methods=['GET'])
def get_voucher_by_id_route(id):
    voucher = get_voucher_by_id(id)
    if voucher:
        return jsonify({"success": True, "voucher": voucher})
    return jsonify({"success": False, "message": "Voucher not found"}), 404

@voucher_routes.route('/api/voucher/<int:id>', methods=['PUT'])
def update_voucher_route(id):
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    # In thông tin data và id để kiểm tra xem chúng có đúng không
    print(f"Updating voucher with ID: {id}")
    print(f"Data: {data}")

    result = update_voucher_admin(id, data)  # Gọi hàm update_voucher
    if result:
        return jsonify({"success": True, "message": "Voucher updated successfully"})
    return jsonify({"success": False, "message": "Failed to update voucher"}), 500



# PUT: Chuyển đổi trạng thái voucher (kích hoạt/tắt)
@voucher_routes.route('/api/voucher/<int:id>/toggle', methods=['PUT'])
def toggle_voucher(id):
    result = toggle_voucher_status(id)
    if result:
        return jsonify({"success": True, "message": "Voucher status toggled"})
    return jsonify({"success": False, "message": "Failed to toggle voucher status"}), 500
