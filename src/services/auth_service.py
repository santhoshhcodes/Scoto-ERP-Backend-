import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.security import create_access_token, verify_password, get_password_hash
from src.utils.mailer import send_otp_email
from src.schemas.auth import (
    LoginRequest,
    LoginResponse,
    AuthMetaResponse,
    DropdownOption,
    UserProfile,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ActivateAccountRequest,
    VerifyDeviceOtpRequest,
    ChangePasswordRequest,
    ChangePasswordResponse,
    FirstTimeActivateRequest,
    FirstTimeActivateResponse,
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
            or not verify_password(
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
                    Status,
                    Email,
                    IsFirstLogin
                FROM UserDetails
                WHERE UPPER(TRIM(UserID)) = UPPER(TRIM(:user_id))
                  AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                  AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
            """),
            {
                "user_id": payload.user_id,
                "ccode": payload.company_code,
                "lcode": payload.location_code,
            },
        ).mappings().first()

        if not user_row or (
            user_row["Status"]
            and user_row["Status"].strip().lower() not in {"approved", "active"}
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not approved",
            )

        canonical_user_id = user_row["UserID"]

        # 3. Device Trust Verification (Adaptive 2FA on New Browser/Machine)
        if payload.device_id:
            device_record = db.execute(
                text("""
                    SELECT TOP 1 IsTrusted
                    FROM UserTrustedDevices
                    WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                      AND DeviceId = :device_id
                      AND IsTrusted = 1
                """),
                {
                    "user_id": canonical_user_id,
                    "device_id": payload.device_id.strip(),
                },
            ).first()

            if not device_record:
                email = (user_row["Email"] or "").strip()
                if email and "@" in email:
                    otp_code = f"{secrets.randbelow(900000) + 100000}"
                    expires_at = datetime.now() + timedelta(minutes=10)

                    # Expire previous device OTPs
                    db.execute(
                        text("""
                            UPDATE UserPasswordOTP
                            SET IsUsed = 1
                            WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                              AND Purpose = 'DEVICE_VERIFICATION'
                              AND IsUsed = 0
                        """),
                        {"user_id": canonical_user_id},
                    )

                    db.execute(
                        text("""
                            INSERT INTO UserPasswordOTP (
                                Ccode, Lcode, UserId, Email, OTPCode, Purpose, ExpiresAt, IsUsed, AttemptsCount, CreatedAt
                            )
                            VALUES (
                                :ccode, :lcode, :user_id, :email, :otp_code, 'DEVICE_VERIFICATION', :expires_at, 0, 0, GETDATE()
                            )
                        """),
                        {
                            "ccode": payload.company_code,
                            "lcode": payload.location_code,
                            "user_id": canonical_user_id,
                            "email": email,
                            "otp_code": otp_code,
                            "expires_at": expires_at,
                        },
                    )
                    db.commit()

                    send_otp_email(
                        to_email=email,
                        user_name=user_row["UserName"] or canonical_user_id,
                        otp_code=otp_code,
                        purpose="New Device Login Verification",
                    )

                    parts = email.split("@")
                    name_p = parts[0]
                    dom_p = parts[1] if len(parts) > 1 else ""
                    masked = name_p[:2] + "***" + (name_p[-1] if len(name_p) > 2 else "") + f"@{dom_p}"

                    return LoginResponse(
                        requires_2fa=True,
                        email_masked=masked,
                        message="New browser/server detected. Enter the OTP code sent to your registered email to verify this device.",
                    )
            else:
                # Update last login time on trusted device
                try:
                    db.execute(
                        text("""
                            UPDATE UserTrustedDevices
                            SET LastLoginAt = GETDATE()
                            WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                              AND DeviceId = :device_id
                        """),
                        {
                            "user_id": canonical_user_id,
                            "device_id": payload.device_id.strip(),
                        },
                    )
                    db.commit()
                except Exception:
                    pass

        # 4. Fetch company, location, and financial year
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

    @staticmethod
    def forgot_password(
        db: Session,
        payload: ForgotPasswordRequest,
    ) -> ForgotPasswordResponse:
        user = db.execute(
            text("""
                SELECT UserID, UserName, Status, Email
                FROM UserDetails
                WHERE UPPER(TRIM(UserID)) = UPPER(TRIM(:user_id))
                  AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                  AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
            """),
            {
                "user_id": payload.user_id,
                "ccode": payload.company_code,
                "lcode": payload.location_code,
            },
        ).mappings().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User ID '{payload.user_id}' was not found for the selected company and location.",
            )

        if user["Status"] and user["Status"].strip().lower() not in {"approved", "active"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated or pending approval.",
            )

        email = (user["Email"] or "").strip()
        if not email or "@" not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No registered email address found for this user. Please contact your Super Administrator.",
            )

        canonical_user_id = user["UserID"]

        # Generate 6-digit cryptographically secure OTP
        otp_code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.now() + timedelta(minutes=10)

        try:
            # Expire previous unused OTPs for this user
            db.execute(
                text("""
                    UPDATE UserPasswordOTP
                    SET IsUsed = 1
                    WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                      AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                      AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
                      AND IsUsed = 0
                """),
                {
                    "user_id": canonical_user_id,
                    "ccode": payload.company_code,
                    "lcode": payload.location_code,
                },
            )

            # Insert new OTP record
            db.execute(
                text("""
                    INSERT INTO UserPasswordOTP (
                        Ccode, Lcode, UserId, Email, OTPCode, Purpose, ExpiresAt, IsUsed, AttemptsCount, CreatedAt
                    )
                    VALUES (
                        :ccode, :lcode, :user_id, :email, :otp_code, 'FORGOT_PASSWORD', :expires_at, 0, 0, GETDATE()
                    )
                """),
                {
                    "ccode": payload.company_code,
                    "lcode": payload.location_code,
                    "user_id": canonical_user_id,
                    "email": email,
                    "otp_code": otp_code,
                    "expires_at": expires_at,
                },
            )
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate OTP record. Please try again.",
            )

        # Dispatch email
        email_sent = send_otp_email(
            to_email=email,
            user_name=user["UserName"] or canonical_user_id,
            otp_code=otp_code,
            purpose="Password Reset",
        )

        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email. Please check server SMTP configuration.",
            )

        # Create masked email for privacy
        parts = email.split("@")
        name_part = parts[0]
        domain_part = parts[1] if len(parts) > 1 else ""
        masked_name = name_part[:2] + "***" + (name_part[-1] if len(name_part) > 2 else "")
        masked_email = f"{masked_name}@{domain_part}"

        return ForgotPasswordResponse(
            status="success",
            message=f"A 6-digit OTP code has been sent to {masked_email}",
            email_masked=masked_email,
        )

    @staticmethod
    def verify_otp(
        db: Session,
        payload: VerifyOtpRequest,
    ) -> VerifyOtpResponse:
        otp_row = db.execute(
            text("""
                SELECT TOP 1 OTPId, OTPCode, ExpiresAt, IsUsed, AttemptsCount
                FROM UserPasswordOTP
                WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                  AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                  AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
                  AND IsUsed = 0
                ORDER BY OTPId DESC
            """),
            {
                "user_id": payload.user_id,
                "ccode": payload.company_code,
                "lcode": payload.location_code,
            },
        ).mappings().first()

        if not otp_row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active OTP request found. Please request a new OTP.",
            )

        if otp_row["ExpiresAt"] < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The OTP has expired. Please request a new code.",
            )

        if otp_row["AttemptsCount"] >= 5:
            db.execute(
                text("UPDATE UserPasswordOTP SET IsUsed = 1 WHERE OTPId = :id"),
                {"id": otp_row["OTPId"]},
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum failed attempts exceeded. This OTP is expired. Please request a new code.",
            )

        if str(otp_row["OTPCode"]).strip() != str(payload.otp_code).strip():
            db.execute(
                text("UPDATE UserPasswordOTP SET AttemptsCount = AttemptsCount + 1 WHERE OTPId = :id"),
                {"id": otp_row["OTPId"]},
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code. Please check your email and try again.",
            )

        return VerifyOtpResponse(
            status="success",
            message="OTP verified successfully.",
            verified=True,
        )

    @staticmethod
    def reset_password(
        db: Session,
        payload: ResetPasswordRequest,
    ) -> ResetPasswordResponse:
        if not payload.new_password or len(payload.new_password.strip()) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long.",
            )

        otp_row = db.execute(
            text("""
                SELECT TOP 1 OTPId, OTPCode, ExpiresAt, IsUsed, AttemptsCount, UserId
                FROM UserPasswordOTP
                WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                  AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                  AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
                  AND IsUsed = 0
                ORDER BY OTPId DESC
            """),
            {
                "user_id": payload.user_id,
                "ccode": payload.company_code,
                "lcode": payload.location_code,
            },
        ).mappings().first()

        if not otp_row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active OTP found. Please request a new OTP first.",
            )

        if otp_row["ExpiresAt"] < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new code.",
            )

        if str(otp_row["OTPCode"]).strip() != str(payload.otp_code).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code provided.",
            )

        hashed_password = get_password_hash(payload.new_password.strip())
        canonical_user_id = otp_row["UserId"]

        try:
            db.execute(
                text("""
                    UPDATE Login
                    SET Password = :pw, isLoggedIN = 'FALSE'
                    WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                      AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                      AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
                """),
                {
                    "pw": hashed_password,
                    "user_id": canonical_user_id,
                    "ccode": payload.company_code,
                    "lcode": payload.location_code,
                },
            )
            db.execute(
                text("""
                    UPDATE UserDetails
                    SET Password = :pw, IsFirstLogin = 0
                    WHERE UPPER(TRIM(UserID)) = UPPER(TRIM(:user_id))
                      AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                      AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
                """),
                {
                    "pw": hashed_password,
                    "user_id": canonical_user_id,
                    "ccode": payload.company_code,
                    "lcode": payload.location_code,
                },
            )
            db.execute(
                text("UPDATE UserPasswordOTP SET IsUsed = 1 WHERE OTPId = :id"),
                {"id": otp_row["OTPId"]},
            )
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password in database. Please try again.",
            )

        return ResetPasswordResponse(
            status="success",
            message="Your password has been successfully updated. You can now log in.",
        )

    @staticmethod
    def activate_account(
        db: Session,
        payload: ActivateAccountRequest,
    ) -> ResetPasswordResponse:
        return AuthService.reset_password(
            db=db,
            payload=ResetPasswordRequest(
                user_id=payload.user_id,
                company_code=payload.company_code,
                location_code=payload.location_code,
                otp_code=payload.otp_code,
                new_password=payload.new_password,
            ),
        )

    @staticmethod
    def verify_device_otp(
        db: Session,
        payload: VerifyDeviceOtpRequest,
    ) -> LoginResponse:
        # 1. Verify OTP
        otp_row = db.execute(
            text("""
                SELECT TOP 1 OTPId, OTPCode, ExpiresAt, IsUsed, AttemptsCount, UserId
                FROM UserPasswordOTP
                WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                  AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                  AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
                  AND IsUsed = 0
                ORDER BY OTPId DESC
            """),
            {
                "user_id": payload.user_id,
                "ccode": payload.company_code,
                "lcode": payload.location_code,
            },
        ).mappings().first()

        if not otp_row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active device verification OTP request found. Please login again.",
            )

        if otp_row["ExpiresAt"] < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The device verification OTP has expired. Please sign in again.",
            )

        if str(otp_row["OTPCode"]).strip() != str(payload.otp_code).strip():
            db.execute(
                text("UPDATE UserPasswordOTP SET AttemptsCount = AttemptsCount + 1 WHERE OTPId = :id"),
                {"id": otp_row["OTPId"]},
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code. Please check your email.",
            )

        canonical_user_id = otp_row["UserId"]

        # 2. Register Device in UserTrustedDevices
        try:
            device_exists = db.execute(
                text("""
                    SELECT 1 FROM UserTrustedDevices
                    WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                      AND DeviceId = :device_id
                """),
                {
                    "user_id": canonical_user_id,
                    "device_id": payload.device_id.strip(),
                },
            ).first()

            if not device_exists:
                db.execute(
                    text("""
                        INSERT INTO UserTrustedDevices (
                            DeviceId, UserId, Ccode, Lcode, DeviceName, BrowserAgent, IsTrusted, FirstLoginAt, LastLoginAt
                        )
                        VALUES (
                            :device_id, :user_id, :ccode, :lcode, 'Office/Server Browser', :browser_agent, 1, GETDATE(), GETDATE()
                        )
                    """),
                    {
                        "device_id": payload.device_id.strip(),
                        "user_id": canonical_user_id,
                        "ccode": payload.company_code,
                        "lcode": payload.location_code,
                        "browser_agent": payload.browser_agent,
                    },
                )
            else:
                db.execute(
                    text("""
                        UPDATE UserTrustedDevices
                        SET IsTrusted = 1, LastLoginAt = GETDATE()
                        WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                          AND DeviceId = :device_id
                    """),
                    {
                        "user_id": canonical_user_id,
                        "device_id": payload.device_id.strip(),
                    },
                )

            # Mark OTP as used
            db.execute(
                text("UPDATE UserPasswordOTP SET IsUsed = 1 WHERE OTPId = :id"),
                {"id": otp_row["OTPId"]},
            )
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register trusted device.",
            )

        # 3. Build Login Response with Token
        user_row = db.execute(
            text("""
                SELECT UserID, UserName, UserType, Designation, profileImg
                FROM UserDetails
                WHERE UPPER(TRIM(UserID)) = UPPER(TRIM(:user_id))
                  AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                  AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
            """),
            {
                "user_id": canonical_user_id,
                "ccode": payload.company_code,
                "lcode": payload.location_code,
            },
        ).mappings().first()

        company_row = db.execute(
            text("SELECT CompanyName FROM MstCompany WHERE CCode = :ccode"),
            {"ccode": payload.company_code},
        ).mappings().first()

        location_row = db.execute(
            text("SELECT LocName FROM LocationMst WHERE Ccode = :ccode AND Lcode = :lcode"),
            {"ccode": payload.company_code, "lcode": payload.location_code},
        ).mappings().first()

        financial_year_row = db.execute(
            text("SELECT FinacialYear FROM MstFinacialYear WHERE YearCode = :year_code AND Ccode = :ccode AND Lcode = :lcode"),
            {"year_code": payload.fin_year_code, "ccode": payload.company_code, "lcode": payload.location_code},
        ).mappings().first()

        user_profile = UserProfile(
            user_id=user_row["UserID"],
            user_name=user_row["UserName"] or user_row["UserID"],
            role_code=user_row["UserType"] or "USER",
            designation=user_row["Designation"],
            profile_img=user_row["profileImg"],
            company_code=payload.company_code,
            company_name=company_row["CompanyName"] if company_row else payload.company_code,
            location_code=payload.location_code,
            location_name=location_row["LocName"] if location_row else payload.location_code,
            fin_year_code=payload.fin_year_code,
            fin_year=financial_year_row["FinacialYear"] if financial_year_row else payload.fin_year_code,
        )

        token_payload = {
            "sub": user_profile.user_id,
            "ccode": user_profile.company_code,
            "lcode": user_profile.location_code,
            "fin_year": user_profile.fin_year_code,
            "role": user_profile.role_code,
        }
        access_token = create_access_token(token_payload)

        return LoginResponse(
            access_token=access_token,
            user=user_profile,
            requires_2fa=False,
            message="Device verified successfully.",
        )

    @staticmethod
    def change_password(
        db: Session,
        payload: ChangePasswordRequest,
    ) -> ChangePasswordResponse:
        if not payload.new_password or len(payload.new_password.strip()) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 6 characters long.",
            )

        login_row = db.execute(
            text("""
                SELECT UserId, Password
                FROM Login
                WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                  AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                  AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
            """),
            {
                "user_id": payload.user_id,
                "ccode": payload.company_code,
                "lcode": payload.location_code,
            },
        ).mappings().first()

        if not login_row or not verify_password(payload.current_password, login_row["Password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        hashed_new_pw = get_password_hash(payload.new_password.strip())

        try:
            db.execute(
                text("""
                    UPDATE Login
                    SET Password = :pw
                    WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                      AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                      AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
                """),
                {
                    "pw": hashed_new_pw,
                    "user_id": payload.user_id,
                    "ccode": payload.company_code,
                    "lcode": payload.location_code,
                },
            )
            db.execute(
                text("""
                    UPDATE UserDetails
                    SET Password = :pw
                    WHERE UPPER(TRIM(UserID)) = UPPER(TRIM(:user_id))
                      AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                      AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
                """),
                {
                    "pw": hashed_new_pw,
                    "user_id": payload.user_id,
                    "ccode": payload.company_code,
                    "lcode": payload.location_code,
                },
            )
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password. Please try again.",
            )

        return ChangePasswordResponse(
            status="success",
            message="Password has been changed successfully.",
        )

    @staticmethod
    def first_time_activate(
        db: Session,
        payload: FirstTimeActivateRequest,
    ) -> FirstTimeActivateResponse:
        user = db.execute(
            text("""
                SELECT UserID, UserName, Status, Email, IsFirstLogin
                FROM UserDetails
                WHERE UPPER(TRIM(UserID)) = UPPER(TRIM(:user_id))
                  AND UPPER(TRIM(Ccode)) = UPPER(TRIM(:ccode))
                  AND UPPER(TRIM(Lcode)) = UPPER(TRIM(:lcode))
            """),
            {
                "user_id": payload.user_id,
                "ccode": payload.company_code,
                "lcode": payload.location_code,
            },
        ).mappings().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User ID '{payload.user_id}' was not found. Please contact your Super Administrator to register your profile.",
            )

        if user["Status"] and user["Status"].strip().lower() not in {"approved", "active"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is not approved yet. Please contact the administrator.",
            )

        email = (user["Email"] or "").strip()
        if not email or "@" not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No registered email address found for your profile. Please contact Super Administrator.",
            )

        canonical_user_id = user["UserID"]
        otp_code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.now() + timedelta(minutes=10)

        try:
            # Expire previous activation OTPs
            db.execute(
                text("""
                    UPDATE UserPasswordOTP
                    SET IsUsed = 1
                    WHERE UPPER(TRIM(UserId)) = UPPER(TRIM(:user_id))
                      AND Purpose = 'FIRST_TIME_SETUP'
                      AND IsUsed = 0
                """),
                {"user_id": canonical_user_id},
            )

            db.execute(
                text("""
                    INSERT INTO UserPasswordOTP (
                        Ccode, Lcode, UserId, Email, OTPCode, Purpose, ExpiresAt, IsUsed, AttemptsCount, CreatedAt
                    )
                    VALUES (
                        :ccode, :lcode, :user_id, :email, :otp_code, 'FIRST_TIME_SETUP', :expires_at, 0, 0, GETDATE()
                    )
                """),
                {
                    "ccode": payload.company_code,
                    "lcode": payload.location_code,
                    "user_id": canonical_user_id,
                    "email": email,
                    "otp_code": otp_code,
                    "expires_at": expires_at,
                },
            )
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate activation OTP.",
            )

        # Dispatch activation email
        send_otp_email(
            to_email=email,
            user_name=user["UserName"] or canonical_user_id,
            otp_code=otp_code,
            purpose="Account Activation & Password Setup",
        )

        parts = email.split("@")
        name_p = parts[0]
        dom_p = parts[1] if len(parts) > 1 else ""
        masked = name_p[:2] + "***" + (name_p[-1] if len(name_p) > 2 else "") + f"@{dom_p}"

        return FirstTimeActivateResponse(
            status="success",
            message=f"An activation code has been sent to {masked}",
            email_masked=masked,
        )

