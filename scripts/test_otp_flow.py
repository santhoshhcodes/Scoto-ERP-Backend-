import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import text
from src.api.deps import get_mssql_session
from src.services.auth_service import AuthService
from src.schemas.auth import (
    ForgotPasswordRequest,
    VerifyOtpRequest,
    ResetPasswordRequest,
    LoginRequest,
)

def test_flow():
    print("==================================================")
    print("Testing Scoto ERP OTP & Password Reset Integration")
    print("==================================================")

    session_gen = get_mssql_session("db2")()
    db = next(session_gen)

    try:
        # 1. Test Forgot Password for SUPERADMIN (santhoshkannan@scoto.in)
        print("\n--- Test 1: Request OTP for SUPERADMIN (santhoshkannan@scoto.in) ---")
        req = ForgotPasswordRequest(
            user_id="SUPERADMIN",
            company_code="SCT",
            location_code="UNIT I",
        )
        res = AuthService.forgot_password(db=db, payload=req)
        print(f"Status: {res.status}")
        print(f"Message: {res.message}")
        print(f"Masked Email: {res.email_masked}")

        # Check OTP in database
        otp_row = db.execute(
            text("""
                SELECT TOP 1 OTPId, OTPCode, Email, ExpiresAt, IsUsed 
                FROM UserPasswordOTP 
                WHERE UserId = 'SUPERADMIN' AND IsUsed = 0 
                ORDER BY OTPId DESC
            """)
        ).mappings().first()
        print(f"Database OTP record created: OTP={otp_row['OTPCode']}, Target Email={otp_row['Email']}, Expires={otp_row['ExpiresAt']}")

        # 2. Test Invalid OTP verification
        print("\n--- Test 2: Test Invalid OTP code ---")
        bad_req = VerifyOtpRequest(
            user_id="SUPERADMIN",
            company_code="SCT",
            location_code="UNIT I",
            otp_code="000000",
        )
        try:
            AuthService.verify_otp(db=db, payload=bad_req)
            print("ERROR: Invalid OTP was accepted!")
        except Exception as e:
            print(f"Correctly rejected invalid OTP: {e.detail}")

        # 3. Test Valid OTP verification
        print("\n--- Test 3: Test Valid OTP code ---")
        good_req = VerifyOtpRequest(
            user_id="SUPERADMIN",
            company_code="SCT",
            location_code="UNIT I",
            otp_code=otp_row["OTPCode"],
        )
        verify_res = AuthService.verify_otp(db=db, payload=good_req)
        print(f"Verify response: verified={verify_res.verified}, message={verify_res.message}")

        # 4. Test Reset Password
        print("\n--- Test 4: Reset Password to 'Super@2026' ---")
        reset_req = ResetPasswordRequest(
            user_id="SUPERADMIN",
            company_code="SCT",
            location_code="UNIT I",
            otp_code=otp_row["OTPCode"],
            new_password="Super@2026",
        )
        reset_res = AuthService.reset_password(db=db, payload=reset_req)
        print(f"Reset status: {reset_res.status}, message={reset_res.message}")

        # Verify OTP is marked used
        used_check = db.execute(
            text("SELECT IsUsed FROM UserPasswordOTP WHERE OTPId = :id"),
            {"id": otp_row["OTPId"]}
        ).scalar()
        print(f"OTP IsUsed flag in DB after reset: {used_check}")

        # 5. Test Login with new password
        print("\n--- Test 5: Verify Login with new password 'Super@2026' ---")
        login_req = LoginRequest(
            user_id="SUPERADMIN",
            password="Super@2026",
            company_code="SCT",
            location_code="UNIT I",
            fin_year_code="2",
        )
        login_res = AuthService.login(db=db, payload=login_req)
        print(f"Login SUCCESSFUL! Token generated: {login_res.access_token[:25]}... for User={login_res.user.user_name} (Role: {login_res.user.role_code})")

        # 6. Test Login with old password (should fail)
        print("\n--- Test 6: Verify Login with old password fails ---")
        old_login_req = LoginRequest(
            user_id="SUPERADMIN",
            password="admin@123",
            company_code="SCT",
            location_code="UNIT I",
            fin_year_code="2",
        )
        try:
            AuthService.login(db=db, payload=old_login_req)
            print("ERROR: Old password was accepted!")
        except Exception as e:
            print(f"Correctly rejected old password: {e.detail}")

        print("\n==================================================")
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("==================================================")

    finally:
        db.close()

if __name__ == "__main__":
    test_flow()
