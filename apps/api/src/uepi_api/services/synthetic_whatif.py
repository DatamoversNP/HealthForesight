"""What-if on the loaded synthetic payer population.

The payment result is the application engine. The oracle is a separate check
and is not copied into observations. Clinical policies stay not measurable.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict, List, Mapping, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from uepi_api.models.canonical_data import ClaimsLineDB
from uepi_api.models.policy import Policy
from uepi_api.services.enrollment_exposure import measured_enrollment_member_months
from uepi_api.services.expansion_demo_scenarios import (
    apply_infusion_soc,
    apply_ncci_mue,
    apply_ncci_ptp,
    apply_therapy_coverage,
)
from uepi_api.services.reimbursement_mppr import apply_mppr
from uepi_api.services.reimbursement_sos import apply_sos
from uepi_api.services.synthetic_payer_integration import POLICY_FACTS, WINDOW_INCLUSIVE_END
from uepi_common.synthetic_payer.generate import REFERENCE_DATE, WINDOW_START
from uepi_common.synthetic_payer.oracle import (
    oracle_infusion_by_claim,
    oracle_mppr,
    oracle_mue,
    oracle_ptp,
    oracle_sos,
    oracle_therapy,
)

SOURCE_SYSTEM = "SYNTHETIC_PAYER_V1"
LONGITUDINAL_SOURCE = "SYNTHETIC_LONGITUDINAL_V1"
CLINICAL_KEYS = {"mri", "ncd", "lcd"}
PAYMENT_KEYS = {"mppr", "sos", "ptp", "mue", "therapy", "infusion"}
_IDENTITY_CACHE: Dict[str, Any] = {}

CLINICAL_REASON = (
    "Source events are stored. A population payment or utilization outcome is not measurable "
    "for this policy. No endpoint contract is applied."
)


class WhatIfRejected(ValueError):
    """The requested what-if is outside the supported synthetic mechanisms."""


def clear_identity_cache() -> None:
    _IDENTITY_CACHE.clear()


def dataset_identity(db: Session, tenant_id: UUID) -> Dict[str, Any]:
    """Describe the database this process is reading. Cached after the first read."""
    cache_key = str(tenant_id)
    if cache_key in _IDENTITY_CACHE:
        return _IDENTITY_CACHE[cache_key]
    db.execute(text("SET LOCAL statement_timeout = 120000"))
    database_name = db.execute(text("SELECT current_database()")).scalar()
    claim_rows = db.execute(
        text(
            """
            SELECT COUNT(*) FROM claims_lines
            WHERE tenant_id = :tenant_id AND source_system = :source
            """
        ),
        {"tenant_id": tenant_id, "source": SOURCE_SYSTEM},
    ).scalar()
    if not claim_rows:
        longitudinal_rows = db.execute(
            text(
                """
                SELECT COUNT(*) FROM claims_lines
                WHERE tenant_id = :tenant_id AND source_system = :source
                """
            ),
            {"tenant_id": tenant_id, "source": LONGITUDINAL_SOURCE},
        ).scalar()
        if longitudinal_rows:
            member_months = measured_enrollment_member_months(
                db, tenant_id, date(2025, 7, 1), date(2026, 9, 30)
            )
            payload = {
                "synthetic": True,
                "label": "Longitudinal synthetic catalog",
                "database_name": database_name,
                "source_system": LONGITUDINAL_SOURCE,
                "claim_rows": int(longitudinal_rows),
                "covered_lives": None,
                "member_months": member_months,
                "what_if_engine": "LONGITUDINAL_PAYMENT",
                "supported_what_if_keys": sorted(PAYMENT_KEYS),
                "what_if_period": "POST",
                "not_real_adjudication": True,
                "not_measured_savings": True,
                "honesty": (
                    "Payment what-if runs on POST-period ACTIVE longitudinal claim lines for mppr, sos, ptp, "
                    "mue, therapy, and infusion only. Clinical policies stay unavailable. "
                    "A simulated difference is not measured savings."
                ),
            }
            _IDENTITY_CACHE[cache_key] = payload
            return payload
        payload = {
            "synthetic": False,
            "database_name": database_name,
            "source_system": None,
        }
        _IDENTITY_CACHE[cache_key] = payload
        return payload
    covered_lives = db.execute(
        text(
            """
            SELECT COUNT(*) FROM enrollment_records
            WHERE tenant_id = :tenant_id
              AND source_system = :source
              AND enrollment_month = :reference_date
            """
        ),
        {"tenant_id": tenant_id, "source": SOURCE_SYSTEM, "reference_date": REFERENCE_DATE},
    ).scalar()
    member_months = measured_enrollment_member_months(
        db, tenant_id, WINDOW_START, WINDOW_INCLUSIVE_END
    )
    payload = {
        "synthetic": True,
        "label": "Synthetic payer population",
        "database_name": database_name,
        "source_system": SOURCE_SYSTEM,
        "covered_lives": int(covered_lives or 0),
        "member_months": member_months,
        "claim_rows": int(claim_rows),
        "pharmacy_rows": 0,
        "dataset_role": (
            "Covered population plus a policy-event extract. "
            "Not a complete medical or pharmacy book."
        ),
        "not_real_adjudication": True,
        "not_measured_savings": True,
        "window": [WINDOW_START.isoformat(), date(2026, 10, 1).isoformat()],
        "window_end_inclusive_for_exposure": WINDOW_INCLUSIVE_END.isoformat(),
    }
    _IDENTITY_CACHE[cache_key] = payload
    return payload


def _money(value: float) -> float:
    return round(float(value), 2)


def _optional_rate(amount: Optional[float], exposure: Optional[float]) -> Optional[float]:
    if amount is None or exposure is None or exposure <= 0:
        return None
    return amount / exposure


def _params(raw: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    return dict(raw or {})


def _require_range(name: str, value: float, low: float, high: float) -> float:
    if value < low or value > high:
        raise WhatIfRejected(f"{name} must be between {low} and {high}")
    return value


def run_population_whatif(
    lines: List[Mapping[str, Any]],
    policy_key: str,
    parameters: Optional[Mapping[str, Any]],
    member_months: Optional[float],
) -> Dict[str, Any]:
    """Run one policy. Lines must already be that policy's active, in-scope events."""
    params = _params(parameters)
    facts = POLICY_FACTS.get(policy_key)
    if facts is None:
        raise WhatIfRejected(f"Unknown synthetic policy {policy_key}")
    base = {
        "policy_key": policy_key,
        "policy_name": facts["name"],
        "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
        "composition": "SINGLE_POLICY_ONLY",
        "real_world_savings": False,
        "cms_adjudication": False,
        "confidence_interval": None,
        "p_value": None,
        "statistical_significance": None,
        "member_months": member_months,
        "lines_included": len(lines),
        "parameters": {},
    }
    if policy_key in CLINICAL_KEYS:
        return {
            **base,
            "status": "unavailable",
            "outcome_status": "NOT_MEASURABLE",
            "execution": "NOT_MEASURABLE",
            "reason": CLINICAL_REASON,
            "baseline_allowed": None,
            "simulated_allowed": None,
            "allowed_difference": None,
            "allowed_difference_per_enrolled_member_month": None,
            "baseline_plan_paid": None,
            "simulated_plan_paid": None,
            "plan_paid_difference": None,
            "payment_impact_dollars": None,
            "oracle_match": None,
            "label": CLINICAL_REASON,
        }
    if policy_key not in PAYMENT_KEYS:
        raise WhatIfRejected(f"{policy_key} is not a supported payment what-if")
    if not lines:
        return {
            **base,
            "status": "unavailable",
            "outcome_status": "NO_IN_SCOPE_LINES",
            "execution": "SYNTHETIC_SIMULATION",
            "reason": "No active in-scope claim lines for this policy.",
            "baseline_allowed": None,
            "simulated_allowed": None,
            "allowed_difference": None,
            "allowed_difference_per_enrolled_member_month": None,
            "baseline_plan_paid": None,
            "simulated_plan_paid": None,
            "plan_paid_difference": None,
            "payment_impact_dollars": None,
            "oracle_match": None,
            "label": "No in-scope lines. The difference is unavailable, not zero.",
        }

    engine, oracle, used = _apply(policy_key, lines, params)
    totals = engine["totals"]
    baseline_allowed = _money(totals["baseline_paid"])
    simulated_allowed = _money(totals["post_policy_paid"])
    payment_impact = _money(totals["payment_impact"])
    oracle_baseline = _money(oracle["baseline_paid"])
    oracle_post = _money(oracle["post_policy_paid"])
    oracle_impact = _money(oracle["payment_impact"])
    matched = (
        abs(baseline_allowed - oracle_baseline) < 0.02
        and abs(simulated_allowed - oracle_post) < 0.02
        and abs(payment_impact - oracle_impact) < 0.02
    )
    baseline_plan_paid = _money(sum(float(row.get("paid_amount") or 0) for row in lines))
    if baseline_allowed > 0:
        simulated_plan_paid = _money(simulated_allowed * (baseline_plan_paid / baseline_allowed))
    else:
        simulated_plan_paid = None
    allowed_difference = _money(simulated_allowed - baseline_allowed)
    plan_paid_difference = (
        None if simulated_plan_paid is None else _money(simulated_plan_paid - baseline_plan_paid)
    )
    return {
        **base,
        "status": "completed" if matched else "reconciliation_failed",
        "outcome_status": "SYNTHETIC_SIMULATION",
        "execution": "SYNTHETIC_SIMULATION",
        "parameters": used,
        "baseline_allowed": baseline_allowed,
        "simulated_allowed": simulated_allowed,
        "allowed_difference": allowed_difference,
        "allowed_difference_per_enrolled_member_month": _optional_rate(allowed_difference, member_months),
        "baseline_plan_paid": baseline_plan_paid,
        "simulated_plan_paid": simulated_plan_paid,
        "plan_paid_difference": plan_paid_difference,
        "plan_paid_difference_per_enrolled_member_month": _optional_rate(plan_paid_difference, member_months),
        "payment_impact_dollars": payment_impact,
        "payment_impact_meaning": (
            "Baseline allowed minus simulated allowed. Positive means the simulated allowed "
            "is lower. This is not measured savings."
        ),
        "allowed_difference_meaning": (
            "Simulated allowed minus baseline allowed. Negative means simulated allowed is "
            "below baseline allowed. Divided by enrolled member-months when that denominator is measured."
        ),
        "plan_paid_meaning": (
            "Baseline plan paid is the stored plan-paid amount on these lines. "
            "Simulated plan paid applies that same plan-paid share of allowed to the simulated allowed. "
            "It is not a separate adjudication."
        ),
        "oracle_match": matched,
        "oracle_check": {
            "baseline_allowed": oracle_baseline,
            "simulated_allowed": oracle_post,
            "payment_impact_dollars": oracle_impact,
            "copied_into_result": False,
        },
        "label": (
            "Synthetic allowed-dollar simulation. Not measured savings, not a confidence interval, "
            "and not real payer adjudication."
        ),
        "volume_held_constant": True,
        "utilization_change_pct": None,
    }


