#!/usr/bin/env python3
"""Mark pending analyses as complete with mock results, then create observations"""
import requests
import json
from uuid import UUID
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer dev-token-123", "Content-Type": "application/json"}

def get_pending_analyses():
    """Get all pending analyses"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analyses",
            headers=HEADERS,
            params={"analysis_type": "IMPACT"},
            timeout=30
        )
        response.raise_for_status()
        analyses = response.json()
        return [a for a in analyses if a.get("status") == "PENDING"]
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def create_mock_result():
    """Create a mock analysis result"""
    return {
        "impact_summary": {
            "observed_effect_size": -0.15,
            "observed_percent_change": -15.0,
            "confidence_interval_lower": -0.20,
            "confidence_interval_upper": -0.10,
            "p_value": 0.01,
            "statistical_significance": "SIGNIFICANT",
        },
        "pre_period": {
            "start": "2024-06-01",
            "end": "2024-11-30",
            "utilization_per_1k": 125.5,
            "cost_per_member": 45.2,
            "member_months": 12000,
        },
        "post_period": {
            "start": "2024-12-01",
            "end": "2024-12-31",
            "utilization_per_1k": 106.7,
            "cost_per_member": 38.4,
            "member_months": 2000,
        },
        "method_checks": {
            "pre_trends_parallel": True,
            "control_balance": True,
            "seasonality_risk": "LOW",
            "data_sufficiency": "SUFFICIENT",
        },
        "trust_panel": {
            "confidence_score": 0.85,
            "data_sufficiency": "SUFFICIENT",
            "method_quality": "HIGH",
        },
        "comparisons": {
            "vs_baseline": {
                "baseline_utilization_per_1k": 130.0,
                "baseline_cost_per_member": 48.0,
                "change_from_baseline_pct": -18.0,
            },
            "vs_predicted": {
                "predicted_utilization_per_1k": 110.0,
                "predicted_cost_per_member": 40.0,
                "prediction_accuracy_pct": 85.0,
                "within_predicted_range": True,
            }
        }
    }

def complete_analysis_via_db(analysis_id, policy_id, tenant_id):
    """Mark analysis as complete and create result via direct database update"""
    # This needs to be done via a script that can access the database
    # For now, let's create an API endpoint or use a Python script with DB access
    print(f"   ⚠️  Need to update database directly - creating helper script...")
    return False

def main():
    print("\n" + "="*60)
    print("Mark Analyses Complete & Create Observations")
    print("="*60)
    print("\n⚠️  This requires database access to update analysis status.")
    print("   Creating a database script instead...\n")
    
    # Create a Python script that can be run to update the database
    script_content = '''#!/usr/bin/env python3
"""Update pending analyses to COMPLETED with mock results"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))

from uepi_api.database import SessionLocal
from uepi_api.models.analysis import Analysis, AnalysisStatus, ImpactAnalysisResult
from uuid import UUID
from datetime import datetime

TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

def create_mock_result():
    return {
        "impact_summary": {
            "observed_effect_size": -0.15,
            "observed_percent_change": -15.0,
            "confidence_interval_lower": -0.20,
            "confidence_interval_upper": -0.10,
            "p_value": 0.01,
        },
        "pre_period": {"start": "2024-06-01", "end": "2024-11-30", "utilization_per_1k": 125.5, "cost_per_member": 45.2},
        "post_period": {"start": "2024-12-01", "end": "2024-12-31", "utilization_per_1k": 106.7, "cost_per_member": 38.4},
        "method_checks": {"pre_trends_parallel": True, "control_balance": True, "seasonality_risk": "LOW"},
        "trust_panel": {"confidence_score": 0.85, "data_sufficiency": "SUFFICIENT"},
    }

db = SessionLocal()
try:
    # Get pending analyses
    pending = db.query(Analysis).filter(
        Analysis.tenant_id == TENANT_ID,
        Analysis.analysis_type == "IMPACT",
        Analysis.status == AnalysisStatus.PENDING.value
    ).all()
    
    print(f"Found {len(pending)} pending analyses")
    
    completed = 0
    for analysis in pending:
        # Check if result exists
        existing = db.query(ImpactAnalysisResult).filter(
            ImpactAnalysisResult.analysis_id == analysis.id
        ).first()
        
        if not existing:
            # Create mock result
            result = ImpactAnalysisResult(
                tenant_id=TENANT_ID,
                analysis_id=analysis.id,
                policy_id=analysis.policy_id,
                result_data_json=create_mock_result(),
                schema_version="1.0",
            )
            db.add(result)
        
        # Update status
        analysis.status = AnalysisStatus.COMPLETED.value
        completed += 1
        print(f"  ✅ Marked {analysis.id} as COMPLETED")
    
    db.commit()
    print(f"\\n✅ Marked {completed} analyses as COMPLETED")
    print("   Observations will be created automatically by the monitor!")
    
except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
'''
    
    script_path = Path(__file__).parent / "update_analyses_to_complete.py"
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    
    print(f"✅ Created script: {script_path}")
    print(f"\n🚀 Running it now...\n")
    
    import subprocess
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    if result.returncode == 0:
        print("\n✅ Analyses marked as complete!")
        print("   The monitor will now automatically create observations.")
        print("   Check status: cd scripts && ./check_status.sh")

if __name__ == "__main__":
    import sys
    from pathlib import Path
    main()
