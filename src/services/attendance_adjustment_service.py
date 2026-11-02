from datetime import datetime, time, date
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

from src.schemas.attendance import (
    ApprovalDecision,
    DailyReviewUpsert,
    LateFineUpsert,
    LeaveCreate,
    MonthlyLateFineRecord,
    PermissionCreate,
)


class AttendanceAdjustmentService:
    @staticmethod
    def _validate_employee(db: Session, employee_code: str):
        found = db.execute(
            text("""
                SELECT 1
                FROM dbo.Employee_Mst
                WHERE EmployeeCode = :code AND IsActive = 1
            """),
            {"code": employee_code},
        ).first()

        if not found:
            raise HTTPException(
                status_code=404,
                detail="Active employee was not found in Employee_Mst.",
            )



    @staticmethod
    def _commit(db: Session, action):
        try:
            result = action()
            db.commit()
            return result

        except HTTPException:
            db.rollback()
            raise

        except Exception:
            db.rollback()
            logger.exception(
                "Attendance adjustment failed during database operation"
            )
            raise HTTPException(
                status_code=500,
                detail="Unable to save the attendance adjustment.",
            )

    @staticmethod
    def create_permission(db: Session, data: PermissionCreate):
        AttendanceAdjustmentService._validate_employee(
            db, data.employee_code
        )

        def action():
            emp_code = str(data.employee_code).strip()[:50]
            att_date = data.attendance_date
            perm_mins = int(data.permission_minutes)
            p_type = (data.permission_type or "OFFICIAL")[:30]
            p_reason = (data.reason or f"Permission granted ({perm_mins} mins)")[:500]
            created_by = (data.created_by or "HR Admin")[:50]

            existing = db.execute(
                text("""
                    SELECT PermissionId FROM dbo.Attendance_Permission
                    WHERE EmployeeCode = :c AND AttendanceDate = :d
                """),
                {"c": emp_code, "d": att_date},
            ).scalar()

            if existing:
                permission_id = existing
                db.execute(
                    text("""
                        UPDATE dbo.Attendance_Permission
                        SET PermissionMinutes = :pm,
                            PermissionType = :pt,
                            PermissionStartTime = :pst,
                            PermissionEndTime = :pet,
                            Reason = :r,
                            ApprovalStatus = 'APPROVED',
                            ApprovedBy = :by,
                            ApprovedAt = SYSDATETIME(),
                            UpdatedBy = :by,
                            UpdatedAt = SYSDATETIME()
                        WHERE PermissionId = :id
                    """),
                    {
                        "id": permission_id,
                        "pm": perm_mins,
                        "pt": p_type,
                        "pst": data.permission_start_time,
                        "pet": data.permission_end_time,
                        "r": p_reason,
                        "by": created_by,
                    },
                )
            else:
                permission_id = db.execute(
                    text("""
                        INSERT INTO dbo.Attendance_Permission (
                            EmployeeCode, AttendanceDate, PermissionMinutes,
                            PermissionType, PermissionStartTime, PermissionEndTime,
                            Reason, ApprovalStatus, ApprovedBy, ApprovedAt,
                            CreatedBy
                        )
                        OUTPUT INSERTED.PermissionId
                        VALUES (
                            :c, :d, :pm, :pt, :pst, :pet, :r, 'APPROVED', :by, SYSDATETIME(), :by
                        )
                    """),
                    {
                        "c": emp_code,
                        "d": att_date,
                        "pm": perm_mins,
                        "pt": p_type,
                        "pst": data.permission_start_time,
                        "pet": data.permission_end_time,
                        "r": p_reason,
                        "by": created_by,
                    },
                ).scalar_one()

            # Also sync into dbo.Attendance_Late_Fine if a fine record exists
            db.execute(
                text("""
                    UPDATE dbo.Attendance_Late_Fine
                    SET PermissionMinutesApplied = :pm,
                        FineStatus = CASE
                            WHEN LateMinutes <= :pm THEN 'WAIVED'
                            ELSE FineStatus
                        END,
                        FineAmount = CASE
                            WHEN LateMinutes <= :pm THEN 0
                            ELSE FineAmount
                        END,
                        WaivedBy = CASE
                            WHEN LateMinutes <= :pm THEN :by
                            ELSE WaivedBy
                        END,
                        WaivedAt = CASE
                            WHEN LateMinutes <= :pm THEN SYSDATETIME()
                            ELSE WaivedAt
                        END,
                        UpdatedBy = :by,
                        UpdatedAt = SYSDATETIME()
                    WHERE EmployeeCode = :c AND AttendanceDate = :d
                """),
                {"c": emp_code, "d": att_date, "pm": perm_mins, "by": created_by},
            )

            return {
                "permission_id": permission_id,
                "employee_code": emp_code,
                "attendance_date": str(att_date),
                "approval_status": "APPROVED",
            }

        return AttendanceAdjustmentService._commit(db, action)

    @staticmethod
    def decide_permission(
        db: Session, permission_id: int, data: ApprovalDecision
    ):
        def action():
            result = db.execute(
                text("""
                    UPDATE dbo.Attendance_Permission
                    SET ApprovalStatus = :decision,
                        ApprovedBy = :approved_by,
                        ApprovedAt = CASE
                            WHEN :decision = 'APPROVED' THEN SYSDATETIME()
                            ELSE ApprovedAt
                        END,
                        CancelledBy = CASE
                            WHEN :decision = 'CANCELLED' THEN :approved_by
                            ELSE CancelledBy
                        END,
                        CancelledAt = CASE
                            WHEN :decision = 'CANCELLED' THEN SYSDATETIME()
                            ELSE CancelledAt
                        END,
                        UpdatedBy = :approved_by,
                        UpdatedAt = SYSDATETIME()
                    WHERE PermissionId = :permission_id
                """),
                {
                    "decision": data.decision,
                    "approved_by": data.approved_by,
                    "permission_id": permission_id,
                },
            )

            if result.rowcount == 0:
                raise HTTPException(404, "Permission record was not found.")

            return {
                "permission_id": permission_id,
                "approval_status": data.decision,
            }

        return AttendanceAdjustmentService._commit(db, action)

    @staticmethod
    def create_leave(db: Session, data: LeaveCreate):
        if data.end_date < data.start_date:
            raise HTTPException(
                status_code=400,
                detail="Leave end date cannot precede leave start date.",
            )

        AttendanceAdjustmentService._validate_employee(
            db, data.employee_code
        )

        def action():
            emp_code = str(data.employee_code).strip()[:50]
            valid_leave_types = {"ON_DUTY", "COMP_OFF", "EL", "CL", "SL", "LOP", "OTHER"}
            leave_alias_map = {
                "CASUAL": "CL",
                "CASUAL_LEAVE": "CL",
                "CL": "CL",
                "SICK": "SL",
                "SICK_LEAVE": "SL",
                "SL": "SL",
                "EARNED": "EL",
                "EARNED_LEAVE": "EL",
                "EL": "EL",
                "LOSS_OF_PAY": "LOP",
                "LOP": "LOP",
                "UNPAID": "LOP",
                "COMP_OFF": "COMP_OFF",
                "COMPENSATION": "COMP_OFF",
                "ON_DUTY": "ON_DUTY",
                "OTHER": "OTHER",
            }
            clean_lt = str(data.leave_type).strip().upper()
            l_type = leave_alias_map.get(clean_lt, clean_lt if clean_lt in valid_leave_types else "CL")[:20]
            l_days = data.leave_days
            l_session = (data.leave_session or "FULL_DAY")[:20]
            l_reason = (data.reason or f"Leave applied ({l_type})")[:500]
            created_by = (data.created_by or "HR Admin")[:50]

            existing = db.execute(
                text("""
                    SELECT LeaveId FROM dbo.Attendance_Leave
                    WHERE EmployeeCode = :c AND StartDate = :sd AND EndDate = :ed
                """),
                {"c": emp_code, "sd": data.start_date, "ed": data.end_date},
            ).scalar()

            if existing:
                leave_id = existing
                db.execute(
                    text("""
                        UPDATE dbo.Attendance_Leave
                        SET LeaveType = :lt,
                            LeaveDays = :ld,
                            LeaveSession = :ls,
                            SessionStartTime = :sst,
                            SessionEndTime = :set,
                            Reason = :r,
                            ApprovalStatus = 'APPROVED',
                            ApprovedBy = :by,
                            ApprovedAt = SYSDATETIME(),
                            UpdatedBy = :by,
                            UpdatedAt = SYSDATETIME()
                        WHERE LeaveId = :id
                    """),
                    {
                        "id": leave_id,
                        "lt": l_type,
                        "ld": l_days,
                        "ls": l_session,
                        "sst": data.session_start_time,
                        "set": data.session_end_time,
                        "r": l_reason,
                        "by": created_by,
                    },
                )
            else:
                leave_id = db.execute(
                    text("""
                        INSERT INTO dbo.Attendance_Leave (
                            EmployeeCode, StartDate, EndDate, LeaveType, LeaveDays,
                            LeaveSession, SessionStartTime, SessionEndTime, Reason,
                            ApprovalStatus, ApprovedBy, ApprovedAt, CreatedBy
                        )
                        OUTPUT INSERTED.LeaveId
                        VALUES (
                            :c, :sd, :ed, :lt, :ld, :ls, :sst, :set, :r,
                            'APPROVED', :by, SYSDATETIME(), :by
                        )
                    """),
                    {
                        "c": emp_code,
                        "sd": data.start_date,
                        "ed": data.end_date,
                        "lt": l_type,
                        "ld": l_days,
                        "ls": l_session,
                        "sst": data.session_start_time,
                        "set": data.session_end_time,
                        "r": l_reason,
                        "by": created_by,
                    },
                ).scalar_one()

            # Synchronize each date into dbo.Attendance_Daily_Review
            from datetime import timedelta
            cur = data.start_date
            status_val = "ON_LEAVE" if l_type in ("CL", "CASUAL_LEAVE") else l_type
            while cur <= data.end_date:
                db.execute(
                    text("""
                        IF EXISTS (SELECT 1 FROM dbo.Attendance_Daily_Review WHERE EmployeeCode = :c AND AttendanceDate = :d)
                            UPDATE dbo.Attendance_Daily_Review
                            SET ReviewStatus = :st, ReviewCategory = :cat, ReviewReason = :r,
                                ReviewedBy = :by, ReviewedAt = SYSDATETIME(), UpdatedBy = :by, UpdatedAt = SYSDATETIME()
                            WHERE EmployeeCode = :c AND AttendanceDate = :d
                        ELSE
                            INSERT INTO dbo.Attendance_Daily_Review (
                                EmployeeCode, AttendanceDate, ReviewStatus,
                                ReviewCategory, ReviewReason, ReviewedBy, ReviewedAt, CreatedBy
                            )
                            VALUES (:c, :d, :st, :cat, :r, :by, SYSDATETIME(), :by)
                    """),
                    {
                        "c": emp_code,
                        "d": cur,
                        "st": status_val,
                        "cat": l_type,
                        "r": l_reason,
                        "by": created_by,
                    },
                )
                cur += timedelta(days=1)

            return {
                "leave_id": leave_id,
                "employee_code": emp_code,
                "approval_status": "APPROVED",
            }

        return AttendanceAdjustmentService._commit(db, action)

    @staticmethod
    def decide_leave(db: Session, leave_id: int, data: ApprovalDecision):
        def action():
            result = db.execute(
                text("""
                    UPDATE dbo.Attendance_Leave
                    SET ApprovalStatus = :decision,
                        ApprovedBy = :approved_by,
                        ApprovedAt = CASE
                            WHEN :decision = 'APPROVED' THEN SYSDATETIME()
                            ELSE ApprovedAt
                        END,
                        CancelledBy = CASE
                            WHEN :decision = 'CANCELLED' THEN :approved_by
                            ELSE CancelledBy
                        END,
                        CancelledAt = CASE
                            WHEN :decision = 'CANCELLED' THEN SYSDATETIME()
                            ELSE CancelledAt
                        END,
                        UpdatedBy = :approved_by,
                        UpdatedAt = SYSDATETIME()
                    WHERE LeaveId = :leave_id
                """),
                {
                    "decision": data.decision,
                    "approved_by": data.approved_by,
                    "leave_id": leave_id,
                },
            )

            if result.rowcount == 0:
                raise HTTPException(404, "Leave record was not found.")

            # If approved or cancelled, sync to dbo.Attendance_Daily_Review
            leave_row = db.execute(
                text("SELECT EmployeeCode, StartDate, EndDate, LeaveType, Reason FROM dbo.Attendance_Leave WHERE LeaveId = :id"),
                {"id": leave_id}
            ).mappings().first()

            if leave_row:
                from datetime import timedelta
                cur = leave_row["StartDate"]
                emp_code = leave_row["EmployeeCode"]
                while cur <= leave_row["EndDate"]:
                    if data.decision == "APPROVED":
                        status_val = "ON_LEAVE" if leave_row["LeaveType"] in ("CL", "CASUAL_LEAVE") else leave_row["LeaveType"]
                        db.execute(
                            text("""
                                IF EXISTS (SELECT 1 FROM dbo.Attendance_Daily_Review WHERE EmployeeCode = :c AND AttendanceDate = :d)
                                    UPDATE dbo.Attendance_Daily_Review
                                    SET ReviewStatus = :st, ReviewCategory = :cat, ReviewReason = :r,
                                        ReviewedBy = :by, ReviewedAt = SYSDATETIME(), UpdatedBy = :by, UpdatedAt = SYSDATETIME()
                                    WHERE EmployeeCode = :c AND AttendanceDate = :d
                                ELSE
                                    INSERT INTO dbo.Attendance_Daily_Review (
                                        EmployeeCode, AttendanceDate, ReviewStatus,
                                        ReviewCategory, ReviewReason, ReviewedBy, ReviewedAt, CreatedBy
                                    )
                                    VALUES (:c, :d, :st, :cat, :r, :by, SYSDATETIME(), :by)
                            """),
                            {
                                "c": emp_code,
                                "d": cur,
                                "st": status_val,
                                "cat": leave_row["LeaveType"],
                                "r": leave_row["Reason"],
                                "by": data.approved_by,
                            },
                        )
                    cur += timedelta(days=1)

            return {"leave_id": leave_id, "approval_status": data.decision}

        return AttendanceAdjustmentService._commit(db, action)

    @staticmethod
    def save_daily_review(db: Session, data: DailyReviewUpsert):
        AttendanceAdjustmentService._validate_employee(db, data.employee_code)

        if (
            data.corrected_check_in
            and data.corrected_check_out
            and data.corrected_check_out < data.corrected_check_in
        ):
            raise HTTPException(
                400, "Corrected check-out cannot precede corrected check-in."
            )

        def action():
            emp_code = str(data.employee_code).strip()[:50]
            att_date = data.attendance_date
            rev_by = (data.reviewed_by or "Attendance In-charge").strip()[:50]
            rev_cat = (data.review_category or "")[:30]
            rev_reason = (data.review_reason or "")[:500]

            # 1. Update or Insert into dbo.Attendance_Daily_Review
            updated = db.execute(
                text("""
                    UPDATE dbo.Attendance_Daily_Review
                    SET ReviewStatus = :review_status,
                        ReviewCategory = :review_category,
                        ReviewReason = :review_reason,
                        CorrectedCheckIn = :corrected_check_in,
                        CorrectedCheckOut = :corrected_check_out,
                        ReviewedBy = :reviewed_by,
                        ReviewedAt = SYSDATETIME(),
                        UpdatedBy = :reviewed_by,
                        UpdatedAt = SYSDATETIME()
                    WHERE EmployeeCode = :employee_code
                      AND AttendanceDate = :attendance_date
                """),
                {
                    "employee_code": emp_code,
                    "attendance_date": att_date,
                    "review_status": data.review_status,
                    "review_category": rev_cat,
                    "review_reason": rev_reason,
                    "corrected_check_in": data.corrected_check_in,
                    "corrected_check_out": data.corrected_check_out,
                    "reviewed_by": rev_by,
                },
            )

            if updated.rowcount == 0:
                db.execute(
                    text("""
                        INSERT INTO dbo.Attendance_Daily_Review
                        (
                            EmployeeCode, AttendanceDate, ReviewStatus,
                            ReviewCategory, ReviewReason, CorrectedCheckIn,
                            CorrectedCheckOut, ReviewedBy, ReviewedAt, CreatedBy
                        )
                        VALUES
                        (
                            :employee_code, :attendance_date, :review_status,
                            :review_category, :review_reason, :corrected_check_in,
                            :corrected_check_out, :reviewed_by, SYSDATETIME(),
                            :reviewed_by
                        )
                    """),
                    {
                        "employee_code": emp_code,
                        "attendance_date": att_date,
                        "review_status": data.review_status,
                        "review_category": rev_cat,
                        "review_reason": rev_reason,
                        "corrected_check_in": data.corrected_check_in,
                        "corrected_check_out": data.corrected_check_out,
                        "reviewed_by": rev_by,
                    },
                )

            # 2. Synchronize into dbo.Attendance_Leave
            valid_leave_types = {"ON_DUTY", "COMP_OFF", "EL", "CL", "SL", "LOP", "OTHER"}
            leave_alias_map = {
                "CASUAL": "CL",
                "CASUAL_LEAVE": "CL",
                "CL": "CL",
                "SICK": "SL",
                "SICK_LEAVE": "SL",
                "SL": "SL",
                "EARNED": "EL",
                "EARNED_LEAVE": "EL",
                "EL": "EL",
                "LOSS_OF_PAY": "LOP",
                "LOP": "LOP",
                "UNPAID": "LOP",
                "COMP_OFF": "COMP_OFF",
                "COMPENSATION": "COMP_OFF",
                "ON_DUTY": "ON_DUTY",
                "OTHER": "OTHER",
            }
            leave_status_map = {
                "ON_LEAVE": "CL",
                "LOP": "LOP",
                "COMP_OFF": "COMP_OFF",
                "ON_DUTY": "ON_DUTY",
                "HALF_DAY": "CL",
            }

            if data.review_status in leave_status_map:
                raw_lt = getattr(data, "leave_type", None)
                if raw_lt:
                    clean_lt = str(raw_lt).strip().upper()
                    l_type = leave_alias_map.get(clean_lt, clean_lt if clean_lt in valid_leave_types else "CL")
                else:
                    l_type = leave_status_map[data.review_status]

                if l_type not in valid_leave_types:
                    l_type = "CL"
                l_type = l_type[:20]

                l_days = Decimal("0.5") if data.review_status == "HALF_DAY" else Decimal("1.0")
                if data.review_status == "HALF_DAY":
                    l_session = ("1ST_HALF" if "FIRST" in rev_cat or "1" in rev_cat else "2ND_HALF" if "SECOND" in rev_cat or "2" in rev_cat else "1ST_HALF")[:20]
                else:
                    l_session = "FULL_DAY"
                l_reason = (rev_reason or f"{data.review_status} marked in Daily Review")[:500]

                existing_leave = db.execute(
                    text("""
                        SELECT LeaveId FROM dbo.Attendance_Leave
                        WHERE EmployeeCode = :c AND StartDate = :d AND EndDate = :d
                    """),
                    {"c": emp_code, "d": att_date},
                ).scalar()

                if existing_leave:
                    db.execute(
                        text("""
                            UPDATE dbo.Attendance_Leave
                            SET LeaveType = :lt,
                                LeaveDays = :ld,
                                LeaveSession = :ls,
                                Reason = :r,
                                ApprovalStatus = 'APPROVED',
                                ApprovedBy = :by,
                                ApprovedAt = SYSDATETIME(),
                                UpdatedBy = :by,
                                UpdatedAt = SYSDATETIME()
                            WHERE LeaveId = :id
                        """),
                        {
                            "id": existing_leave,
                            "lt": l_type,
                            "ld": l_days,
                            "ls": l_session,
                            "r": l_reason,
                            "by": rev_by,
                        },
                    )
                else:
                    db.execute(
                        text("""
                            INSERT INTO dbo.Attendance_Leave (
                                EmployeeCode, StartDate, EndDate, LeaveType, LeaveDays,
                                LeaveSession, Reason, ApprovalStatus, ApprovedBy, ApprovedAt,
                                CreatedBy
                            )
                            VALUES (
                                :c, :d, :d, :lt, :ld, :ls, :r, 'APPROVED', :by, SYSDATETIME(), :by
                            )
                        """),
                        {
                            "c": emp_code,
                            "d": att_date,
                            "lt": l_type,
                            "ld": l_days,
                            "ls": l_session,
                            "r": l_reason,
                            "by": rev_by,
                        },
                    )
            else:
                # If changed to Present / On-field / Absent, mark any single-day leave on that date as CANCELLED
                db.execute(
                    text("""
                        UPDATE dbo.Attendance_Leave
                        SET ApprovalStatus = 'CANCELLED',
                            CancelledBy = :by,
                            CancelledAt = SYSDATETIME(),
                            UpdatedBy = :by,
                            UpdatedAt = SYSDATETIME()
                        WHERE EmployeeCode = :c
                          AND StartDate = :d
                          AND EndDate = :d
                          AND ApprovalStatus != 'CANCELLED'
                    """),
                    {"c": emp_code, "d": att_date, "by": rev_by},
                )

            # 3. Synchronize into dbo.Attendance_Permission
            perm_mins = getattr(data, "permission_minutes", None) or 0
            if perm_mins > 0:
                p_reason = (rev_reason or f"Permission granted ({perm_mins} mins) in Daily Review")[:500]
                existing_perm = db.execute(
                    text("""
                        SELECT PermissionId FROM dbo.Attendance_Permission
                        WHERE EmployeeCode = :c AND AttendanceDate = :d
                    """),
                    {"c": emp_code, "d": att_date},
                ).scalar()

                if existing_perm:
                    db.execute(
                        text("""
                            UPDATE dbo.Attendance_Permission
                            SET PermissionMinutes = :pm,
                                Reason = :r,
                                ApprovalStatus = 'APPROVED',
                                ApprovedBy = :by,
                                ApprovedAt = SYSDATETIME(),
                                UpdatedBy = :by,
                                UpdatedAt = SYSDATETIME()
                            WHERE PermissionId = :id
                        """),
                        {"id": existing_perm, "pm": perm_mins, "r": p_reason, "by": rev_by},
                    )
                else:
                    db.execute(
                        text("""
                            INSERT INTO dbo.Attendance_Permission (
                                EmployeeCode, AttendanceDate, PermissionMinutes,
                                PermissionType, Reason, ApprovalStatus, ApprovedBy, ApprovedAt,
                                CreatedBy
                            )
                            VALUES (
                                :c, :d, :pm, 'OFFICIAL', :r, 'APPROVED', :by, SYSDATETIME(), :by
                            )
                        """),
                        {"c": emp_code, "d": att_date, "pm": perm_mins, "r": p_reason, "by": rev_by},
                    )

            # 4. Synchronize persistent On-Site status into dbo.Employee_Mst
            should_remove_onsite = bool(data.remove_on_site_master or data.remove_on_field_master)
            should_set_onsite = bool(
                data.set_on_site_master
                or data.set_on_field_master
                or (
                    data.review_status in ("ON_SITE", "ON_FIELD")
                    and data.set_on_site_master is not False
                    and not should_remove_onsite
                )
            )

            if should_remove_onsite:
                db.execute(
                    text("""
                        UPDATE dbo.Employee_Mst
                        SET IsOnSite = 0,
                            UpdatedAt = SYSDATETIME(),
                            UpdatedBy = :reviewed_by
                        WHERE EmployeeCode = :employee_code
                    """),
                    {"employee_code": emp_code, "reviewed_by": rev_by},
                )
            elif should_set_onsite:
                db.execute(
                    text("""
                        UPDATE dbo.Employee_Mst
                        SET IsOnSite = 1,
                            UpdatedAt = SYSDATETIME(),
                            UpdatedBy = :reviewed_by
                        WHERE EmployeeCode = :employee_code
                    """),
                    {"employee_code": emp_code, "reviewed_by": rev_by},
                )

            return {
                "employee_code": data.employee_code,
                "attendance_date": data.attendance_date,
                "review_status": data.review_status,
            }

        return AttendanceAdjustmentService._commit(db, action)

    @staticmethod
    def save_late_fine(db: Session, data: LateFineUpsert):
        AttendanceAdjustmentService._validate_employee(db, data.employee_code)

        if data.fine_status == "CONFIRMED" and data.fine_amount is None:
            raise HTTPException(
                400, "Enter the fine amount before confirming the fine."
            )

        def action():
            emp_code = str(data.employee_code).strip()[:50]
            att_date = data.attendance_date
            entered_by = (data.entered_by or "HR Admin")[:50]
            reason = (data.reason or "")[:500]
            values = data.model_dump()
            values["employee_code"] = emp_code
            values["entered_by"] = entered_by
            values["reason"] = reason

            updated = db.execute(
                text("""
                    UPDATE dbo.Attendance_Late_Fine
                    SET ActualCheckIn = :actual_check_in,
                        ShiftStartTime = :shift_start_time,
                        AllowedUntil = :allowed_until,
                        PermissionMinutesApplied = :permission_minutes_applied,
                        LateMinutes = :late_minutes,
                        FineAmount = :fine_amount,
                        CurrencyCode = 'INR',
                        FineStatus = :fine_status,
                        Reason = :reason,
                        UpdatedBy = :entered_by,
                        UpdatedAt = SYSDATETIME(),
                        ConfirmedBy = CASE
                            WHEN :fine_status = 'CONFIRMED' THEN :entered_by
                            ELSE ConfirmedBy
                        END,
                        ConfirmedAt = CASE
                            WHEN :fine_status = 'CONFIRMED' THEN SYSDATETIME()
                            ELSE ConfirmedAt
                        END,
                        WaivedBy = CASE
                            WHEN :fine_status = 'WAIVED' THEN :entered_by
                            ELSE WaivedBy
                        END,
                        WaivedAt = CASE
                            WHEN :fine_status = 'WAIVED' THEN SYSDATETIME()
                            ELSE WaivedAt
                        END
                    WHERE EmployeeCode = :employee_code
                      AND AttendanceDate = :attendance_date
                """),
                values,
            )

            if updated.rowcount == 0:
                db.execute(
                    text("""
                        INSERT INTO dbo.Attendance_Late_Fine
                        (
                            EmployeeCode, AttendanceDate, ActualCheckIn,
                            ShiftStartTime, AllowedUntil, PermissionMinutesApplied,
                            LateMinutes, FineAmount, CurrencyCode, FineStatus,
                            Reason, EnteredBy, ConfirmedBy, ConfirmedAt,
                            WaivedBy, WaivedAt
                        )
                        VALUES
                        (
                            :employee_code, :attendance_date, :actual_check_in,
                            :shift_start_time, :allowed_until, :permission_minutes_applied,
                            :late_minutes, :fine_amount, 'INR', :fine_status,
                            :reason, :entered_by,
                            CASE WHEN :fine_status = 'CONFIRMED' THEN :entered_by END,
                            CASE WHEN :fine_status = 'CONFIRMED' THEN SYSDATETIME() END,
                            CASE WHEN :fine_status = 'WAIVED' THEN :entered_by END,
                            CASE WHEN :fine_status = 'WAIVED' THEN SYSDATETIME() END
                        )
                    """),
                    values,
                )

            # Sync to dbo.Attendance_Permission if permission_minutes_applied > 0
            perm_applied = data.permission_minutes_applied or 0
            if perm_applied > 0:
                p_reason = (reason or f"Permission applied ({perm_applied} mins) in Late Fine")[:500]
                existing_perm = db.execute(
                    text("""
                        SELECT PermissionId FROM dbo.Attendance_Permission
                        WHERE EmployeeCode = :c AND AttendanceDate = :d
                    """),
                    {"c": emp_code, "d": att_date},
                ).scalar()

                if existing_perm:
                    db.execute(
                        text("""
                            UPDATE dbo.Attendance_Permission
                            SET PermissionMinutes = :pm,
                                Reason = :r,
                                ApprovalStatus = 'APPROVED',
                                ApprovedBy = :by,
                                ApprovedAt = SYSDATETIME(),
                                UpdatedBy = :by,
                                UpdatedAt = SYSDATETIME()
                            WHERE PermissionId = :id
                        """),
                        {"id": existing_perm, "pm": perm_applied, "r": p_reason, "by": entered_by},
                    )
                else:
                    db.execute(
                        text("""
                            INSERT INTO dbo.Attendance_Permission (
                                EmployeeCode, AttendanceDate, PermissionMinutes,
                                PermissionType, Reason, ApprovalStatus, ApprovedBy, ApprovedAt,
                                CreatedBy
                            )
                            VALUES (
                                :c, :d, :pm, 'OFFICIAL', :r, 'APPROVED', :by, SYSDATETIME(), :by
                            )
                        """),
                        {"c": emp_code, "d": att_date, "pm": perm_applied, "r": p_reason, "by": entered_by},
                    )

            return {
                "employee_code": data.employee_code,
                "attendance_date": data.attendance_date,
                "late_minutes": data.late_minutes,
                "fine_amount": data.fine_amount,
                "fine_status": data.fine_status,
            }

        return AttendanceAdjustmentService._commit(db, action)

    @staticmethod
    def get_monthly_late_fines(
        db1: Session,
        db2: Session,
        month: int,
        year: int,
        employee_code: Optional[str] = None,
    ) -> List[MonthlyLateFineRecord]:
        emp_rows = db2.execute(
            text("""
                SELECT EmployeeCode, DisplayName, FirstName, LastName, ESSLEmployeeCode
                FROM dbo.Employee_Mst
                WHERE IsActive = 1
                  AND (:employee_code IS NULL OR EmployeeCode = :employee_code)
            """),
            {"employee_code": employee_code},
        ).mappings().all()

        emp_map = {}
        essl_to_emp = {}
        for e in emp_rows:
            code = str(e["EmployeeCode"]).strip()
            disp = (e["DisplayName"] or "").strip()
            parts = [str(e.get("FirstName") or "").strip(), str(e.get("LastName") or "").strip()]
            full_name = disp or " ".join(p for p in parts if p) or code
            emp_map[code] = {
                "code": code,
                "name": full_name,
                "essl_code": str(e["ESSLEmployeeCode"]).strip() if e.get("ESSLEmployeeCode") else None
            }
            if e.get("ESSLEmployeeCode"):
                essl_to_emp[str(e["ESSLEmployeeCode"]).strip()] = code

        fine_rows = db2.execute(
            text("""
                SELECT 
                    FineId, EmployeeCode, AttendanceDate, ActualCheckIn,
                    ShiftStartTime, AllowedUntil, PermissionMinutesApplied,
                    LateMinutes, FineAmount, CurrencyCode, FineStatus,
                    Reason, EnteredBy, ConfirmedBy, WaivedBy
                FROM dbo.Attendance_Late_Fine
                WHERE MONTH(AttendanceDate) = :m AND YEAR(AttendanceDate) = :y
                  AND (:employee_code IS NULL OR EmployeeCode = :employee_code)
            """),
            {"m": month, "y": year, "employee_code": employee_code},
        ).mappings().all()

        fines_by_key = {}
        records = []
        for r in fine_rows:
            code = str(r["EmployeeCode"]).strip()
            d = r["AttendanceDate"]
            emp = emp_map.get(code, {"name": code})
            fines_by_key[(code, d)] = True
            records.append(
                MonthlyLateFineRecord(
                    fine_id=r["FineId"],
                    employee_code=code,
                    employee_name=emp["name"],
                    attendance_date=d,
                    actual_check_in=r["ActualCheckIn"],
                    shift_start_time=r["ShiftStartTime"],
                    allowed_until=r["AllowedUntil"],
                    permission_minutes_applied=int(r["PermissionMinutesApplied"] or 0),
                    late_minutes=int(r["LateMinutes"] or 0),
                    fine_amount=r["FineAmount"],
                    currency_code=r["CurrencyCode"] or "INR",
                    fine_status=r["FineStatus"],
                    reason=r["Reason"],
                    entered_by=r["EnteredBy"],
                    confirmed_by=r["ConfirmedBy"] or r["WaivedBy"],
                )
            )

        # 1.b Query Attendance_Permission for permission records
        perm_rows = db2.execute(
            text("""
                SELECT 
                    PermissionId, EmployeeCode, AttendanceDate, PermissionMinutes,
                    Reason, CreatedBy
                FROM dbo.Attendance_Permission
                WHERE MONTH(AttendanceDate) = :m AND YEAR(AttendanceDate) = :y
                  AND (:employee_code IS NULL OR EmployeeCode = :employee_code)
            """),
            {"m": month, "y": year, "employee_code": employee_code},
        ).mappings().all()

        for p in perm_rows:
            p_code = str(p["EmployeeCode"]).strip()
            p_date = p["AttendanceDate"]
            if (p_code, p_date) not in fines_by_key and p_code in emp_map:
                emp = emp_map.get(p_code, {"name": p_code})
                perm_mins = int(p["PermissionMinutes"] or 0)
                fines_by_key[(p_code, p_date)] = True
                records.append(
                    MonthlyLateFineRecord(
                        fine_id=None,
                        employee_code=p_code,
                        employee_name=emp["name"],
                        attendance_date=p_date,
                        actual_check_in=None,
                        shift_start_time=time(9, 30),
                        allowed_until=time(9, 40),
                        permission_minutes_applied=perm_mins,
                        late_minutes=0,
                        fine_amount=Decimal("0.00"),
                        currency_code="INR",
                        fine_status="WAIVED",
                        reason=p["Reason"] or f"Permission granted ({perm_mins} mins)",
                        entered_by=p["CreatedBy"] or "HR",
                        confirmed_by=None,
                    )
                )

        table = f"dbo.DeviceLogs_{month}_{year}"
        exists = db1.execute(text("SELECT OBJECT_ID(:t, 'U')"), {"t": table}).scalar()
        if exists:
            codes = list(essl_to_emp.keys())
            if codes:
                codes_sql = ",".join(f"'{c}'" for c in codes)
                log_rows = db1.execute(text(f"""
                    SELECT UserId, CAST(LogDate AS DATE) as d, MIN(LogDate) as first_in
                    FROM {table}
                    WHERE UserId IN ({codes_sql})
                    GROUP BY UserId, CAST(LogDate AS DATE)
                    HAVING CAST(MIN(LogDate) AS TIME) > '09:40:00'
                """)).mappings().all()

                for lr in log_rows:
                    essl_user = str(lr["UserId"]).strip()
                    app_code = essl_to_emp.get(essl_user, essl_user)
                    log_d = lr["d"]
                    if (app_code, log_d) not in fines_by_key and app_code in emp_map:
                        emp = emp_map.get(app_code, {"name": app_code})
                        fi = lr["first_in"]
                        shift_dt = datetime.combine(log_d, time(9, 30))
                        late_mins = max(0, int((fi - shift_dt).total_seconds() // 60))
                        records.append(
                            MonthlyLateFineRecord(
                                fine_id=None,
                                employee_code=app_code,
                                employee_name=emp["name"],
                                attendance_date=log_d,
                                actual_check_in=fi,
                                shift_start_time=time(9, 30),
                                allowed_until=time(9, 40),
                                permission_minutes_applied=0,
                                late_minutes=late_mins,
                                fine_amount=Decimal("0.00"),
                                currency_code="INR",
                                fine_status="UNPROCESSED",
                                reason="Late arrival recorded by biometric terminal",
                                entered_by="System",
                                confirmed_by=None,
                            )
                        )

        records.sort(key=lambda x: (x.attendance_date, x.employee_name), reverse=True)
        return records
