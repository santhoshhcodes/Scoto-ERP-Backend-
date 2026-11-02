from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.models.employee import Employee
from src.schemas.employee import EmployeeCreate, EmployeeUpdate

PROTECTED_EMPLOYEE_FIELDS = {
    "EmployeeId",
    "EmployeeCode",
    "EmployeeSource",
        "ESSLStatus",
    "ESSLSyncedAt",
    "CreatedBy",
    "CreatedAt",
    "UpdatedBy",
    "UpdatedAt",
}

AUTHORIZED_ROLES = {
    "SUPER_ADMIN",
    "ADMIN",
    "SYSTEMADMIN",
    "HR_MANAGER",
    "ACCOUNTS_OFFICER",
    "1",
    "2",
}


def list_employees(
    db: Session,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    source: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    stmt = select(Employee)

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Employee.EmployeeCode.ilike(term),
                Employee.FirstName.ilike(term),
                Employee.LastName.ilike(term),
                Employee.DisplayName.ilike(term),
                Employee.DepartmentName.ilike(term),
                Employee.DesignationName.ilike(term),
                Employee.MobileNumber.ilike(term),
                Employee.ESSLEmployeeCode.ilike(term),
            )
        )

    if is_active is not None:
        stmt = stmt.where(Employee.IsActive == is_active)

    if source:
        source_val = source.strip().upper()
        if source_val == "ESSL":
            stmt = stmt.where(
                or_(
                    Employee.EmployeeSource == "ESSL",
                    Employee.ESSLEmployeeCode.isnot(None),
                )
            )
        elif source_val == "MANUAL":
            stmt = stmt.where(Employee.EmployeeSource == "MANUAL")

    stmt = stmt.order_by(Employee.EmployeeId.desc())
    stmt = stmt.offset(skip).limit(limit)

    return list(db.scalars(stmt).all())


def get_employee(db: Session, employee_id: int) -> Employee:
    employee = db.get(Employee, employee_id)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found",
        )

    return employee


def create_employee(db: Session, payload: EmployeeCreate) -> Employee:
    employee_code = payload.EmployeeCode.strip()
    first_name = payload.FirstName.strip()

    if not employee_code:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Employee code is required",
        )

    if not first_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="First name is required",
        )

    existing = db.scalar(
        select(Employee).where(Employee.EmployeeCode == employee_code)
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee code '{employee_code}' already exists",
        )

    data = payload.model_dump(exclude_unset=True)

    # Clean strings
    for k, v in list(data.items()):
        if isinstance(v, str):
            v_stripped = v.strip()
            data[k] = v_stripped if v_stripped else None

    data["EmployeeCode"] = employee_code
    data["FirstName"] = first_name

    if not data.get("DisplayName"):
        parts = [
            first_name,
            data.get("MiddleName"),
            data.get("LastName"),
        ]
        data["DisplayName"] = " ".join(p for p in parts if p and p.strip())

    data["EmploymentStatus"] = data.get("EmploymentStatus") or "ACTIVE"
    data["EmployeeSource"] = "MANUAL"
    data["ESSLEmployeeCode"] = None
    data["ESSLStatus"] = "NOT_LINKED"
    data["IsActive"] = data.get("IsActive") if data.get("IsActive") is not None else True
    data["CreatedAt"] = datetime.now()
    data["CreatedBy"] = "ADMIN"

    _calculate_salaries(data)

    employee = Employee(**data)
    db.add(employee)

    try:
        db.commit()
        db.refresh(employee)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create employee: {str(e)}",
        )

    return employee


def update_employee(
    db: Session,
    employee_id: int,
    payload: EmployeeUpdate,
) -> Employee:
    employee = get_employee(db, employee_id)

    # Partial update: only fields explicitly set by client are present
    changes = payload.model_dump(exclude_unset=True)

    # Strictly protect identifiers and sync linkage against modification
    for field in PROTECTED_EMPLOYEE_FIELDS:
        if field in changes:
            curr_val = getattr(employee, field, None)
            new_val = changes[field]
            # Normalize for comparison
            if curr_val is not None and new_val is not None:
                if str(curr_val).strip() != str(new_val).strip():
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={
                            "message": f"System-managed field '{field}' is immutable and cannot be modified.",
                            "field": field,
                            "current_value": str(curr_val),
                            "attempted_value": str(new_val),
                        },
                    )
            elif curr_val != new_val:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": f"System-managed field '{field}' is immutable and cannot be modified.",
                        "field": field,
                    },
                )
            # Remove protected field so it is never overwritten
            changes.pop(field, None)

    # Normalize empty strings to None and trim whitespace
    cleaned_changes: Dict[str, Any] = {}
    for field, value in changes.items():
        if isinstance(value, str):
            val_stripped = value.strip()
            cleaned_changes[field] = val_stripped if val_stripped else None
        else:
            cleaned_changes[field] = value

    if "ESSLEmployeeCode" in cleaned_changes:
        code_val = cleaned_changes["ESSLEmployeeCode"]
        if code_val:
            cleaned_changes["ESSLStatus"] = "LINKED"
            if getattr(employee, "EmployeeSource", None) == "MANUAL":
                cleaned_changes["EmployeeSource"] = "ESSL"
        else:
            cleaned_changes["ESSLStatus"] = "NOT_LINKED"

    if "FirstName" in cleaned_changes:
        if not cleaned_changes["FirstName"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="First name cannot be empty",
            )

    if cleaned_changes.get("PANNumber"):
        pan = cleaned_changes["PANNumber"].upper()
        if len(pan) > 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="PAN Number cannot exceed 10 characters",
            )
        cleaned_changes["PANNumber"] = pan

    if cleaned_changes.get("AadhaarNumber"):
        aadhaar = cleaned_changes["AadhaarNumber"].replace(" ", "").replace("-", "")
        if len(aadhaar) > 12:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Aadhaar Number cannot exceed 12 digits",
            )
        cleaned_changes["AadhaarNumber"] = aadhaar

    if "DisplayName" not in cleaned_changes and any(
        k in cleaned_changes for k in ("FirstName", "MiddleName", "LastName")
    ):
        fn = cleaned_changes.get("FirstName", employee.FirstName) or ""
        mn = cleaned_changes.get("MiddleName", employee.MiddleName) or ""
        ln = cleaned_changes.get("LastName", employee.LastName) or ""
        parts = [p.strip() for p in (fn, mn, ln) if p and p.strip()]
        if parts:
            cleaned_changes["DisplayName"] = " ".join(parts)

    _recalculate_update_salaries(employee, cleaned_changes)

    for field, value in cleaned_changes.items():
        if not hasattr(employee, field):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported employee field: {field}",
            )
        setattr(employee, field, value)

    employee.UpdatedAt = datetime.now()
    employee.UpdatedBy = "ADMIN"

    try:
        db.commit()
        db.refresh(employee)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update employee in database: {str(e)}",
        )

    return employee


