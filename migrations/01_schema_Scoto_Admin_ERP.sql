-- ============================================================================
-- SCOTO ADMIN ERP - PRODUCTION MASTER DDL SCHEMA SCRIPT
-- Target Database: [Scoto_Admin_ERP]
-- Tables: Exactly 33 core tables used by FastAPI backend & React frontend
-- Generated directly from production schema specifications in Microsoft SQL Server
-- ============================================================================

USE [Scoto_Admin_ERP];
GO

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

-- ============================================================================
-- Table 1: dbo.[MstCompany]
-- ============================================================================
IF OBJECT_ID(N'dbo.[MstCompany]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[MstCompany] (
        [Ccode] VARCHAR(50) NULL,
        [CompanyName] VARCHAR(150) NULL,
        [Address1] VARCHAR(150) NULL,
        [Address2] VARCHAR(150) NULL,
        [City] VARCHAR(150) NULL,
        [PinCode] VARCHAR(50) NULL,
        [State] VARCHAR(150) NULL,
        [Country] VARCHAR(150) NULL,
        [PhoneCode] VARCHAR(50) NULL,
        [PhoneNo] VARCHAR(150) NULL,
        [MobileCode] VARCHAR(50) NULL,
        [Mobile] VARCHAR(150) NULL,
        [MailID] VARCHAR(150) NULL,
        [TinNo] VARCHAR(150) NULL,
        [GSTNo] VARCHAR(150) NULL,
        [PanNo] VARCHAR(150) NULL,
        [Others] VARCHAR(250) NULL,
        [IP] VARCHAR(250) NULL,
        [SystemName] VARCHAR(250) NULL,
        [UserID] VARCHAR(50) NULL,
        [UserName] VARCHAR(50) NULL,
        [CreateOn] NVARCHAR(100) NULL,
        [Status] NVARCHAR(50) NULL
    );
END
GO

-- ============================================================================
-- Table 2: dbo.[LocationMst]
-- ============================================================================
IF OBJECT_ID(N'dbo.[LocationMst]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[LocationMst] (
        [Ccode] VARCHAR(50) NULL,
        [Lcode] VARCHAR(50) NULL,
        [LocName] VARCHAR(150) NULL,
        [LocAddress] VARCHAR(250) NULL,
        [GSTNo] VARCHAR(500) NULL,
        [District] VARCHAR(250) NULL,
        [State] VARCHAR(250) NULL,
        [Country] VARCHAR(250) NULL,
        [PIN] VARCHAR(250) NULL
    );
END
GO

-- ============================================================================
-- Table 3: dbo.[MstFinacialYear]
-- ============================================================================
IF OBJECT_ID(N'dbo.[MstFinacialYear]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[MstFinacialYear] (
        [Ccode] NVARCHAR(50) NULL,
        [Lcode] NVARCHAR(50) NULL,
        [YearCode] NVARCHAR(50) NULL,
        [StartingPeriod] NVARCHAR(50) NULL,
        [EndingPeriod] NVARCHAR(50) NULL,
        [FinacialYear] NVARCHAR(50) NULL,
        [ActiveMode] NVARCHAR(50) NULL,
        [Status] NVARCHAR(50) NULL,
        [IP] NVARCHAR(50) NULL,
        [SystemName] NVARCHAR(50) NULL,
        [UserID] NVARCHAR(50) NULL,
        [UserName] NVARCHAR(150) NULL,
        [CreateOn] NVARCHAR(50) NULL,
        [OpeningBalance] NUMERIC(18,2) NULL DEFAULT 0,
        [BalanceType] VARCHAR(10) NULL DEFAULT 'Dr'
    );
END
GO

-- ============================================================================
-- Table 4: dbo.[Login]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Login]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Login] (
        [Ccode] VARCHAR(50) NULL,
        [Lcode] VARCHAR(50) NULL,
        [UserId] VARCHAR(50) NULL,
        [Password] VARCHAR(50) NULL,
        [isLoggedIN] BIT NULL
    );
END
GO

-- ============================================================================
-- Table 5: dbo.[UserDetails]
-- ============================================================================
IF OBJECT_ID(N'dbo.[UserDetails]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[UserDetails] (
        [Ccode] VARCHAR(50) NULL,
        [Lcode] VARCHAR(50) NULL,
        [UserName] VARCHAR(50) NULL,
        [UserID] VARCHAR(50) NULL,
        [Password] VARCHAR(MAX) NULL,
        [Designation] VARCHAR(50) NULL,
        [isActive] VARCHAR(50) NULL,
        [DesigCode] VARCHAR(50) NULL,
        [Host_IP] VARCHAR(50) NULL,
        [Host_Name] VARCHAR(50) NULL,
        [Status] VARCHAR(50) NULL,
        [CreatedBy] VARCHAR(50) NULL,
        [CreatedOn] VARCHAR(50) NULL,
        [UserType] VARCHAR(50) NULL,
        [profileImg] VARCHAR(500) NULL,
        [DeptName] NVARCHAR(150) NULL
    );
END
GO

-- ============================================================================
-- Table 6: dbo.[Acc_Mst_AccountLedgerHeader]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Acc_Mst_AccountLedgerHeader]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Acc_Mst_AccountLedgerHeader] (
        [Ccode] NVARCHAR(50) NULL,
        [Lcode] NVARCHAR(50) NULL,
        [AccCateCode] NVARCHAR(50) NULL,
        [AccCateName] NVARCHAR(MAX) NULL,
        [AccGroupCode] NVARCHAR(150) NULL,
        [AccGroupName] NVARCHAR(MAX) NULL,
        [AccSubGroupCode] NVARCHAR(150) NULL,
        [AccSubGroupName] NVARCHAR(MAX) NULL,
        [AccLedgerHeaderCode] NVARCHAR(150) NULL,
        [AccLedgerHeaderName] NVARCHAR(MAX) NULL,
        [Status] NVARCHAR(50) NULL,
        [UserId] NVARCHAR(50) NULL,
        [UserName] NVARCHAR(500) NULL,
        [CreateOn] NVARCHAR(50) NULL,
        [SysIp] NVARCHAR(50) NULL,
        [SysName] NVARCHAR(50) NULL
    );
END
GO

-- ============================================================================
-- Table 7: dbo.[Acc_Mst_GeneralLedger]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Acc_Mst_GeneralLedger]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Acc_Mst_GeneralLedger] (
        [Ccode] NVARCHAR(50) NULL,
        [Lcode] NVARCHAR(50) NULL,
        [AccCateCode] VARCHAR(50) NULL,
        [AccCateName] NVARCHAR(MAX) NULL,
        [AccGroupCode] NVARCHAR(50) NULL,
        [AccGroupName] NVARCHAR(MAX) NULL,
        [AccSubGrpCode] NVARCHAR(150) NULL,
        [AccSubGrpName] NVARCHAR(MAX) NULL,
        [AccLedgerHeaderCode] NVARCHAR(150) NULL,
        [AccLedgerHeaderName] NVARCHAR(MAX) NULL,
        [AccGenLdgCode] NVARCHAR(150) NULL,
        [AccGenLdgName] NVARCHAR(MAX) NULL,
        [CostCenter] NVARCHAR(MAX) NULL,
        [Status] NVARCHAR(50) NULL,
        [SysIp] NVARCHAR(50) NULL,
        [SysName] NVARCHAR(150) NULL,
        [UserID] NVARCHAR(50) NULL,
        [UserName] NVARCHAR(50) NULL,
        [CreateOn] NVARCHAR(50) NULL,
        [OpeningBalance] NUMERIC(18,2) NULL DEFAULT 0,
        [BalanceType] VARCHAR(10) NULL DEFAULT 'Dr'
    );
