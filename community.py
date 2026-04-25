"""
community.py  UC-13: Community Awards

UC-13 Awards:
  Awards are computed on-the-fly from the current month's data.
  Four categories: Top Rated Movie, Most Active Reviewer,
  Most Watched Movie, Genre of the Month.
  Archive: previous months pulled from CommunityAwards table if populated,
  otherwise computed live for the last 6 months.

SOLID:
  SRP  — two related community features; each has its own route section.
  OCP  — new award categories = new query in _compute_awards(), no other changes.
  DIP  — DB via get_connection() only.
CRT:
  Cohesion — all functions relate to community/social features.
  Coupling — no imports from other blueprints.
"""

from flask import Blueprint, jsonify, session, request
from db import get_connection

community_bp = Blueprint("community", __name__)


def _login_required():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in first."}), 401
    return None


# ══════════════════════════════════════════════════════════════════════════════
# UC-09: CINE-COMPATIBILITY
# ══════════════════════════════════════════════════════════════════════════════

def _genre_vector(cursor, user_id: int) -> dict:
    """
    Returns {genre: percentage} — normalised so all values sum to 100.
    This lets us compare users with different rating volumes fairly.
    """
    cursor.execute(
        """
        SELECT m.Genres, r.RatingValue
        FROM   Ratings r
        JOIN   VW_MoviesComplete m ON r.MovieID = m.MovieID
        WHERE  r.UserID = ? AND m.Genres IS NOT NULL
        """,
        (user_id,)
    )
    rows = cursor.fetchall()

    raw = {}
    for genres_str, rating in rows:
        for genre in genres_str.split(","):
            genre = genre.strip()
            if genre:
                raw[genre] = raw.get(genre, 0.0) + float(rating)

    total = sum(raw.values()) or 1
    return {g: round(s / total * 100, 2) for g, s in raw.items()}


def _compatibility_score(v1: dict, v2: dict) -> float:
    """
    Overlap coefficient: sum of min(pct_u1, pct_u2) across shared genres.
    Returns 0–100.
    """
    all_genres = set(v1.keys()) | set(v2.keys())
    overlap    = sum(min(v1.get(g, 0), v2.get(g, 0)) for g in all_genres)
    return round(overlap, 1)


