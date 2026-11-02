
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)
from src.services import employee_service

router = APIRouter(
    prefix="/employees",
    tags=["Employee Master"],
)


@router.get("", response_model=list[EmployeeResponse])
def get_employees(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    source: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db2: Session = Depends(get_mssql_session("db2")),
):
    return employee_service.list_employees(
        db2,
        search,
        is_active,
        source,
        skip,
        limit,
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db2: Session = Depends(get_mssql_session("db2")),
):
    return employee_service.get_employee(
        db2,
        employee_id,
    )


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=201,
)
def create_employee(
    payload: EmployeeCreate,
    db2: Session = Depends(get_mssql_session("db2")),
):
    return employee_service.create_employee(
        db2,
        payload,
    )


@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db2: Session = Depends(get_mssql_session("db2")),
):
    return employee_service.update_employee(
        db2,
        employee_id,
        payload,
    )

@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    db2: Session = Depends(get_mssql_session("db2")),
):
    return employee_service.delete_employee(db2, employee_id)

@router.patch("/by-code/{employee_code}/toggle-onsite")
@router.patch("/by-code/{employee_code}/toggle-onfield")
def toggle_onsite_by_code(
    employee_code: str,
    db2: Session = Depends(get_mssql_session("db2")),
):
    return employee_service.toggle_onsite_by_code(db2, employee_code)


# Backwards compatibility alias
toggle_onfield_by_code = toggle_onsite_by_code
