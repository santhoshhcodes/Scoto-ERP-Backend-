"""
Transaction Number and Financial Year Helpers for Quotations, Proformas, and Sales Invoices.

Standard numbering formats:
  - Quotation:       SQ{finCode}-{seq:03d}   (e.g., SQ2627-001)
  - Proforma:        SP{finCode}-{seq:03d}   (e.g., SP2627-001)
  - Sales Invoice:   SI{finCode}-{seq:03d}   (e.g., SI2627-001)

Where:
  - 'SQ' = Scoto Quotation
  - 'SP' = Scoto Proforma
  - 'SI' = Scoto Invoice
  - '2627' = Financial Year Code (e.g. 2627 for FY 2026-2027, 2526 for FY 2025-2026)
  - '001' = Unique 3-digit sequential number for that financial year
"""

import re
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_fin_year_code(fin_year: Optional[str] = None, fallback_date: Optional[Any] = None) -> str:
    """
    Returns the 4-digit financial year short code (e.g. '2627' for FY 2026-2027, '2526' for FY 2025-2026).
    """
    if fin_year and str(fin_year).strip().upper() not in ("ALL", "", "NONE", "NULL"):
        cleaned = re.sub(r"(?i)\bfy[:\s]*", "", str(fin_year)).strip().replace("_", "-")
        # Match '2026-2027' or '2026_2027'
        m4 = re.search(r"(\d{4})[-_](\d{4})", cleaned)
        if m4:
            return f"{m4.group(1)[-2:]}{m4.group(2)[-2:]}"
        # Match '26-27' or '26/27'
        m2 = re.search(r"(\d{2})[-/](\d{2})", cleaned)
        if m2:
            return f"{m2.group(1)}{m2.group(2)}"
        # Match plain 4 digits like '2627'
        if re.match(r"^\d{4}$", cleaned):
            return cleaned

    # Fallback to date (in India: Apr 1 to Mar 31)
    d = fallback_date or date.today()
    if isinstance(d, str):
        try:
            d = datetime.strptime(d[:10], "%Y-%m-%d").date()
        except Exception:
            d = date.today()
    elif isinstance(d, datetime):
        d = d.date()
    elif not isinstance(d, date):
        d = date.today()

    year = d.year
    month = d.month
    start_year = year if month >= 4 else year - 1
    end_year = start_year + 1
    return f"{str(start_year)[-2:]}{str(end_year)[-2:]}"


def get_full_fin_year(fin_year: Optional[str] = None, fallback_date: Optional[Any] = None) -> str:
    """
    Returns full 'YYYY-YYYY' financial year string (e.g. '2026-2027').
    """
    if fin_year and str(fin_year).strip().upper() not in ("ALL", "", "NONE", "NULL"):
        cleaned = re.sub(r"(?i)\bfy[:\s]*", "", str(fin_year)).strip().replace("_", "-")
        m4 = re.search(r"(\d{4})[-_](\d{4})", cleaned)
        if m4:
            return f"{m4.group(1)}-{m4.group(2)}"
        m2 = re.search(r"(\d{2})[-/](\d{2})", cleaned)
        if m2:
            return f"20{m2.group(1)}-20{m2.group(2)}"
        if re.match(r"^\d{4}$", cleaned):
            y1 = int(cleaned[:2]) + 2000
            y2 = int(cleaned[2:]) + 2000
            return f"{y1}-{y2}"

    d = fallback_date or date.today()
    if isinstance(d, str):
        try:
            d = datetime.strptime(d[:10], "%Y-%m-%d").date()
        except Exception:
            d = date.today()
    elif isinstance(d, datetime):
        d = d.date()
    elif not isinstance(d, date):
        d = date.today()

    year = d.year
    month = d.month
    start_year = year if month >= 4 else year - 1
    end_year = start_year + 1
    return f"{start_year}-{end_year}"


def generate_next_trans_no(
    db: Session,
    prefix: str,
    table_name: str,
    fin_year: Optional[str] = None,
    fallback_date: Optional[Any] = None,
) -> str:
    """
    Generates the next sequential TransNo for a given table and prefix.
    Prefix:
      - 'SQ' for Acc_Quotation_Main
      - 'SP' for Acc_Proforma_Inv_Main
      - 'SI' for Acc_Sales_Inv_Main

    Format: {prefix}{finCode}-{next_seq:03d} (e.g. SQ2627-004, SP2627-005, SI2627-027).
    """
    prefix = prefix.strip().upper()
    fin_code = get_fin_year_code(fin_year, fallback_date)
    pattern_pfx = f"{prefix}{fin_code}-"

    sql = f"""
        SELECT TransNo
        FROM {table_name}
        WHERE TransNo LIKE :search_pfx
    """
    rows = db.execute(text(sql), {"search_pfx": f"{pattern_pfx}%"}).fetchall()

    max_seq = 0
    regex = re.compile(rf"^{prefix}{fin_code}-(\d+)", re.IGNORECASE)
    for r in rows:
        t_no = str(r[0] or "").strip()
        m = regex.match(t_no)
        if m:
            try:
                seq = int(m.group(1))
                if seq > max_seq:
                    max_seq = seq
            except ValueError:
                pass

    next_seq = max_seq + 1
    return f"{pattern_pfx}{next_seq:03d}"


def check_trans_no_exists(
    db: Session,
    table_name: str,
    trans_no: str,
    exclude_trans_no: Optional[str] = None,
) -> bool:
    """
    Checks if a TransNo already exists in the given database table (ignoring soft-deleted rows).
    """
    t_no = (trans_no or "").strip()
    if not t_no:
        return False

    query = f"""
        SELECT 1
        FROM {table_name}
        WHERE TransNo = :trans_no
          AND (Status IS NULL OR Status <> 'Delete')
    """
    params = {"trans_no": t_no}

    if exclude_trans_no and exclude_trans_no.strip():
        query += " AND TransNo <> :exclude_trans_no"
        params["exclude_trans_no"] = exclude_trans_no.strip()

    row = db.execute(text(query), params).first()
    return row is not None
