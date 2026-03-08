"""Data validation utilities"""
from datetime import datetime
from typing import Any
import json

from pydantic import BaseModel, ValidationError, field_validator
from pydantic_core import ValidationError as CoreValidationError


class ClaimsLine(BaseModel):
    """Claims line model with validation"""
    tenant_id: str
    member_id: str
    claim_id: str
    claim_line_id: str
    service_from_date: str
    service_to_date: str
    paid_date: str
    lob: str  # COMMERCIAL, MA, MEDICAID
    market: str
    cpt_hcpcs: str
    rendering_npi: str
    allowed_amount: float
    paid_amount: float
    units: float
    in_network_flag: bool
    
    # Optional fields
    place_of_service: str | None = None
    bill_type: str | None = None
    revenue_code: str | None = None
    modifier_1: str | None = None
    diag_1: str | None = None
    drg: str | None = None
    billing_npi: str | None = None
    
    @field_validator("lob")
    @classmethod
    def validate_lob(cls, v: str) -> str:
        """Validate line of business"""
        valid_lobs = {"COMMERCIAL", "MA", "MEDICAID"}
        if v not in valid_lobs:
            raise ValueError(f"lob must be one of {valid_lobs}")
        return v
    
    @field_validator("service_from_date", "service_to_date", "paid_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate date format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD")
        return v
    
    @field_validator("allowed_amount", "paid_amount", "units")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        """Validate positive numbers"""
        if v < 0:
            raise ValueError(f"Value must be non-negative: {v}")
        return v


class EnrollmentRecord(BaseModel):
    """Enrollment record model"""
    member_id: str
    lob: str
    market: str
    enrolled_flag: bool
    gender: str | None = None
    dob_year: int | None = None
    risk_score: float | None = None


class ProviderRecord(BaseModel):
    """Provider record model"""
    npi: str
    provider_name: str
    specialty: str
    market: str
    facility_flag: bool
    tax_id: str | None = None
    system_affiliation: str | None = None


def validate_claims_line(row: dict[str, Any]) -> tuple[bool, str | None, ClaimsLine | None]:
    """Validate a single claims line"""
    try:
        claims_line = ClaimsLine(**row)
        return True, None, claims_line
    except ValidationError as e:
        error_msg = "; ".join([f"{err['loc']}: {err['msg']}" for err in e.errors()])
        return False, error_msg, None


def validate_claims_batch(rows: list[dict[str, Any]]) -> tuple[list[ClaimsLine], list[dict]]:
    """Validate a batch of claims lines"""
    valid_rows = []
    errors = []
    
    for idx, row in enumerate(rows):
        is_valid, error_msg, validated = validate_claims_line(row)
        if is_valid and validated:
            valid_rows.append(validated)
        else:
            errors.append({
                "row_number": idx + 1,
                "error": error_msg or "Unknown validation error",
                "data": row,
            })
    
    return valid_rows, errors

