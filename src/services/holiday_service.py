from datetime import date, datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.schemas.attendance import HolidayCreate, HolidayUpdate, HolidayResponse


class HolidayService:
    @staticmethod
    def ensure_holiday_table(db: Session):
        """
        Ensures dbo.Attendance_Holiday table exists in DB2.
        """
        try:
            db.execute(text("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Attendance_Holiday' AND schema_id = SCHEMA_ID('dbo'))
                BEGIN
                    CREATE TABLE dbo.Attendance_Holiday (
                        HolidayId INT IDENTITY(1,1) PRIMARY KEY,
                        HolidayDate DATE NOT NULL UNIQUE,
                        HolidayName NVARCHAR(100) NOT NULL,
                        HolidayType NVARCHAR(30) DEFAULT 'OFFICIAL',
                        Description NVARCHAR(250) NULL,
                        Year INT NOT NULL,
                        IsActive BIT DEFAULT 1,
                        CreatedBy NVARCHAR(50) NULL DEFAULT 'HR Admin',
                        CreatedAt DATETIME DEFAULT GETDATE(),
                        UpdatedBy NVARCHAR(50) NULL,
                        UpdatedAt DATETIME DEFAULT GETDATE()
                    );
                    CREATE INDEX IX_Attendance_Holiday_Year ON dbo.Attendance_Holiday(Year, IsActive);
                    CREATE INDEX IX_Attendance_Holiday_Date ON dbo.Attendance_Holiday(HolidayDate);
                END
            """))
            db.commit()
        except Exception:
            db.rollback()

    @staticmethod
    def list_holidays(db: Session, year: Optional[int] = None) -> List[HolidayResponse]:
        HolidayService.ensure_holiday_table(db)
        sql = """
            SELECT HolidayId, HolidayDate, HolidayName, HolidayType, Description, Year, IsActive
            FROM dbo.Attendance_Holiday
            WHERE (:year IS NULL OR Year = :year)
              AND IsActive = 1
            ORDER BY HolidayDate ASC
        """
        rows = db.execute(text(sql), {"year": year}).mappings().all()
        return [
            HolidayResponse(
                holiday_id=r["HolidayId"],
                holiday_date=r["HolidayDate"],
                holiday_name=r["HolidayName"],
                holiday_type=r["HolidayType"] or "OFFICIAL",
                description=r["Description"],
                year=r["Year"],
                is_active=bool(r["IsActive"]),
            )
            for r in rows
        ]

    @staticmethod
    def create_holiday(db: Session, data: HolidayCreate) -> HolidayResponse:
        HolidayService.ensure_holiday_table(db)
        
        existing = db.execute(
            text("SELECT HolidayId FROM dbo.Attendance_Holiday WHERE HolidayDate = :d"),
            {"d": data.holiday_date},
        ).scalar()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A holiday is already scheduled on {data.holiday_date}.",
            )

        h_year = data.year or data.holiday_date.year
        sql = """
            INSERT INTO dbo.Attendance_Holiday (
                HolidayDate, HolidayName, HolidayType, Description, Year, IsActive, CreatedBy, CreatedAt
            )
            OUTPUT INSERTED.HolidayId
            VALUES (
                :hd, :hn, :ht, :desc, :yr, :act, :by, SYSDATETIME()
            )
        """
        try:
            holiday_id = db.execute(
                text(sql),
                {
                    "hd": data.holiday_date,
                    "hn": data.holiday_name.strip(),
                    "ht": (data.holiday_type or "OFFICIAL").strip(),
                    "desc": data.description.strip() if data.description else None,
                    "yr": h_year,
                    "act": 1 if data.is_active else 0,
                    "by": data.created_by or "HR Admin",
                },
            ).scalar_one()
            db.commit()

            return HolidayResponse(
                holiday_id=holiday_id,
                holiday_date=data.holiday_date,
                holiday_name=data.holiday_name.strip(),
                holiday_type=data.holiday_type or "OFFICIAL",
                description=data.description,
                year=h_year,
                is_active=data.is_active,
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create holiday record: {str(e)}",
            )

    @staticmethod
    def update_holiday(db: Session, holiday_id: int, data: HolidayUpdate) -> HolidayResponse:
        HolidayService.ensure_holiday_table(db)

        existing = db.execute(
            text("SELECT HolidayId, HolidayDate, HolidayName, HolidayType, Description, Year, IsActive FROM dbo.Attendance_Holiday WHERE HolidayId = :id"),
            {"id": holiday_id},
        ).mappings().first()

        if not existing:
            raise HTTPException(status_code=404, detail="Holiday record not found.")

        new_name = data.holiday_name.strip() if data.holiday_name else existing["HolidayName"]
        new_type = data.holiday_type.strip() if data.holiday_type else existing["HolidayType"]
        new_desc = data.description.strip() if data.description is not None else existing["Description"]
        new_active = data.is_active if data.is_active is not None else existing["IsActive"]

        try:
            db.execute(
                text("""
                    UPDATE dbo.Attendance_Holiday
                    SET HolidayName = :hn,
                        HolidayType = :ht,
                        Description = :desc,
                        IsActive = :act,
                        UpdatedBy = :by,
                        UpdatedAt = SYSDATETIME()
                    WHERE HolidayId = :id
                """),
                {
                    "id": holiday_id,
                    "hn": new_name,
                    "ht": new_type,
                    "desc": new_desc,
                    "act": 1 if new_active else 0,
                    "by": data.updated_by or "HR Admin",
                },
            )
            db.commit()

            return HolidayResponse(
                holiday_id=holiday_id,
                holiday_date=existing["HolidayDate"],
                holiday_name=new_name,
                holiday_type=new_type,
                description=new_desc,
                year=existing["Year"],
                is_active=bool(new_active),
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update holiday: {str(e)}",
            )

    @staticmethod
    def delete_holiday(db: Session, holiday_id: int):
        HolidayService.ensure_holiday_table(db)
        try:
            result = db.execute(
                text("DELETE FROM dbo.Attendance_Holiday WHERE HolidayId = :id"),
                {"id": holiday_id},
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Holiday not found.")
            db.commit()
            return {"success": True, "message": "Holiday deleted successfully."}
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete holiday: {str(e)}",
            )
