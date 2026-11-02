from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session


def ensure_sales_invoice_tables_exist(db: Session) -> None:
    """
    Compatibility initializer from the original endpoint.
    Prefer creating these tables through a controlled migration in production.
    """
    sql = """
    IF OBJECT_ID('dbo.Acc_Sales_Inv_Main', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Acc_Sales_Inv_Main (
            Ccode NVARCHAR(10) DEFAULT 'SCT',
            Lcode NVARCHAR(10) DEFAULT 'UNIT I',
            FinYearCode NVARCHAR(10) DEFAULT '2',
            FinYearVal NVARCHAR(20) DEFAULT '2025_2026',
            TransNo NVARCHAR(50) NOT NULL PRIMARY KEY,
            TransDate NVARCHAR(30), InvoiceNo NVARCHAR(50), InvoiceDate NVARCHAR(30),
            CustomerName NVARCHAR(255), CustomerCode NVARCHAR(50), GST NVARCHAR(50),
            TotalQty DECIMAL(18,2) DEFAULT 0, TotalItemAmount DECIMAL(18,2) DEFAULT 0,
            TotalCGSTAmount DECIMAL(18,2) DEFAULT 0, TotalSGSTAmount DECIMAL(18,2) DEFAULT 0,
            TotalIGSTAmount DECIMAL(18,2) DEFAULT 0, TotalAmount DECIMAL(18,2) DEFAULT 0,
            RoundType DECIMAL(18,2) DEFAULT 0, RoundOff DECIMAL(18,2) DEFAULT 0,
            NetAmount DECIMAL(18,2) DEFAULT 0, UserName NVARCHAR(50) DEFAULT 'ADMIN',
            UserCode NVARCHAR(50) DEFAULT 'ADMIN', SysIp NVARCHAR(50) DEFAULT '127.0.0.1',
            SysName NVARCHAR(50) DEFAULT 'API_SERVER', CreateOn NVARCHAR(50),
            Approval_Status NVARCHAR(50) DEFAULT '0', ApprovedBy NVARCHAR(50),
            ApprovedOn NVARCHAR(50), Remarks NVARCHAR(500), Status NVARCHAR(20) DEFAULT 'Add',
            GRN NVARCHAR(50)
        );
    END;

    IF OBJECT_ID('dbo.Acc_Sales_Inv_Sub', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Acc_Sales_Inv_Sub (
            Ccode NVARCHAR(10) DEFAULT 'SCT', Lcode NVARCHAR(10) DEFAULT 'UNIT I',
            FinYearCode NVARCHAR(10) DEFAULT '2', FinYearVal NVARCHAR(20) DEFAULT '2025_2026',
            TransNo NVARCHAR(50), TransDate NVARCHAR(30), InvoiceNo NVARCHAR(50),
            InvoiceDate NVARCHAR(30), CustomerName NVARCHAR(255), CustomerCode NVARCHAR(50),
            ItemCode NVARCHAR(50), ProductType NVARCHAR(255), HSNCode NVARCHAR(50),
            Qty DECIMAL(18,2) DEFAULT 0, Rate DECIMAL(18,2) DEFAULT 0,
            ItemValue DECIMAL(18,2) DEFAULT 0, SerialNo NVARCHAR(100),
            GST NVARCHAR(50) DEFAULT '18', CGST DECIMAL(18,2) DEFAULT 0,
            SGST DECIMAL(18,2) DEFAULT 0, IGST DECIMAL(18,2) DEFAULT 0,
            NetAmount DECIMAL(18,2) DEFAULT 0, Status NVARCHAR(20) DEFAULT 'Add',
            UserName NVARCHAR(50) DEFAULT 'ADMIN', Usercode NVARCHAR(50) DEFAULT 'ADMIN',
            SysName NVARCHAR(50) DEFAULT 'API_SERVER', SysIp NVARCHAR(50) DEFAULT '127.0.0.1',
            CreateOn NVARCHAR(50)
        );
    END;
    """
    db.execute(text(sql))
    db.commit()


