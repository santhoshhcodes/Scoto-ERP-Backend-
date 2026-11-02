
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.schemas.master import LedgerCreate, LedgerUpdate


def get_ledgers(
    db: Session,
    search: str | None = None,
    ledger_type: str | None = None,
):
    query = """
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
            '' AS BankName,
            '' AS AccountNo,
            '' AS IFSCCode,
            '' AS BranchName,
            '' AS GSTNo,
            '' AS PanNo,
            '' AS City,
            '' AS State,
            '' AS MobileNo,
            '' AS MailID,
            0 AS OpeningBalance,
            'Dr' AS BalanceType
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
            BankName,
            AccountNo,
            IFSCCode,
            BranchName,
            GSTNo,
            PanNo,
            City,
            State,
            MobileNo,
            MailID,
            0 AS OpeningBalance,
            'Cr' AS BalanceType
        FROM dbo.Acc_Mst_Ledger
        WHERE Status <> 'Delete'
    """

    rows = db.execute(text(query)).mappings().all()
    ledgers = [dict(row) for row in rows]

    if ledger_type and ledger_type != "ALL":
        ledgers = [
            item for item in ledgers
            if item.get("LedgerType") == ledger_type
        ]

    if search and search.strip():
        term = search.strip().casefold()
        ledgers = [
            item for item in ledgers
            if any(
                term in str(item.get(field) or "").casefold()
                for field in (
                    "LedgerName",
                    "LedgerCode",
                    "GSTNo",
                    "City",
                )
            )
        ]

    return {
        "success": True,
        "count": len(ledgers),
        "data": ledgers,
    }


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


def create_ledger(db: Session, payload: LedgerCreate):
    ledger_code = payload.LedgerCode.strip()
    ledger_name = payload.LedgerName.strip()

    if not ledger_code or not ledger_name:
        raise HTTPException(
            status_code=422,
            detail="Ledger code and ledger name are required",
        )

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
                    SysIp, SysName, UserID, UserName, CreateOn
                )
                VALUES (
                    '01', '01',
                    'CAT-01', 'General',
                    'GRP-01', :acc_grp,
                    '', :acc_sub_grp,
                    'HDR-01', :acc_header,
                    :ledger_code, :ledger_name,
                    :cost_center, 'Add',
                    '127.0.0.1', 'API_SERVER',
                    'ADMIN', 'Super Admin', GETDATE()
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
                },
            )

        else:
            insert_sql = """
                INSERT INTO dbo.Acc_Mst_Ledger (
                    Ccode, Lcode, LedgerCode,
                    LedgerGrpId, LedgerGrpName, LedgerCategory,
                    Region, SupplyFor, LedgerName, ChequePrintName,
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
                    UserName, CreateOn, LedgerType
                )
                VALUES (
                    '01', '01', :ledger_code,
                    'GRP-01', :acc_grp, 'Sundry Creditors',
                    :region, 'Goods', :ledger_name, :cheque_print_name,
                    :ledger_class, :house_no, :add1, :add2, :area, :city,
                    :pincode, :state, :country, :mobile_no, :tel_no,
                    :contect_name, :contect_no, :mail_id, :website,
                    'BNK-01', :bank_name, :account_no, :branch_name,
                    :branch_addr, :ifsc_code, :swift_code, :iban_code,
                    :gst_no, :cin_no, :pan_no, :tan_no, :ie_code, :lei_code,
                    :msme_status, :msme_no, :payment_days, 'Days',
                    'No', '0', '', 'Standard', '', '', '', '',
                    'HDR-01', :acc_header, 'No', 'No', 'None',
                    'Add', '1', '0', '127.0.0.1', 'API_SERVER',
                    'ADMIN', 'Super Admin', GETDATE(), :ledger_type
                )
            """

            db.execute(
                text(insert_sql),
                {
                    "ledger_code": ledger_code,
                    "acc_grp": payload.AccGroupName or "Sundry Creditors",
                    "region": payload.Region or "Domestic",
                    "ledger_name": ledger_name,
                    "cheque_print_name": payload.ChequePrintName or ledger_name,
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
                    "acc_header": (
                        payload.AccLedgerHeaderName or "Liabilities"
                    ),
                    "ledger_type": payload.LedgerType or "Supplier",
                },
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
    existing = db.execute(
        text("""
            SELECT TOP 1 LedgerCode
            FROM dbo.Acc_Mst_Ledger
            WHERE LedgerCode = :code
              AND Status <> 'Delete'
        """),
        {"code": ledger_code},
    ).first()

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Party ledger not found",
        )

    update_sql = """
        UPDATE dbo.Acc_Mst_Ledger
        SET
            LedgerName = COALESCE(:ledger_name, LedgerName),
            ChequePrintName = COALESCE(
                :cheque_print_name, ChequePrintName
            ),
            BankName = COALESCE(:bank_name, BankName),
            AccountNo = COALESCE(:account_no, AccountNo),
            IFSCCode = COALESCE(:ifsc_code, IFSCCode),
            BranchName = COALESCE(:branch_name, BranchName),
            GSTNo = COALESCE(:gst_no, GSTNo),
            PanNo = COALESCE(:pan_no, PanNo),
            City = COALESCE(:city, City),
            State = COALESCE(:state, State),
            MobileNo = COALESCE(:mobile_no, MobileNo),
            MailID = COALESCE(:mail_id, MailID)
        WHERE LedgerCode = :ledger_code
          AND Status <> 'Delete'
    """

    try:
        db.execute(
            text(update_sql),
            {
                "ledger_code": ledger_code,
                "ledger_name": payload.LedgerName,
                "cheque_print_name": payload.ChequePrintName,
                "bank_name": payload.BankName,
                "account_no": payload.AccountNo,
                "ifsc_code": payload.IFSCCode,
                "branch_name": payload.BranchName,
                "gst_no": payload.GSTNo,
                "pan_no": payload.PanNo,
                "city": payload.City,
                "state": payload.State,
                "mobile_no": payload.MobileNo,
                "mail_id": payload.MailID,
            },
        )
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": f"Ledger {ledger_code} updated successfully",
    }


def delete_ledger(db: Session, ledger_code: str):
    try:
        party_result = db.execute(
            text("""
                UPDATE dbo.Acc_Mst_Ledger
                SET Status = 'Delete'
                WHERE LedgerCode = :code
                  AND Status <> 'Delete'
            """),
            {"code": ledger_code},
        )

        general_result = db.execute(
            text("""
                UPDATE dbo.Acc_Mst_GeneralLedger
                SET Status = 'Delete'
                WHERE AccGenLdgCode = :code
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
