from flask import Blueprint, request, jsonify
import app.services.user_service as user_service

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/api/check_username', methods=['GET'])
def get_user():
    username = request.args.get('username')
    user = user_service.get_user_by_username(username)
    
    if user:
        return jsonify({
            "MaTaiKhoan": user.MaTaiKhoan,
            "Username": user.Username,
            "HoTen": user.HoTen,
            "DiaChi": user.DiaChi,
            "SoDienThoai": user.SoDienThoai,
            "Email": user.Email,
            "TrangThai": user.TrangThai
        })
  
    return jsonify({"error": "User not found"}), 404

@user_routes.route("/api/khachhang", methods=["GET"])
def get_all_khachhang():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 5))
    search = request.args.get("search")
    result = user_service.get_khachhang(page, page_size, search)
    return jsonify(result)

@user_routes.route("/api/capnhat_trangthai_taikhoan/<int:id>/toggle", methods=["PUT"])
def toggle_trangthai(id):
    result = user_service.toggle_trangthai_khachhang(id)
    return jsonify(result)

@user_routes.route('/api/doi-mat-khau', methods=['POST'])
def doi_mat_khau_route():
    data = request.json
    result = user_service.doi_mat_khau_service(
        username=data.get('username'),
        matkhau_cu=data.get('matkhaucu'),
        matkhau_moi=data.get('matkhaumoi'),
        xacnhan_mk=data.get('xacnhanmk')
    )
    return jsonify(result)
@user_routes.route("/api/khoa-tai-khoan/<int:id>", methods=["PUT"])
def khoa_tai_khoan(id):
    result = user_service.update_trang_thai_tai_khoan(id, False)
    return jsonify(result)

@user_routes.route("/api/mo-khoa-tai-khoan/<int:id>", methods=["PUT"])
def mo_khoa_tai_khoan(id):
    result = user_service.update_trang_thai_tai_khoan(id, True)
    return jsonify(result)
@user_routes.route('/api/get_all_nhanvien', methods=['GET'])
def get_all_nhanvien():
    try:
        page = request.args.get('page', type=int, default=1)
        page_size = request.args.get('pageSize', type=int, default=5)
        search_term = request.args.get('search', type=str, default='')

        result = user_service.get_all_nhanvien_service(page, page_size, search_term)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
@user_routes.route('/api/nhanvien', methods=['POST'])
def add_nhanvien():
    try:
        data = request.get_json()
        result = user_service.them_nhan_vien(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