def _date(value: Optional[str]) -> str:
    return value or datetime.now().strftime("%d/%m/%Y")


def _approval_code(value: Optional[str]) -> str:
    return "1" if (value or "").strip().lower() in {"approved", "1"} else "0"


def _header_values(payload, trans_no: str) -> dict:
    return {
        "trans_no": trans_no,
        "trans_date": _date(payload.TransDate),
        "invoice_no": payload.InvoiceNo or "",
        "invoice_date": _date(payload.InvoiceDate),
        "customer_code": payload.CustomerCode or "",
        "customer_name": payload.CustomerName or "",
        "gst": payload.GST or "",
        "total_qty": payload.TotalQty or 0,
        "total_item_amount": payload.TotalItemAmount or 0,
        "total_cgst_amount": payload.TotalCGSTAmount or 0,
        "total_sgst_amount": payload.TotalSGSTAmount or 0,
        "total_igst_amount": payload.TotalIGSTAmount or 0,
        "total_amount": payload.TotalAmount or 0,
        "round_off": payload.RoundOff or 0,
        "net_amount": payload.FinalNetAmount if payload.FinalNetAmount is not None else (payload.TotalAmount or 0),
        "grn": payload.GRN or "",
        "remarks": payload.Remarks or "",
        "approval_status": _approval_code(payload.ApprovalStatus),
    }


def _insert_items(db: Session, trans_no: str, payload) -> None:
    sql = text("""
        INSERT INTO Acc_Sales_Inv_Sub (
            Ccode, Lcode, FinYearCode, FinYearVal, TransNo, TransDate,
            InvoiceNo, InvoiceDate, CustomerCode, CustomerName,
            ItemCode, ProductType, HSNCode, Qty, Rate, ItemValue, SerialNo,
            GST, CGST, SGST, IGST, NetAmount, Status, UserName, Usercode,
            SysName, SysIp, CreateOn
        ) VALUES (
            'SCT', 'UNIT I', '2', '2025_2026', :trans_no, :trans_date,
            :invoice_no, :invoice_date, :customer_code, :customer_name,
            :item_code, :product_type, :hsn_code, :qty, :rate, :item_value, :serial_no,
            :gst, :cgst, :sgst, :igst, :net_amount, 'Add', 'ADMIN', 'ADMIN',
            'API_SERVER', '127.0.0.1', CONVERT(VARCHAR(30), GETDATE(), 120)
        )
    """)
    common = {
        "trans_no": trans_no, "trans_date": _date(payload.TransDate),
        "invoice_no": payload.InvoiceNo or "", "invoice_date": _date(payload.InvoiceDate),
        "customer_code": payload.CustomerCode or "", "customer_name": payload.CustomerName or "",
    }
    for item in payload.Items:
        db.execute(sql, {
            **common,
            "item_code": item.ItemCode or "", "product_type": item.ProductType or "",
            "hsn_code": item.HSNCode or "", "qty": item.Qty or 0, "rate": item.Rate or 0,
            "item_value": item.ItemValue or 0, "serial_no": item.SerialNo or "",
            "gst": str(item.GST if item.GST is not None else 18),
            "cgst": item.CGST or 0, "sgst": item.SGST or 0, "igst": item.IGST or 0,
            "net_amount": item.NetAmount or 0,
        })


