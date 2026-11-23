from datetime import datetime
from decimal import Decimal
from urllib.parse import unquote
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.helpers.pagination import paginate_raw_sql
from src.helpers.sorting import resolve_raw_sort
from src.schemas.master import LedgerCreate, LedgerUpdate


def _sync_opening_balance_transaction(
    db: Session,
    ledger_code: str,
    ledger_name: str,
    opening_balance: float | Decimal | str | None,
    balance_type: str | None,
    acc_head_code: str = "",
    acc_head_name: str = "",
):
    """
    Syncs the opening balance entry into dbo.Acc_Trans_All
    matching legacy accounting journal format.
    """
    try:
        amt = Decimal(str(opening_balance or 0))
    except Exception:
        amt = Decimal(0)

    b_type = (balance_type or "Cr").strip()
    cr_amt = amt if b_type == "Cr" else Decimal(0)
    dr_amt = amt if b_type == "Dr" else Decimal(0)

    # Check if an Opening Balance record already exists for this ledger
    existing_trans = db.execute(
        text("""
            SELECT TOP 1 TransNo
            FROM dbo.Acc_Trans_All
            WHERE TransType = 'Opening Balance'
              AND LeaderCode = :code
              AND Status <> 'Delete'
        """),
        {"code": ledger_code},
    ).first()

    if existing_trans:
        if amt > 0:
            db.execute(
                text("""
                    UPDATE dbo.Acc_Trans_All
                    SET
                        LedgerName = :name,
                        AccHeadCode = COALESCE(NULLIF(:head_code, ''), AccHeadCode),
                        AccHeadName = COALESCE(NULLIF(:head_name, ''), AccHeadName),
                        CreditAmount = :cr,
                        DebitAmount = :dr,
                        Status = 'Active'
                    WHERE TransNo = :trans_no
                """),
                {
                    "trans_no": existing_trans[0],
                    "name": ledger_name,
                    "head_code": acc_head_code,
                    "head_name": acc_head_name,
                    "cr": cr_amt,
                    "dr": dr_amt,
                },
            )
        else:
            db.execute(
                text("""
                    UPDATE dbo.Acc_Trans_All
                    SET Status = 'Delete'
                    WHERE TransNo = :trans_no
                """),
                {"trans_no": existing_trans[0]},
            )
    elif amt > 0:
        year_str = datetime.now().strftime("%y")
        next_year_str = str(int(year_str) + 1)
        trans_no = f"O-BAL/{year_str}-{next_year_str}/{ledger_code}"

        db.execute(
            text("""
                INSERT INTO dbo.Acc_Trans_All (
                    CCode, LCode, FinYearCode, FinYearVal,
                    TransNo, TransDate, LeaderCode, LedgerName,
                    AccHeadCode, AccHeadName, TransType,
                    CreditAmount, DebitAmount, Status,
                    UserId, UserName, CreatedBy
                )
                VALUES (
                    'SCT', 'UNIT I', '01', CONVERT(VARCHAR(4), CASE WHEN MONTH(GETDATE()) >= 4 THEN YEAR(GETDATE()) ELSE YEAR(GETDATE()) - 1 END) + '_' + CONVERT(VARCHAR(4), CASE WHEN MONTH(GETDATE()) >= 4 THEN YEAR(GETDATE()) + 1 ELSE YEAR(GETDATE()) END),
                    :trans_no, CONVERT(VARCHAR(10), GETDATE(), 103),
                    :code, :name, :head_code, :head_name, 'Opening Balance',
                    :cr, :dr, 'Add', 'ADMIN', 'Super Admin',
                    CONVERT(VARCHAR(30), GETDATE(), 100)
                )
            """),
            {
                "trans_no": trans_no,
                "code": ledger_code,
                "name": ledger_name,
                "head_code": acc_head_code or "",
                "head_name": acc_head_name or "",
                "cr": cr_amt,
                "dr": dr_amt,
            },
        )


ALLOWED_LEDGER_SORTS = {
    "LedgerCode": "LedgerCode",
    "LedgerName": "LedgerName",
    "AccGroupName": "AccGroupName",
    "AccCateName": "AccCateName",
    "AccLedgerHeaderName": "AccLedgerHeaderName",
    "LedgerType": "LedgerType",
    "Region": "Region",
    "City": "City",
    "GSTNo": "GSTNo",
    "Status": "Status",
}


