import sys
import re
sys.path.insert(0, 'c:/Projects/Scoto/office/scoto-backend')
from src.api.deps import get_mssql_session
from sqlalchemy import text

def clean(s):
    if not s:
        return ""
    val = re.sub(r"(?i)^(m\s*/\s*s\.?|messrs\.?|shri\.?|smt\.?|mr\.?|mrs\.?)\s*", "", str(s).strip())
    val = re.sub(r"[\.,\'\"\-\s]+$", "", val).strip()
    return val

gen = get_mssql_session('db2')()
db = next(gen)

# 1. Clean Acc_Mst_Ledger
ledgers = db.execute(text("SELECT LedgerCode, LedgerName FROM dbo.Acc_Mst_Ledger WHERE LedgerName LIKE '%M/s%' OR LedgerName LIKE '%M/S%'")).fetchall()
for code, name in ledgers:
    new_name = clean(name)
    print(f"Updating Ledger {code}: '{name}' -> '{new_name}'")
    db.execute(
        text("UPDATE dbo.Acc_Mst_Ledger SET LedgerName = :n, ChequePrintName = :n WHERE LedgerCode = :c"),
        {"n": new_name, "c": code}
    )

# 2. Clean Acc_Sales_Inv_Main
invoices = db.execute(text("SELECT TransNo, CustomerName FROM dbo.Acc_Sales_Inv_Main WHERE CustomerName LIKE '%M/s%' OR CustomerName LIKE '%M/S%'")).fetchall()
for tno, cname in invoices:
    new_cname = clean(cname)
    print(f"Updating Invoice Main {tno}: '{cname}' -> '{new_cname}'")
    db.execute(
        text("UPDATE dbo.Acc_Sales_Inv_Main SET CustomerName = :n WHERE TransNo = :t"),
        {"n": new_cname, "t": tno}
    )

# 3. Clean Acc_Sales_Inv_Sub
db.execute(text("""
    UPDATE s
    SET s.CustomerName = m.CustomerName
    FROM dbo.Acc_Sales_Inv_Sub s
    INNER JOIN dbo.Acc_Sales_Inv_Main m ON s.TransNo = m.TransNo
"""))

db.commit()
print("All DB records successfully cleaned of 'M/s.' prefix!")
