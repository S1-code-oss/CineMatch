import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("SQLITE_DB_PATH", "cinematch.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_user_recommendations(user_id: int, top_n: int = 10) -> list[sqlite3.Row]:
    # top-n movies from user's top-3 genres not yet rated
    sql = """
    WITH UserTopGenres AS (
        SELECT mg.GenreID
        FROM   Ratings r
        JOIN   MovieGenres mg ON r.MovieID = mg.MovieID
        WHERE  r.UserID = :user_id
          AND  r.RatingValue >= 4.0
        GROUP  BY mg.GenreID
        ORDER  BY AVG(r.RatingValue) DESC, COUNT(*) DESC
        LIMIT  3
    )
    SELECT  m.MovieID,
            m.Title,
            m.ReleaseYear,
            m.AverageRating,
            (SELECT GROUP_CONCAT(g2.GenreName, ', ')
             FROM   MovieGenres mg2
             JOIN   Genres g2 ON mg2.GenreID = g2.GenreID
             WHERE  mg2.MovieID = m.MovieID) AS Genres
    FROM    Movies m
    JOIN    MovieGenres mg2    ON m.MovieID  = mg2.MovieID
    JOIN    UserTopGenres utg  ON mg2.GenreID = utg.GenreID
    WHERE   m.MovieID NOT IN (
                SELECT MovieID FROM Ratings WHERE UserID = :user_id
            )
      AND   m.IsApproved = 1
    GROUP   BY m.MovieID, m.Title, m.ReleaseYear, m.AverageRating
    ORDER   BY m.AverageRating DESC
    LIMIT   :top_n
    """
    with get_connection() as conn:
        return conn.execute(sql, {"user_id": user_id, "top_n": top_n}).fetchall()


def calculate_compatibility(user1_id: int, user2_id: int) -> dict:
    # jaccard similarity on liked genres (>= 4 stars)
    genre_sql = """
        SELECT DISTINCT mg.GenreID
        FROM   Ratings r
        JOIN   MovieGenres mg ON r.MovieID = mg.MovieID
        WHERE  r.UserID = ? AND r.RatingValue >= 4.0
    """
    with get_connection() as conn:
        u1_genres = {row[0] for row in conn.execute(genre_sql, (user1_id,))}
        u2_genres = {row[0] for row in conn.execute(genre_sql, (user2_id,))}

        shared = len(u1_genres & u2_genres)
        total  = len(u1_genres | u2_genres)
        score  = round(shared * 100.0 / total, 2) if total > 0 else 0.0

        row = conn.execute(
            "SELECT Username FROM Users WHERE UserID = ?", (user1_id,)
        ).fetchone()
        u1_name = row["Username"] if row else str(user1_id)

        row = conn.execute(
            "SELECT Username FROM Users WHERE UserID = ?", (user2_id,)
        ).fetchone()
        u2_name = row["Username"] if row else str(user2_id)

    return {"User1": u1_name, "User2": u2_name, "CompatibilityScore": score}


def get_user_stats(user_id: int) -> sqlite3.Row | None:
    # aggregate rating stats per user
    sql = """
    SELECT
        u.Username,
        COUNT(DISTINCT r.MovieID)       AS TotalMoviesRated,
        COALESCE(AVG(r.RatingValue), 0) AS AverageRatingGiven,
        (SELECT g.GenreName
         FROM   Ratings r2
         JOIN   MovieGenres mg ON r2.MovieID = mg.MovieID
         JOIN   Genres g       ON mg.GenreID = g.GenreID
         WHERE  r2.UserID = :user_id
         GROUP  BY g.GenreName
         ORDER  BY COUNT(*) DESC
         LIMIT  1)                      AS MostWatchedGenre,
        SUM(CASE WHEN r.RatingValue = 1.0 THEN 1 ELSE 0 END) AS OneStarCount,
        SUM(CASE WHEN r.RatingValue = 2.0 THEN 1 ELSE 0 END) AS TwoStarCount,
        SUM(CASE WHEN r.RatingValue = 3.0 THEN 1 ELSE 0 END) AS ThreeStarCount,
        SUM(CASE WHEN r.RatingValue = 4.0 THEN 1 ELSE 0 END) AS FourStarCount,
        SUM(CASE WHEN r.RatingValue = 5.0 THEN 1 ELSE 0 END) AS FiveStarCount
    FROM  Users u
    LEFT  JOIN Ratings r ON u.UserID = r.UserID
    WHERE u.UserID = :user_id
    GROUP BY u.Username, u.UserID
    """
    with get_connection() as conn:
        return conn.execute(sql, {"user_id": user_id}).fetchone()


def get_trending_movies(days_back: int = 7, top_n: int = 10) -> list[sqlite3.Row]:
    # movies with most ratings + watchlist adds in the last N days
    sql = """
    SELECT  m.MovieID,
            m.Title,
            m.ReleaseYear,
            m.AverageRating,
            COUNT(DISTINCT r.UserID) AS RecentRatings,
            COUNT(DISTINCT w.UserID) AS RecentWatchlistAdds
    FROM    Movies m
    LEFT    JOIN Ratings   r ON m.MovieID = r.MovieID
                             AND r.RatedAt >= datetime('now', :days_param)
    LEFT    JOIN Watchlist w ON m.MovieID = w.MovieID
                             AND w.AddedAt >= datetime('now', :days_param)
    WHERE   m.IsApproved = 1
    GROUP   BY m.MovieID, m.Title, m.ReleaseYear, m.AverageRating
    HAVING  COUNT(DISTINCT r.UserID) + COUNT(DISTINCT w.UserID) > 0
    ORDER   BY COUNT(DISTINCT r.UserID) + COUNT(DISTINCT w.UserID) DESC
    LIMIT   :top_n
    """
    days_param = f"-{days_back} days"
    with get_connection() as conn:
        return conn.execute(
            sql, {"days_param": days_param, "top_n": top_n}
        ).fetchall()
