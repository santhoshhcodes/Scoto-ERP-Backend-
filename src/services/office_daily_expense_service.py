
import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.schemas.office_daily_expense import (
    DailyItemCreate,
    DailyItemUpdate,
    DailyUsageSave,
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


class OfficeDailyExpenseService:

    # ---------------------------------------------------------
    # ITEMS
    # ---------------------------------------------------------
    @staticmethod
    def list_items(db: Session, include_inactive: bool = False):
        rows = db.execute(text("""
            SELECT ItemId AS id, ItemName AS name,
                   UnitRate AS rate, UnitName AS unit,
                   VendorName AS vendor, Category AS category,
                   IconType AS icon_type, IsActive AS is_active
            FROM dbo.OfficeDaily_Item
            WHERE (:include_inactive = 1 OR IsActive = 1)
            ORDER BY ItemName
        """), {"include_inactive": include_inactive}).mappings().all()

        return [dict(row) for row in rows]

    @staticmethod
    def create_item(db: Session, data: DailyItemCreate, created_by: str):
        name = data.name.strip()
        vendor = data.vendor.strip()

        if not name or not vendor:
            raise HTTPException(400, "Item name and vendor are required.")

        try:
            result = db.execute(text("""
                INSERT INTO dbo.OfficeDaily_Item
                    (ItemName, UnitRate, UnitName, VendorName,
                     Category, IconType, CreatedBy)
                OUTPUT INSERTED.ItemId
                VALUES
                    (:name, :rate, :unit, :vendor,
                     :category, :icon_type, :created_by)
            """), {
                "name": name,
                "rate": money(data.rate),
                "unit": data.unit.strip(),
                "vendor": vendor,
                "category": data.category.strip() or "Other",
                "icon_type": data.icon_type,
                "created_by": created_by,
            })

            item_id = result.scalar_one()
            db.commit()
            return {"item_id": item_id, "message": "Item created."}

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def update_item(
        db: Session, item_id: int, data: DailyItemUpdate
    ):
        try:
            result = db.execute(text("""
                UPDATE dbo.OfficeDaily_Item
                SET ItemName = :name,
                    UnitRate = :rate,
                    UnitName = :unit,
                    VendorName = :vendor,
                    Category = :category,
                    IconType = :icon_type,
                    IsActive = :is_active,
                    UpdatedAt = SYSDATETIME()
                WHERE ItemId = :item_id
            """), {
                "item_id": item_id,
                "name": data.name.strip(),
                "rate": money(data.rate),
                "unit": data.unit.strip(),
                "vendor": data.vendor.strip(),
                "category": data.category.strip() or "Other",
                "icon_type": data.icon_type,
                "is_active": data.is_active,
            })

            if result.rowcount == 0:
                raise HTTPException(404, "Expense item not found.")

            db.commit()
            return {"message": "Item updated."}

        except Exception:
            db.rollback()
            raise

    # ---------------------------------------------------------
    # DAILY USAGE
    # ---------------------------------------------------------
    @staticmethod
    def get_daily_usage(db: Session, expense_date: date):
        rows = db.execute(text("""
            SELECT EntryId AS entry_id, ExpenseDate AS expense_date,
                   ItemId AS item_id, ItemName AS item_name,
                   Quantity AS quantity, UnitRate AS rate,
                   Amount AS amount, VendorName AS vendor,
                   Category AS category, Status AS status,
                   SettlementId AS settlement_id, Remarks AS remarks
            FROM dbo.OfficeDaily_Entry
            WHERE ExpenseDate = :expense_date
            ORDER BY EntryId
        """), {"expense_date": expense_date}).mappings().all()

        entries = [dict(row) for row in rows]
        return {
            "expense_date": expense_date,
            "total_amount": sum(
                (Decimal(str(row["amount"])) for row in entries),
                Decimal("0.00"),
            ),
            "entries": entries,
        }

    @staticmethod
    def save_daily_usage(
        db: Session,
        data: DailyUsageSave,
        created_by: str,
    ):
        # Reject duplicate item IDs in the same request.
        item_ids = [item.item_id for item in data.items]
        if len(item_ids) != len(set(item_ids)):
            raise HTTPException(400, "Duplicate item IDs in request.")

        try:
            # Lock existing rows for this date while replacing its usage.
            existing = db.execute(text("""
                SELECT EntryId, Status
                FROM dbo.OfficeDaily_Entry WITH (UPDLOCK, HOLDLOCK)
                WHERE ExpenseDate = :expense_date
            """), {"expense_date": data.expense_date}).mappings().all()

            if any(row["Status"] == "SETTLED" for row in existing):
                raise HTTPException(
                    409,
                    "This date contains settled expenses and cannot be "
                    "replaced. Use an adjustment workflow instead.",
                )

            # Resolve current item rates and vendors on the server.
            prepared = []
            for item in data.items:
                master = db.execute(text("""
                    SELECT ItemId, ItemName, UnitRate, UnitName,
                           VendorName, Category
                    FROM dbo.OfficeDaily_Item
                    WHERE ItemId = :item_id AND IsActive = 1
                """), {"item_id": item.item_id}).mappings().first()

                if not master:
                    raise HTTPException(
                        400, f"Active item {item.item_id} not found."
                    )

                qty = Decimal(str(item.quantity))
                rate = Decimal(str(master["UnitRate"]))
                amount = money(qty * rate)

                prepared.append({
                    "item_id": item.item_id,
                    "item_name": master["ItemName"],
                    "quantity": qty,
                    "rate": rate,
                    "amount": amount,
                    "vendor": master["VendorName"],
                    "category": master["Category"],
                    "remarks": item.remarks,
                })

            # Replace only unsettled entries for this date.
            db.execute(text("""
                DELETE FROM dbo.OfficeDaily_Entry
                WHERE ExpenseDate = :expense_date
                  AND Status = 'UNSETTLED'
            """), {"expense_date": data.expense_date})

            for row in prepared:
                db.execute(text("""
                    INSERT INTO dbo.OfficeDaily_Entry
                    (
                        ExpenseDate, ItemId, ItemName, Quantity,
                        UnitRate, Amount, VendorName, Category,
                        Status, Remarks, CreatedBy
                    )
                    VALUES
                    (
                        :expense_date, :item_id, :item_name, :quantity,
                        :rate, :amount, :vendor, :category,
                        'UNSETTLED', :remarks, :created_by
                    )
                """), {
                    **row,
                    "expense_date": data.expense_date,
                    "created_by": created_by,
                })

            db.commit()

        except Exception:
            db.rollback()
            raise

        return OfficeDailyExpenseService.get_daily_usage(
            db, data.expense_date
        )

    # ---------------------------------------------------------
    # PERIOD REGISTER
    # ---------------------------------------------------------
    @staticmethod
    def list_entries(
        db: Session,
        from_date: date,
        to_date: date,
        search: str | None = None,
    ):
        if from_date > to_date:
            raise HTTPException(400, "from_date must not exceed to_date.")

        rows = db.execute(text("""
            SELECT EntryId AS entry_id, ExpenseDate AS expense_date,
                   ItemId AS item_id, ItemName AS item_name,
                   Quantity AS quantity, UnitRate AS rate,
                   Amount AS amount, VendorName AS vendor,
                   Category AS category, Status AS status,
                   SettlementId AS settlement_id, Remarks AS remarks
            FROM dbo.OfficeDaily_Entry
            WHERE ExpenseDate >= :from_date
              AND ExpenseDate < DATEADD(day, 1, :to_date)
              AND (
                    :search IS NULL
                    OR ItemName LIKE :pattern
                    OR VendorName LIKE :pattern
                    OR Category LIKE :pattern
                  )
            ORDER BY ExpenseDate DESC, EntryId DESC
        """), {
            "from_date": from_date,
            "to_date": to_date,
            "search": search.strip() if search and search.strip() else None,
            "pattern": f"%{search.strip()}%" if search and search.strip() else "%",
        }).mappings().all()

        entries = [dict(row) for row in rows]

        total = sum(
            (Decimal(str(row["amount"])) for row in entries),
            Decimal("0.00"),
        )
        unsettled = sum(
            (
                Decimal(str(row["amount"]))
                for row in entries
                if row["status"] == "UNSETTLED"
            ),
            Decimal("0.00"),
        )

        return {
            "from_date": from_date,
            "to_date": to_date,
            "total_amount": total,
            "unsettled_amount": unsettled,
            "entries": entries,
        }

    # ---------------------------------------------------------
    # VENDOR BALANCES
    # ---------------------------------------------------------
    @staticmethod
    def vendor_summary(db: Session, period_month: str):
        start, end = month_dates(period_month)

        rows = db.execute(text("""
            SELECT
                VendorName AS vendor,
                COUNT(*) AS entry_count,
                SUM(Quantity) AS total_quantity,
                SUM(Amount) AS total_amount,
                SUM(CASE WHEN Status = 'UNSETTLED'
                         THEN Amount ELSE 0 END) AS unsettled_amount
            FROM dbo.OfficeDaily_Entry
            WHERE ExpenseDate >= :start_date
              AND ExpenseDate < :end_date
            GROUP BY VendorName
            ORDER BY VendorName
        """), {"start_date": start, "end_date": end}).mappings().all()

        return {
            "period_month": period_month,
            "vendors": [dict(row) for row in rows],
        }

    # ---------------------------------------------------------
    # SETTLE A VENDOR
    # ---------------------------------------------------------
    @staticmethod
    def settle_vendor(db: Session, data: SettlementCreate, created_by: str = "admin"):
        from src.services.office_expense_service import OfficeExpenseService
        return OfficeExpenseService.settle_vendor(db, data, created_by)

