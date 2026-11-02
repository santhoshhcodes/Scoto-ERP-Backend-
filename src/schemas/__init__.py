"""
Schemas Package for Scoto Backend.
Central export point for all domain Pydantic models.
Enables clean imports like:
    `from src.schemas import LoginRequest, EmployeeCreate, QuotationCreate, ...`
"""

# Common
from src.schemas.common import (
    DateRangeFilter,
    DropdownOption,
    PaginatedResponse,
    PaginationMeta,
    StandardResponse,
)

# Authentication
from src.schemas.auth import (
    AuthMetaResponse,
    LoginRequest,
    LoginResponse,
    UserProfile,
)

# Employees
from src.schemas.employee import (
    EmployeeBase,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeShort,
    EmployeeUpdate,
)

# Attendance & Leave
from src.schemas.attendance import (
    ApprovalDecision,
    DailyAttendanceSummaryRecord,
    DailyReconciliationRecord,
    DailyReviewUpsert,
    DayStatusEnum,
    LateFineUpsert,
    LeaveCreate,
    MonthlyAttendanceDayLog,
    MonthlyEmployeeReport,
    MonthlyLateFineRecord,
    MonthlySummaryResponse,
    PermissionCreate,
)

# Master (Item & Ledger)
from src.schemas.master import (
    ItemBase,
    ItemCreate,
    ItemUpdate,
    LedgerBase,
    LedgerCreate,
    LedgerUpdate,
)

# Quotations
from src.schemas.quotation import (
    QuotationApprovalUpdate,
    QuotationBase,
    QuotationCreate,
    QuotationItemBase,
    QuotationItemCreate,
    QuotationUpdate,
)

# Proforma Invoices
from src.schemas.proforma import (
    ProformaApprovalUpdate,
    ProformaBase,
    ProformaCreate,
    ProformaItemBase,
    ProformaItemCreate,
    ProformaUpdate,
)

# Delivery Challan
from src.schemas.delivery_challan import (
    DeliveryChallanBase,
    DeliveryChallanCreate,
    DeliveryChallanItemBase,
    DeliveryChallanItemCreate,
    DeliveryChallanUpdate,
)

# Sales Invoice
from src.schemas.sales_invoice import (
    SalesInvoiceApprovalUpdate,
    SalesInvoiceBase,
    SalesInvoiceCreate,
    SalesInvoiceItem,
    SalesInvoiceItemBase,
    SalesInvoiceItemCreate,
    SalesInvoiceSerial,
    SalesInvoiceSerialBase,
    SalesInvoiceSerialCreate,
    SalesInvoiceUpdate,
)

# Office Expenses & Petty Cash
from src.schemas.office_expense import (
    BatchExpenseCreate,
    FundCreate,
    MoneyReceivedCreate,
    OfficeExpenseCreate,
    OfficeTransactionResponse,
    SettlementCreate,
)

# Daily Office Expenses
from src.schemas.office_daily_expense import (
    DailyItemCreate,
    DailyItemUpdate,
    DailyQuantityInput,
    DailyUsageSave,
)

# ESSL Biometrics
from src.schemas.essl_adms import ESSLAttendancePunch

__all__ = [
    # Common
    "DropdownOption",
    "PaginationMeta",
    "PaginatedResponse",
    "StandardResponse",
    "DateRangeFilter",
    # Auth
    "LoginRequest",
    "LoginResponse",
    "UserProfile",
    "AuthMetaResponse",
    # Employee
    "EmployeeBase",
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeResponse",
    "EmployeeShort",
    # Attendance
    "DayStatusEnum",
    "DailyReconciliationRecord",
    "MonthlyAttendanceDayLog",
    "MonthlyEmployeeReport",
    "MonthlySummaryResponse",
    "DailyAttendanceSummaryRecord",
    "PermissionCreate",
    "ApprovalDecision",
    "LeaveCreate",
    "DailyReviewUpsert",
    "LateFineUpsert",
    "MonthlyLateFineRecord",
    # Master
    "ItemBase",
    "ItemCreate",
    "ItemUpdate",
    "LedgerBase",
    "LedgerCreate",
    "LedgerUpdate",
    # Quotation
    "QuotationItemBase",
    "QuotationItemCreate",
    "QuotationBase",
    "QuotationCreate",
    "QuotationUpdate",
    "QuotationApprovalUpdate",
    # Proforma
    "ProformaItemBase",
    "ProformaItemCreate",
    "ProformaBase",
    "ProformaCreate",
    "ProformaUpdate",
    "ProformaApprovalUpdate",
    # Delivery Challan
    "DeliveryChallanItemBase",
    "DeliveryChallanItemCreate",
    "DeliveryChallanBase",
    "DeliveryChallanCreate",
    "DeliveryChallanUpdate",
    # Sales Invoice
    "SalesInvoiceItem",
    "SalesInvoiceItemBase",
    "SalesInvoiceItemCreate",
    "SalesInvoiceSerial",
    "SalesInvoiceSerialBase",
    "SalesInvoiceSerialCreate",
    "SalesInvoiceBase",
    "SalesInvoiceCreate",
    "SalesInvoiceUpdate",
    "SalesInvoiceApprovalUpdate",
    # Office Expenses
    "FundCreate",
    "MoneyReceivedCreate",
    "OfficeExpenseCreate",
    "BatchExpenseCreate",
    "OfficeTransactionResponse",
    "SettlementCreate",
    # Daily Office Expenses
    "DailyItemCreate",
    "DailyItemUpdate",
    "DailyQuantityInput",
    "DailyUsageSave",
    # ESSL Biometrics
    "ESSLAttendancePunch",
]
