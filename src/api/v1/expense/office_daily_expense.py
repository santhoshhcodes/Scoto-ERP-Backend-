
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.schemas.office_daily_expense import (
    DailyItemCreate,
    DailyItemUpdate,
    DailyUsageSave,
    SettlementCreate,
)
from src.services.office_daily_expense_service import (
    OfficeDailyExpenseService as Service,
)

router = APIRouter(
    prefix="/daily",
    tags=["Daily Office Expenses"],
)

DB = Depends(get_mssql_session("db2"))


@router.get("/items")
def list_items(
    include_inactive: bool = False,
    db: Session = DB,
):
    return Service.list_items(db, include_inactive)


@router.post("/items", status_code=201)
def create_item(
    data: DailyItemCreate,
    db: Session = DB,
):
    return Service.create_item(db, data, created_by="admin")


@router.put("/items/{item_id}")
def update_item(
    item_id: int,
    data: DailyItemUpdate,
    db: Session = DB,
):
    return Service.update_item(db, item_id, data)


@router.get("/usage/{expense_date}")
def get_daily_usage(
    expense_date: date,
    db: Session = DB,
):
    return Service.get_daily_usage(db, expense_date)


@router.put("/usage")
def save_daily_usage(
    data: DailyUsageSave,
    db: Session = DB,
):
    return Service.save_daily_usage(db, data, created_by="admin")


@router.get("/register")
def get_register(
    from_date: date,
    to_date: date,
    search: str | None = None,
    db: Session = DB,
):
    return Service.list_entries(db, from_date, to_date, search)


@router.get("/vendors")
def get_vendor_summary(
    period_month: str = Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    db: Session = DB,
):
    return Service.vendor_summary(db, period_month)


@router.post("/settlements", status_code=201)
def settle_vendor(
    data: SettlementCreate,
    db: Session = DB,
):
    return Service.settle_vendor(db, data)


@router.get("/settlements/history")
def settlement_history(
    period_month: str = Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    db: Session = DB,
):
    from sqlalchemy import text

    rows = db.execute(text("""
        SELECT SettlementId AS settlement_id,
               VendorName AS vendor_name,
               PeriodMonth AS period_month,
               Amount AS amount,
               PaymentDate AS payment_date,
               PaymentMethod AS payment_method,
               Category AS category,
               FundId AS fund_id,
               LedgerTransactionId AS ledger_transaction_id,
               Reference AS reference,
               Remarks AS remarks,
               CreatedAt AS created_at
        FROM dbo.OfficeDaily_Settlement
        WHERE PeriodMonth = :period_month
        ORDER BY PaymentDate DESC, SettlementId DESC
    """), {"period_month": period_month}).mappings().all()

    return [dict(row) for row in rows]
