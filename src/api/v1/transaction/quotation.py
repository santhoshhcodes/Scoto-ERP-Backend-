from fastapi.responses import StreamingResponse
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session

from src.schemas.transaction import (
    QuotationCreate,
    QuotationUpdate,
    QuotationApprovalUpdate,
)

from src.services.quotation_service import (
    QuotationService,
)
from src.services.quotation_excel_service import (
    QuotationExcelService,
)


router = APIRouter(
    prefix="/quotations",
    tags=["Transaction - Quotation"],
)


# =========================================================
# GET ALL QUOTATIONS
# =========================================================

@router.get("")
def get_quotations(
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(
        get_mssql_session("db2")
    ),
):

    quotations = QuotationService.get_quotations(
        db=db,
        search=search,
        status=status,
    )

    return {
        "success": True,
        "count": len(quotations),
        "data": quotations,
    }


# =========================================================
# EXPORT QUOTATION TO EXCEL
# =========================================================

@router.get("/{trans_no:path}/export-excel")
@router.get("/export-excel/{trans_no:path}")
def export_quotation_excel(
    trans_no: str,
    db: Session = Depends(
        get_mssql_session("db2")
    ),
):
    excel_stream = QuotationExcelService.generate_excel(
        db=db,
        trans_no=trans_no,
    )

    safe_trans_no = (
        trans_no.replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )
    filename = f"quote_{safe_trans_no}.xlsx"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


# =========================================================
# GET SINGLE QUOTATION
# =========================================================

@router.get("/{trans_no:path}")
def get_quotation_by_no(
    trans_no: str,
    db: Session = Depends(
        get_mssql_session("db2")
    ),
):

    quotation = (
        QuotationService.get_quotation_by_no(
            db=db,
            trans_no=trans_no,
        )
    )

    return {
        "success": True,
        "data": quotation,
    }


# =========================================================
# CREATE
# =========================================================

@router.post("")
def create_quotation(
    payload: QuotationCreate,
    db: Session = Depends(
        get_mssql_session("db2")
    ),
):

    trans_no = (
        QuotationService.create_quotation(
            db=db,
            payload=payload,
        )
    )

    return {
        "success": True,
        "message": (
            f"Quotation {trans_no} "
            "saved successfully."
        ),
        "trans_no": trans_no,
    }


# =========================================================
# UPDATE
# =========================================================

@router.put("/{trans_no:path}")
def update_quotation(
    trans_no: str,
    payload: QuotationUpdate,
    db: Session = Depends(
        get_mssql_session("db2")
    ),
):

    QuotationService.update_quotation(
        db=db,
        trans_no=trans_no,
        payload=payload,
    )

    return {
        "success": True,
        "message": (
            f"Quotation {trans_no} "
            "updated successfully."
        ),
    }


# =========================================================
# APPROVAL
# =========================================================

@router.patch("/{trans_no:path}/approval")
def update_quotation_approval(
    trans_no: str,
    payload: QuotationApprovalUpdate,
    db: Session = Depends(
        get_mssql_session("db2")
    ),
):

    status_value = (
        QuotationService
        .update_quotation_approval(
            db=db,
            trans_no=trans_no,
            payload=payload,
        )
    )

    return {
        "success": True,
        "message": (
            f"Quotation {trans_no} "
            f"status changed to {status_value}."
        ),
        "trans_no": trans_no,
        "status": status_value,
    }


# =========================================================
# DELETE
# =========================================================

@router.delete("/{trans_no:path}")
def delete_quotation(
    trans_no: str,
    db: Session = Depends(
        get_mssql_session("db2")
    ),
):

    QuotationService.delete_quotation(
        db=db,
        trans_no=trans_no,
    )

    return {
        "success": True,
        "message": (
            f"Quotation {trans_no} "
            "deleted successfully."
        ),
    }