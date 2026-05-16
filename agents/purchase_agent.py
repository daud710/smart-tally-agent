"""
purchase_agent.py — Purchase voucher and debit note entry in Tally
Supports GST with Input Tax Credit (ITC) tracking.
"""

from modules.tally_connector import send_to_tally
from modules.validators import VoucherInput, safe_xml_string
from pydantic import ValidationError


def xml_purchase_voucher(date: str, vendor: str, amount: float,
                         gst_pct: float, narration: str = "",
                         is_interstate: bool = False) -> str:
    """Build XML for a GST purchase voucher with ITC."""
    base = round(amount / (1 + gst_pct / 100), 2)
    gst_amount = round(amount - base, 2)
    safe_narration = safe_xml_string(narration)

    if is_interstate:
        tax_entries = f"""<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Input IGST</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{gst_amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>"""
    else:
        cgst = sgst = round(gst_amount / 2, 2)
        tax_entries = f"""<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Input CGST</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{cgst}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Input SGST</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{sgst}</AMOUNT>
</ALLLEDGERENTRIES.LIST>"""

    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<VOUCHER VCHTYPE="Purchase" ACTION="Create">
<DATE>{date}</DATE>
<VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
<NARRATION>{safe_narration}</NARRATION>
<PARTYLEDGERNAME>{vendor}</PARTYLEDGERNAME>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{vendor}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Purchase</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{base}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
{tax_entries}
</VOUCHER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def xml_debit_note(date: str, vendor: str, amount: float,
                   gst_pct: float, narration: str = "") -> str:
    """Build XML for a debit note (purchase return)."""
    base = round(amount / (1 + gst_pct / 100), 2)
    cgst = sgst = round((amount - base) / 2, 2)
    safe_narration = safe_xml_string(narration)

    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<VOUCHER VCHTYPE="Debit Note" ACTION="Create">
<DATE>{date}</DATE>
<VOUCHERTYPENAME>Debit Note</VOUCHERTYPENAME>
<NARRATION>{safe_narration}</NARRATION>
<PARTYLEDGERNAME>{vendor}</PARTYLEDGERNAME>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{vendor}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Purchase</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{base}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Input CGST</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{cgst}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Input SGST</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{sgst}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
</VOUCHER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def create_purchase_voucher(date: str, vendor: str, amount: float,
                            gst_pct: float, narration: str = "",
                            is_interstate: bool = False) -> dict:
    """Validate and post a purchase voucher to Tally."""
    try:
        validated = VoucherInput(date=date, party=vendor, amount=amount,
                                 gst_pct=gst_pct, narration=narration)
        xml = xml_purchase_voucher(validated.date, validated.party, validated.amount,
                                   validated.gst_pct, validated.narration, is_interstate)
        result = send_to_tally(xml)
        base = round(validated.amount / (1 + validated.gst_pct / 100), 2)
        itc  = round(validated.amount - base, 2)
        return {"success": result["success"],
                "message": f"Purchase posted — Vendor: {vendor}, ITC: ₹{itc}" if result["success"] else result["error"],
                "data": {"date": date, "vendor": vendor, "amount": amount, "itc": itc}}
    except ValidationError as e:
        return {"success": False, "message": str(e), "data": {}}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}


def create_debit_note(date: str, vendor: str, amount: float,
                      gst_pct: float, narration: str = "") -> dict:
    """Validate and post a debit note to Tally."""
    try:
        validated = VoucherInput(date=date, party=vendor, amount=amount,
                                 gst_pct=gst_pct, narration=narration)
        xml = xml_debit_note(validated.date, validated.party, validated.amount,
                             validated.gst_pct, validated.narration)
        result = send_to_tally(xml)
        return {"success": result["success"],
                "message": f"Debit note posted for {vendor}" if result["success"] else result["error"],
                "data": {"date": date, "vendor": vendor, "amount": amount}}
    except ValidationError as e:
        return {"success": False, "message": str(e), "data": {}}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}
