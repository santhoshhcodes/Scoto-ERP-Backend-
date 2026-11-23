"""
Common and reusable Pydantic schemas across the Scoto ERP platform.
Designed for 100% backward compatibility with all frontend modules.
"""

from datetime import date
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class DropdownOption(BaseModel):
    """Generic key-value option for frontend dropdowns/selects."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class PaginationParams(BaseModel):
    """Standard incoming pagination and sorting query parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=500, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Column identifier to sort by")
    sort_order: Optional[str] = Field(default="desc", description="Sort direction ('asc' or 'desc')")
    all: bool = Field(default=False, description="When True, fetch all matching records without pagination")


class PaginationMeta(BaseModel):
    """Standard pagination metadata envelope."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1)
    total_records: int = Field(default=0, ge=0)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)
    has_next: bool = False
    has_previous: bool = False
    has_prev: bool = False


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard generic envelope for paginated list responses.
    Guarantees backward compatibility with both legacy `.data` and `.items` consumers.
    """
    success: bool = True
    count: int = 0
    total: int = 0
    data: List[T] = Field(default_factory=list)
    items: List[T] = Field(default_factory=list)
    pagination: PaginationMeta


class StandardResponse(BaseModel):
    """Generic operation response with status and message."""
    success: bool = True
    message: str = "Operation successful"
    data: Optional[Any] = None


class DateRangeFilter(BaseModel):
    """Common date range query parameter filter."""
    from_date: Optional[date] = None
    to_date: Optional[date] = None


class APIResponse(BaseModel, Generic[T]):
    """Standard generic API response wrapper."""
    model_config = ConfigDict(from_attributes=True)

    status: bool = True
    message: str = "Success"
    data: Optional[T] = None
    pagination: Optional[PaginationMeta] = None
