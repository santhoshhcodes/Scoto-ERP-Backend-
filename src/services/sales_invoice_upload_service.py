import io
import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal
import difflib
import openpyxl
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile

# Indian GST State Codes Map
GST_STATE_MAP = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
    "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur",
    "15": "Mizoram", "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal",
    "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra and Nagar Haveli and Daman and Diu", "27": "Maharashtra", "29": "Karnataka",
    "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry",
    "35": "Andaman and Nicobar Islands", "36": "Telangana", "37": "Andhra Pradesh", "38": "Ladakh",
}


class SalesInvoiceUploadService:
    """
    High-Performance Bulk Sales Invoice & Smart Ledger/Item Reconciler Service.
    Supports up to 100+ Excel workbooks or multi-sheet invoice files.
    """

    @staticmethod
    def _clean_str(val: Any) -> str:
        if val is None:
            return ""
        return str(val).strip()

    @staticmethod
    def _to_float(val: Any) -> float:
        if val is None:
            return 0.0
        try:
            s = str(val).replace(",", "").replace("₹", "").strip()
            return float(s)
        except Exception:
            return 0.0

    @staticmethod
    def _extract_gst(text_block: str) -> str:
        if not text_block:
            return ""
        match = re.search(r"([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})", text_block.upper())
        return match.group(1) if match else ""

    @staticmethod
    def _extract_pan(gst: str) -> str:
        if len(gst) == 15:
            return gst[2:12]
        return ""

    @staticmethod
    def _clean_customer_name(name: str) -> str:
        if not name:
            return ""
        s = str(name).strip()
        # Remove typical prefixes: M/s., M/S., M/s, M/S, MS, Messrs., Shri, Smt, etc.
        prev = None
        while prev != s:
            prev = s
            s = re.sub(r"(?i)^(m\s*/?\s*s\.?|messrs\.?|shri\.?|smt\.?|mr\.?|mrs\.?)\s*", "", s).strip()
        # Strip trailing punctuation .,'"- and whitespace
        s = re.sub(r"[\.,\'\"\-\s]+$", "", s).strip()
        return s

    @classmethod
    def _normalize_name(cls, name: str) -> str:
        if not name:
            return ""
        s = cls._clean_customer_name(name)
        # Remove legal entity suffixes for fuzzy comparison
        s = re.sub(r"(?i)\s*(pvt\.?\s*ltd\.?|private\s*limited|p\.?\s*ltd\.?|limited|ltd\.?|llp|inc\.?)\s*\.*$", "", s)
        s = re.sub(r"[^\w\s]", "", s)
        return " ".join(s.lower().split())

    @classmethod
    def _parse_template_sheet(cls, sheet, filename: str) -> Optional[Dict[str, Any]]:
        """
        Parses an individual printable tax invoice sheet (like the standard Scoto template).
        """
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 5:
            return None

        invoice_no = ""
        invoice_date = ""
        client_name = ""
        client_address_lines = []
        client_gst = ""
        client_contact = ""

        # Flags and indices
        client_section_found = False
        client_done = False
        item_header_row_idx = None
        total_row_idx = None

        for r_idx, row in enumerate(rows):
            row_str = " ".join([cls._clean_str(c) for c in row if c is not None])
            row_str_upper = row_str.upper()

            # 1. Invoice No & Date detection
            for c_idx, cell in enumerate(row):
                c_str = cls._clean_str(cell)
                c_upper = c_str.upper()
                if "INVOICE NO" in c_upper:
                    # Look in next cell or row below
                    if c_idx + 1 < len(row) and cls._clean_str(row[c_idx + 1]):
                        invoice_no = cls._clean_str(row[c_idx + 1])
                    elif r_idx + 1 < len(rows) and cls._clean_str(rows[r_idx + 1][c_idx]):
                        invoice_no = cls._clean_str(rows[r_idx + 1][c_idx])

                if "INVOICE DATE" in c_upper:
                    if c_idx + 1 < len(row) and cls._clean_str(row[c_idx + 1]):
                        invoice_date = cls._clean_str(row[c_idx + 1])
                    elif r_idx + 1 < len(rows) and cls._clean_str(rows[r_idx + 1][c_idx]):
                        invoice_date = cls._clean_str(rows[r_idx + 1][c_idx])

            # 2. Items Header Detection: check if row has DESCRIPTION or PARTICULARS along with QTY, PRICE, RATE, or AMOUNT
            has_desc = any(t in row_str_upper for t in ("ITEM DESCRIPTION", "DESCRIPTION OF GOODS", "PARTICULARS", "DESCRIPTION"))
            has_qty_amt = any(t in row_str_upper for t in ("QTY", "QUANTITY", "AMOUNT", "PRICE", "RATE"))
            if has_desc and has_qty_amt and item_header_row_idx is None:
                item_header_row_idx = r_idx
                client_done = True

            # 3. Client Section Detection
            if any(term in row_str_upper for term in ("NAME & ADDRESS OF CLIENT", "NAME & ADDRESS", "CLIENT:", "BILLED TO:", "BUYER:")):
                client_section_found = True
                continue

            if client_section_found and not client_done:
                # Client column is typically Column B (index 1)
                first_val = ""
                for cell in row[1:2]:  # Strictly check client column (index 1)
                    if cls._clean_str(cell):
                        first_val = cls._clean_str(cell)
                        break

                if not first_val and cls._clean_str(row[0]):
                    first_val = cls._clean_str(row[0])

                if first_val:
                    fv_upper = first_val.upper()
                    if "ITEM DESCRIPTION" in fv_upper or "PARTICULARS" in fv_upper or (has_desc and has_qty_amt):
                        client_done = True
                    elif "GST" in fv_upper:
                        extracted = cls._extract_gst(first_val)
                        if not extracted:
                            extracted = cls._extract_gst(row_str)
                        if extracted:
                            client_gst = extracted
                    elif "KIND ATTN" in fv_upper or "ATTN:" in fv_upper:
                        client_contact = first_val.replace("Kind Attn:", "").replace("Attn:", "").strip()
                    elif not client_name and not any(term in fv_upper for term in ("SERVICE PROVIDER", "SCOTO", "INVOICE", "NAME & ADDRESS")):
                        client_name = cls._clean_customer_name(first_val)
                    elif client_name and not any(term in fv_upper for term in ("SERVICE PROVIDER", "SCOTO", "TEL", "KIND ATTN")):
                        client_address_lines.append(first_val)

            # 4. Totals Row Detection
            if item_header_row_idx is not None and r_idx > item_header_row_idx:
                if any(cls._clean_str(c).upper() in ("TOTAL", "SUB TOTAL", "SUBTOTAL") for c in row if c is not None):
                    total_row_idx = r_idx

        if not invoice_no and filename:
            # Fallback invoice no from filename
            clean_fname = re.sub(r"(?i)\.(xlsx?|xlsm)$", "", filename).strip()
            invoice_no = clean_fname

        if not invoice_no or not client_name:
            return None

        # Parse Address details
        full_address = ", ".join(client_address_lines)
        city = ""
        pincode = ""
        pin_match = re.search(r"\b(\d{6})\b", full_address) or re.search(r"\b(\d{3}\s*\d{3})\b", full_address)
        if pin_match:
            pincode = pin_match.group(1).replace(" ", "")

        # Try to infer City
        for line in client_address_lines:
            for part in line.split(","):
                part_clean = part.strip()
                if any(char.isdigit() for char in part_clean) and any(kw in part_clean.lower() for kw in ("coimbatore", "chennai", "erode", "tirupur", "bangalore", "mumbai", "delhi")):
                    city = re.sub(r"[0-9\-\.]", "", part_clean).strip()
                    break
            if city:
                break
        if not city:
            city = "Coimbatore"

        state_code = client_gst[:2] if len(client_gst) >= 2 else "33"
        state = GST_STATE_MAP.get(state_code, "Tamil Nadu")

        # Parse Line Items between item_header_row_idx and total_row_idx
        items = []
        if item_header_row_idx is not None:
            header_row = rows[item_header_row_idx]
            # Identify columns
            desc_col = None
            qty_col = None
            rate_col = None
            amt_col = None

            for c_idx, cell in enumerate(header_row):
                c_str = cls._clean_str(cell).upper()
                if "DESCRIPTION" in c_str or "PARTICULAR" in c_str:
                    desc_col = c_idx
                elif "UNIT" in c_str or "QTY" in c_str:
                    qty_col = c_idx
                elif "PRICE" in c_str or "RATE" in c_str:
                    rate_col = c_idx
                elif "AMOUNT" in c_str or "TOTAL" in c_str:
                    amt_col = c_idx

            end_idx = total_row_idx if total_row_idx is not None else len(rows)
            for r_idx in range(item_header_row_idx + 1, end_idx):
                row = rows[r_idx]
                if not any(row):
                    continue

                desc_val = cls._clean_str(row[desc_col]) if desc_col is not None and desc_col < len(row) else ""
                if not desc_val:
                    # Look across non-empty cells
                    desc_val = next((cls._clean_str(c) for c in row[:3] if cls._clean_str(c)), "")

                if not desc_val or any(k in desc_val.upper() for k in ("TOTAL", "CGST", "SGST", "IGST", "ROUND OFF", "GRAND TOTAL")):
                    continue

                # Extract HSN Code from Description (e.g., '998314 - Previses Year Service...' -> HSN '998314')
                hsn_code = ""
                hsn_match = re.search(r"\b(\d{4,8})\b", desc_val)
                if hsn_match:
                    hsn_code = hsn_match.group(1)

                clean_desc = re.sub(r"^\d{4,8}\s*[-:]*\s*", "", desc_val).strip() or desc_val

                qty = cls._to_float(row[qty_col]) if qty_col is not None and qty_col < len(row) else 1.0
                if qty <= 0:
                    qty = 1.0

                rate = cls._to_float(row[rate_col]) if rate_col is not None and rate_col < len(row) else 0.0
                amt = cls._to_float(row[amt_col]) if amt_col is not None and amt_col < len(row) else (qty * rate)

                if rate == 0.0 and amt > 0:
                    rate = amt / qty
                if amt == 0.0 and rate > 0:
                    amt = qty * rate

                if amt > 0:
                    items.append({
                        "item_desc": clean_desc,
                        "raw_desc": desc_val,
                        "hsn_code": hsn_code or "998314",
                        "uom": "No",
                        "qty": qty,
                        "rate": rate,
                        "taxable_amount": round(amt, 2),
                        "gst_rate": 18.0,
                    })

        # Parse Totals and Taxes
        subtotal = sum(i["taxable_amount"] for i in items)
        cgst_amt = 0.0
        sgst_amt = 0.0
        igst_amt = 0.0
        round_off = 0.0
        grand_total = 0.0

        for row in rows:
            row_str = " ".join([cls._clean_str(c) for c in row if c is not None]).upper()
            if "CGST" in row_str:
                for cell in reversed(row):
                    f = cls._to_float(cell)
                    if f > 0:
                        cgst_amt = f
                        break
            elif "SGST" in row_str:
                for cell in reversed(row):
                    f = cls._to_float(cell)
                    if f > 0:
                        sgst_amt = f
                        break
            elif "IGST" in row_str:
                for cell in reversed(row):
                    f = cls._to_float(cell)
                    if f > 0:
                        igst_amt = f
                        break
            elif "ROUND OFF" in row_str:
                for cell in reversed(row):
                    if cell is not None and str(cell).strip():
                        round_off = cls._to_float(cell)
                        break
            elif "GRAND TOTAL" in row_str or "TOTAL INVOICE VALUE" in row_str:
                for cell in reversed(row):
                    f = cls._to_float(cell)
                    if f > 0:
                        grand_total = f
                        break

        if grand_total == 0.0:
            if cgst_amt == 0.0 and sgst_amt == 0.0 and igst_amt == 0.0 and subtotal > 0:
                if state_code != "33":
                    igst_amt = round(subtotal * 0.18, 2)
                    cgst_amt = 0.0
                    sgst_amt = 0.0
                else:
                    cgst_amt = round(subtotal * 0.09, 2)
                    sgst_amt = round(subtotal * 0.09, 2)
                    igst_amt = 0.0
            grand_total = round(subtotal + cgst_amt + sgst_amt + igst_amt + round_off, 2)

        # Standardize Invoice Date to YYYY-MM-DD
        inv_date_standard = date.today().isoformat()
        if invoice_date:
            cleaned_d = invoice_date.split(" ")[0].strip()
            for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d-%B-%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                try:
                    inv_date_standard = datetime.strptime(cleaned_d, fmt).date().isoformat()
                    break
                except Exception:
                    pass

        return {
            "invoice_no": invoice_no,
            "invoice_date": inv_date_standard,
            "customer_name": client_name,
            "address1": client_address_lines[0] if client_address_lines else "",
            "address2": ", ".join(client_address_lines[1:]) if len(client_address_lines) > 1 else "",
            "city": city,
            "state": state,
            "pincode": pincode,
            "gst_no": client_gst,
            "pan_no": cls._extract_pan(client_gst),
            "contact_name": client_contact,
            "total_qty": sum(i["qty"] for i in items) if items else 1.0,
            "total_item_amount": round(subtotal, 2),
            "total_cgst": round(cgst_amt, 2),
            "total_sgst": round(sgst_amt, 2),
            "total_igst": round(igst_amt, 2),
            "round_off": round(round_off, 2),
            "net_amount": round(grand_total, 2),
            "items": items,
            "source_file": filename,
        }

    @classmethod
    def _parse_tabular_sheet(cls, sheet, filename: str) -> List[Dict[str, Any]]:
        """
        Parses a consolidated invoice register table (one row per item or invoice).
        """
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []

        header = [cls._clean_str(c).upper() for c in rows[0]]
        # Check if table headers look like invoice register
        if not any("INVOICE" in h for h in header) and not any("CUSTOMER" in h or "CLIENT" in h for h in header):
            return []

        inv_col = next((i for i, h in enumerate(header) if "INVOICE NO" in h or "INV NO" in h or "TRANS NO" in h), None)
        date_col = next((i for i, h in enumerate(header) if "DATE" in h), None)
        cust_col = next((i for i, h in enumerate(header) if "CUSTOMER" in h or "CLIENT" in h or "PARTY" in h), None)
        gst_col = next((i for i, h in enumerate(header) if "GST" in h), None)
        desc_col = next((i for i, h in enumerate(header) if "ITEM" in h or "DESC" in h or "PARTICULAR" in h), None)
        hsn_col = next((i for i, h in enumerate(header) if "HSN" in h or "SAC" in h), None)
        qty_col = next((i for i, h in enumerate(header) if "QTY" in h or "QUANTITY" in h), None)
        rate_col = next((i for i, h in enumerate(header) if "RATE" in h or "PRICE" in h), None)
        amt_col = next((i for i, h in enumerate(header) if "TAXABLE" in h or "AMOUNT" in h or "ITEM VALUE" in h), None)
        net_col = next((i for i, h in enumerate(header) if "NET" in h or "TOTAL" in h or "GRAND" in h), None)

        if inv_col is None or cust_col is None:
            return []

        invoices_map: Dict[str, Dict[str, Any]] = {}
        for r_idx in range(1, len(rows)):
            row = rows[r_idx]
            if not any(row):
                continue

            inv_no = cls._clean_str(row[inv_col])
            cust_name = cls._clean_customer_name(cls._clean_str(row[cust_col]))
            if not inv_no or not cust_name:
                continue

            inv_date = cls._clean_str(row[date_col]) if date_col is not None else date.today().isoformat()
            gst_no = cls._extract_gst(cls._clean_str(row[gst_col])) if gst_col is not None else ""
            desc = cls._clean_str(row[desc_col]) if desc_col is not None else "General Service"
            hsn = cls._clean_str(row[hsn_col]) if hsn_col is not None else "998314"
            qty = cls._to_float(row[qty_col]) if qty_col is not None else 1.0
            rate = cls._to_float(row[rate_col]) if rate_col is not None else 0.0
            amt = cls._to_float(row[amt_col]) if amt_col is not None else (qty * rate)

            if inv_no not in invoices_map:
                invoices_map[inv_no] = {
                    "invoice_no": inv_no,
                    "invoice_date": inv_date,
                    "customer_name": cust_name,
                    "address1": "",
                    "address2": "",
                    "city": "Coimbatore",
                    "state": GST_STATE_MAP.get(gst_no[:2], "Tamil Nadu") if gst_no else "Tamil Nadu",
                    "pincode": "",
                    "gst_no": gst_no,
                    "pan_no": cls._extract_pan(gst_no),
                    "contact_name": "",
                    "total_qty": 0.0,
                    "total_item_amount": 0.0,
                    "total_cgst": 0.0,
                    "total_sgst": 0.0,
                    "total_igst": 0.0,
                    "round_off": 0.0,
                    "net_amount": 0.0,
                    "items": [],
                    "source_file": filename,
                }

            inv = invoices_map[inv_no]
            inv["items"].append({
                "item_desc": desc,
                "raw_desc": desc,
                "hsn_code": hsn,
                "uom": "No",
                "qty": qty,
                "rate": rate,
                "taxable_amount": round(amt, 2),
                "gst_rate": 18.0,
            })
            inv["total_qty"] += qty
            inv["total_item_amount"] += amt

        # Compute totals for tabular invoices
        result = []
        for inv in invoices_map.values():
            sub = inv["total_item_amount"]
            cgst = round(sub * 0.09, 2)
            sgst = round(sub * 0.09, 2)
            inv["total_cgst"] = cgst
            inv["total_sgst"] = sgst
            inv["net_amount"] = round(sub + cgst + sgst, 2)
            result.append(inv)
        return result

    @classmethod
    def parse_uploaded_files(cls, files: List[Tuple[str, bytes]]) -> List[Dict[str, Any]]:
        """
        Parses up to 100 Excel files / sheets and returns a unified list of raw invoice documents.
        """
        all_invoices = []
        for filename, file_bytes in files:
            try:
                wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
                for sheet in wb.worksheets:
                    # 1. Try template parser
                    parsed_single = cls._parse_template_sheet(sheet, filename)
                    if parsed_single and parsed_single["items"]:
                        all_invoices.append(parsed_single)
                    else:
                        # 2. Try tabular parser
                        tabular_invoices = cls._parse_tabular_sheet(sheet, filename)
                        if tabular_invoices:
                            all_invoices.extend(tabular_invoices)
            except Exception as e:
                # Skip invalid or corrupted workbooks without aborting the batch
                continue
        return all_invoices

    @classmethod
    def reconcile_and_preview(
        cls,
        db: Session,
        files: List[Tuple[str, bytes]],
        c_code: str = "SCT",
        l_code: str = "UNIT I",
    ) -> Dict[str, Any]:
        """
        Dry-run analysis that builds the 3 preview tables:
        1. Invoices Master (Acc_Sales_Inv_Main)
        2. Line Items (Acc_Sales_Inv_Sub)
        3. Smart Customer Ledgers (Acc_Mst_Ledger)
        """
        raw_invoices = cls.parse_uploaded_files(files)
        if not raw_invoices:
            raise HTTPException(
                status_code=400,
                detail="No readable invoices found. Please verify the uploaded Excel files match the Scoto Invoice template or register layout.",
            )

        # 1. Load Existing Database Customers for Fast O(1) & Fuzzy Reconciliation
        db_ledgers = db.execute(text("""
            SELECT 
                LedgerCode,
                LedgerName,
                GSTNo,
                PanNo,
                City,
                State,
                ISNULL(OpeningBalance, 0) AS OpeningBalance
            FROM dbo.Acc_Mst_Ledger
            WHERE Status <> 'Delete'
        """)).mappings().all()

        gst_to_ledger = {}
        exact_name_to_ledger = {}
        all_db_ledgers = []

        for l in db_ledgers:
            l_dict = dict(l)
            code = l_dict["LedgerCode"]
            name = l_dict["LedgerName"].strip()
            clean_name = cls._clean_customer_name(name)
            gst = (l_dict["GSTNo"] or "").strip().upper()

            if gst and len(gst) == 15 and gst != "NA":
                gst_to_ledger[gst] = l_dict
            exact_name_to_ledger[clean_name.lower()] = l_dict
            exact_name_to_ledger[name.lower()] = l_dict
            all_db_ledgers.append({
                "code": code,
                "name": clean_name,
                "raw_name": name,
                "norm_name": cls._normalize_name(name),
                "gst": gst,
                "data": l_dict,
            })

        # 2. Load Existing Invoices to Detect Duplicates
        existing_inv_nos = set(
            r[0].strip()
            for r in db.execute(text("SELECT TransNo FROM dbo.Acc_Sales_Inv_Main WHERE Status <> 'Delete'")).fetchall()
            if r[0]
        )

        # 3. Load Existing Items from dbo.Mst_Item
        db_items = db.execute(text("""
            SELECT ItemCode, ItemType, ItemDescription, HSNCode, UOM 
            FROM dbo.Mst_Item 
            WHERE Status <> 'Delete'
        """)).mappings().all()

        hsn_to_item = {}
        desc_to_item = {}
        for itm in db_items:
            i_dict = dict(itm)
            hsn = (i_dict["HSNCode"] or "").strip()
            desc = (i_dict["ItemType"] or i_dict["ItemDescription"] or "").strip().lower()
            if hsn and hsn not in hsn_to_item:
                hsn_to_item[hsn] = i_dict
            if desc and desc not in desc_to_item:
                desc_to_item[desc] = i_dict

        # Determine next available customer ledger sequence for preview
        max_seq = 25
        row_seq = db.execute(text("""
            SELECT TOP 1 LedgerCode 
            FROM dbo.Acc_Mst_Ledger 
            WHERE LedgerCode LIKE 'CUS/%' 
            ORDER BY LedgerCode DESC
        """)).fetchone()
        if row_seq and row_seq[0]:
            digits = re.search(r"(\d+)$", str(row_seq[0]).strip())
            if digits:
                max_seq = int(digits.group(1))
        next_cust_seq = max_seq + 1

        # 4. Process Ledgers Map & Reconciliation
        unique_customers: Dict[str, Dict[str, Any]] = {}
        for inv in raw_invoices:
            c_raw_name = inv["customer_name"].strip()
            c_clean_name = cls._clean_customer_name(c_raw_name)
            c_gst = inv["gst_no"].strip().upper()
            lookup_key = c_gst if c_gst else c_clean_name.lower()

            if lookup_key not in unique_customers:
                matched_ledger = None
                match_type = "NEW_LEDGER"
                match_score = 0
                suggested_code = ""
                suggested_name = ""

                # Tier 1: Exact GST Match
                if c_gst and c_gst in gst_to_ledger:
                    matched_ledger = gst_to_ledger[c_gst]
                    match_type = "EXACT_GST"
                    match_score = 100
                    suggested_code = matched_ledger["LedgerCode"]
                    suggested_name = matched_ledger["LedgerName"]
                # Tier 2: Exact Name Match (clean or raw)
                elif c_clean_name.lower() in exact_name_to_ledger:
                    matched_ledger = exact_name_to_ledger[c_clean_name.lower()]
                    match_type = "EXACT_NAME"
                    match_score = 100
                    suggested_code = matched_ledger["LedgerCode"]
                    suggested_name = matched_ledger["LedgerName"]
                elif c_raw_name.lower() in exact_name_to_ledger:
                    matched_ledger = exact_name_to_ledger[c_raw_name.lower()]
                    match_type = "EXACT_NAME"
                    match_score = 100
                    suggested_code = matched_ledger["LedgerCode"]
                    suggested_name = matched_ledger["LedgerName"]
                # Tier 3: Fuzzy Name Similarity Match
                else:
                    norm_excel_name = cls._normalize_name(c_clean_name)
                    best_score = 0.0
                    best_match = None
                    for candidate in all_db_ledgers:
                        ratio = difflib.SequenceMatcher(None, norm_excel_name, candidate["norm_name"]).ratio()
                        if ratio > best_score:
                            best_score = ratio
                            best_match = candidate

                    if best_match and best_score >= 0.70:
                        matched_ledger = best_match["data"]
                        match_type = "FUZZY_NAME"
                        match_score = int(best_score * 100)
                        suggested_code = matched_ledger["LedgerCode"]
                        suggested_name = matched_ledger["LedgerName"]

                is_matched = (match_score >= 80)
                assigned_preview_code = suggested_code if is_matched else f"CUS/{next_cust_seq:05d}"
                if not is_matched:
                    next_cust_seq += 1

                unique_customers[lookup_key] = {
                    "lookup_key": lookup_key,
                    "customer_name": c_clean_name,
                    "excel_customer_name": c_raw_name,
                    "gst_no": c_gst,
                    "excel_gst": c_gst,
                    "pan_no": inv["pan_no"],
                    "excel_pan": inv["pan_no"],
                    "address1": inv["address1"],
                    "address2": inv["address2"],
                    "city": inv["city"],
                    "state": inv["state"],
                    "pincode": inv["pincode"],
                    "match_type": match_type,
                    "match_score": match_score,
                    "exists_in_db": is_matched,
                    "is_create_new": not is_matched,
                    "action": "MAP_EXISTING" if is_matched else "CREATE_NEW",
                    "suggested_ledger_code": suggested_code,
                    "suggested_ledger_name": suggested_name,
                    "matched_ledger_code": suggested_code if is_matched else "",
                    "selected_ledger_code": suggested_code if is_matched else "",
                    "assigned_code": assigned_preview_code,
                }

        # 5. Build Table 1 (Invoices Master) & Table 2 (Line Items)
        invoices_table = []
        items_table = []
        item_master_tracker = {}

        for inv_idx, inv in enumerate(raw_invoices):
            inv_no = inv["invoice_no"]
            c_name = cls._clean_customer_name(inv["customer_name"])
            c_gst = inv["gst_no"].strip().upper()
            lookup_key = c_gst if c_gst else c_name.lower()
            cust_rec = unique_customers.get(lookup_key, {})

            is_duplicate = inv_no in existing_inv_nos
            invoice_status = "Duplicate in DB (Blocked)" if is_duplicate else ("Ready" if cust_rec.get("selected_ledger_code") or cust_rec.get("is_create_new") else "Action Required")
            linked_code = cust_rec.get("selected_ledger_code") or cust_rec.get("matched_ledger_code") or cust_rec.get("assigned_code") or "Unmapped"

            invoices_table.append({
                "id": inv_idx + 1,
                "invoice_no": inv_no,
                "invoice_date": inv["invoice_date"],
                "customer_name": c_name,
                "gst_no": c_gst,
                "total_qty": inv["total_qty"],
                "total_item_amount": inv["total_item_amount"],
                "total_cgst": inv["total_cgst"],
                "total_sgst": inv["total_sgst"],
                "total_igst": inv["total_igst"],
                "round_off": inv["round_off"],
                "net_amount": inv["net_amount"],
                "items_count": len(inv["items"]),
                "items": inv["items"],
                "status": invoice_status,
                "is_duplicate": is_duplicate,
                "source_file": inv["source_file"],
                "linked_ledger_code": cust_rec.get("selected_ledger_code") or (f"New ({cust_rec.get('city')})" if cust_rec.get("is_create_new") else "Unmapped"),
            })

            # Process Line Items for Table 2
            for itm_idx, itm in enumerate(inv["items"]):
                clean_desc = itm["item_desc"]
                hsn = itm["hsn_code"]
                item_key = f"{hsn}_{clean_desc.lower()}"

                # Match against Mst_Item
                matched_item = hsn_to_item.get(hsn) or desc_to_item.get(clean_desc.lower())
                item_status = "Matched (Mst_Item)" if matched_item else "New Item / Service"
                resolved_item_code = matched_item["ItemCode"] if matched_item else f"ITM-{hsn}"

                if item_key not in item_master_tracker:
                    item_master_tracker[item_key] = {
                        "hsn_code": hsn,
                        "item_desc": clean_desc,
                        "raw_desc": itm["raw_desc"],
                        "matched": bool(matched_item),
                        "suggested_item_code": resolved_item_code,
                    }

                is_igst_inv = inv.get("total_igst", 0.0) > 0
                cgst_item = 0.0 if is_igst_inv else round(itm["taxable_amount"] * (itm["gst_rate"] / 200), 2)
                sgst_item = 0.0 if is_igst_inv else round(itm["taxable_amount"] * (itm["gst_rate"] / 200), 2)
                igst_item = round(itm["taxable_amount"] * (itm["gst_rate"] / 100), 2) if is_igst_inv else 0.0

                items_table.append({
                    "id": len(items_table) + 1,
                    "invoice_no": inv_no,
                    "item_desc": clean_desc,
                    "hsn_code": hsn,
                    "qty": itm["qty"],
                    "uom": itm["uom"],
                    "rate": itm["rate"],
                    "taxable_amount": itm["taxable_amount"],
                    "gst_rate": itm["gst_rate"],
                    "cgst": cgst_item,
                    "sgst": sgst_item,
                    "igst": igst_item,
                    "line_net": round(itm["taxable_amount"] + cgst_item + sgst_item + igst_item, 2),
                    "item_master_status": item_status,
                })

        return {
            "success": True,
            "summary": {
                "total_files": len(files),
                "total_invoices": len(invoices_table),
                "total_items": len(items_table),
                "total_taxable_amount": round(sum(inv["total_item_amount"] for inv in invoices_table), 2),
                "total_gst_amount": round(sum(inv["total_cgst"] + inv["total_sgst"] + inv["total_igst"] for inv in invoices_table), 2),
                "total_net_amount": round(sum(inv["net_amount"] for inv in invoices_table), 2),
                "matched_ledgers_count": sum(1 for c in unique_customers.values() if not c["is_create_new"]),
                "new_ledgers_count": sum(1 for c in unique_customers.values() if c["is_create_new"]),
                "duplicate_invoices_count": sum(1 for inv in invoices_table if inv["is_duplicate"]),
            },
            "invoices": invoices_table,
            "items": items_table,
            "ledgers": list(unique_customers.values()),
            "items_master": list(item_master_tracker.values()),
            "raw_payload": raw_invoices,
        }

    @classmethod
    def _generate_next_ledger_code(cls, db: Session) -> str:
        """Generates the next sequential customer ledger code like CUS/00008."""
        row = db.execute(text("""
            SELECT TOP 1 LedgerCode 
            FROM dbo.Acc_Mst_Ledger 
            WHERE LedgerCode LIKE 'CUS/%' 
            ORDER BY LedgerCode DESC
        """)).fetchone()

        max_seq = 6
        if row and row[0]:
            code_str = str(row[0]).strip()
            digits = re.search(r"(\d+)$", code_str)
            if digits:
                max_seq = int(digits.group(1))

        return f"CUS/{max_seq + 1:05d}"

    @classmethod
    def _generate_next_item_code(cls, db: Session) -> str:
        """Generates the next sequential item code like BOM/00058."""
        row = db.execute(text("""
            SELECT TOP 1 ItemCode 
            FROM dbo.Mst_Item 
            WHERE ItemCode LIKE 'BOM/%' 
            ORDER BY ItemCode DESC
        """)).fetchone()

        max_seq = 57
        if row and row[0]:
            code_str = str(row[0]).strip()
            digits = re.search(r"(\d+)$", code_str)
            if digits:
                max_seq = int(digits.group(1))

        return f"BOM/{max_seq + 1:05d}"

    @classmethod
    def commit_bulk_invoices(
        cls,
        db: Session,
        payload: Dict[str, Any],
        c_code: str = "SCT",
        l_code: str = "UNIT I",
        user_name: str = "ACCSCOTO",
    ) -> Dict[str, Any]:
        """
        Executes the transactional database commit:
        1. Auto-creates approved new ledgers in dbo.Acc_Mst_Ledger
        2. Optionally registers missing items in dbo.Mst_Item
        3. Inserts invoice headers into dbo.Acc_Sales_Inv_Main
        4. Inserts line items into dbo.Acc_Sales_Inv_Sub
        """
        invoices = payload.get("invoices", [])
        ledgers = payload.get("ledgers", [])
        auto_create_items = bool(payload.get("auto_create_items", False))
        now_str = datetime.now().strftime("%b  %d %Y %I:%M%p")

        if not invoices:
            raise HTTPException(status_code=400, detail="No invoices provided for commit.")

        created_ledgers_count = 0
        created_items_count = 0
        inserted_invoices_count = 0
        inserted_items_count = 0
        skipped_duplicates = []
        ledger_code_map: Dict[str, str] = {}

        try:
            # 1. Process and Create New Ledgers
            for led in ledgers:
                lookup_key = led.get("lookup_key")
                action = led.get("action")
                is_create_new = led.get("is_create_new", False)
                if action == "MAP_EXISTING":
                    is_create_new = False
                elif action == "CREATE_NEW":
                    is_create_new = True

                selected_code = led.get("selected_ledger_code") or led.get("matched_ledger_code")

                # If user mapped to an existing ledger:
                if selected_code and not is_create_new:
                    if lookup_key:
                        ledger_code_map[lookup_key] = selected_code
                    clean_n = cls._clean_customer_name(led.get("customer_name") or led.get("excel_customer_name"))
                    if clean_n:
                        ledger_code_map[clean_n.lower()] = selected_code
                    gst_val = (led.get("gst_no") or led.get("excel_gst") or "").strip().upper()
                    if gst_val:
                        ledger_code_map[gst_val] = selected_code
                elif is_create_new:
                    new_code = cls._generate_next_ledger_code(db)
                    cust_name = cls._clean_customer_name(led.get("customer_name") or led.get("excel_customer_name") or "New Customer")
                    gst_no = (led.get("gst_no") or led.get("excel_gst") or "").strip().upper()
                    pan_no = led.get("pan_no") or led.get("excel_pan") or (gst_no[2:12] if len(gst_no) == 15 else "")

                    insert_ledger_sql = """
                        INSERT INTO dbo.Acc_Mst_Ledger (
                            Ccode, Lcode, LedgerCode, LedgerGrpId, LedgerGrpName,
                            LedgerCategory, AccountType, LedgerType, LedgerName,
                            ChequePrintName, Add1, Add2, City, PinCode, State, Country,
                            GSTNo, PanNo, Status, IsActive, Approval_Status,
                            OpeningBalance, BalanceType, UserID, UserName, CreateOn
                        ) VALUES (
                            :ccode, :lcode, :code, '1', 'Customer',
                            'Sundry Debtors', 'Domestic Customer', 'Customer', :name,
                            :cheque_name, :add1, :add2, :city, :pin, :state, 'India',
                            :gst, :pan, 'Active', 'Yes', '1',
                            0.00, 'Dr', :user, :user, :now
                        )
                    """
                    db.execute(text(insert_ledger_sql), {
                        "ccode": c_code,
                        "lcode": l_code,
                        "code": new_code,
                        "name": cust_name,
                        "cheque_name": cust_name,
                        "add1": (led.get("address1") or "")[:750],
                        "add2": (led.get("address2") or "")[:750],
                        "city": (led.get("city") or "Coimbatore")[:750],
                        "pin": (led.get("pincode") or "")[:50],
                        "state": (led.get("state") or "Tamil Nadu")[:750],
                        "gst": gst_no[:150],
                        "pan": pan_no[:150],
                        "user": user_name,
                        "now": now_str,
                    })
                    if lookup_key:
                        ledger_code_map[lookup_key] = new_code
                    if cust_name:
                        ledger_code_map[cust_name.lower()] = new_code
                    if gst_no:
                        ledger_code_map[gst_no] = new_code
                    created_ledgers_count += 1

            # 2. Process Items in Mst_Item if auto_create_items is checked
            item_code_map: Dict[str, str] = {}
            if auto_create_items:
                raw_items = payload.get("items_master", [])
                for itm in raw_items:
                    if not itm.get("matched"):
                        next_itm_code = cls._generate_next_item_code(db)
                        desc = itm.get("item_desc", "Service").strip()
                        hsn = itm.get("hsn_code", "998314").strip()

                        db.execute(text("""
                            INSERT INTO dbo.Mst_Item (
                                Ccode, Lcode, ItemCode, ItemType, ItemDescription,
                                ProductType, HSNCode, UOM, Status, UserCode, UserName, CreatedOn
                            ) VALUES (
                                :ccode, :lcode, :code, :desc, :desc,
                                'Service', :hsn, 'No', 'Active', :user, :user, :now
                            )
                        """), {
                            "ccode": c_code,
                            "lcode": l_code,
                            "code": next_itm_code,
                            "desc": desc,
                            "hsn": hsn,
                            "user": user_name,
                            "now": now_str,
                        })
                        item_code_map[f"{hsn}_{desc.lower()}"] = next_itm_code
                        created_items_count += 1

            # 3. Insert Invoices (Acc_Sales_Inv_Main & Acc_Sales_Inv_Sub)
            for inv in invoices:
                inv_no = inv.get("invoice_no")
                inv_date = inv.get("invoice_date", date.today().isoformat())
                c_name = cls._clean_customer_name(inv.get("customer_name"))
                c_gst = inv.get("gst_no", "").strip().upper()
                lookup_key = c_gst if c_gst else c_name.lower()
                final_cust_code = (
                    ledger_code_map.get(lookup_key)
                    or (ledger_code_map.get(c_gst) if c_gst else None)
                    or ledger_code_map.get(c_name.lower())
                    or "CUS/00001"
                )

                # Compute Financial Year from TransDate
                dt = datetime.strptime(inv_date[:10], "%Y-%m-%d") if "-" in inv_date else datetime.now()
                start_yr = dt.year if dt.month >= 4 else dt.year - 1
                fin_year_val = f"{start_yr}-{start_yr + 1}"
                fin_year_code = "01"

                # Check if exists in DB to prevent duplicates
                existing = db.execute(
                    text("SELECT TOP 1 TransNo FROM dbo.Acc_Sales_Inv_Main WHERE TransNo = :v_no AND Status <> 'Delete'"),
                    {"v_no": inv_no},
                ).first()

                if existing:
                    # User requirement: "not allowed the duplicate" -> strictly block duplicate insertion
                    skipped_duplicates.append(inv_no)
                    continue

                # Header Insert
                db.execute(text("""
                    INSERT INTO dbo.Acc_Sales_Inv_Main (
                        Ccode, Lcode, FinYearCode, FinYearVal, TransNo, TransDate,
                        InvoiceNo, InvoiceDate, CustomerCode, CustomerName, GST,
                        TotalQty, TotalItemAmount, TotalCGSTAmount, TotalSGSTAmount,
                        TotalIGSTAmount, TotalAmount, RoundType, RoundOff, NetAmount,
                        Approval_Status, Status, UserName, UserCode, CreateOn
                    ) VALUES (
                        :ccode, :lcode, :fy_code, :fy_val, :trans_no, :trans_date,
                        :inv_no, :inv_date, :cust_code, :cust_name, :gst,
                        :qty, :item_amt, :cgst, :sgst,
                        :igst, :tot_amt, 0, :round_off, :net_amt,
                        'Approved', 'Active', :user, :user, :now
                    )
                """), {
                    "ccode": c_code,
                    "lcode": l_code,
                    "fy_code": fin_year_code,
                    "fy_val": fin_year_val,
                    "trans_no": inv_no,
                    "trans_date": inv_date,
                    "inv_no": inv_no,
                    "inv_date": inv_date,
                    "cust_code": final_cust_code,
                    "cust_name": c_name,
                    "gst": c_gst,
                    "qty": inv.get("total_qty", 1.0),
                    "item_amt": inv.get("total_item_amount", 0.0),
                    "cgst": inv.get("total_cgst", 0.0),
                    "sgst": inv.get("total_sgst", 0.0),
                    "igst": inv.get("total_igst", 0.0),
                    "tot_amt": inv.get("net_amount", 0.0),
                    "round_off": inv.get("round_off", 0.0),
                    "net_amt": inv.get("net_amount", 0.0),
                    "user": user_name,
                    "now": now_str,
                })
                inserted_invoices_count += 1

                # Line Items Insert
                items_for_inv = inv.get("items", [])
                for itm in items_for_inv:
                    hsn = itm.get("hsn_code", "998314")
                    desc = itm.get("item_desc", "Service")
                    item_key = f"{hsn}_{desc.lower()}"
                    resolved_item_code = item_code_map.get(item_key) or f"ITM-{hsn}"
                    taxable = itm.get("taxable_amount", 0.0)
                    rate_pct = itm.get("gst_rate", 18.0)
                    is_igst_inv = inv.get("total_igst", 0.0) > 0
                    if is_igst_inv:
                        cgst_line = 0.0
                        sgst_line = 0.0
                        igst_line = round(taxable * (rate_pct / 100), 2)
                    else:
                        cgst_line = round(taxable * (rate_pct / 200), 2)
                        sgst_line = round(taxable * (rate_pct / 200), 2)
                        igst_line = 0.0
                    net_line = round(taxable + cgst_line + sgst_line + igst_line, 2)

                    db.execute(text("""
                        INSERT INTO dbo.Acc_Sales_Inv_Sub (
                            Ccode, Lcode, FinYearCode, FinYearVal, TransNo, TransDate,
                            InvoiceNo, InvoiceDate, CustomerCode, CustomerName,
                            ItemCode, ProductType, HSNCode, Qty, Rate, ItemValue,
                            SerialNo, GST, CGST, SGST, IGST, NetAmount, Status,
                            UserName, Usercode, CreateOn
                        ) VALUES (
                            :ccode, :lcode, :fy_code, :fy_val, :trans_no, :trans_date,
                            :inv_no, :inv_date, :cust_code, :cust_name,
                            :item_code, :prod_type, :hsn, :qty, :rate, :val,
                            '-', :gst_pct, :cgst, :sgst, :igst, :net_amt, 'Active',
                            :user, :user, :now
                        )
                    """), {
                        "ccode": c_code,
                        "lcode": l_code,
                        "fy_code": fin_year_code,
                        "fy_val": fin_year_val,
                        "trans_no": inv_no,
                        "trans_date": inv_date,
                        "inv_no": inv_no,
                        "inv_date": inv_date,
                        "cust_code": final_cust_code,
                        "cust_name": c_name,
                        "item_code": resolved_item_code,
                        "prod_type": desc,
                        "hsn": hsn,
                        "qty": itm.get("qty", 1.0),
                        "rate": itm.get("rate", taxable),
                        "val": taxable,
                        "gst_pct": str(rate_pct),
                        "cgst": cgst_line,
                        "sgst": sgst_line,
                        "igst": igst_line,
                        "net_amt": net_line,
                        "user": user_name,
                        "now": now_str,
                    })
                    inserted_items_count += 1

            if inserted_invoices_count == 0 and skipped_duplicates:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invoices ({', '.join(skipped_duplicates)}) already exist in the database. Duplicate invoices are not allowed.",
                )

            db.commit()
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Bulk invoice commit failed and was safely rolled back: {str(e)}",
            )

        return {
            "success": True,
            "message": f"Bulk import complete! {inserted_invoices_count} Sales Invoices and {inserted_items_count} line items successfully saved.{f' ({len(skipped_duplicates)} duplicate(s) rejected)' if skipped_duplicates else ''}",
            "invoices_committed": inserted_invoices_count,
            "items_committed": inserted_items_count,
            "invoices_inserted": inserted_invoices_count,
            "items_inserted": inserted_items_count,
            "ledgers_created": created_ledgers_count,
            "items_created": created_items_count,
            "skipped_duplicates": skipped_duplicates,
        }