END
GO

-- ============================================================================
-- Table 8: dbo.[Acc_Mst_Ledger]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Acc_Mst_Ledger]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Acc_Mst_Ledger] (
        [Ccode] NVARCHAR(50) NULL,
        [Lcode] NVARCHAR(50) NULL,
        [LedgerCode] VARCHAR(50) NULL,
        [LedgerGrpId] NVARCHAR(50) NULL,
        [LedgerGrpName] NVARCHAR(250) NULL,
        [LedgerCategory] VARCHAR(50) NULL,
        [Region] NVARCHAR(150) NULL,
        [SupplyFor] NVARCHAR(250) NULL,
        [LedgerName] NVARCHAR(MAX) NULL,
        [ChequePrintName] NVARCHAR(MAX) NULL,
        [Ledger_Class] VARCHAR(50) NULL,
        [HouseNo] NVARCHAR(50) NULL,
        [Add1] NVARCHAR(750) NULL,
        [Add2] NVARCHAR(750) NULL,
        [City] NVARCHAR(750) NULL,
        [PinCode] NVARCHAR(50) NULL,
        [State] NVARCHAR(750) NULL,
        [Country] NVARCHAR(750) NULL,
        [MobileNo] NVARCHAR(50) NULL,
        [TelNo] NVARCHAR(50) NULL,
        [ContectName] NVARCHAR(MAX) NULL,
        [ContectNo] NVARCHAR(MAX) NULL,
        [MailID] NVARCHAR(50) NULL,
        [WebSite] NVARCHAR(250) NULL,
        [BankId] NVARCHAR(50) NULL,
        [BankName] NVARCHAR(750) NULL,
        [AccountNo] NVARCHAR(750) NULL,
        [BranchName] NVARCHAR(750) NULL,
        [Branch_Addr] VARCHAR(750) NULL,
        [IFSCCode] NVARCHAR(750) NULL,
        [SWIFTCode] NVARCHAR(750) NULL,
        [IBANCode] NVARCHAR(750) NULL,
        [GSTNo] NVARCHAR(150) NULL,
        [CINNo] NVARCHAR(150) NULL,
        [PanNo] NVARCHAR(150) NULL,
        [TanNo] NVARCHAR(150) NULL,
        [IECode] NVARCHAR(150) NULL,
        [LEICode] NVARCHAR(150) NULL,
        [MSME_Status] NVARCHAR(150) NULL,
        [MSME_No] NVARCHAR(150) NULL,
        [PaymentDays] NVARCHAR(150) NULL,
        [DayCondition] NVARCHAR(150) NULL,
        [AdvancePayment] NVARCHAR(150) NULL,
        [AdvanceCondition] NVARCHAR(150) NULL,
        [Inco_Terms] VARCHAR(MAX) NULL,
        [PaymentTerms] VARCHAR(150) NULL,
        [TC] NVARCHAR(MAX) NULL,
        [PackingTerms] NVARCHAR(MAX) NULL,
        [Quality] NVARCHAR(MAX) NULL,
        [Warranty] NVARCHAR(MAX) NULL,
        [AccountTypeCode] NVARCHAR(50) NULL,
        [AccountType] NVARCHAR(100) NULL,
        [PaymentBlock] NVARCHAR(150) NULL,
        [SupplierBlock] NVARCHAR(150) NULL,
        [RoundOff] NVARCHAR(150) NULL,
        [Status] NVARCHAR(750) NULL,
        [IsActive] NVARCHAR(150) NULL,
        [Approval_Status] NVARCHAR(50) NULL,
        [SysIp] NVARCHAR(50) NULL,
        [SysName] NVARCHAR(150) NULL,
        [UserID] NVARCHAR(750) NULL,
        [UserName] NVARCHAR(750) NULL,
        [CreateOn] NVARCHAR(750) NULL,
        [ApprovedBy] NVARCHAR(150) NULL,
        [ApprovedOn] NVARCHAR(150) NULL,
        [AccGrpCode] NVARCHAR(50) NULL,
        [AccGrpName] NVARCHAR(150) NULL,
        [LedgerNameCategory] VARCHAR(150) NULL,
        [MSME_Certificate_No] NVARCHAR(150) NULL,
        [Supplier_Status] NVARCHAR(50) NULL,
        [Inco_Terms1] VARCHAR(MAX) NULL,
        [Inco_Terms2] VARCHAR(MAX) NULL,
        [Inco_Terms3] VARCHAR(MAX) NULL,
        [Area] NVARCHAR(MAX) NULL,
        [LedgerType] NVARCHAR(150) NULL,
        [OpeningBalance] NUMERIC(18,2) NULL DEFAULT 0,
        [BalanceType] VARCHAR(10) NULL DEFAULT 'Cr'
    );
END
GO

-- ============================================================================
-- Table 9: dbo.[Mst_Item]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Mst_Item]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Mst_Item] (
        [ItemCode] VARCHAR(50) NULL,
        [ItemType] VARCHAR(250) NULL,
        [ItemDescription] VARCHAR(MAX) NULL,
        [ProductType] NVARCHAR(50) NULL,
        [HSNCode] VARCHAR(50) NULL,
        [UOM] VARCHAR(50) NULL,
        [SerialNo] NVARCHAR(150) NULL,
        [Ccode] NVARCHAR(10) NULL,
        [Lcode] NVARCHAR(10) NULL,
        [Status] VARCHAR(50) NULL,
        [Host_IP] VARCHAR(50) NULL,
        [Host_Name] VARCHAR(50) NULL,
        [UserCode] NVARCHAR(50) NULL,
        [UserName] VARCHAR(50) NULL,
        [CreatedOn] NVARCHAR(50) NULL
    );
END
GO