def get_ledgers(
    db: Session,
    search: Optional[str] = None,
    ledger_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    fetch_all: bool = False,
):
    union_query = """
        SELECT
            AccGenLdgCode AS LedgerCode,
            AccGenLdgName AS LedgerName,
            '' AS ChequePrintName,
            AccLedgerHeaderName,
            AccGroupName,
            AccCateName,
            CostCenter,
            Status,
            'General Ledger' AS LedgerType,
            '' AS Ledger_Class,
            'Domestic' AS Region,
            '' AS HouseNo,
            '' AS Add1,
            '' AS Add2,
            '' AS Area,
            '' AS City,
            '' AS PinCode,
            '' AS State,
            'India' AS Country,
            '' AS MobileNo,
            '' AS TelNo,
            '' AS ContectName,
            '' AS ContectNo,
            '' AS MailID,
            '' AS WebSite,
            '' AS BankName,
            '' AS AccountNo,
            '' AS BranchName,
            '' AS Branch_Addr,
            '' AS IFSCCode,
            '' AS SWIFTCode,
            '' AS IBANCode,
            '' AS GSTNo,
            '' AS PanNo,
            '' AS TanNo,
            '' AS CINNo,
            '' AS IECode,
            '' AS LEICode,
            '' AS MSME_Status,
            '' AS MSME_No,
            '30' AS PaymentDays,
            COALESCE(OpeningBalance, 0) AS OpeningBalance,
            COALESCE(BalanceType, 'Dr') AS BalanceType,
            '' AS CustomerUnit,
            '' AS ParentLedgerCode
        FROM dbo.Acc_Mst_GeneralLedger
        WHERE Status <> 'Delete'

        UNION ALL

        SELECT
            LedgerCode,
            LedgerName,
            ChequePrintName,
            AccountType AS AccLedgerHeaderName,
            LedgerGrpName AS AccGroupName,
            LedgerCategory AS AccCateName,
            '' AS CostCenter,
            Status,
            LedgerType,
            Ledger_Class,
            Region,
            HouseNo,
            Add1,
            Add2,
            Area,
            City,
            PinCode,
            State,
            Country,
            MobileNo,
            TelNo,
            ContectName,
            ContectNo,
            MailID,
            WebSite,
            BankName,
            AccountNo,
            BranchName,
            Branch_Addr,
            IFSCCode,
            SWIFTCode,
            IBANCode,
            GSTNo,
            PanNo,
            TanNo,
            CINNo,
            IECode,
            LEICode,
            MSME_Status,
            MSME_No,
            PaymentDays,
            COALESCE(OpeningBalance, 0) AS OpeningBalance,
            COALESCE(BalanceType, 'Cr') AS BalanceType,
            CustomerUnit,
            ParentLedgerCode
        FROM dbo.Acc_Mst_Ledger
        WHERE Status <> 'Delete'
    """

    base_query = f"""
        SELECT *
        FROM ({union_query}) AS _unified_ledgers
        WHERE 1=1
    """

    params = {}
    if ledger_type and ledger_type != "ALL":
        base_query += " AND LedgerType = :ledger_type"
        params["ledger_type"] = ledger_type

    if search and search.strip():
        base_query += """
            AND (
                LedgerName LIKE :search
                OR LedgerCode LIKE :search
                OR GSTNo LIKE :search
                OR City LIKE :search
            )
        """
        params["search"] = f"%{search.strip()}%"

    sort_col, sort_dir = resolve_raw_sort(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_sort_columns=ALLOWED_LEDGER_SORTS,
        default_column="LedgerCode",
        default_order="ASC",
    )

    return paginate_raw_sql(
        db=db,
        base_query=base_query,
        params=params,
        page=page,
        page_size=page_size,
        sort_column=sort_col,
        sort_order=sort_dir,
        fetch_all=fetch_all,
    )


def get_account_headers(db: Session):
    query = """
        SELECT
            AccLedgerHeaderCode,
            AccLedgerHeaderName,
            AccCateCode,
            AccCateName,
            AccGroupCode,
            AccGroupName
        FROM dbo.Acc_Mst_AccountLedgerHeader
        WHERE Status <> 'Delete'
    """

    rows = db.execute(text(query)).mappings().all()

    return {
        "success": True,
        "data": [dict(row) for row in rows],
    }