def _insert_serials(db: Session, trans_no: str, payload) -> None:
    sql = text("""
        INSERT INTO Acc_GRN_Stock (
            Ccode, Lcode, FinYearCode, FinYearVal, ProductType, HSNCode,
            MaterialInventory, SerialNo, TransNo, TransDate, Status,
            UserName, UserCode, SysIp, SysName, CreateOn
        ) VALUES (
            'SCT', 'UNIT I', '2', '2025_2026', :product_type, :hsn_code,
            :material_inv, :serial_no, :trans_no, :trans_date, 'Add',
            'ADMIN', 'ADMIN', '127.0.0.1', 'API_SERVER', CONVERT(VARCHAR(30), GETDATE(), 120)
        )
    """)
    for serial in payload.Serials:
        db.execute(sql, {
            "product_type": serial.ProductType or "", "hsn_code": serial.HSNCode or "",
            "material_inv": serial.MaterialInventory or "", "serial_no": serial.SerialNo or "",
            "trans_no": trans_no, "trans_date": _date(payload.TransDate),
        })


def get_sales_invoices(
    db: Session, search: Optional[str] = None, approval_status: Optional[str] = None,
    company_code: Optional[str] = "SCT", location_code: Optional[str] = "UNIT I",
):
    sql = """
        SELECT TransNo, TransDate, InvoiceNo, InvoiceDate, CustomerCode, CustomerName,
               GRN, Remarks, TotalQty, TotalItemAmount, TotalCGSTAmount, TotalSGSTAmount,
               TotalIGSTAmount, TotalAmount, RoundType, RoundOff,
               NetAmount AS FinalNetAmount, Approval_Status,
               CASE WHEN LTRIM(RTRIM(Approval_Status)) = '1'
                      OR LOWER(LTRIM(RTRIM(Approval_Status))) = 'approved'
                    THEN 'Approved' ELSE 'Pending' END AS ApprovalStatus,
               ApprovedBy, ApprovedOn, CreateOn AS CreatedOn
        FROM Acc_Sales_Inv_Main
        WHERE (Status IS NULL OR Status <> 'Delete')
    """
    params = {}
    if company_code:
        sql += " AND (Ccode = :ccode OR Ccode IS NULL)"
        params["ccode"] = company_code
    if location_code:
        sql += " AND (Lcode = :lcode OR Lcode IS NULL)"
        params["lcode"] = location_code
    if search:
        sql += """ AND (TransNo LIKE :search OR InvoiceNo LIKE :search
                    OR CustomerName LIKE :search OR CustomerCode LIKE :search
                    OR Remarks LIKE :search)"""
        params["search"] = f"%{search}%"
    if approval_status and approval_status.upper() != "ALL":
        if approval_status.strip().lower() in {"approved", "1"}:
            sql += " AND (Approval_Status = '1' OR Approval_Status = 'Approved')"
        else:
            sql += """ AND (Approval_Status = '0' OR Approval_Status = 'Pending'
                        OR Approval_Status IS NULL OR Approval_Status = '')"""
    sql += " ORDER BY TransNo DESC"
    rows = db.execute(text(sql), params).mappings().all()
    data = []
    for row in rows:
        item = dict(row)
        item["items_count"] = db.execute(text("""
            SELECT COUNT(*) FROM Acc_Sales_Inv_Sub
            WHERE TransNo = :trans_no AND (Status IS NULL OR Status <> 'Delete')
        """), {"trans_no": item["TransNo"]}).scalar() or 0
        data.append(item)
    return {"status": "success", "data": data, "total": len(data)}


def get_available_proforma_invoices(db: Session):
    rows = db.execute(text("""
        SELECT TransNo, TransDate, CustomerCode, CustomerName, TotalQty, NetAmount, Remarks
        FROM Acc_Proforma_Inv_Main
        WHERE Status <> 'Delete'
        ORDER BY TransNo DESC
    """)).mappings().all()
    return {"status": "success", "data": [dict(row) for row in rows]}