-- ============================================================================
-- Table 10: dbo.[Employee_Mst]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Employee_Mst]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Employee_Mst] (
        [EmployeeId] BIGINT IDENTITY(1,1) NOT NULL,
        [EmployeeCode] VARCHAR(50) NOT NULL,
        [FirstName] NVARCHAR(100) NOT NULL,
        [MiddleName] NVARCHAR(100) NULL,
        [LastName] NVARCHAR(100) NULL,
        [DisplayName] NVARCHAR(250) NULL,
        [ProfilePhotoPath] NVARCHAR(500) NULL,
        [DateOfBirth] DATE NULL,
        [Gender] VARCHAR(20) NULL,
        [BloodGroup] VARCHAR(5) NULL,
        [MaritalStatus] VARCHAR(20) NULL,
        [Nationality] NVARCHAR(50) NULL,
        [MobileNumber] VARCHAR(20) NULL,
        [AlternateMobileNumber] VARCHAR(20) NULL,
        [Email] NVARCHAR(254) NULL,
        [AddressLine1] NVARCHAR(250) NULL,
        [AddressLine2] NVARCHAR(250) NULL,
        [City] NVARCHAR(100) NULL,
        [District] NVARCHAR(100) NULL,
        [State] NVARCHAR(100) NULL,
        [PostalCode] VARCHAR(15) NULL,
        [Country] NVARCHAR(100) NULL,
        [FatherName] NVARCHAR(200) NULL,
        [FatherMobileNumber] VARCHAR(20) NULL,
        [MotherName] NVARCHAR(200) NULL,
        [MotherMobileNumber] VARCHAR(20) NULL,
        [EmergencyContactName] NVARCHAR(200) NULL,
        [EmergencyContactNumber] VARCHAR(20) NULL,
        [EmergencyContactRelation] NVARCHAR(50) NULL,
        [DateOfJoining] DATE NULL,
        [DateOfLeaving] DATE NULL,
        [EmploymentType] VARCHAR(30) NULL,
        [EmploymentStatus] VARCHAR(30) DEFAULT ('ACTIVE') NOT NULL,
        [CompanyCode] VARCHAR(20) NULL,
        [CompanyName] NVARCHAR(150) NULL,
        [LocationCode] VARCHAR(50) NULL,
        [LocationName] NVARCHAR(150) NULL,
        [DepartmentId] INT NULL,
        [DepartmentName] NVARCHAR(100) NULL,
        [DesignationId] INT NULL,
        [DesignationName] NVARCHAR(100) NULL,
        [JobTitle] NVARCHAR(100) NULL,
        [ReportingManagerCode] VARCHAR(50) NULL,
        [AppRole] VARCHAR(30) NULL,
        [IsAppUser] BIT DEFAULT ((0)) NOT NULL,
        [EmployeeSource] VARCHAR(20) DEFAULT ('MANUAL') NOT NULL,
        [ESSLEmployeeCode] VARCHAR(50) NULL,
        [ESSLStatus] VARCHAR(30) DEFAULT ('NOT_LINKED') NOT NULL,
        [ESSLSyncedAt] DATETIME2(7) NULL,
        [BankName] NVARCHAR(150) NULL,
        [BankBranch] NVARCHAR(150) NULL,
        [AccountHolderName] NVARCHAR(200) NULL,
        [AccountNumber] VARCHAR(50) NULL,
        [IFSCCode] VARCHAR(20) NULL,
        [AccountType] VARCHAR(30) NULL,
        [AadhaarNumber] VARCHAR(12) NULL,
        [PANNumber] VARCHAR(10) NULL,
        [PFApplicable] BIT NULL,
        [PFUAN] VARCHAR(30) NULL,
        [PFNumber] VARCHAR(50) NULL,
        [PFJoiningDate] DATE NULL,
        [ESIApplicable] BIT NULL,
        [ESINumber] VARCHAR(30) NULL,
        [SalaryGrade] VARCHAR(30) NULL,
        [PayFrequency] VARCHAR(20) DEFAULT ('MONTHLY') NULL,
        [SalaryEffectiveFrom] DATE NULL,
        [BasicSalary] DECIMAL(12,2) NULL,
        [HRA] DECIMAL(12,2) NULL,
        [DA] DECIMAL(12,2) NULL,
        [OtherAllowances] DECIMAL(12,2) NULL,
        [GrossSalary] DECIMAL(12,2) NULL,
        [EmployeePFContribution] DECIMAL(12,2) NULL,
        [EmployerPFContribution] DECIMAL(12,2) NULL,
        [EmployeeESIContribution] DECIMAL(12,2) NULL,
        [EmployerESIContribution] DECIMAL(12,2) NULL,
        [ProfessionalTax] DECIMAL(12,2) NULL,
        [OtherDeductions] DECIMAL(12,2) NULL,
        [NetSalary] DECIMAL(12,2) NULL,
        [PreviousGrossSalary] DECIMAL(12,2) NULL,
        [LastSalaryRevisionDate] DATE NULL,
        [SalaryRemarks] NVARCHAR(500) NULL,
        [Notes] NVARCHAR(1000) NULL,
        [IsActive] BIT DEFAULT ((1)) NOT NULL,
        [CreatedBy] VARCHAR(50) NULL,
        [CreatedAt] DATETIME2(7) DEFAULT (sysdatetime()) NOT NULL,
        [UpdatedBy] VARCHAR(50) NULL,
        [UpdatedAt] DATETIME2(7) NULL,
        [IsOnSite] BIT DEFAULT ((0)) NOT NULL,
        CONSTRAINT [PK_Employee_Mst] PRIMARY KEY CLUSTERED ([EmployeeId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_Employee_Mst_EmployeeCode' AND object_id = OBJECT_ID('dbo.[Employee_Mst]'))
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX [UQ_Employee_Mst_EmployeeCode] ON dbo.[Employee_Mst] ([EmployeeCode]);
END
GO

-- ============================================================================
-- Table 11: dbo.[Attendance_Policy]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Attendance_Policy]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Attendance_Policy] (
        [PolicyId] INT IDENTITY(1,1) NOT NULL,
        [CompanyCode] VARCHAR(20) DEFAULT ('SCT') NOT NULL,
        [LocationCode] VARCHAR(50) DEFAULT ('UNIT I') NOT NULL,
        [ShiftStartTime] TIME(7) DEFAULT ('09:40:00') NOT NULL,
        [ShiftEndTime] TIME(7) NULL,
        [GraceMinutes] INT DEFAULT ((0)) NULL,
        [EffectiveFrom] DATE DEFAULT ('2026-01-01') NOT NULL,
        [EffectiveTo] DATE NULL,
        [IsActive] BIT DEFAULT ((1)) NOT NULL,
        [CreatedBy] VARCHAR(50) NULL,
        [CreatedAt] DATETIME2(7) DEFAULT (sysdatetime()) NOT NULL,
        [UpdatedBy] VARCHAR(50) NULL,
        [UpdatedAt] DATETIME2(7) NULL,
        CONSTRAINT [PK_Attendance_Policy] PRIMARY KEY CLUSTERED ([PolicyId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_AttendancePolicy_CompanyLocation' AND object_id = OBJECT_ID('dbo.[Attendance_Policy]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_AttendancePolicy_CompanyLocation] ON dbo.[Attendance_Policy] ([CompanyCode], [LocationCode], [IsActive], [EffectiveFrom]);
END
GO

-- ============================================================================
-- Table 12: dbo.[Attendance_Daily_Review]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Attendance_Daily_Review]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Attendance_Daily_Review] (
        [ReviewId] BIGINT IDENTITY(1,1) NOT NULL,
        [EmployeeCode] VARCHAR(50) NOT NULL,
        [AttendanceDate] DATE NOT NULL,
        [ReviewStatus] VARCHAR(30) DEFAULT ('PENDING_REVIEW') NOT NULL,
        [ReviewCategory] VARCHAR(30) NULL,
        [ReviewReason] NVARCHAR(500) NULL,
        [CorrectedCheckIn] DATETIME2(7) NULL,
        [CorrectedCheckOut] DATETIME2(7) NULL,
        [ReviewedBy] VARCHAR(50) NULL,
        [ReviewedAt] DATETIME2(7) NULL,
        [CreatedBy] VARCHAR(50) NULL,
        [CreatedAt] DATETIME2(7) DEFAULT (sysdatetime()) NOT NULL,
        [UpdatedBy] VARCHAR(50) NULL,
        [UpdatedAt] DATETIME2(7) NULL,
        CONSTRAINT [PK_Attendance_Daily_Review] PRIMARY KEY CLUSTERED ([ReviewId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_AttendanceReview_DateStatus' AND object_id = OBJECT_ID('dbo.[Attendance_Daily_Review]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_AttendanceReview_DateStatus] ON dbo.[Attendance_Daily_Review] ([AttendanceDate], [ReviewStatus]);
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_AttendanceDailyReview_EmployeeDate' AND object_id = OBJECT_ID('dbo.[Attendance_Daily_Review]'))
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX [UQ_AttendanceDailyReview_EmployeeDate] ON dbo.[Attendance_Daily_Review] ([EmployeeCode], [AttendanceDate]);
END
GO

-- ============================================================================
-- Table 13: dbo.[Attendance_Leave]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Attendance_Leave]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Attendance_Leave] (
        [LeaveId] BIGINT IDENTITY(1,1) NOT NULL,
        [EmployeeCode] VARCHAR(50) NOT NULL,
        [StartDate] DATE NOT NULL,
        [EndDate] DATE NOT NULL,
        [LeaveType] VARCHAR(20) NOT NULL,
        [LeaveDays] DECIMAL(5,2) NOT NULL,
        [LeaveSession] VARCHAR(20) NULL,
        [SessionStartTime] TIME(7) NULL,
        [SessionEndTime] TIME(7) NULL,
        [Reason] NVARCHAR(500) NULL,
        [ApprovalStatus] VARCHAR(20) DEFAULT ('PENDING') NOT NULL,
        [ApprovedBy] VARCHAR(50) NULL,
        [ApprovedAt] DATETIME2(7) NULL,
        [CreatedBy] VARCHAR(50) NULL,
        [CreatedAt] DATETIME2(7) DEFAULT (sysdatetime()) NOT NULL,
        [UpdatedBy] VARCHAR(50) NULL,
        [UpdatedAt] DATETIME2(7) NULL,
        [CancelledBy] VARCHAR(50) NULL,
        [CancelledAt] DATETIME2(7) NULL,
        CONSTRAINT [PK_Attendance_Leave] PRIMARY KEY CLUSTERED ([LeaveId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_AttendanceLeave_EmployeeDates' AND object_id = OBJECT_ID('dbo.[Attendance_Leave]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_AttendanceLeave_EmployeeDates] ON dbo.[Attendance_Leave] ([EmployeeCode], [StartDate], [EndDate], [ApprovalStatus]);
END
GO

-- ============================================================================
-- Table 14: dbo.[Attendance_Permission]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Attendance_Permission]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Attendance_Permission] (
        [PermissionId] BIGINT IDENTITY(1,1) NOT NULL,
        [EmployeeCode] VARCHAR(50) NOT NULL,
        [AttendanceDate] DATE NOT NULL,
        [PermissionMinutes] INT NOT NULL,
        [PermissionType] VARCHAR(30) NULL,
        [PermissionStartTime] TIME(7) NULL,
        [PermissionEndTime] TIME(7) NULL,
        [Reason] NVARCHAR(500) NULL,
        [ApprovalStatus] VARCHAR(20) DEFAULT ('PENDING') NOT NULL,
        [ApprovedBy] VARCHAR(50) NULL,
        [ApprovedAt] DATETIME2(7) NULL,
        [CreatedBy] VARCHAR(50) NULL,
        [CreatedAt] DATETIME2(7) DEFAULT (sysdatetime()) NOT NULL,
        [UpdatedBy] VARCHAR(50) NULL,
        [UpdatedAt] DATETIME2(7) NULL,
        [CancelledBy] VARCHAR(50) NULL,
        [CancelledAt] DATETIME2(7) NULL,
        CONSTRAINT [PK_Attendance_Permission] PRIMARY KEY CLUSTERED ([PermissionId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_AttendancePermission_EmployeeDate' AND object_id = OBJECT_ID('dbo.[Attendance_Permission]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_AttendancePermission_EmployeeDate] ON dbo.[Attendance_Permission] ([EmployeeCode], [AttendanceDate], [ApprovalStatus]);
END
GO

-- ============================================================================
-- Table 15: dbo.[Attendance_Late_Fine]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Attendance_Late_Fine]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Attendance_Late_Fine] (
        [FineId] BIGINT IDENTITY(1,1) NOT NULL,
        [EmployeeCode] VARCHAR(50) NOT NULL,
        [AttendanceDate] DATE NOT NULL,
        [ActualCheckIn] DATETIME2(7) NULL,
        [ShiftStartTime] TIME(7) NULL,
        [AllowedUntil] TIME(7) NULL,
        [PermissionMinutesApplied] INT NULL,
        [LateMinutes] INT DEFAULT ((0)) NOT NULL,
        [FineAmount] DECIMAL(12,2) NULL,
        [CurrencyCode] CHAR(3) DEFAULT ('INR') NULL,
        [FineStatus] VARCHAR(20) DEFAULT ('PENDING') NOT NULL,
        [Reason] NVARCHAR(500) NULL,
        [EnteredBy] VARCHAR(50) NULL,
        [CreatedAt] DATETIME2(7) DEFAULT (sysdatetime()) NOT NULL,
        [UpdatedBy] VARCHAR(50) NULL,
        [UpdatedAt] DATETIME2(7) NULL,
        [ConfirmedBy] VARCHAR(50) NULL,
        [ConfirmedAt] DATETIME2(7) NULL,
        [WaivedBy] VARCHAR(50) NULL,
        [WaivedAt] DATETIME2(7) NULL,
        CONSTRAINT [PK_Attendance_Late_Fine] PRIMARY KEY CLUSTERED ([FineId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_AttendanceLateFine_DateStatus' AND object_id = OBJECT_ID('dbo.[Attendance_Late_Fine]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_AttendanceLateFine_DateStatus] ON dbo.[Attendance_Late_Fine] ([AttendanceDate], [FineStatus]);
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_AttendanceLateFine_EmployeeDate' AND object_id = OBJECT_ID('dbo.[Attendance_Late_Fine]'))
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX [UQ_AttendanceLateFine_EmployeeDate] ON dbo.[Attendance_Late_Fine] ([EmployeeCode], [AttendanceDate]);
END
GO

-- ============================================================================
-- Table 16: dbo.[Attendance_Holiday]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Attendance_Holiday]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Attendance_Holiday] (
        [HolidayId] INT IDENTITY(1,1) NOT NULL,
        [HolidayDate] DATE NOT NULL,
        [HolidayName] NVARCHAR(100) NOT NULL,
        [HolidayType] NVARCHAR(30) DEFAULT ('OFFICIAL') NULL,
        [Description] NVARCHAR(250) NULL,
        [Year] INT NOT NULL,
        [IsActive] BIT DEFAULT ((1)) NULL,
        [CreatedBy] NVARCHAR(50) DEFAULT ('HR Admin') NULL,
        [CreatedAt] DATETIME DEFAULT (getdate()) NULL,
        [UpdatedBy] NVARCHAR(50) NULL,
        [UpdatedAt] DATETIME DEFAULT (getdate()) NULL,
        CONSTRAINT [PK_Attendance_Holiday] PRIMARY KEY CLUSTERED ([HolidayId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Attendance_Holiday_Date' AND object_id = OBJECT_ID('dbo.[Attendance_Holiday]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_Attendance_Holiday_Date] ON dbo.[Attendance_Holiday] ([HolidayDate]);
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Attendance_Holiday_Year' AND object_id = OBJECT_ID('dbo.[Attendance_Holiday]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_Attendance_Holiday_Year] ON dbo.[Attendance_Holiday] ([Year], [IsActive]);
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_Attendance_Holiday_HolidayDate' AND object_id = OBJECT_ID('dbo.[Attendance_Holiday]'))
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX [UQ_Attendance_Holiday_HolidayDate] ON dbo.[Attendance_Holiday] ([HolidayDate]);
END
GO

-- ============================================================================
-- Table 17: dbo.[Acc_Quotation_Main]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Acc_Quotation_Main]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Acc_Quotation_Main] (
        [Ccode] NVARCHAR(150) NULL,
        [Lcode] NVARCHAR(150) NULL,
        [FinYearVal] NVARCHAR(150) NULL,
        [FinYearCode] NVARCHAR(150) NULL,
        [TransNo] NVARCHAR(150) NULL,
        [SuppCode] NVARCHAR(10) NULL,
        [TransDate] NVARCHAR(150) NULL,
        [CustomerName] NVARCHAR(MAX) NULL,
        [Remarks] NVARCHAR(MAX) NULL,
        [TotQty] DECIMAL(18,2) NULL,
        [TotItemAmt] DECIMAL(18,2) NULL,
        [TotCGSTAmt] DECIMAL(18,2) NULL,
        [TotSGSTAmt] DECIMAL(18,2) NULL,
        [TotIGSTAmt] DECIMAL(18,2) NULL,
        [TotLineAmt] DECIMAL(18,2) NULL,
        [RoundOffType] NVARCHAR(150) NULL,
        [RoundOffVal] DECIMAL(18,2) NULL,
        [NetAmount] DECIMAL(18,2) NULL,
        [UserName] NVARCHAR(150) NULL,
        [UserCode] NVARCHAR(150) NULL,
        [SysIp] NVARCHAR(150) NULL,
        [SysName] NVARCHAR(150) NULL,
        [CreateOn] NVARCHAR(150) NULL,
        [ApprovalStatus] NVARCHAR(150) NULL,
        [ApprovedBy] NVARCHAR(150) NULL,
        [ApprovedOn] NVARCHAR(150) NULL,
        [Status] NVARCHAR(150) NULL,
        [Product] VARCHAR(250) NULL,
        [purpose] VARCHAR(400) NULL,
        [terms_conditions] VARCHAR(500) NULL
    );
