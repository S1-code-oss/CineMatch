"""
admin.py — Admin Blueprint: user restriction & movie library management.

SOLID:
  SRP  — two concerns (users, movies) but both are admin-only CRUD operations.
         Each concern has its own clearly labelled section.
         Authentication lives in admin_auth.py, not here.
  OCP  — adding a new admin feature = new route; existing routes unchanged.
  LSP  — N/A (no inheritance).
  ISP  — _require_admin() is the single guard; endpoints don't duplicate the check.
  DIP  — DB via get_connection(); no pyodbc details in business logic.

CRT:
  Cohesion   — every function either manages users or manages movies for admins.
  Coupling   — no imports from any user-facing blueprint.
  Readability — _require_admin() extracted once; col_map in update_movie keeps
                SQL generation clean and injection-free.

Security:
  _require_admin() checks for admin_id in session (set only by admin_auth.py).
  A regular user session (user_id) can never contain admin_id.
"""

from flask import Blueprint, request, jsonify, session
from db import get_connection

admin_bp = Blueprint("admin", __name__)


# ── Auth guard ─────────────────────────────────────────────────────────────────

def _require_admin():
    """
    Only sessions created by /api/admin/login carry admin_id.
    Regular user sessions never do, so this guard is privilege-escalation-proof.
    Returns a JSON 401 tuple on failure, or None on success.
    """
    if "admin_id" not in session:
        return jsonify({"success": False, "message": "Admin login required."}), 401
    return None


# ── USER MANAGEMENT ────────────────────────────────────────────────────────────

