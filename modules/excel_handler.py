"""
excel_handler.py — Read and write Excel templates for bulk operations
Handles bulk import of ledgers, vouchers, stock items, and employees.
"""

import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import io
from typing import Optional


# ─── Template Creators ───────────────────────────────────────────────────────

def create_ledger_template() -> bytes:
    """Create an Excel template for bulk ledger creation."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ledgers"

    headers = ["Ledger Name*", "Parent Group*", "GSTIN (optional)", "State (optional)"]
    sample  = ["Ramesh Traders", "Sundry Debtors", "27AAACR1234A1Z5", "Maharashtra"]

    _style_header_row(ws, headers)
    ws.append(sample)
    _auto_fit_columns(ws)

    # Add instructions
    ws2 = wb.create_sheet("Instructions")
    ws2["A1"] = "Instructions for Ledger Import"
    ws2["A1"].font = Font(bold=True, size=12)
    ws2["A3"] = "Required columns: Ledger Name, Parent Group"
    ws2["A4"] = "Parent Group examples: Sundry Debtors, Sundry Creditors, Bank Accounts, Cash-in-Hand, Sales Accounts, Purchase Accounts"
    ws2["A5"] = "GSTIN: Required only for parties with GST registration"

    return _save_to_bytes(wb)


def create_sales_template() -> bytes:
    """Create an Excel template for bulk sales voucher entry."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales Vouchers"

    headers = ["Date (YYYYMMDD)*", "Party Name*", "Total Amount*", "GST %*", "Narration"]
    sample  = ["20240101", "Ramesh Traders", "11800", "18", "Sales of goods"]

    _style_header_row(ws, headers)
    ws.append(sample)
    _auto_fit_columns(ws)
    return _save_to_bytes(wb)


def create_purchase_template() -> bytes:
    """Create an Excel template for bulk purchase voucher entry."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Purchase Vouchers"

    headers = ["Date (YYYYMMDD)*", "Vendor Name*", "Total Amount*", "GST %*", "Narration"]
    sample  = ["20240101", "Suresh Suppliers", "5900", "18", "Purchase of material"]

    _style_header_row(ws, headers)
    ws.append(sample)
    _auto_fit_columns(ws)
    return _save_to_bytes(wb)


def create_employee_template() -> bytes:
    """Create an Excel template for bulk employee/payroll data."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Employees"

    headers = ["Employee Name*", "Employee ID*", "Department*", "Basic Salary*"]
    sample  = ["Rahul Kumar", "EMP001", "Accounts", "30000"]

    _style_header_row(ws, headers)
    ws.append(sample)
    _auto_fit_columns(ws)
    return _save_to_bytes(wb)


def create_payment_template() -> bytes:
    """Create an Excel template for bulk payment/receipt entries."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Payments"

    headers = ["Date (YYYYMMDD)*", "Party Name*", "Amount*", "Bank/Cash Ledger*", "Narration"]
    sample  = ["20240101", "Ramesh Traders", "50000", "Bank Account", "Payment against invoice"]

    _style_header_row(ws, headers)
    ws.append(sample)
    _auto_fit_columns(ws)
    return _save_to_bytes(wb)


# ─── Excel Readers ───────────────────────────────────────────────────────────

def read_ledger_excel(file_bytes) -> dict:
    """
    Read ledger data from an uploaded Excel file.
    Returns {"success": True, "data": [...]} or {"success": False, "error": str}
    """
    try:
        df = pd.read_excel(file_bytes, engine="openpyxl")
        df.columns = df.columns.str.strip().str.replace("*", "", regex=False)
        df = df.dropna(subset=["Ledger Name", "Parent Group"])
        df = df.fillna("")

        records = []
        for _, row in df.iterrows():
            records.append({
                "name":   str(row.get("Ledger Name", "")).strip(),
                "parent": str(row.get("Parent Group", "")).strip(),
                "gstin":  str(row.get("GSTIN (optional)", "")).strip(),
                "state":  str(row.get("State (optional)", "")).strip(),
            })
        return {"success": True, "data": records, "count": len(records)}
    except Exception as e:
        return {"success": False, "error": f"Failed to read Excel file: {str(e)}"}


def read_sales_excel(file_bytes) -> dict:
    """Read sales voucher data from uploaded Excel file."""
    try:
        df = pd.read_excel(file_bytes, engine="openpyxl")
        df.columns = df.columns.str.strip().str.replace("*", "", regex=False)
        df = df.dropna(subset=["Date (YYYYMMDD)", "Party Name", "Total Amount"])
        df = df.fillna("")

        records = []
        for _, row in df.iterrows():
            records.append({
                "date":       str(int(row["Date (YYYYMMDD)"])),
                "party":      str(row["Party Name"]).strip(),
                "amount":     float(row["Total Amount"]),
                "gst_pct":    float(row.get("GST %", 18)),
                "narration":  str(row.get("Narration", "")).strip(),
            })
        return {"success": True, "data": records, "count": len(records)}
    except Exception as e:
        return {"success": False, "error": f"Failed to read Excel file: {str(e)}"}


def read_employee_excel(file_bytes) -> dict:
    """Read employee data from uploaded Excel file."""
    try:
        df = pd.read_excel(file_bytes, engine="openpyxl")
        df.columns = df.columns.str.strip().str.replace("*", "", regex=False)
        df = df.dropna(subset=["Employee Name", "Basic Salary"])
        df = df.fillna("")

        records = []
        for _, row in df.iterrows():
            records.append({
                "name":         str(row.get("Employee Name", "")).strip(),
                "emp_id":       str(row.get("Employee ID", "")).strip(),
                "dept":         str(row.get("Department", "")).strip(),
                "basic_salary": float(row.get("Basic Salary", 0)),
            })
        return {"success": True, "data": records, "count": len(records)}
    except Exception as e:
        return {"success": False, "error": f"Failed to read Excel file: {str(e)}"}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _style_header_row(ws, headers: list):
    """Apply bold + blue header styling to the first row."""
    ws.append(headers)
    for col_num, _ in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="2E86AB", end_color="2E86AB", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")


def _auto_fit_columns(ws):
    """Auto-fit column widths based on content."""
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=10)
        ws.column_dimensions[get_column_letter(col[0].column)].width = max(max_len + 4, 15)


def _save_to_bytes(wb) -> bytes:
    """Save workbook to a bytes buffer."""
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