END
GO

-- ============================================================================
-- Table 18: dbo.[Acc_Quotation_Sub]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Acc_Quotation_Sub]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Acc_Quotation_Sub] (
        [Ccode] NVARCHAR(150) NULL,
        [Lcode] NVARCHAR(150) NULL,
        [FinYearCode] NVARCHAR(150) NULL,
        [FinYearVal] NVARCHAR(150) NULL,
        [TransNo] NVARCHAR(150) NULL,
        [TransDate] NVARCHAR(150) NULL,
        [ItemCode] NVARCHAR(150) NULL,
        [ProductType] NVARCHAR(500) NULL,
        [HSNCode] NVARCHAR(150) NULL,
        [Rate] DECIMAL(18,2) NULL,
        [Qty] DECIMAL(18,2) NULL,
        [ItemValue] DECIMAL(18,2) NULL,
        [GST] NVARCHAR(250) NULL,
        [CGST] DECIMAL(18,2) NULL,
        [SGST] DECIMAL(18,2) NULL,
        [IGST] DECIMAL(18,2) NULL,
        [NetAmount] DECIMAL(18,2) NULL,
        [Service] NVARCHAR(150) NULL,
        [Status] NVARCHAR(150) NULL,
        [UserName] NVARCHAR(150) NULL,
        [UserCode] NVARCHAR(150) NULL,
        [SysIP] NVARCHAR(150) NULL,
        [SysName] NVARCHAR(150) NULL,
        [CreateOn] NVARCHAR(150) NULL,
        [UOM] VARCHAR(150) NULL,
        [id] INT IDENTITY(1,1) NOT NULL,
        [order_id] VARCHAR(100) NULL,
        [Prod_highlight] VARCHAR(100) NULL
    );
