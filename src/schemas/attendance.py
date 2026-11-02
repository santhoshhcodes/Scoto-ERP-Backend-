from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class DayStatusEnum(str, Enum):
    FULL_DAY = "FULL_DAY"
    HALF_DAY = "HALF_DAY"
    SHORT_HOURS = "SHORT_HOURS"
    SINGLE_PUNCH_ANOMALY = "SINGLE_PUNCH_ANOMALY"

    NO_CHECK_IN_REVIEW = "NO_CHECK_IN_REVIEW"
    PRESENT_CONFIRMED = "PRESENT_CONFIRMED"
    ABSENT_CONFIRMED = "ABSENT_CONFIRMED"
    ON_DUTY = "ON_DUTY"
    DEVICE_ISSUE = "DEVICE_ISSUE"

    ON_LEAVE = "ON_LEAVE"
    LOP = "LOP"
    COMP_OFF = "COMP_OFF"
    ON_SITE = "ON_SITE"
    ON_FIELD = "ON_FIELD"
    WEEKLY_OFF = "WEEKLY_OFF"
    HOLIDAY = "HOLIDAY"


class DailyReconciliationRecord(BaseModel):
    attendance_date: date
    employee_code: str
    employee_name: str
    first_in: Optional[datetime] = None
    last_out: Optional[datetime] = None
    total_minutes: int = 0
    duration_formatted: str = "--:--"


class MonthlyAttendanceDayLog(BaseModel):
    date: str
    date_str: Optional[str] = None
    iso_date: str
    day_name: str
    in_time: str = ""
    out_time: str = ""
    shift: str = "GS"
    total_duration: str = "00:00"
    duration_str: Optional[str] = None
    total_minutes: int = 0
    status: str = "Present"
    remarks: str = ""
    is_holiday: bool = False
    holiday_name: Optional[str] = None


class MonthlyEmployeeReport(BaseModel):
    employee_code: str
    employee_name: str
    company_name: str = "SCOTO"
    total_duration_formatted: str = "0 Hrs 0 Min"
    total_duration_str: Optional[str] = None
    total_minutes: int = 0
    present_days: int = 0
    leaves: int = 0
    leave_days: Optional[int] = None
    holiday: int = 0
    holiday_days: Optional[int] = None
    absent_days: int = 0
    weekly_off: int = 0
    weekly_off_days: Optional[int] = None
    single_punch_days: int = 0
    days: List[MonthlyAttendanceDayLog] = []


class MonthlySummaryResponse(BaseModel):
    month: int
    year: int
    month_name: str
    start_date: str
    end_date: str
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    company_name: str = "SCOTO"
    printed_on: str
    employees: List[MonthlyEmployeeReport] = []


class DailyAttendanceSummaryRecord(BaseModel):
    employee_code: str
    employee_name: str
    target_date: date

    essl_employee_code: Optional[str] = None
    essl_linked: bool = False
    is_on_site: bool = False
    is_on_field: bool = False

    first_in: Optional[datetime] = None
    last_out: Optional[datetime] = None
    total_punches: int = 0
    total_minutes: int = 0

    status: DayStatusEnum
    leave_type: Optional[str] = None
    leave_approval_status: Optional[str] = None

    permission_minutes: int = 0
    shift_start_time: Optional[time] = None
    allowed_until: Optional[time] = None
    late_minutes: int = 0

    review_status: Optional[str] = None
    review_reason: Optional[str] = None

    fine_amount: Optional[Decimal] = None
    fine_status: Optional[str] = None

    scheduled_checkout: Optional[time] = None
    early_exit_minutes: int = 0
    early_permission_minutes: int = 0
    on_duty_minutes: int = 0
    is_holiday: bool = False
    holiday_name: Optional[str] = None
    is_weekly_off: bool = False


class PermissionCreate(BaseModel):
    employee_code: str = Field(min_length=1, max_length=50)
    attendance_date: date
    permission_minutes: int = Field(gt=0)
    permission_type: Optional[str] = Field(default=None, max_length=30)
    permission_start_time: Optional[time] = None
    permission_end_time: Optional[time] = None
    reason: Optional[str] = Field(default=None, max_length=500)
    created_by: str = Field(min_length=1, max_length=50)


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern="^(APPROVED|REJECTED|CANCELLED)$")
    approved_by: str = Field(min_length=1, max_length=50)


