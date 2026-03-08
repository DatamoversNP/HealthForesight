"""Lineage endpoints - File storage implementation with comprehensive tracking"""
from typing import Annotated, List, Dict, Any
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_ingestions import list_ingestions
from uepi_api.storage_analyses import list_analyses
from uepi_api.storage_lineage import get_full_lineage, compute_coverage_from_data_files

router = APIRouter()


@router.get("/lineage/coverage")
async def get_data_coverage(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get data coverage heatmap from ingestions and actual data files"""
    try:
        # Load all ingestions
        ingestions = list_ingestions(current_user.tenant_id)
        
        # Build coverage map from ingestion metadata
        coverage: Dict[str, Dict[str, Dict[str, Dict[str, int]]]] = {}
        
        for ingestion in ingestions:
            if ingestion.get("status") != "COMPLETED":
                continue
            
            metadata = ingestion.get("metadata", {})
            ingestion_coverage = metadata.get("coverage", {})
            
            # Merge coverage data
            for year, year_data in ingestion_coverage.items():
                if year not in coverage:
                    coverage[year] = {}
                
                if isinstance(year_data, dict):
                    for month, month_data in year_data.items():
                        if month not in coverage[year]:
                            coverage[year][month] = {}
                        
                        if isinstance(month_data, dict):
                            for lob, lob_data in month_data.items():
                                if lob not in coverage[year][month]:
                                    coverage[year][month][lob] = {}
                                
                                if isinstance(lob_data, dict):
                                    for market, count in lob_data.items():
                                        if isinstance(count, (int, float)):
                                            coverage[year][month][lob][market] = coverage[year][month][lob].get(market, 0) + int(count)
        
        # If coverage is empty, try to compute from actual data files
        if not coverage:
            coverage = compute_coverage_from_data_files(current_user.tenant_id)
        
        # Get the most recent ingestion timestamp for snapshot
        latest_ingestion = None
        if ingestions:
            completed = [ing for ing in ingestions if ing.get("status") == "COMPLETED"]
            if completed:
                latest_ingestion = max(
                    completed,
                    key=lambda x: x.get("completed_at", "") or x.get("created_at", "")
                )
        
        return {
            "snapshot_id": latest_ingestion.get("id") if latest_ingestion else None,
            "created_at": latest_ingestion.get("completed_at") or latest_ingestion.get("created_at") if latest_ingestion else datetime.utcnow().isoformat(),
            "coverage": coverage,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Try fallback: compute from files
        try:
            coverage = compute_coverage_from_data_files(current_user.tenant_id)
            return {
                "snapshot_id": None,
                "created_at": datetime.utcnow().isoformat(),
                "coverage": coverage,
            }
        except:
            return {
                "snapshot_id": None,
                "created_at": datetime.utcnow().isoformat(),
                "coverage": {},
            }


@router.get("/lineage/ingestions")
async def list_recent_ingestions(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    limit: int = Query(50, ge=1, le=200),
):
    """List recent ingestions from file storage"""
    try:
        ingestions = list_ingestions(current_user.tenant_id)
        
        # Also check pipeline runs if no ingestions found
        if not ingestions:
            from uepi_api.storage_pipelines import list_pipelines
            from uepi_api.storage_pipeline_runs import list_pipeline_runs
            
            pipelines = list_pipelines(current_user.tenant_id)
            for pipeline in pipelines:
                try:
                    pipeline_id = pipeline.get("pipeline_id")
                    if isinstance(pipeline_id, str):
                        pipeline_id = UUID(pipeline_id)
                    runs = list_pipeline_runs(current_user.tenant_id, pipeline_id)
                    for run in runs:
                        if run.get("status") == "COMPLETED":
                            # Convert pipeline run to ingestion format
                            ingestions.append({
                                "id": run.get("run_id"),
                                "tenant_id": str(current_user.tenant_id),
                                "ingestion_type": pipeline.get("target_dataset_type", "CLAIMS"),
                                "status": "COMPLETED",
                                "manifest_uri": run.get("output_uri", ""),
                                "started_at": run.get("started_at"),
                                "completed_at": run.get("completed_at"),
                                "created_at": run.get("started_at") or run.get("created_at"),
                                "metadata": run.get("metadata", {}),
                            })
                except Exception as e:
                    print(f"Error loading pipeline runs: {e}")
                    continue
        
        # Sort by created_at descending (most recent first)
        ingestions_sorted = sorted(
            ingestions,
            key=lambda x: x.get("created_at", "") or x.get("started_at", ""),
            reverse=True
        )
        
        # Format response to match expected interface
        result = []
        for ingestion in ingestions_sorted[:limit]:
            result.append({
                "id": ingestion.get("id"),
                "ingestion_type": ingestion.get("ingestion_type", "UNKNOWN"),
                "status": ingestion.get("status", "PENDING"),
                "created_at": ingestion.get("created_at") or ingestion.get("started_at"),
                "started_at": ingestion.get("started_at"),
                "completed_at": ingestion.get("completed_at"),
            })
        
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return []


@router.get("/lineage/analyses")
async def list_analysis_runs(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """List analysis runs - Legacy endpoint"""
    return await list_analysis_runs_v2(current_user)


@router.get("/lineage/analysis-runs")
async def list_analysis_runs_v2(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    limit: int = Query(50, ge=1, le=200),
):
    """List analysis runs from file storage"""
    try:
        # Get all analyses
        all_analyses = list_analyses(current_user.tenant_id)
        
        # Convert analyses to analysis runs format
        analysis_runs = []
        for analysis in all_analyses:
            # Get result indices to determine if analysis completed
            from uepi_api.storage_analyses import list_result_indices
            result_indices = list_result_indices(UUID(analysis.get("id")), current_user.tenant_id)
            
            analysis_runs.append({
                "id": analysis.get("id"),
                "analysis_id": analysis.get("id"),
                "status": analysis.get("status", "PENDING"),
                "analysis_type": analysis.get("analysis_type", "UNKNOWN"),
                "model_version": "1.0",  # Default version
                "started_at": analysis.get("created_at"),  # Use created_at as started_at
                "ended_at": analysis.get("updated_at") if analysis.get("status") in ["COMPLETED", "FAILED"] else None,
                "has_results": len(result_indices) > 0,
            })
        
        # Sort by started_at descending
        analysis_runs.sort(
            key=lambda x: x.get("started_at", ""),
            reverse=True
        )
        
        return analysis_runs[:limit]
    except Exception as e:
        import traceback
        traceback.print_exc()
        return []


@router.get("/lineage/full")
async def get_full_lineage_tracking(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get complete lineage from source to dashboards"""
    try:
        return get_full_lineage(current_user.tenant_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load lineage: {str(e)}")