END
GO

-- ============================================================================
-- Table 19: dbo.[Acc_Proforma_Inv_Main]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Acc_Proforma_Inv_Main]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Acc_Proforma_Inv_Main] (
        [Ccode] NVARCHAR(150) NULL,
        [Lcode] NVARCHAR(150) NULL,
        [FinYearVal] NVARCHAR(150) NULL,
        [FinYearCode] NVARCHAR(150) NULL,
        [TransNo] NVARCHAR(150) NULL,
        [TransDate] NVARCHAR(150) NULL,
        [QuotationNo] NVARCHAR(150) NULL,
        [QuotationDate] NVARCHAR(150) NULL,
        [CustomerCode] NVARCHAR(150) NULL,
        [CustomerName] NVARCHAR(MAX) NULL,
        [TotalQty] DECIMAL(18,0) NULL,
        [TotalItemAmount] DECIMAL(18,0) NULL,
        [TotalCGSTAmount] DECIMAL(18,0) NULL,
        [TotalSGSTAmount] DECIMAL(18,0) NULL,
        [TotalIGSTAmount] DECIMAL(18,0) NULL,
        [TotalAmount] DECIMAL(18,0) NULL,
        [Remarks] NVARCHAR(MAX) NULL,
        [RoundType] NVARCHAR(150) NULL,
        [RoundOff] DECIMAL(18,0) NULL,
        [NetAmount] DECIMAL(18,0) NULL,
        [UserName] NVARCHAR(150) NULL,
        [UserCode] NVARCHAR(150) NULL,
        [SysIp] NVARCHAR(150) NULL,
        [SysName] NVARCHAR(150) NULL,
        [CreateOn] NVARCHAR(150) NULL,
        [ApprovalStatus] NVARCHAR(150) NULL,
        [ApprovedBy] NVARCHAR(150) NULL,
        [ApprovedOn] NVARCHAR(150) NULL,
        [Status] NVARCHAR(150) NULL
    );
