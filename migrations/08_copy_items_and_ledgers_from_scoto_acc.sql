/*
===============================================================================
Migration 08: Copy Master Data (Mst_Item & Acc_Mst_Ledger)
Source Database : SCOTO_ACC_ERP
Target Database : Scoto_Admin_ERP

Description:
  Inserts Item Master (Mst_Item) and Ledger Master (Acc_Mst_Ledger) records
  from SCOTO_ACC_ERP into Scoto_Admin_ERP.
  
  Features:
  - Idempotent: Uses NOT EXISTS checks to prevent duplicate key errors.
  - Explicit Column Mappings: All 15 Mst_Item columns and 77 Acc_Mst_Ledger columns.
===============================================================================
*/

-- =============================================================
-- Step 1: Copy Mst_Item (Item Master: Products, BOM items, HSN)
-- =============================================================
INSERT INTO [dbo].[Mst_Item] (
    [ItemCode],
    [ItemType],
    [ItemDescription],
    [ProductType],
    [HSNCode],
    [UOM],
    [SerialNo],
    [Ccode],
    [Lcode],
    [Status],
    [Host_IP],
    [Host_Name],
    [UserCode],
    [UserName],
    [CreatedOn]
)
SELECT 
    src.[ItemCode],
    src.[ItemType],
    src.[ItemDescription],
    src.[ProductType],
    src.[HSNCode],
    src.[UOM],
    src.[SerialNo],
    src.[Ccode],
    src.[Lcode],
    src.[Status],
    src.[Host_IP],
    src.[Host_Name],
    src.[UserCode],
    src.[UserName],
    src.[CreatedOn]
FROM [SCOTO_ACC_ERP].[dbo].[Mst_Item] src
WHERE NOT EXISTS (
    SELECT 1 FROM [dbo].[Mst_Item] tgt 
    WHERE tgt.[ItemCode] = src.[ItemCode]
);
GO

-- =============================================================
-- Step 2: Copy Acc_Mst_Ledger (Ledger Master: Customers, Suppliers, Banks)
-- =============================================================
INSERT INTO [dbo].[Acc_Mst_Ledger] (
    [Ccode],
    [Lcode],
    [LedgerCode],
    [LedgerGrpId],
    [LedgerGrpName],
    [LedgerCategory],
    [Region],
    [SupplyFor],
    [LedgerName],
    [ChequePrintName],
    [Ledger_Class],
    [HouseNo],
    [Add1],
    [Add2],
    [City],
    [PinCode],
    [State],
    [Country],
    [MobileNo],
    [TelNo],
    [ContectName],
    [ContectNo],
    [MailID],
    [WebSite],
    [BankId],
    [BankName],
    [AccountNo],
    [BranchName],
    [Branch_Addr],
    [IFSCCode],
    [SWIFTCode],
    [IBANCode],
    [GSTNo],
    [CINNo],
    [PanNo],
    [TanNo],
    [IECode],
    [LEICode],
    [MSME_Status],
    [MSME_No],
    [PaymentDays],
    [DayCondition],
    [AdvancePayment],
    [AdvanceCondition],
    [Inco_Terms],
    [PaymentTerms],
    [TC],
    [PackingTerms],
    [Quality],
    [Warranty],
    [AccountTypeCode],
    [AccountType],
    [PaymentBlock],
    [SupplierBlock],
    [RoundOff],
    [Status],
    [IsActive],
    [Approval_Status],
    [SysIp],
    [SysName],
    [UserID],
    [UserName],
    [CreateOn],
    [ApprovedBy],
    [ApprovedOn],
    [AccGrpCode],
    [AccGrpName],
    [LedgerNameCategory],
    [MSME_Certificate_No],
    [Supplier_Status],
    [Inco_Terms1],
    [Inco_Terms2],
    [Inco_Terms3],
    [Area],
    [LedgerType],
    [OpeningBalance],
    [BalanceType]
)
SELECT
    src.[Ccode],
    src.[Lcode],
    src.[LedgerCode],
    src.[LedgerGrpId],
    src.[LedgerGrpName],
    src.[LedgerCategory],
    src.[Region],
    src.[SupplyFor],
    src.[LedgerName],
    src.[ChequePrintName],
    src.[Ledger_Class],
    src.[HouseNo],
    src.[Add1],
    src.[Add2],
    src.[City],
    src.[PinCode],
    src.[State],
    src.[Country],
    src.[MobileNo],
    src.[TelNo],
    src.[ContectName],
    src.[ContectNo],
    src.[MailID],
    src.[WebSite],
    src.[BankId],
    src.[BankName],
    src.[AccountNo],
    src.[BranchName],
    src.[Branch_Addr],
    src.[IFSCCode],
    src.[SWIFTCode],
    src.[IBANCode],
    src.[GSTNo],
    src.[CINNo],
    src.[PanNo],
    src.[TanNo],
    src.[IECode],
    src.[LEICode],
    src.[MSME_Status],
    src.[MSME_No],
    src.[PaymentDays],
    src.[DayCondition],
    src.[AdvancePayment],
    src.[AdvanceCondition],
    src.[Inco_Terms],
    src.[PaymentTerms],
    src.[TC],
    src.[PackingTerms],
    src.[Quality],
    src.[Warranty],
    src.[AccountTypeCode],
    src.[AccountType],
    src.[PaymentBlock],
    src.[SupplierBlock],
    src.[RoundOff],
    src.[Status],
    src.[IsActive],
    src.[Approval_Status],
    src.[SysIp],
    src.[SysName],
    src.[UserID],
    src.[UserName],
    src.[CreateOn],
    src.[ApprovedBy],
    src.[ApprovedOn],
    src.[AccGrpCode],
    src.[AccGrpName],
    src.[LedgerNameCategory],
    src.[MSME_Certificate_No],
    src.[Supplier_Status],
    src.[Inco_Terms1],
    src.[Inco_Terms2],
    src.[Inco_Terms3],
    src.[Area],
    src.[LedgerType],
    0.00 AS [OpeningBalance],
    CASE WHEN src.[LedgerType] = 'Customer' THEN 'Dr' ELSE 'Cr' END AS [BalanceType]
FROM [SCOTO_ACC_ERP].[dbo].[Acc_Mst_Ledger] src
WHERE NOT EXISTS (
    SELECT 1 FROM [dbo].[Acc_Mst_Ledger] tgt 
    WHERE tgt.[LedgerCode] = src.[LedgerCode]
);
GO
