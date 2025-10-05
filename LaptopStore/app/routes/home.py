from flask import Blueprint, jsonify
import app.services.home_service as home_service
from flask import request

api = Blueprint('api', __name__)

@api.route('/api/vouchers', methods=['GET'])
def api_vouchers():
    return jsonify(home_service.get_valid_vouchers())

@api.route('/api/banners', methods=['GET'])
def api_banners():
    return jsonify(home_service.get_banners())

@api.route('/api/products', methods=['GET'])
def api_products():
    return jsonify(home_service.get_products())

@api.route('/api/categories', methods=['GET'])
def api_categories():
    return jsonify(home_service.get_categories())
@api.route('/api/get_hang', methods=['GET'])
def get_hang():
    return jsonify(home_service.get_hang())


@api.route('/api/dangky', methods=['POST'])
def api_dangky():
    data = request.json
    result = home_service.dang_ky_tai_khoan(data)
    return jsonify(result)


@api.route('/api/dangnhap', methods=['POST'])
def api_dang_nhap():
    data = request.json
    username = data.get('Username')
    password = data.get('Password')

    result = home_service.dang_nhap_tai_khoan(username, password)

    print(result)
    return jsonify(result)
@api.route('/api/capnhat-thongtin', methods=['POST'])
def capnhat_thong_tin():
    data = request.json
    response = home_service.capnhat_thong_tin_service(data)
    return jsonify(response)
@api.route('/api/hoso', methods=['GET'])
def api_hoso():
    taikhoan = request.args.get('username')  # Giả sử username được truyền qua query string
    if not taikhoan:
        return jsonify({"success": False, "message": "Tên đăng nhập không hợp lệ."}), 400

    result = home_service.get_user_profile(taikhoan)
    return jsonify(result)
@api.route('/api/dangxuat', methods=['POST'])
def dang_xuat():
    taikhoan = request.json.get('username')  # Lấy username từ body request

    if not taikhoan:
        return jsonify({"success": False, "message": "Tên đăng nhập không hợp lệ."}), 400

    result = home_service.dang_xuat(taikhoan)
    return jsonify(result)
@api.route('/api/giohang', methods=['POST'])
def api_giohang():
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({"success": False, "message": "Tên đăng nhập không hợp lệ."}), 400
    
    result = home_service.get_user_cart(username)
    return jsonify(result)
@api.route("/api/apply_coupon", methods=["POST"])
def apply_coupon():
    data = request.json
    code = data.get("coupon")

    if not code:
        return jsonify({"success": False, "message": "Thiếu mã giảm giá."}), 400

    coupon = home_service.check_coupon(code)
    if not coupon:
        return jsonify({"success": False, "message": "Mã giảm giá không hợp lệ."}), 404

    return jsonify({"success": True, "message": "Áp dụng thành công!", "coupon": coupon})
