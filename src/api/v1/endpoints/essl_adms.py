# src/api/v1/endpoints/essl_logs.py

import re
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session

router = APIRouter(prefix="/essl-logs", tags=["ESSL Attendance Logs"])


@router.get("")
def get_essl_logs(
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    employee_code: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_mssql_session("db1")),
) -> dict[str, Any]:
    """
    Read attendance logs directly from DB1.
    No data is inserted into DB2.
    """

    year, month_number = map(int, month.split("-"))
    table_name = f"DeviceLogs_{month_number}_{year}"

    # Only allow the expected monthly table naming convention.
    if not re.fullmatch(r"DeviceLogs_(0?[1-9]|1[0-2])_\d{4}", table_name):
        raise HTTPException(status_code=400, detail="Invalid log table")

    try:
        # Verify that the monthly table exists in the current DB1.
        table_check = db.execute(
            text("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo'
                  AND TABLE_NAME = :table_name
            """),
            {"table_name": table_name},
        ).scalar()

        if not table_check:
            raise HTTPException(
                status_code=404,
                detail=f"ESSL log table dbo.{table_name} was not found in DB1",
            )

        # Discover actual columns instead of assuming the ESSL schema.
        columns = db.execute(
            text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo'
                  AND TABLE_NAME = :table_name
                ORDER BY ORDINAL_POSITION
            """),
            {"table_name": table_name},
        ).scalars().all()

        column_lookup = {column.lower(): column for column in columns}

        date_column = next(
            (
                column_lookup[name]
                for name in ("logdate", "logtime", "attendancedate")
                if name in column_lookup
            ),
            None,
        )

        if not date_column:
            raise HTTPException(
                status_code=500,
                detail=f"No recognized timestamp column in {table_name}",
            )

        user_column = next(
            (
                column_lookup[name]
                for name in ("userid", "employeeid", "user_id", "pin")
                if name in column_lookup
            ),
            None,
        )

        # Table/column identifiers are selected only from validated database metadata.
        query = f"SELECT TOP ({limit}) * FROM dbo.[{table_name}] WHERE 1=1"
        params: dict[str, Any] = {}

        if from_date:
            query += f" AND [{date_column}] >= :from_date"
            params["from_date"] = from_date

        if to_date:
            query += f" AND [{date_column}] < :to_date"
            params["to_date"] = to_date

        if employee_code:
            if not user_column:
                raise HTTPException(
                    status_code=400,
                    detail="This log table has no recognized employee ID column",
                )

            query += f" AND CAST([{user_column}] AS VARCHAR(100)) = :employee_code"
            params["employee_code"] = employee_code

        query += f" ORDER BY [{date_column}] DESC"

        rows = db.execute(text(query), params).mappings().all()

        return {
            "source": "DB1",
            "table": f"dbo.{table_name}",
            "count": len(rows),
            "limit": limit,
            "logs": [dict(row) for row in rows],
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read ESSL logs: {str(exc)}",
        ) from exc
