from typing import Any, Dict, List, Optional
from decimal import Decimal
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
    def get_client_autocomplete(
        db: Session,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Fast auto-complete search across Ledger Master for Clients/Customers.
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
                0 AS OpeningBalance,
                'Dr' AS BalanceType
            FROM dbo.Acc_Mst_Ledger
            WHERE Status <> 'Delete'
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
        Retrieves all distinct Financial Years across transactions and Tally.
        """
        sql = """
            SELECT DISTINCT LTRIM(RTRIM(FinYearVal)) AS FinYear
            FROM (
                SELECT FinYearVal FROM dbo.Acc_Quotation_Main WHERE FinYearVal IS NOT NULL AND Status <> 'Delete'
                UNION ALL
                SELECT FinYearVal FROM dbo.Acc_Proforma_Inv_Main WHERE FinYearVal IS NOT NULL AND Status <> 'Delete'
                UNION ALL
                SELECT FinYearVal FROM dbo.Acc_Sales_Inv_Main WHERE FinYearVal IS NOT NULL AND Status <> 'Delete'
                UNION ALL
                SELECT FinYearVal FROM dbo.Acc_Trans_All WHERE FinYearVal IS NOT NULL AND ISNULL(Status, '') <> 'Delete'
            ) t
            WHERE LTRIM(RTRIM(FinYearVal)) <> ''
            ORDER BY FinYear DESC
        """
        rows = db.execute(text(sql)).fetchall()
        years = [r[0] for r in rows if r[0]]
        defaults = ["2026-2027", "2025_2026", "2024_2025"]
        for d in defaults:
            if d not in years:
                years.append(d)
        return years

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
                0 AS OpeningBalance,
                'Dr' AS BalanceType
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
                    0 AS OpeningBalance,
                    'Dr' AS BalanceType
                FROM dbo.Acc_Mst_GeneralLedger
                WHERE (AccGenLdgCode = :code OR AccGenLdgName = :code)
                  AND Status <> 'Delete'
            """
            ledger_row = db.execute(text(gen_sql), {"code": code}).mappings().first()

        if not ledger_row:
            raise HTTPException(
                status_code=404,
                detail=f"Customer/Ledger '{client_code}' not found in Ledger Master.",
            )

        customer = dict(ledger_row)
        c_code = customer["LedgerCode"]
        c_name = customer["LedgerName"]
        c_name_clean = c_name.strip()
        c_name_like = f"%{c_name_clean}%"

        params = {
            "code": c_code,
            "name_lower": c_name_clean.lower(),
            "name_like": c_name_like,
            "fin_year": fy,
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
            WHERE (SuppCode = :code OR LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower OR CustomerName LIKE :name_like)
              AND Status <> 'Delete'
              AND (:fin_year = 'ALL' OR LTRIM(RTRIM(FinYearVal)) = :fin_year)
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
            WHERE (CustomerCode = :code OR LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower OR CustomerName LIKE :name_like)
              AND Status <> 'Delete'
              AND (:fin_year = 'ALL' OR LTRIM(RTRIM(FinYearVal)) = :fin_year)
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
            WHERE (CustomerCode = :code OR LOWER(LTRIM(RTRIM(CustomerName))) = :name_lower OR CustomerName LIKE :name_like)
              AND Status <> 'Delete'
              AND (:fin_year = 'ALL' OR LTRIM(RTRIM(FinYearVal)) = :fin_year)
            ORDER BY InvoiceDate DESC, TransNo DESC
        """
        sales_invoices = [dict(r) for r in db.execute(text(sales_inv_sql), params).mappings().all()]

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
            WHERE (LeaderCode = :code OR LOWER(LTRIM(RTRIM(LedgerName))) = :name_lower OR LedgerName LIKE :name_like)
              AND ISNULL(Status, '') <> 'Delete'
              AND (:fin_year = 'ALL' OR LTRIM(RTRIM(FinYearVal)) = :fin_year)
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

            if matched_sales_inv:
                status_label = "Invoiced & Completed" if collected_pct >= 100 else "Invoiced - Balance Due"
            elif adv_collected >= (pf_amount * (target_pct / 100.0)):
                status_label = "Target Advance Cleared"
            elif adv_collected > 0:
                status_label = f"Partial Advance ({collected_pct}%)"
            else:
                status_label = f"Advance Awaited ({target_pct}% Target)"

            milestones.append({
                "proforma_no": pf_no,
                "proforma_date": pf.get("TransDate"),
                "quotation_no": quote_no,
                "total_order_value": pf_amount,
                "target_advance_pct": target_pct,
                "target_advance_amount": round(pf_amount * (target_pct / 100.0), 2),
                "advance_collected": adv_collected,
                "advance_percentage_achieved": collected_pct,
                "sales_invoice_no": matched_sales_inv.get("TransNo") if matched_sales_inv else None,
                "sales_invoice_date": matched_sales_inv.get("InvoiceDate") if matched_sales_inv else None,
                "sales_invoice_amount": cls._to_float(matched_sales_inv.get("NetAmount")) if matched_sales_inv else None,
                "balance_pending": max(0.0, pf_amount - adv_collected),
                "status": status_label,
                "fin_year": pf.get("FinYearVal"),
            })

        # 7. Unified Chronological Timeline
        timeline = []
        for q in quotes:
            timeline.append({
                "doc_type": "Quotation",
                "doc_no": q.get("TransNo"),
                "doc_date": q.get("TransDate"),
                "fin_year": q.get("FinYearVal"),
                "amount": cls._to_float(q.get("NetAmount")),
                "status": q.get("ApprovalStatus") or "Active",
                "reference": q.get("Product") or "",
                "remarks": q.get("Remarks") or "",
                "terms": q.get("terms_conditions") or "",
            })
        for p in proformas:
            timeline.append({
                "doc_type": "Proforma Invoice",
                "doc_no": p.get("TransNo"),
                "doc_date": p.get("TransDate"),
                "fin_year": p.get("FinYearVal"),
                "amount": cls._to_float(p.get("NetAmount")),
                "status": p.get("ApprovalStatus") or "Issued",
                "reference": f"Quote: {p.get('QuotationNo') or '-'}",
                "remarks": p.get("Remarks") or "",
                "terms": "",
            })
        for s in sales_invoices:
            timeline.append({
                "doc_type": "Sales Invoice",
                "doc_no": s.get("TransNo"),
                "doc_date": s.get("InvoiceDate"),
                "fin_year": s.get("FinYearVal"),
                "amount": cls._to_float(s.get("NetAmount")),
                "status": s.get("ApprovalStatus") or "Billed",
                "reference": f"Ref: {s.get('InvoiceNo') or '-'}",
                "remarks": s.get("Remarks") or "",
                "terms": "",
            })
        for t in tally_vouchers:
            timeline.append({
                "doc_type": f"Tally {t.get('TransType')}",
                "doc_no": t.get("TransNo"),
                "doc_date": t.get("TransDate"),
                "fin_year": t.get("FinYearVal"),
                "debit": cls._to_float(t.get("DebitAmount")),
                "credit": cls._to_float(t.get("CreditAmount")),
                "amount": cls._to_float(t.get("CreditAmount")) if cls._to_float(t.get("CreditAmount")) > 0 else cls._to_float(t.get("DebitAmount")),
                "status": "Tally Ingested",
                "reference": t.get("AccHeadName") or "",
                "remarks": t.get("Narration") or "",
                "terms": "",
            })

        # 8. Statement of Account / Running Ledger
        running_ledger = []
        op_bal = cls._to_float(customer.get("OpeningBalance"))
        op_type = str(customer.get("BalanceType") or "Dr").strip()
        current_balance = op_bal if op_type.lower() == "dr" else -op_bal

        running_ledger.append({
            "entry_date": "Opening",
            "particulars": "Opening Balance",
            "voucher_type": "Opening",
            "voucher_no": "-",
            "debit": op_bal if op_type.lower() == "dr" else 0.0,
            "credit": op_bal if op_type.lower() == "cr" else 0.0,
            "running_balance": current_balance,
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
            ledger_raw.append({
                "date": str(t.get("TransDate") or ""),
                "particulars": f"Tally {t.get('TransType')} ({t.get('Narration') or ''})".strip(),
                "voucher_type": t.get("TransType"),
                "voucher_no": t.get("TransNo"),
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

        # 9. Key Performance Indicators
        tot_quoted = sum(cls._to_float(q.get("NetAmount")) for q in quotes)
        tot_pi = sum(cls._to_float(p.get("NetAmount")) for p in proformas)
        tot_invoiced = sum(cls._to_float(s.get("NetAmount")) for s in sales_invoices)
        tot_tally_receipts = sum(cls._to_float(v.get("CreditAmount")) for v in all_receipt_vouchers)
        tot_tally_payments = sum(cls._to_float(v.get("DebitAmount")) for v in tally_vouchers if v.get("TransType", "").lower() in ("payment", "cash payments", "bank payment"))
        net_outstanding = round(tot_invoiced - tot_tally_receipts, 2)

        return {
            "success": True,
            "customer_info": customer,
            "selected_fin_year": fy,
            "kpis": {
                "total_quotations_count": len(quotes),
                "total_quoted_amount": round(tot_quoted, 2),
                "total_proforma_count": len(proformas),
                "total_proforma_amount": round(tot_pi, 2),
                "total_sales_invoices_count": len(sales_invoices),
                "total_invoiced_amount": round(tot_invoiced, 2),
                "total_tally_receipts_amount": round(tot_tally_receipts, 2),
                "total_tally_payments_amount": round(tot_tally_payments, 2),
                "net_outstanding": net_outstanding,
                "closing_balance": round(current_balance, 2),
            },
            "milestones": milestones,
            "quotations": quotes,
            "proformas": proformas,
            "sales_invoices": sales_invoices,
            "tally_vouchers": tally_vouchers,
            "timeline": timeline,
            "running_ledger": running_ledger,
        }
