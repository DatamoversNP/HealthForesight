"""Shared what-if scenario runner. Used by the Celery worker task and by sync scripts (no worker import)."""
from uuid import UUID
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session


def run_whatif_scenario_sync(
    tenant_id: str,
    analysis_id: str,
    policy_id: str,
    scenario_params: dict,
    baseline_filters: dict,
    db: Optional[Session] = None,
) -> dict:
    """
    Run what-if scenario simulation (DB + simulation + store result).
    Callable from Celery task or from scripts without importing uepi_worker.tasks.
    """
    from uepi_api.models.analysis import Analysis, AnalysisStatus, AnalysisResultIndex, WhatIfScenarioResult
    from uepi_api.models.policy import Policy
    from uepi_common.models import CanonicalPolicy, PolicyStatus, PolicyScope, EffectivePeriod, Enforcement
    from uepi_worker.whatif import simulate_scenario, ScenarioParameters
    from uepi_worker.analytics import load_claims_data

    own_db = False
    if db is None:
        from uepi_api.database import SessionLocal
        db = SessionLocal()
        own_db = True
    try:
        analysis = db.query(Analysis).filter(Analysis.id == UUID(analysis_id)).first()
        if not analysis:
            return {"status": "error", "message": "Analysis not found"}

        analysis.status = AnalysisStatus.RUNNING.value
        db.commit()

        policy_record = db.query(Policy).filter(Policy.id == UUID(policy_id)).first()
        if not policy_record:
            analysis.status = AnalysisStatus.FAILED.value
            if hasattr(Analysis, "error_message"):
                analysis.error_message = "Policy not found"
            db.commit()
            return {"status": "error", "message": "Policy not found"}

        policy_metadata = policy_record.policy_metadata_json if hasattr(policy_record, "policy_metadata_json") else {}
        policy = CanonicalPolicy(
            policy_id=policy_record.id,
            policy_name=policy_record.name,
            policy_type=policy_record.policy_type,
            description=policy_record.description or "",
            status=PolicyStatus(policy_record.status) if hasattr(policy_record, "status") else PolicyStatus.ACTIVE,
            scope=PolicyScope(**policy_metadata.get("scope", {})) if policy_metadata.get("scope") else PolicyScope(lob=None, markets=None, network=None),
            effective_period=EffectivePeriod(
                start_date=datetime.fromisoformat(policy_metadata["effective_period"]["start_date"]) if policy_metadata.get("effective_period", {}).get("start_date") else datetime.utcnow(),
                end_date=datetime.fromisoformat(policy_metadata["effective_period"]["end_date"]) if policy_metadata.get("effective_period", {}).get("end_date") else None,
            ) if policy_metadata.get("effective_period") else EffectivePeriod(start_date=datetime.utcnow(), end_date=None),
            enforcement=Enforcement(**policy_metadata["enforcement"]) if policy_metadata.get("enforcement") else None,
            policy_logic=None,
        )

        start_dt = datetime.utcnow() - timedelta(days=365)
        end_dt = datetime.utcnow()
        baseline_df = None
        try:
            from uepi_api.database_claims_loader import load_claims_from_database
            from uepi_api.services.policy_scoped_data_generation import build_policy_claims_filters

            policy_dict = {
                "scope": policy_metadata.get("scope") or {},
                "policy_levers": policy_metadata.get("policy_levers", []),
                "logic": policy_metadata.get("logic", {}),
                "policy_logic": policy_metadata.get("policy_logic", {}),
            }
            pf = build_policy_claims_filters(policy_dict)
            db_filters: Dict[str, Any] = {}
            if pf.get("lob"):
                db_filters["lob"] = pf["lob"]
            if pf.get("markets"):
                db_filters["markets"] = pf["markets"]
            elif pf.get("market"):
                db_filters["markets"] = [pf["market"]] if isinstance(pf["market"], str) else pf["market"]
            if pf.get("cpt_codes") or pf.get("procedure_codes"):
                db_filters["cpt_codes"] = pf.get("cpt_codes") or pf.get("procedure_codes")
            if pf.get("service_categories"):
                db_filters["service_categories"] = pf["service_categories"]
            elif pf.get("service_category"):
                db_filters["service_category"] = pf["service_category"]
            if pf.get("diagnosis_codes"):
                db_filters["diagnosis_codes"] = pf["diagnosis_codes"]

            pdf = load_claims_from_database(
                UUID(tenant_id),
                start_dt.date(),
                end_dt.date(),
                filters=db_filters if db_filters else None,
                db=db,
            )
            if not pdf.empty:
                import polars as pl
                baseline_df = pl.from_pandas(pdf)
                print(f"What-if: loaded {len(baseline_df)} claims from database")
        except Exception as db_err:
            print(f"What-if: DB load failed: {db_err}")

        if baseline_df is None or baseline_df.is_empty() or len(baseline_df) == 0:
            baseline_df = load_claims_data(
                UUID(tenant_id),
                baseline_filters,
                start_dt,
                end_dt,
            )
            if not baseline_df.is_empty() and len(baseline_df) > 0:
                print(f"What-if: loaded {len(baseline_df)} claims from fallback")

        if baseline_df.is_empty() or len(baseline_df) == 0:
            analysis.status = AnalysisStatus.FAILED.value
            err_msg = "No claims found for policy scope; check scope and data availability."
            if hasattr(Analysis, "error_message"):
                analysis.error_message = err_msg
            db.commit()
            return {"status": "error", "message": err_msg}

        scenario = ScenarioParameters(
            policy_id=policy_id,
            lever_adjustments=scenario_params.get("lever_adjustments", {}),
            elasticity_adjustments=scenario_params.get("elasticity_adjustments", {}),
            member_count_multiplier=scenario_params.get("member_count_multiplier", 1.0),
            utilization_trend=scenario_params.get("utilization_trend", 0.0),
            cost_inflation=scenario_params.get("cost_inflation", 0.02),
            projection_months=scenario_params.get("projection_months", 12),
        )

        elasticity_curves = None
        try:
            from uepi_api.storage_learning import get_latest_elasticity_model
            pt = policy.policy_type
            policy_type = (getattr(pt, "value", None) if pt is not None else None) or pt or "PRIOR_AUTH"
            if not isinstance(policy_type, str):
                policy_type = getattr(policy_type, "value", str(policy_type))
            latest_model = get_latest_elasticity_model(
                tenant_id=UUID(tenant_id),
                policy_type=policy_type,
                service_category=None,
            )
            if latest_model:
                elasticity_coefficients = latest_model.get("elasticity_coefficients", {})
                if elasticity_coefficients:
                    elasticity_curves = {}
                    for category, coeffs in elasticity_coefficients.items():
                        if isinstance(coeffs, dict):
                            elasticity_curves[category] = {
                                "elasticity": coeffs.get("utilization_elasticity", coeffs.get("elasticity", -0.3)),
                                "cost_elasticity": coeffs.get("cost_elasticity", -0.2),
                                "confidence": latest_model.get("confidence", 0.7),
                                "model_version": latest_model.get("version", "v1.0"),
                            }
        except Exception as e:
            print(f"Warning: Could not load latest elasticity models for what-if scenario: {e}")

        result = simulate_scenario(
            UUID(tenant_id),
            policy,
            baseline_df,
            scenario,
            elasticity_curves=elasticity_curves,
            use_latest_elasticity_models=True,
        )

        result_dict = {
            "scenario_id": result.scenario_id,
            "baseline_metrics": result.baseline_metrics,
            "projected_metrics": result.projected_metrics,
            "impact_metrics": result.impact_metrics,
            "confidence_intervals": {k: list(v) for k, v in result.confidence_intervals.items()},
            "confidence_score": result.confidence_score,
            "sensitivity_analysis": result.sensitivity_analysis,
        }

        try:
            existing_result = db.query(WhatIfScenarioResult).filter(
                WhatIfScenarioResult.analysis_id == UUID(analysis_id)
            ).first()
            if existing_result:
                existing_result.result_data_json = result_dict
                existing_result.updated_at = datetime.utcnow()
                db.add(existing_result)
            else:
                whatif_result_db = WhatIfScenarioResult(
                    tenant_id=UUID(tenant_id),
                    analysis_id=UUID(analysis_id),
                    policy_id=UUID(policy_id),
                    result_data_json=result_dict,
                    schema_version="1.0",
                )
                db.add(whatif_result_db)
            existing_index = db.query(AnalysisResultIndex).filter(
                AnalysisResultIndex.analysis_id == UUID(analysis_id),
                AnalysisResultIndex.result_type == "WHATIF_SCENARIO",
            ).first()
            if not existing_index:
                result_index = AnalysisResultIndex(
                    tenant_id=UUID(tenant_id),
                    analysis_id=UUID(analysis_id),
                    result_type="WHATIF_SCENARIO",
                    data_uri=None,
                    schema_version="1.0",
                )
                db.add(result_index)
            db.commit()
        except Exception as db_error:
            db.rollback()
            print(f"Failed to store what-if result in database: {db_error}")

        analysis.status = AnalysisStatus.COMPLETED.value
        db.commit()
        return {
            "status": "completed",
            "analysis_id": analysis_id,
            "result_uri": "database",
            "confidence_score": result.confidence_score,
        }
    except Exception as e:
        try:
            a = db.query(Analysis).filter(Analysis.id == UUID(analysis_id)).first()
            if a:
                a.status = AnalysisStatus.FAILED.value
                err_msg = str(e)
                if hasattr(Analysis, "error_message"):
                    a.error_message = (err_msg[:2000] if len(err_msg) > 2000 else err_msg) or None
                db.commit()
        except Exception:
            pass
        raise
    finally:
        if own_db and db is not None:
            db.close()
