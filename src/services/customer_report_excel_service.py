"""
Executive Customer Report & Ledger Dossier Excel Service.
Generates two clean, compact, beautifully formatted Scoto ERP accounting sheets:
  1. Statement of Account: Detailed invoice & receipt ledger with clear GST & TDS breakdown.
  2. Executive Summary: High-level KPI cards and invoice-by-invoice settlement matrix.

Both sheets feature a standardized Dual Header:
  - Left: Service Provider (Scoto Systec Private Limited)
  - Right: Customer Profile & KYC Details
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
# CORPORATE STYLING & COLOR PALETTE
# =============================================================================
C_PRIMARY = "6F2C8F"       # Scoto Signature Purple
C_NAVY = "0F172A"          # Deep Slate / Dark Navy
C_HEADER_FILL = "1E293B"   # Table Header Dark
C_ZEBRA_FILL = "F8FAFC"    # Soft Gray Alternating Row
C_CARD_BG = "F1F5F9"       # KPI Card Fill
C_BORDER = "CBD5E1"        # Soft Gray Border
C_BORDER_DARK = "334155"   # Contrast Border
C_WHITE = "FFFFFF"

# Status colors
C_GREEN_BG = "DCFCE7"
C_GREEN_TEXT = "15803D"
C_AMBER_BG = "FEF3C7"
C_AMBER_TEXT = "B45309"
C_ROSE_BG = "FEE2E2"
C_ROSE_TEXT = "B91C1C"
C_BLUE_BG = "EFF6FF"
C_BLUE_TEXT = "1D4ED8"

# Fonts (Slightly larger, clear and readable)
FONT_FAMILY = "Calibri"
font_title = Font(name=FONT_FAMILY, size=15.5, bold=True, color="FFFFFF")
font_subtitle = Font(name=FONT_FAMILY, size=10.5, italic=True, color="E2E8F0")
font_box_header = Font(name=FONT_FAMILY, size=11, bold=True, color="FFFFFF")
font_box_title = Font(name=FONT_FAMILY, size=11.5, bold=True, color="0F172A")
font_box_body = Font(name=FONT_FAMILY, size=10, color="334155")
font_box_bold = Font(name=FONT_FAMILY, size=10, bold=True, color="0F172A")

font_sec_header = Font(name=FONT_FAMILY, size=11.5, bold=True, color="0F172A")
font_tbl_header = Font(name=FONT_FAMILY, size=10.5, bold=True, color="FFFFFF")
font_data = Font(name=FONT_FAMILY, size=10, color="0F172A")
font_data_bold = Font(name=FONT_FAMILY, size=10, bold=True, color="0F172A")
font_mono = Font(name="Consolas", size=9.5, color="1E293B")
font_mono_bold = Font(name="Consolas", size=9.5, bold=True, color="0F172A")

# Fills
fill_primary = PatternFill(start_color=C_PRIMARY, end_color=C_PRIMARY, fill_type="solid")
fill_navy = PatternFill(start_color=C_NAVY, end_color=C_NAVY, fill_type="solid")
fill_header = PatternFill(start_color=C_HEADER_FILL, end_color=C_HEADER_FILL, fill_type="solid")
fill_zebra = PatternFill(start_color=C_ZEBRA_FILL, end_color=C_ZEBRA_FILL, fill_type="solid")
fill_card = PatternFill(start_color=C_CARD_BG, end_color=C_CARD_BG, fill_type="solid")
fill_total = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

fill_green = PatternFill(start_color=C_GREEN_BG, end_color=C_GREEN_BG, fill_type="solid")
fill_amber = PatternFill(start_color=C_AMBER_BG, end_color=C_AMBER_BG, fill_type="solid")
fill_rose = PatternFill(start_color=C_ROSE_BG, end_color=C_ROSE_BG, fill_type="solid")
fill_blue = PatternFill(start_color=C_BLUE_BG, end_color=C_BLUE_BG, fill_type="solid")

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

# Number formats
NUM_CURRENCY = "#,##0.00"
NUM_QTY = "#,##0"


def _apply_compact_page_setup(ws, orientation="landscape"):
    """Configures tight, compact page layout and margins to fit on standard page."""
    ws.views.sheetView[0].showGridLines = True
    ws.page_setup.orientation = orientation
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_margins.left = 0.3
    ws.page_margins.right = 0.3
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.5


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
        Generates an Executive Customer Dossier Excel workbook strictly containing TWO sheets:
          1. Statement of Account (Detailed Ledger of Invoices & Receipts with GST & TDS)
          2. Executive Summary (KPI Snapshot & Invoice Settlement Matrix)
        """
        dossier = CustomerReportService.get_customer_dossier(db, client_code=client_code, fin_year=fin_year)
        customer = dossier.get("customer_info", {})
        kpis = dossier.get("kpis", {})
        invoices_breakdown = dossier.get("invoices_breakdown", [])
        running_ledger = dossier.get("running_ledger", [])
        fy_display = dossier.get("selected_fin_year") or fin_year or "ALL"

        wb = openpyxl.Workbook()

        # Sheet 1: Statement of Account
        ws1 = wb.active
        ws1.title = "Statement of Account"
        cls._build_statement_of_account_sheet(ws1, customer=customer, kpis=kpis, ledger=running_ledger, fin_year=fy_display)

        # Sheet 2: Executive Summary
        ws2 = wb.create_sheet(title="Executive Summary")
        cls._build_executive_summary_sheet(ws2, customer=customer, kpis=kpis, invoices=invoices_breakdown, fin_year=fy_display)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    # =========================================================================
    # DUAL HEADER BUILDER (Our Company Left, Customer KYC Right)
    # =========================================================================
    @classmethod
    def _render_dual_header(
        cls,
        ws,
        customer: Dict[str, Any],
        title_text: str,
        subtitle_text: str,
        max_col: int = 14,
    ) -> int:
        """
        Renders standardized Top Title Banner and Dual Header Box:
          - Banner: Rows 1-2
          - Dual Box: Rows 4-10
            - Left (Cols 1 to half): Our Company Profile
            - Right (Cols half+1 to max_col): Customer Profile & KYC
        Returns the next available row index.
        """
        _apply_compact_page_setup(ws, orientation="landscape")

        # 1. Title Banner (Rows 1-2)
        end_col_letter = get_column_letter(max_col)
        ws.merge_cells(f"A1:{end_col_letter}1")
        ws.merge_cells(f"A2:{end_col_letter}2")

        c1 = ws["A1"]
        c1.value = title_text.upper()
        c1.font = font_title
        c1.fill = fill_primary
        c1.alignment = align_center
        ws.row_dimensions[1].height = 24

        c2 = ws["A2"]
        c2.value = subtitle_text
        c2.font = font_subtitle
        c2.fill = fill_primary
        c2.alignment = align_center
        ws.row_dimensions[2].height = 16

        # 2. Dual Header Box (Rows 4 to 10)
        mid_col = max_col // 2
        col_left_end = get_column_letter(mid_col)
        col_right_start = get_column_letter(mid_col + 1)
        col_right_end = end_col_letter

        # Header titles
        ws.merge_cells(f"A4:{col_left_end}4")
        h_left = ws["A4"]
        h_left.value = "SERVICE PROVIDER / ISSUING COMPANY"
        h_left.font = font_box_header
        h_left.fill = fill_header
        h_left.alignment = align_left

        ws.merge_cells(f"{col_right_start}4:{col_right_end}4")
        h_right = ws[f"{col_right_start}4"]
        h_right.value = "CUSTOMER / BILLED TO"
        h_right.font = font_box_header
        h_right.fill = fill_header
        h_right.alignment = align_left
        ws.row_dimensions[4].height = 18

        # Company details (Left)
        company_rows = [
            ("Company Name:", "SCOTO SYSTEC PRIVATE LIMITED", font_box_bold),
            ("Registered Office:", "No: 61-A, First Floor, HM Enclave, 50 Feet Road,", font_box_body),
            ("City & State:", "Ramanathapuram, Coimbatore - 641045, Tamil Nadu, India", font_box_body),
            ("Tax Identifiers:", "GSTIN: 33AAVCS5957L1ZF | PAN: AAVCS5957L", font_box_bold),
            ("Contact Details:", "Phone: +91 422 4355555 | Email: accounts@scoto.in", font_box_body),
            ("Web / Portal:", "ERP Portal: https://erp.scoto.in | Web: www.scoto.in", font_box_body),
        ]

        # Customer details (Right)
        c_name = customer.get("LedgerName") or customer.get("CustomerName") or "-"
        c_code = customer.get("LedgerCode") or customer.get("CustomerCode") or "-"
        c_gst = customer.get("GSTNo") or "-"
        c_pan = customer.get("PanNo") or "-"
        c_contact = customer.get("ContectName") or "-"
        c_phone = customer.get("MobileNo") or "-"
        c_email = customer.get("MailID") or "-"

        add1 = (customer.get("Add1") or "").strip()
        add2 = (customer.get("Add2") or "").strip()
        city = (customer.get("City") or "").strip()
        state = (customer.get("State") or "").strip()
        pincode = str(customer.get("PinCode") or "").strip()

        addr_line = ", ".join(p for p in (add1, add2) if p) or "-"
        city_line = ", ".join(p for p in (city, state) if p)
        if pincode:
            city_line = f"{city_line} - {pincode}" if city_line else f"PIN: {pincode}"
        if not city_line:
            city_line = "-"

        customer_rows = [
            ("Client Name:", f"{c_name} ({c_code})", font_box_bold),
            ("Address:", addr_line, font_box_body),
            ("City / State:", city_line, font_box_body),
            ("Tax Identifiers:", f"GSTIN: {c_gst} | PAN: {c_pan}", font_box_bold),
            ("Contact Person:", f"{c_contact} | Phone: {c_phone}", font_box_body),
            ("Email Address:", f"{c_email}", font_box_body),
        ]

        # Fill dual box rows (5 to 10) - tight row heights
        for idx in range(6):
            r = 5 + idx
            ws.row_dimensions[r].height = 15.5

            # Left side
            lbl_l, val_l, fnt_l = company_rows[idx]
            cell_lbl_l = ws.cell(row=r, column=1, value=lbl_l)
            cell_lbl_l.font = font_box_bold
            cell_lbl_l.fill = fill_zebra
            cell_lbl_l.alignment = align_left
            cell_lbl_l.border = border_cell

            ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=mid_col)
            cell_val_l = ws.cell(row=r, column=2, value=val_l)
            cell_val_l.font = fnt_l
            cell_val_l.alignment = align_left
            cell_val_l.border = border_cell

            # Right side
            lbl_r, val_r, fnt_r = customer_rows[idx]
            col_r_lbl = mid_col + 1
            col_r_val = mid_col + 2

            cell_lbl_r = ws.cell(row=r, column=col_r_lbl, value=lbl_r)
            cell_lbl_r.font = font_box_bold
            cell_lbl_r.fill = fill_zebra
            cell_lbl_r.alignment = align_left
            cell_lbl_r.border = border_cell

            ws.merge_cells(start_row=r, start_column=col_r_val, end_row=r, end_column=max_col)
            cell_val_r = ws.cell(row=r, column=col_r_val, value=val_r)
            cell_val_r.font = fnt_r
            cell_val_r.alignment = align_left
            cell_val_r.border = border_cell

        return 12  # Next section row

    # =========================================================================
    # SHEET 1: STATEMENT OF ACCOUNT (Detailed Ledger with GST & TDS breakdown)
    # =========================================================================
    @classmethod
    def _build_statement_of_account_sheet(
        cls,
        ws,
        customer: Dict[str, Any],
        kpis: Dict[str, Any],
        ledger: List[Dict[str, Any]],
        fin_year: str,
    ):
        """Builds Sheet 1: Detailed Statement of Account with 14 compact columns."""
        subtitle = f"Financial Period: FY {fin_year} | Statement Generated On: {datetime.now().strftime('%d-%b-%Y %I:%M %p')}"
        next_row = cls._render_dual_header(
            ws,
            customer=customer,
            title_text="STATEMENT OF ACCOUNT / CUSTOMER DOSSIER",
            subtitle_text=subtitle,
            max_col=14,
        )

        # Section Header
        sec_cell = ws.cell(row=next_row, column=1, value="DETAILED SALES INVOICES & PAYMENT RECEIPTS LEDGER")
        sec_cell.font = font_sec_header
        ws.row_dimensions[next_row].height = 19
        next_row += 1

        headers = [
            ("Date", align_center),
            ("Voucher Type", align_center),
            ("Doc / Ref No", align_center),
            ("Particulars / Narration", align_left),
            ("Taxable (₹)", align_right),
            ("CGST (₹)", align_right),
            ("SGST (₹)", align_right),
            ("IGST (₹)", align_right),
            ("Total GST (₹)", align_right),
            ("Invoice (Debit ₹)", align_right),
            ("TDS (₹)", align_right),
            ("Bank / Cash (₹)", align_right),
            ("Settled (Credit ₹)", align_right),
            ("Running Balance (₹)", align_right),
        ]

        ws.row_dimensions[next_row].height = 22
        for col_idx, (hdr_text, aln) in enumerate(headers, start=1):
            cell = ws.cell(row=next_row, column=col_idx, value=hdr_text)
            cell.font = font_tbl_header
            cell.fill = fill_header
            cell.alignment = aln
            cell.border = border_cell

        curr_row = next_row + 1

        # Totals accumulators
        tot_taxable = 0.0
        tot_cgst = 0.0
        tot_sgst = 0.0
        tot_igst = 0.0
        tot_gst = 0.0
        tot_debit = 0.0
        tot_tds = 0.0
        tot_net_received = 0.0
        tot_credit = 0.0
        last_balance = 0.0

        for idx, entry in enumerate(ledger, start=1):
            ws.row_dimensions[curr_row].height = 18.5
            v_type = entry.get("voucher_type") or "General Ledger"
            taxable = float(entry.get("taxable_amt") or 0.0)
            cgst = float(entry.get("cgst_amt") or 0.0)
            sgst = float(entry.get("sgst_amt") or 0.0)
            igst = float(entry.get("igst_amt") or 0.0)
            total_gst = float(entry.get("total_gst") or 0.0)
            debit = float(entry.get("debit") or 0.0)
            tds = float(entry.get("tds_amt") or 0.0)
            net_rcvd = float(entry.get("net_received") or 0.0)
            credit = float(entry.get("credit") or 0.0)
            bal = float(entry.get("running_balance") or 0.0)
            last_balance = bal

            tot_taxable += taxable
            tot_cgst += cgst
            tot_sgst += sgst
            tot_igst += igst
            tot_gst += total_gst
            tot_debit += debit
            tot_tds += tds
            tot_net_received += net_rcvd
            tot_credit += credit

            bal_str = f"₹{abs(bal):,.2f} {'Dr' if bal >= 0 else 'Cr'}"
            fill_row = fill_zebra if idx % 2 == 0 else PatternFill(fill_type=None)

            row_data = [
                (entry.get("entry_date") or "-", align_center, font_data, None),
                (v_type, align_center, font_data, None),
                (entry.get("voucher_no") or "-", align_center, font_mono_bold, None),
                (entry.get("particulars") or "-", align_left, font_data, None),
                (taxable if taxable > 0 else "-", align_right, font_data, NUM_CURRENCY if taxable > 0 else None),
                (cgst if cgst > 0 else "-", align_right, font_data, NUM_CURRENCY if cgst > 0 else None),
                (sgst if sgst > 0 else "-", align_right, font_data, NUM_CURRENCY if sgst > 0 else None),
                (igst if igst > 0 else "-", align_right, font_data, NUM_CURRENCY if igst > 0 else None),
                (total_gst if total_gst > 0 else "-", align_right, font_data, NUM_CURRENCY if total_gst > 0 else None),
                (debit if debit > 0 else "-", align_right, Font(name=FONT_FAMILY, size=10, bold=True, color=C_ROSE_TEXT), NUM_CURRENCY if debit > 0 else None),
                (tds if tds > 0 else "-", align_right, Font(name=FONT_FAMILY, size=10, bold=True, color=C_AMBER_TEXT), NUM_CURRENCY if tds > 0 else None),
                (net_rcvd if net_rcvd > 0 else "-", align_right, Font(name=FONT_FAMILY, size=10, bold=True, color=C_GREEN_TEXT), NUM_CURRENCY if net_rcvd > 0 else None),
                (credit if credit > 0 else "-", align_right, Font(name=FONT_FAMILY, size=10, bold=True, color=C_GREEN_TEXT), NUM_CURRENCY if credit > 0 else None),
                (bal_str, align_right, font_data_bold, None),
            ]

            for col_idx, (val, aln, fnt, fmt) in enumerate(row_data, start=1):
                cell = ws.cell(row=curr_row, column=col_idx, value=val)
                cell.alignment = aln
                cell.font = fnt
                cell.fill = fill_row
                cell.border = border_cell
                if fmt:
                    cell.number_format = fmt

            curr_row += 1

        # Summary / Totals Row
        ws.row_dimensions[curr_row].height = 21
        ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=4)
        tot_label = ws.cell(row=curr_row, column=1, value="TOTALS & CLOSING RUNNING BALANCE")
        tot_label.font = font_tbl_header
        tot_label.fill = fill_header
        tot_label.alignment = align_center

        total_values = [
            (5, tot_taxable),
            (6, tot_cgst),
            (7, tot_sgst),
            (8, tot_igst),
            (9, tot_gst),
            (10, tot_debit),
            (11, tot_tds),
            (12, tot_net_received),
            (13, tot_credit),
        ]

        for col_idx, val in total_values:
            cell = ws.cell(row=curr_row, column=col_idx, value=val)
            cell.font = font_tbl_header
            cell.fill = fill_header
            cell.alignment = align_right
            cell.number_format = NUM_CURRENCY
            cell.border = border_total

        # Final Balance cell
        bal_final_str = f"₹{abs(last_balance):,.2f} {'Dr' if last_balance >= 0 else 'Cr'}"
        c_bal = ws.cell(row=curr_row, column=14, value=bal_final_str)
        c_bal.font = font_tbl_header
        c_bal.fill = fill_header
        c_bal.alignment = align_right
        c_bal.border = border_total

        # Tailored compact column widths for Sheet 1
        compact_widths_s1 = {
            "A": 11,   # Date
            "B": 13,   # Voucher Type
            "C": 14,   # Doc / Ref No
            "D": 25,   # Particulars
            "E": 13,   # Taxable
            "F": 10,   # CGST
            "G": 10,   # SGST
            "H": 10,   # IGST
            "I": 12,   # Total GST
            "J": 14,   # Invoice Debit
            "K": 11,   # TDS
            "L": 13,   # Bank / Cash
            "M": 14,   # Total Settled
            "N": 15,   # Running Balance
        }
        for col_l, w in compact_widths_s1.items():
            ws.column_dimensions[col_l].width = w

    # =========================================================================
    # SHEET 2: EXECUTIVE SUMMARY (KPIs + Invoice Settlement Matrix)
    # =========================================================================
    @classmethod
    def _build_executive_summary_sheet(
        cls,
        ws,
        customer: Dict[str, Any],
        kpis: Dict[str, Any],
        invoices: List[Dict[str, Any]],
        fin_year: str,
    ):
        """Builds Sheet 2: Executive 1-page summary with KPI cards and Invoice Matrix."""
        subtitle = f"Financial Period: FY {fin_year} | Executive Status Snapshot as of {datetime.now().strftime('%d-%b-%Y')}"
        next_row = cls._render_dual_header(
            ws,
            customer=customer,
            title_text="EXECUTIVE INVOICE SETTLEMENT & RECEIVABLES SUMMARY",
            subtitle_text=subtitle,
            max_col=11,
        )

        # Section: KPI Summary Cards
        ws.cell(row=next_row, column=1, value="FINANCIAL RECEIVABLES & COLLECTION SNAPSHOT").font = font_sec_header
        ws.row_dimensions[next_row].height = 19
        next_row += 1

        tot_invoiced = float(kpis.get("total_invoiced_amount") or 0.0)
        tot_collections = float(kpis.get("total_collections") or kpis.get("total_receipts_amount") or 0.0)
        net_outstanding = float(kpis.get("net_outstanding") or kpis.get("total_balance_due") or 0.0)

        tot_gst_all = sum(
            float(inv.get("TotalCGSTAmount") or 0.0) +
            float(inv.get("TotalSGSTAmount") or 0.0) +
            float(inv.get("TotalIGSTAmount") or 0.0)
            for inv in invoices
        )
        tot_tds_all = sum(
            sum(float(r.get("tds_amount") or 0.0) for r in inv.get("matched_receipts", []))
            for inv in invoices
        )

        kpi_cards = [
            ("TOTAL INVOICED / BILLED", tot_invoiced, NUM_CURRENCY, fill_blue, C_BLUE_TEXT),
            ("TOTAL GST CHARGED", tot_gst_all, NUM_CURRENCY, fill_card, "0F172A"),
            ("TDS WITHHELD BY CLIENT", tot_tds_all, NUM_CURRENCY, fill_amber, C_AMBER_TEXT),
            ("NET CASH / BANK COLLECTED", tot_collections, NUM_CURRENCY, fill_green, C_GREEN_TEXT),
            ("NET OUTSTANDING BALANCE", net_outstanding, NUM_CURRENCY, fill_rose, C_ROSE_TEXT),
        ]

        card_col_spans = [
            (1, 2),
            (3, 4),
            (5, 6),
            (7, 8),
            (9, 11),
        ]

        ws.row_dimensions[next_row].height = 16
        ws.row_dimensions[next_row + 1].height = 21

        for idx, (label, val, fmt, fill, color) in enumerate(kpi_cards):
            c_start, c_end = card_col_spans[idx]
            ws.merge_cells(start_row=next_row, start_column=c_start, end_row=next_row, end_column=c_end)
            c_lbl = ws.cell(row=next_row, column=c_start, value=label)
            c_lbl.font = Font(name=FONT_FAMILY, size=8.5, bold=True, color="475569")
            c_lbl.fill = fill
            c_lbl.alignment = align_center
            c_lbl.border = border_cell

            ws.merge_cells(start_row=next_row + 1, start_column=c_start, end_row=next_row + 1, end_column=c_end)
            c_val = ws.cell(row=next_row + 1, column=c_start, value=val)
            c_val.font = Font(name=FONT_FAMILY, size=11.5, bold=True, color=color)
            c_val.fill = fill
            c_val.alignment = align_center
            c_val.number_format = fmt
            c_val.border = border_cell

        next_row += 3

        # Section: Invoice Settlement Matrix
        ws.cell(row=next_row, column=1, value="SALES INVOICE SETTLEMENT MATRIX (INVOICE-BY-INVOICE)").font = font_sec_header
        ws.row_dimensions[next_row].height = 19
        next_row += 1

        headers = [
            ("Invoice No", align_center),
            ("Invoice Date", align_center),
            ("Fin Year", align_center),
            ("Taxable Value (₹)", align_right),
            ("GST Amount (₹)", align_right),
            ("Total Invoice (₹)", align_right),
            ("Cash / Bank (₹)", align_right),
            ("TDS (₹)", align_right),
            ("Total Settled (₹)", align_right),
            ("Balance Due (₹)", align_right),
            ("Payment Status", align_center),
        ]

        ws.row_dimensions[next_row].height = 22
        for col_idx, (hdr_text, aln) in enumerate(headers, start=1):
            cell = ws.cell(row=next_row, column=col_idx, value=hdr_text)
            cell.font = font_tbl_header
            cell.fill = fill_header
            cell.alignment = aln
            cell.border = border_cell

        curr_row = next_row + 1

        tot_matrix_taxable = 0.0
        tot_matrix_gst = 0.0
        tot_matrix_inv = 0.0
        tot_matrix_cash = 0.0
        tot_matrix_tds = 0.0
        tot_matrix_settled = 0.0
        tot_matrix_due = 0.0

        for idx, inv in enumerate(invoices, start=1):
            ws.row_dimensions[curr_row].height = 18.5
            inv_no = inv.get("InvoiceNo") or "-"
            inv_date = str(inv.get("InvoiceDate") or "-")[:10]
            fy = (inv.get("fin_year") or inv.get("FinYearVal") or "-").replace("_", "-")

            taxable = float(inv.get("TotalItemAmount") or 0.0)
            cgst = float(inv.get("TotalCGSTAmount") or 0.0)
            sgst = float(inv.get("TotalSGSTAmount") or 0.0)
            igst = float(inv.get("TotalIGSTAmount") or 0.0)
            gst = cgst + sgst + igst
            net_inv = float(inv.get("net_amount_float") or inv.get("NetAmount") or 0.0)
            settled = float(inv.get("amount_paid") or 0.0)
            due = float(inv.get("balance_due") or 0.0)

            matched = inv.get("matched_receipts", [])
            inv_tds = sum(float(m.get("tds_amount") or 0.0) for m in matched)
            inv_cash = max(0.0, settled - inv_tds)

            tot_matrix_taxable += taxable
            tot_matrix_gst += gst
            tot_matrix_inv += net_inv
            tot_matrix_cash += inv_cash
            tot_matrix_tds += inv_tds
            tot_matrix_settled += settled
            tot_matrix_due += due

            status_lbl = (inv.get("payment_status_label") or "Pending").upper()
            if status_lbl == "PAID":
                st_fill = fill_green
                st_color = C_GREEN_TEXT
            elif status_lbl == "PARTIALLY PAID":
                st_fill = fill_amber
                st_color = C_AMBER_TEXT
            else:
                st_fill = fill_rose
                st_color = C_ROSE_TEXT

            fill_row = fill_zebra if idx % 2 == 0 else PatternFill(fill_type=None)

            row_data = [
                (inv_no, align_center, font_mono_bold, None),
                (inv_date, align_center, font_data, None),
                (fy, align_center, font_data, None),
                (taxable if taxable > 0 else "-", align_right, font_data, NUM_CURRENCY if taxable > 0 else None),
                (gst if gst > 0 else "-", align_right, font_data, NUM_CURRENCY if gst > 0 else None),
                (net_inv, align_right, font_data_bold, NUM_CURRENCY),
                (inv_cash if inv_cash > 0 else "-", align_right, font_data, NUM_CURRENCY if inv_cash > 0 else None),
                (inv_tds if inv_tds > 0 else "-", align_right, font_data, NUM_CURRENCY if inv_tds > 0 else None),
                (settled if settled > 0 else "-", align_right, Font(name=FONT_FAMILY, size=10, bold=True, color=C_GREEN_TEXT), NUM_CURRENCY if settled > 0 else None),
                (due if due > 0 else "-", align_right, Font(name=FONT_FAMILY, size=10, bold=True, color=C_ROSE_TEXT), NUM_CURRENCY if due > 0 else None),
                (status_lbl, align_center, Font(name=FONT_FAMILY, size=9, bold=True, color=st_color), None),
            ]

            for col_idx, (val, aln, fnt, fmt) in enumerate(row_data, start=1):
                cell = ws.cell(row=curr_row, column=col_idx, value=val)
                cell.alignment = aln
                cell.font = fnt
                cell.fill = st_fill if col_idx == 11 else fill_row
                cell.border = border_cell
                if fmt:
                    cell.number_format = fmt

            curr_row += 1

        # Summary / Totals Row
        ws.row_dimensions[curr_row].height = 21
        ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=3)
        tot_label = ws.cell(row=curr_row, column=1, value="TOTAL INVOICE PORTFOLIO")
        tot_label.font = font_tbl_header
        tot_label.fill = fill_header
        tot_label.alignment = align_center

        matrix_totals = [
            (4, tot_matrix_taxable),
            (5, tot_matrix_gst),
            (6, tot_matrix_inv),
            (7, tot_matrix_cash),
            (8, tot_matrix_tds),
            (9, tot_matrix_settled),
            (10, tot_matrix_due),
        ]

        for col_idx, val in matrix_totals:
            cell = ws.cell(row=curr_row, column=col_idx, value=val)
            cell.font = font_tbl_header
            cell.fill = fill_header
            cell.alignment = align_right
            cell.number_format = NUM_CURRENCY
            cell.border = border_total

        c_empty = ws.cell(row=curr_row, column=11, value="")
        c_empty.fill = fill_header
        c_empty.border = border_total

        # Tailored compact column widths for Sheet 2
        compact_widths_s2 = {
            "A": 15,   # Invoice No
            "B": 11,   # Invoice Date
            "C": 10,   # Fin Year
            "D": 13,   # Taxable
            "E": 12,   # GST
            "F": 14,   # Total Invoice
            "G": 13,   # Cash / Bank
            "H": 11,   # TDS
            "I": 14,   # Total Settled
            "J": 14,   # Balance Due
            "K": 12,   # Status
        }
        for col_l, w in compact_widths_s2.items():
            ws.column_dimensions[col_l].width = w
