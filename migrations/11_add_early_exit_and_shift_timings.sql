-- ============================================================================
-- SCOTO ADMIN ERP - MIGRATION SCRIPT 11: ATTENDANCE ENHANCEMENTS
-- Target Database: [Scoto_Admin_ERP] / [scotoAdmin]
-- Description: 
--   1. Adds custom shift timings (ShiftStartTime, ShiftEndTime) to Employee_Mst.
--   2. Adds early exit & fine tracking columns to Attendance_Late_Fine.
--   3. Safely verifies ClientCode, ClientName, PlaceOfVisit on Attendance_Daily_Review.
--   4. Backfills default values for existing attendance records.
-- Safe & Idempotent: Can be run multiple times without error or data loss.
-- ============================================================================

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

PRINT 'Starting migration: 11_add_early_exit_and_shift_timings...';

-- ============================================================================
-- 1. ADD SHIFT TIMINGS TO Employee_Mst
-- ============================================================================

IF OBJECT_ID(N'dbo.Employee_Mst', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Employee_Mst', N'ShiftStartTime') IS NULL
BEGIN
    ALTER TABLE dbo.Employee_Mst
    ADD [ShiftStartTime] TIME(7) NULL;
    PRINT 'Added ShiftStartTime to Employee_Mst';
END;
GO

IF OBJECT_ID(N'dbo.Employee_Mst', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Employee_Mst', N'ShiftEndTime') IS NULL
BEGIN
    ALTER TABLE dbo.Employee_Mst
    ADD [ShiftEndTime] TIME(7) NULL;
    PRINT 'Added ShiftEndTime to Employee_Mst';
END;
GO

-- ============================================================================
-- 2. ADD EARLY EXIT & CLOSING COLUMNS TO Attendance_Late_Fine
-- ============================================================================

IF OBJECT_ID(N'dbo.Attendance_Late_Fine', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Attendance_Late_Fine', N'ActualCheckOut') IS NULL
BEGIN
    ALTER TABLE dbo.Attendance_Late_Fine
    ADD [ActualCheckOut] DATETIME2(7) NULL;
    PRINT 'Added ActualCheckOut to Attendance_Late_Fine';
END;
GO

IF OBJECT_ID(N'dbo.Attendance_Late_Fine', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Attendance_Late_Fine', N'ShiftEndTime') IS NULL
BEGIN
    ALTER TABLE dbo.Attendance_Late_Fine
    ADD [ShiftEndTime] TIME(7) NULL;
    PRINT 'Added ShiftEndTime to Attendance_Late_Fine';
END;
GO

IF OBJECT_ID(N'dbo.Attendance_Late_Fine', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Attendance_Late_Fine', N'EarlyExitMinutes') IS NULL
BEGIN
    ALTER TABLE dbo.Attendance_Late_Fine
    ADD [EarlyExitMinutes] INT NULL CONSTRAINT DF_Attendance_Late_Fine_EarlyExit DEFAULT 0;
    PRINT 'Added EarlyExitMinutes to Attendance_Late_Fine';
END;
GO

IF OBJECT_ID(N'dbo.Attendance_Late_Fine', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Attendance_Late_Fine', N'EarlyPermissionMinutes') IS NULL
BEGIN
    ALTER TABLE dbo.Attendance_Late_Fine
    ADD [EarlyPermissionMinutes] INT NULL CONSTRAINT DF_Attendance_Late_Fine_EarlyPerm DEFAULT 0;
    PRINT 'Added EarlyPermissionMinutes to Attendance_Late_Fine';
END;
GO

IF OBJECT_ID(N'dbo.Attendance_Late_Fine', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Attendance_Late_Fine', N'FineType') IS NULL
BEGIN
    ALTER TABLE dbo.Attendance_Late_Fine
    ADD [FineType] VARCHAR(50) NULL CONSTRAINT DF_Attendance_Late_Fine_FineType DEFAULT 'LATE';
    PRINT 'Added FineType to Attendance_Late_Fine';
END;
GO

-- ============================================================================
-- 3. ENSURE CLIENT SITE COLUMNS IN Attendance_Daily_Review (FROM MIGRATION 05)
-- ============================================================================

IF OBJECT_ID(N'dbo.Attendance_Daily_Review', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Attendance_Daily_Review', N'ClientCode') IS NULL
BEGIN
    ALTER TABLE dbo.Attendance_Daily_Review
    ADD [ClientCode] VARCHAR(50) NULL;
    PRINT 'Added ClientCode to Attendance_Daily_Review';
END;
GO

IF OBJECT_ID(N'dbo.Attendance_Daily_Review', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Attendance_Daily_Review', N'ClientName') IS NULL
BEGIN
    ALTER TABLE dbo.Attendance_Daily_Review
    ADD [ClientName] NVARCHAR(250) NULL;
    PRINT 'Added ClientName to Attendance_Daily_Review';
END;
GO

IF OBJECT_ID(N'dbo.Attendance_Daily_Review', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Attendance_Daily_Review', N'PlaceOfVisit') IS NULL
BEGIN
    ALTER TABLE dbo.Attendance_Daily_Review
    ADD [PlaceOfVisit] NVARCHAR(250) NULL;
    PRINT 'Added PlaceOfVisit to Attendance_Daily_Review';
END;
GO

-- ============================================================================
-- 4. SAFE BACKFILL FOR EXISTING FINE RECORDS
-- ============================================================================

IF OBJECT_ID(N'dbo.Attendance_Late_Fine', N'U') IS NOT NULL
BEGIN
    UPDATE dbo.Attendance_Late_Fine
    SET [FineType] = 'LATE'
    WHERE [FineType] IS NULL;

    UPDATE dbo.Attendance_Late_Fine
    SET [EarlyExitMinutes] = 0
    WHERE [EarlyExitMinutes] IS NULL;

    UPDATE dbo.Attendance_Late_Fine
    SET [EarlyPermissionMinutes] = 0
    WHERE [EarlyPermissionMinutes] IS NULL;
    PRINT 'Backfilled existing Attendance_Late_Fine default values';
END;
GO

PRINT 'Migration 11 completed successfully!';
GO
