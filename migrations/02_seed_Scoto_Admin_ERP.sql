USE [Scoto_Admin_ERP];
GO

-- 1. Base Company Profile
IF NOT EXISTS (SELECT 1 FROM dbo.MstCompany WHERE Ccode = 'SCT')
BEGIN
    INSERT INTO dbo.MstCompany (Ccode, CompanyName, City, State, Country, Status)
    VALUES ('SCT', 'Scoto Systec Private Limited', 'Bengaluru', 'Karnataka', 'India', 'Active');
END
GO

-- 2. Location Units
IF NOT EXISTS (SELECT 1 FROM dbo.LocationMst WHERE Lcode = 'UNIT I')
BEGIN
    INSERT INTO dbo.LocationMst (Ccode, Lcode, LocName, State, Country)
    VALUES ('SCT', 'UNIT I', 'Unit I - Factory & Office', 'Karnataka', 'India');
END
GO

-- 3. Financial Years
IF NOT EXISTS (SELECT 1 FROM dbo.MstFinacialYear WHERE FinacialYear = '2025_2026')
BEGIN
    INSERT INTO dbo.MstFinacialYear (Ccode, Lcode, YearCode, StartingPeriod, EndingPeriod, FinacialYear, ActiveMode, Status)
    VALUES
    ('SCT', 'UNIT I', '1', '01/04/2024', '31/03/2025', '2024_2025', '0', 'Active'),
    ('SCT', 'UNIT I', '2', '01/04/2025', '31/03/2026', '2025_2026', '1', 'Active'),
    ('SCT', 'UNIT I', '3', '01/04/2026', '31/03/2027', '2026-2027', '0', 'Active');
END
GO

-- 4. Primary Accounting Headers
IF NOT EXISTS (SELECT 1 FROM dbo.Acc_Mst_AccountLedgerHeader WHERE AccLedgerHeaderName = 'Assets')
BEGIN
    INSERT INTO dbo.Acc_Mst_AccountLedgerHeader (Ccode, Lcode, AccLedgerHeaderCode, AccLedgerHeaderName, Status)
    VALUES
    ('SCT', 'UNIT I', '01', 'Assets', 'Active'),
    ('SCT', 'UNIT I', '02', 'Liabilities', 'Active'),
    ('SCT', 'UNIT I', '03', 'Income', 'Active'),
    ('SCT', 'UNIT I', '04', 'Expenses', 'Active'),
    ('SCT', 'UNIT I', '05', 'Equity', 'Active');
END
GO

-- 5. Default Super Admin User
IF NOT EXISTS (SELECT 1 FROM dbo.Login WHERE UserId = 'ADMIN')
BEGIN
    INSERT INTO dbo.Login (Ccode, Lcode, UserId, Password)
    VALUES ('SCT', 'UNIT I', 'ADMIN', 'admin@123');

    INSERT INTO dbo.UserDetails (UserID, UserName, Ccode, Lcode, Password, UserType, Status, isActive)
    VALUES ('ADMIN', 'System Administrator', 'SCT', 'UNIT I', 'admin@123', 'SuperAdmin', 'Active', '1');
END
GO

-- 6. Default Attendance Policy
IF NOT EXISTS (SELECT 1 FROM dbo.Attendance_Policy WHERE CompanyCode = 'SCT' AND LocationCode = 'UNIT I')
BEGIN
    INSERT INTO dbo.Attendance_Policy (CompanyCode, LocationCode, ShiftStartTime, ShiftEndTime, GraceMinutes, EffectiveFrom, IsActive, CreatedBy, CreatedAt)
    VALUES ('SCT', 'UNIT I', '09:40:00', '18:30:00', 15, '2020-01-01', 1, 'SYSTEM_INIT', GETDATE());
END
GO

PRINT '[OK] Seed data inserted successfully into [Scoto_Admin_ERP]!';
GO
