"""
Pydantic schemas for Sales Invoices (Acc_Sales_Inv_Main, Acc_Sales_Inv_Sub, Acc_GRN_Stock).
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SalesInvoiceItem(BaseModel):
    """Line item in a sales invoice."""
    model_config = ConfigDict(extra="ignore")

    ItemCode: Optional[str] = None
    ProductType: Optional[str] = None
    HSNCode: Optional[str] = None
    Qty: float = 0.0
    Rate: float = 0.0
    ItemValue: float = 0.0
    SerialNo: Optional[str] = None
    GST: Optional[float] = 18.0
    CGST: float = 0.0
    SGST: float = 0.0
    IGST: float = 0.0
    NetAmount: float = 0.0


class SalesInvoiceSerial(BaseModel):
    """Serial number tracking for a sales invoice item."""
    model_config = ConfigDict(extra="ignore")

    ProductType: Optional[str] = None
    HSNCode: Optional[str] = None
    MaterialInventory: Optional[str] = None
    SerialNo: Optional[str] = None


# Backwards compatibility aliases
SalesInvoiceItemBase = SalesInvoiceItem
SalesInvoiceItemCreate = SalesInvoiceItem
SalesInvoiceSerialBase = SalesInvoiceSerial
SalesInvoiceSerialCreate = SalesInvoiceSerial


class SalesInvoiceBase(BaseModel):
    """Header information for a sales invoice."""
    model_config = ConfigDict(extra="ignore")

    TransNo: Optional[str] = None
    TransDate: Optional[str] = None
    InvoiceNo: Optional[str] = None
    InvoiceDate: Optional[str] = None
    CustomerCode: Optional[str] = None
    CustomerName: Optional[str] = None
    GST: Optional[str] = None
    TotalQty: float = 0.0
    TotalItemAmount: float = 0.0
    TotalCGSTAmount: float = 0.0
    TotalSGSTAmount: float = 0.0
    TotalIGSTAmount: float = 0.0
    TotalAmount: float = 0.0
    RoundType: Optional[str] = "None"
    RoundOff: float = 0.0
    FinalNetAmount: Optional[float] = None
    GRN: Optional[str] = None
    Remarks: Optional[str] = None
    ApprovalStatus: Optional[str] = "Pending"
    Items: List[SalesInvoiceItem] = Field(default_factory=list)
    Serials: List[SalesInvoiceSerial] = Field(default_factory=list)


class SalesInvoiceCreate(SalesInvoiceBase):
    pass


class SalesInvoiceUpdate(SalesInvoiceBase):
    pass


class SalesInvoiceApprovalUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ApprovalStatus: str = "Pending"
    ApprovedBy: Optional[str] = "ADMIN"
