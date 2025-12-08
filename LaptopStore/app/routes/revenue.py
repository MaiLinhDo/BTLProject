from flask import Blueprint, jsonify
from app.services.revenue_service import get_revenue_by_product_and_category

revenue_routes = Blueprint("revenue_routes", __name__)

@revenue_routes.route("/api/revenue/today", methods=["GET"])
def get_revenue_today():
    data = get_revenue_by_product_and_category()
    return jsonify({
        "success": True,
        "revenueByProduct": data["revenueByProduct"],
        "revenueByCategory": data["revenueByCategory"]
    })
