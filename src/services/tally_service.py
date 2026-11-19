"""
Tally Upload & Ingestion Service
Faithfully ports the logic from Scoto Accounts .NET Rpt_Tally_Upload.aspx.cs
Interacts with db2 (MSSQL):
  - Ingestion Table: dbo.Acc_Trans_All
  - General Ledger Master: dbo.Acc_Mst_GeneralLedger
  - Financial Year: dbo.MstFinacialYear
"""
import io
import re
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
import openpyxl
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException


class TallyService:
    FIXED_COLUMNS = {
        "date",
        "particulars",
        "voucher type",
        "voucher no.",
        "voucher no",
        "narration",
        "gross total",
    }

    @staticmethod
    def _is_empty(value: Any) -> bool:
        if value is None:
            return True
        return str(value).strip() == ""

    @staticmethod
    def _find_header_row(ws) -> int:
        """Find row where Col 1 is 'Date' and Col 2 is 'Particulars'."""
        for row in range(1, min(ws.max_row + 1, 35)):
            val1 = str(ws.cell(row=row, column=1).value or "").strip().lower()
            val2 = str(ws.cell(row=row, column=2).value or "").strip().lower()
            if val1 == "date" and val2 == "particulars":
                return row
        return 0

    @staticmethod
    def _parse_transaction_date(cell_value: Any) -> Tuple[str, date]:
        """
        Parses various date representations from Tally Excel.
        Returns:
            trans_date_str: 'yyyyMMdd' (as expected by Acc_Trans_All)
            date_obj: python date object
        """
        if isinstance(cell_value, (datetime, date)):
            d = cell_value if isinstance(cell_value, date) else cell_value.date()
            return d.strftime("%Y%m%d"), d

        text_val = str(cell_value or "").strip()
        if not text_val:
            raise ValueError("Empty date value")

        # Try Excel serial date
        try:
            val_float = float(text_val)
            d = datetime.fromordinal(datetime(1899, 12, 30).toordinal() + int(val_float)).date()
            return d.strftime("%Y%m%d"), d
        except (ValueError, TypeError, OverflowError):
            pass

        formats = [
            "%d-%b-%y",
            "%d-%b-%Y",
            "%d/%m/%Y",
            "%d/%m/%y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d.%m.%Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(text_val, fmt).date()
                return dt.strftime("%Y%m%d"), dt
            except ValueError:
                continue

        match = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})$", text_val)
        if match:
            day, month, yr = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if yr < 100:
                yr += 2000
            dt = date(yr, month, day)
            return dt.strftime("%Y%m%d"), dt

        raise ValueError(f"Unable to parse date string '{text_val}'")

    @classmethod
    def _parse_debit_credit_amount(
        cls,
        amount_raw: Any,
        is_main_particulars: bool = False,
        voucher_type: str = "Sales",
    ) -> Tuple[Decimal, Decimal]:
        """
        Extracts credit and debit amounts from Tally value:
        Recognizes 'Cr', 'Dr', commas, negative signs, currency symbols.
        If suffix is not present, infers correctly according to accounting conventions.
        """
        if amount_raw is None:
            return Decimal("0.00"), Decimal("0.00")

        text_val = str(amount_raw).strip()
        if not text_val:
            return Decimal("0.00"), Decimal("0.00")

        is_credit = text_val.lower().endswith("cr")
        is_debit = text_val.lower().endswith("dr")

        cleaned = text_val
        if is_credit or is_debit:
            cleaned = cleaned[:-2].strip()

        cleaned = cleaned.replace(",", "").replace("₹", "").replace("Rs.", "").strip()

        try:
            amt = Decimal(cleaned)
        except Exception:
            return Decimal("0.00"), Decimal("0.00")

        amt = abs(amt)

        # 1. Explicit Dr / Cr suffix
        if is_debit:
            return Decimal("0.00"), amt
        elif is_credit:
            return amt, Decimal("0.00")

        # 2. No suffix - infer based on voucher type and whether it's main customer/vendor or revenue/tax ledger
        v_type = voucher_type.strip().lower()
        if is_main_particulars:
            if v_type in ("sales", "journal"):
                # Customer / Debtor is debited
                return Decimal("0.00"), amt
            elif v_type in ("receipt", "purchase", "contra"):
                # Customer is credited
                return amt, Decimal("0.00")
            elif v_type in ("payment",):
                return Decimal("0.00"), amt
            else:
                return Decimal("0.00"), amt
        else:
            # Dynamic ledger column (e.g. Sales, CGST, SGST, Bank)
            if v_type in ("sales",):
                # Revenue & tax outputs are credited
                return amt, Decimal("0.00")
            elif v_type in ("receipt",):
                # Bank / Cash receiving money is debited
                return Decimal("0.00"), amt
            elif v_type in ("payment",):
                # Bank / Cash paying money is credited
                return amt, Decimal("0.00")
            elif v_type in ("purchase",):
                # Expenses & purchases are debited
                return Decimal("0.00"), amt
            else:
                return amt, Decimal("0.00")

    @staticmethod
    def _get_financial_year(db2: Session, trans_date: date, c_code: str = "SCT", l_code: str = "UNIT I") -> Tuple[str, str]:
        """
        Resolves FinYearCode and FinYearVal from dbo.MstFinacialYear for the given date.
        """
        try:
            fy_start_year = trans_date.year if trans_date.month >= 4 else trans_date.year - 1
            fy_val_default = f"{fy_start_year}_{fy_start_year + 1}"

            fy_val_dash = f"{fy_start_year}-{fy_start_year + 1}"

            sql = """
                SELECT TOP 1 YearCode AS FinYearCode, FinacialYear AS FinYear
                FROM dbo.MstFinacialYear
                WHERE Ccode = :c_code
                  AND Lcode = :l_code
                  AND (
                      FinacialYear = :fy_val 
                      OR FinacialYear = :fy_dash 
                      OR REPLACE(FinacialYear, '_', '-') = :fy_dash
                  )
            """
            row = db2.execute(
                text(sql),
                {"c_code": c_code, "l_code": l_code, "fy_val": fy_val_default, "fy_dash": fy_val_dash},
            ).mappings().first()

            if row:
                return str(row["FinYearCode"]), str(row["FinYear"])

            sql_range = """
                SELECT TOP 1 YearCode AS FinYearCode, FinacialYear AS FinYear
                FROM dbo.MstFinacialYear
                WHERE Ccode = :c_code
                  AND Lcode = :l_code
                ORDER BY YearCode DESC
            """
            row_range = db2.execute(
                text(sql_range),
                {"c_code": c_code, "l_code": l_code},
            ).mappings().first()

            if row_range:
                return str(row_range["FinYearCode"]), str(row_range["FinYear"])

            return "1", fy_val_default
        except Exception:
            return "1", f"{trans_date.year}_{trans_date.year + 1}"

    @staticmethod
    def _load_ledger_cache(db2: Session, c_code: str = "SCT", l_code: str = "UNIT I") -> Dict[str, Dict[str, str]]:
        """Pre-loads active General Ledgers and Party Ledgers into memory for fast O(1) matching."""
        cache = {}

        # 1. Load General Ledgers (Sales, CGST, SGST, Banks, TDS, Expenses)
        gl_sql = """
            SELECT AccGenLdgCode, AccGenLdgName, AccLedgerHeaderCode, AccLedgerHeaderName
            FROM dbo.Acc_Mst_GeneralLedger
            WHERE ISNULL(Status, '') != 'Delete'
        """
        for r in db2.execute(text(gl_sql)).mappings().all():
            name_key = str(r["AccGenLdgName"] or "").strip().lower()
            if name_key:
                cache[name_key] = {
                    "code": str(r["AccGenLdgCode"] or "NA"),
                    "name": str(r["AccGenLdgName"] or ""),
                    "head_code": str(r["AccLedgerHeaderCode"] or "NA"),
                    "head_name": str(r["AccLedgerHeaderName"] or "NA"),
                }

        # 2. Load Party Sub-Ledgers (Customers CUS/ and Suppliers SUP/)
        party_sql = """
            SELECT LedgerCode, LedgerName, AccountTypeCode, AccountType
            FROM dbo.Acc_Mst_Ledger
            WHERE ISNULL(Status, '') != 'Delete'
        """
        for r in db2.execute(text(party_sql)).mappings().all():
            name_key = str(r["LedgerName"] or "").strip().lower()
            if name_key:
                cache[name_key] = {
                    "code": str(r["LedgerCode"] or "NA"),
                    "name": str(r["LedgerName"] or ""),
                    "head_code": str(r["AccountTypeCode"] or "1-2-9-1"),
                    "head_name": str(r["AccountType"] or "Domestic Customer"),
                }

        return cache

    @classmethod
    def parse_tally_workbook(
        cls,
        file_bytes: bytes,
        db2: Session,
        c_code: str = "SCT",
        l_code: str = "UNIT I",
    ) -> Dict[str, Any]:
        """
        Parses Tally Excel workbook and performs dry-run validation against General Ledger Master.
        """
        try:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid Excel file: {str(e)}")

        if not wb.sheetnames:
            raise HTTPException(status_code=400, detail="Excel workbook has no worksheets.")

        ledger_cache = cls._load_ledger_cache(db2, c_code, l_code)

        # Pre-query existing vouchers to identify duplicates during preview
        existing_vouchers_set = set()
        try:
            ex_rows = db2.execute(
                text("""
                    SELECT DISTINCT LTRIM(RTRIM(TransNo)), LTRIM(RTRIM(TransDate)), LOWER(LTRIM(RTRIM(TransType)))
                    FROM dbo.Acc_Trans_All
                    WHERE (Status IS NULL OR Status <> 'Delete')
                """)
            ).fetchall()
            for r in ex_rows:
                if r[0] and r[1] and r[2]:
                    existing_vouchers_set.add((str(r[0]), str(r[1]), str(r[2])))
        except Exception:
            pass

        processed_sheets = []
        parsed_vouchers = []
        total_debits = Decimal("0.00")
        total_credits = Decimal("0.00")
        unmatched_ledgers = set()
        matched_ledgers = set()

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            if ws.max_row < 2:
                continue

            header_row_idx = cls._find_header_row(ws)
            if header_row_idx == 0:
                continue

            col_map = {}
            for col_idx in range(1, ws.max_column + 1):
                col_name = str(ws.cell(row=header_row_idx, column=col_idx).value or "").strip()
                if col_name:
                    col_map[col_name.lower()] = (col_idx, col_name)

            req = ["date", "particulars", "voucher type", "gross total"]
            missing_req = [r for r in req if r not in col_map]
            if missing_req:
                continue

            voucher_no_col_info = col_map.get("voucher no.") or col_map.get("voucher no")
            if not voucher_no_col_info:
                continue

            date_col_idx = col_map["date"][0]
            particulars_col_idx = col_map["particulars"][0]
            vtype_col_idx = col_map["voucher type"][0]
            vno_col_idx = voucher_no_col_info[0]
            narration_col_idx = col_map.get("narration", (None, None))[0]
            gross_col_idx = col_map["gross total"][0]

            dynamic_cols = []
            for col_lower, (c_idx, c_orig) in col_map.items():
                if col_lower not in cls.FIXED_COLUMNS:
                    dynamic_cols.append((c_idx, c_orig))

            sheet_voucher_count = 0

            for r_idx in range(header_row_idx + 1, ws.max_row + 1):
                date_val = ws.cell(row=r_idx, column=date_col_idx).value
                particulars_val = str(ws.cell(row=r_idx, column=particulars_col_idx).value or "").strip()

                if cls._is_empty(date_val) or not particulars_val:
                    continue

                if particulars_val.lower() == "grand total":
                    continue

                vno_val = str(ws.cell(row=r_idx, column=vno_col_idx).value or "").strip()
                if not vno_val:
                    continue

                vtype_val = str(ws.cell(row=r_idx, column=vtype_col_idx).value or "").strip()
                narration_val = (
                    str(ws.cell(row=r_idx, column=narration_col_idx).value or "").strip()
                    if narration_col_idx
                    else ""
                )
                gross_val = ws.cell(row=r_idx, column=gross_col_idx).value

                try:
                    trans_date_str, date_obj = cls._parse_transaction_date(date_val)
                except Exception:
                    continue

                main_cr, main_dr = cls._parse_debit_credit_amount(
                    gross_val,
                    is_main_particulars=True,
                    voucher_type=vtype_val,
                )

                p_match = ledger_cache.get(particulars_val.lower())
                if p_match:
                    matched_ledgers.add(particulars_val)
                else:
                    unmatched_ledgers.add(particulars_val)

                voucher_entries = []

                # 1. Process dynamic ledger columns
                for dyn_col_idx, dyn_name in dynamic_cols:
                    dyn_val = ws.cell(row=r_idx, column=dyn_col_idx).value
                    if cls._is_empty(dyn_val):
                        continue

                    col_cr, col_dr = cls._parse_debit_credit_amount(
                        dyn_val,
                        is_main_particulars=False,
                        voucher_type=vtype_val,
                    )
                    if col_cr == 0 and col_dr == 0:
                        continue

                    d_match = ledger_cache.get(dyn_name.lower())
                    if d_match:
                        matched_ledgers.add(dyn_name)
                        col_ledger_code = d_match["code"]
                        col_head_code = d_match["head_code"]
                        col_head_name = d_match["head_name"]
                    else:
                        unmatched_ledgers.add(dyn_name)
                        col_ledger_code = "NA"
                        col_head_code = "NA"
                        col_head_name = "NA"

                    voucher_entries.append({
                        "ledger_name": dyn_name,
                        "ledger_code": col_ledger_code,
                        "acc_head_name": col_head_name,
                        "acc_head_code": col_head_code,
                        "credit_amount": float(col_cr),
                        "debit_amount": float(col_dr),
                        "is_matched": bool(d_match),
                    })
                    total_credits += col_cr
                    total_debits += col_dr

                # 2. Main Particulars Ledger Entry
                voucher_entries.append({
                    "ledger_name": particulars_val,
                    "ledger_code": p_match["code"] if p_match else "NA",
                    "acc_head_name": p_match["head_name"] if p_match else "NA",
                    "acc_head_code": p_match["head_code"] if p_match else "NA",
                    "credit_amount": float(main_cr),
                    "debit_amount": float(main_dr),
                    "is_matched": bool(p_match),
                })
                total_credits += main_cr
                total_debits += main_dr

                is_in_db = (str(vno_val).strip(), str(trans_date_str).strip(), str(vtype_val).strip().lower()) in existing_vouchers_set

                parsed_vouchers.append({
                    "sheet_name": sheet_name,
                    "row_number": r_idx,
                    "trans_date": trans_date_str,
                    "trans_date_display": date_obj.strftime("%d-%b-%Y"),
                    "voucher_no": vno_val,
                    "voucher_type": vtype_val,
                    "particulars": particulars_val,
                    "narration": narration_val,
                    "gross_total": float(main_cr if main_cr > 0 else main_dr),
                    "is_already_in_db": is_in_db,
                    "entries": voucher_entries,
                })
                sheet_voucher_count += 1

            if sheet_voucher_count > 0:
                processed_sheets.append({
                    "sheet_name": sheet_name,
                    "voucher_count": sheet_voucher_count,
                })

        already_in_db_cnt = sum(1 for v in parsed_vouchers if v.get("is_already_in_db"))

        return {
            "summary": {
                "total_sheets": len(processed_sheets),
                "total_vouchers": len(parsed_vouchers),
                "already_in_db_count": already_in_db_cnt,
                "new_vouchers_count": len(parsed_vouchers) - already_in_db_cnt,
                "total_entries": sum(len(v["entries"]) for v in parsed_vouchers),
                "total_debit": float(total_debits),
                "total_credit": float(total_credits),
                "is_balanced": abs(total_debits - total_credits) < Decimal("0.05"),
                "matched_ledgers_count": len(matched_ledgers),
                "unmatched_ledgers_count": len(unmatched_ledgers),
            },
            "sheets": processed_sheets,
            "vouchers": parsed_vouchers,
            "unmatched_ledgers": sorted(list(unmatched_ledgers)),
        }

    @classmethod
    def ingest_tally_workbook(
        cls,
        file_bytes: bytes,
        db2: Session,
        c_code: str = "SCT",
        l_code: str = "UNIT I",
        user_id: str = "ACCSCOTO",
        user_name: str = "ACCSCOTO",
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes actual DB insertion into dbo.Acc_Trans_All matching .NET Rpt_Tally_Upload.aspx.cs.
        Includes smart deduplication to prevent duplicate entries if an Excel file is uploaded multiple times.
        """
        parsed = cls.parse_tally_workbook(file_bytes, db2, c_code, l_code)
        vouchers = parsed["vouchers"]

        if not vouchers:
            raise HTTPException(
                status_code=400,
                detail="No voucher records found in the Excel file.",
            )

        inserted_count = 0
        inserted_vouchers_count = 0
        skipped_duplicate_vouchers = 0
        skipped_duplicate_entries = 0
        overwritten_vouchers_count = 0
        now_str = datetime.now().strftime("%b %d %Y %I:%M%p")
        fy_cache: Dict[str, Tuple[str, str]] = {}

        insert_sql = """
            INSERT INTO dbo.Acc_Trans_All (
                CCode, LCode, FinYearCode, FinYearVal,
                TransNo, TransDate, LeaderCode, LedgerName,
                AccHeadCode, AccHeadName, TransType,
                CreditAmount, DebitAmount, Narration,
                Status, UserId, UserName, CreatedBy
            ) VALUES (
                :ccode, :lcode, :fy_code, :fy_val,
                :trans_no, :trans_date, :leader_code, :ledger_name,
                :acc_head_code, :acc_head_name, :trans_type,
                :credit_amt, :debit_amt, :narration,
                'Add', :user_id, :user_name, :created_by
            )
        """

        try:
            for v in vouchers:
                trans_date_str = v["trans_date"]
                v_no = str(v["voucher_no"]).strip()
                v_type = str(v["voucher_type"]).strip()

                # Deduplication check: check if voucher already exists in Acc_Trans_All
                existing_check = db2.execute(
                    text("""
                        SELECT TOP 1 TransNo
                        FROM dbo.Acc_Trans_All
                        WHERE TransNo = :vno
                          AND TransDate = :vdate
                          AND TransType = :vtype
                          AND (Status IS NULL OR Status <> 'Delete')
                    """),
                    {"vno": v_no, "vdate": trans_date_str, "vtype": v_type},
                ).first()

                if existing_check:
                    if overwrite:
                        db2.execute(
                            text("""
                                UPDATE dbo.Acc_Trans_All
                                SET Status = 'Delete'
                                WHERE TransNo = :vno
                                  AND TransDate = :vdate
                                  AND TransType = :vtype
                                  AND (Status IS NULL OR Status <> 'Delete')
                            """),
                            {"vno": v_no, "vdate": trans_date_str, "vtype": v_type},
                        )
                        overwritten_vouchers_count += 1
                    else:
                        skipped_duplicate_vouchers += 1
                        skipped_duplicate_entries += len(v["entries"])
                        continue

                if trans_date_str not in fy_cache:
                    dt = datetime.strptime(trans_date_str, "%Y%m%d").date()
                    fy_cache[trans_date_str] = cls._get_financial_year(db2, dt, c_code, l_code)

                fy_code, fy_val = fy_cache[trans_date_str]

                for entry in v["entries"]:
                    db2.execute(
                        text(insert_sql),
                        {
                            "ccode": c_code,
                            "lcode": l_code,
                            "fy_code": fy_code,
                            "fy_val": fy_val,
                            "trans_no": v_no,
                            "trans_date": trans_date_str,
                            "leader_code": entry["ledger_code"],
                            "ledger_name": entry["ledger_name"],
                            "acc_head_code": entry["acc_head_code"],
                            "acc_head_name": entry["acc_head_name"],
                            "trans_type": v_type,
                            "credit_amt": entry["credit_amount"],
                            "debit_amt": entry["debit_amount"],
                            "narration": v["narration"],
                            "user_id": user_id,
                            "user_name": user_name,
                            "created_by": now_str,
                        },
                    )
                    inserted_count += 1
                inserted_vouchers_count += 1

            db2.commit()
        except Exception as e:
            db2.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Tally upload transaction failed during database insert: {str(e)}",
            )

        if skipped_duplicate_vouchers > 0:
            msg = (
                f"Upload processed: {inserted_vouchers_count} vouchers inserted ({inserted_count} entries), "
                f"{skipped_duplicate_vouchers} duplicate vouchers skipped (already present)."
            )
        else:
            msg = f"Tally Excel uploaded successfully: {inserted_vouchers_count} vouchers inserted ({inserted_count} entries)."

        return {
            "success": True,
            "message": msg,
            "sheets_processed": len(parsed["sheets"]),
            "vouchers_processed": len(vouchers),
            "vouchers_inserted": inserted_vouchers_count,
            "entries_inserted": inserted_count,
            "duplicate_vouchers_skipped": skipped_duplicate_vouchers,
            "duplicate_entries_skipped": skipped_duplicate_entries,
            "overwritten_vouchers_count": overwritten_vouchers_count,
            "total_debit": parsed["summary"]["total_debit"],
            "total_credit": parsed["summary"]["total_credit"],
            "unmatched_ledgers": parsed["unmatched_ledgers"],
        }

    @staticmethod
    def get_recent_transactions(
        db2: Session,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
        trans_type: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        fin_year: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves ingested transactions from dbo.Acc_Trans_All.
        """
        where_clauses = ["ISNULL(Status, '') != 'Delete'"]
        params = {"limit": limit, "offset": offset}

        if search and search.strip():
            where_clauses.append(
                "(TransNo LIKE :search OR LedgerName LIKE :search OR Narration LIKE :search)"
            )
            params["search"] = f"%{search.strip()}%"

        if trans_type and trans_type.strip() and trans_type.upper() != "ALL":
            where_clauses.append("TransType = :trans_type")
            params["trans_type"] = trans_type.strip()

        if from_date and from_date.strip():
            f_clean = from_date.replace("-", "").strip()
            where_clauses.append("TransDate >= :from_date")
            params["from_date"] = f_clean

        if to_date and to_date.strip():
            t_clean = to_date.replace("-", "").strip()
            where_clauses.append("TransDate <= :to_date")
            params["to_date"] = t_clean

        if fin_year and fin_year.upper() != "ALL":
            fy_dash = fin_year.replace("_", "-").strip()
            fy_under = fin_year.replace("-", "_").strip()
            parts = fy_dash.split("-")
            if len(parts) == 2 and len(parts[0]) == 4 and len(parts[1]) == 4:
                d_start = f"{parts[0]}0401"
                d_end = f"{parts[1]}0331"
                where_clauses.append("""(
                    REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') = :fy_dash
                    OR REPLACE(LTRIM(RTRIM(FinYearVal)), '-', '_') = :fy_under
                    OR FinYearCode = :fin_year
                    OR (
                        REPLACE(REPLACE(TransDate, '-', ''), '/', '') >= :d_start
                        AND REPLACE(REPLACE(TransDate, '-', ''), '/', '') <= :d_end
                    )
                )""")
                params["fy_dash"] = fy_dash
                params["fy_under"] = fy_under
                params["fin_year"] = fin_year
                params["d_start"] = d_start
                params["d_end"] = d_end
            else:
                where_clauses.append("(FinYearVal = :fin_year OR FinYearCode = :fin_year)")
                params["fin_year"] = fin_year

        where_sql = " AND ".join(where_clauses)

        count_sql = f"SELECT COUNT(*) AS total FROM dbo.Acc_Trans_All WHERE {where_sql}"
        total = db2.execute(text(count_sql), params).scalar() or 0

        data_sql = f"""
            SELECT
                TransNo, TransDate, LeaderCode, LedgerName,
                AccHeadCode, AccHeadName, TransType,
                CreditAmount, DebitAmount, Narration,
                Status, UserId, UserName, CreatedBy, FinYearVal
            FROM dbo.Acc_Trans_All
            WHERE {where_sql}
            ORDER BY TransDate DESC, TransNo DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """
        rows = db2.execute(text(data_sql), params).mappings().all()

        results = []
        for r in rows:
            d_raw = str(r["TransDate"] or "")
            if len(d_raw) == 8 and d_raw.isdigit():
                d_display = f"{d_raw[6:8]}-{d_raw[4:6]}-{d_raw[0:4]}"
            else:
                d_display = d_raw

            results.append({
                "trans_no": str(r["TransNo"] or ""),
                "trans_date": d_raw,
                "trans_date_display": d_display,
                "ledger_code": str(r["LeaderCode"] or "NA"),
                "ledger_name": str(r["LedgerName"] or ""),
                "acc_head_code": str(r["AccHeadCode"] or "NA"),
                "acc_head_name": str(r["AccHeadName"] or "NA"),
                "trans_type": str(r["TransType"] or ""),
                "credit_amount": float(r["CreditAmount"] or 0),
                "debit_amount": float(r["DebitAmount"] or 0),
                "narration": str(r["Narration"] or ""),
                "status": str(r["Status"] or "Add"),
                "created_by": str(r["CreatedBy"] or ""),
                "fin_year": str(r["FinYearVal"] or ""),
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "records": results,
        }

    @staticmethod
    def generate_sample_template() -> bytes:
        """
        Generates an authentic sample Tally Excel file matching the format expected by Scoto Accounts.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sample Customer"

        headers_info = [
            ["Scoto Systec Private Limited"],
            ["No: 61-A, First Floor, HM Enclave, 50 Feet Road, Ramanathapuram, Coimbatore"],
            ["Sample Customer Textiles Pvt Ltd"],
            ["Ledger Account"],
            ["1-Apr-2025 to 31-Mar-2026"],
        ]
        for row_idx, info in enumerate(headers_info, 1):
            ws.cell(row=row_idx, column=1, value=info[0])

        cols = [
            "Date", "Particulars", "Voucher Type", "Voucher No.", "Narration",
            "Gross Total", "Sales", "CGST Output 9%", "SGST Output 9%", "City Union Bank"
        ]
        for col_idx, col_name in enumerate(cols, 1):
            cell = ws.cell(row=7, column=col_idx, value=col_name)
            cell.font = openpyxl.styles.Font(bold=True)

        ws.append([
            "10-Apr-2025", "Sample Customer Textiles Pvt Ltd", "Sales", "101", "Goods dispatched",
            "118000.00 Cr", "100000.00", "9000.00", "9000.00", None
        ])
        ws.append([
            "16-Apr-2025", "Sample Customer Textiles Pvt Ltd", "Receipt", "102", "BY NEFT TRF: AXSK251060009707",
            "118000.00 Dr", None, None, None, "118000.00"
        ])

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()