def get_next_ledger_code(db: Session, ledger_type: str) -> str:
    """
    Generates next sequential official ERP code:
      - Customer: CUS/00001, CUS/00029, etc.
      - Supplier: SUP/00001, SUP/00006, etc.
      - General Ledger: GL/00001, GL/00763, etc.
    """
    l_type = (ledger_type or "").strip().lower()
    is_customer = l_type == "customer"
    is_gl = l_type == "general ledger"

    if is_gl:
        row = db.execute(text("""
            SELECT MAX(TRY_CAST(SUBSTRING(AccGenLdgCode, 4, 10) AS INT))
            FROM dbo.Acc_Mst_GeneralLedger
            WHERE AccGenLdgCode LIKE 'GL/%'
        """)).scalar()
        max_seq = row or 0
        return f"GL/{max_seq + 1:05d}"
    elif is_customer:
        row = db.execute(text("""
            SELECT MAX(TRY_CAST(SUBSTRING(LedgerCode, 5, 10) AS INT))
            FROM dbo.Acc_Mst_Ledger
            WHERE LedgerCode LIKE 'CUS/%'
        """)).scalar()
        max_seq = row or 0
        return f"CUS/{max_seq + 1:05d}"
    else:
        row = db.execute(text("""
            SELECT MAX(TRY_CAST(SUBSTRING(LedgerCode, 5, 10) AS INT))
            FROM dbo.Acc_Mst_Ledger
            WHERE LedgerCode LIKE 'SUP/%'
        """)).scalar()
        max_seq = row or 0
        return f"SUP/{max_seq + 1:05d}"


