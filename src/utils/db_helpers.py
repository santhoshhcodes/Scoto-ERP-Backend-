"""
Database utility helpers for SQLAlchemy row mapping, serialization, and query building.
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, Iterable, List
from uuid import UUID


def row_to_dict(row: Any) -> Dict[str, Any]:
    """
    Safely convert an SQLAlchemy Row, RowMapping, ORM model, or dictionary into a plain dict.
    """
    if row is None:
        return {}
    if isinstance(row, dict):
        return dict(row)
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    if hasattr(row, "__dict__"):
        d = dict(row.__dict__)
        d.pop("_sa_instance_state", None)
        return d
    try:
        return dict(row)
    except Exception:
        return {}


def rows_to_dicts(rows: Iterable[Any]) -> List[Dict[str, Any]]:
    """Convert an iterable of database rows into a list of plain dictionaries."""
    if not rows:
        return []
    return [row_to_dict(r) for r in rows]


def serialize_db_val(val: Any) -> Any:
    """
    Convert non-standard types (Decimal, datetime, date, time, UUID)
    to JSON-serializable primitives.
    """
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (datetime, date, time)):
        return val.isoformat()
    if isinstance(val, UUID):
        return str(val)
    if isinstance(val, bytes):
        try:
            return val.decode("utf-8")
        except UnicodeDecodeError:
            return str(val)
    return val


def serialize_db_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively convert all values in a record dict to JSON-serializable types."""
    if not isinstance(record, dict):
        return record
    return {k: serialize_db_val(v) for k, v in record.items()}


def escape_like_term(term: str) -> str:
    """Escape special wildcards for SQL LIKE clauses."""
    if not term:
        return ""
    # In SQL Server, [] are wildcard delimiters
    return (
        term.replace("[", "[[]")
        .replace("%", "[%]")
        .replace("_", "[_]")
    )