END
GO

-- ============================================================================
-- Table 20: dbo.[Acc_Proforma_Inv_Sub]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Acc_Proforma_Inv_Sub]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Acc_Proforma_Inv_Sub] (
        [Ccode] NVARCHAR(150) NULL,
        [Lcode] NVARCHAR(150) NULL,
        [FinYearCode] NVARCHAR(150) NULL,
        [FinYearVal] NVARCHAR(150) NULL,
        [TransNo] NVARCHAR(150) NULL,
        [TransDate] NVARCHAR(150) NULL,
        [QuotationNo] NVARCHAR(150) NULL,
        [QuotationDate] NVARCHAR(150) NULL,
        [CustomerCode] NVARCHAR(150) NULL,
        [CustomerName] NVARCHAR(MAX) NULL,
        [ItemCode] NVARCHAR(150) NULL,
        [ProductType] NVARCHAR(MAX) NULL,
        [HSNCode] NVARCHAR(150) NULL,
        [Qty] DECIMAL(18,2) NULL,
        [Rate] DECIMAL(18,2) NULL,
        [ItemValue] DECIMAL(18,2) NULL,
        [GST] NVARCHAR(150) NULL,
        [CGST] DECIMAL(18,2) NULL,
        [SGST] DECIMAL(18,2) NULL,
        [IGST] DECIMAL(18,2) NULL,
        [NetAmount] DECIMAL(18,2) NULL,
        [Service] NVARCHAR(150) NULL,
        [Status] NVARCHAR(150) NULL,
        [UserName] NVARCHAR(150) NULL,
        [UserCode] NVARCHAR(150) NULL,
        [SysIp] NVARCHAR(150) NULL,
        [SysName] NVARCHAR(150) NULL,
        [CreateOn] NVARCHAR(150) NULL,
        [id] INT IDENTITY(1,1) NOT NULL
    );
END
GO

-- ============================================================================
-- Table 21: dbo.[Acc_Sales_Inv_Main]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Acc_Sales_Inv_Main]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Acc_Sales_Inv_Main] (
        [Ccode] NVARCHAR(150) NULL,
        [Lcode] NVARCHAR(150) NULL,
        [FinYearCode] NVARCHAR(150) NULL,
        [FinYearVal] NCHAR(10) NULL,
        [TransNo] NVARCHAR(150) NULL,
        [TransDate] NVARCHAR(150) NULL,
        [InvoiceNo] NVARCHAR(150) NULL,
        [InvoiceDate] NVARCHAR(150) NULL,
        [CustomerName] NVARCHAR(150) NULL,
        [CustomerCode] NVARCHAR(150) NULL,
        [GST] NVARCHAR(150) NULL,
        [TotalQty] DECIMAL(18,0) NULL,
        [TotalItemAmount] DECIMAL(18,0) NULL,
        [TotalCGSTAmount] DECIMAL(18,0) NULL,
        [TotalSGSTAmount] DECIMAL(18,0) NULL,
        [TotalIGSTAmount] DECIMAL(18,0) NULL,
        [TotalAmount] DECIMAL(18,0) NULL,
        [RoundType] DECIMAL(18,0) NULL,
        [RoundOff] DECIMAL(18,0) NULL,
        [NetAmount] DECIMAL(18,0) NULL,
        [UserName] NVARCHAR(150) NULL,
        [UserCode] NVARCHAR(150) NULL,
        [SysIp] NVARCHAR(150) NULL,
        [SysName] NVARCHAR(150) NULL,
        [CreateOn] NVARCHAR(150) NULL,
        [Approval_Status] NVARCHAR(150) NULL,
        [ApprovedBy] NVARCHAR(150) NULL,
        [ApprovedOn] NVARCHAR(150) NULL,
        [Remarks] NVARCHAR(150) DEFAULT ('No Remarks') NULL,
        [Status] NVARCHAR(150) NULL,
        [GRN] NVARCHAR(150) NULL
    );
END
GO

-- ============================================================================
-- Table 22: dbo.[Acc_Sales_Inv_Sub]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Acc_Sales_Inv_Sub]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Acc_Sales_Inv_Sub] (
        [Ccode] NVARCHAR(150) NULL,
        [Lcode] NVARCHAR(150) NULL,
        [FinYearCode] NVARCHAR(150) NULL,
        [FinYearVal] NVARCHAR(150) NULL,
        [TransNo] NVARCHAR(150) NULL,
        [TransDate] NVARCHAR(150) NULL,
        [InvoiceNo] NVARCHAR(150) NULL,
        [InvoiceDate] NVARCHAR(150) NULL,
        [CustomerName] NVARCHAR(MAX) NULL,
        [CustomerCode] NVARCHAR(150) NULL,
        [ItemCode] NVARCHAR(150) NULL,
        [ProductType] NVARCHAR(MAX) NULL,
        [HSNCode] NVARCHAR(150) NULL,
        [Qty] DECIMAL(18,2) NULL,
        [Rate] DECIMAL(18,2) NULL,
        [ItemValue] DECIMAL(18,2) NULL,
        [SerialNo] NVARCHAR(150) NULL,
        [GST] NVARCHAR(150) NOT NULL,
        [CGST] DECIMAL(18,2) NULL,
        [SGST] DECIMAL(18,2) NULL,
        [IGST] DECIMAL(18,2) NULL,
        [NetAmount] DECIMAL(18,2) NULL,
        [Status] NVARCHAR(150) NULL,
        [UserName] NVARCHAR(150) NULL,
        [Usercode] NVARCHAR(150) NULL,
        [SysName] NVARCHAR(150) NULL,
        [SysIp] NVARCHAR(150) NULL,
        [CreateOn] NVARCHAR(150) NULL
    );
END
GO

-- ============================================================================
-- Table 23: dbo.[Acc_Trans_All]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Acc_Trans_All]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Acc_Trans_All] (
        [CCode] NVARCHAR(50) NULL,
        [LCode] NVARCHAR(50) NULL,
        [FinYearCode] NVARCHAR(50) NULL,
        [FinYearVal] NVARCHAR(50) NULL,
        [TransNo] NVARCHAR(50) NULL,
        [TransDate] NVARCHAR(50) NULL,
        [LeaderCode] NVARCHAR(MAX) NULL,
        [LedgerName] NVARCHAR(MAX) NULL,
        [AccHeadCode] NVARCHAR(50) NULL,
        [AccHeadName] NVARCHAR(MAX) NULL,
        [TransType] NVARCHAR(100) NULL,
        [CreditAmount] DECIMAL(18,2) NULL,
        [DebitAmount] DECIMAL(18,2) NULL,
        [Status] NVARCHAR(50) NULL,
        [UserId] NVARCHAR(50) NULL,
        [UserName] NVARCHAR(50) NULL,
        [CreatedBy] NVARCHAR(50) NULL,
        [RefNo] NVARCHAR(150) NULL,
        [RefDate] NVARCHAR(150) NULL,
        [Narration] NVARCHAR(MAX) NULL
    );
