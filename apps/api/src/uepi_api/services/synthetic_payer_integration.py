"""Load the synthetic payer pilot and run application calculations on it.

Stored baselines and observations come from database aggregates and the payment
engines. Oracle figures are compared afterwards and are not written as results.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from datetime import date, datetime
from typing import Any, Dict, List, Mapping
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from uepi_api.models.canonical_data import ClaimsLineDB
from uepi_api.models.policy import Policy
from uepi_api.models.tenant import Tenant, User, user_roles
from uepi_api.password_utils import hash_password
from uepi_api.repositories.canonical_data import CanonicalDataRepository
from uepi_api.services.database_baseline_computation import (
    compute_general_baseline_from_database,
    compute_policy_specific_baseline_from_database,
)
from uepi_api.services.enrollment_exposure import clear_enrollment_cache, measured_enrollment_member_months
from uepi_api.services.synthetic_population import simulate_payment_population
from uepi_api.storage_auth import DEFAULT_TENANT_ID
from uepi_api.storage_baselines import create_baseline
from uepi_api.storage_observations import create_observation
from uepi_common.synthetic_payer.enrollment_rows import iter_enrollment_month_rows
from uepi_common.synthetic_payer.generate import (
    POLICIES,
    REFERENCE_DATE,
    SEED,
    WINDOW_END,
    WINDOW_START,
    generate_events,
    generate_population,
)
from uepi_common.synthetic_payer.oracle import (
    oracle_infusion_by_claim,
    oracle_mppr,
    oracle_mue,
    oracle_not_measurable,
    oracle_ptp,
    oracle_sos,
    oracle_therapy,
)

LOCAL_LOGIN_EMAIL = "synthetic.local@example.com"
LOCAL_LOGIN_PASSWORD = "synthetic-local-only"
SOURCE_SYSTEM = "SYNTHETIC_PAYER_V1"
WINDOW_INCLUSIVE_END = date(2026, 9, 30)

POLICY_FACTS: Dict[str, Dict[str, Any]] = {
    "mppr": {"name": "Multiple procedure payment reduction", "codes": ["27447", "64483"], "execution": "SYNTHETIC_SIMULATION"},
    "sos": {"name": "Imaging site of service", "codes": ["72148"], "execution": "SYNTHETIC_SIMULATION"},
    "ptp": {"name": "Procedure-to-procedure edit", "codes": ["70553", "70551"], "execution": "SYNTHETIC_SIMULATION"},
    "mue": {"name": "Unit cap (demo cap 4, not a CMS MUE)", "codes": ["97110"], "execution": "SYNTHETIC_SIMULATION"},
    "therapy": {"name": "Outpatient therapy coverage", "codes": ["97110"], "execution": "SYNTHETIC_SIMULATION"},
    "infusion": {"name": "Infusion site of care", "codes": ["96413"], "execution": "SYNTHETIC_SIMULATION"},
    "mri": {"name": "Lumbar MRI prior authorization", "codes": ["72148"], "execution": "NOT_MEASURABLE"},
    "ncd": {"name": "NCD 220.2 study", "codes": ["70551"], "execution": "NOT_MEASURABLE"},
    "lcd": {"name": "LCD L34425 orbit, face, and neck study", "codes": ["70540"], "execution": "NOT_MEASURABLE"},
}

PAYMENT_ORACLES = {
    "mppr_favorable": lambda lines: oracle_mppr(lines, 0.5),
    "sos_policy": lambda lines: oracle_sos(lines, 0.8),
    "sos_neutral": lambda lines: oracle_sos(lines, 1.0),
    "sos_adverse": lambda lines: oracle_sos(lines, 1.1),
    "ptp": lambda lines: oracle_ptp(lines),
    "mue": lambda lines: oracle_mue(lines),
    "therapy": lambda lines: oracle_therapy(lines),
    "infusion": lambda lines: oracle_infusion_by_claim(lines),
}


def assert_disposable_database(url: str) -> None:
    lowered = (url or "").lower()
    if "55434" not in lowered or "synthetic_payer" not in lowered:
        raise RuntimeError("Refusing a database that is not the disposable synthetic payer database on port 55434")
    if "azure" in lowered or "database.windows.net" in lowered:
        raise RuntimeError("Refusing a cloud database")


def assess_realism(population: Dict[str, Any], lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Say what the generated file is. Do not treat it as a full payer extract."""
    lives = len(population["members"])
    by_cohort = Counter(row["cohort"] for row in population["members"])
    by_policy = Counter(row["policy_key"] for row in lines)
    by_status = Counter(row["line_status"] for row in lines)
    days_by_member: Dict[str, int] = {}
    for row in population["coverage"]:
        start = date.fromisoformat(row["start_date"])
        end = date.fromisoformat(row["end_date"])
        days_by_member[row["member_id"]] = days_by_member.get(row["member_id"], 0) + (end - start).days
    day_values = list(days_by_member.values())
    mean_days = sum(day_values) / len(day_values) if day_values else 0
    users = lives - by_cohort.get("none", 0)
    return {
        "covered_lives": lives,
        "reference_date": REFERENCE_DATE.isoformat(),
        "reference_enrolled": sum(1 for row in population["members"] if row["reference_enrolled"]),
        "window": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
        "window_is_half_open": True,
        "calendar_months_in_window": 33,
        "mean_enrolled_days": round(mean_days, 2),
        "mean_enrolled_days_as_30_day_months": round(mean_days / 30, 2),
        "claim_file_role": "policy_specific_extract_plus_one_background_office_visit",
        "comprehensive_medical_file": False,
        "pharmacy_file": False,
        "zero_claim_members": by_cohort.get("none", 0),
        "zero_claim_prevalence": round(by_cohort.get("none", 0) / lives, 4) if lives else None,
        "using_members": users,
        "claim_rows": len(lines),
        "active_claim_rows": by_status.get("ACTIVE", 0),
        "lines_per_using_member": round(len(lines) / users, 3) if users else None,
        "lines_by_policy_key": dict(by_policy),
        "members_by_cohort": dict(by_cohort),
        "evidence_informed_distributions": [],
        "synthetic_assumptions": [
            "Cohort is index modulo 100. Sixty percent of members are non-users by that rule.",
            "A using member gets one service day. MPPR and PTP have two lines that day. Background reversals add rows.",
            "Allowed amounts are fixture-scale synthetic prices, not a fee schedule.",
            "Coinsurance is 0.20. Deductible and pharmacy benefit are not simulated.",
            "Partial months use SYNTHETIC_PARTIAL_MONTH_V1.",
            "No cited commercial benchmark sets the claim frequency.",
        ],
    }


