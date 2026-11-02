import io
import os
import re
from datetime import datetime

import openpyxl
from fastapi import HTTPException
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, TwoCellAnchor
from openpyxl.styles import Alignment, Border, Font, Side
from sqlalchemy import text
from sqlalchemy.orm import Session


from src.utils.formatters import num_to_indian_words, to_float


class QuotationExcelService:
    """
    Quotation Excel Generator Service
    Generates a spreadsheet matching the Scoto ERP 'quote.xlsm' template.
    Sheet Name: 'Invoice'
    """

    # ------------------------------------------------------------------ helpers
    to_float = staticmethod(to_float)
    num_to_indian_words = staticmethod(num_to_indian_words)

    @staticmethod
    def parse_date(date_val):
        """Return a datetime (or None) so Excel stores a real date."""
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            return date_val
        s = str(date_val).strip().split(' ')[0]
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(s, fmt)
            except Exception:
                pass
        return None

    # ----------------------------------------------------------------- generate
    @classmethod
    def generate_excel(cls, db: Session, trans_no: str) -> io.BytesIO:
        # 1. Header
        header_sql = """
            SELECT
                TransNo,
                CONVERT(VARCHAR(30), TransDate, 120) AS TransDate,
                Product AS ProdType,
                SuppCode,
                CustomerName,
                Remarks AS Narration,
                Purpose,
                terms_conditions AS TermsAndConditions,
                TotQty AS TotalQty,
                TotItemAmt AS TotalItemAmount,
                TotCGSTAmt AS TotalCGSTAmount,
                TotSGSTAmt AS TotalSGSTAmount,
                TotIGSTAmt AS TotalIGSTAmount,
                TotLineAmt AS TotalAmount,
                RoundOffType AS RoundType,
                RoundOffVal AS RoundOff,
                NetAmount AS FinalNetAmount,
                ApprovalStatus
            FROM Acc_Quotation_Main
            WHERE TransNo = :trans_no
              AND Status <> 'Delete'
        """
        header_row = db.execute(text(header_sql), {"trans_no": trans_no}).mappings().first()
        if not header_row:
            raise HTTPException(status_code=404, detail=f"Quotation {trans_no} not found")
        quotation = dict(header_row)

        # 2. Items
        items_sql = """
            SELECT
                order_id, ItemCode, ProductType, Prod_highlight, HSNCode, UOM,
                Rate, Qty, ItemValue, GST, CGST, SGST, IGST, NetAmount, Service
            FROM Acc_Quotation_Sub
            WHERE TransNo = :trans_no
              AND Status <> 'Delete'
            ORDER BY TRY_CAST(order_id AS INT) ASC, id ASC
        """
        items_rows = db.execute(text(items_sql), {"trans_no": trans_no}).mappings().all()
        quotation["Items"] = [dict(it) for it in items_rows]

        # 3. Client ledger
        ledger_sql = """
            SELECT TOP 1
                LedgerCode, LedgerName, Add1, Add2, City, PinCode, State,
                GSTNo, MobileNo, ContectName
            FROM Acc_Mst_Ledger
            WHERE (
                (:supp_code IS NOT NULL AND :supp_code <> '' AND LedgerCode = :supp_code)
                OR (:cust_name IS NOT NULL AND :cust_name <> '' AND LedgerName = :cust_name)
            )
        """
        ledger_row = db.execute(
            text(ledger_sql),
            {
                "supp_code": quotation.get("SuppCode") or "",
                "cust_name": quotation.get("CustomerName") or "",
            },
        ).mappings().first()
        quotation["Ledger"] = dict(ledger_row) if ledger_row else {}

        # 4. Build workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Invoice"
        cls._build_sheet(ws, quotation)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    # ------------------------------------------------------------- sheet layout
    @classmethod
    def _build_sheet(cls, ws, quotation: dict):
        FF = "Calibri"
        thin = Side(border_style="thin", color="000000")
        double = Side(border_style="double", color="000000")

        # ---- page / view setup (same as template)
        ws.sheet_view.showGridLines = False
        ws.page_setup.orientation = "portrait"
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.print_options.horizontalCentered = True
        ws.page_margins.left = 0.28
        ws.page_margins.right = 0.13
        ws.page_margins.top = 1.21
        ws.page_margins.bottom = 0.49
        ws.page_margins.header = 0.98
        ws.page_margins.footer = 0.51

        # ---- column widths (same as template)
        widths = {"A": 3.7109375, "B": 29.5, "C": 17.0, "D": 6.0,
                  "E": 4.5, "F": 2.5, "G": 12.5, "H": 10.0,
                  "I": 14.5, "J": 3.28515625}
        for col, w in widths.items():
            ws.column_dimensions[col].width = w

        # ---- border accumulator (so later calls never wipe earlier edges)
        edges = {}

        def edge(r, c, **kw):
            d = edges.setdefault((r, c), {})
            d.update(kw)

        def hline(row_for_top, c1, c2, side=thin, where="top"):
            for c in range(c1, c2 + 1):
                edge(row_for_top, c, **{where: side})

        def vline(col, r1, r2, side=thin, where="left"):
            for r in range(r1, r2 + 1):
                edge(r, col, **{where: side})

        def box(c1, r1, c2, r2, side=thin):
            hline(r1, c1, c2, side, "top")
            hline(r2, c1, c2, side, "bottom")
            vline(c1, r1, r2, side, "left")
            vline(c2, r1, r2, side, "right")

        def put(ref, value=None, font=None, align=None, fmt=None):
            c = ws[ref]
            if value is not None:
                c.value = value
            if font:
                c.font = font
            if align:
                c.alignment = align
            if fmt:
                c.number_format = fmt
            return c

        def A(h=None, v="center", wrap=False, indent=0, shrink=False):
            return Alignment(horizontal=h, vertical=v, wrap_text=wrap, indent=indent, shrink_to_fit=shrink)

        f = lambda size=10, b=False, i=False, u=None, name=FF: Font(name=name, size=size, bold=b, italic=i, underline=u)

        # ---- row heights (same as template)
        heights = {3: 12.75, 4: 22.5, 5: 12.75, 7: 9, 8: 16.5, 9: 20.25, 10: 15, 11: 15,
                   12: 15, 13: 15, 14: 23.25}
        for r, h in heights.items():
            ws.row_dimensions[r].height = h

        # =====================================================================
        # Rows 3-5 : Title + logo
        # =====================================================================
        put("C4", "QUOTATION", f(18, b=True), Alignment(horizontal="center"))

        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "scoto_logo_header.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "scoto_logo_header.png")
        if os.path.exists(logo_path):
            try:
                img = OpenpyxlImage(logo_path)
                img.anchor = TwoCellAnchor(
                    editAs="absolute",
                    _from=AnchorMarker(col=6, colOff=114300, row=2, rowOff=136525),
                    to=AnchorMarker(col=8, colOff=847725, row=4, rowOff=98425),
                )
                ws.add_image(img)
            except Exception:
                put("G4", "SCOTO", Font(name=FF, size=18, bold=True, color="5A2D82"), A("center"))
        else:
            put("G4", "SCOTO", Font(name=FF, size=18, bold=True, color="5A2D82"), A("center"))

        # =====================================================================
        # Rows 6-14 : Client / Service provider / Quote no & date
        # =====================================================================
        put("B6", "Name & Address  of Client:", f(11, b=True, u="single"))
        put("C6", "Service Provider :", f(11, b=True, u="single"))
        ws.merge_cells("G6:H6")

        ledger = quotation.get("Ledger", {}) or {}
        client_name = quotation.get("CustomerName", "") or ""
        add1 = (ledger.get("Add1") or "").strip()
        add2 = (ledger.get("Add2") or "").strip()
        city = (ledger.get("City") or "").strip()
        pincode = str(ledger.get("PinCode") or "").strip()
        gst_no = str(ledger.get("GSTNo") or "").strip()
        contact_name = str(ledger.get("ContectName") or "").strip()
        if not contact_name or contact_name.upper() == "NA":
            contact_name = "MANAGEMENT"

        put("B8", f"{client_name}," if client_name else "", f(11, b=True), A(None, "top", True))
        addr_line = f"{add1} {add2}".strip() if add2 else add1
        put("B9", addr_line, f(11), A(None, "top", True))
        city_pin = f"{city} - {pincode}." if city and pincode else (city or pincode or "")
        put("B10", city_pin, f(11))
        gst_txt = f"GSTN: {gst_no}" if gst_no and gst_no.upper() != "NA" else "GSTN:"
        put("B13", gst_txt, f(11, b=True), A("left"))

        # Service provider block (merged C:F, like template)
        provider = [
            (8, "SCOTO SYSTEC PRIVATE LIMITED", f(11, b=True)),
            (9, "No: 61-A, First Floor, HM Enclave,", f(10)),
            (10, "Thiruvalluvar Nagar, 50 Feet Road,", f(10)),
            (11, "Ramanathapuram,", f(10)),
            (12, "Coimbatore - 641045, India", f(10)),
        ]
        ws.merge_cells("C7:E7")
        for r, txt, fnt in provider:
            ws.merge_cells(f"C{r}:F{r}")
            put(f"C{r}", txt, fnt, A("left"))
        put("C13", "GSTN: 33AAVCS5957L1ZF", f(10, b=True), A("left"))

        # Quote no / date
        ws.merge_cells("G8:H8")
        put("G8", "Quote No.", f(10, b=True), A("center", "center"))
        put("I8", "Quote Date", f(10, b=True), A("center", "center"))
        ws.merge_cells("G9:H9")
        ws.merge_cells("G11:H11")
        ws.merge_cells("G12:H12")
        put("G9", quotation.get("TransNo", "") or "", f(10, b=True, name="Verdana"), A("center", "center", shrink=True))
        qdate = cls.parse_date(quotation.get("TransDate"))
        put("I9", qdate if qdate else "", f(10, b=True, name="Verdana"), A("center", "center", shrink=True),
            "[$-409]d\\-mmm\\-yyyy;@")

        # Row 14 : Kind Attn / Tel
        put("B14", f"Kind Attn: {contact_name}", f(10, b=True), A(None, "center"))
        ws.merge_cells("C14:F14")
        put("C14", "Tel :91 422 4210406", f(10), A("left", "center"))
        ws.merge_cells("G14:H14")

        # borders for this block
        hline(6, 2, 9, thin, "top")                      # top of row 6
        vline(3, 6, 13, thin, "left")                    # B | C
        vline(7, 6, 14, thin, "left")                    # F | G
        vline(9, 6, 14, thin, "left")                    # H | I
        hline(8, 7, 9, thin, "top")                      # top of quote no/date boxes
        hline(13, 2, 6, thin, "bottom")                  # line above Kind Attn row
        box(2, 14, 2, 14)                                # Kind Attn box
        box(3, 14, 6, 14)                                # Tel box
        box(7, 14, 8, 14)
        box(9, 14, 9, 14)

        # =====================================================================
        # Rows 15-17 : table header
        # =====================================================================
        ws.merge_cells("B16:C16")
        ws.merge_cells("E16:F16")
        ws.merge_cells("G16:H16")
        hdr = f(10, b=True, u="single")
        put("B16", "Description", hdr, A("center"))
        put("E16", "Qty", hdr, A("center"))
        put("G16", "Price", hdr, A("center"))
        put("I16", "Amount", hdr, A("center"))
        hline(15, 2, 9, thin, "top")

        # =====================================================================
        # Item rows (start at row 18, minimum 2 rows)
        # =====================================================================
        items = quotation.get("Items", []) or []
        start = 18
        n_rows = max(len(items), 2)
        r = start
        for idx in range(n_rows):
            ws.merge_cells(f"B{r}:C{r}")
            ws.merge_cells(f"E{r}:F{r}")
            ws.merge_cells(f"G{r}:H{r}")
            if idx < len(items):
                it = items[idx]
                name = it.get("ProductType", "") or it.get("ItemCode", "") or ""
                hl = it.get("Prod_highlight", "")
                desc = name
                if hl and str(hl).strip() and str(hl).strip() != str(name).strip():
                    desc = f"{name} - {hl}"
                put(f"B{r}", desc, f(12), A("left", "center", True))
                put(f"E{r}", cls.to_float(it.get("Qty")), f(10), A("center", "center"), "#,##0")
                put(f"G{r}", cls.to_float(it.get("Rate")), f(10), A("right", "center"),
                    "#,##0.00_);(#,##0.00)")
                put(f"I{r}", cls.to_float(it.get("ItemValue")), f(10), A(None, "center"), "#,##0.00")
                lines = max(1, -(-len(str(desc)) // 42))   # wrap estimate for merged B:C at 12pt
                ws.row_dimensions[r].height = max(20.25 if idx == 0 else 16.5, 16.5 * lines)
            else:
                ws.row_dimensions[r].height = 20.25 if idx == 0 else 16.5
            r += 1
        last_item_row = r - 1

        # =====================================================================
        # Totals
        # =====================================================================
        tot_item_amt = cls.to_float(quotation.get("TotalItemAmount"))
        tot_cgst = cls.to_float(quotation.get("TotalCGSTAmount"))
        tot_sgst = cls.to_float(quotation.get("TotalSGSTAmount"))
        tot_igst = cls.to_float(quotation.get("TotalIGSTAmount"))
        grand_total = cls.to_float(quotation.get("FinalNetAmount"))

        gst_pct = 18.0
        if items:
            gst_pct = cls.to_float(items[0].get("GST"), 18.0) or 18.0
        half = f"{gst_pct / 2:g}%"
        full = f"{gst_pct:g}%"

        # Total row
        r_total = r
        ws.row_dimensions[r_total].height = 27.75
        ws.merge_cells(f"G{r_total}:H{r_total}")
        put(f"G{r_total}", "Total", f(10, b=True), A("center", "center"))
        put(f"I{r_total}", tot_item_amt, f(10), A(None, "center"), "#,##0.00")
        edge(r_total, 9, top=thin, bottom=thin)
        r += 1

        # tiny spacer
        ws.row_dimensions[r].height = 5.25
        r += 1

        # tax rows
        tax_rows = ([(f"IGST @ {full}", tot_igst)] if tot_igst > 0
                    else [(f"CGST @ {half}", tot_cgst), (f"SGST @ {half}", tot_sgst)])
        for lbl, val in tax_rows:
            ws.row_dimensions[r].height = 16.5
            ws.merge_cells(f"G{r}:H{r}")
            put(f"G{r}", lbl, f(10), A("center", "center"))
            put(f"I{r}", val, f(10), A(None, "center"), "#,##0.00")
            r += 1

        # tiny spacer
        ws.row_dimensions[r].height = 1.5
        r += 1

        # Grand total
        r_grand = r
        ws.row_dimensions[r_grand].height = 24.75
        ws.merge_cells(f"G{r_grand}:H{r_grand}")
        put(f"G{r_grand}", "Grand Total : ", f(10, b=True), A("center", "center"))
        put(f"I{r_grand}", grand_total, f(10, b=True), A(None, "center"), "#,##0.00_);(#,##0.00)")
        edge(r_grand, 9, top=thin)

        # vertical dividers for the whole items/totals table
        vline(5, 15, r_grand, thin, "left")     # D | E
        vline(7, 15, r_grand, thin, "left")     # F | G
        vline(9, 15, r_grand, thin, "left")     # H | I
        hline(r_grand, 2, 9, double, "bottom")
        r += 1

        # =====================================================================
        # Amount in words
        # =====================================================================
        r_words = r
        ws.row_dimensions[r_words].height = 15.75
        put(f"B{r_words}", "Amount in words :", f(10, b=True))
        put(f"C{r_words}", cls.num_to_indian_words(grand_total), f(10, b=True))
        r += 1
        ws.row_dimensions[r].height = 15.75          # blank row under words
        hline(r, 2, 9, double, "bottom")
        r += 1

        # =====================================================================
        # Company & bank details
        # =====================================================================
        ws.row_dimensions[r].height = 15.75
        put(f"B{r}", "SCOTO SYSTEC PVT LTD", f(10, b=True, u="single"))
        put(f"H{r}", "Bank Details:", f(10, b=True, u="single"), A("right"))
        r += 1
        put(f"B{r}", "GSTIN: 33AAVCS5957L1ZF", f(10, b=True))
        put(f"H{r}", "SCOTO SYSTEC PRIVATE LIMITED", f(10, b=True), A("right"))
        r += 1
        put(f"H{r}", "CITY UNION BANK", f(10), A("right"))
        r += 1
        put(f"H{r}", "A/c No:  510909010084515", f(10, b=True), A("right"), "@")
        r += 1
        ws.row_dimensions[r].height = 15.75
        put(f"H{r}", "IFSC Code: CIUB0000214", f(10), A("right"))
        r += 1

        # =====================================================================
        # Terms & conditions
        # =====================================================================
        r_terms = r
        ws.row_dimensions[r].height = 14.45
        ws.merge_cells(f"B{r}:I{r}")
        put(f"B{r}", "Terms & Conditions:", f(10, b=True, u="single"), A("left"))
        hline(r, 2, 9, double, "top")
        r += 1

        default_terms = [
            "1. Quotation valid for only 10 Days.",
            "2. Payment :100% in Advance",
            "3. Delivery: 5 to 7 Working Days against payment.",
            "4. All payments Should be made in favor of \"Scoto Systec Pvt Ltd\" payable at coimbatore.",
            "5. Project Kick start : Immediate after receiving the Advance.",
        ]
        custom = quotation.get("TermsAndConditions")
        terms = []
        if custom and str(custom).strip():
            terms = [l.strip() for l in re.split(r"\r?\n|<br\s*/?>", str(custom)) if l.strip()]
        if not terms:
            terms = default_terms
        for line in terms:
            ws.row_dimensions[r].height = 14.45
            ws.merge_cells(f"B{r}:I{r}")
            put(f"B{r}", line, f(10), A("left"))
            r += 1

        # blank merged row + thanks row + tiny closing row
        ws.row_dimensions[r].height = 12.75
        ws.merge_cells(f"B{r}:I{r}")
        hline(r, 2, 9, thin, "top")
        r += 1
        ws.row_dimensions[r].height = 12.75
        ws.merge_cells(f"B{r}:I{r}")
        put(f"B{r}", "Thanks for your Business", f(11, i=True), A("center"))
        r += 1
        ws.row_dimensions[r].height = 6.75
        r_last = r

        # =====================================================================
        # Outer frame B3:I(last)
        # =====================================================================
        hline(5, 2, 9, thin, "bottom")                 # under the title block
        vline(2, 3, r_last, thin, "left")
        vline(9, 3, r_last, thin, "right")
        hline(3, 2, 9, thin, "top")
        hline(r_last, 2, 9, thin, "bottom")

        # ---- apply collected borders (after merges so all cells exist)
        for (rr, cc), d in edges.items():
            cell = ws.cell(row=rr, column=cc)
            old = cell.border
            cell.border = Border(
                left=d.get("left", old.left),
                right=d.get("right", old.right),
                top=d.get("top", old.top),
                bottom=d.get("bottom", old.bottom),
            )

        # make borders of merged ranges consistent (outer edges of each merge)
        for mr in ws.merged_cells.ranges:
            top_left = ws.cell(row=mr.min_row, column=mr.min_col).border
            bottom_right = ws.cell(row=mr.max_row, column=mr.max_col).border
            for rr in range(mr.min_row, mr.max_row + 1):
                for cc in range(mr.min_col, mr.max_col + 1):
                    cell = ws.cell(row=rr, column=cc)
                    b = cell.border
                    cell.border = Border(
                        left=top_left.left if cc == mr.min_col else b.left,
                        right=bottom_right.right if cc == mr.max_col else b.right,
                        top=top_left.top if rr == mr.min_row else b.top,
                        bottom=bottom_right.bottom if rr == mr.max_row else b.bottom,
                    )

        ws.print_area = f"A2:J{r_last + 1}"