"""
Service layer for generating Executive Customer Report & Ledger Dossier Excel Workbooks (.xlsx).
Replaces frontend-only ad-hoc exports with authentic, multi-sheet, beautifully formatted
Scoto ERP accounting workbooks matching the design of the Expense and Transaction modules.
"""

import io
from datetime import datetime
from typing import Any, Dict, List, Optional

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session

from src.services.customer_report_service import CustomerReportService


# =============================================================================
# THEME & COLOR PALETTE (Matched to Scoto ERP Corporate & Expense Themes)
# =============================================================================
C_PRIMARY = "6F2C8F"       # Scoto Purple
C_NAVY = "0F172A"          # Corporate Dark Slate
C_SLATE_HEADER = "1E293B"  # Table Header Dark
C_SLATE_BG = "F8FAFC"      # Soft zebra background
C_CARD_BG = "F1F5F9"       # KPI card background
C_BORDER = "CBD5E1"        # Soft border
C_BORDER_DARK = "64748B"   # Dark border
C_WHITE = "FFFFFF"
C_GREEN_BG = "DCFCE7"      # Paid / Credit Soft Green
C_GREEN_TEXT = "15803D"
C_AMBER_BG = "FEF3C7"      # Partial / Milestone Soft Amber
C_AMBER_TEXT = "B45309"
C_ROSE_BG = "FEE2E2"       # Pending / Overdue Soft Rose
C_ROSE_TEXT = "B91C1C"
C_BLUE_BG = "EFF6FF"       # Info / Invoice Soft Blue
C_BLUE_TEXT = "1D4ED8"

# Fonts
FONT_FAMILY = "Calibri"
font_title = Font(name=FONT_FAMILY, size=16, bold=True, color="FFFFFF")
font_subtitle = Font(name=FONT_FAMILY, size=10, italic=True, color="E2E8F0")
font_sec_header = Font(name=FONT_FAMILY, size=11, bold=True, color="0F172A")
font_tbl_header = Font(name=FONT_FAMILY, size=10, bold=True, color="FFFFFF")
font_tbl_header_light = Font(name=FONT_FAMILY, size=10, bold=True, color="1E293B")
font_data = Font(name=FONT_FAMILY, size=10, color="0F172A")
font_data_bold = Font(name=FONT_FAMILY, size=10, bold=True, color="0F172A")
font_mono = Font(name="Consolas", size=9, color="1E293B")
font_mono_bold = Font(name="Consolas", size=9, bold=True, color="0F172A")
font_kpi_label = Font(name=FONT_FAMILY, size=8, bold=True, color="475569")
font_kpi_value = Font(name=FONT_FAMILY, size=13, bold=True, color="0F172A")

# Fills
fill_primary = PatternFill(start_color=C_PRIMARY, end_color=C_PRIMARY, fill_type="solid")
fill_navy = PatternFill(start_color=C_NAVY, end_color=C_NAVY, fill_type="solid")
fill_tbl_header = PatternFill(start_color=C_SLATE_HEADER, end_color=C_SLATE_HEADER, fill_type="solid")
fill_tbl_header_light = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
fill_card = PatternFill(start_color=C_CARD_BG, end_color=C_CARD_BG, fill_type="solid")
fill_zebra = PatternFill(start_color=C_SLATE_BG, end_color=C_SLATE_BG, fill_type="solid")
fill_green = PatternFill(start_color=C_GREEN_BG, end_color=C_GREEN_BG, fill_type="solid")
fill_amber = PatternFill(start_color=C_AMBER_BG, end_color=C_AMBER_BG, fill_type="solid")
fill_rose = PatternFill(start_color=C_ROSE_BG, end_color=C_ROSE_BG, fill_type="solid")
fill_blue = PatternFill(start_color=C_BLUE_BG, end_color=C_BLUE_BG, fill_type="solid")
fill_total = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

# Borders
thin_side = Side(style="thin", color=C_BORDER)
border_cell = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
border_total = Border(
    top=Side(style="thin", color=C_NAVY),
    bottom=Side(style="double", color=C_NAVY),
    left=thin_side,
    right=thin_side,
)

