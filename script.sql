-- ==================================
--CineMatch Database Script 
-- ===================================

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'CineMatch')
    CREATE DATABASE [CineMatch];
GO

USE [CineMatch];
GO

-- ===================================================
-- TABLES
-- =================================================

-- Users
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Users' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE Users (
        UserID          INT IDENTITY(1,1) PRIMARY KEY,
        Username        NVARCHAR(50)  NOT NULL,
        Email           NVARCHAR(100) NOT NULL,
        PasswordHash    NVARCHAR(255) NOT NULL,
        FullName        NVARCHAR(100) NULL,
        ProfilePicture  NVARCHAR(255) NULL,
        Bio             NVARCHAR(500) NULL,
        Location        NVARCHAR(100) NULL,
        Role            NVARCHAR(20)  NULL DEFAULT 'User',
        IsActive        BIT           NULL DEFAULT 1,
        WatchlistPublic BIT           NULL DEFAULT 0,
        CreatedAt       DATETIME      NULL DEFAULT GETDATE(),
        LastLogin       DATETIME      NULL,
        CONSTRAINT UQ_Users_Username UNIQUE (Username),
        CONSTRAINT UQ_Users_Email    UNIQUE (Email),
        CONSTRAINT CHK_Email         CHECK  (Email LIKE '%_@__%.__%'),
        CONSTRAINT CHK_UserRole      CHECK  (Role = 'Admin' OR Role = 'User')
    );
END
GO

-- Movies
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Movies' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE Movies (
        MovieID        INT IDENTITY(1,1) PRIMARY KEY,
        TMDB_ID        INT           NULL,
        Title          NVARCHAR(200) NOT NULL,
        OriginalTitle  NVARCHAR(200) NULL,
        ReleaseYear    INT           NULL,
        Runtime        INT           NULL,
        Description    NVARCHAR(MAX) NULL,
        PosterURL      NVARCHAR(500) NULL,
        BackdropURL    NVARCHAR(500) NULL,
        TrailerURL     NVARCHAR(500) NULL,
        Director       NVARCHAR(100) NULL,
        Cast           NVARCHAR(MAX) NULL,
        AverageRating  DECIMAL(3,2)  NULL DEFAULT 0.0,
        TotalRatings   INT           NULL DEFAULT 0,
        IsApproved     BIT           NULL DEFAULT 1,
        AddedBy        INT           NULL,
        CreatedAt      DATETIME      NULL DEFAULT GETDATE(),
        UpdatedAt      DATETIME      NULL DEFAULT GETDATE(),
        CONSTRAINT UQ_Movies_TMDB_ID  UNIQUE (TMDB_ID),
        CONSTRAINT CHK_AverageRating  CHECK (AverageRating >= 0 AND AverageRating <= 5),
        CONSTRAINT CHK_ReleaseYear    CHECK (ReleaseYear >= 1888 AND ReleaseYear <= 2100),
        CONSTRAINT CHK_Runtime        CHECK (Runtime > 0),
        CONSTRAINT FK_Movies_AddedBy  FOREIGN KEY (AddedBy) REFERENCES Users(UserID)
    );
END
GO

-- Handle existing tables missing newer columns
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'TMDB_ID')
    ALTER TABLE Movies ADD TMDB_ID INT NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'Description')
    ALTER TABLE Movies ADD Description NVARCHAR(MAX) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'PosterURL')
    ALTER TABLE Movies ADD PosterURL NVARCHAR(500) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'BackdropURL')
    ALTER TABLE Movies ADD BackdropURL NVARCHAR(500) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'TrailerURL')
    ALTER TABLE Movies ADD TrailerURL NVARCHAR(500) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'Cast')
    ALTER TABLE Movies ADD Cast NVARCHAR(MAX) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'IsApproved')
    ALTER TABLE Movies ADD IsApproved BIT NULL DEFAULT 1;
GO

-- Approve all existing movies
UPDATE Movies SET IsApproved = 1 WHERE IsApproved IS NULL;
GO

-- Genres
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Genres' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE Genres (
        GenreID     INT IDENTITY(1,1) PRIMARY KEY,
        GenreName   NVARCHAR(50)  NOT NULL,
        Description NVARCHAR(255) NULL,
        CONSTRAINT UQ_Genres_GenreName UNIQUE (GenreName)
    );
END
GO

