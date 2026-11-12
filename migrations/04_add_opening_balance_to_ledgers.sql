-- ============================================================================
-- SCOTO ERP - MIGRATION SCRIPT: ADD OPENING BALANCE COLUMNS TO LEDGER MASTERS
-- Description: Adds OpeningBalance and BalanceType columns to Acc_Mst_GeneralLedger
--              and Acc_Mst_Ledger tables.
-- Safe & Idempotent: Can be run multiple times without error or data loss.
-- ============================================================================

-- Note: Ensure target database is selected (e.g. USE [SCOTO_ACC_ERP] or USE [Scoto_Admin_ERP])

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

PRINT 'Starting migration: Add OpeningBalance & BalanceType to Ledger Masters...';

-- ============================================================================
-- 1. ADD COLUMNS TO Acc_Mst_GeneralLedger
-- ============================================================================

IF COL_LENGTH(N'dbo.Acc_Mst_GeneralLedger', N'OpeningBalance') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Mst_GeneralLedger ADD [OpeningBalance] NUMERIC(18,2) NULL CONSTRAINT DF_Acc_Mst_GeneralLedger_OpeningBalance DEFAULT 0;
    PRINT 'Added column OpeningBalance to Acc_Mst_GeneralLedger';
END
GO

IF COL_LENGTH(N'dbo.Acc_Mst_GeneralLedger', N'BalanceType') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Mst_GeneralLedger ADD [BalanceType] VARCHAR(10) NULL CONSTRAINT DF_Acc_Mst_GeneralLedger_BalanceType DEFAULT 'Dr';
    PRINT 'Added column BalanceType to Acc_Mst_GeneralLedger';
END
GO

-- ============================================================================
-- 2. ADD COLUMNS TO Acc_Mst_Ledger
-- ============================================================================

IF COL_LENGTH(N'dbo.Acc_Mst_Ledger', N'OpeningBalance') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Mst_Ledger ADD [OpeningBalance] NUMERIC(18,2) NULL CONSTRAINT DF_Acc_Mst_Ledger_OpeningBalance DEFAULT 0;
    PRINT 'Added column OpeningBalance to Acc_Mst_Ledger';
END
GO

IF COL_LENGTH(N'dbo.Acc_Mst_Ledger', N'BalanceType') IS NULL
BEGIN
    ALTER TABLE dbo.Acc_Mst_Ledger ADD [BalanceType] VARCHAR(10) NULL CONSTRAINT DF_Acc_Mst_Ledger_BalanceType DEFAULT 'Cr';
    PRINT 'Added column BalanceType to Acc_Mst_Ledger';
END
GO

-- ============================================================================
-- 3. INITIALIZE EXISTING NULL VALUES
-- ============================================================================

UPDATE dbo.Acc_Mst_GeneralLedger
SET 
    [OpeningBalance] = ISNULL([OpeningBalance], 0),
    [BalanceType] = ISNULL([BalanceType], 'Dr')
WHERE [OpeningBalance] IS NULL OR [BalanceType] IS NULL;
GO

UPDATE dbo.Acc_Mst_Ledger
SET 
    [OpeningBalance] = ISNULL([OpeningBalance], 0),
    [BalanceType] = ISNULL([BalanceType], 'Cr')
WHERE [OpeningBalance] IS NULL OR [BalanceType] IS NULL;
GO

PRINT 'Migration: OpeningBalance & BalanceType added and initialized successfully!';
GO

