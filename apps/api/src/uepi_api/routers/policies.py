"""Policy endpoints - database-only"""
from __future__ import annotations

from typing import Annotated, Optional, Union
from datetime import datetime
from uuid import UUID
import sqlalchemy.exc

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel as PydanticBaseModel
from pydantic import BaseModel
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, verify_token
from uepi_api.database import get_db
from uepi_api.models.policy import Policy, PolicyVersion, PolicyCodeSet
from uepi_common.models import (
    ChangeType, CodeType, EnforcementStrength, PolicyType, 
    CanonicalPolicy, PolicyStatus, PolicyScope, EffectivePeriod,
    Enforcement, PolicyLever, EnforcementMechanism, PolicyTouchpoint,
    ExpectedBehavioralResponse, AnalyticsExpectations, UIHints, LineOfBusiness
)

router = APIRouter()


class PolicyCodeSetCreate(BaseModel):
    """Policy code set creation model"""
    code_type: CodeType
    code: str
    code_group: str | None = None


class PolicyVersionCreate(BaseModel):
    """Policy version creation model"""
    effective_start_date: datetime
    effective_end_date: datetime | None = None
    change_type: ChangeType
    enforcement_strength: EnforcementStrength
    justification: str | None = None
    code_sets: list[PolicyCodeSetCreate] = []


class PolicyCreate(BaseModel):
    """Policy creation model - supports both simple and canonical policy structure"""
    name: str
    policy_type: PolicyType
    owner_role: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PolicyStatus] = PolicyStatus.DRAFT
    # Optional canonical policy fields for advanced configuration
    scope: Optional[PolicyScope] = None
    effective_period: Optional[EffectivePeriod] = None
    enforcement: Optional[Enforcement] = None
    policy_levers: Optional[list[PolicyLever]] = None
    # New: PolicyLogic JSON from Policy Builder (full structured logic)
    policy_logic: Optional[dict] = None  # PolicyLogic JSON structure
    expected_behavioral_response: Optional[ExpectedBehavioralResponse] = None
    analytics_expectations: Optional[AnalyticsExpectations] = None
    ui_hints: Optional[UIHints] = None


class PolicyResponse(BaseModel):
    """Policy response model - supports both DB and canonical policy structure"""
    id: UUID
    tenant_id: UUID
    name: str
    policy_type: str
    owner_role: Optional[str]
    description: Optional[str]
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    scope: Optional[PolicyScope] = None
    effective_period: Optional[EffectivePeriod] = None
    enforcement: Optional[Enforcement] = None
    policy_levers: Optional[list[PolicyLever]] = None
    expected_behavioral_response: Optional[ExpectedBehavioralResponse] = None
    analytics_expectations: Optional[AnalyticsExpectations] = None
    ui_hints: Optional[UIHints] = None
    
    class Config:
        from_attributes = True


