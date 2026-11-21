-- ============================================================================
-- SCOTO ADMIN ERP - MIGRATION SCRIPT 12: CUSTOMER UNIT & MULTI-PLANT COLUMNS
-- Target Database: [Scoto_Admin_ERP] / [scotoAdmin]
-- Description:
--   1. Adds CustomerUnit and ParentLedgerCode to dbo.Acc_Mst_Ledger.
--   2. Adds CustomerUnit to dbo.Acc_Sales_Inv_Main (Sales Invoice Header).
--   3. Adds CustomerUnit to dbo.Acc_Sales_Inv_Sub (Sales Invoice Line Items).
--   4. Adds CustomerUnit to dbo.Acc_Receipts_Sub (Receipt Allocations).
-- Safe & Idempotent: Can be run multiple times without error or data loss.
-- ============================================================================

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

PRINT 'Starting migration: 12_add_customer_unit_to_ledgers_and_invoices...';

-- ============================================================================
-- 1. ADD CUSTOMER UNIT & PARENT LEDGER TO Acc_Mst_Ledger
-- ============================================================================

IF OBJECT_ID(N'dbo.Acc_Mst_Ledger', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Acc_Mst_Ledger', N'CustomerUnit') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Mst_Ledger
    ADD [CustomerUnit] NVARCHAR(150) NULL;
    PRINT 'Added CustomerUnit to Acc_Mst_Ledger';
END;
GO

IF OBJECT_ID(N'dbo.Acc_Mst_Ledger', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Acc_Mst_Ledger', N'ParentLedgerCode') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Mst_Ledger
    ADD [ParentLedgerCode] VARCHAR(50) NULL;
    PRINT 'Added ParentLedgerCode to Acc_Mst_Ledger';
END;
GO

-- ============================================================================
-- 2. ADD CUSTOMER UNIT TO Acc_Sales_Inv_Main
-- ============================================================================

IF OBJECT_ID(N'dbo.Acc_Sales_Inv_Main', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Acc_Sales_Inv_Main', N'CustomerUnit') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Sales_Inv_Main
    ADD [CustomerUnit] NVARCHAR(150) NULL;
    PRINT 'Added CustomerUnit to Acc_Sales_Inv_Main';
END;
GO

-- ============================================================================
-- 3. ADD CUSTOMER UNIT TO Acc_Sales_Inv_Sub
-- ============================================================================

IF OBJECT_ID(N'dbo.Acc_Sales_Inv_Sub', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Acc_Sales_Inv_Sub', N'CustomerUnit') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Sales_Inv_Sub
    ADD [CustomerUnit] NVARCHAR(150) NULL;
    PRINT 'Added CustomerUnit to Acc_Sales_Inv_Sub';
END;
GO

-- ============================================================================
-- 4. ADD CUSTOMER UNIT TO Acc_Receipts_Sub
-- ============================================================================

IF OBJECT_ID(N'dbo.Acc_Receipts_Sub', N'U') IS NOT NULL
 AND COL_LENGTH(N'dbo.Acc_Receipts_Sub', N'CustomerUnit') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Receipts_Sub
    ADD [CustomerUnit] NVARCHAR(150) NULL;
    PRINT 'Added CustomerUnit to Acc_Receipts_Sub';
END;
GO

PRINT 'Migration 12 finished successfully!';
GO