-- MovieGenres
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'MovieGenres' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE MovieGenres (
        MovieGenreID INT IDENTITY(1,1) PRIMARY KEY,
        MovieID      INT NOT NULL,
        GenreID      INT NOT NULL,
        CONSTRAINT UQ_MovieGenre      UNIQUE (MovieID, GenreID),
        CONSTRAINT FK_MovieGenres_Movie FOREIGN KEY (MovieID) REFERENCES Movies(MovieID) ON DELETE CASCADE,
        CONSTRAINT FK_MovieGenres_Genre FOREIGN KEY (GenreID) REFERENCES Genres(GenreID) ON DELETE CASCADE
    );
END
GO

-- StreamingPlatforms
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'StreamingPlatforms' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE StreamingPlatforms (
        PlatformID   INT IDENTITY(1,1) PRIMARY KEY,
        PlatformName NVARCHAR(50)  NOT NULL,
        LogoURL      NVARCHAR(255) NULL,
        Website      NVARCHAR(255) NULL,
        CONSTRAINT UQ_StreamingPlatforms_Name UNIQUE (PlatformName)
    );
END
GO

-- MoviePlatforms
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'MoviePlatforms' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE MoviePlatforms (
        MoviePlatformID INT IDENTITY(1,1) PRIMARY KEY,
        MovieID         INT      NOT NULL,
        PlatformID      INT      NOT NULL,
        AvailableFrom   DATETIME NULL,
        AvailableUntil  DATETIME NULL,
        CONSTRAINT UQ_MoviePlatform          UNIQUE (MovieID, PlatformID),
        CONSTRAINT FK_MoviePlatforms_Movie    FOREIGN KEY (MovieID)    REFERENCES Movies(MovieID)             ON DELETE CASCADE,
        CONSTRAINT FK_MoviePlatforms_Platform FOREIGN KEY (PlatformID) REFERENCES StreamingPlatforms(PlatformID) ON DELETE CASCADE
    );
END
GO

-- Ratings
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Ratings' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE Ratings (
        RatingID    INT IDENTITY(1,1) PRIMARY KEY,
        UserID      INT            NOT NULL,
        MovieID     INT            NOT NULL,
        RatingValue DECIMAL(2,1)   NOT NULL,
        RatedAt     DATETIME       NULL DEFAULT GETDATE(),
        UpdatedAt   DATETIME       NULL DEFAULT GETDATE(),
        CONSTRAINT UQ_UserMovieRating UNIQUE (UserID, MovieID),
        CONSTRAINT CHK_RatingValue    CHECK  (RatingValue >= 1.0 AND RatingValue <= 5.0),
        CONSTRAINT FK_Ratings_User    FOREIGN KEY (UserID)  REFERENCES Users(UserID)  ON DELETE CASCADE,
        CONSTRAINT FK_Ratings_Movie   FOREIGN KEY (MovieID) REFERENCES Movies(MovieID) ON DELETE CASCADE
    );
END
GO

-- Reviews
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Reviews' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE Reviews (
        ReviewID   INT IDENTITY(1,1) PRIMARY KEY,
        RatingID   INT           NOT NULL,
        UserID     INT           NOT NULL,
        MovieID    INT           NOT NULL,
        ReviewText NVARCHAR(MAX) NOT NULL,
        IsPublic   BIT           NULL DEFAULT 1,
        LikesCount INT           NULL DEFAULT 0,
        CreatedAt  DATETIME      NULL DEFAULT GETDATE(),
        UpdatedAt  DATETIME      NULL DEFAULT GETDATE(),
        CONSTRAINT UQ_UserMovieReview UNIQUE (UserID, MovieID),
        CONSTRAINT FK_Reviews_Rating  FOREIGN KEY (RatingID) REFERENCES Ratings(RatingID) ON DELETE CASCADE,
        CONSTRAINT FK_Reviews_User    FOREIGN KEY (UserID)   REFERENCES Users(UserID),
        CONSTRAINT FK_Reviews_Movie   FOREIGN KEY (MovieID)  REFERENCES Movies(MovieID)
    );
END
GO

-- Watchlist
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Watchlist' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE Watchlist (
        WatchlistID INT IDENTITY(1,1) PRIMARY KEY,
        UserID      INT          NOT NULL,
        MovieID     INT          NOT NULL,
        AddedAt     DATETIME     NULL DEFAULT GETDATE(),
        Priority    INT          NULL DEFAULT 0,
        Notes       NVARCHAR(500) NULL,
        CONSTRAINT UQ_UserWatchlist   UNIQUE (UserID, MovieID),
        CONSTRAINT FK_Watchlist_User  FOREIGN KEY (UserID)  REFERENCES Users(UserID)  ON DELETE CASCADE,
        CONSTRAINT FK_Watchlist_Movie FOREIGN KEY (MovieID) REFERENCES Movies(MovieID) ON DELETE CASCADE
    );
