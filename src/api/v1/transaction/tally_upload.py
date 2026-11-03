"""
Tally Upload Endpoints
Replicates and modernizes the Tally Excel upload workflow from Rpt_Tally_Upload.aspx.cs
"""

from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.services.tally_service import TallyService

router = APIRouter(
    prefix="/tally",
    tags=["Transaction - Tally Upload"],
)


@router.post("/preview", status_code=status.HTTP_200_OK)
async def preview_tally_excel(
    file: UploadFile = File(..., description="Tally Excel file (.xlsx)"),
    c_code: str = Form(default="SCT", description="Company code"),
    l_code: str = Form(default="UNIT I", description="Location code"),
    db2: Session = Depends(get_mssql_session("db2")),
):
    """
    Parses the uploaded Tally Excel file without writing to the database.
    Returns extracted vouchers, balanced debits/credits, and ledger mapping matches.
    """
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx Excel files are supported for Tally upload.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    return TallyService.parse_tally_workbook(
        file_bytes=file_bytes,
        db2=db2,
        c_code=c_code,
        l_code=l_code,
    )


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_tally_excel(
    file: UploadFile = File(..., description="Tally Excel file (.xlsx)"),
    c_code: str = Form(default="SCT", description="Company code"),
    l_code: str = Form(default="UNIT I", description="Location code"),
    user_id: str = Form(default="ACCSCOTO", description="Operating User ID"),
    user_name: str = Form(default="ACCSCOTO", description="Operating User Name"),
    db2: Session = Depends(get_mssql_session("db2")),
):
    """
    Ingests vouchers from Tally Excel into dbo.Acc_Trans_All.
    Executes the exact database mapping from Rpt_Tally_Upload.aspx.cs.
    """
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx Excel files are supported for Tally upload.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    return TallyService.ingest_tally_workbook(
        file_bytes=file_bytes,
        db2=db2,
        c_code=c_code,
        l_code=l_code,
        user_id=user_id,
        user_name=user_name,
    )


@router.get("/transactions", status_code=status.HTTP_200_OK)
def get_tally_transactions(
    limit: int = Query(default=100, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None, description="Search voucher no or ledger name"),
    voucher_type: Optional[str] = Query(default=None, description="Filter by voucher type (Sales, Receipt, Payment, etc.)"),
    from_date: Optional[str] = Query(default=None, description="From date (YYYY-MM-DD or YYYYMMDD)"),
    to_date: Optional[str] = Query(default=None, description="To date (YYYY-MM-DD or YYYYMMDD)"),
    fin_year: Optional[str] = Query(default=None, description="Financial Year filter"),
    db2: Session = Depends(get_mssql_session("db2")),
):
    """
    Retrieves imported Tally accounting transactions from dbo.Acc_Trans_All.
    """
    return TallyService.get_recent_transactions(
        db2=db2,
        limit=limit,
        offset=skip,
        search=search,
        trans_type=voucher_type,
        from_date=from_date,
        to_date=to_date,
        fin_year=fin_year,
    )


@router.get("/template", status_code=status.HTTP_200_OK)
def download_tally_template():
    """
    Generates and downloads a sample Tally Excel file matching the expected format.
    """
    template_bytes = TallyService.generate_sample_template()
    return Response(
        content=template_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=Tally_Upload_Template.xlsx"
        },
    )
