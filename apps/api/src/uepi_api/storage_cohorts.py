"""File-based storage for cohorts - database only"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from uepi_api.models.cohort import Cohort as CohortDB
from sqlalchemy import desc


def create_cohort(tenant_id: UUID, name: str, description: Optional[str], criteria: dict) -> dict:
    """Create a new cohort - stored in database"""
    return _create_cohort(tenant_id, name, description, criteria)


def _create_cohort(tenant_id: UUID, name: str, description: Optional[str], criteria: dict) -> dict:
    """Create cohort in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        cohort_id = uuid4()
        
        cohort_db = CohortDB(
            id=cohort_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            filters_json=criteria,
        )
        
        db.add(cohort_db)
        db.commit()
        db.refresh(cohort_db)
        
        return {
            "id": str(cohort_db.id),
            "tenant_id": str(cohort_db.tenant_id),
            "name": cohort_db.name,
            "description": cohort_db.description,
            "criteria": cohort_db.filters_json if cohort_db.filters_json else {},
            "created_at": cohort_db.created_at.isoformat() if cohort_db.created_at else None,
            "updated_at": cohort_db.updated_at.isoformat() if cohort_db.updated_at else None,
            "last_used_at": cohort_db.last_used_at.isoformat() if cohort_db.last_used_at else None,
            "member_count": None,  # Will be calculated when members are fetched
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create cohort: {e}")
    finally:
        db.close()


def get_cohort(tenant_id: UUID, cohort_id: UUID) -> Optional[dict]:
    """Get a cohort by ID - from database"""
    return _get_cohort(tenant_id, cohort_id)


def _get_cohort(tenant_id: UUID, cohort_id: UUID) -> Optional[dict]:
    """Get cohort from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        cohort_db = db.query(CohortDB).filter(
            CohortDB.tenant_id == tenant_id,
            CohortDB.id == cohort_id
        ).first()
        
        if not cohort_db:
            return None
        
        return {
            "id": str(cohort_db.id),
            "tenant_id": str(cohort_db.tenant_id),
            "name": cohort_db.name,
            "description": cohort_db.description,
            "criteria": cohort_db.filters_json if cohort_db.filters_json else {},
            "created_at": cohort_db.created_at.isoformat() if cohort_db.created_at else None,
            "updated_at": cohort_db.updated_at.isoformat() if cohort_db.updated_at else None,
            "last_used_at": cohort_db.last_used_at.isoformat() if cohort_db.last_used_at else None,
            "member_count": None,  # Will be calculated when members are fetched
        }
        
    except Exception as e:
        print(f"ERROR get_cohort (DB): {e}")
        return None
    finally:
        db.close()


def list_cohorts(tenant_id: UUID, skip: int = 0, limit: int = 100) -> list[dict]:
    """List all cohorts for a tenant - from database"""
    return _list_cohorts(tenant_id, skip, limit)


def _list_cohorts(tenant_id: UUID, skip: int = 0, limit: int = 100) -> list[dict]:
    """List cohorts from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        cohorts_db = db.query(CohortDB).filter(
            CohortDB.tenant_id == tenant_id
        ).order_by(desc(CohortDB.created_at)).offset(skip).limit(limit).all()
        
        result = []
        for cohort_db in cohorts_db:
            result.append({
                "id": str(cohort_db.id),
                "tenant_id": str(cohort_db.tenant_id),
                "name": cohort_db.name,
                "description": cohort_db.description,
                "criteria": cohort_db.filters_json if cohort_db.filters_json else {},
                "created_at": cohort_db.created_at.isoformat() if cohort_db.created_at else None,
                "updated_at": cohort_db.updated_at.isoformat() if cohort_db.updated_at else None,
                "last_used_at": cohort_db.last_used_at.isoformat() if cohort_db.last_used_at else None,
                "member_count": None,  # Will be calculated when members are fetched
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_cohorts (DB): {e}")
        return []
    finally:
        db.close()


def update_cohort(tenant_id: UUID, cohort_id: UUID, name: Optional[str] = None, 
                  description: Optional[str] = None, criteria: Optional[dict] = None) -> Optional[dict]:
    """Update a cohort - stored in database"""
    return _update_cohort(tenant_id, cohort_id, name, description, criteria)


def _update_cohort(tenant_id: UUID, cohort_id: UUID, name: Optional[str] = None, 
                  description: Optional[str] = None, criteria: Optional[dict] = None) -> Optional[dict]:
    """Update cohort in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        cohort_db = db.query(CohortDB).filter(
            CohortDB.tenant_id == tenant_id,
            CohortDB.id == cohort_id
        ).first()
        
        if not cohort_db:
            return None
        
        if name is not None:
            cohort_db.name = name
        if description is not None:
            cohort_db.description = description
        if criteria is not None:
            cohort_db.filters_json = criteria
        
        db.commit()
        db.refresh(cohort_db)
        
        return {
            "id": str(cohort_db.id),
            "tenant_id": str(cohort_db.tenant_id),
            "name": cohort_db.name,
            "description": cohort_db.description,
            "criteria": cohort_db.filters_json if cohort_db.filters_json else {},
            "created_at": cohort_db.created_at.isoformat() if cohort_db.created_at else None,
            "updated_at": cohort_db.updated_at.isoformat() if cohort_db.updated_at else None,
            "last_used_at": cohort_db.last_used_at.isoformat() if cohort_db.last_used_at else None,
            "member_count": None,
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_cohort (DB): {e}")
        return None
    finally:
        db.close()


def delete_cohort(tenant_id: UUID, cohort_id: UUID) -> bool:
    """Delete a cohort - from database"""
    return _delete_cohort(tenant_id, cohort_id)


def _delete_cohort(tenant_id: UUID, cohort_id: UUID) -> bool:
    """Delete cohort from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        cohort_db = db.query(CohortDB).filter(
            CohortDB.tenant_id == tenant_id,
            CohortDB.id == cohort_id
        ).first()
        
        if not cohort_db:
            return False
        
        db.delete(cohort_db)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        print(f"ERROR delete_cohort (DB): {e}")
        return False
    finally:
        db.close()


def get_cohort_members(tenant_id: UUID, cohort_id: UUID, policies: list[dict], 
                       performance: list[dict], skip: int = 0, limit: int = 100) -> list[dict]:
    """Get members (policies) that match cohort criteria"""
    cohort = get_cohort(tenant_id, cohort_id)
    if not cohort:
        return []
    
    criteria = cohort.get("criteria", {})
    matched = []
    
    # Apply filters based on criteria
    if criteria.get("utilization_change"):
        util_filter = criteria["utilization_change"]
        min_val = util_filter.get("min", -float("inf"))
        max_val = util_filter.get("max", float("inf"))
        matched = [
            p for p in performance
            if min_val <= abs(p.get("avg_utilization_change_pct", 0)) <= max_val
        ]
    elif criteria.get("cost_impact"):
        cost_filter = criteria["cost_impact"]
        min_val = cost_filter.get("min", -float("inf"))
        max_val = cost_filter.get("max", float("inf"))
        matched = [
            p for p in performance
            if min_val <= (p.get("avg_cost_impact", 0)) <= max_val
        ]
    elif criteria.get("created_after"):
        after_date = datetime.fromisoformat(criteria["created_after"].replace("Z", "+00:00"))
        matched = [
            p for p in policies
            if p.get("created_at") and datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")) >= after_date
        ]
    elif criteria.get("status"):
        matched = [p for p in policies if p.get("status") == criteria["status"]]
    else:
        return []
    
    # Create a lookup map for policies by ID
    policy_lookup = {}
    for policy in policies:
        policy_id = policy.get("id") or policy.get("policy_id")
        if policy_id:
            policy_id_str = str(policy_id)
            policy_lookup[policy_id_str] = policy
    
    # Get full policy details
    matched_with_details = []
    for match in matched[skip:skip + limit]:
        policy_id = match.get("policy_id") or match.get("id")
        if not policy_id:
            continue
            
        policy_id_str = str(policy_id)
        policy = policy_lookup.get(policy_id_str)
        
        if not policy:
            for p in policies:
                p_id = str(p.get("id") or p.get("policy_id") or "")
                if p_id == policy_id_str:
                    policy = p
                    break
        
        perf = None
        if performance:
            perf = next((p for p in performance if str(p.get("policy_id", "")) == policy_id_str), None)
        
        result = {
            "policy_id": policy_id_str,
            "id": policy_id_str,
        }
        
        if policy:
            policy_name = (
                policy.get("name") or 
                policy.get("policy_name") or 
                policy.get("description") or 
                f"Policy {policy_id_str[:8]}"
            )
            policy_name = " ".join(policy_name.split())
            if len(policy_name) > 100:
                policy_name = policy_name[:100] + "..."
            
            result["name"] = policy_name
            result["policy_name"] = policy_name
            result["status"] = policy.get("status")
            result["policy_type"] = policy.get("policy_type")
            result["description"] = policy.get("description")
            result["created_at"] = policy.get("created_at")
        else:
            policy_name = (
                match.get("policy_name") or 
                (perf.get("policy_name") if perf else None) or 
                f"Policy {policy_id_str[:8]}"
            )
            result["name"] = policy_name
            result["policy_name"] = policy_name
        
        if perf:
            result["avg_utilization_change_pct"] = perf.get("avg_utilization_change_pct", 0)
            result["avg_cost_impact"] = perf.get("avg_cost_impact", 0)
            result["is_predicted"] = perf.get("is_predicted", False)
        elif match.get("avg_utilization_change_pct") is not None:
            result["avg_utilization_change_pct"] = match.get("avg_utilization_change_pct", 0)
            result["avg_cost_impact"] = match.get("avg_cost_impact") or match.get("cost_impact", 0)
        
        matched_with_details.append(result)
    
    # Update last_used_at
    from uepi_api.database import SessionLocal
    db: Session = SessionLocal()
    try:
        cohort_db = db.query(CohortDB).filter(
            CohortDB.tenant_id == tenant_id,
            CohortDB.id == cohort_id
        ).first()
        if cohort_db:
            cohort_db.last_used_at = datetime.utcnow()
            db.commit()
    except Exception:
        pass
    finally:
        db.close()
    
    return matched_with_details
