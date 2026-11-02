import calendar
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.schemas.attendance import (
    DailyAttendanceSummaryRecord,
    DailyReconciliationRecord,
    MonthlyAttendanceDayLog,
    MonthlyEmployeeReport,
    MonthlySummaryResponse,
)


class AttendanceService:
    @staticmethod
    def _log_table(db1: Session, month: int, year: int) -> Optional[str]:
        table = f"dbo.DeviceLogs_{month}_{year}"
        exists = db1.execute(
            text("SELECT OBJECT_ID(:table_name, 'U')"),
            {"table_name": table},
        ).scalar()

        if exists is None:
            return None

        return table

    @staticmethod
    def _employee_name(row: dict) -> str:
        if row.get("DisplayName"):
            return str(row["DisplayName"]).strip()

        parts = [
            str(row.get("FirstName") or "").strip(),
            str(row.get("MiddleName") or "").strip(),
            str(row.get("LastName") or "").strip(),
        ]
        name = " ".join(part for part in parts if part)
        return name or str(row.get("EmployeeCode") or "Unknown")

    @staticmethod
    def _employee_rows(db2: Session, employee_code: Optional[str] = None) -> list:
        sql = """
            SELECT EmployeeCode, FirstName, MiddleName, LastName,
                   DisplayName, ESSLEmployeeCode, EmployeeSource,
                   CompanyCode, LocationCode, IsActive, IsOnSite
            FROM dbo.Employee_Mst
            WHERE IsActive = 1
              AND (:employee_code IS NULL OR EmployeeCode = :employee_code)
            ORDER BY EmployeeCode
        """
        rows = db2.execute(
            text(sql),
            {"employee_code": employee_code},
        ).mappings().all()

        employees = []
        for row in rows:
            item = dict(row)
            item["employee_name"] = AttendanceService._employee_name(item)
            essl_code = str(item.get("ESSLEmployeeCode") or "").strip()
            item["essl_code"] = essl_code or None
            item["essl_linked"] = bool(essl_code)
            is_onsite = bool(row.get("IsOnSite") if row.get("IsOnSite") is not None else row.get("IsOnField"))
            item["is_on_site"] = is_onsite
            item["is_on_field"] = is_onsite
            employees.append(item)

        return employees

    @staticmethod
    def get_reconciliation_logs(
        db1: Session,
        db2: Session,
        month: int,
        year: int,
        employee_code: Optional[str] = None,
        limit: int = 5000,
        offset: int = 0,
    ) -> List[DailyReconciliationRecord]:
        table = AttendanceService._log_table(db1, month, year)
        if not table:
            return []

        essl_filter = None
        if employee_code:
            employee = db2.execute(
                text("""
                    SELECT EmployeeCode, ESSLEmployeeCode
                    FROM dbo.Employee_Mst
                    WHERE EmployeeCode = :code AND IsActive = 1
                """),
                {"code": employee_code},
            ).mappings().first()

            if employee and employee.get("ESSLEmployeeCode"):
                essl_filter = str(employee["ESSLEmployeeCode"]).strip()
            else:
                # DB2 employee has no verified ESSL mapping or is inactive
                return []

        sql = f"""
            SELECT
                CAST(dl.LogDate AS DATE) AS attendance_date,
                e.EmployeeCode AS essl_employee_code,
                e.EmployeeName AS essl_employee_name,
                MIN(dl.LogDate) AS first_in,
                MAX(dl.LogDate) AS last_out,
                DATEDIFF(MINUTE, MIN(dl.LogDate), MAX(dl.LogDate))
                    AS total_minutes
            FROM {table} AS dl
            INNER JOIN dbo.Employees AS e
                ON e.EmployeeCode = dl.UserId
            WHERE (e.RecordStatus = 1 OR e.RecordStatus IS NULL)
              AND (:essl_code IS NULL OR e.EmployeeCode = :essl_code)
            GROUP BY CAST(dl.LogDate AS DATE), e.EmployeeCode, e.EmployeeName
            ORDER BY attendance_date DESC, e.EmployeeName ASC
        """

        punch_rows = db1.execute(
            text(sql),
            {"essl_code": essl_filter},
        ).mappings().all()

        employees = AttendanceService._employee_rows(db2)
        by_essl = {}
        for employee in employees:
            if employee.get("essl_code"):
                by_essl[str(employee["essl_code"]).strip()] = employee

        output = []
        for row in punch_rows:
            app_employee = by_essl.get(str(row["essl_employee_code"]).strip())

            # DB2 is the source for employees displayed in the ERP.
            # Ignore ESSL punch records with no active ERP employee mapping.
            if app_employee is None:
                continue

            app_code = app_employee["EmployeeCode"]
            name = app_employee["employee_name"]

            if employee_code and app_code != employee_code:
                continue

            first_in = row["first_in"]
            last_out = row["last_out"] if row["last_out"] != row["first_in"] else None
            if row["last_out"] == row["first_in"]:
                # Single punch discrimination: if punch is >= 14:00, it is Checkout Only (Exit)
                if row["first_in"] and row["first_in"].time() >= time(14, 0):
                    first_in = None
                    last_out = row["last_out"]
                else:
                    first_in = row["first_in"]
                    last_out = None
            minutes = max(int(row["total_minutes"] or 0), 0) if (first_in and last_out) else 0
            duration_formatted = f"{minutes // 60} hrs {minutes % 60} mins" if last_out else "--:--"

            output.append(
                DailyReconciliationRecord(
                    attendance_date=row["attendance_date"],
                    employee_code=app_code,
                    employee_name=name,
                    first_in=first_in,
                    last_out=last_out,
                    total_minutes=minutes,
                    duration_formatted=duration_formatted,
                )
            )

        return output[offset:offset + limit]

    @staticmethod
    def get_monthly_report(
        db1: Session,
        db2: Session,
        month: int,
        year: int,
        employee_code: Optional[str] = None,
    ) -> MonthlySummaryResponse:
        today = date.today()
        num_days = calendar.monthrange(year, month)[1]

        start_date_obj = date(year, month, 1)
        end_date_obj = date(year, month, num_days)
        start_date_str = start_date_obj.strftime("%b %d %Y")
        end_date_str = end_date_obj.strftime("%b %d %Y")
        month_name = start_date_obj.strftime("%B")
        printed_on = datetime.now().strftime("%b %d %Y %H:%M")

        table = AttendanceService._log_table(db1, month, year)
        employees = AttendanceService._employee_rows(db2, employee_code)

        codes = [
            str(employee["essl_code"]).strip()
            for employee in employees
            if employee.get("essl_code")
        ]

        # 1. Punches from DeviceLogs
        punches_by_emp_and_date = {}
        if table and codes:
            punch_sql = f"""
                SELECT
                    UserId AS EmployeeCode,
                    CAST(LogDate AS DATE) AS log_date,
                    MIN(LogDate) AS first_in,
                    MAX(LogDate) AS last_out,
                    COUNT(*) AS punch_count
                FROM {table}
                WHERE UserId IN ({",".join(f"'{c}'" for c in codes)})
                  AND CAST(LogDate AS DATE) <= :end_date
                GROUP BY UserId, CAST(LogDate AS DATE)
            """
            rows = db1.execute(
                text(punch_sql),
                {"end_date": min(end_date_obj, today)},
            ).mappings().all()
            for r in rows:
                key = (str(r["EmployeeCode"]).strip(), r["log_date"])
                punches_by_emp_and_date[key] = dict(r)

        # 2. Approved Leaves
        leave_rows = db2.execute(
            text("""
                SELECT EmployeeCode, LeaveType, ApprovalStatus,
                       StartDate, EndDate
                FROM dbo.Attendance_Leave
                WHERE ApprovalStatus = 'APPROVED'
                  AND StartDate <= :end_date
                  AND EndDate >= :start_date
            """),
            {"start_date": start_date_obj, "end_date": end_date_obj},
        ).mappings().all()

        emp_leaves = {}
        for l in leave_rows:
            emp_leaves.setdefault(str(l["EmployeeCode"]).strip(), []).append(dict(l))

        # 3. Daily Reviews / Adjustments (LOP, Casual Leave, Comp Off, Half Day, On Duty, etc.)
        review_rows = db2.execute(
            text("""
                SELECT EmployeeCode, AttendanceDate, ReviewStatus, ReviewCategory, ReviewReason,
                       CorrectedCheckIn, CorrectedCheckOut
                FROM dbo.Attendance_Daily_Review
                WHERE AttendanceDate >= :start_date AND AttendanceDate <= :end_date
            """),
            {"start_date": start_date_obj, "end_date": end_date_obj},
        ).mappings().all()

        emp_reviews = {}
        for rev in review_rows:
            emp_reviews[(str(rev["EmployeeCode"]).strip(), rev["AttendanceDate"])] = dict(rev)

        # 4. Attendance Policies
        policy_rows = db2.execute(
            text("""
                SELECT PolicyId, CompanyCode, LocationCode,
                       ShiftStartTime, ShiftEndTime, GraceMinutes
                FROM dbo.Attendance_Policy
                WHERE IsActive = 1
                ORDER BY PolicyId DESC
            """)
        ).mappings().all()
        policies = [dict(row) for row in policy_rows]

        # 5. Approved/Pending Permissions
        permission_rows = db2.execute(
            text("""
                SELECT EmployeeCode, AttendanceDate, SUM(PermissionMinutes) AS permission_minutes
                FROM dbo.Attendance_Permission
                WHERE AttendanceDate >= :start_date AND AttendanceDate <= :end_date
                  AND (ApprovalStatus != 'REJECTED' OR ApprovalStatus IS NULL)
                GROUP BY EmployeeCode, AttendanceDate
            """),
            {"start_date": start_date_obj, "end_date": end_date_obj},
        ).mappings().all()
        emp_permissions = {
            (str(row["EmployeeCode"]).strip(), row["AttendanceDate"]): int(row["permission_minutes"] or 0)
            for row in permission_rows
        }

        # 5b. Holidays from dbo.Attendance_Holiday
        holidays_by_date = {}
        try:
            h_table_exists = db2.execute(
                text("SELECT OBJECT_ID('dbo.Attendance_Holiday', 'U')")
            ).scalar()
            if h_table_exists:
                h_rows = db2.execute(
                    text("""
                        SELECT HolidayDate, HolidayName, HolidayType
                        FROM dbo.Attendance_Holiday
                        WHERE IsActive = 1
                          AND HolidayDate >= :start_date AND HolidayDate <= :end_date
                    """),
                    {"start_date": start_date_obj, "end_date": end_date_obj},
                ).mappings().all()
                for h in h_rows:
                    holidays_by_date[h["HolidayDate"]] = dict(h)
        except Exception:
            pass

        # 6. Late Fines (Waived, Confirmed, Pending)
        fine_rows = db2.execute(
            text("""
                SELECT EmployeeCode, AttendanceDate, LateMinutes, PermissionMinutesApplied, FineAmount, FineStatus
                FROM dbo.Attendance_Late_Fine
                WHERE AttendanceDate >= :start_date AND AttendanceDate <= :end_date
            """),
            {"start_date": start_date_obj, "end_date": end_date_obj},
        ).mappings().all()
        emp_fines = {
            (str(row["EmployeeCode"]).strip(), row["AttendanceDate"]): dict(row)
            for row in fine_rows
        }

        employee_reports = []
        for emp in employees:
            app_code = str(emp["EmployeeCode"]).strip()
            essl_code = str(emp.get("essl_code") or "").strip()
            name = emp["employee_name"]
            is_on_site = bool(emp.get("is_on_site") if emp.get("is_on_site") is not None else emp.get("is_on_field"))

            policy = next(
                (
                    p for p in policies
                    if (p["CompanyCode"] or "") == (emp.get("CompanyCode") or "")
                    and (p["LocationCode"] or "") == (emp.get("LocationCode") or "")
                ),
                None,
            )
            if policy is None:
                policy = next(
                    (
                        p for p in policies
                        if p["CompanyCode"] == "SCT"
                        and p["LocationCode"] == "UNIT I"
                    ),
                    None,
                )

            shift_start = (
                policy["ShiftStartTime"] if (policy and policy.get("ShiftStartTime"))
                else time(9, 30)
            )
            grace_minutes = int((policy["GraceMinutes"] if (policy and policy.get("GraceMinutes") is not None) else 10) or 10)

            day_logs = []
            present_days = 0
            leaves_count = 0
            holiday_count = 0
            absent_days = 0
            weekly_off_count = 0
            single_punch_days = 0
            emp_total_minutes = 0

            for d in range(1, num_days + 1):
                cur_date = date(year, month, d)
                date_label = cur_date.strftime("%d-%b-%Y")
                iso_date = cur_date.strftime("%Y-%m-%d")
                day_name = cur_date.strftime("%a")

                if cur_date > today:
                    # Future date in current month
                    day_logs.append(
                        MonthlyAttendanceDayLog(
                            date=date_label,
                            date_str=date_label,
                            iso_date=iso_date,
                            day_name=day_name,
                            in_time="",
                            out_time="",
                            shift="GS",
                            total_duration="00:00",
                            duration_str="00:00",
                            total_minutes=0,
                            status="-",
                            remarks="",
                        )
                    )
                    continue

                rev = emp_reviews.get((app_code, cur_date))
                punch = punches_by_emp_and_date.get((essl_code, cur_date)) if essl_code else None
                fine = emp_fines.get((app_code, cur_date))

                perm_minutes = emp_permissions.get((app_code, cur_date), 0)
                if fine and fine.get("PermissionMinutesApplied") is not None:
                    perm_minutes = max(perm_minutes, int(fine["PermissionMinutesApplied"] or 0))

                shift_start_dt = datetime.combine(cur_date, shift_start)
                if perm_minutes > 0:
                    allowed_dt = shift_start_dt + timedelta(minutes=perm_minutes)
                else:
                    allowed_dt = shift_start_dt + timedelta(minutes=grace_minutes)

                # Compute punch times if available
                first_in = punch["first_in"] if punch else None
                last_out = punch["last_out"] if punch else None
                p_count = int(punch["punch_count"]) if punch else 0

                if rev:
                    first_in = rev.get("CorrectedCheckIn") or first_in
                    last_out = rev.get("CorrectedCheckOut") or last_out

                # Standard eSSL single punch discrimination
                if p_count == 1 and (not rev or (not rev.get("CorrectedCheckIn") and not rev.get("CorrectedCheckOut"))):
                    single_punch = punch["first_in"]
                    if single_punch.time() >= time(14, 0):
                        # Checkout only in evening (Missing IN-Punch)
                        first_in = None
                        last_out = single_punch
                    else:
                        # Check-in only in morning (Missing OUT-Punch)
                        first_in = single_punch
                        last_out = None
                elif p_count > 1 and first_in and last_out:
                    if (last_out - first_in).total_seconds() < 300:
                        if first_in.time() >= time(14, 0):
                            first_in = None
                        else:
                            last_out = None
                elif p_count == 0 and not rev:
                    first_in = None
                    last_out = None

                in_time_str = first_in.strftime("%H:%M") if first_in else ""
                out_time_str = last_out.strftime("%H:%M") if last_out else ""
                dur_str = "00:00"
                mins = 0
                if first_in and last_out and last_out > first_in:
                    mins = max(0, int((last_out - first_in).total_seconds() // 60))
                    dur_str = f"{mins // 60}:{mins % 60:02d}"
                    emp_total_minutes += mins
                elif first_in or last_out:
                    single_punch_days += 1

                # Calculate late minutes:
                # Crucial eSSL rule: missing morning IN-punch (or checkout only) must NOT be penalized as late!
                late_minutes = 0
                if fine and fine.get("LateMinutes") is not None:
                    late_minutes = int(fine["LateMinutes"] or 0)
                elif first_in:
                    if perm_minutes > 0:
                        if first_in > allowed_dt:
                            late_minutes = max(0, int((first_in - allowed_dt).total_seconds() // 60))
                    else:
                        if first_in > allowed_dt:
                            late_minutes = max(0, int((first_in - shift_start_dt).total_seconds() // 60))
                else:
                    late_minutes = 0

                # Determine day status with precedence:
                # 1. Manual review from Daily Review table
                # 2. Punch from device
                # 3. Approved leave from Leave table
                # 4. On-Site persistent setting
                # 5. Sunday / Weekly off
                # 6. Absent
                if rev and rev.get("ReviewStatus") and rev["ReviewStatus"] != "PENDING_REVIEW":
                    r_stat = rev["ReviewStatus"]
                    r_cat = rev.get("ReviewCategory") or ""
                    r_reason = rev.get("ReviewReason") or ""

                    if r_stat == "LOP":
                        status_str = "LOP"
                    elif r_stat == "COMP_OFF":
                        status_str = "Comp Off"
                    elif r_stat == "HALF_DAY":
                        status_str = "Half Day"
                    elif r_stat == "ON_DUTY":
                        status_str = "On Duty"
                        present_days += 1
                    elif r_stat in ("ON_SITE", "ON_FIELD"):
                        status_str = "Onsite"
                        present_days += 1
                    elif r_stat == "ON_LEAVE":
                        if r_cat == "CASUAL_LEAVE" or "casual" in r_reason.lower():
                            status_str = "Casual Leave"
                        else:
                            status_str = "Leave"
                        leaves_count += 1
                    elif r_stat in ("PRESENT_CONFIRMED", "FULL_DAY"):
                        status_str = "Present"
                        present_days += 1
                    elif r_stat == "ABSENT_CONFIRMED":
                        status_str = "Absent"
                        absent_days += 1
                    else:
                        status_str = r_stat
                elif punch:
                    if first_in and first_in.time() >= time(13, 30):
                        # Arrived after 01:30 PM -> 2nd half Half Day
                        status_str = "Half Day"
                        present_days += 1
                    elif mins >= 480:
                        status_str = "Present"
                        present_days += 1
                    elif mins >= 240:
                        status_str = "Half Day"
                        present_days += 1
                    elif is_on_site:
                        status_str = "Present"
                        present_days += 1
                    else:
                        status_str = "Present"
                        present_days += 1
                else:
                    # Check approved leaves first
                    matching_leave = None
                    for lv in emp_leaves.get(app_code, []):
                        if lv["StartDate"] <= cur_date <= lv["EndDate"]:
                            matching_leave = lv
                            break

                    if matching_leave:
                        l_type = matching_leave.get("LeaveType")
                        if l_type == "LOP":
                            status_str = "LOP"
                        elif l_type == "COMP_OFF":
                            status_str = "Comp Off"
                        elif l_type == "ON_DUTY":
                            status_str = "On Duty"
                            present_days += 1
                        elif l_type == "HALF_DAY":
                            status_str = "Half Day"
                        else:
                            status_str = "Casual Leave"
                            leaves_count += 1
                    elif cur_date in holidays_by_date:
                        # Office Holiday (Diwali, Pongal, etc.) - applied to ALL staff including On-Site
                        status_str = "Holiday"
                        holiday_count += 1
                    elif cur_date.weekday() == 6:
                        # Sunday / Weekly Off - applies to ALL staff including On-Site
                        status_str = "WO"
                        weekly_off_count += 1
                    elif is_on_site:
                        # Working day On-Site duty
                        status_str = "Onsite"
                        present_days += 1
                    else:
                        status_str = "Absent"
                        absent_days += 1

                # Construct remarks in single column (Column 7):
                # Combines: Leave, Half Day, On-Site, Late minutes, Permission minutes, Fine status (WITHOUT MONEY AMOUNT)
                remarks_parts = []

                # 1. Leave & Adjustments
                if status_str == "Casual Leave":
                    remarks_parts.append("Casual Leave (CL)")
                elif status_str == "LOP":
                    remarks_parts.append("Loss of Pay (LOP)")
                elif status_str == "Comp Off":
                    remarks_parts.append("Compensation Off")
                elif status_str == "On Duty":
                    remarks_parts.append("On Duty")
                elif status_str in ("Onsite", "On-Site", "Onfield"):
                    remarks_parts.append("On-Site Duty")
                elif status_str == "Leave":
                    remarks_parts.append("Approved Leave")

                # 2. Half Day
                if status_str == "Half Day":
                    half_str = "Half Day"
                    if rev and rev.get("ReviewCategory"):
                        cat = rev.get("ReviewCategory")
                        if "1" in cat or "FIRST" in cat.upper():
                            half_str = "Half Day (1st Half: 09:30-13:30)"
                        elif "2" in cat or "SECOND" in cat.upper():
                            half_str = "Half Day (2nd Half: 13:30-18:30)"
                    remarks_parts.append(half_str)

                # 2b. Single punch remarks
                if first_in and not last_out:
                    remarks_parts.append("Missing Out-Punch")
                elif not first_in and last_out:
                    remarks_parts.append("Checkout Only (Missing In)")

                # 3. Late delay (only when actual late arrival occurred)
                if late_minutes > 0:
                    remarks_parts.append(f"Late: {late_minutes} mins")

                # 3b. Early exit check: only if out punch exists and checkout is before 18:45 (6:45 PM)
                if last_out and last_out.time() < time(18, 45) and status_str in ("Present", "Half Day"):
                    early_diff = int((datetime.combine(cur_date, time(18, 45)) - last_out).total_seconds() // 60)
                    if early_diff > 0:
                        remarks_parts.append(f"Early Exit: {early_diff}m")

                # 4. Permission
                if perm_minutes > 0:
                    remarks_parts.append(f"Permission: {perm_minutes} mins")

                # 5. Fine Status (STRICTLY NO MONEY AMOUNT as requested)
                if fine:
                    f_stat = fine.get("FineStatus")
                    if f_stat == "CONFIRMED":
                        remarks_parts.append("Fine Confirmed")
                    elif f_stat == "WAIVED":
                        remarks_parts.append("Fine Waived")
                    elif f_stat == "PENDING":
                        remarks_parts.append("Late Fine Pending")
                elif late_minutes > 0 and status_str not in ("Absent", "WO", "LOP", "Casual Leave"):
                    remarks_parts.append("Late Fine Pending")

                # 6. Holiday / Weekly Off / Absent if no other remark
                if status_str == "Holiday":
                    h_info = holidays_by_date.get(cur_date, {})
                    h_name = h_info.get("HolidayName") or "Holiday"
                    if not any("Holiday" in r for r in remarks_parts):
                        remarks_parts.append(f"Holiday: {h_name}")
                elif status_str == "WO" and not remarks_parts:
                    remarks_parts.append("Weekly Off")

                remarks_str = " | ".join(remarks_parts)

                day_logs.append(
                    MonthlyAttendanceDayLog(
                        date=date_label,
                        date_str=date_label,
                        iso_date=iso_date,
                        day_name=day_name,
                        in_time=in_time_str,
                        out_time=out_time_str,
                        shift="GS",
                        total_duration=dur_str,
                        duration_str=dur_str,
                        total_minutes=mins,
                        status=status_str,
                        remarks=remarks_str,
                        is_holiday=bool(cur_date in holidays_by_date),
                        holiday_name=holidays_by_date.get(cur_date, {}).get("HolidayName") if cur_date in holidays_by_date else None,
                    )
                )

            total_hrs = emp_total_minutes // 60
            total_rem_mins = emp_total_minutes % 60
            formatted_tot = f"{total_hrs} Hrs {total_rem_mins} Min"

            employee_reports.append(
                MonthlyEmployeeReport(
                    employee_code=app_code,
                    employee_name=name,
                    company_name="SCOTO",
                    total_duration_formatted=formatted_tot,
                    total_duration_str=formatted_tot,
                    total_minutes=emp_total_minutes,
                    present_days=present_days,
                    leaves=leaves_count,
                    leave_days=leaves_count,
                    holiday=holiday_count,
                    holiday_days=holiday_count,
                    absent_days=absent_days,
                    weekly_off=weekly_off_count,
                    weekly_off_days=weekly_off_count,
                    single_punch_days=single_punch_days,
                    days=day_logs,
                )
            )

        return MonthlySummaryResponse(
            month=month,
            year=year,
            month_name=month_name,
            start_date=start_date_str,
            end_date=end_date_str,
            from_date=start_date_str,
            to_date=end_date_str,
            company_name="SCOTO",
            printed_on=printed_on,
            employees=employee_reports,
        )
    @staticmethod
    def get_daily_summary(
        db1: Session,
        db2: Session,
        target_date: date,
        employee_code: Optional[str] = None,
        limit: int = 5000,
        offset: int = 0,
    ) -> List[DailyAttendanceSummaryRecord]:
        table = AttendanceService._log_table(
            db1, target_date.month, target_date.year
        )
        employees = AttendanceService._employee_rows(db2, employee_code)

        codes = [
            str(employee["essl_code"]).strip()
            for employee in employees
            if employee.get("essl_code")
        ]

        punches = {}
        if table and codes:
            punch_sql = f"""
                SELECT
                    UserId AS EmployeeCode,
                    MIN(LogDate) AS first_in,
                    MAX(LogDate) AS last_out,
                    COUNT(*) AS punch_count
                FROM {table}
                WHERE CAST(LogDate AS DATE) = :target_date
                  AND UserId IN ({",".join(f"'{c}'" for c in codes)})
                GROUP BY UserId
            """
            rows = db1.execute(
                text(punch_sql),
                {"target_date": target_date},
            ).mappings().all()

            for row in rows:
                punches[str(row["EmployeeCode"]).strip()] = dict(row)

        policy_rows = db2.execute(
            text("""
                SELECT PolicyId, CompanyCode, LocationCode,
                       ShiftStartTime, ShiftEndTime, GraceMinutes
                FROM dbo.Attendance_Policy
                WHERE IsActive = 1
                ORDER BY PolicyId DESC
            """)
        ).mappings().all()
        policies = [dict(row) for row in policy_rows]

        permission_rows = db2.execute(
            text("""
                SELECT EmployeeCode, SUM(PermissionMinutes) AS permission_minutes
                FROM dbo.Attendance_Permission
                WHERE AttendanceDate = :target_date
                  AND ApprovalStatus = 'APPROVED'
                GROUP BY EmployeeCode
            """),
            {"target_date": target_date},
        ).mappings().all()
        permissions = {
            row["EmployeeCode"]: int(row["permission_minutes"] or 0)
            for row in permission_rows
        }

        leave_rows = db2.execute(
            text("""
                SELECT EmployeeCode, LeaveType, ApprovalStatus,
                       StartDate, EndDate, LeaveId
                FROM dbo.Attendance_Leave
                WHERE ApprovalStatus = 'APPROVED'
                  AND StartDate <= :target_date
                  AND EndDate >= :target_date
                ORDER BY LeaveId DESC
            """),
            {"target_date": target_date},
        ).mappings().all()
        leaves = {}
        for row in leave_rows:
            leaves.setdefault(row["EmployeeCode"], dict(row))

        review_rows = db2.execute(
            text("""
                SELECT EmployeeCode, ReviewStatus, ReviewReason,
                       CorrectedCheckIn, CorrectedCheckOut
                FROM dbo.Attendance_Daily_Review
                WHERE AttendanceDate = :target_date
            """),
            {"target_date": target_date},
        ).mappings().all()
        reviews = {row["EmployeeCode"]: dict(row) for row in review_rows}

        fine_rows = db2.execute(
            text("""
                SELECT EmployeeCode, FineAmount, FineStatus, PermissionMinutesApplied, LateMinutes
                FROM dbo.Attendance_Late_Fine
                WHERE AttendanceDate = :target_date
            """),
            {"target_date": target_date},
        ).mappings().all()
        fines = {row["EmployeeCode"]: dict(row) for row in fine_rows}

        # Check if target_date is a Holiday in dbo.Attendance_Holiday
        target_holiday = None
        try:
            h_exists = db2.execute(text("SELECT OBJECT_ID('dbo.Attendance_Holiday', 'U')")).scalar()
            if h_exists:
                target_holiday = db2.execute(
                    text("""
                        SELECT HolidayDate, HolidayName, HolidayType
                        FROM dbo.Attendance_Holiday
                        WHERE IsActive = 1 AND HolidayDate = :target_date
                    """),
                    {"target_date": target_date},
                ).mappings().first()
        except Exception:
            pass

        output = []
        for employee in employees:
            code = str(employee["EmployeeCode"])
            essl_code = str(employee["essl_code"]).strip() if employee.get("essl_code") else None
            punch = punches.get(essl_code) if essl_code else None

            policy = next(
                (
                    p for p in policies
                    if (p["CompanyCode"] or "") == (employee.get("CompanyCode") or "")
                    and (p["LocationCode"] or "") == (employee.get("LocationCode") or "")
                ),
                None,
            )
            if policy is None:
                policy = next(
                    (
                        p for p in policies
                        if p["CompanyCode"] == "SCT"
                        and p["LocationCode"] == "UNIT I"
                    ),
                    None,
                )

            shift_start = (
                policy["ShiftStartTime"] if (policy and policy.get("ShiftStartTime"))
                else time(9, 30)
            )
            shift_start_dt = datetime.combine(target_date, shift_start)
            
            fine = fines.get(code)
            permission_minutes = permissions.get(code, 0)
            if fine and fine.get("PermissionMinutesApplied") is not None:
                permission_minutes = max(permission_minutes, int(fine["PermissionMinutesApplied"] or 0))

            if permission_minutes > 0:
                allowed_dt = shift_start_dt + timedelta(minutes=permission_minutes)
            else:
                grace_minutes = int((policy["GraceMinutes"] if (policy and policy.get("GraceMinutes") is not None) else 10) or 10)
                allowed_dt = shift_start_dt + timedelta(minutes=grace_minutes)

            first_in = punch["first_in"] if punch else None
            last_out = punch["last_out"] if punch else None
            punch_count = int(punch["punch_count"]) if punch else 0

            review = reviews.get(code)
            leave = leaves.get(code)

            if review:
                first_in = review.get("CorrectedCheckIn") or first_in
                last_out = review.get("CorrectedCheckOut") or last_out

            # Standard eSSL single punch discrimination:
            # If only 1 punch recorded on this day:
            # - If punch occurred before 14:00 (2:00 PM): It is an IN-punch. (Missing Out-Punch)
            # - If punch occurred at or after 14:00 (2:00 PM): It is an OUT-punch / Checkout Only. (Missing IN-Punch)
            if punch_count == 1 and (not review or (not review.get("CorrectedCheckIn") and not review.get("CorrectedCheckOut"))):
                single_punch = punch["first_in"]
                if single_punch.time() >= time(14, 0):
                    first_in = None
                    last_out = single_punch
                else:
                    first_in = single_punch
                    last_out = None
            elif punch_count > 1 and first_in and last_out:
                if (last_out - first_in).total_seconds() < 300:
                    if first_in.time() >= time(14, 0):
                        first_in = None
                    else:
                        last_out = None
            elif punch_count == 0 and not review:
                first_in = None
                last_out = None

            total_minutes = 0
            if first_in and last_out and last_out > first_in:
                total_minutes = int((last_out - first_in).total_seconds() // 60)

            late_minutes = 0
            if first_in:
                if permission_minutes > 0:
                    if first_in > allowed_dt:
                        late_minutes = max(0, int((first_in - allowed_dt).total_seconds() // 60))
                else:
                    if first_in > allowed_dt:
                        late_minutes = max(0, int((first_in - shift_start_dt).total_seconds() // 60))
            else:
                # Checkout only (or missing in punch) -> NEVER count late arrival!
                late_minutes = 0

            if fine and (fine.get("FineStatus") == "WAIVED" or (fine.get("LateMinutes") == 0 and fine.get("PermissionMinutesApplied", 0) > 0)):
                late_minutes = 0

            fine_amount = fine["FineAmount"] if fine else None
            fine_status = fine["FineStatus"] if fine else None
            if fine_status == "WAIVED" or late_minutes == 0:
                if fine_status == "WAIVED":
                    fine_amount = 0

            is_on_site_emp = bool(employee.get("is_on_site") if employee.get("is_on_site") is not None else employee.get("is_on_field"))
            is_sunday = (target_date.weekday() == 6)

            # Scheduled Shift End time (standard 19:30 or policy ShiftEndTime)
            shift_end = (
                policy["ShiftEndTime"] if (policy and policy.get("ShiftEndTime"))
                else time(19, 30)
            )

            # Early Exit Calculation:
            # Rule: If out punch was NOT inserted -> DO NOT calculate early exit!
            # If out punch IS inserted: checkout at or after 18:45 (6:45 PM) is ON TIME (0 early exit)!
            early_exit_minutes = 0
            if last_out:
                checkout_cutoff = datetime.combine(target_date, time(18, 45))
                if shift_end < time(18, 45):
                    checkout_cutoff = datetime.combine(target_date, shift_end)

                if last_out < checkout_cutoff:
                    early_exit_minutes = max(0, int((checkout_cutoff - last_out).total_seconds() // 60))
                else:
                    early_exit_minutes = 0
            else:
                early_exit_minutes = 0

            early_permission_minutes = int(review.get("EarlyPermissionMinutes") or 0) if review and "EarlyPermissionMinutes" in review else 0
            on_duty_minutes = int(review.get("OnDutyMinutes") or 0) if review and "OnDutyMinutes" in review else 0
            if on_duty_minutes > 0:
                total_minutes += on_duty_minutes

            # Status determination with industry-level rules:
            if review and review["ReviewStatus"] != "PENDING_REVIEW":
                status_value = review["ReviewStatus"]
            elif leave:
                if leave["LeaveType"] == "LOP":
                    status_value = "LOP"
                elif leave["LeaveType"] == "COMP_OFF":
                    status_value = "COMP_OFF"
                elif leave["LeaveType"] == "ON_DUTY":
                    status_value = "ON_DUTY"
                else:
                    status_value = "ON_LEAVE"
            elif is_on_site_emp and first_in:
                # Rule 3: On-Site staff who punched in at the office device!
                # Mark as Present/Half-Day based on work duration, but DO NOT reset their persistent
                # IsOnSite master designation in Employee_Mst.
                if first_in.time() >= time(13, 30):
                    status_value = "HALF_DAY"
                elif total_minutes >= 480:
                    status_value = "FULL_DAY"
                elif total_minutes >= 240:
                    status_value = "HALF_DAY"
                else:
                    status_value = "SHORT_HOURS" 
            elif target_holiday:
                # Rule 4: Office Holiday (Diwali, Pongal, etc.) applies to everyone
                status_value = "HOLIDAY"
                late_minutes = 0
                fine_amount = None
                fine_status = None
            elif is_sunday:
                # Rule 2: Sunday Weekly Off applies to everyone including On-Site staff
                status_value = "WEEKLY_OFF"
                late_minutes = 0
                fine_amount = None
                fine_status = None
            elif is_on_site_emp:
                # Persistent On-Site staff on a normal working day
                status_value = "ON_SITE"
            elif not first_in and not last_out:
                status_value = "NO_CHECK_IN_REVIEW"
            elif (first_in and not last_out) or (not first_in and last_out):
                status_value = "SINGLE_PUNCH_ANOMALY"
            elif first_in and first_in.time() >= time(13, 30):
                # Rule 5: Arrival after 01:30 PM (3-4 hours late) -> 2nd half Half-Day
                status_value = "HALF_DAY"
            elif total_minutes >= 480:
                status_value = "FULL_DAY"
            elif total_minutes >= 240:
                status_value = "HALF_DAY"
            else:
                status_value = "SHORT_HOURS"

            output.append(
                DailyAttendanceSummaryRecord(
                    employee_code=code,
                    employee_name=employee["employee_name"],
                    target_date=target_date,
                    essl_employee_code=employee.get("ESSLEmployeeCode"),
                    essl_linked=employee["essl_linked"],
                    first_in=first_in,
                    last_out=last_out,
                    total_punches=punch_count,
                    total_minutes=total_minutes,
                    status=status_value,
                    leave_type=leave["LeaveType"] if leave else None,
                    leave_approval_status=leave["ApprovalStatus"] if leave else None,
                    permission_minutes=permission_minutes,
                    shift_start_time=shift_start,
                    allowed_until=allowed_dt.time(),
                    late_minutes=late_minutes,
                    review_status=review["ReviewStatus"] if review else None,
                    review_reason=review["ReviewReason"] if review else None,
                    fine_amount=fine_amount,
                    fine_status=fine_status,
                    is_on_site=is_on_site_emp,
                    is_on_field=is_on_site_emp,
                    scheduled_checkout=shift_end,
                    early_exit_minutes=early_exit_minutes,
                    early_permission_minutes=early_permission_minutes,
                    on_duty_minutes=on_duty_minutes,
                    is_holiday=bool(target_holiday),
                    holiday_name=target_holiday["HolidayName"] if target_holiday else None,
                    is_weekly_off=is_sunday,
                )
            )

        output.sort(key=lambda item: (item.status, item.employee_name.lower()))
        return output[offset:offset + limit]