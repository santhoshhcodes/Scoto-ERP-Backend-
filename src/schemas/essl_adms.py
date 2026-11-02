from pydantic import BaseModel, Field


class ESSLAttendancePunch(BaseModel):
    employee_code: str = Field(min_length=1, max_length=100)
    punch_time: str = Field(min_length=1, max_length=50)
    device_serial: str | None = None
    punch_state: str | None = None
    verify_type: str | None = None
    raw_data: str | None = None