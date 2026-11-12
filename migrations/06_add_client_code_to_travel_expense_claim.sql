-- Migration 06: Add ClientCode to TravelExpense_Claim
-- Links travel claims directly to Customer Master (Acc_Mst_Ledger)

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'TravelExpense_Claim' AND COLUMN_NAME = 'ClientCode'
)
BEGIN
    ALTER TABLE dbo.TravelExpense_Claim
    ADD ClientCode VARCHAR(50) NULL;
    PRINT 'Added ClientCode column to TravelExpense_Claim';
END
GO

