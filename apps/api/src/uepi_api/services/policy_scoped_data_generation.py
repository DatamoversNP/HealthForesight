"""Policy-scoped data generation - Generate claims data that matches policy scopes"""
from typing import Dict, Any, List, Optional, Set
from uuid import UUID, uuid4
from datetime import date, datetime, timedelta
from pathlib import Path
import pandas as pd
import random

from sqlalchemy.orm import Session
from uepi_api.database import SessionLocal
from uepi_api.repositories.canonical_data import CanonicalDataRepository
from uepi_api.storage_policies import get_policy


def extract_policy_target_codes(policy: Dict[str, Any]) -> Dict[str, List[str]]:
    """Extract target codes from policy levers and scope
    
    Returns:
        Dict with:
        - procedure_codes: List of CPT/HCPCS codes
        - diagnosis_codes: List of ICD codes
        - service_categories: List of service categories
        - lob: List of lines of business
        - markets: List of markets
    """
    target_codes = {
        "procedure_codes": [],
        "diagnosis_codes": [],
        "service_categories": [],
        "lob": [],
        "markets": [],
    }
    
    # Extract from policy scope (top-level or metadata)
    meta = policy.get("policy_metadata_json") or policy.get("metadata") or {}
    policy_scope = policy.get("scope") or meta.get("scope") or {}
    policy_scope = policy_scope if isinstance(policy_scope, dict) else {}
    if policy_scope:
        if policy_scope.get("lob"):
            lob_value = policy_scope["lob"]
            target_codes["lob"] = lob_value if isinstance(lob_value, list) else [lob_value]
        
        if policy_scope.get("markets"):
            markets_value = policy_scope["markets"]
            target_codes["markets"] = markets_value if isinstance(markets_value, list) else [markets_value]
    
    # Extract from policy levers
    # Try multiple locations for policy levers (different policy structures)
    policy_levers = []
    
    # Option 1: policy.policy_levers (top-level, used by some policies)
    if policy.get("policy_levers"):
        policy_levers = policy["policy_levers"]
    
    # Option 2: policy.logic.policy_levers or policy.logic.levers
    if not policy_levers:
        policy_logic = policy.get("logic", {}) or policy.get("policy_logic", {}) or {}
        policy_levers = policy_logic.get("policy_levers", []) or policy_logic.get("levers", []) or []
    
    for lever in policy_levers:
        if not isinstance(lever, dict):
            continue
        
        # Extract codes from either "targets" or "parameters" (different structures)
        targets = lever.get("targets", {}) or {}
        parameters = lever.get("parameters", {}) or {}
        
        # Combine both sources
        all_codes = {}
        if targets:
            all_codes.update(targets)
        if parameters:
            all_codes.update(parameters)
        
        # Procedure codes (CPT/HCPCS) - check multiple field names
        for code_field in ["procedure_codes", "cpt_codes", "hcpcs_codes", "codes"]:
            if all_codes.get(code_field):
                codes = all_codes[code_field]
                if isinstance(codes, list):
                    target_codes["procedure_codes"].extend(codes)
                else:
                    target_codes["procedure_codes"].append(codes)
        
        # Diagnosis codes (ICD) - check multiple field names
        for code_field in ["diagnosis_codes", "icd_codes", "diagnosis"]:
            if all_codes.get(code_field):
                codes = all_codes[code_field]
                if isinstance(codes, list):
                    target_codes["diagnosis_codes"].extend(codes)
                else:
                    target_codes["diagnosis_codes"].append(codes)
        
        # Service categories
        for cat_field in ["service_categories", "service_category", "categories"]:
            if all_codes.get(cat_field):
                cats = all_codes[cat_field]
                if isinstance(cats, list):
                    target_codes["service_categories"].extend(cats)
                else:
                    target_codes["service_categories"].append(cats)
    
    # Remove duplicates
    target_codes["procedure_codes"] = list(set(target_codes["procedure_codes"]))
    target_codes["diagnosis_codes"] = list(set(target_codes["diagnosis_codes"]))
    target_codes["service_categories"] = list(set(target_codes["service_categories"]))
    
    return target_codes


