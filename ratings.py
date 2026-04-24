"""
UC03 Rating Movies
handles: POST /api/ratings          = submit or update rating
         GET  /api/ratings/<movie_id> = get all ratings for one movie
         GET  /api/ratings/me/<movie_id> = get logged-in user's rating for a movie
"""

from flask import Blueprint, request, jsonify, session
from db import get_connection

ratings_bp = Blueprint("ratings", __name__)


def _login_required():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in first."}), 401
    return None


# UC03 Submit or update a rating 

@ratings_bp.route("/ratings", methods=["POST"])
def submit_rating():

    err = _login_required()
    if err:
        return err

    data     = request.get_json()
    movie_id = data.get("movie_id")
    rating   = data.get("rating")

    # presence checks 
    if movie_id is None:
        return jsonify({"success": False, "message": "Movie ID is required."}), 400
    if rating is None:
        return jsonify({"success": False, "message": "Rating value is required."}), 400

    # Validate rating range 
    try:
        rating = float(rating)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Rating must be a number."}), 400

    if rating < 1.0 or rating > 5.0:
        return jsonify({"success": False, "message": "Rating must be between 1 and 5."}), 400

    # Round to nearest 0.5 (half-star ratings)
    rating = round(rating * 2) / 2

    user_id = session["user_id"]

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # Check movie exists
        cursor.execute(
            "SELECT MovieID FROM Movies WHERE MovieID = ? AND IsApproved = 1",
            (movie_id,)
        )
        if not cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Movie not found."}), 404

       
        cursor.execute(
            "SELECT RatingID FROM Ratings WHERE UserID = ? AND MovieID = ?",
            (user_id, movie_id)
        )
        existing = cursor.fetchone()

        #if user already rated this movie
        if existing:
            # TR_Ratings_UpdateMovieAverage trigger works on update rating automatically
            cursor.execute(
                """
                UPDATE Ratings
                SET    RatingValue = ?, UpdatedAt = GETDATE()
                WHERE  UserID  = ?
                AND    MovieID = ?
                """,
                (rating, user_id, movie_id)
            )
            conn.commit()
            conn.close()
            return jsonify({
                "success": True,
                "message": f"Rating updated to {rating} stars.",
                "action":  "updated"
            }), 200

        else:
            #if not already rated, then insert nayi
            # TR_Ratings_UpdateMovieAverage trigger on insert as well.
            cursor.execute(
                """
                INSERT INTO Ratings (UserID, MovieID, RatingValue, RatedAt)
                VALUES (?, ?, ?, GETDATE())
                """,
                (user_id, movie_id, rating)
            )
            conn.commit()
            conn.close()
            return jsonify({
                "success": True,
                "message": f"Rated {rating} stars successfully.",
                "action":  "created"
            }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# logged-in user's rating for a specific movie 

@ratings_bp.route("/ratings/me/<int:movie_id>", methods=["GET"])
def get_my_rating(movie_id: int):
    err = _login_required()
    if err:
        return err

    user_id = session["user_id"]

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT RatingID, RatingValue FROM Ratings WHERE UserID = ? AND MovieID = ?",
            (user_id, movie_id)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify({
                "success":   True,
                "rated":     True,
                "rating_id": row[0],
                "rating":    float(row[1])
            }), 200
        else:
            return jsonify({"success": True, "rated": False}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# Get all ratings for a movie

@ratings_bp.route("/ratings/<int:movie_id>", methods=["GET"])
def get_movie_ratings(movie_id: int):
    err = _login_required()
    if err:
        return err

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT AVG(RatingValue) AS Average,
                   COUNT(*)         AS Total
            FROM   Ratings
            WHERE  MovieID = ?
            """,
            (movie_id,)
        )
        row = cursor.fetchone()
        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "average": float(row[0]) if row[0] else 0.0,
                "total":   row[1]
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
