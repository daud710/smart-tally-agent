"""
gst_ledger_setup.py — Auto-create all standard GST ledgers in Tally
New in V3: Creates all required GST, TDS, Sales, Purchase, Cash, Bank,
           Debtors, and Creditors ledgers in a single click.
"""

from modules.tally_connector import send_to_tally


# Standard ledgers that every GST-registered company needs
GST_LEDGERS = [
    {"name": "Output CGST",      "parent": "Duties & Taxes",    "gst_type": "Central Tax",    "duty_head": "GST"},
    {"name": "Output SGST",      "parent": "Duties & Taxes",    "gst_type": "State Tax",       "duty_head": "GST"},
    {"name": "Output IGST",      "parent": "Duties & Taxes",    "gst_type": "Integrated Tax",  "duty_head": "GST"},
    {"name": "Input CGST",       "parent": "Duties & Taxes",    "gst_type": "Central Tax",    "duty_head": "GST"},
    {"name": "Input SGST",       "parent": "Duties & Taxes",    "gst_type": "State Tax",       "duty_head": "GST"},
    {"name": "Input IGST",       "parent": "Duties & Taxes",    "gst_type": "Integrated Tax",  "duty_head": "GST"},
    {"name": "TDS Payable",      "parent": "Duties & Taxes",    "gst_type": "",                "duty_head": "TDS"},
    {"name": "Sales",            "parent": "Sales Accounts",    "gst_type": "",                "duty_head": ""},
    {"name": "Purchase",         "parent": "Purchase Accounts", "gst_type": "",                "duty_head": ""},
    {"name": "Cash",             "parent": "Cash-in-Hand",      "gst_type": "",                "duty_head": ""},
    {"name": "Bank Account",     "parent": "Bank Accounts",     "gst_type": "",                "duty_head": ""},
    {"name": "Sundry Debtors",   "parent": "Sundry Debtors",    "gst_type": "",                "duty_head": ""},
    {"name": "Sundry Creditors", "parent": "Sundry Creditors",  "gst_type": "",                "duty_head": ""},
]


def xml_create_gst_ledger(name: str, parent: str, gst_type: str = "", duty_head: str = "") -> str:
    """Build XML to create a single ledger in Tally."""
    gst_tag  = f"<TAXTYPE>{gst_type}</TAXTYPE>"   if gst_type  else ""
    duty_tag = f"<DUTYHEAD>{duty_head}</DUTYHEAD>" if duty_head else ""
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>All Masters</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<LEDGER NAME="{name}" ACTION="Create">
<NAME>{name}</NAME>
<PARENT>{parent}</PARENT>
{gst_tag}
{duty_tag}
</LEDGER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def create_all_gst_ledgers(company_name: str = "") -> dict:
    """
    Create all standard GST ledgers in Tally in one call.
    
    Returns:
        {"total": int, "success": int, "failed": int, "details": list}
    """
    results = []
    for ledger in GST_LEDGERS:
        xml = xml_create_gst_ledger(
            ledger["name"],
            ledger["parent"],
            ledger.get("gst_type", ""),
            ledger.get("duty_head", "")
        )
        result = send_to_tally(xml)
        results.append({"ledger": ledger["name"], "result": result})

    success_count = sum(1 for r in results if r["result"].get("success"))
    failed_count  = len(results) - success_count
    return {
        "total":   len(results),
        "success": success_count,
        "failed":  failed_count,
        "details": results
    }
