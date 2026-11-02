"""
Centralized API v1 Router.
Aggregates all domain endpoints under the /api/v1 prefix.
"""

from fastapi import APIRouter

from src.api.v1.attendance import router as attendance_router
from src.api.v1.attendance_adjustments import router as attendance_adjustments_router
from src.api.v1.endpoints.auth import router as auth_router
from src.api.v1.endpoints.employees import router as employee_router
from src.api.v1.endpoints.essl_adms import router as essl_adms_router
from src.api.v1.masters.itemmaster import router as item_router
from src.api.v1.masters.ledger import router as ledger_router
from src.api.v1.expense.office_daily_expense import router as office_daily_expense_router
from src.api.v1.expense.office_expense import router as office_expense_router
from src.api.v1.transaction.delivery_challan import router as delivery_router
from src.api.v1.transaction.proforma import router as proforma_router
from src.api.v1.transaction.quotation import router as quotation_router
from src.api.v1.transaction.sales_invoices import router as sales_invoice_router
from src.api.v1.transaction.tally_upload import router as tally_router
from src.api.v1.transaction.customer_report import router as customer_report_router
from src.api.v1.expense.travel_expense import router as travel_expense_router

api_router = APIRouter()

# Authentication & Users
api_router.include_router(auth_router)

# Employee Master
api_router.include_router(employee_router, prefix="/employee")

# Attendance Management & Reconciliation
api_router.include_router(attendance_router)
api_router.include_router(attendance_adjustments_router)

# Master Data (Items & Ledgers)
api_router.include_router(item_router, prefix="/master")
api_router.include_router(ledger_router, prefix="/master")

# Transactions (Quotations, Proformas, Delivery Challans, Invoices, Tally)
api_router.include_router(quotation_router, prefix="/transaction")
api_router.include_router(proforma_router, prefix="/transaction")
api_router.include_router(delivery_router, prefix="/transaction")
api_router.include_router(sales_invoice_router, prefix="/transaction")
api_router.include_router(tally_router, prefix="/transaction")
api_router.include_router(customer_report_router, prefix="/transaction")

# Office Expenses & Petty Cash Ledger
api_router.include_router(office_expense_router, prefix="/office-expenses")
api_router.include_router(office_daily_expense_router, prefix="/office-expenses")
api_router.include_router(travel_expense_router, prefix="/travel-expenses")

# ESSL Biometrics Device Logs
api_router.include_router(essl_adms_router, prefix="/essl_adms")

__all__ = [
    "api_router",
    "auth_router",
    "employee_router",
    "attendance_router",
    "attendance_adjustments_router",
    "item_router",
    "ledger_router",
    "quotation_router",
    "proforma_router",
    "delivery_router",
    "sales_invoice_router",
    "tally_router",
    "customer_report_router",
    "office_expense_router",
    "office_daily_expense_router",
    "essl_adms_router",
]
