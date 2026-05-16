"""
gst_calculator.py — GST calculation utilities
Supports HSN-based rate lookup, CGST/SGST/IGST split, and Education Mode date validation.
"""

from datetime import datetime


# HSN code to GST rate mapping (common codes)
HSN_GST_RATES = {
    "1001": 0,   # Wheat
    "0401": 0,   # Milk
    "0402": 5,   # Milk powder
    "6109": 5,   # T-shirts
    "6203": 12,  # Men's suits
    "8471": 18,  # Computers
    "8517": 18,  # Mobile phones
    "8703": 28,  # Cars
    "2402": 28,  # Cigarettes
    "9403": 18,  # Furniture
    "3004": 12,  # Medicines
    "2710": 18,  # Petrol/Diesel
    "default": 18
}


def get_gst_rate(hsn: str) -> int:
    """Return the GST rate for a given HSN code. Defaults to 18% if unknown."""
    return HSN_GST_RATES.get(str(hsn)[:4], HSN_GST_RATES["default"])


def calculate_gst(amount: float, gst_rate: float, is_interstate: bool = False) -> dict:
    """
    Calculate GST breakdown from a total (GST-inclusive) amount.
    
    Args:
        amount: Total amount including GST
        gst_rate: GST percentage (0, 5, 12, 18, or 28)
        is_interstate: True for IGST, False for CGST+SGST split
    
    Returns:
        dict with taxable, igst/cgst/sgst, gst_total, grand_total, rate
    """
    taxable = round(amount / (1 + gst_rate / 100), 2)
    gst_total = round(amount - taxable, 2)

    if is_interstate:
        return {
            "taxable":     taxable,
            "igst":        gst_total,
            "cgst":        0,
            "sgst":        0,
            "gst_total":   gst_total,
            "grand_total": amount,
            "rate":        gst_rate
        }
    else:
        half = round(gst_total / 2, 2)
        return {
            "taxable":     taxable,
            "igst":        0,
            "cgst":        half,
            "sgst":        half,
            "gst_total":   gst_total,
            "grand_total": amount,
            "rate":        gst_rate
        }


def calculate_gst_by_hsn(amount: float, hsn: str, is_interstate: bool = False) -> dict:
    """Calculate GST using HSN code to determine the rate."""
    rate = get_gst_rate(hsn)
    result = calculate_gst(amount, rate, is_interstate)
    result["hsn"] = hsn
    return result


def calculate_gst_exclusive(taxable_amount: float, gst_rate: float, is_interstate: bool = False) -> dict:
    """
    Calculate GST when the given amount is the taxable value (GST-exclusive).
    """
    gst_total = round(taxable_amount * gst_rate / 100, 2)
    grand_total = round(taxable_amount + gst_total, 2)

    if is_interstate:
        return {
            "taxable":     taxable_amount,
            "igst":        gst_total,
            "cgst":        0,
            "sgst":        0,
            "gst_total":   gst_total,
            "grand_total": grand_total,
            "rate":        gst_rate
        }
    else:
        half = round(gst_total / 2, 2)
        return {
            "taxable":     taxable_amount,
            "igst":        0,
            "cgst":        half,
            "sgst":        half,
            "gst_total":   gst_total,
            "grand_total": grand_total,
            "rate":        gst_rate
        }


def validate_education_mode_date(date_str: str) -> dict:
    """
    Validate that the date is allowed in Tally Education Mode.
    Education Mode only allows: day 1, day 2, or the last day of the month.
    
    Args:
        date_str: Date in YYYYMMDD format
    
    Returns:
        {"valid": bool, "message": str}
    """
    try:
        date = datetime.strptime(date_str, "%Y%m%d")
        day = date.day
        # Get last day of the month
        import calendar
        last_day = calendar.monthrange(date.year, date.month)[1]
        if day in [1, 2, last_day]:
            return {"valid": True, "message": f"Date {date.strftime('%d-%m-%Y')} is valid for Education Mode"}
        return {
            "valid": False,
            "message": f"Education Mode only allows day 1, 2, or {last_day} of the month. Got day {day}."
        }
    except ValueError:
        return {"valid": False, "message": f"Invalid date format: {date_str}. Use YYYYMMDD."}


def get_valid_education_dates(year: int, month: int) -> list:
    """Return the three valid dates for Education Mode for a given month."""
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    return [
        datetime(year, month, 1).strftime("%Y%m%d"),
        datetime(year, month, 2).strftime("%Y%m%d"),
        datetime(year, month, last_day).strftime("%Y%m%d"),
    ]
