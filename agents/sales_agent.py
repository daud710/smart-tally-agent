"""
sales_agent.py — Sales voucher and credit note entry in Tally
Supports GST (CGST+SGST for intrastate, IGST for interstate) and cash/credit sales.
"""

from modules.tally_connector import send_to_tally
from modules.validators import VoucherInput, safe_xml_string
from modules.excel_handler import read_sales_excel
from pydantic import ValidationError


def xml_sales_voucher(date: str, party: str, amount: float,
                      gst_pct: float, narration: str = "",
                      is_interstate: bool = False) -> str:
    """Build XML for a GST sales voucher."""
    base  = round(amount / (1 + gst_pct / 100), 2)
    gst_amount = round(amount - base, 2)
    safe_narration = safe_xml_string(narration)

    if is_interstate:
        tax_entries = f"""<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Output IGST</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{gst_amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>"""
    else:
        cgst = sgst = round(gst_amount / 2, 2)
        tax_entries = f"""<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Output CGST</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{cgst}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Output SGST</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{sgst}</AMOUNT>
</ALLLEDGERENTRIES.LIST>"""

    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<VOUCHER VCHTYPE="Sales" ACTION="Create">
<DATE>{date}</DATE>
<VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
<NARRATION>{safe_narration}</NARRATION>
<PARTYLEDGERNAME>{party}</PARTYLEDGERNAME>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{party}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Sales</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{base}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
{tax_entries}
</VOUCHER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def xml_credit_note(date: str, party: str, amount: float,
                    gst_pct: float, narration: str = "") -> str:
    """Build XML for a credit note (sales return)."""
    base = round(amount / (1 + gst_pct / 100), 2)
    cgst = sgst = round((amount - base) / 2, 2)
    safe_narration = safe_xml_string(narration)

    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<VOUCHER VCHTYPE="Credit Note" ACTION="Create">
<DATE>{date}</DATE>
<VOUCHERTYPENAME>Credit Note</VOUCHERTYPENAME>
<NARRATION>{safe_narration}</NARRATION>
<PARTYLEDGERNAME>{party}</PARTYLEDGERNAME>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{party}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Sales</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{base}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Output CGST</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{cgst}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>Output SGST</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{sgst}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
</VOUCHER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def create_sales_voucher(date: str, party: str, amount: float,
                         gst_pct: float, narration: str = "",
                         is_interstate: bool = False) -> dict:
    """Validate and post a sales voucher to Tally."""
    try:
        validated = VoucherInput(date=date, party=party, amount=amount,
                                 gst_pct=gst_pct, narration=narration)
        xml = xml_sales_voucher(validated.date, validated.party, validated.amount,
                                validated.gst_pct, validated.narration, is_interstate)
        result = send_to_tally(xml)
        base = round(validated.amount / (1 + validated.gst_pct / 100), 2)
        gst_amount = round(validated.amount - base, 2)
        msg = f"Sales voucher posted — Party: {party}, Amount: ₹{amount}, GST: ₹{gst_amount}"
        return {"success": result["success"],
                "message": msg if result["success"] else result["error"],
                "data": {"date": date, "party": party, "amount": amount,
                         "taxable": base, "gst": gst_amount}}
    except ValidationError as e:
        return {"success": False, "message": str(e), "data": {}}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}


def create_credit_note(date: str, party: str, amount: float,
                       gst_pct: float, narration: str = "") -> dict:
    """Validate and post a credit note to Tally."""
    try:
        validated = VoucherInput(date=date, party=party, amount=amount,
                                 gst_pct=gst_pct, narration=narration)
        xml = xml_credit_note(validated.date, validated.party, validated.amount,
                              validated.gst_pct, validated.narration)
        result = send_to_tally(xml)
        return {"success": result["success"],
                "message": f"Credit note posted for {party}" if result["success"] else result["error"],
                "data": {"date": date, "party": party, "amount": amount}}
    except ValidationError as e:
        return {"success": False, "message": str(e), "data": {}}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}


def create_bulk_sales(file_bytes) -> dict:
    """Create multiple sales vouchers from an uploaded Excel file."""
    read_result = read_sales_excel(file_bytes)
    if not read_result["success"]:
        return {"total": 0, "success": 0, "failed": 0, "details": [], "error": read_result["error"]}

    results = []
    for row in read_result["data"]:
        r = create_sales_voucher(
            date=row["date"], party=row["party"],
            amount=row["amount"], gst_pct=row["gst_pct"],
            narration=row.get("narration", "")
        )
        results.append({"party": row["party"], "amount": row["amount"],
                         "status": "success" if r["success"] else "failed",
                         "message": r["message"]})

    success_count = sum(1 for r in results if r["status"] == "success")
    return {"total": len(results), "success": success_count,
            "failed": len(results) - success_count, "details": results}