@community_bp.route("/compatibility", methods=["GET"])
def get_compatibility():
    """
    UC-09 Typical Flow:
      3. Verify other user exists.
      4. Retrieve genre distributions for both users.
      5. Calculate overlap.
      6. Return compatibility score + side-by-side genre breakdown.
    """
    err = _login_required()
    if err:
        return err

    other_username = (request.args.get("username") or "").strip()
    if not other_username:
        return jsonify({"success": False, "message": "Username is required."}), 400

    my_id = session["user_id"]

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # ── Step 3: Verify other user exists ──────────────────────────────────
        cursor.execute(
            "SELECT UserID, Username FROM Users WHERE Username = ? AND IsActive = 1",
            (other_username,)
        )
        other_row = cursor.fetchone()
        if not other_row:
            conn.close()
            return jsonify({"success": False, "message": "User not found."}), 404

        other_id, other_username_db = other_row

        if other_id == my_id:
            conn.close()
            return jsonify({"success": False, "message": "You can't check compatibility with yourself!"}), 400

        # ── Step 4: Build genre vectors ────────────────────────────────────────
        my_vector    = _genre_vector(cursor, my_id)
        other_vector = _genre_vector(cursor, other_id)

        # ── Alternate flow: insufficient data ──────────────────────────────────
        if not my_vector:
            conn.close()
            return jsonify({
                "success": False,
                "message": "You need to rate some movies first to check compatibility.",
            }), 400

        if not other_vector:
            conn.close()
            return jsonify({
                "success": False,
                "message": f"{other_username_db} hasn't rated any movies yet.",
            }), 400

        # ── Step 5: Calculate compatibility ───────────────────────────────────
        score = _compatibility_score(my_vector, other_vector)

        # ── Step 6: Build side-by-side genre breakdown ─────────────────────────
        all_genres = sorted(
            set(my_vector.keys()) | set(other_vector.keys()),
            key=lambda g: -(my_vector.get(g, 0) + other_vector.get(g, 0))
        )[:8]

        breakdown = [
            {
                "genre":     g,
                "my_pct":    my_vector.get(g, 0),
                "their_pct": other_vector.get(g, 0),
                "shared":    min(my_vector.get(g, 0), other_vector.get(g, 0)) > 0,
            }
            for g in all_genres
        ]

        # Compatibility label
        if score >= 80:   label = "Cinema Soulmates 💫"
        elif score >= 60: label = "Great Match 🎬"
        elif score >= 40: label = "Some Common Ground 🍿"
        elif score >= 20: label = "Different Tastes 🎭"
        else:             label = "Total Opposites 🌓"

        conn.close()
        return jsonify({
            "success":          True,
            "my_username":      session["username"],
            "other_username":   other_username_db,
            "compatibility":    score,
            "label":            label,
            "genre_breakdown":  breakdown,
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# ══════════════════════════════════════════════════════════════════════════════
# UC-13: COMMUNITY AWARDS
# ══════════════════════════════════════════════════════════════════════════════

def _compute_awards(cursor, year: int, month: int) -> dict:
    """
    Compute four award categories for the given year/month.
    All queries are parameterised and scoped to that month.
    Returns a dict with keys: top_movie, top_reviewer, most_watched, top_genre.
    """
    # ── 1. Top Rated Movie of the Month ───────────────────────────────────────
    # Movie with highest average rating from ratings submitted this month
    cursor.execute(
        """
        SELECT TOP 1 m.Title, AVG(r.RatingValue) AS Avg, COUNT(*) AS Cnt
        FROM   Ratings r
        JOIN   VW_MoviesComplete m ON r.MovieID = m.MovieID
        WHERE  YEAR(r.RatedAt)  = ? AND MONTH(r.RatedAt)  = ?
        AND    m.IsApproved = 1
        GROUP  BY m.MovieID, m.Title
        HAVING COUNT(*) >= 1
        ORDER  BY AVG(r.RatingValue) DESC, COUNT(*) DESC
        """,
        (year, month)
    )
    row = cursor.fetchone()
    top_movie = {
        "title":  row[0] if row else None,
        "value":  f"{float(row[1]):.1f}★ ({row[2]} ratings)" if row else None,
    }

    # ── 2. Most Active Reviewer ────────────────────────────────────────────────
    cursor.execute(
        """
        SELECT TOP 1 u.Username, COUNT(*) AS ReviewCount
        FROM   Reviews rv
        JOIN   Users   u ON rv.UserID = u.UserID
        WHERE  YEAR(rv.CreatedAt) = ? AND MONTH(rv.CreatedAt) = ?
        GROUP  BY u.UserID, u.Username
        ORDER  BY COUNT(*) DESC
        """,
        (year, month)
    )
    row = cursor.fetchone()
    top_reviewer = {
        "username": row[0] if row else None,
        "value":    f"{row[1]} review{'s' if row and row[1] != 1 else ''}" if row else None,
    }

    # ── 3. Most Watched (Watchlist Adds) ──────────────────────────────────────
    cursor.execute(
        """
        SELECT TOP 1 m.Title, COUNT(*) AS Adds
        FROM   Watchlist w
        JOIN   VW_MoviesComplete m ON w.MovieID = m.MovieID
        WHERE  YEAR(w.AddedAt) = ? AND MONTH(w.AddedAt) = ?
        AND    m.IsApproved = 1
        GROUP  BY m.MovieID, m.Title
        ORDER  BY COUNT(*) DESC
        """,
        (year, month)
    )
    row = cursor.fetchone()
    most_watched = {
        "title": row[0] if row else None,
        "value": f"{row[1]} watchlist add{'s' if row and row[1] != 1 else ''}" if row else None,
    }

    # ── 4. Genre of the Month ─────────────────────────────────────────────────
    cursor.execute(
        """
        SELECT m.Genres, COUNT(*) AS Cnt
        FROM   Ratings r
        JOIN   VW_MoviesComplete m ON r.MovieID = m.MovieID
        WHERE  YEAR(r.RatedAt) = ? AND MONTH(r.RatedAt) = ?
        AND    m.Genres IS NOT NULL
        GROUP  BY m.Genres
        ORDER  BY COUNT(*) DESC
        """,
        (year, month)
    )
    genre_counts = {}
    for genres_str, cnt in cursor.fetchall():
        for g in genres_str.split(","):
            g = g.strip()
            if g:
                genre_counts[g] = genre_counts.get(g, 0) + cnt

    top_genre_name  = max(genre_counts, key=genre_counts.get) if genre_counts else None
    top_genre_count = genre_counts.get(top_genre_name, 0) if top_genre_name else 0

    top_genre = {
        "genre": top_genre_name,
        "value": f"{top_genre_count} rating{'s' if top_genre_count != 1 else ''}" if top_genre_name else None,
    }

    return {
        "top_movie":    top_movie,
        "top_reviewer": top_reviewer,
        "most_watched": most_watched,
        "top_genre":    top_genre,
    }


@community_bp.route("/awards", methods=["GET"])
def get_awards():
    """
    UC-13 Typical Flow:
      1. Load current month's awards (computed live).
      2. Load archive of last 6 months.

    UC-13 Alternate Flow (no current month data):
      Returns last month's awards + a note.
    """
    err = _login_required()
    if err:
        return err

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # Current month
        cursor.execute("SELECT YEAR(GETDATE()), MONTH(GETDATE())")
        row            = cursor.fetchone()
        current_year   = row[0]
        current_month  = row[1]

        current_awards = _compute_awards(cursor, current_year, current_month)

        # Check if current month has any data at all
        cursor.execute(
            """
            SELECT COUNT(*) FROM Ratings
            WHERE  YEAR(RatedAt) = ? AND MONTH(RatedAt) = ?
            """,
            (current_year, current_month)
        )
        has_current_data = cursor.fetchone()[0] > 0

        # Archive: last 5 completed months
        archive = []
        y, m = current_year, current_month
        for _ in range(5):
            m -= 1
            if m == 0:
                m = 12
                y -= 1
            awards = _compute_awards(cursor, y, m)
            # Only include months with at least some data
            if any(v.get("title") or v.get("username") or v.get("genre")
                   for v in awards.values()):
                archive.append({
                    "year":   y,
                    "month":  m,
                    "label":  _month_label(y, m),
                    "awards": awards,
                })

        conn.close()

        return jsonify({
            "success":          True,
            "current_month":    _month_label(current_year, current_month),
            "has_current_data": has_current_data,
            "current_awards":   current_awards,
            "archive":          archive,
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


def _month_label(year: int, month: int) -> str:
    months = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{months[month-1]} {year}"