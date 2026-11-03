from fastapi.responses import StreamingResponse
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.schemas.sales_invoice import (
    SalesInvoiceCreate,
    SalesInvoiceUpdate,
    SalesInvoiceApprovalUpdate,
)
from src.services import sales_invoice_service as service
from src.services.sales_invoice_excel_service import SalesInvoiceExcelService

router = APIRouter(prefix="/sales-invoices", tags=["Transaction - Sales Invoice"])


@router.get("")
def list_sales_invoices(
    search: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None, description="ALL, Approved, or Pending"),
    company_code: Optional[str] = Query(default="SCT"),
    location_code: Optional[str] = Query(default="UNIT I"),
    fin_year: Optional[str] = Query(default=None, description="Financial Year filter"),
    db: Session = Depends(get_mssql_session("db2")),
):
    service.ensure_sales_invoice_tables_exist(db)
    return service.get_sales_invoices(
        db=db, search=search, approval_status=status,
        company_code=company_code, location_code=location_code,
        fin_year=fin_year,
    )


@router.get("/meta/proforma-invoices")
def list_proforma_invoices(
    company_code: Optional[str] = Query(default="SCT"),
    location_code: Optional[str] = Query(default="UNIT I"),
    db: Session = Depends(get_mssql_session("db2")),
):
    # The source query does not filter by these parameters; retained for API compatibility.
    return service.get_available_proforma_invoices(db)



@router.get("/{trans_no:path}/export-excel")
@router.get("/export-excel/{trans_no:path}")
def export_sales_invoice_excel(
    trans_no: str,
    db: Session = Depends(get_mssql_session("db2")),
):
    service.ensure_sales_invoice_tables_exist(db)
    excel_stream = SalesInvoiceExcelService.generate_excel(
        db=db,
        trans_no=trans_no,
    )
    safe_trans_no = (
        trans_no.replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        .strip()
    )
    filename = f"sales_invoice_{safe_trans_no}.xlsx"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/{trans_no:path}")

def get_sales_invoice(
    trans_no: str,
    db: Session = Depends(get_mssql_session("db2")),
):
    service.ensure_sales_invoice_tables_exist(db)
    return service.get_sales_invoice_by_no(db, trans_no)


@router.post("", status_code=201)
def create_sales_invoice(
    payload: SalesInvoiceCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    service.ensure_sales_invoice_tables_exist(db)
    return service.create_sales_invoice(db, payload)


@router.put("/{trans_no:path}")
def update_sales_invoice(
    trans_no: str,
    payload: SalesInvoiceUpdate,
    db: Session = Depends(get_mssql_session("db2")),
):
    service.ensure_sales_invoice_tables_exist(db)
    return service.update_sales_invoice(db, trans_no, payload)


@router.delete("/{trans_no:path}")
def delete_sales_invoice(
    trans_no: str,
    db: Session = Depends(get_mssql_session("db2")),
):
    service.ensure_sales_invoice_tables_exist(db)
    return service.delete_sales_invoice(db, trans_no)


@router.patch("/{trans_no:path}/approval")
def set_sales_invoice_approval(
    trans_no: str,
    payload: SalesInvoiceApprovalUpdate,
    db: Session = Depends(get_mssql_session("db2")),
):
    service.ensure_sales_invoice_tables_exist(db)
    return service.update_sales_invoice_approval(db, trans_no, payload)
