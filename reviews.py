"""
UC04 Writing Reviews
Handles: POST /api/reviews          = submit a review (UC 3 precondition must have rated first)
         GET  /api/reviews/<movie_id> = get all public reviews for a movie
"""

from flask import Blueprint, request, jsonify, session
from db import get_connection

reviews_bp = Blueprint("reviews", __name__)

MAX_REVIEW_LENGTH = 1000  # characters


def _login_required():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in first."}), 401
    return None


# UC04 Submit a review

@reviews_bp.route("/reviews", methods=["POST"])
def submit_review():

    err = _login_required()
    if err:
        return err

    data        = request.get_json()
    movie_id    = data.get("movie_id")
    review_text = (data.get("review_text") or "").strip()

    # Presence check
    if not movie_id:
        return jsonify({"success": False, "message": "Movie ID is required."}), 400

    #Validate review text
    if not review_text:
        return jsonify({"success": False, "message": "Review cannot be empty."}), 400

    if len(review_text) > MAX_REVIEW_LENGTH:
        return jsonify({
            "success": False,
            "message": f"Review exceeds maximum length of {MAX_REVIEW_LENGTH} characters."
        }), 400

    user_id = session["user_id"]

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        #check user has rated this movie as review must be linked to a existing rating
        cursor.execute(
            "SELECT RatingID FROM Ratings WHERE UserID = ? AND MovieID = ?",
            (user_id, movie_id)
        )
        rating_row = cursor.fetchone()

        if not rating_row:
            conn.close()
            return jsonify({
                "success": False,
                "message": "You must rate this movie before writing a review."
            }), 400

        rating_id = rating_row[0]

        # check if review already exists for this user+movie 
        cursor.execute(
            "SELECT ReviewID FROM Reviews WHERE UserID = ? AND MovieID = ?",
            (user_id, movie_id)
        )
        existing = cursor.fetchone()

        if existing:
            #if yes, update existing review
            cursor.execute(
                """
                UPDATE Reviews
                SET    ReviewText = ?, UpdatedAt = GETDATE()
                WHERE  UserID  = ?
                AND    MovieID = ?
                """,
                (review_text, user_id, movie_id)
            )
            conn.commit()
            conn.close()
            return jsonify({
                "success": True,
                "message": "Review updated successfully.",
                "action":  "updated"
            }), 200

        else:
            # else, insert new review. IsPublic defaults to 1 so review appears on movie detail and profile
            cursor.execute(
                """
                INSERT INTO Reviews (RatingID, UserID, MovieID, ReviewText, IsPublic, CreatedAt)
                VALUES (?, ?, ?, ?, 1, GETDATE())
                """,
                (rating_id, user_id, movie_id, review_text)
            )
            conn.commit()
            conn.close()
            return jsonify({
                "success": True,
                "message": "Review submitted successfully.",
                "action":  "created"
            }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# all public reviews for a movie 

@reviews_bp.route("/reviews/<int:movie_id>", methods=["GET"])
def get_reviews(movie_id: int):
    err = _login_required()
    if err:
        return err

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT u.Username, rt.RatingValue, r.ReviewText, r.CreatedAt
            FROM   Reviews r
            JOIN   Users   u  ON r.UserID   = u.UserID
            JOIN   Ratings rt ON r.RatingID = rt.RatingID
            WHERE  r.MovieID  = ?
            AND    r.IsPublic  = 1
            ORDER  BY r.CreatedAt DESC
            """,
            (movie_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        reviews = [
            {
                "username":    row.Username,
                "rating":      float(row.RatingValue),
                "review_text": row.ReviewText,
                "created_at":  row.CreatedAt.strftime("%Y-%m-%d") if row.CreatedAt else ""
            }
            for row in rows
        ]

        return jsonify({"success": True, "data": reviews}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# get logged-in user's review for a specific movie 

@reviews_bp.route("/reviews/me/<int:movie_id>", methods=["GET"])
def get_my_review(movie_id: int):
    err = _login_required()
    if err:
        return err

    user_id = session["user_id"]

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT ReviewText FROM Reviews WHERE UserID = ? AND MovieID = ?",
            (user_id, movie_id)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify({
                "success":     True,
                "has_review":  True,
                "review_text": row[0]
            }), 200
        else:
            return jsonify({"success": True, "has_review": False}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
