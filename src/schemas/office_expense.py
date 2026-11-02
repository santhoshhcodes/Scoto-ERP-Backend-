from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class FundCreate(BaseModel):
    fund_name: str = Field(min_length=1, max_length=100)
    opening_balance: Decimal = Field(
        default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2
    )


class MoneyReceivedCreate(BaseModel):
    fund_id: int | None = Field(default=None)
    transaction_date: date
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    received_from: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    remarks: str | None = Field(default=None, max_length=500)


class OfficeExpenseCreate(BaseModel):
    fund_id: int | None = Field(default=None)
    expense_date: date
    product_name: str | None = Field(default=None, max_length=200)
    category: str = Field(default="Other", max_length=100)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    receiver_name: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    quantity: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    remarks: str | None = Field(default=None, max_length=500)


class BatchExpenseCreate(BaseModel):
    fund_id: int | None = Field(default=None)
    items: list[dict]
    created_by: str = "admin"


class OfficeTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: int
    message: str


class SettlementCreate(BaseModel):
    vendor_name: str = Field(min_length=1, max_length=150)
    period_month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    payment_date: date
    payment_method: Literal[
        "Cash", "UPI", "Bank Transfer", "Cheque"
    ]
    category: str = Field(default="Other", max_length=80)
    fund_id: int | None = Field(default=None, gt=0)
    reference: str | None = Field(default=None, max_length=150)
    remarks: str | None = Field(default=None, max_length=500)



class TransactionUpdate(BaseModel):
    transaction_date: date | None = None
    transaction_type: str | None = None
    category: str | None = None
    product_name: str | None = None
    description: str | None = None
    amount: Decimal | None = None
    received_from: str | None = None
    receiver_name: str | None = None
    quantity: Decimal | None = None
    remarks: str | None = None
    updated_by: str | None = "admin"
