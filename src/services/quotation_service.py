from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi import HTTPException

from src.schemas.transaction import (
    QuotationCreate,
    QuotationUpdate,
    QuotationApprovalUpdate,
)


class QuotationService:

    # =========================================================
    # TABLE INITIALIZATION
    # =========================================================

    @staticmethod
    def ensure_tables_exist(db: Session) -> None:

        table_init_sql = """
        IF NOT EXISTS (
            SELECT *
            FROM sysobjects
            WHERE name = 'Acc_Quotation_Main'
              AND xtype = 'U'
        )
        BEGIN
            CREATE TABLE Acc_Quotation_Main (
                Ccode VARCHAR(10) DEFAULT '01',
                Lcode VARCHAR(10) DEFAULT '01',
                FinYearVal VARCHAR(20) DEFAULT '2026-2027',
                FinYearCode VARCHAR(10) DEFAULT '01',
                TransNo VARCHAR(50) PRIMARY KEY,
                TransDate VARCHAR(30),
                SuppCode VARCHAR(50),
                CustomerName NVARCHAR(255),
                Product VARCHAR(50),
                Remarks NVARCHAR(500),
                Purpose NVARCHAR(500),
                terms_conditions NVARCHAR(MAX),
                TotQty NUMERIC(18,2) DEFAULT 0,
                TotItemAmt NUMERIC(18,2) DEFAULT 0,
                TotCGSTAmt NUMERIC(18,2) DEFAULT 0,
                TotSGSTAmt NUMERIC(18,2) DEFAULT 0,
                TotIGSTAmt NUMERIC(18,2) DEFAULT 0,
                TotLineAmt NUMERIC(18,2) DEFAULT 0,
                RoundOffType VARCHAR(20) DEFAULT 'None',
                RoundOffVal NUMERIC(18,2) DEFAULT 0,
                NetAmount NUMERIC(18,2) DEFAULT 0,
                ApprovalStatus VARCHAR(50) DEFAULT 'Pending',
                ApprovedBy VARCHAR(50),
                ApprovedOn DATETIME,
                Status VARCHAR(20) DEFAULT 'Add',
                UserName VARCHAR(50) DEFAULT 'ADMIN',
                UserCode VARCHAR(50) DEFAULT 'ADMIN',
                SysIp VARCHAR(50) DEFAULT '127.0.0.1',
                SysName VARCHAR(50) DEFAULT 'API_SERVER',
                CreatedOn DATETIME DEFAULT GETDATE()
            );
        END;

        IF NOT EXISTS (
            SELECT *
            FROM sysobjects
            WHERE name = 'Acc_Quotation_Sub'
              AND xtype = 'U'
        )
        BEGIN
            CREATE TABLE Acc_Quotation_Sub (
                Ccode VARCHAR(10) DEFAULT '01',
                Lcode VARCHAR(10) DEFAULT '01',
                FinYearCode VARCHAR(10) DEFAULT '01',
                FinYearVal VARCHAR(20) DEFAULT '2026-2027',
                TransNo VARCHAR(50),
                TransDate VARCHAR(30),
                order_id VARCHAR(10) DEFAULT '1',
                ItemCode VARCHAR(50),
                ProductType NVARCHAR(255),
                Prod_highlight NVARCHAR(500),
                UOM VARCHAR(20),
                HSNCode VARCHAR(30),
                Rate NUMERIC(18,2) DEFAULT 0,
                Qty NUMERIC(18,2) DEFAULT 0,
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
                SysIP VARCHAR(50) DEFAULT '127.0.0.1',
                SysName VARCHAR(50) DEFAULT 'API_SERVER',
                CreateOn DATETIME DEFAULT GETDATE()
            );
        END;
        """

        db.execute(text(table_init_sql))
        db.commit()

    # =========================================================
    # GET ALL QUOTATIONS
    # =========================================================

    @staticmethod
    def get_quotations(
        db: Session,
        search: str | None = None,
        status: str | None = None,
        fin_year: str | None = None,
    ):

        QuotationService.ensure_tables_exist(db)

        query = """
            SELECT
                TransNo,
                FinYearVal,
                FinYearCode,
                CONVERT(VARCHAR(10), TransDate, 120) AS TransDate,
                Product AS ProdType,
                SuppCode AS CustomerCode,
                CustomerName,
                Remarks AS Narration,
                Purpose,
                terms_conditions AS TermsAndConditions,
                TotQty AS TotalQty,
                TotItemAmt AS TotalItemAmount,
                TotCGSTAmt AS TotalCGSTAmount,
                TotSGSTAmt AS TotalSGSTAmount,
                TotIGSTAmt AS TotalIGSTAmount,
                TotLineAmt AS TotalAmount,
                RoundOffType AS RoundType,
                RoundOffVal AS RoundOff,
                NetAmount AS FinalNetAmount,
                ApprovalStatus
            FROM Acc_Quotation_Main
            WHERE Status <> 'Delete'
        """

        params = {}

        if search:
            query += """
                AND (
                    TransNo LIKE :search
                    OR CustomerName LIKE :search
                    OR Remarks LIKE :search
                )
            """
            params["search"] = f"%{search}%"

        if status and status != "ALL":
            query += """
                AND ApprovalStatus = :status
            """
            params["status"] = status

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

        results = (
            db.execute(
                text(query),
                params,
            )
            .mappings()
            .all()
        )

        quotations = []

        for row in results:

            quotation = dict(row)

            items_query = """
                SELECT
                    order_id,
                    ItemCode,
                    ProductType,
                    Prod_highlight,
                    HSNCode,
                    UOM,
                    Rate,
                    Qty,
                    ItemValue,
                    GST,
                    CGST,
                    SGST,
                    IGST,
                    NetAmount,
                    Service
                FROM Acc_Quotation_Sub
                WHERE TransNo = :trans_no
                  AND Status <> 'Delete'
                ORDER BY CAST(order_id AS INT) ASC
            """

            items = (
                db.execute(
                    text(items_query),
                    {
                        "trans_no": quotation["TransNo"]
                    },
                )
                .mappings()
                .all()
            )

            quotation["Items"] = [
                dict(item)
                for item in items
            ]

            quotations.append(quotation)

        return quotations

    # =========================================================
    # GET SINGLE QUOTATION
    # =========================================================

    @staticmethod
    def get_quotation_by_no(
        db: Session,
        trans_no: str,
    ):

        QuotationService.ensure_tables_exist(db)

        header_query = """
            SELECT
                TransNo,
                CONVERT(VARCHAR(10), TransDate, 120) AS TransDate,
                Product AS ProdType,
                SuppCode AS CustomerCode,
                CustomerName,
                Remarks AS Narration,
                Purpose,
                terms_conditions AS TermsAndConditions,
                TotQty AS TotalQty,
                TotItemAmt AS TotalItemAmount,
                TotCGSTAmt AS TotalCGSTAmount,
                TotSGSTAmt AS TotalSGSTAmount,
                TotIGSTAmt AS TotalIGSTAmount,
                TotLineAmt AS TotalAmount,
                RoundOffType AS RoundType,
                RoundOffVal AS RoundOff,
                NetAmount AS FinalNetAmount,
                ApprovalStatus
            FROM Acc_Quotation_Main
            WHERE TransNo = :trans_no
              AND Status <> 'Delete'
        """

        header = (
            db.execute(
                text(header_query),
                {"trans_no": trans_no},
            )
            .mappings()
            .first()
        )

        if not header:
            raise HTTPException(
                status_code=404,
                detail=f"Quotation {trans_no} not found",
            )

        items_query = """
            SELECT
                order_id,
                ItemCode,
                ProductType,
                Prod_highlight,
                HSNCode,
                UOM,
                Rate,
                Qty,
                ItemValue,
                GST,
                CGST,
                SGST,
                IGST,
                NetAmount,
                Service
            FROM Acc_Quotation_Sub
            WHERE TransNo = :trans_no
              AND Status <> 'Delete'
            ORDER BY CAST(order_id AS INT) ASC
        """

        items = (
            db.execute(
                text(items_query),
                {"trans_no": trans_no},
            )
            .mappings()
            .all()
        )

        data = dict(header)

        data["Items"] = [
            dict(item)
            for item in items
        ]

        return data

    # =========================================================
    # CREATE QUOTATION
    # =========================================================

    @staticmethod
    def create_quotation(
        db: Session,
        payload: QuotationCreate,
    ):

        QuotationService.ensure_tables_exist(db)

        trans_no = payload.TransNo

        if not trans_no:

            count = (
                db.execute(
                    text(
                        """
                        SELECT COUNT(1)
                        FROM Acc_Quotation_Main
                        """
                    )
                ).scalar()
                or 0
            )

            trans_no = (
                f"QUO-2026-{str(count + 1).zfill(3)}"
            )

        duplicate = db.execute(
            text(
                """
                SELECT TransNo
                FROM Acc_Quotation_Main
                WHERE TransNo = :trans_no
                  AND Status <> 'Delete'
                """
            ),
            {
                "trans_no": trans_no
            },
        ).fetchone()

        if duplicate:
            raise HTTPException(
                status_code=400,
                detail=f"Quotation {trans_no} already exists.",
            )

        try:

            # ---------------------------------------------
            # Header
            # ---------------------------------------------

            insert_header = """
                INSERT INTO Acc_Quotation_Main (
                    Ccode,
                    Lcode,
                    FinYearVal,
                    FinYearCode,
                    TransNo,
                    TransDate,
                    SuppCode,
                    CustomerName,
                    Product,
                    Remarks,
                    Purpose,
                    terms_conditions,
                    TotQty,
                    TotItemAmt,
                    TotCGSTAmt,
                    TotSGSTAmt,
                    TotIGSTAmt,
                    TotLineAmt,
                    RoundOffType,
                    RoundOffVal,
                    NetAmount,
                    ApprovalStatus,
                    Status,
                    UserName,
                    UserCode,
                    SysIp,
                    SysName
                )
                VALUES (
                    '01',
                    '01',
                    '2026-2027',
                    '01',
                    :trans_no,
                    :trans_date,
                    :cust_code,
                    :cust_name,
                    :prod_type,
                    :narration,
                    :purpose,
                    :terms,
                    :tot_qty,
                    :tot_item_amt,
                    :tot_cgst,
                    :tot_sgst,
                    :tot_igst,
                    :tot_amt,
                    :round_type,
                    :round_off,
                    :net_amount,
                    :approval_status,
                    'Add',
                    'ADMIN',
                    'ADMIN',
                    '127.0.0.1',
                    'API_SERVER'
                )
            """

            db.execute(
                text(insert_header),
                {
                    "trans_no": trans_no,
                    "trans_date": payload.TransDate,
                    "cust_code": (
                        payload.CustomerCode
                        or "SUP-1001"
                    ),
                    "cust_name": payload.CustomerName,
                    "prod_type": (
                        payload.ProdType or "1"
                    ),
                    "narration": (
                        payload.Narration or ""
                    ),
                    "purpose": (
                        payload.Purpose or ""
                    ),
                    "terms": (
                        payload.TermsAndConditions
                        or ""
                    ),
                    "tot_qty": payload.TotalQty,
                    "tot_item_amt": (
                        payload.TotalItemAmount
                    ),
                    "tot_cgst": (
                        payload.TotalCGSTAmount
                    ),
                    "tot_sgst": (
                        payload.TotalSGSTAmount
                    ),
                    "tot_igst": (
                        payload.TotalIGSTAmount
                    ),
                    "tot_amt": payload.TotalAmount,
                    "round_type": (
                        payload.RoundType or "None"
                    ),
                    "round_off": (
                        payload.RoundOff or 0
                    ),
                    "net_amount": (
                        payload.FinalNetAmount
                    ),
                    "approval_status": (
                        "1"
                        if str(
                            payload.ApprovalStatus
                        ).strip()
                        in ["1", "Approved"]
                        else "0"
                    ),
                },
            )

            # ---------------------------------------------
            # Detail Items
            # ---------------------------------------------

            for index, item in enumerate(
                payload.Items,
                start=1,
            ):

                insert_item = """
                    INSERT INTO Acc_Quotation_Sub (
                        Ccode,
                        Lcode,
                        FinYearCode,
                        FinYearVal,
                        TransNo,
                        TransDate,
                        order_id,
                        ItemCode,
                        ProductType,
                        Prod_highlight,
                        HSNCode,
                        UOM,
                        Rate,
                        Qty,
                        ItemValue,
                        GST,
                        CGST,
                        SGST,
                        IGST,
                        NetAmount,
                        Service,
                        Status,
                        UserName,
                        UserCode,
                        SysIP,
                        SysName
                    )
                    VALUES (
                        '01',
                        '01',
                        '01',
                        '2026-2027',
                        :trans_no,
                        :trans_date,
                        :order_id,
                        :item_code,
                        :prod_type,
                        :highlight,
                        :hsn,
                        :uom,
                        :rate,
                        :qty,
                        :item_val,
                        :gst,
                        :cgst,
                        :sgst,
                        :igst,
                        :net_amt,
                        :service,
                        'Add',
                        'ADMIN',
                        'ADMIN',
                        '127.0.0.1',
                        'API_SERVER'
                    )
                """

                db.execute(
                    text(insert_item),
                    {
                        "trans_no": trans_no,
                        "trans_date": payload.TransDate,
                        "order_id": str(
                            item.order_id or index
                        ),
                        "item_code": (
                            item.ItemCode
                            or f"ITM-{index}"
                        ),
                        "prod_type": (
                            item.ProductType
                        ),
                        "highlight": (
                            item.Prod_highlight
                            or ""
                        ),
                        "hsn": (
                            item.HSNCode or ""
                        ),
                        "uom": (
                            item.UOM or "Pcs"
                        ),
                        "rate": item.Rate,
                        "qty": item.Qty,
                        "item_val": item.ItemValue,
                        "gst": item.GST,
                        "cgst": item.CGST,
                        "sgst": item.SGST,
                        "igst": item.IGST,
                        "net_amt": item.NetAmount,
                        "service": (
                            item.Service
                            or "Standard Supply"
                        ),
                    },
                )

            db.commit()

            return trans_no

        except Exception as exc:

            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=str(exc),
            )

    # =========================================================
    # UPDATE QUOTATION
    # =========================================================

    @staticmethod
    def update_quotation(
        db: Session,
        trans_no: str,
        payload: QuotationUpdate,
    ):

        QuotationService.ensure_tables_exist(db)

        try:

            update_header = """
                UPDATE Acc_Quotation_Main
                SET
                    TransDate = :trans_date,
                    CustomerName = :cust_name,
                    Product = :prod_type,
                    Remarks = :narration,
                    Purpose = :purpose,
                    terms_conditions = :terms,
                    TotQty = :tot_qty,
                    TotItemAmt = :tot_item_amt,
                    TotCGSTAmt = :tot_cgst,
                    TotSGSTAmt = :tot_sgst,
                    TotIGSTAmt = :tot_igst,
                    TotLineAmt = :tot_amt,
                    RoundOffType = :round_type,
                    RoundOffVal = :round_off,
                    NetAmount = :net_amount,
                    ApprovalStatus = :approval_status,
                    Status = 'Edit'
                WHERE TransNo = :trans_no
                  AND Status <> 'Delete'
            """

            result = db.execute(
                text(update_header),
                {
                    "trans_no": trans_no,
                    "trans_date": payload.TransDate,
                    "cust_name": payload.CustomerName,
                    "prod_type": (
                        payload.ProdType or "1"
                    ),
                    "narration": (
                        payload.Narration or ""
                    ),
                    "purpose": (
                        payload.Purpose or ""
                    ),
                    "terms": (
                        payload.TermsAndConditions
                        or ""
                    ),
                    "tot_qty": payload.TotalQty,
                    "tot_item_amt": (
                        payload.TotalItemAmount
                    ),
                    "tot_cgst": (
                        payload.TotalCGSTAmount
                    ),
                    "tot_sgst": (
                        payload.TotalSGSTAmount
                    ),
                    "tot_igst": (
                        payload.TotalIGSTAmount
                    ),
                    "tot_amt": payload.TotalAmount,
                    "round_type": (
                        payload.RoundType or "None"
                    ),
                    "round_off": (
                        payload.RoundOff or 0
                    ),
                    "net_amount": (
                        payload.FinalNetAmount
                    ),
                    "approval_status": (
                        "1"
                        if str(
                            payload.ApprovalStatus
                        ).strip()
                        in ["1", "Approved"]
                        else "0"
                    ),
                },
            )

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Quotation {trans_no} not found",
                )

            # ---------------------------------------------
            # Replace items
            # ---------------------------------------------

            db.execute(
                text(
                    """
                    DELETE FROM Acc_Quotation_Sub
                    WHERE TransNo = :trans_no
                    """
                ),
                {
                    "trans_no": trans_no
                },
            )

            for index, item in enumerate(
                payload.Items,
                start=1,
            ):

                insert_item = """
                    INSERT INTO Acc_Quotation_Sub (
                        Ccode,
                        Lcode,
                        FinYearCode,
                        FinYearVal,
                        TransNo,
                        TransDate,
                        order_id,
                        ItemCode,
                        ProductType,
                        Prod_highlight,
                        HSNCode,
                        UOM,
                        Rate,
                        Qty,
                        ItemValue,
                        GST,
                        CGST,
                        SGST,
                        IGST,
                        NetAmount,
                        Service,
                        Status,
                        UserName,
                        UserCode,
                        SysIP,
                        SysName
                    )
                    VALUES (
                        '01',
                        '01',
                        '01',
                        '2026-2027',
                        :trans_no,
                        :trans_date,
                        :order_id,
                        :item_code,
                        :prod_type,
                        :highlight,
                        :hsn,
                        :uom,
                        :rate,
                        :qty,
                        :item_val,
                        :gst,
                        :cgst,
                        :sgst,
                        :igst,
                        :net_amt,
                        :service,
                        'Edit',
                        'ADMIN',
                        'ADMIN',
                        '127.0.0.1',
                        'API_SERVER'
                    )
                """

                db.execute(
                    text(insert_item),
                    {
                        "trans_no": trans_no,
                        "trans_date": payload.TransDate,
                        "order_id": str(
                            item.order_id or index
                        ),
                        "item_code": (
                            item.ItemCode
                            or f"ITM-{index}"
                        ),
                        "prod_type": item.ProductType,
                        "highlight": (
                            item.Prod_highlight
                            or ""
                        ),
                        "hsn": (
                            item.HSNCode or ""
                        ),
                        "uom": (
                            item.UOM or "Pcs"
                        ),
                        "rate": item.Rate,
                        "qty": item.Qty,
                        "item_val": item.ItemValue,
                        "gst": item.GST,
                        "cgst": item.CGST,
                        "sgst": item.SGST,
                        "igst": item.IGST,
                        "net_amt": item.NetAmount,
                        "service": (
                            item.Service
                            or "Standard Supply"
                        ),
                    },
                )

            db.commit()

        except HTTPException:
            db.rollback()
            raise

        except Exception as exc:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=str(exc),
            )

    # =========================================================
    # APPROVAL
    # =========================================================

    @staticmethod
    def update_quotation_approval(
        db: Session,
        trans_no: str,
        payload: QuotationApprovalUpdate,
    ):

        QuotationService.ensure_tables_exist(db)

        status_value = (
            "1"
            if str(
                payload.ApprovalStatus
            ).strip()
            in ["1", "Approved"]
            else "0"
        )

        result = db.execute(
            text(
                """
                UPDATE Acc_Quotation_Main
                SET
                    ApprovalStatus = :status,
                    ApprovedBy = :approved_by,
                    ApprovedOn =
                        CASE
                            WHEN :status = '1'
                            THEN GETDATE()
                            ELSE NULL
                        END
                WHERE TransNo = :trans_no
                  AND Status <> 'Delete'
                """
            ),
            {
                "trans_no": trans_no,
                "status": status_value,
                "approved_by": (
                    payload.ApprovedBy
                    or "ADMIN"
                ),
            },
        )

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Quotation {trans_no} not found",
            )

        db.commit()

        return status_value

    # =========================================================
    # DELETE
    # =========================================================

    @staticmethod
    def delete_quotation(
        db: Session,
        trans_no: str,
    ):

        QuotationService.ensure_tables_exist(db)

        try:

            result = db.execute(
                text(
                    """
                    UPDATE Acc_Quotation_Main
                    SET Status = 'Delete'
                    WHERE TransNo = :trans_no
                    """
                ),
                {
                    "trans_no": trans_no
                },
            )

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Quotation {trans_no} not found",
                )

            db.execute(
                text(
                    """
                    UPDATE Acc_Quotation_Sub
                    SET Status = 'Delete'
                    WHERE TransNo = :trans_no
                    """
                ),
                {
                    "trans_no": trans_no
                },
            )

            db.commit()

        except HTTPException:
            db.rollback()
            raise

        except Exception as exc:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=str(exc),
            )