def _claim_payload(line: Mapping[str, Any], in_network: Dict[str, bool]) -> Dict[str, Any]:
    extras = {
        "policy_key": line.get("policy_key"),
        "line_status": line.get("line_status"),
        "modifier": line.get("modifier"),
        "role": line.get("role"),
        "site": line.get("site"),
        "allowed_per_unit": line.get("allowed_per_unit"),
        "medically_necessary_units": line.get("medically_necessary_units"),
        "anatomical_region": line.get("anatomical_region"),
        "auth_status": line.get("auth_status"),
        "code_authority": line.get("code_authority"),
        "evidence_class": line.get("evidence_class"),
    }
    diagnosis = line.get("diagnosis")
    return {
        "claim_id": line["claim_id"],
        "claim_line_id": line["claim_line_id"],
        "member_id": line["member_id"],
        "provider_id": line["provider_id"],
        "service_date": line["service_date"],
        "lob": "COMMERCIAL",
        "market": "SYNTHETIC",
        "cpt_code": line["cpt_code"],
        "icd10_diagnosis_codes": [diagnosis] if diagnosis else None,
        "service_category": str(line.get("policy_key") or "OTHER"),
        "place_of_service": str(line.get("place_of_service") or "11"),
        "units": line.get("units") or 1,
        "allowed_amount": line["allowed_amount"],
        "paid_amount": line["paid_amount"],
        "member_cost_share": line["member_cost_share"],
        "in_network": in_network.get(line["provider_id"], True),
        "requires_prior_auth": line.get("policy_key") in {"mri", "ncd", "lcd"},
        "prior_auth_approved": None,
        "facility_type": line.get("site"),
        "record_hash": json.dumps(extras, separators=(",", ":")),
    }