def build_policy_claims_filters(policy: Dict[str, Any]) -> Dict[str, Any]:
    """Build unified claims filters from policy scope + levers (merged, consistent across all policy operations).

    Use this for: baselines, predicted impact, observations, what-if, elasticity.
    Returns a dict suitable for CanonicalDataRepository.get_claims_lines, load_claims_from_database, etc.

    Returns:
        Dict with: lob, market, procedure_codes (cpt/hcpcs merged), service_categories, diagnosis_codes
    """
    meta = policy.get("policy_metadata_json") or policy.get("metadata") or {}
    scope = policy.get("scope") or meta.get("scope") or {}
    scope = scope if isinstance(scope, dict) else {}
    policy_levers = policy.get("policy_levers")
    if policy_levers is None:
        policy_levers = meta.get("policy_levers") or []
    logic = policy.get("logic") or meta.get("logic") or {}
    policy_logic = policy.get("policy_logic") or meta.get("policy_logic") or {}
    policy_dict = {
        "scope": scope,
        "policy_levers": policy_levers,
        "logic": logic,
        "policy_logic": policy_logic,
    }
    target_codes = extract_policy_target_codes(policy_dict)

    merged_procedure = []
    merged_service = []
    merged_diagnosis = []
    if scope.get("procedure_codes"):
        merged_procedure = scope["procedure_codes"] if isinstance(scope["procedure_codes"], list) else [scope["procedure_codes"]]
    merged_procedure = list(set(merged_procedure + (target_codes.get("procedure_codes") or [])))

    if scope.get("service_categories"):
        merged_service = scope["service_categories"] if isinstance(scope["service_categories"], list) else [scope["service_categories"]]
    elif scope.get("service_category"):
        merged_service = [scope["service_category"]]
    merged_service = list(set(merged_service + (target_codes.get("service_categories") or [])))

    if scope.get("diagnosis_codes"):
        merged_diagnosis = scope["diagnosis_codes"] if isinstance(scope["diagnosis_codes"], list) else [scope["diagnosis_codes"]]
    merged_diagnosis = list(set(merged_diagnosis + (target_codes.get("diagnosis_codes") or [])))

    lob = scope.get("lob")
    market = scope.get("markets") or scope.get("market")

    return {
        "lob": lob,
        "market": market,
        "markets": market if isinstance(market, list) else ([market] if market else None),
        "procedure_codes": merged_procedure if merged_procedure else None,
        "cpt_codes": merged_procedure if merged_procedure else None,
        "hcpcs_codes": merged_procedure if merged_procedure else None,
        "service_categories": merged_service if merged_service else None,
        "service_category": merged_service[0] if len(merged_service) == 1 else None,
        "diagnosis_codes": merged_diagnosis if merged_diagnosis else None,
    }


def validate_policy_scope(policy: Dict[str, Any]) -> Dict[str, Any]:
    """Validate policy scope and procedure codes are defined for analytics.

    Returns validation result with issues and recommendations.
    """
    scope = policy.get("scope", {}) or {}
    policy_dict = {
        "scope": scope,
        "policy_levers": policy.get("policy_levers", []),
        "logic": policy.get("logic", {}),
        "policy_logic": policy.get("policy_logic", {}),
    }
    pf = build_policy_claims_filters(policy_dict)

    issues = []
    if not scope:
        issues.append("Scope is empty")
    if not pf.get("lob") and not pf.get("market") and not pf.get("markets"):
        issues.append("LOB and markets not defined in scope")
    if not pf.get("cpt_codes") and not pf.get("procedure_codes"):
        issues.append("Procedure/CPT codes not defined (scope or levers)")
    if not pf.get("service_categories") and not pf.get("service_category"):
        issues.append("Service categories not defined (scope or levers)")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "has_scope": bool(scope),
        "has_lob": bool(pf.get("lob")),
        "has_markets": bool(pf.get("markets") or pf.get("market")),
        "has_procedure_codes": bool(pf.get("cpt_codes")),
        "has_service_categories": bool(pf.get("service_categories") or pf.get("service_category")),
    }


