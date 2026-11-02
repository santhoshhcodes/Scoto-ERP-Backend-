"""
Common and reusable Pydantic schemas across the Scoto ERP platform.
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


class PaginationMeta(BaseModel):
    """Pagination metadata model."""
    total: int = Field(ge=0, description="Total number of items")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=50, ge=1, description="Items per page")
    total_pages: int = Field(default=1, ge=1, description="Total pages")
    has_next: bool = False
    has_prev: bool = False


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic envelope for paginated list responses."""
    success: bool = True
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
