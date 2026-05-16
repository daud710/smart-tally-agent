"""
config.py — Central configuration for Smart Tally Accounting Agent V3
All settings are loaded from environment variables. Never hardcode secrets.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Tally Connection ───────────────────────────────────────────────────────
TALLY_URL = os.environ.get("TALLY_URL", "http://localhost:9000")
TALLY_TIMEOUT = int(os.environ.get("TALLY_TIMEOUT", "10"))

# Education Mode: only dates 1, 2, and the last day of the month are valid
EDUCATION_MODE_VALID_DAYS = [1, 2, 31]

# ─── Groq AI ─────────────────────────────────────────────────────────────────
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-70b-8192"
GROQ_MAX_TOKENS = 1000
GROQ_TEMPERATURE = 0.1
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ─── App Settings ─────────────────────────────────────────────────────────────
APP_TITLE = "Smart Tally Accounting Agent V3"
APP_VERSION = "3.0.0"

# ─── GST States (India) ──────────────────────────────────────────────────────
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Jammu & Kashmir", "Ladakh", "Chandigarh",
    "Dadra & Nagar Haveli", "Daman & Diu", "Lakshadweep", "Puducherry"
]

# ─── GST Rates ───────────────────────────────────────────────────────────────
GST_RATES = [0, 5, 12, 18, 28]

# ─── Voucher Types ───────────────────────────────────────────────────────────
VOUCHER_TYPES = [
    "Sales", "Purchase", "Payment", "Receipt",
    "Contra", "Journal", "Credit Note", "Debit Note",
    "Stock Journal", "Physical Stock"
]
