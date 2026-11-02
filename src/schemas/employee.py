from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EmployeeBase(BaseModel):
    # Personal details
    FirstName: str = Field(min_length=1, max_length=100)
    MiddleName: Optional[str] = Field(default=None, max_length=100)
    LastName: Optional[str] = Field(default=None, max_length=100)
    DisplayName: Optional[str] = Field(default=None, max_length=250)
    ProfilePhotoPath: Optional[str] = Field(default=None, max_length=500)

    DateOfBirth: Optional[date] = None
    Gender: Optional[str] = Field(default=None, max_length=20)
    BloodGroup: Optional[str] = Field(default=None, max_length=5)
    MaritalStatus: Optional[str] = Field(default=None, max_length=20)
    Nationality: Optional[str] = Field(default="Indian", max_length=50)

    # Contact details
    MobileNumber: Optional[str] = Field(default=None, max_length=20)
    AlternateMobileNumber: Optional[str] = Field(default=None, max_length=20)
    Email: Optional[str] = Field(default=None, max_length=254)

    # Address details
    AddressLine1: Optional[str] = Field(default=None, max_length=250)
    AddressLine2: Optional[str] = Field(default=None, max_length=250)
    City: Optional[str] = Field(default=None, max_length=100)
    District: Optional[str] = Field(default=None, max_length=100)
    State: Optional[str] = Field(default=None, max_length=100)
    PostalCode: Optional[str] = Field(default=None, max_length=15)
    Country: Optional[str] = Field(default="India", max_length=100)

    # Family and emergency contact
    FatherName: Optional[str] = Field(default=None, max_length=200)
    FatherMobileNumber: Optional[str] = Field(default=None, max_length=20)
    MotherName: Optional[str] = Field(default=None, max_length=200)
    MotherMobileNumber: Optional[str] = Field(default=None, max_length=20)
    EmergencyContactName: Optional[str] = Field(default=None, max_length=200)
    EmergencyContactNumber: Optional[str] = Field(default=None, max_length=20)
    EmergencyContactRelation: Optional[str] = Field(default=None, max_length=50)

    # Employment details
    DateOfJoining: Optional[date] = None
    DateOfLeaving: Optional[date] = None
    EmploymentType: Optional[str] = Field(default="FULL_TIME", max_length=30)
    EmploymentStatus: Optional[str] = Field(default="ACTIVE", max_length=30)

    CompanyCode: Optional[str] = Field(default=None, max_length=20)
    CompanyName: Optional[str] = Field(default=None, max_length=150)
    LocationCode: Optional[str] = Field(default=None, max_length=50)
    LocationName: Optional[str] = Field(default=None, max_length=150)

    DepartmentId: Optional[int] = None
    DepartmentName: Optional[str] = Field(default=None, max_length=100)
    DesignationId: Optional[int] = None
    DesignationName: Optional[str] = Field(default=None, max_length=100)
    JobTitle: Optional[str] = Field(default=None, max_length=100)
    ReportingManagerCode: Optional[str] = Field(default=None, max_length=50)

    # ERP access
    AppRole: Optional[str] = Field(default=None, max_length=30)
    IsAppUser: Optional[bool] = False
    IsOnSite: Optional[bool] = False
    IsOnField: Optional[bool] = None

    # Bank details (Sensitive)
    BankName: Optional[str] = Field(default=None, max_length=150)
    BankBranch: Optional[str] = Field(default=None, max_length=150)
    AccountHolderName: Optional[str] = Field(default=None, max_length=200)
    AccountNumber: Optional[str] = Field(default=None, max_length=50)
    IFSCCode: Optional[str] = Field(default=None, max_length=20)
    AccountType: Optional[str] = Field(default="SAVINGS", max_length=30)

    # Statutory details (Sensitive)
    AadhaarNumber: Optional[str] = Field(default=None, max_length=12)
    PANNumber: Optional[str] = Field(default=None, max_length=10)
    PFApplicable: Optional[bool] = False
    PFUAN: Optional[str] = Field(default=None, max_length=30)
    PFNumber: Optional[str] = Field(default=None, max_length=50)
    PFJoiningDate: Optional[date] = None
    ESIApplicable: Optional[bool] = False
    ESINumber: Optional[str] = Field(default=None, max_length=30)

    # Salary details (Sensitive)
    SalaryGrade: Optional[str] = Field(default=None, max_length=30)
    PayFrequency: Optional[str] = Field(default="MONTHLY", max_length=20)
    SalaryEffectiveFrom: Optional[date] = None
    BasicSalary: Optional[Decimal] = None
    HRA: Optional[Decimal] = None
    DA: Optional[Decimal] = None
    OtherAllowances: Optional[Decimal] = None
    GrossSalary: Optional[Decimal] = None
    EmployeePFContribution: Optional[Decimal] = None
    EmployerPFContribution: Optional[Decimal] = None
    EmployeeESIContribution: Optional[Decimal] = None
    EmployerESIContribution: Optional[Decimal] = None
    ProfessionalTax: Optional[Decimal] = None
    OtherDeductions: Optional[Decimal] = None
    NetSalary: Optional[Decimal] = None
    PreviousGrossSalary: Optional[Decimal] = None
    LastSalaryRevisionDate: Optional[date] = None
    SalaryRemarks: Optional[str] = Field(default=None, max_length=500)

    # Notes
    Notes: Optional[str] = Field(default=None, max_length=1000)


