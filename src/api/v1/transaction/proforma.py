from fastapi.responses import StreamingResponse

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.schemas.transaction import (
    ProformaCreate,
    ProformaUpdate,
    ProformaApprovalUpdate,
)
from src.services.proforma_service import ProformaInvoiceService
from src.services.proforma_excel_service import ProformaExcelService


router = APIRouter(
    prefix="/proforma-invoices",
    tags=["Transaction - Proforma Invoice"],
)


@router.get("")
def get_proforma_invoices(
    search: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_mssql_session("db2")),
):
    """Get all active proforma invoices with their items."""
    data = ProformaInvoiceService.get_all(
        db=db,
        search=search,
        approval_status=status_filter,
    )

    return {
        "success": True,
        "count": len(data),
        "data": data,
    }


# Keep this route before the single-invoice route.
@router.patch("/{trans_no:path}/approval")
def update_proforma_approval(
    trans_no: str,
    payload: ProformaApprovalUpdate,
    db: Session = Depends(get_mssql_session("db2")),
):
    """Approve or set an invoice back to pending."""
    approval_status = ProformaInvoiceService.update_approval(
        db=db,
        trans_no=trans_no,
        payload=payload,
    )

    status_label = (
        "Approved" if approval_status == "1" else "Pending"
    )

    return {
        "success": True,
        "message": (
            f"Proforma Invoice {trans_no} status changed to "
            f"{status_label}."
        ),
        "trans_no": trans_no,
        "status": approval_status,
        "status_label": status_label,
    }


# =========================================================
# EXPORT PROFORMA INVOICE TO EXCEL
# =========================================================

@router.get("/{trans_no:path}/export-excel")
@router.get("/export-excel/{trans_no:path}")
def export_proforma_excel(
    trans_no: str,
    db: Session = Depends(get_mssql_session("db2")),
):
    excel_stream = ProformaExcelService.generate_excel(
        db=db,
        trans_no=trans_no,
    )

    safe_trans_no = (
        trans_no.replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )
    filename = f"proforma_{safe_trans_no}.xlsx"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/{trans_no:path}")
def get_proforma_invoice(
    trans_no: str,
    db: Session = Depends(get_mssql_session("db2")),
):
    """Get one proforma invoice with its line items."""
    data = ProformaInvoiceService.get_by_no(
        db=db,
        trans_no=trans_no,
    )

    return {
        "success": True,
        "data": data,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_proforma_invoice(
    payload: ProformaCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    """Create a proforma invoice and its line items."""
    trans_no = ProformaInvoiceService.create(
        db=db,
        payload=payload,
    )

    return {
        "success": True,
        "message": (
            f"Proforma Invoice {trans_no} created successfully."
        ),
        "trans_no": trans_no,
    }


@router.put("/{trans_no:path}")
def update_proforma_invoice(
    trans_no: str,
    payload: ProformaUpdate,
    db: Session = Depends(get_mssql_session("db2")),
):
    """Update the invoice header and replace its line items."""
    ProformaInvoiceService.update(
        db=db,
        trans_no=trans_no,
        payload=payload,
    )

    return {
        "success": True,
        "message": (
            f"Proforma Invoice {trans_no} updated successfully."
        ),
        "trans_no": trans_no,
    }


@router.delete("/{trans_no:path}")
def delete_proforma_invoice(
    trans_no: str,
    db: Session = Depends(get_mssql_session("db2")),
):
    """Soft-delete the invoice and its line items."""
    ProformaInvoiceService.delete(
        db=db,
        trans_no=trans_no,
    )

    return {
        "success": True,
        "message": (
            f"Proforma Invoice {trans_no} deleted successfully."
        ),
        "trans_no": trans_no,
    }
