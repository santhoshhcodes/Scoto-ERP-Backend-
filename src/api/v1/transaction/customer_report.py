from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.services.customer_report_service import CustomerReportService

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


@router.get("/dossier/{client_code:path}")
def get_customer_dossier_by_path(
    client_code: str,
    fin_year: Optional[str] = Query(default="ALL"),
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Comprehensive Customer 360 Dossier:
    Includes Customer Master KYC, Quotes, Proformas, Invoices, Tally Receipts,
    Percentage Milestone Tracking, and Running Ledger.
    """
    return CustomerReportService.get_customer_dossier(
        db=db,
        client_code=client_code,
        fin_year=fin_year,
    )


@router.get("/dossier")
def get_customer_dossier_by_query(
    client_code: str = Query(...),
    fin_year: Optional[str] = Query(default="ALL"),
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Query parameter variant for customer dossier.
    """
    return CustomerReportService.get_customer_dossier(
        db=db,
        client_code=client_code,
        fin_year=fin_year,
    )