def _apply(policy_key: str, lines: List[Mapping[str, Any]], params: Mapping[str, Any]):
    if policy_key == "mppr":
        secondary_pct = _require_range("secondary_pct", float(params.get("secondary_pct", 0.5)), 0.0, 1.0)
        used = {"secondary_pct": secondary_pct}
        return apply_mppr(lines, secondary_pct=secondary_pct), oracle_mppr(lines, secondary_pct), used
    if policy_key == "sos":
        hospital_pct = _require_range("hospital_pct", float(params.get("hospital_pct", 0.8)), 0.0, 2.0)
        used = {"hospital_pct": hospital_pct}
        return apply_sos(lines, hospital_pct=hospital_pct), oracle_sos(lines, hospital_pct), used
    if policy_key == "ptp":
        indicator = str(params.get("modifier_indicator", "1"))
        if indicator not in {"0", "1", "9"}:
            raise WhatIfRejected("modifier_indicator must be 0, 1, or 9")
        used = {"modifier_indicator": indicator}
        return apply_ncci_ptp(lines, modifier_indicator=indicator), oracle_ptp(lines, indicator), used
    if policy_key == "mue":
        mue_value = int(params.get("mue_value", 4))
        if mue_value < 0 or mue_value > 100:
            raise WhatIfRejected("mue_value must be between 0 and 100")
        used = {"mue_value": mue_value, "mue_value_note": "Demo cap. Not a CMS MUE."}
        return apply_ncci_mue(lines, mue_value=mue_value), oracle_mue(lines, mue_value), used
    if policy_key == "therapy":
        return apply_therapy_coverage(lines), oracle_therapy(lines), {}
    office_allowed = _require_range("office_allowed", float(params.get("office_allowed", 3200.0)), 0.0, 100000.0)
    steer = int(params.get("steer_hopd_count", 1))
    if steer < 0 or steer > 20:
        raise WhatIfRejected("steer_hopd_count must be between 0 and 20")
    used = {"office_allowed": office_allowed, "steer_hopd_count": steer, "applied": "per_claim"}
    engine = _infusion_population(lines, office_allowed=office_allowed, steer_hopd_count=steer)
    oracle = oracle_infusion_by_claim(lines, office_allowed=office_allowed, steer_hopd_count=steer)
    return engine, oracle, used


