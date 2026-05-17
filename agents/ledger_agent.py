"""
ledger_agent.py — Create ledgers in Tally individually or in bulk from Excel
Supports bank details, opening balance, credit limit, mobile, email, GSTIN, state.
"""

from modules.tally_connector import send_to_tally
from modules.validators import LedgerInput, safe_xml_string
from modules.excel_handler import read_ledger_excel
from pydantic import ValidationError

TALLY_GROUPS = [
    "Sundry Debtors",
    "Sundry Creditors",
    "Bank Accounts",
    "Cash-in-Hand",
    "Sales Accounts",
    "Purchase Accounts",
    "Duties & Taxes",
    "Indirect Expenses",
    "Indirect Incomes",
    "Direct Expenses",
    "Direct Incomes",
    "Capital Account",
    "Loans (Liability)",
    "Fixed Assets",
    "Current Assets",
    "Current Liabilities",
    "Investments",
    "Suspense A/c",
    "Provisions",
    "Reserves & Surplus",
    "Secured Loans",
    "Unsecured Loans",
    "Stock-in-Hand",
    "Deposits (Asset)",
    "Loans & Advances (Asset)",
    "Miscellaneous Expenses (Asset)",
    "Branch / Divisions",
    "Salary Payable",
    "TDS Payable",
]


def xml_create_ledger(
    name: str,
    parent: str,
    gstin: str = "",
    state: str = "",
    opening_balance: float = 0.0,
    bank_ac_no: str = "",
    bank_name: str = "",
    ifsc: str = "",
    mobile: str = "",
    email: str = "",
    credit_limit: float = 0.0,
    credit_days: int = 0,
) -> str:
    """Build XML to create a single ledger in Tally with full details."""
    safe_name = safe_xml_string(name)

    gstin_tag  = f"<GSTIN>{safe_xml_string(gstin)}</GSTIN>" if gstin else ""
    state_tag  = f"<STATENAME>{safe_xml_string(state)}</STATENAME>" if state else ""
    ob_tag     = f"<OPENINGBALANCE>{opening_balance}</OPENINGBALANCE>" if opening_balance else ""
    mobile_tag = f"<LEDMOBILE>{safe_xml_string(mobile)}</LEDMOBILE>" if mobile else ""
    email_tag  = f"<EMAIL>{safe_xml_string(email)}</EMAIL>" if email else ""
    cl_tag     = f"<CREDITLIMIT>{credit_limit}</CREDITLIMIT>" if credit_limit else ""
    cd_tag     = f"<BILLCREDITPERIOD>{credit_days} Days</BILLCREDITPERIOD>" if credit_days else ""

    # Bank details — only relevant for Bank Accounts group
    bank_tags = ""
    if parent == "Bank Accounts" and bank_ac_no:
        bank_tags = f"""<BANKACNO>{safe_xml_string(bank_ac_no)}</BANKACNO>
<BANKNAME>{safe_xml_string(bank_name)}</BANKNAME>
<IFSCODE>{safe_xml_string(ifsc)}</IFSCODE>"""

    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>All Masters</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<LEDGER NAME="{safe_name}" ACTION="Create">
<NAME>{safe_name}</NAME>
<PARENT>{parent}</PARENT>
{gstin_tag}
{state_tag}
{ob_tag}
{mobile_tag}
{email_tag}
{cl_tag}
{cd_tag}
{bank_tags}
</LEDGER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def create_single_ledger(
    name: str,
    parent: str,
    gstin: str = "",
    state: str = "",
    opening_balance: float = 0.0,
    bank_ac_no: str = "",
    bank_name: str = "",
    ifsc: str = "",
    mobile: str = "",
    email: str = "",
    credit_limit: float = 0.0,
    credit_days: int = 0,
) -> dict:
    """Validate and create a single ledger in Tally."""
    try:
        validated = LedgerInput(name=name, parent=parent, gstin=gstin, state=state)
        xml = xml_create_ledger(
            name=validated.name,
            parent=validated.parent,
            gstin=validated.gstin,
            state=validated.state,
            opening_balance=opening_balance,
            bank_ac_no=bank_ac_no,
            bank_name=bank_name,
            ifsc=ifsc,
            mobile=mobile,
            email=email,
            credit_limit=credit_limit,
            credit_days=credit_days,
        )
        result = send_to_tally(xml)
        if result["success"]:
            return {
                "success": True,
                "message": f"Ledger '{name}' created successfully",
                "data": {"name": name, "parent": parent},
            }
        return {"success": False, "message": result.get("error", "Tally error"), "data": {}}
    except ValidationError as e:
        return {"success": False, "message": str(e), "data": {}}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}


def create_bulk_ledgers(ledger_list: list) -> dict:
    """Create multiple ledgers in Tally from a list of dicts."""
    results = []
    seen_names = set()

    for ledger in ledger_list:
        name = ledger.get("name", "").strip()
        if not name:
            results.append({"ledger": name, "status": "skipped", "message": "Empty ledger name"})
            continue
        if name.lower() in seen_names:
            results.append({"ledger": name, "status": "skipped", "message": "Duplicate in batch"})
            continue
        seen_names.add(name.lower())

        result = create_single_ledger(
            name=name,
            parent=ledger.get("parent", ""),
            gstin=ledger.get("gstin", ""),
            state=ledger.get("state", ""),
            opening_balance=float(ledger.get("opening_balance", 0) or 0),
            bank_ac_no=ledger.get("bank_ac_no", ""),
            bank_name=ledger.get("bank_name", ""),
            ifsc=ledger.get("ifsc", ""),
            mobile=ledger.get("mobile", ""),
            email=ledger.get("email", ""),
            credit_limit=float(ledger.get("credit_limit", 0) or 0),
            credit_days=int(ledger.get("credit_days", 0) or 0),
        )
        status = "success" if result["success"] else "failed"
        results.append({"ledger": name, "status": status, "message": result["message"]})

    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count  = sum(1 for r in results if r["status"] == "failed")
    skipped_count = sum(1 for r in results if r["status"] == "skipped")

    return {
        "total":   len(ledger_list),
        "success": success_count,
        "failed":  failed_count,
        "skipped": skipped_count,
        "details": results,
    }


def create_ledgers_from_excel(file_bytes) -> dict:
    """Read an Excel file and create all ledgers in Tally."""
    read_result = read_ledger_excel(file_bytes)
    if not read_result["success"]:
        return {
            "total": 0, "success": 0, "failed": 0, "skipped": 0,
            "details": [], "error": read_result["error"],
        }
    return create_bulk_ledgers(read_result["data"])
