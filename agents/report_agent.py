"""
report_agent.py — Generate MIS reports and export data from Tally
Fetches trial balance, ledger statements, and other reports via XML.
"""

from modules.tally_connector import send_to_tally


def xml_trial_balance(from_date: str, to_date: str) -> str:
    """Build XML to export trial balance from Tally."""
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
<BODY><EXPORTDATA>
<REQUESTDESC>
<REPORTNAME>Trial Balance</REPORTNAME>
<STATICVARIABLES>
<SVFROMDATE>{from_date}</SVFROMDATE>
<SVTODATE>{to_date}</SVTODATE>
</STATICVARIABLES>
</REQUESTDESC>
</EXPORTDATA></BODY>
</ENVELOPE>"""


def xml_ledger_statement(ledger_name: str, from_date: str, to_date: str) -> str:
    """Build XML to export a specific ledger statement."""
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
<BODY><EXPORTDATA>
<REQUESTDESC>
<REPORTNAME>Ledger</REPORTNAME>
<STATICVARIABLES>
<SVLEDGERNAME>{ledger_name}</SVLEDGERNAME>
<SVFROMDATE>{from_date}</SVFROMDATE>
<SVTODATE>{to_date}</SVTODATE>
</STATICVARIABLES>
</REQUESTDESC>
</EXPORTDATA></BODY>
</ENVELOPE>"""


def xml_balance_sheet(as_on_date: str) -> str:
    """Build XML to export balance sheet from Tally."""
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
<BODY><EXPORTDATA>
<REQUESTDESC>
<REPORTNAME>Balance Sheet</REPORTNAME>
<STATICVARIABLES>
<SVTODATE>{as_on_date}</SVTODATE>
</STATICVARIABLES>
</REQUESTDESC>
</EXPORTDATA></BODY>
</ENVELOPE>"""


def xml_profit_loss(from_date: str, to_date: str) -> str:
    """Build XML to export Profit & Loss statement from Tally."""
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
<BODY><EXPORTDATA>
<REQUESTDESC>
<REPORTNAME>Profit and Loss</REPORTNAME>
<STATICVARIABLES>
<SVFROMDATE>{from_date}</SVFROMDATE>
<SVTODATE>{to_date}</SVTODATE>
</STATICVARIABLES>
</REQUESTDESC>
</EXPORTDATA></BODY>
</ENVELOPE>"""


def get_trial_balance(from_date: str, to_date: str) -> dict:
    """Fetch trial balance data from Tally."""
    try:
        xml = xml_trial_balance(from_date, to_date)
        result = send_to_tally(xml)
        return {"success": result["success"],
                "data": result.get("response", ""),
                "message": "Trial balance fetched" if result["success"] else result["error"]}
    except Exception as e:
        return {"success": False, "message": str(e), "data": ""}


def get_ledger_statement(ledger_name: str, from_date: str, to_date: str) -> dict:
    """Fetch a ledger statement from Tally."""
    try:
        xml = xml_ledger_statement(ledger_name, from_date, to_date)
        result = send_to_tally(xml)
        return {"success": result["success"],
                "ledger": ledger_name,
                "data": result.get("response", ""),
                "message": f"Statement for {ledger_name} fetched" if result["success"] else result["error"]}
    except Exception as e:
        return {"success": False, "message": str(e), "data": ""}


def get_balance_sheet(as_on_date: str) -> dict:
    """Fetch balance sheet from Tally."""
    try:
        xml = xml_balance_sheet(as_on_date)
        result = send_to_tally(xml)
        return {"success": result["success"],
                "data": result.get("response", ""),
                "message": "Balance sheet fetched" if result["success"] else result["error"]}
    except Exception as e:
        return {"success": False, "message": str(e), "data": ""}


def get_profit_loss(from_date: str, to_date: str) -> dict:
    """Fetch P&L statement from Tally."""
    try:
        xml = xml_profit_loss(from_date, to_date)
        result = send_to_tally(xml)
        return {"success": result["success"],
                "data": result.get("response", ""),
                "message": "P&L statement fetched" if result["success"] else result["error"]}
    except Exception as e:
        return {"success": False, "message": str(e), "data": ""}
