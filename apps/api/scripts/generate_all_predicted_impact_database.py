#!/usr/bin/env python3
"""
Generate predicted impact for all policies using database as source
and storing results in database
"""
import sys
from pathlib import Path
from uuid import UUID

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import SessionLocal
from uepi_api.models.policy import Policy
from uepi_api.models.analysis import BaselineAnalysisResult
from uepi_api.storage_policies import get_policy, update_policy
from uepi_api.storage_auth import DEFAULT_TENANT_ID
# Import directly from the module
import importlib.util
policy_predicted_impact_path = Path(__file__).parent.parent / "src" / "uepi_api" / "routers" / "policy_predicted_impact.py"
spec = importlib.util.spec_from_file_location("policy_predicted_impact", policy_predicted_impact_path)
policy_predicted_impact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy_predicted_impact)

generate_predicted_impact_for_policy = policy_predicted_impact.generate_predicted_impact_for_policy
store_predicted_impact_in_metadata = policy_predicted_impact.store_predicted_impact_in_metadata
from sqlalchemy.orm.attributes import flag_modified

def get_baseline_metrics_from_database(tenant_id: UUID):
    """Get baseline metrics from database (latest baseline analysis)"""
    db = SessionLocal()
    try:
        # Get latest baseline analysis result
        baseline_result = db.query(BaselineAnalysisResult).filter(
            BaselineAnalysisResult.tenant_id == tenant_id
        ).order_by(BaselineAnalysisResult.created_at.desc()).first()
        
        if not baseline_result:
            print("  ⚠️  No baseline analysis found in database")
            return None
        
        result_data = baseline_result.result_data_json
        if not result_data:
            return None
        
        # Extract baseline metrics from result
        # The structure depends on how baseline stores metrics
        baseline_metrics = {}
        
        # Try to extract from different possible structures
        if isinstance(result_data, dict):
            # Check for metrics in various locations
            if "baseline_metrics" in result_data:
                baseline_metrics = result_data["baseline_metrics"]
            elif "metrics" in result_data:
                baseline_metrics = result_data["metrics"]
            elif "summary" in result_data and "metrics" in result_data["summary"]:
                baseline_metrics = result_data["summary"]["metrics"]
            else:
                # Use the result data itself as baseline metrics
                baseline_metrics = result_data
        
        if baseline_metrics:
            print(f"  ✅ Loaded baseline metrics from database (analysis: {baseline_result.analysis_id})")
            return baseline_metrics
        else:
            print("  ⚠️  Baseline result found but no metrics extracted")
            return None
            
    except Exception as e:
        print(f"  ⚠️  Error loading baseline from database: {e}")
        return None
    finally:
        db.close()

