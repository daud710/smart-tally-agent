"""
app.py — Smart Tally Accounting Agent V3
Main Streamlit dashboard with all modules accessible from the sidebar.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from datetime import datetime
import calendar

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Tally Agent V3",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Imports ───────────────────────────────────────────────────────────────────
from modules.tally_connector import test_tally_connection
from modules.tally_config import full_tally_setup, xml_configure_company
from modules.gst_ledger_setup import create_all_gst_ledgers, GST_LEDGERS
from modules.ai_agent import parse_voucher_from_text, ask_accounting_question
from modules.gst_calculator import (calculate_gst, calculate_gst_exclusive,
                                     get_valid_education_dates, validate_education_mode_date)
from modules.validators import GSTINValidator
from modules.excel_handler import (create_ledger_template, create_sales_template,
                                    create_purchase_template, create_employee_template,
                                    create_payment_template)
from agents.ledger_agent import create_single_ledger, create_ledgers_from_excel
from agents.sales_agent import create_sales_voucher, create_credit_note, create_bulk_sales
from agents.purchase_agent import create_purchase_voucher, create_debit_note
from agents.payment_agent import create_payment, create_receipt, create_contra
from agents.journal_agent import create_journal, create_journal_multi
from agents.stock_agent import create_stock_journal, create_physical_stock, create_stock_item
from agents.report_agent import get_trial_balance, get_ledger_statement, get_balance_sheet
from payroll.payroll_calculator import calculate_salary, calculate_payroll_for_team, summarize_payroll
from payroll.payslip_generator import generate_payslip_bytes
from gst_returns.gstr1_generator import generate_gstr1_json
from gst_returns.gstr3b_generator import generate_gstr3b_excel
from config import INDIAN_STATES, GST_RATES, APP_TITLE, APP_VERSION

# ── Helpers ───────────────────────────────────────────────────────────────────

def show_result(result: dict, success_key="message", error_key="error"):
    """Display a standardised success/error result."""
    if result.get("success"):
        st.success(result.get(success_key, result.get("message", "Done")))
    else:
        st.error(result.get(error_key, result.get("message", "An error occurred")))


def get_valid_dates_for_month(year: int, month: int) -> list:
    dates = get_valid_education_dates(year, month)
    return dates


def date_selector(key_prefix: str) -> str:
    """Render a date selector restricted to Education Mode valid dates."""
    col1, col2 = st.columns(2)
    now = datetime.now()
    with col1:
        year  = st.selectbox("Year",  [now.year - 1, now.year, now.year + 1],
                              index=1, key=f"{key_prefix}_year")
    with col2:
        month = st.selectbox("Month",
                              list(range(1, 13)),
                              format_func=lambda m: calendar.month_name[m],
                              index=now.month - 1, key=f"{key_prefix}_month")
    valid_dates = get_valid_dates_for_month(year, month)
    labels = {
        valid_dates[0]: f"1st {calendar.month_abbr[month]} {year}",
        valid_dates[1]: f"2nd {calendar.month_abbr[month]} {year}",
        valid_dates[2]: f"Last day — {calendar.monthrange(year, month)[1]} {calendar.month_abbr[month]} {year}",
    }
    chosen = st.selectbox("Date (Education Mode — only 1st, 2nd, or last day)",
                           valid_dates, format_func=lambda d: labels[d],
                           key=f"{key_prefix}_date")
    return chosen


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/color/96/accounting.png", width=60)
    st.title("Smart Tally Agent")
    st.caption(f"V{APP_VERSION} — Education Mode")
    st.divider()

    # Tally connection status
    conn = test_tally_connection()
    if conn["connected"]:
        st.success("Tally Connected")
    else:
        st.error("Tally Offline")
        st.caption("Open Tally → Enable port 9000")

    st.divider()

    MODULE = st.radio(
        "Select Module",
        options=[
            "🏠  Dashboard",
            "⚙️  Company Setup",
            "📒  Ledger Management",
            "💰  Sales & Credit Note",
            "🛒  Purchase & Debit Note",
            "💳  Payment & Receipt",
            "📖  Journal Entry",
            "📦  Stock Management",
            "🧮  GST Calculator",
            "🤖  AI Assistant",
            "📋  OCR Bill Scanner",
            "👥  Payroll",
            "📊  GST Returns",
            "📈  Reports",
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("Education Mode Date Rules")
    st.caption("✅ 1st of month")
    st.caption("✅ 2nd of month")
    st.caption("✅ Last day of month")
    st.caption("❌ Any other date")


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

if "Dashboard" in MODULE:
    st.title("Smart Tally Accounting Agent V3")
    st.markdown("**Zero Error | AI-Powered | Education Mode Ready**")

    # Connection status card
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status = "Connected" if conn["connected"] else "Offline"
        color  = "green" if conn["connected"] else "red"
        st.metric("Tally Status", status)
    with col2:
        st.metric("AI Engine", "Groq llama3-70b")
    with col3:
        st.metric("Version", f"V{APP_VERSION}")
    with col4:
        st.metric("Mode", "Education")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("What This Agent Does")
        st.markdown("""
**Configuration (New in V3)**
- Enable GST via XML (no manual F11 clicking)
- Configure all company features automatically
- Auto-create all GST ledgers in one click

**Voucher Entry**
- Sales (Cash + Credit + GST)
- Purchase with ITC tracking
- Payment, Receipt, Contra
- Journal, Credit Note, Debit Note
- Stock Journal, Physical Stock