END
GO

-- ============================================================================
-- Table 24: dbo.[Acc_GRN_Stock]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Acc_GRN_Stock]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Acc_GRN_Stock] (
        [Ccode] NVARCHAR(150) NULL,
        [Lcode] NVARCHAR(150) NULL,
        [FinYearCode] NVARCHAR(150) NULL,
        [FinYearVal] NVARCHAR(150) NULL,
        [TransNo] NVARCHAR(150) NULL,
        [TransDate] NVARCHAR(150) NULL,
        [GRN] NVARCHAR(150) NULL,
        [ProductType] NVARCHAR(150) NULL,
        [HSNCode] NVARCHAR(150) NULL,
        [MaterialInventory] NUMERIC(18,2) NULL,
        [SerialNo] NVARCHAR(150) NULL,
        [MinusQty] NUMERIC(18,2) NULL,
        [Stock] NVARCHAR(150) NULL,
        [Status] NVARCHAR(150) NULL,
        [CreateOn] NVARCHAR(150) NULL,
        [UserName] NVARCHAR(150) NULL,
        [UserCode] NVARCHAR(150) NULL,
        [SysIp] NVARCHAR(150) NULL,
        [SysName] NVARCHAR(150) NULL,
        [IsSold] BIT DEFAULT ((0)) NULL
    );
END
GO

-- ============================================================================
-- Table 25: dbo.[Delivery_main]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Delivery_main]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Delivery_main] (
        [Deliveryno] VARCHAR(100) NULL,
        [Deliverydate] VARCHAR(100) NULL,
        [Returntype] VARCHAR(100) NULL,
        [Suppliername] VARCHAR(100) NULL,
        [SupplierInvoice] VARCHAR(100) NULL,
        [Deliverymode] VARCHAR(100) NULL,
        [TotalAmt] VARCHAR(100) NULL,
        [GSTName] VARCHAR(100) NULL,
        [SGST_Per] VARCHAR(100) NULL,
        [SGSTAmt] VARCHAR(100) NULL,
        [CGST_Per] VARCHAR(100) NULL,
        [CGSTAmt] VARCHAR(100) NULL,
        [IGST_Per] VARCHAR(100) NULL,
        [IGSTAmt] VARCHAR(100) NULL,
        [FinalInvoice] VARCHAR(100) NULL,
        [Ccode] VARCHAR(100) NULL,
        [Lcode] VARCHAR(100) NULL,
        [TransType] VARCHAR(100) NULL,
        [Supplier_ref_no] VARCHAR(200) NULL,
        [Supplier_ref_date] VARCHAR(200) NULL,
        [purpose] VARCHAR(200) NULL
    );
END
GO

-- ============================================================================
-- Table 26: dbo.[Delivery_sub]
-- ============================================================================
IF OBJECT_ID(N'dbo.[Delivery_sub]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[Delivery_sub] (
        [Ccode] VARCHAR(100) NULL,
        [Lcode] VARCHAR(100) NULL,
        [Item] VARCHAR(100) NULL,
        [Qty] VARCHAR(100) NULL,
        [Rate] VARCHAR(100) NULL,
        [InvoiceTotal] VARCHAR(100) NULL,
        [Deliveryno] VARCHAR(100) NULL,
        [HSN] VARCHAR(100) NULL,
        [UOM] VARCHAR(20) NULL
    );
END
GO

-- ============================================================================
-- Table 27: dbo.[OfficeExpense_Fund]
-- ============================================================================
IF OBJECT_ID(N'dbo.[OfficeExpense_Fund]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[OfficeExpense_Fund] (
        [FundId] INT IDENTITY(1,1) NOT NULL,
        [FundName] NVARCHAR(100) NOT NULL,
        [OpeningBalance] DECIMAL(18,2) DEFAULT ((0)) NOT NULL,
        [CurrencyCode] CHAR(3) DEFAULT ('INR') NOT NULL,
        [IsActive] BIT DEFAULT ((1)) NOT NULL,
        [CreatedBy] VARCHAR(50) NULL,
        [CreatedAt] DATETIME2(7) DEFAULT (sysdatetime()) NOT NULL,
        CONSTRAINT [PK_OfficeExpense_Fund] PRIMARY KEY CLUSTERED ([FundId])
    );
END
GO

