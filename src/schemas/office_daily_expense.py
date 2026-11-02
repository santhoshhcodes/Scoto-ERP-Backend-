"""
Pydantic schemas for Daily Office Items, Daily Usage entries, and Settlements.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# Re-export SettlementCreate to maintain backwards compatibility
from src.schemas.office_expense import SettlementCreate


class DailyItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=150)
    rate: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    unit: str = Field(min_length=1, max_length=30)
    vendor: str = Field(min_length=1, max_length=150)
    category: str = Field(default="Other", max_length=80)
    icon_type: str = Field(default="other", max_length=30)


class DailyItemUpdate(DailyItemCreate):
    is_active: bool = True


class DailyQuantityInput(BaseModel):
    item_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=3)
    remarks: Optional[str] = Field(default=None, max_length=500)


class DailyUsageSave(BaseModel):
    expense_date: date
    items: List[DailyQuantityInput] = Field(max_length=500)


__all__ = [
    "DailyItemCreate",
    "DailyItemUpdate",
    "DailyQuantityInput",
    "DailyUsageSave",
    "SettlementCreate",
]
