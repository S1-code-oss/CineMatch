

USE [master]
GO

--create database only if it doesnt already exist
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'CineMatch')
BEGIN
    CREATE DATABASE [CineMatch]
     CONTAINMENT = NONE
     ON PRIMARY
    ( NAME = N'CineMatch', FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL17.SQLEXPRESS\MSSQL\DATA\CineMatch.mdf' , SIZE = 8192KB , MAXSIZE = UNLIMITED, FILEGROWTH = 65536KB )
     LOG ON
    ( NAME = N'CineMatch_log', FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL17.SQLEXPRESS\MSSQL\DATA\CineMatch_log.ldf' , SIZE = 8192KB , MAXSIZE = 2048GB , FILEGROWTH = 65536KB )
     WITH CATALOG_COLLATION = DATABASE_DEFAULT, LEDGER = OFF
END
GO

ALTER DATABASE [CineMatch] SET COMPATIBILITY_LEVEL = 170
GO
IF (1 = FULLTEXTSERVICEPROPERTY('IsFullTextInstalled'))
BEGIN
    EXEC [CineMatch].[dbo].[sp_fulltext_database] @action = 'enable'
END
GO
ALTER DATABASE [CineMatch] SET ANSI_NULL_DEFAULT OFF
GO
ALTER DATABASE [CineMatch] SET ANSI_NULLS OFF
GO
ALTER DATABASE [CineMatch] SET ANSI_PADDING OFF
GO
ALTER DATABASE [CineMatch] SET ANSI_WARNINGS OFF
GO
ALTER DATABASE [CineMatch] SET ARITHABORT OFF
GO
ALTER DATABASE [CineMatch] SET AUTO_CLOSE ON
GO
ALTER DATABASE [CineMatch] SET AUTO_SHRINK OFF
GO
ALTER DATABASE [CineMatch] SET AUTO_UPDATE_STATISTICS ON
GO
ALTER DATABASE [CineMatch] SET CURSOR_CLOSE_ON_COMMIT OFF
GO
ALTER DATABASE [CineMatch] SET CURSOR_DEFAULT GLOBAL
GO
ALTER DATABASE [CineMatch] SET CONCAT_NULL_YIELDS_NULL OFF
GO
ALTER DATABASE [CineMatch] SET NUMERIC_ROUNDABORT OFF
GO
ALTER DATABASE [CineMatch] SET QUOTED_IDENTIFIER OFF
GO
ALTER DATABASE [CineMatch] SET RECURSIVE_TRIGGERS OFF
GO
ALTER DATABASE [CineMatch] SET ENABLE_BROKER
GO
ALTER DATABASE [CineMatch] SET AUTO_UPDATE_STATISTICS_ASYNC OFF
GO
ALTER DATABASE [CineMatch] SET DATE_CORRELATION_OPTIMIZATION OFF
GO
ALTER DATABASE [CineMatch] SET TRUSTWORTHY OFF
GO
ALTER DATABASE [CineMatch] SET ALLOW_SNAPSHOT_ISOLATION OFF
GO
ALTER DATABASE [CineMatch] SET PARAMETERIZATION SIMPLE
GO
ALTER DATABASE [CineMatch] SET READ_COMMITTED_SNAPSHOT OFF
GO
ALTER DATABASE [CineMatch] SET HONOR_BROKER_PRIORITY OFF
GO
ALTER DATABASE [CineMatch] SET RECOVERY SIMPLE
GO
ALTER DATABASE [CineMatch] SET MULTI_USER
GO
ALTER DATABASE [CineMatch] SET PAGE_VERIFY CHECKSUM
GO
ALTER DATABASE [CineMatch] SET DB_CHAINING OFF
GO
ALTER DATABASE [CineMatch] SET FILESTREAM( NON_TRANSACTED_ACCESS = OFF )
GO
ALTER DATABASE [CineMatch] SET TARGET_RECOVERY_TIME = 60 SECONDS
GO
ALTER DATABASE [CineMatch] SET DELAYED_DURABILITY = DISABLED
GO
ALTER DATABASE [CineMatch] SET OPTIMIZED_LOCKING = OFF
GO
ALTER DATABASE [CineMatch] SET ACCELERATED_DATABASE_RECOVERY = OFF
GO
ALTER DATABASE [CineMatch] SET QUERY_STORE = ON
GO
ALTER DATABASE [CineMatch] SET QUERY_STORE (OPERATION_MODE = READ_WRITE, CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30), DATA_FLUSH_INTERVAL_SECONDS = 900, INTERVAL_LENGTH_MINUTES = 60, MAX_STORAGE_SIZE_MB = 1000, QUERY_CAPTURE_MODE = AUTO, SIZE_BASED_CLEANUP_MODE = AUTO, MAX_PLANS_PER_QUERY = 200, WAIT_STATS_CAPTURE_MODE = ON)
GO

USE [CineMatch]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- ============================================================
--  TABLES
-- ============================================================

-- Movies
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Movies' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[Movies](
        [MovieID]       [int] IDENTITY(1,1) NOT NULL,
        [TMDB_ID]       [int] NULL,
        [Title]         [nvarchar](200) NOT NULL,
        [OriginalTitle] [nvarchar](200) NULL,
        [ReleaseYear]   [int] NULL,
        [Runtime]       [int] NULL,
        [Description]   [nvarchar](max) NULL,
        [PosterURL]     [nvarchar](500) NULL,
        [BackdropURL]   [nvarchar](500) NULL,
        [TrailerURL]    [nvarchar](500) NULL,
        [Director]      [nvarchar](100) NULL,
        [Cast]          [nvarchar](max) NULL,
        [AverageRating] [decimal](3, 2) NULL,
        [TotalRatings]  [int] NULL,
        [IsApproved]    [bit] NULL,
        [AddedBy]       [int] NULL,
        [CreatedAt]     [datetime] NULL,
        [UpdatedAt]     [datetime] NULL,
        CONSTRAINT [PK_Movies] PRIMARY KEY CLUSTERED ([MovieID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
        CONSTRAINT [UQ_Movies_TMDB_ID] UNIQUE NONCLUSTERED ([TMDB_ID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
END
GO

-- If the table already existed, add any columns that may be missing
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'TMDB_ID')
    ALTER TABLE [dbo].[Movies] ADD [TMDB_ID] [int] NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'Description')
    ALTER TABLE [dbo].[Movies] ADD [Description] [nvarchar](max) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'PosterURL')
    ALTER TABLE [dbo].[Movies] ADD [PosterURL] [nvarchar](500) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'BackdropURL')
    ALTER TABLE [dbo].[Movies] ADD [BackdropURL] [nvarchar](500) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'TrailerURL')
    ALTER TABLE [dbo].[Movies] ADD [TrailerURL] [nvarchar](500) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'Cast')
    ALTER TABLE [dbo].[Movies] ADD [Cast] [nvarchar](max) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Movies') AND name = 'IsApproved')
    ALTER TABLE [dbo].[Movies] ADD [IsApproved] [bit] NULL DEFAULT 1;
