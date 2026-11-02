from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.schemas.attendance import (
    HolidayCreate,
    HolidayUpdate,
    HolidayResponse,
    DailyAttendanceSummaryRecord,
    DailyReconciliationRecord,
    MonthlySummaryResponse,
)
from src.services.attendance_service import AttendanceService
from src.services.holiday_service import HolidayService
from src.services.device_service import DeviceService


router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get(
    "/reconciliation",
    response_model=List[DailyReconciliationRecord],
    status_code=status.HTTP_200_OK,
)
def get_daily_reconciliation(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2035),
    employee_code: Optional[str] = Query(None, min_length=1, max_length=50),
    limit: int = Query(5000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    db1: Session = Depends(get_mssql_session("db1")),
    db2: Session = Depends(get_mssql_session("db2")),
):
    try:
        return AttendanceService.get_reconciliation_logs(
            db1=db1,
            db2=db2,
            month=month,
            year=year,
            employee_code=employee_code,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve attendance reconciliation records.",
        )


@router.get(
    "/monthly-report",
    response_model=MonthlySummaryResponse,
    status_code=status.HTTP_200_OK,
)
def get_monthly_attendance_report(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2035),
    employee_code: Optional[str] = Query(None, min_length=1, max_length=50),
    db1: Session = Depends(get_mssql_session("db1")),
    db2: Session = Depends(get_mssql_session("db2")),
):
    try:
        return AttendanceService.get_monthly_report(
            db1=db1,
            db2=db2,
            month=month,
            year=year,
            employee_code=employee_code,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate monthly attendance report.",
        )


@router.get(
    "/daily-summary",
    response_model=List[DailyAttendanceSummaryRecord],
    status_code=status.HTTP_200_OK,
)
def get_daily_summary(
    target_date: date = Query(...),
    employee_code: Optional[str] = Query(None, min_length=1, max_length=50),
    limit: int = Query(5000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    db1: Session = Depends(get_mssql_session("db1")),
    db2: Session = Depends(get_mssql_session("db2")),
):
    try:
        return AttendanceService.get_daily_summary(
            db1=db1,
            db2=db2,
            target_date=target_date,
            employee_code=employee_code,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate the daily attendance summary.",
        )


@router.post(
    "/download-logs",
    status_code=status.HTTP_200_OK,
    summary="Download biometric punch logs directly from eSSL device into DB1",
)
def download_device_logs(
    device_id: Optional[int] = Query(
        None,
        description="Optional target device ID",
    ),
    db1: Session = Depends(get_mssql_session("db1")),
    db2: Session = Depends(get_mssql_session("db2")),
):
    try:
        return DeviceService.download_biometric_logs(
            db1=db1,
            db2=db2,
            device_id=device_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download logs from device: {str(e)}",
        )



@router.get(
    "/holidays",
    response_model=List[HolidayResponse],
    status_code=status.HTTP_200_OK,
)
def list_holidays(
    year: Optional[int] = Query(None, ge=2020, le=2035),
    db: Session = Depends(get_mssql_session("db2")),
):
    try:
        return HolidayService.list_holidays(db=db, year=year)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to retrieve holidays: {str(e)}",
        )


@router.post(
    "/holidays",
    response_model=HolidayResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_holiday(
    data: HolidayCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return HolidayService.create_holiday(db=db, data=data)


@router.put(
    "/holidays/{holiday_id}",
    response_model=HolidayResponse,
    status_code=status.HTTP_200_OK,
)
def update_holiday(
    holiday_id: int,
    data: HolidayUpdate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return HolidayService.update_holiday(db=db, holiday_id=holiday_id, data=data)


@router.delete(
    "/holidays/{holiday_id}",
    status_code=status.HTTP_200_OK,
)
def delete_holiday(
    holiday_id: int,
    db: Session = Depends(get_mssql_session("db2")),
):
    return HolidayService.delete_holiday(db=db, holiday_id=holiday_id)
