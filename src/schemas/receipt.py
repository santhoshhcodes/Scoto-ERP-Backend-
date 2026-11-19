"""
Pydantic schemas for Customer Receipts & Advances.
Maps to Acc_Receipts_Main, Acc_Receipts_Sub, and Acc_Trans_All.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReceiptAllocationItem(BaseModel):
    """Line item allocation for a receipt against an Invoice, Proforma, or Quotation."""
    model_config = ConfigDict(extra="ignore")

    DocType: str = Field(
        default="SALES_INVOICE",
        description="Type of linked document: 'SALES_INVOICE', 'PROFORMA', 'QUOTATION', or 'ON_ACCOUNT'",
    )
    DocNo: str = Field(
        ...,
        description="Reference document number (e.g. SINV/26-27/00009, PI-2026-014, QT/25-26/00049)",
    )
    DocDate: Optional[str] = Field(default="", description="Date of document")
    SecondaryDocNo: Optional[str] = Field(default="", description="Secondary reference like QuotationNo or InvoiceNo")
    TotalDocAmount: float = Field(default=0.0, description="Gross total value of document")
    AlreadyPaid: float = Field(default=0.0, description="Amount already paid/settled so far")
    AllocatedAmount: float = Field(..., description="Gross amount allocated/settled in this receipt")
    TDSPercentage: float = Field(default=0.0, description="TDS percentage deducted by customer")
    TDSAmount: float = Field(default=0.0, description="TDS amount deducted for this line")
    LineTotal: float = Field(default=0.0, description="Net received amount for this line (Allocated - TDS)")
    Remarks: Optional[str] = Field(default="", description="Line remarks")

    # Item & Tax Breakdown Fields
    ItemDescription: Optional[str] = Field(default="", description="Product or service description")
    TaxableAmount: float = Field(default=0.0, description="Taxable value")
    GSTPercentage: float = Field(default=0.0, description="GST %")
    CGSTPercentage: float = Field(default=0.0, description="CGST %")
    CGSTAmount: float = Field(default=0.0, description="CGST ₹")
    SGSTPercentage: float = Field(default=0.0, description="SGST %")
    SGSTAmount: float = Field(default=0.0, description="SGST ₹")
    IGSTPercentage: float = Field(default=0.0, description="IGST %")
    IGSTAmount: float = Field(default=0.0, description="IGST ₹")
    TotalGSTAmount: float = Field(default=0.0, description="Total GST ₹")


class CustomerReceiptCreate(BaseModel):
    """Payload to record a customer receipt or advance."""
    model_config = ConfigDict(extra="ignore")

    CCode: Optional[str] = Field(default="SCT", description="Company Code")
    LCode: Optional[str] = Field(default="UNIT I", description="Location Code")
    FinYearVal: Optional[str] = Field(default=None, description="e.g. '2026_2027'")
    ReceiptDate: str = Field(..., description="Date of payment (YYYY-MM-DD or DD/MM/YYYY)")
    ReceiptType: str = Field(
        default="Invoice Settlement",
        description="Category: 'Advance against Quotation', 'Advance against Proforma', 'Invoice Settlement', 'On Account'",
    )
    CustomerCode: str = Field(..., description="Customer Ledger Code or SuppCode")
    CustomerName: str = Field(..., description="Customer Name as displayed")

    # Deposit Account (Scoto's Bank or Cash)
    DepositGLCode: str = Field(..., description="General Ledger Code of Bank/Cash, e.g. 'GL/00077'")
    DepositAccountName: Optional[str] = Field(default="", description="e.g. 'HSBC - CA - 073-500266-001'")
    BankName: Optional[str] = Field(default="HSBC", description="Bank name")
    BankBranch: Optional[str] = Field(default="", description="Bank branch")
    AccountNo: Optional[str] = Field(default="", description="Bank account number")

    # Payment details
    PayMode: str = Field(default="NEFT/RTGS", description="'NEFT/RTGS', 'IMPS/UPI', 'Cheque', 'Cash', 'OnLine'")
    RefNo: Optional[str] = Field(default="", description="UTR Number / Cheque Number / Transaction Reference")
    RefDate: Optional[str] = Field(default="", description="Date of UTR / Cheque")

    # Financial breakdown
    GrossAmount: float = Field(..., description="Total settlement amount (credited to customer)")
    TDSAmount: float = Field(default=0.0, description="TDS deducted by customer")
    TDSPercentage: float = Field(default=0.0, description="TDS percentage")
    TDSSection: Optional[str] = Field(default="194C", description="TDS Section: '194C', '194J', etc.")
    TotGSTAmt: float = Field(default=0.0, description="Total GST amount across allocated documents")
    NetAmount: float = Field(..., description="Net money credited to bank (GrossAmount - TDSAmount)")
    Remarks: Optional[str] = Field(default="", description="General notes / transaction narration")

    # Allocated documents
    Allocations: List[ReceiptAllocationItem] = Field(default_factory=list, description="Documents settled by this receipt")


class CustomerReceiptResponse(BaseModel):
    """Summary response of a recorded receipt."""
    model_config = ConfigDict(extra="ignore")

    TransNo: str
    TransDate: str
    CustomerCode: Optional[str] = None
    CustomerName: Optional[str] = None
    ReceiptType: Optional[str] = None
    BankName: Optional[str] = None
    DepositGLCode: Optional[str] = None
    PayMode: Optional[str] = None
    RefNo: Optional[str] = None
    GrossAmount: float = 0.0
    TDSAmount: float = 0.0
    NetAmount: float = 0.0
    Remarks: Optional[str] = None
    Status: Optional[str] = "Add"
    CreatedOn: Optional[str] = None
    AllocationsCount: int = 0

