"""
Stage 2 Policy API - Policy Intake/Configuration & Versioning
Supports standalone and composite policies with validation, import, and similarity detection
"""
from typing import Annotated, List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pathlib import Path
import tempfile

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_common.data_contracts.policy_logic import PolicyLogic, PolicyVersion
from uepi_common.policy.policy_validator import PolicyValidator
from uepi_common.policy.policy_import_mapper import PolicyImportMapper
from uepi_common.policy.policy_similarity import PolicySimilarityDetector
from uepi_common.data_contracts.policy_metadata import (
    get_all_policy_types,
    get_policy_types_by_category,
    LeverType,
    POLICY_TYPE_CATALOG,
)

router = APIRouter()

# Initialize services
_validator = PolicyValidator()
_import_mapper = PolicyImportMapper()
_similarity_detector = PolicySimilarityDetector(similarity_threshold=0.85)


@router.get("/policy-types", response_model=List[Dict[str, Any]])
async def get_policy_types(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    category: Optional[str] = None,
):
    """Get all policy types (levers) with metadata"""
    if category:
        types = get_policy_types_by_category(category)
    else:
        types = get_all_policy_types()
    
    return [t.model_dump() for t in types]


@router.get("/policy-types/{lever_type}", response_model=Dict[str, Any])
async def get_policy_type_metadata(
    lever_type: LeverType,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get metadata for a specific policy type"""
    from uepi_common.data_contracts.policy_metadata import get_policy_type_metadata
    
    metadata = get_policy_type_metadata(lever_type)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Policy type {lever_type} not found")
    
    return metadata.model_dump()


@router.post("/policies/validate", response_model=Dict[str, Any])
async def validate_policy(
    policy: PolicyLogic,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Validate a policy against schema"""
    is_valid, errors, warnings = _validator.validate(policy)
    readiness_score, readiness_issues = _validator.calculate_readiness_score(policy)
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "readiness_score": readiness_score,
        "readiness_issues": readiness_issues,
        "is_standalone": policy.is_standalone(),
        "is_composite": policy.is_composite(),
        "lever_count": len(policy.levers),
    }


@router.post("/policies/import", response_model=List[Dict[str, Any]])
async def import_policies(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    file: UploadFile = File(...),
    file_format: str = Form("auto"),  # auto, csv, excel, json
    mapping_config_json: Optional[str] = Form(None),
):
    """Import policies from external file (CSV/Excel/JSON)"""
    mapping_config = None
    if mapping_config_json:
        import json
        mapping_config = json.loads(mapping_config_json)
    
    # Save uploaded file temporarily
    suffix = Path(file.filename).suffix if file.filename else ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        # Detect format
        if file_format == "auto":
            if suffix.lower() == ".csv":
                file_format = "csv"
            elif suffix.lower() in [".xlsx", ".xls"]:
                file_format = "excel"
            elif suffix.lower() == ".json":
                file_format = "json"
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Import policies
        if file_format == "csv":
            policies = _import_mapper.map_from_csv(tmp_path, mapping_config)
        elif file_format == "excel":
            policies = _import_mapper.map_from_excel(tmp_path, mapping_config=mapping_config)
        elif file_format == "json":
            policies = _import_mapper.map_from_json(tmp_path, mapping_config)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Validate imported policies
        results = []
        for policy in policies:
            is_valid, errors, warnings = _validator.validate(policy)
            readiness_score, readiness_issues = _validator.calculate_readiness_score(policy)
            
            results.append({
                "policy": policy.model_dump(),
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "readiness_score": readiness_score,
                "readiness_issues": readiness_issues,
            })
        
        return results
    
    finally:
        # Clean up temp file
        if tmp_path.exists():
            tmp_path.unlink()


@router.post("/policies/{policy_id}/check-similarity", response_model=List[Dict[str, Any]])
async def check_policy_similarity(
    policy_id: UUID,
    policy: PolicyLogic,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Check for similar/duplicate policies"""
    from uepi_api.storage_policies import list_policies
    
    # Get all existing policies
    existing_policies_data = list_policies(current_user.tenant_id)
    
    # Convert to PolicyLogic objects (simplified - you may need to adjust based on storage format)
    existing_policies = []
    for p_data in existing_policies_data:
        try:
            # Try to reconstruct PolicyLogic from stored data
            # This is a placeholder - adjust based on your storage format
            if "logic" in p_data and p_data["logic"]:
                existing_policies.append(PolicyLogic(**p_data["logic"]))
        except:
            continue
    
    # Find similar policies
    similar = _similarity_detector.find_similar_policies(policy, existing_policies)
    
    return [
        {
            "policy_id": str(sim_policy.policy_id),
            "policy_name": sim_policy.policy_name,
            "similarity_score": score,
            "is_exact_duplicate": _similarity_detector.is_exact_duplicate(policy, sim_policy),
        }
        for sim_policy, score in similar
    ]


@router.get("/policies/{policy_id}/versions", response_model=List[Dict[str, Any]])
async def get_policy_versions(
    policy_id: str,  # Accept both UUID and string IDs
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get all versions of a policy"""
    from uepi_api.storage_policies import get_policy
    
    # get_policy handles both UUID and string IDs
    policy = get_policy(policy_id, current_user.tenant_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Extract versions from policy metadata or root level
    versions = policy.get("versions", [])
    if not versions:
        metadata = policy.get("metadata", {})
        versions = metadata.get("versions", [])
    return versions


@router.post("/policies/{policy_id}/versions", response_model=Dict[str, Any])
async def create_policy_version(
    policy_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    version_number: str = Form(...),
    change_description: Optional[str] = Form(None),
    policy_logic_json: str = Form(...),
):
    """Create a new version of a policy"""
    from uepi_api.storage_policies import get_policy, update_policy
    from datetime import date
    import json
    
    # Parse policy_logic from JSON
    try:
        policy_logic = PolicyLogic(**json.loads(policy_logic_json))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid policy logic JSON: {str(e)}")
    
    # Get existing policy
    existing = get_policy(policy_id, current_user.tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Validate new version
    is_valid, errors, warnings = _validator.validate(policy_logic)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Policy validation failed: {errors}")
    
    # Create version
    version = PolicyVersion(
        version_number=version_number,
        effective_date=policy_logic.effective_start,
        expiration_date=policy_logic.effective_end,
        created_by=current_user.email or "system",
        change_description=change_description,
        policy_logic=policy_logic,
        status="DRAFT",
    )
    
    # Update policy with new version
    existing_versions = existing.get("versions", [])
    existing_versions.append(version.model_dump())
    
    update_policy(
        policy_id,
        current_user.tenant_id,
        {"versions": existing_versions, "logic": policy_logic.model_dump()}
    )
    
    return version.model_dump()


@router.get("/policies/{policy_id}/readiness", response_model=Dict[str, Any])
async def get_policy_readiness(
    policy_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get policy readiness score and issues"""
    from uepi_api.storage_policies import get_policy
    
    policy_data = get_policy(policy_id, current_user.tenant_id)
    if not policy_data:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Reconstruct PolicyLogic from stored data
    if "logic" in policy_data and policy_data["logic"]:
        try:
            policy = PolicyLogic(**policy_data["logic"])
            readiness_score, readiness_issues = _validator.calculate_readiness_score(policy)
            
            return {
                "readiness_score": readiness_score,
                "readiness_issues": readiness_issues,
                "is_ready": readiness_score >= 0.8,
                "policy_name": policy.policy_name,
                "lever_count": len(policy.levers),
                "is_standalone": policy.is_standalone(),
                "is_composite": policy.is_composite(),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calculating readiness: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Policy logic not found")

