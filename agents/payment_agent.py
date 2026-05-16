"""
payment_agent.py — Payment, Receipt, and Contra voucher entry in Tally
Supports cash, bank, and UPI payments.
"""

from modules.tally_connector import send_to_tally
from modules.validators import PaymentInput, safe_xml_string
from pydantic import ValidationError


def xml_payment(date: str, party: str, amount: float,
                bank_ledger: str = "Bank Account", narration: str = "") -> str:
    """Build XML for a payment voucher (money going out)."""
    safe_narration = safe_xml_string(narration)
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<VOUCHER VCHTYPE="Payment" ACTION="Create">
<DATE>{date}</DATE>
<VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>
<NARRATION>{safe_narration}</NARRATION>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{party}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{bank_ledger}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
</VOUCHER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def xml_receipt(date: str, party: str, amount: float,
                bank_ledger: str = "Bank Account", narration: str = "") -> str:
    """Build XML for a receipt voucher (money coming in)."""
    safe_narration = safe_xml_string(narration)
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<VOUCHER VCHTYPE="Receipt" ACTION="Create">
<DATE>{date}</DATE>
<VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME>
<NARRATION>{safe_narration}</NARRATION>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{bank_ledger}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{party}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
</VOUCHER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def xml_contra(date: str, from_ledger: str, to_ledger: str, amount: float) -> str:
    """
    Build XML for a contra voucher (cash ↔ bank transfer).
    from_ledger: the account being credited (e.g., Bank Account)
    to_ledger:   the account being debited  (e.g., Cash)
    """
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<VOUCHER VCHTYPE="Contra" ACTION="Create">
<DATE>{date}</DATE>
<VOUCHERTYPENAME>Contra</VOUCHERTYPENAME>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{to_ledger}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <AMOUNT>-{amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
  <LEDGERNAME>{from_ledger}</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>{amount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
</VOUCHER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def create_payment(date: str, party: str, amount: float,
                   bank_ledger: str = "Bank Account", narration: str = "") -> dict:
    """Validate and post a payment voucher to Tally."""
    try:
        validated = PaymentInput(date=date, party=party, amount=amount,
                                 bank_ledger=bank_ledger, narration=narration)
        xml = xml_payment(validated.date, validated.party, validated.amount,
                          validated.bank_ledger, validated.narration)
        result = send_to_tally(xml)
        return {"success": result["success"],
                "message": f"Payment of ₹{amount} to {party} posted" if result["success"] else result["error"],
                "data": {"date": date, "party": party, "amount": amount, "via": bank_ledger}}
    except ValidationError as e:
        return {"success": False, "message": str(e), "data": {}}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}


def create_receipt(date: str, party: str, amount: float,
                   bank_ledger: str = "Bank Account", narration: str = "") -> dict:
    """Validate and post a receipt voucher to Tally."""
    try:
        validated = PaymentInput(date=date, party=party, amount=amount,
                                 bank_ledger=bank_ledger, narration=narration)
        xml = xml_receipt(validated.date, validated.party, validated.amount,
                          validated.bank_ledger, validated.narration)
        result = send_to_tally(xml)
        return {"success": result["success"],
                "message": f"Receipt of ₹{amount} from {party} posted" if result["success"] else result["error"],
                "data": {"date": date, "party": party, "amount": amount, "via": bank_ledger}}
    except ValidationError as e:
        return {"success": False, "message": str(e), "data": {}}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}


def create_contra(date: str, from_ledger: str, to_ledger: str, amount: float) -> dict:
    """Post a contra entry (cash-bank transfer) to Tally."""
    try:
        if amount <= 0:
            return {"success": False, "message": "Amount must be positive", "data": {}}
        xml = xml_contra(date, from_ledger, to_ledger, round(amount, 2))
        result = send_to_tally(xml)
        return {"success": result["success"],
                "message": f"Contra ₹{amount} from {from_ledger} to {to_ledger}" if result["success"] else result["error"],
                "data": {"date": date, "from": from_ledger, "to": to_ledger, "amount": amount}}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}