class EmployeeCreate(EmployeeBase):
    EmployeeCode: str = Field(min_length=1, max_length=50)


class EmployeeUpdate(BaseModel):
    # Protected system identifiers (validated by backend service; cannot be changed)
    EmployeeId: Optional[int] = None
    EmployeeCode: Optional[str] = None
    EmployeeSource: Optional[str] = None
    ESSLEmployeeCode: Optional[str] = None
    ESSLStatus: Optional[str] = None
    ESSLSyncedAt: Optional[datetime] = None
    CreatedBy: Optional[str] = None
    CreatedAt: Optional[datetime] = None
    UpdatedBy: Optional[str] = None
    UpdatedAt: Optional[datetime] = None

    # Personal details
    FirstName: Optional[str] = Field(default=None, min_length=1, max_length=100)
    MiddleName: Optional[str] = Field(default=None, max_length=100)
    LastName: Optional[str] = Field(default=None, max_length=100)
    DisplayName: Optional[str] = Field(default=None, max_length=250)
    ProfilePhotoPath: Optional[str] = Field(default=None, max_length=500)

    DateOfBirth: Optional[date] = None
    Gender: Optional[str] = Field(default=None, max_length=20)
    BloodGroup: Optional[str] = Field(default=None, max_length=5)
    MaritalStatus: Optional[str] = Field(default=None, max_length=20)
    Nationality: Optional[str] = Field(default=None, max_length=50)

    # Contact details
    MobileNumber: Optional[str] = Field(default=None, max_length=20)
    AlternateMobileNumber: Optional[str] = Field(default=None, max_length=20)
    Email: Optional[str] = Field(default=None, max_length=254)

    # Address details
    AddressLine1: Optional[str] = Field(default=None, max_length=250)
    AddressLine2: Optional[str] = Field(default=None, max_length=250)
    City: Optional[str] = Field(default=None, max_length=100)
    District: Optional[str] = Field(default=None, max_length=100)
    State: Optional[str] = Field(default=None, max_length=100)
    PostalCode: Optional[str] = Field(default=None, max_length=15)
    Country: Optional[str] = Field(default=None, max_length=100)

    # Family and emergency contact
    FatherName: Optional[str] = Field(default=None, max_length=200)
    FatherMobileNumber: Optional[str] = Field(default=None, max_length=20)
    MotherName: Optional[str] = Field(default=None, max_length=200)
    MotherMobileNumber: Optional[str] = Field(default=None, max_length=20)
    EmergencyContactName: Optional[str] = Field(default=None, max_length=200)
    EmergencyContactNumber: Optional[str] = Field(default=None, max_length=20)
    EmergencyContactRelation: Optional[str] = Field(default=None, max_length=50)

    # Employment details
    DateOfJoining: Optional[date] = None
    DateOfLeaving: Optional[date] = None
    EmploymentType: Optional[str] = Field(default=None, max_length=30)
    EmploymentStatus: Optional[str] = Field(default=None, max_length=30)

    CompanyCode: Optional[str] = Field(default=None, max_length=20)
    CompanyName: Optional[str] = Field(default=None, max_length=150)
    LocationCode: Optional[str] = Field(default=None, max_length=50)
    LocationName: Optional[str] = Field(default=None, max_length=150)

    DepartmentId: Optional[int] = None
    DepartmentName: Optional[str] = Field(default=None, max_length=100)
    DesignationId: Optional[int] = None
    DesignationName: Optional[str] = Field(default=None, max_length=100)
    JobTitle: Optional[str] = Field(default=None, max_length=100)
    ReportingManagerCode: Optional[str] = Field(default=None, max_length=50)

    # ERP access
    AppRole: Optional[str] = Field(default=None, max_length=30)
    IsAppUser: Optional[bool] = None
    IsActive: Optional[bool] = None

    # Bank details (Sensitive)
    BankName: Optional[str] = Field(default=None, max_length=150)
    BankBranch: Optional[str] = Field(default=None, max_length=150)
    AccountHolderName: Optional[str] = Field(default=None, max_length=200)
    AccountNumber: Optional[str] = Field(default=None, max_length=50)
    IFSCCode: Optional[str] = Field(default=None, max_length=20)
    AccountType: Optional[str] = Field(default=None, max_length=30)

    # Statutory details (Sensitive)
    AadhaarNumber: Optional[str] = Field(default=None, max_length=12)
    PANNumber: Optional[str] = Field(default=None, max_length=10)
    PFApplicable: Optional[bool] = None
    PFUAN: Optional[str] = Field(default=None, max_length=30)
    PFNumber: Optional[str] = Field(default=None, max_length=50)
    PFJoiningDate: Optional[date] = None
    ESIApplicable: Optional[bool] = None
    ESINumber: Optional[str] = Field(default=None, max_length=30)

    # Salary details (Sensitive)
    SalaryGrade: Optional[str] = Field(default=None, max_length=30)
    PayFrequency: Optional[str] = Field(default=None, max_length=20)
    SalaryEffectiveFrom: Optional[date] = None
    BasicSalary: Optional[Decimal] = None
    HRA: Optional[Decimal] = None
    DA: Optional[Decimal] = None
    OtherAllowances: Optional[Decimal] = None
    GrossSalary: Optional[Decimal] = None
    EmployeePFContribution: Optional[Decimal] = None
    EmployerPFContribution: Optional[Decimal] = None
    EmployeeESIContribution: Optional[Decimal] = None
    EmployerESIContribution: Optional[Decimal] = None
    ProfessionalTax: Optional[Decimal] = None
    OtherDeductions: Optional[Decimal] = None
    NetSalary: Optional[Decimal] = None
    PreviousGrossSalary: Optional[Decimal] = None
    LastSalaryRevisionDate: Optional[date] = None
    SalaryRemarks: Optional[str] = Field(default=None, max_length=500)

    # Notes
    Notes: Optional[str] = Field(default=None, max_length=1000)


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    EmployeeId: int
    EmployeeCode: str
    FirstName: str
    MiddleName: Optional[str] = None
    LastName: Optional[str] = None
    DisplayName: Optional[str] = None
    ProfilePhotoPath: Optional[str] = None

    DateOfBirth: Optional[date] = None
    Gender: Optional[str] = None
    BloodGroup: Optional[str] = None
    MaritalStatus: Optional[str] = None
    Nationality: Optional[str] = None

    MobileNumber: Optional[str] = None
    AlternateMobileNumber: Optional[str] = None
    Email: Optional[str] = None

    AddressLine1: Optional[str] = None
    AddressLine2: Optional[str] = None
    City: Optional[str] = None
    District: Optional[str] = None
    State: Optional[str] = None
    PostalCode: Optional[str] = None
    Country: Optional[str] = None

    FatherName: Optional[str] = None
    FatherMobileNumber: Optional[str] = None
    MotherName: Optional[str] = None
    MotherMobileNumber: Optional[str] = None
    EmergencyContactName: Optional[str] = None
    EmergencyContactNumber: Optional[str] = None
    EmergencyContactRelation: Optional[str] = None

    DateOfJoining: Optional[date] = None
    DateOfLeaving: Optional[date] = None
    EmploymentType: Optional[str] = None
    EmploymentStatus: Optional[str] = None

    CompanyCode: Optional[str] = None
    CompanyName: Optional[str] = None
    LocationCode: Optional[str] = None
    LocationName: Optional[str] = None

    DepartmentId: Optional[int] = None
    DepartmentName: Optional[str] = None
    DesignationId: Optional[int] = None
    DesignationName: Optional[str] = None
    JobTitle: Optional[str] = None
    ReportingManagerCode: Optional[str] = None

    AppRole: Optional[str] = None
    IsAppUser: Optional[bool] = None

    EmployeeSource: Optional[str] = None
    ESSLEmployeeCode: Optional[str] = None
    ESSLStatus: Optional[str] = None
    ESSLSyncedAt: Optional[datetime] = None

    BankName: Optional[str] = None
    BankBranch: Optional[str] = None
    AccountHolderName: Optional[str] = None
    AccountNumber: Optional[str] = None
    IFSCCode: Optional[str] = None
    AccountType: Optional[str] = None

    AadhaarNumber: Optional[str] = None
    PANNumber: Optional[str] = None
    PFApplicable: Optional[bool] = None
    PFUAN: Optional[str] = None
    PFNumber: Optional[str] = None
    PFJoiningDate: Optional[date] = None
    ESIApplicable: Optional[bool] = None
    ESINumber: Optional[str] = None

    SalaryGrade: Optional[str] = None
    PayFrequency: Optional[str] = None
    SalaryEffectiveFrom: Optional[date] = None
    BasicSalary: Optional[Decimal] = None
    HRA: Optional[Decimal] = None
    DA: Optional[Decimal] = None
    OtherAllowances: Optional[Decimal] = None
    GrossSalary: Optional[Decimal] = None
    EmployeePFContribution: Optional[Decimal] = None
    EmployerPFContribution: Optional[Decimal] = None
    EmployeeESIContribution: Optional[Decimal] = None
    EmployerESIContribution: Optional[Decimal] = None
    ProfessionalTax: Optional[Decimal] = None
    OtherDeductions: Optional[Decimal] = None
    NetSalary: Optional[Decimal] = None
    PreviousGrossSalary: Optional[Decimal] = None
    LastSalaryRevisionDate: Optional[date] = None
    SalaryRemarks: Optional[str] = None

    Notes: Optional[str] = None
    IsActive: Optional[bool] = None
    CreatedBy: Optional[str] = None
    CreatedAt: Optional[datetime] = None
    UpdatedBy: Optional[str] = None
    UpdatedAt: Optional[datetime] = None


class EmployeeShort(BaseModel):
    """Compact summary of employee information for lists and selectors."""
    model_config = ConfigDict(from_attributes=True)

    EmployeeId: int
    EmployeeCode: str
    DisplayName: Optional[str] = None
    FirstName: str
    LastName: Optional[str] = None
    DepartmentName: Optional[str] = None
    DesignationName: Optional[str] = None
    ProfilePhotoPath: Optional[str] = None
    IsActive: bool = True


__all__ = [
    "EmployeeBase",
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeResponse",
    "EmployeeShort",
]
