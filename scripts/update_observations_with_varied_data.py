#!/usr/bin/env python3
"""Update existing observations with varied data based on policy_id"""

import sys
import json
import hashlib
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
db_url = "postgresql://postgres:postgres@localhost:5432/uepi_db"
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

def update_observations():
    """Update observations with varied data"""
    print("="*80)
    print("UPDATING OBSERVATIONS WITH VARIED DATA")
    print("="*80)
    print()
    
    db = SessionLocal()
    try:
        # Get all observations
        result = db.execute(text("""
            SELECT observation_id, policy_id, metrics_json, comparisons_json
            FROM observations
            ORDER BY computed_at DESC
        """))
        
        observations = result.fetchall()
        print(f"Found {len(observations)} observations to update")
        print()
        
        updated_count = 0
        for obs_id, policy_id, metrics_json, comparisons_json in observations:
            if not policy_id:
                continue
            
            # Generate varied values based on policy_id hash
            policy_hash = int(hashlib.md5(str(policy_id).encode()).hexdigest()[:8], 16)
            
            base_util = 100.0 + (policy_hash % 50)  # 100-150
            base_cost = 30.0 + (policy_hash % 30)    # 30-60
            reduction_pct = 0.10 + ((policy_hash % 20) / 100.0)  # 10-30% reduction
            predicted_util = base_util * (1 - reduction_pct * 0.8)  # Predicted is 80% of actual reduction
            predicted_cost = base_cost * (1 - reduction_pct * 0.8)
            observed_util = base_util * (1 - reduction_pct)
            observed_cost = base_cost * (1 - reduction_pct)
            
            # Update metrics
            metrics = metrics_json if isinstance(metrics_json, dict) else json.loads(metrics_json) if metrics_json else {}
            metrics['utilization_per_1k'] = round(observed_util, 1)
            metrics['cost_per_member'] = round(observed_cost, 2)
            metrics['cost_pmpm'] = round(observed_cost, 2)
            metrics['member_months'] = 2000
            
            # Update comparisons
            comparisons = comparisons_json if isinstance(comparisons_json, dict) else json.loads(comparisons_json) if comparisons_json else {}
            
            # Update vs_baseline
            vs_baseline = comparisons.get('vs_baseline', {})
            vs_baseline['baseline_utilization_per_1k'] = round(base_util, 1)
            vs_baseline['baseline_utilization'] = round(base_util, 1)
            vs_baseline['observed_utilization_per_1k'] = round(observed_util, 1)
            vs_baseline['observed_utilization'] = round(observed_util, 1)
            vs_baseline['baseline_cost_per_member'] = round(base_cost, 2)
            vs_baseline['baseline_cost_pmpm'] = round(base_cost, 2)
            vs_baseline['observed_cost_pmpm'] = round(observed_cost, 2)
            
            util_change = observed_util - base_util
            util_change_pct = (util_change / base_util) * 100 if base_util > 0 else 0
            cost_change = observed_cost - base_cost
            cost_change_pct = (cost_change / base_cost) * 100 if base_cost > 0 else 0
            
            vs_baseline['change_from_baseline'] = round(util_change, 1)
            vs_baseline['change_from_baseline_pct'] = round(util_change_pct, 1)
            vs_baseline['utilization_change'] = round(util_change, 1)
            vs_baseline['utilization_change_pct'] = round(util_change_pct, 1)
            vs_baseline['cost_change'] = round(cost_change, 2)
            vs_baseline['cost_change_pct'] = round(cost_change_pct, 1)
            
            # Update vs_predicted
            vs_predicted = comparisons.get('vs_predicted', {})
            vs_predicted['predicted_utilization_per_1k'] = round(predicted_util, 1)
            vs_predicted['predicted_utilization'] = round(predicted_util, 1)
            vs_predicted['observed_utilization_per_1k'] = round(observed_util, 1)
            vs_predicted['observed_utilization'] = round(observed_util, 1)
            vs_predicted['predicted_cost_pmpm'] = round(predicted_cost, 2)
            vs_predicted['predicted_cost_per_member'] = round(predicted_cost, 2)
            vs_predicted['observed_cost_pmpm'] = round(observed_cost, 2)
            vs_predicted['observed_cost_per_member'] = round(observed_cost, 2)
            
            # Compute prediction errors
            util_error = abs(observed_util - predicted_util)
            util_error_pct = (util_error / predicted_util) * 100 if predicted_util > 0 else 0
            cost_error = abs(observed_cost - predicted_cost)
            cost_error_pct = (cost_error / predicted_cost) * 100 if predicted_cost > 0 else 0
            
            vs_predicted['prediction_error'] = round(util_error, 1)
            vs_predicted['prediction_error_pct'] = round(util_error_pct, 1)
            vs_predicted['utilization_prediction_error'] = round(util_error, 1)
            vs_predicted['utilization_prediction_error_pct'] = round(util_error_pct, 1)
            vs_predicted['cost_prediction_error'] = round(cost_error, 2)
            vs_predicted['cost_prediction_error_pct'] = round(cost_error_pct, 1)
            
            # Compute predicted changes
            predicted_util_change = observed_util - predicted_util
            predicted_util_change_pct = (predicted_util_change / predicted_util) * 100 if predicted_util > 0 else 0
            predicted_cost_change = observed_cost - predicted_cost
            predicted_cost_change_pct = (predicted_cost_change / predicted_cost) * 100 if predicted_cost > 0 else 0
            
            vs_predicted['predicted_utilization_change'] = round(predicted_util_change, 1)
            vs_predicted['predicted_utilization_change_pct'] = round(predicted_util_change_pct, 1)
            vs_predicted['predicted_change_pmpm'] = round(predicted_cost_change, 2)
            vs_predicted['predicted_cost_change_pmpm'] = round(predicted_cost_change, 2)
            vs_predicted['predicted_change_pct'] = round(predicted_cost_change_pct, 1)
            vs_predicted['predicted_cost_change_pct'] = round(predicted_cost_change_pct, 1)
            
            # Prediction accuracy
            accuracy = 100.0 - (util_error_pct + cost_error_pct) / 2.0
            vs_predicted['prediction_accuracy_pct'] = round(max(0, accuracy), 1)
            
            comparisons['vs_baseline'] = vs_baseline
            comparisons['vs_predicted'] = vs_predicted
            
            # Update in database
            db.execute(text("""
                UPDATE observations
                SET metrics_json = :metrics,
                    comparisons_json = :comparisons
                WHERE observation_id = :obs_id
            """), {
                "metrics": json.dumps(metrics),
                "comparisons": json.dumps(comparisons),
                "obs_id": obs_id
            })
            
            updated_count += 1
            if updated_count <= 3:
                print(f"Updated observation {obs_id[:8]}...")
                print(f"  Policy: {str(policy_id)[:8]}")
                print(f"  Baseline util: {base_util:.1f} -> Observed: {observed_util:.1f} -> Predicted: {predicted_util:.1f}")
                print(f"  Baseline cost: ${base_cost:.2f} -> Observed: ${observed_cost:.2f} -> Predicted: ${predicted_cost:.2f}")
                print()
        
        db.commit()
        
        print("="*80)
        print(f"✅ Updated {updated_count} observations with varied data")
        print("="*80)
        print()
        print("Each policy now has unique observation values based on its policy_id.")
        print("Refresh your browser to see the updated data!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    update_observations()
