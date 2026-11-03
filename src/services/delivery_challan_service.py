
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.schemas.transaction import (
    DeliveryChallanCreate,
    DeliveryChallanUpdate,
)


class DeliveryChallanService:
    """Database operations and business logic for Delivery Challans."""

    HEADER_COLUMNS = """
        Ccode,
        Lcode,
        Deliveryno,
        Deliverydate,
        Returntype,
        TransType,
        Suppliername,
        SupplierInvoice,
        Deliverymode,
        Supplier_ref_no,
        Supplier_ref_date,
        purpose,
        TotalAmt,
        GSTName,
        SGST_Per,
        SGSTAmt,
        CGST_Per,
        CGSTAmt,
        IGST_Per,
        IGSTAmt,
        FinalInvoice
    """

    ITEM_COLUMNS = """
        Item,
        HSN,
        UOM,
        Qty,
        Rate,
        InvoiceTotal
    """

    @staticmethod
    def _get_items(
        db: Session,
        delivery_no: str,
    ) -> List[Dict[str, Any]]:
        query = text("""
            SELECT Item, HSN, UOM, Qty, Rate, InvoiceTotal
            FROM Delivery_sub
            WHERE Deliveryno = :delivery_no
            ORDER BY Item
        """)

        result = db.execute(
            query,
            {"delivery_no": delivery_no},
        ).mappings().all()

        return [dict(row) for row in result]

    @classmethod
    def get_all(
        cls,
        db: Session,
        search: Optional[str] = None,
        return_type: Optional[str] = None,
        fin_year: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conditions = []
        params: Dict[str, Any] = {}

        if search:
            conditions.append("""
                (
                    Deliveryno LIKE :search
                    OR Suppliername LIKE :search
                    OR purpose LIKE :search
                    OR Supplier_ref_no LIKE :search
                )
            """)
            params["search"] = f"%{search}%"

        if return_type:
            conditions.append("Returntype = :return_type")
            params["return_type"] = return_type

        if fin_year and fin_year.upper() != "ALL":


            parts = fin_year.replace('-', '_').split('_')


            if len(parts) == 2 and len(parts[0]) == 4 and len(parts[1]) == 4:


                start_d = f"{parts[0]}-04-01"


                end_d = f"{parts[1]}-03-31"


                short_fy = f"{parts[0][2:]}-{parts[1][2:]}"


                conditions.append("""(


                    (TRY_CAST(Deliverydate AS DATE) >= :start_d AND TRY_CAST(Deliverydate AS DATE) <= :end_d)


                    OR Deliveryno LIKE :short_fy


                )""")


                params["start_d"] = start_d


                params["end_d"] = end_d


                params["short_fy"] = f"%{short_fy}%"


            else:


                conditions.append("Deliveryno LIKE :fy")


                params["fy"] = f"%{fin_year}%"

        where_clause = (
            "WHERE " + " AND ".join(conditions)
            if conditions
            else ""
        )

        query = text(f"""
            SELECT {cls.HEADER_COLUMNS}
            FROM Delivery_main
            {where_clause}
            ORDER BY Deliverydate DESC, Deliveryno DESC
        """)

        rows = db.execute(query, params).mappings().all()
        delivery_challans = []

        for row in rows:
            challan = dict(row)
            challan["Items"] = cls._get_items(
                db,
                str(challan["Deliveryno"]),
            )
            delivery_challans.append(challan)

        return delivery_challans

    @classmethod
    def get_by_no(
        cls,
        db: Session,
        delivery_no: str,
    ) -> Dict[str, Any]:
        query = text(f"""
            SELECT {cls.HEADER_COLUMNS}
            FROM Delivery_main
            WHERE Deliveryno = :delivery_no
        """)

        row = db.execute(
            query,
            {"delivery_no": delivery_no},
        ).mappings().first()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Delivery Challan not found.",
            )

        challan = dict(row)
        challan["Items"] = cls._get_items(db, delivery_no)

        return challan

    @staticmethod
    def _generate_delivery_no(db: Session) -> str:
        """
        Preserves the existing DC-2026-001 style.
        For production, replace COUNT-based numbering with a
        transaction-safe sequence or numbering table.
        """
        result = db.execute(text("""
            SELECT COUNT(1)
            FROM Delivery_main
            WHERE Deliveryno LIKE 'DC-2026-%'
        """)).scalar_one()

        return f"DC-2026-{int(result) + 1:03d}"

    @staticmethod
    def _insert_header(
        db: Session,
        delivery_no: str,
        payload: DeliveryChallanCreate,
    ) -> None:
        query = text("""
            INSERT INTO Delivery_main (
                Ccode, Lcode, Deliveryno, Deliverydate,
                Returntype, TransType, Suppliername,
                SupplierInvoice, Deliverymode, Supplier_ref_no,
                Supplier_ref_date, purpose, TotalAmt, GSTName,
                SGST_Per, SGSTAmt, CGST_Per, CGSTAmt,
                IGST_Per, IGSTAmt, FinalInvoice
            )
            VALUES (
                :Ccode, :Lcode, :Deliveryno, :Deliverydate,
                :Returntype, :TransType, :Suppliername,
                :SupplierInvoice, :Deliverymode, :Supplier_ref_no,
                :Supplier_ref_date, :purpose, :TotalAmt, :GSTName,
                :SGST_Per, :SGSTAmt, :CGST_Per, :CGSTAmt,
                :IGST_Per, :IGSTAmt, :FinalInvoice
            )
        """)

        db.execute(query, {
            "Ccode": "01",
            "Lcode": "01",
            "Deliveryno": delivery_no,
            "Deliverydate": payload.Deliverydate,
            "Returntype": payload.Returntype or "",
            "TransType": payload.TransType or "",
            "Suppliername": payload.Suppliername or "",
            "SupplierInvoice": payload.SupplierInvoice or "",
            "Deliverymode": payload.Deliverymode or "",
            "Supplier_ref_no": payload.Supplier_ref_no or "",
            "Supplier_ref_date": payload.Supplier_ref_date,
            "purpose": payload.purpose or "",
            "TotalAmt": payload.TotalAmt or 0,
            "GSTName": payload.GSTName or "",
            "SGST_Per": payload.SGST_Per or 0,
            "SGSTAmt": payload.SGSTAmt or 0,
            "CGST_Per": payload.CGST_Per or 0,
            "CGSTAmt": payload.CGSTAmt or 0,
            "IGST_Per": payload.IGST_Per or 0,
            "IGSTAmt": payload.IGSTAmt or 0,
            "FinalInvoice": payload.FinalInvoice or 0,
        })

    @staticmethod
    def _insert_items(
        db: Session,
        delivery_no: str,
        items: list,
    ) -> None:
        if not items:
            return

        query = text("""
            INSERT INTO Delivery_sub (
                Ccode, Lcode, Deliveryno,
                Item, HSN, UOM, Qty, Rate, InvoiceTotal
            )
            VALUES (
                :Ccode, :Lcode, :Deliveryno,
                :Item, :HSN, :UOM, :Qty, :Rate, :InvoiceTotal
            )
        """)

        for item in items:
            db.execute(query, {
                "Ccode": "01",
                "Lcode": "01",
                "Deliveryno": delivery_no,
                "Item": item.Item,
                "HSN": item.HSN or "",
                "UOM": item.UOM or "",
                "Qty": item.Qty or 0,
                "Rate": item.Rate or 0,
                "InvoiceTotal": item.InvoiceTotal or 0,
            })

    @classmethod
    def create(
        cls,
        db: Session,
        payload: DeliveryChallanCreate,
    ) -> str:
        try:
            delivery_no = payload.Deliveryno or cls._generate_delivery_no(db)

            exists = db.execute(
                text("""
                    SELECT 1
                    FROM Delivery_main
                    WHERE Deliveryno = :delivery_no
                """),
                {"delivery_no": delivery_no},
            ).first()

            if exists:
                raise HTTPException(
                    status_code=409,
                    detail="Delivery Challan number already exists.",
                )

            cls._insert_header(db, delivery_no, payload)
            cls._insert_items(
                db,
                delivery_no,
                payload.Items or [],
            )

            db.commit()
            return delivery_no

        except Exception:
            db.rollback()
            raise

    @classmethod
    def update(
        cls,
        db: Session,
        delivery_no: str,
        payload: DeliveryChallanUpdate,
    ) -> None:
        try:
            update_query = text("""
                UPDATE Delivery_main
                SET
                    Deliverydate = :Deliverydate,
                    Returntype = :Returntype,
                    TransType = :TransType,
                    Suppliername = :Suppliername,
                    SupplierInvoice = :SupplierInvoice,
                    Deliverymode = :Deliverymode,
                    Supplier_ref_no = :Supplier_ref_no,
                    Supplier_ref_date = :Supplier_ref_date,
                    purpose = :purpose,
                    TotalAmt = :TotalAmt,
                    GSTName = :GSTName,
                    SGST_Per = :SGST_Per,
                    SGSTAmt = :SGSTAmt,
                    CGST_Per = :CGST_Per,
                    CGSTAmt = :CGSTAmt,
                    IGST_Per = :IGST_Per,
                    IGSTAmt = :IGSTAmt,
                    FinalInvoice = :FinalInvoice
                WHERE Deliveryno = :delivery_no
            """)

            result = db.execute(update_query, {
                "Deliverydate": payload.Deliverydate,
                "Returntype": payload.Returntype or "",
                "TransType": payload.TransType or "",
                "Suppliername": payload.Suppliername or "",
                "SupplierInvoice": payload.SupplierInvoice or "",
                "Deliverymode": payload.Deliverymode or "",
                "Supplier_ref_no": payload.Supplier_ref_no or "",
                "Supplier_ref_date": payload.Supplier_ref_date,
                "purpose": payload.purpose or "",
                "TotalAmt": payload.TotalAmt or 0,
                "GSTName": payload.GSTName or "",
                "SGST_Per": payload.SGST_Per or 0,
                "SGSTAmt": payload.SGSTAmt or 0,
                "CGST_Per": payload.CGST_Per or 0,
                "CGSTAmt": payload.CGSTAmt or 0,
                "IGST_Per": payload.IGST_Per or 0,
                "IGSTAmt": payload.IGSTAmt or 0,
                "FinalInvoice": payload.FinalInvoice or 0,
                "delivery_no": delivery_no,
            })

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Delivery Challan not found.",
                )

            # Replace the existing item list with the submitted list.
            db.execute(
                text("""
                    DELETE FROM Delivery_sub
                    WHERE Deliveryno = :delivery_no
                """),
                {"delivery_no": delivery_no},
            )

            cls._insert_items(
                db,
                delivery_no,
                payload.Items or [],
            )

            db.commit()

        except Exception:
            db.rollback()
            raise

    @classmethod
    def delete(
        cls,
        db: Session,
        delivery_no: str,
    ) -> None:
        try:
            exists = db.execute(
                text("""
                    SELECT 1
                    FROM Delivery_main
                    WHERE Deliveryno = :delivery_no
                """),
                {"delivery_no": delivery_no},
            ).first()

            if not exists:
                raise HTTPException(
                    status_code=404,
                    detail="Delivery Challan not found.",
                )

            # Delete child records before the header.
            db.execute(
                text("""
                    DELETE FROM Delivery_sub
                    WHERE Deliveryno = :delivery_no
                """),
                {"delivery_no": delivery_no},
            )

            db.execute(
                text("""
                    DELETE FROM Delivery_main
                    WHERE Deliveryno = :delivery_no
                """),
                {"delivery_no": delivery_no},
            )

            db.commit()

        except Exception:
            db.rollback()
            raise
