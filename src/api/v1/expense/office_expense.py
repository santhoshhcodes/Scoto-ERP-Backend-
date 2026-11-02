from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from src.schemas.office_expense import (
    FundCreate,
    MoneyReceivedCreate,
    OfficeExpenseCreate,
    BatchExpenseCreate,
    TransactionUpdate,
)
from src.services.office_expense_service import OfficeExpenseService
from src.api.deps import get_mssql_session

# Router prefix is "/office-expenses" so when included under "/api/v1",
# the endpoints are available at "/api/v1/office-expenses/..."
router = APIRouter(
    prefix="",
    tags=["Office Expenses"],
)


# =====================================================================
# Balance & Overview (No fund requirement)
# =====================================================================

@router.get("/balance")
def get_office_balance(
    fund_id: int | None = None,
    db: Session = Depends(get_mssql_session("db2")),
):
    return OfficeExpenseService.get_balance(db, fund_id)


# =====================================================================
# Transactions (Petty Cash Ledger: Received Credits & Expense Debits)
# =====================================================================

@router.get("/transactions")
def get_transactions(
    fund_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    transaction_type: str | None = None,
    db: Session = Depends(get_mssql_session("db2")),
):
    return OfficeExpenseService.list_transactions(
        db=db,
        fund_id=fund_id,
        from_date=from_date,
        to_date=to_date,
        transaction_type=transaction_type,
    )


@router.post("/transactions/credit")
def record_money_received(
    data: MoneyReceivedCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return OfficeExpenseService.add_credit(
        db=db,
        fund_id=data.fund_id,
        transaction_date=data.transaction_date,
        amount=data.amount,
        received_from=data.received_from,
        description=data.description,
        remarks=data.remarks,
        created_by="admin",
    )


@router.post("/transactions/debit")
def record_office_expense(
    data: OfficeExpenseCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return OfficeExpenseService.add_expense(
        db=db,
        fund_id=data.fund_id,
        expense_date=data.expense_date,
        product_name=data.product_name,
        amount=data.amount,
        receiver_name=data.receiver_name,
        remarks=data.remarks,
        created_by="admin",
        category=data.category,
        description=data.description,
        quantity=data.quantity,
    )



@router.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return OfficeExpenseService.update_transaction(
        db=db,
        transaction_id=transaction_id,
        transaction_date=data.transaction_date,
        transaction_type=data.transaction_type,
        category=data.category,
        product_name=data.product_name,
        description=data.description,
        amount=data.amount,
        received_from=data.received_from,
        receiver_name=data.receiver_name,
        quantity=data.quantity,
        remarks=data.remarks,
        updated_by=data.updated_by or "admin",
    )

@router.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_mssql_session("db2")),
):
    return OfficeExpenseService.delete_transaction(db, transaction_id)


@router.post("/transactions/batch")
def batch_add_expenses(
    data: BatchExpenseCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return OfficeExpenseService.batch_add_expenses(
        db=db,
        fund_id=data.fund_id,
        items=data.items,
        created_by=data.created_by or "admin",
    )


# =====================================================================
# Monthly Report
# =====================================================================

@router.get("/reports/monthly")
def get_monthly_report(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    fund_id: int | None = None,
    db: Session = Depends(get_mssql_session("db2")),
):
    return OfficeExpenseService.monthly_report(
        db=db,
        fund_id=fund_id,
        year=year,
        month=month,
    )


# =====================================================================
# Funds (Optional / Backward compatibility)
# =====================================================================

@router.get("/funds")
def get_office_funds(
    db: Session = Depends(get_mssql_session("db2")),
):
    return OfficeExpenseService.list_funds(db)


@router.post("/funds")
def create_office_fund(
    data: FundCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return OfficeExpenseService.create_fund(
        db=db,
        fund_name=data.fund_name,
        opening_balance=data.opening_balance,
        created_by="admin",
    )


@router.get("/funds/{fund_id}/balance")
def get_office_fund_balance_compat(
    fund_id: int,
    db: Session = Depends(get_mssql_session("db2")),
):
    return OfficeExpenseService.get_balance(db, fund_id)


# =====================================================================
# Backward Compatibility Endpoints
# =====================================================================

@router.get("/expenses")
def get_expenses_compat(
    fund_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_mssql_session("db2")),
):
    return OfficeExpenseService.list_transactions(
        db=db,
        fund_id=fund_id,
        from_date=from_date,
        to_date=to_date,
        transaction_type="DEBIT",
    )


@router.post("/expenses")
def record_expense_compat(
    data: OfficeExpenseCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return record_office_expense(data=data, db=db)


@router.delete("/expenses/{expense_id}")
def delete_expense_compat(
    expense_id: int,
    db: Session = Depends(get_mssql_session("db2")),
):
    return delete_transaction(transaction_id=expense_id, db=db)


@router.post("/expenses/batch")
def batch_expense_compat(
    data: BatchExpenseCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return batch_add_expenses(data=data, db=db)