END
GO

-- UserPreferences
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'UserPreferences' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE UserPreferences (
        PreferenceID           INT IDENTITY(1,1) PRIMARY KEY,
        UserID                 INT          NOT NULL,
        ExcludedGenres         NVARCHAR(MAX) NULL,
        NotificationsEnabled   BIT          NULL DEFAULT 1,
        Theme                  NVARCHAR(20) NULL DEFAULT 'Dark',
        CONSTRAINT UQ_UserPreference      UNIQUE (UserID),
        CONSTRAINT FK_UserPreferences_User FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
    );
END
GO

-- CollaborativeSessions
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CollaborativeSessions' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE CollaborativeSessions (
        SessionID                INT IDENTITY(1,1) PRIMARY KEY,
        User1ID                  INT            NOT NULL,
        User2ID                  INT            NOT NULL,
        CompatibilityScore       DECIMAL(5,2)   NULL,
        SharedGenres             NVARCHAR(MAX)  NULL,
        TopRecommendationMovieID INT            NULL,
        CreatedAt                DATETIME       NULL DEFAULT GETDATE(),
        CONSTRAINT CHK_CompatibilityScore         CHECK  (CompatibilityScore >= 0 AND CompatibilityScore <= 100),
        CONSTRAINT CHK_DifferentUsers             CHECK  (User1ID <> User2ID),
        CONSTRAINT FK_CollaborativeSessions_User1 FOREIGN KEY (User1ID) REFERENCES Users(UserID),
        CONSTRAINT FK_CollaborativeSessions_User2 FOREIGN KEY (User2ID) REFERENCES Users(UserID),
        CONSTRAINT FK_CollaborativeSessions_TopMovie FOREIGN KEY (TopRecommendationMovieID) REFERENCES Movies(MovieID)
    );
END
GO

-- CommunityAwards
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CommunityAwards' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE CommunityAwards (
        AwardID       INT IDENTITY(1,1) PRIMARY KEY,
        AwardMonth    DATE          NOT NULL,
        AwardCategory NVARCHAR(100) NOT NULL,
        WinnerUserID  INT           NULL,
        WinnerMovieID INT           NULL,
        WinnerGenreID INT           NULL,
        AwardValue    NVARCHAR(255) NULL,
        CreatedAt     DATETIME      NULL DEFAULT GETDATE(),
        CONSTRAINT FK_CommunityAwards_WinnerUser  FOREIGN KEY (WinnerUserID)  REFERENCES Users(UserID),
        CONSTRAINT FK_CommunityAwards_WinnerMovie FOREIGN KEY (WinnerMovieID) REFERENCES Movies(MovieID),
        CONSTRAINT FK_CommunityAwards_WinnerGenre FOREIGN KEY (WinnerGenreID) REFERENCES Genres(GenreID)
    );
END
GO

