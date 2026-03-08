"""Data generation endpoints - Generate claims data for demonstration"""
from typing import Annotated, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.database import get_db
from uepi_api.services.data_generation_service import generate_claims_data_for_date

router = APIRouter()


class DataGenerationRequest(BaseModel):
    """Data generation request model"""
    target_date: Optional[str] = None  # YYYY-MM-DD, defaults to yesterday
    member_count: int = 10000
    claims_per_member: float = 2.5


class DataGenerationResponse(BaseModel):
    """Data generation response model"""
    success: bool
    target_date: str
    claims_generated: int
    claims_loaded: int
    members_covered: int
    error: Optional[str] = None


@router.post("/data/generate-claims", response_model=DataGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_claims_data(
    request: DataGenerationRequest,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
):
    """Generate claims data for a specific date and load to database
    
    This endpoint generates realistic claims data for demonstration purposes.
    Data is loaded directly to the database claims_lines table.
    
    Args:
        request: Data generation request with target_date, member_count, claims_per_member
    
    Returns:
        Generation results
    """
    # Determine target date (default to yesterday)
    if request.target_date:
        target_date = datetime.strptime(request.target_date, "%Y-%m-%d").date()
    else:
        target_date = (datetime.now() - timedelta(days=1)).date()
    
    # Generate data
    result = generate_claims_data_for_date(
        tenant_id=current_user.tenant_id,
        target_date=target_date,
        member_count=request.member_count,
        claims_per_member=request.claims_per_member,
        db=db,
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate claims data: {result.get('error', 'Unknown error')}"
        )
    
    return DataGenerationResponse(
        success=True,
        target_date=result["target_date"],
        claims_generated=result["claims_generated"],
        claims_loaded=result["claims_loaded"],
        members_covered=result["members_covered"],
    )


@router.post("/data/generate-claims/policy-scoped", response_model=DataGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_policy_scoped_claims_data(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
    policy_id: str = Query(..., description="Policy ID to generate scoped data for"),
    request: DataGenerationRequest = Body(...),
):
    """Generate claims data that matches a policy's scope
    
    This endpoint generates data with procedure codes, diagnosis codes, and service
    categories that match the policy's scope, enabling policy-specific baseline computation.
    """
    from uuid import UUID
    from uepi_api.services.policy_scoped_data_generation import generate_policy_scoped_claims_data
    
    # Determine target date (default to yesterday)
    if request.target_date:
        target_date = datetime.strptime(request.target_date, "%Y-%m-%d").date()
    else:
        target_date = (datetime.now() - timedelta(days=1)).date()
    
    try:
        policy_id_uuid = UUID(policy_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid policy_id format: {policy_id}")
    
    # Generate policy-scoped data
    result = generate_policy_scoped_claims_data(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id_uuid,
        target_date=target_date,
        member_count=request.member_count,
        claims_per_member=request.claims_per_member,
        db=db,
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate policy-scoped claims data: {result.get('error', 'Unknown error')}"
        )
    
    return DataGenerationResponse(
        success=True,
        target_date=result["target_date"],
        claims_generated=result["claims_generated"],
        claims_loaded=result["claims_loaded"],
        members_covered=result["members_covered"],
    )


@router.post("/data/generate-claims/date-range", response_model=Dict[str, Any], status_code=status.HTTP_202_ACCEPTED)
async def generate_claims_data_for_date_range(
    background_tasks: BackgroundTasks,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    member_count: int = Query(10000, description="Number of members"),
    claims_per_member: float = Query(2.5, description="Average claims per member per day"),
):
    """Generate claims data for a date range and load to database via pipeline
    
    This is a repeatable pipeline operation that generates claims data for each day
    in the specified range and loads it directly to the database.
    Uses background task for long-running operations.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        member_count: Number of members to generate data for
        claims_per_member: Average claims per member per day
    
    Returns:
        Job acceptance response
    """
    from uuid import uuid4
    
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")
    
    total_days = (end - start).days + 1
    if total_days > 365:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
    
    # Create job ID
    job_id = str(uuid4())
    
    # Run in background
    background_tasks.add_task(
        _generate_claims_data_for_date_range_task,
        tenant_id=current_user.tenant_id,
        start_date=start,
        end_date=end,
        member_count=member_count,
        claims_per_member=claims_per_member,
        job_id=job_id,
    )
    
    return {
        "success": True,
        "job_id": job_id,
        "message": f"Data generation started for {start_date} to {end_date} ({total_days} days)",
        "start_date": start_date,
        "end_date": end_date,
        "total_days": total_days,
        "status": "ACCEPTED",
    }


def _generate_claims_data_for_date_range_task(
    tenant_id: UUID,
    start_date: date,
    end_date: date,
    member_count: int,
    claims_per_member: float,
    job_id: str,
):
    """Background task to generate claims data for date range"""
    from uepi_api.database import SessionLocal
    
    db = SessionLocal()
    try:
        results = {
            "success": True,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_days": (end_date - start_date).days + 1,
            "days_processed": 0,
            "days_failed": 0,
            "total_claims_generated": 0,
            "total_claims_loaded": 0,
            "total_members_covered": 0,
            "daily_results": [],
            "errors": [],
        }
        
        current_date = start_date
        day_count = 0
        
        while current_date <= end_date:
            day_count += 1
            try:
                # Generate data for this date
                result = generate_claims_data_for_date(
                    tenant_id=tenant_id,
                    target_date=current_date,
                    member_count=member_count,
                    claims_per_member=claims_per_member,
                    db=db,
                )
                
                if result.get("success"):
                    results["days_processed"] += 1
                    results["total_claims_generated"] += result.get("claims_generated", 0)
                    results["total_claims_loaded"] += result.get("claims_loaded", 0)
                    results["total_members_covered"] = max(results["total_members_covered"], result.get("members_covered", 0))
                    results["daily_results"].append({
                        "date": current_date.isoformat(),
                        "claims_generated": result.get("claims_generated", 0),
                        "claims_loaded": result.get("claims_loaded", 0),
                        "members_covered": result.get("members_covered", 0),
                    })
                    
                    if day_count % 5 == 0:
                        print(f"✅ Processed {day_count} days: {results['days_processed']} successful, {results['days_failed']} failed, {results['total_claims_loaded']:,} total claims loaded")
                    
                    # Log every day for first 10 days
                    if day_count <= 10:
                        print(f"   Day {day_count} ({current_date}): {result.get('claims_loaded', 0)} claims loaded")
                else:
                    results["days_failed"] += 1
                    error_msg = result.get("error", "Unknown error")
                    results["errors"].append({
                        "date": current_date.isoformat(),
                        "error": error_msg,
                    })
            except Exception as e:
                results["days_failed"] += 1
                results["errors"].append({
                    "date": current_date.isoformat(),
                    "error": str(e),
                })
            
            current_date += timedelta(days=1)
        
        if results["days_failed"] > 0:
            results["success"] = False
        
        print(f"✅ Date range generation complete: {results['days_processed']} days processed, {results['total_claims_loaded']:,} claims loaded")
        return results
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ ERROR in date range generation: {e}")
        print(f"Traceback: {error_trace}")
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        db.close()


@router.get("/data/generate-claims/status", response_model=Dict[str, Any])
async def check_data_generation_status(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Check data generation status by querying database for claims in date range
    
    This endpoint checks if claims data exists in the database for the specified
    date range, which indicates if data generation has completed.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Status information including claim counts and date coverage
    """
    from uepi_api.repositories.canonical_data import CanonicalDataRepository
    from datetime import date as date_type
    
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    repo = CanonicalDataRepository(db)
    
    # Get total claims count
    total_count = repo.count_claims_lines(current_user.tenant_id)
    
    # Get claims for date range
    claims_df = repo.get_claims_lines(
        tenant_id=current_user.tenant_id,
        start_date=start,
        end_date=end,
    )
    
    date_range_count = len(claims_df) if not claims_df.empty else 0
    
    # Get date distribution if data exists
    date_distribution = {}
    if not claims_df.empty and 'service_date' in claims_df.columns:
        dates = claims_df['service_date'].value_counts().sort_index()
        date_distribution = {
            "first_date": str(dates.index.min()),
            "last_date": str(dates.index.max()),
            "unique_dates": len(dates),
            "total_days_in_range": (end - start).days + 1,
            "coverage_pct": (len(dates) / ((end - start).days + 1) * 100) if (end - start).days > 0 else 0,
        }
        
        # Sample daily counts
        sample_dates = {}
        for sample_date in [start, start + timedelta(days=(end-start).days//2), end]:
            if sample_date in dates.index:
                sample_dates[sample_date.isoformat()] = int(dates[sample_date])
        date_distribution["sample_daily_counts"] = sample_dates
    
    # Calculate totals if data exists
    totals = {}
    if not claims_df.empty:
        if 'paid_amount' in claims_df.columns:
            totals["total_paid"] = float(claims_df['paid_amount'].sum())
        if 'allowed_amount' in claims_df.columns:
            totals["total_allowed"] = float(claims_df['allowed_amount'].sum())
        if 'member_id' in claims_df.columns:
            totals["unique_members"] = int(claims_df['member_id'].nunique())
        totals["total_claims"] = len(claims_df)
    
    return {
        "success": True,
        "start_date": start_date,
        "end_date": end_date,
        "total_claims_in_database": total_count,
        "claims_in_date_range": date_range_count,
        "data_exists": date_range_count > 0,
        "date_distribution": date_distribution if date_distribution else None,
        "totals": totals if totals else None,
        "status": "COMPLETE" if date_range_count > 0 else "IN_PROGRESS_OR_MISSING",
    }


@router.post("/data/generate-claims/yesterday", response_model=DataGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_claims_data_yesterday(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    member_count: int = Query(10000, ge=100, le=100000),
    claims_per_member: float = Query(2.5, ge=0.1, le=10.0),
    db: Session = Depends(get_db),
):
    """Quick endpoint to generate claims data for yesterday"""
    target_date = (datetime.now() - timedelta(days=1)).date()
    
    result = generate_claims_data_for_date(
        tenant_id=current_user.tenant_id,
        target_date=target_date,
        member_count=member_count,
        claims_per_member=claims_per_member,
        db=db,
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate claims data: {result.get('error', 'Unknown error')}"
        )
    
    return DataGenerationResponse(
        success=True,
        target_date=result["target_date"],
        claims_generated=result["claims_generated"],
        claims_loaded=result["claims_loaded"],
        members_covered=result["members_covered"],
    )
