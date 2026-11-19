/*
===============================================================================
Migration 07: Add Customer Receipts and Master Tables to Scoto_Admin_ERP
Extracted directly from SCOTO_ACC_ERP reference database.
Creates all necessary receipt headers, line items, ledger breakdowns, and master formats.
===============================================================================
*/

-- =============================================================
-- Table: dbo.Acc_Receipts_Main
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Receipts_Main]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Receipts_Main] (
        [CCode] [nvarchar](150) NULL,
        [LCode] [nvarchar](150) NULL,
        [FinYearCode] [nvarchar](150) NULL,
        [FinYearVal] [nvarchar](150) NULL,
        [TransNo] [nvarchar](150) NULL,
        [Disp_TransNo] [nvarchar](150) NULL,
        [TransVal] [nvarchar](150) NULL,
        [TransDate] [nvarchar](150) NULL,
        [ReceiptType] [nvarchar](150) NULL,
        [TransType] [nvarchar](150) NULL,
        [BankCode] [nvarchar](150) NULL,
        [BankName] [nvarchar](500) NULL,
        [BankShortName] [nvarchar](500) NULL,
        [AccountsNo] [nvarchar](150) NULL,
        [BankGLCode] [nvarchar](150) NULL,
        [BankGLName] [nvarchar](MAX) NULL,
        [BankLdgHeadCode] [nvarchar](150) NULL,
        [BankLdgHeadName] [nvarchar](MAX) NULL,
        [RefNo] [nvarchar](150) NULL,
        [RefDate] [nvarchar](150) NULL,
        [PayMode] [nvarchar](150) NULL,
        [Remarks] [nvarchar](MAX) NULL,
        [BRSDate] [nvarchar](150) NULL,
        [MemberType] [nvarchar](500) NULL,
        [MemberName] [nvarchar](500) NULL,
        [TotInvAmt] [decimal](18,2) NULL,
        [TotReceivedAmt] [decimal](18,2) NULL,
        [TotBalanceAmt] [decimal](18,2) NULL,
        [TotGSTAmt] [decimal](18,2) NULL,
        [TotTDSAmt] [decimal](18,2) NULL,
        [TotTCSAmt] [decimal](18,2) NULL,
        [NetAmount] [decimal](18,2) NULL,
        [RoundOffType] [nvarchar](150) NULL,
        [RoundOff] [decimal](18,2) NULL,
        [InvoiceAmount] [decimal](18,2) NULL,
        [Status] [nvarchar](150) NULL,
        [ApprovalRemarks] [nvarchar](MAX) NULL,
        [ApprovalStatus] [nvarchar](150) NULL,
        [ApprovedBy] [nvarchar](150) NULL,
        [ApprovedOn] [nvarchar](150) NULL,
        [SysName] [nvarchar](150) NULL,
        [SysIp] [nvarchar](150) NULL,
        [UserId] [nvarchar](150) NULL,
        [UserName] [nvarchar](150) NULL,
        [CreateOn] [nvarchar](150) NULL
    );
    PRINT 'Created table [dbo].[Acc_Receipts_Main] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Receipts_Sub
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Receipts_Sub]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Receipts_Sub] (
        [CCode] [nvarchar](150) NULL,
        [LCode] [nvarchar](150) NULL,
        [FinYearCode] [nvarchar](150) NULL,
        [FinYearVal] [nvarchar](150) NULL,
        [TransNo] [nvarchar](150) NULL,
        [TransDate] [nvarchar](150) NULL,
        [LedgerCode] [nvarchar](150) NULL,
        [LedgerName] [nvarchar](MAX) NULL,
        [LedgerHeadCode] [nvarchar](150) NULL,
        [LedgerHeadName] [nvarchar](MAX) NULL,
        [PartyName] [nvarchar](MAX) NULL,
        [InvNo] [nvarchar](150) NULL,
        [InvDate] [nvarchar](150) NULL,
        [InvoiceAmt] [decimal](18,2) NULL,
        [GSTName] [nvarchar](150) NULL,
        [CGSTPer] [decimal](18,2) NULL,
        [CGSTAmt] [decimal](18,2) NULL,
        [SGSTPer] [decimal](18,2) NULL,
        [SGSTAmt] [decimal](18,2) NULL,
        [IGSTPer] [decimal](18,2) NULL,
        [IGSTAmt] [decimal](18,2) NULL,
        [GSTAmt] [decimal](18,2) NULL,
        [TDSName] [nvarchar](250) NULL,
        [TDSPer] [decimal](18,2) NULL,
        [TDSAmt] [decimal](18,2) NULL,
        [TCSName] [nvarchar](250) NULL,
        [TCSPer] [decimal](18,2) NULL,
        [TCSAmt] [decimal](18,2) NULL,
        [SubTotal] [decimal](18,2) NULL,
        [RoundOffType] [nvarchar](250) NULL,
        [RoundOff] [decimal](18,2) NULL,
        [LineTotal] [decimal](18,2) NULL,
        [Status] [nvarchar](150) NULL,
        [SysName] [nvarchar](150) NULL,
        [SysIp] [nvarchar](150) NULL,
        [UserId] [nvarchar](150) NULL,
        [UserName] [nvarchar](150) NULL
    );
    PRINT 'Created table [dbo].[Acc_Receipts_Sub] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Receipts_Ledger
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Receipts_Ledger]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Receipts_Ledger] (
        [Ccode] [nvarchar](100) NULL,
        [LCode] [nvarchar](100) NULL,
        [FinYearCode] [nvarchar](100) NULL,
        [FinYearVal] [nvarchar](100) NULL,
        [TransNo] [nvarchar](100) NULL,
        [TransDate] [nvarchar](100) NULL,
        [GenLdgCode] [nvarchar](100) NULL,
        [GenLdgName] [nvarchar](100) NULL,
        [ACCateCode] [nvarchar](100) NULL,
        [ACCateName] [nvarchar](100) NULL,
        [CrAmt] [decimal](18,2) NULL,
        [DrAmt] [decimal](18,2) NULL,
        [Status] [nvarchar](100) NULL,
        [UserCode] [nvarchar](100) NULL,
        [UserName] [nvarchar](100) NULL
    );
    PRINT 'Created table [dbo].[Acc_Receipts_Ledger] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Cash_Receipts_Main
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Cash_Receipts_Main]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Cash_Receipts_Main] (
        [Ccode] [nvarchar](100) NULL,
        [Lcode] [nvarchar](100) NULL,
        [FinYearCode] [nvarchar](100) NULL,
        [FinYearVal] [nvarchar](100) NULL,
        [TransNo] [nvarchar](100) NULL,
        [TransDate] [nvarchar](100) NULL,
        [AccType] [nvarchar](100) NULL,
        [RefNo] [nvarchar](100) NULL,
        [RefDate] [nvarchar](100) NULL,
        [TotCreditAmt] [decimal](18,2) NULL,
        [TotDebitAmt] [decimal](18,2) NULL,
        [Narration] [nvarchar](MAX) NULL,
        [Status] [nvarchar](100) NULL,
        [SysIp] [nvarchar](100) NULL,
        [SysName] [nvarchar](100) NULL,
        [UserId] [nvarchar](100) NULL,
        [UserName] [nvarchar](100) NULL,
        [CreateOn] [nvarchar](100) NULL,
        [ApprovedRemarks] [nvarchar](MAX) NULL,
        [ApprovedStatus] [nvarchar](100) NULL,
        [ApprovedBy] [nvarchar](100) NULL,
        [ApprovedOn] [nvarchar](100) NULL
    );
    PRINT 'Created table [dbo].[Acc_Cash_Receipts_Main] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Cash_Receipts_Sub
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Cash_Receipts_Sub]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Cash_Receipts_Sub] (
        [Ccode] [nvarchar](100) NULL,
        [Lcode] [nvarchar](100) NULL,
        [FinYearCode] [nvarchar](100) NULL,
        [FinYearVal] [nvarchar](100) NULL,
        [TransNo] [nvarchar](100) NULL,
        [TransDate] [nvarchar](100) NULL,
        [AccType] [nvarchar](100) NULL,
        [RefNo] [nvarchar](100) NULL,
        [RefDate] [nvarchar](100) NULL,
        [TransType] [nvarchar](100) NULL,
        [VoucherType] [nvarchar](100) NULL,
        [LedgerCode] [nvarchar](100) NULL,
        [LedgerName] [nvarchar](MAX) NULL,
        [LedgerHeaderCode] [nvarchar](100) NULL,
        [LedgerHeaderName] [nvarchar](MAX) NULL,
        [CreditAmt] [decimal](18,2) NULL,
        [DebitAmt] [decimal](18,2) NULL,
        [Status] [nvarchar](100) NULL,
        [SysIp] [nvarchar](100) NULL,
        [SysName] [nvarchar](100) NULL,
        [UserId] [nvarchar](100) NULL,
        [UserName] [nvarchar](100) NULL,
        [CreateOn] [nvarchar](100) NULL
    );
    PRINT 'Created table [dbo].[Acc_Cash_Receipts_Sub] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Cash_Receipts_Ledger
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Cash_Receipts_Ledger]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Cash_Receipts_Ledger] (
        [Ccode] [nvarchar](100) NULL,
        [LCode] [nvarchar](100) NULL,
        [FinYearCode] [nvarchar](100) NULL,
        [FinYearVal] [nvarchar](100) NULL,
        [TransNo] [nvarchar](100) NULL,
        [TransDate] [nvarchar](100) NULL,
        [GenLdgCode] [nvarchar](100) NULL,
        [GenLdgName] [nvarchar](100) NULL,
        [ACCateCode] [nvarchar](100) NULL,
        [ACCateName] [nvarchar](100) NULL,
        [CrAmt] [decimal](18,2) NULL,
        [DrAmt] [decimal](18,2) NULL,
        [Status] [nvarchar](100) NULL,
        [UserCode] [nvarchar](100) NULL,
        [UserName] [nvarchar](100) NULL
    );
    PRINT 'Created table [dbo].[Acc_Cash_Receipts_Ledger] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Coral_Receipts_Main
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Coral_Receipts_Main]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Coral_Receipts_Main] (
        [CCode] [nvarchar](150) NULL,
        [LCode] [nvarchar](150) NULL,
        [FinYearCode] [nvarchar](150) NULL,
        [FinYearVal] [nvarchar](150) NULL,
        [TransNo] [nvarchar](150) NULL,
        [TransDate] [nvarchar](150) NULL,
        [TransType] [nvarchar](150) NULL,
        [CustCode] [nvarchar](150) NULL,
        [CustName] [nvarchar](500) NULL,
        [BankCode] [nvarchar](150) NULL,
        [BankName] [nvarchar](500) NULL,
        [AccountsNo] [nvarchar](150) NULL,
        [GenLdgerName] [nvarchar](MAX) NULL,
        [RefNo] [nvarchar](150) NULL,
        [Remarks] [nvarchar](MAX) NULL,
        [TotInvAmt] [decimal](18,2) NULL,
        [TotReceivedAmt] [decimal](18,2) NULL,
        [TotBalanceAmt] [decimal](18,2) NULL,
        [TotTDSAmt] [decimal](18,2) NULL,
        [TotTCSAmt] [decimal](18,2) NULL,
        [NetAmount] [decimal](18,2) NULL,
        [RoundOffType] [nvarchar](150) NULL,
        [RoundOff] [decimal](18,2) NULL,
        [InvoiceAmount] [decimal](18,2) NULL,
        [Status] [nvarchar](150) NULL,
        [ApprovalRemarks] [nvarchar](MAX) NULL,
        [ApprovalStatus] [nvarchar](150) NULL,
        [ApprovedBy] [nvarchar](150) NULL,
        [ApprovedOn] [nvarchar](150) NULL,
        [SysName] [nvarchar](150) NULL,
        [SysIp] [nvarchar](150) NULL,
        [UserId] [nvarchar](150) NULL,
        [UserName] [nvarchar](150) NULL,
        [CreateOn] [nvarchar](150) NULL,
        [SuppType] [nvarchar](150) NULL
    );
    PRINT 'Created table [dbo].[Acc_Coral_Receipts_Main] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Coral_Receipts_Sub
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Coral_Receipts_Sub]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Coral_Receipts_Sub] (
        [CCode] [nvarchar](150) NULL,
        [LCode] [nvarchar](150) NULL,
        [FinYearCode] [nvarchar](150) NULL,
        [FinYearVal] [nvarchar](150) NULL,
        [TransNo] [nvarchar](150) NULL,
        [TransDate] [nvarchar](150) NULL,
        [InvNo] [nvarchar](150) NULL,
        [InvDate] [nvarchar](150) NULL,
        [InvoiceAmt] [decimal](18,2) NULL,
        [ReceivedAmt] [decimal](18,2) NULL,
        [BalanceAmt] [decimal](18,2) NULL,
        [TDSName] [nvarchar](250) NULL,
        [TDSPer] [decimal](18,2) NULL,
        [TDSAmt] [decimal](18,2) NULL,
        [TCSName] [nvarchar](250) NULL,
        [TCSPer] [decimal](18,2) NULL,
        [TCSAmt] [decimal](18,2) NULL,
        [LineAmount] [decimal](18,2) NULL,
        [Status] [nvarchar](150) NULL,
        [SysName] [nvarchar](150) NULL,
        [SysIp] [nvarchar](150) NULL,
        [UserId] [nvarchar](150) NULL,
        [UserName] [nvarchar](150) NULL,
        [TDSCalc] [nvarchar](150) NULL,
        [TDSAmtAdj] [nvarchar](150) NULL,
        [TCSAmtAdj] [nvarchar](150) NULL,
        [InvCurType] [nvarchar](150) NULL,
        [InvExcRate] [decimal](18,4) NULL,
        [InvAmt_INR] [decimal](18,2) NULL,
        [CurType] [nvarchar](150) NULL,
        [ExcRate] [decimal](18,4) NULL,
        [ReceivedAmt_INR] [decimal](18,2) NULL,
        [ForexType] [nvarchar](150) NULL,
        [ForexAmt] [decimal](18,2) NULL,
        [BankChagres] [decimal](18,2) NULL,
        [TotReceiptAmt] [decimal](18,2) NULL,
        [BankCharesAmt_INR] [decimal](18,2) NULL,
        [TotReceiptsAmt_INR] [decimal](18,2) NULL
    );
    PRINT 'Created table [dbo].[Acc_Coral_Receipts_Sub] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Coral_Receipts_Ledger
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Coral_Receipts_Ledger]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Coral_Receipts_Ledger] (
        [Ccode] [nvarchar](100) NULL,
        [LCode] [nvarchar](100) NULL,
        [FinYearCode] [nvarchar](100) NULL,
        [FinYearVal] [nvarchar](100) NULL,
        [TransNo] [nvarchar](100) NULL,
        [TransDate] [nvarchar](100) NULL,
        [GenLdgCode] [nvarchar](100) NULL,
        [GenLdgName] [nvarchar](100) NULL,
        [ACCateCode] [nvarchar](100) NULL,
        [ACCateName] [nvarchar](100) NULL,
        [CrAmt] [decimal](18,2) NULL,
        [DrAmt] [decimal](18,2) NULL,
        [Status] [nvarchar](100) NULL,
        [UserCode] [nvarchar](100) NULL,
        [UserName] [nvarchar](100) NULL
    );
    PRINT 'Created table [dbo].[Acc_Coral_Receipts_Ledger] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Escrow_Receipts_Main
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Escrow_Receipts_Main]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Escrow_Receipts_Main] (
        [CCode] [nvarchar](150) NULL,
        [LCode] [nvarchar](150) NULL,
        [FinYearCode] [nvarchar](150) NULL,
        [FinYearVal] [nvarchar](150) NULL,
        [TransNo] [nvarchar](150) NULL,
        [TransDate] [nvarchar](150) NULL,
        [BankCode] [nvarchar](150) NULL,
        [BankName] [nvarchar](500) NULL,
        [AccountsNo] [nvarchar](150) NULL,
        [GenLdgerName] [nvarchar](MAX) NULL,
        [RefNo] [nvarchar](150) NULL,
        [Remarks] [nvarchar](MAX) NULL,
        [TotInvAmt] [decimal](18,2) NULL,
        [TotReceivedAmt] [decimal](18,2) NULL,
        [BalanceAmt] [decimal](18,2) NULL,
        [TotTDSAmt] [decimal](18,2) NULL,
        [TotTCSAmt] [decimal](18,2) NULL,
        [NetAmount] [decimal](18,2) NULL,
        [RoundOffType] [nvarchar](150) NULL,
        [RoundOff] [decimal](18,2) NULL,
        [InvoiceAmount] [decimal](18,2) NULL,
        [Status] [nvarchar](150) NULL,
        [ApprovalRemarks] [nvarchar](MAX) NULL,
        [ApprovalStatus] [nvarchar](150) NULL,
        [ApprovedBy] [nvarchar](150) NULL,
        [ApprovedOn] [nvarchar](150) NULL,
        [SysName] [nvarchar](150) NULL,
        [SysIp] [nvarchar](150) NULL,
        [UserId] [nvarchar](150) NULL,
        [UserName] [nvarchar](150) NULL,
        [CreateOn] [nvarchar](150) NULL
    );
    PRINT 'Created table [dbo].[Acc_Escrow_Receipts_Main] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Escrow_Receipts_Sub
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Escrow_Receipts_Sub]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Escrow_Receipts_Sub] (
        [CCode] [nvarchar](150) NULL,
        [LCode] [nvarchar](150) NULL,
        [FinYearCode] [nvarchar](150) NULL,
        [FinYearVal] [nvarchar](150) NULL,
        [TransNo] [nvarchar](150) NULL,
        [TransDate] [nvarchar](150) NULL,
        [ProfromaInvNo] [nvarchar](150) NULL,
        [ProfromaInvDate] [nvarchar](150) NULL,
        [InvoiceAmt] [decimal](18,2) NULL,
        [ReceivedAmt] [decimal](18,2) NULL,
        [BalanceAmt] [decimal](18,2) NULL,
        [TDSName] [nvarchar](250) NULL,
        [TDSPer] [decimal](18,2) NULL,
        [TDSAmt] [decimal](18,2) NULL,
        [TCSName] [nvarchar](250) NULL,
        [TCSPer] [decimal](18,2) NULL,
        [TCSAmt] [decimal](18,2) NULL,
        [LineAmount] [decimal](18,2) NULL,
        [Status] [nvarchar](150) NULL,
        [SysName] [nvarchar](150) NULL,
        [SysIp] [nvarchar](150) NULL,
        [UserId] [nvarchar](150) NULL,
        [UserName] [nvarchar](150) NULL,
        [TDSAmtAdj] [decimal](18,2) NULL,
        [TCSAmtAdj] [decimal](18,2) NULL
    );
    PRINT 'Created table [dbo].[Acc_Escrow_Receipts_Sub] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Escrow_Receipts_Ledger
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Escrow_Receipts_Ledger]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Escrow_Receipts_Ledger] (
        [Ccode] [nvarchar](100) NULL,
        [LCode] [nvarchar](100) NULL,
        [FinYearCode] [nvarchar](100) NULL,
        [FinYearVal] [nvarchar](100) NULL,
        [TransNo] [nvarchar](100) NULL,
        [TransDate] [nvarchar](100) NULL,
        [GenLdgCode] [nvarchar](100) NULL,
        [GenLdgName] [nvarchar](100) NULL,
        [ACCateCode] [nvarchar](100) NULL,
        [ACCateName] [nvarchar](100) NULL,
        [CrAmt] [decimal](18,2) NULL,
        [DrAmt] [decimal](18,2) NULL,
        [Status] [nvarchar](100) NULL,
        [UserCode] [nvarchar](100) NULL,
        [UserName] [nvarchar](100) NULL
    );
    PRINT 'Created table [dbo].[Acc_Escrow_Receipts_Ledger] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Mst_ReceiptType
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Mst_ReceiptType]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Mst_ReceiptType] (
        [Ccode] [nvarchar](50) NULL,
        [Lcode] [nvarchar](50) NULL,
        [ReceiptTypeName] [nvarchar](MAX) NULL,
        [Status] [nvarchar](150) NULL,
        [SysIp] [nvarchar](150) NULL,
        [SysName] [nvarchar](150) NULL,
        [UserID] [nvarchar](150) NULL,
        [UserName] [nvarchar](150) NULL,
        [CreateOn] [nvarchar](150) NULL
    );
    PRINT 'Created table [dbo].[Acc_Mst_ReceiptType] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Mst_PayRecpts_Format_New
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Mst_PayRecpts_Format_New]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Mst_PayRecpts_Format_New] (
        [Ccode] [nvarchar](500) NULL,
        [Lcode] [nvarchar](500) NULL,
        [AccCateSNo] [nvarchar](50) NULL,
        [AccCateCode] [nvarchar](500) NULL,
        [AccCateName] [nvarchar](500) NULL,
        [AccGroupSNo] [nvarchar](50) NULL,
        [AccGroupCode] [nvarchar](500) NULL,
        [AccGroupName] [nvarchar](500) NULL,
        [AccSubGrpSNo] [nvarchar](50) NULL,
        [AccSubGrpCode] [nvarchar](500) NULL,
        [AccSubGrpName] [nvarchar](500) NULL,
        [AccLedgerHeaderSNo] [nvarchar](50) NULL,
        [AccLedgerHeaderCode] [nvarchar](500) NULL,
        [AccLedgerHeaderName] [nvarchar](500) NULL,
        [AccGenLdgCode] [nvarchar](500) NULL
    );
    PRINT 'Created table [dbo].[Acc_Mst_PayRecpts_Format_New] successfully.';
