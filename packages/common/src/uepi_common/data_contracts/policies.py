"""Canonical Policy Export data contract - for importing policies from external systems"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class PolicyExportRecord(BaseModel):
    """Canonical Policy Export record - for importing policies from external systems
    
    This contract supports importing policy metadata from external UM systems,
    policy management tools, or manual exports. The system maps this into UEPI's
    PolicyLogic schema after validation.
    
    Schema Version: 1.0
    Format: CSV, Excel, or JSON
    """
    
    # Policy Header
    policy_name: str = Field(..., description="Policy name")
    policy_type: str = Field(..., description="Policy type (e.g., 'PRIOR_AUTH', 'SITE_OF_CARE', 'FREQUENCY_LIMIT')")
    description: Optional[str] = Field(None, description="Policy description")
    owner_role: Optional[str] = Field(None, description="Policy owner role (e.g., 'Medical Director')")
    
    # Effective Period
    effective_start_date: date = Field(..., description="Policy effective start date")
    effective_end_date: Optional[date] = Field(None, description="Policy effective end date (if terminated)")
    
    # Scope
    lob: Optional[str] = Field(None, description="Line of business (comma-separated if multiple)")
    market: Optional[str] = Field(None, description="Market/region (comma-separated if multiple)")
    network_tier: Optional[str] = Field(None, description="Network tier (e.g., 'TIER_1', 'ALL')")
    
    # Code Sets (semi-structured - will be parsed and validated)
    cpt_codes: Optional[str] = Field(None, description="CPT codes (comma-separated or range, e.g., '99213-99215,70450-70498')")
    hcpcs_codes: Optional[str] = Field(None, description="HCPCS codes (comma-separated)")
    drg_codes: Optional[str] = Field(None, description="DRG codes (comma-separated)")
    service_categories: Optional[str] = Field(None, description="Service categories (comma-separated)")
    
    # Policy Logic Hints (for mapping to PolicyLogic schema)
    lever_type: Optional[str] = Field(None, description="Primary lever type (e.g., 'PRIOR_AUTH', 'SITE_OF_CARE')")
    conditions: Optional[str] = Field(None, description="Conditions in natural language (for manual review)")
    exceptions: Optional[str] = Field(None, description="Exceptions in natural language (for manual review)")
    
    # Additional Context
    source_system: Optional[str] = Field(None, description="Source system (e.g., 'Epic UM', 'Custom Rules Engine')")
    export_date: Optional[date] = Field(None, description="Date of export from source system")
    version: Optional[str] = Field(None, description="Policy version in source system")
    
    class Config:
        json_schema_extra = {
            "example": {
                "policy_name": "Outpatient MRI Prior Authorization",
                "policy_type": "PRIOR_AUTH",
                "description": "Requires prior auth for outpatient MRI procedures",
                "owner_role": "Medical Director",
                "effective_start_date": "2024-01-01",
                "lob": "Commercial,Medicare",
                "market": "CA,TX",
                "cpt_codes": "70450-70498,70551-70553",
                "lever_type": "PRIOR_AUTH",
                "conditions": "Age > 18, Outpatient setting",
                "exceptions": "Emergency, Inpatient",
                "source_system": "Epic UM",
                "export_date": "2024-01-15",
            }
        }

