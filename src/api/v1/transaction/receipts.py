"""
API router for Customer Receipts & Advance Payments.
Provides endpoints for recording receipts, listing transactions, fetching open invoices/quotations,
and bank deposit account options.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.schemas.receipt import (
    CustomerReceiptCreate,
    CustomerReceiptResponse,
)
from src.services.receipt_service import ReceiptService

router = APIRouter(prefix="/receipts", tags=["Transaction - Customer Receipts & Advances"])


@router.get("", summary="List Customer Receipts")
def list_customer_receipts(
    search: Optional[str] = Query(default=None, description="Search across Voucher No, Customer, UTR, Remarks"),
    customer_code: Optional[str] = Query(default=None, description="Filter by customer code or name"),
    fin_year: Optional[str] = Query(default=None, description="Financial Year, e.g. '2026_2027' or 'ALL'"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Returns a paginated list of recorded customer receipts and advances.
    """
    return ReceiptService.get_customer_receipts(
        db=db,
        search=search,
        customer_code=customer_code,
        fin_year=fin_year,
        limit=limit,
        offset=offset,
    )


@router.get("/deposit-accounts", summary="Get Available Bank & Cash Deposit Accounts")
def get_deposit_accounts(
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Returns Scoto's company bank accounts and cash ledgers for receiving customer payments.
    """
    return ReceiptService.get_deposit_accounts(db)


@router.get("/open-documents", summary="Get Open Documents by Query Param")
def get_open_documents_by_query(
    customer_code: str = Query(default=""),
    customer_name: Optional[str] = Query(default=None),
    db: Session = Depends(get_mssql_session("db2")),
):
    return ReceiptService.get_open_documents_for_customer(
        db=db,
        customer_code=customer_code,
        customer_name=customer_name,
    )


@router.get("/open-documents/{customer_code:path}", summary="Get Open Documents for Customer Allocation")
def get_open_documents_for_customer(
    customer_code: str,
    customer_name: Optional[str] = Query(default=None),
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Fetches open Sales Invoices, Proformas, and Quotations for a customer with amounts paid and balance due.
    """
    return ReceiptService.get_open_documents_for_customer(
        db=db,
        customer_code=customer_code,
        customer_name=customer_name,
    )


@router.post("", summary="Record Customer Receipt / Advance", status_code=status.HTTP_201_CREATED)
def create_customer_receipt(
    payload: CustomerReceiptCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Records a new customer advance or invoice settlement.
    Atomically updates Acc_Receipts_Main, Acc_Receipts_Sub, and writes balanced double-entries to Acc_Trans_All.
    """
    return ReceiptService.create_customer_receipt(
        db=db,
        payload=payload,
        user="ADMIN",
    )


@router.get("/{trans_no:path}", summary="Get Single Receipt Details")
def get_receipt_details(
    trans_no: str,
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Returns header details, document allocations, and general ledger postings for a receipt voucher.
    """
    return ReceiptService.get_receipt_details(db, trans_no)


@router.delete("/{trans_no:path}", summary="Void / Reverse Receipt")
def void_customer_receipt(
    trans_no: str,
    reason: Optional[str] = Query(default="Voided by user", description="Reason for cancellation"),
    db: Session = Depends(get_mssql_session("db2")),
):
    """
    Safely voids a receipt and reverses its accounting ledger postings.
    """
    return ReceiptService.void_customer_receipt(
        db=db,
        trans_no=trans_no,
        reason=reason,
        user="ADMIN",
    )

