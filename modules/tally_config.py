"""
tally_config.py — Tally company configuration via XML (equivalent to F11 menu)
New in V3: Automate company features, GST setup, and ledger creation via XML.

IMPORTANT: The company_name must match exactly what is shown in Tally
(case-sensitive — e.g., "Demo Company" not "DEMO")
"""

from modules.tally_connector import send_to_tally


# ─── A: Configure Company Features (F11 equivalent) ─────────────────────────

def xml_configure_company(company_name: str, features: dict) -> str:
    """
    Build XML to alter company features — equivalent to pressing F11 in Tally.
    
    Args:
        company_name: Exact company name as shown in Tally (case-sensitive)
        features: dict of feature flags, e.g.:
            {
                "gst_enabled": True,
                "inventory_enabled": True,
                "dc_note_enabled": True,
                "invoice_mode": True,
                "purchase_invoice": True,
                "multiple_godown": False,
                "sales_order": True,
                "purchase_order": True,
                "bill_by_bill": True,
                "cost_centre": False,
                "budgets": False,
                "zero_valued_entries": True
            }
    """
    name = company_name.replace("&", "&amp;")

    gst_tag     = "<ISGSTON>Yes</ISGSTON>"         if features.get("gst_enabled")          else "<ISGSTON>No</ISGSTON>"
    inv_tag     = "<ISINVENTORYON>Yes</ISINVENTORYON>" if features.get("inventory_enabled") else "<ISINVENTORYON>No</ISINVENTORYON>"
    dc_tag      = "<ISDCNOTEON>Yes</ISDCNOTEON>"    if features.get("dc_note_enabled")      else "<ISDCNOTEON>No</ISDCNOTEON>"
    inv_mode    = "<ISINVOICINGON>Yes</ISINVOICINGON>" if features.get("invoice_mode")      else "<ISINVOICINGON>No</ISINVOICINGON>"
    purch_inv   = "<PURCASINVOICE>Yes</PURCASINVOICE>" if features.get("purchase_invoice")  else "<PURCASINVOICE>No</PURCASINVOICE>"
    godown      = "<ISMULTIGODOWNON>Yes</ISMULTIGODOWNON>" if features.get("multiple_godown") else "<ISMULTIGODOWNON>No</ISMULTIGODOWNON>"
    sales_ord   = "<ISSALESORDERSON>Yes</ISSALESORDERSON>" if features.get("sales_order")   else "<ISSALESORDERSON>No</ISSALESORDERSON>"
    purch_ord   = "<ISPURCORDERSON>Yes</ISPURCORDERSON>"   if features.get("purchase_order") else "<ISPURCORDERSON>No</ISPURCORDERSON>"
    bill_bill   = "<ISBILLWISEON>Yes</ISBILLWISEON>" if features.get("bill_by_bill")        else "<ISBILLWISEON>No</ISBILLWISEON>"
    cost_ctr    = "<ISCOSTCENTRESON>Yes</ISCOSTCENTRESON>" if features.get("cost_centre")   else "<ISCOSTCENTRESON>No</ISCOSTCENTRESON>"
    budgets     = "<ISBUDGETSON>Yes</ISBUDGETSON>"   if features.get("budgets")             else "<ISBUDGETSON>No</ISBUDGETSON>"
    zero_val    = "<USEZEROENTRIES>Yes</USEZEROENTRIES>" if features.get("zero_valued_entries") else "<USEZEROENTRIES>No</USEZEROENTRIES>"
    dc_inv      = "<DNOTEASINVOICE>Yes</DNOTEASINVOICE><CNOTEASINVOICE>Yes</CNOTEASINVOICE>" if features.get("dc_note_enabled") else ""

    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>All Masters</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<COMPANY NAME="{name}" ACTION="Alter">
{gst_tag}
{inv_tag}
{dc_tag}
{dc_inv}
{inv_mode}
{purch_inv}
{godown}
{sales_ord}
{purch_ord}
{bill_bill}
{cost_ctr}
{budgets}
{zero_val}
</COMPANY>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


# ─── B: Enable GST + Set GSTIN ───────────────────────────────────────────────

def xml_enable_gst(company_name: str, gstin: str, state: str) -> str:
    """
    Build XML to enable GST and set GSTIN and state for the company.
    
    Args:
        company_name: Exact company name as shown in Tally
        gstin: 15-character GST identification number
        state: State name (e.g., "Maharashtra")
    """
    name = company_name.replace("&", "&amp;")
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>All Masters</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<COMPANY NAME="{name}" ACTION="Alter">
<ISGSTON>Yes</ISGSTON>
<GSTIN>{gstin}</GSTIN>
<STATENAME>{state}</STATENAME>
<GSTREGISTRATIONTYPE>Regular</GSTREGISTRATIONTYPE>
</COMPANY>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


# ─── D: One-Click Full Tally Setup ───────────────────────────────────────────

def full_tally_setup(company_name: str, gstin: str, state: str) -> dict:
    """
    Complete one-click setup for a new Tally company:
      Step 1 — Enable GST and set GSTIN
      Step 2 — Configure all company features
      Step 3 — Create all standard GST ledgers
    
    Returns a dict with step-by-step results.
    """
    from modules.gst_ledger_setup import create_all_gst_ledgers

    steps = []

    # Step 1: Enable GST
    xml1 = xml_enable_gst(company_name, gstin, state)
    r1 = send_to_tally(xml1)
    steps.append({"step": "Enable GST", "result": r1})

    # Step 2: Configure features
    features = {
        "gst_enabled": True,
        "inventory_enabled": True,
        "dc_note_enabled": True,
        "invoice_mode": True,
        "purchase_invoice": True,
        "sales_order": True,
        "purchase_order": True,
        "bill_by_bill": True,
        "zero_valued_entries": True,
        "multiple_godown": False,
        "cost_centre": False,
        "budgets": False,
    }
    xml2 = xml_configure_company(company_name, features)
    r2 = send_to_tally(xml2)
    steps.append({"step": "Configure Features", "result": r2})

    # Step 3: Create all standard ledgers
    r3 = create_all_gst_ledgers(company_name)
    steps.append({"step": "Create GST Ledgers", "result": r3})

    all_ok = all(s["result"].get("success", False) for s in steps[:2])
    return {
        "company": company_name,
        "gstin": gstin,
        "state": state,
        "steps": steps,
        "all_success": all_ok
    }
