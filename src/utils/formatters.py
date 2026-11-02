"""
Data formatting, numerical normalization, and currency converters.
Includes Indian currency number-to-words generator and INR currency formatting.
"""

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Optional, Union

CENT = Decimal("0.01")


def to_float(val: Any, default: float = 0.0) -> float:
    """
    Safely convert any value to float.
    Handles numeric strings, commas (e.g. 1,250.50), whitespace, and embedded currency symbols via regex fallback.
    """
    if val is None:
        return default
    try:
        cleaned = str(val).replace(",", "").strip()
        return float(cleaned)
    except Exception:
        try:
            cleaned = str(val).replace(",", "").strip()
            digits = re.findall(r"[-+]?\d*\.?\d+", cleaned)
            if digits:
                return float(digits[0])
        except Exception:
            pass
        return default


def to_decimal(
    val: Any,
    default: Decimal = Decimal("0.00"),
    decimal_places: int = 2,
) -> Decimal:
    """
    Safely convert a value to Decimal with half-up rounding.
    Handles commas in formatted strings.
    """
    if val is None or val == "":
        return default
    try:
        cleaned = str(val).replace(",", "").strip()
        quantizer = Decimal(10) ** -decimal_places
        return Decimal(cleaned).quantize(quantizer, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return default


def num_to_indian_words(amount: Any) -> str:
    """
    Convert an amount in INR to Indian Currency words (Crores, Lakhs, Thousands, Rupees, Paise).
    Example: 15420.50 -> 'RUPEES FIFTEEN THOUSAND FOUR HUNDRED TWENTY AND PAISE FIFTY ONLY'
    """
    try:
        val = float(amount or 0)
    except Exception:
        val = 0.0

    val = round(val, 2)
    integer_part = int(val)
    paise_part = int(round((val - integer_part) * 100))

    ones = [
        "", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE",
        "TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN",
        "SEVENTEEN", "EIGHTEEN", "NINETEEN"
    ]
    tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"]

    def below_thousand(n: int) -> list[str]:
        res = []
        if n >= 100:
            res.append(ones[n // 100] + " HUNDRED")
            n %= 100
        if 1 <= n <= 19:
            res.append(ones[n])
        elif n >= 20:
            t = tens[n // 10]
            o = ones[n % 10]
            res.append(f"{t} {o}".strip())
        return res

    if integer_part == 0:
        words = ["ZERO"]
    else:
        words = []
        crores = integer_part // 10000000
        remainder = integer_part % 10000000

        lakhs = remainder // 100000
        remainder %= 100000

        thousands = remainder // 1000
        remainder %= 1000

        if crores > 0:
            words.extend(below_thousand(crores))
            words.append("CRORE")

        if lakhs > 0:
            words.extend(below_thousand(lakhs))
            words.append("LAKH")

        if thousands > 0:
            words.extend(below_thousand(thousands))
            words.append("THOUSAND")

        if remainder > 0:
            words.extend(below_thousand(remainder))

    rupees_str = " ".join(words).strip()
    if paise_part > 0:
        paise_words = " ".join(below_thousand(paise_part)).strip()
        return f"RUPEES {rupees_str} AND PAISE {paise_words} ONLY"
    return f"RUPEES {rupees_str} ONLY"


def format_inr(
    amount: Union[Decimal, float, int, None],
    show_symbol: bool = True,
) -> str:
    """
    Format a number following the Indian numbering system.
    Example: 1234567.89 -> '₹ 12,34,567.89'
    """
    if amount is None:
        return "₹ 0.00" if show_symbol else "0.00"

    try:
        d = Decimal(str(amount)).quantize(CENT, rounding=ROUND_HALF_UP)
    except Exception:
        d = Decimal("0.00")

    sign = "-" if d < 0 else ""
    abs_d = abs(d)
    parts = str(abs_d).split(".")
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else "00"

    if len(integer_part) <= 3:
        formatted_int = integer_part
    else:
        last_three = integer_part[-3:]
        rest = integer_part[:-3]
        # Group rest by 2 digits from right to left
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        formatted_int = ",".join(groups) + "," + last_three

    result = f"{sign}{formatted_int}.{decimal_part}"
    return f"₹ {result}" if show_symbol else result


def clean_string(val: Optional[str]) -> Optional[str]:
    """Strip whitespace from string and return None if empty."""
    if val is None:
        return None
    val = str(val).strip()
    return val if val else None
