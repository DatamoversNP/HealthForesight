"""Policy import endpoints - import policies from external systems"""
from typing import Annotated, Optional
from uuid import UUID
import json
import tempfile
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, verify_token
from uepi_api.database import get_db
from uepi_api.models.policy import Policy, PolicyVersion, PolicyStatus
from uepi_common.policy.importer import PolicyPackageImporter, PolicyPackage, PolicyMappingResult
from uepi_common.policy.mapper import ExternalPolicyFormat
from uepi_common.models import CanonicalPolicy, PolicyType, EffectivePeriod

router = APIRouter()


class PolicyImportReview(BaseModel):
    """Policy import review request - user confirms mapping"""
    policy_id: Optional[UUID] = None  # If None, create new policy
    canonical_policy: dict  # Mapped canonical policy
    save_as_version: bool = False  # If True, save as new version of existing policy
    change_description: Optional[str] = None  # Description of changes for version


class PolicyImportResponse(BaseModel):
    """Policy import response"""
    success: bool
    policy_id: UUID
    version_id: Optional[UUID] = None
    mapping_result: dict
    warnings: list[str] = []
    errors: list[str] = []


@router.post("/policies/import/upload", response_model=PolicyImportResponse, status_code=201)
async def upload_policy_package(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    file: UploadFile = File(...),
    source_system: str = Form(...),  # e.g., "Epic UM", "HealthRules", "Internal"
    source_format: str = Form("JSON"),  # JSON, CSV, EXCEL
    db: Session = Depends(get_db),
):
    """Upload policy package from external system (Phase 4: Policy Import)
    
    This endpoint:
    1. Accepts policy package (JSON/CSV/Excel)
    2. Maps to UEPI canonical format
    3. Returns mapping result for user review
    
    User must call /policies/import/review to finalize import.
    """
    # Validate file format
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    format_map = {'.json': ExternalPolicyFormat.JSON, '.csv': ExternalPolicyFormat.CSV, '.xlsx': ExternalPolicyFormat.EXCEL, '.xls': ExternalPolicyFormat.EXCEL}
    
    if file_ext not in format_map:
        raise HTTPException(status_code=400, detail="File must be JSON, CSV, or Excel")
    
    detected_format = format_map[file_ext]
    if source_format.upper() not in [f.value for f in ExternalPolicyFormat]:
        raise HTTPException(status_code=400, detail=f"Invalid source format: {source_format}")
    
    external_format = ExternalPolicyFormat(source_format.upper())
    
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Read file content
        if file_ext == '.json':
            with open(tmp_path, 'r') as f:
                raw_data = json.load(f)
        else:
            # CSV/Excel would require pandas - for MVP, only support JSON
            raise HTTPException(
                status_code=400,
                detail="Only JSON format is supported. CSV and Excel import coming soon.",
            )
        
        # Create policy package
        package = PolicyPackage(
            source_system=source_system,
            source_format=external_format,
            raw_data=raw_data,
        )
        
        # Import and map
        importer = PolicyPackageImporter()
        mapping_result = importer.import_package(package, auto_map=True)
        
        if not mapping_result.success:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Policy import failed",
                    "errors": mapping_result.mapping_errors,
                    "warnings": mapping_result.mapping_warnings,
                },
            )
        
        # Return mapping result for review (don't save yet)
        return PolicyImportResponse(
            success=True,
            policy_id=UUID(int=0),  # Placeholder - will be assigned on review
            mapping_result=mapping_result.to_dict(),
            warnings=mapping_result.mapping_warnings,
            errors=mapping_result.mapping_errors,
        )
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/policies/import/review", response_model=PolicyImportResponse, status_code=201)
async def review_and_save_policy_import(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    review_data: PolicyImportReview = Body(...),
    db: Session = Depends(get_db),
):
    """Review and save imported policy (Phase 4: Policy Import Review)
    
    This endpoint:
    1. Accepts reviewed canonical policy
    2. Validates mapping
    3. Saves as new policy or new version
    4. Creates audit trail
    """
    from datetime import datetime
    from uuid import uuid4
    
    try:
        # Reconstruct canonical policy from dict
        canonical_dict = review_data.canonical_policy
        
        # Build canonical policy object
        canonical_policy = CanonicalPolicy(
            policy_id=review_data.policy_id or uuid4(),
            policy_name=canonical_dict.get("policy_name", "Imported Policy"),
            policy_type=PolicyType(canonical_dict.get("policy_type", "PRIOR_AUTH")),
            description=canonical_dict.get("description"),
            status=PolicyStatus.DRAFT,  # Start as draft
            scope=canonical_dict.get("scope"),
            effective_period=canonical_dict.get("effective_period"),
            enforcement=canonical_dict.get("enforcement"),
            policy_levers=canonical_dict.get("policy_levers", []),
            expected_behavioral_response=canonical_dict.get("expected_behavioral_response"),
            analytics_expectations=canonical_dict.get("analytics_expectations"),
            ui_hints=canonical_dict.get("ui_hints"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Save as new policy or new version
        if review_data.save_as_version and review_data.policy_id:
            # Save as new version of existing policy
            policy = db.query(Policy).filter(
                Policy.id == review_data.policy_id,
                Policy.tenant_id == current_user.tenant_id,
            ).first()
            
            if not policy:
                raise HTTPException(status_code=404, detail="Policy not found")
            
            # Get next version number
            max_version = db.query(PolicyVersion).filter(
                PolicyVersion.policy_id == review_data.policy_id,
            ).order_by(PolicyVersion.version_number.desc()).first()
            
            version_number = (max_version.version_number + 1) if max_version else 1
            
            # Create new version
            version = PolicyVersion(
                tenant_id=current_user.tenant_id,
                policy_id=review_data.policy_id,
                version_number=version_number,
                effective_start_date=canonical_policy.effective_period.start_date if canonical_policy.effective_period else datetime.utcnow(),
                effective_end_date=canonical_policy.effective_period.end_date if canonical_policy.effective_period else None,
                change_type="IMPORT",  # Imported from external system
                enforcement_strength="MEDIUM",
                justification=review_data.change_description or "Imported from external system",
                version_metadata_json={
                    "import_source": "external_system",
                    "canonical_policy": canonical_dict,
                },
            )
            db.add(version)
            db.commit()
            db.refresh(version)
            
            # Update policy metadata
            policy.policy_metadata_json = canonical_dict
            policy.updated_at = datetime.utcnow()
            db.commit()
            
            return PolicyImportResponse(
                success=True,
                policy_id=review_data.policy_id,
                version_id=version.id,
                mapping_result={"canonical_policy": canonical_dict},
                warnings=[],
                errors=[],
            )
        else:
            # Save as new policy
            policy = Policy(
                tenant_id=current_user.tenant_id,
                name=canonical_policy.policy_name,
                policy_type=canonical_policy.policy_type.value,
                owner_role=None,
                description=canonical_policy.description,
                status=PolicyStatus.DRAFT.value,
                policy_metadata_json={
                    "scope": canonical_policy.scope.model_dump() if hasattr(canonical_policy.scope, "model_dump") else canonical_policy.scope.dict() if hasattr(canonical_policy.scope, "dict") else canonical_policy.scope,
                    "effective_period": canonical_policy.effective_period.model_dump() if hasattr(canonical_policy.effective_period, "model_dump") else canonical_policy.effective_period.dict() if hasattr(canonical_policy.effective_period, "dict") else canonical_policy.effective_period,
                    "enforcement": canonical_policy.enforcement.model_dump() if hasattr(canonical_policy.enforcement, "model_dump") else canonical_policy.enforcement.dict() if hasattr(canonical_policy.enforcement, "dict") else canonical_policy.enforcement,
                    "policy_levers": [lever.model_dump() if hasattr(lever, "model_dump") else lever.dict() if hasattr(lever, "dict") else lever for lever in canonical_policy.policy_levers] if canonical_policy.policy_levers else [],
                },
            )
            db.add(policy)
            db.commit()
            db.refresh(policy)
            
            # Create initial version
            version = PolicyVersion(
                tenant_id=current_user.tenant_id,
                policy_id=policy.id,
                version_number=1,
                effective_start_date=canonical_policy.effective_period.start_date if canonical_policy.effective_period else datetime.utcnow(),
                effective_end_date=canonical_policy.effective_period.end_date if canonical_policy.effective_period else None,
                change_type="IMPORT",
                enforcement_strength="MEDIUM",
                justification="Initial import from external system",
                version_metadata_json={
                    "import_source": "external_system",
                    "canonical_policy": canonical_dict,
                },
            )
            db.add(version)
            db.commit()
            db.refresh(version)
            
            return PolicyImportResponse(
                success=True,
                policy_id=policy.id,
                version_id=version.id,
                mapping_result={"canonical_policy": canonical_dict},
                warnings=[],
                errors=[],
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save imported policy: {str(e)}",
        )

