"""
Pydantic schemas for Proforma Invoices (Acc_Proforma_Inv_Main & Acc_Proforma_Inv_Sub).
"""

from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProformaItemBase(BaseModel):
    """Line item in a proforma invoice."""
    model_config = ConfigDict(extra="ignore")

    order_id: Optional[Any] = "1"
    ItemCode: Optional[str] = None
    ProductType: Optional[str] = ""
    Prod_highlight: Optional[str] = ""
    HSNCode: Optional[str] = ""
    UOM: Optional[str] = "Pcs"
    Qty: Optional[float] = 1.0
    Rate: Optional[float] = 0.0
    ItemValue: Optional[float] = 0.0
    GST: Optional[float] = 0.0
    CGST: Optional[float] = 0.0
    SGST: Optional[float] = 0.0
    IGST: Optional[float] = 0.0
    NetAmount: Optional[float] = 0.0
    Service: Optional[str] = "Supply & Installation"


class ProformaItemCreate(ProformaItemBase):
    pass


class ProformaBase(BaseModel):
    """Header information for a proforma invoice."""
    model_config = ConfigDict(extra="ignore")

    TransNo: Optional[str] = None
    TransDate: Optional[str] = None
    QuotationNo: Optional[str] = None
    QuotationDate: Optional[str] = None
    CustomerCode: Optional[str] = None
    CustomerName: Optional[str] = ""
    Remarks: Optional[str] = ""
    ApprovalStatus: Optional[str] = "Pending"
    ProdType: Optional[str] = "1"
    ProductName: Optional[str] = None
    Narration: Optional[str] = ""
    Purpose: Optional[str] = ""
    TermsAndConditions: Optional[str] = ""

    TotalQty: Optional[float] = 0.0
    TotalItemAmount: Optional[float] = 0.0
    TotalCGSTAmount: Optional[float] = 0.0
    TotalSGSTAmount: Optional[float] = 0.0
    TotalIGSTAmount: Optional[float] = 0.0
    TotalAmount: Optional[float] = 0.0
    RoundType: Optional[str] = "None"
    RoundOff: Optional[float] = 0.0
    FinalNetAmount: Optional[float] = 0.0


class ProformaCreate(ProformaBase):
    Items: List[ProformaItemCreate] = Field(default_factory=list)


class ProformaUpdate(ProformaBase):
    Items: List[ProformaItemCreate] = Field(default_factory=list)


class ProformaApprovalUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ApprovalStatus: Optional[str] = "Approved"
    ApprovedBy: Optional[str] = "ADMIN"