**Python Direct (No Tally)**
- Payroll — Salary, PF, ESI, TDS, PDF payslips
- GSTR-1 JSON for GST portal
- GSTR-3B Excel summary
- OCR Bill Scanner with AI parsing
        """)

    with col_b:
        st.subheader("Quick Start Guide")
        st.markdown("""
**Step 1 — Connect Tally**
Open TallyPrime → Gateway of Tally → F12 → Enable HTTP server on port 9000

**Step 2 — Setup Company (V3 Feature)**
Go to Company Setup → Enter company name + GSTIN → Click "Run Full Setup"
This will automatically:
- Enable GST
- Configure all features
- Create 13 standard ledgers

**Step 3 — Start Entering Vouchers**
Use the sidebar to navigate to Sales, Purchase, Payment, etc.

**Education Mode Restriction**
Tally Education Mode only allows 3 dates per month:
- 1st of the month
- 2nd of the month
- Last day of the month
        """)

        st.info("**Tip:** Start with Company Setup for new companies — it configures everything in one click.")


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: COMPANY SETUP
# ─────────────────────────────────────────────────────────────────────────────

elif "Company Setup" in MODULE:
    st.title("Company Setup — One-Click Configuration")
    st.info("Run this once for a new company. It enables GST, configures all features, and creates all standard ledgers.")

    tab1, tab2 = st.tabs(["One-Click Full Setup", "Manual Features"])

    with tab1:
        st.subheader("Full Setup for New Company")
        st.warning("Make sure the company is open in Tally and the name matches exactly (case-sensitive).")

        company_name = st.text_input("Company Name (exact match as shown in Tally)", placeholder="e.g. Demo Company")
        gstin        = st.text_input("GSTIN (15 characters)", placeholder="e.g. 27AAACR1234A1Z5").upper()
        state        = st.selectbox("State", INDIAN_STATES)

        if gstin:
            gst_check = GSTINValidator.validate(gstin)
            if gst_check["valid"]:
                st.success(f"Valid GSTIN — State code: {gst_check['state_code']}")
            else:
                st.error(gst_check["message"])

        if st.button("Run Full Setup", type="primary", disabled=not company_name):
            with st.spinner("Setting up company... this may take 30 seconds"):
                result = full_tally_setup(company_name, gstin, state)

            st.subheader("Setup Results")
            for step in result["steps"]:
                step_name = step["step"]
                step_res  = step["result"]

                if step_name == "Create GST Ledgers":
                    total   = step_res.get("total", 0)
                    success = step_res.get("success", 0)
                    failed  = step_res.get("failed", 0)
                    if success > 0:
                        st.success(f"✅ {step_name}: {success}/{total} ledgers created")
                    if failed > 0:
                        st.warning(f"⚠️ {failed} ledgers already exist or failed")

                    with st.expander("Ledger Details"):
                        for detail in step_res.get("details", []):
                            icon = "✅" if detail["result"].get("success") else "❌"
                            st.write(f"{icon} {detail['ledger']}")
                else:
                    if step_res.get("success"):
                        st.success(f"✅ {step_name}: Success")
                    else:
                        st.error(f"❌ {step_name}: {step_res.get('error', 'Failed')}")

    with tab2:
        st.subheader("Configure Individual Features (F11)")
        company_name2 = st.text_input("Company Name", key="features_company")

        cols = st.columns(3)
        features = {}
        feature_list = [
            ("GST Enable",        "gst_enabled",         True),
            ("Inventory",         "inventory_enabled",   True),
            ("Invoice Mode",      "invoice_mode",        True),
            ("Purchase Invoice",  "purchase_invoice",    True),
            ("Credit/Debit Note", "dc_note_enabled",     True),
            ("Bill by Bill",      "bill_by_bill",        True),
            ("Sales Order",       "sales_order",         True),
            ("Purchase Order",    "purchase_order",      True),
            ("Multiple Godown",   "multiple_godown",     False),
            ("Cost Centre",       "cost_centre",         False),
            ("Budgets",           "budgets",             False),
            ("Zero Value Entries","zero_valued_entries", True),
        ]
        for i, (label, key, default) in enumerate(feature_list):
            with cols[i % 3]:
                features[key] = st.checkbox(label, value=default, key=f"feat_{key}")

        if st.button("Apply Features", disabled=not company_name2):
            xml = xml_configure_company(company_name2, features)
            from modules.tally_connector import send_to_tally
            result = send_to_tally(xml)
            show_result(result)

    st.divider()
    st.subheader("Create GST Ledgers Only")
    company_for_ledgers = st.text_input("Company Name (for ledger creation only)", key="gst_ledger_company")
    if st.button("Create All GST Ledgers", disabled=not company_for_ledgers):
        with st.spinner("Creating ledgers..."):
            result = create_all_gst_ledgers(company_for_ledgers)
        st.success(f"Done: {result['success']}/{result['total']} ledgers created")
        if result["failed"] > 0:
            st.warning(f"{result['failed']} ledgers may already exist")


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: LEDGER MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

elif "Ledger" in MODULE:
    st.title("Ledger Management")

    tab1, tab2 = st.tabs(["Create Single Ledger", "Bulk Import (Excel)"])

    with tab1:
        st.subheader("Create a New Ledger")
        col1, col2 = st.columns(2)
        with col1:
            l_name   = st.text_input("Ledger Name*", placeholder="e.g. Ramesh Traders")
            l_parent = st.selectbox("Parent Group*", [
                "Sundry Debtors", "Sundry Creditors", "Bank Accounts",
                "Cash-in-Hand", "Sales Accounts", "Purchase Accounts",
                "Duties & Taxes", "Indirect Expenses", "Indirect Income",
                "Direct Expenses", "Direct Income", "Capital Account",
                "Loans (Liability)", "Fixed Assets"
            ])
        with col2:
            l_gstin = st.text_input("GSTIN (optional)", placeholder="15-char GSTIN")
            l_state = st.selectbox("State (optional)", [""] + INDIAN_STATES)

        if st.button("Create Ledger", type="primary", disabled=not l_name):
            result = create_single_ledger(l_name, l_parent, l_gstin, l_state)
            show_result(result)

    with tab2:
        st.subheader("Bulk Ledger Import from Excel")
        col1, col2 = st.columns([2, 1])
        with col1:
            uploaded = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
        with col2:
            template = create_ledger_template()
            st.download_button("Download Template", template,
                               "ledger_template.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if uploaded and st.button("Import Ledgers", type="primary"):
            with st.spinner("Creating ledgers..."):
                result = create_ledgers_from_excel(uploaded.read())
            st.success(f"Done: {result['success']} created, {result['failed']} failed, {result['skipped']} skipped")
            if result["details"]:
                import pandas as pd
                st.dataframe(pd.DataFrame(result["details"]), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: SALES & CREDIT NOTE
# ─────────────────────────────────────────────────────────────────────────────

elif "Sales" in MODULE:
    st.title("Sales & Credit Note")

    tab1, tab2, tab3 = st.tabs(["Sales Voucher", "Credit Note (Return)", "Bulk Sales (Excel)"])

    with tab1:
        st.subheader("Create Sales Voucher")
        date     = date_selector("sales")
        col1, col2 = st.columns(2)
        with col1:
            party   = st.text_input("Customer Name*", placeholder="e.g. Ramesh Traders")
            amount  = st.number_input("Total Amount (GST inclusive) ₹*", min_value=0.01, step=0.01)
        with col2:
            gst_pct = st.selectbox("GST Rate %*", GST_RATES, index=3)
            narr    = st.text_input("Narration (optional)")
            is_inter = st.checkbox("Interstate Sale (IGST)")

        if gst_pct > 0 and amount > 0:
            from modules.gst_calculator import calculate_gst
            breakdown = calculate_gst(amount, gst_pct, is_inter)
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Taxable Value", f"₹ {breakdown['taxable']:,.2f}")
            if is_inter:
                col_b.metric("IGST", f"₹ {breakdown['igst']:,.2f}")
            else:
                col_b.metric("CGST", f"₹ {breakdown['cgst']:,.2f}")
                col_c.metric("SGST", f"₹ {breakdown['sgst']:,.2f}")

        if st.button("Post Sales Voucher", type="primary", disabled=not party):
            result = create_sales_voucher(date, party, round(amount, 2), gst_pct, narr, is_inter)
            show_result(result)

    with tab2:
        st.subheader("Credit Note (Sales Return)")
        date_cn = date_selector("creditnote")
        col1, col2 = st.columns(2)
        with col1:
            cn_party  = st.text_input("Customer Name*", key="cn_party")
            cn_amount = st.number_input("Return Amount ₹*", min_value=0.01, step=0.01, key="cn_amount")
        with col2:
            cn_gst    = st.selectbox("GST Rate %*", GST_RATES, index=3, key="cn_gst")
            cn_narr   = st.text_input("Narration (optional)", key="cn_narr")

        if st.button("Post Credit Note", type="primary", disabled=not cn_party):
            result = create_credit_note(date_cn, cn_party, round(cn_amount, 2), cn_gst, cn_narr)
            show_result(result)

    with tab3:
        st.subheader("Bulk Sales from Excel")
        col1, col2 = st.columns([2, 1])
        with col1:
            sales_file = st.file_uploader("Upload Sales Excel", type=["xlsx", "xls"], key="sales_bulk")
        with col2:
            tmpl = create_sales_template()
            st.download_button("Download Template", tmpl, "sales_template.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if sales_file and st.button("Import Sales", type="primary"):
            with st.spinner("Posting sales vouchers..."):
                result = create_bulk_sales(sales_file.read())
            st.success(f"Done: {result['success']} posted, {result['failed']} failed")
            if result["details"]:
                import pandas as pd
                st.dataframe(pd.DataFrame(result["details"]), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: PURCHASE & DEBIT NOTE
# ─────────────────────────────────────────────────────────────────────────────

elif "Purchase" in MODULE:
    st.title("Purchase & Debit Note")

    tab1, tab2 = st.tabs(["Purchase Voucher", "Debit Note (Return)"])

    with tab1:
        st.subheader("Create Purchase Voucher")
        date_p = date_selector("purchase")
        col1, col2 = st.columns(2)
        with col1:
            p_vendor = st.text_input("Vendor Name*", placeholder="e.g. Suresh Suppliers")
            p_amount = st.number_input("Total Amount (GST inclusive) ₹*", min_value=0.01, step=0.01, key="p_amount")
        with col2:
            p_gst    = st.selectbox("GST Rate %*", GST_RATES, index=3, key="p_gst")
            p_narr   = st.text_input("Narration (optional)", key="p_narr")
            p_inter  = st.checkbox("Interstate Purchase (IGST)", key="p_inter")

        if p_gst > 0 and p_amount > 0:
            breakdown = calculate_gst(p_amount, p_gst, p_inter)
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Taxable Value", f"₹ {breakdown['taxable']:,.2f}")
            col_b.metric("ITC Available", f"₹ {breakdown['gst_total']:,.2f}")
            col_c.metric("GST Rate", f"{p_gst}%")

        if st.button("Post Purchase Voucher", type="primary", disabled=not p_vendor):
            result = create_purchase_voucher(date_p, p_vendor, round(p_amount, 2), p_gst, p_narr, p_inter)
            show_result(result)

    with tab2:
        st.subheader("Debit Note (Purchase Return)")
        date_dn = date_selector("debitnote")
        col1, col2 = st.columns(2)
        with col1:
            dn_vendor = st.text_input("Vendor Name*", key="dn_vendor")
            dn_amount = st.number_input("Return Amount ₹*", min_value=0.01, step=0.01, key="dn_amount")
        with col2:
            dn_gst  = st.selectbox("GST Rate %*", GST_RATES, index=3, key="dn_gst")
            dn_narr = st.text_input("Narration (optional)", key="dn_narr")

        if st.button("Post Debit Note", type="primary", disabled=not dn_vendor):
            result = create_debit_note(date_dn, dn_vendor, round(dn_amount, 2), dn_gst, dn_narr)
            show_result(result)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: PAYMENT & RECEIPT
# ─────────────────────────────────────────────────────────────────────────────

elif "Payment" in MODULE:
    st.title("Payment, Receipt & Contra")

    tab1, tab2, tab3 = st.tabs(["Payment", "Receipt", "Contra (Cash/Bank Transfer)"])

    BANK_OPTIONS = ["Bank Account", "Cash", "UPI Account", "HDFC Bank", "SBI Bank", "ICICI Bank"]

    with tab1:
        st.subheader("Payment Voucher")
        date_pay = date_selector("payment")
        col1, col2 = st.columns(2)
        with col1:
            pay_party = st.text_input("Pay To (Party Name)*", placeholder="e.g. Ramesh Traders")
            pay_amt   = st.number_input("Amount ₹*", min_value=0.01, step=0.01, key="pay_amt")
        with col2:
            pay_bank  = st.selectbox("Pay Via", BANK_OPTIONS, key="pay_bank")
            pay_narr  = st.text_input("Narration (optional)", key="pay_narr")

        if st.button("Post Payment", type="primary", disabled=not pay_party):
            result = create_payment(date_pay, pay_party, round(pay_amt, 2), pay_bank, pay_narr)
            show_result(result)

    with tab2:
        st.subheader("Receipt Voucher")
        date_rec = date_selector("receipt")
        col1, col2 = st.columns(2)
        with col1:
            rec_party = st.text_input("Received From (Party Name)*", key="rec_party")
            rec_amt   = st.number_input("Amount ₹*", min_value=0.01, step=0.01, key="rec_amt")
        with col2:
            rec_bank  = st.selectbox("Received In", BANK_OPTIONS, key="rec_bank")
            rec_narr  = st.text_input("Narration (optional)", key="rec_narr")

        if st.button("Post Receipt", type="primary", disabled=not rec_party):
            result = create_receipt(date_rec, rec_party, round(rec_amt, 2), rec_bank, rec_narr)
            show_result(result)

    with tab3:
        st.subheader("Contra Voucher (Cash ↔ Bank Transfer)")
        date_con = date_selector("contra")
        col1, col2 = st.columns(2)
        with col1:
            con_from = st.selectbox("Transfer From", BANK_OPTIONS, key="con_from")
            con_amt  = st.number_input("Amount ₹*", min_value=0.01, step=0.01, key="con_amt")
        with col2:
            con_to   = st.selectbox("Transfer To", BANK_OPTIONS, index=1, key="con_to")

        if st.button("Post Contra", type="primary"):
            result = create_contra(date_con, con_from, con_to, round(con_amt, 2))
            show_result(result)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: JOURNAL ENTRY
# ─────────────────────────────────────────────────────────────────────────────

elif "Journal" in MODULE:
    st.title("Journal Entry")

    tab1, tab2 = st.tabs(["Simple Journal (Dr / Cr)", "Compound Journal (Multiple Lines)"])

    with tab1:
        st.subheader("Simple Journal Entry")
        date_jrn = date_selector("journal")
        col1, col2 = st.columns(2)
        with col1:
            jrn_dr   = st.text_input("Debit Ledger*", placeholder="e.g. Salary Expenses")
            jrn_amt  = st.number_input("Amount ₹*", min_value=0.01, step=0.01, key="jrn_amt")
        with col2:
            jrn_cr   = st.text_input("Credit Ledger*", placeholder="e.g. Bank Account")
            jrn_narr = st.text_input("Narration (optional)", key="jrn_narr")

        if jrn_amt > 0:
            col_a, col_b = st.columns(2)
            col_a.markdown(f"**Dr** {jrn_dr or '—'} ₹{jrn_amt:,.2f}")
            col_b.markdown(f"**Cr** {jrn_cr or '—'} ₹{jrn_amt:,.2f}")

        if st.button("Post Journal Entry", type="primary", disabled=not (jrn_dr and jrn_cr)):
            result = create_journal(date_jrn, jrn_dr, jrn_cr, round(jrn_amt, 2), jrn_narr)
            show_result(result)

    with tab2:
        st.subheader("Compound Journal (Multiple Debit/Credit Lines)")
        date_jrn2 = date_selector("journal2")
        jrn_narr2 = st.text_input("Narration", key="jrn_narr2")

        if "journal_entries" not in st.session_state:
            st.session_state.journal_entries = [
                {"ledger": "", "type": "debit",  "amount": 0.0},
                {"ledger": "", "type": "credit", "amount": 0.0},
            ]

        st.write("**Entries:**")
        for i, entry in enumerate(st.session_state.journal_entries):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.session_state.journal_entries[i]["ledger"] = st.text_input(
                    f"Ledger {i+1}", value=entry["ledger"], key=f"jled_{i}")
            with col2:
                st.session_state.journal_entries[i]["type"] = st.selectbox(
                    "Type", ["debit", "credit"], key=f"jtype_{i}",
                    index=0 if entry["type"] == "debit" else 1)
            with col3:
                st.session_state.journal_entries[i]["amount"] = st.number_input(
                    "Amount ₹", min_value=0.0, step=0.01, value=entry["amount"], key=f"jamt_{i}")
            with col4:
                if st.button("✕", key=f"jdel_{i}") and len(st.session_state.journal_entries) > 2:
                    st.session_state.journal_entries.pop(i)
                    st.rerun()

        col_add, col_check = st.columns(2)
        with col_add:
            if st.button("+ Add Line"):
                st.session_state.journal_entries.append({"ledger": "", "type": "debit", "amount": 0.0})
                st.rerun()
        with col_check:
            total_dr = sum(e["amount"] for e in st.session_state.journal_entries if e["type"] == "debit")
            total_cr = sum(e["amount"] for e in st.session_state.journal_entries if e["type"] == "credit")
            if abs(total_dr - total_cr) < 0.01:
                st.success(f"Balanced ✓ Dr ₹{total_dr:,.2f} = Cr ₹{total_cr:,.2f}")
            else:
                st.error(f"Imbalance: Dr ₹{total_dr:,.2f} vs Cr ₹{total_cr:,.2f}")

        if st.button("Post Compound Journal", type="primary"):
            result = create_journal_multi(date_jrn2, st.session_state.journal_entries, jrn_narr2)
            show_result(result)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: STOCK MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

elif "Stock" in MODULE:
    st.title("Stock Management")

    tab1, tab2, tab3 = st.tabs(["Stock Journal (Transfer)", "Physical Stock", "Create Stock Item"])

    with tab1:
        st.subheader("Stock Journal — Transfer Between Godowns")
        date_stk = date_selector("stock")
        col1, col2 = st.columns(2)
        with col1:
            stk_item = st.text_input("Stock Item Name* (exact Tally name)", key="stk_item")
            stk_qty  = st.number_input("Quantity*", min_value=0.001, step=0.001, key="stk_qty")
            stk_rate = st.number_input("Rate per unit ₹*", min_value=0.0, step=0.01, key="stk_rate")
        with col2:
            stk_from = st.text_input("From Godown*", value="Main Location", key="stk_from")
            stk_to   = st.text_input("To Godown*",   value="Secondary",     key="stk_to")

        if stk_qty > 0 and stk_rate > 0:
            st.metric("Total Value", f"₹ {stk_qty * stk_rate:,.2f}")

        if st.button("Post Stock Journal", type="primary", disabled=not stk_item):
            result = create_stock_journal(date_stk, stk_item, stk_qty, stk_from, stk_to, stk_rate)
            show_result(result)

    with tab2:
        st.subheader("Physical Stock Voucher (Stock Count Adjustment)")
        date_phy = date_selector("physical")
        col1, col2 = st.columns(2)
        with col1:
            phy_item = st.text_input("Stock Item Name*", key="phy_item")
            phy_qty  = st.number_input("Actual Physical Qty*", min_value=0.0, step=0.001, key="phy_qty")
        with col2:
            phy_godown = st.text_input("Godown*", value="Main Location", key="phy_godown")
            phy_rate   = st.number_input("Rate per unit ₹*", min_value=0.0, step=0.01, key="phy_rate")

        if st.button("Post Physical Stock", type="primary", disabled=not phy_item):
            result = create_physical_stock(date_phy, phy_item, phy_qty, phy_godown, phy_rate)
            show_result(result)

    with tab3:
        st.subheader("Create New Stock Item")
        col1, col2 = st.columns(2)
        with col1:
            si_name = st.text_input("Item Name*", key="si_name")
            si_unit = st.selectbox("Unit of Measure*", ["Nos", "Kg", "Ltr", "Mtr", "Box", "Pcs", "Set"])
        with col2:
            si_gst = st.selectbox("GST Rate %*", GST_RATES, index=3, key="si_gst")
            si_hsn = st.text_input("HSN Code (optional)", key="si_hsn")

        if st.button("Create Stock Item", type="primary", disabled=not si_name):
            result = create_stock_item(si_name, si_unit, float(si_gst), si_hsn)
            show_result(result)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: GST CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────

elif "GST Calculator" in MODULE:
    st.title("GST Calculator")

    tab1, tab2 = st.tabs(["Calculate GST", "HSN Rate Lookup"])

    with tab1:
        st.subheader("GST Breakdown Calculator")
        col1, col2 = st.columns(2)
        with col1:
            calc_amount = st.number_input("Amount ₹*", min_value=0.01, step=0.01)
            calc_rate   = st.selectbox("GST Rate %", GST_RATES, index=3)
        with col2:
            calc_inclusive = st.radio("Amount Type", ["GST Inclusive (Total)", "GST Exclusive (Taxable)"])
            calc_inter     = st.checkbox("Interstate (IGST)")

        if calc_amount > 0:
            if "Inclusive" in calc_inclusive:
                breakdown = calculate_gst(calc_amount, calc_rate, calc_inter)
            else:
                breakdown = calculate_gst_exclusive(calc_amount, calc_rate, calc_inter)

            st.divider()
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Taxable Value",  f"₹ {breakdown['taxable']:,.2f}")
            col_b.metric("GST Total",      f"₹ {breakdown['gst_total']:,.2f}")
            col_c.metric("Grand Total",    f"₹ {breakdown['grand_total']:,.2f}")
            col_d.metric("Rate",           f"{breakdown['rate']}%")

            st.divider()
            if calc_inter:
                st.info(f"**IGST:** ₹ {breakdown['igst']:,.2f}")
            else:
                col1, col2 = st.columns(2)
                col1.info(f"**CGST ({breakdown['rate']/2}%):** ₹ {breakdown['cgst']:,.2f}")
                col2.info(f"**SGST ({breakdown['rate']/2}%):** ₹ {breakdown['sgst']:,.2f}")

    with tab2:
        st.subheader("HSN Code → GST Rate Lookup")
        from modules.gst_calculator import HSN_GST_RATES, get_gst_rate
        hsn_input = st.text_input("Enter HSN Code", placeholder="e.g. 8517")
        if hsn_input:
            rate = get_gst_rate(hsn_input)
            st.metric(f"GST Rate for HSN {hsn_input}", f"{rate}%")

        st.divider()
        st.subheader("Common HSN Codes")
        import pandas as pd
        hsn_data = [
            {"HSN": k, "GST Rate": f"{v}%"} for k, v in HSN_GST_RATES.items() if k != "default"
        ]
        st.dataframe(pd.DataFrame(hsn_data), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: AI ASSISTANT
# ─────────────────────────────────────────────────────────────────────────────

elif "AI Assistant" in MODULE:
    st.title("AI Accounting Assistant")
    st.markdown("Powered by **Groq llama3-70b** — ask accounting questions or describe a transaction.")

    tab1, tab2 = st.tabs(["Parse Transaction (to Tally)", "Ask Accounting Question"])

    with tab1:
        st.subheader("Natural Language → Tally Voucher")
        st.markdown("Describe the transaction in plain English. The AI will extract the details.")
        user_entry = st.text_area("Describe the Transaction",
                                   placeholder="e.g. Sold goods to Sharma Traders for Rs 11800 including 18% GST on 1st January",
                                   height=100)
        if st.button("Parse Transaction", type="primary", disabled=not user_entry):
            with st.spinner("AI is analysing..."):
                result = parse_voucher_from_text(user_entry)
            if result["success"]:
                st.success("Transaction parsed successfully!")
                data = result["data"]
                col1, col2, col3 = st.columns(3)
                col1.metric("Voucher Type", data.get("voucher_type", "—"))
                col2.metric("Amount",       f"₹ {data.get('amount', 0):,.2f}")
                col3.metric("GST Rate",     f"{data.get('gst_pct', 0)}%")
                st.json(data)

                st.divider()
                st.info("Review the details above, then go to the relevant module to post this voucher.")
            else:
                st.error(result["error"])

    with tab2:
        st.subheader("Ask an Accounting / GST Question")
        question = st.text_area("Your Question",
                                 placeholder="e.g. What is the GST rate on hotel accommodation? How do I record a bank charge?",
                                 height=100)
        if st.button("Get Answer", type="primary", disabled=not question):
            with st.spinner("Thinking..."):
                answer = ask_accounting_question(question)
            if answer.startswith("ERROR:"):
                st.error(answer)
            else:
                st.markdown("### Answer")
                st.markdown(answer)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: OCR BILL SCANNER
# ─────────────────────────────────────────────────────────────────────────────

elif "OCR" in MODULE:
    st.title("OCR Bill Scanner")
    st.markdown("Upload a photo of a bill or invoice. The AI will extract accounting data from it.")

    st.warning("**Requirement:** Tesseract OCR must be installed on your Windows PC. "
               "Download from: https://github.com/tesseract-ocr/tesseract")

    uploaded_bill = st.file_uploader("Upload Bill Image",
                                      type=["png", "jpg", "jpeg", "bmp", "tiff"])

    if uploaded_bill:
        col1, col2 = st.columns(2)
        with col1:
            st.image(uploaded_bill, caption="Uploaded Bill", use_container_width=True)
        with col2:
            if st.button("Scan & Extract Data", type="primary"):
                from modules.ocr_handler import process_bill_image
                with st.spinner("Scanning bill..."):
                    result = process_bill_image(uploaded_bill.read())
                if result["success"]:
                    st.success("Bill scanned successfully!")
                    data = result["data"]
                    st.json(data)
                    if result.get("raw_text"):
                        with st.expander("Raw OCR Text"):
                            st.text(result["raw_text"])
                else:
                    st.error(result["error"])
                    if result.get("tip"):
                        st.info(result["tip"])


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: PAYROLL
# ─────────────────────────────────────────────────────────────────────────────

elif "Payroll" in MODULE:
    st.title("Payroll Management")
    st.markdown("Pure Python payroll — runs without Tally. Calculates salary, PF, ESI, TDS and generates PDF payslips.")

    tab1, tab2, tab3 = st.tabs(["Single Employee", "Bulk Payroll", "Download Payslip"])

    with tab1:
        st.subheader("Single Employee Salary Calculator")
        col1, col2, col3 = st.columns(3)
        with col1:
            emp_name = st.text_input("Employee Name*")
            emp_id   = st.text_input("Employee ID*", placeholder="EMP001")
        with col2:
            emp_dept = st.text_input("Department", placeholder="Accounts")
            emp_desg = st.text_input("Designation", placeholder="Accountant")
        with col3:
            basic   = st.number_input("Basic Salary ₹*", min_value=1.0, step=500.0, value=30000.0)
            hra_pct = st.number_input("HRA %", min_value=0.0, max_value=100.0, value=40.0, step=5.0)

        if basic > 0:
            salary = calculate_salary(basic, hra_pct)
            st.divider()
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Gross Salary", f"₹ {salary['gross']:,.2f}")
            col_b.metric("Total Deductions", f"₹ {salary['total_deductions']:,.2f}")
            col_c.metric("Net Pay", f"₹ {salary['net_pay']:,.2f}")
            col_d.metric("PF (Employee)", f"₹ {salary['pf']:,.2f}")

            with st.expander("Full Breakdown"):
                import pandas as pd
                earnings = [
                    {"Component": "Basic",    "Amount (₹)": salary["basic"]},
                    {"Component": "HRA",      "Amount (₹)": salary["hra"]},
                    {"Component": "DA",       "Amount (₹)": salary["da"]},
                    {"Component": "**GROSS**","Amount (₹)": salary["gross"]},
                ]
                deductions = [
                    {"Deduction": "PF",             "Amount (₹)": salary["pf"]},
                    {"Deduction": "ESI",            "Amount (₹)": salary["esi"]},
                    {"Deduction": "Professional Tax","Amount (₹)": salary["prof_tax"]},
                    {"Deduction": "TDS (monthly)",  "Amount (₹)": salary["tds"]},
                    {"Deduction": "**TOTAL**",      "Amount (₹)": salary["total_deductions"]},
                ]
                c1, c2 = st.columns(2)
                c1.dataframe(pd.DataFrame(earnings),   use_container_width=True, hide_index=True)
                c2.dataframe(pd.DataFrame(deductions), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Bulk Payroll from Excel")
        from modules.excel_handler import create_employee_template
        col1, col2 = st.columns([2, 1])
        with col1:
            emp_file = st.file_uploader("Upload Employee Excel", type=["xlsx", "xls"], key="emp_bulk")
        with col2:
            tmpl = create_employee_template()
            st.download_button("Download Template", tmpl, "employee_template.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if emp_file:
            from modules.excel_handler import read_employee_excel
            emp_data = read_employee_excel(emp_file.read())
            if emp_data["success"]:
                payroll = calculate_payroll_for_team([
                    {"name": e["name"], "emp_id": e["emp_id"],
                     "dept": e["dept"],  "basic": e["basic_salary"]}
                    for e in emp_data["data"]
                ])
                summary = summarize_payroll(payroll)
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Employees", summary["employee_count"])
                col_b.metric("Total Gross", f"₹ {summary['total_gross']:,.2f}")
                col_c.metric("Total Net Pay", f"₹ {summary['total_net_pay']:,.2f}")

                import pandas as pd
                df = pd.DataFrame(payroll)[["name", "emp_id", "dept", "gross", "pf",
                                             "esi", "tds", "net_pay"]]
                df.columns = ["Name", "Emp ID", "Dept", "Gross", "PF", "ESI", "TDS", "Net Pay"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.error(emp_data["error"])

    with tab3:
        st.subheader("Generate & Download PDF Payslip")
        col1, col2 = st.columns(2)
        with col1:
            ps_name  = st.text_input("Employee Name*", key="ps_name")
            ps_id    = st.text_input("Employee ID*",   key="ps_id",   placeholder="EMP001")
            ps_dept  = st.text_input("Department",     key="ps_dept")
            ps_desg  = st.text_input("Designation",    key="ps_desg")
        with col2:
            ps_basic = st.number_input("Basic Salary ₹*", min_value=1.0, step=500.0,
                                        value=30000.0, key="ps_basic")
            ps_month = st.text_input("Payslip Month", value=datetime.now().strftime("%B %Y"), key="ps_month")

        if st.button("Generate Payslip", type="primary", disabled=not ps_name):
            salary_data = calculate_salary(ps_basic)
            emp_info = {"name": ps_name, "emp_id": ps_id,
                        "dept": ps_dept, "designation": ps_desg}
            result = generate_payslip_bytes(emp_info, salary_data, ps_month)
            if result["success"]:
                st.success("Payslip generated!")
                st.download_button(
                    "Download PDF Payslip",
                    data=result["bytes"],
                    file_name=result["filename"],
                    mime="application/pdf"
                )
            else:
                st.error(result["error"])


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: GST RETURNS
# ─────────────────────────────────────────────────────────────────────────────

elif "GST Returns" in MODULE:
    st.title("GST Returns Generator")
    st.markdown("Generate GSTR-1 JSON and GSTR-3B Excel — ready for GST portal upload.")

    tab1, tab2 = st.tabs(["GSTR-1 (JSON)", "GSTR-3B (Excel)"])

    with tab1:
        st.subheader("GSTR-1 — Outward Supplies Return")
        col1, col2 = st.columns(2)
        with col1:
            g1_gstin  = st.text_input("Company GSTIN*", key="g1_gstin").upper()
            g1_period = st.text_input("Period (MMYYYY)*", placeholder="032024", key="g1_period")
        with col2:
            st.info("Upload your sales data from an Excel file to generate GSTR-1 JSON")

        st.markdown("**Sample Sales Data (enter manually for demo):**")
        st.markdown("For production use, upload an Excel file with your actual sales data.")

        if st.button("Generate Sample GSTR-1", disabled=not (g1_gstin and g1_period)):
            sample_sales = [
                {"invoice_no": "INV001", "date": "20240101", "party_name": "ABC Pvt Ltd",
                 "party_gstin": "27AAACR1234A1Z5", "taxable": 100000, "cgst": 9000,
                 "sgst": 9000, "igst": 0, "gst_rate": 18, "total": 118000},
                {"invoice_no": "INV002", "date": "20240102", "party_name": "Consumer Sale",
                 "party_gstin": "", "taxable": 5000, "cgst": 300,
                 "sgst": 300, "igst": 0, "gst_rate": 12, "total": 5600},
            ]
            result = generate_gstr1_json(sample_sales, g1_gstin, g1_period)
            if result["success"]:
                summary = result["summary"]
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Total Invoices", summary["total_invoices"])
                col_b.metric("Total Taxable",  f"₹ {summary['total_taxable']:,.2f}")
                col_c.metric("Total Tax",      f"₹ {summary['total_tax']:,.2f}")
                with open(result["file"], "r") as f:
                    json_content = f.read()
                st.download_button("Download GSTR-1 JSON", json_content,
                                   result["file"], "application/json")
                st.success(f"GSTR-1 JSON generated: {result['file']}")
            else:
                st.error(result["error"])

    with tab2:
        st.subheader("GSTR-3B — Monthly Summary Return")
        col1, col2 = st.columns(2)
        with col1:
            g3_gstin  = st.text_input("Company GSTIN*", key="g3_gstin").upper()
            g3_period = st.text_input("Period", placeholder="March 2024", key="g3_period")

        if st.button("Generate Sample GSTR-3B", disabled=not (g3_gstin and g3_period)):
            sample_sales = [
                {"taxable": 100000, "cgst": 9000, "sgst": 9000, "igst": 0},
                {"taxable": 50000,  "cgst": 2500, "sgst": 2500, "igst": 0},
            ]
            sample_purchases = [
                {"taxable": 60000,  "cgst": 5400, "sgst": 5400, "igst": 0},
            ]
            result = generate_gstr3b_excel(g3_gstin, g3_period, sample_sales, sample_purchases)
            if result["success"]:
                summary = result["summary"]
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Total Sales",       f"₹ {summary['total_sales']:,.2f}")
                col_b.metric("ITC Available",     f"₹ {summary['itc_cgst'] + summary['itc_sgst']:,.2f}")
                col_c.metric("Net Tax Payable",   f"₹ {summary['total_tax_payable']:,.2f}")
                st.download_button("Download GSTR-3B Excel", result["bytes"],
                                   result["filename"],
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.success("GSTR-3B Excel generated!")
            else:
                st.error(result["error"])


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: REPORTS
# ─────────────────────────────────────────────────────────────────────────────

elif "Reports" in MODULE:
    st.title("Reports from Tally")
    st.info("These reports are fetched directly from Tally — make sure Tally is open and connected.")

    tab1, tab2 = st.tabs(["Trial Balance / P&L", "Ledger Statement"])

    with tab1:
        st.subheader("Fetch Reports from Tally")
        col1, col2 = st.columns(2)
        with col1:
            rpt_from = st.text_input("From Date (YYYYMMDD)", placeholder="20240101")
        with col2:
            rpt_to   = st.text_input("To Date (YYYYMMDD)",   placeholder="20240131")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Get Trial Balance", disabled=not (rpt_from and rpt_to)):
                result = get_trial_balance(rpt_from, rpt_to)
                if result["success"]:
                    st.success("Trial Balance fetched")
                    st.code(result["data"][:3000] + "..." if len(result["data"]) > 3000 else result["data"])
                else:
                    st.error(result["message"])
        with col_b:
            if st.button("Get Balance Sheet", disabled=not rpt_to):
                result = get_balance_sheet(rpt_to)
                if result["success"]:
                    st.success("Balance Sheet fetched")
                    st.code(result["data"][:3000] + "..." if len(result["data"]) > 3000 else result["data"])
                else:
                    st.error(result["message"])

    with tab2:
        st.subheader("Ledger Statement")
        col1, col2, col3 = st.columns(3)
        with col1:
            led_name = st.text_input("Ledger Name", placeholder="e.g. Ramesh Traders")
        with col2:
            led_from = st.text_input("From Date (YYYYMMDD)", placeholder="20240101", key="led_from")
        with col3:
            led_to   = st.text_input("To Date (YYYYMMDD)",   placeholder="20240131", key="led_to")

        if st.button("Get Ledger Statement", disabled=not (led_name and led_from and led_to)):
            result = get_ledger_statement(led_name, led_from, led_to)
            if result["success"]:
                st.success(f"Statement for {led_name} fetched")
                st.code(result["data"][:3000] + "..." if len(result["data"]) > 3000 else result["data"])
            else:
                st.error(result["message"])
