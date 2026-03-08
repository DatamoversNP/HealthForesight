"""
Epic 5: Behavioral Signal Detection - Storage Module
Database only
"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.behavior import BehaviorProfile, BehaviorCluster as BehaviorClusterDB
from sqlalchemy import desc
from uepi_common.models_enhanced import (
    ProviderBehaviorProfile,
    BehaviorCluster,
    SignalMetric,
    BehaviorType,
)


def _safe_uuid(value: Any) -> Optional[UUID]:
    """Safely convert value to UUID"""
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return UUID(value)
        except (ValueError, AttributeError):
            return None
    return None


# Provider Behavior Profiles
def create_behavior_profile(
    tenant_id: UUID,
    profile_data: Dict[str, Any]
) -> ProviderBehaviorProfile:
    """Create a new behavior profile - stored in database"""
    return _create_behavior_profile(tenant_id, profile_data)


def _create_behavior_profile(
    tenant_id: UUID,
    profile_data: Dict[str, Any]
) -> ProviderBehaviorProfile:
    """Create behavior profile in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        provider_id = profile_data.get("provider_id")
        if not provider_id:
            raise ValueError("provider_id is required")
        
        signals_data = profile_data.get("signals", [])
        signals = [
            SignalMetric(**sig) if isinstance(sig, dict) else sig
            for sig in signals_data
        ]
        
        first_detected = datetime.fromisoformat(profile_data["first_detected"].replace("Z", "+00:00")) if isinstance(profile_data.get("first_detected"), str) else profile_data.get("first_detected", datetime.utcnow())
        
        profile_id = str(uuid4())
        profile_db = BehaviorProfile(
            tenant_id=tenant_id,
            profile_id=profile_id,
            behavior_type=profile_data.get("behavior_type", "NEUTRAL"),
            provider_id=provider_id,
            signals_json={
                "signals": [sig.model_dump(mode='json') if hasattr(sig, 'model_dump') else sig for sig in signals],
                "provider_name": profile_data.get("provider_name"),
                "policy_version_id": str(profile_data.get("policy_version_id")) if profile_data.get("policy_version_id") else None,
            },
            detected_at=first_detected,
            confidence=profile_data.get("confidence", 0.5),
        )
        
        db.add(profile_db)
        db.commit()
        db.refresh(profile_db)
        
        return ProviderBehaviorProfile(
            provider_id=provider_id,
            provider_name=profile_data.get("provider_name"),
            behavior_type=BehaviorType(profile_db.behavior_type),
            confidence=float(profile_db.confidence) if profile_db.confidence else 0.5,
            signals=signals,
            policy_version_id=_safe_uuid(profile_data.get("policy_version_id")),
            first_detected=profile_db.detected_at,
            last_updated=profile_db.updated_at,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create behavior profile: {e}")
    finally:
        db.close()


def get_behavior_profile(
    tenant_id: UUID,
    provider_id: str
) -> Optional[ProviderBehaviorProfile]:
    """Get behavior profile for a provider - from database"""
    return _get_behavior_profile(tenant_id, provider_id)


def _get_behavior_profile(
    tenant_id: UUID,
    provider_id: str
) -> Optional[ProviderBehaviorProfile]:
    """Get behavior profile from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        profile_db = db.query(BehaviorProfile).filter(
            BehaviorProfile.tenant_id == tenant_id,
            BehaviorProfile.provider_id == provider_id
        ).first()
        
        if not profile_db:
            return None
        
        signals_json = profile_db.signals_json if profile_db.signals_json else {}
        return ProviderBehaviorProfile(
            provider_id=provider_id,
            provider_name=signals_json.get("provider_name"),
            behavior_type=BehaviorType(profile_db.behavior_type),
            confidence=float(profile_db.confidence) if profile_db.confidence else 0.5,
            signals=[SignalMetric(**sig) if isinstance(sig, dict) else sig for sig in signals_json.get("signals", [])],
            policy_version_id=UUID(signals_json["policy_version_id"]) if signals_json.get("policy_version_id") else None,
            first_detected=profile_db.detected_at,
            last_updated=profile_db.updated_at,
        )
        
    except Exception as e:
        print(f"ERROR get_behavior_profile (DB): {e}")
        return None
    finally:
        db.close()


def list_behavior_profiles(
    tenant_id: UUID,
    behavior_type: Optional[BehaviorType] = None,
    min_confidence: Optional[float] = None
) -> List[ProviderBehaviorProfile]:
    """List behavior profiles - from database"""
    return _list_behavior_profiles(tenant_id, behavior_type, min_confidence)


def _list_behavior_profiles(
    tenant_id: UUID,
    behavior_type: Optional[BehaviorType] = None,
    min_confidence: Optional[float] = None
) -> List[ProviderBehaviorProfile]:
    """List behavior profiles from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(BehaviorProfile).filter(BehaviorProfile.tenant_id == tenant_id)
        
        if behavior_type:
            query = query.filter(BehaviorProfile.behavior_type == behavior_type.value)
        
        if min_confidence is not None:
            query = query.filter(BehaviorProfile.confidence >= str(min_confidence))
        
        profiles_db = query.order_by(desc(BehaviorProfile.updated_at)).all()
        
        result = []
        for profile_db in profiles_db:
            signals_json = profile_db.signals_json if profile_db.signals_json else {}
            result.append(ProviderBehaviorProfile(
                provider_id=profile_db.provider_id,
                provider_name=signals_json.get("provider_name"),
                behavior_type=BehaviorType(profile_db.behavior_type),
                confidence=float(profile_db.confidence) if profile_db.confidence else 0.5,
                signals=[SignalMetric(**sig) if isinstance(sig, dict) else sig for sig in signals_json.get("signals", [])],
                policy_version_id=UUID(signals_json["policy_version_id"]) if signals_json.get("policy_version_id") else None,
                first_detected=profile_db.detected_at,
                last_updated=profile_db.updated_at,
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_behavior_profiles (DB): {e}")
        return []
    finally:
        db.close()


def update_behavior_profile(
    tenant_id: UUID,
    provider_id: str,
    updates: Dict[str, Any]
) -> Optional[ProviderBehaviorProfile]:
    """Update behavior profile - stored in database"""
    return _update_behavior_profile(tenant_id, provider_id, updates)


def _update_behavior_profile(
    tenant_id: UUID,
    provider_id: str,
    updates: Dict[str, Any]
) -> Optional[ProviderBehaviorProfile]:
    """Update behavior profile in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        profile_db = db.query(BehaviorProfile).filter(
            BehaviorProfile.tenant_id == tenant_id,
            BehaviorProfile.provider_id == provider_id
        ).first()
        
        if not profile_db:
            return None
        
        signals_json = profile_db.signals_json if profile_db.signals_json else {}
        
        if "signals" in updates:
            signals_data = updates["signals"]
            signals = [
                SignalMetric(**sig) if isinstance(sig, dict) else sig
                for sig in signals_data
            ]
            signals_json["signals"] = [sig.model_dump(mode='json') if hasattr(sig, 'model_dump') else sig for sig in signals]
        
        if "behavior_type" in updates:
            profile_db.behavior_type = updates["behavior_type"]
        
        if "confidence" in updates:
            profile_db.confidence = str(updates["confidence"])
        
        if "provider_name" in updates:
            signals_json["provider_name"] = updates["provider_name"]
        
        profile_db.signals_json = signals_json
        
        db.commit()
        db.refresh(profile_db)
        
        return ProviderBehaviorProfile(
            provider_id=provider_id,
            provider_name=signals_json.get("provider_name"),
            behavior_type=BehaviorType(profile_db.behavior_type),
            confidence=float(profile_db.confidence) if profile_db.confidence else 0.5,
            signals=[SignalMetric(**sig) if isinstance(sig, dict) else sig for sig in signals_json.get("signals", [])],
            policy_version_id=UUID(signals_json["policy_version_id"]) if signals_json.get("policy_version_id") else None,
            first_detected=profile_db.detected_at,
            last_updated=profile_db.updated_at,
        )
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_behavior_profile (DB): {e}")
        return None
    finally:
        db.close()


# Behavior Clusters
def create_behavior_cluster(
    tenant_id: UUID,
    cluster_data: Dict[str, Any]
) -> BehaviorCluster:
    """Create a new behavior cluster - stored in database"""
    return _create_behavior_cluster(tenant_id, cluster_data)


def _create_behavior_cluster(
    tenant_id: UUID,
    cluster_data: Dict[str, Any]
) -> BehaviorCluster:
    """Create behavior cluster in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        cluster_id = str(cluster_data.get("cluster_id") or uuid4())
        
        cluster_db = BehaviorClusterDB(
            tenant_id=tenant_id,
            cluster_id=cluster_id,
            cluster_type=cluster_data.get("cluster_type", "UTILIZATION"),
            members_json=cluster_data.get("members", []),
            characteristics_json=cluster_data.get("characteristics", {}),
        )
        
        db.add(cluster_db)
        db.commit()
        db.refresh(cluster_db)
        
        return BehaviorCluster(
            cluster_id=cluster_id,
            cluster_type=cluster_data.get("cluster_type", "UTILIZATION"),
            members=cluster_db.members_json if cluster_db.members_json else [],
            characteristics=cluster_db.characteristics_json if cluster_db.characteristics_json else {},
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create behavior cluster: {e}")
    finally:
        db.close()


def get_behavior_cluster(
    tenant_id: UUID,
    cluster_id: UUID
) -> Optional[BehaviorCluster]:
    """Get behavior cluster - from database"""
    return _get_behavior_cluster(tenant_id, str(cluster_id))


def _get_behavior_cluster(
    tenant_id: UUID,
    cluster_id: str
) -> Optional[BehaviorCluster]:
    """Get behavior cluster from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        cluster_db = db.query(BehaviorClusterDB).filter(
            BehaviorClusterDB.tenant_id == tenant_id,
            BehaviorClusterDB.cluster_id == cluster_id
        ).first()
        
        if not cluster_db:
            return None
        
        return BehaviorCluster(
            cluster_id=cluster_id,
            cluster_type=cluster_db.cluster_type,
            members=cluster_db.members_json if cluster_db.members_json else [],
            characteristics=cluster_db.characteristics_json if cluster_db.characteristics_json else {},
        )
        
    except Exception as e:
        print(f"ERROR get_behavior_cluster (DB): {e}")
        return None
    finally:
        db.close()


def list_behavior_clusters(
    tenant_id: UUID,
    behavior_type: Optional[BehaviorType] = None
) -> List[BehaviorCluster]:
    """List behavior clusters - from database"""
    return _list_behavior_clusters(tenant_id, behavior_type.value if behavior_type else None)


def _list_behavior_clusters(
    tenant_id: UUID,
    cluster_type: Optional[str] = None
) -> List[BehaviorCluster]:
    """List behavior clusters from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(BehaviorClusterDB).filter(BehaviorClusterDB.tenant_id == tenant_id)
        
        if cluster_type:
            query = query.filter(BehaviorClusterDB.cluster_type == cluster_type)
        
        clusters_db = query.all()
        
        result = []
        for cluster_db in clusters_db:
            result.append(BehaviorCluster(
                cluster_id=cluster_db.cluster_id,
                cluster_type=cluster_db.cluster_type,
                members=cluster_db.members_json if cluster_db.members_json else [],
                characteristics=cluster_db.characteristics_json if cluster_db.characteristics_json else {},
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_behavior_clusters (DB): {e}")
        return []
    finally:
        db.close()