@admin_bp.route("/admin/users", methods=["GET"])
def list_users():
    """Return all registered users (excluding admin accounts) with status info."""
    err = _require_admin()
    if err:
        return err
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT UserID, Username, Email, Role, IsActive, CreatedAt, LastLogin
            FROM   Users
            ORDER  BY CreatedAt DESC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        users = [
            {
                "user_id":    r.UserID,
                "username":   r.Username,
                "email":      r.Email,
                "role":       r.Role,
                "is_active":  bool(r.IsActive),
                "created_at": r.CreatedAt.strftime("%Y-%m-%d") if r.CreatedAt else "",
                "last_login": r.LastLogin.strftime("%Y-%m-%d") if r.LastLogin else "Never",
            }
            for r in rows
        ]
        return jsonify({"success": True, "data": users}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/admin/users/<int:user_id>/restrict", methods=["PATCH"])
def toggle_user_restriction(user_id: int):
    """
    Toggle IsActive for a non-admin user.
    Guards:
      - Cannot restrict yourself.
      - Cannot restrict another admin.
    """
    err = _require_admin()
    if err:
        return err

    # SRP guard: admins cannot self-restrict via this endpoint
    if user_id == session.get("admin_id"):
        return jsonify({"success": False, "message": "Cannot restrict your own account."}), 400

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT IsActive, Role FROM Users WHERE UserID = ?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            conn.close()
            return jsonify({"success": False, "message": "User not found."}), 404

        if row.Role == "Admin":
            conn.close()
            return jsonify({"success": False, "message": "Cannot restrict another admin."}), 403

        new_status = 0 if row.IsActive else 1
        cursor.execute(
            "UPDATE Users SET IsActive = ? WHERE UserID = ?", (new_status, user_id)
        )
        conn.commit()
        conn.close()

        action = "unrestricted" if new_status else "restricted"
        return jsonify({
            "success":   True,
            "message":   f"User {action}.",
            "is_active": bool(new_status),
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ── MOVIE LIBRARY MANAGEMENT ───────────────────────────────────────────────────

@admin_bp.route("/admin/movies", methods=["GET"])
def list_all_movies():
    """Return ALL movies including unapproved ones (admin-only view)."""
    err = _require_admin()
    if err:
        return err
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT MovieID, Title, ReleaseYear, Runtime, Description,
                   PosterURL, TrailerURL, Director, Cast,
                   AverageRating, TotalRatings, Genres, Platforms, IsApproved
            FROM   VW_MoviesComplete
            ORDER  BY MovieID DESC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        movies = [
            {
                "movie_id":       r.MovieID,
                "title":          r.Title,
                "release_year":   r.ReleaseYear,
                "runtime":        r.Runtime,
                "description":    r.Description,
                "poster_url":     r.PosterURL  or "",
                "trailer_url":    r.TrailerURL or "",
                "director":       r.Director   or "",
                "cast":           r.Cast       or "",
                "average_rating": float(r.AverageRating) if r.AverageRating else 0.0,
                "total_ratings":  r.TotalRatings or 0,
                "genres":         r.Genres    or "",
                "platforms":      r.Platforms or "",
                "is_approved":    bool(r.IsApproved),
            }
            for r in rows
        ]
        return jsonify({"success": True, "data": movies}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/admin/movies", methods=["POST"])
def add_movie():
    """
    Add a new movie to the library (auto-approved).
    Required: title, release_year.
    Optional: runtime, description, poster_url, trailer_url, director, cast.
    """
    err = _require_admin()
    if err:
        return err

    data = request.get_json() or {}

    title        = (data.get("title")       or "").strip()
    release_year = data.get("release_year")
    runtime      = data.get("runtime")
    description  = (data.get("description") or "").strip()
    poster_url   = (data.get("poster_url")  or "").strip()
    trailer_url  = (data.get("trailer_url") or "").strip()
    director     = (data.get("director")    or "").strip()
    cast         = (data.get("cast")        or "").strip()

    if not title:
        return jsonify({"success": False, "message": "Title is required."}), 400
    if not release_year:
        return jsonify({"success": False, "message": "Release year is required."}), 400

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Movies
                (Title, ReleaseYear, Runtime, Description,
                 PosterURL, TrailerURL, Director, Cast, IsApproved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                title,
                release_year,
                runtime     or None,
                description or None,
                poster_url  or None,
                trailer_url or None,
                director    or None,
                cast        or None,
            )
        )
        conn.commit()

        # Retrieve the new ID (OUTPUT clause causes pyodbc trigger errors)
        cursor.execute(
            "SELECT TOP 1 MovieID FROM Movies WHERE Title = ? ORDER BY MovieID DESC",
            (title,)
        )
        new_id = cursor.fetchone()[0]
        conn.close()

        return jsonify({
            "success":  True,
            "message":  "Movie added.",
            "movie_id": new_id,
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/admin/movies/<int:movie_id>", methods=["PATCH"])
def update_movie(movie_id: int):
    """
    Update editable fields of a movie.
    Uses a whitelist (col_map) to prevent arbitrary column injection —
    only allowed keys are translated to actual column names.
    """
    err = _require_admin()
    if err:
        return err

    data = request.get_json() or {}

    # OCP / Security: whitelist — unknown keys are silently ignored
    col_map = {
        "title":        "Title",
        "release_year": "ReleaseYear",
        "runtime":      "Runtime",
        "description":  "Description",
        "poster_url":   "PosterURL",
        "trailer_url":  "TrailerURL",
        "director":     "Director",
        "cast":         "Cast",
    }
    updates = {k: v for k, v in data.items() if k in col_map}

    if not updates:
        return jsonify({"success": False, "message": "No valid fields to update."}), 400

    set_clause = ", ".join(f"{col_map[k]} = ?" for k in updates)
    params     = list(updates.values()) + [movie_id]

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE Movies SET {set_clause} WHERE MovieID = ?", params
        )
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "message": "Movie not found."}), 404
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Movie updated."}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/admin/movies/<int:movie_id>", methods=["DELETE"])
def delete_movie(movie_id: int):
    """Permanently delete a movie and all its related ratings/reviews (via DB cascade)."""
    err = _require_admin()
    if err:
        return err
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Movies WHERE MovieID = ?", (movie_id,))
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "message": "Movie not found."}), 404
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Movie deleted."}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/admin/movies/<int:movie_id>/approve", methods=["PATCH"])
def toggle_approval(movie_id: int):
    """Toggle IsApproved on a movie (approve ↔ unapprove)."""
    err = _require_admin()
    if err:
        return err
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT IsApproved FROM Movies WHERE MovieID = ?", (movie_id,))
        row = cursor.fetchone()
        if row is None:
            conn.close()
            return jsonify({"success": False, "message": "Movie not found."}), 404

        new_val = 0 if row[0] else 1
        cursor.execute(
            "UPDATE Movies SET IsApproved = ? WHERE MovieID = ?", (new_val, movie_id)
        )
        conn.commit()
        conn.close()

        status = "approved" if new_val else "unapproved"
        return jsonify({
            "success":     True,
            "message":     f"Movie {status}.",
            "is_approved": bool(new_val),
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ── ADMIN STATS ────────────────────────────────────────────────────────────────

@admin_bp.route("/admin/stats", methods=["GET"])
def admin_stats():
    """Dashboard summary counts: total users, restricted, total movies, pending approval."""
    err = _require_admin()
    if err:
        return err
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM Users WHERE Role    = 'User') AS total_users,
                (SELECT COUNT(*) FROM Users WHERE IsActive = 0)     AS restricted_users,
                (SELECT COUNT(*) FROM Movies)                       AS total_movies,
                (SELECT COUNT(*) FROM Movies WHERE IsApproved = 0)  AS pending_movies
            """
        )
        r = cursor.fetchone()
        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "total_users":      r[0],
                "restricted_users": r[1],
                "total_movies":     r[2],
                "pending_movies":   r[3],
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500