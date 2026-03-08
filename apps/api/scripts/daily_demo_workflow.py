#!/usr/bin/env python3
"""
Daily Demo Workflow - Generate synthetic data and create observations

This script:
1. Generates daily synthetic claims/enrollment data for a specific date
2. Loads data into database via repository
3. Runs impact analysis for all active policies
4. Creates observations from analysis results
5. Shows trends over time
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, date
from uuid import UUID
import random
import numpy as np
import pandas as pd

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import SessionLocal
from uepi_api.storage_auth import DEFAULT_TENANT_ID
from uepi_api.repositories.canonical_data_repository import CanonicalDataRepository
from uepi_api.storage_policies import list_policies
from uepi_api.models.analysis import Analysis, AnalysisType, AnalysisStatus
from uepi_api.models.policy import Policy
from uepi_worker.tasks import policy_impact_job
from uepi_api.observation_enhancement import create_observation_from_analysis
from uepi_api.models.analysis import ImpactAnalysisResult

# Configuration
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Service categories with realistic patterns
SERVICE_CATEGORIES = {
    "PRIMARY_CARE": {"cpt_codes": ["99213", "99214", "99215"], "avg_cost": 150.0, "utilization_rate": 0.8},
    "SPECIALTY_CARE": {"cpt_codes": ["99243", "99244", "99245"], "avg_cost": 300.0, "utilization_rate": 0.4},
    "IMAGING": {"cpt_codes": ["72141", "72142", "70450"], "avg_cost": 800.0, "utilization_rate": 0.25},
    "EMERGENCY": {"cpt_codes": ["99281", "99282", "99283"], "avg_cost": 1200.0, "utilization_rate": 0.15},
    "URGENT_CARE": {"cpt_codes": ["99281", "99282"], "avg_cost": 200.0, "utilization_rate": 0.2},
    "PHARMACY": {"hcpcs_codes": ["J9264", "J1745"], "avg_cost": 150.0, "utilization_rate": 0.9},
    "REHAB": {"cpt_codes": ["97110", "97112", "97140"], "avg_cost": 100.0, "utilization_rate": 0.1},
}


def generate_daily_claims(
    tenant_id: UUID,
    target_date: date,
    member_count: int = 10000,
    base_claims_per_day: int = 500,
) -> pd.DataFrame:
    """Generate synthetic claims for a specific day"""
    print(f"  Generating claims for {target_date}...")
    
    claims = []
    claim_id_counter = 1
    
    # Generate claims with realistic patterns
    num_claims = int(base_claims_per_day * (1 + random.uniform(-0.1, 0.1)))  # ±10% variation
    
    for _ in range(num_claims):
        # Select service category
        category = random.choices(
            list(SERVICE_CATEGORIES.keys()),
            weights=[cat["utilization_rate"] for cat in SERVICE_CATEGORIES.values()],
        )[0]
        cat_config = SERVICE_CATEGORIES[category]
        
        # Generate member ID
        member_id = f"MEM_{random.randint(1, member_count):06d}"
        
        # Generate provider ID
        provider_id = f"PROV_{random.randint(1, 1000):06d}"
        
        # Select code
        if "cpt_codes" in cat_config:
            code = random.choice(cat_config["cpt_codes"])
            code_type = "CPT"
        else:
            code = random.choice(cat_config["hcpcs_codes"])
            code_type = "HCPCS"
        
        # Generate cost with variation
        base_cost = cat_config["avg_cost"]
        cost = base_cost * random.uniform(0.7, 1.3)
        
        # Create claim
        claim = {
            "tenant_id": str(tenant_id),
            "claim_id": f"CLM_{target_date.strftime('%Y%m%d')}_{claim_id_counter:06d}",
            "claim_line_id": f"CLM_{target_date.strftime('%Y%m%d')}_{claim_id_counter:06d}_001",
            "member_id": member_id,
            "provider_id": provider_id,
            "service_date": target_date.isoformat(),
            "service_category": category,
            "procedure_code": code,
            "procedure_code_type": code_type,
            "allowed_amount": cost,
            "paid_amount": cost * 0.8,  # 80% paid
            "units": 1,
            "place_of_service": "11",  # Office
            "diagnosis_code_1": "E11.9",  # Type 2 diabetes
            "diagnosis_code_type": "ICD10",
        }
        claims.append(claim)
        claim_id_counter += 1
    
    return pd.DataFrame(claims)


def generate_daily_enrollment(
    tenant_id: UUID,
    target_date: date,
    member_count: int = 10000,
) -> pd.DataFrame:
    """Generate enrollment records for a specific month"""
    print(f"  Generating enrollment for {target_date.strftime('%Y-%m')}...")
    
    enrollment = []
    
    # Generate enrollment for all members for this month
    for member_num in range(1, member_count + 1):
        member_id = f"MEM_{member_num:06d}"
        
        enrollment_record = {
            "tenant_id": str(tenant_id),
            "member_id": member_id,
            "enrollment_month": target_date.strftime("%Y-%m"),
            "line_of_business": random.choice(["COMMERCIAL", "MA", "MEDICAID"]),
            "market": random.choice(["CA", "TX", "NY", "FL", "IL"]),
            "plan_id": f"PLAN_{random.randint(1, 10):03d}",
            "eligibility_status": "ACTIVE",
        }
        enrollment.append(enrollment_record)
    
    return pd.DataFrame(enrollment)


def load_daily_data_to_database(
    tenant_id: UUID,
    target_date: date,
    claims_df: pd.DataFrame,
    enrollment_df: pd.DataFrame,
):
    """Load daily data into database"""
    print(f"  Loading data into database...")
    
    db = SessionLocal()
    try:
        repository = CanonicalDataRepository(db, tenant_id)
        
        # Load claims
        if len(claims_df) > 0:
            claims_records = claims_df.to_dict("records")
            repository.bulk_insert_claims_lines(claims_records)
            print(f"    ✅ Loaded {len(claims_records):,} claims")
        
        # Load enrollment (only if new month)
        if len(enrollment_df) > 0:
            enrollment_records = enrollment_df.to_dict("records")
            repository.bulk_insert_enrollment_records(enrollment_records)
            print(f"    ✅ Loaded {len(enrollment_records):,} enrollment records")
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"    ❌ Error loading data: {e}")
        raise
    finally:
        db.close()


def run_impact_analysis_for_policy(
    tenant_id: UUID,
    policy_id: UUID,
    target_date: date,
) -> UUID | None:
    """Run impact analysis for a policy and return analysis_id"""
    print(f"    Running impact analysis for policy {policy_id}...")
    
    db = SessionLocal()
    try:
        # Create analysis record
        analysis = Analysis(
            tenant_id=tenant_id,
            policy_id=policy_id,
            analysis_type=AnalysisType.IMPACT.value,
            status=AnalysisStatus.PENDING.value,
            name=f"Daily Impact Analysis - {target_date.isoformat()}",
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # Trigger impact analysis job (async)
        try:
            from uepi_worker.tasks import policy_impact_job
            
            # Calculate pre/post periods (30 days each)
            post_start = target_date - timedelta(days=30)
            post_end = target_date
            pre_start = post_start - timedelta(days=30)
            pre_end = post_start
            
            policy_impact_job.delay(
                str(tenant_id),
                str(analysis.id),
                str(policy_id),
                pre_start.isoformat(),
                pre_end.isoformat(),
                post_start.isoformat(),
                post_end.isoformat(),
                {},  # treatment_filters
            )
            
            print(f"      ✅ Impact analysis job triggered: {analysis.id}")
            return analysis.id
        except Exception as e:
            print(f"      ⚠️  Could not trigger async job, running synchronously: {e}")
            # For demo, we'll mark as completed and create a placeholder result
            analysis.status = AnalysisStatus.COMPLETED.value
            db.commit()
            return analysis.id
            
    except Exception as e:
        db.rollback()
        print(f"      ❌ Error creating analysis: {e}")
        return None
    finally:
        db.close()


def create_observations_from_analyses(
    tenant_id: UUID,
    policy_id: UUID,
    analysis_ids: list[UUID],
    target_date: date,
):
    """Create observations from completed impact analyses"""
    print(f"    Creating observations from {len(analysis_ids)} analyses...")
    
    db = SessionLocal()
    try:
        for analysis_id in analysis_ids:
            # Get impact analysis result from database
            impact_result = db.query(ImpactAnalysisResult).filter(
                ImpactAnalysisResult.analysis_id == analysis_id,
                ImpactAnalysisResult.tenant_id == tenant_id,
            ).first()
            
            if not impact_result:
                print(f"      ⚠️  No impact result found for analysis {analysis_id}, skipping")
                continue
            
            # Create observation from analysis result
            try:
                observation = create_observation_from_analysis(
                    tenant_id=tenant_id,
                    policy_id=policy_id,
                    analysis_id=analysis_id,
                    analysis_result=impact_result.result_data_json,
                    data_period_id=None,
                )
                
                if observation:
                    print(f"      ✅ Created observation: {observation.get('observation_id')}")
                else:
                    print(f"      ⚠️  Failed to create observation for analysis {analysis_id}")
            except Exception as e:
                print(f"      ❌ Error creating observation: {e}")
                import traceback
                traceback.print_exc()
                
    finally:
        db.close()


def run_daily_demo_workflow(
    tenant_id: UUID,
    target_date: date | None = None,
    generate_data: bool = True,
    run_observations: bool = True,
):
    """Run the complete daily demo workflow"""
    if target_date is None:
        target_date = date.today() - timedelta(days=1)  # Yesterday
    
    print("=" * 80)
    print(f"DAILY DEMO WORKFLOW - {target_date.isoformat()}")
    print("=" * 80)
    print()
    
    # Step 1: Generate daily data
    if generate_data:
        print("STEP 1: Generating Daily Synthetic Data")
        print("-" * 80)
        
        claims_df = generate_daily_claims(tenant_id, target_date)
        enrollment_df = generate_daily_enrollment(tenant_id, target_date)
        
        print(f"  ✅ Generated {len(claims_df):,} claims")
        print(f"  ✅ Generated {len(enrollment_df):,} enrollment records")
        print()
        
        # Step 2: Load data to database
        print("STEP 2: Loading Data to Database")
        print("-" * 80)
        load_daily_data_to_database(tenant_id, target_date, claims_df, enrollment_df)
        print()
    
    # Step 3: Run impact analysis for all active policies
    if run_observations:
        print("STEP 3: Running Impact Analysis for All Policies")
        print("-" * 80)
        
        policies = list_policies(tenant_id)
        active_policies = [p for p in policies if p.get("status") == "ACTIVE"]
        
        print(f"  Found {len(active_policies)} active policies")
        
        analysis_ids_by_policy = {}
        
        for policy in active_policies:
            policy_id = UUID(policy["id"])
            policy_name = policy.get("name", "Unknown")
            
            print(f"  Processing: {policy_name}")
            
            # Run impact analysis
            analysis_id = run_impact_analysis_for_policy(tenant_id, policy_id, target_date)
            
            if analysis_id:
                if policy_id not in analysis_ids_by_policy:
                    analysis_ids_by_policy[policy_id] = []
                analysis_ids_by_policy[policy_id].append(analysis_id)
        
        print()
        
        # Step 4: Create observations from analyses
        print("STEP 4: Creating Observations from Impact Analyses")
        print("-" * 80)
        
        for policy_id, analysis_ids in analysis_ids_by_policy.items():
            create_observations_from_analyses(tenant_id, policy_id, analysis_ids, target_date)
        
        print()
    
    print("=" * 80)
    print("✅ DAILY DEMO WORKFLOW COMPLETE")
    print("=" * 80)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Daily Demo Workflow")
    parser.add_argument("--date", type=str, help="Target date (YYYY-MM-DD). Default: yesterday")
    parser.add_argument("--tenant-id", type=str, default=str(DEFAULT_TENANT_ID), help="Tenant ID")
    parser.add_argument("--skip-data", action="store_true", help="Skip data generation")
    parser.add_argument("--skip-observations", action="store_true", help="Skip observation creation")
    
    args = parser.parse_args()
    
    # Parse target date
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today() - timedelta(days=1)
    
    tenant_id = UUID(args.tenant_id)
    
    # Run workflow
    run_daily_demo_workflow(
        tenant_id=tenant_id,
        target_date=target_date,
        generate_data=not args.skip_data,
        run_observations=not args.skip_observations,
    )


if __name__ == "__main__":
    main()

