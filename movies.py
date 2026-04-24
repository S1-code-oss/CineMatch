"""UC02 browsing library and UC06 filtering movies
Handle:  GET /api/movies           =full catalog
         GET /api/movies/<id>      =single movie detail
         GET /api/movies/filter    =filtered catalog (genre, year, rating, platform)
"""

from flask import Blueprint, jsonify, session, request
from db import get_connection

movies_bp = Blueprint("movies", __name__)

# login check
def _login_required():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in first."}), 401
    return None

# format one movie row into a dict 
# solid open closed as if new column is added to Movies later, only
# this one function chanegs 
def _format_movie(row) -> dict:
    return {
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
    }


# UC02 get all movies

@movies_bp.route("/movies", methods=["GET"])
def get_movies():

    err = _login_required()
    if err:
        return err

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # VW_MoviesComplete already combines genres and platforms
        # IsApproved = 1 means admin approved movie, UC-14 does this
        cursor.execute(
            """
            SELECT MovieID, Title, ReleaseYear, Runtime, Description,
                   PosterURL, TrailerURL, Director, Cast,
                   AverageRating, TotalRatings, Genres, Platforms
            FROM   VW_MoviesComplete
            WHERE  IsApproved = 1
            ORDER  BY AverageRating DESC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        # Alternate flow if catalog is empty
        if not rows:
            return jsonify({
                "success": True,
                "message": "Library is empty.",
                "data":    []
            }), 200

        movies = [_format_movie(r) for r in rows]
        return jsonify({"success": True, "data": movies}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# UC02 get one movie detail

@movies_bp.route("/movies/<int:movie_id>", methods=["GET"])
def get_movie_detail(movie_id: int):

    err = _login_required()
    if err:
        return err

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # fetch the movie 
        cursor.execute(
            """
            SELECT MovieID, Title, ReleaseYear, Runtime, Description,
                   PosterURL, TrailerURL, Director, Cast,
                   AverageRating, TotalRatings, Genres, Platforms
            FROM   VW_MoviesComplete
            WHERE  MovieID    = ?
            AND    IsApproved = 1
            """,
            (movie_id,)
        )
        row = cursor.fetchone()

        if row is None:
            conn.close()
            return jsonify({"success": False, "message": "Movie not found."}), 404

        movie = _format_movie(row)

        # get public reviews for this movie as UC-02 says reviews to appear on detail page
        cursor.execute(
            """
            SELECT r.ReviewText, r.CreatedAt, u.Username, rt.RatingValue
            FROM   Reviews r
            JOIN   Users   u  ON r.UserID  = u.UserID
            JOIN   Ratings rt ON r.RatingID = rt.RatingID
            WHERE  r.MovieID  = ?
            AND    r.IsPublic  = 1
            ORDER  BY r.CreatedAt DESC
            """,
            (movie_id,)
        )
        review_rows = cursor.fetchall()

        reviews = [
            {
                "username":     rv.Username,
                "rating":       float(rv.RatingValue),
                "review_text":  rv.ReviewText,
                "created_at":   rv.CreatedAt.strftime("%Y-%m-%d") if rv.CreatedAt else "",
            }
            for rv in review_rows
        ]

        # get rating (how many stars)
        cursor.execute(
            """
            SELECT CAST(RatingValue AS INT) AS Stars, COUNT(*) AS Total
            FROM   Ratings
            WHERE  MovieID = ?
            GROUP  BY CAST(RatingValue AS INT)
            ORDER  BY Stars
            """,
            (movie_id,)
        )
        dist_rows   = cursor.fetchall()
        conn.close()

        rating_distribution = {str(r.Stars): r.Total for r in dist_rows}
        # mkae sure all 5 star levels present even if count is 0
        for star in ["1", "2", "3", "4", "5"]:
            rating_distribution.setdefault(star, 0)

        movie["reviews"]             = reviews
        movie["rating_distribution"] = rating_distribution

        return jsonify({"success": True, "data": movie}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# UC06 filter movies 

@movies_bp.route("/movies/filter", methods=["GET"])
def filter_movies():
    
    err = _login_required()
    if err:
        return err

    genre    = request.args.get("genre",    "").strip()
    platform = request.args.get("platform", "").strip()
    year_min = request.args.get("year_min", type=int)
    year_max = request.args.get("year_max", type=int)
    rating   = request.args.get("rating",   type=float)

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        conditions = ["IsApproved = 1"]
        params     = []

        if year_min is not None:
            conditions.append("ReleaseYear >= ?")
            params.append(year_min)

        if year_max is not None:
            conditions.append("ReleaseYear <= ?")
            params.append(year_max)

        if rating is not None:
            conditions.append("AverageRating >= ?")
            params.append(rating)

        # Each selected genre must appear in the Genres string
        if genre:
            for g in [g.strip() for g in genre.split(",") if g.strip()]:
                conditions.append("Genres LIKE ?")
                params.append(f"%{g}%")

        # movie must be on at least one selected platform
        if platform:
            plat_list = [p.strip() for p in platform.split(",") if p.strip()]
            if plat_list:
                plat_conditions = " OR ".join(["Platforms LIKE ?" for _ in plat_list])
                conditions.append(f"({plat_conditions})")
                params.extend([f"%{p}%" for p in plat_list])

        where_clause = " AND ".join(conditions)

        cursor.execute(
            f"""
            SELECT MovieID, Title, ReleaseYear, Runtime, Description,
                   PosterURL, TrailerURL, Director, Cast,
                   AverageRating, TotalRatings, Genres, Platforms
            FROM   VW_MoviesComplete
            WHERE  {where_clause}
            ORDER  BY AverageRating DESC
            """,
            tuple(params)
        )
        rows = cursor.fetchall()
        conn.close()

        movies = [_format_movie(r) for r in rows]
        return jsonify({
            "success": True,
            "count":   len(movies),
            "data":    movies
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
