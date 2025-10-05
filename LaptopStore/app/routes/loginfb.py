from flask import Blueprint, request, jsonify, redirect, url_for
import requests
from app.services.home_service import add_user_to_db

facebook_api = Blueprint('facebook_api', __name__)



# API Facebook Login: Trả về URL đăng nhập Facebook
@facebook_api.route('/api/facebook-login', methods=['GET'])
def facebook_login():
    url = f"{authorization_endpoint}?client_id={client_id}" + \
          f"&redirect_uri={redirect_uri}" + \
          f"&scope=email,public_profile" + \
          f"&response_type=code" + \
          f"&auth_type=rerequest"
    return jsonify({"url": url})


# API Facebook Callback: Xử lý mã xác thực và thêm người dùng
@facebook_api.route('/api/facebook-login-callback', methods=['GET'])
def facebook_login_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No authorization code provided"}), 400

    # Lấy access token từ Facebook
    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": code
    }

    token_response = requests.get(token_endpoint, params=token_data)
    if token_response.status_code != 200:
        return jsonify({"error": "Failed to get access token"}), 500

    token_json = token_response.json()
    access_token = token_json.get("access_token")
    if not access_token:
        return jsonify({"error": "No access token received"}), 500

    # Lấy thông tin người dùng từ Facebook
    user_response = requests.get(user_info_endpoint, params={"access_token": access_token})
    if user_response.status_code != 200:
        return jsonify({"error": "Failed to get user info"}), 500

    user_json = user_response.json()
    email = user_json.get("email")
    full_name = user_json.get("name")

    if not email:
        return jsonify({"error": "No email found"}), 500

    # Thêm người dùng vào database thông qua service
    add_user_to_db(email, full_name)

    return jsonify({
        "email": email,
        "name": full_name
    })