END;
GO

-- =============================================================
-- Table: dbo.Acc_Mst_PayRecpts_Sch_Format_New
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Acc_Mst_PayRecpts_Sch_Format_New]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] (
        [Ccode] [nvarchar](500) NULL,
        [Lcode] [nvarchar](500) NULL,
        [AccCateSNo] [nvarchar](50) NULL,
        [AccCateCode] [nvarchar](500) NULL,
        [AccCateName] [nvarchar](500) NULL,
        [AccGroupSNo] [nvarchar](50) NULL,
        [AccGroupCode] [nvarchar](500) NULL,
        [AccGroupName] [nvarchar](500) NULL,
        [AccSubGrpSNo] [nvarchar](50) NULL,
        [AccSubGrpCode] [nvarchar](500) NULL,
        [AccSubGrpName] [nvarchar](500) NULL,
        [AccLedgerHeaderSNo] [nvarchar](50) NULL,
        [AccLedgerHeaderCode] [nvarchar](500) NULL,
        [AccLedgerHeaderName] [nvarchar](500) NULL,
        [AccLedgerSubHeaderSNo] [nvarchar](500) NULL,
        [AccLedgerSubHeaderCode] [nvarchar](500) NULL,
        [AccLedgerSubHeaderName] [nvarchar](500) NULL,
        [AccGenLdgCode] [nvarchar](500) NULL
    );
    PRINT 'Created table [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] successfully.';