def _lines_from_database(db: Session, tenant_id: UUID) -> List[Dict[str, Any]]:
    rows = db.query(ClaimsLineDB).filter(ClaimsLineDB.tenant_id == tenant_id).all()
    loaded = []
    for row in rows:
        extra = json.loads(row.record_hash or "{}")
        loaded.append(
            {
                "member_id": row.member_id,
                "provider_id": row.provider_id,
                "claim_id": row.claim_id,
                "claim_line_id": row.claim_line_id,
                "cpt_code": row.cpt_code,
                "service_date": row.service_date.isoformat(),
                "allowed_amount": float(row.allowed_amount),
                "paid_amount": float(row.paid_amount),
                "member_cost_share": float(row.member_cost_share),
                "units": float(row.units),
                "place_of_service": row.place_of_service,
                **extra,
            }
        )
    return loaded


def _active(lines: List[Mapping[str, Any]], key: str) -> List[Mapping[str, Any]]:
    return [row for row in lines if row.get("policy_key") == key and row.get("line_status") == "ACTIVE"]


def _cohort_money(lines: List[Mapping[str, Any]]) -> Dict[str, Any]:
    allowed = round(sum(float(row["allowed_amount"]) for row in lines), 2)
    paid = round(sum(float(row["paid_amount"]) for row in lines), 2)
    share = round(sum(float(row["member_cost_share"]) for row in lines), 2)
    return {
        "active_lines": len(lines),
        "total_allowed": allowed,
        "total_plan_paid": paid,
        "total_member_cost_share": share,
        "allowed_equals_plan_paid_plus_share": abs(allowed - paid - share) < 0.05,
    }


def _seed_access(db: Session) -> None:
    tenant = db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()
    if tenant is None:
        db.add(Tenant(id=DEFAULT_TENANT_ID, name="Synthetic payer local", domain="synthetic.local"))
        db.commit()
    user = db.query(User).filter(User.email == LOCAL_LOGIN_EMAIL, User.tenant_id == DEFAULT_TENANT_ID).first()
    if user is None:
        user = User(
            id=uuid4(),
            tenant_id=DEFAULT_TENANT_ID,
            email=LOCAL_LOGIN_EMAIL,
            full_name="Synthetic local",
            is_active="true",
            auth_source="local",
            password_hash=hash_password(LOCAL_LOGIN_PASSWORD),
        )
        db.add(user)
        db.commit()
        db.execute(user_roles.insert().values(user_id=user.id, role="POLICY_ADMIN"))
        db.commit()


def _seed_policies(db: Session) -> None:
    for spec in POLICIES:
        facts = POLICY_FACTS[spec["key"]]
        if db.query(Policy).filter(Policy.id == UUID(spec["policy_id"])).first():
            continue
        metadata = {
            "document_id": spec["document_id"],
            "policy_key": spec["key"],
            "operational_activation": "PROHIBITED",
            "execution": facts["execution"],
            "code_authority": "CANDIDATE_NOT_APPROVED",
            "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
            "scope": {"procedure_codes": facts["codes"], "lob": ["COMMERCIAL"]},
        }
        db.add(
            Policy(
                id=UUID(spec["policy_id"]),
                tenant_id=DEFAULT_TENANT_ID,
                name=facts["name"],
                policy_type="PAYMENT_POLICY" if facts["execution"] == "SYNTHETIC_SIMULATION" else "CLINICAL_POLICY",
                description=(
                    f"{spec['document_id']}. Operational activation prohibited. "
                    "Synthetic illustration. Codes are candidates, not approved includes."
                ),
                status="ACTIVE",
                policy_metadata_json=metadata,
            )
        )
    db.commit()


