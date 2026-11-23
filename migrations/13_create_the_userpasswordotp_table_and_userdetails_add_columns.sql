USE [Scoto_Admin_ERP];
GO

-- 1. Create the OTP Tracking Table
IF OBJECT_ID(N'dbo.[UserPasswordOTP]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[UserPasswordOTP] (
        [OTPId] INT IDENTITY(1,1) PRIMARY KEY,
        [Ccode] VARCHAR(50) NOT NULL,
        [Lcode] VARCHAR(50) NOT NULL,
        [UserId] VARCHAR(50) NOT NULL,
        [Email] VARCHAR(150) NOT NULL,
        [OTPCode] VARCHAR(10) NOT NULL,
        [Purpose] VARCHAR(50) NOT NULL, -- 'FIRST_TIME_SETUP' or 'FORGOT_PASSWORD'
        [ExpiresAt] DATETIME NOT NULL,
        [IsUsed] BIT DEFAULT 0,
        [AttemptsCount] INT DEFAULT 0,
        [CreatedAt] DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_UserPasswordOTP_User ON dbo.[UserPasswordOTP] ([UserId], [OTPCode], [IsUsed]);
END
GO

-- 2. Add Email & First-Login flags to UserDetails (if not already existing)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.[UserDetails]') AND name = 'Email')
BEGIN
    ALTER TABLE dbo.[UserDetails] ADD [Email] VARCHAR(150) NULL;
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.[UserDetails]') AND name = 'IsFirstLogin')
BEGIN
    ALTER TABLE dbo.[UserDetails] ADD [IsFirstLogin] BIT DEFAULT 1;
END
GO

-- 3. CRITICAL: Expand Password column size in Login table
-- Current column is VARCHAR(50). Modern bcrypt password hashes are 60 characters long.
-- Expanding to VARCHAR(255) prevents password truncation errors.
ALTER TABLE dbo.[Login] ALTER COLUMN [Password] VARCHAR(255) NULL;
GO

-- 4. Set the Admin's official email address (replace 'ADMIN' with your actual admin UserId)
UPDATE dbo.[UserDetails]
SET [Email] = 'scotosystecadmin@gmail.com'
WHERE [UserID] = 'ADMIN'; -- or your specific admin ID
GO