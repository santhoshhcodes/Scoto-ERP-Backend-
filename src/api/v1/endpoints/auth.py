
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.schemas.auth import (
    LoginRequest,
    LoginResponse,
    AuthMetaResponse,
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
from src.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get(
    "/meta",
    response_model=AuthMetaResponse,
)
def get_auth_metadata(
    company_code: Optional[str] = None,
    location_code: Optional[str] = None,
    db: Session = Depends(get_mssql_session("db2")),
) -> AuthMetaResponse:
    return AuthService.get_auth_metadata(
        db=db,
        company_code=company_code,
        location_code=location_code,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_mssql_session("db2")),
) -> LoginResponse:
    return AuthService.login(
        db=db,
        payload=payload,
    )


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_mssql_session("db2")),
) -> ForgotPasswordResponse:
    return AuthService.forgot_password(
        db=db,
        payload=payload,
    )


@router.post(
    "/verify-otp",
    response_model=VerifyOtpResponse,
)
def verify_otp(
    payload: VerifyOtpRequest,
    db: Session = Depends(get_mssql_session("db2")),
) -> VerifyOtpResponse:
    return AuthService.verify_otp(
        db=db,
        payload=payload,
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_mssql_session("db2")),
) -> ResetPasswordResponse:
    return AuthService.reset_password(
        db=db,
        payload=payload,
    )


@router.post(
    "/activate-account",
    response_model=ResetPasswordResponse,
)
def activate_account(
    payload: ActivateAccountRequest,
    db: Session = Depends(get_mssql_session("db2")),
) -> ResetPasswordResponse:
    return AuthService.activate_account(
        db=db,
        payload=payload,
    )


@router.post(
    "/verify-device-otp",
    response_model=LoginResponse,
)
def verify_device_otp(
    payload: VerifyDeviceOtpRequest,
    db: Session = Depends(get_mssql_session("db2")),
) -> LoginResponse:
    return AuthService.verify_device_otp(
        db=db,
        payload=payload,
    )


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_mssql_session("db2")),
) -> ChangePasswordResponse:
    return AuthService.change_password(
        db=db,
        payload=payload,
    )


@router.post(
    "/first-time-activate",
    response_model=FirstTimeActivateResponse,
)
def first_time_activate(
    payload: FirstTimeActivateRequest,
    db: Session = Depends(get_mssql_session("db2")),
) -> FirstTimeActivateResponse:
    return AuthService.first_time_activate(
        db=db,
        payload=payload,
    )


