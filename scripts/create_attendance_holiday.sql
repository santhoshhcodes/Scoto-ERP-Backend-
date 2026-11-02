-- ========================================================
-- Table: dbo.Attendance_Holiday
-- Database: db2 (Company ERP Database - SCOTO / DB2)
-- Purpose: Office Leave / Festival & Annual Holiday Master
-- ========================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Attendance_Holiday' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.Attendance_Holiday (
        HolidayId INT IDENTITY(1,1) PRIMARY KEY,
        HolidayDate DATE NOT NULL UNIQUE,
        HolidayName NVARCHAR(100) NOT NULL,
        HolidayType NVARCHAR(30) DEFAULT 'OFFICIAL', -- OFFICIAL, FESTIVAL, MANDATORY, OPTIONAL
        Description NVARCHAR(250) NULL,
        Year INT NOT NULL,
        IsActive BIT DEFAULT 1,
        CreatedBy NVARCHAR(50) NULL DEFAULT 'HR Admin',
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedBy NVARCHAR(50) NULL,
        UpdatedAt DATETIME DEFAULT GETDATE()
    );

    CREATE INDEX IX_Attendance_Holiday_Year ON dbo.Attendance_Holiday(Year, IsActive);
    CREATE INDEX IX_Attendance_Holiday_Date ON dbo.Attendance_Holiday(HolidayDate);
    
    PRINT 'Table dbo.Attendance_Holiday created successfully.';
END
ELSE
BEGIN
    PRINT 'Table dbo.Attendance_Holiday already exists.';
END
GO
