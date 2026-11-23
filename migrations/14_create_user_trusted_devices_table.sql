USE [Scoto_Admin_ERP];
GO

-- ============================================================================
-- Migration 14: Create UserTrustedDevices Table for Adaptive 2FA Device Trust
-- Target Database: [Scoto_Admin_ERP]
-- Purpose: Track recognized browser / device fingerprints per user
-- ============================================================================

IF OBJECT_ID(N'dbo.[UserTrustedDevices]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[UserTrustedDevices] (
        [DeviceId] VARCHAR(100) NOT NULL,
        [UserId] VARCHAR(50) NOT NULL,
        [Ccode] VARCHAR(50) NOT NULL,
        [Lcode] VARCHAR(50) NOT NULL,
        [DeviceName] VARCHAR(150) NULL,
        [BrowserAgent] VARCHAR(500) NULL,
        [IPAddress] VARCHAR(50) NULL,
        [IsTrusted] BIT DEFAULT 1,
        [FirstLoginAt] DATETIME DEFAULT GETDATE(),
        [LastLoginAt] DATETIME DEFAULT GETDATE(),
        CONSTRAINT PK_UserTrustedDevices PRIMARY KEY ([DeviceId], [UserId])
    );

    CREATE INDEX IX_UserTrustedDevices_Lookup 
        ON dbo.[UserTrustedDevices] ([UserId], [DeviceId], [IsTrusted]);
END
GO
