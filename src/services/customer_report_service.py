from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date
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
                    OR GSTNo LIKE :term
                    OR City LIKE :term
                    OR MobileNo LIKE :term
                )
            """
            params["term"] = f"%{term}%"

        sql += " ORDER BY LedgerName ASC"

        rows = db.execute(text(sql), params).mappings().all()
        return [dict(r) for r in rows]

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
                ChequePrintName,
                AccountType AS AccLedgerHeaderName,
                LedgerGrpName,
                LedgerType,
                GSTNo,
                PanNo,
                City,
                State,
                MobileNo,
                MailID,
                ISNULL(OpeningBalance, 0) AS OpeningBalance,
                ISNULL(NULLIF(LTRIM(RTRIM(BalanceType)), ''), 'Dr') AS BalanceType
            FROM dbo.Acc_Mst_Ledger
            WHERE (LedgerCode = :code OR LedgerName = :code)
              AND Status <> 'Delete'
        """
        ledger_row = db.execute(text(ledger_sql), {"code": code}).mappings().first()
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
                    '' AS GSTNo,
                    '' AS PanNo,
                    '' AS City,
                    '' AS State,
                    '' AS MobileNo,
                    '' AS MailID,
                    ISNULL(OpeningBalance, 0) AS OpeningBalance,
                    ISNULL(NULLIF(LTRIM(RTRIM(BalanceType)), ''), 'Dr') AS BalanceType
                FROM dbo.Acc_Mst_GeneralLedger
                WHERE (AccGenLdgCode = :code OR AccGenLdgName = :code)
                  AND Status <> 'Delete'
            """
            ledger_row = db.execute(text(gen_sql), {"code": code}).mappings().first()

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
                    GST AS GSTNo,
                    '' AS PanNo,
                    '' AS City,
                    '' AS State,
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
                        '' AS GSTNo,
                        '' AS PanNo,
                        '' AS City,
                        '' AS State,
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
        c_code = customer["LedgerCode"]
        c_name = customer["LedgerName"]
        c_name_clean = c_name.strip()
        c_name_like = f"%{c_name_clean}%"

        core_name = re.sub(r"(?i)\s*(pvt\.?\s*ltd\.?|private\s*limited|p\.?\s*ltd\.?|limited|ltd\.?)\s*\.*$", "", c_name_clean).strip()
        c_core_like = f"%{core_name}%" if len(core_name) >= 4 else c_name_like

        fy_raw = (fin_year or "ALL").strip()
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
            "name_lower": c_name_clean.lower(),
            "name_like": c_name_like,
            "core_like": c_core_like,
            "is_all": is_all,
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
            WHERE ((:code <> '' AND SuppCode = :code) OR LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower OR CustomerName LIKE :name_like OR CustomerName LIKE :core_like)
              AND Status <> 'Delete'
              AND (
                  :is_all = 1
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') = :fy_dash
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '-', '_') = :fy_under
                  OR LTRIM(RTRIM(FinYearCode)) = :fy_dash
                  OR LTRIM(RTRIM(FinYearCode)) = :fy_under
                  OR (:year_code <> '' AND LTRIM(RTRIM(FinYearCode)) = :year_code)
              )
            ORDER BY TransDate DESC, TransNo DESC
        """
        quotes = [dict(r) for r in db.execute(text(quote_sql), params).mappings().all()]

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
            WHERE ((:code <> '' AND CustomerCode = :code) OR LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower OR CustomerName LIKE :name_like OR CustomerName LIKE :core_like)
              AND Status <> 'Delete'
              AND (
                  :is_all = 1
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') = :fy_dash
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '-', '_') = :fy_under
                  OR LTRIM(RTRIM(FinYearCode)) = :fy_dash
                  OR LTRIM(RTRIM(FinYearCode)) = :fy_under
                  OR (:year_code <> '' AND LTRIM(RTRIM(FinYearCode)) = :year_code)
              )
            ORDER BY TransDate DESC, TransNo DESC
        """
        proformas = [dict(r) for r in db.execute(text(proforma_sql), params).mappings().all()]

        # 4. Sales Invoices
        sales_inv_sql = """
            SELECT
                TransNo,
                InvoiceNo,
                InvoiceDate,
                CustomerCode,
                CustomerName,
                GST,
                TotalQty,
                TotalAmount,
                NetAmount,
                Approval_Status AS ApprovalStatus,
                Remarks,
                LTRIM(RTRIM(FinYearVal)) AS FinYearVal
            FROM dbo.Acc_Sales_Inv_Main
            WHERE ((:code <> '' AND CustomerCode = :code) OR LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower OR CustomerName LIKE :name_like OR CustomerName LIKE :core_like)
              AND Status <> 'Delete'
              AND (
                  :is_all = 1
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') = :fy_dash
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '-', '_') = :fy_under
                  OR LTRIM(RTRIM(FinYearCode)) = :fy_dash
                  OR LTRIM(RTRIM(FinYearCode)) = :fy_under
                  OR (:year_code <> '' AND LTRIM(RTRIM(FinYearCode)) = :year_code)
              )
            ORDER BY InvoiceDate DESC, TransNo DESC
        """
        sales_invoices = [dict(r) for r in db.execute(text(sales_inv_sql), params).mappings().all()]

        # Standardize ApprovalStatus (never show raw 0 or 1)
        for q in quotes:
            q["ApprovalStatus"] = cls._normalize_approval_status(q.get("ApprovalStatus"), default="Pending")
        for p in proformas:
            p["ApprovalStatus"] = cls._normalize_approval_status(p.get("ApprovalStatus"), default="Pending")
        for s in sales_invoices:
            s["ApprovalStatus"] = cls._normalize_approval_status(s.get("ApprovalStatus"), default="Approved")

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
            WHERE ((:code <> '' AND LeaderCode = :code) OR LOWER(LTRIM(RTRIM(LedgerName))) = :name_lower OR LedgerName LIKE :name_like OR LedgerName LIKE :core_like)
              AND ISNULL(Status, '') <> 'Delete'
              AND ISNULL(TransType, '') <> 'Opening Balance'
              AND (
                  :is_all = 1
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') = :fy_dash
                  OR REPLACE(LTRIM(RTRIM(FinYearVal)), '-', '_') = :fy_under
                  OR LTRIM(RTRIM(FinYearCode)) = :fy_dash
                  OR LTRIM(RTRIM(FinYearCode)) = :fy_under
                  OR (:year_code <> '' AND LTRIM(RTRIM(FinYearCode)) = :year_code)
              )
            ORDER BY TransDate DESC, TransNo DESC
        """
        tally_vouchers = [dict(r) for r in db.execute(text(tally_sql), params).mappings().all()]

        # 6. Compute Milestone Breakdown (% Advance & Reconciliation)
        milestones = []
        all_receipt_vouchers = [
            v for v in tally_vouchers
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

        prior_debits = 0.0
        prior_credits = 0.0
        parts = fy_dash.split("-")
        if is_all == 0 and len(parts) == 2 and len(parts[0]) == 4:
            prior_tally_sql = """
                SELECT 
                    ISNULL(SUM(DebitAmount), 0) AS PriorDebit,
                    ISNULL(SUM(CreditAmount), 0) AS PriorCredit
                FROM dbo.Acc_Trans_All
                WHERE ((:code <> '' AND LeaderCode = :code) OR LOWER(LTRIM(RTRIM(LedgerName))) = :name_lower OR LedgerName LIKE :name_like OR LedgerName LIKE :core_like)
                  AND ISNULL(Status, '') <> 'Delete'
                  AND ISNULL(TransType, '') <> 'Opening Balance'
                  AND (
                      (REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') < :fy_dash AND LTRIM(RTRIM(FinYearVal)) <> '')
                      OR (:year_code <> '' AND ISNUMERIC(FinYearCode) = 1 AND CAST(FinYearCode AS INT) < CAST(:year_code AS INT))
                  )
            """
            prior_tally = db.execute(text(prior_tally_sql), params).mappings().first()
            if prior_tally:
                prior_debits += cls._to_float(prior_tally.get("PriorDebit"))
                prior_credits += cls._to_float(prior_tally.get("PriorCredit"))

            prior_sales_sql = """
                SELECT ISNULL(SUM(NetAmount), 0) AS PriorSales
                FROM dbo.Acc_Sales_Inv_Main
                WHERE ((:code <> '' AND CustomerCode = :code) OR LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower OR CustomerName LIKE :name_like OR CustomerName LIKE :core_like)
                  AND Status <> 'Delete'
                  AND (
                      (REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') < :fy_dash AND LTRIM(RTRIM(FinYearVal)) <> '')
                      OR (:year_code <> '' AND ISNUMERIC(FinYearCode) = 1 AND CAST(FinYearCode AS INT) < CAST(:year_code AS INT))
                  )
            """
            prior_sales = db.execute(text(prior_sales_sql), params).mappings().first()
            if prior_sales:
                prior_debits += cls._to_float(prior_sales.get("PriorSales"))

        current_balance = master_balance + (prior_debits - prior_credits)
        op_particulars = "Opening Balance"
        if is_all == 0 and (prior_debits > 0 or prior_credits > 0):
            op_particulars = f"Opening Balance (B/F for FY {fy_dash})"

        running_ledger.append({
            "entry_date": "Opening",
            "particulars": op_particulars,
            "voucher_type": "Opening",
            "voucher_no": "-",
            "debit": current_balance if current_balance >= 0 else 0.0,
            "credit": abs(current_balance) if current_balance < 0 else 0.0,
            "running_balance": round(current_balance, 2),
        })

        # Combine Sales Invoices (Debits) and Tally Entries
        ledger_raw = []
        for s in sales_invoices:
            ledger_raw.append({
                "date": str(s.get("InvoiceDate") or ""),
                "particulars": f"Sales Invoice - {s.get('TransNo')}",
                "voucher_type": "Sales Invoice",
                "voucher_no": s.get("TransNo"),
                "debit": cls._to_float(s.get("NetAmount")),
                "credit": 0.0,
            })

        for t in tally_vouchers:
            cr = cls._to_float(t.get("CreditAmount"))
            dr = cls._to_float(t.get("DebitAmount"))
            trans_no = str(t.get("TransNo") or "").strip()
            trans_type = str(t.get("TransType") or "").strip()
            narration = str(t.get("Narration") or "").strip()
            is_erp = trans_no.startswith("R-BK/") or trans_no.startswith("R-CS/") or trans_no.startswith("R-")

            if is_erp:
                desc = f"Customer Receipt - {trans_no}"
                v_type = "Customer Receipt"
            elif trans_type.lower() in ("receipt", "cash receipts", "bank receipt"):
                desc = f"Payment Receipt - {trans_no}"
                v_type = "Payment Receipt"
            elif trans_type.lower() in ("payment", "cash payments", "bank payment"):
                desc = f"Payment - {trans_no}"
                v_type = "Payment"
            else:
                desc = f"{trans_type} - {trans_no}"
                v_type = trans_type or "Journal"

            if narration:
                desc += f" ({narration})"

            ledger_raw.append({
                "date": str(t.get("TransDate") or ""),
                "particulars": desc,
                "voucher_type": v_type,
                "voucher_no": trans_no,
                "debit": dr,
                "credit": cr,
            })

        # Sort ledger rows
        def parse_date_sort(d_str: str):
            if not d_str:
                return "00000000"
            clean = d_str.replace("/", "").replace("-", "")
            if len(clean) == 8 and clean[:4].isdigit():
                return clean
            # If dd/mm/yyyy
            parts = re.split(r"[/.-]", d_str)
            if len(parts) == 3 and len(parts[2]) == 4:
                return f"{parts[2]}{parts[1].zfill(2)}{parts[0].zfill(2)}"
            return clean

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
                "debit": dr,
                "credit": cr,
                "running_balance": round(current_balance, 2),
            })

        # 9. Calculate Precise Invoice Paid vs Pending Tracking (Explicit + FIFO)
        invoices_breakdown, invoices_summary = cls.calculate_invoices_payment_status(
            sales_invoices=sales_invoices,
            receipt_vouchers=all_receipt_vouchers,
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
