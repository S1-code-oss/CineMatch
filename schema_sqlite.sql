PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Users (
    UserID          INTEGER PRIMARY KEY AUTOINCREMENT,
    Username        TEXT    NOT NULL,
    Email           TEXT    NOT NULL,
    PasswordHash    TEXT    NOT NULL,
    FullName        TEXT    NULL,
    ProfilePicture  TEXT    NULL,
    Bio             TEXT    NULL,
    Location        TEXT    NULL,
    Role            TEXT    NULL DEFAULT 'User'  CHECK (Role IN ('Admin', 'User')),
    IsActive        INTEGER NULL DEFAULT 1,
    WatchlistPublic INTEGER NULL DEFAULT 0,
    CreatedAt       TEXT    NULL DEFAULT (datetime('now')),
    LastLogin       TEXT    NULL,
    CONSTRAINT UQ_Users_Username UNIQUE (Username),
    CONSTRAINT UQ_Users_Email    UNIQUE (Email),
    CONSTRAINT CHK_Email         CHECK  (Email LIKE '%_@__%.__%')
);

CREATE TABLE IF NOT EXISTS Movies (
    MovieID        INTEGER PRIMARY KEY AUTOINCREMENT,
    TMDB_ID        INTEGER NULL,
    Title          TEXT    NOT NULL,
    OriginalTitle  TEXT    NULL,
    ReleaseYear    INTEGER NULL CHECK (ReleaseYear >= 1888 AND ReleaseYear <= 2100),
    Runtime        INTEGER NULL CHECK (Runtime > 0),
    Description    TEXT    NULL,
    PosterURL      TEXT    NULL,
    BackdropURL    TEXT    NULL,
    TrailerURL     TEXT    NULL,
    Director       TEXT    NULL,
    Cast           TEXT    NULL,
    AverageRating  REAL    NULL DEFAULT 0.0 CHECK (AverageRating >= 0 AND AverageRating <= 5),
    TotalRatings   INTEGER NULL DEFAULT 0,
    IsApproved     INTEGER NULL DEFAULT 1,
    AddedBy        INTEGER NULL,
    CreatedAt      TEXT    NULL DEFAULT (datetime('now')),
    UpdatedAt      TEXT    NULL DEFAULT (datetime('now')),
    CONSTRAINT UQ_Movies_TMDB_ID  UNIQUE (TMDB_ID),
    CONSTRAINT FK_Movies_AddedBy  FOREIGN KEY (AddedBy) REFERENCES Users(UserID)
);

CREATE TABLE IF NOT EXISTS Genres (
    GenreID     INTEGER PRIMARY KEY AUTOINCREMENT,
    GenreName   TEXT NOT NULL,
    Description TEXT NULL,
    CONSTRAINT UQ_Genres_GenreName UNIQUE (GenreName)
);

