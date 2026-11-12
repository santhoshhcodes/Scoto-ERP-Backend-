-- ============================================================================
-- SCOTO ADMIN ERP - MIGRATION SCRIPT: QUOTATION REVISION SUPPORT (0R, 1R, 2R, 3R)
-- Target Database: [Scoto_Admin_ERP]
-- Description: Adds revision tracking, version locking, and history support 
--              for Acc_Quotation_Main and Acc_Quotation_Sub tables.
-- Safe & Idempotent: Can be run multiple times without data loss or error.
-- ============================================================================

-- Note: Select your target database before executing (e.g., USE [SCOTO_ACC_ERP] or USE [Scoto_Admin_ERP])
-- If running in SSMS, ensure the database dropdown at top-left is set to your target database.


SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

PRINT 'Starting migration: Quotation Revision Support...';

-- ============================================================================
-- 1. ADD REVISION COLUMNS TO Acc_Quotation_Main
-- ============================================================================

-- BaseTransNo: Root quotation number (e.g. 'SQ2627-001') linking all versions together
IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'BaseTransNo') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Quotation_Main ADD [BaseTransNo] VARCHAR(50) NULL;
    PRINT 'Added column BaseTransNo to Acc_Quotation_Main';
END
GO

-- RevNo: Numeric version counter: 0 (Original), 1 (1R), 2 (2R), 3 (3R)
IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'RevNo') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Quotation_Main ADD [RevNo] INT NOT NULL CONSTRAINT DF_Acc_Quotation_Main_RevNo DEFAULT 0;
    PRINT 'Added column RevNo to Acc_Quotation_Main';
END
GO

-- RevLabel: Display version label ('ORIGINAL', '1R', '2R', '3R')
IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'RevLabel') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Quotation_Main ADD [RevLabel] VARCHAR(10) NOT NULL CONSTRAINT DF_Acc_Quotation_Main_RevLabel DEFAULT 'ORIGINAL';
    PRINT 'Added column RevLabel to Acc_Quotation_Main';
END
GO

-- IsActiveRevision: 1 for the current latest active version, 0 when superseded
IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'IsActiveRevision') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Quotation_Main ADD [IsActiveRevision] BIT NOT NULL CONSTRAINT DF_Acc_Quotation_Main_IsActive DEFAULT 1;
    PRINT 'Added column IsActiveRevision to Acc_Quotation_Main';
END
GO

-- IsLocked: 1 when RevNo >= 3 (hard limit reached, no further revisions allowed)
IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'IsLocked') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Quotation_Main ADD [IsLocked] BIT NOT NULL CONSTRAINT DF_Acc_Quotation_Main_IsLocked DEFAULT 0;
    PRINT 'Added column IsLocked to Acc_Quotation_Main';
END
GO

-- RevReason: Business reason / negotiation remark for the revision
IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'RevReason') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Quotation_Main ADD [RevReason] NVARCHAR(500) NULL;
    PRINT 'Added column RevReason to Acc_Quotation_Main';
END
GO

-- ParentTransNo: Direct predecessor (e.g. for SQ2627-001-2R, parent is SQ2627-001-1R)
IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'ParentTransNo') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Quotation_Main ADD [ParentTransNo] VARCHAR(50) NULL;
    PRINT 'Added column ParentTransNo to Acc_Quotation_Main';
END
GO

-- SupersededOn: Timestamp when this revision was replaced by a newer one
IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'SupersededOn') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Quotation_Main ADD [SupersededOn] DATETIME NULL;
    PRINT 'Added column SupersededOn to Acc_Quotation_Main';
END
GO


-- ============================================================================
-- 2. ADD REVISION COLUMN TO Acc_Quotation_Sub (Line Items)
-- ============================================================================

-- BaseTransNo: Allows direct grouping of line items across all versions
IF COL_LENGTH(N'dbo.Acc_Quotation_Sub', N'BaseTransNo') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Quotation_Sub ADD [BaseTransNo] VARCHAR(50) NULL;
    PRINT 'Added column BaseTransNo to Acc_Quotation_Sub';
END
GO


-- ============================================================================
-- 3. SAFE DATA BACKFILL FOR EXISTING QUOTATIONS
-- ============================================================================

PRINT 'Backfilling existing quotation records...';

UPDATE dbo.Acc_Quotation_Main
SET 
    [BaseTransNo] = ISNULL([BaseTransNo], [TransNo]),
    [RevNo] = ISNULL([RevNo], 0),
    [RevLabel] = ISNULL([RevLabel], 'ORIGINAL'),
    [IsActiveRevision] = ISNULL([IsActiveRevision], 1),
    [IsLocked] = ISNULL([IsLocked], 0)
WHERE [BaseTransNo] IS NULL OR [RevNo] IS NULL;
GO

UPDATE dbo.Acc_Quotation_Sub
SET 
    [BaseTransNo] = ISNULL([BaseTransNo], [TransNo])
WHERE [BaseTransNo] IS NULL;
GO

PRINT 'Quotation Revision Support migration completed successfully!';
GO

-- ============================================================================
-- 4. VERIFICATION QUERY (Run this to verify the changes)
-- ============================================================================
SELECT TOP 10
    [TransNo],
    [BaseTransNo],
    [RevNo],
    [RevLabel],
    [IsActiveRevision],
    [IsLocked],
    [CustomerName],
    [NetAmount]
FROM dbo.Acc_Quotation_Main
ORDER BY [TransNo] DESC;
GO