def create_ledger(db: Session, payload: LedgerCreate):
    ledger_code = (payload.LedgerCode or "").strip()
    ledger_name = (payload.LedgerName or "").strip()

    if not ledger_name:
        raise HTTPException(
            status_code=422,
            detail="Ledger name is required",
        )

    # Auto-generate next sequential code if missing or dummy format (CUS-xxxx, SUP-xxxx, GL-xxxx)
    if not ledger_code or any(ledger_code.upper().startswith(p) for p in ("CUS-", "SUP-", "GL-", "AUTO")):
        ledger_code = get_next_ledger_code(db, payload.LedgerType)

    if payload.LedgerType == "General Ledger":
        duplicate_sql = """
            SELECT TOP 1 AccGenLdgCode
            FROM dbo.Acc_Mst_GeneralLedger
            WHERE AccGenLdgCode = :code
              AND Status <> 'Delete'
        """
    else:
        duplicate_sql = """
            SELECT TOP 1 LedgerCode
            FROM dbo.Acc_Mst_Ledger
            WHERE LedgerCode = :code
              AND Status <> 'Delete'
        """

    duplicate = db.execute(
        text(duplicate_sql),
        {"code": ledger_code},
    ).first()

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=f"Ledger code '{ledger_code}' already exists.",
        )

    try:
        val_str = str(payload.OpeningBalance or "").strip()
        opening_bal = Decimal(val_str) if val_str else Decimal(0)
    except Exception:
        opening_bal = Decimal(0)

    balance_type = payload.BalanceType or ("Dr" if payload.LedgerType in ("General Ledger", "Customer") else "Cr")

    try:
        if payload.LedgerType == "General Ledger":
            insert_sql = """
                INSERT INTO dbo.Acc_Mst_GeneralLedger (
                    Ccode, Lcode,
                    AccCateCode, AccCateName,
                    AccGroupCode, AccGroupName,
                    AccSubGrpCode, AccSubGrpName,
                    AccLedgerHeaderCode, AccLedgerHeaderName,
                    AccGenLdgCode, AccGenLdgName,
                    CostCenter, Status,
                    SysIp, SysName, UserID, UserName, CreateOn,
                    OpeningBalance, BalanceType
                )
                VALUES (
                    'SCT', 'UNIT I',
                    'CAT-01', 'General',
                    'GRP-01', :acc_grp,
                    '', :acc_sub_grp,
                    'HDR-01', :acc_header,
                    :ledger_code, :ledger_name,
                    :cost_center, :status,
                    '127.0.0.1', 'API_SERVER',
                    'ADMIN', 'Super Admin', GETDATE(),
                    :opening_bal, :balance_type
                )
            """

            db.execute(
                text(insert_sql),
                {
                    "acc_grp": payload.AccGroupName or "General",
                    "acc_sub_grp": payload.AccSubGroupName or "",
                    "acc_header": payload.AccLedgerHeaderName or "Assets",
                    "ledger_code": ledger_code,
                    "ledger_name": ledger_name,
                    "cost_center": payload.CostCenter or "Cost Centre",
                    "status": payload.Status or "Add",
                    "opening_bal": opening_bal,
                    "balance_type": balance_type,
                },
            )
            head_code = "HDR-01"
            head_name = payload.AccLedgerHeaderName or "General Ledger"

        else:
            is_customer = (payload.LedgerType or "").strip().lower() == "customer"
            grp_id = "Customer" if is_customer else "Supplier"
            grp_name = "Customer" if is_customer else "Supplier"
            category = "Sundry Debtors" if is_customer else "Sundry Creditors"
            acc_type_code = "1-2-9-1" if is_customer else "2-2-2-2"
            acc_type_name = "Domestic Customer" if is_customer else "Domestic Suppliers"
            supply_for = "Customer" if is_customer else (getattr(payload, "SupplyFor", None) or "Goods")
            ledger_type = "Customer" if is_customer else "Supplier"

            # Multi-unit parsing
            raw_unit = (getattr(payload, "CustomerUnit", None) or "").strip().upper()
            clean_unit = None
            if raw_unit and raw_unit not in ("UNIT", "UNIT-", "UNIT -", "NONE", "NULL"):
                if not (raw_unit.startswith("UNIT ") or raw_unit.startswith("PLANT ") or raw_unit.startswith("SITE ")):
                    clean_unit = f"UNIT {raw_unit}"
                else:
                    clean_unit = raw_unit
            parent_ledger_code = getattr(payload, "ParentLedgerCode", None) or None
            if parent_ledger_code:
                parent_ledger_code = parent_ledger_code.strip() or None

            insert_sql = """
                INSERT INTO dbo.Acc_Mst_Ledger (
                    Ccode, Lcode, LedgerCode,
                    LedgerGrpId, LedgerGrpName, LedgerCategory,
                    Region, SupplyFor, LedgerName, ChequePrintName,
                    CustomerUnit, ParentLedgerCode,
                    Ledger_Class, HouseNo, Add1, Add2, Area, City,
                    PinCode, State, Country, MobileNo, TelNo,
                    ContectName, ContectNo, MailID, WebSite,
                    BankId, BankName, AccountNo, BranchName,
                    Branch_Addr, IFSCCode, SWIFTCode, IBANCode,
                    GSTNo, CINNo, PanNo, TanNo, IECode, LEICode,
                    MSME_Status, MSME_No, PaymentDays, DayCondition,
                    AdvancePayment, AdvanceCondition, Inco_Terms,
                    PaymentTerms, TC, PackingTerms, Quality, Warranty,
                    AccountTypeCode, AccountType, PaymentBlock,
                    SupplierBlock, RoundOff, Status, IsActive,
                    Approval_Status, SysIp, SysName, UserID,
                    UserName, CreateOn, LedgerType,
                    OpeningBalance, BalanceType
                )
                VALUES (
                    'SCT', 'UNIT I', :ledger_code,
                    :grp_id, :grp_name, :category,
                    :region, :supply_for, :ledger_name, :cheque_print_name,
                    :customer_unit, :parent_ledger_code,
                    :ledger_class, :house_no, :add1, :add2, :area, :city,
                    :pincode, :state, :country, :mobile_no, :tel_no,
                    :contect_name, :contect_no, :mail_id, :website,
                    'BNK-01', :bank_name, :account_no, :branch_name,
                    :branch_addr, :ifsc_code, :swift_code, :iban_code,
                    :gst_no, :cin_no, :pan_no, :tan_no, :ie_code, :lei_code,
                    :msme_status, :msme_no, :payment_days, 'Days',
                    'No', '0', '', 'Standard', '', '', '', '',
                    :acc_type_code, :acc_type_name, 'No', 'No', 'None',
                    'Add', '1', '0', '127.0.0.1', 'API_SERVER',
                    'ADMIN', 'Super Admin', GETDATE(), :ledger_type,
                    :opening_bal, :balance_type
                )
            """

            db.execute(
                text(insert_sql),
                {
                    "ledger_code": ledger_code,
                    "grp_id": grp_id,
                    "grp_name": grp_name,
                    "category": category,
                    "acc_type_code": acc_type_code,
                    "acc_type_name": acc_type_name,
                    "supply_for": supply_for,
                    "region": payload.Region or "Domestic",
                    "ledger_name": ledger_name,
                    "cheque_print_name": payload.ChequePrintName or ledger_name,
                    "customer_unit": clean_unit,
                    "parent_ledger_code": parent_ledger_code,
                    "ledger_class": payload.Ledger_Class or "Pvt Company",
                    "house_no": payload.HouseNo or "",
                    "add1": payload.Add1 or "",
                    "add2": payload.Add2 or "",
                    "area": payload.Area or "",
                    "city": payload.City or "",
                    "pincode": payload.PinCode or "",
                    "state": payload.State or "",
                    "country": payload.Country or "India",
                    "mobile_no": payload.MobileNo or "",
                    "tel_no": payload.TelNo or "",
                    "contect_name": payload.ContectName or "",
                    "contect_no": payload.ContectNo or "",
                    "mail_id": payload.MailID or "",
                    "website": payload.WebSite or "",
                    "bank_name": payload.BankName or "",
                    "account_no": payload.AccountNo or "",
                    "branch_name": payload.BranchName or "",
                    "branch_addr": payload.Branch_Addr or "",
                    "ifsc_code": payload.IFSCCode or "",
                    "swift_code": payload.SWIFTCode or "",
                    "iban_code": payload.IBANCode or "",
                    "gst_no": payload.GSTNo or "",
                    "cin_no": payload.CINNo or "",
                    "pan_no": payload.PanNo or "",
                    "tan_no": payload.TanNo or "",
                    "ie_code": payload.IECode or "",
                    "lei_code": payload.LEICode or "",
                    "msme_status": payload.MSME_Status or "2",
                    "msme_no": payload.MSME_No or "",
                    "payment_days": payload.PaymentDays or "30",
                    "ledger_type": ledger_type,
                    "opening_bal": opening_bal,
                    "balance_type": balance_type,
                },
            )
            head_code = acc_type_code
            head_name = acc_type_name

        # Sync opening balance to Acc_Trans_All
        _sync_opening_balance_transaction(
            db=db,
            ledger_code=ledger_code,
            ledger_name=ledger_name,
            opening_balance=opening_bal,
            balance_type=balance_type,
            acc_head_code=head_code,
            acc_head_name=head_name,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": (
            f"Ledger '{ledger_name}' ({ledger_code}) created successfully"
        ),
        "ledger_code": ledger_code,
    }


