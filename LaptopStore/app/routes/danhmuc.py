from flask import Blueprint, request, jsonify
import app.services.danhmuc_service as danhmuc_service

danhmuc_routes = Blueprint("danhmuc_routes", __name__)

# Route lấy tất cả danh mục sản phẩm
@danhmuc_routes.route('/api/get_categories', methods=['GET'])
def get_categories():
    # Gọi service để lấy danh sách danh mục sản phẩm
    result = danhmuc_service.get_all_categories()
    return jsonify(result)
@danhmuc_routes.route('/api/get_category_by_id/<int:id>', methods=['GET'])
def get_category_by_id(id):
    try:
        result = danhmuc_service.get_category_by_id(id)
        if "success" in result and not result["success"]:
            return jsonify(result), 404
        return jsonify(result)
    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": str(e)}), 500


@danhmuc_routes.route("/api/hang", methods=["GET"])
def get_all():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 5))
    search = request.args.get("search")
    result = danhmuc_service.get_categories(page, page_size, search)
    return jsonify(result)

@danhmuc_routes.route("/api/hang", methods=["POST"])
def add():
    data = request.get_json()
    result = danhmuc_service.add_category(data)
    return jsonify(result)

@danhmuc_routes.route("/api/hang", methods=["PUT"])
def update():
    data = request.get_json()
    result = danhmuc_service.update_category(data)
    return jsonify(result)

@danhmuc_routes.route("/api/hang/<int:ma_hang>/toggle", methods=["PUT"])
def toggle(ma_hang):
    result = danhmuc_service.toggle_status(ma_hang)
    return jsonify(result)

@danhmuc_routes.route('/api/get_danhmuc_by_id/<int:id>', methods=['GET'])
def get_danhmuc_by_id(id):
    try:
        result = danhmuc_service.get_danhmuc_by_id(id)
        if "success" in result and not result["success"]:
            return jsonify(result), 404
        return jsonify(result)
    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": str(e)}), 500


@danhmuc_routes.route("/api/danhmuc", methods=["GET"])
def get_all_danhmuc():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 5))
    search = request.args.get("search")
    result = danhmuc_service.get_danhmuc(page, page_size, search)
    return jsonify(result)

@danhmuc_routes.route("/api/danhmuc", methods=["POST"])
def add_danhmuc():
    data = request.get_json()
    result = danhmuc_service.add_danhmuc(data)
    return jsonify(result)

@danhmuc_routes.route("/api/danhmuc", methods=["PUT"])
def update_danhmuc():
    data = request.get_json()
    result = danhmuc_service.update_danhmuc(data)
    return jsonify(result)

@danhmuc_routes.route("/api/danhmuc/<int:ma_dm>/toggle", methods=["PUT"])
def toggle_danhmuc(ma_dm):
    result = danhmuc_service.toggle_status_danhmuc(ma_dm)
    return jsonify(result)