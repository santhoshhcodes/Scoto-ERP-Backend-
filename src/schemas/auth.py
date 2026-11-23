from pydantic import BaseModel
from typing import Optional, List

class LoginRequest(BaseModel):
    user_id: str
    password: str
    company_code: str
    location_code: str
    fin_year_code: str
    device_id: Optional[str] = None
    browser_agent: Optional[str] = None

class UserProfile(BaseModel):
    user_id: str
    user_name: str
    role_code: str
    designation: Optional[str] = None
    profile_img: Optional[str] = None
    company_code: str
    company_name: str
    location_code: str
    location_name: str
    fin_year_code: str
    fin_year: str

class LoginResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    user: Optional[UserProfile] = None
    requires_2fa: bool = False
    email_masked: Optional[str] = None
    message: Optional[str] = None

class DropdownOption(BaseModel):
    id: str
    name: str

class AuthMetaResponse(BaseModel):
    companies: List[DropdownOption]
    locations: List[DropdownOption]
    financial_years: List[DropdownOption]

class ForgotPasswordRequest(BaseModel):
    user_id: str
    company_code: str
    location_code: str

class ForgotPasswordResponse(BaseModel):
    status: str = "success"
    message: str
    email_masked: str

class VerifyOtpRequest(BaseModel):
    user_id: str
    company_code: str
    location_code: str
    otp_code: str

class VerifyOtpResponse(BaseModel):
    status: str = "success"
    message: str
    verified: bool

class ResetPasswordRequest(BaseModel):
    user_id: str
    company_code: str
    location_code: str
    otp_code: str
    new_password: str

class ResetPasswordResponse(BaseModel):
    status: str = "success"
    message: str

class ActivateAccountRequest(BaseModel):
    user_id: str
    company_code: str
    location_code: str
    otp_code: str
    new_password: str

class VerifyDeviceOtpRequest(BaseModel):
    user_id: str
    company_code: str
    location_code: str
    fin_year_code: str
    otp_code: str
    device_id: str
    browser_agent: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    user_id: str
    company_code: str
    location_code: str
    current_password: str
    new_password: str

class ChangePasswordResponse(BaseModel):
    status: str = "success"
    message: str

class FirstTimeActivateRequest(BaseModel):
    user_id: str
    company_code: str
    location_code: str

class FirstTimeActivateResponse(BaseModel):
    status: str = "success"
    message: str
    email_masked: str


