"""
Pagination helper for Scoto ERP.
Provides dual support:
1. ORM Select queries (for Employee and SQLAlchemy ORM models)
2. Raw T-SQL queries with native Microsoft SQL Server `OFFSET ... FETCH NEXT`
Guarantees 100% backward compatibility for all response formats.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select


def get_offset(page: int, page_size: int) -> int:
    """Calculate SQL OFFSET safely."""
    return max(0, (page - 1) * page_size)


def get_total_pages(total_records: int, page_size: int) -> int:
    """Calculate total pages."""
    if total_records <= 0 or page_size <= 0:
        return 0
    return (total_records + page_size - 1) // page_size


def build_pagination_envelope(
    records: List[Any],
    total_records: int,
    page: int,
    page_size: int,
) -> Dict[str, Any]:
    """
    Constructs a standardized, backwards-compatible pagination response.
    Includes both .data and .items, and .count and .total.
    """
    total_pages = get_total_pages(total_records, page_size)
    pagination = {
        "page": page,
        "page_size": page_size,
        "total_records": total_records,
        "total": total_records,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
        "has_prev": page > 1,
    }

    return {
        "success": True,
        "count": total_records,
        "total": total_records,
        "data": records,
        "items": records,
        "pagination": pagination,
    }


def paginate_query(
    db: Session,
    query: Select,
    page: int = 1,
    page_size: int = 20,
    count_query: Optional[Select] = None,
    include_total: bool = True,
) -> Dict[str, Any]:
    """
    Execute a SQLAlchemy ORM / Core SELECT query with pagination.
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    elif page_size > 500:
        page_size = 500

    offset = get_offset(page, page_size)

    if include_total:
        if count_query is not None:
            total_records = db.execute(count_query).scalar_one()
        else:
            count_statement = select(func.count()).select_from(
                query.order_by(None).subquery()
            )
            total_records = db.execute(count_statement).scalar_one()

        paginated_query = query.limit(page_size).offset(offset)
        result = db.execute(paginated_query)
        # Attempt scalars first; fallback to mappings
        try:
            records = result.scalars().all()
        except Exception:
            records = [dict(r) for r in result.mappings().all()]

        return build_pagination_envelope(
            records=records,
            total_records=total_records,
            page=page,
            page_size=page_size,
        )
    else:
        paginated_query = query.limit(page_size + 1).offset(offset)
        result = db.execute(paginated_query)
        try:
            records = list(result.scalars().all())
        except Exception:
            records = [dict(r) for r in result.mappings().all()]

        has_next = len(records) > page_size
        records = records[:page_size]

        pagination = {
            "page": page,
            "page_size": page_size,
            "has_next": has_next,
            "has_previous": page > 1,
            "has_prev": page > 1,
        }

        return {
            "success": True,
            "count": len(records),
            "total": len(records),
            "data": records,
            "items": records,
            "pagination": pagination,
        }


def paginate_raw_sql(
    db: Session,
    base_query: str,
    params: Optional[Dict[str, Any]] = None,
    page: int = 1,
    page_size: int = 20,
    sort_column: str = "TransDate",
    sort_order: str = "DESC",
    count_query: Optional[str] = None,
    fetch_all: bool = False,
) -> Dict[str, Any]:
    """
    Execute a raw T-SQL query with native Microsoft SQL Server pagination:
    ORDER BY {sort_column} {sort_order} OFFSET :_sql_offset ROWS FETCH NEXT :_sql_page_size ROWS ONLY

    Guarantees SQL injection safety by ensuring sort_column and sort_order are validated.
    """
    exec_params = dict(params or {})

    # Normalize sort order
    order_normalized = "ASC" if str(sort_order).strip().lower() == "asc" else "DESC"

    if fetch_all or page_size <= 0:
        # User explicitly requested all records (e.g. for modal dropdowns / excel export)
        full_sql = f"""
            {base_query}
            ORDER BY {sort_column} {order_normalized}
        """
        rows = db.execute(text(full_sql), exec_params).mappings().all()
        records = [dict(r) for r in rows]
        total_records = len(records)
        return build_pagination_envelope(
            records=records,
            total_records=total_records,
            page=1,
            page_size=max(1, total_records),
        )

    # 1. Total records count
    if count_query:
        cnt_sql = count_query
    else:
        cnt_sql = f"SELECT COUNT(1) FROM ({base_query}) AS _subquery_count"

    total_records = db.execute(text(cnt_sql), exec_params).scalar() or 0

    # 2. Paginated rows with T-SQL OFFSET ... FETCH NEXT
    offset = get_offset(page, page_size)
    paged_sql = f"""
        {base_query}
        ORDER BY {sort_column} {order_normalized}
        OFFSET :_sql_offset ROWS
        FETCH NEXT :_sql_page_size ROWS ONLY
    """
    paged_params = {**exec_params, "_sql_offset": offset, "_sql_page_size": page_size}
    rows = db.execute(text(paged_sql), paged_params).mappings().all()
    records = [dict(r) for r in rows]

    return build_pagination_envelope(
        records=records,
        total_records=total_records,
        page=page,
        page_size=page_size,
    )
