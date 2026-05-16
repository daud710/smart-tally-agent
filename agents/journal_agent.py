"""
journal_agent.py — Journal voucher entry in Tally
Validates that debit = credit before sending to Tally.
"""

from modules.tally_connector import send_to_tally
from modules.validators import JournalInput, safe_xml_string
from pydantic import ValidationError


def xml_journal(date: str, debit_ledger: str, credit_ledger: str,
                amount: float, narration: str = "") -> str:
    """Build XML for a journal voucher."""
    safe_narration = safe_xml_string(narration)
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<VOUCHER VCHTYPE="Journal" ACTION="Create">
<DATE>{date}</DATE>
<VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>
<NARRATION>{safe_narration}</NARRATION>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{debit_ledger}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{credit_ledger}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
</VOUCHER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def xml_journal_multi(date: str, entries: list, narration: str = "") -> str:
    """
    Build XML for a journal with multiple debit/credit lines.
    
    entries: list of {"ledger": str, "amount": float, "type": "debit"|"credit"}
    Validates that total debits == total credits before building XML.
    """
    total_debit  = sum(e["amount"] for e in entries if e["type"] == "debit")
    total_credit = sum(e["amount"] for e in entries if e["type"] == "credit")

    if round(total_debit, 2) != round(total_credit, 2):
        raise ValueError(f"Debit-Credit imbalance: Debit ₹{total_debit} ≠ Credit ₹{total_credit}")

    lines = []
    for entry in entries:
        is_positive = "Yes" if entry["type"] == "debit" else "No"
        sign = "-" if entry["type"] == "debit" else ""
        lines.append(f"""<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{entry['ledger']}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>{is_positive}</ISDEEMEDPOSITIVE>
  <AMOUNT>{sign}{entry['amount']}</AMOUNT>
</ALLLEDGERENTRIES.LIST>""")

    safe_narration = safe_xml_string(narration)
    entries_xml = "\n".join(lines)

    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<VOUCHER VCHTYPE="Journal" ACTION="Create">
<DATE>{date}</DATE>
<VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>
<NARRATION>{safe_narration}</NARRATION>
{entries_xml}
</VOUCHER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def create_journal(date: str, debit_ledger: str, credit_ledger: str,
                   amount: float, narration: str = "") -> dict:
    """Validate debit-credit balance and post a journal entry to Tally."""
    try:
        validated = JournalInput(
            date=date, debit_ledger=debit_ledger, credit_ledger=credit_ledger,
            amount=amount, narration=narration
        )
        xml = xml_journal(validated.date, validated.debit_ledger,
                          validated.credit_ledger, validated.amount, validated.narration)
        result = send_to_tally(xml)
        return {
            "success": result["success"],
            "message": f"Journal entry posted — Dr: {debit_ledger}, Cr: {credit_ledger}, ₹{amount}" if result["success"] else result["error"],
            "data": {"date": date, "debit": debit_ledger, "credit": credit_ledger, "amount": amount}
        }
    except ValidationError as e:
        return {"success": False, "message": str(e), "data": {}}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}


def create_journal_multi(date: str, entries: list, narration: str = "") -> dict:
    """Post a compound journal entry with multiple lines to Tally."""
    try:
        xml = xml_journal_multi(date, entries, narration)
        result = send_to_tally(xml)
        total_debit = sum(e["amount"] for e in entries if e["type"] == "debit")
        return {
            "success": result["success"],
            "message": f"Compound journal posted — {len(entries)} lines, Total: ₹{total_debit}" if result["success"] else result["error"],
            "data": {"date": date, "lines": len(entries), "total": total_debit}
        }
    except ValueError as e:
        return {"success": False, "message": str(e), "data": {}}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}
