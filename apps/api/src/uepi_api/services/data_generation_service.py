"""Data generation service - Generates claims data for demonstration"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import date, datetime, timedelta
from pathlib import Path
import pandas as pd
import random

from sqlalchemy.orm import Session
from uepi_api.database import SessionLocal
from uepi_api.repositories.canonical_data import CanonicalDataRepository


def generate_claims_data_for_date(
    tenant_id: UUID,
    target_date: date,
    member_count: int = 10000,
    claims_per_member: float = 2.5,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Generate claims data for a specific date and load to database
    
    This generates realistic claims data for demonstration purposes.
    Data is loaded directly to database claims_lines table.
    
    Args:
        tenant_id: Tenant ID
        target_date: Date for which to generate data
        member_count: Number of members to generate claims for
        claims_per_member: Average claims per member for the date
    
    Returns:
        Dict with generation results
    """
    from sqlalchemy.orm import Session
    
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        repo = CanonicalDataRepository(db)
        
        # Generate member IDs (use existing members from database if available)
        existing_claims = repo.get_claims_lines(tenant_id=tenant_id, limit=1000)
        if not existing_claims.empty and 'member_id' in existing_claims.columns:
            member_ids = existing_claims['member_id'].unique().tolist()
            # Extend with generated IDs if needed
            while len(member_ids) < member_count:
                member_ids.append(f"MEM_{len(member_ids):06d}")
            member_ids = member_ids[:member_count]
        else:
            member_ids = [f"MEM_{i:06d}" for i in range(member_count)]
        
        # Generate provider IDs
        if not existing_claims.empty and 'provider_id' in existing_claims.columns:
            provider_ids = existing_claims['provider_id'].unique().tolist()
            if len(provider_ids) < 100:
                provider_ids.extend([f"PROV_{i:05d}" for i in range(len(provider_ids), 100)])
        else:
            provider_ids = [f"PROV_{i:05d}" for i in range(100)]
        
        # Service categories and codes
        service_categories = {
            "PRIMARY_CARE": {"codes": ["99213", "99214", "99215"], "avg_cost": 150.0},
            "SPECIALTY_CARE": {"codes": ["99243", "99244", "99245"], "avg_cost": 300.0},
            "ADVANCED_IMAGING": {"codes": ["70450", "72141", "72142"], "avg_cost": 800.0},
            "LABORATORY": {"codes": ["80053", "85025", "85027"], "avg_cost": 50.0},
            "URGENT_CARE": {"codes": ["99281", "99282", "99283"], "avg_cost": 200.0},
        }
        
        # Generate claims
        total_claims = int(member_count * claims_per_member)
        claims_data = []
        
        # Use deterministic seed based on date for reproducibility
        random.seed(int(target_date.strftime("%Y%m%d")))  # Deterministic based on date
        
        print(f"   Generating {total_claims} claims for {target_date.isoformat()}...")
        
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
            paid_amount = allowed_amount * random.uniform(0.8, 1.0)  # Insurance pays 80-100%
            
            # Generate system affiliation (required for baseline analysis)
            system_affiliations = ["HOSPITAL_SYSTEM_A", "HOSPITAL_SYSTEM_B", "INDEPENDENT", "PHYSICIAN_GROUP"]
            system_affiliation = random.choice(system_affiliations)
            
            # Generate unique claim_line_id with timestamp to avoid duplicates
            import time
            timestamp_suffix = int(time.time() * 1000000) % 1000000  # Microsecond precision, mod for shorter ID
            claim_data = {
                'tenant_id': tenant_id,
                'claim_id': f"CLM_{target_date.strftime('%Y%m%d')}_{i:06d}_{timestamp_suffix:06d}",
                'claim_line_id': f"CLM_{target_date.strftime('%Y%m%d')}_{i:06d}_01_{timestamp_suffix:06d}",
                'member_id': member_id,
                'provider_id': provider_id,
                'service_date': target_date,
                'paid_date': target_date + timedelta(days=random.randint(1, 30)),
                'lob': random.choice(["COMMERCIAL", "MEDICARE", "MEDICAID"]),
                'market': random.choice(["CA", "TX", "NY", "FL"]),
                'cpt_code': cpt_code,
                'hcpcs_code': '',
                'procedure_code': cpt_code,  # Alias for compatibility
                'primary_diagnosis_code': random.choice(["E11.9", "I10", "M79.3", "Z00.00"]),  # Common diagnosis codes
                'secondary_diagnosis_code': None,
                'service_category': category,
                'place_of_service': random.choice(["11", "22", "23"]),  # Office, Outpatient, ER
                'units': float(random.randint(1, 3)),
                'allowed_amount': float(allowed_amount),
                'paid_amount': float(paid_amount),
                'member_cost_share': float(allowed_amount - paid_amount),
                'in_network': random.choice([True, True, True, False]),  # 75% in-network
                'system_affiliation': system_affiliation,  # Required for baseline analysis
                'facility_type': random.choice(["HOSPITAL", "CLINIC", "OFFICE", "URGENT_CARE"]),
                'source_system': 'DATA_GENERATOR',
                'source_file_id': f"generated_{target_date.isoformat()}",
                'ingestion_id': UUID('00000000-0000-0000-0000-000000000000'),
            }
            claims_data.append(claim_data)
        
        # Bulk insert to database (with duplicate handling)
        try:
            loaded_count = repo.bulk_insert_claims_lines(
                tenant_id=tenant_id,
                claims_data=claims_data,
                source_system='DATA_GENERATOR',
                source_file_id=f"generated_{target_date.isoformat()}",
                ingestion_id=UUID('00000000-0000-0000-0000-000000000000'),
            )
            
            # Commit the transaction
            db.commit()
        except Exception as insert_error:
            error_str = str(insert_error)
            # Check if it's a duplicate key error
            if "duplicate" in error_str.lower() or "unique constraint" in error_str.lower() or "uq_claims_lines" in error_str.lower():
                db.rollback()
                # Data already exists for this date - return success with existing count
                existing_count = repo.count_claims_lines(tenant_id)
                return {
                    "success": True,
                    "target_date": target_date.isoformat(),
                    "claims_generated": len(claims_data),
                    "claims_loaded": 0,  # No new claims loaded (already exist)
                    "members_covered": len(set(c['member_id'] for c in claims_data)),
                    "message": f"Data already exists for {target_date.isoformat()}",
                }
            else:
                db.rollback()
                raise  # Re-raise if it's a different error
        
        return {
            "success": True,
            "target_date": target_date.isoformat(),
            "claims_generated": len(claims_data),
            "claims_loaded": loaded_count,
            "members_covered": len(set(c['member_id'] for c in claims_data)),
        }
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in generate_claims_data_for_date: {e}")
        print(f"Traceback: {error_trace}")
        return {
            "success": False,
            "error": str(e),
            "traceback": error_trace,
        }
    finally:
        if should_close:
            db.close()
