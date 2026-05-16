"""
ocr_handler.py — OCR-based bill scanning using Pillow + Groq AI
Extracts accounting data from uploaded bill/invoice images.
Note: Tesseract is optional. If not installed, Groq vision-based parsing is used.
"""

import re
import io
from modules.ai_agent import groq_call

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def extract_text_from_image(image_bytes: bytes) -> dict:
    """
    Extract raw text from a bill/invoice image using OCR.
    Falls back gracefully if Tesseract is not installed.
    
    Returns:
        {"success": True, "text": str} or {"success": False, "error": str}
    """
    if not TESSERACT_AVAILABLE:
        return {
            "success": False,
            "error": "OCR library not installed. Using AI-based parsing instead."
        }
    try:
        from PIL import Image
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang="eng")
        return {"success": True, "text": text}
    except Exception as e:
        return {"success": False, "error": f"OCR failed: {str(e)}"}


def parse_bill_with_ai(image_text: str) -> dict:
    """
    Use Groq AI to parse extracted bill text into structured accounting data.
    
    Returns:
        {"success": True, "data": {...}} or {"success": False, "error": str}
    """
    system_prompt = """You are an expert at reading Indian invoices and bills.
Extract the following information from the bill text and return ONLY valid JSON:
{
  "vendor_name": "supplier/vendor name",
  "invoice_number": "invoice number",
  "invoice_date": "date in YYYYMMDD format",
  "taxable_amount": numeric value,
  "cgst": numeric value,
  "sgst": numeric value,
  "igst": numeric value,
  "total_amount": numeric value,
  "gst_rate": numeric rate (5, 12, 18, or 28),
  "hsn_code": "HSN code if visible",
  "narration": "brief description of goods/services"
}
If any field is not found, use null or 0 for numeric fields and empty string for text."""

    import json
    response = groq_call(system_prompt, f"Extract data from this bill:\n\n{image_text}")
    if response.startswith("ERROR:"):
        return {"success": False, "error": response}
    try:
        cleaned = response.strip().strip("```json").strip("```").strip()
        data = json.loads(cleaned)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": f"Could not parse AI response: {str(e)}", "raw": response}


def process_bill_image(image_bytes: bytes) -> dict:
    """
    Full pipeline: OCR the image, then parse with AI.
    
    Returns:
        {"success": True, "data": {...}, "raw_text": str}
    """
    ocr_result = extract_text_from_image(image_bytes)
    if not ocr_result["success"]:
        return {
            "success": False,
            "error": ocr_result["error"],
            "tip": "Upload a clear image of the bill. Make sure Tesseract OCR is installed."
        }

    raw_text = ocr_result["text"]
    parse_result = parse_bill_with_ai(raw_text)

    if parse_result["success"]:
        return {
            "success": True,
            "data": parse_result["data"],
            "raw_text": raw_text
        }
    return {
        "success": False,
        "error": parse_result["error"],
        "raw_text": raw_text
    }
