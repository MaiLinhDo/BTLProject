from flask import Flask
from dotenv import load_dotenv
from app.routes.home import api
from app.routes.login import login_api
from app.routes.loginfb import facebook_api
from app.routes.APIChat import apichat
from app.routes.sanpham import product_routes
from app.routes.danhmuc import danhmuc_routes
from app.routes.order_routes import order_routes
from app.routes.voucher import voucher_routes
from app.routes.user import user_routes
from app.routes.revenue import revenue_routes
from app.routes.banner import banner_routes
#from app.routes.phieunhap import phieunhap_routes
from flask_cors import CORS 
def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    # Đăng ký Blueprint
    app.register_blueprint(api)
    app.register_blueprint(login_api)
    app.register_blueprint(facebook_api)
    app.register_blueprint(apichat)
    app.register_blueprint(product_routes)
    app.register_blueprint(danhmuc_routes)
    app.register_blueprint(order_routes)
    app.register_blueprint(voucher_routes)
    app.register_blueprint(user_routes)
    app.register_blueprint(revenue_routes)
  #  app.register_blueprint(phieunhap_routes)
    app.register_blueprint(banner_routes)
    return app
