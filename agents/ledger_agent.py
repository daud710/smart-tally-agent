"""
ledger_agent.py — Create ledgers in Tally individually or in bulk from Excel
Skips duplicates and reports progress on each entry.
"""

from modules.tally_connector import send_to_tally
from modules.validators import LedgerInput, safe_xml_string
from modules.excel_handler import read_ledger_excel
from pydantic import ValidationError


def xml_create_ledger(name: str, parent: str, gstin: str = "", state: str = "") -> str:
    """Build XML to create a single ledger in Tally."""
    safe_name = safe_xml_string(name)
    gstin_tag = f"<GSTIN>{gstin}</GSTIN>" if gstin else ""
    state_tag = f"<STATENAME>{state}</STATENAME>" if state else ""
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
</LEDGER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def create_single_ledger(name: str, parent: str, gstin: str = "", state: str = "") -> dict:
    """
    Validate and create a single ledger in Tally.
    
    Returns:
        {"success": bool, "message": str, "data": dict}
    """
    try:
        validated = LedgerInput(name=name, parent=parent, gstin=gstin, state=state)
        xml = xml_create_ledger(validated.name, validated.parent, validated.gstin, validated.state)
        result = send_to_tally(xml)
        if result["success"]:
            return {"success": True, "message": f"Ledger '{name}' created successfully", "data": {"name": name, "parent": parent}}
        return {"success": False, "message": result["error"], "data": {}}
    except ValidationError as e:
        return {"success": False, "message": str(e), "data": {}}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}


def create_bulk_ledgers(ledger_list: list) -> dict:
    """
    Create multiple ledgers in Tally from a list of dicts.
    Each dict: {"name": str, "parent": str, "gstin": str, "state": str}
    
    Returns:
        {"total": int, "success": int, "failed": int, "details": list}
    """
    results = []
    seen_names = set()

    for ledger in ledger_list:
        name = ledger.get("name", "").strip()
        if not name:
            results.append({"ledger": name, "status": "skipped", "message": "Empty ledger name"})
            continue
        if name.lower() in seen_names:
            results.append({"ledger": name, "status": "skipped", "message": "Duplicate — already processed in this batch"})
            continue
        seen_names.add(name.lower())

        result = create_single_ledger(
            name=name,
            parent=ledger.get("parent", ""),
            gstin=ledger.get("gstin", ""),
            state=ledger.get("state", "")
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
        "details": results
    }


def create_ledgers_from_excel(file_bytes) -> dict:
    """
    Read an Excel file and create all ledgers in Tally.
    
    Returns bulk creation result dict.
    """
    read_result = read_ledger_excel(file_bytes)
    if not read_result["success"]:
        return {"total": 0, "success": 0, "failed": 0, "skipped": 0,
                "details": [], "error": read_result["error"]}
    return create_bulk_ledgers(read_result["data"])
