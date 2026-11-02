"""
Pydantic schemas for Delivery Challan (Delivery_main & Delivery_sub).
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DeliveryChallanItemBase(BaseModel):
    """Line item in a delivery challan."""
    model_config = ConfigDict(extra="ignore")

    Item: Optional[str] = ""
    ProductType: Optional[str] = ""
    HSN: Optional[str] = "8543"
    HSNCode: Optional[str] = "8543"
    UOM: Optional[str] = "Pcs"
    Qty: Optional[float] = 1.0
    Rate: Optional[float] = 0.0
    InvoiceTotal: Optional[float] = 0.0
    ItemValue: Optional[float] = 0.0


class DeliveryChallanItemCreate(DeliveryChallanItemBase):
    pass


class DeliveryChallanBase(BaseModel):
    """Header information for a delivery challan."""
    model_config = ConfigDict(extra="ignore")

    Deliveryno: Optional[str] = None
    Deliverydate: Optional[str] = None
    Returntype: Optional[str] = "1"
    TransType: Optional[str] = "Customer"
    Suppliername: Optional[str] = ""
    SupplierInvoice: Optional[str] = ""
    Deliverymode: Optional[str] = "By Road / Courier"
    Supplier_ref_no: Optional[str] = ""
    Supplier_ref_date: Optional[str] = ""
    purpose: Optional[str] = ""

    TotalAmt: Optional[float] = 0.0
    GSTName: Optional[str] = "GST 18%"
    SGST_Per: Optional[float] = 9.0
    SGSTAmt: Optional[float] = 0.0
    CGST_Per: Optional[float] = 9.0
    CGSTAmt: Optional[float] = 0.0
    IGST_Per: Optional[float] = 0.0
    IGSTAmt: Optional[float] = 0.0
    FinalInvoice: Optional[float] = 0.0


class DeliveryChallanCreate(DeliveryChallanBase):
    Items: List[DeliveryChallanItemCreate] = Field(default_factory=list)


class DeliveryChallanUpdate(DeliveryChallanBase):
    Items: List[DeliveryChallanItemCreate] = Field(default_factory=list)
