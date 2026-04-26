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



# UC-13: COMMUNITY AWARDS

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