def generate_predicted_impact_for_all_policies():
    """Generate predicted impact for all policies"""
    print("="*60)
    print("GENERATING PREDICTED IMPACT FOR ALL POLICIES")
    print("="*60)
    print("\nUsing database as source and storing results in database")
    
    # Get baseline metrics from database
    print("\n1. Loading baseline metrics from database...")
    baseline_metrics = get_baseline_metrics_from_database(DEFAULT_TENANT_ID)
    
    # Get all policies
    print("\n2. Loading policies from database...")
    db = SessionLocal()
    try:
        policies = db.query(Policy).filter(
            Policy.tenant_id == DEFAULT_TENANT_ID
        ).all()
        
        print(f"  Found {len(policies)} policies")
        
        if len(policies) == 0:
            print("  ❌ No policies found")
            return 1
        
        # Generate predicted impact for each policy
        print("\n3. Generating predicted impact for each policy...")
        results = {
            "generated": 0,
            "skipped": 0,
            "errors": 0,
            "details": [],
        }
        
        for i, policy in enumerate(policies, 1):
            policy_id = policy.id
            policy_name = policy.name
            
            print(f"\n  [{i}/{len(policies)}] {policy_name} ({policy_id})...")
            
            try:
                # Get policy data
                policy_data = get_policy(policy_id, DEFAULT_TENANT_ID)
                if not policy_data:
                    print(f"    ⚠️  Could not load policy data")
                    results["skipped"] += 1
                    results["details"].append({
                        "policy_id": str(policy_id),
                        "policy_name": policy_name,
                        "status": "skipped",
                        "reason": "Could not load policy data"
                    })
                    continue
                
                # Check if predicted impact already exists
                metadata = policy_data.get("metadata", {})
                existing_predicted_impact = metadata.get("predicted_impact")
                
                if existing_predicted_impact:
                    print(f"    ⏭️  Predicted impact already exists, skipping")
                    results["skipped"] += 1
                    results["details"].append({
                        "policy_id": str(policy_id),
                        "policy_name": policy_name,
                        "status": "skipped",
                        "reason": "Predicted impact already exists"
                    })
                    continue
                
                # Get policy levers from metadata (can be in multiple places)
                policy_levers = (
                    policy_data.get("policy_levers") or
                    metadata.get("policy_levers") or
                    policy_data.get("metadata", {}).get("policy_levers") or
                    []
                )
                
                if not policy_levers:
                    print(f"    ⚠️  No policy levers found, skipping")
                    results["skipped"] += 1
                    results["details"].append({
                        "policy_id": str(policy_id),
                        "policy_name": policy_name,
                        "status": "skipped",
                        "reason": "No policy levers"
                    })
                    continue
                
                # Get policy scope
                policy_scope = (
                    policy_data.get("scope") or
                    metadata.get("scope") or
                    policy_data.get("metadata", {}).get("scope") or
                    {}
                )
                
                # Generate predicted impact
                print(f"    Generating predicted impact...")
                predicted_impact = generate_predicted_impact_for_policy(
                    tenant_id=DEFAULT_TENANT_ID,
                    policy_id=policy_id,
                    policy_levers=policy_levers,
                    policy_scope=policy_scope,
                    baseline_metrics=baseline_metrics,
                )
                
                # Store predicted impact in policy metadata
                updated_metadata = store_predicted_impact_in_metadata(
                    policy_metadata=metadata,
                    predicted_impact=predicted_impact,
                )
                
                # Update policy in database
                policy.policy_metadata_json = updated_metadata
                flag_modified(policy, "policy_metadata_json")
                db.commit()
                
                print(f"    ✅ Generated and stored predicted impact")
                results["generated"] += 1
                results["details"].append({
                    "policy_id": str(policy_id),
                    "policy_name": policy_name,
                    "status": "generated",
                    "predicted_impact": {
                        "utilization_change_pct": predicted_impact.utilization_change_pct,
                        "cost_change_pct": predicted_impact.cost_change_pct,
                        "confidence_score": predicted_impact.confidence_score,
                    }
                })
                
            except Exception as e:
                db.rollback()
                print(f"    ❌ Error: {e}")
                import traceback
                traceback.print_exc()
                results["errors"] += 1
                results["details"].append({
                    "policy_id": str(policy_id),
                    "policy_name": policy_name,
                    "status": "error",
                    "error": str(e)
                })
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"  Generated: {results['generated']}")
        print(f"  Skipped: {results['skipped']}")
        print(f"  Errors: {results['errors']}")
        print(f"  Total: {len(policies)}")
        
        # Show details for generated policies
        if results["generated"] > 0:
            print("\n  Generated predicted impact for:")
            for detail in results["details"]:
                if detail["status"] == "generated":
                    impact = detail.get("predicted_impact", {})
                    print(f"    - {detail['policy_name']}")
                    print(f"      Utilization: {impact.get('utilization_change_pct', 0):.1f}%")
                    print(f"      Cost: {impact.get('cost_change_pct', 0):.1f}%")
                    print(f"      Confidence: {impact.get('confidence_score', 0):.1f}%")
        
        # Verify storage in database
        print("\n4. Verifying predicted impact in database...")
        db.refresh(policy)  # Refresh to get latest
        policies_with_impact = 0
        for p in policies:
            policy_data = get_policy(p.id, DEFAULT_TENANT_ID)
            if policy_data and policy_data.get("metadata", {}).get("predicted_impact"):
                policies_with_impact += 1
        
        print(f"  ✅ {policies_with_impact} policies have predicted impact stored in database")
        
        return 0 if results["errors"] == 0 else 1
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()

def main():
    return generate_predicted_impact_for_all_policies()

if __name__ == "__main__":
    sys.exit(main())

