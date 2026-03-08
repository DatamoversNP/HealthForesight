"""Data period storage - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, date

from sqlalchemy.orm import Session
from uepi_api.models.data_period import DataPeriod


def create_data_period(
    tenant_id: UUID,
    period_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new data period - stored in database"""
    return _create_data_period(tenant_id, period_data)


def _create_data_period(
    tenant_id: UUID,
    period_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create data period in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Generate period_id if not provided
        period_id = period_data.get("period_id") or f"{period_data.get('start_date', '').replace('-', '')}-{uuid4().hex[:8]}"
        
        # Parse dates - model uses period_start_date and period_end_date
        start_date = datetime.utcnow()
        if period_data.get("start_date"):
            if isinstance(period_data["start_date"], str):
                start_date = datetime.fromisoformat(period_data["start_date"].replace("Z", "+00:00"))
            elif isinstance(period_data["start_date"], (date, datetime)):
                start_date = datetime.combine(period_data["start_date"], datetime.min.time()) if isinstance(period_data["start_date"], date) else period_data["start_date"]
        
        end_date = datetime.utcnow()
        if period_data.get("end_date"):
            if isinstance(period_data["end_date"], str):
                end_date = datetime.fromisoformat(period_data["end_date"].replace("Z", "+00:00"))
            elif isinstance(period_data["end_date"], (date, datetime)):
                end_date = datetime.combine(period_data["end_date"], datetime.min.time()) if isinstance(period_data["end_date"], date) else period_data["end_date"]
        
        # Parse UUIDs
        data_snapshot_id = UUID(period_data["data_snapshot_id"]) if period_data.get("data_snapshot_id") else None
        
        # Create data period in database
        # Store additional fields in metadata_json
        metadata = period_data.get("metadata", {})
        metadata.update({
            "period_type": period_data.get("period_type", "MONTHLY"),
            "ingestion_timestamp": period_data.get("ingestion_timestamp", datetime.utcnow().isoformat()),
            "ingestion_id": str(period_data["ingestion_id"]) if period_data.get("ingestion_id") else None,
            "data_status": period_data.get("data_status", "COMPLETE"),
            "baseline_eligible": period_data.get("baseline_eligible", True),
            "policies_effective": period_data.get("policies_effective", []),
            "version": period_data.get("version", 1),
            "parent_period_id": period_data.get("parent_period_id"),
        })
        
        data_period = DataPeriod(
            tenant_id=tenant_id,
            period_id=period_id,
            name=period_data.get("name"),
            description=period_data.get("description"),
            period_start_date=start_date,
            period_end_date=end_date,
            data_snapshot_id=data_snapshot_id,
            metadata_json=metadata,
        )
        
        db.add(data_period)
        db.commit()
        db.refresh(data_period)
        
        meta = data_period.metadata_json or {}
        # Return as dict (same format as file-based); model uses period_start_date/period_end_date and metadata_json
        # Include id (UUID) for FK use (e.g. observations.data_period_id); period_id is the string identifier
        return {
            "id": str(data_period.id),
            "period_id": data_period.period_id,
            "tenant_id": str(data_period.tenant_id),
            "period_type": meta.get("period_type", "MONTHLY"),
            "start_date": data_period.period_start_date.isoformat() if data_period.period_start_date else None,
            "end_date": data_period.period_end_date.isoformat() if data_period.period_end_date else None,
            "ingestion_timestamp": meta.get("ingestion_timestamp"),
            "ingestion_id": meta.get("ingestion_id"),
            "data_status": meta.get("data_status", "COMPLETE"),
            "baseline_eligible": meta.get("baseline_eligible", True),
            "policies_effective": meta.get("policies_effective", []),
            "version": meta.get("version", 1),
            "parent_period_id": meta.get("parent_period_id"),
            "created_at": data_period.created_at.isoformat() if data_period.created_at else None,
            "updated_at": data_period.updated_at.isoformat() if data_period.updated_at else None,
            "metadata": meta,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create data period: {e}")
    finally:
        db.close()


def get_data_period(tenant_id: UUID, period_id: str) -> Optional[Dict[str, Any]]:
    """Get a data period by period_id (string e.g. '20260301-9b48c70c') - from database"""
    return _get_data_period(tenant_id, period_id)


def get_data_period_by_id(tenant_id: UUID, period_uuid: str) -> Optional[Dict[str, Any]]:
    """Get a data period by primary key id (UUID). Use when observation stores data_period_id as UUID."""
    return _get_data_period_by_id(tenant_id, period_uuid)


def _get_data_period_by_id(tenant_id: UUID, period_uuid: str) -> Optional[Dict[str, Any]]:
    """Get data period from database by id (UUID)."""
    from uepi_api.database import SessionLocal

    db: Session = SessionLocal()
    try:
        period_uuid_parsed = period_uuid if isinstance(period_uuid, UUID) else UUID(str(period_uuid))
        data_period = db.query(DataPeriod).filter(
            DataPeriod.tenant_id == tenant_id,
            DataPeriod.id == period_uuid_parsed,
        ).first()

        if not data_period:
            return None

        meta = data_period.metadata_json or {}
        return {
            "id": str(data_period.id),
            "period_id": data_period.period_id,
            "tenant_id": str(data_period.tenant_id),
            "period_type": meta.get("period_type", "MONTHLY"),
            "start_date": data_period.period_start_date.isoformat() if data_period.period_start_date else None,
            "end_date": data_period.period_end_date.isoformat() if data_period.period_end_date else None,
            "ingestion_timestamp": meta.get("ingestion_timestamp"),
            "ingestion_id": meta.get("ingestion_id"),
            "data_status": meta.get("data_status", "COMPLETE"),
            "baseline_eligible": meta.get("baseline_eligible", True),
            "policies_effective": meta.get("policies_effective", []),
            "version": meta.get("version", 1),
            "parent_period_id": meta.get("parent_period_id"),
            "created_at": data_period.created_at.isoformat() if data_period.created_at else None,
            "updated_at": data_period.updated_at.isoformat() if data_period.updated_at else None,
            "metadata": meta,
        }
    except Exception as e:
        print(f"ERROR get_data_period_by_id (DB): {e}")
        return None
    finally:
        db.close()


def _get_data_period(tenant_id: UUID, period_id: str) -> Optional[Dict[str, Any]]:
    """Get data period from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        data_period = db.query(DataPeriod).filter(
            DataPeriod.tenant_id == tenant_id,
            DataPeriod.period_id == period_id
        ).first()
        
        if not data_period:
            return None
        
        meta = data_period.metadata_json or {}
        # Return as dict (same format as file-based); model uses period_start_date/period_end_date and metadata_json
        return {
            "id": str(data_period.id),
            "period_id": data_period.period_id,
            "tenant_id": str(data_period.tenant_id),
            "period_type": meta.get("period_type", "MONTHLY"),
            "start_date": data_period.period_start_date.isoformat() if data_period.period_start_date else None,
            "end_date": data_period.period_end_date.isoformat() if data_period.period_end_date else None,
            "ingestion_timestamp": meta.get("ingestion_timestamp"),
            "ingestion_id": meta.get("ingestion_id"),
            "data_status": meta.get("data_status", "COMPLETE"),
            "baseline_eligible": meta.get("baseline_eligible", True),
            "policies_effective": meta.get("policies_effective", []),
            "version": meta.get("version", 1),
            "parent_period_id": meta.get("parent_period_id"),
            "created_at": data_period.created_at.isoformat() if data_period.created_at else None,
            "updated_at": data_period.updated_at.isoformat() if data_period.updated_at else None,
            "metadata": meta,
        }
        
    except Exception as e:
        print(f"ERROR get_data_period (DB): {e}")
        return None
    finally:
        db.close()


def list_data_periods(
    tenant_id: UUID,
    period_type: Optional[str] = None,
    baseline_eligible: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List data periods for a tenant - from database"""
    return _list_data_periods(tenant_id, period_type, baseline_eligible, start_date, end_date)


def _list_data_periods(
    tenant_id: UUID,
    period_type: Optional[str] = None,
    baseline_eligible: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List data periods from database"""
    from uepi_api.database import SessionLocal
    from sqlalchemy import desc
    
    db: Session = SessionLocal()
    try:
        query = db.query(DataPeriod).filter(DataPeriod.tenant_id == tenant_id)
        
        # Sort by start_date descending (most recent first)
        periods = query.order_by(desc(DataPeriod.period_start_date)).all()
        
        # Convert to dict format
        result = []
        for data_period in periods:
            metadata = data_period.metadata_json if data_period.metadata_json else {}
            
            # Apply filters (after loading since fields are in metadata)
            if period_type and metadata.get("period_type") != period_type:
                continue
            if baseline_eligible is not None and metadata.get("baseline_eligible") != baseline_eligible:
                continue
            if start_date:
                end_dt_str = data_period.period_end_date.isoformat() if data_period.period_end_date else None
                if end_dt_str and end_dt_str < start_date:
                    continue
            if end_date:
                start_dt_str = data_period.period_start_date.isoformat() if data_period.period_start_date else None
                if start_dt_str and start_dt_str > end_date:
                    continue
            
            result.append({
                "period_id": data_period.period_id,
                "tenant_id": str(data_period.tenant_id),
                "period_type": metadata.get("period_type", "MONTHLY"),
                "start_date": data_period.period_start_date.isoformat() if data_period.period_start_date else None,
                "end_date": data_period.period_end_date.isoformat() if data_period.period_end_date else None,
                "ingestion_timestamp": metadata.get("ingestion_timestamp"),
                "ingestion_id": metadata.get("ingestion_id"),
                "data_status": metadata.get("data_status", "COMPLETE"),
                "baseline_eligible": metadata.get("baseline_eligible", True),
                "policies_effective": metadata.get("policies_effective", []),
                "version": metadata.get("version", 1),
                "parent_period_id": metadata.get("parent_period_id"),
                "created_at": data_period.created_at.isoformat() if data_period.created_at else None,
                "updated_at": data_period.updated_at.isoformat() if data_period.updated_at else None,
                "metadata": {k: v for k, v in metadata.items() if k not in ["period_type", "ingestion_timestamp", "ingestion_id", "data_status", "baseline_eligible", "policies_effective", "version", "parent_period_id"]},
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_data_periods (DB): {e}")
        return []
    finally:
        db.close()


def update_data_period(
    tenant_id: UUID,
    period_id: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update a data period in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        data_period = db.query(DataPeriod).filter(
            DataPeriod.tenant_id == tenant_id,
            DataPeriod.period_id == period_id
        ).first()
        
        if not data_period:
            return None
        
        # Update fields
        metadata = data_period.metadata_json if data_period.metadata_json else {}
        
        for key, value in updates.items():
            if key in ['start_date', 'period_start_date']:
                if isinstance(value, str):
                    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                elif isinstance(value, date):
                    value = datetime.combine(value, datetime.min.time())
                data_period.period_start_date = value
            elif key in ['end_date', 'period_end_date']:
                if isinstance(value, str):
                    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                elif isinstance(value, date):
                    value = datetime.combine(value, datetime.min.time())
                data_period.period_end_date = value
            elif key == 'name':
                data_period.name = value
            elif key == 'description':
                data_period.description = value
            elif key == 'data_snapshot_id':
                data_period.data_snapshot_id = UUID(value) if isinstance(value, str) else value
            elif key in ['period_type', 'ingestion_timestamp', 'ingestion_id', 'data_status', 'baseline_eligible', 'policies_effective', 'version', 'parent_period_id']:
                # Store in metadata
                metadata[key] = value
            elif key == 'metadata':
                # Merge metadata
                if isinstance(value, dict):
                    metadata.update(value)
            else:
                # Store other fields in metadata
                metadata[key] = value
        
        data_period.metadata_json = metadata
        
        db.commit()
        db.refresh(data_period)
        
        # Return as dict
        metadata = data_period.metadata_json if data_period.metadata_json else {}
        return {
            "period_id": data_period.period_id,
            "tenant_id": str(data_period.tenant_id),
            "period_type": metadata.get("period_type", "MONTHLY"),
            "start_date": data_period.period_start_date.isoformat() if data_period.period_start_date else None,
            "end_date": data_period.period_end_date.isoformat() if data_period.period_end_date else None,
            "ingestion_timestamp": metadata.get("ingestion_timestamp"),
            "ingestion_id": metadata.get("ingestion_id"),
            "data_status": metadata.get("data_status", "COMPLETE"),
            "baseline_eligible": metadata.get("baseline_eligible", True),
            "policies_effective": metadata.get("policies_effective", []),
            "version": metadata.get("version", 1),
            "parent_period_id": metadata.get("parent_period_id"),
            "created_at": data_period.created_at.isoformat() if data_period.created_at else None,
            "updated_at": data_period.updated_at.isoformat() if data_period.updated_at else None,
            "metadata": {k: v for k, v in metadata.items() if k not in ["period_type", "ingestion_timestamp", "ingestion_id", "data_status", "baseline_eligible", "policies_effective", "version", "parent_period_id"]},
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update data period: {e}")
    finally:
        db.close()


def get_baseline_eligible_periods(
    tenant_id: UUID,
    policy_effective_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get baseline-eligible periods (pre-policy data)"""
    all_periods = list_data_periods(tenant_id, baseline_eligible=True)
    
    if policy_effective_date:
        # Filter to periods that end before policy effective date
        baseline_periods = [
            p for p in all_periods
            if p.get("end_date") and p["end_date"] < policy_effective_date
        ]
    else:
        # Return all baseline-eligible periods
        baseline_periods = all_periods
    
    # Sort by end_date descending (most recent first)
    baseline_periods.sort(key=lambda p: p.get("end_date", ""), reverse=True)
    
    return baseline_periods


def get_latest_baseline_period(
    tenant_id: UUID,
    policy_effective_date: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Get the latest baseline-eligible period"""
    baseline_periods = get_baseline_eligible_periods(tenant_id, policy_effective_date)
    return baseline_periods[0] if baseline_periods else None
