
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.schemas.transaction import (
    ProformaCreate,
    ProformaUpdate,
    ProformaApprovalUpdate,
)


class ProformaInvoiceService:
    """Business logic and database operations for Proforma Invoices."""

    @staticmethod
    def ensure_tables_exist(db: Session) -> None:
        """Create the Proforma Invoice tables if they do not exist."""
        sql = """
        IF OBJECT_ID('dbo.Acc_Proforma_Inv_Main', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.Acc_Proforma_Inv_Main (
                Ccode VARCHAR(10) DEFAULT '01',
                Lcode VARCHAR(10) DEFAULT '01',
                FinYearVal VARCHAR(20) DEFAULT '2026-2027',
                FinYearCode VARCHAR(10) DEFAULT '01',
                TransNo VARCHAR(50) PRIMARY KEY,
                TransDate VARCHAR(30),
                QuotationNo VARCHAR(50),
                QuotationDate VARCHAR(30),
                CustomerCode VARCHAR(50),
                CustomerName NVARCHAR(255),
                TotalQty NUMERIC(18,2) DEFAULT 0,
                TotalItemAmount NUMERIC(18,2) DEFAULT 0,
                TotalCGSTAmount NUMERIC(18,2) DEFAULT 0,
                TotalSGSTAmount NUMERIC(18,2) DEFAULT 0,
                TotalIGSTAmount NUMERIC(18,2) DEFAULT 0,
                TotalAmount NUMERIC(18,2) DEFAULT 0,
                Remarks NVARCHAR(500),
                RoundType VARCHAR(20) DEFAULT 'None',
                RoundOff NUMERIC(18,2) DEFAULT 0,
                NetAmount NUMERIC(18,2) DEFAULT 0,
                ApprovalStatus VARCHAR(50) DEFAULT '0',
                ApprovedBy VARCHAR(50),
                ApprovedOn DATETIME,
                Status VARCHAR(20) DEFAULT 'Add',
                UserName VARCHAR(50) DEFAULT 'ADMIN',
                UserCode VARCHAR(50) DEFAULT 'ADMIN',
                SysIp VARCHAR(50) DEFAULT '127.0.0.1',
                SysName VARCHAR(50) DEFAULT 'API_SERVER',
                CreateOn DATETIME DEFAULT GETDATE()
            );
        END;

        IF OBJECT_ID('dbo.Acc_Proforma_Inv_Sub', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.Acc_Proforma_Inv_Sub (
                Ccode VARCHAR(10) DEFAULT '01',
                Lcode VARCHAR(10) DEFAULT '01',
                FinYearCode VARCHAR(10) DEFAULT '01',
                FinYearVal VARCHAR(20) DEFAULT '2026-2027',
                TransNo VARCHAR(50),
                TransDate VARCHAR(30),
                QuotationNo VARCHAR(50),
                QuotationDate VARCHAR(30),
                CustomerCode VARCHAR(50),
                CustomerName NVARCHAR(255),
                ItemCode VARCHAR(50),
                ProductType NVARCHAR(255),
                HSNCode VARCHAR(30),
                Qty NUMERIC(18,2) DEFAULT 0,
                Rate NUMERIC(18,2) DEFAULT 0,
                ItemValue NUMERIC(18,2) DEFAULT 0,
                GST NUMERIC(18,2) DEFAULT 0,
                CGST NUMERIC(18,2) DEFAULT 0,
                SGST NUMERIC(18,2) DEFAULT 0,
                IGST NUMERIC(18,2) DEFAULT 0,
                NetAmount NUMERIC(18,2) DEFAULT 0,
                Service NVARCHAR(255) DEFAULT 'Standard Supply',
                Status VARCHAR(20) DEFAULT 'Add',
                UserName VARCHAR(50) DEFAULT 'ADMIN',
                UserCode VARCHAR(50) DEFAULT 'ADMIN',
                SysIp VARCHAR(50) DEFAULT '127.0.0.1',
                SysName VARCHAR(50) DEFAULT 'API_SERVER',
                CreateOn DATETIME DEFAULT GETDATE()
            );
        END;
        """
        db.execute(text(sql))
        db.commit()

    @staticmethod
    def _get_items(
        db: Session,
        trans_no: str,
    ) -> List[Dict[str, Any]]:
        result = db.execute(
            text("""
                SELECT
                    ItemCode, ProductType, HSNCode, Qty, Rate,
                    ItemValue, GST, CGST, SGST, IGST, NetAmount, Service
                FROM Acc_Proforma_Inv_Sub
                WHERE TransNo = :trans_no
                  AND (Status IS NULL OR Status <> 'Delete')
            """),
            {"trans_no": trans_no},
        ).mappings().all()

        return [dict(row) for row in result]

    @staticmethod
    def _header_select() -> str:
        return """
            SELECT
                TransNo,
                CONVERT(VARCHAR(10), TransDate, 120) AS TransDate,
                QuotationNo,
                CONVERT(VARCHAR(10), QuotationDate, 120) AS QuotationDate,
                CustomerCode,
                CustomerName,
                Remarks,
                TotalQty,
                TotalItemAmount,
                TotalCGSTAmount,
                TotalSGSTAmount,
                TotalIGSTAmount,
                TotalAmount,
                RoundType,
                RoundOff,
                NetAmount AS FinalNetAmount,
                CASE
                    WHEN LTRIM(RTRIM(ApprovalStatus)) = '1'
                      OR LOWER(LTRIM(RTRIM(ApprovalStatus))) = 'approved'
                    THEN 'Approved'
                    ELSE 'Pending'
                END AS ApprovalStatus,
                ApprovalStatus AS ApprovalStatusCode,
                CreateOn AS CreatedOn
            FROM Acc_Proforma_Inv_Main
        """

    @classmethod
    def get_all(
        cls,
        db: Session,
        search: Optional[str] = None,
        approval_status: Optional[str] = None,
        fin_year: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cls.ensure_tables_exist(db)

        query = cls._header_select() + """
            WHERE (Status IS NULL OR Status <> 'Delete')
        """
        params: Dict[str, Any] = {}

        if search:
            query += """
                AND (
                    TransNo LIKE :search
                    OR QuotationNo LIKE :search
                    OR CustomerName LIKE :search
                    OR Remarks LIKE :search
                )
            """
            params["search"] = f"%{search}%"

        if approval_status and approval_status.upper() != "ALL":
            if approval_status.lower() in ("approved", "1"):
                query += """
                    AND (
                        ApprovalStatus = '1'
                        OR LOWER(ApprovalStatus) = 'approved'
                    )
                """
            else:
                query += """
                    AND (
                        ApprovalStatus = '0'
                        OR LOWER(ApprovalStatus) = 'pending'
                        OR ApprovalStatus IS NULL
                        OR ApprovalStatus = ''
                    )
                """

        if fin_year and fin_year.upper() != "ALL":
            fy_dash = fin_year.replace("_", "-").strip()
            fy_under = fin_year.replace("-", "_").strip()
            parts = fy_dash.split("-")
            if len(parts) == 2 and len(parts[0]) == 4 and len(parts[1]) == 4:
                start_d = f"{parts[0]}-04-01"
                end_d = f"{parts[1]}-03-31"
                query += """
                    AND (
                        REPLACE(LTRIM(RTRIM(FinYearVal)), '_', '-') = :fy_dash
                        OR REPLACE(LTRIM(RTRIM(FinYearVal)), '-', '_') = :fy_under
                        OR FinYearCode = :fin_year
                        OR (
                            TRY_CAST(TransDate AS DATE) >= :start_d
                            AND TRY_CAST(TransDate AS DATE) <= :end_d
                        )
                    )
                """
                params["fy_dash"] = fy_dash
                params["fy_under"] = fy_under
                params["fin_year"] = fin_year
                params["start_d"] = start_d
                params["end_d"] = end_d
            else:
                query += """
                    AND (FinYearVal = :fin_year OR FinYearCode = :fin_year)
                """
                params["fin_year"] = fin_year

        query += " ORDER BY CreateOn DESC"

        rows = db.execute(text(query), params).mappings().all()
        invoices = []

        for row in rows:
            invoice = dict(row)
            invoice["Items"] = cls._get_items(
                db,
                str(invoice["TransNo"]),
            )
            invoices.append(invoice)

        return invoices

    @classmethod
    def get_by_no(
        cls,
        db: Session,
        trans_no: str,
    ) -> Dict[str, Any]:
        cls.ensure_tables_exist(db)

        query = cls._header_select() + """
            WHERE TransNo = :trans_no
              AND (Status IS NULL OR Status <> 'Delete')
        """

        row = db.execute(
            text(query),
            {"trans_no": trans_no},
        ).mappings().first()

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Proforma Invoice {trans_no} not found.",
            )

        invoice = dict(row)
        invoice["Items"] = cls._get_items(db, trans_no)
        return invoice

    @staticmethod
    def _generate_trans_no(db: Session) -> str:
        """
        Generate the existing PI-2026-001 style number.
        COUNT-based numbering can collide during concurrent requests.
        Use a transaction-safe sequence for production.
        """
        count = db.execute(
            text("""
                SELECT COUNT(1)
                FROM Acc_Proforma_Inv_Main
                WHERE TransNo LIKE 'PI-2026-%'
            """)
        ).scalar_one()

        return f"PI-2026-{int(count) + 1:03d}"

    @staticmethod
    def _approval_value(value: Optional[str]) -> str:
        return (
            "1"
            if str(value or "").strip().lower() in ("1", "approved")
            else "0"
        )

    @staticmethod
    def _insert_items(
        db: Session,
        payload: Any,
        trans_no: str,
    ) -> None:
        sql = text("""
            INSERT INTO Acc_Proforma_Inv_Sub (
                Ccode, Lcode, FinYearCode, FinYearVal,
                TransNo, TransDate, QuotationNo, QuotationDate,
                CustomerCode, CustomerName, ItemCode, ProductType,
                HSNCode, Qty, Rate, ItemValue, GST, CGST, SGST,
                IGST, NetAmount, Service, Status, UserName, UserCode,
                SysIp, SysName, CreateOn
            )
            VALUES (
                '01', '01', '01', '2026-2027',
                :trans_no, :trans_date, :quo_no, :quo_date,
                :cust_code, :cust_name, :item_code, :prod_type,
                :hsn, :qty, :rate, :item_val, :gst, :cgst, :sgst,
                :igst, :net_amt, :service, :row_status, 'ADMIN',
                'ADMIN', '127.0.0.1', 'API_SERVER', GETDATE()
            )
        """)

        for index, item in enumerate(payload.Items or [], start=1):
            db.execute(sql, {
                "trans_no": trans_no,
                "trans_date": payload.TransDate,
                "quo_no": payload.QuotationNo or "",
                "quo_date": payload.QuotationDate or payload.TransDate,
                "cust_code": payload.CustomerCode or "SUP-1001",
                "cust_name": payload.CustomerName,
                "item_code": item.ItemCode or f"ITM-{index}",
                "prod_type": item.ProductType,
                "hsn": item.HSNCode or "",
                "qty": item.Qty,
                "rate": item.Rate,
                "item_val": item.ItemValue,
                "gst": item.GST,
                "cgst": item.CGST,
                "sgst": item.SGST,
                "igst": item.IGST,
                "net_amt": item.NetAmount,
                "service": item.Service or "Supply & Installation",
                "row_status": "Add",
            })

    @classmethod
    def create(
        cls,
        db: Session,
        payload: ProformaCreate,
    ) -> str:
        try:
            cls.ensure_tables_exist(db)

            trans_no = payload.TransNo or cls._generate_trans_no(db)

            duplicate = db.execute(
                text("""
                    SELECT 1
                    FROM Acc_Proforma_Inv_Main
                    WHERE TransNo = :trans_no
                      AND (Status IS NULL OR Status <> 'Delete')
                """),
                {"trans_no": trans_no},
            ).first()

            if duplicate:
                raise HTTPException(
                    status_code=409,
                    detail=f"Proforma Invoice {trans_no} already exists.",
                )

            db.execute(
                text("""
                    INSERT INTO Acc_Proforma_Inv_Main (
                        Ccode, Lcode, FinYearVal, FinYearCode,
                        TransNo, TransDate, QuotationNo, QuotationDate,
                        CustomerCode, CustomerName, TotalQty,
                        TotalItemAmount, TotalCGSTAmount, TotalSGSTAmount,
                        TotalIGSTAmount, TotalAmount, Remarks, RoundType,
                        RoundOff, NetAmount, ApprovalStatus, Status,
                        UserName, UserCode, SysIp, SysName, CreateOn
                    )
                    VALUES (
                        '01', '01', '2026-2027', '01',
                        :trans_no, :trans_date, :quo_no, :quo_date,
                        :cust_code, :cust_name, :tot_qty,
                        :tot_item_amt, :tot_cgst, :tot_sgst,
                        :tot_igst, :tot_amt, :remarks, :round_type,
                        :round_off, :net_amount, :approval_status, 'Add',
                        'ADMIN', 'ADMIN', '127.0.0.1', 'API_SERVER',
                        GETDATE()
                    )
                """),
                {
                    "trans_no": trans_no,
                    "trans_date": payload.TransDate,
                    "quo_no": payload.QuotationNo or "",
                    "quo_date": payload.QuotationDate or payload.TransDate,
                    "cust_code": payload.CustomerCode or "SUP-1001",
                    "cust_name": payload.CustomerName,
                    "tot_qty": payload.TotalQty,
                    "tot_item_amt": payload.TotalItemAmount,
                    "tot_cgst": payload.TotalCGSTAmount,
                    "tot_sgst": payload.TotalSGSTAmount,
                    "tot_igst": payload.TotalIGSTAmount,
                    "tot_amt": payload.TotalAmount,
                    "remarks": payload.Remarks or "",
                    "round_type": payload.RoundType or "None",
                    "round_off": payload.RoundOff or 0,
                    "net_amount": payload.FinalNetAmount,
                    "approval_status": cls._approval_value(
                        payload.ApprovalStatus
                    ),
                },
            )

            cls._insert_items(db, payload, trans_no)
            db.commit()
            return trans_no

        except Exception:
            db.rollback()
            raise

    @classmethod
    def update(
        cls,
        db: Session,
        trans_no: str,
        payload: ProformaUpdate,
    ) -> None:
        try:
            cls.ensure_tables_exist(db)

            result = db.execute(
                text("""
                    UPDATE Acc_Proforma_Inv_Main
                    SET
                        TransDate = :trans_date,
                        QuotationNo = :quo_no,
                        QuotationDate = :quo_date,
                        CustomerName = :cust_name,
                        TotalQty = :tot_qty,
                        TotalItemAmount = :tot_item_amt,
                        TotalCGSTAmount = :tot_cgst,
                        TotalSGSTAmount = :tot_sgst,
                        TotalIGSTAmount = :tot_igst,
                        TotalAmount = :tot_amt,
                        Remarks = :remarks,
                        RoundType = :round_type,
                        RoundOff = :round_off,
                        NetAmount = :net_amount,
                        ApprovalStatus = :approval_status,
                        Status = 'Edit'
                    WHERE TransNo = :trans_no
                      AND (Status IS NULL OR Status <> 'Delete')
                """),
                {
                    "trans_no": trans_no,
                    "trans_date": payload.TransDate,
                    "quo_no": payload.QuotationNo or "",
                    "quo_date": payload.QuotationDate or payload.TransDate,
                    "cust_name": payload.CustomerName,
                    "tot_qty": payload.TotalQty,
                    "tot_item_amt": payload.TotalItemAmount,
                    "tot_cgst": payload.TotalCGSTAmount,
                    "tot_sgst": payload.TotalSGSTAmount,
                    "tot_igst": payload.TotalIGSTAmount,
                    "tot_amt": payload.TotalAmount,
                    "remarks": payload.Remarks or "",
                    "round_type": payload.RoundType or "None",
                    "round_off": payload.RoundOff or 0,
                    "net_amount": payload.FinalNetAmount,
                    "approval_status": cls._approval_value(
                        payload.ApprovalStatus
                    ),
                },
            )

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Proforma Invoice {trans_no} not found.",
                )

            # Preserve the original behavior: replace all existing items.
            db.execute(
                text("""
                    DELETE FROM Acc_Proforma_Inv_Sub
                    WHERE TransNo = :trans_no
                """),
                {"trans_no": trans_no},
            )

            cls._insert_items(db, payload, trans_no)
            db.commit()

        except Exception:
            db.rollback()
            raise

    @classmethod
    def update_approval(
        cls,
        db: Session,
        trans_no: str,
        payload: ProformaApprovalUpdate,
    ) -> str:
        try:
            cls.ensure_tables_exist(db)

            approval_status = cls._approval_value(payload.ApprovalStatus)

            result = db.execute(
                text("""
                    UPDATE Acc_Proforma_Inv_Main
                    SET
                        ApprovalStatus = :approval_status,
                        ApprovedBy = :approved_by,
                        ApprovedOn = CASE
                            WHEN :approval_status = '1' THEN GETDATE()
                            ELSE NULL
                        END
                    WHERE TransNo = :trans_no
                      AND (Status IS NULL OR Status <> 'Delete')
                """),
                {
                    "trans_no": trans_no,
                    "approval_status": approval_status,
                    "approved_by": payload.ApprovedBy or "ADMIN",
                },
            )

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Proforma Invoice {trans_no} not found.",
                )

            db.commit()
            return approval_status

        except Exception:
            db.rollback()
            raise

    @classmethod
    def delete(
        cls,
        db: Session,
        trans_no: str,
    ) -> None:
        """Soft-delete an invoice and its line items."""
        try:
            cls.ensure_tables_exist(db)

            result = db.execute(
                text("""
                    UPDATE Acc_Proforma_Inv_Main
                    SET Status = 'Delete'
                    WHERE TransNo = :trans_no
                      AND (Status IS NULL OR Status <> 'Delete')
                """),
                {"trans_no": trans_no},
            )

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Proforma Invoice {trans_no} not found.",
                )

            db.execute(
                text("""
                    UPDATE Acc_Proforma_Inv_Sub
                    SET Status = 'Delete'
                    WHERE TransNo = :trans_no
                """),
                {"trans_no": trans_no},
            )

            db.commit()

        except Exception:
            db.rollback()
            raise
