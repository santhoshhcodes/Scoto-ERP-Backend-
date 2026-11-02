"""
Pydantic schemas for Item Master and Ledger Master.
"""

from typing import Optional
from pydantic import BaseModel, Field


# ==========================================
# Item Master Schemas
# ==========================================

class ItemBase(BaseModel):
    ProductType: str = Field(..., examples=["ESSL"])
    ItemCode: str = Field(..., examples=["ITM-8001"])
    ItemDescription: str = Field(..., examples=["eSSL Face Attendance Terminal uFace 800"])
    ItemType: str = Field(..., examples=["Face Recognition Terminal"])
    HSNCode: str = Field(..., examples=["8543"])
    UOM: str = Field(..., examples=["Pcs"])
    SerialNo: str = Field(default="YES", examples=["YES"])
    Status: str = Field(default="ACTIVE")


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    ProductType: Optional[str] = None
    ItemDescription: Optional[str] = None
    ItemType: Optional[str] = None
    HSNCode: Optional[str] = None
    UOM: Optional[str] = None
    SerialNo: Optional[str] = None
    Status: Optional[str] = None


# ==========================================
# Ledger Master Schemas
# ==========================================

class LedgerBase(BaseModel):
    LedgerType: str = Field(default="Supplier", examples=["Supplier"])
    LedgerCode: str = Field(..., examples=["SUP-1001"])
    LedgerName: str = Field(..., examples=["eSSL Security Systems India Pvt Ltd"])
    ChequePrintName: Optional[str] = None
    Ledger_Class: Optional[str] = "Pvt Company"
    Region: Optional[str] = "Domestic"
    AccLedgerHeaderName: Optional[str] = "Liabilities"
    AccGroupName: Optional[str] = "Sundry Creditors (Suppliers & Vendors)"
    AccSubGroupName: Optional[str] = None
    CostCenter: Optional[str] = "Cost Centre"

    # Address & Contact
    HouseNo: Optional[str] = None
    Add1: Optional[str] = None
    Add2: Optional[str] = None
    Area: Optional[str] = None
    City: Optional[str] = None
    PinCode: Optional[str] = None
    State: Optional[str] = None
    Country: Optional[str] = "India"
    MobileNo: Optional[str] = None
    TelNo: Optional[str] = None
    ContectName: Optional[str] = None
    ContectNo: Optional[str] = None
    MailID: Optional[str] = None
    WebSite: Optional[str] = None

    # Bank Details
    BankName: Optional[str] = None
    AccountNo: Optional[str] = None
    BranchName: Optional[str] = None
    Branch_Addr: Optional[str] = None
    IFSCCode: Optional[str] = None
    SWIFTCode: Optional[str] = None
    IBANCode: Optional[str] = None

    # Statutory & Tax
    GSTNo: Optional[str] = None
    PanNo: Optional[str] = None
    TanNo: Optional[str] = None
    CINNo: Optional[str] = None
    IECode: Optional[str] = None
    LEICode: Optional[str] = None
    MSME_Status: Optional[str] = "2"
    MSME_No: Optional[str] = None
    PaymentDays: Optional[str] = "30"

    # Balances & Status
    OpeningBalance: Optional[str] = "0.00"
    BalanceType: Optional[str] = "Cr"
    Status: str = Field(default="ACTIVE")


class LedgerCreate(LedgerBase):
    pass


class LedgerUpdate(BaseModel):
    LedgerType: Optional[str] = None
    LedgerName: Optional[str] = None
    ChequePrintName: Optional[str] = None
    Ledger_Class: Optional[str] = None
    Region: Optional[str] = None
    AccLedgerHeaderName: Optional[str] = None
    AccGroupName: Optional[str] = None
    AccSubGroupName: Optional[str] = None
    CostCenter: Optional[str] = None
    HouseNo: Optional[str] = None
    Add1: Optional[str] = None
    Add2: Optional[str] = None
    Area: Optional[str] = None
    City: Optional[str] = None
    PinCode: Optional[str] = None
    State: Optional[str] = None
    Country: Optional[str] = None
    MobileNo: Optional[str] = None
    TelNo: Optional[str] = None
    ContectName: Optional[str] = None
    ContectNo: Optional[str] = None
    MailID: Optional[str] = None
    WebSite: Optional[str] = None
    BankName: Optional[str] = None
    AccountNo: Optional[str] = None
    BranchName: Optional[str] = None
    Branch_Addr: Optional[str] = None
    IFSCCode: Optional[str] = None
    SWIFTCode: Optional[str] = None
    IBANCode: Optional[str] = None
    GSTNo: Optional[str] = None
    PanNo: Optional[str] = None
    TanNo: Optional[str] = None
    CINNo: Optional[str] = None
    IECode: Optional[str] = None
    LEICode: Optional[str] = None
    MSME_Status: Optional[str] = None
    MSME_No: Optional[str] = None
    PaymentDays: Optional[str] = None
    OpeningBalance: Optional[str] = None
    BalanceType: Optional[str] = None
    Status: Optional[str] = None


__all__ = [
    "ItemBase",
    "ItemCreate",
    "ItemUpdate",
    "LedgerBase",
    "LedgerCreate",
    "LedgerUpdate",
]