def generate_policy_scoped_claims_data(
    tenant_id: UUID,
    policy_id: UUID,
    target_date: date,
    member_count: int = 10000,
    claims_per_member: float = 2.5,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Generate claims data that matches a policy's scope
    
    This function generates data with procedure codes, diagnosis codes, and service
    categories that match the policy's scope, enabling policy-specific baseline computation.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
    
    try:
        # Get policy to extract scope
        policy = get_policy(policy_id, tenant_id)
        if not policy:
            return {
                "success": False,
                "error": f"Policy {policy_id} not found",
            }
        
        # Extract target codes from policy
        target_codes = extract_policy_target_codes(policy)
        
        repo = CanonicalDataRepository(db)
        
        # Get existing members and providers
        existing_claims = repo.get_claims_lines(tenant_id=tenant_id, limit=1000)
        if not existing_claims.empty and 'member_id' in existing_claims.columns:
            member_ids = existing_claims['member_id'].unique().tolist()
            while len(member_ids) < member_count:
                member_ids.append(f"MEM_{len(member_ids):06d}")
            member_ids = member_ids[:member_count]
        else:
            member_ids = [f"MEM_{i:06d}" for i in range(member_count)]
        
        if not existing_claims.empty and 'provider_id' in existing_claims.columns:
            provider_ids = existing_claims['provider_id'].unique().tolist()
            if len(provider_ids) < 100:
                provider_ids.extend([f"PROV_{i:05d}" for i in range(len(provider_ids), 100)])
        else:
            provider_ids = [f"PROV_{i:05d}" for i in range(100)]
        
        # Default service categories and codes (if policy doesn't specify)
        default_service_categories = {
            "PRIMARY_CARE": {"codes": ["99213", "99214", "99215"], "avg_cost": 150.0},
            "SPECIALTY_CARE": {"codes": ["99243", "99244", "99245"], "avg_cost": 300.0},
            "ADVANCED_IMAGING": {"codes": ["70450", "72141", "72142"], "avg_cost": 800.0},
            "LABORATORY": {"codes": ["80053", "85025", "85027"], "avg_cost": 50.0},
            "URGENT_CARE": {"codes": ["99281", "99282", "99283"], "avg_cost": 200.0},
        }
        
        # Use policy-specific codes if available, otherwise use defaults
        if target_codes["procedure_codes"]:
            # Map procedure codes to service categories
            service_categories = {}
            for code in target_codes["procedure_codes"]:
                # Determine category based on code
                if code.startswith("992"):
                    category = "PRIMARY_CARE" if code in ["99213", "99214", "99215"] else "SPECIALTY_CARE"
                elif code.startswith("7") or code.startswith("70") or code.startswith("72"):  # MRI codes start with 72
                    category = "ADVANCED_IMAGING"
                elif code.startswith("8"):
                    category = "LABORATORY"
                else:
                    category = "SPECIALTY_CARE"
                
                if category not in service_categories:
                    service_categories[category] = {"codes": [], "avg_cost": default_service_categories.get(category, {}).get("avg_cost", 800.0)}  # Higher cost for imaging
                service_categories[category]["codes"].append(code)
            
            print(f"   Using {len(target_codes['procedure_codes'])} policy-specific procedure codes: {target_codes['procedure_codes'][:5]}")
        else:
            # Use default categories, but filter by policy service_categories if specified
            if target_codes["service_categories"]:
                service_categories = {cat: default_service_categories[cat] for cat in target_codes["service_categories"] if cat in default_service_categories}
            else:
                service_categories = default_service_categories
        
        # If no service categories after filtering, use all defaults
        if not service_categories:
            service_categories = default_service_categories
        
        # Generate claims
        total_claims = int(member_count * claims_per_member)
        claims_data = []
        
        random.seed(int(target_date.strftime("%Y%m%d")) + hash(str(policy_id)) % 10000)  # Deterministic but policy-specific
        
        # Use policy scope LOB and markets - MUST match policy requirements
        # If policy specifies LOB/markets, use ONLY those (not random)
        lob_options = target_codes["lob"] if target_codes["lob"] else ["COMMERCIAL", "MEDICARE", "MEDICAID"]
        market_options = target_codes["markets"] if target_codes["markets"] else ["CA", "TX", "NY", "FL"]
        
        # Ensure we have at least one option
        if not lob_options:
            lob_options = ["COMMERCIAL"]
        if not market_options:
            market_options = ["CA"]
        
        print(f"   📋 Using LOB: {lob_options}, Markets: {market_options}")
        
        # Default diagnosis codes if not specified
        diagnosis_codes = target_codes["diagnosis_codes"] if target_codes["diagnosis_codes"] else ["E11.9", "I10", "M79.3", "Z00.00"]
        
        for i in range(total_claims):
            member_id = random.choice(member_ids)
            provider_id = random.choice(provider_ids)
            category = random.choice(list(service_categories.keys()))
            code_info = service_categories[category]
            cpt_code = random.choice(code_info["codes"])
            
            # Generate cost with variation
            base_cost = code_info["avg_cost"]
            cost_variation = random.uniform(0.7, 1.3)
            allowed_amount = base_cost * cost_variation
            paid_amount = allowed_amount * random.uniform(0.8, 1.0)
            
            # Generate system affiliation
            system_affiliations = ["HOSPITAL_SYSTEM_A", "HOSPITAL_SYSTEM_B", "INDEPENDENT", "PHYSICIAN_GROUP"]
            system_affiliation = random.choice(system_affiliations)
            
            # Generate unique claim IDs to avoid duplicate constraint violations
            unique_suffix = uuid4().hex[:8]
            claim_data = {
                'tenant_id': tenant_id,
                'claim_id': f"CLM_{target_date.strftime('%Y%m%d')}_{policy_id.hex[:8]}_{i:06d}_{unique_suffix}",
                'claim_line_id': f"CLM_{target_date.strftime('%Y%m%d')}_{policy_id.hex[:8]}_{i:06d}_01_{unique_suffix}",
                'member_id': member_id,
                'provider_id': provider_id,
                'service_date': target_date,
                'paid_date': target_date + timedelta(days=random.randint(1, 30)),
                'lob': random.choice(lob_options),  # Will always match policy if policy specifies
                'market': random.choice(market_options),  # Will always match policy if policy specifies
                'cpt_code': cpt_code,
                'hcpcs_code': '',
                'procedure_code': cpt_code,
                'primary_diagnosis_code': random.choice(diagnosis_codes),
                'secondary_diagnosis_code': None,
                'service_category': category,
                'place_of_service': random.choice(["11", "22", "23"]),
                'units': float(random.randint(1, 3)),
                'allowed_amount': float(allowed_amount),
                'paid_amount': float(paid_amount),
                'member_cost_share': float(allowed_amount - paid_amount),
                'in_network': random.choice([True, True, True, False]),
                'system_affiliation': system_affiliation,
                'facility_type': random.choice(["HOSPITAL", "CLINIC", "OFFICE", "URGENT_CARE"]),
                'source_system': 'DATA_GENERATOR',
                'source_file_id': f"generated_{policy_id.hex[:8]}_{target_date.isoformat()}",
                'ingestion_id': UUID('00000000-0000-0000-0000-000000000000'),
            }
            claims_data.append(claim_data)
        
        # Bulk insert to database (with duplicate handling)
        try:
            loaded_count = repo.bulk_insert_claims_lines(
                tenant_id=tenant_id,
                claims_data=claims_data,
                source_system='DATA_GENERATOR',
                source_file_id=f"generated_{policy_id.hex[:8]}_{target_date.isoformat()}",
                ingestion_id=UUID('00000000-0000-0000-0000-000000000000'),
            )
            db.commit()
        except Exception as insert_error:
            error_str = str(insert_error)
            import traceback
            error_trace = traceback.format_exc()
            print(f"ERROR in bulk_insert_claims_lines: {error_str}")
            print(f"Traceback: {error_trace}")
            
            if "duplicate" in error_str.lower() or "unique constraint" in error_str.lower():
                db.rollback()
                # Try to insert with ON CONFLICT handling or skip duplicates
                print(f"⚠️  Duplicate constraint violation - attempting to insert with conflict handling")
                # For now, return error so caller knows data wasn't loaded
                return {
                    "success": False,
                    "target_date": target_date.isoformat(),
                    "claims_generated": len(claims_data),
                    "claims_loaded": 0,
                    "members_covered": len(set(c['member_id'] for c in claims_data)),
                    "error": f"Duplicate constraint violation: {error_str[:200]}",
                }
            else:
                db.rollback()
                raise
        
        return {
            "success": True,
            "target_date": target_date.isoformat(),
            "claims_generated": len(claims_data),
            "claims_loaded": loaded_count,
            "members_covered": len(set(c['member_id'] for c in claims_data)),
            "policy_id": str(policy_id),
        }
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in generate_policy_scoped_claims_data: {e}")
        print(f"Traceback: {error_trace}")
        return {
            "success": False,
            "error": str(e),
            "traceback": error_trace,
        }
    finally:
        if should_close:
            db.close()
