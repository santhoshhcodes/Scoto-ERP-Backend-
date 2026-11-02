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


class ProformaExcelService:
    """
    Proforma Invoice Excel Generator Service
    Generates a spreadsheet matching the Scoto ERP 'proforma_sample.xlsm' template.
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
        # 1. Header from Acc_Proforma_Inv_Main
        header_sql = """
            SELECT
                TransNo,
                CONVERT(VARCHAR(30), TransDate, 120) AS TransDate,
                QuotationNo,
                CONVERT(VARCHAR(30), QuotationDate, 120) AS QuotationDate,
                CustomerCode,
                CustomerName,
                TotalQty,
                TotalItemAmount,
                TotalCGSTAmount,
                TotalSGSTAmount,
                TotalIGSTAmount,
                TotalAmount,
                Remarks,
                RoundType,
                RoundOff,
                NetAmount AS FinalNetAmount,
                ApprovalStatus
            FROM Acc_Proforma_Inv_Main
            WHERE TransNo = :trans_no
              AND (Status IS NULL OR Status <> 'Delete')
        """
        header_row = db.execute(text(header_sql), {"trans_no": trans_no}).mappings().first()
        if not header_row:
            raise HTTPException(status_code=404, detail=f"Proforma Invoice {trans_no} not found")
        proforma = dict(header_row)

        # 2. Line items from Acc_Proforma_Inv_Sub
        items_sql = """
            SELECT
                id, ItemCode, ProductType, HSNCode, Rate, Qty, ItemValue,
                GST, CGST, SGST, IGST, NetAmount, Service
            FROM Acc_Proforma_Inv_Sub
            WHERE TransNo = :trans_no
              AND (Status IS NULL OR Status <> 'Delete')
            ORDER BY id ASC
        """
        items_rows = db.execute(text(items_sql), {"trans_no": trans_no}).mappings().all()
        proforma["Items"] = [dict(it) for it in items_rows]

        # 3. Client ledger
        ledger_sql = """
            SELECT TOP 1
                LedgerCode, LedgerName, Add1, Add2, City, PinCode, State,
                GSTNo, MobileNo, ContectName
            FROM Acc_Mst_Ledger
            WHERE (
                (:cust_code IS NOT NULL AND :cust_code <> '' AND LedgerCode = :cust_code)
                OR (:cust_name IS NOT NULL AND :cust_name <> '' AND LedgerName = :cust_name)
            )
        """
        ledger_row = db.execute(
            text(ledger_sql),
            {
                "cust_code": proforma.get("CustomerCode") or "",
                "cust_name": proforma.get("CustomerName") or "",
            },
        ).mappings().first()
        proforma["Ledger"] = dict(ledger_row) if ledger_row else {}

        # 4. Build workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Invoice"
        cls._build_sheet(ws, proforma)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    # ------------------------------------------------------------- sheet layout
    @classmethod
    def _build_sheet(cls, ws, proforma: dict):
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

        # ---- column widths (same as template).  Layout columns: B..H, I = spacer
        widths = {"A": 3.7109375, "B": 31.0, "C": 21.0, "D": 6.0,
                  "E": 1.0, "F": 12.5, "G": 10.0, "H": 14.5,
                  "I": 3.28515625}
        for col, w in widths.items():
            ws.column_dimensions[col].width = w

        # ---- border accumulator
        edges = {}

        def edge(r, c, **kw):
            edges.setdefault((r, c), {}).update(kw)

        def hline(row, c1, c2, side=thin, where="top"):
            for c in range(c1, c2 + 1):
                edge(row, c, **{where: side})

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

        def A(h=None, v="center", wrap=False, shrink=False):
            return Alignment(horizontal=h, vertical=v, wrap_text=wrap, shrink_to_fit=shrink)

        f = lambda size=10, b=False, i=False, u=None, name=FF: Font(name=name, size=size, bold=b, italic=i, underline=u)

        B_, C_, D_, E_, F_, G_, H_ = 2, 3, 4, 5, 6, 7, 8

        # ---- row heights (same as template)
        heights = {3: 12.75, 4: 22.5, 5: 12.75, 7: 9, 8: 16.5, 9: 20.25, 10: 15, 11: 15,
                   12: 15, 13: 15, 14: 23.25}
        for r, h in heights.items():
            ws.row_dimensions[r].height = h

        # =====================================================================
        # Rows 3-5 : Title + logo
        # =====================================================================
        put("C4", "PROFORMA INVOICE", f(18, b=True), Alignment(horizontal="center"))

        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "scoto_logo_header.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "scoto_logo_header.png")
        if os.path.exists(logo_path):
            try:
                img = OpenpyxlImage(logo_path)
                img.anchor = TwoCellAnchor(
                    editAs="absolute",
                    _from=AnchorMarker(col=5, colOff=177800, row=2, rowOff=114300),
                    to=AnchorMarker(col=7, colOff=908050, row=4, rowOff=76200),
                )
                ws.add_image(img)
            except Exception:
                put("F4", "SCOTO", Font(name=FF, size=18, bold=True, color="5A2D82"), A("center"))
        else:
            put("F4", "SCOTO", Font(name=FF, size=18, bold=True, color="5A2D82"), A("center"))

        # =====================================================================
        # Rows 6-14 : Client / Service provider / Proforma no & date
        # =====================================================================
        put("B6", "Name & Address  of Client:", f(11, b=True, u="single"))
        put("C6", "Service Provider :", f(11, b=True, u="single"))
        ws.merge_cells("F6:G6")

        ledger = proforma.get("Ledger", {}) or {}
        client_name = (proforma.get("CustomerName") or "").strip()
        add1 = (ledger.get("Add1") or "").strip()
        add2 = (ledger.get("Add2") or "").strip()
        city = (ledger.get("City") or "").strip()
        state = (ledger.get("State") or "").strip()
        pincode = str(ledger.get("PinCode") or "").strip()
        gst_no = str(ledger.get("GSTNo") or "").strip()
        contact_name = str(ledger.get("ContectName") or "").strip()
        if not contact_name or contact_name.upper() == "NA":
            contact_name = "Management"

        # client block (3 address lines like the template)
        put("B8", client_name, f(11, b=True), A(None, "bottom", True))
        put("B9", add1 or add2, f(11))
        line2 = ", ".join(p for p in ((add2 if add1 else ""), city) if p)
        put("B10", line2, f(11))
        line3 = ", ".join(p for p in (state, "INDIA") if p)
        if pincode:
            line3 = f"{line3}, Pincode-{pincode}."
        put("B11", line3, f(10))
        gst_txt = f"GST No: {gst_no}" if gst_no and gst_no.upper() != "NA" else "GST No:"
        put("B13", gst_txt, f(11, b=True), A("left"))

        # service provider block
        ws.merge_cells("C7:D7")
        provider = [
            (8, "SCOTO SYSTEC PRIVATE LIMITED", f(10, b=True)),
            (9, "No: 61-A, First Floor, HM Enclave,", f(10)),
            (10, "Thiruvalluvar Nagar, 50 Feet Road,", f(10)),
            (11, "Ramanathapuram,", f(10)),
            (12, "Coimbatore - 641045, India", f(10)),
        ]
        for r, txt, fnt in provider:
            ws.merge_cells(f"C{r}:E{r}")
            put(f"C{r}", txt, fnt, A("left"))
        put("C13", "GSTN: 33AAVCS5957L1ZF", f(10, b=True), A("left"))

        # proforma no / date
        ws.merge_cells("F8:G8")
        ws.merge_cells("F9:G9")
        put("F8", "Proforma No.", f(10, b=True), A("center", "center"))
        put("H8", "Proforma Date", f(10, b=True), A("center", "center"))
        put("F9", proforma.get("TransNo", "") or "", f(10, b=True, name="Verdana"), A("center", "center", shrink=True))
        pdate = cls.parse_date(proforma.get("TransDate"))
        put("H9", pdate if pdate else "", f(10, b=True, name="Verdana"), A("center", "center", shrink=True),
            "[$-409]d\\-mmm\\-yyyy;@")

        # row 14
        put("B14", f"Kind Attn: {contact_name}", f(10, b=True), A(None, "center"))
        ws.merge_cells("C14:E14")
        put("C14", "Tel :91 422 4210406", f(10), A("left", "center"))
        ws.merge_cells("F14:G14")

        # borders for this block
        hline(6, B_, H_, thin, "top")
        vline(C_, 6, 13, thin, "left")           # B | C
        vline(F_, 6, 14, thin, "left")           # E | F
        vline(H_, 6, 14, thin, "left")           # G | H
        hline(8, F_, H_, thin, "top")            # top of proforma no/date boxes
        hline(13, B_, E_, thin, "bottom")
        box(B_, 14, B_, 14)
        box(C_, 14, E_, 14)
        box(F_, 14, G_, 14)
        box(H_, 14, H_, 14)

        # =====================================================================
        # Rows 15-17 : table header
        # =====================================================================
        ws.merge_cells("B16:C16")
        ws.merge_cells("D16:E16")
        ws.merge_cells("F16:G16")
        hdr = f(10, b=True, u="single")
        put("B16", "Item Description", hdr, A("center"))
        put("D16", "Units", hdr, A("center"))
        put("F16", "Price", hdr, A("center"))
        put("H16", "Amount", hdr, A("center"))
        hline(15, B_, H_, thin, "top")

        # =====================================================================
        # Item rows (start at row 18, minimum 2 rows)
        # =====================================================================
        items = proforma.get("Items", []) or []
        start = 18
        n_rows = max(len(items), 2)
        r = start
        for idx in range(n_rows):
            ws.merge_cells(f"B{r}:C{r}")
            ws.merge_cells(f"D{r}:E{r}")
            ws.merge_cells(f"F{r}:G{r}")
            min_h = 17.25 if idx != 1 else 30
            if idx < len(items):
                it = items[idx]
                name = it.get("ProductType", "") or it.get("ItemCode", "") or ""
                svc = it.get("Service", "")
                desc = name
                if svc and str(svc).strip() and str(svc).strip() != str(name).strip():
                    desc = f"{name} ({svc})"
                put(f"B{r}", desc, f(11), A("left", "center", True))
                put(f"D{r}", cls.to_float(it.get("Qty")), f(10), A("center", "center"), "#,##0")
                put(f"F{r}", cls.to_float(it.get("Rate")), f(10), A("right", "center"),
                    "_(* #,##0.00_);_(* \\(#,##0.00\\);_(* \\-??_);_(@_)")
                put(f"H{r}", cls.to_float(it.get("ItemValue")), f(10), A(None, "center"), "#,##0.00")
                lines = max(1, -(-len(str(desc)) // 50))      # wrap estimate for merged B:C at 11pt
                ws.row_dimensions[r].height = max(min_h, 15 * lines + 2)
            else:
                ws.row_dimensions[r].height = min_h
            r += 1

        # =====================================================================
        # Totals
        # =====================================================================
        tot_item_amt = cls.to_float(proforma.get("TotalItemAmount"))
        tot_cgst = cls.to_float(proforma.get("TotalCGSTAmount"))
        tot_sgst = cls.to_float(proforma.get("TotalSGSTAmount"))
        tot_igst = cls.to_float(proforma.get("TotalIGSTAmount"))
        grand_total = cls.to_float(
            proforma.get("FinalNetAmount") or proforma.get("NetAmount") or proforma.get("TotalAmount"))

        gst_pct = 18.0
        if items:
            gst_pct = cls.to_float(items[0].get("GST"), 18.0) or 18.0
        half = f"{gst_pct / 2:g}%"
        full = f"{gst_pct:g}%"

        # Total row
        r_total = r
        ws.row_dimensions[r_total].height = 27.75
        ws.merge_cells(f"B{r_total}:C{r_total}")
        ws.merge_cells(f"F{r_total}:G{r_total}")
        put(f"F{r_total}", "Total", f(10, b=True), A("center", "center"))
        put(f"H{r_total}", tot_item_amt, f(10), A(None, "center"), "#,##0.00")
        edge(r_total, H_, top=thin, bottom=thin)
        r += 1

        ws.row_dimensions[r].height = 6                  # spacer
        r += 1

        tax_rows = ([(f"IGST @ {full}", tot_igst)] if tot_igst > 0
                    else [(f"CGST @ {half}", tot_cgst), (f"SGST @ {half}", tot_sgst)])
        for lbl, val in tax_rows:
            ws.row_dimensions[r].height = 16.5
            ws.merge_cells(f"B{r}:C{r}")
            ws.merge_cells(f"D{r}:E{r}")
            ws.merge_cells(f"F{r}:G{r}")
            put(f"F{r}", lbl, f(10), A("center", "center"))
            put(f"H{r}", val, f(10), A(None, "center"), "#,##0.00")
            r += 1

        ws.row_dimensions[r].height = 8.25               # spacer
        r += 1

        r_grand = r
        ws.row_dimensions[r_grand].height = 24.75
        ws.merge_cells(f"F{r_grand}:G{r_grand}")
        put(f"F{r_grand}", "Grand Total : ", f(10, b=True), A("center", "center"))
        put(f"H{r_grand}", grand_total, f(10, b=True), A(None, "center"), "#,##0.00_);(#,##0.00)")
        edge(r_grand, H_, top=thin)

        # vertical dividers of the items / totals table
        vline(D_, 15, r_grand, thin, "left")
        vline(F_, 15, r_grand, thin, "left")
        vline(H_, 15, r_grand, thin, "left")
        hline(r_grand, B_, H_, double, "bottom")
        r += 1

        # =====================================================================
        # Amount in words
        # =====================================================================
        ws.row_dimensions[r].height = 15.75
        put(f"B{r}", "Amount in words :", f(10))
        put(f"C{r}", cls.num_to_indian_words(grand_total), f(10, b=True))
        r += 1
        ws.row_dimensions[r].height = 15.75              # blank row
        hline(r, B_, H_, double, "bottom")
        r += 1

        # =====================================================================
        # Company & bank details
        # =====================================================================
        ws.row_dimensions[r].height = 15.75
        put(f"B{r}", "SCOTO SYSTEC PVT LTD", f(10, b=True, u="single"))
        put(f"G{r}", "Bank Details:", f(10, b=True, u="single"), A("right", "bottom"))
        r += 1
        put(f"B{r}", "GSTIN: 33AAVCS5957L1ZF", f(10, b=True))
        put(f"G{r}", "SCOTO SYSTEC PVT LTD", f(10, b=True), A("right", "bottom"))
        r += 1
        put(f"G{r}", "CITY UNION BANK", f(10), A("right", "bottom"))
        r += 1
        put(f"G{r}", "A/c No:  510909010084515", f(10, b=True), A("right", "bottom"), "@")
        r += 1
        ws.row_dimensions[r].height = 15.75
        put(f"G{r}", "IFSC Code: CIUB0000214", f(10), A("right", "bottom"))
        hline(r, B_, H_, double, "bottom")
        r += 1

        # =====================================================================
        # Place / Date / Signatory
        # =====================================================================
        ws.row_dimensions[r].height = 7.5                # thin spacer
        r += 1
        put(f"B{r}", "Place : Coimbatore, India", f(10, b=True))
        put(f"F{r}", "For SCOTO SYSTEC PVT LTD.,", f(10, b=True))
        r += 1
        ws.merge_cells(f"F{r}:H{r + 1}")                 # signature space
        r += 1
        ws.row_dimensions[r].height = 11.25
        r += 1
        inv_date = cls.parse_date(proforma.get("TransDate"))
        date_txt = inv_date.strftime("%d-%b-%Y").upper() if inv_date else ""
        put(f"B{r}", f"Date : {date_txt}", f(10, b=True))
        put(f"F{r}", "Authorised Signatory", f(10))
        r += 1

        # blank merged row, thanks row, closing row
        ws.row_dimensions[r].height = 12.75
        ws.merge_cells(f"B{r}:H{r}")
        hline(r, B_, H_, thin, "top")
        r += 1
        ws.row_dimensions[r].height = 12.75
        ws.merge_cells(f"B{r}:H{r}")
        put(f"B{r}", "Thanks for your Business", f(11, i=True), A("center"))
        r += 1
        ws.row_dimensions[r].height = 6.75
        r_last = r
        r += 1
        put(f"B{r}", "* This is a computer generated Document. No Signature required.", f(9))

        # =====================================================================
        # Outer frame B3:H(last)
        # =====================================================================
        hline(5, B_, H_, thin, "bottom")
        vline(B_, 3, r_last, thin, "left")
        vline(H_, 3, r_last, thin, "right")
        hline(3, B_, H_, thin, "top")
        hline(r_last, B_, H_, thin, "bottom")

        for (rr, cc), d in edges.items():
            cell = ws.cell(row=rr, column=cc)
            old = cell.border
            cell.border = Border(
                left=d.get("left", old.left),
                right=d.get("right", old.right),
                top=d.get("top", old.top),
                bottom=d.get("bottom", old.bottom),
            )

        # make merged ranges consistent (outer edges of each merge)
        for mr in ws.merged_cells.ranges:
            tl = ws.cell(row=mr.min_row, column=mr.min_col).border
            br = ws.cell(row=mr.max_row, column=mr.max_col).border
            for rr in range(mr.min_row, mr.max_row + 1):
                for cc in range(mr.min_col, mr.max_col + 1):
                    cell = ws.cell(row=rr, column=cc)
                    b = cell.border
                    cell.border = Border(
                        left=tl.left if cc == mr.min_col else b.left,
                        right=br.right if cc == mr.max_col else b.right,
                        top=tl.top if rr == mr.min_row else b.top,
                        bottom=br.bottom if rr == mr.max_row else b.bottom,
                    )

        ws.print_area = f"A2:I{r + 1}"