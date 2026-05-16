"""
payslip_generator.py — Generate professional PDF payslips using ReportLab
Produces A4 payslips with earnings, deductions, and net pay summary.
"""

import os
import io
from payroll.payroll_calculator import calculate_salary

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                     Paragraph, Spacer, HRFlowable)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_payslip_pdf(emp_data: dict, salary: dict, month: str,
                          output_dir: str = "payslips") -> dict:
    """
    Generate a PDF payslip for one employee.
    
    Args:
        emp_data: {"name": str, "emp_id": str, "dept": str, "designation": str}
        salary:   Output of calculate_salary()
        month:    e.g. "March 2024"
        output_dir: Directory to save the PDF
    
    Returns:
        {"success": True, "file": path} or {"success": False, "error": str}
    """
    if not REPORTLAB_AVAILABLE:
        return {"success": False, "error": "ReportLab not installed. Run: pip install reportlab"}

    try:
        os.makedirs(output_dir, exist_ok=True)
        safe_name = emp_data.get("name", "Employee").replace(" ", "_")
        safe_month = month.replace(" ", "_")
        filename = os.path.join(output_dir, f"Payslip_{safe_name}_{safe_month}.pdf")

        doc = SimpleDocTemplate(filename, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        # ── Header ──────────────────────────────────────────────────────────
        title_style = ParagraphStyle("title", parent=styles["Heading1"],
                                     alignment=TA_CENTER, fontSize=16,
                                     textColor=colors.HexColor("#1a365d"))
        story.append(Paragraph("SALARY PAYSLIP", title_style))
        story.append(Paragraph(f"Month: {month}", ParagraphStyle(
            "sub", parent=styles["Normal"], alignment=TA_CENTER, fontSize=11,
            textColor=colors.HexColor("#4a5568"))))
        story.append(Spacer(1, 0.4*cm))
        story.append(HRFlowable(width="100%", thickness=2,
                                 color=colors.HexColor("#2b6cb0")))
        story.append(Spacer(1, 0.3*cm))

        # ── Employee Info ────────────────────────────────────────────────────
        emp_info = [
            ["Employee Name", emp_data.get("name", "—"),
             "Employee ID",   emp_data.get("emp_id", "—")],
            ["Department",    emp_data.get("dept", "—"),
             "Designation",   emp_data.get("designation", "—")],
        ]
        t = Table(emp_info, colWidths=[4*cm, 6*cm, 4*cm, 5.5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ebf8ff")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#ebf8ff")),
            ("FONTNAME",   (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME",   (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 10),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#bee3f8")),
            ("PADDING",    (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))

        # ── Earnings & Deductions table ──────────────────────────────────────
        header_style = ParagraphStyle("col_header", parent=styles["Normal"],
                                      fontName="Helvetica-Bold", fontSize=11,
                                      textColor=colors.white, alignment=TA_CENTER)
        data = [
            [Paragraph("EARNINGS", header_style), "",
             Paragraph("DEDUCTIONS", header_style), ""],
            ["Basic Salary",    f"₹ {salary['basic']:,.2f}",
             "Provident Fund",  f"₹ {salary['pf']:,.2f}"],
            ["HRA",             f"₹ {salary['hra']:,.2f}",
             "ESI",             f"₹ {salary['esi']:,.2f}"],
            ["DA",              f"₹ {salary['da']:,.2f}",
             "Professional Tax",f"₹ {salary['prof_tax']:,.2f}"],
            ["",                "",
             "TDS (Income Tax)",f"₹ {salary['tds']:,.2f}"],
            [Paragraph("<b>Gross Salary</b>", styles["Normal"]),
             Paragraph(f"<b>₹ {salary['gross']:,.2f}</b>", styles["Normal"]),
             Paragraph("<b>Total Deductions</b>", styles["Normal"]),
             Paragraph(f"<b>₹ {salary['total_deductions']:,.2f}</b>", styles["Normal"])],
        ]
        t2 = Table(data, colWidths=[5.5*cm, 4*cm, 5.5*cm, 4.5*cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#276749")),
            ("BACKGROUND", (2, 0), (3, 0), colors.HexColor("#c53030")),
            ("SPAN",       (0, 0), (1, 0)),
            ("SPAN",       (2, 0), (3, 0)),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f7fafc")),
            ("FONTNAME",   (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 10),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("PADDING",    (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f7fafc")]),
        ]))
        story.append(t2)
        story.append(Spacer(1, 0.5*cm))

        # ── Net Pay ──────────────────────────────────────────────────────────
        net_style = ParagraphStyle("net", parent=styles["Heading2"],
                                   alignment=TA_CENTER, fontSize=14,
                                   textColor=colors.HexColor("#276749"))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            f"Net Salary Payable: <b>₹ {salary['net_pay']:,.2f}</b>", net_style))
        story.append(Spacer(1, 0.3*cm))

        note_style = ParagraphStyle("note", parent=styles["Normal"],
                                    fontSize=8, textColor=colors.grey,
                                    alignment=TA_CENTER)
        story.append(Paragraph("This is a computer-generated payslip and does not require a signature.",
                                note_style))

        doc.build(story)
        return {"success": True, "file": filename, "message": f"Payslip saved: {filename}"}

    except Exception as e:
        return {"success": False, "error": f"PDF generation failed: {str(e)}"}


def generate_payslip_bytes(emp_data: dict, salary: dict, month: str) -> dict:
    """
    Generate a payslip PDF and return it as bytes (for Streamlit download).
    """
    if not REPORTLAB_AVAILABLE:
        return {"success": False, "error": "ReportLab not installed"}

    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        # Reuse the file-based generator but capture output
        result = generate_payslip_pdf(emp_data, salary, month, output_dir="/tmp/payslips_temp")
        if result["success"]:
            with open(result["file"], "rb") as f:
                pdf_bytes = f.read()
            return {"success": True, "bytes": pdf_bytes, "filename": os.path.basename(result["file"])}
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