GO

-- Approve all existing movies so they show up in the app
UPDATE [dbo].[Movies] SET [IsApproved] = 1 WHERE [IsApproved] IS NULL;
GO

-- Genres
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Genres' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[Genres](
        [GenreID]     [int] IDENTITY(1,1) NOT NULL,
        [GenreName]   [nvarchar](50) NOT NULL,
        [Description] [nvarchar](255) NULL,
        CONSTRAINT [PK_Genres] PRIMARY KEY CLUSTERED ([GenreID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
        CONSTRAINT [UQ_Genres_GenreName] UNIQUE NONCLUSTERED ([GenreName] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
END
GO

-- MovieGenres
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'MovieGenres' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[MovieGenres](
        [MovieGenreID] [int] IDENTITY(1,1) NOT NULL,
        [MovieID]      [int] NOT NULL,
        [GenreID]      [int] NOT NULL,
        CONSTRAINT [PK_MovieGenres] PRIMARY KEY CLUSTERED ([MovieGenreID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
        CONSTRAINT [UQ_MovieGenre] UNIQUE NONCLUSTERED ([MovieID] ASC, [GenreID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
END
GO

-- StreamingPlatforms
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'StreamingPlatforms' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[StreamingPlatforms](
        [PlatformID]   [int] IDENTITY(1,1) NOT NULL,
        [PlatformName] [nvarchar](50) NOT NULL,
        [LogoURL]      [nvarchar](255) NULL,
        [Website]      [nvarchar](255) NULL,
        CONSTRAINT [PK_StreamingPlatforms] PRIMARY KEY CLUSTERED ([PlatformID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
        CONSTRAINT [UQ_StreamingPlatforms_Name] UNIQUE NONCLUSTERED ([PlatformName] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
END
GO

-- MoviePlatforms
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'MoviePlatforms' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[MoviePlatforms](
        [MoviePlatformID] [int] IDENTITY(1,1) NOT NULL,
        [MovieID]         [int] NOT NULL,
        [PlatformID]      [int] NOT NULL,
        [AvailableFrom]   [datetime] NULL,
        [AvailableUntil]  [datetime] NULL,
        CONSTRAINT [PK_MoviePlatforms] PRIMARY KEY CLUSTERED ([MoviePlatformID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
        CONSTRAINT [UQ_MoviePlatform] UNIQUE NONCLUSTERED ([MovieID] ASC, [PlatformID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
END
GO

-- CollaborativeSessions
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CollaborativeSessions' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[CollaborativeSessions](
        [SessionID]                 [int] IDENTITY(1,1) NOT NULL,
        [User1ID]                   [int] NOT NULL,
        [User2ID]                   [int] NOT NULL,
        [CompatibilityScore]        [decimal](5, 2) NULL,
        [SharedGenres]              [nvarchar](max) NULL,
        [TopRecommendationMovieID]  [int] NULL,
        [CreatedAt]                 [datetime] NULL,
        CONSTRAINT [PK_CollaborativeSessions] PRIMARY KEY CLUSTERED ([SessionID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
END
GO

-- CommunityAwards
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CommunityAwards' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[CommunityAwards](
        [AwardID]       [int] IDENTITY(1,1) NOT NULL,
        [AwardMonth]    [date] NOT NULL,
        [AwardCategory] [nvarchar](100) NOT NULL,
        [WinnerUserID]  [int] NULL,
        [WinnerMovieID] [int] NULL,
        [WinnerGenreID] [int] NULL,
        [AwardValue]    [nvarchar](255) NULL,
        [CreatedAt]     [datetime] NULL,
        CONSTRAINT [PK_CommunityAwards] PRIMARY KEY CLUSTERED ([AwardID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
END
GO

-- Ratings
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Ratings' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[Ratings](
        [RatingID]    [int] IDENTITY(1,1) NOT NULL,
        [UserID]      [int] NOT NULL,
        [MovieID]     [int] NOT NULL,
        [RatingValue] [decimal](2, 1) NOT NULL,
        [RatedAt]     [datetime] NULL,
        [UpdatedAt]   [datetime] NULL,
        CONSTRAINT [PK_Ratings] PRIMARY KEY CLUSTERED ([RatingID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
        CONSTRAINT [UQ_UserMovieRating] UNIQUE NONCLUSTERED ([UserID] ASC, [MovieID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
END
GO

-- Reviews
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Reviews' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[Reviews](
        [ReviewID]   [int] IDENTITY(1,1) NOT NULL,
        [RatingID]   [int] NOT NULL,
        [UserID]     [int] NOT NULL,
        [MovieID]    [int] NOT NULL,
        [ReviewText] [nvarchar](max) NOT NULL,
        [IsPublic]   [bit] NULL,
        [LikesCount] [int] NULL,
        [CreatedAt]  [datetime] NULL,
        [UpdatedAt]  [datetime] NULL,
        CONSTRAINT [PK_Reviews] PRIMARY KEY CLUSTERED ([ReviewID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
        CONSTRAINT [UQ_UserMovieReview] UNIQUE NONCLUSTERED ([UserID] ASC, [MovieID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
END
GO

-- UserPreferences
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'UserPreferences' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[UserPreferences](
        [PreferenceID]          [int] IDENTITY(1,1) NOT NULL,
        [UserID]                [int] NOT NULL,
        [ExcludedGenres]        [nvarchar](max) NULL,
        [NotificationsEnabled]  [bit] NULL,
        [Theme]                 [nvarchar](20) NULL,
        CONSTRAINT [PK_UserPreferences] PRIMARY KEY CLUSTERED ([PreferenceID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
        CONSTRAINT [UQ_UserPreference] UNIQUE NONCLUSTERED ([UserID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
END
GO

-- Users
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Users' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[Users](
        [UserID]          [int] IDENTITY(1,1) NOT NULL,
        [Username]        [nvarchar](50) NOT NULL,
        [Email]           [nvarchar](100) NOT NULL,
        [PasswordHash]    [nvarchar](255) NOT NULL,
        [FullName]        [nvarchar](100) NULL,
        [ProfilePicture]  [nvarchar](255) NULL,
        [Bio]             [nvarchar](500) NULL,
        [Location]        [nvarchar](100) NULL,
        [Role]            [nvarchar](20) NULL,
        [IsActive]        [bit] NULL,
        [WatchlistPublic] [bit] NULL,
        [CreatedAt]       [datetime] NULL,
        [LastLogin]       [datetime] NULL,
        CONSTRAINT [PK_Users] PRIMARY KEY CLUSTERED ([UserID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
        CONSTRAINT [UQ_Users_Username] UNIQUE NONCLUSTERED ([Username] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
        CONSTRAINT [UQ_Users_Email] UNIQUE NONCLUSTERED ([Email] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
END
GO

-- Watchlist
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Watchlist' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[Watchlist](
        [WatchlistID] [int] IDENTITY(1,1) NOT NULL,
        [UserID]      [int] NOT NULL,
        [MovieID]     [int] NOT NULL,
        [AddedAt]     [datetime] NULL,
        [Priority]    [int] NULL,
        [Notes]       [nvarchar](500) NULL,
        CONSTRAINT [PK_Watchlist] PRIMARY KEY CLUSTERED ([WatchlistID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
        CONSTRAINT [UQ_UserWatchlist] UNIQUE NONCLUSTERED ([UserID] ASC, [MovieID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
                  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
END
GO

-- ============================================================
--  VIEW  (always drop and recreate to pick up fixes)
-- ============================================================

IF OBJECT_ID('dbo.VW_MoviesComplete', 'V') IS NOT NULL
    DROP VIEW [dbo].[VW_MoviesComplete];
GO

-- VIEWS
-- View: Movies Complete
CREATE VIEW [dbo].[VW_MoviesComplete] AS
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
--  INDEXES  (CREATE only if they do not exist)
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_MovieGenres_GenreID' AND object_id = OBJECT_ID('dbo.MovieGenres'))
    CREATE NONCLUSTERED INDEX [IX_MovieGenres_GenreID] ON [dbo].[MovieGenres] ([GenreID] ASC)
        WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
              DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON,
              OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY];
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_MovieGenres_MovieID' AND object_id = OBJECT_ID('dbo.MovieGenres'))
    CREATE NONCLUSTERED INDEX [IX_MovieGenres_MovieID] ON [dbo].[MovieGenres] ([MovieID] ASC)
        WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
              DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON,
              OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY];
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Movies_AverageRating' AND object_id = OBJECT_ID('dbo.Movies'))
    CREATE NONCLUSTERED INDEX [IX_Movies_AverageRating] ON [dbo].[Movies] ([AverageRating] DESC)
        WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
              DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON,
              OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY];
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Movies_ReleaseYear' AND object_id = OBJECT_ID('dbo.Movies'))
    CREATE NONCLUSTERED INDEX [IX_Movies_ReleaseYear] ON [dbo].[Movies] ([ReleaseYear] ASC)
        WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
              DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON,
              OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY];
GO

SET ANSI_PADDING ON
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Movies_Title' AND object_id = OBJECT_ID('dbo.Movies'))
    CREATE NONCLUSTERED INDEX [IX_Movies_Title] ON [dbo].[Movies] ([Title] ASC)
        WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
              DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON,
              OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY];
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Ratings_MovieID' AND object_id = OBJECT_ID('dbo.Ratings'))
    CREATE NONCLUSTERED INDEX [IX_Ratings_MovieID] ON [dbo].[Ratings] ([MovieID] ASC)
        WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
              DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON,
              OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY];
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Ratings_RatedAt' AND object_id = OBJECT_ID('dbo.Ratings'))
    CREATE NONCLUSTERED INDEX [IX_Ratings_RatedAt] ON [dbo].[Ratings] ([RatedAt] DESC)
        WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
              DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON,
              OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY];
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Ratings_UserID' AND object_id = OBJECT_ID('dbo.Ratings'))
    CREATE NONCLUSTERED INDEX [IX_Ratings_UserID] ON [dbo].[Ratings] ([UserID] ASC)
        WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
              DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON,
              OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY];
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Reviews_MovieID' AND object_id = OBJECT_ID('dbo.Reviews'))
    CREATE NONCLUSTERED INDEX [IX_Reviews_MovieID] ON [dbo].[Reviews] ([MovieID] ASC)
        WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
              DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON,
              OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY];
GO

SET ANSI_PADDING ON
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Users_Email' AND object_id = OBJECT_ID('dbo.Users'))
    CREATE NONCLUSTERED INDEX [IX_Users_Email] ON [dbo].[Users] ([Email] ASC)
        WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
              DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON,
              OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY];
GO

SET ANSI_PADDING ON
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Users_Username' AND object_id = OBJECT_ID('dbo.Users'))
    CREATE NONCLUSTERED INDEX [IX_Users_Username] ON [dbo].[Users] ([Username] ASC)
        WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
              DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON,
              OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY];
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Watchlist_UserID' AND object_id = OBJECT_ID('dbo.Watchlist'))
    CREATE NONCLUSTERED INDEX [IX_Watchlist_UserID] ON [dbo].[Watchlist] ([UserID] ASC)
        WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
              DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON,
              OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY];
GO

-- ============================================================
--  COLUMN DEFAULTS  (add only if not already present)
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.CollaborativeSessions') AND name = 'DF_CollaborativeSessions_CreatedAt')
    ALTER TABLE [dbo].[CollaborativeSessions] ADD DEFAULT (getdate()) FOR [CreatedAt];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.CommunityAwards') AND name = 'DF_CommunityAwards_CreatedAt')
    ALTER TABLE [dbo].[CommunityAwards] ADD DEFAULT (getdate()) FOR [CreatedAt];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Movies') AND name = 'DF_Movies_AverageRating')
    ALTER TABLE [dbo].[Movies] ADD DEFAULT ((0.0)) FOR [AverageRating];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Movies') AND name = 'DF_Movies_TotalRatings')
    ALTER TABLE [dbo].[Movies] ADD DEFAULT ((0)) FOR [TotalRatings];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Movies') AND name = 'DF_Movies_IsApproved')
    ALTER TABLE [dbo].[Movies] ADD DEFAULT ((1)) FOR [IsApproved];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Movies') AND name = 'DF_Movies_CreatedAt')
    ALTER TABLE [dbo].[Movies] ADD DEFAULT (getdate()) FOR [CreatedAt];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Movies') AND name = 'DF_Movies_UpdatedAt')
    ALTER TABLE [dbo].[Movies] ADD DEFAULT (getdate()) FOR [UpdatedAt];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Ratings') AND name = 'DF_Ratings_RatedAt')
    ALTER TABLE [dbo].[Ratings] ADD DEFAULT (getdate()) FOR [RatedAt];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Ratings') AND name = 'DF_Ratings_UpdatedAt')
    ALTER TABLE [dbo].[Ratings] ADD DEFAULT (getdate()) FOR [UpdatedAt];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Reviews') AND name = 'DF_Reviews_IsPublic')
    ALTER TABLE [dbo].[Reviews] ADD DEFAULT ((1)) FOR [IsPublic];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Reviews') AND name = 'DF_Reviews_LikesCount')
    ALTER TABLE [dbo].[Reviews] ADD DEFAULT ((0)) FOR [LikesCount];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Reviews') AND name = 'DF_Reviews_CreatedAt')
    ALTER TABLE [dbo].[Reviews] ADD DEFAULT (getdate()) FOR [CreatedAt];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Reviews') AND name = 'DF_Reviews_UpdatedAt')
    ALTER TABLE [dbo].[Reviews] ADD DEFAULT (getdate()) FOR [UpdatedAt];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.UserPreferences') AND name = 'DF_UserPreferences_NotificationsEnabled')
    ALTER TABLE [dbo].[UserPreferences] ADD DEFAULT ((1)) FOR [NotificationsEnabled];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.UserPreferences') AND name = 'DF_UserPreferences_Theme')
    ALTER TABLE [dbo].[UserPreferences] ADD DEFAULT ('Dark') FOR [Theme];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Users') AND name = 'DF_Users_Role')
    ALTER TABLE [dbo].[Users] ADD DEFAULT ('User') FOR [Role];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Users') AND name = 'DF_Users_IsActive')
    ALTER TABLE [dbo].[Users] ADD DEFAULT ((1)) FOR [IsActive];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Users') AND name = 'DF_Users_WatchlistPublic')
    ALTER TABLE [dbo].[Users] ADD DEFAULT ((0)) FOR [WatchlistPublic];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Users') AND name = 'DF_Users_CreatedAt')
    ALTER TABLE [dbo].[Users] ADD DEFAULT (getdate()) FOR [CreatedAt];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Watchlist') AND name = 'DF_Watchlist_AddedAt')
    ALTER TABLE [dbo].[Watchlist] ADD DEFAULT (getdate()) FOR [AddedAt];
GO
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE parent_object_id = OBJECT_ID('dbo.Watchlist') AND name = 'DF_Watchlist_Priority')
    ALTER TABLE [dbo].[Watchlist] ADD DEFAULT ((0)) FOR [Priority];
GO

-- ============================================================
--  FOREIGN KEYS  (add only if not already present)
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_CollaborativeSessions_TopMovie' AND parent_object_id = OBJECT_ID('dbo.CollaborativeSessions'))
    ALTER TABLE [dbo].[CollaborativeSessions] WITH CHECK ADD FOREIGN KEY([TopRecommendationMovieID]) REFERENCES [dbo].[Movies] ([MovieID]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_CollaborativeSessions_User1' AND parent_object_id = OBJECT_ID('dbo.CollaborativeSessions'))
    ALTER TABLE [dbo].[CollaborativeSessions] WITH CHECK ADD CONSTRAINT [FK_CollaborativeSessions_User1] FOREIGN KEY([User1ID]) REFERENCES [dbo].[Users] ([UserID]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_CollaborativeSessions_User2' AND parent_object_id = OBJECT_ID('dbo.CollaborativeSessions'))
    ALTER TABLE [dbo].[CollaborativeSessions] WITH CHECK ADD CONSTRAINT [FK_CollaborativeSessions_User2] FOREIGN KEY([User2ID]) REFERENCES [dbo].[Users] ([UserID]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_CommunityAwards_WinnerUser' AND parent_object_id = OBJECT_ID('dbo.CommunityAwards'))
    ALTER TABLE [dbo].[CommunityAwards] WITH CHECK ADD CONSTRAINT [FK_CommunityAwards_WinnerUser] FOREIGN KEY([WinnerUserID]) REFERENCES [dbo].[Users] ([UserID]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_CommunityAwards_WinnerMovie' AND parent_object_id = OBJECT_ID('dbo.CommunityAwards'))
    ALTER TABLE [dbo].[CommunityAwards] WITH CHECK ADD CONSTRAINT [FK_CommunityAwards_WinnerMovie] FOREIGN KEY([WinnerMovieID]) REFERENCES [dbo].[Movies] ([MovieID]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_CommunityAwards_WinnerGenre' AND parent_object_id = OBJECT_ID('dbo.CommunityAwards'))
    ALTER TABLE [dbo].[CommunityAwards] WITH CHECK ADD CONSTRAINT [FK_CommunityAwards_WinnerGenre] FOREIGN KEY([WinnerGenreID]) REFERENCES [dbo].[Genres] ([GenreID]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_MovieGenres_Genre' AND parent_object_id = OBJECT_ID('dbo.MovieGenres'))
    ALTER TABLE [dbo].[MovieGenres] WITH CHECK ADD CONSTRAINT [FK_MovieGenres_Genre] FOREIGN KEY([GenreID]) REFERENCES [dbo].[Genres] ([GenreID]) ON DELETE CASCADE;
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_MovieGenres_Movie' AND parent_object_id = OBJECT_ID('dbo.MovieGenres'))
    ALTER TABLE [dbo].[MovieGenres] WITH CHECK ADD CONSTRAINT [FK_MovieGenres_Movie] FOREIGN KEY([MovieID]) REFERENCES [dbo].[Movies] ([MovieID]) ON DELETE CASCADE;
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_MoviePlatforms_Movie' AND parent_object_id = OBJECT_ID('dbo.MoviePlatforms'))
    ALTER TABLE [dbo].[MoviePlatforms] WITH CHECK ADD CONSTRAINT [FK_MoviePlatforms_Movie] FOREIGN KEY([MovieID]) REFERENCES [dbo].[Movies] ([MovieID]) ON DELETE CASCADE;
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_MoviePlatforms_Platform' AND parent_object_id = OBJECT_ID('dbo.MoviePlatforms'))
    ALTER TABLE [dbo].[MoviePlatforms] WITH CHECK ADD CONSTRAINT [FK_MoviePlatforms_Platform] FOREIGN KEY([PlatformID]) REFERENCES [dbo].[StreamingPlatforms] ([PlatformID]) ON DELETE CASCADE;
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Movies_AddedBy' AND parent_object_id = OBJECT_ID('dbo.Movies'))
    ALTER TABLE [dbo].[Movies] WITH CHECK ADD CONSTRAINT [FK_Movies_AddedBy] FOREIGN KEY([AddedBy]) REFERENCES [dbo].[Users] ([UserID]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Ratings_Movie' AND parent_object_id = OBJECT_ID('dbo.Ratings'))
    ALTER TABLE [dbo].[Ratings] WITH CHECK ADD CONSTRAINT [FK_Ratings_Movie] FOREIGN KEY([MovieID]) REFERENCES [dbo].[Movies] ([MovieID]) ON DELETE CASCADE;
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Ratings_User' AND parent_object_id = OBJECT_ID('dbo.Ratings'))
    ALTER TABLE [dbo].[Ratings] WITH CHECK ADD CONSTRAINT [FK_Ratings_User] FOREIGN KEY([UserID]) REFERENCES [dbo].[Users] ([UserID]) ON DELETE CASCADE;
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Reviews_Movie' AND parent_object_id = OBJECT_ID('dbo.Reviews'))
    ALTER TABLE [dbo].[Reviews] WITH CHECK ADD CONSTRAINT [FK_Reviews_Movie] FOREIGN KEY([MovieID]) REFERENCES [dbo].[Movies] ([MovieID]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Reviews_Rating' AND parent_object_id = OBJECT_ID('dbo.Reviews'))
    ALTER TABLE [dbo].[Reviews] WITH CHECK ADD CONSTRAINT [FK_Reviews_Rating] FOREIGN KEY([RatingID]) REFERENCES [dbo].[Ratings] ([RatingID]) ON DELETE CASCADE;
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Reviews_User' AND parent_object_id = OBJECT_ID('dbo.Reviews'))
    ALTER TABLE [dbo].[Reviews] WITH CHECK ADD CONSTRAINT [FK_Reviews_User] FOREIGN KEY([UserID]) REFERENCES [dbo].[Users] ([UserID]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_UserPreferences_User' AND parent_object_id = OBJECT_ID('dbo.UserPreferences'))
    ALTER TABLE [dbo].[UserPreferences] WITH CHECK ADD CONSTRAINT [FK_UserPreferences_User] FOREIGN KEY([UserID]) REFERENCES [dbo].[Users] ([UserID]) ON DELETE CASCADE;
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Watchlist_Movie' AND parent_object_id = OBJECT_ID('dbo.Watchlist'))
    ALTER TABLE [dbo].[Watchlist] WITH CHECK ADD CONSTRAINT [FK_Watchlist_Movie] FOREIGN KEY([MovieID]) REFERENCES [dbo].[Movies] ([MovieID]) ON DELETE CASCADE;
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Watchlist_User' AND parent_object_id = OBJECT_ID('dbo.Watchlist'))
    ALTER TABLE [dbo].[Watchlist] WITH CHECK ADD CONSTRAINT [FK_Watchlist_User] FOREIGN KEY([UserID]) REFERENCES [dbo].[Users] ([UserID]) ON DELETE CASCADE;
GO

-- ============================================================
--  CHECK CONSTRAINTS  (add only if not already present)
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CHK_CompatibilityScore' AND parent_object_id = OBJECT_ID('dbo.CollaborativeSessions'))
BEGIN
    ALTER TABLE [dbo].[CollaborativeSessions] WITH CHECK ADD CONSTRAINT [CHK_CompatibilityScore] CHECK (([CompatibilityScore]>=(0) AND [CompatibilityScore]<=(100)));
    ALTER TABLE [dbo].[CollaborativeSessions] CHECK CONSTRAINT [CHK_CompatibilityScore];
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CHK_DifferentUsers' AND parent_object_id = OBJECT_ID('dbo.CollaborativeSessions'))
BEGIN
    ALTER TABLE [dbo].[CollaborativeSessions] WITH CHECK ADD CONSTRAINT [CHK_DifferentUsers] CHECK (([User1ID]<>[User2ID]));
    ALTER TABLE [dbo].[CollaborativeSessions] CHECK CONSTRAINT [CHK_DifferentUsers];
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CHK_AverageRating' AND parent_object_id = OBJECT_ID('dbo.Movies'))
BEGIN
    ALTER TABLE [dbo].[Movies] WITH CHECK ADD CONSTRAINT [CHK_AverageRating] CHECK (([AverageRating]>=(0) AND [AverageRating]<=(5)));
    ALTER TABLE [dbo].[Movies] CHECK CONSTRAINT [CHK_AverageRating];
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CHK_ReleaseYear' AND parent_object_id = OBJECT_ID('dbo.Movies'))
BEGIN
    ALTER TABLE [dbo].[Movies] WITH CHECK ADD CONSTRAINT [CHK_ReleaseYear] CHECK (([ReleaseYear]>=(1888) AND [ReleaseYear]<=(2100)));
    ALTER TABLE [dbo].[Movies] CHECK CONSTRAINT [CHK_ReleaseYear];
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CHK_Runtime' AND parent_object_id = OBJECT_ID('dbo.Movies'))
BEGIN
    ALTER TABLE [dbo].[Movies] WITH CHECK ADD CONSTRAINT [CHK_Runtime] CHECK (([Runtime]>(0)));
    ALTER TABLE [dbo].[Movies] CHECK CONSTRAINT [CHK_Runtime];
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CHK_RatingValue' AND parent_object_id = OBJECT_ID('dbo.Ratings'))
BEGIN
    ALTER TABLE [dbo].[Ratings] WITH CHECK ADD CONSTRAINT [CHK_RatingValue] CHECK (([RatingValue]>=(1.0) AND [RatingValue]<=(5.0)));
    ALTER TABLE [dbo].[Ratings] CHECK CONSTRAINT [CHK_RatingValue];
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CHK_Email' AND parent_object_id = OBJECT_ID('dbo.Users'))
BEGIN
    ALTER TABLE [dbo].[Users] WITH CHECK ADD CONSTRAINT [CHK_Email] CHECK (([Email] like '%_@__%.__%'));
    ALTER TABLE [dbo].[Users] CHECK CONSTRAINT [CHK_Email];
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CHK_UserRole' AND parent_object_id = OBJECT_ID('dbo.Users'))
BEGIN
    ALTER TABLE [dbo].[Users] WITH CHECK ADD CHECK (([Role]='Admin' OR [Role]='User'));
END
GO

-- ============================================================
--  STORED PROCEDURES  (always drop and recreate)
-- ============================================================

-- SP 1: Get User Recommendations
IF OBJECT_ID('dbo.SP_GetUserRecommendations', 'P') IS NOT NULL
    DROP PROCEDURE [dbo].[SP_GetUserRecommendations];
GO
CREATE PROCEDURE [dbo].[SP_GetUserRecommendations]
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
    JOIN MovieGenres mg   ON m.MovieID  = mg.MovieID
    JOIN UserTopGenres utg ON mg.GenreID = utg.GenreID
    WHERE m.MovieID NOT IN (SELECT MovieID FROM Ratings WHERE UserID = @UserID)
      AND m.IsApproved = 1
    GROUP BY m.MovieID, m.Title, m.ReleaseYear, m.AverageRating
    ORDER BY m.AverageRating DESC;
END;
GO

-- SP 2: Calculate Compatibility
IF OBJECT_ID('dbo.SP_CalculateCompatibility', 'P') IS NOT NULL
    DROP PROCEDURE [dbo].[SP_CalculateCompatibility];
GO
CREATE PROCEDURE [dbo].[SP_CalculateCompatibility]
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
    DROP PROCEDURE [dbo].[SP_GetUserStats];
GO
CREATE PROCEDURE [dbo].[SP_GetUserStats]
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT
        u.Username,
        COUNT(DISTINCT r.MovieID)           AS TotalMoviesRated,
        ISNULL(AVG(r.RatingValue), 0)       AS AverageRatingGiven,
        (SELECT TOP 1 g.GenreName
         FROM Ratings r2
         JOIN MovieGenres mg ON r2.MovieID = mg.MovieID
         JOIN Genres g       ON mg.GenreID = g.GenreID
         WHERE r2.UserID = @UserID
         GROUP BY g.GenreName
         ORDER BY COUNT(*) DESC)            AS MostWatchedGenre,
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
    DROP PROCEDURE [dbo].[SP_GetTrendingMovies];
GO
CREATE PROCEDURE [dbo].[SP_GetTrendingMovies]
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

-- ============================================================
USE [master]
GO
ALTER DATABASE [CineMatch] SET READ_WRITE
GO