CREATE TABLE IF NOT EXISTS MovieGenres (
    MovieGenreID INTEGER PRIMARY KEY AUTOINCREMENT,
    MovieID      INTEGER NOT NULL,
    GenreID      INTEGER NOT NULL,
    CONSTRAINT UQ_MovieGenre        UNIQUE (MovieID, GenreID),
    CONSTRAINT FK_MovieGenres_Movie FOREIGN KEY (MovieID) REFERENCES Movies(MovieID) ON DELETE CASCADE,
    CONSTRAINT FK_MovieGenres_Genre FOREIGN KEY (GenreID) REFERENCES Genres(GenreID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS StreamingPlatforms (
    PlatformID   INTEGER PRIMARY KEY AUTOINCREMENT,
    PlatformName TEXT NOT NULL,
    LogoURL      TEXT NULL,
    Website      TEXT NULL,
    CONSTRAINT UQ_StreamingPlatforms_Name UNIQUE (PlatformName)
);

CREATE TABLE IF NOT EXISTS MoviePlatforms (
    MoviePlatformID INTEGER PRIMARY KEY AUTOINCREMENT,
    MovieID         INTEGER NOT NULL,
    PlatformID      INTEGER NOT NULL,
    AvailableFrom   TEXT    NULL,
    AvailableUntil  TEXT    NULL,
    CONSTRAINT UQ_MoviePlatform           UNIQUE (MovieID, PlatformID),
    CONSTRAINT FK_MoviePlatforms_Movie    FOREIGN KEY (MovieID)    REFERENCES Movies(MovieID)             ON DELETE CASCADE,
    CONSTRAINT FK_MoviePlatforms_Platform FOREIGN KEY (PlatformID) REFERENCES StreamingPlatforms(PlatformID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Ratings (
    RatingID    INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID      INTEGER NOT NULL,
    MovieID     INTEGER NOT NULL,
    RatingValue REAL    NOT NULL CHECK (RatingValue >= 1.0 AND RatingValue <= 5.0),
    RatedAt     TEXT    NULL DEFAULT (datetime('now')),
    UpdatedAt   TEXT    NULL DEFAULT (datetime('now')),
    CONSTRAINT UQ_UserMovieRating UNIQUE (UserID, MovieID),
    CONSTRAINT FK_Ratings_User    FOREIGN KEY (UserID)  REFERENCES Users(UserID)  ON DELETE CASCADE,
    CONSTRAINT FK_Ratings_Movie   FOREIGN KEY (MovieID) REFERENCES Movies(MovieID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Reviews (
    ReviewID   INTEGER PRIMARY KEY AUTOINCREMENT,
    RatingID   INTEGER NOT NULL,
    UserID     INTEGER NOT NULL,
    MovieID    INTEGER NOT NULL,
    ReviewText TEXT    NOT NULL,
    IsPublic   INTEGER NULL DEFAULT 1,
    LikesCount INTEGER NULL DEFAULT 0,
    CreatedAt  TEXT    NULL DEFAULT (datetime('now')),
    UpdatedAt  TEXT    NULL DEFAULT (datetime('now')),
    CONSTRAINT UQ_UserMovieReview UNIQUE (UserID, MovieID),
    CONSTRAINT FK_Reviews_Rating  FOREIGN KEY (RatingID) REFERENCES Ratings(RatingID) ON DELETE CASCADE,
    CONSTRAINT FK_Reviews_User    FOREIGN KEY (UserID)   REFERENCES Users(UserID),
    CONSTRAINT FK_Reviews_Movie   FOREIGN KEY (MovieID)  REFERENCES Movies(MovieID)
);

CREATE TABLE IF NOT EXISTS Watchlist (
    WatchlistID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID      INTEGER NOT NULL,
    MovieID     INTEGER NOT NULL,
    AddedAt     TEXT    NULL DEFAULT (datetime('now')),
    Priority    INTEGER NULL DEFAULT 0,
    Notes       TEXT    NULL,
    CONSTRAINT UQ_UserWatchlist   UNIQUE (UserID, MovieID),
    CONSTRAINT FK_Watchlist_User  FOREIGN KEY (UserID)  REFERENCES Users(UserID)  ON DELETE CASCADE,
    CONSTRAINT FK_Watchlist_Movie FOREIGN KEY (MovieID) REFERENCES Movies(MovieID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS UserPreferences (
    PreferenceID         INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID               INTEGER NOT NULL,
    ExcludedGenres       TEXT    NULL,
    NotificationsEnabled INTEGER NULL DEFAULT 1,
    Theme                TEXT    NULL DEFAULT 'Dark',
    CONSTRAINT UQ_UserPreference       UNIQUE (UserID),
    CONSTRAINT FK_UserPreferences_User FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS CollaborativeSessions (
    SessionID                INTEGER PRIMARY KEY AUTOINCREMENT,
    User1ID                  INTEGER NOT NULL,
    User2ID                  INTEGER NOT NULL,
    CompatibilityScore       REAL    NULL CHECK (CompatibilityScore >= 0 AND CompatibilityScore <= 100),
    SharedGenres             TEXT    NULL,
    TopRecommendationMovieID INTEGER NULL,
    CreatedAt                TEXT    NULL DEFAULT (datetime('now')),
    CHECK (User1ID <> User2ID),
    CONSTRAINT FK_CollabSessions_User1    FOREIGN KEY (User1ID) REFERENCES Users(UserID),
    CONSTRAINT FK_CollabSessions_User2    FOREIGN KEY (User2ID) REFERENCES Users(UserID),
    CONSTRAINT FK_CollabSessions_TopMovie FOREIGN KEY (TopRecommendationMovieID) REFERENCES Movies(MovieID)
);

CREATE TABLE IF NOT EXISTS CommunityAwards (
    AwardID       INTEGER PRIMARY KEY AUTOINCREMENT,
    AwardMonth    TEXT    NOT NULL,
    AwardCategory TEXT    NOT NULL,
    WinnerUserID  INTEGER NULL,
    WinnerMovieID INTEGER NULL,
    WinnerGenreID INTEGER NULL,
    AwardValue    TEXT    NULL,
    CreatedAt     TEXT    NULL DEFAULT (datetime('now')),
    CONSTRAINT FK_CommunityAwards_WinnerUser  FOREIGN KEY (WinnerUserID)  REFERENCES Users(UserID),
    CONSTRAINT FK_CommunityAwards_WinnerMovie FOREIGN KEY (WinnerMovieID) REFERENCES Movies(MovieID),
    CONSTRAINT FK_CommunityAwards_WinnerGenre FOREIGN KEY (WinnerGenreID) REFERENCES Genres(GenreID)
);

CREATE INDEX IF NOT EXISTS IX_MovieGenres_MovieID   ON MovieGenres (MovieID);
CREATE INDEX IF NOT EXISTS IX_MovieGenres_GenreID   ON MovieGenres (GenreID);
CREATE INDEX IF NOT EXISTS IX_Movies_Title          ON Movies (Title);
CREATE INDEX IF NOT EXISTS IX_Movies_ReleaseYear    ON Movies (ReleaseYear);
CREATE INDEX IF NOT EXISTS IX_Movies_AverageRating  ON Movies (AverageRating DESC);
CREATE INDEX IF NOT EXISTS IX_Ratings_UserID        ON Ratings (UserID);
CREATE INDEX IF NOT EXISTS IX_Ratings_MovieID       ON Ratings (MovieID);
CREATE INDEX IF NOT EXISTS IX_Ratings_RatedAt       ON Ratings (RatedAt DESC);
CREATE INDEX IF NOT EXISTS IX_Reviews_MovieID       ON Reviews (MovieID);
CREATE INDEX IF NOT EXISTS IX_Users_Username        ON Users (Username);
CREATE INDEX IF NOT EXISTS IX_Users_Email           ON Users (Email);
CREATE INDEX IF NOT EXISTS IX_Watchlist_UserID      ON Watchlist (UserID);

DROP VIEW IF EXISTS VW_MoviesComplete;
CREATE VIEW VW_MoviesComplete AS
SELECT
    m.MovieID,
    m.Title,
    m.ReleaseYear,
    m.Runtime,
    m.Description,
    m.PosterURL,
    m.TrailerURL,
    m.Director,
    m.Cast,
    m.AverageRating,
    m.TotalRatings,
    m.IsApproved,
    (SELECT GROUP_CONCAT(g.GenreName, ', ')
     FROM MovieGenres mg2
     JOIN Genres g ON mg2.GenreID = g.GenreID
     WHERE mg2.MovieID = m.MovieID) AS Genres,
    (SELECT GROUP_CONCAT(sp.PlatformName, ', ')
     FROM MoviePlatforms mp2
     JOIN StreamingPlatforms sp ON mp2.PlatformID = sp.PlatformID
     WHERE mp2.MovieID = m.MovieID) AS Platforms
FROM Movies m;
