from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.services.customer_report_service import CustomerReportService
from src.services.customer_report_excel_service import CustomerReportExcelService

router = APIRouter(
    prefix="/customer-report",
    tags=["Transaction - Customer Wise Report"],
)


@router.get("/clients")
def get_customer_clients(
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Search and retrieve customer list from Ledger Master for report autocomplete.
    """
    clients = CustomerReportService.get_client_autocomplete(
        db=db,
        search=search,
        limit=limit,
    )
    return {
        "success": True,
        "count": len(clients),
        "data": clients,
    }


@router.get("/financial-years")
def get_report_financial_years(
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Get all distinct financial years available across transactions and Tally.
    """
    years = CustomerReportService.get_available_fin_years(db=db)
    return {
        "success": True,
        "data": years,
    }


@router.get("/portfolio-summary")
def get_customer_portfolio_summary(
    fin_year: Optional[str] = Query(default="ALL"),
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Industry & Portfolio-level Client Financial Analytics for Customer 360 Dashboard:
    Total clients, overall turnover, collections, TDS, and top outstanding clients.
    """
    return {
        "success": True,
        "data": CustomerReportService.get_portfolio_summary(
            db=db,
            fin_year=fin_year,
        ),
    }


@router.get("/dossier/{client_code:path}")
def get_customer_dossier_by_path(
    client_code: str,
    fin_year: Optional[str] = Query(default="ALL"),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    from_month: Optional[str] = Query(default=None),
    to_month: Optional[str] = Query(default=None),
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Comprehensive Customer 360 Dossier:
    Includes Customer Master KYC, Quotes, Proformas, Invoices, Tally Receipts,
    Percentage Milestone Tracking, and Running Ledger with date/month range filtering.
    """
    return CustomerReportService.get_customer_dossier(
        db=db,
        client_code=client_code,
        fin_year=fin_year,
        from_date=from_date,
        to_date=to_date,
        from_month=from_month,
        to_month=to_month,
    )


@router.get("/dossier")
def get_customer_dossier_by_query(
    client_code: str = Query(...),
    fin_year: Optional[str] = Query(default="ALL"),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    from_month: Optional[str] = Query(default=None),
    to_month: Optional[str] = Query(default=None),
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Query parameter variant for customer dossier.
    """
    return CustomerReportService.get_customer_dossier(
        db=db,
        client_code=client_code,
        fin_year=fin_year,
        from_date=from_date,
        to_date=to_date,
        from_month=from_month,
        to_month=to_month,
    )


@router.get("/export-excel/{client_code:path}")
@router.get("/{client_code:path}/export-excel")
def export_customer_dossier_excel(
    client_code: str,
    fin_year: Optional[str] = Query(default="ALL"),
    tab: Optional[str] = Query(default="ALL"),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    from_month: Optional[str] = Query(default=None),
    to_month: Optional[str] = Query(default=None),
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Exports the comprehensive Customer 360 Report & Ledger Dossier as an Executive Excel Workbook (.xlsx).
    Includes Summary & KYC, Sales Invoices & Settlement, Advance Milestones, Statement of Account, and Receipts.
    """
    excel_stream = CustomerReportExcelService.generate_excel(
        db=db,
        client_code=client_code,
        fin_year=fin_year,
        tab=tab,
        from_date=from_date,
        to_date=to_date,
        from_month=from_month,
        to_month=to_month,
    )
    safe_code = client_code.replace("/", "_").replace("\\", "_").replace(" ", "_").strip()
    safe_fy = (fin_year or "ALL").replace("/", "_").replace("\\", "_").replace(" ", "_").strip()
    month_suffix = ""
    if from_month and to_month:
        safe_fm = str(from_month).replace("/", "_").replace("-", "").strip()
        safe_tm = str(to_month).replace("/", "_").replace("-", "").strip()
        month_suffix = f"_{safe_fm}_to_{safe_tm}"
    filename = f"Customer_Dossier_{safe_code}_{safe_fy}{month_suffix}.xlsx"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )

