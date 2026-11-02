from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


ExpenseCategory = Literal[
    "PETROL",
    "FOOD",
    "BUS_TICKET",
    "ROOM",
    "OTHER",
]


class TravelExpenseItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expense_category: ExpenseCategory
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    description: str | None = None
    remarks: str | None = None
    bill_receipt_number: str | None = None
    attachment_path: str | None = None


class TravelExpenseClaimCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_code: str
    travel_start_date: date
    travel_end_date: date
    client_name: str | None = None
    destination: str
    purpose: str
    fund_id: int | None = None
    status: Literal["PENDING", "APPROVED", "PAID"] = "PENDING"
    paid_date: date | None = None
    record_petty_cash: bool = True
    items: list[TravelExpenseItemCreate] = Field(min_length=1)


class TravelExpenseStatusUpdate(BaseModel):
    status: Literal["PENDING", "APPROVED", "PAID", "REJECTED"]
    paid_date: date | None = None
    record_petty_cash: bool = True