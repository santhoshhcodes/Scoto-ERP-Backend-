"""
Service layer for Customer Receipts & Advance Payments.
Manages atomic transactions across:
  - dbo.Acc_Receipts_Main (Header)
  - dbo.Acc_Receipts_Sub (Allocations against Invoices / Proformas / Quotations)
  - dbo.Acc_Trans_All (Central double-entry ledger for Customer Report & Sales Invoice status)
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import re

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.helpers.pagination import build_pagination_envelope
from src.helpers.sorting import resolve_raw_sort
from src.schemas.receipt import (
    CustomerReceiptCreate,
    CustomerReceiptResponse,
    ReceiptAllocationItem,
)
from src.services.customer_report_service import CustomerReportService


def _to_float(val: Any) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _parse_date(date_str: Optional[str]) -> Tuple[datetime, str, str]:
    """
    Parses a date string in various formats (YYYY-MM-DD, DD/MM/YYYY)
    Returns: (datetime_obj, dd/mm/yyyy_str, yyyy-mm-dd_str)
    """
    now = datetime.now()
    if not date_str:
        return now, now.strftime("%d/%m/%Y"), now.strftime("%Y-%m-%d")

    date_str = str(date_str).strip()
    dt = None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(date_str[:10], fmt)
            break
        except ValueError:
            pass

    if dt is None:
        dt = now

    return dt, dt.strftime("%d/%m/%Y"), dt.strftime("%Y-%m-%d")


def _get_fin_year_info(dt: datetime) -> Dict[str, str]:
    """
    Determines Indian Financial Year (April 1 to March 31).
    For example, Nov 2026 -> FinYearVal: '2026_2027', FinYearCode: '2', FinTag: '26-27'
    """
    year = dt.year
    month = dt.month
    start_year = year if month >= 4 else year - 1
    end_year = start_year + 1

    fin_year_val = f"{start_year}_{end_year}"
    fin_year_code = "2" if start_year >= 2026 else "1"
    fin_tag = f"{str(start_year)[-2:]}-{str(end_year)[-2:]}"

    return {
        "FinYearVal": fin_year_val,
        "FinYearCode": fin_year_code,
        "FinTag": fin_tag,
    }


class ReceiptService:

    @classmethod
    def get_deposit_accounts(cls, db: Session) -> List[Dict[str, Any]]:
        """
        Returns active Bank and Cash deposit accounts.
        """
        sql = """
            SELECT DISTINCT
                AccGenLdgCode AS code,
                AccGenLdgName AS name,
                AccSubGrpName AS group_name,
                AccLedgerHeaderName AS header_name
            FROM dbo.Acc_Mst_GeneralLedger
            WHERE AccSubGrpName IN ('Bank Accounts', 'Cash Balances', 'Current Accounts', 'Cash-in-Hand')
               OR AccLedgerHeaderName IN ('Current Accounts', 'Cash-in-Hand', 'Bank Accounts')
               OR AccGenLdgName LIKE '%HSBC%'
               OR AccGenLdgName LIKE '%Indian Bank%'
               OR AccGenLdgName LIKE '%Cash%'
            ORDER BY AccGenLdgCode ASC
        """
        rows = [dict(r) for r in db.execute(text(sql)).mappings().all()]

        # Provide standard defaults if GL table yields limited results
        known_defaults = [
            {"code": "GL/00077", "name": "HSBC - CA - 073-500266-001", "type": "Bank", "account_no": "073-500266-001", "bank_name": "HSBC"},
            {"code": "GL/00078", "name": "Indian Bank - CA - 6847005424", "type": "Bank", "account_no": "6847005424", "bank_name": "Indian Bank"},
            {"code": "GL/00081", "name": "Cash-in-Hand", "type": "Cash", "account_no": "", "bank_name": "Cash"},
        ]

        if not rows:
            return known_defaults

        formatted = []
        for r in rows:
            name = str(r.get("name") or "").strip()
            code = str(r.get("code") or "").strip()
            is_cash = "cash" in name.lower() or "cash" in str(r.get("group_name", "")).lower()
            acc_no = ""
            acc_match = re.search(r"(\d{6,})", name)
            if acc_match:
                acc_no = acc_match.group(1)

            bank_name = "Cash" if is_cash else ("HSBC" if "hsbc" in name.lower() else "Indian Bank" if "indian" in name.lower() else name.split("-")[0].strip())
            formatted.append({
                "code": code,
                "name": name,
                "type": "Cash" if is_cash else "Bank",
                "account_no": acc_no,
                "bank_name": bank_name,
            })

        # Ensure known accounts are present
        codes = {x["code"] for x in formatted}
        for d in known_defaults:
            if d["code"] not in codes:
                formatted.insert(0, d)

        return formatted

    @classmethod
    def get_open_documents_for_customer(
        cls,
        db: Session,
        customer_code: str,
        customer_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves pending Sales Invoices, Proformas, and Quotations for a customer,
        calculating the amount already paid and balance pending for easy allocation.
        """
        customer_code = (customer_code or "").strip()
        customer_name = (customer_name or "").strip()

        # Fetch Customer Dossier to leverage its precise reconciliation engine
        dossier = CustomerReportService.get_customer_dossier(db, customer_code or customer_name, fin_year="ALL")

        # 1. Open Sales Invoices
        raw_invoices = dossier.get("invoices_breakdown", [])
        open_invoices = []
        for inv in raw_invoices:
            bal_due = _to_float(inv.get("balance_due"))
            status_label = inv.get("payment_status", "PENDING")
            trans_no = inv.get("trans_no") or inv.get("TransNo")

            # Fetch sub-items from Acc_Sales_Inv_Sub
            sub_rows = db.execute(text("""
                SELECT ProductType, ItemCode, HSNCode, Qty, Rate, ItemValue, GST, CGST, SGST, IGST, NetAmount
                FROM dbo.Acc_Sales_Inv_Sub
                WHERE TransNo = :tno
            """), {"tno": trans_no}).mappings().all()

            sub_items = [dict(r) for r in sub_rows]
            product_desc = ", ".join(r.get("ProductType") or "" for r in sub_items if r.get("ProductType")) or "Services"

            # Header taxes from Acc_Sales_Inv_Main
            h_row = db.execute(text("""
                SELECT TotalItemAmount, TotalCGSTAmount, TotalSGSTAmount, TotalIGSTAmount, NetAmount
                FROM dbo.Acc_Sales_Inv_Main
                WHERE TransNo = :tno
            """), {"tno": trans_no}).mappings().first()
            h_dict = dict(h_row) if h_row else {}

            taxable_amt = _to_float(h_dict.get("TotalItemAmount"))
            cgst_amt = _to_float(h_dict.get("TotalCGSTAmount"))
            sgst_amt = _to_float(h_dict.get("TotalSGSTAmount"))
            igst_amt = _to_float(h_dict.get("TotalIGSTAmount"))
            tot_gst = cgst_amt + sgst_amt + igst_amt
            gst_pct = 18.0
            if sub_items and sub_items[0].get("GST"):
                try:
                    gst_pct = float(sub_items[0]["GST"])
                except Exception:
                    pass
            elif taxable_amt > 0 and tot_gst > 0:
                gst_pct = round((tot_gst / taxable_amt) * 100, 1)

            open_invoices.append({
                "doc_type": "SALES_INVOICE",
                "trans_no": trans_no,
                "invoice_no": inv.get("invoice_no") or inv.get("InvoiceNo") or trans_no,
                "invoice_date": inv.get("invoice_date") or inv.get("InvoiceDate") or inv.get("trans_date"),
                "total_amount": _to_float(inv.get("net_amount_float") or inv.get("NetAmount") or inv.get("net_amount")),
                "already_paid": _to_float(inv.get("amount_paid")),
                "balance_due": max(0.0, bal_due),
                "payment_status": status_label,
                "fin_year": inv.get("fin_year") or inv.get("FinYearVal"),
                "remarks": inv.get("remarks") or inv.get("Remarks"),
                # Product & GST Breakdown
                "product_desc": product_desc,
                "items": sub_items,
                "taxable_amount": taxable_amt,
                "gst_percentage": gst_pct,
                "cgst_amount": cgst_amt,
                "sgst_amount": sgst_amt,
                "igst_amount": igst_amt,
                "total_gst_amount": tot_gst,
            })

        # 2. Open Proforma Invoices & Advance Progress
        proformas = dossier.get("proformas", [])
        milestones = dossier.get("milestones", [])
        open_proformas = []
        for pf in proformas:
            pf_no = str(pf.get("TransNo") or "").strip()
            total_amt = _to_float(pf.get("NetAmount"))
            # Match milestone
            ms = next((m for m in milestones if str(m.get("proforma_no") or "").strip() == pf_no), None)
            adv_collected = _to_float(ms.get("advance_collected")) if ms else 0.0
            bal_pending = max(0.0, total_amt - adv_collected)

            # Query Proforma Main & Sub items
            pf_main = db.execute(text("""
                SELECT TotalItemAmount, TotalCGSTAmount, TotalSGSTAmount, TotalIGSTAmount, NetAmount
                FROM dbo.Acc_Proforma_Inv_Main
                WHERE TransNo = :tno
            """), {"tno": pf_no}).mappings().first()
            pf_dict = dict(pf_main) if pf_main else {}

            pf_subs = db.execute(text("""
                SELECT ProductType, ItemCode, HSNCode, Qty, Rate, ItemValue, GST, CGST, SGST, IGST, NetAmount
                FROM dbo.Acc_Proforma_Inv_Sub
                WHERE TransNo = :tno
            """), {"tno": pf_no}).mappings().all()
            pf_sub_items = [dict(r) for r in pf_subs]
            pf_product_desc = ", ".join(r.get("ProductType") or "" for r in pf_sub_items if r.get("ProductType")) or "Proforma Services"

            pf_taxable = _to_float(pf_dict.get("TotalItemAmount"))
            pf_cgst = _to_float(pf_dict.get("TotalCGSTAmount"))
            pf_sgst = _to_float(pf_dict.get("TotalSGSTAmount"))
            pf_igst = _to_float(pf_dict.get("TotalIGSTAmount"))
            pf_tot_gst = pf_cgst + pf_sgst + pf_igst
            pf_gst_pct = 18.0
            if pf_sub_items and pf_sub_items[0].get("GST"):
                try:
                    pf_gst_pct = float(pf_sub_items[0]["GST"])
                except Exception:
                    pass

            open_proformas.append({
                "doc_type": "PROFORMA",
                "trans_no": pf_no,
                "doc_date": pf.get("TransDate"),
                "quotation_no": pf.get("QuotationNo"),
                "total_amount": total_amt,
                "already_paid": adv_collected,
                "balance_pending": bal_pending,
                "target_advance_pct": ms.get("target_advance_pct", 30.0) if ms else 30.0,
                "status": ms.get("status") if ms else "Active",
                "fin_year": pf.get("FinYearVal"),
                # Product & GST Breakdown
                "product_desc": pf_product_desc,
                "items": pf_sub_items,
                "taxable_amount": pf_taxable,
                "gst_percentage": pf_gst_pct,
                "cgst_amount": pf_cgst,
                "sgst_amount": pf_sgst,
                "igst_amount": pf_igst,
                "total_gst_amount": pf_tot_gst,
            })

        # 3. Active Quotations
        quotes = dossier.get("quotations", [])
        open_quotes = []
        for q in quotes:
            q_no = str(q.get("TransNo") or "").strip()
            total_amt = _to_float(q.get("NetAmount"))
            matched_ms = [m for m in milestones if str(m.get("quotation_no") or "").strip() == q_no]
            adv_collected = sum(_to_float(m.get("advance_collected")) for m in matched_ms)
            bal_pending = max(0.0, total_amt - adv_collected)

            # Query Quotation Main & Sub items
            q_main = db.execute(text("""
                SELECT TotItemAmt AS TotalItemAmount, TotCGSTAmt AS TotalCGSTAmount, TotSGSTAmt AS TotalSGSTAmount, TotIGSTAmt AS TotalIGSTAmount, NetAmount
                FROM dbo.Acc_Quotation_Main
                WHERE TransNo = :tno
            """), {"tno": q_no}).mappings().first()
            q_dict = dict(q_main) if q_main else {}

            q_subs = db.execute(text("""
                SELECT ProductType, ItemCode, HSNCode, Qty, Rate, ItemValue, GST, CGST, SGST, IGST, NetAmount
                FROM dbo.Acc_Quotation_Sub
                WHERE TransNo = :tno
            """), {"tno": q_no}).mappings().all()
            q_sub_items = [dict(r) for r in q_subs]
            q_product_desc = q.get("Product") or (", ".join(r.get("ProductType") or "" for r in q_sub_items if r.get("ProductType")) or "Quotation Item")

            q_taxable = _to_float(q_dict.get("TotalItemAmount"))
            q_cgst = _to_float(q_dict.get("TotalCGSTAmount"))
            q_sgst = _to_float(q_dict.get("TotalSGSTAmount"))
            q_igst = _to_float(q_dict.get("TotalIGSTAmount"))
            q_tot_gst = q_cgst + q_sgst + q_igst
            q_gst_pct = 18.0
            if q_sub_items and q_sub_items[0].get("GST"):
                try:
                    q_gst_pct = float(q_sub_items[0]["GST"])
                except Exception:
                    pass

            open_quotes.append({
                "doc_type": "QUOTATION",
                "trans_no": q_no,
                "doc_date": q.get("TransDate"),
                "total_amount": total_amt,
                "already_paid": adv_collected,
                "balance_pending": bal_pending,
                "product": q_product_desc,
                "fin_year": q.get("FinYearVal"),
                # Product & GST Breakdown
                "product_desc": q_product_desc,
                "items": q_sub_items,
                "taxable_amount": q_taxable,
                "gst_percentage": q_gst_pct,
                "cgst_amount": q_cgst,
                "sgst_amount": q_sgst,
                "igst_amount": q_igst,
                "total_gst_amount": q_tot_gst,
            })

        return {
            "customer_code": dossier.get("customer_code") or customer_code,
            "customer_name": dossier.get("customer_name") or customer_name,
            "invoices": open_invoices,
            "proformas": open_proformas,
            "quotations": open_quotes,
            "outstanding_balance": dossier.get("invoices_summary", {}).get("total_balance_due", 0.0),
        }

    @classmethod
    def create_customer_receipt(
        cls,
        db: Session,
        payload: CustomerReceiptCreate,
        user: str = "ADMIN",
    ) -> Dict[str, Any]:
        """
        Creates a new customer receipt atomically across Acc_Receipts_Main, Acc_Receipts_Sub, and Acc_Trans_All.
        """
        gross_amt = round(_to_float(payload.GrossAmount), 2)
        tds_amt = round(_to_float(payload.TDSAmount), 2)
        net_amt = round(_to_float(payload.NetAmount), 2)

        # Basic arithmetic integrity validation
        if abs((net_amt + tds_amt) - gross_amt) > 0.05:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Arithmetic mismatch: Net Amount (₹{net_amt}) + TDS (₹{tds_amt}) does not equal Gross Settlement (₹{gross_amt}).",
            )

        if gross_amt <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gross Settlement Amount must be greater than zero.",
            )

        # Date and Financial Year
        dt, trans_date_formatted, trans_date_iso = _parse_date(payload.ReceiptDate)
        fin_info = _get_fin_year_info(dt)
        fin_year_val = payload.FinYearVal or fin_info["FinYearVal"]
        fin_year_code = fin_info["FinYearCode"]
        fin_tag = fin_info["FinTag"]

        # Prefix: R-CS for Cash, R-BK for Bank
        is_cash = "cash" in payload.PayMode.lower() or "cash" in payload.DepositGLCode.lower()
        prefix = "R-CS" if is_cash else "R-BK"

        # Thread-safe sequence generation inside transaction
        seq_sql = text("""
            SELECT ISNULL(MAX(TRY_CAST(TransVal AS INT)), 0) AS max_val
            FROM dbo.Acc_Receipts_Main WITH (UPDLOCK, HOLDLOCK)
            WHERE FinYearVal = :fin_year_val AND TransNo LIKE :prefix_like
        """)
        current_seq = db.execute(seq_sql, {
            "fin_year_val": fin_year_val,
            "prefix_like": f"{prefix}/{fin_tag}/%",
        }).scalar() or 0

        next_seq = current_seq + 1
        trans_no = f"{prefix}/{fin_tag}/{next_seq:05d}"
        trans_val = str(next_seq)

        # Determine primary linked document identifier for narration
        linked_docs = []
        for alloc in payload.Allocations:
            doc_ref = (alloc.DocNo or "").strip()
            if alloc.SecondaryDocNo:
                doc_ref += f" ({alloc.SecondaryDocNo})"
            if doc_ref:
                linked_docs.append(doc_ref)

        primary_doc_str = ", ".join(linked_docs) if linked_docs else (payload.ReceiptType or "Direct Payment")

        # Calculate proportional GST across allocated documents
        total_receipt_gst = 0.0
        calculated_allocations = []
        if payload.Allocations:
            for alloc in payload.Allocations:
                alloc_gross = round(_to_float(alloc.AllocatedAmount), 2)
                alloc_tds = round(_to_float(alloc.TDSAmount), 2)
                alloc_line_tot = round(alloc_gross - alloc_tds, 2)

                doc_total = _to_float(alloc.TotalDocAmount)
                ratio = min(1.0, alloc_gross / doc_total) if doc_total > 0 else 1.0

                cgst_a = round(_to_float(alloc.CGSTAmount) * ratio, 2)
                sgst_a = round(_to_float(alloc.SGSTAmount) * ratio, 2)
                igst_a = round(_to_float(alloc.IGSTAmount) * ratio, 2)
                tot_gst_a = round(cgst_a + sgst_a + igst_a, 2)
                total_receipt_gst += tot_gst_a

                gst_name = "IGST" if igst_a > 0 else "GST"
                cgst_per = _to_float(alloc.CGSTPercentage) or (_to_float(alloc.GSTPercentage) / 2 if cgst_a > 0 else 0.0)
                sgst_per = _to_float(alloc.SGSTPercentage) or (_to_float(alloc.GSTPercentage) / 2 if sgst_a > 0 else 0.0)
                igst_per = _to_float(alloc.IGSTPercentage) or (_to_float(alloc.GSTPercentage) if igst_a > 0 else 0.0)

                calculated_allocations.append({
                    "alloc": alloc,
                    "gross": alloc_gross,
                    "tds": alloc_tds,
                    "net": alloc_line_tot,
                    "cgst_amt": cgst_a,
                    "sgst_amt": sgst_a,
                    "igst_amt": igst_a,
                    "tot_gst_amt": tot_gst_a,
                    "cgst_per": cgst_per,
                    "sgst_per": sgst_per,
                    "igst_per": igst_per,
                    "gst_name": gst_name,
                })

        # 1. Insert Header: dbo.Acc_Receipts_Main
        insert_main_sql = text("""
            INSERT INTO dbo.Acc_Receipts_Main (
                CCode, LCode, FinYearCode, FinYearVal, TransNo, Disp_TransNo, TransVal,
                TransDate, ReceiptType, TransType, BankCode, BankName, BankShortName,
                AccountsNo, BankGLCode, BankGLName, BankLdgHeadCode, BankLdgHeadName,
                RefNo, RefDate, PayMode, Remarks, MemberType, MemberName,
                TotInvAmt, TotReceivedAmt, TotBalanceAmt, TotGSTAmt, TotTDSAmt, TotTCSAmt,
                NetAmount, RoundOffType, RoundOff, InvoiceAmount, Status,
                ApprovalRemarks, ApprovalStatus, ApprovedBy, ApprovedOn,
                SysName, SysIp, UserId, UserName, CreateOn
            ) VALUES (
                :ccode, :lcode, :fin_year_code, :fin_year_val, :trans_no, :disp_trans_no, :trans_val,
                :trans_date, :receipt_type, :trans_type, :bank_code, :bank_name, :bank_short_name,
                :accounts_no, :bank_gl_code, :bank_gl_name, :bank_ldg_head_code, :bank_ldg_head_name,
                :ref_no, :ref_date, :pay_mode, :remarks, :member_type, :member_name,
                :tot_inv_amt, :tot_received_amt, :tot_balance_amt, :tot_gst_amt, :tot_tds_amt, 0.0,
                :net_amount, 'None', 0.0, :invoice_amount, 'Add',
                'Auto-approved on ERP entry', '1', :approved_by, :approved_on,
                'API_SERVER', '127.0.0.1', :user_id, :user_name, :create_on
            )
        """)

        db.execute(insert_main_sql, {
            "ccode": payload.CCode or "SCT",
            "lcode": payload.LCode or "UNIT I",
            "fin_year_code": fin_year_code,
            "fin_year_val": fin_year_val,
            "trans_no": trans_no,
            "disp_trans_no": trans_no,
            "trans_val": trans_val,
            "trans_date": trans_date_formatted,
            "receipt_type": payload.ReceiptType or "Regular Collections",
            "trans_type": "Cash Receipt" if is_cash else "Bank Receipt",
            "bank_code": payload.DepositGLCode,
            "bank_name": payload.DepositAccountName or payload.BankName or "Bank",
            "bank_short_name": payload.BankName or "Bank",
            "accounts_no": payload.AccountNo or "",
            "bank_gl_code": payload.DepositGLCode,
            "bank_gl_name": payload.DepositAccountName or payload.BankName or "Bank Account",
            "bank_ldg_head_code": "1-2-2-1" if is_cash else "1-2-1-2",
            "bank_ldg_head_name": "Cash-in-Hand" if is_cash else "Current Accounts",
            "ref_no": payload.RefNo or "",
            "ref_date": payload.RefDate or trans_date_formatted,
            "pay_mode": payload.PayMode or "NEFT/RTGS",
            "remarks": payload.Remarks or f"Customer payment received against {primary_doc_str}",
            "member_type": "Customer",
            "member_name": payload.CustomerName,
            "tot_inv_amt": gross_amt,
            "tot_received_amt": net_amt,
            "tot_balance_amt": 0.0,
            "tot_gst_amt": round(total_receipt_gst, 2),
            "tot_tds_amt": tds_amt,
            "net_amount": net_amt,
            "invoice_amount": gross_amt,
            "approved_by": user,
            "approved_on": trans_date_formatted,
            "user_id": user,
            "user_name": user,
            "create_on": datetime.now().strftime("%b %d %Y %I:%M%p"),
        })

        # Fetch CustomerUnit from Customer Master if available
        cust_unit_val = getattr(payload, "CustomerUnit", None)
        if not cust_unit_val and payload.CustomerCode:
            try:
                u_row = db.execute(text("SELECT CustomerUnit FROM dbo.Acc_Mst_Ledger WHERE LedgerCode = :c"), {"c": payload.CustomerCode}).scalar()
                if u_row:
                    cust_unit_val = str(u_row).strip()
            except Exception:
                pass

        # 2. Insert Line Items: dbo.Acc_Receipts_Sub
        insert_sub_sql = text("""
            INSERT INTO dbo.Acc_Receipts_Sub (
                CCode, LCode, FinYearCode, FinYearVal, TransNo, TransDate,
                LedgerCode, LedgerName, PartyName, InvNo, InvDate, InvoiceAmt,
                GSTName, CGSTPer, CGSTAmt, SGSTPer, SGSTAmt, IGSTPer, IGSTAmt, GSTAmt,
                TDSName, TDSPer, TDSAmt, TCSName, TCSPer, TCSAmt, SubTotal,
                RoundOffType, RoundOff, LineTotal, Status, SysName, SysIp, UserId, UserName,
                CustomerUnit
            ) VALUES (
                :ccode, :lcode, :fin_year_code, :fin_year_val, :trans_no, :trans_date,
                :ledger_code, :ledger_name, :party_name, :inv_no, :inv_date, :invoice_amt,
                :gst_name, :cgst_per, :cgst_amt, :sgst_per, :sgst_amt, :igst_per, :igst_amt, :gst_amt,
                :tds_name, :tds_per, :tds_amt, '-Select-', 0.0, 0.0, :sub_total,
                'None', 0.0, :line_total, 'Add', 'API_SERVER', '127.0.0.1', :user_id, :user_name,
                :customer_unit
            )
        """)

        if calculated_allocations:
            for item in calculated_allocations:
                alloc = item["alloc"]
                db.execute(insert_sub_sql, {
                    "ccode": payload.CCode or "SCT",
                    "lcode": payload.LCode or "UNIT I",
                    "fin_year_code": fin_year_code,
                    "fin_year_val": fin_year_val,
                    "trans_no": trans_no,
                    "trans_date": trans_date_formatted,
                    "ledger_code": payload.CustomerCode,
                    "ledger_name": payload.CustomerName,
                    "party_name": payload.CustomerName,
                    "inv_no": alloc.DocNo,
                    "inv_date": alloc.DocDate or trans_date_formatted,
                    "invoice_amt": item["gross"],
                    "gst_name": item["gst_name"],
                    "cgst_per": item["cgst_per"],
                    "cgst_amt": item["cgst_amt"],
                    "sgst_per": item["sgst_per"],
                    "sgst_amt": item["sgst_amt"],
                    "igst_per": item["igst_per"],
                    "igst_amt": item["igst_amt"],
                    "gst_amt": item["tot_gst_amt"],
                    "tds_name": f"TDS - {payload.TDSSection or '194C'}" if item["tds"] > 0 else "-Select-",
                    "tds_per": _to_float(alloc.TDSPercentage),
                    "tds_amt": item["tds"],
                    "sub_total": item["gross"],
                    "line_total": item["net"],
                    "user_id": user,
                    "user_name": user,
                    "customer_unit": cust_unit_val,
                })
        else:
            # Single generic allocation when no specific document was provided
            db.execute(insert_sub_sql, {
                "ccode": payload.CCode or "SCT",
                "lcode": payload.LCode or "UNIT I",
                "fin_year_code": fin_year_code,
                "fin_year_val": fin_year_val,
                "trans_no": trans_no,
                "trans_date": trans_date_formatted,
                "ledger_code": payload.CustomerCode,
                "ledger_name": payload.CustomerName,
                "party_name": payload.CustomerName,
                "inv_no": primary_doc_str,
                "inv_date": trans_date_formatted,
                "invoice_amt": gross_amt,
                "gst_name": "GST",
                "cgst_per": 0.0,
                "cgst_amt": 0.0,
                "sgst_per": 0.0,
                "sgst_amt": 0.0,
                "igst_per": 0.0,
                "igst_amt": 0.0,
                "gst_amt": 0.0,
                "tds_name": f"TDS - {payload.TDSSection or '194C'}" if tds_amt > 0 else "-Select-",
                "tds_per": _to_float(payload.TDSPercentage),
                "tds_amt": tds_amt,
                "sub_total": gross_amt,
                "line_total": net_amt,
                "user_id": user,
                "user_name": user,
                "customer_unit": cust_unit_val,
            })

        # 3. Post Balanced Double-Entry rows to dbo.Acc_Trans_All
        insert_trans_all_sql = text("""
            INSERT INTO dbo.Acc_Trans_All (
                CCode, LCode, FinYearCode, FinYearVal, TransNo, TransDate,
                LeaderCode, LedgerName, AccHeadCode, AccHeadName, TransType,
                CreditAmount, DebitAmount, Status, UserId, UserName, CreatedBy,
                RefNo, RefDate, Narration
            ) VALUES (
                :ccode, :lcode, :fin_year_code, :fin_year_val, :trans_no, :trans_date,
                :leader_code, :ledger_name, :acc_head_code, :acc_head_name, :trans_type,
                :credit_amount, :debit_amount, 'Add', :user_id, :user_name, :created_by,
                :ref_no, :ref_date, :narration
            )
        """)

        created_by_str = datetime.now().strftime("%b %d %Y %I:%M%p")

        # Row 1: Debit Bank / Cash (Increases bank balance by net amount received)
        db.execute(insert_trans_all_sql, {
            "ccode": payload.CCode or "SCT",
            "lcode": payload.LCode or "UNIT I",
            "fin_year_code": fin_year_code,
            "fin_year_val": fin_year_val,
            "trans_no": trans_no,
            "trans_date": trans_date_formatted,
            "leader_code": payload.DepositGLCode,
            "ledger_name": payload.DepositAccountName or payload.BankName or "Bank Account",
            "acc_head_code": "1-2-2-1" if is_cash else "1-2-1-2",
            "acc_head_name": "Cash Balances" if is_cash else "Current Accounts",
            "trans_type": "Receipt",
            "credit_amount": 0.0,
            "debit_amount": net_amt,
            "user_id": user,
            "user_name": user,
            "created_by": created_by_str,
            "ref_no": payload.RefNo or "",
            "ref_date": payload.RefDate or trans_date_formatted,
            "narration": f"Receipt from {payload.CustomerName} for {primary_doc_str} - Mode: {payload.PayMode} - Ref: {payload.RefNo or 'N/A'}",
        })

        # Row 2: Debit TDS Receivable (if customer deducted tax at source)
        if tds_amt > 0:
            db.execute(insert_trans_all_sql, {
                "ccode": payload.CCode or "SCT",
                "lcode": payload.LCode or "UNIT I",
                "fin_year_code": fin_year_code,
                "fin_year_val": fin_year_val,
                "trans_no": trans_no,
                "trans_date": trans_date_formatted,
                "leader_code": "GL/00166",  # Contracts 194C / TDS Receivable
                "ledger_name": f"TDS Receivable - {payload.TDSSection or '194C'}",
                "acc_head_code": "1-2-8-2",
                "acc_head_name": "TDS Receivable",
                "trans_type": "Receipt",
                "credit_amount": 0.0,
                "debit_amount": tds_amt,
                "user_id": user,
                "user_name": user,
                "created_by": created_by_str,
                "ref_no": payload.RefNo or "",
                "ref_date": payload.RefDate or trans_date_formatted,
                "narration": f"TDS deducted by {payload.CustomerName} on {primary_doc_str} ({payload.TDSPercentage}%)",
            })

        # Row 3: Credit Customer Ledger (Decreases customer's outstanding balance)
        # Note: The narration contains the primary document number (e.g. SINV/... or PI-...)
        # so CustomerReportService and SalesInvoiceService match it instantly!
        customer_narration = f"Receipt against {primary_doc_str} - Mode: {payload.PayMode} - Ref: {payload.RefNo or 'N/A'}"
        if tds_amt > 0:
            customer_narration += f" - TDS Deducted: Rs. {tds_amt:.2f}"

        db.execute(insert_trans_all_sql, {
            "ccode": payload.CCode or "SCT",
            "lcode": payload.LCode or "UNIT I",
            "fin_year_code": fin_year_code,
            "fin_year_val": fin_year_val,
            "trans_no": trans_no,
            "trans_date": trans_date_formatted,
            "leader_code": payload.CustomerCode,
            "ledger_name": payload.CustomerName,
            "acc_head_code": "1-2-2-1",
            "acc_head_name": "Sundry Debtors",
            "trans_type": "Receipt",
            "credit_amount": gross_amt,
            "debit_amount": 0.0,
            "user_id": user,
            "user_name": user,
            "created_by": created_by_str,
            "ref_no": payload.RefNo or "",
            "ref_date": payload.RefDate or trans_date_formatted,
            "narration": customer_narration,
        })

        db.commit()

        return {
            "success": True,
            "message": f"Customer receipt '{trans_no}' successfully recorded.",
            "trans_no": trans_no,
            "trans_date": trans_date_formatted,
            "customer_code": payload.CustomerCode,
            "customer_name": payload.CustomerName,
            "gross_amount": gross_amt,
            "tds_amount": tds_amt,
            "net_amount": net_amt,
            "bank_name": payload.DepositAccountName or payload.BankName,
            "pay_mode": payload.PayMode,
            "ref_no": payload.RefNo,
            "allocations_count": len(payload.Allocations),
        }

    ALLOWED_SORT_COLUMNS = {
        "TransNo": "m.TransNo",
        "TransDate": "m.TransDate",
        "CustomerName": "m.MemberName",
        "ReceiptType": "m.ReceiptType",
        "BankName": "m.BankName",
        "PayMode": "m.PayMode",
        "GrossAmount": "m.TotInvAmt",
        "NetAmount": "m.NetAmount",
        "CreatedOn": "m.CreateOn",
    }

    @classmethod
    def get_customer_receipts(
        cls,
        db: Session,
        search: Optional[str] = None,
        customer_code: Optional[str] = None,
        fin_year: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "desc",
        fetch_all: bool = False,
    ) -> Dict[str, Any]:
        """
        Lists customer receipts with search, customer filter, pagination and dynamic sorting.
        Supports both limit/offset and page/page_size seamlessly.
        """
        calc_page = page if page and page > 0 else ((offset // limit) + 1 if limit > 0 else 1)
        calc_limit = page_size if page_size and page_size > 0 else limit
        calc_offset = (calc_page - 1) * calc_limit if page else offset

        where_clauses = ["ISNULL(m.Status, '') <> 'Delete'"]
        params = {"limit": calc_limit, "offset": calc_offset}

        if customer_code:
            where_clauses.append("(m.MemberName LIKE :cust OR m.BankGLCode = :cust)")
            params["cust"] = f"%{customer_code}%"

        if fin_year and fin_year.upper() != "ALL":
            fy_dash = fin_year.replace("_", "-").strip()
            fy_under = fin_year.replace("-", "_").strip()
            where_clauses.append("""(
                REPLACE(LTRIM(RTRIM(m.FinYearVal)), '_', '-') = :fy_dash
                OR REPLACE(LTRIM(RTRIM(m.FinYearVal)), '-', '_') = :fy_under
            )""")
            params["fy_dash"] = fy_dash
            params["fy_under"] = fy_under

        if search:
            where_clauses.append("(m.TransNo LIKE :search OR m.MemberName LIKE :search OR m.RefNo LIKE :search OR m.Remarks LIKE :search)")
            params["search"] = f"%{search}%"

        where_sql = " AND ".join(where_clauses)

        count_sql = text(f"SELECT COUNT(*) FROM dbo.Acc_Receipts_Main m WHERE {where_sql}")
        total_count = db.execute(count_sql, params).scalar() or 0

        sort_col, sort_dir = resolve_raw_sort(
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_sort_columns=cls.ALLOWED_SORT_COLUMNS,
            default_column="m.TransDate",
            default_order="DESC",
        )

        order_by_clause = f"{sort_col} {sort_dir}"
        if "transno" not in sort_col.lower():
            order_by_clause += ", m.TransNo DESC"

        if fetch_all or calc_limit <= 0:
            list_sql = text(f"""
                SELECT
                    m.TransNo,
                    m.TransDate,
                    m.MemberName AS CustomerName,
                    m.ReceiptType,
                    m.BankName,
                    m.BankGLCode AS DepositGLCode,
                    m.PayMode,
                    m.RefNo,
                    ISNULL(m.TotInvAmt, m.NetAmount) AS GrossAmount,
                    ISNULL(m.TotTDSAmt, 0.0) AS TDSAmount,
                    ISNULL(m.NetAmount, 0.0) AS NetAmount,
                    m.Remarks,
                    m.Status,
                    m.CreateOn AS CreatedOn,
                    m.FinYearVal
                FROM dbo.Acc_Receipts_Main m
                WHERE {where_sql}
                ORDER BY {order_by_clause}
            """)
        else:
            list_sql = text(f"""
                SELECT
                    m.TransNo,
                    m.TransDate,
                    m.MemberName AS CustomerName,
                    m.ReceiptType,
                    m.BankName,
                    m.BankGLCode AS DepositGLCode,
                    m.PayMode,
                    m.RefNo,
                    ISNULL(m.TotInvAmt, m.NetAmount) AS GrossAmount,
                    ISNULL(m.TotTDSAmt, 0.0) AS TDSAmount,
                    ISNULL(m.NetAmount, 0.0) AS NetAmount,
                    m.Remarks,
                    m.Status,
                    m.CreateOn AS CreatedOn,
                    m.FinYearVal
                FROM dbo.Acc_Receipts_Main m
                WHERE {where_sql}
                ORDER BY {order_by_clause}
                OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """)

        items = [dict(r) for r in db.execute(list_sql, params).mappings().all()]

        # Convert numeric fields to float
        for item in items:
            item["GrossAmount"] = _to_float(item.get("GrossAmount"))
            item["TDSAmount"] = _to_float(item.get("TDSAmount"))
            item["NetAmount"] = _to_float(item.get("NetAmount"))

        envelope = build_pagination_envelope(
            records=items,
            total_records=total_count,
            page=calc_page,
            page_size=calc_limit,
        )
        envelope["limit"] = calc_limit
        envelope["offset"] = calc_offset
        return envelope

    @classmethod
    def get_receipt_details(cls, db: Session, trans_no: str) -> Dict[str, Any]:
        """
        Retrieves full details of a receipt including header, sub line allocations, and general ledger postings.
        """
        trans_no = (trans_no or "").strip()

        header_sql = text("""
            SELECT TOP 1 *
            FROM dbo.Acc_Receipts_Main
            WHERE TransNo = :trans_no AND ISNULL(Status, '') <> 'Delete'
        """)
        header = db.execute(header_sql, {"trans_no": trans_no}).mappings().first()
        if not header:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Receipt '{trans_no}' not found.")

        header_dict = dict(header)

        sub_sql = text("""
            SELECT *
            FROM dbo.Acc_Receipts_Sub
            WHERE TransNo = :trans_no AND ISNULL(Status, '') <> 'Delete'
        """)
        subs = [dict(r) for r in db.execute(sub_sql, {"trans_no": trans_no}).mappings().all()]

        gl_sql = text("""
            SELECT *
            FROM dbo.Acc_Trans_All
            WHERE TransNo = :trans_no AND ISNULL(Status, '') <> 'Delete'
            ORDER BY DebitAmount DESC, CreditAmount DESC
        """)
        gl_entries = [dict(r) for r in db.execute(gl_sql, {"trans_no": trans_no}).mappings().all()]

        return {
            "header": header_dict,
            "allocations": subs,
            "ledger_entries": gl_entries,
        }

    @classmethod
    def void_customer_receipt(
        cls,
        db: Session,
        trans_no: str,
        reason: str = "Voided by user",
        user: str = "ADMIN",
    ) -> Dict[str, Any]:
        """
        Safely voids a receipt by updating Status = 'Delete' across Main, Sub, and Trans_All.
        """
        trans_no = (trans_no or "").strip()

        # Check existence
        check = db.execute(
            text("SELECT 1 FROM dbo.Acc_Receipts_Main WHERE TransNo = :trans_no AND ISNULL(Status, '') <> 'Delete'"),
            {"trans_no": trans_no},
        ).first()
        if not check:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Receipt '{trans_no}' not found or already voided.")

        # Mark as Delete
        db.execute(text("UPDATE dbo.Acc_Receipts_Main SET Status = 'Delete', Remarks = ISNULL(Remarks, '') + ' [Voided: ' + :reason + ']' WHERE TransNo = :trans_no"), {"trans_no": trans_no, "reason": reason})
        db.execute(text("UPDATE dbo.Acc_Receipts_Sub SET Status = 'Delete' WHERE TransNo = :trans_no"), {"trans_no": trans_no})
        db.execute(text("UPDATE dbo.Acc_Trans_All SET Status = 'Delete' WHERE TransNo = :trans_no"), {"trans_no": trans_no})

        db.commit()

        return {
            "success": True,
            "message": f"Receipt '{trans_no}' has been safely voided.",
            "trans_no": trans_no,
        }
