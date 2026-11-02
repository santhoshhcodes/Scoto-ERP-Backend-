"""
Date and time utility functions for attendance, financial periods, and reporting.
"""

import calendar
from datetime import date, datetime, time, timedelta
from typing import Any, Optional, Tuple


def format_duration_hhmm(total_minutes: int) -> str:
    """Format total minutes into 'HH:MM' string."""
    if total_minutes is None or total_minutes < 0:
        return "00:00"
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def format_duration_human(total_minutes: int) -> str:
    """Format total minutes into 'X Hrs Y Min' string."""
    if total_minutes is None or total_minutes <= 0:
        return "0 Hrs 0 Min"
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours} Hrs {minutes} Min"


def parse_date_safe(val: Any) -> Optional[date]:
    """Safely parse various date representations (str, date, datetime) into a date object."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        # Try common formats
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(val[:10], fmt).date()
            except ValueError:
                continue
    return None


def parse_datetime_safe(val: Any) -> Optional[datetime]:
    """Safely parse various datetime representations into a datetime object."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime.combine(val, time.min)
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d-%m-%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
        ):
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                continue
    return None


def parse_time_safe(val: Any) -> Optional[time]:
    """Safely parse a time representation into a time object."""
    if val is None:
        return None
    if isinstance(val, time):
        return val
    if isinstance(val, datetime):
        return val.time()
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"):
            try:
                return datetime.strptime(val, fmt).time()
            except ValueError:
                continue
    return None


def get_month_date_range(year: int, month: int) -> Tuple[date, date]:
    """Return the start date and end date for a given year and month."""
    _, last_day = calendar.monthrange(year, month)
    return date(year, month, 1), date(year, month, last_day)


def month_dates(period_month: str) -> Tuple[date, date]:
    """
    Parse a 'YYYY-MM' period string and return:
    (first_day_of_month, first_day_of_next_month)
    Convenient for range queries: [start, end).
    """
    year, month = map(int, period_month.split("-"))
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


def get_financial_year(target_date: Optional[date] = None) -> str:
    """
    Get the Indian financial year string (e.g. '2025-2026') for a given date.
    Indian FY runs from April 1 to March 31.
    """
    d = target_date or date.today()
    if d.month >= 4:
        start_year = d.year
        end_year = d.year + 1
    else:
        start_year = d.year - 1
        end_year = d.year
    return f"{start_year}-{end_year}"


def get_financial_year_dates(fin_year_str: str) -> Tuple[date, date]:
    """
    Get start (Apr 1) and end (Mar 31) dates from a financial year string like '2025-2026' or '25-26'.
    """
    parts = fin_year_str.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid financial year format: {fin_year_str}")

    start_year = int(parts[0])
    if start_year < 100:
        start_year += 2000

    end_year = int(parts[1])
    if end_year < 100:
        end_year += 2000

    return date(start_year, 4, 1), date(end_year, 3, 31)
