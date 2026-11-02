
# src/services/essl_adms_service.py

import logging
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def save_biometric_punch_to_etimetrack(
    db: Session,
    employee_code: str,
    punch_time: datetime,
    punch_state: str | None = None,
    verify_type: str | None = None,
) -> bool:
    """
    Insert a punch into the existing DB1 monthly DeviceLogs table.
    Returns True if inserted, False if it already exists.
    Does not create tables or assume a DeviceId.
    """
    if not employee_code or not employee_code.strip():
        raise ValueError("Employee code is missing")

    table_name = f"DeviceLogs_{punch_time.month}_{punch_time.year}"

    # The identifier is generated exclusively from a validated datetime.
    if not (
        1 <= punch_time.month <= 12
        and 2000 <= punch_time.year <= 2100
    ):
        raise ValueError("Invalid punch date")

    statement = text(f"""
        IF NOT EXISTS (
            SELECT 1
            FROM dbo.[{table_name}]
            WHERE UserId = :user_id
              AND LogDate = :log_date
        )
        BEGIN
            INSERT INTO dbo.[{table_name}] (
                DownloadDate,
                UserId,
                LogDate,
                Direction,
                AttDirection,
                UpdateFlag,
                IsApproved,
                CreatedDate
            )
            VALUES (
                SYSDATETIME(),
                :user_id,
                :log_date,
                :direction,
                :att_direction,
                0,
                0,
                SYSDATETIME()
            );

            SELECT 1 AS inserted;
        END
        ELSE
        BEGIN
            SELECT 0 AS inserted;
        END
    """)

    try:
        # Do not silently create a table if the monthly table is missing.
        exists = db.execute(
            text("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo'
                  AND TABLE_NAME = :table_name
            """),
            {"table_name": table_name},
        ).scalar_one()

        if not exists:
            raise RuntimeError(
                f"Existing DB1 table dbo.{table_name} does not exist"
            )

        result = db.execute(
            statement,
            {
                "user_id": employee_code.strip(),
                "log_date": punch_time,
                "direction": punch_state,
                "att_direction": verify_type,
            },
        )

        inserted = bool(result.scalar_one())
        db.commit()
        return inserted

    except Exception:
        db.rollback()
        logger.exception("Failed to save punch to DB1")
        raise