END;
GO

-- =============================================================
-- Seed Data: dbo.Acc_Mst_ReceiptType (35 rows from SCOTO_ACC_ERP)
-- =============================================================
IF NOT EXISTS (SELECT 1 FROM [dbo].[Acc_Mst_ReceiptType])
BEGIN
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'CDS-HO', 'Donation', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'CDS-HO', 'Depot', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'CDS-HO', 'Advance Receipt', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'CDS-HO', 'Rent Receipt', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'CDS-HO', 'Interest', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'CDS-HO', 'Others', 'Delete', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT I', 'Regualr Collections', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT I', 'Special Collections', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT I', 'Mass Income', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT I', 'Special Mass Income', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT I', 'Depot Income', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT I', 'Various Income', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT II', 'Education', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT III', 'Regualr Collections', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'CDS-HO', 'Contra', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'CDS-HO', 'Fixed Asset', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'CDS-HO', 'Mass Stipend', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT II', 'Others Receipt', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT I', 'Others Receipt', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'CDS-HO', 'Special Collection', 'Delete', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'CDS-HO', 'Others Receipt', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT I', 'Rental', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT I', 'Interest', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT I', 'Fixed Asset', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT I', 'Contra Receipts', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT III', 'Special Collections', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT III', 'Mass Income', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT III', 'Special Mass Income', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT III', 'Depot Income', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT III', 'Various Income', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT III', 'Others Receipt', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT III', 'Rental', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT III', 'Interest', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT III', 'Fixed Asset', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    INSERT INTO [dbo].[Acc_Mst_ReceiptType] ([Ccode], [Lcode], [ReceiptTypeName], [Status], [SysIp], [SysName], [UserID], [UserName], [CreateOn]) VALUES ('CDS', 'UNIT III', 'Contra Receipts', 'Add', '192.168.0.18', 'SCOTOPC', 'CDS', 'CDS', 'Mar 21 2025 10:18AM');
    PRINT 'Seeded [dbo].[Acc_Mst_ReceiptType] with 35 reference rows.';
