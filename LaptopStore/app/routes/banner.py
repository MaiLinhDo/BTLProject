from flask import Blueprint, request, jsonify
import app.services.banner_service as banner_service

banner_routes = Blueprint("banner", __name__)

@banner_routes.route("/api/get_all_banners", methods=["GET"])
def get_all_banners():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 5))
    search = request.args.get("search")
    return jsonify(banner_service.get_all_banners(page, page_size, search))

@banner_routes.route("/api/banners", methods=["POST"])
def add_banner():
    data = request.json
    return jsonify(banner_service.add_banner(data))

@banner_routes.route("/api/banners", methods=["PUT"])
def update_banner():
    data = request.json
    return jsonify(banner_service.update_banner(data))
@banner_routes.route("/api/banners/<int:ma_banner>", methods=["DELETE"])
def delete_banner(ma_banner):
    return jsonify(banner_service.delete_banner(ma_banner))


@banner_routes.route("/api/get_banner_by_id/<int:ma_banner>", methods=["GET"])
def get_banner_by_id(ma_banner):
    return jsonify(banner_service.get_banner_by_id(ma_banner))
