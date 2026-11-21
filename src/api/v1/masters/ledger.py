
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.schemas.master import LedgerCreate, LedgerUpdate
from src.services import ledger_services

router = APIRouter(
    prefix="/ledgers",
    tags=["Master - Ledger Master"],
)


@router.get("")
def read_ledgers(
    search: Optional[str] = Query(default=None),
    ledger_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_mssql_session("db2")),
):
    return ledger_services.get_ledgers(
        db=db,
        search=search,
        ledger_type=ledger_type,
    )


@router.get("/next-code")
def read_next_ledger_code(
    ledger_type: str = Query(default="Customer"),
    db: Session = Depends(get_mssql_session("db2")),
):
    next_code = ledger_services.get_next_ledger_code(db=db, ledger_type=ledger_type)
    return {
        "success": True,
        "ledger_type": ledger_type,
        "next_code": next_code,
    }


@router.get("/headers")
def read_account_headers(
    db: Session = Depends(get_mssql_session("db2")),
):
    return ledger_services.get_account_headers(db)


@router.post("", status_code=201)
def create_ledger(
    payload: LedgerCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return ledger_services.create_ledger(db, payload)


@router.put("/{ledger_code:path}")
def edit_ledger(
    ledger_code: str,
    payload: LedgerUpdate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return ledger_services.update_ledger(
        db,
        ledger_code,
        payload,
    )


@router.delete("/{ledger_code:path}")
def remove_ledger(
    ledger_code: str,
    db: Session = Depends(get_mssql_session("db2")),
):
    return ledger_services.delete_ledger(db, ledger_code)