def get_sales_invoice_by_no(db: Session, trans_no: str):
    header = db.execute(text("""
        SELECT TransNo, TransDate, InvoiceNo, InvoiceDate, CustomerCode, CustomerName,
               GST, GRN, Remarks, TotalQty, TotalItemAmount, TotalCGSTAmount,
               TotalSGSTAmount, TotalIGSTAmount, TotalAmount, RoundType, RoundOff,
               NetAmount AS FinalNetAmount, Approval_Status,
               CASE WHEN LTRIM(RTRIM(Approval_Status)) = '1'
                      OR LOWER(LTRIM(RTRIM(Approval_Status))) = 'approved'
                    THEN 'Approved' ELSE 'Pending' END AS ApprovalStatus,
               ApprovedBy, ApprovedOn, CreateOn AS CreatedOn
        FROM Acc_Sales_Inv_Main
        WHERE TransNo = :trans_no AND (Status IS NULL OR Status <> 'Delete')
    """), {"trans_no": trans_no}).mappings().first()
    if not header:
        raise HTTPException(status_code=404, detail=f"Sales Invoice '{trans_no}' not found.")
    data = dict(header)
    data["Items"] = [dict(r) for r in db.execute(text("""
        SELECT ItemCode, ProductType, HSNCode, Qty, Rate, ItemValue, SerialNo,
               GST, CGST, SGST, IGST, NetAmount
        FROM Acc_Sales_Inv_Sub
        WHERE TransNo = :trans_no AND (Status IS NULL OR Status <> 'Delete')
    """), {"trans_no": trans_no}).mappings().all()]
    data["Serials"] = [dict(r) for r in db.execute(text("""
        SELECT ProductType, HSNCode, MaterialInventory, SerialNo
        FROM Acc_GRN_Stock
        WHERE TransNo = :trans_no AND (Status IS NULL OR Status <> 'Delete')
    """), {"trans_no": trans_no}).mappings().all()]
    return {"status": "success", "data": data}


def create_sales_invoice(db: Session, payload):
    try:
        trans_no = (payload.TransNo or "").strip()
        if not trans_no or trans_no.startswith("SINV-2026-"):
            year = datetime.now().strftime("%y")
            next_year = str((int(year) + 1) % 100).zfill(2)
            fin_tag = f"{year}-{next_year}"
            # Kept compatible with the original numbering scheme; protect against races
            # with a unique constraint/retry or a dedicated sequence in production.
            count = db.execute(text("SELECT COUNT(*) FROM Acc_Sales_Inv_Main WITH (UPDLOCK, HOLDLOCK)")).scalar() or 0
            trans_no = f"SINV/{fin_tag}/{count + 1:05d}"

        exists = db.execute(text("""
            SELECT 1 FROM Acc_Sales_Inv_Main WHERE TransNo = :trans_no
        """), {"trans_no": trans_no}).first()
        if exists:
            raise HTTPException(status_code=409, detail=f"Sales Invoice '{trans_no}' already exists.")

        db.execute(text("""
            INSERT INTO Acc_Sales_Inv_Main (
                Ccode, Lcode, FinYearCode, FinYearVal, TransNo, TransDate, InvoiceNo,
                InvoiceDate, CustomerCode, CustomerName, GST, TotalQty, TotalItemAmount,
                TotalCGSTAmount, TotalSGSTAmount, TotalIGSTAmount, TotalAmount, RoundType,
                RoundOff, NetAmount, GRN, Remarks, UserName, UserCode, SysIp, SysName,
                CreateOn, Approval_Status, Status
            ) VALUES (
                'SCT', 'UNIT I', '2', '2025_2026', :trans_no, :trans_date, :invoice_no,
                :invoice_date, :customer_code, :customer_name, :gst, :total_qty,
                :total_item_amount, :total_cgst_amount, :total_sgst_amount, :total_igst_amount,
                :total_amount, 0, :round_off, :net_amount, :grn, :remarks, 'ADMIN', 'ADMIN',
                '127.0.0.1', 'API_SERVER', CONVERT(VARCHAR(30), GETDATE(), 120),
                :approval_status, 'Add'
            )
        """), _header_values(payload, trans_no))
        _insert_items(db, trans_no, payload)
        _insert_serials(db, trans_no, payload)
        db.commit()
        return {"status": "success", "message": f"Sales Invoice '{trans_no}' created successfully.", "trans_no": trans_no}
    except Exception:
        db.rollback()
        raise