@router.post("/policies", response_model=PolicyResponse, status_code=201)
async def create_policy(
    policy_data: PolicyCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Create a new policy - supports both simple and canonical structure"""
    from uuid import uuid4
    from uepi_api.routers.access import ROLE_PERMISSIONS
    
    # Check permissions - only UM_LEADER and POLICY_ADMIN can create policies
    has_permission = False
    
    # Ensure roles is a list
    if not current_user.roles:
        user_roles = []
    elif isinstance(current_user.roles, list):
        user_roles = current_user.roles
    elif isinstance(current_user.roles, str):
        user_roles = [current_user.roles]
    else:
        user_roles = list(current_user.roles) if hasattr(current_user.roles, '__iter__') else []
    
    # Check each role for create permission
    for role_name in user_roles:
        if not role_name:
            continue
        role_perms = ROLE_PERMISSIONS.get(role_name, {})
        if "policies" in role_perms and "create" in role_perms["policies"]:
            has_permission = True
            break
    
    if not has_permission:
        raise HTTPException(
            status_code=403, 
            detail=f"Permission denied: You do not have permission to create policies. Your roles: {user_roles}. Required: UM_LEADER or POLICY_ADMIN"
        )
    
    # Database-only mode - use database directly
    try:
        # Build canonical policy metadata - support both individual fields and policy_logic JSON
        policy_metadata = None
        
        # If policy_logic is provided (from Policy Builder), use it directly
        if policy_data.policy_logic:
            policy_metadata = policy_data.policy_logic
            # Extract scope and effective_period from policy_logic for backward compatibility
            if not policy_data.scope and policy_metadata.get("scope"):
                policy_data.scope = PolicyScope(**policy_metadata["scope"])
            if not policy_data.effective_period and policy_metadata.get("effective_period"):
                ep = policy_metadata["effective_period"]
                policy_data.effective_period = EffectivePeriod(
                    start_date=datetime.fromisoformat(ep["start_date"]) if isinstance(ep.get("start_date"), str) else ep["start_date"],
                    end_date=datetime.fromisoformat(ep["end_date"]) if ep.get("end_date") and isinstance(ep["end_date"], str) else ep.get("end_date"),
                )
        # Otherwise, build from individual fields (legacy/quick create)
        elif (policy_data.scope or policy_data.effective_period or policy_data.enforcement or 
              policy_data.policy_levers or policy_data.expected_behavioral_response or 
              policy_data.analytics_expectations or policy_data.ui_hints):
            policy_metadata = {
                "scope": policy_data.scope.model_dump(mode='json') if policy_data.scope else None,
                "effective_period": policy_data.effective_period.model_dump(mode='json') if policy_data.effective_period else None,
                "enforcement": policy_data.enforcement.model_dump(mode='json') if policy_data.enforcement else None,
                "policy_levers": [lever.model_dump(mode='json') for lever in policy_data.policy_levers] if policy_data.policy_levers else [],
                "expected_behavioral_response": policy_data.expected_behavioral_response.model_dump(mode='json') if policy_data.expected_behavioral_response else None,
                "analytics_expectations": policy_data.analytics_expectations.model_dump(mode='json') if policy_data.analytics_expectations else None,
                "ui_hints": policy_data.ui_hints.model_dump(mode='json') if policy_data.ui_hints else None,
            }
        
        # Determine status
        status_value = policy_data.status.value if policy_data.status else PolicyStatus.ACTIVE.value
        if status_value == "DRAFT":
            status_value = "ACTIVE"  # Auto-activate on create for now
        
        policy = Policy(
            tenant_id=current_user.tenant_id,
            name=policy_data.name,
            policy_type=policy_data.policy_type.value,
            owner_role=policy_data.owner_role,
            description=policy_data.description,
            status=status_value,
            policy_metadata_json=policy_metadata,
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        # Generate predicted impact (Stage 3.5)
        try:
            from uepi_api.routers.policy_predicted_impact import (
                generate_predicted_impact_for_policy,
                store_predicted_impact_in_metadata,
            )
            
            # Extract policy levers from metadata
            policy_levers = policy_metadata.get("policy_levers", []) if policy_metadata else []
            policy_scope = policy_metadata.get("scope") if policy_metadata else None
            
            if policy_levers:  # Only generate if policy has levers
                # Item 8: Load baseline metrics if available
                baseline_metrics = None
                try:
                    from uepi_api.storage_baselines import get_latest_baseline
                    baseline = get_latest_baseline(current_user.tenant_id)
                    if baseline:
                        baseline_metrics = baseline.get("baseline_metrics", {}) or baseline.get("metrics", {})
                except Exception:
                    pass  # Use None if baseline not available
                
                predicted_impact = generate_predicted_impact_for_policy(
                    tenant_id=current_user.tenant_id,
                    policy_id=policy.id,
                    policy_levers=policy_levers,
                    policy_scope=policy_scope,
                    baseline_metrics=baseline_metrics,
                )
                
                # Store predicted impact in database (dedicated table - database-only)
                from uepi_api.storage_policy_predicted_impact import store_predicted_impact
                from datetime import datetime, timezone
                
                # Get baseline_id
                baseline_id = None
                if baseline and baseline.get("id"):
                    baseline_id = str(baseline.get("id"))
                
                # Store in dedicated database table (primary storage)
                predicted_impact_dict = predicted_impact.model_dump(mode='json')
                stored_result = store_predicted_impact(
                    policy_id=policy.id,
                    tenant_id=current_user.tenant_id,
                    predicted_impact_data={
                        "metrics": predicted_impact_dict.get("metrics", {}),
                        "model_version": predicted_impact_dict.get("model_version"),
                        "confidence": predicted_impact_dict.get("confidence"),
                        "predicted_at": datetime.now(timezone.utc).isoformat(),
                        "prediction_method": predicted_impact_dict.get("prediction_method", "ELASTICITY_MODEL"),
                        "baseline_id": baseline_id,
                        # Include all additional fields for frontend display
                        "provider_response": predicted_impact_dict.get("provider_response"),
                        "patient_response": predicted_impact_dict.get("patient_response"),
                        "substitution_effects": predicted_impact_dict.get("substitution_effects", []),
                        "warnings": predicted_impact_dict.get("warnings", []),
                        "limitations": predicted_impact_dict.get("limitations", []),
                        "baseline_reference": predicted_impact_dict.get("baseline_reference"),
                        "model_versions": predicted_impact_dict.get("model_versions", {}),
                    }
                )
                
                # Also store in policy metadata for backward compatibility
                policy_metadata = store_predicted_impact_in_metadata(
                    policy_metadata or {},
                    predicted_impact,
                )
                policy.policy_metadata_json = policy_metadata
                db.commit()
                db.refresh(policy)
        except Exception as pred_error:
            # Don't fail policy creation if prediction fails
            print(f"Failed to generate predicted impact for policy {policy.id}: {pred_error}")
            import traceback
            traceback.print_exc()
        
        # Convert to response format
        response_dict = {
            "id": str(policy.id),
            "tenant_id": str(policy.tenant_id),
            "name": policy.name,
            "policy_type": policy.policy_type,
            "owner_role": policy.owner_role,
            "description": policy.description,
            "status": policy.status,
            "created_at": policy.created_at.isoformat() if policy.created_at else None,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
        }
        if policy_metadata:
            response_dict.update({
                "scope": PolicyScope(**policy_metadata["scope"]) if policy_metadata.get("scope") else None,
                "effective_period": EffectivePeriod(**policy_metadata["effective_period"]) if policy_metadata.get("effective_period") else None,
                "enforcement": Enforcement(**policy_metadata["enforcement"]) if policy_metadata.get("enforcement") else None,
                "policy_levers": [PolicyLever(**lever) for lever in policy_metadata.get("policy_levers", [])],
                "expected_behavioral_response": ExpectedBehavioralResponse(**policy_metadata["expected_behavioral_response"]) if policy_metadata.get("expected_behavioral_response") else None,
                "analytics_expectations": AnalyticsExpectations(**policy_metadata["analytics_expectations"]) if policy_metadata.get("analytics_expectations") else None,
                "ui_hints": UIHints(**policy_metadata["ui_hints"]) if policy_metadata.get("ui_hints") else None,
            })
        
        return PolicyResponse(**response_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {e}")


@router.get("/policies", response_model=list[PolicyResponse])
async def list_policies(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    policy_type: str | None = Query(None),
):
    """List policies for current tenant - database-only"""
    try:
        if db is None:
            raise sqlalchemy.exc.OperationalError("Database not available", None, None)
        
        # Test database connection first with a simple query (with timeout)
        try:
            from sqlalchemy import text
            # Use a quick connection test with timeout
            result = db.execute(text("SELECT 1"))
            result.fetchone()  # Consume the result
        except Exception as conn_error:
            print(f"ERROR: Database connection failed in list_policies: {conn_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=503, detail=f"Database connection failed: {str(conn_error)}")
        
        # Debug: Check tenant_id types
        print(f"DEBUG list_policies: current_user.tenant_id = {current_user.tenant_id} (type: {type(current_user.tenant_id)})")
        
        # Check total policies and tenant distribution (with timeout protection)
        # Skip this debug query if it's causing timeouts - just proceed with the actual query
        # try:
        #     total_policies = db.query(Policy).count()
        #     print(f"DEBUG list_policies: Total policies in DB: {total_policies}")
        # except Exception as query_error:
        #     print(f"WARNING: Debug query failed in list_policies: {query_error}")
        #     # Don't fail the request, just log the warning
        
        # Check policies for this tenant
        from uuid import UUID
        tenant_id_uuid = current_user.tenant_id if isinstance(current_user.tenant_id, UUID) else UUID(str(current_user.tenant_id))
        
        # Also check what tenant_ids exist in the database FIRST
        from sqlalchemy import func, distinct
        try:
            tenant_ids_in_db = db.query(distinct(Policy.tenant_id)).all()
            tenant_id_strings = [str(t[0]) for t in tenant_ids_in_db]
            print(f"DEBUG list_policies: Tenant IDs in DB: {tenant_id_strings}")
            
            # Check total policies count
            total_policies_all_tenants = db.query(Policy).count()
            print(f"DEBUG list_policies: Total policies in DB (all tenants): {total_policies_all_tenants}")
            
            # If no policies for this tenant but data exists, check if we should return all data
            if total_policies_all_tenants > 0 and str(tenant_id_uuid) not in tenant_id_strings:
                print(f"WARNING: No policies found for tenant {tenant_id_uuid}, but {total_policies_all_tenants} policies exist for other tenants")
                print(f"WARNING: Available tenant IDs: {tenant_id_strings}")
                # For demo/local dev, if only one tenant exists, return that tenant's data
                if len(tenant_id_strings) == 1:
                    print(f"INFO: Only one tenant in DB, using that tenant's data: {tenant_id_strings[0]}")
                    tenant_id_uuid = UUID(tenant_id_strings[0])
        except Exception as debug_error:
            print(f"DEBUG list_policies: Could not check tenant IDs: {debug_error}")
        
        query = db.query(Policy).filter(Policy.tenant_id == tenant_id_uuid)
        
        if policy_type:
            query = query.filter(Policy.policy_type == policy_type)
        
        policies = query.order_by(Policy.created_at.desc()).offset(skip).limit(limit).all()
        
        # Debug logging
        print(f"DEBUG list_policies: Found {len(policies)} policies for tenant {tenant_id_uuid}")
        print(f"DEBUG list_policies: Query filter: tenant_id == {tenant_id_uuid}")
        
        # Convert to response format, including canonical fields if available
        result = []
        for policy in policies:
            policy_dict = {
                "id": str(policy.id),
                "tenant_id": str(policy.tenant_id),
                "name": policy.name,
                "policy_type": str(policy.policy_type) if policy.policy_type else "UNKNOWN",  # Ensure it's a string
                "owner_role": policy.owner_role,
                "description": policy.description,
                "status": str(getattr(policy, 'status', 'ACTIVE')) if getattr(policy, 'status', 'ACTIVE') else None,  # Ensure it's a string
                "created_at": policy.created_at.isoformat() if policy.created_at else None,
                "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
            }
            
            # If canonical metadata exists, parse it
            if hasattr(policy, 'policy_metadata_json') and policy.policy_metadata_json:
                metadata = policy.policy_metadata_json
                if isinstance(metadata, dict):
                    policy_dict.update({
                        "scope": metadata.get("scope"),
                        "effective_period": metadata.get("effective_period"),
                        "enforcement": metadata.get("enforcement"),
                        "policy_levers": metadata.get("policy_levers"),
                        "expected_behavioral_response": metadata.get("expected_behavioral_response"),
                        "analytics_expectations": metadata.get("analytics_expectations"),
                        "ui_hints": metadata.get("ui_hints"),
                    })
            
            try:
                # Convert dates to strings if they're datetime objects
                if 'created_at' in policy_dict and policy_dict['created_at'] and hasattr(policy_dict['created_at'], 'isoformat'):
                    policy_dict['created_at'] = policy_dict['created_at'].isoformat()
                if 'updated_at' in policy_dict and policy_dict['updated_at'] and hasattr(policy_dict['updated_at'], 'isoformat'):
                    policy_dict['updated_at'] = policy_dict['updated_at'].isoformat()
                
                response_obj = PolicyResponse(**policy_dict)
                result.append(response_obj)
            except Exception as validation_error:
                print(f"WARNING: Failed to create PolicyResponse for policy {policy.id}: {validation_error}")
                print(f"  policy_dict keys: {list(policy_dict.keys())}")
                print(f"  policy_dict: {policy_dict}")
                import traceback
                traceback.print_exc()
                # Skip this policy but continue with others
                continue
        
        return result
    except Exception as e:
        # Other database errors
        error_msg = f"Database query failed in list_policies: {e}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        # Log to stderr as well for visibility
        import sys
        sys.stderr.write(f"ERROR: {error_msg}\n")
        sys.stderr.write(traceback.format_exc())
        return []


class PolicyWithClaimCount(BaseModel):
    """Policy with claim count for what-if / baseline data availability"""
    id: str
    name: str
    policy_type: str
    claim_count: int
    description: Optional[str] = None


# Cap to avoid N heavy count queries (each counts over claims_lines; ~1–2s per policy)
POLICIES_WITH_CLAIM_COUNTS_MAX = 20


@router.get("/policies/with-claim-counts", response_model=list[PolicyWithClaimCount])
async def list_policies_with_claim_counts(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=20),
):
    """List policies with claim counts (scope+levers). Capped for performance (each policy = 1 count query). Sorted by claim_count descending."""
    from datetime import date, timedelta
    from uepi_api.repositories.canonical_data import CanonicalDataRepository
    from uepi_api.services.policy_scoped_data_generation import build_policy_claims_filters

    tenant_id_uuid = current_user.tenant_id if isinstance(current_user.tenant_id, UUID) else UUID(str(current_user.tenant_id))
    repo = CanonicalDataRepository(db)
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    cap = min(limit, POLICIES_WITH_CLAIM_COUNTS_MAX)
    query = db.query(Policy).filter(Policy.tenant_id == tenant_id_uuid)
    policies = query.order_by(Policy.created_at.desc()).limit(cap).all()

    out = []
    for policy in policies:
        meta = getattr(policy, "policy_metadata_json", None) or {}
        policy_dict = {
            "scope": meta.get("scope") or {},
            "policy_levers": meta.get("policy_levers", []),
            "logic": meta.get("logic", {}),
            "policy_logic": meta.get("policy_logic", {}),
        }
        try:
            pf = build_policy_claims_filters(policy_dict)
        except Exception:
            pf = {}
        count = repo.count_claims_for_filters(
            tenant_id=tenant_id_uuid,
            start_date=start_date,
            end_date=end_date,
            lob=pf.get("lob"),
            market=pf.get("markets") or pf.get("market"),
            cpt_codes=pf.get("cpt_codes"),
            hcpcs_codes=pf.get("cpt_codes"),
            service_categories=pf.get("service_categories"),
        )
        out.append(
            PolicyWithClaimCount(
                id=str(policy.id),
                name=policy.name or "",
                policy_type=str(policy.policy_type) if policy.policy_type else "UNKNOWN",
                claim_count=count,
                description=policy.description,
            )
        )
    out.sort(key=lambda x: x.claim_count, reverse=True)
    return out


@router.get("/policies/claim-counts-breakdown")
async def list_policies_claim_counts_breakdown(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    """Diagnostic: claim counts per policy at each filter level (tenant+date, +LOB+market, +procedure/CPT, +service_categories).
    Uses scope + levers merged (same as baseline). So you can see counts before changing the main count query."""
    from datetime import date, timedelta
    from uepi_api.repositories.canonical_data import CanonicalDataRepository
    from uepi_api.services.policy_scoped_data_generation import extract_policy_target_codes

    tenant_id_uuid = current_user.tenant_id if isinstance(current_user.tenant_id, UUID) else UUID(str(current_user.tenant_id))
    repo = CanonicalDataRepository(db)
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    query = db.query(Policy).filter(Policy.tenant_id == tenant_id_uuid)
    policies = query.order_by(Policy.created_at.desc()).limit(limit).all()

    policies_breakdown = []
    for policy in policies:
        meta = getattr(policy, "policy_metadata_json", None) or {}
        scope = meta.get("scope") or {}
        policy_dict = {
            "scope": scope,
            "policy_levers": meta.get("policy_levers", []),
            "logic": meta.get("logic", {}),
            "policy_logic": meta.get("policy_logic", {}),
        }
        try:
            target_codes = extract_policy_target_codes(policy_dict)
        except Exception:
            target_codes = {}

        # From levers only (current with-claim-counts behavior)
        lever_procedure = list(set(target_codes.get("procedure_codes") or []))
        lever_service = list(set(target_codes.get("service_categories") or []))

        # Merged scope + levers (same as database_baseline_computation)
        merged_procedure = []
        merged_service = []
        if scope.get("procedure_codes"):
            merged_procedure = scope["procedure_codes"] if isinstance(scope["procedure_codes"], list) else [scope["procedure_codes"]]
        merged_procedure = list(set(merged_procedure + lever_procedure))
        if scope.get("service_categories"):
            merged_service = scope["service_categories"] if isinstance(scope["service_categories"], list) else [scope["service_categories"]]
        elif scope.get("service_category"):
            merged_service = [scope["service_category"]]
        merged_service = list(set(merged_service + lever_service))

        lob_filter = scope.get("lob")
        market_filter = scope.get("markets") or scope.get("market")

        # Count at each level
        c_tenant = repo.count_claims_for_filters(
            tenant_id=tenant_id_uuid, start_date=start_date, end_date=end_date,
        )
        c_lob_market = repo.count_claims_for_filters(
            tenant_id=tenant_id_uuid, start_date=start_date, end_date=end_date,
            lob=lob_filter, market=market_filter,
        )
        c_plus_cpt = repo.count_claims_for_filters(
            tenant_id=tenant_id_uuid, start_date=start_date, end_date=end_date,
            lob=lob_filter, market=market_filter,
            cpt_codes=merged_procedure if merged_procedure else None,
            hcpcs_codes=merged_procedure if merged_procedure else None,
        )
        c_full = repo.count_claims_for_filters(
            tenant_id=tenant_id_uuid, start_date=start_date, end_date=end_date,
            lob=lob_filter, market=market_filter,
            cpt_codes=merged_procedure if merged_procedure else None,
            hcpcs_codes=merged_procedure if merged_procedure else None,
            service_categories=merged_service if merged_service else None,
        )
        # Current endpoint behavior (levers only, no scope procedure/service)
        c_current = repo.count_claims_for_filters(
            tenant_id=tenant_id_uuid, start_date=start_date, end_date=end_date,
            lob=lob_filter, market=market_filter,
            cpt_codes=lever_procedure if lever_procedure else None,
            hcpcs_codes=lever_procedure if lever_procedure else None,
            service_categories=lever_service if lever_service else None,
        )

        policies_breakdown.append({
            "policy_id": str(policy.id),
            "name": policy.name or "",
            "policy_type": str(policy.policy_type) if policy.policy_type else "UNKNOWN",
            "filters_used": {
                "lob": lob_filter,
                "markets": market_filter,
                "procedure_codes_from_scope": len(scope.get("procedure_codes") or []) if isinstance(scope.get("procedure_codes"), list) else (1 if scope.get("procedure_codes") else 0),
                "procedure_codes_from_levers": len(lever_procedure),
                "procedure_codes_merged": len(merged_procedure),
                "service_categories_from_scope": len(scope.get("service_categories") or []) if isinstance(scope.get("service_categories"), list) else (1 if scope.get("service_category") else 0),
                "service_categories_from_levers": len(lever_service),
                "service_categories_merged": len(merged_service),
            },
            "counts": {
                "tenant_and_date_only": c_tenant,
                "plus_lob_market": c_lob_market,
                "plus_procedure_codes_merged": c_plus_cpt,
                "plus_service_categories_full": c_full,
                "current_endpoint_levers_only": c_current,
            },
        })

    return {
        "tenant_id": str(tenant_id_uuid),
        "date_range": {"start": str(start_date), "end": str(end_date)},
        "policies": policies_breakdown,
    }


@router.get("/policies/{policy_id}/claim-counts-breakdown")
async def get_policy_claim_counts_breakdown(
    policy_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Claim counts breakdown for a single policy (scope+levers merged). Use on policy page."""
    from datetime import date, timedelta
    from uepi_api.repositories.canonical_data import CanonicalDataRepository
    from uepi_api.services.policy_scoped_data_generation import build_policy_claims_filters, validate_policy_scope

    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.tenant_id == current_user.tenant_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    tenant_id_uuid = current_user.tenant_id if isinstance(current_user.tenant_id, UUID) else UUID(str(current_user.tenant_id))
    repo = CanonicalDataRepository(db)
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    meta = getattr(policy, "policy_metadata_json", None) or {}
    policy_dict = {
        "scope": meta.get("scope") or {},
        "policy_levers": meta.get("policy_levers", []),
        "logic": meta.get("logic", {}),
        "policy_logic": meta.get("policy_logic", {}),
    }
    pf = build_policy_claims_filters(policy_dict)

    c_tenant = repo.count_claims_for_filters(tenant_id=tenant_id_uuid, start_date=start_date, end_date=end_date)
    c_lob_market = repo.count_claims_for_filters(
        tenant_id=tenant_id_uuid, start_date=start_date, end_date=end_date,
        lob=pf.get("lob"), market=pf.get("markets") or pf.get("market"),
    )
    c_full = repo.count_claims_for_filters(
        tenant_id=tenant_id_uuid, start_date=start_date, end_date=end_date,
        lob=pf.get("lob"), market=pf.get("markets") or pf.get("market"),
        cpt_codes=pf.get("cpt_codes"), hcpcs_codes=pf.get("cpt_codes"),
        service_categories=pf.get("service_categories"),
    )

    validation = validate_policy_scope(policy_dict) if policy_dict else {"valid": False, "issues": []}

    return {
        "policy_id": str(policy.id),
        "name": policy.name or "",
        "tenant_id": str(tenant_id_uuid),
        "date_range": {"start": str(start_date), "end": str(end_date)},
        "filters": {
            "lob": pf.get("lob"),
            "markets": pf.get("markets") or pf.get("market"),
            "procedure_codes_count": len(pf.get("cpt_codes") or []),
            "service_categories_count": len(pf.get("service_categories") or []),
        },
        "counts": {
            "tenant_and_date_only": c_tenant,
            "plus_lob_market": c_lob_market,
            "full_scope": c_full,
        },
        "validation": validation,
    }


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Get policy by ID"""
    try:
        policy = db.query(Policy).filter(
            Policy.id == policy_id,
            Policy.tenant_id == current_user.tenant_id,
        ).first()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Convert to response format
        policy_dict = {
            "id": str(policy.id),
            "tenant_id": str(policy.tenant_id),
            "name": policy.name,
            "policy_type": policy.policy_type,
            "owner_role": policy.owner_role,
            "description": policy.description,
            "status": getattr(policy, 'status', 'ACTIVE'),
            "created_at": policy.created_at.isoformat() if policy.created_at else None,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
        }
        
        if hasattr(policy, 'policy_metadata_json') and policy.policy_metadata_json:
            metadata = policy.policy_metadata_json
            if isinstance(metadata, dict):
                policy_dict.update({
                    "scope": metadata.get("scope"),
                    "effective_period": metadata.get("effective_period"),
                    "enforcement": metadata.get("enforcement"),
                    "policy_levers": metadata.get("policy_levers"),
                    "expected_behavioral_response": metadata.get("expected_behavioral_response"),
                    "analytics_expectations": metadata.get("analytics_expectations"),
                    "ui_hints": metadata.get("ui_hints"),
                })
        
        return PolicyResponse(**policy_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get policy: {e}")


@router.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: UUID,
    policy_data: PolicyCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Update policy"""
    try:
        policy = db.query(Policy).filter(
            Policy.id == policy_id,
            Policy.tenant_id == current_user.tenant_id,
        ).first()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        policy.name = policy_data.name
        policy.policy_type = policy_data.policy_type.value
        policy.owner_role = policy_data.owner_role
        policy.description = policy_data.description
        if policy_data.status:
            policy.status = policy_data.status.value
        policy.updated_at = datetime.utcnow()
        
        # Update policy_metadata_json - merge with existing metadata
        if not policy.policy_metadata_json:
            policy.policy_metadata_json = {}
        if not isinstance(policy.policy_metadata_json, dict):
            policy.policy_metadata_json = {}
        
        # Update metadata fields if provided
        if policy_data.policy_levers is not None:
            policy.policy_metadata_json['policy_levers'] = [lever.model_dump(mode='json') if hasattr(lever, 'model_dump') else lever for lever in policy_data.policy_levers]
        
        if policy_data.scope is not None:
            policy.policy_metadata_json['scope'] = policy_data.scope.model_dump(mode='json') if hasattr(policy_data.scope, 'model_dump') else policy_data.scope
        
        if policy_data.effective_period is not None:
            policy.policy_metadata_json['effective_period'] = policy_data.effective_period.model_dump(mode='json') if hasattr(policy_data.effective_period, 'model_dump') else policy_data.effective_period
        
        if policy_data.enforcement is not None:
            policy.policy_metadata_json['enforcement'] = policy_data.enforcement.model_dump(mode='json') if hasattr(policy_data.enforcement, 'model_dump') else policy_data.enforcement
        
        if policy_data.expected_behavioral_response is not None:
            policy.policy_metadata_json['expected_behavioral_response'] = policy_data.expected_behavioral_response.model_dump(mode='json') if hasattr(policy_data.expected_behavioral_response, 'model_dump') else policy_data.expected_behavioral_response
        
        if policy_data.analytics_expectations is not None:
            policy.policy_metadata_json['analytics_expectations'] = policy_data.analytics_expectations.model_dump(mode='json') if hasattr(policy_data.analytics_expectations, 'model_dump') else policy_data.analytics_expectations
        
        if policy_data.ui_hints is not None:
            policy.policy_metadata_json['ui_hints'] = policy_data.ui_hints.model_dump(mode='json') if hasattr(policy_data.ui_hints, 'model_dump') else policy_data.ui_hints
        
        db.commit()
        db.refresh(policy)
        
        # Convert to response format
        policy_dict = {
            "id": str(policy.id),
            "tenant_id": str(policy.tenant_id),
            "name": policy.name,
            "policy_type": policy.policy_type,
            "owner_role": policy.owner_role,
            "description": policy.description,
            "status": getattr(policy, 'status', 'ACTIVE'),
            "created_at": policy.created_at.isoformat() if policy.created_at else None,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
        }
        
        if hasattr(policy, 'policy_metadata_json') and policy.policy_metadata_json:
            metadata = policy.policy_metadata_json
            if isinstance(metadata, dict):
                policy_dict.update({
                    "scope": metadata.get("scope"),
                    "effective_period": metadata.get("effective_period"),
                    "enforcement": metadata.get("enforcement"),
                    "policy_levers": metadata.get("policy_levers"),
                })
        
        return PolicyResponse(**policy_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update policy: {e}")


class PolicyStatusUpdate(PydanticBaseModel):
    """Policy status update model"""
    status: PolicyStatus


@router.patch("/policies/{policy_id}/status", response_model=PolicyResponse)
async def update_policy_status(
    policy_id: UUID,
    status_data: PolicyStatusUpdate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Activate or deactivate a policy"""
    status_value = status_data.status.value
    
    try:
        policy = db.query(Policy).filter(
            Policy.id == policy_id,
            Policy.tenant_id == current_user.tenant_id,
        ).first()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Validate status value
        valid_statuses = ["ACTIVE", "DRAFT", "RETIRED", "INACTIVE"]
        if status_value not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        policy.status = status_value
        policy.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(policy)
        
        # Convert to response format
        policy_dict = {
            "id": str(policy.id),
            "tenant_id": str(policy.tenant_id),
            "name": policy.name,
            "policy_type": policy.policy_type,
            "owner_role": policy.owner_role,
            "description": policy.description,
            "status": policy.status,
            "created_at": policy.created_at.isoformat() if policy.created_at else None,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
        }
        
        if hasattr(policy, 'policy_metadata_json') and policy.policy_metadata_json:
            metadata = policy.policy_metadata_json
            if isinstance(metadata, dict):
                policy_dict.update({
                    "scope": metadata.get("scope"),
                    "effective_period": metadata.get("effective_period"),
                    "enforcement": metadata.get("enforcement"),
                })
        
        return PolicyResponse(**policy_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update policy status: {e}")


@router.post("/policies/{policy_id}/versions", status_code=201)
async def create_policy_version(
    policy_id: UUID,
    version_data: PolicyVersionCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Create a new policy version"""
    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.tenant_id == current_user.tenant_id,
    ).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Get next version number
    max_version = db.query(PolicyVersion).filter(
        PolicyVersion.policy_id == policy_id,
    ).order_by(PolicyVersion.version_number.desc()).first()
    
    version_number = (max_version.version_number + 1) if max_version else 1
    
    version = PolicyVersion(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id,
        version_number=version_number,
        effective_start_date=version_data.effective_start_date,
        effective_end_date=version_data.effective_end_date,
        change_type=version_data.change_type.value,
        enforcement_strength=version_data.enforcement_strength.value,
        justification=version_data.justification,
    )
    db.add(version)
    db.flush()
    
    # Add code sets
    for code_set_data in version_data.code_sets:
        code_set = PolicyCodeSet(
            tenant_id=current_user.tenant_id,
            version_id=version.id,
            code_type=code_set_data.code_type.value,
            code=code_set_data.code,
            code_group=code_set_data.code_group,
        )
        db.add(code_set)
    
    db.commit()
    db.refresh(version)
    return {
        "id": version.id,
        "policy_id": version.policy_id,
        "version_number": version.version_number,
        "effective_start_date": version.effective_start_date,
        "effective_end_date": version.effective_end_date,
        "change_type": version.change_type,
        "enforcement_strength": version.enforcement_strength,
    }


@router.get("/policies/{policy_id}/versions")
async def list_policy_versions(
    policy_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """List versions for a policy"""
    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.tenant_id == current_user.tenant_id,
    ).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    versions = db.query(PolicyVersion).filter(
        PolicyVersion.policy_id == policy_id,
        PolicyVersion.tenant_id == current_user.tenant_id,
    ).order_by(PolicyVersion.version_number.desc()).all()
    
    return [
        {
            "id": v.id,
            "version_number": v.version_number,
            "effective_start_date": v.effective_start_date,
            "effective_end_date": v.effective_end_date,
            "change_type": v.change_type,
            "enforcement_strength": v.enforcement_strength,
        }
        for v in versions
    ]


@router.get("/policies/{policy_id}/predicted-impact")
async def get_policy_predicted_impact(
    policy_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Get predicted impact for a policy (Stage 3.5) - from database"""
    from uepi_api.storage_policy_predicted_impact import get_predicted_impact
    
    try:
        # Get from dedicated database table (primary source - database-only)
        predicted_impact = get_predicted_impact(
            policy_id=policy_id,
            tenant_id=current_user.tenant_id,
        )
        
        # Fallback to metadata if not in dedicated table (backward compatibility)
        if not predicted_impact:
            from uepi_api.routers.policy_predicted_impact import get_predicted_impact_from_metadata
            # Load only metadata column to avoid fetching full policy row (faster)
            row = db.query(Policy.policy_metadata_json).filter(
                Policy.id == policy_id,
                Policy.tenant_id == current_user.tenant_id,
            ).first()
            if row is None:
                raise HTTPException(status_code=404, detail="Policy not found")
            policy_metadata = row[0] if hasattr(row, "__getitem__") else row
            predicted_impact = get_predicted_impact_from_metadata(policy_metadata)
        
        if not predicted_impact:
            raise HTTPException(status_code=404, detail="Predicted impact not found for this policy")
        
        return predicted_impact
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve predicted impact: {e}")


@router.post("/policies/{policy_id}/predicted-impact")
async def generate_policy_predicted_impact(
    policy_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Generate predicted impact for a policy (Stage 3.5)"""
    from uepi_api.routers.policy_predicted_impact import (
        generate_predicted_impact_for_policy,
        store_predicted_impact_in_metadata,
    )
    
    try:
        policy = db.query(Policy).filter(
            Policy.id == policy_id,
            Policy.tenant_id == current_user.tenant_id,
        ).first()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Get policy metadata
        policy_metadata = policy.policy_metadata_json if hasattr(policy, 'policy_metadata_json') else {}
        
        # Extract policy levers from metadata or policy structure
        policy_levers = policy_metadata.get("policy_levers", [])
        if not policy_levers and hasattr(policy, 'policy_levers'):
            # Try to extract from policy object if available
            policy_levers = policy.policy_levers or []
        
        policy_scope = policy_metadata.get("scope")
        if not policy_scope and hasattr(policy, 'scope'):
            policy_scope = policy.scope
        
        if not policy_levers:
            raise HTTPException(
                status_code=400,
                detail="Policy does not have policy levers. Predicted impact requires policy levers to be defined."
            )
        
        # Item 8: Load baseline metrics if available
        # Use policy-specific baseline first, then fall back to general baseline
        baseline_metrics = None
        try:
            from uepi_api.storage_baselines import get_latest_baseline
            # Try policy-specific baseline first (uses historical data before activation)
            baseline = get_latest_baseline(current_user.tenant_id, policy_id=policy_id)
            if not baseline:
                # Fall back to general baseline if no policy-specific baseline exists
                baseline = get_latest_baseline(current_user.tenant_id, policy_id=None)
            
            if baseline:
                baseline_metrics_dict = baseline.get("baseline_metrics", {}) or baseline.get("metrics", {})
                if baseline_metrics_dict:
                    # Map baseline metric names to predicted impact expected names
                    baseline_metrics = {
                        "utilization_per_1k": baseline_metrics_dict.get("util_rate_target_per_1000_mm") or baseline_metrics_dict.get("util_rate_total_per_1000_mm") or 0.0,
                        "cost_pmpm": baseline_metrics_dict.get("allowed_pmpm_target") or baseline_metrics_dict.get("allowed_pmpm_total") or 0.0,
                        "member_count": int(baseline_metrics_dict.get("unique_members", 0)),
                        "member_months": baseline_metrics_dict.get("member_months", 0),
                    }
                    # Remove None values
                    baseline_metrics = {k: v for k, v in baseline_metrics.items() if v is not None and v != 0}
                    if not baseline_metrics:
                        baseline_metrics = None
        except Exception as e:
            print(f"⚠️ Could not load baseline metrics for predicted impact: {e}")
            baseline_metrics = None  # Use None if baseline not available
        
        # Generate predicted impact
        predicted_impact = generate_predicted_impact_for_policy(
            tenant_id=current_user.tenant_id,
            policy_id=policy.id,
            policy_levers=policy_levers,
            policy_scope=policy_scope,
            baseline_metrics=baseline_metrics,
        )
        
        # Store predicted impact in database (dedicated table)
        from uepi_api.storage_policy_predicted_impact import store_predicted_impact
        from uepi_api.storage_baselines import get_latest_baseline
        
        # Get baseline_id for the predicted impact record
        baseline_id = None
        baseline = get_latest_baseline(current_user.tenant_id, policy_id=policy_id)
        if not baseline:
            baseline = get_latest_baseline(current_user.tenant_id, policy_id=None)
        if baseline and baseline.get("id"):
            baseline_id = baseline.get("id")
        
        # Store in dedicated database table (include enhanced data: confidence_intervals, ramp_up_projections)
        predicted_impact_dict = predicted_impact.model_dump(mode='json')
        enhanced_data = getattr(predicted_impact, '_enhanced_data', None) or {}
        stored_result = store_predicted_impact(
            policy_id=policy_id,
            tenant_id=current_user.tenant_id,
            predicted_impact_data={
                "metrics": predicted_impact_dict.get("metrics", {}),
                "model_version": predicted_impact_dict.get("model_version"),
                "confidence": predicted_impact_dict.get("confidence"),
                "predicted_at": predicted_impact_dict.get("predicted_at"),
                "prediction_method": predicted_impact_dict.get("prediction_method", "ELASTICITY_MODEL"),
                "baseline_id": str(baseline_id) if baseline_id else None,
                # Include all additional fields for frontend display
                "provider_response": predicted_impact_dict.get("provider_response"),
                "patient_response": predicted_impact_dict.get("patient_response"),
                "substitution_effects": predicted_impact_dict.get("substitution_effects", []),
                "warnings": predicted_impact_dict.get("warnings", []),
                "limitations": predicted_impact_dict.get("limitations", []),
                "baseline_reference": predicted_impact_dict.get("baseline_reference"),
                "model_versions": predicted_impact_dict.get("model_versions", {}),
                # Phase 1/2: confidence intervals and ramp-up projections
                "confidence_intervals": enhanced_data.get("confidence_intervals"),
                "ramp_up_projections": enhanced_data.get("ramp_up_projections"),
            }
        )
        
        # Also store in policy metadata for backward compatibility (but primary storage is database table)
        policy_metadata = store_predicted_impact_in_metadata(
            policy_metadata or {},
            predicted_impact,
        )
        policy.policy_metadata_json = policy_metadata
        db.commit()
        db.refresh(policy)
        
        # Return the predicted impact (include enhanced data for response)
        predicted_impact_dict = predicted_impact.model_dump(mode='json')
        if enhanced_data:
            predicted_impact_dict.update(enhanced_data)
        return predicted_impact_dict
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate predicted impact: {str(e)}")


@router.post("/policies/generate-predicted-impact")
async def generate_all_policies_predicted_impact(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    force: bool = Query(False, description="Force regenerate even if predicted impact exists"),
):
    """Generate predicted impact for all policies that don't have it (Stage 3.5)
    
    Args:
        force: If True, regenerate predicted impact even if it already exists
    """
    from uepi_api.routers.policy_predicted_impact import (
        generate_predicted_impact_for_policy,
        store_predicted_impact_in_metadata,
        get_predicted_impact_from_metadata,
    )
    
    results = {
        "total_policies": 0,
        "generated": 0,
        "skipped": 0,
        "errors": 0,
        "details": [],
    }
    
    try:
        # Get all policies for the tenant
        policies = db.query(Policy).filter(
            Policy.tenant_id == current_user.tenant_id,
        ).all()
        
        results["total_policies"] = len(policies)
        
        for policy in policies:
            try:
                # Check if predicted impact already exists
                policy_metadata = policy.policy_metadata_json if hasattr(policy, 'policy_metadata_json') else {}
                existing_predicted_impact = get_predicted_impact_from_metadata(policy_metadata)
                
                if existing_predicted_impact and not force:
                    results["skipped"] += 1
                    results["details"].append({
                        "policy_id": str(policy.id),
                        "policy_name": policy.name,
                        "status": "skipped",
                        "reason": "Predicted impact already exists",
                    })
                    continue
                
                # Extract policy levers
                policy_levers = policy_metadata.get("policy_levers", [])
                if not policy_levers:
                    results["skipped"] += 1
                    results["details"].append({
                        "policy_id": str(policy.id),
                        "policy_name": policy.name,
                        "status": "skipped",
                        "reason": "Policy does not have policy levers",
                    })
                    continue
                
                policy_scope = policy_metadata.get("scope")
                
                # Load baseline metrics from database (policy-specific if available, otherwise general)
                baseline_metrics = None
                try:
                    from uepi_api.storage_baselines import get_latest_baseline
                    # Try policy-specific baseline first
                    policy_baseline = get_latest_baseline(current_user.tenant_id, policy_id=policy.id)
                    if not policy_baseline:
                        # Fallback to general baseline
                        policy_baseline = get_latest_baseline(current_user.tenant_id, policy_id=None)
                    
                    if policy_baseline:
                        baseline_metrics_dict = policy_baseline.get("baseline_metrics", {}) or policy_baseline.get("metrics", {})
                        if baseline_metrics_dict:
                            # Map to format expected by predicted impact generator
                            baseline_metrics = {
                                "utilization_per_1k": baseline_metrics_dict.get("util_rate_target_per_1000_mm") or baseline_metrics_dict.get("util_rate_total_per_1000_mm") or 0.0,
                                "cost_pmpm": baseline_metrics_dict.get("allowed_pmpm_target") or baseline_metrics_dict.get("allowed_pmpm_total") or 0.0,
                                "member_count": int(baseline_metrics_dict.get("unique_members", 0)),
                                "member_months": baseline_metrics_dict.get("member_months", 0),
                            }
                except Exception as e:
                    print(f"Warning: Could not load baseline metrics for policy {policy.id}: {e}")
                
                # Generate predicted impact using real baseline data
                predicted_impact = generate_predicted_impact_for_policy(
                    tenant_id=current_user.tenant_id,
                    policy_id=policy.id,
                    policy_levers=policy_levers,
                    policy_scope=policy_scope,
                    baseline_metrics=baseline_metrics,  # Use real baseline metrics from database
                )
                
                # Store predicted impact in database (dedicated table - database-only)
                from uepi_api.storage_policy_predicted_impact import store_predicted_impact
                from datetime import datetime, timezone
                
                # Get baseline_id
                baseline_id = None
                if policy_baseline and policy_baseline.get("id"):
                    baseline_id = str(policy_baseline.get("id"))
                
                # Store in dedicated database table (primary storage; include enhanced data)
                predicted_impact_dict = predicted_impact.model_dump(mode='json')
                enhanced_data = getattr(predicted_impact, '_enhanced_data', None) or {}
                stored_result = store_predicted_impact(
                    policy_id=policy.id,
                    tenant_id=current_user.tenant_id,
                    predicted_impact_data={
                        "metrics": predicted_impact_dict.get("metrics", {}),
                        "model_version": predicted_impact_dict.get("model_version"),
                        "confidence": predicted_impact_dict.get("confidence"),
                        "predicted_at": datetime.now(timezone.utc).isoformat(),
                        "prediction_method": predicted_impact_dict.get("prediction_method", "ELASTICITY_MODEL"),
                        "baseline_id": baseline_id,
                        # Include all additional fields for frontend display
                        "provider_response": predicted_impact_dict.get("provider_response"),
                        "patient_response": predicted_impact_dict.get("patient_response"),
                        "substitution_effects": predicted_impact_dict.get("substitution_effects", []),
                        "warnings": predicted_impact_dict.get("warnings", []),
                        "limitations": predicted_impact_dict.get("limitations", []),
                        "baseline_reference": predicted_impact_dict.get("baseline_reference"),
                        "model_versions": predicted_impact_dict.get("model_versions", {}),
                        "confidence_intervals": enhanced_data.get("confidence_intervals"),
                        "ramp_up_projections": enhanced_data.get("ramp_up_projections"),
                    }
                )
                
                # Also store in policy metadata for backward compatibility
                policy_metadata = store_predicted_impact_in_metadata(
                    policy_metadata or {},
                    predicted_impact,
                )
                policy.policy_metadata_json = policy_metadata
                db.commit()
                db.refresh(policy)
                
                results["generated"] += 1
                results["details"].append({
                    "policy_id": str(policy.id),
                    "policy_name": policy.name,
                    "status": "generated",
                    "confidence_score": predicted_impact.metrics.confidence_score,
                })
                
            except Exception as e:
                results["errors"] += 1
                results["details"].append({
                    "policy_id": str(policy.id),
                    "policy_name": policy.name,
                    "status": "error",
                    "error": str(e),
                })
                continue
        
        # Commit all changes
        db.commit()
        
        return results
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate predicted impact for policies: {str(e)}")


@router.post("/policies/complete-scope-and-regenerate")
async def complete_scope_and_regenerate(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Complete scope for all policies, remove policy-level baselines, regenerate baselines, generate predicted impact."""
    from uepi_api.storage_baselines import delete_policy_level_baselines
    from uepi_api.baseline_refresh import refresh_baseline
    from uepi_api.storage_policies import get_policy
    from uepi_api.routers.policy_predicted_impact import generate_predicted_impact_for_policy, store_predicted_impact_in_metadata

    tenant_id_uuid = current_user.tenant_id if isinstance(current_user.tenant_id, UUID) else UUID(str(current_user.tenant_id))

    # 1. Complete scope (call complete-configurations logic inline)
    policies = db.query(Policy).filter(Policy.tenant_id == tenant_id_uuid).all()
    default_scope = {
        "lob": ["COMMERCIAL", "MA", "MEDICAID"],
        "markets": ["BOS", "DFW", "NYC"],
        "network": ["IN"],
        "procedure_codes": ["99213", "99214", "72148", "72149"],
        "service_categories": ["PRIMARY_CARE", "ADVANCED_IMAGING"],
    }
    scope_updated = 0
    for policy in policies:
        metadata = dict(policy.policy_metadata_json or {})
        scope = dict(metadata.get("scope") or {})
        changed = False
        for key, val in default_scope.items():
            if not scope.get(key):
                scope[key] = val
                changed = True
        if changed:
            metadata["scope"] = scope
            if not metadata.get("policy_levers"):
                metadata["policy_levers"] = [{"lever_type": "PRIOR_AUTH", "targets": {"procedure_codes": default_scope["procedure_codes"][:4]}}]
            policy.policy_metadata_json = metadata
            scope_updated += 1
    db.commit()

    # 2. Delete policy-level baselines
    deleted = delete_policy_level_baselines(tenant_id_uuid)

    # 3. Regenerate baselines for all policies
    baseline_success = 0
    for policy in policies:
        try:
            b = refresh_baseline(tenant_id=tenant_id_uuid, policy_id=policy.id, baseline_type="ROLLING", window_months=12, refresh_reason="SCOPE_COMPLETE_REGEN", db=db)
            if b:
                baseline_success += 1
        except Exception:
            pass

    # 4. Generate predicted impact for all policies
    impact_success = 0
    for policy in policies:
        try:
            policy_data = get_policy(policy.id, tenant_id_uuid)
            if not policy_data:
                continue
            meta = policy_data.get("policy_metadata_json") or policy_data.get("metadata") or {}
            result = generate_predicted_impact_for_policy(
                tenant_id=tenant_id_uuid,
                policy_id=policy.id,
                policy_levers=meta.get("policy_levers", []),
                policy_scope=meta.get("scope", {}),
                baseline_metrics=None,
            )
            updated_metadata = store_predicted_impact_in_metadata(dict(meta), result)
            policy.policy_metadata_json = updated_metadata
            impact_success += 1
        except Exception:
            pass
    db.commit()

    return {
        "scope_updated": scope_updated,
        "baselines_deleted": deleted,
        "baselines_regenerated": baseline_success,
        "predicted_impacts_generated": impact_success,
        "total_policies": len(policies),
    }


@router.post("/policies/complete-configurations")
async def complete_policy_configurations(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Complete configurations for all policies - add missing levers, scope, conditions, exceptions"""
    try:
        from datetime import datetime as dt
        
        # Get all policies for the tenant
        policies = db.query(Policy).filter(Policy.tenant_id == current_user.tenant_id).all()
        
        updated_count = 0
        skipped_count = 0
        errors_list = []
        
        def get_default_scope():
            """Scope matching common claims data (LOB, markets used in claims_lines)."""
            return {
                "lob": ["COMMERCIAL", "MA", "MEDICAID"],
                "markets": ["BOS", "DFW", "NYC"],
                "network": ["IN"],
                "procedure_codes": ["99213", "99214", "72148", "72149"],  # Primary care + imaging
                "service_categories": ["PRIMARY_CARE", "ADVANCED_IMAGING"],
            }
        
        def get_default_effective_period():
            return {
                "start_date": dt.now().isoformat(),
                "end_date": None
            }
        
        def get_default_levers_for_policy_type(policy_type: str, policy_codes: list[str] = None):
            if not policy_codes:
                policy_codes = ["72148", "72149"]
            
            policy_type_upper = policy_type.upper()
            
            if policy_type_upper in ["PRIOR_AUTH", "PA"]:
                return [{
                    "lever_type": "PRIOR_AUTH",
                    "parameters": {
                        "requires_pa": True,
                        "pa_touchpoint": "PA_WORKFLOW",
                        "override_allowed": False,
                    },
                    "targets": {
                        "code_type": "CPT",
                        "codes": policy_codes[:5],
                        "code_groups": [],
                    }
                }]
            elif policy_type_upper in ["SITE_OF_CARE"]:
                return [{
                    "lever_type": "SITE_OF_CARE",
                    "parameters": {
                        "allowed_sites": ["FREESTANDING", "OFFICE"],
                        "disallowed_sites": ["HOSPITAL_OP"],
                        "redirect_to": "FREESTANDING",
                        "deny_if_disallowed": False,
                    },
                    "targets": {
                        "code_type": "CPT",
                        "codes": policy_codes[:5],
                        "code_groups": [],
                    }
                }]
            elif policy_type_upper in ["DURATION_FREQUENCY_LIMIT", "FREQUENCY_LIMIT"]:
                return [{
                    "lever_type": "DURATION_FREQUENCY_LIMIT",
                    "parameters": {
                        "max_visits": 20,
                        "time_period": "YEAR",
                        "reset_date": "CALENDAR_YEAR",
                        "accumulate_across_providers": True,
                    },
                    "targets": {
                        "code_type": "CPT",
                        "codes": policy_codes[:5],
                        "code_groups": [],
                    }
                }]
            elif policy_type_upper in ["COST_SHARING"]:
                return [{
                    "lever_type": "COST_SHARING",
                    "parameters": {
                        "copay": 75.0,
                        "coinsurance": 0.0,
                        "deductible_applies": False,
                        "out_of_pocket_applies": True,
                    },
                    "targets": {
                        "code_type": "CPT",
                        "codes": policy_codes[:5],
                        "code_groups": [],
                    }
                }]
            elif policy_type_upper in ["NETWORK_RESTRICTION"]:
                return [{
                    "lever_type": "NETWORK_RESTRICTION",
                    "parameters": {
                        "allowed_network": ["IN"],
                        "oon_allowed": False,
                    },
                    "targets": {
                        "code_type": "CPT",
                        "codes": policy_codes[:5],
                        "code_groups": [],
                    }
                }]
            elif policy_type_upper in ["STEP_THERAPY"]:
                return [{
                    "lever_type": "STEP_THERAPY",
                    "parameters": {
                        "requires_step_therapy": True,
                        "steps": [],
                    },
                    "targets": {
                        "code_type": "CPT",
                        "codes": policy_codes[:5],
                        "code_groups": [],
                    }
                }]
            elif policy_type_upper in ["COVERAGE"]:
                return [{
                    "lever_type": "COVERAGE",
                    "parameters": {
                        "covered": True,
                        "coverage_level": "STANDARD",
                    },
                    "targets": {
                        "code_type": "CPT",
                        "codes": policy_codes[:5],
                        "code_groups": [],
                    }
                }]
            elif policy_type_upper in ["BENEFIT"]:
                return [{
                    "lever_type": "COST_SHARING",
                    "parameters": {
                        "copay": 50.0,
                        "coinsurance": 0.0,
                        "deductible_applies": True,
                    },
                    "targets": {
                        "code_type": "CPT",
                        "codes": policy_codes[:5],
                        "code_groups": [],
                    }
                }]
            else:
                return [{
                    "lever_type": "PRIOR_AUTH",
                    "parameters": {
                        "requires_pa": True,
                    },
                    "targets": {
                        "code_type": "CPT",
                        "codes": policy_codes[:5],
                        "code_groups": [],
                    }
                }]
        
        for policy in policies:
            try:
                metadata = policy.policy_metadata_json if policy.policy_metadata_json else {}
                
                # Check if policy already has complete configuration
                has_levers = metadata.get("policy_levers") and len(metadata.get("policy_levers", [])) > 0
                has_scope = metadata.get("scope")
                has_effective_period = metadata.get("effective_period")
                
                if has_levers and has_scope and has_effective_period:
                    skipped_count += 1
                    continue
                
                # Get codes from policy version if available
                version = db.query(PolicyVersion).filter(
                    PolicyVersion.policy_id == policy.id
                ).order_by(PolicyVersion.version_number.desc()).first()
                
                policy_codes = []
                if version:
                    code_sets = db.query(PolicyCodeSet).filter(
                        PolicyCodeSet.version_id == version.id,
                        PolicyCodeSet.code_type == "CPT"
                    ).all()
                    policy_codes = [cs.code for cs in code_sets]
                
                # Add missing configurations
                needs_update = False
                
                # Add scope if missing, or complete incomplete scope
                default_scope = get_default_scope()
                scope = metadata.get("scope") or {}
                if not isinstance(scope, dict):
                    scope = {}
                scope_updated = False
                for key, default_val in default_scope.items():
                    if not scope.get(key):
                        scope[key] = default_val
                        scope_updated = True
                if scope_updated or not has_scope:
                    metadata["scope"] = scope
                    needs_update = True
                
                # Add effective period if missing
                if not has_effective_period:
                    if version and version.effective_start_date:
                        metadata["effective_period"] = {
                            "start_date": version.effective_start_date.isoformat() if hasattr(version.effective_start_date, 'isoformat') else str(version.effective_start_date),
                            "end_date": version.effective_end_date.isoformat() if version.effective_end_date and hasattr(version.effective_end_date, 'isoformat') else (str(version.effective_end_date) if version.effective_end_date else None)
                        }
                    else:
                        metadata["effective_period"] = get_default_effective_period()
                    needs_update = True
                
                # Add policy levers if missing
                if not has_levers:
                    levers = get_default_levers_for_policy_type(policy.policy_type, policy_codes)
                    metadata["policy_levers"] = levers
                    needs_update = True
                
                # Add empty conditions and exceptions if missing
                if "apply_when" not in metadata:
                    metadata["apply_when"] = []
                    needs_update = True
                
                if "global_exceptions" not in metadata:
                    metadata["global_exceptions"] = []
                    needs_update = True
                
                # Update policy if changes were made
                if needs_update:
                    policy.policy_metadata_json = metadata
                    policy.updated_at = dt.utcnow()
                    db.commit()
                    updated_count += 1
                
            except Exception as e:
                errors_list.append({"policy_id": str(policy.id), "policy_name": policy.name, "error": str(e)})
                db.rollback()
                continue
        
        return {
            "total_policies": len(policies),
            "updated": updated_count,
            "skipped": skipped_count,
            "errors": errors_list
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to complete policy configurations: {str(e)}")

