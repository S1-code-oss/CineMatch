#UC08 CineBlend handle POST /api/cineblend  =compare logged-in user with a friend by username

from flask import Blueprint, request, jsonify, session
from db import get_connection

cineblend_bp = Blueprint("cineblend", __name__)


def _login_required():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in first."}), 401
    return None


def _get_top_genres(conn, user_id):
    """Return top 5 genres the user rated >= 3.5, ordered by average rating."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT TOP 5 g.GenreName, AVG(CAST(r.RatingValue AS FLOAT)) AS AvgRating
        FROM   Ratings r
        JOIN   MovieGenres mg ON r.MovieID = mg.MovieID
        JOIN   Genres g       ON mg.GenreID = g.GenreID
        WHERE  r.UserID = ?
        AND    r.RatingValue >= 3.5
        GROUP  BY g.GenreName
        ORDER  BY AvgRating DESC
        """,
        (user_id,)
    )
    return [row.GenreName for row in cursor.fetchall()]


def _get_rating_count(conn, user_id):
    """Return total number of ratings the user has submitted."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM Ratings WHERE UserID = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    return row.cnt if row else 0


# UC08 Run CineBlend

@cineblend_bp.route("/cineblend", methods=["POST"])
def run_cineblend():

    err = _login_required()
    if err:
        return err

    data            = request.get_json()
    friend_username = (data or {}).get("friend_username", "").strip()

    if not friend_username:
        return jsonify({"success": False, "message": "Friend username is required."}), 400

    user_id   = session["user_id"]
    friend_id = None

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # look up logged-in user
        cursor.execute(
            "SELECT UserID, Username, Email FROM Users WHERE UserID = ?",
            (user_id,)
        )
        me = cursor.fetchone()
        if not me:
            conn.close()
            return jsonify({"success": False, "message": "Your account was not found."}), 404

        # search friend by username
        cursor.execute(
            "SELECT UserID, Username, Email FROM Users WHERE Username = ?",
            (friend_username,)
        )
        friend = cursor.fetchone()
        if not friend:
            conn.close()
            return jsonify({"success": False, "message": f"User '{friend_username}' not found."}), 404

        if friend.UserID == user_id:
            conn.close()
            return jsonify({"success": False, "message": "You cannot blend with yourself."}), 400

        friend_id = friend.UserID

        # calculate compatibility using a fresh cursor to avoid result set conflicts
        compat_cursor = conn.cursor()
        compat_cursor.execute(
            "EXEC SP_CalculateCompatibility @User1ID = ?, @User2ID = ?",
            (user_id, friend_id)
        )
        compat_row          = compat_cursor.fetchone()
        compatibility_score = 0.0
        if compat_row:
            for col in compat_row:
                try:
                    compatibility_score = float(col)
                    break
                except (TypeError, ValueError):
                    continue
        compat_cursor.close()

        # get top genres for each user
        my_genres     = _get_top_genres(conn, user_id)
        friend_genres = _get_top_genres(conn, friend_id)
        shared_genres = [g for g in my_genres if g in friend_genres]

        # get personalised recommendations using a fresh cursor
        rec_cursor = conn.cursor()
        rec_cursor.execute(
            "EXEC SP_GetUserRecommendations @UserID = ?, @TopN = 10",
            (user_id,)
        )
        rec_rows = rec_cursor.fetchall()
        rec_ids  = [row.MovieID for row in rec_rows]
        rec_cursor.close()

        recommendations = []
        if rec_ids:
            placeholders = ",".join("?" * len(rec_ids))
            detail_cursor = conn.cursor()
            detail_cursor.execute(
                f"""
                SELECT MovieID, Title, ReleaseYear, Runtime, PosterURL,
                       AverageRating, Genres
                FROM   VW_MoviesComplete
                WHERE  MovieID IN ({placeholders})
                AND    IsApproved = 1
                """,
                tuple(rec_ids)
            )
            rec_detail = {row.MovieID: row for row in detail_cursor.fetchall()}
            detail_cursor.close()

            for mid in rec_ids:
                r = rec_detail.get(mid)
                if r:
                    recommendations.append({
                        "movie_id":       r.MovieID,
                        "title":          r.Title,
                        "release_year":   r.ReleaseYear,
                        "runtime":        r.Runtime,
                        "poster_url":     r.PosterURL,
                        "average_rating": float(r.AverageRating) if r.AverageRating else 0.0,
                        "genres":         r.Genres or "",
                    })

        # get top pick (highest-rated shared-genre movie)
        top_pick = None
        if shared_genres:
            like_genre   = shared_genres[0]
            top_cursor   = conn.cursor()
            top_cursor.execute(
                """
                SELECT TOP 1
                       m.MovieID, m.Title, m.ReleaseYear, m.Runtime,
                       m.PosterURL, m.AverageRating, m.Genres
                FROM   VW_MoviesComplete m
                WHERE  m.IsApproved = 1
                AND    m.Genres LIKE ?
                ORDER  BY m.AverageRating DESC
                """,
                (f"%{like_genre}%",)
            )
            tp = top_cursor.fetchone()
            top_cursor.close()
            if tp:
                top_pick = {
                    "movie_id":       tp.MovieID,
                    "title":          tp.Title,
                    "release_year":   tp.ReleaseYear,
                    "runtime":        tp.Runtime,
                    "poster_url":     tp.PosterURL,
                    "average_rating": float(tp.AverageRating) if tp.AverageRating else 0.0,
                    "genres":         tp.Genres or "",
                }

        # rating counts
        my_count     = _get_rating_count(conn, user_id)
        friend_count = _get_rating_count(conn, friend_id)

        conn.close()

        return jsonify({
            "success":             True,
            "compatibility_score": compatibility_score,
            "shared_genres":       shared_genres,
            "my_genres":           my_genres,
            "friend_genres":       friend_genres,
            "me": {
                "username":     me.Username,
                "rating_count": my_count,
            },
            "friend": {
                "username":     friend.Username,
                "rating_count": friend_count,
            },
            "top_pick":        top_pick,
            "recommendations": recommendations,
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}\nfriend_id was: {friend_id}"}), 500
