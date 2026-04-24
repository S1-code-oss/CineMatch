"""
UC10 Trending Movies
handles GET /api/trending          = top trending movies (last 7 days)
         GET /api/trending/<days>   = trending over 30 days or 90
"""

from flask import Blueprint, request, jsonify, session
from db import get_connection

trending_bp = Blueprint("trending", __name__)


def _login_required():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in first."}), 401
    return None


# UC10 Get trending movie

@trending_bp.route("/trending", methods=["GET"])
def get_trending():

    err = _login_required()
    if err:
        return err

    days = request.args.get("days", 7, type=int)
    top_n = request.args.get("top", 20, type=int)

    # sensible bounds
    days  = max(1, min(days, 365))
    top_n = max(1, min(top_n, 100))

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # SP_GetTrendingMovies is already in the DB
        # It returns MovieID, Title, ReleaseYear, AverageRating, RecentRatings, RecentWatchlistAdds
        cursor.execute(
            "EXEC SP_GetTrendingMovies @DaysBack = ?, @TopN = ?",
            (days, top_n)
        )
        rows = cursor.fetchall()

        # SP only returns a few columns,get full detail from VW_MoviesComplete
        movie_ids = [row.MovieID for row in rows]
        trend_map = {
            row.MovieID: {
                "recent_ratings":       row.RecentRatings,
                "recent_watchlist_adds": row.RecentWatchlistAdds,
                "trend_score":          row.RecentRatings + row.RecentWatchlistAdds
            }
            for row in rows
        }

        if not movie_ids:
            conn.close()
            return jsonify({
                "success": True,
                "days":    days,
                "data":    [],
                "message": f"No trending movies in the last {days} days."
            }), 200

        # Build parameterised IN clause
        placeholders = ",".join("?" * len(movie_ids))
        cursor.execute(
            f"""
            SELECT MovieID, Title, ReleaseYear, Runtime, Description,
                   PosterURL, TrailerURL, Director, Cast,
                   AverageRating, TotalRatings, Genres, Platforms
            FROM   VW_MoviesComplete
            WHERE  MovieID     IN ({placeholders})
            AND    IsApproved   = 1
            """,
            tuple(movie_ids)
        )
        detail_rows = cursor.fetchall()
        conn.close()

        # Merge detail with trend scores, preserve SP's ranking order
        detail_map = {row.MovieID: row for row in detail_rows}
        movies = []
        for mid in movie_ids:
            row = detail_map.get(mid)
            if not row:
                continue
            t = trend_map[mid]
            movies.append({
                "movie_id":              row.MovieID,
                "title":                 row.Title,
                "release_year":          row.ReleaseYear,
                "runtime":               row.Runtime,
                "description":           row.Description,
                "poster_url":            row.PosterURL,
                "trailer_url":           row.TrailerURL,
                "director":              row.Director,
                "cast":                  row.Cast,
                "average_rating":        float(row.AverageRating) if row.AverageRating else 0.0,
                "total_ratings":         row.TotalRatings,
                "genres":                row.Genres or "",
                "platforms":             row.Platforms or "",
                "recent_ratings":        t["recent_ratings"],
                "recent_watchlist_adds": t["recent_watchlist_adds"],
                "trend_score":           t["trend_score"],
            })

        return jsonify({
            "success": True,
            "days":    days,
            "data":    movies
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
