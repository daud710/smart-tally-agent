"""
payroll_emailer.py — Send payslips via email using Gmail SMTP
Requires Gmail app password (not regular password) — enable 2FA first.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from payroll.payslip_generator import generate_payslip_pdf
from payroll.payroll_calculator import calculate_salary


def send_payslip_email(
    sender_email: str,
    app_password: str,
    recipient_email: str,
    emp_name: str,
    pdf_path: str,
    month: str
) -> dict:
    """
    Send a payslip PDF to an employee via Gmail SMTP.
    
    Args:
        sender_email:    Gmail address of the sender (HR/accounts team)
        app_password:    Gmail App Password (16-char, not the regular password)
        recipient_email: Employee's email address
        emp_name:        Employee name (for the subject line)
        pdf_path:        Local path to the generated PDF payslip
        month:           Month string (e.g., "March 2024")
    
    Returns:
        {"success": bool, "message": str}
    """
    try:
        msg = MIMEMultipart()
        msg["From"]    = sender_email
        msg["To"]      = recipient_email
        msg["Subject"] = f"Your Salary Payslip — {month}"

        body = f"""Dear {emp_name},

Please find attached your salary payslip for {month}.

If you have any questions, please contact the HR/Accounts team.

Regards,
HR & Accounts Team

---
This is an automated email. Please do not reply to this message.
"""
        msg.attach(MIMEText(body, "plain"))

        # Attach PDF
        if not os.path.exists(pdf_path):
            return {"success": False, "message": f"PDF file not found: {pdf_path}"}

        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition",
                        f'attachment; filename="{os.path.basename(pdf_path)}"')
        msg.attach(part)

        # Send via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        return {"success": True, "message": f"Payslip sent to {recipient_email}"}

    except smtplib.SMTPAuthenticationError:
        return {"success": False,
                "message": "Gmail authentication failed. Use an App Password, not your regular password."}
    except smtplib.SMTPException as e:
        return {"success": False, "message": f"SMTP error: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def bulk_send_payslips(
    sender_email: str,
    app_password: str,
    employees: list,
    month: str,
    output_dir: str = "payslips"
) -> dict:
    """
    Generate and email payslips to all employees in bulk.
    
    Args:
        employees: list of {"name": str, "emp_id": str, "dept": str,
                             "basic": float, "email": str}
    
    Returns:
        {"total": int, "sent": int, "failed": int, "details": list}
    """
    results = []
    for emp in employees:
        emp_email = emp.get("email", "").strip()
        if not emp_email:
            results.append({"emp": emp.get("name"), "status": "skipped",
                             "message": "No email address provided"})
            continue

        salary = calculate_salary(emp.get("basic", 0))
        pdf_result = generate_payslip_pdf(emp, salary, month, output_dir)

        if not pdf_result["success"]:
            results.append({"emp": emp.get("name"), "status": "failed",
                             "message": f"PDF generation failed: {pdf_result['error']}"})
            continue

        email_result = send_payslip_email(
            sender_email, app_password, emp_email,
            emp.get("name", ""), pdf_result["file"], month
        )
        results.append({
            "emp":     emp.get("name"),
            "email":   emp_email,
            "status":  "sent" if email_result["success"] else "failed",
            "message": email_result["message"]
        })

    sent_count   = sum(1 for r in results if r["status"] == "sent")
    failed_count = sum(1 for r in results if r["status"] == "failed")

    return {
        "total":   len(employees),
        "sent":    sent_count,
        "failed":  failed_count,
        "skipped": len(employees) - sent_count - failed_count,
        "details": results
    }
