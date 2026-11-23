from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional, Dict, Any, List

from fastapi import HTTPException
from sqlalchemy import text, bindparam
from sqlalchemy.orm import Session

from src.helpers.pagination import paginate_raw_sql
from src.helpers.sorting import resolve_raw_sort
from src.schemas.travel_expense import TravelExpenseClaimCreate, TravelExpenseStatusUpdate
from src.services.office_expense_service import OfficeExpenseService


CENT = Decimal("0.01")


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )


class TravelExpenseService:

    @staticmethod
    def _employee(db: Session, employee_code: str):
        employee = db.execute(
            text("""
                SELECT
                    EmployeeCode,
                    COALESCE(
                        NULLIF(DisplayName, ''),
                        CONCAT(
                            FirstName, ' ',
                            COALESCE(LastName, '')
                        )
                    ) AS EmployeeName,
                    DepartmentName,
                    DesignationName,
                    COALESCE(IsOnSite, 0) AS IsOnSite
                FROM dbo.Employee_Mst
                WHERE EmployeeCode = :employee_code
                  AND IsActive = 1
            """),
            {"employee_code": employee_code},
        ).mappings().first()

        if not employee:
            raise HTTPException(
                status_code=400,
                detail=f"Employee '{employee_code}' not found or is inactive.",
            )

        return employee

    @staticmethod
    def list_employees(db: Session):
        rows = db.execute(
            text("""
                SELECT
                    EmployeeCode AS employee_code,
                    COALESCE(
                        NULLIF(DisplayName, ''),
                        CONCAT(
                            FirstName, ' ',
                            COALESCE(LastName, '')
                        )
                    ) AS employee_name,
                    DepartmentName AS department_name,
                    DesignationName AS designation_name,
                    COALESCE(IsOnSite, 0) AS is_on_site
                FROM dbo.Employee_Mst
                WHERE IsActive = 1
                ORDER BY IsOnSite DESC, DisplayName, EmployeeCode
            """)
        ).mappings().all()

        return [dict(row) for row in rows]

    @staticmethod
    def create_claim(
        db: Session,
        data: TravelExpenseClaimCreate,
        created_by: str,
    ):
        if data.travel_end_date < data.travel_start_date:
            raise HTTPException(
                status_code=400,
                detail="Travel end date cannot be before travel start date.",
            )

        employee = TravelExpenseService._employee(db, data.employee_code)

        prepared_items = []
        total_amount = Decimal("0.00")

        for item in data.items:
            try:
                amount = Decimal(str(item.amount))
            except (InvalidOperation, TypeError, ValueError):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid expense amount.",
                )

            if not amount.is_finite() or amount <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Each expense amount must be greater than zero.",
                )

            amount = money(amount)
            total_amount += amount

            prepared_items.append({
                "expense_category": item.expense_category,
                "amount": amount,
                "description": item.description,
                "remarks": item.remarks,
                "bill_receipt_number": item.bill_receipt_number,
                "attachment_path": item.attachment_path,
            })

        total_amount = money(total_amount)
        status = data.status or "PENDING"
        paid_date = data.paid_date if status == "PAID" else None

        try:
            # Insert the claim header
            claim_id = db.execute(
                text("""
                    INSERT INTO dbo.TravelExpense_Claim
                    (
                        EmployeeCode,
                        TravelStartDate,
                        TravelEndDate,
                        ClientCode,
                        ClientName,
                        Destination,
                        Purpose,
                        TotalAmount,
                        Status,
                        FundId,
                        PaidDate,
                        CreatedBy
                    )
                    OUTPUT INSERTED.ClaimId
                    VALUES
                    (
                        :employee_code,
                        :travel_start_date,
                        :travel_end_date,
                        :client_code,
                        :client_name,
                        :destination,
                        :purpose,
                        :total_amount,
                        :status,
                        :fund_id,
                        :paid_date,
                        :created_by
                    )
                """),
                {
                    "employee_code": data.employee_code,
                    "travel_start_date": data.travel_start_date,
                    "travel_end_date": data.travel_end_date,
                    "client_code": data.client_code,
                    "client_name": data.client_name,
                    "destination": data.destination,
                    "purpose": data.purpose,
                    "total_amount": total_amount,
                    "status": status,
                    "fund_id": data.fund_id,
                    "paid_date": paid_date,
                    "created_by": created_by,
                },
            ).scalar_one()

            # Insert all individual expense items
            for item in prepared_items:
                db.execute(
                    text("""
                        INSERT INTO dbo.TravelExpense_Item
                        (
                            ClaimId,
                            ExpenseCategory,
                            Amount,
                            Description,
                            Remarks,
                            BillReceiptNumber,
                            AttachmentPath
                        )
                        VALUES
                        (
                            :claim_id,
                            :expense_category,
                            :amount,
                            :description,
                            :remarks,
                            :bill_receipt_number,
                            :attachment_path
                        )
                    """),
                    {
                        "claim_id": claim_id,
                        **item,
                    },
                )

            # If paid upfront and record_petty_cash requested, record in OfficeExpense_Transaction
            expense_id = None
            if status == "PAID" and data.record_petty_cash:
                balance = OfficeExpenseService.get_balance(db, data.fund_id)
                available = Decimal(str(balance.get("available_balance") or 0))
                if total_amount > available or (available - total_amount) < 0:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Insufficient Petty Cash balance. Available: ₹{available:.2f}, "
                            f"Total Claim: ₹{total_amount:.2f}, Projected Closing Balance: ₹{(available - total_amount):.2f}. "
                            f"Immediate settlement cannot proceed because the closing balance cannot be negative."
                        ),
                    )

                expense_id = db.execute(
                    text("""
                        INSERT INTO dbo.OfficeExpense_Transaction
                        (
                            FundId,
                            ExpenseDate,
                            ReceiverName,
                            ProductName,
                            Amount,
                            Remarks,
                            CreatedBy,
                            TransactionType,
                            Category,
                            Description
                        )
                        OUTPUT INSERTED.ExpenseId
                        VALUES
                        (
                            :fund_id,
                            :expense_date,
                            :receiver_name,
                            :product_name,
                            :amount,
                            :remarks,
                            :created_by,
                            'DEBIT',
                            'Travel Expense',
                            :description
                        )
                    """),
                    {
                        "fund_id": data.fund_id,
                        "expense_date": paid_date or data.travel_start_date,
                        "receiver_name": employee["EmployeeName"],
                        "product_name": f"Travel: {data.destination}",
                        "amount": total_amount,
                        "remarks": f"Claim #{claim_id}",
                        "created_by": created_by,
                        "description": f"Travel Claim #{claim_id} for {employee['EmployeeName']} to {data.destination}: {data.purpose}",
                    },
                ).scalar_one()

                db.execute(
                    text("""
                        UPDATE dbo.TravelExpense_Claim
                        SET ExpenseId = :expense_id
                        WHERE ClaimId = :claim_id
                    """),
                    {
                        "claim_id": claim_id,
                        "expense_id": expense_id,
                    },
                )

            db.commit()

            return {
                "claim_id": claim_id,
                "employee_code": data.employee_code,
                "employee_name": employee["EmployeeName"],
                "total_amount": total_amount,
                "item_count": len(prepared_items),
                "status": status,
                "expense_id": expense_id,
                "message": "Travel expense claim created successfully.",
            }

        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def _audit_claims(db: Session, claims: list[dict]) -> list[dict]:
        if not claims:
            return claims

        emp_codes = {str(c["employee_code"]) for c in claims if c.get("employee_code")}
        dates_start = [c["travel_start_date"] for c in claims if c.get("travel_start_date")]
        dates_end = [c["travel_end_date"] for c in claims if c.get("travel_end_date")]

        if not emp_codes or not dates_start or not dates_end:
            for c in claims:
                c["attendance_audit"] = {
                    "status": "UNVERIFIED",
                    "badge_text": "No Audit",
                    "badge_color": "slate",
                    "verified_days": 0,
                    "working_days": 0,
                    "total_days": 0,
                    "verified_dates": [],
                    "missing_dates": [],
                    "client_match": None,
                    "message": "Missing date range or employee code.",
                }
            return claims

        min_date = min(dates_start)
        max_date = max(dates_end)

        stmt = text("""
            SELECT
                r.EmployeeCode,
                r.AttendanceDate,
                r.ReviewStatus,
                r.ClientCode,
                r.ClientName,
                r.PlaceOfVisit
            FROM dbo.Attendance_Daily_Review r
            WHERE r.EmployeeCode IN :emp_list
              AND r.AttendanceDate >= :min_date
              AND r.AttendanceDate <= :max_date
              AND r.ReviewStatus IN ('ON_SITE', 'ON_FIELD', 'ON_DUTY')
        """).bindparams(bindparam("emp_list", expanding=True))

        review_rows = db.execute(
            stmt,
            {
                "emp_list": list(emp_codes),
                "min_date": min_date,
                "max_date": max_date,
            },
        ).mappings().all()

        # Map by (EmployeeCode, AttendanceDate)
        review_map = {}
        for r in review_rows:
            key = (str(r["EmployeeCode"]), r["AttendanceDate"])
            review_map[key] = dict(r)

        for c in claims:
            emp = str(c.get("employee_code") or "")
            s_date = c.get("travel_start_date")
            e_date = c.get("travel_end_date")
            claim_client_code = c.get("client_code")
            claim_client_name = (c.get("client_name") or "").strip().lower()

            if not emp or not s_date or not e_date or e_date < s_date:
                c["attendance_audit"] = {
                    "status": "UNVERIFIED",
                    "badge_text": "Invalid Range",
                    "badge_color": "slate",
                    "verified_days": 0,
                    "working_days": 0,
                    "total_days": 0,
                    "verified_dates": [],
                    "missing_dates": [],
                    "client_match": None,
                    "message": "Invalid travel start or end date.",
                }
                continue

            curr = s_date
            all_dates = []
            working_dates = []
            while curr <= e_date:
                all_dates.append(curr)
                if curr.weekday() != 6:  # Skip Sundays
                    working_dates.append(curr)
                curr += timedelta(days=1)

            if not working_dates and all_dates:
                working_dates = all_dates

            total_days = len(all_dates)
            working_days_count = len(working_dates)

            verified_dates = []
            missing_dates = []
            matched_clients = 0

            for d in working_dates:
                rev = review_map.get((emp, d))
                if rev:
                    verified_dates.append(d.isoformat())
                    rev_cc = rev.get("ClientCode")
                    rev_cn = (rev.get("ClientName") or "").strip().lower()
                    if claim_client_code and rev_cc and claim_client_code == rev_cc:
                        matched_clients += 1
                    elif claim_client_name and rev_cn and (claim_client_name in rev_cn or rev_cn in claim_client_name):
                        matched_clients += 1
                else:
                    missing_dates.append(d.isoformat())

            verified_count = len(verified_dates)
            has_client_spec = bool(claim_client_code or claim_client_name)
            client_match = (matched_clients > 0) if has_client_spec else None

            if verified_count == working_days_count and working_days_count > 0:
                audit_status = "VERIFIED"
                badge_text = "On-Site Verified"
                badge_color = "emerald"
                message = f"All {working_days_count} deployment day(s) confirmed on-site in attendance."
            elif verified_count > 0:
                audit_status = "PARTIAL"
                badge_text = f"Partial ({verified_count}/{working_days_count}d)"
                badge_color = "amber"
                message = f"{verified_count} of {working_days_count} day(s) confirmed on-site. Missing {len(missing_dates)} date(s)."
            else:
                audit_status = "UNVERIFIED"
                badge_text = "No On-Site Record"
                badge_color = "rose"
                message = f"No On-Site attendance regularized for the {working_days_count} claimed date(s)."

            c["attendance_audit"] = {
                "status": audit_status,
                "badge_text": badge_text,
                "badge_color": badge_color,
                "verified_days": verified_count,
                "working_days": working_days_count,
                "total_days": total_days,
                "verified_dates": verified_dates,
                "missing_dates": missing_dates,
                "client_match": client_match,
                "message": message,
            }

        return claims

    ALLOWED_SORT_COLUMNS = {
        "claim_id": "c.ClaimId",
        "ClaimId": "c.ClaimId",
        "employee_code": "c.EmployeeCode",
        "travel_start_date": "c.TravelStartDate",
        "travel_end_date": "c.TravelEndDate",
        "client_name": "c.ClientName",
        "total_amount": "c.TotalAmount",
        "status": "c.Status",
        "created_date": "c.CreatedDate",
    }

    @staticmethod
    def list_claims(
        db: Session,
        employee_code: str | None = None,
        status: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "desc",
        fetch_all: bool = False,
    ):
        if from_date and to_date and from_date > to_date:
            raise HTTPException(
                status_code=400,
                detail="from_date cannot be later than to_date.",
            )

        if status:
            status = status.upper()
            if status not in {"PENDING", "APPROVED", "PAID", "REJECTED"}:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid claim status.",
                )

        params = {
            "employee_code": employee_code,
            "status": status,
            "from_date": from_date,
            "to_date": to_date,
        }

        where_clause = """
            WHERE
                (:employee_code IS NULL OR c.EmployeeCode = :employee_code)
                AND (:status IS NULL OR c.Status = :status)
                AND (:from_date IS NULL OR c.TravelStartDate >= :from_date)
                AND (:to_date IS NULL OR c.TravelStartDate < DATEADD(day, 1, :to_date))
        """

        group_by_clause = """
            GROUP BY
                c.ClaimId,
                c.EmployeeCode,
                e.DisplayName,
                e.FirstName,
                e.LastName,
                e.DepartmentName,
                e.DesignationName,
                c.TravelStartDate,
                c.TravelEndDate,
                c.ClientCode,
                c.ClientName,
                c.Destination,
                c.Purpose,
                c.TotalAmount,
                c.Status,
                c.FundId,
                c.ExpenseId,
                c.PaidDate,
                c.CreatedDate,
                c.CreatedBy
        """

        select_cols = """
            SELECT
                c.ClaimId AS claim_id,
                c.EmployeeCode AS employee_code,
                COALESCE(
                    NULLIF(e.DisplayName, ''),
                    CONCAT(e.FirstName, ' ', COALESCE(e.LastName, ''))
                ) AS employee_name,
                e.DepartmentName AS department_name,
                e.DesignationName AS designation_name,
                c.TravelStartDate AS travel_start_date,
                c.TravelEndDate AS travel_end_date,
                c.ClientCode AS client_code,
                c.ClientName AS client_name,
                c.Destination AS destination,
                c.Purpose AS purpose,
                c.TotalAmount AS total_amount,
                c.Status AS status,
                c.FundId AS fund_id,
                c.ExpenseId AS expense_id,
                c.PaidDate AS paid_date,
                c.CreatedDate AS created_date,
                c.CreatedBy AS created_by,
                COUNT(i.ItemId) AS item_count,
                COALESCE(SUM(CASE WHEN i.ExpenseCategory = 'PETROL' THEN i.Amount ELSE 0 END), 0) AS petrol_amount,
                COALESCE(SUM(CASE WHEN i.ExpenseCategory = 'FOOD' THEN i.Amount ELSE 0 END), 0) AS food_amount,
                COALESCE(SUM(CASE WHEN i.ExpenseCategory = 'BUS_TICKET' THEN i.Amount ELSE 0 END), 0) AS bus_ticket_amount,
                COALESCE(SUM(CASE WHEN i.ExpenseCategory = 'ROOM' THEN i.Amount ELSE 0 END), 0) AS room_amount,
                COALESCE(SUM(CASE WHEN i.ExpenseCategory = 'OTHER' THEN i.Amount ELSE 0 END), 0) AS other_amount
            FROM dbo.TravelExpense_Claim c
            LEFT JOIN dbo.Employee_Mst e
                ON e.EmployeeCode = c.EmployeeCode
            LEFT JOIN dbo.TravelExpense_Item i
                ON i.ClaimId = c.ClaimId
        """

        sort_col, sort_dir = resolve_raw_sort(
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_sort_columns=TravelExpenseService.ALLOWED_SORT_COLUMNS,
            default_column="c.ClaimId",
            default_order="DESC",
        )

        # If paginated request
        if page is not None or page_size is not None or fetch_all:
            count_sql = f"""
                SELECT COUNT(DISTINCT c.ClaimId)
                FROM dbo.TravelExpense_Claim c
                {where_clause}
            """
            total_records = db.execute(text(count_sql), params).scalar() or 0

            calc_page = page if page and page > 0 else 1
            calc_size = page_size if page_size and page_size > 0 else 20

            if fetch_all or calc_size <= 0:
                paged_sql = f"""
                    {select_cols}
                    {where_clause}
                    {group_by_clause}
                    ORDER BY {sort_col} {sort_dir}
                """
                rows = db.execute(text(paged_sql), params).mappings().all()
            else:
                calc_offset = (calc_page - 1) * calc_size
                paged_sql = f"""
                    {select_cols}
                    {where_clause}
                    {group_by_clause}
                    ORDER BY {sort_col} {sort_dir}
                    OFFSET :_offset ROWS FETCH NEXT :_size ROWS ONLY
                """
                exec_params = {**params, "_offset": calc_offset, "_size": calc_size}
                rows = db.execute(text(paged_sql), exec_params).mappings().all()

            claims = [dict(row) for row in rows]
            audited = TravelExpenseService._audit_claims(db, claims)
            envelope = {
                "success": True,
                "count": total_records,
                "total": total_records,
                "claims": audited,
                "data": audited,
                "items": audited,
                "pagination": {
                    "page": calc_page,
                    "page_size": calc_size,
                    "total_records": total_records,
                    "total": total_records,
                    "total_pages": (total_records + calc_size - 1) // calc_size if total_records > 0 else 0,
                    "has_next": calc_page < ((total_records + calc_size - 1) // calc_size if total_records > 0 else 0),
                    "has_previous": calc_page > 1,
                    "has_prev": calc_page > 1,
                }
            }
            return envelope

        # Legacy raw array
        legacy_sql = f"""
            {select_cols}
            {where_clause}
            {group_by_clause}
            ORDER BY c.ClaimId DESC
        """
        rows = db.execute(text(legacy_sql), params).mappings().all()
        claims = [dict(row) for row in rows]
        return TravelExpenseService._audit_claims(db, claims)

    @staticmethod
    def get_claim(db: Session, claim_id: int):
        claim = db.execute(
            text("""
                SELECT
                    c.ClaimId AS claim_id,
                    c.EmployeeCode AS employee_code,
                    COALESCE(
                        NULLIF(e.DisplayName, ''),
                        CONCAT(e.FirstName, ' ', COALESCE(e.LastName, ''))
                    ) AS employee_name,
                    e.DepartmentName AS department_name,
                    e.DesignationName AS designation_name,
                    c.TravelStartDate AS travel_start_date,
                    c.TravelEndDate AS travel_end_date,
                    c.ClientCode AS client_code,
                    c.ClientName AS client_name,
                    c.Destination AS destination,
                    c.Purpose AS purpose,
                    c.TotalAmount AS total_amount,
                    c.Status AS status,
                    c.FundId AS fund_id,
                    c.ExpenseId AS expense_id,
                    c.PaidDate AS paid_date,
                    c.CreatedDate AS created_date,
                    c.CreatedBy AS created_by
                FROM dbo.TravelExpense_Claim c
                LEFT JOIN dbo.Employee_Mst e
                    ON e.EmployeeCode = c.EmployeeCode
                WHERE c.ClaimId = :claim_id
            """),
            {"claim_id": claim_id},
        ).mappings().first()

        if not claim:
            raise HTTPException(
                status_code=404,
                detail="Travel expense claim not found.",
            )

        items = db.execute(
            text("""
                SELECT
                    ItemId AS item_id,
                    ClaimId AS claim_id,
                    ExpenseCategory AS expense_category,
                    Amount AS amount,
                    Description AS description,
                    Remarks AS remarks,
                    BillReceiptNumber AS bill_receipt_number,
                    AttachmentPath AS attachment_path
                FROM dbo.TravelExpense_Item
                WHERE ClaimId = :claim_id
                ORDER BY ItemId
            """),
            {"claim_id": claim_id},
        ).mappings().all()

        result = dict(claim)
        result["items"] = [dict(item) for item in items]
        result["items_total"] = money(
            sum(
                (Decimal(str(item["amount"])) for item in items),
                Decimal("0.00"),
            )
        )

        TravelExpenseService._audit_claims(db, [result])
        audit = result.get("attendance_audit")
        if audit:
            s_date = result.get("travel_start_date")
            e_date = result.get("travel_end_date")
            emp = result.get("employee_code")
            daily_breakdown = []
            if s_date and e_date and emp:
                reviews = db.execute(
                    text("""
                        SELECT
                            AttendanceDate,
                            ReviewStatus,
                            ReviewReason,
                            ClientCode,
                            ClientName,
                            PlaceOfVisit
                        FROM dbo.Attendance_Daily_Review
                        WHERE EmployeeCode = :employee_code
                          AND AttendanceDate >= :s_date
                          AND AttendanceDate <= :e_date
                    """),
                    {
                        "employee_code": emp,
                        "s_date": s_date,
                        "e_date": e_date,
                    },
                ).mappings().all()
                day_rev_map = {r["AttendanceDate"]: dict(r) for r in reviews}

                curr = s_date
                while curr <= e_date:
                    rev = day_rev_map.get(curr)
                    daily_breakdown.append({
                        "date": curr.isoformat(),
                        "day_name": curr.strftime("%a"),
                        "is_sunday": curr.weekday() == 6,
                        "is_onsite": rev["ReviewStatus"] in ('ON_SITE', 'ON_FIELD', 'ON_DUTY') if rev else False,
                        "review_status": rev["ReviewStatus"] if rev else None,
                        "review_reason": rev.get("ReviewReason") if rev else None,
                        "client_code": rev.get("ClientCode") if rev else None,
                        "client_name": rev.get("ClientName") if rev else None,
                        "place_of_visit": rev.get("PlaceOfVisit") if rev else None,
                    })
                    curr += timedelta(days=1)
            audit["daily_breakdown"] = daily_breakdown

        return result

    @staticmethod
    def update_status(
        db: Session,
        claim_id: int,
        data: TravelExpenseStatusUpdate,
        updated_by: str = "admin",
    ):
        status = data.status.upper()

        if status not in {"PENDING", "APPROVED", "PAID", "REJECTED"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid claim status.",
            )

        claim = TravelExpenseService.get_claim(db, claim_id)
        current_expense_id = claim.get("expense_id")
        paid_date = data.paid_date or date.today()

        try:
            new_expense_id = current_expense_id

            if status == "PAID":
                # If not already recorded in OfficeExpense_Transaction and petty cash requested
                if not current_expense_id and data.record_petty_cash:
                    fund_id = claim.get("fund_id")
                    claim_amount = Decimal(str(claim.get("total_amount") or 0))

                    balance = OfficeExpenseService.get_balance(db, fund_id)
                    available = Decimal(str(balance.get("available_balance") or 0))
                    if claim_amount > available or (available - claim_amount) < 0:
                        raise HTTPException(
                            status_code=400,
                            detail=(
                                f"Insufficient Petty Cash balance. Available: ₹{available:.2f}, "
                                f"Claim Amount: ₹{claim_amount:.2f}, Projected Closing Balance: ₹{(available - claim_amount):.2f}. "
                                f"Settlement cannot proceed because the closing balance cannot be negative."
                            ),
                        )

                    new_expense_id = db.execute(
                        text("""
                            INSERT INTO dbo.OfficeExpense_Transaction
                            (
                                FundId,
                                ExpenseDate,
                                ReceiverName,
                                ProductName,
                                Amount,
                                Remarks,
                                CreatedBy,
                                TransactionType,
                                Category,
                                Description
                            )
                            OUTPUT INSERTED.ExpenseId
                            VALUES
                            (
                                :fund_id,
                                :expense_date,
                                :receiver_name,
                                :product_name,
                                :amount,
                                :remarks,
                                :created_by,
                                'DEBIT',
                                'Travel Expense',
                                :description
                            )
                        """),
                        {
                            "fund_id": claim.get("fund_id"),
                            "expense_date": paid_date,
                            "receiver_name": claim.get("employee_name"),
                            "product_name": f"Travel: {claim.get('destination')}",
                            "amount": claim.get("total_amount"),
                            "remarks": f"Claim #{claim_id}",
                            "created_by": updated_by,
                            "description": f"Travel Claim #{claim_id} for {claim.get('employee_name')} to {claim.get('destination')}: {claim.get('purpose')}",
                        },
                    ).scalar_one()

                db.execute(
                    text("""
                        UPDATE dbo.TravelExpense_Claim
                        SET Status = :status,
                            PaidDate = :paid_date,
                            ExpenseId = :expense_id
                        WHERE ClaimId = :claim_id
                    """),
                    {
                        "claim_id": claim_id,
                        "status": status,
                        "paid_date": paid_date,
                        "expense_id": new_expense_id,
                    },
                )
            else:
                # If reverting from PAID to PENDING, APPROVED, or REJECTED, remove ledger entry
                if current_expense_id:
                    db.execute(
                        text("DELETE FROM dbo.OfficeExpense_Transaction WHERE ExpenseId = :expense_id"),
                        {"expense_id": current_expense_id},
                    )
                    new_expense_id = None

                db.execute(
                    text("""
                        UPDATE dbo.TravelExpense_Claim
                        SET Status = :status,
                            PaidDate = NULL,
                            ExpenseId = NULL
                        WHERE ClaimId = :claim_id
                    """),
                    {
                        "claim_id": claim_id,
                        "status": status,
                    },
                )

            db.commit()

            return {
                "claim_id": claim_id,
                "status": status,
                "expense_id": new_expense_id,
                "paid_date": paid_date if status == "PAID" else None,
                "message": f"Travel expense claim status updated to {status}.",
            }

        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def delete_claim(db: Session, claim_id: int):
        claim = TravelExpenseService.get_claim(db, claim_id)
        try:
            if claim.get("expense_id"):
                db.execute(
                    text("DELETE FROM dbo.OfficeExpense_Transaction WHERE ExpenseId = :expense_id"),
                    {"expense_id": claim["expense_id"]},
                )
            db.execute(
                text("DELETE FROM dbo.TravelExpense_Item WHERE ClaimId = :claim_id"),
                {"claim_id": claim_id},
            )
            db.execute(
                text("DELETE FROM dbo.TravelExpense_Claim WHERE ClaimId = :claim_id"),
                {"claim_id": claim_id},
            )
            db.commit()

            return {
                "claim_id": claim_id,
                "message": f"Travel expense claim #{claim_id} deleted successfully.",
            }
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def summary(
        db: Session,
        from_date: date | None = None,
        to_date: date | None = None,
        employee_code: str | None = None,
    ):
        if from_date and to_date and from_date > to_date:
            raise HTTPException(
                status_code=400,
                detail="from_date cannot be later than to_date.",
            )

        params = {
            "from_date": from_date,
            "to_date": to_date,
            "employee_code": employee_code,
        }

        # Overall totals, claim counts, and overall category breakdowns
        overall = db.execute(
            text("""
                SELECT
                    COUNT(DISTINCT c.ClaimId) AS claim_count,
                    COALESCE(SUM(c.TotalAmount), 0) AS total_amount,
                    COALESCE(SUM(
                        CASE WHEN c.Status = 'PENDING'
                             THEN c.TotalAmount ELSE 0 END
                    ), 0) AS pending_amount,
                    COALESCE(SUM(
                        CASE WHEN c.Status = 'APPROVED'
                             THEN c.TotalAmount ELSE 0 END
                    ), 0) AS approved_amount,
                    COALESCE(SUM(
                        CASE WHEN c.Status = 'PAID'
                             THEN c.TotalAmount ELSE 0 END
                    ), 0) AS paid_amount,
                    COALESCE(SUM(
                        CASE WHEN c.Status = 'REJECTED'
                             THEN c.TotalAmount ELSE 0 END
                    ), 0) AS rejected_amount
                FROM dbo.TravelExpense_Claim c
                WHERE (:from_date IS NULL
                       OR c.TravelStartDate >= :from_date)
                  AND (:to_date IS NULL
                       OR c.TravelStartDate < DATEADD(day, 1, :to_date))
                  AND (:employee_code IS NULL
                       OR c.EmployeeCode = :employee_code)
            """),
            params,
        ).mappings().one()

        # Employee-wise individual breakdown with category totals!
        employees = db.execute(
            text("""
                SELECT
                    c.EmployeeCode AS employee_code,
                    COALESCE(
                        NULLIF(e.DisplayName, ''),
                        CONCAT(e.FirstName, ' ', COALESCE(e.LastName, ''))
                    ) AS employee_name,
                    e.DepartmentName AS department_name,
                    e.DesignationName AS designation_name,
                    COUNT(DISTINCT c.ClaimId) AS claim_count,
                    COALESCE(SUM(i.Amount), 0) AS total_amount,
                    COALESCE(SUM(CASE WHEN i.ExpenseCategory = 'PETROL' THEN i.Amount ELSE 0 END), 0) AS petrol_amount,
                    COALESCE(SUM(CASE WHEN i.ExpenseCategory = 'FOOD' THEN i.Amount ELSE 0 END), 0) AS food_amount,
                    COALESCE(SUM(CASE WHEN i.ExpenseCategory = 'BUS_TICKET' THEN i.Amount ELSE 0 END), 0) AS bus_ticket_amount,
                    COALESCE(SUM(CASE WHEN i.ExpenseCategory = 'ROOM' THEN i.Amount ELSE 0 END), 0) AS room_amount,
                    COALESCE(SUM(CASE WHEN i.ExpenseCategory = 'OTHER' THEN i.Amount ELSE 0 END), 0) AS other_amount
                FROM dbo.TravelExpense_Claim c
                LEFT JOIN dbo.TravelExpense_Item i
                    ON i.ClaimId = c.ClaimId
                LEFT JOIN dbo.Employee_Mst e
                    ON e.EmployeeCode = c.EmployeeCode
                WHERE (:from_date IS NULL
                       OR c.TravelStartDate >= :from_date)
                  AND (:to_date IS NULL
                       OR c.TravelStartDate < DATEADD(day, 1, :to_date))
                  AND (:employee_code IS NULL
                       OR c.EmployeeCode = :employee_code)
                GROUP BY
                    c.EmployeeCode,
                    e.DisplayName,
                    e.FirstName,
                    e.LastName,
                    e.DepartmentName,
                    e.DesignationName
                ORDER BY total_amount DESC
            """),
            params,
        ).mappings().all()

        # Category-wise totals across all items
        categories = db.execute(
            text("""
                SELECT
                    i.ExpenseCategory AS expense_category,
                    COUNT(i.ItemId) AS item_count,
                    COALESCE(SUM(i.Amount), 0) AS total_amount
                FROM dbo.TravelExpense_Item i
                INNER JOIN dbo.TravelExpense_Claim c
                    ON c.ClaimId = i.ClaimId
                WHERE (:from_date IS NULL
                       OR c.TravelStartDate >= :from_date)
                  AND (:to_date IS NULL
                       OR c.TravelStartDate < DATEADD(day, 1, :to_date))
                  AND (:employee_code IS NULL
                       OR c.EmployeeCode = :employee_code)
                GROUP BY i.ExpenseCategory
                ORDER BY total_amount DESC
            """),
            params,
        ).mappings().all()

        return {
            "from_date": from_date,
            "to_date": to_date,
            "employee_code": employee_code,
            "overall": dict(overall),
            "employees": [dict(row) for row in employees],
            "categories": [dict(row) for row in categories],
        }
