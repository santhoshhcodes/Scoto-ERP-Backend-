-- Migration 05: Add ClientCode, ClientName, and PlaceOfVisit to Attendance_Daily_Review
-- Allows dedicated, structured tracking of on-site deployments and client visits

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Attendance_Daily_Review' AND COLUMN_NAME = 'ClientCode'
)
BEGIN
    ALTER TABLE dbo.Attendance_Daily_Review
    ADD ClientCode VARCHAR(50) NULL;
    PRINT 'Added ClientCode column to Attendance_Daily_Review';
END
GO

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Attendance_Daily_Review' AND COLUMN_NAME = 'ClientName'
)
BEGIN
    ALTER TABLE dbo.Attendance_Daily_Review
    ADD ClientName NVARCHAR(250) NULL;
    PRINT 'Added ClientName column to Attendance_Daily_Review';
END
GO

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Attendance_Daily_Review' AND COLUMN_NAME = 'PlaceOfVisit'
)
BEGIN
    ALTER TABLE dbo.Attendance_Daily_Review
    ADD PlaceOfVisit NVARCHAR(250) NULL;
    PRINT 'Added PlaceOfVisit column to Attendance_Daily_Review';
END
GO

