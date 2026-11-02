from datetime import date
from decimal import Decimal,ROUND_HALF_UP, InvalidOperation

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.schemas.office_daily_expense import (
    SettlementCreate,
)
CENT = Decimal("0.01")

def money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)

def month_dates(period_month: str):
    year, month = map(int, period_month.split("-"))
    start = date(year, month, 1)
    end = (
        date(year + 1, 1, 1)
        if month == 12
        else date(year, month + 1, 1)
    )
    return start, end

class OfficeExpenseService:
    EXPENSE_CATEGORIES = {
        "Tea & Snacks",
        "Drinking Water",
        "Flowers",
        "Stationery",
        "Cleaning",
        "Travel",
        "Maintenance",
        "Other",
    }

    @staticmethod
    def _amount(value) -> Decimal:
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise HTTPException(400, "Invalid transaction amount.")

        if not amount.is_finite() or amount <= 0:
            raise HTTPException(400, "Amount must be greater than zero.")

        return amount.quantize(Decimal("0.01"))

    @staticmethod
    def _get_fund(db: Session, fund_id: int):
        fund = db.execute(
            text("""
                SELECT FundId, FundName, OpeningBalance,
                       CurrencyCode, IsActive
                FROM dbo.OfficeExpense_Fund
                WHERE FundId = :fund_id
            """),
            {"fund_id": fund_id},
        ).mappings().first()

        if not fund:
            raise HTTPException(404, "Office expense fund not found.")

        if not fund["IsActive"]:
            raise HTTPException(400, "This fund is inactive.")

        return fund

    @staticmethod
    def create_fund(
        db: Session,
        fund_name: str,
        opening_balance: Decimal,
        created_by: str,
    ):
        name = (fund_name or "").strip()
        if not name:
            raise HTTPException(400, "Fund name is required.")

        try:
            opening_balance = Decimal(str(opening_balance))
        except (InvalidOperation, TypeError, ValueError):
            raise HTTPException(400, "Invalid opening balance.")

        if (
            not opening_balance.is_finite()
            or opening_balance < 0
        ):
            raise HTTPException(
                400, "Opening balance cannot be negative."
            )

        try:
            result = db.execute(
                text("""
                    INSERT INTO dbo.OfficeExpense_Fund
                        (FundName, OpeningBalance, CurrencyCode,
                         IsActive, CreatedBy)
                    OUTPUT INSERTED.FundId
                    VALUES
                        (:name, :balance, 'INR', 1, :created_by)
                """),
                {
                    "name": name,
                    "balance": opening_balance,
                    "created_by": created_by,
                },
            )
            fund_id = result.scalar_one()
            db.commit()

            return {
                "fund_id": fund_id,
                "message": "Office expense fund created successfully.",
            }
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_balance(db: Session, fund_id: int | None = None):
        if fund_id:
            fund = OfficeExpenseService._get_fund(db, fund_id)
            totals = db.execute(
                text("""
                    SELECT
                        COALESCE(SUM(
                            CASE WHEN TransactionType = 'CREDIT'
                                 THEN Amount ELSE 0 END
                        ), 0) AS total_received,
                        COALESCE(SUM(
                            CASE WHEN TransactionType = 'DEBIT'
                                 THEN Amount ELSE 0 END
                        ), 0) AS total_expenses
                    FROM dbo.OfficeExpense_Transaction
                    WHERE FundId = :fund_id
                """),
                {"fund_id": fund_id},
            ).mappings().one()

            opening = Decimal(str(fund["OpeningBalance"] or 0))
            received = Decimal(str(totals["total_received"] or 0))
            spent = Decimal(str(totals["total_expenses"] or 0))

            return {
                "fund_id": fund_id,
                "fund_name": fund["FundName"],
                "currency_code": fund["CurrencyCode"],
                "opening_balance": opening,
                "total_received": received,
                "total_expenses": spent,
                "available_balance": opening + received - spent,
            }

        # Global petty cash ledger balance (no fund_id required)
        totals = db.execute(
            text("""
                SELECT
                    COALESCE(SUM(
                        CASE WHEN TransactionType = 'CREDIT'
                             THEN Amount ELSE 0 END
                    ), 0) AS total_received,
                    COALESCE(SUM(
                        CASE WHEN TransactionType = 'DEBIT'
                             THEN Amount ELSE 0 END
                    ), 0) AS total_expenses
                FROM dbo.OfficeExpense_Transaction
            """)
        ).mappings().one()

        # Opening balance is sum of initial fund balances or 0
        fund_opening = db.execute(
            text("""
                SELECT COALESCE(SUM(OpeningBalance), 0)
                FROM dbo.OfficeExpense_Fund
                WHERE IsActive = 1
            """)
        ).scalar_one()

        opening = Decimal(str(fund_opening or 0))
        received = Decimal(str(totals["total_received"] or 0))
        spent = Decimal(str(totals["total_expenses"] or 0))

        return {
            "fund_id": None,
            "fund_name": "Petty Cash",
            "currency_code": "INR",
            "opening_balance": opening,
            "total_received": received,
            "total_expenses": spent,
            "available_balance": opening + received - spent,
        }

    @staticmethod
    def _insert_transaction(
        db: Session,
        *,
        fund_id: int | None,
        transaction_date: date,
        transaction_type: str,
        category: str,
        description: str | None,
        amount: Decimal,
        received_from: str | None,
        receiver_name: str | None,
        quantity: Decimal | None,
        remarks: str | None,
        serial_no: int | None,
        created_by: str,
    ):
        result = db.execute(
            text("""
                INSERT INTO dbo.OfficeExpense_Transaction
                (
                    FundId, SerialNo, ExpenseDate, ReceiverName,
                    ProductName, Amount, Remarks, CreatedBy,
                    TransactionType, Category, [Description],
                    ReceivedFrom, Quantity
                )
                OUTPUT INSERTED.ExpenseId
                VALUES
                (
                    :fund_id, :serial_no, :transaction_date,
                    :receiver_name, :product_name, :amount,
                    :remarks, :created_by, :transaction_type,
                    :category, :description, :received_from, :quantity
                )
            """),
            {
                "fund_id": fund_id,
                "serial_no": serial_no,
                "transaction_date": transaction_date,
                "receiver_name": receiver_name,
                "product_name": category,
                "amount": amount,
                "remarks": remarks,
                "created_by": created_by,
                "transaction_type": transaction_type,
                "category": category,
                "description": description,
                "received_from": received_from,
                "quantity": quantity,
            },
        )
        return result.scalar_one()

    @staticmethod
    def add_credit(
        db: Session,
        fund_id: int | None = None,
        transaction_date: date = None,
        amount: Decimal = Decimal("0"),
        received_from: str = "",
        description: str | None = None,
        remarks: str | None = None,
        created_by: str = "admin",
    ):
        if fund_id:
            OfficeExpenseService._get_fund(db, fund_id)
        amount = OfficeExpenseService._amount(amount)

        source = (received_from or "").strip()
        if not source:
            raise HTTPException(
                400, "Owner or management name is required."
            )

        try:
            transaction_id = OfficeExpenseService._insert_transaction(
                db,
                fund_id=fund_id,
                transaction_date=transaction_date or date.today(),
                transaction_type="CREDIT",
                category="Money Received",
                description=description or f"Money received from {source}",
                amount=amount,
                received_from=source,
                receiver_name=None,
                quantity=None,
                remarks=remarks,
                serial_no=None,
                created_by=created_by,
            )
            db.commit()

            return {
                "transaction_id": transaction_id,
                "message": "Money received recorded successfully.",
                **OfficeExpenseService.get_balance(db, fund_id),
            }
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def add_expense(
        db: Session,
        fund_id: int | None = None,
        expense_date: date = None,
        product_name: str | None = None,
        amount: Decimal = Decimal("0"),
        receiver_name: str | None = None,
        remarks: str | None = None,
        serial_no: int | None = None,
        created_by: str = "admin",
        category: str | None = None,
        description: str | None = None,
        quantity: Decimal | None = None,
    ):
        if fund_id:
            OfficeExpenseService._get_fund(db, fund_id)
        amount = OfficeExpenseService._amount(amount)

        desc = (description or product_name or category or "Office Expense").strip()
        if not desc:
            raise HTTPException(400, "Expense description is required.")

        selected_category = (category or desc).strip()
        if not selected_category:
            selected_category = "Other"

        balance = OfficeExpenseService.get_balance(db, fund_id)
        if amount > balance["available_balance"]:
            raise HTTPException(
                400,
                f"Insufficient balance. Available: ₹{balance['available_balance']:.2f}, Requested: ₹{amount:.2f}",
            )

        if quantity is not None:
            try:
                quantity = Decimal(str(quantity))
            except (InvalidOperation, TypeError, ValueError):
                raise HTTPException(400, "Invalid quantity.")

            if not quantity.is_finite() or quantity <= 0:
                raise HTTPException(
                    400, "Quantity must be greater than zero."
                )

        try:
            transaction_id = OfficeExpenseService._insert_transaction(
                db,
                fund_id=fund_id,
                transaction_date=expense_date or date.today(),
                transaction_type="DEBIT",
                category=selected_category,
                description=desc,
                amount=amount,
                received_from=None,
                receiver_name=receiver_name,
                quantity=quantity,
                remarks=remarks,
                serial_no=serial_no,
                created_by=created_by,
            )
            db.commit()

            return {
                "transaction_id": transaction_id,
                "message": "Office expense recorded successfully.",
                **OfficeExpenseService.get_balance(db, fund_id),
            }
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def list_transactions(
        db: Session,
        fund_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        transaction_type: str | None = None,
    ):
        if fund_id:
            OfficeExpenseService._get_fund(db, fund_id)

        if from_date and to_date and from_date > to_date:
            raise HTTPException(
                400, "from_date cannot be later than to_date."
            )

        if transaction_type:
            transaction_type = transaction_type.upper()
            if transaction_type not in {"CREDIT", "DEBIT"}:
                raise HTTPException(
                    400, "transaction_type must be CREDIT or DEBIT."
                )

        rows = db.execute(
            text("""
                SELECT
                    ExpenseId AS TransactionId,
                    FundId,
                    ExpenseDate AS TransactionDate,
                    TransactionType,
                    Category,
                    [Description],
                    ProductName,
                    Amount,
                    ReceivedFrom,
                    ReceiverName,
                    Quantity,
                    Remarks,
                    SerialNo,
                    CreatedBy,
                    CreatedAt,
                    UpdatedBy,
                    UpdatedAt
                FROM dbo.OfficeExpense_Transaction
                WHERE (:fund_id IS NULL OR FundId = :fund_id)
                  AND (:from_date IS NULL OR ExpenseDate >= :from_date)
                  AND (:to_date IS NULL OR ExpenseDate < DATEADD(day, 1, :to_date))
                  AND (
                      :transaction_type IS NULL
                      OR TransactionType = :transaction_type
                  )
                ORDER BY ExpenseDate, SerialNo, ExpenseId
            """),
            {
                "fund_id": fund_id,
                "from_date": from_date,
                "to_date": to_date,
                "transaction_type": transaction_type,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    @staticmethod
    def list_expenses(
        db: Session,
        fund_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        return OfficeExpenseService.list_transactions(
            db,
            fund_id,
            from_date,
            to_date,
            "DEBIT",
        )

    @staticmethod
    def monthly_report(
        db: Session,
        year: int,
        month: int,
        fund_id: int | None = None,
    ):
        if month < 1 or month > 12:
            raise HTTPException(
                400, "Month must be between 1 and 12."
            )

        start_date = date(year, month, 1)
        end_date = (
            date(year + 1, 1, 1)
            if month == 12
            else date(year, month + 1, 1)
        )

        base_opening = Decimal("0.00")
        if fund_id:
            fund = OfficeExpenseService._get_fund(db, fund_id)
            base_opening = Decimal(str(fund["OpeningBalance"] or 0))
        else:
            fund_opening = db.execute(
                text("""
                    SELECT COALESCE(SUM(OpeningBalance), 0)
                    FROM dbo.OfficeExpense_Fund
                    WHERE IsActive = 1
                """)
            ).scalar_one()
            base_opening = Decimal(str(fund_opening or 0))

        opening_result = db.execute(
            text("""
                SELECT COALESCE(SUM(
                    CASE
                        WHEN TransactionType = 'CREDIT' THEN Amount
                        WHEN TransactionType = 'DEBIT' THEN -Amount
                        ELSE 0
                    END
                ), 0)
                FROM dbo.OfficeExpense_Transaction
                WHERE (:fund_id IS NULL OR FundId = :fund_id)
                  AND ExpenseDate < :start_date
            """),
            {
                "fund_id": fund_id,
                "start_date": start_date,
            },
        ).scalar_one()

        totals = db.execute(
            text("""
                SELECT
                    COALESCE(SUM(CASE
                        WHEN TransactionType = 'CREDIT'
                        THEN Amount ELSE 0 END), 0) AS funds_received,
                    COALESCE(SUM(CASE
                        WHEN TransactionType = 'DEBIT'
                        THEN Amount ELSE 0 END), 0) AS total_expenses
                FROM dbo.OfficeExpense_Transaction
                WHERE (:fund_id IS NULL OR FundId = :fund_id)
                  AND ExpenseDate >= :start_date
                  AND ExpenseDate < :end_date
            """),
            {
                "fund_id": fund_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        ).mappings().one()

        opening_balance = base_opening + Decimal(str(opening_result or 0))
        received = Decimal(str(totals["funds_received"] or 0))
        expenses = Decimal(str(totals["total_expenses"] or 0))

        transactions = OfficeExpenseService.list_transactions(
            db,
            fund_id,
            start_date,
            date.fromordinal(end_date.toordinal() - 1),
        )

        return {
            "fund_id": fund_id,
            "year": year,
            "month": month,
            "opening_balance": opening_balance,
            "funds_received": received,
            "total_expenses": expenses,
            "closing_balance": opening_balance + received - expenses,
            "transactions": transactions,
        }

    @staticmethod
    def list_funds(db: Session):
        rows = db.execute(
            text("""
                SELECT
                    f.FundId,
                    f.FundName,
                    f.OpeningBalance,
                    f.CurrencyCode,
                    f.IsActive,
                    f.CreatedBy,
                    f.CreatedAt,
                    f.OpeningBalance + COALESCE(SUM(
                        CASE
                            WHEN t.TransactionType = 'CREDIT'
                                THEN t.Amount
                            WHEN t.TransactionType = 'DEBIT'
                                THEN -t.Amount
                            ELSE 0
                        END
                    ), 0) AS available_balance,
                    COALESCE(SUM(CASE
                        WHEN t.TransactionType = 'CREDIT'
                        THEN t.Amount ELSE 0 END), 0) AS total_received,
                    COALESCE(SUM(CASE
                        WHEN t.TransactionType = 'DEBIT'
                        THEN t.Amount ELSE 0 END), 0) AS total_expenses
                FROM dbo.OfficeExpense_Fund f
                LEFT JOIN dbo.OfficeExpense_Transaction t
                    ON t.FundId = f.FundId
                WHERE f.IsActive = 1
                GROUP BY
                    f.FundId, f.FundName, f.OpeningBalance,
                    f.CurrencyCode, f.IsActive, f.CreatedBy, f.CreatedAt
                ORDER BY f.FundId DESC
            """)
        ).mappings().all()

        return [dict(row) for row in rows]


    @staticmethod
    def update_transaction(
        db: Session,
        transaction_id: int,
        transaction_date: date | None = None,
        transaction_type: str | None = None,
        category: str | None = None,
        product_name: str | None = None,
        description: str | None = None,
        amount: Decimal | None = None,
        received_from: str | None = None,
        receiver_name: str | None = None,
        quantity: Decimal | None = None,
        remarks: str | None = None,
        updated_by: str = "admin",
    ):
        try:
            existing = db.execute(
                text("""
                    SELECT ExpenseId, FundId, TransactionType, Amount, ExpenseDate
                    FROM dbo.OfficeExpense_Transaction
                    WHERE ExpenseId = :transaction_id
                """),
                {"transaction_id": transaction_id},
            ).mappings().first()

            if not existing:
                raise HTTPException(404, "Transaction not found.")

            parsed_amount = None
            if amount is not None:
                parsed_amount = OfficeExpenseService._amount(amount)

            db.execute(
                text("""
                    UPDATE dbo.OfficeExpense_Transaction
                    SET
                        ExpenseDate = COALESCE(:expense_date, ExpenseDate),
                        TransactionType = COALESCE(:transaction_type, TransactionType),
                        Category = COALESCE(:category, Category),
                        ProductName = COALESCE(:product_name, ProductName),
                        [Description] = COALESCE(:description, [Description]),
                        Amount = COALESCE(:amount, Amount),
                        ReceivedFrom = COALESCE(:received_from, ReceivedFrom),
                        ReceiverName = COALESCE(:receiver_name, ReceiverName),
                        Quantity = COALESCE(:quantity, Quantity),
                        Remarks = COALESCE(:remarks, Remarks),
                        UpdatedBy = :updated_by,
                        UpdatedAt = SYSDATETIME()
                    WHERE ExpenseId = :transaction_id
                """),
                {
                    "transaction_id": transaction_id,
                    "expense_date": transaction_date,
                    "transaction_type": transaction_type,
                    "category": category,
                    "product_name": product_name,
                    "description": description,
                    "amount": parsed_amount,
                    "received_from": received_from,
                    "receiver_name": receiver_name,
                    "quantity": quantity,
                    "remarks": remarks,
                    "updated_by": updated_by,
                },
            )
            db.commit()

            return {
                "transaction_id": transaction_id,
                "message": "Transaction updated successfully.",
                **OfficeExpenseService.get_balance(db, existing["FundId"]),
            }
        except HTTPException:
            raise
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def delete_transaction(db: Session, transaction_id: int):
        try:
            result = db.execute(
                text("""
                    DELETE FROM dbo.OfficeExpense_Transaction
                    WHERE ExpenseId = :transaction_id
                """),
                {"transaction_id": transaction_id},
            )

            if result.rowcount == 0:
                db.rollback()
                raise HTTPException(404, "Transaction not found.")

            db.commit()
            return {"message": "Transaction deleted successfully."}
        except HTTPException:
            raise
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def delete_expense(db: Session, expense_id: int):
        return OfficeExpenseService.delete_transaction(db, expense_id)

    @staticmethod
    def batch_add_expenses(
        db: Session,
        fund_id: int | None,
        items: list,
        created_by: str,
    ):
        balance = OfficeExpenseService.get_balance(db, fund_id)

        normalized_items = []
        total_required = Decimal("0.00")

        for item in items:
            amount = OfficeExpenseService._amount(item.get("amount", 0))
            total_required += amount
            normalized_items.append((item, amount))

        if total_required > balance["available_balance"]:
            raise HTTPException(
                400,
                f"Insufficient funds. Required: ₹{total_required:.2f}; "
                f"available: ₹{balance['available_balance']:.2f}.",
            )

        inserted_count = 0

        try:
            for item, amount in normalized_items:
                product = str(item.get("product_name") or item.get("description") or item.get("category") or "Office Expense").strip()
                transaction_id = OfficeExpenseService._insert_transaction(
                    db,
                    fund_id=fund_id,
                    transaction_date=item.get("expense_date") or date.today(),
                    transaction_type="DEBIT",
                    category=str(item.get("category") or product).strip(),
                    description=item.get("description") or product,
                    amount=amount,
                    received_from=None,
                    receiver_name=item.get("receiver_name"),
                    quantity=item.get("quantity"),
                    remarks=item.get("remarks"),
                    serial_no=item.get("serial_no"),
                    created_by=created_by,
                )
                inserted_count += 1

            db.commit()
        except Exception:
            db.rollback()
            raise

        return {
            "message": f"Successfully recorded {inserted_count} expenses.",
            "inserted_count": inserted_count,
            **OfficeExpenseService.get_balance(db, fund_id),
        }


    # ---------------------------------------------------------
    # SETTLE A VENDOR
    # ---------------------------------------------------------
    @staticmethod
    def settle_vendor(
        db: Session,
        data: SettlementCreate,
        created_by: str,
    ):
        from src.services.office_expense_service import OfficeExpenseService

        vendor = data.vendor_name.strip()
        if not vendor:
            raise HTTPException(400, "Vendor name is required.")

        start, end = month_dates(data.period_month)

        try:
            # Serialize ledger settlements to reduce concurrent balance races.
            lock_result = db.execute(text("""
                DECLARE @result INT;
                EXEC @result = sys.sp_getapplock
                    @Resource = 'OfficeExpenseLedger',
                    @LockMode = 'Exclusive',
                    @LockOwner = 'Transaction',
                    @LockTimeout = 10000;
                SELECT @result;
            """)).scalar_one()

            if lock_result < 0:
                raise HTTPException(
                    503, "Could not lock the petty cash ledger. Retry."
                )

            # Lock all outstanding entries for this vendor and month.
            rows = db.execute(text("""
                SELECT EntryId, Amount
                FROM dbo.OfficeDaily_Entry WITH (UPDLOCK, HOLDLOCK)
                WHERE VendorName = :vendor
                  AND ExpenseDate >= :start_date
                  AND ExpenseDate < :end_date
                  AND Status = 'UNSETTLED'
            """), {
                "vendor": vendor,
                "start_date": start,
                "end_date": end,
            }).mappings().all()

            if not rows:
                raise HTTPException(
                    409, "No unsettled expenses found for this vendor and month."
                )

            amount = money(sum(
                (Decimal(str(row["Amount"])) for row in rows),
                Decimal("0.00"),
            ))

            # Validate fund and available cash using the existing ledger service.
            if data.fund_id is not None:
                OfficeExpenseService._get_fund(db, data.fund_id)

            balance = OfficeExpenseService.get_balance(db, data.fund_id)

            if amount > Decimal(str(balance["available_balance"])):
                raise HTTPException(
                    400,
                    f"Insufficient petty cash. Available: "
                    f"₹{balance['available_balance']:.2f}; "
                    f"required: ₹{amount:.2f}.",
                )

            # Create settlement record first; transaction remains uncommitted.
            settlement_id = db.execute(text("""
                INSERT INTO dbo.OfficeDaily_Settlement
                (
                    VendorName, PeriodMonth, Amount, PaymentDate,
                    PaymentMethod, Category, FundId, Reference,
                    Remarks, CreatedBy
                )
                OUTPUT INSERTED.SettlementId
                VALUES
                (
                    :vendor, :period_month, :amount, :payment_date,
                    :payment_method, :category, :fund_id, :reference,
                    :remarks, :created_by
                )
            """), {
                "vendor": vendor,
                "period_month": data.period_month,
                "amount": amount,
                "payment_date": data.payment_date,
                "payment_method": data.payment_method,
                "category": data.category.strip() or "Other",
                "fund_id": data.fund_id,
                "reference": data.reference,
                "remarks": data.remarks,
                "created_by": created_by,
            }).scalar_one()

            # Insert into the EXISTING petty cash ledger.
            # Do not call add_expense(): it commits internally.
            description = (
                f"{vendor} monthly bill settlement "
                f"({data.period_month})"
            )

            ledger_transaction_id = OfficeExpenseService._insert_transaction(
                db,
                fund_id=data.fund_id,
                transaction_date=data.payment_date,
                transaction_type="DEBIT",
                category=data.category.strip() or "Other",
                description=description,
                amount=amount,
                received_from=None,
                receiver_name=vendor,
                quantity=None,
                remarks=data.remarks or data.reference,
                serial_no=None,
                created_by=created_by,
            )

            # Link the settlement to its ledger transaction.
            db.execute(text("""
                UPDATE dbo.OfficeDaily_Settlement
                SET LedgerTransactionId = :transaction_id
                WHERE SettlementId = :settlement_id
            """), {
                "transaction_id": ledger_transaction_id,
                "settlement_id": settlement_id,
            })

            # Mark only the entries included in this settlement.
            entry_ids = [row["EntryId"] for row in rows]

            # Update by the selected IDs, not every entry for this vendor.
            for entry_id in entry_ids:
                db.execute(text("""
                    UPDATE dbo.OfficeDaily_Entry
                    SET Status = 'SETTLED',
                        SettlementId = :settlement_id,
                        UpdatedAt = SYSDATETIME()
                    WHERE EntryId = :entry_id
                      AND Status = 'UNSETTLED'
                """), {
                    "settlement_id": settlement_id,
                    "entry_id": entry_id,
                })

            db.commit()

            return {
                "settlement_id": settlement_id,
                "ledger_transaction_id": ledger_transaction_id,
                "vendor": vendor,
                "period_month": data.period_month,
                "amount": amount,
                "payment_date": data.payment_date,
                "payment_method": data.payment_method,
                "message": "Vendor settlement recorded successfully.",
            }

        except Exception:
            db.rollback()
            raise

