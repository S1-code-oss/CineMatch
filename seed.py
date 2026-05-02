"""
CineMatch - Combined Seed Script
Fetches movies from TMDB and streaming platform data from JustWatch,
then inserts everything into your SQL Server database.

Replaces: fetch_movies_simple.py + justwatch_integration.py

Setup:
    pip install requests pyodbc simplejustwatchapi python-dotenv

Run:
    python seed.py
"""

import time
import os
import requests
import pyodbc
from dotenv import load_dotenv

try:
    from simplejustwatchapi.justwatch import search as jw_search
except ImportError:
    print("❌ Missing library! Run: pip install simplejustwatchapi")
    exit()

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

TMDB_API_KEY     = os.getenv("TMDB_API_KEY", "YOUR_TMDB_KEY_HERE")
TMDB_BASE        = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE  = "https://image.tmdb.org/t/p/w500"

SQL_SERVER       = os.getenv("SQL_SERVER", r"localhost\SQLEXPRESS")
SQL_DATABASE     = os.getenv("SQL_DATABASE", "CineMatch")
USE_WINDOWS_AUTH = True   # set False and fill below if using SQL auth
SQL_USERNAME     = os.getenv("SQL_USERNAME", "")
SQL_PASSWORD     = os.getenv("SQL_PASSWORD", "")

# How many pages of TMDB popular movies to fetch (20 movies per page)
PAGES_TO_FETCH = 5

# JustWatch country/language
JW_COUNTRY  = "US"
JW_LANGUAGE = "en"

# Only track these platforms (must match JustWatch provider names exactly)
PLATFORMS_WE_CARE_ABOUT = {
    "Netflix", "Max", "HBO Max", "Disney Plus",
    "Amazon Prime Video", "Hulu", "Apple TV Plus",
    "Paramount Plus", "Peacock",
}

# Maps JustWatch provider name → (display name, website) for your DB
PLATFORM_INFO = {
    "Netflix":            ("Netflix",       "https://netflix.com"),
    "Max":                ("Max",           "https://max.com"),
    "HBO Max":            ("HBO Max",       "https://hbomax.com"),
    "Disney Plus":        ("Disney+",       "https://disneyplus.com"),
    "Amazon Prime Video": ("Prime Video",   "https://primevideo.com"),
    "Hulu":               ("Hulu",          "https://hulu.com"),
    "Apple TV Plus":      ("Apple TV+",     "https://tv.apple.com"),
    "Paramount Plus":     ("Paramount+",    "https://paramountplus.com"),
    "Peacock":            ("Peacock",       "https://peacocktv.com"),
}

GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
    53: "Thriller", 10752: "War", 37: "Western",
}


# ── Database ──────────────────────────────────────────────────────────────────

def connect_db():
    try:
        if USE_WINDOWS_AUTH:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};"
                f"UID={SQL_USERNAME};PWD={SQL_PASSWORD}"
            )
        conn = pyodbc.connect(conn_str)
        print("✅ Connected to database!")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None


def get_or_create_genre(cursor, conn, genre_name: str) -> int:
    cursor.execute("SELECT GenreID FROM Genres WHERE GenreName = ?", genre_name)
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO Genres (GenreName) VALUES (?)", genre_name)
    genre_id = int(cursor.execute("SELECT @@IDENTITY").fetchone()[0])
    conn.commit()
    return genre_id


def get_or_create_platform(cursor, conn, jw_name: str) -> int:
    display_name, website = PLATFORM_INFO.get(jw_name, (jw_name, ""))
    cursor.execute("SELECT PlatformID FROM StreamingPlatforms WHERE PlatformName = ?", display_name)
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(
        "INSERT INTO StreamingPlatforms (PlatformName, Website) VALUES (?, ?)",
        display_name, website
    )
    platform_id = int(cursor.execute("SELECT @@IDENTITY").fetchone()[0])
    conn.commit()
    print(f"  ➕ New platform: {display_name}")
    return platform_id


