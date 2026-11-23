"""
Filtering and search helpers for Scoto ERP.
Provides safe dynamic filtering and keyword search for both:
1. SQLAlchemy ORM Select queries
2. Raw T-SQL string queries
"""

from typing import Any, Dict, List, Mapping, Optional, Tuple
from sqlalchemy.sql import Select


def apply_filters(
    query: Select,
    filters: Mapping[str, Any],
    allowed_filters: Mapping[str, Any],
) -> Select:
    """
    Apply safe equality filters to a SQLAlchemy query.
    """
    for filter_name, value in filters.items():
        if value is None:
            continue

        column = allowed_filters.get(filter_name)
        if column is None:
            raise ValueError(f"Filtering by '{filter_name}' is not allowed")

        query = query.where(column == value)

    return query


def apply_search(
    query: Select,
    search: Optional[str],
    search_columns: List[Any],
) -> Select:
    """
    Apply case-insensitive search across approved columns in SQLAlchemy ORM query.
    """
    if not search or not search_columns:
        return query

    from sqlalchemy import or_

    search_value = f"%{search.strip()}%"
    conditions = [column.ilike(search_value) for column in search_columns]

    return query.where(or_(*conditions))


def build_raw_search(
    search: Optional[str],
    search_columns: List[str],
    params: Dict[str, Any],
    param_key: str = "search",
) -> str:
    """
    Constructs a safe raw SQL search clause (col1 LIKE :search OR col2 LIKE :search)
    and populates `params[param_key]`.

    Returns an SQL snippet e.g. " AND (col1 LIKE :search OR col2 LIKE :search)" or empty string.
    """
    if not search or not search.strip() or not search_columns:
        return ""

    clauses = [f"{col} LIKE :{param_key}" for col in search_columns]
    params[param_key] = f"%{search.strip()}%"
    return f" AND ({' OR '.join(clauses)})"
