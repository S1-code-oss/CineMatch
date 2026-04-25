"""
recommendations.py — UC-07: Viewing Recommendations

Algorithm: Weighted Genre Affinity Scoring
==========================================
1. Fetch all ratings by the user, joined to each movie's genres.
2. For every genre a user has rated, accumulate a WEIGHTED score:
       genre_score[genre] += rating_value   (higher rating = stronger signal)
3. Normalise scores to get genre affinity percentages.
4. For each candidate movie (not yet rated by the user, approved):
       candidate_score = sum of genre_affinity[genre] for genres in movie
5. Rank candidates by candidate_score DESC, return top N.

Fallback (no rating history): return top-rated movies globally.

SOLID:
  SRP  — only handles recommendation logic.
  OCP  — scoring algorithm is in _score_candidates(); swapping to ML = change one function.
  DIP  — DB via get_connection() only.
CRT:
  Cohesion — every function relates to recommendation computation.
  Coupling — zero imports from other blueprints.
"""

from flask import Blueprint, jsonify, session, request
from db import get_connection

recommendations_bp = Blueprint("recommendations", __name__)

TOP_N_DEFAULT = 20


def _login_required():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in first."}), 401
    return None


# ── Core algorithm helpers ─────────────────────────────────────────────────────

def _build_genre_affinity(cursor, user_id: int) -> dict:
    """
    Returns {genre: affinity_score} where affinity_score is the
    sum of ratings the user gave to movies containing that genre.
    Higher-rated genres score more — a 5★ action movie contributes
    more to 'Action' than a 2★ one.
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

    genre_scores = {}
    for genres_str, rating in rows:
        for genre in genres_str.split(","):
            genre = genre.strip()
            if genre:
                genre_scores[genre] = genre_scores.get(genre, 0.0) + float(rating)

    return genre_scores


def _score_candidates(candidates: list, genre_affinity: dict) -> list:
    """
    Score each candidate movie by summing the user's affinity for
    each of its genres. Returns candidates sorted by score DESC.
    """
    scored = []
    for movie in candidates:
        score = 0.0
        genres = [g.strip() for g in (movie["genres"] or "").split(",") if g.strip()]
        for g in genres:
            score += genre_affinity.get(g, 0.0)
        # Tie-break by global average rating
        score += float(movie["average_rating"]) * 0.1
        scored.append({**movie, "recommendation_score": round(score, 2)})

    scored.sort(key=lambda x: x["recommendation_score"], reverse=True)
    return scored


# ── UC-07 endpoint ─────────────────────────────────────────────────────────────

@recommendations_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    """
    UC-07 Typical Flow:
      2. System retrieves user's rating history → builds genre affinity map.
      3. System finds approved movies user hasn't rated yet.
      4. Scores and ranks them by genre affinity.
      Returns top N with recommendation_score and matched_genres.

    UC-07 Alternate Flow (no rating history):
      Returns global top-rated movies as fallback.
    """
    err = _login_required()
    if err:
        return err

    user_id = session["user_id"]
    top_n   = request.args.get("top", TOP_N_DEFAULT, type=int)
    top_n   = max(1, min(top_n, 50))

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # ── Step 1: Check if user has any ratings ──────────────────────────────
        cursor.execute(
            "SELECT COUNT(*) FROM Ratings WHERE UserID = ?", (user_id,)
        )
        rating_count = cursor.fetchone()[0]

        # ── Alternate flow: no ratings ─────────────────────────────────────────
        if rating_count == 0:
            cursor.execute(
                f"""
                SELECT TOP {top_n}
                       MovieID, Title, ReleaseYear, Runtime, Description,
                       PosterURL, TrailerURL, Director, Cast,
                       AverageRating, TotalRatings, Genres, Platforms
                FROM   VW_MoviesComplete
                WHERE  IsApproved = 1
                ORDER  BY AverageRating DESC
                """
            )
            rows = cursor.fetchall()
            conn.close()

            movies = [_fmt(r) for r in rows]
            return jsonify({
                "success":    True,
                "personalised": False,
                "message":    "Rate some movies to get personalised recommendations!",
                "data":       movies,
            }), 200

        # ── Step 2: Build genre affinity ───────────────────────────────────────
        genre_affinity = _build_genre_affinity(cursor, user_id)

        if not genre_affinity:
            conn.close()
            return jsonify({
                "success":    True,
                "personalised": False,
                "message":    "No genre data found. Rate more movies!",
                "data":       [],
            }), 200

        # ── Step 3: Fetch candidate movies (not yet rated by user) ─────────────
        cursor.execute(
            """
            SELECT MovieID, Title, ReleaseYear, Runtime, Description,
                   PosterURL, TrailerURL, Director, Cast,
                   AverageRating, TotalRatings, Genres, Platforms
            FROM   VW_MoviesComplete
            WHERE  IsApproved = 1
            AND    MovieID NOT IN (
                SELECT MovieID FROM Ratings WHERE UserID = ?
            )
            """,
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        candidates = [_fmt(r) for r in rows]

        # ── Step 4: Score and rank ─────────────────────────────────────────────
        scored = _score_candidates(candidates, genre_affinity)[:top_n]

        # Attach top matching genres for UI display
        top_genres = sorted(genre_affinity.items(), key=lambda x: x[1], reverse=True)[:3]
        top_genre_names = [g for g, _ in top_genres]

        return jsonify({
            "success":      True,
            "personalised": True,
            "top_genres":   top_genre_names,
            "data":         scored,
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# ── Genre affinity breakdown (used by profile/dashboard) ──────────────────────

@recommendations_bp.route("/recommendations/affinity", methods=["GET"])
def get_affinity():
    """Returns the user's genre affinity map — used by the dashboard."""
    err = _login_required()
    if err:
        return err
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        affinity = _build_genre_affinity(cursor, session["user_id"])
        conn.close()

        total = sum(affinity.values()) or 1
        sorted_genres = sorted(affinity.items(), key=lambda x: x[1], reverse=True)
        result = [
            {
                "genre":   g,
                "score":   round(s, 1),
                "percent": round(s / total * 100, 1),
            }
            for g, s in sorted_genres
        ]
        return jsonify({"success": True, "data": result}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ── Helper: format a movie row ─────────────────────────────────────────────────

def _fmt(row) -> dict:
    return {
        "movie_id":       row.MovieID,
        "title":          row.Title,
        "release_year":   row.ReleaseYear,
        "runtime":        row.Runtime,
        "description":    row.Description,
        "poster_url":     row.PosterURL  or "",
        "trailer_url":    row.TrailerURL or "",
        "director":       row.Director   or "",
        "cast":           row.Cast       or "",
        "average_rating": float(row.AverageRating) if row.AverageRating else 0.0,
        "total_ratings":  row.TotalRatings or 0,
        "genres":         row.Genres    or "",
        "platforms":      row.Platforms or "",
    }