def update_ledger(
    db: Session,
    ledger_code: str,
    payload: LedgerUpdate,
):
    ledger_code = unquote(str(ledger_code or "")).strip()

    # Check if Party Ledger or General Ledger
    party_existing = db.execute(
        text("""
            SELECT TOP 1 LedgerCode, LedgerName, OpeningBalance, BalanceType
            FROM dbo.Acc_Mst_Ledger
            WHERE (LedgerCode = :code OR LOWER(LTRIM(RTRIM(LedgerCode))) = LOWER(:code))
              AND Status <> 'Delete'
        """),
        {"code": ledger_code},
    ).mappings().first()

    general_existing = None
    if not party_existing:
        general_existing = db.execute(
            text("""
                SELECT TOP 1 AccGenLdgCode, AccGenLdgName, OpeningBalance, BalanceType
                FROM dbo.Acc_Mst_GeneralLedger
                WHERE (AccGenLdgCode = :code OR LOWER(LTRIM(RTRIM(AccGenLdgCode))) = LOWER(:code))
                  AND Status <> 'Delete'
            """),
            {"code": ledger_code},
        ).mappings().first()

    if not party_existing and not general_existing:
        raise HTTPException(
            status_code=404,
            detail=f"Ledger '{ledger_code}' not found.",
        )

    opening_bal = None
    if payload.OpeningBalance is not None:
        val_str = str(payload.OpeningBalance).strip()
        if val_str != "":
            try:
                opening_bal = Decimal(val_str)
            except Exception:
                opening_bal = Decimal(0)
        else:
            opening_bal = Decimal(0)

    try:
        if party_existing:
            clean_unit = None
            update_unit = 0
            if getattr(payload, "CustomerUnit", None) is not None:
                update_unit = 1
                raw_u = str(payload.CustomerUnit).strip().upper()
                if raw_u and raw_u not in ("UNIT", "UNIT-", "UNIT -", "NONE", "NULL"):
                    if not (raw_u.startswith("UNIT ") or raw_u.startswith("PLANT ") or raw_u.startswith("SITE ")):
                        clean_unit = f"UNIT {raw_u}"
                    else:
                        clean_unit = raw_u
                else:
                    clean_unit = None

            clean_parent = None
            update_parent = 0
            if getattr(payload, "ParentLedgerCode", None) is not None:
                update_parent = 1
                clean_parent = str(payload.ParentLedgerCode).strip() or None

            update_sql = """
                UPDATE dbo.Acc_Mst_Ledger
                SET
                    LedgerName = COALESCE(:ledger_name, LedgerName),
                    ChequePrintName = COALESCE(:cheque_print_name, ChequePrintName),
                    Ledger_Class = COALESCE(:ledger_class, Ledger_Class),
                    Region = COALESCE(:region, Region),
                    AccountType = COALESCE(:acc_header, AccountType),
                    LedgerGrpName = COALESCE(:acc_grp, LedgerGrpName),
                    HouseNo = COALESCE(:house_no, HouseNo),
                    Add1 = COALESCE(:add1, Add1),
                    Add2 = COALESCE(:add2, Add2),
                    Area = COALESCE(:area, Area),
                    City = COALESCE(:city, City),
                    PinCode = COALESCE(:pincode, PinCode),
                    State = COALESCE(:state, State),
                    Country = COALESCE(:country, Country),
                    MobileNo = COALESCE(:mobile_no, MobileNo),
                    TelNo = COALESCE(:tel_no, TelNo),
                    ContectName = COALESCE(:contect_name, ContectName),
                    ContectNo = COALESCE(:contect_no, ContectNo),
                    MailID = COALESCE(:mail_id, MailID),
                    WebSite = COALESCE(:website, WebSite),
                    BankName = COALESCE(:bank_name, BankName),
                    AccountNo = COALESCE(:account_no, AccountNo),
                    BranchName = COALESCE(:branch_name, BranchName),
                    Branch_Addr = COALESCE(:branch_addr, Branch_Addr),
                    IFSCCode = COALESCE(:ifsc_code, IFSCCode),
                    SWIFTCode = COALESCE(:swift_code, SWIFTCode),
                    IBANCode = COALESCE(:iban_code, IBANCode),
                    GSTNo = COALESCE(:gst_no, GSTNo),
                    PanNo = COALESCE(:pan_no, PanNo),
                    TanNo = COALESCE(:tan_no, TanNo),
                    CINNo = COALESCE(:cin_no, CINNo),
                    IECode = COALESCE(:ie_code, IECode),
                    LEICode = COALESCE(:lei_code, LEICode),
                    MSME_Status = COALESCE(:msme_status, MSME_Status),
                    MSME_No = COALESCE(:msme_no, MSME_No),
                    PaymentDays = COALESCE(:payment_days, PaymentDays),
                    OpeningBalance = COALESCE(:opening_bal, OpeningBalance),
                    BalanceType = COALESCE(:balance_type, BalanceType),
                    LedgerType = COALESCE(:ledger_type, LedgerType),
                    CustomerUnit = CASE WHEN :update_unit = 1 THEN :customer_unit ELSE CustomerUnit END,
                    ParentLedgerCode = CASE WHEN :update_parent = 1 THEN :parent_ledger_code ELSE ParentLedgerCode END
                WHERE LedgerCode = :ledger_code
                  AND Status <> 'Delete'
            """

            db.execute(
                text(update_sql),
                {
                    "ledger_code": ledger_code,
                    "ledger_name": payload.LedgerName,
                    "cheque_print_name": payload.ChequePrintName,
                    "ledger_class": payload.Ledger_Class,
                    "region": payload.Region,
                    "acc_header": payload.AccLedgerHeaderName,
                    "acc_grp": payload.AccGroupName,
                    "house_no": payload.HouseNo,
                    "add1": payload.Add1,
                    "add2": payload.Add2,
                    "area": payload.Area,
                    "city": payload.City,
                    "pincode": payload.PinCode,
                    "state": payload.State,
                    "country": payload.Country,
                    "mobile_no": payload.MobileNo,
                    "tel_no": payload.TelNo,
                    "contect_name": payload.ContectName,
                    "contect_no": payload.ContectNo,
                    "mail_id": payload.MailID,
                    "website": payload.WebSite,
                    "bank_name": payload.BankName,
                    "account_no": payload.AccountNo,
                    "branch_name": payload.BranchName,
                    "branch_addr": payload.Branch_Addr,
                    "ifsc_code": payload.IFSCCode,
                    "swift_code": payload.SWIFTCode,
                    "iban_code": payload.IBANCode,
                    "gst_no": payload.GSTNo,
                    "pan_no": payload.PanNo,
                    "tan_no": payload.TanNo,
                    "cin_no": payload.CINNo,
                    "ie_code": payload.IECode,
                    "lei_code": payload.LEICode,
                    "msme_status": payload.MSME_Status,
                    "msme_no": payload.MSME_No,
                    "payment_days": payload.PaymentDays,
                    "opening_bal": opening_bal,
                    "balance_type": payload.BalanceType,
                    "ledger_type": payload.LedgerType,
                    "update_unit": update_unit,
                    "customer_unit": clean_unit,
                    "update_parent": update_parent,
                    "parent_ledger_code": clean_parent,
                },
            )

            eff_name = payload.LedgerName or party_existing["LedgerName"]
            eff_bal = opening_bal if opening_bal is not None else party_existing.get("OpeningBalance", 0)
            eff_type = payload.BalanceType or party_existing.get("BalanceType", "Cr")
            _sync_opening_balance_transaction(db, ledger_code, eff_name, eff_bal, eff_type)

        else:
            update_sql = """
                UPDATE dbo.Acc_Mst_GeneralLedger
                SET
                    AccGenLdgName = COALESCE(:ledger_name, AccGenLdgName),
                    AccLedgerHeaderName = COALESCE(:acc_header, AccLedgerHeaderName),
                    AccGroupName = COALESCE(:acc_grp, AccGroupName),
                    AccSubGrpName = COALESCE(:acc_sub_grp, AccSubGrpName),
                    CostCenter = COALESCE(:cost_center, CostCenter),
                    OpeningBalance = COALESCE(:opening_bal, OpeningBalance),
                    BalanceType = COALESCE(:balance_type, BalanceType),
                    Status = COALESCE(:status, Status)
                WHERE AccGenLdgCode = :ledger_code
                  AND Status <> 'Delete'
            """

            db.execute(
                text(update_sql),
                {
                    "ledger_code": ledger_code,
                    "ledger_name": payload.LedgerName,
                    "acc_header": payload.AccLedgerHeaderName,
                    "acc_grp": payload.AccGroupName,
                    "acc_sub_grp": payload.AccSubGroupName,
                    "cost_center": payload.CostCenter,
                    "opening_bal": opening_bal,
                    "balance_type": payload.BalanceType,
                    "status": payload.Status,
                },
            )

            eff_name = payload.LedgerName or general_existing["AccGenLdgName"]
            eff_bal = opening_bal if opening_bal is not None else general_existing.get("OpeningBalance", 0)
            eff_type = payload.BalanceType or general_existing.get("BalanceType", "Dr")
            _sync_opening_balance_transaction(db, ledger_code, eff_name, eff_bal, eff_type)

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": f"Ledger {ledger_code} updated successfully",
    }