END;
GO

-- =============================================================
-- Seed Data: dbo.Acc_Mst_PayRecpts_Format_New (46 rows from SCOTO_ACC_ERP)
-- =============================================================
IF NOT EXISTS (SELECT 1 FROM [dbo].[Acc_Mst_PayRecpts_Format_New])
BEGIN
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '1', '', 'Opening Balance', '1', '', 'Opening Balance', '1', '', 'Opening Balance', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Programe Income', '1', '', 'Voluntary Contribution', '1', '', 'Voluntary Contribution', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Programe Income', '2', '', 'Receipts from Main Objects', '1', '', 'Receipts from Main Objects', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Programe Income', '3', '', 'Receipts from Incidental Objects', '1', '', 'Receipts from Incidental Objects', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Receipt from other than Main Objects', '1', '', 'Receipt from other than Main Objects', '1', '', 'Receipt from other than Main Objects', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '3', '', 'Any other Income', '1', '', 'Any other Income', '1', '', 'Any other Income', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '4', '', 'Capital Receipts', '1', '', 'Capital Receipts', '1', '', 'Capital Receipts', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '5', '', 'Other Capital Receipts', '1', '', 'Other Capital Receipts', '1', '', 'Other Capital Receipts', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '6', '', 'Contra Receipt', '1', '', 'Contra Receipt', '1', '', 'Contra Receipt', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '7', '', 'Total Receipts (1+2+3+4+5+6+7)', '1', '', 'Total Receipts (1+2+3+4+5+6+7)', '1', '', 'Total Receipts (1+2+3+4+5+6+7)', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '1', '', 'Programe Expenses', '1', '', 'Religious', '1', '', 'Religious', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '1', '', 'Programe Expenses', '2', '', 'Relief of the Poor', '1', '', 'Relief of the Poor', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '1', '', 'Programe Expenses', '3', '', 'Education', '1', '', 'Education', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '1', '', 'Programe Expenses', '4', '', 'Medical Relief', '1', '', 'Medical Relief', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '1', '', 'Programe Expenses', '5', '', 'Preservation of Environment', '1', '', 'Preservation of Environment', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '1', '', 'Programe Expenses', '6', '', 'General Public Utility', '1', '', 'General Public Utility', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '2', '', 'Other Expenses', '1', '', 'Other Expenses', '1', '', 'Other Expenses', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '3', '', 'Admin Expenses', '1', '', 'Admin Expenses', '1', '', 'Admin Expenses', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '4', '', 'Capital Payments', '1', '', 'Capital Payments', '1', '', 'Capital Payments', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '5', '', 'Other Capital Payments', '1', '', 'Other Capital Payments', '1', '', 'Other Capital Payments', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '6', '', 'Contra Payments', '1', '', 'Contra Payments', '1', '', 'Contra Payments', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Closing Balance', '1', '', 'Closing Balance', '1', '', 'Closing Balance', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '8', '', 'Total Payments (1+2+3+4+5+6+7)', '1', '', 'Total Payments (1+2+3+4+5+6+7)', '1', '', 'Total Payments (1+2+3+4+5+6+7)', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '1', '1', 'RECEIPTS', '1', '', 'Opening Balance', '1', '', 'Opening Balance', '1', '', 'Opening Balance', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '1', '1', 'RECEIPTS', '2', '', 'Programe Income', '1', '', 'Voluntary Contribution', '1', '', 'Voluntary Contribution', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '1', '1', 'RECEIPTS', '2', '', 'Programe Income', '2', '', 'Receipts from Main Objects', '1', '', 'Receipts from Main Objects', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '1', '1', 'RECEIPTS', '2', '', 'Programe Income', '3', '', 'Receipts from Incidental Objects', '1', '', 'Receipts from Incidental Objects', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '1', '1', 'RECEIPTS', '2', '', 'Receipt from other than Main Objects', '1', '', 'Receipt from other than Main Objects', '1', '', 'Receipt from other than Main Objects', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '1', '1', 'RECEIPTS', '3', '', 'Any other Income', '1', '', 'Any other Income', '1', '', 'Any other Income', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '1', '1', 'RECEIPTS', '4', '', 'Capital Receipts', '1', '', 'Capital Receipts', '1', '', 'Capital Receipts', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '1', '1', 'RECEIPTS', '5', '', 'Other Capital Receipts', '1', '', 'Other Capital Receipts', '1', '', 'Other Capital Receipts', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '1', '1', 'RECEIPTS', '6', '', 'Contra Receipt', '1', '', 'Contra Receipt', '1', '', 'Contra Receipt', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '1', '1', 'RECEIPTS', '7', '', 'Total Receipts (1+2+3+4+5+6+7)', '1', '', 'Total Receipts (1+2+3+4+5+6+7)', '1', '', 'Total Receipts (1+2+3+4+5+6+7)', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '1', '', 'Programe Expenses', '1', '', 'Religious', '1', '', 'Religious', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '1', '', 'Programe Expenses', '2', '', 'Relief of the Poor', '1', '', 'Relief of the Poor', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '1', '', 'Programe Expenses', '3', '', 'Education', '1', '', 'Education', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '1', '', 'Programe Expenses', '4', '', 'Medical Relief', '1', '', 'Medical Relief', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '1', '', 'Programe Expenses', '5', '', 'Preservation of Environment', '1', '', 'Preservation of Environment', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '1', '', 'Programe Expenses', '6', '', 'General Public Utility', '1', '', 'General Public Utility', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '2', '', 'Other Expenses', '1', '', 'Other Expenses', '1', '', 'Other Expenses', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '3', '', 'Admin Expenses', '1', '', 'Admin Expenses', '1', '', 'Admin Expenses', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '4', '', 'Capital Payments', '1', '', 'Capital Payments', '1', '', 'Capital Payments', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '5', '', 'Other Capital Payments', '1', '', 'Other Capital Payments', '1', '', 'Other Capital Payments', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '6', '', 'Contra Payments', '1', '', 'Contra Payments', '1', '', 'Contra Payments', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '7', '', 'Closing Balance', '1', '', 'Closing Balance', '1', '', 'Closing Balance', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'UNIT II', '2', '2', 'PAYMENTS', '8', '', 'Total Payments (1+2+3+4+5+6+7)', '1', '', 'Total Payments (1+2+3+4+5+6+7)', '1', '', 'Total Payments (1+2+3+4+5+6+7)', '');
    PRINT 'Seeded [dbo].[Acc_Mst_PayRecpts_Format_New] with 46 reference rows.';
