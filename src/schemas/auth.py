from pydantic import BaseModel
from typing import Optional, List

class LoginRequest(BaseModel):
    user_id: str
    password: str
    company_code: str
    location_code: str
    fin_year_code: str

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
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

class DropdownOption(BaseModel):
    id: str
    name: str

class AuthMetaResponse(BaseModel):
    companies: List[DropdownOption]
    locations: List[DropdownOption]
    financial_years: List[DropdownOption]
