/*
===============================================================================
Migration 10: Standardize Company Code and Location Code to 'SCT' & 'UNIT I'
Target Database: Scoto_Admin_ERP

Description:
  Updates existing legacy rows in transaction and master tables that have
  Ccode = '01' / '1' or Lcode = '01' / '1' to the official standard:
    - Ccode = 'SCT'
    - Lcode = 'UNIT I'
===============================================================================
*/

-- 1. Quotations
UPDATE [dbo].[Acc_Quotation_Main]
SET [Ccode] = 'SCT', [Lcode] = 'UNIT I'
WHERE [Ccode] IN ('01', '1', '') OR [Ccode] IS NULL
   OR [Lcode] IN ('01', '1', '') OR [Lcode] IS NULL;
GO

UPDATE [dbo].[Acc_Quotation_Sub]
SET [Ccode] = 'SCT', [Lcode] = 'UNIT I'
WHERE [Ccode] IN ('01', '1', '') OR [Ccode] IS NULL
   OR [Lcode] IN ('01', '1', '') OR [Lcode] IS NULL;
GO

-- 2. Proforma Invoices
UPDATE [dbo].[Acc_Proforma_Inv_Main]
SET [Ccode] = 'SCT', [Lcode] = 'UNIT I'
WHERE [Ccode] IN ('01', '1', '') OR [Ccode] IS NULL
   OR [Lcode] IN ('01', '1', '') OR [Lcode] IS NULL;
GO

UPDATE [dbo].[Acc_Proforma_Inv_Sub]
SET [Ccode] = 'SCT', [Lcode] = 'UNIT I'
WHERE [Ccode] IN ('01', '1', '') OR [Ccode] IS NULL
   OR [Lcode] IN ('01', '1', '') OR [Lcode] IS NULL;
GO

-- 3. Delivery Challans (if tables exist)
IF OBJECT_ID(N'[dbo].[Delivery_main]', N'U') IS NOT NULL
BEGIN
    UPDATE [dbo].[Delivery_main]
    SET [Ccode] = 'SCT', [Lcode] = 'UNIT I'
    WHERE [Ccode] IN ('01', '1', '') OR [Ccode] IS NULL
       OR [Lcode] IN ('01', '1', '') OR [Lcode] IS NULL;
END;
GO

IF OBJECT_ID(N'[dbo].[Delivery_sub]', N'U') IS NOT NULL
BEGIN
    UPDATE [dbo].[Delivery_sub]
    SET [Ccode] = 'SCT', [Lcode] = 'UNIT I'
    WHERE [Ccode] IN ('01', '1', '') OR [Ccode] IS NULL
       OR [Lcode] IN ('01', '1', '') OR [Lcode] IS NULL;
END;
GO

-- 4. Item Master & Ledger Master
UPDATE [dbo].[Mst_Item]
SET [Ccode] = 'SCT', [Lcode] = 'UNIT I'
WHERE [Ccode] IN ('01', '1', '') OR [Ccode] IS NULL
   OR [Lcode] IN ('01', '1', '') OR [Lcode] IS NULL;
GO

UPDATE [dbo].[Acc_Mst_Ledger]
SET [Ccode] = 'SCT', [Lcode] = 'UNIT I'
WHERE [Ccode] IN ('01', '1', '') OR [Ccode] IS NULL
   OR [Lcode] IN ('01', '1', '') OR [Lcode] IS NULL;
GO
