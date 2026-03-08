#!/usr/bin/env python3
"""Check observation data structure and metrics"""

import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
db_url = "postgresql://postgres:postgres@localhost:5432/uepi_db"
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

def check_observation_data():
    """Check observation data structure"""
    print("="*80)
    print("CHECKING OBSERVATION DATA")
    print("="*80)
    print()
    
    db = SessionLocal()
    try:
        # Get a sample observation
        result = db.execute(text("""
            SELECT 
                id,
                policy_id,
                metrics_json,
                comparisons_json,
                behavioral_explanation_json,
                computed_at
            FROM observations
            ORDER BY computed_at DESC
            LIMIT 5
        """))
        
        observations = result.fetchall()
        print(f"Found {len(observations)} recent observations")
        print()
        
        for i, obs in enumerate(observations, 1):
            obs_id, policy_id, metrics_json, comparisons_json, behavioral_json, computed_at = obs
            
            print(f"Observation {i}:")
            print(f"  ID: {obs_id}")
            print(f"  Policy ID: {policy_id}")
            print(f"  Computed At: {computed_at}")
            print()
            
            # Parse JSON fields (may already be dicts if JSONB, or strings)
            if isinstance(metrics_json, str):
                metrics = json.loads(metrics_json) if metrics_json else {}
            else:
                metrics = metrics_json if metrics_json else {}
            
            if isinstance(comparisons_json, str):
                comparisons = json.loads(comparisons_json) if comparisons_json else {}
            else:
                comparisons = comparisons_json if comparisons_json else {}
            
            if isinstance(behavioral_json, str):
                behavioral = json.loads(behavioral_json) if behavioral_json else {}
            else:
                behavioral = behavioral_json if behavioral_json else {}
            
            print("  Metrics JSON:")
            print(f"    Keys: {list(metrics.keys())}")
            for key, value in metrics.items():
                if isinstance(value, (int, float, str)):
                    print(f"    {key}: {value}")
                else:
                    print(f"    {key}: {type(value).__name__}")
            
            print()
            print("  Comparisons JSON:")
            if comparisons:
                print(f"    Keys: {list(comparisons.keys())}")
                for key, value in comparisons.items():
                    if isinstance(value, dict):
                        print(f"    {key}:")
                        for subkey, subvalue in value.items():
                            if isinstance(subvalue, (int, float, str)):
                                print(f"      {subkey}: {subvalue}")
                            else:
                                print(f"      {subkey}: {type(subvalue).__name__}")
                    elif isinstance(value, (int, float, str)):
                        print(f"    {key}: {value}")
                    else:
                        print(f"    {key}: {type(value).__name__}")
            else:
                print("    (empty or null)")
            
            print()
            print("  Behavioral Explanation JSON:")
            if behavioral:
                print(f"    Keys: {list(behavioral.keys())}")
                print(f"    Summary: {behavioral.get('summary', 'N/A')}")
            else:
                print("    (empty or null)")
            
            print()
            print("-"*80)
            print()
        
        # Check for observations with missing comparison data
        print("Checking for observations with missing comparison data...")
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN comparisons_json IS NULL OR comparisons_json::text = '{}' THEN 1 END) as missing_comparisons,
                COUNT(CASE WHEN metrics_json IS NULL OR metrics_json::text = '{}' THEN 1 END) as missing_metrics
            FROM observations
        """))
        
        stats = result.fetchone()
        total, missing_comparisons, missing_metrics = stats
        print(f"  Total observations: {total}")
        print(f"  Missing comparisons: {missing_comparisons}")
        print(f"  Missing metrics: {missing_metrics}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_observation_data()
