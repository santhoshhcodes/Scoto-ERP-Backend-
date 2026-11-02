
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.schemas.auth import (
    LoginRequest,
    LoginResponse,
    AuthMetaResponse,
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
