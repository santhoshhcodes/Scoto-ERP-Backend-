"""
Utilities Package for Scoto Backend.
Exports security, datetime, formatting, database, response, and excel helpers.
"""

from src.utils.datetime_helpers import (
    format_duration_hhmm,
    format_duration_human,
    get_financial_year,
    get_financial_year_dates,
    get_month_date_range,
    month_dates,
    parse_date_safe,
    parse_datetime_safe,
    parse_time_safe,
)
from src.utils.db_helpers import (
    escape_like_term,
    row_to_dict,
    rows_to_dicts,
    serialize_db_record,
    serialize_db_val,
)
from src.utils.excel_helpers import (
    BorderAccumulator,
    make_alignment,
    style_cell,
)
from src.utils.formatters import (
    clean_string,
    format_inr,
    num_to_indian_words,
    to_decimal,
    to_float,
)
from src.utils.response import (
    error_response,
    paginated_response,
    success_response,
)
from src.utils.security import (
    ALGORITHM,
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
    get_password_hash,
    pwd_context,
    verify_legacy_password,
    verify_password,
)

__all__ = [
    # Security
    "ALGORITHM",
    "DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES",
    "pwd_context",
    "verify_legacy_password",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_access_token",
    # Datetime
    "format_duration_hhmm",
    "format_duration_human",
    "parse_date_safe",
    "parse_datetime_safe",
    "parse_time_safe",
    "get_month_date_range",
    "month_dates",
    "get_financial_year",
    "get_financial_year_dates",
    # Formatters
    "to_float",
    "to_decimal",
    "num_to_indian_words",
    "format_inr",
    "clean_string",
    # Database
    "row_to_dict",
    "rows_to_dicts",
    "serialize_db_val",
    "serialize_db_record",
    "escape_like_term",
    # Response
    "success_response",
    "error_response",
    "paginated_response",
    # Excel
    "BorderAccumulator",
    "make_alignment",
    "style_cell",
]