def delete_employee(db: Session, employee_id: int):
    employee = get_employee(db, employee_id)

    if not employee.IsActive:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee is already inactive",
        )

    employee.IsActive = False
    employee.EmploymentStatus = "INACTIVE"
    employee.UpdatedAt = datetime.now()
    employee.UpdatedBy = "ADMIN"

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate employee: {str(e)}",
        )

    return {
        "message": "Employee deactivated successfully",
        "employee_id": employee_id,
        "employee_code": employee.EmployeeCode,
        "is_active": False,
    }


def _calculate_salaries(data: Dict[str, Any]) -> None:
    basic = data.get("BasicSalary") or Decimal("0")
    hra = data.get("HRA") or Decimal("0")
    da = data.get("DA") or Decimal("0")
    allowances = data.get("OtherAllowances") or Decimal("0")

    if not data.get("GrossSalary") and any(
        data.get(k) for k in ("BasicSalary", "HRA", "DA", "OtherAllowances")
    ):
        data["GrossSalary"] = basic + hra + da + allowances

    gross = data.get("GrossSalary") or Decimal("0")
    pf = data.get("EmployeePFContribution") or Decimal("0")
    esi = data.get("EmployeeESIContribution") or Decimal("0")
    pt = data.get("ProfessionalTax") or Decimal("0")
    other_ded = data.get("OtherDeductions") or Decimal("0")
    total_ded = pf + esi + pt + other_ded

    if not data.get("NetSalary") and gross > 0:
        data["NetSalary"] = max(Decimal("0"), gross - total_ded)


def _recalculate_update_salaries(
    employee: Employee,
    changes: Dict[str, Any],
) -> None:
    salary_keys = {"BasicSalary", "HRA", "DA", "OtherAllowances"}
    if salary_keys.intersection(changes) and "GrossSalary" not in changes:
        basic = Decimal(str(changes.get("BasicSalary", employee.BasicSalary) or 0))
        hra = Decimal(str(changes.get("HRA", employee.HRA) or 0))
        da = Decimal(str(changes.get("DA", employee.DA) or 0))
        allowances = Decimal(str(changes.get("OtherAllowances", employee.OtherAllowances) or 0))
        changes["GrossSalary"] = basic + hra + da + allowances

    deduction_keys = {
        "GrossSalary",
        "EmployeePFContribution",
        "EmployeeESIContribution",
        "ProfessionalTax",
        "OtherDeductions",
    }
    if deduction_keys.intersection(changes) and "NetSalary" not in changes:
        gross = Decimal(str(changes.get("GrossSalary", employee.GrossSalary) or 0))
        pf = Decimal(str(changes.get("EmployeePFContribution", employee.EmployeePFContribution) or 0))
        esi = Decimal(str(changes.get("EmployeeESIContribution", employee.EmployeeESIContribution) or 0))
        pt = Decimal(str(changes.get("ProfessionalTax", employee.ProfessionalTax) or 0))
        other_ded = Decimal(str(changes.get("OtherDeductions", employee.OtherDeductions) or 0))
        total_ded = pf + esi + pt + other_ded
        if gross > 0:
            changes["NetSalary"] = max(Decimal("0"), gross - total_ded)


def toggle_onsite_by_code(db: Session, employee_code: str):
    emp = db.scalar(select(Employee).where(Employee.EmployeeCode == employee_code.strip()))
    if not emp:
        raise HTTPException(404, f"Employee with code {employee_code} not found")
    emp.IsOnSite = not bool(emp.IsOnSite)
    db.commit()
    db.refresh(emp)
    is_on_site = bool(emp.IsOnSite)
    return {
        "employee_code": emp.EmployeeCode,
        "is_on_site": is_on_site,
        "is_on_field": is_on_site,
    }


# Backwards compatibility alias
toggle_onfield_by_code = toggle_onsite_by_code