END;
GO

-- =============================================================
-- Seed Data: dbo.Acc_Mst_PayRecpts_Sch_Format_New (58 rows from SCOTO_ACC_ERP)
-- =============================================================
IF NOT EXISTS (SELECT 1 FROM [dbo].[Acc_Mst_PayRecpts_Sch_Format_New])
BEGIN
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '1', '', 'Opening Balance', '1', '', 'Cash in Hand', '1', '', 'Cash in Hand', '1', '', 'Cash in Hand', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '1', '', 'Opening Balance', '2', '', 'Cash at Bank', '2', '', 'Cash at Bank', '1', '', 'Cash at Bank', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '1', '', 'Opening Balance', '3', '', 'Fixed/ Recuring Deposits', '3', '', 'Fixed/ Recuring Deposits', '1', '', 'Fixed/ Recuring Deposits', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '1', '', 'Opening Balance', '4', '', 'Corpus Fund FD', '4', '', 'Corpus Fund FD', '1', '', 'Corpus Fund FD', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '1', '', 'Opening Balance', '5', '', 'Total', '5', '', 'Total', '1', '', 'Total', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '1', '', 'Rent Advance', '1', '', 'Rent Advance', '1', '', 'Rent Advance', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '2', '', 'Loan Recovery', '2', '', 'Loan Recovery', '1', '', 'Loan Recovery', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '3', '', 'GST Tax Collection', '3', '', 'GST Tax Collection', '1', '', 'CGST - 9% Received', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '3', '', 'GST Tax Collection', '3', '', 'GST Tax Collection', '2', '', 'SGST - 9% Received', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '3', '', 'GST Tax Collection', '3', '', 'GST Tax Collection', '3', '', 'IGST - 18% Received', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '4', '', 'Sundry Creditors', '4', '', 'Sundry Creditors', '1', '', 'Sundry Creditors', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '5', '', 'Sundry Debtors', '5', '', 'Sundry Debtors', '1', '', 'Sundry Debtors', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '6', '', 'TDS Payable', '6', '', 'TDS Payable', '1', '', 'TDS Payable', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '6', '', 'TDS Payable', '6', '', 'TDS Payable', '1', '', 'TDS - Contracts - Individuals/HUF 194-C - 1%', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '6', '', 'TDS Payable', '6', '', 'TDS Payable', '2', '', 'TDS - Contracts - Others  194-C -2%', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '6', '', 'TDS Payable', '6', '', 'TDS Payable', '3', '', 'TDS - Professional Fee 194-J -10%', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '6', '', 'TDS Payable', '6', '', 'TDS Payable', '4', '', 'TDS - Technical Services 194-JB 2%', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '7', '', 'TDS Receivable', '7', '', 'TDS Receivable', '1', '', 'TDS Receivable', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '8', '', 'Sale of Fixed Asset', '8', '', 'Sale of Fixed Asset', '1', '', 'Sale of Fixed Asset', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '9', '', 'Sale or redemption of investments', '9', '', 'Sale or redemption of investments', '1', '', 'Sale or redemption of investments', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '10', '', 'Advances & Deposits', '10', '', 'Advances & Deposits', '1', '', 'Advances & Deposits', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '2', '', 'Capital Receipt', '11', '', 'Total', '11', '', 'Total', '1', '', 'Total', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '3', '', 'Other Capital Receipts', '1', '', 'Other Capital Receipts', '1', '', 'Other Capital Receipts', '1', '', 'Other Capital Receipts', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '4', '', 'Contra Receipt', '1', '', 'Revenue', '1', '', 'Contribution from Diocese', '1', '', 'Contribution from Diocese', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '4', '', 'Contra Receipt', '1', '', 'Capital', '2', '', 'Loan from Diocese', '1', '', 'Loan from Diocese', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '1', '1', 'RECEIPTS', '4', '', 'Contra Receipt', '2', '', 'Total (A+B)', '3', '', 'Total (A+B)', '1', '', 'Total (A+B)', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '5', '', 'Capital Payments', '11', '', 'Total', '11', '', 'Total', '1', '', 'Total', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '6', '', 'Other Capital Payments', '1', '', 'Other Capital Payments', '1', '', 'Other Capital Payments', '1', '', 'Other Capital Payments', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'African Mission', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'Bible Sunday', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'Communio India Sunday', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'Good Friday', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'Holy Childhood', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'Holy See', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'Mission Sunday', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'Peter Pence', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'St.Peter the Apostle', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'Vocation Sunday', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'World Communication Day', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'Contribution to Diocese', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '1', '', 'Revenue', '1', '', 'Revenue', '1', '', 'Mass Remittance', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '2', '', 'Capital', '1', '', 'Capital', '1', '', 'Loan repaid to Diocese', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '7', '', 'Contra Payments ', '3', '', 'Total', '1', '', 'Total', '1', '', 'Total', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '8', '', 'Closing Balance', '1', '', 'Cash in Hand', '1', '', 'Cash in Hand', '1', '', 'Cash in Hand', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '8', '', 'Closing Balance', '2', '', 'Cash at Bank', '2', '', 'Cash at Bank', '1', '', 'Cash at Bank', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '8', '', 'Closing Balance', '3', '', 'Fixed/ Recuring Deposits', '3', '', 'Fixed/ Recuring Deposits', '1', '', 'Fixed/ Recuring Deposits', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '8', '', 'Closing Balance', '4', '', 'Corpus Fund FD', '4', '', 'Corpus Fund FD', '1', '', 'Corpus Fund FD', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '8', '', 'Closing Balance', '5', '', 'Total', '5', '', 'Total', '1', '', 'Total', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '5', '', 'Capital Payments', '1', '', 'Purchase of Fixed Asset', '1', '', 'Purchase of Fixed Asset', '1', '', 'Purchase of Fixed Asset', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '5', '', 'Capital Payments', '2', '', 'TDS Payable', '2', '', 'TDS Payable', '1', '', 'TDS Payable', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '5', '', 'Capital Payments', '3', '', 'TDS Receivable', '3', '', 'TDS Receivable', '1', '', 'TDS Receivable', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '5', '', 'Capital Payments', '4', '', 'Sundry Debtors', '4', '', 'Sundry Debtors', '1', '', 'Sundry Debtors', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '5', '', 'Capital Payments', '5', '', 'Sundry Creditors', '5', '', 'Sundry Creditors', '1', '', 'Sundry Creditors', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '5', '', 'Capital Payments', '6', '', 'Loans & Advances', '6', '', 'Loans & Advances', '1', '', 'Loans & Advances', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '5', '', 'Capital Payments', '7', '', 'Deposits', '7', '', 'Deposits', '1', '', 'Deposits', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '5', '', 'Capital Payments', '8', '', 'Investments Made', '8', '', 'Investments Made', '1', '', 'Investments Made', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '5', '', 'Capital Payments', '9', '', 'GST Paid', '9', '', 'GST Paid', '1', '', 'GST Paid', '');
    INSERT INTO [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] ([Ccode], [Lcode], [AccCateSNo], [AccCateCode], [AccCateName], [AccGroupSNo], [AccGroupCode], [AccGroupName], [AccSubGrpSNo], [AccSubGrpCode], [AccSubGrpName], [AccLedgerHeaderSNo], [AccLedgerHeaderCode], [AccLedgerHeaderName], [AccLedgerSubHeaderSNo], [AccLedgerSubHeaderCode], [AccLedgerSubHeaderName], [AccGenLdgCode]) VALUES ('CDS', 'CDS-HO', '2', '2', 'PAYMENTS', '5', '', 'Capital Payments', '10', '', 'Others', '10', '', 'Others', '1', '', 'Others', '');
    PRINT 'Seeded [dbo].[Acc_Mst_PayRecpts_Sch_Format_New] with 58 reference rows.';
END;
GO
