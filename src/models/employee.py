from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, synonym

from src.db.base import Base


class Employee(Base):
    __tablename__ = "Employee_Mst"
    __table_args__ = {"schema": "dbo"}

    # Primary key (bigint in SQL Server)
    EmployeeId: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # Basic details
    EmployeeCode: Mapped[str] = mapped_column(String(50), nullable=False)
    FirstName: Mapped[str] = mapped_column(String(100), nullable=False)
    MiddleName: Mapped[Optional[str]] = mapped_column(String(100))
    LastName: Mapped[Optional[str]] = mapped_column(String(100))
    DisplayName: Mapped[Optional[str]] = mapped_column(String(250))
    ProfilePhotoPath: Mapped[Optional[str]] = mapped_column(String(500))

    DateOfBirth: Mapped[Optional[date]] = mapped_column(Date)
    Gender: Mapped[Optional[str]] = mapped_column(String(20))
    BloodGroup: Mapped[Optional[str]] = mapped_column(String(5))
    MaritalStatus: Mapped[Optional[str]] = mapped_column(String(20))
    Nationality: Mapped[Optional[str]] = mapped_column(String(50))

    # Contact details
    MobileNumber: Mapped[Optional[str]] = mapped_column(String(20))
    AlternateMobileNumber: Mapped[Optional[str]] = mapped_column(String(20))
    Email: Mapped[Optional[str]] = mapped_column(String(254))

    # Address details
    AddressLine1: Mapped[Optional[str]] = mapped_column(String(250))
    AddressLine2: Mapped[Optional[str]] = mapped_column(String(250))
    City: Mapped[Optional[str]] = mapped_column(String(100))
    District: Mapped[Optional[str]] = mapped_column(String(100))
    State: Mapped[Optional[str]] = mapped_column(String(100))
    PostalCode: Mapped[Optional[str]] = mapped_column(String(15))
    Country: Mapped[Optional[str]] = mapped_column(String(100))

    # Family and emergency contact
    FatherName: Mapped[Optional[str]] = mapped_column(String(200))
    FatherMobileNumber: Mapped[Optional[str]] = mapped_column(String(20))
    MotherName: Mapped[Optional[str]] = mapped_column(String(200))
    MotherMobileNumber: Mapped[Optional[str]] = mapped_column(String(20))
    EmergencyContactName: Mapped[Optional[str]] = mapped_column(String(200))
    EmergencyContactNumber: Mapped[Optional[str]] = mapped_column(String(20))
    EmergencyContactRelation: Mapped[Optional[str]] = mapped_column(String(50))

    # Employment details
    DateOfJoining: Mapped[Optional[date]] = mapped_column(Date)
    DateOfLeaving: Mapped[Optional[date]] = mapped_column(Date)
    EmploymentType: Mapped[Optional[str]] = mapped_column(String(30))
    EmploymentStatus: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")

    CompanyCode: Mapped[Optional[str]] = mapped_column(String(20))
    CompanyName: Mapped[Optional[str]] = mapped_column(String(150))
    LocationCode: Mapped[Optional[str]] = mapped_column(String(50))
    LocationName: Mapped[Optional[str]] = mapped_column(String(150))

    DepartmentId: Mapped[Optional[int]] = mapped_column(Integer)
    DepartmentName: Mapped[Optional[str]] = mapped_column(String(100))
    DesignationId: Mapped[Optional[int]] = mapped_column(Integer)
    DesignationName: Mapped[Optional[str]] = mapped_column(String(100))
    JobTitle: Mapped[Optional[str]] = mapped_column(String(100))
    ReportingManagerCode: Mapped[Optional[str]] = mapped_column(String(50))

    # ERP access (AppRole is varchar(30) in SQL Server)
    AppRole: Mapped[Optional[str]] = mapped_column(String(30))
    IsAppUser: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    IsOnSite: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Backward compatibility synonym
    IsOnField = synonym("IsOnSite")

    # ESSL integration
    EmployeeSource: Mapped[Optional[str]] = mapped_column(String(20), default="MANUAL")
    ESSLEmployeeCode: Mapped[Optional[str]] = mapped_column(String(50))
    ESSLStatus: Mapped[Optional[str]] = mapped_column(String(30), default="NOT_LINKED")
    ESSLSyncedAt: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Bank details
    BankName: Mapped[Optional[str]] = mapped_column(String(150))
    BankBranch: Mapped[Optional[str]] = mapped_column(String(150))
    AccountHolderName: Mapped[Optional[str]] = mapped_column(String(200))
    AccountNumber: Mapped[Optional[str]] = mapped_column(String(50))
    IFSCCode: Mapped[Optional[str]] = mapped_column(String(20))
    AccountType: Mapped[Optional[str]] = mapped_column(String(30))

    # Identity and statutory details
    AadhaarNumber: Mapped[Optional[str]] = mapped_column(String(12))
    PANNumber: Mapped[Optional[str]] = mapped_column(String(10))
    PFApplicable: Mapped[Optional[bool]] = mapped_column(Boolean)
    PFUAN: Mapped[Optional[str]] = mapped_column(String(30))
    PFNumber: Mapped[Optional[str]] = mapped_column(String(50))
    PFJoiningDate: Mapped[Optional[date]] = mapped_column(Date)
    ESIApplicable: Mapped[Optional[bool]] = mapped_column(Boolean)
    ESINumber: Mapped[Optional[str]] = mapped_column(String(30))

    # Salary and payroll
    SalaryGrade: Mapped[Optional[str]] = mapped_column(String(30))
    PayFrequency: Mapped[Optional[str]] = mapped_column(String(20), default="MONTHLY")
    SalaryEffectiveFrom: Mapped[Optional[date]] = mapped_column(Date)

    BasicSalary: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    HRA: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    DA: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    OtherAllowances: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    GrossSalary: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    EmployeePFContribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    EmployerPFContribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    EmployeeESIContribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    EmployerESIContribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    ProfessionalTax: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    OtherDeductions: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    NetSalary: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    PreviousGrossSalary: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    LastSalaryRevisionDate: Mapped[Optional[date]] = mapped_column(Date)
    SalaryRemarks: Mapped[Optional[str]] = mapped_column(String(500))
    Notes: Mapped[Optional[str]] = mapped_column(String(1000))

    # Audit & Lifecycle
    IsActive: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    CreatedBy: Mapped[Optional[str]] = mapped_column(String(50))
    CreatedAt: Mapped[Optional[datetime]] = mapped_column(DateTime)
    UpdatedBy: Mapped[Optional[str]] = mapped_column(String(50))
    UpdatedAt: Mapped[Optional[datetime]] = mapped_column(DateTime)