-- ============================================================================
-- Table 28: dbo.[OfficeExpense_Transaction]
-- ============================================================================
IF OBJECT_ID(N'dbo.[OfficeExpense_Transaction]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[OfficeExpense_Transaction] (
        [ExpenseId] BIGINT IDENTITY(1,1) NOT NULL,
        [FundId] INT NULL,
        [SerialNo] INT NULL,
        [ExpenseDate] DATE NOT NULL,
        [ReceiverName] NVARCHAR(150) NULL,
        [ProductName] NVARCHAR(200) NOT NULL,
        [Amount] DECIMAL(18,2) NOT NULL,
        [Remarks] NVARCHAR(500) NULL,
        [ImportBatchId] UNIQUEIDENTIFIER NULL,
        [SourceRowNo] INT NULL,
        [CreatedBy] VARCHAR(50) NULL,
        [CreatedAt] DATETIME2(7) DEFAULT (sysdatetime()) NOT NULL,
        [UpdatedBy] VARCHAR(50) NULL,
        [UpdatedAt] DATETIME2(7) NULL,
        [TransactionType] VARCHAR(10) NULL,
        [Category] VARCHAR(100) NULL,
        [Description] VARCHAR(500) NULL,
        [ReceivedFrom] VARCHAR(150) NULL,
        [Quantity] DECIMAL(10,2) NULL,
        CONSTRAINT [PK_OfficeExpense_Transaction] PRIMARY KEY CLUSTERED ([ExpenseId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_OfficeExpense_Transaction_FundDate' AND object_id = OBJECT_ID('dbo.[OfficeExpense_Transaction]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_OfficeExpense_Transaction_FundDate] ON dbo.[OfficeExpense_Transaction] ([FundId], [ExpenseDate]);
END
GO

-- ============================================================================
-- Table 29: dbo.[OfficeDaily_Item]
-- ============================================================================
IF OBJECT_ID(N'dbo.[OfficeDaily_Item]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[OfficeDaily_Item] (
        [ItemId] BIGINT IDENTITY(1,1) NOT NULL,
        [ItemName] NVARCHAR(150) NOT NULL,
        [UnitRate] DECIMAL(18,2) NOT NULL,
        [UnitName] NVARCHAR(30) NOT NULL,
        [VendorName] NVARCHAR(150) NOT NULL,
        [Category] NVARCHAR(80) DEFAULT ('Other') NOT NULL,
        [IconType] NVARCHAR(30) DEFAULT ('other') NOT NULL,
        [IsActive] BIT DEFAULT ((1)) NOT NULL,
        [CreatedBy] NVARCHAR(100) NULL,
        [CreatedAt] DATETIME2(7) DEFAULT (sysdatetime()) NOT NULL,
        [UpdatedAt] DATETIME2(7) NULL,
        CONSTRAINT [PK_OfficeDaily_Item] PRIMARY KEY CLUSTERED ([ItemId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_OfficeDaily_Item_Active' AND object_id = OBJECT_ID('dbo.[OfficeDaily_Item]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_OfficeDaily_Item_Active] ON dbo.[OfficeDaily_Item] ([IsActive], [ItemName]);
END
GO

-- ============================================================================
-- Table 30: dbo.[OfficeDaily_Entry]
-- ============================================================================
IF OBJECT_ID(N'dbo.[OfficeDaily_Entry]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[OfficeDaily_Entry] (
        [EntryId] BIGINT IDENTITY(1,1) NOT NULL,
        [ExpenseDate] DATE NOT NULL,
        [ItemId] BIGINT NOT NULL,
        [ItemName] NVARCHAR(150) NOT NULL,
        [Quantity] DECIMAL(18,3) NOT NULL,
        [UnitRate] DECIMAL(18,2) NOT NULL,
        [Amount] DECIMAL(18,2) NOT NULL,
        [VendorName] NVARCHAR(150) NOT NULL,
        [Category] NVARCHAR(80) DEFAULT ('Other') NOT NULL,
        [Status] VARCHAR(20) DEFAULT ('UNSETTLED') NOT NULL,
        [SettlementId] BIGINT NULL,
        [Remarks] NVARCHAR(500) NULL,
        [CreatedBy] NVARCHAR(100) NULL,
        [CreatedAt] DATETIME2(7) DEFAULT (sysdatetime()) NOT NULL,
        [UpdatedAt] DATETIME2(7) NULL,
        CONSTRAINT [PK_OfficeDaily_Entry] PRIMARY KEY CLUSTERED ([EntryId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_OfficeDaily_Entry_Date_Status' AND object_id = OBJECT_ID('dbo.[OfficeDaily_Entry]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_OfficeDaily_Entry_Date_Status] ON dbo.[OfficeDaily_Entry] ([ExpenseDate], [Status]);
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_OfficeDaily_Entry_Vendor_Date' AND object_id = OBJECT_ID('dbo.[OfficeDaily_Entry]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_OfficeDaily_Entry_Vendor_Date] ON dbo.[OfficeDaily_Entry] ([VendorName], [ExpenseDate], [Status]);
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_OfficeDaily_Entry_Date_Item' AND object_id = OBJECT_ID('dbo.[OfficeDaily_Entry]'))
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX [UX_OfficeDaily_Entry_Date_Item] ON dbo.[OfficeDaily_Entry] ([ExpenseDate], [ItemId]);
END
GO

-- ============================================================================
-- Table 31: dbo.[OfficeDaily_Settlement]
-- ============================================================================
IF OBJECT_ID(N'dbo.[OfficeDaily_Settlement]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[OfficeDaily_Settlement] (
        [SettlementId] BIGINT IDENTITY(1,1) NOT NULL,
        [VendorName] NVARCHAR(150) NOT NULL,
        [PeriodMonth] CHAR(7) NOT NULL,
        [Amount] DECIMAL(18,2) NOT NULL,
        [PaymentDate] DATE NOT NULL,
        [PaymentMethod] NVARCHAR(30) NOT NULL,
        [Category] NVARCHAR(80) DEFAULT ('Other') NOT NULL,
        [FundId] INT NULL,
        [LedgerTransactionId] BIGINT NULL,
        [Reference] NVARCHAR(150) NULL,
        [Remarks] NVARCHAR(500) NULL,
        [CreatedBy] NVARCHAR(100) NULL,
        [CreatedAt] DATETIME2(7) DEFAULT (sysdatetime()) NOT NULL,
        CONSTRAINT [PK_OfficeDaily_Settlement] PRIMARY KEY CLUSTERED ([SettlementId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_OfficeDaily_Settlement_Month_Vendor' AND object_id = OBJECT_ID('dbo.[OfficeDaily_Settlement]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_OfficeDaily_Settlement_Month_Vendor] ON dbo.[OfficeDaily_Settlement] ([PeriodMonth], [VendorName]);
END
GO

-- ============================================================================
-- Table 32: dbo.[TravelExpense_Claim]
-- ============================================================================
IF OBJECT_ID(N'dbo.[TravelExpense_Claim]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[TravelExpense_Claim] (
        [ClaimId] INT IDENTITY(1,1) NOT NULL,
        [EmployeeCode] VARCHAR(50) NOT NULL,
        [TravelStartDate] DATE NOT NULL,
        [TravelEndDate] DATE NOT NULL,
        [ClientName] NVARCHAR(200) NULL,
        [Destination] NVARCHAR(200) NOT NULL,
        [Purpose] NVARCHAR(500) NOT NULL,
        [TotalAmount] DECIMAL(12,2) DEFAULT ((0)) NOT NULL,
        [Status] VARCHAR(20) DEFAULT ('PENDING') NOT NULL,
        [FundId] INT NULL,
        [CreatedDate] DATETIME2(0) DEFAULT (sysdatetime()) NOT NULL,
        [CreatedBy] VARCHAR(50) NULL,
        [ExpenseId] BIGINT NULL,
        [PaidDate] DATE NULL,
        CONSTRAINT [PK_TravelExpense_Claim] PRIMARY KEY CLUSTERED ([ClaimId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_TravelExpense_Claim_EmployeeCode' AND object_id = OBJECT_ID('dbo.[TravelExpense_Claim]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_TravelExpense_Claim_EmployeeCode] ON dbo.[TravelExpense_Claim] ([EmployeeCode]);
END
GO

-- ============================================================================
-- Table 33: dbo.[TravelExpense_Item]
-- ============================================================================
IF OBJECT_ID(N'dbo.[TravelExpense_Item]', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[TravelExpense_Item] (
        [ItemId] INT IDENTITY(1,1) NOT NULL,
        [ClaimId] INT NOT NULL,
        [ExpenseCategory] VARCHAR(30) NOT NULL,
        [Amount] DECIMAL(12,2) NOT NULL,
        [Description] NVARCHAR(500) NULL,
        [Remarks] NVARCHAR(500) NULL,
        [BillReceiptNumber] NVARCHAR(100) NULL,
        [AttachmentPath] NVARCHAR(500) NULL,
        CONSTRAINT [PK_TravelExpense_Item] PRIMARY KEY CLUSTERED ([ItemId])
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_TravelExpense_Item_ClaimId' AND object_id = OBJECT_ID('dbo.[TravelExpense_Item]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_TravelExpense_Item_ClaimId] ON dbo.[TravelExpense_Item] ([ClaimId]);
END
GO
