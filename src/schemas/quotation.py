"""
Pydantic schemas for Quotations (Acc_Quotation_Main & Acc_Quotation_Sub).
"""

from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QuotationItemBase(BaseModel):
    """Line item in a quotation."""
    model_config = ConfigDict(extra="ignore")

    order_id: Optional[Any] = "1"
    ItemCode: Optional[str] = None
    ProductType: Optional[str] = ""
    Prod_highlight: Optional[str] = ""
    HSNCode: Optional[str] = ""
    UOM: Optional[str] = "Pcs"
    Rate: Optional[float] = 0.0
    Qty: Optional[float] = 1.0
    ItemValue: Optional[float] = 0.0
    GST: Optional[float] = 0.0
    CGST: Optional[float] = 0.0
    SGST: Optional[float] = 0.0
    IGST: Optional[float] = 0.0
    NetAmount: Optional[float] = 0.0
    Service: Optional[str] = "Standard Supply"


class QuotationItemCreate(QuotationItemBase):
    pass


class QuotationBase(BaseModel):
    """Header information for a quotation."""
    model_config = ConfigDict(extra="ignore")

    TransNo: Optional[str] = None
    TransDate: Optional[str] = None
    ProdType: Optional[str] = "1"
    ProductName: Optional[str] = None
    CustomerCode: Optional[str] = None
    CustomerName: Optional[str] = ""
    Narration: Optional[str] = ""
    Purpose: Optional[str] = ""
    TermsAndConditions: Optional[str] = ""
    ApprovalStatus: Optional[str] = "Pending"

    TotalQty: Optional[float] = 0.0
    TotalItemAmount: Optional[float] = 0.0
    TotalCGSTAmount: Optional[float] = 0.0
    TotalSGSTAmount: Optional[float] = 0.0
    TotalIGSTAmount: Optional[float] = 0.0
    TotalAmount: Optional[float] = 0.0
    RoundType: Optional[str] = "None"
    RoundOff: Optional[float] = 0.0
    FinalNetAmount: Optional[float] = 0.0


class QuotationCreate(QuotationBase):
    Items: List[QuotationItemCreate] = Field(default_factory=list)


class QuotationUpdate(QuotationBase):
    Items: List[QuotationItemCreate] = Field(default_factory=list)


class QuotationApprovalUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ApprovalStatus: Optional[str] = "Approved"
    ApprovedBy: Optional[str] = "ADMIN"
