/*
===============================================================================
Migration 09: Copy General Ledger Master (Acc_Mst_GeneralLedger)
Source Database : SCOTO_ACC_ERP
Target Database : Scoto_Admin_ERP

Description:
  Inserts General Ledger Master (Acc_Mst_GeneralLedger) accounts from 
  SCOTO_ACC_ERP into Scoto_Admin_ERP. Total: 267 chart-of-accounts entries.
  
  Features:
  - Idempotent: Uses NOT EXISTS checks on AccGenLdgCode to prevent duplicate key errors.
  - Explicit Column Mappings: All 21 columns explicitly mapped.
===============================================================================
*/

-- =============================================================
-- Step 1: Copy Acc_Mst_GeneralLedger from SCOTO_ACC_ERP
-- =============================================================
INSERT INTO [dbo].[Acc_Mst_GeneralLedger] (
    [Ccode],
    [Lcode],
    [AccCateCode],
    [AccCateName],
    [AccGroupCode],
    [AccGroupName],
    [AccSubGrpCode],
    [AccSubGrpName],
    [AccLedgerHeaderCode],
    [AccLedgerHeaderName],
    [AccGenLdgCode],
    [AccGenLdgName],
    [CostCenter],
    [Status],
    [SysIp],
    [SysName],
    [UserID],
    [UserName],
    [CreateOn],
    [OpeningBalance],
    [BalanceType]
)
SELECT 
    src.[Ccode],
    src.[Lcode],
    src.[AccCateCode],
    src.[AccCateName],
    src.[AccGroupCode],
    src.[AccGroupName],
    src.[AccSubGrpCode],
    src.[AccSubGrpName],
    src.[AccLedgerHeaderCode],
    src.[AccLedgerHeaderName],
    src.[AccGenLdgCode],
    src.[AccGenLdgName],
    src.[CostCenter],
    src.[Status],
    src.[SysIp],
    src.[SysName],
    src.[UserID],
    src.[UserName],
    src.[CreateOn],
    src.[OpeningBalance],
    src.[BalanceType]
FROM [SCOTO_ACC_ERP].[dbo].[Acc_Mst_GeneralLedger] src
WHERE NOT EXISTS (
    SELECT 1 FROM [dbo].[Acc_Mst_GeneralLedger] tgt 
    WHERE tgt.[AccGenLdgCode] = src.[AccGenLdgCode]
);
GO
