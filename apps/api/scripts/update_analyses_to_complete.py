#!/usr/bin/env python3
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
    print(f"\n✅ Marked {completed} analyses as COMPLETED")
    print("   Observations will be created automatically by the monitor!")
    
except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
