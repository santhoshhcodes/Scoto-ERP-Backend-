"""
Transaction Domain Aggregator Schema.
Re-exports Quotation, Proforma, Delivery Challan, and Sales Invoice schemas.
Allows unified imports from `src.schemas.transaction` while keeping schemas modular.
"""

from src.schemas.delivery_challan import (
    DeliveryChallanBase,
    DeliveryChallanCreate,
    DeliveryChallanItemBase,
    DeliveryChallanItemCreate,
    DeliveryChallanUpdate,
)
from src.schemas.proforma import (
    ProformaApprovalUpdate,
    ProformaBase,
    ProformaCreate,
    ProformaItemBase,
    ProformaItemCreate,
    ProformaUpdate,
)
from src.schemas.quotation import (
    QuotationApprovalUpdate,
    QuotationBase,
    QuotationCreate,
    QuotationItemBase,
    QuotationItemCreate,
    QuotationUpdate,
)
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

__all__ = [
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
]
