from flask import Flask, send_from_directory, redirect
from flask_cors import CORS
import os
from dotenv import load_dotenv
from auth      import auth_bp
from movies    import movies_bp
from ratings   import ratings_bp
from reviews   import reviews_bp
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

# secret key for sessions
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")
CORS(app, supports_credentials=True)

# obeys open close when adding a new use case = new blueprint
app.register_blueprint(auth_bp,       url_prefix="/api")
app.register_blueprint(movies_bp,     url_prefix="/api")
app.register_blueprint(ratings_bp,    url_prefix="/api")
app.register_blueprint(reviews_bp,    url_prefix="/api")
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

@app.route("/cineblend")
def cineblend_page():
    return send_from_directory(BASE_DIR, "cinematch-cineblend.html")

#dashboard and admin/dashboard both redirect to browse for now
@app.route("/dashboard")
def dashboard_page():
    return redirect("/browse")

@app.route("/admin/dashboard")
def admin_dashboard_page():
    return redirect("/browse")


if __name__ == "__main__":
    print("CineMatch backend running at http://localhost:5000")
    app.run(debug=True, port=5000)
