"""
Sorting helper for Scoto ERP.
Provides safe dynamic sorting for both:
1. SQLAlchemy ORM Select queries
2. Raw T-SQL string queries with column whitelist protection
"""

from typing import Any, Dict, Optional, Tuple
from sqlalchemy.sql import Select


def apply_sorting(
    query: Select,
    sort_by: Optional[str],
    sort_order: str = "asc",
    allowed_sort_columns: Optional[Dict[str, Any]] = None,
) -> Select:
    """
    Apply safe dynamic sorting to a SQLAlchemy ORM / Core query using an allowlist.
    """
    if not sort_by:
        return query

    if not allowed_sort_columns:
        raise ValueError("Sorting columns are not configured")

    column = allowed_sort_columns.get(sort_by)

    if column is None:
        raise ValueError(f"Sorting by '{sort_by}' is not allowed")

    order = str(sort_order).lower()

    if order == "asc":
        return query.order_by(column.asc())
    if order == "desc":
        return query.order_by(column.desc())

    raise ValueError("Sort order must be 'asc' or 'desc'")


def resolve_raw_sort(
    sort_by: Optional[str],
    sort_order: Optional[str] = "desc",
    allowed_sort_columns: Optional[Dict[str, str]] = None,
    default_column: str = "TransDate",
    default_order: str = "DESC",
) -> Tuple[str, str]:
    """
    Validates requested sort parameters against an allowlist for raw SQL queries.
    Prevents SQL injection by only allowing mapped, whitelisted database column expressions.

    Returns: (safe_column_expression, safe_order_direction)
    """
    order = "ASC" if str(sort_order or "").strip().lower() == "asc" else "DESC"

    if not sort_by or not allowed_sort_columns:
        return default_column, default_order.upper()

    # Look up column in allowlist (case-insensitive lookup)
    lookup_key = sort_by.strip()
    safe_col = allowed_sort_columns.get(lookup_key)

    if not safe_col:
        # Check case-insensitively
        lower_map = {k.lower(): v for k, v in allowed_sort_columns.items()}
        safe_col = lower_map.get(lookup_key.lower())

    if not safe_col:
        # Fall back to default
        return default_column, default_order.upper()

    return safe_col, order
