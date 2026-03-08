"""
Data Quality API endpoints for validation and quality checks
"""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from pathlib import Path
import json
import asyncio
import subprocess
import sys
from datetime import datetime

from uepi_api.auth import CurrentUser, get_demo_current_user

router = APIRouter()

# Store validation status
_validation_status = {}


class DataQualityReport(BaseModel):
    """Data quality report response with business-friendly trust indicators"""
    timestamp: str
    overall_score: float
    trust_score: Optional[float] = None
    trust_level: Optional[str] = None
    trust_recommendation: Optional[str] = None
    completeness_score: Optional[float] = None
    validity_score: Optional[float] = None
    uniqueness_score: Optional[float] = None
    integrity_score: Optional[float] = None
    consistency_score: Optional[float] = None
    datasets: dict
    issues: list
    comparisons: dict
    executive_summary: Optional[str] = None
    key_concerns: Optional[list] = None


@router.get("/data-quality/report", response_model=DataQualityReport)
async def get_data_quality_report(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get data quality report for tenant (with business-friendly trust indicators)"""
    from uepi_api.services.data_quality_service import EnterpriseDataQualityService
    from uepi_api.storage_file import BASE_PATH
    
    # Try to get latest report from database first
    service = EnterpriseDataQualityService(tenant_id=current_user.tenant_id)
    latest_report = service.get_latest_report()
    
    if latest_report:
        # Return database-stored report with trust indicators
        # Ensure datasets_summary is a dict (not JSON string)
        datasets_summary = latest_report.datasets_summary
        if isinstance(datasets_summary, str):
            import json
            datasets_summary = json.loads(datasets_summary)
        elif datasets_summary is None:
            # Fallback to report_json if datasets_summary is empty
            datasets_summary = latest_report.report_json.get("datasets", {})
        
        # Ensure issues_summary is a list (not JSON string)
        issues_summary = latest_report.issues_summary
        if isinstance(issues_summary, str):
            import json
            issues_summary = json.loads(issues_summary)
        elif issues_summary is None:
            issues_summary = latest_report.report_json.get("issues", [])
        
        report_dict = {
            "timestamp": latest_report.validation_completed_at.isoformat() if latest_report.validation_completed_at else latest_report.created_at.isoformat(),
            "overall_score": latest_report.overall_quality_score,
            "trust_score": latest_report.trust_score,
            "trust_level": latest_report.trust_level,
            "trust_recommendation": latest_report.trust_recommendation,
            "completeness_score": latest_report.completeness_score,
            "validity_score": latest_report.validity_score,
            "uniqueness_score": latest_report.uniqueness_score,
            "integrity_score": latest_report.integrity_score,
            "consistency_score": latest_report.consistency_score,
            "datasets": datasets_summary,
            "issues": issues_summary,
            "comparisons": latest_report.report_json.get("comparisons", {}) if isinstance(latest_report.report_json, dict) else {},
            "executive_summary": latest_report.executive_summary,
            "key_concerns": latest_report.key_concerns or [],
        }
        return DataQualityReport(**report_dict)
    
    # Fallback to file-based report
    report_file = BASE_PATH / "target_data_model" / str(current_user.tenant_id) / "data_quality_report.json"
    
    if not report_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Data quality report not found. Please run data quality validation first."
        )
    
    try:
        with open(report_file, 'r') as f:
            report_data = json.load(f)
        
        # Enhance with trust indicators if not present
        if "trust_score" not in report_data:
            trust_info = service.calculate_trust_score(
                completeness_score=report_data.get("completeness_score", 0),
                validity_score=report_data.get("validity_score", 0),
                uniqueness_score=report_data.get("uniqueness_score", 100),
                integrity_score=report_data.get("integrity_score", 100),
                consistency_score=report_data.get("consistency_score", 85),
                critical_issues=report_data.get("critical_issues", 0),
                high_issues=report_data.get("high_issues", 0),
                total_rows=report_data.get("total_rows", 0),
            )
            report_data.update(trust_info)
        
        return DataQualityReport(**report_data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading data quality report: {str(e)}"
        )


async def _run_validation_script(tenant_id: str):
    """Run validation script in background"""
    # Try multiple possible script locations
    possible_paths = [
        Path(__file__).parent.parent.parent.parent.parent.parent / "scripts" / "comprehensive_data_quality_check.py",
        Path(__file__).parent.parent.parent.parent.parent / "scripts" / "comprehensive_data_quality_check.py",
    ]
    
    script_path = None
    for path in possible_paths:
        if path.exists():
            script_path = path
            break
    
    if not script_path:
        _validation_status[tenant_id] = {
            "status": "error",
            "error": f"Validation script not found. Tried: {[str(p) for p in possible_paths]}",
            "started_at": None,
            "completed_at": None,
        }
        return
    
    _validation_status[tenant_id] = {
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "error": None,
    }
    
    try:
        # Run script asynchronously
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=36000  # 10 hour timeout (no user interaction for 1 hour)
        )
        
        if process.returncode != 0:
            _validation_status[tenant_id] = {
                "status": "error",
                "error": stderr.decode()[:500] if stderr else "Unknown error",
                "started_at": _validation_status[tenant_id].get("started_at"),
                "completed_at": datetime.utcnow().isoformat(),
            }
            return
        
        # Check if report was generated
        from uepi_api.storage_file import BASE_PATH
        report_file = BASE_PATH / "target_data_model" / tenant_id / "data_quality_report.json"
        
        if not report_file.exists():
            _validation_status[tenant_id] = {
                "status": "error",
                "error": "Validation completed but report not generated",
                "started_at": _validation_status[tenant_id].get("started_at"),
                "completed_at": datetime.utcnow().isoformat(),
            }
            return
        
        _validation_status[tenant_id] = {
            "status": "completed",
            "started_at": _validation_status[tenant_id].get("started_at"),
            "completed_at": datetime.utcnow().isoformat(),
            "error": None,
        }
    
    except asyncio.TimeoutError:
        _validation_status[tenant_id] = {
            "status": "error",
            "error": "Validation timed out after 10 minutes",
            "started_at": _validation_status[tenant_id].get("started_at"),
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        _validation_status[tenant_id] = {
            "status": "error",
            "error": str(e),
            "started_at": _validation_status[tenant_id].get("started_at"),
            "completed_at": datetime.utcnow().isoformat(),
        }


@router.post("/data-quality/validate")
async def run_data_quality_validation(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Run data quality validation (async, returns immediately)"""
    tenant_id = str(current_user.tenant_id)
    
    # Check if already running
    if tenant_id in _validation_status:
        current_status = _validation_status[tenant_id]
        if current_status.get("status") == "running":
            return {
                "status": "running",
                "message": "Validation is already running. Use /data-quality/validate/status to check progress.",
                "started_at": current_status.get("started_at"),
            }
    
    # Start validation in background
    script_path = Path(__file__).parent.parent.parent.parent.parent.parent / "scripts" / "comprehensive_data_quality_check.py"
    
    if not script_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Validation script not found: {script_path}"
        )
    
    # Start background task
    asyncio.create_task(_run_validation_script(tenant_id))
    
    return {
        "status": "started",
        "message": "Data quality validation started. Use /data-quality/validate/status to check progress.",
        "started_at": datetime.utcnow().isoformat(),
    }