def delete_ledger(db: Session, ledger_code: str):
    ledger_code = unquote(str(ledger_code or "")).strip()
    try:
        party_result = db.execute(
            text("""
                UPDATE dbo.Acc_Mst_Ledger
                SET Status = 'Delete'
                WHERE (LedgerCode = :code OR LOWER(LTRIM(RTRIM(LedgerCode))) = LOWER(:code))
                  AND Status <> 'Delete'
            """),
            {"code": ledger_code},
        )

        general_result = db.execute(
            text("""
                UPDATE dbo.Acc_Mst_GeneralLedger
                SET Status = 'Delete'
                WHERE (AccGenLdgCode = :code OR LOWER(LTRIM(RTRIM(AccGenLdgCode))) = LOWER(:code))
                  AND Status <> 'Delete'
            """),
            {"code": ledger_code},
        )

        if party_result.rowcount == 0 and general_result.rowcount == 0:
            db.rollback()
            raise HTTPException(
                status_code=404,
                detail="Active ledger not found",
            )

        # Also remove opening balance transaction
        db.execute(
            text("""
                UPDATE dbo.Acc_Trans_All
                SET Status = 'Delete'
                WHERE TransType = 'Opening Balance'
                  AND LeaderCode = :code
            """),
            {"code": ledger_code},
        )

        db.commit()

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": f"Ledger {ledger_code} deleted successfully",
    }