def _infusion_population(
    lines: List[Mapping[str, Any]],
    *,
    office_allowed: float,
    steer_hopd_count: int,
) -> Dict[str, Any]:
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for row in lines:
        grouped.setdefault(str(row.get("claim_id") or ""), []).append(row)
    baseline = 0.0
    post = 0.0
    for claim_lines in grouped.values():
        part = apply_infusion_soc(
            claim_lines,
            steer_hopd_count=steer_hopd_count,
            office_allowed=office_allowed,
        )
        baseline += part["totals"]["baseline_paid"]
        post += part["totals"]["post_policy_paid"]
    impact = _money(baseline - post)
    return {
        "totals": {
            "baseline_paid": _money(baseline),
            "post_policy_paid": _money(post),
            "payment_impact": impact,
        }
    }


def load_policy_lines(
    db: Session,
    tenant_id: UUID,
    policy_key: str,
    *,
    source_system: str = SOURCE_SYSTEM,
    period: Optional[str] = None,
) -> Dict[str, Any]:
    """Active lines for one policy identity, limited to that policy's procedure scope."""
    facts = POLICY_FACTS[policy_key]
    codes = set(facts["codes"])
    token = f'"policy_key":"{policy_key}"'
    rows = (
        db.query(ClaimsLineDB)
        .filter(
            ClaimsLineDB.tenant_id == tenant_id,
            ClaimsLineDB.source_system == source_system,
            ClaimsLineDB.service_category == policy_key,
            ClaimsLineDB.record_hash.contains(token),
        )
        .all()
    )
    included: List[Dict[str, Any]] = []
    excluded_other_policy = 0
    excluded_not_active = 0
    excluded_out_of_scope = 0
    excluded_other_period = 0
    for row in rows:
        extra = json.loads(row.record_hash or "{}")
        if extra.get("policy_key") != policy_key:
            excluded_other_policy += 1
            continue
        if extra.get("line_status") != "ACTIVE":
            excluded_not_active += 1
            continue
        if period and extra.get("period") != period:
            excluded_other_period += 1
            continue
        if row.cpt_code not in codes:
            excluded_out_of_scope += 1
            continue
        included.append(
            {
                "member_id": row.member_id,
                "claim_id": row.claim_id,
                "claim_line_id": row.claim_line_id,
                "cpt_code": row.cpt_code,
                "allowed_amount": float(row.allowed_amount),
                "paid_amount": float(row.paid_amount),
                "member_cost_share": float(row.member_cost_share),
                "units": float(row.units),
                "place_of_service": row.place_of_service,
                **extra,
            }
        )
    return {
        "lines": included,
        "procedure_codes": sorted(codes),
        "excluded_other_policy": excluded_other_policy,
        "excluded_not_active": excluded_not_active,
        "excluded_out_of_scope": excluded_out_of_scope,
        "excluded_other_period": excluded_other_period,
        "source_system": source_system,
        "period": period,
    }


