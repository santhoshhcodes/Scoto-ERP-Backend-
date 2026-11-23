from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional, Dict, Any, List

from src.helpers.pagination import paginate_raw_sql
from src.helpers.sorting import resolve_raw_sort
from src.schemas.transaction import (
    QuotationCreate,
    QuotationUpdate,
    QuotationRevise,
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
                Ccode VARCHAR(10) DEFAULT 'SCT',
                Lcode VARCHAR(10) DEFAULT 'UNIT I',
                FinYearVal VARCHAR(20) DEFAULT '2026-2027',
                FinYearCode VARCHAR(10) DEFAULT '01',
                TransNo VARCHAR(50) PRIMARY KEY,
                BaseTransNo VARCHAR(50) NULL,
                RevNo INT DEFAULT 0,
                RevLabel VARCHAR(10) DEFAULT 'ORIGINAL',
                IsActiveRevision BIT DEFAULT 1,
                IsLocked BIT DEFAULT 0,
                RevReason NVARCHAR(500) NULL,
                ParentTransNo VARCHAR(50) NULL,
                SupersededOn DATETIME NULL,
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
                Ccode VARCHAR(10) DEFAULT 'SCT',
                Lcode VARCHAR(10) DEFAULT 'UNIT I',
                FinYearCode VARCHAR(10) DEFAULT '01',
                FinYearVal VARCHAR(20) DEFAULT '2026-2027',
                TransNo VARCHAR(50),
                BaseTransNo VARCHAR(50) NULL,
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

        -- Safe idempotent column migrations for revisions
        IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'BaseTransNo') IS NULL
            ALTER TABLE dbo.Acc_Quotation_Main ADD [BaseTransNo] VARCHAR(50) NULL;
        IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'RevNo') IS NULL
            ALTER TABLE dbo.Acc_Quotation_Main ADD [RevNo] INT NOT NULL DEFAULT 0;
        IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'RevLabel') IS NULL
            ALTER TABLE dbo.Acc_Quotation_Main ADD [RevLabel] VARCHAR(10) NOT NULL DEFAULT 'ORIGINAL';
        IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'IsActiveRevision') IS NULL
            ALTER TABLE dbo.Acc_Quotation_Main ADD [IsActiveRevision] BIT NOT NULL DEFAULT 1;
        IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'IsLocked') IS NULL
            ALTER TABLE dbo.Acc_Quotation_Main ADD [IsLocked] BIT NOT NULL DEFAULT 0;
        IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'RevReason') IS NULL
            ALTER TABLE dbo.Acc_Quotation_Main ADD [RevReason] NVARCHAR(500) NULL;
        IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'ParentTransNo') IS NULL
            ALTER TABLE dbo.Acc_Quotation_Main ADD [ParentTransNo] VARCHAR(50) NULL;
        IF COL_LENGTH(N'dbo.Acc_Quotation_Main', N'SupersededOn') IS NULL
            ALTER TABLE dbo.Acc_Quotation_Main ADD [SupersededOn] DATETIME NULL;
        IF COL_LENGTH(N'dbo.Acc_Quotation_Sub', N'BaseTransNo') IS NULL
            ALTER TABLE dbo.Acc_Quotation_Sub ADD [BaseTransNo] VARCHAR(50) NULL;
        """

        db.execute(text(table_init_sql))
        db.commit()

    # =========================================================
    # GET ALL QUOTATIONS
    # =========================================================

    ALLOWED_SORT_COLUMNS = {
        "TransNo": "TransNo",
        "TransDate": "TransDate",
        "CustomerName": "CustomerName",
        "CustomerCode": "SuppCode",
        "Product": "Product",
        "TotalQty": "TotQty",
        "TotalItemAmount": "TotItemAmt",
        "TotalCGSTAmount": "TotCGSTAmt",
        "TotalSGSTAmount": "TotSGSTAmt",
        "TotalIGSTAmount": "TotIGSTAmt",
        "TotalAmount": "TotLineAmt",
        "FinalNetAmount": "NetAmount",
        "NetAmount": "NetAmount",
        "ApprovalStatus": "ApprovalStatus",
        "Status": "Status",
    }

    @staticmethod
    def get_quotations(
        db: Session,
        search: Optional[str] = None,
        status: Optional[str] = None,
        fin_year: Optional[str] = None,
        only_active: bool = True,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "desc",
        fetch_all: bool = False,
    ) -> Dict[str, Any]:

        QuotationService.ensure_tables_exist(db)

        query = """
            SELECT
                TransNo,
                ISNULL(BaseTransNo, TransNo) AS BaseTransNo,
                ISNULL(RevNo, 0) AS RevNo,
                ISNULL(RevLabel, 'ORIGINAL') AS RevLabel,
                ISNULL(IsActiveRevision, 1) AS IsActiveRevision,
                ISNULL(IsLocked, 0) AS IsLocked,
                RevReason,
                ParentTransNo,
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

        if only_active:
            query += """
                AND (IsActiveRevision = 1 OR IsActiveRevision IS NULL)
            """

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

        # Resolve safe sort column and direction
        sort_col, sort_dir = resolve_raw_sort(
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_sort_columns=QuotationService.ALLOWED_SORT_COLUMNS,
            default_column="TransDate",
            default_order="DESC",
        )

        paged_res = paginate_raw_sql(
            db=db,
            base_query=query,
            params=params,
            page=page,
            page_size=page_size,
            sort_column=sort_col,
            sort_order=sort_dir,
            fetch_all=fetch_all,
        )

        quotations = []
        for row in paged_res["data"]:
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

        paged_res["data"] = quotations
        paged_res["items"] = quotations
        return paged_res

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
                ISNULL(BaseTransNo, TransNo) AS BaseTransNo,
                ISNULL(RevNo, 0) AS RevNo,
                ISNULL(RevLabel, 'ORIGINAL') AS RevLabel,
                ISNULL(IsActiveRevision, 1) AS IsActiveRevision,
                ISNULL(IsLocked, 0) AS IsLocked,
                RevReason,
                ParentTransNo,
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
            fin_year_val = (payload.FinYearVal or "").replace("_", "-").strip() if getattr(payload, "FinYearVal", None) else ""
            if not fin_year_val and payload.TransDate:
                try:
                    from datetime import datetime
                    dt = datetime.strptime(str(payload.TransDate)[:10], "%Y-%m-%d")
                    start_yr = dt.year if dt.month >= 4 else dt.year - 1
                    fin_year_val = f"{start_yr}-{start_yr + 1}"
                except Exception:
                    pass
            if not fin_year_val:
                fin_year_val = "2026-2027"

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
                    BaseTransNo,
                    RevNo,
                    RevLabel,
                    IsActiveRevision,
                    IsLocked,
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
                    'SCT',
                    'UNIT I',
                    :fin_year_val,
                    '01',
                    :trans_no,
                    :trans_no,
                    0,
                    'ORIGINAL',
                    1,
                    0,
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
                    "fin_year_val": fin_year_val,
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
                        BaseTransNo,
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
                        'SCT',
                        'UNIT I',
                        '01',
                        :fin_year_val,
                        :trans_no,
                        :base_trans_no,
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
                        "fin_year_val": fin_year_val,
                        "trans_no": trans_no,
                        "base_trans_no": trans_no,
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

            # Get BaseTransNo for line items
            base_trans_no = payload.BaseTransNo
            if not base_trans_no:
                base_row = db.execute(
                    text("SELECT ISNULL(BaseTransNo, TransNo) AS BaseTransNo FROM Acc_Quotation_Main WHERE TransNo = :trans_no"),
                    {"trans_no": trans_no}
                ).mappings().first()
                base_trans_no = base_row["BaseTransNo"] if base_row else trans_no

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
                        BaseTransNo,
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
                        'SCT',
                        'UNIT I',
                        '01',
                        :fin_year_val,
                        :trans_no,
                        :base_trans_no,
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
                        "fin_year_val": fin_year_val,
                        "trans_no": trans_no,
                        "base_trans_no": base_trans_no,
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

    # =========================================================
    # REVISE QUOTATION (Insert new row: 1R, 2R, 3R)
    # =========================================================

    @staticmethod
    def revise_quotation(
        db: Session,
        trans_no: str,
        payload: QuotationRevise,
        user_name: str = "ADMIN",
    ):
        QuotationService.ensure_tables_exist(db)

        # 1. Fetch source quotation
        source_query = """
            SELECT
                TransNo,
                ISNULL(BaseTransNo, TransNo) AS BaseTransNo,
                ISNULL(RevNo, 0) AS RevNo,
                ISNULL(RevLabel, 'ORIGINAL') AS RevLabel,
                ISNULL(IsActiveRevision, 1) AS IsActiveRevision,
                ISNULL(IsLocked, 0) AS IsLocked,
                FinYearVal,
                FinYearCode,
                CONVERT(VARCHAR(10), TransDate, 120) AS TransDate,
                SuppCode,
                CustomerName,
                Product,
                Purpose,
                terms_conditions,
                Remarks
            FROM Acc_Quotation_Main
            WHERE TransNo = :trans_no
              AND Status <> 'Delete'
        """
        source = db.execute(text(source_query), {"trans_no": trans_no}).mappings().first()
        if not source:
            raise HTTPException(status_code=404, detail=f"Quotation {trans_no} not found")

        base_trans_no = source["BaseTransNo"] or trans_no

        # 2. Check existing revisions count & max RevNo for this base quotation
        check_rev_sql = """
            SELECT
                MAX(ISNULL(RevNo, 0)) AS max_rev,
                COUNT(1) AS total_count
            FROM Acc_Quotation_Main
            WHERE (BaseTransNo = :base_trans_no OR TransNo = :base_trans_no)
              AND Status <> 'Delete'
        """
        rev_stats = db.execute(text(check_rev_sql), {"base_trans_no": base_trans_no}).mappings().first()
        max_rev = rev_stats["max_rev"] if rev_stats and rev_stats["max_rev"] is not None else 0

        # Enforce maximum 3 revisions hard lock
        if max_rev >= 3:
            raise HTTPException(
                status_code=400,
                detail=f"Quotation {base_trans_no} has reached the maximum limit of 3 revisions (3R). Further revisions are locked. Please create a new quotation.",
            )

        new_rev_no = max_rev + 1
        new_rev_label = f"{new_rev_no}R"
        new_trans_no = f"{base_trans_no}-{new_rev_label}"
        is_locked = 1 if new_rev_no >= 3 else 0

        # Check if new_trans_no already exists
        exists = db.execute(
            text("SELECT 1 FROM Acc_Quotation_Main WHERE TransNo = :t"),
            {"t": new_trans_no}
        ).fetchone()
        if exists:
            raise HTTPException(
                status_code=400,
                detail=f"Revision {new_trans_no} already exists.",
            )

        try:
            # 3. Supersede prior active revisions of this base quotation
            supersede_sql = """
                UPDATE Acc_Quotation_Main
                SET IsActiveRevision = 0,
                    SupersededOn = GETDATE()
                WHERE (BaseTransNo = :base_trans_no OR TransNo = :base_trans_no)
                  AND IsActiveRevision = 1
            """
            db.execute(text(supersede_sql), {"base_trans_no": base_trans_no})

            # 4. Insert new revision row into Acc_Quotation_Main
            fin_year_val = (payload.FinYearVal or source["FinYearVal"] or "2026-2027").replace("_", "-").strip()
            fin_year_code = payload.FinYearCode or source["FinYearCode"] or "01"

            insert_header = """
                INSERT INTO Acc_Quotation_Main (
                    Ccode,
                    Lcode,
                    FinYearVal,
                    FinYearCode,
                    TransNo,
                    BaseTransNo,
                    RevNo,
                    RevLabel,
                    IsActiveRevision,
                    IsLocked,
                    RevReason,
                    ParentTransNo,
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
                    SysName,
                    CreateOn
                )
                VALUES (
                    'SCT',
                    'UNIT I',
                    :fin_year_val,
                    :fin_year_code,
                    :trans_no,
                    :base_trans_no,
                    :rev_no,
                    :rev_label,
                    1,
                    :is_locked,
                    :rev_reason,
                    :parent_trans_no,
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
                    '0',
                    'Revise',
                    :user_name,
                    :user_name,
                    '127.0.0.1',
                    'API_SERVER',
                    GETDATE()
                )
            """

            db.execute(
                text(insert_header),
                {
                    "fin_year_val": fin_year_val,
                    "fin_year_code": fin_year_code,
                    "trans_no": new_trans_no,
                    "base_trans_no": base_trans_no,
                    "rev_no": new_rev_no,
                    "rev_label": new_rev_label,
                    "is_locked": is_locked,
                    "rev_reason": payload.RevReason or "Commercial / Scope Revision",
                    "parent_trans_no": trans_no,
                    "trans_date": payload.TransDate or source["TransDate"],
                    "cust_code": payload.CustomerCode or source["SuppCode"] or "",
                    "cust_name": payload.CustomerName or source["CustomerName"] or "",
                    "prod_type": payload.ProdType or source["Product"] or "1",
                    "narration": payload.Narration or "",
                    "purpose": payload.Purpose or source["Purpose"] or "",
                    "terms": payload.TermsAndConditions or source["terms_conditions"] or "",
                    "tot_qty": payload.TotalQty,
                    "tot_item_amt": payload.TotalItemAmount,
                    "tot_cgst": payload.TotalCGSTAmount,
                    "tot_sgst": payload.TotalSGSTAmount,
                    "tot_igst": payload.TotalIGSTAmount,
                    "tot_amt": payload.TotalAmount,
                    "round_type": payload.RoundType or "None",
                    "round_off": payload.RoundOff or 0,
                    "net_amount": payload.FinalNetAmount,
                    "user_name": user_name,
                },
            )

            # 5. Insert revision line items into Acc_Quotation_Sub
            for index, item in enumerate(payload.Items, start=1):
                insert_item = """
                    INSERT INTO Acc_Quotation_Sub (
                        Ccode,
                        Lcode,
                        FinYearCode,
                        FinYearVal,
                        TransNo,
                        BaseTransNo,
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
                        SysName,
                        CreateOn
                    )
                    VALUES (
                        'SCT',
                        'UNIT I',
                        '01',
                        :fin_year_val,
                        :trans_no,
                        :base_trans_no,
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
                        'Revise',
                        :user_name,
                        :user_name,
                        '127.0.0.1',
                        'API_SERVER',
                        GETDATE()
                    )
                """

                db.execute(
                    text(insert_item),
                    {
                        "fin_year_val": fin_year_val,
                        "trans_no": new_trans_no,
                        "base_trans_no": base_trans_no,
                        "trans_date": payload.TransDate or source["TransDate"],
                        "order_id": str(item.order_id or index),
                        "item_code": item.ItemCode or f"ITM-{index}",
                        "prod_type": item.ProductType or "",
                        "highlight": item.Prod_highlight or "",
                        "hsn": item.HSNCode or "",
                        "uom": item.UOM or "Pcs",
                        "rate": item.Rate or 0,
                        "qty": item.Qty or 0,
                        "item_val": item.ItemValue or 0,
                        "gst": item.GST or 0,
                        "cgst": item.CGST or 0,
                        "sgst": item.SGST or 0,
                        "igst": item.IGST or 0,
                        "net_amt": item.NetAmount or 0,
                        "service": item.Service or "Standard Supply",
                        "user_name": user_name,
                    },
                )

            db.commit()

            return QuotationService.get_quotation_by_no(db, new_trans_no)

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to revise quotation: {str(e)}")

    # =========================================================
    # GET QUOTATION REVISION HISTORY (For comparison)
    # =========================================================

    @staticmethod
    def get_quotation_history(
        db: Session,
        base_trans_no: str,
    ):
        QuotationService.ensure_tables_exist(db)

        # 1. First find the true BaseTransNo if an intermediate revision TransNo was provided
        find_base_sql = """
            SELECT ISNULL(BaseTransNo, TransNo) AS BaseTransNo
            FROM Acc_Quotation_Main
            WHERE TransNo = :base_trans_no
        """
        base_row = db.execute(text(find_base_sql), {"base_trans_no": base_trans_no}).mappings().first()
        root_base = base_row["BaseTransNo"] if base_row else base_trans_no

        # 2. Fetch all revisions sorted chronologically
        history_sql = """
            SELECT
                TransNo,
                ISNULL(BaseTransNo, TransNo) AS BaseTransNo,
                ISNULL(RevNo, 0) AS RevNo,
                ISNULL(RevLabel, 'ORIGINAL') AS RevLabel,
                ISNULL(IsActiveRevision, 1) AS IsActiveRevision,
                ISNULL(IsLocked, 0) AS IsLocked,
                RevReason,
                ParentTransNo,
                CONVERT(VARCHAR(19), SupersededOn, 120) AS SupersededOn,
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
                ApprovalStatus,
                UserName,
                CONVERT(VARCHAR(19), CreateOn, 120) AS CreateOn
            FROM Acc_Quotation_Main
            WHERE (BaseTransNo = :root_base OR TransNo = :root_base)
              AND Status <> 'Delete'
            ORDER BY ISNULL(RevNo, 0) ASC, TransNo ASC
        """

        revisions = db.execute(text(history_sql), {"root_base": root_base}).mappings().all()

        if not revisions:
            raise HTTPException(status_code=404, detail=f"No quotations found for {base_trans_no}")

        result_history = []
        for rev in revisions:
            rev_dict = dict(rev)
            t_no = rev_dict["TransNo"]

            # Fetch line items for this revision
            items_sql = """
                SELECT
                    order_id,
                    ItemCode,
                    ProductType,
                    Prod_highlight,
                    UOM,
                    HSNCode,
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
                ORDER BY TRY_CAST(order_id AS INT), order_id
            """
            items = db.execute(text(items_sql), {"trans_no": t_no}).mappings().all()
            rev_dict["Items"] = [dict(item) for item in items]
            result_history.append(rev_dict)

        max_rev = max([r["RevNo"] for r in result_history]) if result_history else 0
        is_locked = any(r.get("IsLocked") for r in result_history) or max_rev >= 3

        return {
            "base_trans_no": root_base,
            "total_revisions": len(result_history),
            "current_rev_no": max_rev,
            "is_locked": is_locked,
            "can_revise": (not is_locked) and (max_rev < 3),
            "history": result_history,
        }