# Alignments
align_left = Alignment(horizontal="left", vertical="center")
align_right = Alignment(horizontal="right", vertical="center")
align_center = Alignment(horizontal="center", vertical="center")
align_wrap = Alignment(horizontal="left", vertical="center", wrap_text=True)

# Formats
NUM_CURRENCY = "#,##0.00"
NUM_QTY = "#,##0"


def _auto_adjust_columns(ws, min_width: int = 12, max_width: int = 45):
    """Auto-adjust worksheet column widths based on maximum contents."""
    ws.views.sheetView[0].showGridLines = True
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            val = cell.value
            if val is not None:
                # ignore very long text or merged header rows
                text_val = str(val)
                if len(text_val) < 80:
                    max_len = max(max_len, len(text_val))
        calc_width = max(min_width, min(max_len + 3, max_width))
        ws.column_dimensions[col_letter].width = calc_width


class CustomerReportExcelService:

    @classmethod
    def generate_excel(
        cls,
        db: Session,
        client_code: str,
        fin_year: str = "ALL",
        tab: str = "ALL",
    ) -> io.BytesIO:
        """
        Generates an Executive multi-sheet Customer Dossier Excel workbook.
        """
        dossier = CustomerReportService.get_customer_dossier(db, client_code=client_code, fin_year=fin_year)
        customer = dossier.get("customer_info", {})
        kpis = dossier.get("kpis", {})
        invoices_breakdown = dossier.get("invoices_breakdown", [])
        milestones = dossier.get("milestones", [])
        running_ledger = dossier.get("running_ledger", [])
        receipts = dossier.get("receipt_vouchers", []) or dossier.get("tally_vouchers", [])

        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        # -------------------------------------------------------------
        # SHEET 1: EXECUTIVE SUMMARY & CUSTOMER KYC
        # -------------------------------------------------------------
        cls._build_summary_sheet(wb, customer, kpis, fin_year)

        # -------------------------------------------------------------
        # SHEET 2: SALES INVOICES & SETTLEMENT
        # -------------------------------------------------------------
        cls._build_invoices_sheet(wb, customer, invoices_breakdown, fin_year)

        # -------------------------------------------------------------
        # SHEET 3: ADVANCE MILESTONES TRACKER
        # -------------------------------------------------------------
        cls._build_milestones_sheet(wb, customer, milestones, fin_year)

        # -------------------------------------------------------------
        # SHEET 4: STATEMENT OF ACCOUNT (RUNNING LEDGER)
        # -------------------------------------------------------------
        cls._build_ledger_sheet(wb, customer, running_ledger, fin_year)

        # -------------------------------------------------------------
        # SHEET 5: RECEIPTS & VOUCHERS REGISTER
        # -------------------------------------------------------------
        cls._build_receipts_sheet(wb, customer, receipts, fin_year)

        # Save to buffer
        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream

    @classmethod
    def _build_summary_sheet(cls, wb, customer: Dict[str, Any], kpis: Dict[str, Any], fin_year: str):
        ws = wb.create_sheet(title="Dossier Summary")
        ws.views.sheetView[0].showGridLines = True

        # Company Header Banner
        ws.merge_cells("A1:H2")
        title_cell = ws["A1"]
        title_cell.value = "SCOTO ERP — CUSTOMER 360 FINANCIAL DOSSIER"
        title_cell.font = font_title
        title_cell.fill = fill_primary
        title_cell.alignment = align_center

        ws.merge_cells("A3:H3")
        sub_cell = ws["A3"]
        sub_cell.value = f"Systec Private Ltd  |  FY: {fin_year.replace('_', '-')}  |  Generated on: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
        sub_cell.font = font_subtitle
        sub_cell.fill = fill_navy
        sub_cell.alignment = align_center

        # Section: Customer Master KYC Profile
        ws.cell(row=5, column=1, value="CUSTOMER MASTER KYC & CONTACT INFORMATION").font = font_sec_header

        kyc_data = [
            ("Customer / Client Name:", customer.get("LedgerName") or "-", "Ledger Group:", customer.get("LedgerGrpName") or "Customer"),
            ("Ledger Code:", customer.get("LedgerCode") or "-", "Header Group:", customer.get("AccLedgerHeaderName") or "Domestic Customer"),
            ("GSTIN / Tax ID:", customer.get("GSTNo") or "Unregistered / N/A", "PAN Number:", customer.get("PanNo") or "-"),
            ("Contact Person:", customer.get("ContectName") or customer.get("ChequePrintName") or "-", "Mobile / Phone:", customer.get("MobileNo") or "-"),
            ("Email Address:", customer.get("MailID") or "-", "City & State:", f"{customer.get('City') or '-'}, {customer.get('State') or '-'}"),
            ("Registered Address:", f"{customer.get('Add1') or ''} {customer.get('Add2') or ''}".strip() or "-", "PIN Code:", customer.get("PinCode") or "-"),
        ]

        curr_row = 6
        for row_items in kyc_data:
            c1 = ws.cell(row=curr_row, column=1, value=row_items[0])
            c1.font = font_data_bold
            c1.fill = fill_zebra
            c1.border = border_cell

            c2 = ws.cell(row=curr_row, column=2, value=row_items[1])
            c2.font = font_data
            c2.border = border_cell
            ws.merge_cells(start_row=curr_row, start_column=2, end_row=curr_row, end_column=4)

            c3 = ws.cell(row=curr_row, column=5, value=row_items[2])
            c3.font = font_data_bold
            c3.fill = fill_zebra
            c3.border = border_cell

            c4 = ws.cell(row=curr_row, column=6, value=row_items[3])
            c4.font = font_data
            c4.border = border_cell
            ws.merge_cells(start_row=curr_row, start_column=6, end_row=curr_row, end_column=8)

            curr_row += 1

        # Section: Financial KPI Cards
        curr_row += 2
        ws.cell(row=curr_row, column=1, value="FINANCIAL OVERVIEW & RECEIVABLES SNAPSHOT").font = font_sec_header
        curr_row += 1

        kpi_cards = [
            ("TOTAL BILLED (INVOICED)", kpis.get("total_invoiced_amount", 0.0), NUM_CURRENCY, fill_blue, C_BLUE_TEXT),
            ("TOTAL COLLECTIONS / RECEIPTS", kpis.get("total_collections", kpis.get("total_tally_receipts_amount", 0.0)), NUM_CURRENCY, fill_green, C_GREEN_TEXT),
            ("NET BALANCE DUE (RECEIVABLE)", kpis.get("net_outstanding", kpis.get("total_balance_due", 0.0)), NUM_CURRENCY, fill_rose, C_ROSE_TEXT),
            ("RUNNING LEDGER BALANCE", kpis.get("closing_balance", 0.0), NUM_CURRENCY, fill_zebra, "0F172A"),
            ("TOTAL SALES INVOICES RAISED", kpis.get("total_sales_invoices_count", 0), NUM_QTY, fill_card, "0F172A"),
            ("FULLY PAID INVOICES", kpis.get("paid_invoices_count", 0), NUM_QTY, fill_green, C_GREEN_TEXT),
            ("PARTIALLY PAID INVOICES", kpis.get("partial_invoices_count", 0), NUM_QTY, fill_amber, C_AMBER_TEXT),
            ("PENDING / UNPAID INVOICES", kpis.get("pending_invoices_count", 0), NUM_QTY, fill_rose, C_ROSE_TEXT),
        ]

        # Draw 4 cards in Row 1, 4 cards in Row 2
        card_positions = [
            (curr_row, 1, 2), (curr_row, 3, 4), (curr_row, 5, 6), (curr_row, 7, 8),
            (curr_row + 3, 1, 2), (curr_row + 3, 3, 4), (curr_row + 5, 5, 6), (curr_row + 3, 7, 8),
        ]

        # Row A of cards (Financial Amounts)
        c_idx = 0
        for i in range(4):
            lbl, val, fmt, fill, text_color = kpi_cards[i]
            col_start = (i * 2) + 1
            col_end = col_start + 1

            ws.merge_cells(start_row=curr_row, start_column=col_start, end_row=curr_row, end_column=col_end)
            c_lbl = ws.cell(row=curr_row, column=col_start, value=lbl)
            c_lbl.font = Font(name=FONT_FAMILY, size=8, bold=True, color="64748B")
            c_lbl.fill = fill
            c_lbl.alignment = align_center

            ws.merge_cells(start_row=curr_row + 1, start_column=col_start, end_row=curr_row + 1, end_column=col_end)
            c_val = ws.cell(row=curr_row + 1, column=col_start, value=val)
            c_val.font = Font(name=FONT_FAMILY, size=14, bold=True, color=text_color)
            c_val.number_format = fmt
            c_val.fill = fill
            c_val.alignment = align_center

            # borders
            for r in (curr_row, curr_row + 1):
                for c in (col_start, col_end):
                    ws.cell(row=r, column=c).border = border_cell

        # Row B of cards (Counts)
        curr_row += 3
        for i in range(4, 8):
            lbl, val, fmt, fill, text_color = kpi_cards[i]
            col_start = ((i - 4) * 2) + 1
            col_end = col_start + 1

            ws.merge_cells(start_row=curr_row, start_column=col_start, end_row=curr_row, end_column=col_end)
            c_lbl = ws.cell(row=curr_row, column=col_start, value=lbl)
            c_lbl.font = Font(name=FONT_FAMILY, size=8, bold=True, color="64748B")
            c_lbl.fill = fill
            c_lbl.alignment = align_center

            ws.merge_cells(start_row=curr_row + 1, start_column=col_start, end_row=curr_row + 1, end_column=col_end)
            c_val = ws.cell(row=curr_row + 1, column=col_start, value=val)
            c_val.font = Font(name=FONT_FAMILY, size=14, bold=True, color=text_color)
            c_val.number_format = fmt
            c_val.fill = fill
            c_val.alignment = align_center

            for r in (curr_row, curr_row + 1):
                for c in (col_start, col_end):
                    ws.cell(row=r, column=c).border = border_cell

        _auto_adjust_columns(ws)

    @classmethod
    def _build_invoices_sheet(cls, wb, customer: Dict[str, Any], invoices: List[Dict[str, Any]], fin_year: str):
        ws = wb.create_sheet(title="Invoices & Settlements")
        ws.views.sheetView[0].showGridLines = True

        # Header Title
        ws.merge_cells("A1:K1")
        h = ws["A1"]
        h.value = f"SALES INVOICES & PAYMENT SETTLEMENT REGISTER — {customer.get('LedgerName', '')}"
        h.font = Font(name=FONT_FAMILY, size=12, bold=True, color="FFFFFF")
        h.fill = fill_navy
        h.alignment = align_center

        headers = [
            "Sl", "Invoice No", "Invoice Date", "Order / PI Ref", "Total Qty",
            "Billed Amount (₹)", "Amount Paid (₹)", "Balance Due (₹)",
            "Status", "Overdue Days", "Matched Payment Receipts"
        ]

        curr_row = 3
        for col_idx, text in enumerate(headers, start=1):
            cell = ws.cell(row=curr_row, column=col_idx, value=text)
            cell.font = font_tbl_header
            cell.fill = fill_tbl_header
            cell.alignment = align_center if col_idx in (1, 3, 9, 10) else (align_right if col_idx in (5, 6, 7, 8) else align_left)
            cell.border = border_cell

        start_data_row = curr_row + 1
        curr_row += 1

        tot_billed = 0.0
        tot_paid = 0.0
        tot_balance = 0.0

        for idx, inv in enumerate(invoices, start=1):
            billed = float(inv.get("net_amount_float") or inv.get("NetAmount") or 0.0)
            paid = float(inv.get("amount_paid") or 0.0)
            bal = float(inv.get("balance_due") or 0.0)
            raw_status = str(inv.get("payment_status") or "").upper()
            if bal <= 0.01 and (paid > 0.01 or billed == 0):
                status = "PAID"
            elif paid > 0.01 and bal > 0.01:
                status = "PARTIAL"
            elif raw_status == "PENDING_APPROVAL":
                status = "PENDING APPROVAL"
            else:
                status = "UNPAID"

            tot_billed += billed
            tot_paid += paid
            tot_balance += bal

            # Matched receipts string
            m_receipts = inv.get("matched_receipts") or []
            m_str = ", ".join([f"{r.get('voucher_no')} (₹{float(r.get('allocated_amount', 0)):,.2f})" for r in m_receipts]) if m_receipts else "-"

            row_data = [
                (idx, align_center, None),
                (inv.get("TransNo") or inv.get("InvoiceNo"), align_left, font_mono_bold),
                (inv.get("InvoiceDate") or inv.get("TransDate") or "-", align_center, None),
                (inv.get("InvoiceNo") or "-", align_left, font_mono),
                (inv.get("TotalQty") or 0, align_right, NUM_QTY),
                (billed, align_right, NUM_CURRENCY),
                (paid, align_right, NUM_CURRENCY),
                (bal, align_right, NUM_CURRENCY),
                (status, align_center, None),
                (inv.get("days_overdue") or 0, align_center, NUM_QTY),
                (m_str, align_left, None),
            ]

            fill_row = fill_zebra if idx % 2 == 0 else PatternFill(fill_type=None)

            for col_idx, (val, aln, fmt) in enumerate(row_data, start=1):
                cell = ws.cell(row=curr_row, column=col_idx, value=val)
                cell.font = fmt if isinstance(fmt, Font) else font_data
                cell.alignment = aln
                cell.fill = fill_row
                cell.border = border_cell
                if fmt in (NUM_CURRENCY, NUM_QTY):
                    cell.number_format = fmt

                # Status color highlight
                if col_idx == 9:
                    if status == "PAID":
                        cell.fill = fill_green
                        cell.font = Font(name=FONT_FAMILY, size=9, bold=True, color=C_GREEN_TEXT)
                    elif status == "PARTIAL":
                        cell.fill = fill_amber
                        cell.font = Font(name=FONT_FAMILY, size=9, bold=True, color=C_AMBER_TEXT)
                    else:
                        cell.fill = fill_rose
                        cell.font = Font(name=FONT_FAMILY, size=9, bold=True, color=C_ROSE_TEXT)

            curr_row += 1

        # Total Row
        if invoices:
            ws.cell(row=curr_row, column=1, value="").border = border_total
            ws.cell(row=curr_row, column=2, value="TOTAL SUMMARY").font = font_data_bold
            ws.cell(row=curr_row, column=2).fill = fill_total
            ws.cell(row=curr_row, column=2).border = border_total

            for c in range(3, 6):
                cell = ws.cell(row=curr_row, column=c, value="")
                cell.fill = fill_total
                cell.border = border_total

            c6 = ws.cell(row=curr_row, column=6, value=f"=SUM(F{start_data_row}:F{curr_row-1})")
            c6.font = font_data_bold
            c6.number_format = NUM_CURRENCY
            c6.fill = fill_total
            c6.border = border_total
            c6.alignment = align_right

            c7 = ws.cell(row=curr_row, column=7, value=f"=SUM(G{start_data_row}:G{curr_row-1})")
            c7.font = font_data_bold
            c7.number_format = NUM_CURRENCY
            c7.fill = fill_total
            c7.border = border_total
            c7.alignment = align_right

            c8 = ws.cell(row=curr_row, column=8, value=f"=SUM(H{start_data_row}:H{curr_row-1})")
            c8.font = font_data_bold
            c8.number_format = NUM_CURRENCY
            c8.fill = fill_total
            c8.border = border_total
            c8.alignment = align_right

            for c in range(9, 12):
                cell = ws.cell(row=curr_row, column=c, value="")
                cell.fill = fill_total
                cell.border = border_total

        _auto_adjust_columns(ws)

    @classmethod
    def _build_milestones_sheet(cls, wb, customer: Dict[str, Any], milestones: List[Dict[str, Any]], fin_year: str):
        ws = wb.create_sheet(title="Advance Milestones")
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:I1")
        h = ws["A1"]
        h.value = f"QUOTATIONS & PROFORMA ADVANCE MILESTONE TRACKER — {customer.get('LedgerName', '')}"
        h.font = Font(name=FONT_FAMILY, size=12, bold=True, color="FFFFFF")
        h.fill = fill_navy
        h.alignment = align_center

        headers = [
            "Sl", "Proforma No", "Proforma Date", "Quotation Ref", "Total Order Value (₹)",
            "Advance Collected (₹)", "Advance Achieved %", "Milestone Status", "Linked Sales Invoice No"
        ]

        curr_row = 3
        for col_idx, text in enumerate(headers, start=1):
            cell = ws.cell(row=curr_row, column=col_idx, value=text)
            cell.font = font_tbl_header
            cell.fill = fill_tbl_header
            cell.alignment = align_center if col_idx in (1, 3, 7, 8) else (align_right if col_idx in (5, 6) else align_left)
            cell.border = border_cell

        curr_row += 1
        for idx, m in enumerate(milestones, start=1):
            pct = float(m.get("advance_percentage_achieved") or 0.0)
            status = str(m.get("status") or "Active")

            row_data = [
                (idx, align_center, None),
                (m.get("proforma_no") or "-", align_left, font_mono_bold),
                (m.get("proforma_date") or "-", align_center, None),
                (m.get("quotation_no") or "-", align_left, font_mono),
                (float(m.get("total_order_value") or 0.0), align_right, NUM_CURRENCY),
                (float(m.get("advance_collected") or 0.0), align_right, NUM_CURRENCY),
                (f"{pct:.1f}%", align_center, None),
                (status, align_center, None),
                (m.get("sales_invoice_no") or "Pending Dispatch", align_left, font_mono),
            ]

            fill_row = fill_zebra if idx % 2 == 0 else PatternFill(fill_type=None)

            for col_idx, (val, aln, fmt) in enumerate(row_data, start=1):
                cell = ws.cell(row=curr_row, column=col_idx, value=val)
                cell.font = fmt if isinstance(fmt, Font) else font_data
                cell.alignment = aln
                cell.fill = fill_row
                cell.border = border_cell
                if fmt == NUM_CURRENCY:
                    cell.number_format = NUM_CURRENCY

                if col_idx == 8:
                    status_lower = status.lower()
                    if "cleared" in status_lower or "completed" in status_lower or "fully" in status_lower:
                        cell.fill = fill_green
                        cell.font = Font(name=FONT_FAMILY, size=9, bold=True, color=C_GREEN_TEXT)
                    elif "partial" in status_lower:
                        cell.fill = fill_amber
                        cell.font = Font(name=FONT_FAMILY, size=9, bold=True, color=C_AMBER_TEXT)

            curr_row += 1

        _auto_adjust_columns(ws)

    @classmethod
    def _build_ledger_sheet(cls, wb, customer: Dict[str, Any], ledger: List[Dict[str, Any]], fin_year: str):
        ws = wb.create_sheet(title="Statement of Account")
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:G1")
        h = ws["A1"]
        h.value = f"STATEMENT OF ACCOUNT / RUNNING LEDGER — {customer.get('LedgerName', '')}"
        h.font = Font(name=FONT_FAMILY, size=12, bold=True, color="FFFFFF")
        h.fill = fill_navy
        h.alignment = align_center

        headers = [
            "Date", "Particulars / Narration", "Voucher Type", "Voucher No",
            "Debit Amount (₹)", "Credit Amount (₹)", "Running Balance (₹)"
        ]

        curr_row = 3
        for col_idx, text in enumerate(headers, start=1):
            cell = ws.cell(row=curr_row, column=col_idx, value=text)
            cell.font = font_tbl_header
            cell.fill = fill_tbl_header
            cell.alignment = align_center if col_idx in (1, 3) else (align_right if col_idx in (5, 6, 7) else align_left)
            cell.border = border_cell

        curr_row += 1
        for idx, entry in enumerate(ledger, start=1):
            dr = float(entry.get("debit") or 0.0)
            cr = float(entry.get("credit") or 0.0)
            bal = float(entry.get("running_balance") or 0.0)
            bal_str = f"₹{abs(bal):,.2f} {'Dr' if bal >= 0 else 'Cr'}"

            row_data = [
                (entry.get("entry_date") or "-", align_center, None),
                (entry.get("particulars") or "-", align_left, None),
                (entry.get("voucher_type") or "-", align_center, None),
                (entry.get("voucher_no") or "-", align_left, font_mono),
                (dr if dr > 0 else "-", align_right, NUM_CURRENCY if dr > 0 else None),
                (cr if cr > 0 else "-", align_right, NUM_CURRENCY if cr > 0 else None),
                (bal_str, align_right, font_data_bold),
            ]

            fill_row = fill_zebra if idx % 2 == 0 else PatternFill(fill_type=None)

            for col_idx, (val, aln, fmt) in enumerate(row_data, start=1):
                cell = ws.cell(row=curr_row, column=col_idx, value=val)
                cell.font = fmt if isinstance(fmt, Font) else font_data
                cell.alignment = aln
                cell.fill = fill_row
                cell.border = border_cell
                if fmt == NUM_CURRENCY:
                    cell.number_format = NUM_CURRENCY
                    if col_idx == 5:
                        cell.font = Font(name=FONT_FAMILY, size=10, bold=True, color=C_ROSE_TEXT)
                    elif col_idx == 6:
                        cell.font = Font(name=FONT_FAMILY, size=10, bold=True, color=C_GREEN_TEXT)

            curr_row += 1

        _auto_adjust_columns(ws)

    @classmethod
    def _build_receipts_sheet(cls, wb, customer: Dict[str, Any], receipts: List[Dict[str, Any]], fin_year: str):
        ws = wb.create_sheet(title="Receipts & Vouchers")
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:I1")
        h = ws["A1"]
        h.value = f"RECEIPTS & COLLECTIONS REGISTER — {customer.get('LedgerName', '')}"
        h.font = Font(name=FONT_FAMILY, size=12, bold=True, color="FFFFFF")
        h.fill = fill_navy
        h.alignment = align_center

        headers = [
            "Sl", "Voucher No", "Date", "Voucher Type", "Account Head / Ledger",
            "Debit / Charge (₹)", "Credit / Received (₹)", "FY", "Narration / Reference"
        ]

        curr_row = 3
        for col_idx, text in enumerate(headers, start=1):
            cell = ws.cell(row=curr_row, column=col_idx, value=text)
            cell.font = font_tbl_header
            cell.fill = fill_tbl_header
            cell.alignment = align_center if col_idx in (1, 3, 4, 8) else (align_right if col_idx in (6, 7) else align_left)
            cell.border = border_cell

        curr_row += 1
        for idx, r in enumerate(receipts, start=1):
            dr = float(r.get("DebitAmount") or 0.0)
            cr = float(r.get("CreditAmount") or 0.0)

            row_data = [
                (idx, align_center, None),
                (r.get("TransNo") or "-", align_left, font_mono_bold),
                (r.get("TransDate") or "-", align_center, None),
                (r.get("TransType") or "Receipt", align_center, None),
                (r.get("AccHeadName") or r.get("LedgerName") or "-", align_left, None),
                (dr if dr > 0 else "-", align_right, NUM_CURRENCY if dr > 0 else None),
                (cr if cr > 0 else "-", align_right, NUM_CURRENCY if cr > 0 else None),
                (str(r.get("FinYearVal") or r.get("fin_year") or "-").strip().replace("_", "-"), align_center, None),
                (r.get("Narration") or "-", align_left, None),
            ]

            fill_row = fill_zebra if idx % 2 == 0 else PatternFill(fill_type=None)

            for col_idx, (val, aln, fmt) in enumerate(row_data, start=1):
                cell = ws.cell(row=curr_row, column=col_idx, value=val)
                cell.font = fmt if isinstance(fmt, Font) else font_data
                cell.alignment = aln
                cell.fill = fill_row
                cell.border = border_cell
                if fmt == NUM_CURRENCY:
                    cell.number_format = NUM_CURRENCY
                    if col_idx == 7:
                        cell.font = Font(name=FONT_FAMILY, size=10, bold=True, color=C_GREEN_TEXT)

            curr_row += 1

        _auto_adjust_columns(ws)
