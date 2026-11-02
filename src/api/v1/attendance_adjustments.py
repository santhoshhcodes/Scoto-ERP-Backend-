from typing import List, Optional
from fastapi import Query

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.schemas.attendance import (
    ApprovalDecision,
    DailyReviewUpsert,
    LateFineUpsert,
    LeaveCreate,
    MonthlyLateFineRecord,
    PermissionCreate,
)
from src.services.attendance_adjustment_service import (
    AttendanceAdjustmentService,
)


router = APIRouter(
    prefix="/attendance-adjustments",
    tags=["Attendance Adjustments"],
)


@router.post("/permissions", status_code=status.HTTP_201_CREATED)
def create_permission(
    data: PermissionCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return AttendanceAdjustmentService.create_permission(db, data)


@router.patch("/permissions/{permission_id}/decision")
def decide_permission(
    permission_id: int,
    data: ApprovalDecision,
    db: Session = Depends(get_mssql_session("db2")),
):
    return AttendanceAdjustmentService.decide_permission(
        db, permission_id, data
    )


@router.post("/leaves", status_code=status.HTTP_201_CREATED)
def create_leave(
    data: LeaveCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return AttendanceAdjustmentService.create_leave(db, data)


@router.patch("/leaves/{leave_id}/decision")
def decide_leave(
    leave_id: int,
    data: ApprovalDecision,
    db: Session = Depends(get_mssql_session("db2")),
):
    return AttendanceAdjustmentService.decide_leave(db, leave_id, data)


@router.put("/daily-review")
def save_daily_review(
    data: DailyReviewUpsert,
    db: Session = Depends(get_mssql_session("db2")),
):
    return AttendanceAdjustmentService.save_daily_review(db, data)


@router.put("/late-fines")
def save_late_fine(
    data: LateFineUpsert,
    db: Session = Depends(get_mssql_session("db2")),
):
    return AttendanceAdjustmentService.save_late_fine(db, data)


@router.get("/monthly-late-fines", response_model=List[MonthlyLateFineRecord])
def get_monthly_late_fines(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2035),
    employee_code: Optional[str] = Query(None, min_length=1, max_length=50),
    db1: Session = Depends(get_mssql_session("db1")),
    db2: Session = Depends(get_mssql_session("db2")),
):
    try:
        return AttendanceAdjustmentService.get_monthly_late_fines(
            db1=db1, db2=db2, month=month, year=year, employee_code=employee_code
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve monthly late fines: {str(e)}",
        )
