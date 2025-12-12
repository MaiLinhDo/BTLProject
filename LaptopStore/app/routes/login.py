from flask import Blueprint, request, jsonify
import requests
from urllib.parse import quote
from app.services.home_service import add_user_to_db

login_api = Blueprint('login_api', __name__)

# Cấu hình
client_id = "612988759993-1sbf3oa0uanaq6ckmcka0m25qvtk5c4e.apps.googleusercontent.com"
client_secret = "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"
redirect_uri = "http://localhost:59774/Home/GoogleLoginCallback"
token_endpoint = "https://oauth2.googleapis.com/token"
user_info_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"

# API Google Login: Trả về URL đăng nhập Google
@login_api.route('/api/google-login', methods=['GET'])
def google_login():
    authorization_endpoint = "https://accounts.google.com/o/oauth2/auth"
    # Encode redirect_uri để đảm bảo URL được gửi đúng cách
    encoded_redirect_uri = quote(redirect_uri, safe='')
    url = f"{authorization_endpoint}?response_type=code" + \
          f"&client_id={client_id}" + \
          f"&redirect_uri={encoded_redirect_uri}" + \
          f"&scope=email%20profile" + \
          f"&access_type=online" + \
          f"&prompt=select_account"
    print(f"🔍 Google Login URL: {url}")
    print(f"🔍 Redirect URI: {redirect_uri}")
    return jsonify({"redirect_url": url})

# API Google Callback: Xử lý mã xác thực và thêm người dùng
@login_api.route('/api/google-login-callback', methods=['GET'])
def google_login_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No authorization code provided"}), 400

    # Lấy access token từ Google
    token_data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    token_response = requests.post(token_endpoint, data=token_data)
    if token_response.status_code != 200:
        return jsonify({"error": "Failed to get access token"}), 500

    token_json = token_response.json()
    access_token = token_json.get("access_token")
    if not access_token:
        return jsonify({"error": "No access token received"}), 500

    # Lấy thông tin người dùng từ Google
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get(user_info_endpoint, headers=headers)
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
