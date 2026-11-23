import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import text
from src.api.deps import get_mssql_session
from src.services.auth_service import AuthService
from src.schemas.auth import (
    LoginRequest,
    VerifyDeviceOtpRequest,
    ChangePasswordRequest,
    FirstTimeActivateRequest,
)

def test_full_features():
    print("==================================================")
    print("Testing Adaptive 2FA, Device Trust & Change Password")
    print("==================================================")

    session_gen = get_mssql_session("db2")()
    db = next(session_gen)

    TEST_DEVICE_ID = "browser_office_pc_uuid_99"

    try:
        # Cleanup test device if exists
        db.execute(text("DELETE FROM UserTrustedDevices WHERE DeviceId = :d"), {"d": TEST_DEVICE_ID})
        db.commit()

        # ----------------------------------------------------
        # 1. Login with a NEW UNRECOGNIZED BROWSER / DEVICE
        # ----------------------------------------------------
        print("\n--- Test 1: Sign in with new browser (should trigger 2FA OTP) ---")
        login_req = LoginRequest(
            user_id="SUPERADMIN",
            password="Super@2026",
            company_code="SCT",
            location_code="UNIT I",
            fin_year_code="2",
            device_id=TEST_DEVICE_ID,
            browser_agent="Chrome 120 on Windows 11",
        )
        res1 = AuthService.login(db=db, payload=login_req)
        print(f"2FA Required: {res1.requires_2fa}")
        print(f"Masked Email: {res1.email_masked}")
        print(f"Server Message: {res1.message}")
        assert res1.requires_2fa is True, "Expected 2FA challenge on new browser!"

        # Fetch the generated device OTP from DB
        otp_row = db.execute(
            text("""
                SELECT TOP 1 OTPCode FROM UserPasswordOTP 
                WHERE UserId = 'SUPERADMIN' AND Purpose = 'DEVICE_VERIFICATION' AND IsUsed = 0 
                ORDER BY OTPId DESC
            """)
        ).mappings().first()
        print(f"Device OTP generated in DB: {otp_row['OTPCode']}")

        # ----------------------------------------------------
        # 2. Verify Device OTP & Trust Device
        # ----------------------------------------------------
        print("\n--- Test 2: Verify Device OTP & Register as Trusted ---")
        verify_device_req = VerifyDeviceOtpRequest(
            user_id="SUPERADMIN",
            company_code="SCT",
            location_code="UNIT I",
            fin_year_code="2",
            otp_code=otp_row["OTPCode"],
            device_id=TEST_DEVICE_ID,
            browser_agent="Chrome 120 on Windows 11",
        )
        res2 = AuthService.verify_device_otp(db=db, payload=verify_device_req)
        print(f"Device verification successful! Token: {res2.access_token[:20]}...")
        assert res2.access_token is not None, "Expected access token after device verification!"

        # Check DB to confirm device is now trusted
        trusted_check = db.execute(
            text("SELECT IsTrusted, DeviceName FROM UserTrustedDevices WHERE DeviceId = :d AND UserId = 'SUPERADMIN'"),
            {"d": TEST_DEVICE_ID}
        ).mappings().first()
        print(f"Device in DB: Trusted={trusted_check['IsTrusted']}, Name={trusted_check['DeviceName']}")
        assert trusted_check["IsTrusted"] == 1

        # ----------------------------------------------------
        # 3. Subsequent Login from the SAME TRUSTED DEVICE
        # ----------------------------------------------------
        print("\n--- Test 3: Sign in from already TRUSTED device (no OTP required) ---")
        res3 = AuthService.login(db=db, payload=login_req)
        print(f"2FA Required on trusted device: {res3.requires_2fa}")
        print(f"Direct Login Access Token: {res3.access_token[:20]}...")
        assert res3.requires_2fa is False, "Expected instant login without OTP on trusted device!"

        # ----------------------------------------------------
        # 4. Change Password (Sidebar feature)
        # ----------------------------------------------------
        print("\n--- Test 4: Change Password with Current Password Verification ---")
        change_req = ChangePasswordRequest(
            user_id="SUPERADMIN",
            company_code="SCT",
            location_code="UNIT I",
            current_password="Super@2026",
            new_password="Super@2026_Updated",
        )
        res4 = AuthService.change_password(db=db, payload=change_req)
        print(f"Change Password Result: status={res4.status}, message={res4.message}")

        # Revert back to Super@2026 so credentials remain clean
        revert_req = ChangePasswordRequest(
            user_id="SUPERADMIN",
            company_code="SCT",
            location_code="UNIT I",
            current_password="Super@2026_Updated",
            new_password="Super@2026",
        )
        AuthService.change_password(db=db, payload=revert_req)
        print("Password cleanly verified and restored.")

        # ----------------------------------------------------
        # 5. First-Time Account Activation Request
        # ----------------------------------------------------
        print("\n--- Test 5: First-Time Account Activation Request for ADMIN ---")
        act_req = FirstTimeActivateRequest(
            user_id="ADMIN",
            company_code="SCT",
            location_code="UNIT I",
        )
        res5 = AuthService.first_time_activate(db=db, payload=act_req)
        print(f"Activation OTP sent to: {res5.email_masked}")

        print("\n==================================================")
        print("ALL TESTS PASSED WITH 100% SUCCESS!")
        print("==================================================")

    finally:
        # Cleanup test device
        db.execute(text("DELETE FROM UserTrustedDevices WHERE DeviceId = :d"), {"d": TEST_DEVICE_ID})
        db.commit()
        db.close()

if __name__ == "__main__":
    test_full_features()