def _policy_view(spec: Mapping[str, str]) -> Dict[str, Any]:
    facts = POLICY_FACTS[spec["key"]]
    metadata = {
        "document_id": spec["document_id"],
        "policy_key": spec["key"],
        "scope": {"procedure_codes": facts["codes"], "lob": ["COMMERCIAL"]},
        "operational_activation": "PROHIBITED",
        "execution": facts["execution"],
    }
    return {
        "id": spec["policy_id"],
        "name": facts["name"],
        "scope": metadata["scope"],
        "policy_metadata_json": metadata,
    }


def integrate_synthetic_payer(db: Session, lives: int, seed: int = SEED) -> Dict[str, Any]:
    """Generate, load, and calculate. The caller owns the disposable database."""
    started = time.perf_counter()
    clear_enrollment_cache()
    population = generate_population(lives, seed)
    lines = generate_events(population, seed)
    generated_at = time.perf_counter()
    realism = assess_realism(population, lines)
    ingestion_id = uuid4()
    repo = CanonicalDataRepository(db)
    _seed_access(db)
    _seed_policies(db)

    in_network = {row["provider_id"]: row["network_status"] != "OUT" for row in population["providers"]}
    claim_rows = [_claim_payload(line, in_network) for line in lines]
    loaded_claims = 0
    for offset in range(0, len(claim_rows), 2000):
        loaded_claims += repo.bulk_insert_claims_lines(
            DEFAULT_TENANT_ID,
            claim_rows[offset:offset + 2000],
            SOURCE_SYSTEM,
            f"synthetic-payer-{seed}",
            ingestion_id,
        )
    from uepi_api.models.canonical_data import ProviderRecordDB

    for provider in population["providers"]:
        db.add(
            ProviderRecordDB(
                tenant_id=DEFAULT_TENANT_ID,
                provider_id=provider["provider_id"],
                provider_type="SYNTHETIC",
                market="SYNTHETIC",
                network_status=provider["network_status"],
                effective_date=WINDOW_START,
                source_system=SOURCE_SYSTEM,
                source_file_id=f"synthetic-payer-{seed}",
                ingestion_id=ingestion_id,
            )
        )
    db.commit()

    enrollment_count = 0
    batch: List[Dict[str, Any]] = []
    for row in iter_enrollment_month_rows(population):
        batch.append(row)
        if len(batch) >= 2000:
            enrollment_count += repo.bulk_insert_enrollment_records(
                DEFAULT_TENANT_ID, batch, SOURCE_SYSTEM, f"synthetic-payer-{seed}", ingestion_id
            )
            batch = []
    if batch:
        enrollment_count += repo.bulk_insert_enrollment_records(
            DEFAULT_TENANT_ID, batch, SOURCE_SYSTEM, f"synthetic-payer-{seed}", ingestion_id
        )
    loaded_at = time.perf_counter()

    exposure = measured_enrollment_member_months(db, DEFAULT_TENANT_ID, WINDOW_START, WINDOW_INCLUSIVE_END)
    baseline_started = time.perf_counter()
    general = compute_general_baseline_from_database(DEFAULT_TENANT_ID, WINDOW_START, WINDOW_INCLUSIVE_END, db)
    general["active_or_replacement_rows"] = sum(1 for row in lines if row["line_status"] != "REVERSAL")
    general["reversal_rows_included_in_claim_count"] = sum(1 for row in lines if row["line_status"] == "REVERSAL")
    general["evidence_class"] = "SYNTHETIC_ILLUSTRATIVE"
    create_baseline(
        DEFAULT_TENANT_ID,
        {
            "baseline_id": f"synthetic-general-{seed}-{lives}",
            "baseline_type": "FIXED",
            "window_start_date": datetime(2024, 1, 1).isoformat(),
            "window_end_date": datetime(2026, 9, 30).isoformat(),
            "baseline_metrics": general,
            "computed_by": SOURCE_SYSTEM,
            "refresh_reason": "SYNTHETIC_LOAD",
        },
    )

    general_baseline_at = time.perf_counter()
    stored_lines = _lines_from_database(db, DEFAULT_TENANT_ID)
    engines = simulate_payment_population(stored_lines)
    simulated_at = time.perf_counter()
    journeys = []
    mismatches = []
    oracle_seconds = 0.0
    observation_seconds = 0.0
    policy_baseline_seconds = 0.0
    for spec in POLICIES:
        key = spec["key"]
        facts = POLICY_FACTS[key]
        cohort = _active(stored_lines, key)
        money = _cohort_money(cohort)
        policy_baseline_started = time.perf_counter()
        stock = compute_policy_specific_baseline_from_database(
            DEFAULT_TENANT_ID,
            UUID(spec["policy_id"]),
            WINDOW_START,
            WINDOW_INCLUSIVE_END,
            {"procedure_codes": facts["codes"], "lob": "COMMERCIAL"},
            db,
            policy=_policy_view(spec),
        )
        policy_baseline_seconds += time.perf_counter() - policy_baseline_started
        member_months = float(exposure or 0)
        metrics = {
            **money,
            "member_months": member_months,
            "denominator_basis": "ENROLLMENT",
            "enrolled_rate_status": "MEASURED" if member_months > 0 else "NOT_MEASURABLE",
            "paid_pmpm_target": (money["total_plan_paid"] / member_months) if member_months else None,
            "allowed_pmpm_target": (money["total_allowed"] / member_months) if member_months else None,
            "cost_pmpm_meaning": "PAID",
            "exposure_method": "ENROLLMENT_PARTIAL_MONTH",
            "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
            "code_authority": "CANDIDATE_NOT_APPROVED",
            "operational_activation": "PROHIBITED",
            "execution": facts["execution"],
            "cpt_filter_baseline": {
                "total_claims": stock.get("total_claims"),
                "total_allowed": stock.get("total_allowed"),
                "total_paid": stock.get("total_paid"),
                "note": "CPT filter can include another policy that shares a candidate code.",
            },
        }
        cpt_claims = stock.get("total_claims")
        if cpt_claims is not None and int(cpt_claims) != money["active_lines"]:
            metrics["cpt_overlap"] = True
            mismatches.append((key, "policy_scope_lines", int(cpt_claims), money["active_lines"]))
        comparisons: Dict[str, Any] = {"vs_baseline": {"baseline_measures": {
            "allowed": money["total_allowed"],
            "plan_paid": money["total_plan_paid"],
            "member_months": member_months,
        }}}
        oracle_result: Dict[str, Any]
        if facts["execution"] == "SYNTHETIC_SIMULATION":
            engine_key = "mppr_favorable" if key == "mppr" else "sos_policy" if key == "sos" else key
            engine_totals = engines[engine_key]["totals"]
            oracle_lines = _active(stored_lines, key)
            oracle_fn = PAYMENT_ORACLES[engine_key]
            oracle_started = time.perf_counter()
            oracle_result = oracle_fn(oracle_lines)
            oracle_seconds += time.perf_counter() - oracle_started
            for field in ("baseline_paid", "post_policy_paid", "payment_impact"):
                if abs(float(engine_totals[field]) - float(oracle_result[field])) >= 0.02:
                    mismatches.append((key, field, engine_totals[field], oracle_result[field]))
            impact = float(engine_totals["payment_impact"])
            pmpm_change = (float(engine_totals["post_policy_paid"]) - float(engine_totals["baseline_paid"])) / member_months if member_months else None
            metrics.update(
                {
                    "simulation_baseline_allowed": float(engine_totals["baseline_paid"]),
                    "simulation_post_allowed": float(engine_totals["post_policy_paid"]),
                    "payment_impact_dollars": impact,
                    "result_label": "Synthetic payment simulation. Not adjudication and not real-world savings.",
                    "volume_held_constant": True,
                }
            )
            comparisons["vs_baseline"].update(
                {
                    "cost_change": pmpm_change,
                    "cost_change_pmpm": pmpm_change,
                    "cost_change_kind": "simulated_allowed_difference_per_enrolled_member_month",
                    "cost_change_meaning": "Change in simulated allowed dollars per enrolled member-month.",
                    "payment_impact_dollars": impact,
                }
            )
        else:
            oracle_started = time.perf_counter()
            oracle_result = oracle_not_measurable(key, money["active_lines"], "No outcome engine. Source events only.")
            oracle_seconds += time.perf_counter() - oracle_started
            metrics["outcome_status"] = "NOT_MEASURABLE"
            metrics["result_label"] = "Not measurable. No population outcome is shown."
            if oracle_result.get("payment_impact") is not None:
                mismatches.append((key, "payment_impact", None, oracle_result.get("payment_impact")))
        observation_started = time.perf_counter()
        observation = create_observation(
            DEFAULT_TENANT_ID,
            {
                "policy_id": spec["policy_id"],
                "observation_type": "AD_HOC",
                "observation_period_start": "2024-01-01T00:00:00",
                "observation_period_end": "2026-09-30T00:00:00",
                "metrics": metrics,
                "comparisons": comparisons,
                "observed_measures": {
                    "active_lines": money["active_lines"],
                    "execution": facts["execution"],
                },
            },
        )
        observation_seconds += time.perf_counter() - observation_started
        create_baseline(
            DEFAULT_TENANT_ID,
            {
                "baseline_id": f"synthetic-{key}-{seed}-{lives}",
                "baseline_type": "FIXED",
                "policy_id": spec["policy_id"],
                "window_start_date": datetime(2024, 1, 1).isoformat(),
                "window_end_date": datetime(2026, 9, 30).isoformat(),
                "baseline_metrics": metrics,
                "computed_by": SOURCE_SYSTEM,
                "refresh_reason": "SYNTHETIC_LOAD",
            },
        )
        journeys.append(
            {
                "policy_key": key,
                "policy_id": spec["policy_id"],
                "name": facts["name"],
                "execution": facts["execution"],
                "active_lines": money["active_lines"],
                "plan_paid": money["total_plan_paid"],
                "allowed": money["total_allowed"],
                "payment_impact_dollars": metrics.get("payment_impact_dollars"),
                "outcome_status": metrics.get("outcome_status"),
                "verdict_status": observation.get("verdict_status"),
                "observation_id": observation.get("observation_id"),
                "cpt_overlap": bool(metrics.get("cpt_overlap")),
                "operational_activation": "PROHIBITED",
            }
        )
    if mismatches:
        raise RuntimeError(f"Application engines did not match the oracle: {mismatches}")
    return {
        "lives": lives,
        "seed": seed,
        "load_seconds": round(loaded_at - generated_at, 3),
        "generation_seconds": round(generated_at - started, 3),
        "baseline_seconds": round((general_baseline_at - baseline_started) + policy_baseline_seconds, 3),
        "simulation_seconds": round(simulated_at - general_baseline_at, 3),
        "observation_seconds": round(observation_seconds, 3),
        "oracle_seconds": round(oracle_seconds, 3),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "claims_loaded": loaded_claims,
        "enrollment_rows": enrollment_count,
        "provider_rows": len(population["providers"]),
        "member_months": exposure,
        "general_baseline_member_months": general.get("member_months"),
        "general_denominator_basis": general.get("denominator_basis"),
        "realism": realism,
        "journeys": journeys,
        "engine_impacts": {name: engines[name]["totals"]["payment_impact"] for name in engines},
        "login_email": LOCAL_LOGIN_EMAIL,
    }
