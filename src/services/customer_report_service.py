from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date
import calendar
import re
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException


class CustomerReportService:
    """
    Customer 360 Financial & Transaction Report Service
    Aggregates Ledger Master, Quotations, Proforma Invoices, Sales Invoices, and Tally Vouchers.
    """

    @staticmethod
    def _to_float(val: Any) -> float:
        if val is None:
            return 0.0
        try:
            return float(val)
        except Exception:
            return 0.0

    @staticmethod
    def _normalize_date(d_str: Any) -> Optional[str]:
        """Converts YYYY-MM-DD or DD/MM/YYYY into ISO YYYY-MM-DD string."""
        if not d_str:
            return None
        s = str(d_str).strip()
        m1 = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
        if m1:
            return f"{int(m1.group(1)):04d}-{int(m1.group(2)):02d}-{int(m1.group(3)):02d}"
        m2 = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s)
        if m2:
            return f"{int(m2.group(3)):04d}-{int(m2.group(2)):02d}-{int(m2.group(1)):02d}"
        return None

    @staticmethod
    def resolve_period_bounds(
        fin_year: str = "ALL",
        from_month: Optional[str] = None,
        to_month: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str], str, str]:
        """
        Resolves (calc_from_date, calc_to_date, period_display, period_range).
        For an FY like '2026-2027', returns:
          - full year: ('2026-04-01', '2027-03-31', 'April 2026 to March 2027 (FY 2026-2027)', 'April 2026 to March 2027')
          - custom months: ('2026-04-01', '2026-11-30', 'April 2026 to November 2026 (FY 2026-2027)', 'April 2026 to November 2026')
        """
        clean_fy = re.sub(r"(?i)\bfy[:\s]*", "", fin_year or "ALL").strip()
        is_all = clean_fy.upper() in ("ALL", "")
        y1, y2 = None, None
        if not is_all:
            m = re.search(r"(\d{4})[-_](\d{4})", clean_fy)
            if m:
                y1, y2 = int(m.group(1)), int(m.group(2))
            else:
                m2 = re.search(r"(\d{2})[-_](\d{2})", clean_fy)
                if m2:
                    y1, y2 = 2000 + int(m2.group(1)), 2000 + int(m2.group(2))

        calc_from = from_date
        if not calc_from:
            if from_month and "-" in str(from_month):
                p = str(from_month).split("-")
                calc_from = f"{int(p[0]):04d}-{int(p[1]):02d}-01"
            elif from_month and str(from_month).isdigit() and y1:
                mo = int(from_month)
                yr = y1 if mo >= 4 else y2
                calc_from = f"{yr:04d}-{mo:02d}-01"
            elif y1:
                calc_from = f"{y1:04d}-04-01"

        calc_to = to_date
        if not calc_to:
            if to_month and "-" in str(to_month):
                p = str(to_month).split("-")
                yr, mo = int(p[0]), int(p[1])
                last_day = calendar.monthrange(yr, mo)[1]
                calc_to = f"{yr:04d}-{mo:02d}-{last_day:02d}"
            elif to_month and str(to_month).isdigit() and y2:
                mo = int(to_month)
                yr = y1 if mo >= 4 else y2
                last_day = calendar.monthrange(yr, mo)[1]
                calc_to = f"{yr:04d}-{mo:02d}-{last_day:02d}"
            elif y2:
                calc_to = f"{y2:04d}-03-31"

        if is_all and not calc_from and not calc_to:
            period_display = "All Financial Years"
            period_range = "All Financial Years"
        else:
            try:
                d1 = date.fromisoformat(calc_from) if calc_from else None
                d2 = date.fromisoformat(calc_to) if calc_to else None
                s1 = d1.strftime("%B %Y") if d1 else "Beginning"
                s2 = d2.strftime("%B %Y") if d2 else "Present"
                period_range = f"{s1} to {s2}"
                fy_suffix = f" (FY {y1}-{y2})" if (y1 and y2) else ""
                period_display = f"{period_range}{fy_suffix}"
            except Exception:
                period_display = clean_fy
                period_range = clean_fy

        return calc_from, calc_to, period_display, period_range

    @staticmethod
    def _normalize_approval_status(raw_status: Any, default: str = "Pending") -> str:
        if raw_status is None:
            return default
        s = str(raw_status).strip().lower()
        if s in ("1", "approved", "approve", "cleared"):
            return "Approved"
        if s in ("0", "pending", "add", "created", ""):
            return "Pending"
        if s in ("rejected", "cancelled", "cancel", "2"):
            return "Rejected"
        return str(raw_status).strip()

    @staticmethod
    def get_client_autocomplete(
        db: Session,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Fast auto-complete search across Ledger Master, Sales Invoices, and Transactions for Clients/Customers.
        Ensures any customer with invoice or payment records is discoverable.
        """
        sql = """
            SELECT TOP (:limit)
                LedgerCode,
                LedgerName,
                CustomerUnit,
                ParentLedgerCode,
                ChequePrintName,
                AccountType AS AccLedgerHeaderName,
                LedgerGrpName,
                LedgerCategory,
                Status,
                LedgerType,
                BankName,
                AccountNo,
                IFSCCode,
                BranchName,
                GSTNo,
                PanNo,
                City,
                State,
                MobileNo,
                MailID,
                OpeningBalance,
                BalanceType
            FROM (
                SELECT
                    LedgerCode,
                    LedgerName,
                    ISNULL(CustomerUnit, '') AS CustomerUnit,
                    ISNULL(ParentLedgerCode, '') AS ParentLedgerCode,
                    ChequePrintName,
                    AccountType,
                    LedgerGrpName,
                    LedgerCategory,
                    Status,
                    LedgerType,
                    BankName,
                    AccountNo,
                    IFSCCode,
                    BranchName,
                    GSTNo,
                    PanNo,
                    City,
                    State,
                    MobileNo,
                    MailID,
                    ISNULL(OpeningBalance, 0) AS OpeningBalance,
                    ISNULL(NULLIF(LTRIM(RTRIM(BalanceType)), ''), 'Dr') AS BalanceType
                FROM dbo.Acc_Mst_Ledger
                WHERE Status <> 'Delete'

                UNION

                SELECT DISTINCT
                    COALESCE(NULLIF(CustomerCode, ''), 'CUS-' + CONVERT(VARCHAR(20), ABS(CHECKSUM(CustomerName)) % 10000)) AS LedgerCode,
                    CustomerName AS LedgerName,
                    ISNULL(CustomerUnit, '') AS CustomerUnit,
                    '' AS ParentLedgerCode,
                    CustomerName AS ChequePrintName,
                    'Domestic Customer' AS AccountType,
                    'Customer' AS LedgerGrpName,
                    'Sundry Debtors' AS LedgerCategory,
                    'Active' AS Status,
                    'Customer' AS LedgerType,
                    '' AS BankName,
                    '' AS AccountNo,
                    '' AS IFSCCode,
                    '' AS BranchName,
                    GST AS GSTNo,
                    '' AS PanNo,
                    '' AS City,
                    '' AS State,
                    '' AS MobileNo,
                    '' AS MailID,
                    CAST(0 AS NUMERIC(18,2)) AS OpeningBalance,
                    'Dr' AS BalanceType
                FROM dbo.Acc_Sales_Inv_Main
                WHERE CustomerName IS NOT NULL AND LTRIM(RTRIM(CustomerName)) <> ''
                  AND CustomerName NOT IN (SELECT LedgerName FROM dbo.Acc_Mst_Ledger WHERE Status <> 'Delete')
            ) combined
            WHERE 1=1
        """
        params: Dict[str, Any] = {"limit": limit}

        if search and search.strip():
            term = search.strip()
            sql += """
                AND (
                    LedgerCode LIKE :term
                    OR LedgerName LIKE :term
                    OR CustomerUnit LIKE :term
                    OR GSTNo LIKE :term
                    OR City LIKE :term
                    OR MobileNo LIKE :term
                )
            """
            params["term"] = f"%{term}%"

        sql += " ORDER BY LedgerName ASC"

        rows = db.execute(text(sql), params).mappings().all()
        out = []
        for r in rows:
            d = dict(r)
            u = (d.get("CustomerUnit") or "").strip()
            c_name = (d.get("LedgerName") or "").strip()
            city = (d.get("City") or "").strip()
            if u and city:
                d["displayName"] = f"{c_name} - {u} ({city})"
            elif u:
                d["displayName"] = f"{c_name} - {u}"
            elif city:
                d["displayName"] = f"{c_name} ({city})"
            else:
                d["displayName"] = c_name
            out.append(d)
        return out

    @staticmethod
    def get_available_fin_years(db: Session) -> List[str]:
        """
        Retrieves all distinct Financial Years across transactions, invoices, receipts, and Tally,
        normalized to standard YYYY-YYYY format.
        """
        sql = """
            SELECT DISTINCT REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') AS FinYear
            FROM (
                SELECT FinYearVal FROM dbo.Acc_Quotation_Main WHERE FinYearVal IS NOT NULL AND Status <> 'Delete'
                UNION ALL
                SELECT FinYearVal FROM dbo.Acc_Proforma_Inv_Main WHERE FinYearVal IS NOT NULL AND Status <> 'Delete'
                UNION ALL
                SELECT FinYearVal FROM dbo.Acc_Sales_Inv_Main WHERE FinYearVal IS NOT NULL AND Status <> 'Delete'
                UNION ALL
                SELECT FinYearVal FROM dbo.Acc_Receipts_Main WHERE FinYearVal IS NOT NULL AND ISNULL(Status, '') <> 'Delete'
                UNION ALL
                SELECT FinYearVal FROM dbo.Acc_Trans_All WHERE FinYearVal IS NOT NULL AND ISNULL(Status, '') <> 'Delete'
                UNION ALL
                SELECT FinacialYear AS FinYearVal FROM dbo.MstFinacialYear WHERE FinacialYear IS NOT NULL
            ) t
            WHERE LTRIM(RTRIM(FinYearVal)) <> ''
            ORDER BY FinYear DESC
        """
        rows = db.execute(text(sql)).fetchall()
        years = [r[0] for r in rows if r[0]]
        defaults = ["2026-2027", "2025-2026", "2024-2025"]
        for d in defaults:
            if d not in years:
                years.append(d)
        return sorted(list(set(years)), reverse=True)

    @classmethod
    def get_customer_dossier(
        cls,
        db: Session,
        client_code: str,
        fin_year: Optional[str] = "ALL",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        from_month: Optional[str] = None,
        to_month: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates the complete 360 customer financial dossier.
        """
        code = client_code.strip()
        fy = (fin_year or "ALL").strip()

        # 1. Fetch Customer Master Profile
        ledger_sql = """
            SELECT TOP 1
                LedgerCode,
                LedgerName,
                CustomerUnit,
                ParentLedgerCode,
                ChequePrintName,
                AccountType AS AccLedgerHeaderName,
                LedgerGrpName,
                LedgerType,
                HouseNo,
                Add1,
                Add2,
                Area,
                City,
                State,
                PinCode,
                Country,
                ContectName,
                ContectNo,
                MobileNo,
                TelNo,
                MailID,
                GSTNo,
                PanNo,
                ISNULL(OpeningBalance, 0) AS OpeningBalance,
                ISNULL(NULLIF(LTRIM(RTRIM(BalanceType)), ''), 'Dr') AS BalanceType
            FROM dbo.Acc_Mst_Ledger
            WHERE (
                LTRIM(RTRIM(LedgerCode)) = :code
                OR LTRIM(RTRIM(LedgerName)) = :code
                OR LOWER(LTRIM(RTRIM(LedgerName))) = :code_lower
            )
              AND Status <> 'Delete'
        """
        ledger_row = db.execute(text(ledger_sql), {"code": code, "code_lower": code.lower()}).mappings().first()
        if not ledger_row:
            # Try fuzzy match in Acc_Mst_Ledger by name before other fallbacks
            fuzzy_sql = """
                SELECT TOP 1
                    LedgerCode,
                    LedgerName,
                    CustomerUnit,
                    ParentLedgerCode,
                    ChequePrintName,
                    AccountType AS AccLedgerHeaderName,
                    LedgerGrpName,
                    LedgerType,
                    HouseNo,
                    Add1,
                    Add2,
                    Area,
                    City,
                    State,
                    PinCode,
                    Country,
                    ContectName,
                    ContectNo,
                    MobileNo,
                    TelNo,
                    MailID,
                    GSTNo,
                    PanNo,
                    ISNULL(OpeningBalance, 0) AS OpeningBalance,
                    ISNULL(NULLIF(LTRIM(RTRIM(BalanceType)), ''), 'Dr') AS BalanceType
                FROM dbo.Acc_Mst_Ledger
                WHERE (LedgerName LIKE :code_like OR ChequePrintName LIKE :code_like)
                  AND Status <> 'Delete'
            """
            ledger_row = db.execute(text(fuzzy_sql), {"code_like": f"%{code}%"}).mappings().first()

        if not ledger_row:
            # Fallback to General Ledger
            gen_sql = """
                SELECT TOP 1
                    AccGenLdgCode AS LedgerCode,
                    AccGenLdgName AS LedgerName,
                    '' AS ChequePrintName,
                    AccLedgerHeaderName,
                    AccGroupName AS LedgerGrpName,
                    'General Ledger' AS LedgerType,
                    '' AS HouseNo,
                    '' AS Add1,
                    '' AS Add2,
                    '' AS Area,
                    '' AS ContectName,
                    '' AS ContectNo,
                    '' AS TelNo,
                    '' AS GSTNo,
                    '' AS PanNo,
                    '' AS City,
                    '' AS State,
                    '' AS PinCode,
                    '' AS Country,
                    '' AS MobileNo,
                    '' AS MailID,
                    ISNULL(OpeningBalance, 0) AS OpeningBalance,
                    ISNULL(NULLIF(LTRIM(RTRIM(BalanceType)), ''), 'Dr') AS BalanceType
                FROM dbo.Acc_Mst_GeneralLedger
                WHERE (LTRIM(RTRIM(AccGenLdgCode)) = :code OR LTRIM(RTRIM(AccGenLdgName)) = :code OR LOWER(LTRIM(RTRIM(AccGenLdgName))) = :code_lower)
                  AND Status <> 'Delete'
            """
            ledger_row = db.execute(text(gen_sql), {"code": code, "code_lower": code.lower()}).mappings().first()

        if not ledger_row:
            # Fallback to Sales Invoices / Transactions if client is known there
            inv_row = db.execute(text("""
                SELECT TOP 1
                    COALESCE(NULLIF(CustomerCode, ''), :code) AS LedgerCode,
                    CustomerName AS LedgerName,
                    CustomerName AS ChequePrintName,
                    'Domestic Customer' AS AccLedgerHeaderName,
                    'Customer' AS LedgerGrpName,
                    'Customer' AS LedgerType,
                    '' AS HouseNo,
                    '' AS Add1,
                    '' AS Add2,
                    '' AS Area,
                    '' AS ContectName,
                    '' AS ContectNo,
                    '' AS TelNo,
                    GST AS GSTNo,
                    '' AS PanNo,
                    '' AS City,
                    '' AS State,
                    '' AS PinCode,
                    '' AS Country,
                    '' AS MobileNo,
                    '' AS MailID,
                    0 AS OpeningBalance,
                    'Dr' AS BalanceType
                FROM dbo.Acc_Sales_Inv_Main
                WHERE (CustomerCode = :code OR CustomerName = :code OR CustomerName LIKE :name_like)
                  AND (Status IS NULL OR Status <> 'Delete')
            """), {"code": code, "name_like": f"%{code}%"}).mappings().first()
            if inv_row:
                ledger_row = inv_row
            else:
                trans_row = db.execute(text("""
                    SELECT TOP 1
                        COALESCE(NULLIF(LeaderCode, ''), :code) AS LedgerCode,
                        LedgerName,
                        LedgerName AS ChequePrintName,
                        'Domestic Customer' AS AccLedgerHeaderName,
                        'Customer' AS LedgerGrpName,
                        'Customer' AS LedgerType,
                        '' AS HouseNo,
                        '' AS Add1,
                        '' AS Add2,
                        '' AS Area,
                        '' AS ContectName,
                        '' AS ContectNo,
                        '' AS TelNo,
                        '' AS GSTNo,
                        '' AS PanNo,
                        '' AS City,
                        '' AS State,
                        '' AS PinCode,
                        '' AS Country,
                        '' AS MobileNo,
                        '' AS MailID,
                        0 AS OpeningBalance,
                        'Dr' AS BalanceType
                    FROM dbo.Acc_Trans_All
                    WHERE (LeaderCode = :code OR LedgerName = :code OR LedgerName LIKE :name_like)
                      AND (Status IS NULL OR Status <> 'Delete')
                """), {"code": code, "name_like": f"%{code}%"}).mappings().first()
                if trans_row:
                    ledger_row = trans_row

        if not ledger_row:
            raise HTTPException(
                status_code=404,
                detail=f"Customer/Ledger '{client_code}' not found in Ledger Master, Invoices, or Transactions.",
            )

        customer = dict(ledger_row)
        c_code = (customer.get("LedgerCode") or "").strip()
        c_name = (customer.get("LedgerName") or "").strip()
        c_name_clean = c_name.strip()
        c_name_like = f"%{c_name_clean}%"

        # 1.1 Ensure GSTNo is populated: if missing or blank in Ledger Master, check Sales Invoices
        raw_gst = (customer.get("GSTNo") or "").strip()
        if not raw_gst or raw_gst.lower() in ("none", "null", "-", "n/a", "na"):
            try:
                inv_gst_row = db.execute(text("""
                    SELECT TOP 1 GST 
                    FROM dbo.Acc_Sales_Inv_Main 
                    WHERE (CustomerCode = :code OR CustomerName = :name OR CustomerName LIKE :name_like)
                      AND GST IS NOT NULL AND LTRIM(RTRIM(GST)) <> ''
                      AND (Status IS NULL OR Status <> 'Delete')
                    ORDER BY InvoiceDate DESC, TransNo DESC
                """), {"code": c_code, "name": c_name_clean, "name_like": c_name_like}).fetchone()
                if inv_gst_row and inv_gst_row[0] and str(inv_gst_row[0]).strip():
                    customer["GSTNo"] = str(inv_gst_row[0]).strip()
                    raw_gst = customer["GSTNo"]
            except Exception:
                pass

        # 1.2 Ensure PanNo is populated: if missing or blank, derive from 15-digit GSTIN (chars 3-12)
        raw_pan = (customer.get("PanNo") or "").strip()
        if (not raw_pan or raw_pan.lower() in ("none", "null", "-", "n/a", "na")) and raw_gst:
            clean_gst = raw_gst.upper().strip()
            if len(clean_gst) >= 12:
                candidate_pan = clean_gst[2:12]
                if len(candidate_pan) == 10 and candidate_pan[:5].isalpha():
                    customer["PanNo"] = candidate_pan

        # 1.3 Phone fallback from alternate contact fields
        cur_phone = (customer.get("MobileNo") or "").strip()
        if not cur_phone or cur_phone.lower() in ("none", "null", "-"):
            for alt_ph in (customer.get("ContectNo"), customer.get("TelNo")):
                if alt_ph and str(alt_ph).strip() and str(alt_ph).strip().lower() not in ("none", "null", "-"):
                    customer["MobileNo"] = str(alt_ph).strip()
                    break

        # 1.4 Contact Person fallback
        cur_contact = (customer.get("ContectName") or "").strip()
        if not cur_contact or cur_contact.lower() in ("none", "null", "-"):
            for alt_cn in (customer.get("ContactName"), customer.get("ContactPerson"), customer.get("ChequePrintName")):
                if alt_cn and str(alt_cn).strip() and str(alt_cn).strip().lower() not in ("none", "null", "-") and str(alt_cn).strip() != c_name_clean:
                    customer["ContectName"] = str(alt_cn).strip()
                    break

        core_name = re.sub(r"(?i)\s*(pvt\.?\s*ltd\.?|private\s*limited|p\.?\s*ltd\.?|limited|ltd\.?)\s*\.*$", "", c_name_clean).strip()
        c_core_like = f"%{core_name}%" if len(core_name) >= 4 else c_name_like

        fy_raw = (fin_year or "ALL").strip()
        calc_from_date, calc_to_date, period_display, period_range = cls.resolve_period_bounds(
            fin_year=fy_raw,
            from_month=from_month,
            to_month=to_month,
            from_date=from_date,
            to_date=to_date,
        )

        is_all = 1 if fy_raw.upper() in ("ALL", "") else 0

        # Clean any prefix like "FY " or "FY: "
        clean_fy = re.sub(r"(?i)\bfy[:\s]*", "", fy_raw).strip()
        if clean_fy.upper() in ("ALL", ""):
            is_all = 1

        match_full = re.search(r"(\d{4})[-_](\d{4})", clean_fy)
        if match_full:
            fy_dash = f"{match_full.group(1)}-{match_full.group(2)}"
            fy_under = f"{match_full.group(1)}_{match_full.group(2)}"
        else:
            match_short = re.search(r"(\d{2})[-_](\d{2})", clean_fy)
            if match_short:
                y1 = int(match_short.group(1)) + 2000
                y2 = int(match_short.group(2)) + 2000
                fy_dash = f"{y1}-{y2}"
                fy_under = f"{y1}_{y2}"
            else:
                fy_dash = clean_fy.replace("_", "-")
                fy_under = clean_fy.replace("-", "_")

        # Resolve YearCode from MstFinacialYear (e.g. '2' for 2025_2026, '1' for 2024_2025)
        year_code = ""
        if is_all == 0:
            try:
                yc_row = db.execute(text("""
                    SELECT TOP 1 YearCode 
                    FROM dbo.MstFinacialYear 
                    WHERE REPLACE(FinacialYear, '_', '-') = :fy_dash 
                       OR REPLACE(FinacialYear, '-', '_') = :fy_under
                """), {"fy_dash": fy_dash, "fy_under": fy_under}).fetchone()
                if yc_row:
                    year_code = str(yc_row[0]).strip()
            except Exception:
                pass

        params = {
            "code": c_code,
            "unit": (customer.get("CustomerUnit") or "").strip(),
            "has_unit": 1 if (customer.get("CustomerUnit") or "").strip() else 0,
            "name_lower": c_name_clean.lower(),
            "name_like": c_name_like,
            "core_like": c_core_like,
            "is_all": 1,  # Retrieve all customer documents so Python partitions prior vs period by exact date
            "fy_dash": fy_dash,
            "fy_under": fy_under,
            "year_code": year_code,
        }

        # 2. Quotations
        quote_sql = """
            SELECT
                TransNo,
                TransDate,
                CustomerName,
                Product,
                TotQty,
                TotItemAmt,
                TotCGSTAmt,
                TotSGSTAmt,
                TotIGSTAmt,
                NetAmount,
                ApprovalStatus,
                terms_conditions,
                Remarks,
                LTRIM(RTRIM(FinYearVal)) AS FinYearVal
            FROM dbo.Acc_Quotation_Main
            WHERE (
                (:code <> '' AND (SuppCode = :code OR (:has_unit = 1 AND (SuppCode IS NULL OR SuppCode = '') AND LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower)))
                OR (:code = '' AND (LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower OR CustomerName LIKE :name_like OR CustomerName LIKE :core_like))
            )
              AND Status <> 'Delete'
            ORDER BY TransDate DESC, TransNo DESC
        """
        raw_quotes = [dict(r) for r in db.execute(text(quote_sql), params).mappings().all()]

        # 3. Proforma Invoices
        proforma_sql = """
            SELECT
                TransNo,
                TransDate,
                QuotationNo,
                QuotationDate,
                CustomerCode,
                CustomerName,
                TotalQty,
                TotalAmount,
                NetAmount,
                ApprovalStatus,
                Remarks,
                LTRIM(RTRIM(FinYearVal)) AS FinYearVal
            FROM dbo.Acc_Proforma_Inv_Main
            WHERE (
                (:code <> '' AND (CustomerCode = :code OR (:has_unit = 1 AND (CustomerCode IS NULL OR CustomerCode = '') AND LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower)))
                OR (:code = '' AND (LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower OR CustomerName LIKE :name_like OR CustomerName LIKE :core_like))
            )
              AND Status <> 'Delete'
            ORDER BY TransDate DESC, TransNo DESC
        """
        raw_proformas = [dict(r) for r in db.execute(text(proforma_sql), params).mappings().all()]

        # 4. Sales Invoices
        sales_inv_sql = """
            SELECT
                TransNo,
                InvoiceNo,
                InvoiceDate,
                CustomerCode,
                CustomerName,
                CustomerUnit,
                GST,
                TotalQty,
                ISNULL(TotalItemAmount, 0) AS TotalItemAmount,
                ISNULL(TotalCGSTAmount, 0) AS TotalCGSTAmount,
                ISNULL(TotalSGSTAmount, 0) AS TotalSGSTAmount,
                ISNULL(TotalIGSTAmount, 0) AS TotalIGSTAmount,
                TotalAmount,
                NetAmount,
                Approval_Status AS ApprovalStatus,
                Remarks,
                LTRIM(RTRIM(FinYearVal)) AS FinYearVal
            FROM dbo.Acc_Sales_Inv_Main
            WHERE (
                (:code <> '' AND (CustomerCode = :code OR (:has_unit = 1 AND (CustomerCode IS NULL OR CustomerCode = '') AND LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower AND CustomerUnit = :unit)))
                OR (:code = '' AND (LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower OR CustomerName LIKE :name_like OR CustomerName LIKE :core_like))
            )
              AND Status <> 'Delete'
            ORDER BY InvoiceDate DESC, TransNo DESC
        """
        raw_sales_invoices = [dict(r) for r in db.execute(text(sales_inv_sql), params).mappings().all()]

        # 5. Tally Transactions
        tally_sql = """
            SELECT
                TransNo,
                TransDate,
                LeaderCode,
                LedgerName,
                AccHeadName,
                TransType,
                CreditAmount,
                DebitAmount,
                Narration,
                LTRIM(RTRIM(FinYearVal)) AS FinYearVal
            FROM dbo.Acc_Trans_All
            WHERE (
                (:code <> '' AND LeaderCode = :code)
                OR (:code = '' AND (LOWER(LTRIM(RTRIM(LedgerName))) = :name_lower OR LedgerName LIKE :name_like OR LedgerName LIKE :core_like))
            )
              AND ISNULL(Status, '') <> 'Delete'
              AND ISNULL(TransType, '') <> 'Opening Balance'
            ORDER BY TransDate DESC, TransNo DESC
        """
        raw_tally_vouchers = [dict(r) for r in db.execute(text(tally_sql), params).mappings().all()]

        # Standardize ApprovalStatus across all items
        for q in raw_quotes:
            q["ApprovalStatus"] = cls._normalize_approval_status(q.get("ApprovalStatus"), default="Pending")
        for p in raw_proformas:
            p["ApprovalStatus"] = cls._normalize_approval_status(p.get("ApprovalStatus"), default="Pending")
        for s in raw_sales_invoices:
            s["ApprovalStatus"] = cls._normalize_approval_status(s.get("ApprovalStatus"), default="Approved")

        # Partition records by date:
        # Transactions prior to calc_from_date roll into Opening Balance
        prior_debits = 0.0
        prior_credits = 0.0

        quotes = []
        for q in raw_quotes:
            nd = cls._normalize_date(q.get("TransDate"))
            if calc_from_date and nd and nd < calc_from_date:
                continue
            if calc_to_date and nd and nd > calc_to_date:
                continue
            quotes.append(q)

        proformas = []
        for p in raw_proformas:
            nd = cls._normalize_date(p.get("TransDate"))
            if calc_from_date and nd and nd < calc_from_date:
                continue
            if calc_to_date and nd and nd > calc_to_date:
                continue
            proformas.append(p)

        sales_invoices = []
        for s in raw_sales_invoices:
            nd = cls._normalize_date(s.get("InvoiceDate") or s.get("TransDate"))
            amt = cls._to_float(s.get("NetAmount"))
            if calc_from_date and nd and nd < calc_from_date:
                prior_debits += amt
                continue
            if calc_to_date and nd and nd > calc_to_date:
                continue
            sales_invoices.append(s)

        tally_vouchers = []
        for t in raw_tally_vouchers:
            nd = cls._normalize_date(t.get("TransDate"))
            cr = cls._to_float(t.get("CreditAmount"))
            dr = cls._to_float(t.get("DebitAmount"))
            trans_no = str(t.get("TransNo") or "").strip()
            trans_type = str(t.get("TransType") or "").strip()
            is_erp = trans_no.startswith("R-BK/") or trans_no.startswith("R-CS/") or trans_no.startswith("R-")
            is_receipt = is_erp or (trans_type.lower() in ("receipt", "cash receipts", "bank receipt", "coral receipt entry")) or cr > 0

            if calc_from_date and nd and nd < calc_from_date:
                if is_receipt or cr > 0:
                    prior_credits += cr
                elif dr > 0:
                    prior_debits += dr
                continue
            if calc_to_date and nd and nd > calc_to_date:
                continue
            tally_vouchers.append(t)

        # Ensure customer GSTNo and PanNo are populated from loaded sales invoices if still missing
        if not (customer.get("GSTNo") or "").strip() or str(customer.get("GSTNo")).strip().lower() in ("none", "null", "-", "n/a", "na"):
            for s in raw_sales_invoices:
                si_gst = (s.get("GST") or "").strip()
                if si_gst and si_gst.lower() not in ("none", "null", "-", "n/a", "na"):
                    customer["GSTNo"] = si_gst
                    if (not customer.get("PanNo") or str(customer.get("PanNo")).strip().lower() in ("none", "null", "-", "n/a", "na")) and len(si_gst) >= 12:
                        cand_pan = si_gst.upper()[2:12]
                        if len(cand_pan) == 10 and cand_pan[:5].isalpha():
                            customer["PanNo"] = cand_pan
                    break

        # 6. Compute Milestone Breakdown (% Advance & Reconciliation)
        milestones = []
        all_receipt_vouchers = [
            v for v in tally_vouchers
            if v.get("TransType", "").strip().lower() in ("receipt", "cash receipts", "bank receipt", "coral receipt entry")
               or cls._to_float(v.get("CreditAmount")) > 0
        ]
        # Complete lifetime receipts for accurate invoice payment settlement reconciliation
        all_lifetime_receipts = [
            v for v in raw_tally_vouchers
            if v.get("TransType", "").strip().lower() in ("receipt", "cash receipts", "bank receipt", "coral receipt entry")
               or cls._to_float(v.get("CreditAmount")) > 0
        ]

        for pf in proformas:
            pf_no = str(pf.get("TransNo") or "").strip()
            quote_no = str(pf.get("QuotationNo") or "").strip()
            pf_amount = cls._to_float(pf.get("NetAmount"))

            # Link with Sales Invoice
            matched_sales_inv = next(
                (si for si in sales_invoices if str(si.get("InvoiceNo") or "").strip() == pf_no or pf_no in str(si.get("Remarks") or "")),
                None
            )

            # Match Tally Receipts that reference PI or Quote
            matched_receipts = [
                v for v in all_receipt_vouchers
                if (pf_no and pf_no.lower() in str(v.get("Narration") or "").lower())
                or (quote_no and quote_no.lower() in str(v.get("Narration") or "").lower())
            ]
            adv_collected = sum(cls._to_float(v.get("CreditAmount")) for v in matched_receipts)

            # Try to extract target advance % from related quotation terms
            rel_quote = next((q for q in quotes if str(q.get("TransNo") or "").strip() == quote_no), None)
            target_pct = 30.0  # default milestone percentage
            if rel_quote:
                terms_text = str(rel_quote.get("terms_conditions") or "")
                pct_match = re.search(r"(\d{1,3})\s*%", terms_text)
                if pct_match:
                    try:
                        val = float(pct_match.group(1))
                        if 0 < val <= 100:
                            target_pct = val
                    except Exception:
                        pass

            collected_pct = round((adv_collected / pf_amount) * 100.0, 2) if pf_amount > 0 else 0.0
            is_fully_paid = (collected_pct >= 100.0) or (pf_amount > 0 and adv_collected >= pf_amount)

            if matched_sales_inv:
                if is_fully_paid:
                    status_label = "Invoiced & Completed"
                elif adv_collected > 0:
                    status_label = f"Invoiced - Partial Advance ({collected_pct:.0f}%)"
                else:
                    status_label = "Invoiced - Payment Pending"
            elif is_fully_paid:
                status_label = "Advance Fully Paid"
            elif adv_collected > 0:
                status_label = f"Partial Advance ({collected_pct:.0f}%)"
            else:
                status_label = "Advance Pending"

            milestones.append({
                "proforma_no": pf_no,
                "proforma_date": pf.get("TransDate"),
                "quotation_no": quote_no,
                "total_order_value": pf_amount,
                "target_advance_pct": 100.0,
                "target_advance_amount": pf_amount,
                "advance_collected": adv_collected,
                "advance_percentage_achieved": collected_pct,
                "sales_invoice_no": matched_sales_inv.get("TransNo") if matched_sales_inv else None,
                "sales_invoice_date": matched_sales_inv.get("InvoiceDate") if matched_sales_inv else None,
                "sales_invoice_amount": cls._to_float(matched_sales_inv.get("NetAmount")) if matched_sales_inv else None,
                "balance_pending": max(0.0, pf_amount - adv_collected),
                "status": status_label,
                "fin_year": (pf.get("FinYearVal") or "").strip().replace("_", "-"),
            })

        # 7. Unified Chronological Timeline
        timeline = []
        for q in quotes:
            timeline.append({
                "doc_type": "Quotation",
                "doc_no": q.get("TransNo"),
                "doc_date": q.get("TransDate"),
                "fin_year": (q.get("FinYearVal") or "").strip().replace("_", "-"),
                "amount": cls._to_float(q.get("NetAmount")),
                "status": q.get("ApprovalStatus") or "Approved",
                "reference": q.get("Product") or "",
                "remarks": q.get("Remarks") or "",
                "terms": q.get("terms_conditions") or "",
            })
        for p in proformas:
            timeline.append({
                "doc_type": "Proforma Invoice",
                "doc_no": p.get("TransNo"),
                "doc_date": p.get("TransDate"),
                "fin_year": (p.get("FinYearVal") or "").strip().replace("_", "-"),
                "amount": cls._to_float(p.get("NetAmount")),
                "status": p.get("ApprovalStatus") or "Approved",
                "reference": f"Quote: {p.get('QuotationNo') or '-'}",
                "remarks": p.get("Remarks") or "",
                "terms": "",
            })
        for s in sales_invoices:
            timeline.append({
                "doc_type": "Sales Invoice",
                "doc_no": s.get("TransNo"),
                "doc_date": s.get("InvoiceDate"),
                "fin_year": (s.get("FinYearVal") or "").strip().replace("_", "-"),
                "amount": cls._to_float(s.get("NetAmount")),
                "status": s.get("ApprovalStatus") or "Approved",
                "reference": f"Ref: {s.get('InvoiceNo') or '-'}",
                "remarks": s.get("Remarks") or "",
                "terms": "",
            })
        for t in tally_vouchers:
            trans_no = str(t.get("TransNo") or "").strip()
            trans_type = str(t.get("TransType") or "").strip()
            is_erp_receipt = trans_no.startswith("R-BK/") or trans_no.startswith("R-CS/") or trans_no.startswith("R-")
            is_receipt = trans_type.lower() in ("receipt", "cash receipts", "bank receipt", "coral receipt entry") or cls._to_float(t.get("CreditAmount")) > 0

            if is_erp_receipt:
                doc_type = "Customer Receipt"
                status_label = "ERP Verified / Cleared"
            elif is_receipt:
                doc_type = "Payment Receipt"
                status_label = "Bank Cleared"
            elif trans_type.lower() in ("payment", "cash payments", "bank payment"):
                doc_type = "Payment / Refund"
                status_label = "Cleared"
            else:
                doc_type = f"{trans_type} Voucher" if trans_type else "Journal Voucher"
                status_label = "Recorded"

            timeline.append({
                "doc_type": doc_type,
                "doc_no": trans_no,
                "doc_date": t.get("TransDate"),
                "fin_year": (t.get("FinYearVal") or "").strip().replace("_", "-"),
                "debit": cls._to_float(t.get("DebitAmount")),
                "credit": cls._to_float(t.get("CreditAmount")),
                "amount": cls._to_float(t.get("CreditAmount")) if cls._to_float(t.get("CreditAmount")) > 0 else cls._to_float(t.get("DebitAmount")),
                "status": status_label,
                "reference": t.get("AccHeadName") or "",
                "remarks": t.get("Narration") or "",
                "terms": "",
            })

        # 8. Statement of Account / Running Ledger
        running_ledger = []
        op_bal = cls._to_float(customer.get("OpeningBalance"))
        op_type = str(customer.get("BalanceType") or "Dr").strip()
        master_balance = op_bal if op_type.lower() == "dr" else -op_bal

        current_balance = master_balance + (prior_debits - prior_credits)
        op_particulars = "Opening Balance"
        if calc_from_date:
            if calc_from_date.endswith("-04-01") and is_all == 0:
                op_particulars = f"Opening Balance (B/F for FY {fy_dash})"
            else:
                op_particulars = f"Opening Balance (B/F as of {calc_from_date})"
        elif is_all == 0 and (prior_debits > 0 or prior_credits > 0):
            op_particulars = f"Opening Balance (B/F for FY {fy_dash})"

        running_ledger.append({
            "entry_date": "Opening",
            "particulars": op_particulars,
            "voucher_type": "Opening",
            "voucher_no": "-",
            "taxable_amt": 0.0,
            "cgst_amt": 0.0,
            "sgst_amt": 0.0,
            "igst_amt": 0.0,
            "total_gst": 0.0,
            "debit": current_balance if current_balance >= 0 else 0.0,
            "tds_amt": 0.0,
            "net_received": 0.0,
            "credit": abs(current_balance) if current_balance < 0 else 0.0,
            "running_balance": round(current_balance, 2),
        })

        # Fetch Customer_Receipt_Main records for explicit TDS and Net Received tracking
        receipt_tds_map = {}
        try:
            r_has_table = db.execute(text("SELECT OBJECT_ID('dbo.Customer_Receipt_Main', 'U')")).scalar()
            if r_has_table:
                r_sql = """
                    SELECT ReceiptNo, PaidAmount, TotTDSAmt, TDSPercentage, TDSSection, NetAmount, BankName, PaymentMode
                    FROM dbo.Customer_Receipt_Main
                    WHERE ((:code <> '' AND CustomerCode = :code) OR LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower OR CustomerName LIKE :name_like OR CustomerName LIKE :core_like)
                      AND ISNULL(Status, '') <> 'Delete'
                """
                r_rows = db.execute(text(r_sql), params).mappings().all()
                for r in r_rows:
                    receipt_tds_map[str(r["ReceiptNo"]).strip()] = dict(r)
        except Exception:
            pass

        # Combine Sales Invoices (Debits) and Customer Receipts (Credits)
        ledger_raw = []
        for s in sales_invoices:
            taxable = cls._to_float(s.get("TotalItemAmount"))
            cgst = cls._to_float(s.get("TotalCGSTAmount"))
            sgst = cls._to_float(s.get("TotalSGSTAmount"))
            igst = cls._to_float(s.get("TotalIGSTAmount"))
            tot_gst = cgst + sgst + igst
            net_amt = cls._to_float(s.get("NetAmount"))
            if taxable == 0.0 and tot_gst == 0.0:
                taxable = net_amt

            inv_no = str(s.get("InvoiceNo") or s.get("TransNo") or "")
            desc = f"Sales Invoice - {inv_no}"
            if s.get("Remarks"):
                desc += f" ({s.get('Remarks')})"

            ledger_raw.append({
                "date": str(s.get("InvoiceDate") or s.get("TransDate") or ""),
                "particulars": desc,
                "voucher_type": "Sales Invoice",
                "voucher_no": inv_no,
                "taxable_amt": taxable,
                "cgst_amt": cgst,
                "sgst_amt": sgst,
                "igst_amt": igst,
                "total_gst": tot_gst,
                "debit": net_amt,
                "tds_amt": 0.0,
                "net_received": 0.0,
                "credit": 0.0,
            })

        for t in tally_vouchers:
            cr = cls._to_float(t.get("CreditAmount"))
            dr = cls._to_float(t.get("DebitAmount"))
            trans_no = str(t.get("TransNo") or "").strip()
            trans_type = str(t.get("TransType") or "").strip()
            narration = str(t.get("Narration") or "").strip()
            is_erp = trans_no.startswith("R-BK/") or trans_no.startswith("R-CS/") or trans_no.startswith("R-")
            is_receipt = is_erp or (trans_type.lower() in ("receipt", "cash receipts", "bank receipt", "coral receipt entry")) or cr > 0

            # ONLY include Sales Invoice and Payment / Customer Receipts in the ledger statement!
            if not is_receipt and dr > 0 and cr == 0:
                continue

            tds_amt = 0.0
            paid_cash = cr
            if trans_no in receipt_tds_map:
                tds_amt = cls._to_float(receipt_tds_map[trans_no].get("TotTDSAmt"))
                paid_cash = cls._to_float(receipt_tds_map[trans_no].get("PaidAmount"))
                if paid_cash == 0 and cr > 0:
                    paid_cash = max(0.0, cr - tds_amt)
            else:
                tds_match = re.search(r"TDS Deducted:\s*(?:Rs\.\s*)?([0-9,]+(?:\.[0-9]+)?)", narration, re.IGNORECASE)
                if tds_match:
                    try:
                        tds_amt = float(tds_match.group(1).replace(",", ""))
                        paid_cash = max(0.0, cr - tds_amt)
                    except Exception:
                        pass

            if is_erp:
                desc = f"Customer Receipt - {trans_no}"
                v_type = "Customer Receipt"
            elif is_receipt:
                desc = f"Payment Receipt - {trans_no}"
                v_type = "Payment Receipt"
            else:
                desc = f"{trans_type} - {trans_no}"
                v_type = trans_type or "Receipt"

            if narration and "TDS Deducted" not in desc:
                desc += f" ({narration})"

            ledger_raw.append({
                "date": str(t.get("TransDate") or ""),
                "particulars": desc,
                "voucher_type": v_type,
                "voucher_no": trans_no,
                "taxable_amt": 0.0,
                "cgst_amt": 0.0,
                "sgst_amt": 0.0,
                "igst_amt": 0.0,
                "total_gst": 0.0,
                "debit": dr,
                "tds_amt": tds_amt,
                "net_received": paid_cash if cr > 0 else 0.0,
                "credit": cr,
            })

        # Sort ledger rows chronologically using normalized ISO date
        def parse_date_sort(d_str: str):
            if not d_str or str(d_str).strip().lower() in ("opening", "0", ""):
                return "0000-00-00"
            norm = cls._normalize_date(d_str)
            return norm or str(d_str)

        ledger_raw.sort(key=lambda x: parse_date_sort(x["date"]))

        for item in ledger_raw:
            dr = item["debit"]
            cr = item["credit"]
            current_balance += (dr - cr)
            running_ledger.append({
                "entry_date": item["date"],
                "particulars": item["particulars"],
                "voucher_type": item["voucher_type"],
                "voucher_no": item["voucher_no"],
                "taxable_amt": item["taxable_amt"],
                "cgst_amt": item["cgst_amt"],
                "sgst_amt": item["sgst_amt"],
                "igst_amt": item["igst_amt"],
                "total_gst": item["total_gst"],
                "debit": dr,
                "tds_amt": item["tds_amt"],
                "net_received": item["net_received"],
                "credit": cr,
                "running_balance": round(current_balance, 2),
            })

        # 9. Calculate Precise Invoice Paid vs Pending Tracking (Explicit + FIFO)
        # Uses lifetime customer receipts so an invoice settled at any point is properly recognized as PAID
        invoices_breakdown, invoices_summary = cls.calculate_invoices_payment_status(
            sales_invoices=sales_invoices,
            receipt_vouchers=all_lifetime_receipts,
        )

        # 10. Key Performance Indicators
        tot_quoted = sum(cls._to_float(q.get("NetAmount")) for q in quotes)
        tot_pi = sum(cls._to_float(p.get("NetAmount")) for p in proformas)
        tot_invoiced = sum(cls._to_float(s.get("NetAmount")) for s in sales_invoices)
        tot_tally_receipts = sum(cls._to_float(v.get("CreditAmount")) for v in all_receipt_vouchers)
        tot_tally_payments = sum(cls._to_float(v.get("DebitAmount")) for v in tally_vouchers if v.get("TransType", "").lower() in ("payment", "cash payments", "bank payment"))
        net_outstanding = round(tot_invoiced - tot_tally_receipts, 2)

        return {
            "success": True,
            "customer_info": customer,
            "selected_fin_year": fy_dash if is_all == 0 else "ALL",
            "period_display": period_display,
            "period_range": period_range,
            "from_date": calc_from_date,
            "to_date": calc_to_date,
            "from_month": from_month or (calc_from_date[:7] if calc_from_date else None),
            "to_month": to_month or (calc_to_date[:7] if calc_to_date else None),
            "kpis": {
                "total_quotations_count": len(quotes),
                "total_quoted_amount": round(tot_quoted, 2),
                "total_proforma_count": len(proformas),
                "total_proforma_amount": round(tot_pi, 2),
                "total_sales_invoices_count": len(sales_invoices),
                "total_invoiced_amount": round(tot_invoiced, 2),
                "total_collections": round(tot_tally_receipts, 2),
                "total_receipts_amount": round(tot_tally_receipts, 2),
                "total_tally_receipts_amount": round(tot_tally_receipts, 2),
                "total_tally_payments_amount": round(tot_tally_payments, 2),
                "net_outstanding": net_outstanding,
                "net_outstanding_balance": net_outstanding,
                "closing_balance": round(current_balance, 2),
                "paid_invoices_count": invoices_summary["paid_count"],
                "partial_invoices_count": invoices_summary["partial_count"],
                "pending_invoices_count": invoices_summary["pending_count"],
                "overdue_invoices_count": invoices_summary["overdue_count"],
                "total_balance_due": invoices_summary["total_balance_due"],
                "total_amount_collected": invoices_summary["total_paid"],
            },
            "invoices_breakdown": invoices_breakdown,
            "invoices_summary": invoices_summary,
            "milestones": milestones,
            "quotations": quotes,
            "proformas": proformas,
            "sales_invoices": sales_invoices,
            "receipt_vouchers": all_receipt_vouchers,
            "tally_vouchers": tally_vouchers,
            "timeline": timeline,
            "running_ledger": running_ledger,
        }

    @classmethod
    def calculate_invoices_payment_status(
        cls,
        sales_invoices: List[Dict[str, Any]],
        receipt_vouchers: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Computes the exact payment status (PAID, PARTIAL, PENDING) for each sales invoice.
        Uses explicit reference matching first, followed by FIFO allocation of remaining receipts.
        """
        today = date.today()

        def get_inv_date(inv):
            d = inv.get("InvoiceDate") or inv.get("TransDate") or ""
            return str(d)[:10]

        # Initialize tracking directly on items
        for s in sales_invoices:
            net_amt = cls._to_float(s.get("FinalNetAmount") if s.get("FinalNetAmount") is not None else s.get("NetAmount"))
            s["net_amount_float"] = net_amt
            s["amount_paid"] = 0.0
            s["balance_due"] = net_amt
            s["payment_status"] = "PENDING"
            s["payment_status_label"] = "Pending"
            s["matched_receipts"] = []
            s["fin_year"] = (s.get("FinYearVal") or "").strip().replace("_", "-")

        inv_list = list(sales_invoices)
        # Sort ascending by date for FIFO allocation
        inv_list.sort(key=get_inv_date)

        # Available receipts with tracking
        receipts = []
        for r in receipt_vouchers:
            cr_amt = cls._to_float(r.get("CreditAmount"))
            if cr_amt > 0:
                receipts.append({
                    "voucher_no": str(r.get("TransNo") or "").strip(),
                    "date": str(r.get("TransDate") or "").strip(),
                    "narration": str(r.get("Narration") or "").strip(),
                    "total_amount": cr_amt,
                    "remaining_amount": cr_amt,
                })

        # 1. First Pass: Explicit reference matching (Narration contains InvoiceNo or TransNo)
        for inv in inv_list:
            inv_no = str(inv.get("InvoiceNo") or "").strip().lower()
            trans_no = str(inv.get("TransNo") or "").strip().lower()

            for r in receipts:
                if r["remaining_amount"] <= 0:
                    continue
                narr_lower = r["narration"].lower()
                has_match = (inv_no and len(inv_no) >= 3 and inv_no in narr_lower) or \
                            (trans_no and len(trans_no) >= 3 and trans_no in narr_lower)

                if has_match:
                    alloc = min(inv["balance_due"], r["remaining_amount"])
                    if alloc > 0:
                        inv["amount_paid"] = round(inv["amount_paid"] + alloc, 2)
                        inv["balance_due"] = round(max(0.0, inv["net_amount_float"] - inv["amount_paid"]), 2)
                        r["remaining_amount"] = round(r["remaining_amount"] - alloc, 2)
                        inv["matched_receipts"].append({
                            "voucher_no": r["voucher_no"],
                            "voucher_date": r["date"],
                            "allocated_amount": alloc,
                            "type": "Explicit Reference",
                        })

        # 2. Second Pass: FIFO allocation of remaining receipts against unpaid invoices
        for r in receipts:
            if r["remaining_amount"] <= 0:
                continue

            for inv in inv_list:
                if inv["balance_due"] <= 0:
                    continue

                alloc = min(inv["balance_due"], r["remaining_amount"])
                if alloc > 0:
                    inv["amount_paid"] = round(inv["amount_paid"] + alloc, 2)
                    inv["balance_due"] = round(max(0.0, inv["net_amount_float"] - inv["amount_paid"]), 2)
                    r["remaining_amount"] = round(r["remaining_amount"] - alloc, 2)
                    inv["matched_receipts"].append({
                        "voucher_no": r["voucher_no"],
                        "voucher_date": r["date"],
                        "allocated_amount": alloc,
                        "type": "FIFO Allocation",
                    })

                if r["remaining_amount"] <= 0:
                    break

        # 3. Finalize Status and Overdue Days
        paid_count = 0
        partial_count = 0
        pending_count = 0
        overdue_count = 0
        total_invoiced = 0.0
        total_paid = 0.0
        total_balance = 0.0

        for inv in inv_list:
            net = inv["net_amount_float"]
            paid = inv["amount_paid"]
            bal = inv["balance_due"]

            total_invoiced += net
            total_paid += paid
            total_balance += bal

            # Status determination - Payment status based on balance and collections
            app_status = str(inv.get("ApprovalStatus") or inv.get("Approval_Status") or "").strip().lower()
            is_approved = app_status in ("approved", "1")

            if bal <= 0.01 and (paid > 0.01 or net == 0):
                inv["payment_status"] = "PAID"
                inv["payment_status_label"] = "Paid"
                paid_count += 1
            elif paid > 0.01 and bal > 0.01:
                inv["payment_status"] = "PARTIAL"
                inv["payment_status_label"] = "Partially Paid"
                partial_count += 1
            elif not is_approved:
                inv["payment_status"] = "PENDING_APPROVAL"
                inv["payment_status_label"] = "Pending Approval"
                pending_count += 1
            else:
                inv["payment_status"] = "PENDING"
                inv["payment_status_label"] = "Unpaid / Pending"
                pending_count += 1

            # Calculate overdue days safely supporting DD/MM/YYYY and YYYY-MM-DD
            inv_date_str = str(inv.get("InvoiceDate") or inv.get("TransDate") or "").strip()[:10]
            days_overdue = 0
            if bal > 0.01 and inv_date_str:
                inv_dt = None
                for date_fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
                    try:
                        inv_dt = datetime.strptime(inv_date_str, date_fmt).date()
                        break
                    except ValueError:
                        pass
                if inv_dt:
                    age = (today - inv_dt).days
                    if age > 30:
                        days_overdue = age - 30
                        overdue_count += 1

            inv["days_overdue"] = days_overdue
            inv["is_overdue"] = days_overdue > 0

        # Sort back descending by date for UI presentation
        inv_list.sort(key=get_inv_date, reverse=True)

        summary = {
            "total_invoiced": round(total_invoiced, 2),
            "total_paid": round(total_paid, 2),
            "total_balance_due": round(total_balance, 2),
            "total_invoices_count": len(inv_list),
            "paid_count": paid_count,
            "partial_count": partial_count,
            "pending_count": pending_count,
            "overdue_count": overdue_count,
            "unallocated_receipts_amount": round(sum(r["remaining_amount"] for r in receipts), 2),
        }

        return inv_list, summary

    @classmethod
    def get_portfolio_summary(cls, db: Session, fin_year: str = "ALL") -> Dict[str, Any]:
        """
        Industry & Portfolio-level Client Analytics for Customer 360 Dashboard.
        Computes total client count, total billed, collections, TDS, and top debtors.
        """
        fy = (fin_year or "ALL").strip()
        is_all = 1 if fy.upper() in ("ALL", "", "NONE") else 0
        fy_dash = fy.replace("_", "-")
        fy_under = fy.replace("-", "_")
        params = {
            "is_all": is_all,
            "fy_dash": fy_dash,
            "fy_under": fy_under,
        }

        # 1. Total Customer Count
        count_sql = """
            SELECT COUNT(*) AS ClientCount
            FROM dbo.Acc_Mst_Ledger
            WHERE LedgerType = 'Customer' AND Status <> 'Delete'
        """
        try:
            client_count = db.execute(text(count_sql)).scalar() or 0
        except Exception:
            client_count = 0

        if client_count == 0:
            try:
                client_count = db.execute(text("SELECT COUNT(DISTINCT CustomerName) FROM dbo.Acc_Sales_Inv_Main WHERE Status <> 'Delete'")).scalar() or 0
            except Exception:
                client_count = 0

        # 2. Total Invoiced & Taxes
        inv_sql = """
            SELECT 
                ISNULL(COUNT(*), 0) AS TotalInvoices,
                ISNULL(SUM(TotalItemAmount), 0) AS TotalTaxable,
                ISNULL(SUM(TotalCGSTAmount), 0) AS TotalCGST,
                ISNULL(SUM(TotalSGSTAmount), 0) AS TotalSGST,
                ISNULL(SUM(TotalIGSTAmount), 0) AS TotalIGST,
                ISNULL(SUM(NetAmount), 0) AS TotalBilled
            FROM dbo.Acc_Sales_Inv_Main
            WHERE Status <> 'Delete'
              AND (
                  :is_all = 1
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') = :fy_dash
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '-', '_') = :fy_under
              )
        """
        inv_row = db.execute(text(inv_sql), params).mappings().first() or {}
        tot_billed = cls._to_float(inv_row.get("TotalBilled"))
        tot_taxable = cls._to_float(inv_row.get("TotalTaxable"))
        tot_cgst = cls._to_float(inv_row.get("TotalCGST"))
        tot_sgst = cls._to_float(inv_row.get("TotalSGST"))
        tot_igst = cls._to_float(inv_row.get("TotalIGST"))
        tot_gst = tot_cgst + tot_sgst + tot_igst
        if tot_taxable == 0 and tot_billed > 0 and tot_gst == 0:
            tot_taxable = tot_billed

        # 3. Total Collections from Customer Accounts
        rec_sql = """
            SELECT ISNULL(SUM(CreditAmount), 0) AS TotalCollected
            FROM dbo.Acc_Trans_All
            WHERE ISNULL(Status, '') <> 'Delete'
              AND ISNULL(TransType, '') <> 'Opening Balance'
              AND (
                  LOWER(LTRIM(RTRIM(TransType))) IN ('receipt', 'customer receipt', 'cash receipts', 'bank receipt', 'coral receipt entry')
                  OR TransNo LIKE 'R-%' OR TransNo LIKE 'R-BK/%' OR TransNo LIKE 'R-CS/%'
              )
              AND (
                  :is_all = 1
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') = :fy_dash
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '-', '_') = :fy_under
              )
        """
        try:
            rec_row = db.execute(text(rec_sql), params).mappings().first() or {}
            tot_collected = cls._to_float(rec_row.get("TotalCollected"))
        except Exception:
            tot_collected = 0.0

        # 4. Total TDS Deductions
        tds_sql = """
            SELECT ISNULL(SUM(DebitAmount), 0) AS TotalTDS
            FROM dbo.Acc_Trans_All
            WHERE ISNULL(Status, '') <> 'Delete'
              AND (LeaderCode = 'GL/00166' OR LedgerName LIKE '%TDS%')
              AND (
                  :is_all = 1
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') = :fy_dash
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '-', '_') = :fy_under
              )
        """
        try:
            tds_row = db.execute(text(tds_sql), params).mappings().first() or {}
            tot_tds = cls._to_float(tds_row.get("TotalTDS"))
        except Exception:
            tot_tds = 0.0

        # Total Opening Balance of all customer accounts
        op_sql = """
            SELECT 
                ISNULL(SUM(CASE WHEN LOWER(LTRIM(RTRIM(BalanceType))) = 'cr' THEN -ISNULL(OpeningBalance, 0) ELSE ISNULL(OpeningBalance, 0) END), 0) AS TotalOpening
            FROM dbo.Acc_Mst_Ledger
            WHERE LedgerType = 'Customer' AND Status <> 'Delete'
        """
        try:
            tot_opening = cls._to_float(db.execute(text(op_sql)).scalar())
        except Exception:
            tot_opening = 0.0

        total_outstanding = max(0.0, tot_opening + tot_billed - tot_collected)

        # 5. Top 15 Outstanding Clients Breakdown
        top_sql = """
            SELECT TOP 15
                m.LedgerCode,
                m.LedgerName,
                m.City,
                m.State,
                m.GSTNo,
                ISNULL(m.OpeningBalance, 0) AS OpeningBalance,
                ISNULL(m.BalanceType, 'Dr') AS BalanceType,
                ISNULL(s.TotalBilled, 0) AS TotalBilled,
                ISNULL(r.TotalCollected, 0) AS TotalCollected,
                (
                    CASE WHEN LOWER(LTRIM(RTRIM(m.BalanceType))) = 'cr' THEN -ISNULL(m.OpeningBalance, 0) ELSE ISNULL(m.OpeningBalance, 0) END
                    + ISNULL(s.TotalBilled, 0)
                    - ISNULL(r.TotalCollected, 0)
                ) AS NetOutstanding
            FROM dbo.Acc_Mst_Ledger m
            LEFT JOIN (
                SELECT CustomerCode, SUM(NetAmount) AS TotalBilled
                FROM dbo.Acc_Sales_Inv_Main
                WHERE Status <> 'Delete'
                  AND (:is_all = 1 OR REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') = :fy_dash)
                GROUP BY CustomerCode
            ) s ON s.CustomerCode = m.LedgerCode
            LEFT JOIN (
                SELECT LeaderCode, SUM(CreditAmount) AS TotalCollected
                FROM dbo.Acc_Trans_All
                WHERE ISNULL(Status, '') <> 'Delete'
                  AND (
                      LOWER(LTRIM(RTRIM(TransType))) IN ('receipt', 'customer receipt', 'cash receipts', 'bank receipt', 'coral receipt entry')
                      OR TransNo LIKE 'R-%'
                  )
                  AND (:is_all = 1 OR REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') = :fy_dash)
                GROUP BY LeaderCode
            ) r ON r.LeaderCode = m.LedgerCode
            WHERE m.LedgerType = 'Customer'
              AND m.Status <> 'Delete'
            ORDER BY NetOutstanding DESC
        """
        try:
            top_rows = db.execute(text(top_sql), params).mappings().all()
            top_clients = [
                {
                    "client_code": r["LedgerCode"],
                    "client_name": r["LedgerName"],
                    "city": r["City"] or "",
                    "state": r["State"] or "",
                    "gst_no": r["GSTNo"] or "",
                    "opening_balance": cls._to_float(r["OpeningBalance"]),
                    "balance_type": r["BalanceType"] or "Dr",
                    "total_billed": round(cls._to_float(r["TotalBilled"]), 2),
                    "total_invoiced": round(cls._to_float(r["TotalBilled"]), 2),
                    "total_collected": round(cls._to_float(r["TotalCollected"]), 2),
                    "total_collections": round(cls._to_float(r["TotalCollected"]), 2),
                    "total_tds": 0.0,
                    "net_outstanding": round(cls._to_float(r["NetOutstanding"]), 2),
                    "outstanding_balance": round(cls._to_float(r["NetOutstanding"]), 2),
                }
                for r in top_rows
            ]
        except Exception:
            top_clients = []

        return {
            "fin_year": fy,
            "total_clients": client_count,
            "total_clients_count": client_count,
            "total_invoices_count": int(inv_row.get("TotalInvoices") or 0),
            "total_taxable": round(tot_taxable, 2),
            "total_portfolio_taxable": round(tot_taxable, 2),
            "total_cgst": round(tot_cgst, 2),
            "total_sgst": round(tot_sgst, 2),
            "total_igst": round(tot_igst, 2),
            "total_gst": round(tot_gst, 2),
            "total_portfolio_gst": round(tot_gst, 2),
            "total_billed": round(tot_billed, 2),
            "total_portfolio_invoiced": round(tot_billed, 2),
            "total_collected": round(tot_collected, 2),
            "total_portfolio_collections": round(tot_collected, 2),
            "total_tds": round(tot_tds, 2),
            "total_portfolio_tds": round(tot_tds, 2),
            "total_opening": round(tot_opening, 2),
            "total_outstanding": round(total_outstanding, 2),
            "total_portfolio_outstanding": round(total_outstanding, 2),
            "top_clients": top_clients,
            "top_outstanding_clients": top_clients,
        }
