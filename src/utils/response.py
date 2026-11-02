"""
API response envelope helpers for consistent client communication.
"""

from typing import Any, Dict, List, Optional
import math


def success_response(
    data: Any = None,
    message: str = "Operation successful",
    **extra: Any,
) -> Dict[str, Any]:
    """Build a standard successful API response envelope."""
    payload: Dict[str, Any] = {
        "success": True,
        "message": message,
        "data": data,
    }
    if extra:
        payload.update(extra)
    return payload


def error_response(
    message: str,
    error_code: Optional[str] = None,
    details: Any = None,
    **extra: Any,
) -> Dict[str, Any]:
    """Build a standard error API response envelope."""
    payload: Dict[str, Any] = {
        "success": False,
        "message": message,
    }
    if error_code:
        payload["error_code"] = error_code
    if details is not None:
        payload["details"] = details
    if extra:
        payload.update(extra)
    return payload


def paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 50,
    **extra: Any,
) -> Dict[str, Any]:
    """Build a standard paginated response payload."""
    total_pages = math.ceil(total / page_size) if page_size > 0 else 1
    payload: Dict[str, Any] = {
        "success": True,
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }
    if extra:
        payload.update(extra)
    return payload
