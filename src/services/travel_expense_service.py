from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.schemas.travel_expense import TravelExpenseClaimCreate, TravelExpenseStatusUpdate
from src.services.office_expense_service import OfficeExpenseService
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
    def list_claims(
        db: Session,
        employee_code: str | None = None,
        status: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
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

        rows = db.execute(
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
                WHERE
                    (:employee_code IS NULL OR c.EmployeeCode = :employee_code)
                    AND (:status IS NULL OR c.Status = :status)
                    AND (:from_date IS NULL OR c.TravelStartDate >= :from_date)
                    AND (:to_date IS NULL OR c.TravelStartDate < DATEADD(day, 1, :to_date))
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
                ORDER BY c.ClaimId DESC
            """),
            {
                "employee_code": employee_code,
                "status": status,
                "from_date": from_date,
                "to_date": to_date,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

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
