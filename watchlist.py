"""
UC05 Managing Watchlist
handles POST   /api/watchlist          = add a movie to watchlist
         DELETE /api/watchlist/<movie_id> = remove a movie from watchlist
         GET    /api/watchlist           = get all movies in user's watchlist
         GET    /api/watchlist/<movie_id> = check if a specific movie is in watchlist
"""

from flask import Blueprint, request, jsonify, session
from db import get_connection

watchlist_bp = Blueprint("watchlist", __name__)


def _login_required():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in first."}), 401
    return None


# UC05 Add movie to watchlist 

@watchlist_bp.route("/watchlist", methods=["POST"])
def add_to_watchlist():
    
    err = _login_required()
    if err:
        return err

    data     = request.get_json()
    movie_id = data.get("movie_id")

    if not movie_id:
        return jsonify({"success": False, "message": "Movie ID is required."}), 400

    user_id = session["user_id"]

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # check movie exists 
        cursor.execute(
            "SELECT MovieID FROM Movies WHERE MovieID = ? AND IsApproved = 1",
            (movie_id,)
        )
        if not cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Movie not found."}), 404

        # check if already in watchlist 
        cursor.execute(
            "SELECT WatchlistID FROM Watchlist WHERE UserID = ? AND MovieID = ?",
            (user_id, movie_id)
        )
        if cursor.fetchone():
            conn.close()
            return jsonify({
                "success": False,
                "message": "Movie is already in your watchlist.",
                "in_watchlist": True
            }), 200

        # insert into watchlist 
        cursor.execute(
            "INSERT INTO Watchlist (UserID, MovieID, AddedAt) VALUES (?, ?, GETDATE())",
            (user_id, movie_id)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "success":      True,
            "message":      "Added to watchlist.",
            "in_watchlist": True
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# Remove movie from watchlist

@watchlist_bp.route("/watchlist/<int:movie_id>", methods=["DELETE"])
def remove_from_watchlist(movie_id: int):
    """
    Alternate Flow from UC-05:
      User clicks the filled heart icon to remove a movie they already saved.
      System deletes the Watchlist record for (UserID, MovieID).
    """
    err = _login_required()
    if err:
        return err

    user_id = session["user_id"]

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM Watchlist WHERE UserID = ? AND MovieID = ?",
            (user_id, movie_id)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "success":      True,
            "message":      "Removed from watchlist.",
            "in_watchlist": False
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# get user's full watchlist

@watchlist_bp.route("/watchlist", methods=["GET"])
def get_watchlist():
   
    err = _login_required()
    if err:
        return err

    user_id = session["user_id"]

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT m.MovieID, m.Title, m.ReleaseYear, m.Runtime, m.Description,
                   m.PosterURL, m.TrailerURL, m.Director, m.Cast,
                   m.AverageRating, m.TotalRatings, m.Genres, m.Platforms,
                   w.AddedAt
            FROM   Watchlist w
            JOIN   VW_MoviesComplete m ON w.MovieID = m.MovieID
            WHERE  w.UserID    = ?
            AND    m.IsApproved = 1
            ORDER  BY w.AddedAt DESC
            """,
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        movies = [
            {
                "movie_id":       row.MovieID,
                "title":          row.Title,
                "release_year":   row.ReleaseYear,
                "runtime":        row.Runtime,
                "description":    row.Description,
                "poster_url":     row.PosterURL,
                "trailer_url":    row.TrailerURL,
                "director":       row.Director,
                "cast":           row.Cast,
                "average_rating": float(row.AverageRating) if row.AverageRating else 0.0,
                "total_ratings":  row.TotalRatings,
                "genres":         row.Genres or "",
                "platforms":      row.Platforms or "",
                "added_at":       row.AddedAt.strftime("%Y-%m-%d") if row.AddedAt else "",
            }
            for row in rows
        ]

        return jsonify({"success": True, "data": movies}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# check if a specific movie is in user's watchlist 

@watchlist_bp.route("/watchlist/check/<int:movie_id>", methods=["GET"])
def check_watchlist(movie_id: int):
    err = _login_required()
    if err:
        return err

    user_id = session["user_id"]

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT WatchlistID FROM Watchlist WHERE UserID = ? AND MovieID = ?",
            (user_id, movie_id)
        )
        row = cursor.fetchone()
        conn.close()

        return jsonify({"success": True, "in_watchlist": row is not None}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
