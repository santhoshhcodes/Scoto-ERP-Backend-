"""
Helpers Package for Scoto Backend.
Provides domain-specific helper utilities and aliases standard utility functions.
Developers can use either `from src.helpers import ...` or `from src.utils import ...`.
"""

from typing import Any, Dict, Optional

# Re-export all standard utils
from src.utils import *


def format_employee_full_name(
    row_or_employee: Any,
    default_code: str = "Unknown",
) -> str:
    """
    Format employee full name from a dict or ORM object.
    Prefers DisplayName if set, otherwise joins FirstName, MiddleName, and LastName.
    """
    if row_or_employee is None:
        return default_code

    if isinstance(row_or_employee, dict):
        display = row_or_employee.get("DisplayName")
        if display and str(display).strip():
            return str(display).strip()

        first = str(row_or_employee.get("FirstName") or "").strip()
        middle = str(row_or_employee.get("MiddleName") or "").strip()
        last = str(row_or_employee.get("LastName") or "").strip()
        code = str(row_or_employee.get("EmployeeCode") or default_code).strip()
    else:
        display = getattr(row_or_employee, "DisplayName", None)
        if display and str(display).strip():
            return str(display).strip()

        first = str(getattr(row_or_employee, "FirstName", "") or "").strip()
        middle = str(getattr(row_or_employee, "MiddleName", "") or "").strip()
        last = str(getattr(row_or_employee, "LastName", "") or "").strip()
        code = str(getattr(row_or_employee, "EmployeeCode", default_code) or default_code).strip()

    parts = [p for p in (first, middle, last) if p]
    name = " ".join(parts).strip()
    return name or code
