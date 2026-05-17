"""
ocr_handler.py — Bill scanning using Groq Vision API
No Tesseract required. Sends image directly to Groq for AI-based extraction.
"""
import base64
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)


def process_bill_image(image_bytes: bytes) -> dict:
    """
    Send bill image to Groq Vision API and extract accounting data.

    Returns:
        {"success": True, "data": {...}, "raw_text": str}
        or {"success": False, "error": str}
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "GROQ_API_KEY is not set."}

    # Encode image to base64
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    system_prompt = """You are an expert at reading Indian invoices and bills.
Extract the following information and return ONLY valid JSON (no markdown, no explanation):
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
  "gstin": "vendor GSTIN if visible",
  "hsn_code": "HSN code if visible",
  "narration": "brief description of goods/services"
}
If any field is not found, use null or 0 for numeric fields and empty string for text.
Return ONLY the JSON object."""

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": system_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.1
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        raw_text = resp.json()["choices"][0]["message"]["content"]

        # Parse JSON from response
        cleaned = raw_text.strip().strip("```json").strip("```").strip()
        data = json.loads(cleaned)

        return {
            "success": True,
            "data": data,
            "raw_text": raw_text
        }

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out — check internet connection"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot reach Groq — no internet connection"}
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"AI response parse failed: {str(e)}",
            "raw_text": raw_text if 'raw_text' in locals() else ""
        }
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}
