from datetime import date

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from src.schemas.travel_expense import (
    TravelExpenseClaimCreate,
    TravelExpenseStatusUpdate,
)
from src.services.travel_expense_service import TravelExpenseService
from src.api.deps import get_mssql_session

router = APIRouter(
    prefix="",
    tags=["Travel Expenses"],
)

get_db = get_mssql_session("db2")


@router.get("/employees")
def get_travel_employees(
    db: Session = Depends(get_db),
):
    return {
        "employees": TravelExpenseService.list_employees(db)
    }


@router.post("/claims", status_code=201)
def create_travel_claim(
    data: TravelExpenseClaimCreate,
    db: Session = Depends(get_db),
    x_user_code: str = Header(default="admin"),
):
    return TravelExpenseService.create_claim(
        db=db,
        data=data,
        created_by=x_user_code,
    )


@router.get("/claims")
def list_travel_claims(
    employee_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    claims = TravelExpenseService.list_claims(
        db=db,
        employee_code=employee_code,
        status=status,
        from_date=from_date,
        to_date=to_date,
    )

    return {
        "count": len(claims),
        "claims": claims,
    }


@router.get("/claims/{claim_id}")
def get_travel_claim(
    claim_id: int,
    db: Session = Depends(get_db),
):
    return TravelExpenseService.get_claim(
        db=db,
        claim_id=claim_id,
    )


@router.patch("/claims/{claim_id}/status")
def update_travel_claim_status(
    claim_id: int,
    data: TravelExpenseStatusUpdate,
    db: Session = Depends(get_db),
    x_user_code: str = Header(default="admin"),
):
    return TravelExpenseService.update_status(
        db=db,
        claim_id=claim_id,
        data=data,
        updated_by=x_user_code,
    )


@router.delete("/claims/{claim_id}")
def delete_travel_claim(
    claim_id: int,
    db: Session = Depends(get_db),
):
    return TravelExpenseService.delete_claim(
        db=db,
        claim_id=claim_id,
    )


@router.get("/reports/summary")
def get_travel_expense_summary(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    employee_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return TravelExpenseService.summary(
        db=db,
        from_date=from_date,
        to_date=to_date,
        employee_code=employee_code,
    )