@router.get("/data-quality/validate/status")
async def get_validation_status(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get current validation status"""
    tenant_id = str(current_user.tenant_id)
    
    if tenant_id not in _validation_status:
        return {
            "status": "not_started",
            "message": "Validation has not been started yet.",
        }
    
    status_info = _validation_status[tenant_id].copy()
    
    # If completed, try to load the report
    if status_info.get("status") == "completed":
        from uepi_api.storage_file import BASE_PATH
        report_file = BASE_PATH / "target_data_model" / tenant_id / "data_quality_report.json"
        
        if report_file.exists():
            try:
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                status_info["report"] = report_data
            except Exception as e:
                status_info["error"] = f"Failed to load report: {str(e)}"
    
    return status_info


@router.get("/data-quality/summary")
async def get_data_quality_summary(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get data quality summary with business-friendly trust indicators"""
    from uepi_api.services.data_quality_service import EnterpriseDataQualityService
    from uepi_api.storage_file import BASE_PATH
    
    # Try to get latest report from database first
    service = EnterpriseDataQualityService(tenant_id=current_user.tenant_id)
    latest_report = service.get_latest_report()
    
    if latest_report:
        # Return database-stored report
        return {
            "overall_score": latest_report.overall_quality_score,
            "trust_score": latest_report.trust_score,
            "trust_level": latest_report.trust_level,
            "trust_recommendation": latest_report.trust_recommendation,
            "completeness_score": latest_report.completeness_score,
            "validity_score": latest_report.validity_score,
            "uniqueness_score": latest_report.uniqueness_score,
            "integrity_score": latest_report.integrity_score,
            "consistency_score": latest_report.consistency_score,
            "total_issues": latest_report.total_issues,
            "critical_issues": latest_report.critical_issues,
            "high_issues": latest_report.high_issues,
            "medium_issues": latest_report.medium_issues,
            "low_issues": latest_report.low_issues,
            "key_concerns": latest_report.key_concerns or [],
            "executive_summary": latest_report.executive_summary,
            "datasets_summary": latest_report.datasets_summary or {},
            "last_validated_at": latest_report.validation_completed_at.isoformat() if latest_report.validation_completed_at else None,
            "overall_status": latest_report.trust_level.lower(),
        }
    
    # Fallback to file-based report
    tenant_dir = BASE_PATH / "target_data_model" / str(current_user.tenant_id)
    
    summary = {
        "datasets": {},
        "overall_status": "unknown",
        "trust_level": "UNKNOWN",
    }
    
    # Check file existence and sizes
    datasets = {
        "CLAIMS_LINES": tenant_dir / "CLAIMS_LINES" / "claims_lines.csv",
        "ENROLLMENT": tenant_dir / "ENROLLMENT" / "enrollment.csv",
        "PROVIDERS": tenant_dir / "PROVIDERS" / "providers.csv",
    }
    
    for dataset_name, file_path in datasets.items():
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            summary["datasets"][dataset_name] = {
                "exists": True,
                "size_mb": round(size_mb, 2),
            }
        else:
            summary["datasets"][dataset_name] = {
                "exists": False,
                "size_mb": 0,
            }
    
    # Try to load report for scores
    report_file = tenant_dir / "data_quality_report.json"
    if report_file.exists():
        try:
            with open(report_file, 'r') as f:
                report = json.load(f)
            summary["overall_score"] = report.get("overall_score", 0)
            summary["overall_status"] = (
                "excellent" if summary.get("overall_score", 0) >= 90 else
                "good" if summary.get("overall_score", 0) >= 80 else
                "fair" if summary.get("overall_score", 0) >= 60 else
                "poor"
            )
            summary["issues_count"] = len(report.get("issues", []))
        except:
            pass
    
    return summary
