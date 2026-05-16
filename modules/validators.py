"""
validators.py — Input validation using Pydantic
Every external input must be validated before sending to Tally.
"""

import re
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from modules.gst_calculator import validate_education_mode_date


class LedgerInput(BaseModel):
    name: str
    parent: str
    gstin: Optional[str] = ""
    state: Optional[str] = ""

    @field_validator("name", "parent")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: str) -> str:
        if v and len(v) != 15:
            raise ValueError("GSTIN must be exactly 15 characters")
        return v


class VoucherInput(BaseModel):
    date: str
    party: str
    amount: float
    gst_pct: float = 18.0
    narration: Optional[str] = ""

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        result = validate_education_mode_date(v)
        if not result["valid"]:
            raise ValueError(result["message"])
        return v

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(v, 2)

    @field_validator("gst_pct")
    @classmethod
    def gst_must_be_valid(cls, v: float) -> float:
        if v not in [0, 5, 12, 18, 28]:
            raise ValueError("GST rate must be 0, 5, 12, 18, or 28")
        return v


class PaymentInput(VoucherInput):
    bank_ledger: str = "Bank Account"


class JournalInput(BaseModel):
    date: str
    debit_ledger: str
    credit_ledger: str
    amount: float
    narration: Optional[str] = ""

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        result = validate_education_mode_date(v)
        if not result["valid"]:
            raise ValueError(result["message"])
        return v

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(v, 2)

    @model_validator(mode="after")
    def ledgers_must_differ(self) -> "JournalInput":
        if self.debit_ledger.strip() == self.credit_ledger.strip():
            raise ValueError("Debit and credit ledgers must be different")
        return self


class EmployeeInput(BaseModel):
    name: str
    emp_id: str
    department: str
    basic_salary: float

    @field_validator("basic_salary")
    @classmethod
    def salary_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Basic salary must be greater than zero")
        return round(v, 2)


class GSTINValidator:
    """Validate GSTIN format."""
    PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

    @classmethod
    def validate(cls, gstin: str) -> dict:
        gstin = gstin.strip().upper()
        if len(gstin) != 15:
            return {"valid": False, "message": "GSTIN must be exactly 15 characters"}
        if not cls.PATTERN.match(gstin):
            return {"valid": False, "message": "GSTIN format is invalid"}
        return {"valid": True, "message": "GSTIN is valid", "state_code": gstin[:2]}


def safe_xml_string(text: str) -> str:
    """Escape special XML characters to prevent malformed XML."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))
