from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.security import create_access_token, verify_legacy_password
from src.schemas.auth import (
    LoginRequest,
    LoginResponse,
    AuthMetaResponse,
    DropdownOption,
    UserProfile,
)


class AuthService:
    """Authentication and login metadata business logic."""

    @staticmethod
    def get_auth_metadata(
        db: Session,
        company_code: str | None = None,
        location_code: str | None = None,
    ) -> AuthMetaResponse:
        # 1. Companies
        companies_result = db.execute(
            text("""
                SELECT CCode, CompanyName
                FROM MstCompany
            """)
        ).mappings().all()

        companies = [
            DropdownOption(
                id=row["CCode"],
                name=row["CompanyName"],
            )
            for row in companies_result
        ]

        # 2. Locations
        location_query = """
            SELECT Lcode, LocName
            FROM LocationMst
        """
        location_params = {}

        if company_code:
            location_query += " WHERE Ccode = :company_code"
            location_params["company_code"] = company_code

        locations_result = db.execute(
            text(location_query),
            location_params,
        ).mappings().all()

        locations = [
            DropdownOption(
                id=row["Lcode"],
                name=row["LocName"] or row["Lcode"],
            )
            for row in locations_result
        ]

        # 3. Financial years
        financial_year_query = """
            SELECT YearCode, FinacialYear
            FROM MstFinacialYear
        """
        financial_year_params = {}

        if company_code and location_code:
            financial_year_query += """
                WHERE Ccode = :company_code
                  AND Lcode = :location_code
            """
            financial_year_params = {
                "company_code": company_code,
                "location_code": location_code,
            }

        financial_year_query += " ORDER BY YearCode DESC"

        financial_year_result = db.execute(
            text(financial_year_query),
            financial_year_params,
        ).mappings().all()

        financial_years = [
            DropdownOption(
                id=str(row["YearCode"]),
                name=row["FinacialYear"],
            )
            for row in financial_year_result
        ]

        return AuthMetaResponse(
            companies=companies,
            locations=locations,
            financial_years=financial_years,
        )

    @staticmethod
    def login(
        db: Session,
        payload: LoginRequest,
    ) -> LoginResponse:
        # 1. Verify credentials
        login_row = db.execute(
            text("""
                SELECT UserId, Password, isLoggedIN
                FROM Login
                WHERE Ccode = :ccode
                  AND Lcode = :lcode
                  AND UserId = :user_id
            """),
            {
                "ccode": payload.company_code,
                "lcode": payload.location_code,
                "user_id": payload.user_id,
            },
        ).mappings().first()

        if (
            not login_row
            or not verify_legacy_password(
                payload.password,
                login_row["Password"],
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid User ID or Password",
            )

        # 2. Check user details and approval status
        user_row = db.execute(
            text("""
                SELECT
                    UserID,
                    UserName,
                    UserType,
                    Designation,
                    profileImg,
                    Status
                FROM UserDetails
                WHERE UserID = :user_id
                  AND Ccode = :ccode
                  AND LCode = :lcode
            """),
            {
                "user_id": payload.user_id,
                "ccode": payload.company_code,
                "lcode": payload.location_code,
            },
        ).mappings().first()

        if not user_row or (
            user_row["Status"]
            and user_row["Status"].strip().lower() != "approved"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not approved",
            )

        # 3. Fetch company, location, and financial year
        company_row = db.execute(
            text("""
                SELECT CompanyName
                FROM MstCompany
                WHERE CCode = :ccode
            """),
            {"ccode": payload.company_code},
        ).mappings().first()

        location_row = db.execute(
            text("""
                SELECT LocName
                FROM LocationMst
                WHERE Ccode = :ccode
                  AND Lcode = :lcode
            """),
            {
                "ccode": payload.company_code,
                "lcode": payload.location_code,
            },
        ).mappings().first()

        financial_year_row = db.execute(
            text("""
                SELECT FinacialYear
                FROM MstFinacialYear
                WHERE YearCode = :year_code
                  AND Ccode = :ccode
                  AND Lcode = :lcode
            """),
            {
                "year_code": payload.fin_year_code,
                "ccode": payload.company_code,
                "lcode": payload.location_code,
            },
        ).mappings().first()

        user_profile = UserProfile(
            user_id=user_row["UserID"],
            user_name=(
                user_row["UserName"] or user_row["UserID"]
            ),
            role_code=user_row["UserType"] or "USER",
            designation=user_row["Designation"],
            profile_img=user_row["profileImg"],
            company_code=payload.company_code,
            company_name=(
                company_row["CompanyName"]
                if company_row
                else payload.company_code
            ),
            location_code=payload.location_code,
            location_name=(
                location_row["LocName"]
                if location_row
                else payload.location_code
            ),
            fin_year_code=payload.fin_year_code,
            fin_year=(
                financial_year_row["FinacialYear"]
                if financial_year_row
                else payload.fin_year_code
            ),
        )

        # 4. Generate access token
        token_payload = {
            "sub": user_profile.user_id,
            "ccode": user_profile.company_code,
            "lcode": user_profile.location_code,
            "fin_year": user_profile.fin_year_code,
            "role": user_profile.role_code,
        }

        access_token = create_access_token(token_payload)

        # 5. Update login state
        try:
            db.execute(
                text("""
                    UPDATE Login
                    SET isLoggedIN = 'TRUE'
                    WHERE Ccode = :ccode
                      AND Lcode = :lcode
                      AND UserID = :user_id
                """),
                {
                    "ccode": payload.company_code,
                    "lcode": payload.location_code,
                    "user_id": payload.user_id,
                },
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        return LoginResponse(
            access_token=access_token,
            user=user_profile,
        )
