"""
UC-01: Logging In / Registering
Handles: login, register, logout
"""

from flask import Blueprint, request, jsonify, session
import bcrypt
import re
from db import get_connection

auth_bp = Blueprint("auth", __name__)


def _is_valid_email(email: str) -> bool:
    #email format check
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$"
    return bool(re.match(pattern, email))

def _is_strong_password(password: str) -> bool:
    """
    Password must be at least 8 characters and contain at least one
    uppercase letter, one lowercase letter, and one digit.
    """
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True

# register

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    username         = (data.get("username") or "").strip()
    email            = (data.get("email") or "").strip().lower()
    password         = data.get("password") or ""
    confirm_password = data.get("confirm_password") or ""

    # input validation
    if not username:
        return jsonify({"success": False, "message": "Username is required."}), 400
    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400
    if not password:
        return jsonify({"success": False, "message": "Password is required."}), 400

    # format validation
    if len(username) < 3 or len(username) > 50:
        return jsonify({"success": False, "message": "Username must be 3–50 characters."}), 400

    if not _is_valid_email(email):
        return jsonify({"success": False, "message": "Invalid email format."}), 400

    if not _is_strong_password(password):
        return jsonify({
            "success": False,
            "message": "Password must be at least 8 characters and include uppercase, lowercase, and a digit."
        }), 400

    if password != confirm_password:
        return jsonify({"success": False, "message": "Passwords do not match."}), 400

    # db checks uniqueness 
    # Using parameterised queries everywhere so zero SQL injection risk
    # The ? is filled by pyodbc, never by string concatenation
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM Users WHERE Username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Username is already taken."}), 409

        cursor.execute("SELECT 1 FROM Users WHERE Email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "An account with this email already exists."}), 409

        # Hash password 
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Role defaults to 'User' in the DB, IsActive defaults to 1.
        # The TR_Users_CreatePreferences trigger fires automatically here,
        # Note: OUTPUT clause causes SQLFetch sequence errors with pyodbc+triggers,
        # so use INSERT then SELECT separately
        cursor.execute(
            "INSERT INTO Users (Username, Email, PasswordHash) VALUES (?, ?, ?)",
            (username, email, hashed)
        )
        conn.commit()

        cursor.execute(
            "SELECT UserID, Role FROM Users WHERE Username = ?",
            (username,)
        )
        row     = cursor.fetchone()
        user_id = row[0]
        role    = row[1]

        # update lastlogin
        cursor.execute(
            "UPDATE Users SET LastLogin = GETDATE() WHERE UserID = ?",
            (user_id,)
        )
        conn.commit()
        conn.close()

        # creating serverside session (auto-login) 
        session["user_id"]  = user_id
        session["username"] = username
        session["role"]     = role

        return jsonify({
            "success":  True,
            "message":  "Account created successfully.",
            "user_id":  user_id,
            "username": username,
            "role":     role
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# login
@auth_bp.route("/login", methods=["POST"])
def login():
   
    data = request.get_json()

    identifier = (data.get("identifier") or "").strip()   # both username or mail
    password   = data.get("password") or ""

    # Presence check 
    if not identifier:
        return jsonify({"success": False, "message": "Please enter your username or email."}), 400
    if not password:
        return jsonify({"success": False, "message": "Please enter your password."}), 400

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT UserID, Username, PasswordHash, Role, IsActive
            FROM   Users
            WHERE  Username = ? OR Email = ?
            """,
            (identifier, identifier.lower())
        )
        row = cursor.fetchone()

        # "invalid credentials" 
        if row is None:
            conn.close()
            return jsonify({"success": False, "message": "Invalid username/email or password."}), 401

        user_id, username, password_hash, role, is_active = row

        # Account active check
        if not is_active:
            conn.close()
            return jsonify({"success": False, "message": "This account has been deactivated."}), 403

        if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
            conn.close()
            return jsonify({"success": False, "message": "Invalid username/email or password."}), 401

        # update LastLogin timestamp
        cursor.execute(
            "UPDATE Users SET LastLogin = GETDATE() WHERE UserID = ?",
            (user_id,)
        )
        conn.commit()
        conn.close()

        #Create session
        session["user_id"]  = user_id
        session["username"] = username
        session["role"]     = role

        #Tell frontend where to redirect 
        redirect = "/admin/dashboard" if role == "Admin" else "/dashboard"

        return jsonify({
            "success":  True,
            "message":  "Login successful.",
            "user_id":  user_id,
            "username": username,
            "role":     role,
            "redirect": redirect
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


#logout

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out."}), 200


#session checl used by other pages to know if user is logged in

@auth_bp.route("/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"logged_in": False}), 200
    return jsonify({
        "logged_in": True,
        "user_id":   session["user_id"],
        "username":  session["username"],
        "role":      session["role"]
    }), 200