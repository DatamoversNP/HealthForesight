#!/usr/bin/env python3
"""
Generate predicted impact for all policies
Fixes any issues and ensures all policies have predicted impact stored in database
"""
import sys
from pathlib import Path
from uuid import UUID
from datetime import datetime

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import SessionLocal
from uepi_api.models.policy import Policy
from uepi_api.routers.policy_predicted_impact import (
    generate_predicted_impact_for_policy,
    store_predicted_impact_in_metadata,
    get_predicted_impact_from_metadata,
)
from uepi_api.storage_auth import DEFAULT_TENANT_ID
from sqlalchemy.orm.attributes import flag_modified


def main():
    print("=" * 80)
    print("Generate Predicted Impact for All Policies")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Get all policies for the tenant
        policies = db.query(Policy).filter(
            Policy.tenant_id == DEFAULT_TENANT_ID,
        ).all()
        
        print(f"\n📋 Found {len(policies)} policies to process\n")
        
        results = {
            "total": len(policies),
            "generated": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "details": [],
        }
        
        for i, policy in enumerate(policies, 1):
            policy_name = policy.name or f"Policy {str(policy.id)[:8]}"
            print(f"[{i}/{len(policies)}] Processing: {policy_name}")
            
            try:
                # Get policy metadata
                policy_metadata = policy.policy_metadata_json if policy.policy_metadata_json else {}
                
                # Check if predicted impact already exists
                existing_predicted_impact = get_predicted_impact_from_metadata(policy_metadata)
                
                # Extract policy levers
                policy_levers = policy_metadata.get("policy_levers", [])
                
                if not policy_levers:
                    # Try to get levers from policy_levers field directly
                    if hasattr(policy, 'policy_levers') and policy.policy_levers:
                        policy_levers = policy.policy_levers if isinstance(policy.policy_levers, list) else [policy.policy_levers]
                    
                    if not policy_levers:
                        print(f"  ⏭️  Skipped: No policy levers defined")
                        results["skipped"] += 1
                        results["details"].append({
                            "policy_id": str(policy.id),
                            "policy_name": policy_name,
                            "status": "skipped",
                            "reason": "No policy levers defined",
                        })
                        continue
                
                policy_scope = policy_metadata.get("scope")
                
                # Generate predicted impact
                print(f"  🔄 Generating predicted impact...")
                predicted_impact = generate_predicted_impact_for_policy(
                    tenant_id=DEFAULT_TENANT_ID,
                    policy_id=policy.id,
                    policy_levers=policy_levers,
                    policy_scope=policy_scope,
                    baseline_metrics=None,  # Can be enhanced to load actual baseline metrics
                )
                
                # Store predicted impact in metadata
                policy_metadata = store_predicted_impact_in_metadata(
                    policy_metadata,
                    predicted_impact,
                )
                
                # Update policy
                policy.policy_metadata_json = policy_metadata
                flag_modified(policy, "policy_metadata_json")
                
                if existing_predicted_impact:
                    print(f"  ✅ Updated predicted impact (confidence: {predicted_impact.metrics.confidence_score:.1f}%)")
                    results["updated"] += 1
                    status = "updated"
                else:
                    print(f"  ✅ Generated predicted impact (confidence: {predicted_impact.metrics.confidence_score:.1f}%)")
                    results["generated"] += 1
                    status = "generated"
                
                results["details"].append({
                    "policy_id": str(policy.id),
                    "policy_name": policy_name,
                    "status": status,
                    "confidence_score": predicted_impact.metrics.confidence_score,
                    "utilization_change_pct": predicted_impact.metrics.utilization_change_pct,
                    "cost_change_pct": predicted_impact.metrics.cost_change_pct,
                })
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
                results["errors"] += 1
                results["details"].append({
                    "policy_id": str(policy.id),
                    "policy_name": policy_name,
                    "status": "error",
                    "error": str(e),
                })
                continue
        
        # Commit all changes
        db.commit()
        
        print("\n" + "=" * 80)
        print("✅ COMPLETE")
        print("=" * 80)
        print(f"Total policies: {results['total']}")
        print(f"Generated: {results['generated']}")
        print(f"Updated: {results['updated']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Errors: {results['errors']}")
        print("=" * 80)
        
        # Show summary of predictions
        if results["generated"] > 0 or results["updated"] > 0:
            print("\n📊 Predicted Impact Summary:")
            successful = [d for d in results["details"] if d.get("status") in ["generated", "updated"]]
            if successful:
                avg_confidence = sum(d.get("confidence_score", 0) for d in successful) / len(successful)
                print(f"  Average Confidence Score: {avg_confidence:.1f}%")
                print(f"  Policies with predictions: {len(successful)}")
        
        return 0 if results["errors"] == 0 else 1
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