-- ============================================================
--  INDEXES
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_MovieGenres_MovieID' AND object_id = OBJECT_ID('dbo.MovieGenres'))
    CREATE NONCLUSTERED INDEX IX_MovieGenres_MovieID ON MovieGenres (MovieID);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_MovieGenres_GenreID' AND object_id = OBJECT_ID('dbo.MovieGenres'))
    CREATE NONCLUSTERED INDEX IX_MovieGenres_GenreID ON MovieGenres (GenreID);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Movies_Title' AND object_id = OBJECT_ID('dbo.Movies'))
    CREATE NONCLUSTERED INDEX IX_Movies_Title ON Movies (Title);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Movies_ReleaseYear' AND object_id = OBJECT_ID('dbo.Movies'))
    CREATE NONCLUSTERED INDEX IX_Movies_ReleaseYear ON Movies (ReleaseYear);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Movies_AverageRating' AND object_id = OBJECT_ID('dbo.Movies'))
    CREATE NONCLUSTERED INDEX IX_Movies_AverageRating ON Movies (AverageRating DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Ratings_UserID' AND object_id = OBJECT_ID('dbo.Ratings'))
    CREATE NONCLUSTERED INDEX IX_Ratings_UserID ON Ratings (UserID);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Ratings_MovieID' AND object_id = OBJECT_ID('dbo.Ratings'))
    CREATE NONCLUSTERED INDEX IX_Ratings_MovieID ON Ratings (MovieID);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Ratings_RatedAt' AND object_id = OBJECT_ID('dbo.Ratings'))
    CREATE NONCLUSTERED INDEX IX_Ratings_RatedAt ON Ratings (RatedAt DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Reviews_MovieID' AND object_id = OBJECT_ID('dbo.Reviews'))
    CREATE NONCLUSTERED INDEX IX_Reviews_MovieID ON Reviews (MovieID);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Users_Username' AND object_id = OBJECT_ID('dbo.Users'))
    CREATE NONCLUSTERED INDEX IX_Users_Username ON Users (Username);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Users_Email' AND object_id = OBJECT_ID('dbo.Users'))
    CREATE NONCLUSTERED INDEX IX_Users_Email ON Users (Email);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Watchlist_UserID' AND object_id = OBJECT_ID('dbo.Watchlist'))
    CREATE NONCLUSTERED INDEX IX_Watchlist_UserID ON Watchlist (UserID);
GO

-- ============================================================
--  VIEW
-- ============================================================

IF OBJECT_ID('dbo.VW_MoviesComplete', 'V') IS NOT NULL
    DROP VIEW dbo.VW_MoviesComplete;
GO

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
    STUFF((SELECT ', ' + g.GenreName
           FROM MovieGenres mg2
           JOIN Genres g ON mg2.GenreID = g.GenreID
           WHERE mg2.MovieID = m.MovieID
           ORDER BY g.GenreName
           FOR XML PATH('')), 1, 2, '') AS Genres,
    STUFF((SELECT ', ' + sp.PlatformName
           FROM MoviePlatforms mp2
           JOIN StreamingPlatforms sp ON mp2.PlatformID = sp.PlatformID
           WHERE mp2.MovieID = m.MovieID
           ORDER BY sp.PlatformName
           FOR XML PATH('')), 1, 2, '') AS Platforms
FROM Movies m;
GO

-- ============================================================
--  STORED PROCEDURES
-- ============================================================

-- SP 1: Get User Recommendations
IF OBJECT_ID('dbo.SP_GetUserRecommendations', 'P') IS NOT NULL
    DROP PROCEDURE SP_GetUserRecommendations;
GO
CREATE PROCEDURE SP_GetUserRecommendations
    @UserID INT,
    @TopN   INT = 10
AS
BEGIN
    SET NOCOUNT ON;
    WITH UserTopGenres AS (
        SELECT TOP 3
            g.GenreID,
            g.GenreName,
            COUNT(*) AS RatingCount
        FROM Ratings r
        JOIN MovieGenres mg ON r.MovieID = mg.MovieID
        JOIN Genres g       ON mg.GenreID = g.GenreID
        WHERE r.UserID = @UserID AND r.RatingValue >= 4.0
        GROUP BY g.GenreID, g.GenreName
        ORDER BY AVG(r.RatingValue) DESC, COUNT(*) DESC
    )
    SELECT TOP (@TopN)
        m.MovieID,
        m.Title,
        m.ReleaseYear,
        m.AverageRating,
        STUFF((SELECT ', ' + g2.GenreName
               FROM MovieGenres mg2
               JOIN Genres g2 ON mg2.GenreID = g2.GenreID
               WHERE mg2.MovieID = m.MovieID
               FOR XML PATH('')), 1, 2, '') AS Genres
    FROM Movies m
    JOIN MovieGenres mg    ON m.MovieID  = mg.MovieID
    JOIN UserTopGenres utg ON mg.GenreID = utg.GenreID
    WHERE m.MovieID NOT IN (SELECT MovieID FROM Ratings WHERE UserID = @UserID)
      AND m.IsApproved = 1
    GROUP BY m.MovieID, m.Title, m.ReleaseYear, m.AverageRating
    ORDER BY m.AverageRating DESC;
END;
GO

-- SP 2: Calculate Compatibility
IF OBJECT_ID('dbo.SP_CalculateCompatibility', 'P') IS NOT NULL
    DROP PROCEDURE SP_CalculateCompatibility;
GO
CREATE PROCEDURE SP_CalculateCompatibility
    @User1ID INT,
    @User2ID INT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @User1Genres TABLE (GenreID INT);
    DECLARE @User2Genres TABLE (GenreID INT);

    INSERT INTO @User1Genres
        SELECT DISTINCT mg.GenreID
        FROM Ratings r
        JOIN MovieGenres mg ON r.MovieID = mg.MovieID
        WHERE r.UserID = @User1ID AND r.RatingValue >= 4.0;

    INSERT INTO @User2Genres
        SELECT DISTINCT mg.GenreID
        FROM Ratings r
        JOIN MovieGenres mg ON r.MovieID = mg.MovieID
        WHERE r.UserID = @User2ID AND r.RatingValue >= 4.0;

    DECLARE @SharedCount INT;
    DECLARE @TotalCount  INT;

    SELECT @SharedCount = COUNT(*)
        FROM @User1Genres u1
        INNER JOIN @User2Genres u2 ON u1.GenreID = u2.GenreID;

    SELECT @TotalCount = COUNT(DISTINCT GenreID)
        FROM (SELECT GenreID FROM @User1Genres UNION SELECT GenreID FROM @User2Genres) AS AllGenres;

    SELECT
        u1.Username AS User1,
        u2.Username AS User2,
        CASE WHEN @TotalCount > 0
            THEN CAST(@SharedCount * 100.0 / @TotalCount AS DECIMAL(5,2))
            ELSE 0
        END AS CompatibilityScore
    FROM Users u1, Users u2
    WHERE u1.UserID = @User1ID AND u2.UserID = @User2ID;
END;
GO

-- SP 3: Get User Stats
IF OBJECT_ID('dbo.SP_GetUserStats', 'P') IS NOT NULL
    DROP PROCEDURE SP_GetUserStats;
GO
CREATE PROCEDURE SP_GetUserStats
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT
        u.Username,
        COUNT(DISTINCT r.MovieID)     AS TotalMoviesRated,
        ISNULL(AVG(r.RatingValue), 0) AS AverageRatingGiven,
        (SELECT TOP 1 g.GenreName
         FROM Ratings r2
         JOIN MovieGenres mg ON r2.MovieID = mg.MovieID
         JOIN Genres g       ON mg.GenreID = g.GenreID
         WHERE r2.UserID = @UserID
         GROUP BY g.GenreName
         ORDER BY COUNT(*) DESC)      AS MostWatchedGenre,
        SUM(CASE WHEN r.RatingValue = 1.0 THEN 1 ELSE 0 END) AS OneStarCount,
        SUM(CASE WHEN r.RatingValue = 2.0 THEN 1 ELSE 0 END) AS TwoStarCount,
        SUM(CASE WHEN r.RatingValue = 3.0 THEN 1 ELSE 0 END) AS ThreeStarCount,
        SUM(CASE WHEN r.RatingValue = 4.0 THEN 1 ELSE 0 END) AS FourStarCount,
        SUM(CASE WHEN r.RatingValue = 5.0 THEN 1 ELSE 0 END) AS FiveStarCount
    FROM Users u
    LEFT JOIN Ratings r ON u.UserID = r.UserID
    WHERE u.UserID = @UserID
    GROUP BY u.Username, u.UserID;
END;
GO

-- SP 4: Get Trending Movies
IF OBJECT_ID('dbo.SP_GetTrendingMovies', 'P') IS NOT NULL
    DROP PROCEDURE SP_GetTrendingMovies;
GO
CREATE PROCEDURE SP_GetTrendingMovies
    @DaysBack INT = 7,
    @TopN     INT = 10
AS
BEGIN
    SET NOCOUNT ON;
    SELECT TOP (@TopN)
        m.MovieID,
        m.Title,
        m.ReleaseYear,
        m.AverageRating,
        COUNT(DISTINCT r.UserID) AS RecentRatings,
        COUNT(DISTINCT w.UserID) AS RecentWatchlistAdds
    FROM Movies m
    LEFT JOIN Ratings   r ON m.MovieID = r.MovieID
        AND r.RatedAt  >= DATEADD(DAY, -@DaysBack, GETDATE())
    LEFT JOIN Watchlist w ON m.MovieID = w.MovieID
        AND w.AddedAt  >= DATEADD(DAY, -@DaysBack, GETDATE())
    WHERE m.IsApproved = 1
    GROUP BY m.MovieID, m.Title, m.ReleaseYear, m.AverageRating
    HAVING COUNT(DISTINCT r.UserID) + COUNT(DISTINCT w.UserID) > 0
    ORDER BY COUNT(DISTINCT r.UserID) + COUNT(DISTINCT w.UserID) DESC;
END;
GO
