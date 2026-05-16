"""
tally_connector.py — Handles all HTTP communication with Tally via XML
Tally must be open with ODBC/HTTP server enabled on port 9000.
"""

import requests
from config import TALLY_URL, TALLY_TIMEOUT


def send_to_tally(xml: str) -> dict:
    """
    Send XML data to Tally and return a result dict.
    
    Returns:
        {"success": bool, "response": str} on success
        {"success": False, "error": str} on failure
    """
    try:
        resp = requests.post(
            TALLY_URL,
            data=xml.encode("utf-8"),
            headers={"Content-Type": "text/xml;charset=utf-8"},
            timeout=TALLY_TIMEOUT
        )
        if resp.status_code == 200:
            if "LINEERROR" in resp.text or "Error" in resp.text:
                return {"success": False, "error": resp.text}
            return {"success": True, "response": resp.text}
        return {"success": False, "error": f"HTTP {resp.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Tally is not running — check port 9000 is enabled"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Tally connection timed out — check if Tally is open"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_tally_connection() -> dict:
    """
    Test whether Tally is reachable by sending a simple status request.
    
    Returns:
        {"connected": bool, "message": str}
    """
    test_xml = """<ENVELOPE>
<HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
<BODY><EXPORTDATA>
<REQUESTDESC><REPORTNAME>List of Companies</REPORTNAME></REQUESTDESC>
</EXPORTDATA></BODY>
</ENVELOPE>"""
    try:
        resp = requests.post(
            TALLY_URL,
            data=test_xml.encode("utf-8"),
            headers={"Content-Type": "text/xml;charset=utf-8"},
            timeout=5
        )
        if resp.status_code == 200:
            return {"connected": True, "message": "Tally is connected and ready"}
        return {"connected": False, "message": f"Tally responded with HTTP {resp.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"connected": False, "message": "Cannot reach Tally — make sure Tally is open and port 9000 is enabled"}
    except requests.exceptions.Timeout:
        return {"connected": False, "message": "Tally connection timed out"}
    except Exception as e:
        return {"connected": False, "message": f"Error: {str(e)}"}


def get_company_list() -> dict:
    """
    Fetch the list of companies currently open in Tally.
    """
    xml = """<ENVELOPE>
<HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
<BODY><EXPORTDATA>
<REQUESTDESC><REPORTNAME>List of Companies</REPORTNAME></REQUESTDESC>
</EXPORTDATA></BODY>
</ENVELOPE>"""
    return send_to_tally(xml)
