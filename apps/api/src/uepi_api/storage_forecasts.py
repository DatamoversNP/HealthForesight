"""Forecast storage - database only"""
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.forecast import Forecast
from uepi_common.models_enhanced import ForecastDistribution, UncertaintyRange, ConfidenceInterval


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


def create_forecast(
    tenant_id: UUID,
    forecast_data: Dict[str, Any]
) -> ForecastDistribution:
    """Create a new forecast distribution - stored in database"""
    return _create_forecast(tenant_id, forecast_data)


def _create_forecast(
    tenant_id: UUID,
    forecast_data: Dict[str, Any]
) -> ForecastDistribution:
    """Create forecast in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Generate forecast_id if not provided
        forecast_id = str(_safe_uuid(forecast_data.get("forecast_id")) or uuid4())
        
        # Parse policy_id if provided
        policy_id = None
        if forecast_data.get("policy_id"):
            policy_id = UUID(forecast_data["policy_id"]) if isinstance(forecast_data["policy_id"], str) else forecast_data["policy_id"]
        
        # Store forecast data in JSONB
        projections = {
            "metric_name": forecast_data.get("metric_name", ""),
            "point_estimate": forecast_data.get("point_estimate", 0.0),
            "uncertainty_range": forecast_data.get("uncertainty_range"),
            "confidence_interval": forecast_data.get("confidence_interval"),
            "distribution_data": forecast_data.get("distribution_data"),
        }
        
        # Create forecast in database
        forecast = Forecast(
            tenant_id=tenant_id,
            forecast_id=forecast_id,
            policy_id=policy_id,
            projections_json=projections,
            confidence_intervals_json=forecast_data.get("confidence_interval"),
            forecast_date=datetime.fromisoformat(forecast_data["forecast_date"].replace("Z", "+00:00")) if isinstance(forecast_data.get("forecast_date"), str) else forecast_data.get("forecast_date", datetime.utcnow()),
            forecast_horizon=forecast_data.get("forecast_horizon"),
            forecast_method=forecast_data.get("forecast_method"),
        )
        
        db.add(forecast)
        db.commit()
        db.refresh(forecast)
        
        # Return Pydantic model for compatibility
        projections_data = forecast.projections_json if forecast.projections_json else {}
        uncertainty_range = None
        if projections_data.get("uncertainty_range"):
            ur_data = projections_data["uncertainty_range"]
            if isinstance(ur_data, dict):
                uncertainty_range = UncertaintyRange(**ur_data)
        
        confidence_interval = None
        if forecast.confidence_intervals_json:
            ci_data = forecast.confidence_intervals_json
            if isinstance(ci_data, dict):
                confidence_interval = ConfidenceInterval(**ci_data)
        
        return ForecastDistribution(
            forecast_id=UUID(forecast_id),
            metric_name=projections_data.get("metric_name", ""),
            point_estimate=projections_data.get("point_estimate", 0.0),
            uncertainty_range=uncertainty_range,
            confidence_interval=confidence_interval,
            distribution_data=projections_data.get("distribution_data"),
            created_at=forecast.created_at,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create forecast: {e}")
    finally:
        db.close()


def get_forecast(
    tenant_id: UUID,
    forecast_id: UUID
) -> Optional[ForecastDistribution]:
    """Get a forecast by ID - from database"""
    return _get_forecast(tenant_id, forecast_id)


def _get_forecast(
    tenant_id: UUID,
    forecast_id: UUID
) -> Optional[ForecastDistribution]:
    """Get forecast from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        forecast = db.query(Forecast).filter(
            Forecast.tenant_id == tenant_id,
            Forecast.forecast_id == str(forecast_id)
        ).first()
        
        if not forecast:
            return None
        
        # Convert to Pydantic model
        projections_data = forecast.projections_json if forecast.projections_json else {}
        uncertainty_range = None
        if projections_data.get("uncertainty_range"):
            ur_data = projections_data["uncertainty_range"]
            if isinstance(ur_data, dict):
                uncertainty_range = UncertaintyRange(**ur_data)
        
        confidence_interval = None
        if forecast.confidence_intervals_json:
            ci_data = forecast.confidence_intervals_json
            if isinstance(ci_data, dict):
                confidence_interval = ConfidenceInterval(**ci_data)
        
        return ForecastDistribution(
            forecast_id=UUID(forecast.forecast_id),
            metric_name=projections_data.get("metric_name", ""),
            point_estimate=projections_data.get("point_estimate", 0.0),
            uncertainty_range=uncertainty_range,
            confidence_interval=confidence_interval,
            distribution_data=projections_data.get("distribution_data"),
            created_at=forecast.created_at,
        )
        
    except Exception as e:
        print(f"ERROR get_forecast (DB): {e}")
        return None
    finally:
        db.close()


def list_forecasts(
    tenant_id: UUID,
    metric_name: Optional[str] = None,
    policy_id: Optional[UUID] = None
) -> List[ForecastDistribution]:
    """List all forecasts for a tenant, optionally filtered by metric - from database"""
    return _list_forecasts(tenant_id, metric_name, policy_id)


def _list_forecasts(
    tenant_id: UUID,
    metric_name: Optional[str] = None,
    policy_id: Optional[UUID] = None
) -> List[ForecastDistribution]:
    """List forecasts from database"""
    from uepi_api.database import SessionLocal
    from sqlalchemy import desc
    
    db: Session = SessionLocal()
    try:
        query = db.query(Forecast).filter(Forecast.tenant_id == tenant_id)
        
        # Filter by policy_id if provided
        if policy_id:
            query = query.filter(Forecast.policy_id == policy_id)
        
        # Sort by created_at descending (newest first)
        forecasts = query.order_by(desc(Forecast.created_at)).all()
        
        # Convert to Pydantic models
        result = []
        for forecast in forecasts:
            projections_data = forecast.projections_json if forecast.projections_json else {}
            
            # Filter by metric_name if provided
            if metric_name and projections_data.get("metric_name") != metric_name:
                continue
            
            uncertainty_range = None
            if projections_data.get("uncertainty_range"):
                ur_data = projections_data["uncertainty_range"]
                if isinstance(ur_data, dict):
                    uncertainty_range = UncertaintyRange(**ur_data)
            
            confidence_interval = None
            if forecast.confidence_intervals_json:
                ci_data = forecast.confidence_intervals_json
                if isinstance(ci_data, dict):
                    confidence_interval = ConfidenceInterval(**ci_data)
            
            result.append(ForecastDistribution(
                forecast_id=UUID(forecast.forecast_id),
                metric_name=projections_data.get("metric_name", ""),
                point_estimate=projections_data.get("point_estimate", 0.0),
                uncertainty_range=uncertainty_range,
                confidence_interval=confidence_interval,
                distribution_data=projections_data.get("distribution_data"),
                created_at=forecast.created_at,
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_forecasts (DB): {e}")
        return []
    finally:
        db.close()
