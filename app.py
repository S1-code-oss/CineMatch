"""
app.py — CineMatch Flask entry point.
"""

from flask import Flask, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv

from auth            import auth_bp
from movies          import movies_bp
from ratings         import ratings_bp
from reviews         import reviews_bp
from watchlist       import watchlist_bp
from trending        import trending_bp
from profile         import profile_bp
from admin           import admin_bp
from admin_auth      import admin_auth_bp
from recommendations import recommendations_bp
from community       import community_bp

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"]   = False

CORS(app, supports_credentials=True)

app.register_blueprint(auth_bp,            url_prefix="/api")
app.register_blueprint(movies_bp,          url_prefix="/api")
app.register_blueprint(ratings_bp,         url_prefix="/api")
app.register_blueprint(reviews_bp,         url_prefix="/api")
app.register_blueprint(watchlist_bp,       url_prefix="/api")
app.register_blueprint(trending_bp,        url_prefix="/api")
app.register_blueprint(profile_bp,         url_prefix="/api")
app.register_blueprint(admin_bp,           url_prefix="/api")
app.register_blueprint(admin_auth_bp,      url_prefix="/api")
app.register_blueprint(recommendations_bp, url_prefix="/api")
app.register_blueprint(community_bp,       url_prefix="/api")

@app.route("/")
@app.route("/login")
def login_page():
    return send_from_directory(BASE_DIR, "cinematch-login.html")

@app.route("/browse")
def browse_page():
    return send_from_directory(BASE_DIR, "cinematch-browse.html")

@app.route("/profile")
def profile_page():
    return send_from_directory(BASE_DIR, "cinematch-profile.html")

@app.route("/dashboard")
def dashboard_page():
    return send_from_directory(BASE_DIR, "cinematch-dashboard.html")

@app.route("/awards")
def awards_page():
    return send_from_directory(BASE_DIR, "cinematch-awards.html")

@app.route("/recommendations")
def recommendations_page():
    return send_from_directory(BASE_DIR, "cinematch-recommendations.html")

@app.route("/cineblend")
def cineblend_page():
    return send_from_directory(BASE_DIR, "cinematch-cineblend.html")

@app.route("/admin/login")
def admin_login_page():
    return send_from_directory(BASE_DIR, "cinematch-admin-login.html")

@app.route("/admin/dashboard")
def admin_dashboard_page():
    return send_from_directory(BASE_DIR, "cinematch-admin.html")

if __name__ == "__main__":
    print("CineMatch backend running at http://localhost:5000")
    app.run(debug=True, port=5000)