#!/usr/bin/env python3
"""Lean-stg Option A: configure + lifecycle five payment-rule verticals.

Policies: MPPR, Imaging SOS, PTP, MUE, Infusion SOC.
- Stamp registry mechanisms + payment endpoint contracts
- Persist engine known-answer baselines / PIs / observations
- Recompute verdicts; leave attributed effect % UNESTIMATED on continuation metrics
Refuses non-hfleanstg databases.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import psycopg2
from psycopg2.extras import Json, RealDictCursor

REPO = Path(__file__).resolve().parents[3]
OUT = (
    REPO
    / "docs/production/releases/corrections/nine_mock_policies"
    / "REIMBURSEMENT_FIVE_LIFECYCLE_REPORT.json"
)
TENANT = UUID("00000000-0000-0000-0000-000000000001")

FIVE: List[Dict[str, Any]] = [
    {
        "key": "mppr",
        "name_contains": "Multiple Procedure Payment Reduction",
        "policy_type": "PAYMENT_POLICY",
        "mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
        "engine_id": "reimbursement_mppr_v1",
    },
    {
        "key": "sos",
        "name_contains": "Imaging Site-of-Service",
        "policy_type": "SITE_OF_CARE",
        "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
        "engine_id": "reimbursement_sos_v1",
    },
    {
        "key": "ptp",
        "name_contains": "Procedure-to-Procedure (PTP)",
        "policy_type": "CODING_AND_BILLING",
        "mechanism": "NCCI_PTP_FIXTURE",
        "engine_id": "reimbursement_ncci_ptp_v1",
        "extra_ec": {"dec4_expansion": True, "sub_mechanism": "NCCI_PTP"},
    },
    {
        "key": "mue",
        "name_contains": "Medically Unlikely Edit (MUE)",
        "policy_type": "CODING_AND_BILLING",
        "mechanism": "FEE_SCHEDULE_UNIT_PRICE",
        "engine_id": "reimbursement_ncci_mue_v1",
        "extra_ec": {"sub_mechanism": "NCCI_MUE"},
    },
    {
        "key": "infusion",
        "name_contains": "Infusion Site-of-Care",
        "policy_type": "SITE_OF_CARE",
        "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
        "engine_id": "reimbursement_infusion_soc_v1",
        "extra_ec": {"infusion_soc": True},
    },
]

PAYMENT_ENDPOINTS = [
    {
        "metric_id": "allowed_paid_unit_price",
        "direction": "decrease",
        "label": "Allowed/paid unit price (payment-rule primary)",
    },
    {
        "metric_id": "net_payment_exposure",
        "direction": "decrease",
        "label": "Net payment exposure (payer spend)",
    },
]


def _db_url() -> str:
    env = os.environ.get("DATABASE_URL") or os.environ.get("LEAN_STAGING_DATABASE_URL")
    if env:
        url = env.replace("postgresql+psycopg2://", "postgresql://", 1)
        if "hfleanstg" not in url.lower():
            raise SystemExit("Refusing: DATABASE_URL is not lean staging")
        return url
    raw = subprocess.check_output(
        [
            "az",
            "keyvault",
            "secret",
            "show",
            "--vault-name",
            "hfleanstgkv",
            "--name",
            "lean-staging-database-url",
            "--query",
            "value",
            "-o",
            "tsv",
        ],
        text=True,
    ).strip()
    url = raw.replace("postgresql+psycopg2://", "postgresql://", 1)
    if "hfleanstg" not in url.lower():
        raise SystemExit("Refusing: not lean staging")
    return url


def _as_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
    return value if isinstance(value, dict) else {}


def _engine_payload(key: str) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """Return (calc_version, totals, known_answer_report)."""
    if key == "mppr":
        from uepi_api.services.reimbursement_mppr import (
            CALC_VERSION,
            KNOWN_ANSWER_LINES,
            apply_mppr,
            verify_known_answer,
        )

        ka = verify_known_answer()
        totals = apply_mppr(KNOWN_ANSWER_LINES)["totals"]
        return CALC_VERSION, totals, ka
    if key == "sos":
        from uepi_api.services.reimbursement_sos import (
            CALC_VERSION,
            KNOWN_ANSWER_LINES,
            apply_sos,
            verify_known_answer,
        )

        ka = verify_known_answer()
        totals = apply_sos(KNOWN_ANSWER_LINES)["totals"]
        return CALC_VERSION, totals, ka
    if key == "ptp":
        from uepi_api.services.expansion_demo_scenarios import (
            PTP_CALC_VERSION,
            PTP_KNOWN_LINES,
            apply_ncci_ptp,
            verify_ptp_known_answer,
        )

        ka = verify_ptp_known_answer()
        totals = apply_ncci_ptp(PTP_KNOWN_LINES, modifier_indicator="0")["totals"]
        return PTP_CALC_VERSION, totals, ka
    if key == "mue":
        from uepi_api.services.expansion_demo_scenarios import (
            MUE_CALC_VERSION,
            MUE_KNOWN_LINES,
            apply_ncci_mue,
            verify_mue_known_answer,
        )

        ka = verify_mue_known_answer()
        totals = apply_ncci_mue(MUE_KNOWN_LINES)["totals"]
        return MUE_CALC_VERSION, totals, ka
    if key == "infusion":
        from uepi_api.services.expansion_demo_scenarios import (
            INFUSION_CALC_VERSION,
            INFUSION_KNOWN,
            apply_infusion_soc,
            verify_infusion_known_answer,
        )

        ka = verify_infusion_known_answer()
        totals = apply_infusion_soc(INFUSION_KNOWN, steer_hopd_count=2)["totals"]
        return INFUSION_CALC_VERSION, totals, ka
    raise KeyError(key)


def _find_policy(cur, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    cur.execute(
        """
        SELECT id::text AS id, name, policy_type, status, policy_metadata_json
        FROM policies
        WHERE tenant_id=%s::uuid AND name ILIKE %s
        ORDER BY updated_at DESC NULLS LAST
        LIMIT 1
        """,
        (str(TENANT), f"%{spec['name_contains']}%"),
    )
    return cur.fetchone()


def _stamp_policy(cur, policy: Dict[str, Any], spec: Dict[str, Any], calc_version: str) -> Dict[str, Any]:
    meta = _as_dict(policy.get("policy_metadata_json"))
    ec = dict(meta.get("enterprise_classification") or {})
    ec.update(
        {
            "catalog_class": "DEMO_SYNTHETIC",
            "display_label": "Representative Payer Policies",
            "not_verbatim_bcbsnc_policy": True,
            "mechanism": spec["mechanism"],
            "calculation_version": calc_version,
            "reimbursement_vertical_sample": True,
            "lifecycle_validation": "PAYMENT_RULE_SAMPLE",
        }
    )
    for k, v in (spec.get("extra_ec") or {}).items():
        ec[k] = v
    meta["enterprise_classification"] = ec
    meta["analytical_strategy"] = {
        "engine_id": spec["engine_id"],
        "mechanism": spec["mechanism"],
        "calculation_version": calc_version,
        "calculation_family": "REIMBURSEMENT",
        "registry_dispatch": "ENGINE",
    }
    meta["policy_key"] = spec["key"]
    measurement = dict(meta.get("measurement") or {})
    measurement["required_endpoints"] = list(PAYMENT_ENDPOINTS)
    measurement["primary_metric"] = "allowed_paid_unit_price"
    measurement["not_utilization_model"] = True
    meta["measurement"] = measurement
    meta["required_endpoints"] = list(PAYMENT_ENDPOINTS)

    cur.execute(
        """
        UPDATE policies
        SET policy_metadata_json=%s,
            policy_type=%s,
            updated_at=NOW()
        WHERE id=%s::uuid AND tenant_id=%s::uuid
        """,
        (Json(meta), spec["policy_type"], policy["id"], str(TENANT)),
    )
    return meta


def _upsert_baseline_pi_obs(
    *,
    policy_id: str,
    key: str,
    mechanism: str,
    calc_version: str,
    totals: Dict[str, Any],
    ka: Dict[str, Any],
) -> Dict[str, Any]:
    from uepi_api.storage_baselines import create_baseline
    from uepi_api.storage_observations import create_observation
    from uepi_api.storage_policy_predicted_impact import store_predicted_impact
    from uepi_api.database import SessionLocal
    from uepi_api.models.baseline import Baseline
    from uepi_api.models.observation import Observation

    now = datetime.now(timezone.utc)
    payment_impact = float(totals.get("payment_impact") or 0.0)
    payment_impact_pct = totals.get("payment_impact_pct")
    baseline_paid = float(totals.get("baseline_paid") or totals.get("baseline_allowed") or 0.0)
    post_paid = float(totals.get("post_policy_paid") or 0.0)
    if payment_impact_pct is None and baseline_paid:
        payment_impact_pct = round(100.0 * payment_impact / baseline_paid, 4)

    baseline_metrics = {
        "mechanism": mechanism,
        "calculation_version": calc_version,
        "catalog_class": "DEMO_SYNTHETIC",
        "denominator_basis": "ENROLLMENT",
        "total_allowed": totals.get("baseline_allowed", baseline_paid),
        "total_paid": baseline_paid,
        "line_count": totals.get("line_count"),
        "claim_count": totals.get("claim_count"),
        "volume_units": totals.get("volume_units"),
        "primary_metric": "allowed_paid_unit_price",
        "not_utilization_model": True,
        "fixture": "KNOWN_ANSWER_LINES",
        "reimbursement_vertical_sample": True,
        "known_answer_passed": bool(ka.get("passed")),
    }
    baseline_id_str = f"{key}-ka-baseline-{calc_version}"
    db = SessionLocal()
    try:
        existing_bl = (
            db.query(Baseline)
            .filter(Baseline.tenant_id == TENANT, Baseline.baseline_id == baseline_id_str)
            .first()
        )
        if existing_bl:
            existing_bl.baseline_metrics_json = baseline_metrics
            existing_bl.policy_id = UUID(policy_id)
            existing_bl.computed_at = now.replace(tzinfo=None)
            db.add(existing_bl)
            db.commit()
            db.refresh(existing_bl)
            baseline = {
                "id": str(existing_bl.id),
                "baseline_id": existing_bl.baseline_id,
            }
        else:
            baseline = None
    finally:
        db.close()

    if baseline is None:
        baseline = create_baseline(
            TENANT,
            {
                "baseline_id": baseline_id_str,
                "policy_id": policy_id,
                "baseline_type": "POLICY_SPECIFIC",
                "window_start_date": "2025-01-01T00:00:00+00:00",
                "window_end_date": "2025-12-31T23:59:59+00:00",
                "computed_at": now.isoformat(),
                "version": 1,
                "baseline_metrics": baseline_metrics,
            },
            input_refs={
                "policy_id": policy_id,
                "fixture": "KNOWN_ANSWER_LINES",
                "catalog_class": "DEMO_SYNTHETIC",
            },
            config_snapshot={"calculation_version": calc_version, "key": key},
        )

    pred = store_predicted_impact(
        UUID(policy_id),
        TENANT,
        {
            "predicted_at": now.isoformat(),
            "prediction_method": f"{key.upper()}_PAYMENT_RULE",
            "model_version": calc_version,
            "confidence": 1.0 if ka.get("passed") else 0.5,
            "metrics": {
                "payment_impact": payment_impact,
                "payment_impact_pct": payment_impact_pct,
                "baseline_paid": baseline_paid,
                "post_policy_paid": post_paid,
                "volume_effect": 0.0,
                "mix_effect": 0.0,
                "price_effect": (totals.get("reconciliation") or {}).get("price_effect", payment_impact),
                "prediction_method": f"{key.upper()}_PAYMENT_RULE",
                "calculation_version": calc_version,
                "cost_change_meaning": "MECHANISM_KNOWN_ANSWER_NOT_ATTRIBUTED_FIELD_EFFECT",
                # Continuation attributed effect fields stay null
                "cost_change_pct": None,
                "utilization_change_pct": None,
                "utilization_change_per_1k": None,
                "policy_effect_status": "UNESTIMATED",
            },
            "baseline_reference": {
                "baseline_id": baseline.get("baseline_id") or baseline.get("id"),
                "calculation_version": calc_version,
            },
            "limitations": [
                "Deterministic synthetic known-answer fixture — not empirical payer outcomes.",
                "Attributed policy-effect % left UNESTIMATED; payment_impact is mechanism math only.",
            ],
            "warnings": [],
            "model_versions": {key: calc_version},
        },
    )
    pred_id = pred.get("id") if pred else None

    obs_id = f"{key}-ka-obs-{calc_version}"
    obs_metrics = {
        "mechanism": mechanism,
        "calculation_version": calc_version,
        "catalog_class": "DEMO_SYNTHETIC",
        "denominator_basis": "ENROLLMENT",
        "total_paid": post_paid,
        "baseline_paid": baseline_paid,
        "payment_impact": payment_impact,
        "payment_impact_pct": payment_impact_pct,
        "reconciliation": totals.get("reconciliation"),
        "volume_units": totals.get("volume_units"),
        "known_answer_match": bool(ka.get("passed")),
        "reimbursement_vertical_sample": True,
        "comparisons": {
            "vs_baseline": {
                "payment_delta": -payment_impact,
                "payment_delta_pct": -(payment_impact_pct or 0.0)
                if payment_impact_pct is not None
                else None,
            },
            "vs_predicted": {"payment_delta": 0.0, "payment_delta_pct": 0.0, "match": True},
        },
    }
    # Endpoint-contract change pcts so create_observation/compute_verdict can score ON_TRACK.
    # Payment-rule endpoints look up `{metric_id}_change_pct` (decrease => negative).
    impact_pct = float(payment_impact_pct) if payment_impact_pct is not None else None
    endpoint_change_pct = -impact_pct if impact_pct is not None else None
    obs_metrics["comparisons"]["vs_baseline"].update(
        {
            "allowed_paid_unit_price_change_pct": endpoint_change_pct,
            "net_payment_exposure_change_pct": endpoint_change_pct,
            "payment_impact_pct": impact_pct,
        }
    )
    # Flatten comparisons for storage helpers that expect top-level comparisons_json
    comparisons = obs_metrics["comparisons"]
    verdict_reason = (
        f"Observed post-policy paid matches {key.upper()} known-answer prediction "
        f"({calc_version}); price/edit effect only; volume held constant."
    )
    verdict_status = "ON_TRACK" if ka.get("passed") else "INCONCLUSIVE"

    db = SessionLocal()
    try:
        existing_obs = (
            db.query(Observation)
            .filter(Observation.tenant_id == TENANT, Observation.observation_id == obs_id)
            .first()
        )
        if existing_obs:
            existing_obs.metrics_json = obs_metrics
            existing_obs.comparisons_json = comparisons
            existing_obs.verdict_status = verdict_status
            existing_obs.verdict_reason = verdict_reason
            existing_obs.recommendation = (
                f"Maintain {key.upper()} payment-rule sample; expand after claim-field readiness."
            )
            existing_obs.verdict_rule_version = f"{key}-demo-v1"
            existing_obs.policy_id = UUID(policy_id)
            if pred_id:
                try:
                    existing_obs.prediction_id = UUID(str(pred_id))
                except Exception:
                    pass
            db.add(existing_obs)
            db.commit()
            obs = {"observation_id": existing_obs.observation_id, "id": str(existing_obs.id)}
        else:
            obs = None
    finally:
        db.close()

    if obs is None:
        obs = create_observation(
            TENANT,
            {
                "observation_id": obs_id,
                "policy_id": policy_id,
                "prediction_id": pred_id,
                "baseline_version_id": baseline.get("id"),
                "observation_type": "AD_HOC",
                "observation_period_start": "2026-01-01T00:00:00+00:00",
                "observation_period_end": "2026-03-31T23:59:59+00:00",
                "metrics": obs_metrics,
                "comparisons": comparisons,
                "verdict_status": verdict_status,
                "verdict_reason": verdict_reason,
                "recommendation": (
                    f"Maintain {key.upper()} payment-rule sample; expand after claim-field readiness."
                ),
                "verdict_rule_version": f"{key}-demo-v1",
            },
        )

    return {
        "baseline_id": baseline.get("baseline_id") or baseline.get("id"),
        "predicted_impact_id": pred_id,
        "observation_id": obs.get("observation_id") or obs.get("id"),
        "verdict_status": verdict_status,
        "payment_impact": payment_impact,
        "calculation_version": calc_version,
        "known_answer_passed": bool(ka.get("passed")),
    }


def _run_whatifs(policies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from uepi_api.services.reimbursement_whatif import run_reimbursement_whatif

    scenarios = {
        "mppr": {"base_secondary_pct": 0.5, "secondary_pct": 0.4},
        "sos": {"base_hospital_pct": 0.80, "hospital_pct": 0.70},
        "ptp": {},
        "mue": {"base_mue_value": 4, "mue_value": 3},
        "infusion": {"base_steer_hopd_count": 2, "steer_hopd_count": 3},
    }
    out = []
    for p in policies:
        key = p["key"]
        result = run_reimbursement_whatif(
            policy_type=p["policy_type"],
            policy_name=p["name"],
            metadata=p["metadata"],
            policy_id=p["policy_id"],
            scenario_params=scenarios[key],
        )
        out.append(
            {
                "key": key,
                "policy_id": p["policy_id"],
                "status": result.get("status"),
                "mechanism": (result.get("strategy") or {}).get("mechanism"),
                "calculation_version": (result.get("result") or {}).get("calculation_version"),
                "message": result.get("message"),
            }
        )
    return out


def main() -> int:
    sys.path.insert(0, str(REPO / "apps/api/src"))
    sys.path.insert(0, str(REPO / "packages/common/src"))

    url = _db_url()
    os.environ["DATABASE_URL"] = url

    report: Dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "database": "hfleanstg",
        "option": "A",
        "policies": [],
        "whatifs": [],
        "errors": [],
    }

    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    stamped: List[Dict[str, Any]] = []
    try:
        for spec in FIVE:
            row = _find_policy(cur, spec)
            if not row:
                report["errors"].append({"key": spec["key"], "error": "policy_not_found"})
                continue
            calc_version, totals, ka = _engine_payload(spec["key"])
            if not ka.get("passed"):
                report["errors"].append(
                    {"key": spec["key"], "error": "known_answer_failed", "detail": ka}
                )
            meta = _stamp_policy(cur, row, spec, calc_version)
            stamped.append(
                {
                    "key": spec["key"],
                    "policy_id": row["id"],
                    "name": row["name"],
                    "policy_type": spec["policy_type"],
                    "mechanism": spec["mechanism"],
                    "metadata": meta,
                    "calc_version": calc_version,
                    "totals": {
                        "baseline_paid": totals.get("baseline_paid"),
                        "post_policy_paid": totals.get("post_policy_paid"),
                        "payment_impact": totals.get("payment_impact"),
                        "payment_impact_pct": totals.get("payment_impact_pct"),
                    },
                    "known_answer": {"passed": ka.get("passed"), "checks": ka.get("checks")},
                }
            )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    for item in stamped:
        try:
            calc_version, totals, ka = _engine_payload(item["key"])
            lifecycle = _upsert_baseline_pi_obs(
                policy_id=item["policy_id"],
                key=item["key"],
                mechanism=item["mechanism"],
                calc_version=calc_version,
                totals=totals,
                ka=ka,
            )
            item["lifecycle"] = lifecycle
            report["policies"].append(
                {
                    "key": item["key"],
                    "policy_id": item["policy_id"],
                    "name": item["name"],
                    "policy_type": item["policy_type"],
                    "mechanism": item["mechanism"],
                    "calculation_version": calc_version,
                    "known_answer_passed": bool(ka.get("passed")),
                    "payment_impact": totals.get("payment_impact"),
                    "lifecycle": lifecycle,
                }
            )
        except Exception as exc:
            report["errors"].append({"key": item["key"], "error": str(exc)})

    # What-ifs
    try:
        report["whatifs"] = _run_whatifs(stamped)
    except Exception as exc:
        report["errors"].append({"whatif": str(exc)})

    # Enrollment baseline count check for the five
    conn = psycopg2.connect(url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        ids = [p["policy_id"] for p in report["policies"]]
        if ids:
            cur.execute(
                """
                SELECT policy_id::text,
                       COUNT(*) AS n,
                       COUNT(*) FILTER (
                         WHERE baseline_metrics_json->>'denominator_basis'='ENROLLMENT'
                            OR baseline_metrics_json->>'reimbursement_vertical_sample'='true'
                       ) AS enrollment_or_sample
                FROM baselines
                WHERE tenant_id=%s::uuid AND policy_id = ANY(%s::uuid[])
                GROUP BY 1
                """,
                (str(TENANT), ids),
            )
            report["baseline_counts"] = [dict(r) for r in cur.fetchall()]
            cur.execute(
                """
                SELECT policy_id::text, COUNT(*) AS n,
                       COUNT(*) FILTER (WHERE verdict_status IS NOT NULL) AS with_verdict
                FROM observations
                WHERE tenant_id=%s::uuid AND policy_id = ANY(%s::uuid[])
                GROUP BY 1
                """,
                (str(TENANT), ids),
            )
            report["observation_counts"] = [dict(r) for r in cur.fetchall()]
            cur.execute(
                """
                SELECT policy_id::text, COUNT(*) AS n
                FROM policy_predicted_impacts
                WHERE tenant_id=%s::uuid AND policy_id = ANY(%s::uuid[])
                GROUP BY 1
                """,
                (str(TENANT), ids),
            )
            report["pi_counts"] = [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["ok"] = (
        len(report["policies"]) == 5
        and all(p.get("known_answer_passed") for p in report["policies"])
        and all(w.get("status") == "completed" for w in report.get("whatifs") or [])
        and not report["errors"]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps({"ok": report["ok"], "out": str(OUT), "policies": len(report["policies"]), "errors": report["errors"]}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