def update_sales_invoice(db: Session, trans_no: str, payload):
    try:
        exists = db.execute(text("""
            SELECT 1 FROM Acc_Sales_Inv_Main
            WHERE TransNo = :trans_no AND (Status IS NULL OR Status <> 'Delete')
        """), {"trans_no": trans_no}).first()
        if not exists:
            raise HTTPException(status_code=404, detail=f"Sales Invoice '{trans_no}' not found for update.")

        values = _header_values(payload, trans_no)
        db.execute(text("""
            UPDATE Acc_Sales_Inv_Main SET TransDate=:trans_date, InvoiceNo=:invoice_no,
                InvoiceDate=:invoice_date, CustomerCode=:customer_code, CustomerName=:customer_name,
                GST=:gst, TotalQty=:total_qty, TotalItemAmount=:total_item_amount,
                TotalCGSTAmount=:total_cgst_amount, TotalSGSTAmount=:total_sgst_amount,
                TotalIGSTAmount=:total_igst_amount, TotalAmount=:total_amount, RoundOff=:round_off,
                NetAmount=:net_amount, GRN=:grn, Remarks=:remarks, Approval_Status=:approval_status
            WHERE TransNo=:trans_no
        """), values)

        # Preserve the original endpoint's replacement behavior, but keep it atomic.
        db.execute(text("DELETE FROM Acc_Sales_Inv_Sub WHERE TransNo=:trans_no"), {"trans_no": trans_no})
        db.execute(text("DELETE FROM Acc_GRN_Stock WHERE TransNo=:trans_no"), {"trans_no": trans_no})
        _insert_items(db, trans_no, payload)
        _insert_serials(db, trans_no, payload)
        db.commit()
        return {"status": "success", "message": f"Sales Invoice '{trans_no}' updated successfully."}
    except Exception:
        db.rollback()
        raise


def delete_sales_invoice(db: Session, trans_no: str):
    try:
        exists = db.execute(text("""
            SELECT 1 FROM Acc_Sales_Inv_Main
            WHERE TransNo=:trans_no AND (Status IS NULL OR Status <> 'Delete')
        """), {"trans_no": trans_no}).first()
        if not exists:
            raise HTTPException(status_code=404, detail=f"Sales Invoice '{trans_no}' not found.")
        db.execute(text("UPDATE Acc_Sales_Inv_Main SET Status='Delete' WHERE TransNo=:trans_no"), {"trans_no": trans_no})
        db.execute(text("UPDATE Acc_Sales_Inv_Sub SET Status='Delete' WHERE TransNo=:trans_no"), {"trans_no": trans_no})
        # Match the source behavior: serial rows are not changed by soft-delete.
        db.commit()
        return {"status": "success", "message": f"Sales Invoice '{trans_no}' deleted successfully."}
    except Exception:
        db.rollback()
        raise


def update_sales_invoice_approval(db: Session, trans_no: str, payload):
    try:
        code = _approval_code(payload.ApprovalStatus)
        result = db.execute(text("""
            UPDATE Acc_Sales_Inv_Main
            SET Approval_Status=:status_code, ApprovedBy=:approved_by, ApprovedOn=:approved_on
            WHERE TransNo=:trans_no AND (Status IS NULL OR Status <> 'Delete')
        """), {
            "status_code": code, "approved_by": payload.ApprovedBy or "ADMIN",
            "approved_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "trans_no": trans_no,
        })
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Sales Invoice '{trans_no}' not found.")
        db.commit()
        return {
            "status": "success",
            "message": f"Sales Invoice '{trans_no}' approval status set to '{payload.ApprovalStatus}'.",
            "trans_no": trans_no,
            "approval_status": payload.ApprovalStatus,
        }
    except Exception:
        db.rollback()
        raise