def execute_synthetic_whatif(
    db: Session,
    tenant_id: UUID,
    policy_id: UUID,
    parameters: Optional[Mapping[str, Any]],
    extra_policy_ids: Optional[List[UUID]] = None,
) -> Dict[str, Any]:
    if extra_policy_ids and len(extra_policy_ids) > 1:
        raise WhatIfRejected(
            "Ordered composition of more than one policy on the same claim line is not supported. "
            "Run one policy at a time. Summing policies would double-count a shared line."
        )
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.tenant_id == tenant_id).first()
    if policy is None:
        raise WhatIfRejected("Policy was not found in this database")
    metadata = policy.policy_metadata_json or {}
    policy_key = metadata.get("policy_key")
    if not policy_key:
        raise WhatIfRejected("This policy is not part of the synthetic payer population")
    identity = dataset_identity(db, tenant_id)
    if not identity.get("synthetic"):
        raise WhatIfRejected("This database is not the synthetic payer population")
    engine = identity.get("what_if_engine")
    if engine == "NOT_THIS_POPULATION":
        raise WhatIfRejected(identity.get("honesty") or "What-if is not available for this dataset")
    if engine == "LONGITUDINAL_PAYMENT" and str(policy_key) not in PAYMENT_KEYS:
        raise WhatIfRejected(
            "Longitudinal what-if supports only the six payment-rule policies. "
            "Clinical and catalog policies stay unavailable."
        )
    source = str(identity.get("source_system") or SOURCE_SYSTEM)
    period = "POST" if source == LONGITUDINAL_SOURCE else None
    loaded = load_policy_lines(
        db,
        tenant_id,
        str(policy_key),
        source_system=source,
        period=period,
    )
    result = run_population_whatif(
        loaded["lines"],
        str(policy_key),
        parameters,
        identity.get("member_months"),
    )
    result["policy_id"] = str(policy_id)
    result["database_name"] = identity.get("database_name")
    result["covered_lives"] = identity.get("covered_lives")
    result["procedure_codes"] = loaded["procedure_codes"]
    result["source_system"] = source
    result["lines_period"] = period
    result["exclusions"] = {
        "other_policy_identity": loaded["excluded_other_policy"],
        "not_active": loaded["excluded_not_active"],
        "outside_procedure_scope": loaded["excluded_out_of_scope"],
        "other_period": loaded["excluded_other_period"],
    }
    result["population_label"] = identity.get("dataset_role") or identity.get("label")
    result["not_measured_savings"] = True
    return result