def link_movie_platform(cursor, conn, movie_id: int, platform_id: int):
    try:
        cursor.execute(
            "INSERT INTO MoviePlatforms (MovieID, PlatformID, AvailableFrom) VALUES (?, ?, GETDATE())",
            movie_id, platform_id
        )
        conn.commit()
    except Exception:
        conn.rollback()   # already linked — ignore duplicate


# ── TMDB ──────────────────────────────────────────────────────────────────────

def tmdb_get(endpoint, params=None):
    if params is None:
        params = {}
    params["api_key"] = TMDB_API_KEY
    r = requests.get(f"{TMDB_BASE}{endpoint}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_popular_tmdb_ids(pages: int) -> list:
    ids = []
    for page in range(1, pages + 1):
        data = tmdb_get("/movie/popular", {"page": page})
        ids.extend(m["id"] for m in data.get("results", []))
        print(f"  📥 Page {page}/{pages} — {len(data.get('results', []))} movies")
    return ids


def fetch_tmdb_details(tmdb_id: int) -> dict | None:
    try:
        return tmdb_get(f"/movie/{tmdb_id}", {"append_to_response": "credits,videos"})
    except Exception:
        return None


# ── JustWatch ─────────────────────────────────────────────────────────────────

def fetch_jw_platforms(title: str, year: int | None) -> list:
    """Returns list of JustWatch provider name strings available for this movie."""
    try:
        results = jw_search(title, JW_COUNTRY, JW_LANGUAGE, count=5, best_only=False)
        if not results:
            return []

        # Try exact title + year match first
        best = None
        title_lower = title.lower()
        for entry in results:
            if entry.object_type != "MOVIE":
                continue
            if entry.title.lower() == title_lower:
                if year and hasattr(entry, "release_year") and entry.release_year == year:
                    best = entry
                    break
                elif not year:
                    best = entry
                    break

        # Fall back to first movie result
        if not best:
            best = next((e for e in results if e.object_type == "MOVIE"), None)

        if not best:
            return []

        return [
            offer.package.name
            for offer in best.offers
            if offer.monetization_type == "FLATRATE"
            and offer.package.name in PLATFORMS_WE_CARE_ABOUT
        ]

    except Exception as e:
        print(f"  ⚠️  JustWatch error for '{title}': {e}")
        return []


# ── Main insert logic ─────────────────────────────────────────────────────────

def insert_movie(conn, details: dict) -> int | None:
    """
    Inserts one movie (with genres) into the DB.
    Returns the DB MovieID, or None if it already existed / failed.
    """
    cursor = conn.cursor()
    tmdb_id = details.get("id")

    # Skip if already seeded
    cursor.execute("SELECT MovieID FROM Movies WHERE TMDB_ID = ?", tmdb_id)
    if cursor.fetchone():
        return None

    title        = details.get("title", "Unknown")
    release_date = details.get("release_date", "")
    release_year = int(release_date[:4]) if len(release_date) >= 4 else None
    runtime      = details.get("runtime")
    description  = details.get("overview", "")

    poster_path  = details.get("poster_path")
    poster_url   = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

    backdrop_path = details.get("backdrop_path")
    backdrop_url  = f"{TMDB_IMAGE_BASE}{backdrop_path}" if backdrop_path else None

    # Trailer
    trailer_url = None
    for v in details.get("videos", {}).get("results", []):
        if v.get("type") == "Trailer" and v.get("site") == "YouTube":
            trailer_url = f"https://www.youtube.com/watch?v={v['key']}"
            break

    # Director
    director = None
    for person in details.get("credits", {}).get("crew", []):
        if person.get("job") == "Director":
            director = person.get("name")
            break

    # Cast (top 5)
    cast_list = [a.get("name") for a in details.get("credits", {}).get("cast", [])[:5]]
    cast_str  = ", ".join(cast_list) if cast_list else None

    try:
        cursor.execute(
            """
            INSERT INTO Movies
                (TMDB_ID, Title, ReleaseYear, Runtime, Description,
                 PosterURL, BackdropURL, TrailerURL, Director, Cast,
                 AddedBy, IsApproved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
            """,
            tmdb_id, title, release_year, runtime, description,
            poster_url, backdrop_url, trailer_url, director, cast_str,
        )
        movie_id = int(cursor.execute("SELECT @@IDENTITY").fetchone()[0])

        # Genres
        for tmdb_genre_id in details.get("genre_ids", []):
            genre_name = GENRE_MAP.get(tmdb_genre_id)
            if not genre_name:
                # genre_ids is populated on list endpoints; detail endpoint uses genres[]
                continue
            db_genre_id = get_or_create_genre(cursor, conn, genre_name)
            try:
                cursor.execute(
                    "INSERT INTO MovieGenres (MovieID, GenreID) VALUES (?, ?)",
                    movie_id, db_genre_id,
                )
            except Exception:
                pass  # duplicate — ignore

        # genres[] is the key on detail endpoints
        for g in details.get("genres", []):
            genre_name  = g.get("name")
            db_genre_id = get_or_create_genre(cursor, conn, genre_name)
            try:
                cursor.execute(
                    "INSERT INTO MovieGenres (MovieID, GenreID) VALUES (?, ?)",
                    movie_id, db_genre_id,
                )
            except Exception:
                pass

        conn.commit()
        return movie_id

    except Exception as e:
        print(f"  ❌ DB insert failed for '{title}': {e}")
        conn.rollback()
        return None


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("🎬 CineMatch — Combined Seed (TMDB + JustWatch)")
    print("=" * 60)

    if TMDB_API_KEY == "YOUR_TMDB_KEY_HERE":
        print("\n❌ Set TMDB_API_KEY in your .env file first!")
        return

    conn = connect_db()
    if not conn:
        return

    # Step 1: fetch TMDB IDs
    print(f"\n📡 Fetching {PAGES_TO_FETCH} pages from TMDB...")
    tmdb_ids = fetch_popular_tmdb_ids(PAGES_TO_FETCH)
    print(f"   → {len(tmdb_ids)} movies to process\n")

    inserted   = 0
    skipped    = 0
    jw_found   = 0
    jw_missing = 0

    for i, tmdb_id in enumerate(tmdb_ids, 1):

        # Step 2: get full TMDB details
        details = fetch_tmdb_details(tmdb_id)
        if not details:
            skipped += 1
            continue

        title        = details.get("title", "?")
        release_date = details.get("release_date", "")
        year         = int(release_date[:4]) if len(release_date) >= 4 else None

        print(f"[{i}/{len(tmdb_ids)}] {title} ({year})")

        # Step 3: insert movie + genres into DB
        movie_id = insert_movie(conn, details)

        if movie_id is None:
            # already existed — still look it up so we can update platforms
            cursor = conn.cursor()
            cursor.execute("SELECT MovieID FROM Movies WHERE TMDB_ID = ?", tmdb_id)
            row = cursor.fetchone()
            movie_id = row[0] if row else None
            if not movie_id:
                skipped += 1
                time.sleep(0.3)
                continue
            print(f"  ⏭️  Already in DB (MovieID {movie_id}), checking platforms...")
        else:
            inserted += 1
            print(f"  ✅ Inserted (MovieID {movie_id})")

        # Step 4: fetch JustWatch platform data and link to movie
        platforms = fetch_jw_platforms(title, year)
        if platforms:
            jw_found += 1
            cursor = conn.cursor()
            for jw_name in platforms:
                platform_id = get_or_create_platform(cursor, conn, jw_name)
                link_movie_platform(cursor, conn, movie_id, platform_id)
            display = [PLATFORM_INFO.get(p, (p,))[0] for p in platforms]
            print(f"  📺 Streaming on: {', '.join(display)}")
        else:
            jw_missing += 1
            print(f"  ℹ️  Not found on any tracked platform")

        # Be polite to both APIs
        time.sleep(0.8)

    print("\n" + "=" * 60)
    print(f"✅ Movies inserted          : {inserted}")
    print(f"⏭️  Already existed         : {skipped}")
    print(f"📺 Platform data found      : {jw_found}")
    print(f"ℹ️  No platform data        : {jw_missing}")
    print("=" * 60)

    conn.close()
    print("\n✅ Done! Verify with:")
    print("   SELECT * FROM VW_MoviesComplete")


if __name__ == "__main__":
    main()
