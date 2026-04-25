"""
UC-12: Viewing Profile
Handles: GET  /api/profile/<username>
         GET  /api/profile/me
         GET  /api/profile/watchlist-privacy
         POST /api/profile/watchlist-privacy
         POST /api/profile/change-username
         POST /api/profile/change-password
         POST /api/profile/update-info
"""

import bcrypt
import re
from flask import Blueprint, jsonify, session, request
from db import get_connection

profile_bp = Blueprint("profile", __name__)


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _login_required():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in first."}), 401
    return None


def _fmt_date(value) -> str:
    if value is None:
        return "—"
    try:
        return value.strftime("%Y-%m-%d")
    except AttributeError:
        return str(value)[:10]


def _is_strong_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════════════
#  PROFILE QUERY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _get_user_by_username(cursor, username: str):
    cursor.execute(
        """
        SELECT UserID, Username, CreatedAt, Bio, Location
        FROM   Users
        WHERE  Username = ? AND IsActive = 1
        """,
        (username,)
    )
    return cursor.fetchone()


def _get_stats(cursor, user_id: int) -> dict:
    cursor.execute(
        """
        SELECT COUNT(*), ISNULL(AVG(CAST(RatingValue AS FLOAT)), 0)
        FROM   Ratings WHERE UserID = ?
        """,
        (user_id,)
    )
    row         = cursor.fetchone()
    total_rated = row[0]
    avg_rating  = round(row[1], 1)

    cursor.execute("SELECT COUNT(*) FROM Reviews WHERE UserID = ?", (user_id,))
    total_reviews = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT TOP 1 m.Genres
        FROM   Ratings r
        JOIN   VW_MoviesComplete m ON r.MovieID = m.MovieID
        WHERE  r.UserID = ? AND m.Genres IS NOT NULL
        GROUP  BY m.Genres ORDER BY COUNT(*) DESC
        """,
        (user_id,)
    )
    genre_row = cursor.fetchone()
    top_genre = genre_row[0].split(",")[0].strip() if genre_row else "—"

    cursor.execute(
        """
        SELECT TOP 1 (m.ReleaseYear / 10) * 10 AS Decade, COUNT(*) AS Cnt
        FROM   Ratings r
        JOIN   VW_MoviesComplete m ON r.MovieID = m.MovieID
        WHERE  r.UserID = ? AND m.ReleaseYear IS NOT NULL
        GROUP  BY (m.ReleaseYear / 10) * 10 ORDER BY Cnt DESC
        """,
        (user_id,)
    )
    decade_row = cursor.fetchone()
    fav_decade = f"{decade_row[0]}s" if decade_row else "—"

    cursor.execute("SELECT COUNT(*) FROM Watchlist WHERE UserID = ?", (user_id,))
    watchlist_count = cursor.fetchone()[0]

    return {
        "total_rated":     total_rated,
        "avg_rating":      avg_rating,
        "total_reviews":   total_reviews,
        "top_genre":       top_genre,
        "fav_decade":      fav_decade,
        "watchlist_count": watchlist_count,
    }


def _get_rating_distribution(cursor, user_id: int) -> dict:
    cursor.execute(
        """
        SELECT CAST(RatingValue AS INT) AS Stars, COUNT(*) AS Cnt
        FROM   Ratings WHERE UserID = ?
        GROUP  BY CAST(RatingValue AS INT) ORDER BY Stars
        """,
        (user_id,)
    )
    raw = {str(row[0]): row[1] for row in cursor.fetchall()}
    return {str(i): raw.get(str(i), 0) for i in range(1, 6)}


def _get_genre_breakdown(cursor, user_id: int) -> list:
    cursor.execute(
        """
        SELECT m.Genres FROM Ratings r
        JOIN   VW_MoviesComplete m ON r.MovieID = m.MovieID
        WHERE  r.UserID = ? AND m.Genres IS NOT NULL
        """,
        (user_id,)
    )
    genre_counts = {}
    for (genres_str,) in cursor.fetchall():
        for g in genres_str.split(","):
            g = g.strip()
            if g:
                genre_counts[g] = genre_counts.get(g, 0) + 1
    total         = sum(genre_counts.values()) or 1
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return [{"genre": g, "count": c, "percent": round(c / total * 100, 1)} for g, c in sorted_genres]


def _get_decade_breakdown(cursor, user_id: int) -> list:
    cursor.execute(
        """
        SELECT (m.ReleaseYear / 10) * 10 AS Decade, COUNT(*) AS Cnt
        FROM   Ratings r
        JOIN   VW_MoviesComplete m ON r.MovieID = m.MovieID
        WHERE  r.UserID = ? AND m.ReleaseYear IS NOT NULL
        GROUP  BY (m.ReleaseYear / 10) * 10 ORDER BY Decade
        """,
        (user_id,)
    )
    return [{"decade": f"{row[0]}s", "count": row[1]} for row in cursor.fetchall()]


def _get_recent_activity(cursor, user_id: int) -> list:
    cursor.execute(
        """
        SELECT TOP 5 m.Title, r.RatingValue, r.RatedAt
        FROM   Ratings r
        JOIN   VW_MoviesComplete m ON r.MovieID = m.MovieID
        WHERE  r.UserID = ? ORDER BY r.RatedAt DESC
        """,
        (user_id,)
    )
    ratings = [{"type": "rating", "movie": row[0], "rating": int(row[1]), "created_at": _fmt_date(row[2])} for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT TOP 5 m.Title, rv.CreatedAt
        FROM   Reviews rv
        JOIN   VW_MoviesComplete m ON rv.MovieID = m.MovieID
        WHERE  rv.UserID = ? ORDER BY rv.CreatedAt DESC
        """,
        (user_id,)
    )
    reviews = [{"type": "review", "movie": row[0], "rating": None, "created_at": _fmt_date(row[1])} for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT TOP 5 m.Title, w.AddedAt
        FROM   Watchlist w
        JOIN   VW_MoviesComplete m ON w.MovieID = m.MovieID
        WHERE  w.UserID = ? ORDER BY w.AddedAt DESC
        """,
        (user_id,)
    )
    watchlist = [{"type": "watchlist", "movie": row[0], "rating": None, "created_at": _fmt_date(row[1])} for row in cursor.fetchall()]

    combined = ratings + reviews + watchlist
    combined.sort(key=lambda x: x["created_at"], reverse=True)
    return combined[:10]


def _get_public_reviews(cursor, user_id: int) -> list:
    cursor.execute(
        """
        SELECT m.Title, m.Genres, r.RatingValue, rv.ReviewText, rv.CreatedAt
        FROM   Reviews rv
        JOIN   VW_MoviesComplete m ON rv.MovieID = m.MovieID
        JOIN   Ratings r           ON r.RatingID = rv.RatingID
        WHERE  rv.UserID = ? AND rv.IsPublic = 1
        ORDER  BY rv.CreatedAt DESC
        """,
        (user_id,)
    )
    return [
        {"movie": row[0], "genres": row[1] or "", "rating": float(row[2]), "review_text": row[3], "created_at": _fmt_date(row[4])}
        for row in cursor.fetchall()
    ]


def _get_watchlist(cursor, user_id: int, viewer_id: int) -> tuple:
    cursor.execute("SELECT WatchlistPublic FROM Users WHERE UserID = ?", (user_id,))
    pref_row  = cursor.fetchone()
    is_public = bool(pref_row and pref_row[0])
    is_owner  = (viewer_id == user_id)

    if not is_owner and not is_public:
        return [], False

    cursor.execute(
        """
        SELECT m.Title, m.Genres, m.ReleaseYear, m.Runtime, m.AverageRating, w.AddedAt
        FROM   Watchlist w
        JOIN   VW_MoviesComplete m ON w.MovieID = m.MovieID
        WHERE  w.UserID = ? ORDER BY w.AddedAt DESC
        """,
        (user_id,)
    )
    items = [
        {"title": row[0], "genres": row[1] or "", "release_year": row[2], "runtime": row[3],
         "avg_rating": round(float(row[4]) if row[4] else 0.0, 1), "added_at": _fmt_date(row[5])}
        for row in cursor.fetchall()
    ]
    return items, True


def _get_awards(cursor, user_id: int) -> list:
    from datetime import date
    awards = []
    today = date.today()
    y, m = today.year, today.month
    for _ in range(12):
        cursor.execute("""SELECT TOP 1 u.UserID, COUNT(*) AS ReviewCount FROM Reviews rv JOIN Users u ON rv.UserID = u.UserID WHERE YEAR(rv.CreatedAt) = ? AND MONTH(rv.CreatedAt) = ? GROUP BY u.UserID ORDER BY COUNT(*) DESC""", (y, m))
        row = cursor.fetchone()
        if row and row[0] == user_id:
            awards.append({"category": "Most Active Reviewer", "month": date(y, m, 1).strftime("%B %Y"), "value": f"{row[1]} review{'s' if row[1] != 1 else ''}", "icon": "✍️"})
        m -= 1
        if m == 0: m = 12; y -= 1
    return awards


# ═══════════════════════════════════════════════════════════════════════════════
#  SETTINGS ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@profile_bp.route("/profile/watchlist-privacy", methods=["GET"])
def get_watchlist_privacy():
    guard = _login_required()
    if guard:
        return guard
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT WatchlistPublic FROM Users WHERE UserID = ?", (session["user_id"],))
        row = cursor.fetchone()
        conn.close()
        return jsonify({"success": True, "watchlist_public": bool(row and row[0])}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@profile_bp.route("/profile/watchlist-privacy", methods=["POST"])
def toggle_watchlist_privacy():
    guard = _login_required()
    if guard:
        return guard
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT WatchlistPublic FROM Users WHERE UserID = ?", (session["user_id"],))
        row       = cursor.fetchone()
        new_value = 0 if (row and row[0]) else 1
        cursor.execute("UPDATE Users SET WatchlistPublic = ? WHERE UserID = ?", (new_value, session["user_id"]))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "watchlist_public": bool(new_value)}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@profile_bp.route("/profile/change-username", methods=["POST"])
def change_username():
    """Change username with old password confirmation."""
    guard = _login_required()
    if guard:
        return guard

    data         = request.get_json()
    new_username = (data.get("new_username") or "").strip()
    password     = data.get("password") or ""

    if not new_username:
        return jsonify({"success": False, "message": "New username is required."}), 400
    if len(new_username) < 3 or len(new_username) > 50:
        return jsonify({"success": False, "message": "Username must be 3–50 characters."}), 400
    if not password:
        return jsonify({"success": False, "message": "Password confirmation is required."}), 400

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # Verify password
        cursor.execute("SELECT PasswordHash FROM Users WHERE UserID = ?", (session["user_id"],))
        row = cursor.fetchone()
        if not row or not bcrypt.checkpw(password.encode("utf-8"), row[0].encode("utf-8")):
            conn.close()
            return jsonify({"success": False, "message": "Incorrect password."}), 401

        # Check username not taken
        cursor.execute("SELECT 1 FROM Users WHERE Username = ? AND UserID != ?", (new_username, session["user_id"]))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Username is already taken."}), 409

        cursor.execute("UPDATE Users SET Username = ? WHERE UserID = ?", (new_username, session["user_id"]))
        conn.commit()
        conn.close()

        # Update session
        session["username"] = new_username
        return jsonify({"success": True, "message": "Username updated successfully.", "new_username": new_username}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@profile_bp.route("/profile/change-password", methods=["POST"])
def change_password():
    """Change password with old password confirmation."""
    guard = _login_required()
    if guard:
        return guard

    data         = request.get_json()
    old_password = data.get("old_password") or ""
    new_password = data.get("new_password") or ""
    confirm      = data.get("confirm_password") or ""

    if not old_password:
        return jsonify({"success": False, "message": "Current password is required."}), 400
    if not new_password:
        return jsonify({"success": False, "message": "New password is required."}), 400
    if new_password != confirm:
        return jsonify({"success": False, "message": "New passwords do not match."}), 400
    if not _is_strong_password(new_password):
        return jsonify({"success": False, "message": "Password must be 8+ chars with uppercase, lowercase and a digit."}), 400
    if old_password == new_password:
        return jsonify({"success": False, "message": "New password must be different from current password."}), 400

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT PasswordHash FROM Users WHERE UserID = ?", (session["user_id"],))
        row = cursor.fetchone()
        if not row or not bcrypt.checkpw(old_password.encode("utf-8"), row[0].encode("utf-8")):
            conn.close()
            return jsonify({"success": False, "message": "Current password is incorrect."}), 401

        new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cursor.execute("UPDATE Users SET PasswordHash = ? WHERE UserID = ?", (new_hash, session["user_id"]))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Password changed successfully."}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@profile_bp.route("/profile/update-info", methods=["POST"])
def update_info():
    """Update Bio and Location."""
    guard = _login_required()
    if guard:
        return guard

    data     = request.get_json()
    bio      = (data.get("bio") or "").strip()[:300]
    location = (data.get("location") or "").strip()[:100]

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Users SET Bio = ?, Location = ? WHERE UserID = ?",
            (bio or None, location or None, session["user_id"])
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Profile updated successfully."}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@profile_bp.route("/profile/settings-data", methods=["GET"])
def get_settings_data():
    """Get current user data for pre-filling settings form."""
    guard = _login_required()
    if guard:
        return guard
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Username, Bio, Location, WatchlistPublic FROM Users WHERE UserID = ?",
            (session["user_id"],)
        )
        row = cursor.fetchone()
        conn.close()
        return jsonify({
            "success":          True,
            "username":         row[0],
            "bio":              row[1] or "",
            "location":         row[2] or "",
            "watchlist_public": bool(row[3]),
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
#  PROFILE ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@profile_bp.route("/profile/me", methods=["GET"])
def get_own_profile():
    guard = _login_required()
    if guard:
        return guard
    return get_profile(session["username"])


@profile_bp.route("/profile/<username>", methods=["GET"])
def get_profile(username: str):
    guard = _login_required()
    if guard:
        return guard

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        user_row = _get_user_by_username(cursor, username)
        if not user_row:
            conn.close()
            return jsonify({"success": False, "message": "User not found."}), 404

        user_id, username_db, created_at, bio, location = user_row
        viewer_id = session.get("user_id")

        stats        = _get_stats(cursor, user_id)
        distribution = _get_rating_distribution(cursor, user_id)
        genres       = _get_genre_breakdown(cursor, user_id)
        decades      = _get_decade_breakdown(cursor, user_id)
        reviews      = _get_public_reviews(cursor, user_id)
        watchlist, watchlist_visible = _get_watchlist(cursor, user_id, viewer_id)
        awards       = _get_awards(cursor, user_id)

        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "username":            username_db,
                "member_since":        _fmt_date(created_at),
                "bio":                 bio or "",
                "location":            location or "",
                "is_own_profile":      viewer_id == user_id,
                "stats":               stats,
                "rating_distribution": distribution,
                "genre_breakdown":     genres,
                "decade_breakdown":    decades,
                "reviews":             reviews,
                "watchlist":           watchlist,
                "watchlist_public":    watchlist_visible,
                "awards":              awards,
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500