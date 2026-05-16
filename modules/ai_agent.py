"""
ai_agent.py — AI Brain powered by Groq (llama3-70b-8192)
Converts natural language accounting entries into structured voucher data.
"""

import json
import requests
from config import GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL, GROQ_MAX_TOKENS, GROQ_TEMPERATURE


SYSTEM_PROMPT = """You are an expert Indian accountant and Tally ERP specialist.
Your job is to parse natural language accounting entries and extract structured data.

Always respond with ONLY valid JSON in this exact format:
{
  "voucher_type": "Sales|Purchase|Payment|Receipt|Contra|Journal|Credit Note|Debit Note",
  "party": "party name or empty string",
  "amount": numeric_value,
  "date": "YYYYMMDD or empty",
  "gst_pct": numeric_gst_rate (0, 5, 12, 18, or 28),
  "narration": "brief description",
  "bank_ledger": "Bank Account or Cash",
  "is_interstate": false
}

Rules:
- If the transaction mentions GST, extract the rate. Default is 18 if mentioned but rate not clear.
- For payments/receipts, identify if it is via bank, UPI, or cash.
- For interstate transactions, set is_interstate to true.
- Date must be in YYYYMMDD format. Education Mode only allows day 1, 2, or 31.
- Return ONLY the JSON object, no explanation, no markdown.
"""


def groq_call(system_prompt: str, user_message: str) -> str:
    """
    Call the Groq API and return the response text.
    Returns an error string prefixed with "ERROR:" on failure.
    """
    if not GROQ_API_KEY:
        return "ERROR: GROQ_API_KEY is not set. Please add it to your environment secrets."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ],
        "max_tokens":  GROQ_MAX_TOKENS,
        "temperature": GROQ_TEMPERATURE
    }
    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "ERROR: Groq request timed out — check your internet connection"
    except requests.exceptions.ConnectionError:
        return "ERROR: Cannot reach Groq — no internet connection"
    except Exception as e:
        return f"ERROR: {str(e)}"


def parse_voucher_from_text(user_text: str) -> dict:
    """
    Parse a natural language accounting entry into a structured voucher dict.
    
    Args:
        user_text: e.g. "Sold goods to Sharma Traders for Rs 11800 including 18% GST"
    
    Returns:
        {"success": True, "data": {...}} or {"success": False, "error": "..."}
    """
    response = groq_call(SYSTEM_PROMPT, user_text)
    if response.startswith("ERROR:"):
        return {"success": False, "error": response}
    try:
        # Strip markdown code fences if present
        cleaned = response.strip().strip("```json").strip("```").strip()
        data = json.loads(cleaned)
        return {"success": True, "data": data}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"AI returned invalid JSON: {str(e)}", "raw": response}


def ask_accounting_question(question: str) -> str:
    """
    Answer a general accounting or GST question using the Groq AI.
    """
    system = """You are an expert Indian Chartered Accountant with deep knowledge of:
- GST rules and compliance
- Tally ERP accounting entries
- Indian income tax and TDS
- Payroll (PF, ESI, Professional Tax)
- GST returns (GSTR-1, GSTR-3B)

Provide clear, concise, accurate answers. Use Indian accounting terminology.
Always mention relevant GST rates, section numbers, or rules when applicable."""

    return groq_call(system, question)