class LeaveCreate(BaseModel):
    employee_code: str = Field(min_length=1, max_length=50)
    start_date: date
    end_date: date
    leave_type: str = Field(
        pattern="^(EL|CL|SL|LOP|OTHER|COMP_OFF|ON_DUTY)$"
    )
    leave_days: Decimal = Field(
        gt=0, max_digits=5, decimal_places=2
    )
    leave_session: Optional[str] = Field(default=None, max_length=20)
    session_start_time: Optional[time] = None
    session_end_time: Optional[time] = None
    reason: Optional[str] = Field(default=None, max_length=500)
    created_by: str = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class DailyReviewUpsert(BaseModel):
    employee_code: str = Field(min_length=1, max_length=50)
    attendance_date: date
    review_status: str = Field(
        pattern="^(PENDING_REVIEW|PRESENT_CONFIRMED|ABSENT_CONFIRMED|ON_DUTY|DEVICE_ISSUE|ON_LEAVE|LOP|COMP_OFF|HALF_DAY|ON_SITE|ON_FIELD)$"
    )
    review_category: Optional[str] = Field(default=None, max_length=30)
    review_reason: Optional[str] = Field(default=None, max_length=500)
    corrected_check_in: Optional[datetime] = None
    corrected_check_out: Optional[datetime] = None
    reviewed_by: str = Field(min_length=1, max_length=50)
    permission_minutes: Optional[int] = Field(default=None, ge=0)
    early_permission_minutes: Optional[int] = Field(default=None, ge=0)
    on_duty_minutes: Optional[int] = Field(default=None, ge=0)
    leave_type: Optional[str] = Field(default=None, max_length=30)
    set_on_site_master: Optional[bool] = None
    remove_on_site_master: Optional[bool] = None
    set_on_field_master: Optional[bool] = None
    remove_on_field_master: Optional[bool] = None
    is_on_site_action: Optional[bool] = None
    is_on_field_action: Optional[bool] = None


class LateFineUpsert(BaseModel):
    employee_code: str = Field(min_length=1, max_length=50)
    attendance_date: date
    actual_check_in: Optional[datetime] = None
    shift_start_time: Optional[time] = None
    allowed_until: Optional[time] = None
    permission_minutes_applied: Optional[int] = Field(default=None, ge=0)
    late_minutes: int = Field(ge=0)
    fine_amount: Optional[Decimal] = Field(default=None, ge=0)
    fine_status: str = Field(
        default="PENDING",
        pattern="^(PENDING|CONFIRMED|WAIVED)$",
    )
    reason: Optional[str] = Field(default=None, max_length=500)
    entered_by: str = Field(min_length=1, max_length=50)


class MonthlyLateFineRecord(BaseModel):
    fine_id: Optional[int] = None
    employee_code: str
    employee_name: str
    attendance_date: date
    actual_check_in: Optional[datetime] = None
    shift_start_time: Optional[time] = None
    allowed_until: Optional[time] = None
    permission_minutes_applied: int = 0
    late_minutes: int = 0
    fine_amount: Optional[Decimal] = None
    currency_code: str = "INR"
    fine_status: str = "PENDING"
    reason: Optional[str] = None
    entered_by: Optional[str] = None
    confirmed_by: Optional[str] = None


class HolidayCreate(BaseModel):
    holiday_date: date
    holiday_name: str = Field(min_length=1, max_length=100)
    holiday_type: Optional[str] = Field(default="OFFICIAL", max_length=30)
    description: Optional[str] = Field(default=None, max_length=250)
    year: Optional[int] = None
    is_active: bool = True
    created_by: Optional[str] = Field(default="HR Admin", max_length=50)


class HolidayUpdate(BaseModel):
    holiday_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    holiday_type: Optional[str] = Field(default=None, max_length=30)
    description: Optional[str] = Field(default=None, max_length=250)
    is_active: Optional[bool] = None
    updated_by: Optional[str] = Field(default="HR Admin", max_length=50)


class HolidayResponse(BaseModel):
    holiday_id: int
    holiday_date: date
    holiday_name: str
    holiday_type: str = "OFFICIAL"
    description: Optional[str] = None
    year: int
    is_active: bool = True
