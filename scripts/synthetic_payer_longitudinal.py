"""Build the longitudinal 500k database without touching the reference database.

Predictions are written before post-period claims are generated.
"""

from __future__ import annotations

import csv
import io
import json
import os
import resource
import sys
import time
import uuid
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "apps/api/src"), str(ROOT / "packages/common/src")]

DATABASE = "synthetic_payer_500k_longitudinal"
URL = f"postgresql+psycopg2://synthetic:synthetic@127.0.0.1:55434/{DATABASE}"
ADMIN = "postgresql+psycopg2://synthetic:synthetic@127.0.0.1:55434/synthetic_payer"
os.environ["DATABASE_URL"] = URL
os.environ["PG_STATEMENT_TIMEOUT_MS"] = "600000"

TENANT = "00000000-0000-0000-0000-000000000001"
PRE_END = date(2025, 6, 30)
POST_START = date(2025, 7, 1)
POST_END = date(2026, 9, 30)


def main() -> None:
    from sqlalchemy import create_engine, text

    from uepi_api.services.synthetic_payer_integration import assert_disposable_database

    assert_disposable_database(URL)
    if DATABASE in {"synthetic_payer", "synthetic_payer_500k"}:
        raise SystemExit("Refusing to overwrite a reference database")
    started = time.perf_counter()
    admin = create_engine(ADMIN, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": DATABASE}).scalar()
        if exists:
            conn.execute(text(f'DROP DATABASE "{DATABASE}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{DATABASE}"'))
    admin.dispose()

    from uepi_api.config import get_settings
    import uepi_api.database as database_module
    from uepi_api.database import SessionLocal, init_db

    get_settings.cache_clear()
    database_module._engine = None
    database_module._SessionLocal = None
    init_db()
    print("schema ready", round(time.perf_counter() - started, 1), flush=True)

    from uepi_common.synthetic_payer.generate import SEED, generate_population
    from uepi_common.synthetic_payer.longitudinal import (
        ASSUMPTIONS,
        EFFECTIVE_LABEL,
        GENERATOR_VERSION,
        HYPOTHETICAL_EFFECTIVE,
        generate_period_claims,
    )
    from uepi_common.synthetic_payer.enrollment_rows import iter_enrollment_month_rows

    population = generate_population(500_000, seed=SEED)
    pre_claims = generate_period_claims(population, "PRE", seed=SEED)
    print("pre claims", len(pre_claims), round(time.perf_counter() - started, 1), flush=True)
    ingestion = str(uuid.uuid4())
    _copy_reference(population, pre_claims, ingestion, SEED)
    print("pre loaded", round(time.perf_counter() - started, 1), flush=True)

    db = SessionLocal()
    try:
        _seed(db)
        freeze = _freeze_predictions(db, SEED)
    finally:
        db.close()
    freeze_path = ROOT / "data" / "synthetic" / "longitudinal_prediction_freeze.json"
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.write_text(json.dumps(freeze, indent=2))
    print("predictions frozen", round(time.perf_counter() - started, 1), flush=True)

    post_claims = generate_period_claims(population, "POST", seed=SEED)
    print("post claims", len(post_claims), round(time.perf_counter() - started, 1), flush=True)
    _copy_claims(post_claims, ingestion, SEED, "post")
    db = SessionLocal()
    try:
        observed = _observe(db, freeze)
        catalog = _catalog_count()
    finally:
        db.close()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    report = {
        "database": DATABASE,
        "reference_database_untouched": "synthetic_payer_500k",
        "generator": GENERATOR_VERSION,
        "seed": SEED,
        "effective_label": EFFECTIVE_LABEL,
        "hypothetical_effective": HYPOTHETICAL_EFFECTIVE.isoformat(),
        "assumptions": ASSUMPTIONS,
        "members": 500000,
        "pre_claims": len(pre_claims),
        "post_claims": len(post_claims),
        "pharmacy_pre": sum(1 for row in pre_claims if row["pharmacy"]),
        "pharmacy_post": sum(1 for row in post_claims if row["pharmacy"]),
        "freeze": freeze,
        "observed": observed,
        "catalog_definition_packages": catalog,
        "elapsed_seconds": round(time.perf_counter() - started, 1),
        "peak_rss_mb": round(usage.ru_maxrss / (1024 * 1024), 1),
        "staging_loaded": False,
    }
    out = ROOT / "data" / "synthetic" / "longitudinal_500000.json"
    out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps({k: report[k] for k in ("database", "pre_claims", "post_claims", "elapsed_seconds", "peak_rss_mb")}, indent=2))


def _copy_reference(population, claims, ingestion, seed) -> None:
    import psycopg2

    conn = psycopg2.connect("host=127.0.0.1 port=55434 dbname=synthetic_payer_500k_longitudinal user=synthetic password=synthetic")
    cur = conn.cursor()
    _copy_providers(cur, population, ingestion, seed)
    _copy_enrollment(cur, population, ingestion, seed)
    conn.commit()
    _copy_claims(claims, ingestion, seed, "pre", conn)
    conn.close()


def _copy_providers(cur, population, ingestion, seed) -> None:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter="\t", lineterminator="\n")
    for row in population["providers"]:
        writer.writerow([
            str(uuid.uuid4()), TENANT, row["provider_id"], "SYNTHETIC", "SYNTHETIC", row["network_status"],
            "2024-01-01", "SYNTHETIC_LONGITUDINAL_V1", f"synthetic-longitudinal-{seed}", ingestion,
            datetime.utcnow().isoformat(sep=" "), datetime.utcnow().isoformat(sep=" "),
        ])
    buf.seek(0)
    cur.copy_expert(
        """COPY provider_records (id, tenant_id, provider_id, provider_type, market, network_status, effective_date, source_system, source_file_id, ingestion_id, created_at, updated_at) FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N')""",
        buf,
    )


def _copy_enrollment(cur, population, ingestion, seed) -> None:
    from uepi_common.synthetic_payer.enrollment_rows import iter_enrollment_month_rows

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter="\t", lineterminator="\n")
    count = 0
    now = datetime.utcnow().isoformat(sep=" ")
    for row in iter_enrollment_month_rows(population):
        writer.writerow([
            str(uuid.uuid4()), TENANT, row["member_id"], row["enrollment_month"], row["lob"], row["market"],
            row["age_band"], row["gender"], row["risk_score"], row["network_tier"], "t" if row["enrolled_flag"] else "f",
            row["enrollment_start_date"], row["enrollment_end_date"], row["product_type"], row["segment"],
            "SYNTHETIC_LONGITUDINAL_V1", f"synthetic-longitudinal-{seed}", ingestion, now, now,
        ])
        count += 1
        if count % 500000 == 0:
            buf.seek(0)
            cur.copy_expert(
                """COPY enrollment_records (id, tenant_id, member_id, enrollment_month, lob, market, age_band, gender, risk_score, network_tier, enrolled_flag, enrollment_start_date, enrollment_end_date, product_type, segment, source_system, source_file_id, ingestion_id, created_at, updated_at) FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N')""",
                buf,
            )
            buf = io.StringIO()
            writer = csv.writer(buf, delimiter="\t", lineterminator="\n")
            print("enrollment", count, flush=True)
    if buf.tell():
        buf.seek(0)
        cur.copy_expert(
            """COPY enrollment_records (id, tenant_id, member_id, enrollment_month, lob, market, age_band, gender, risk_score, network_tier, enrolled_flag, enrollment_start_date, enrollment_end_date, product_type, segment, source_system, source_file_id, ingestion_id, created_at, updated_at) FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N')""",
            buf,
        )
    print("enrollment done", count, flush=True)


def _copy_claims(claims, ingestion, seed, label, conn=None) -> None:
    import psycopg2

    own = conn is None
    if own:
        conn = psycopg2.connect("host=127.0.0.1 port=55434 dbname=synthetic_payer_500k_longitudinal user=synthetic password=synthetic")
    cur = conn.cursor()
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter="\t", lineterminator="\n")
    now = datetime.utcnow().isoformat(sep=" ")
    for row in claims:
        extras = {
            "policy_key": row["policy_key"],
            "period": row["period"],
            "line_status": row["line_status"],
            "role": row.get("role"),
            "modifier": row.get("modifier"),
            "site": row.get("site"),
            "allowed_per_unit": row.get("allowed_per_unit"),
            "medically_necessary_units": row.get("medically_necessary_units"),
            "ndc": row.get("ndc"),
            "evidence_class": row["evidence_class"],
            "effective_date_label": row["effective_date_label"],
        }
        writer.writerow([
            str(uuid.uuid4()), TENANT, row["claim_id"], row["claim_line_id"], row["member_id"], row["provider_id"],
            row["service_date"], row["adjudication_date"], "COMMERCIAL", "SYNTHETIC", row.get("cpt_code") or "\\N",
            row["service_category"], row["place_of_service"], row["units"], f"{row['allowed_amount']:.2f}",
            f"{row['paid_amount']:.2f}", f"{row['member_cost_share']:.2f}", "t",
            "t" if row["policy_key"] in {"mri", "ncd", "lcd"} else "f",
            row.get("site") or "\\N", "SYNTHETIC_LONGITUDINAL_V1", f"synthetic-longitudinal-{seed}-{label}",
            ingestion, json.dumps(extras, separators=(",", ":")), now, now,
        ])
    buf.seek(0)
    cur.copy_expert(
        """COPY claims_lines (
            id, tenant_id, claim_id, claim_line_id, member_id, provider_id, service_date, adjudication_date,
            lob, market, cpt_code, service_category, place_of_service, units, allowed_amount, paid_amount,
            member_cost_share, in_network, requires_prior_auth, facility_type, source_system, source_file_id,
            ingestion_id, record_hash, created_at, updated_at
        ) FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N')""",
        buf,
    )
    conn.commit()
    if own:
        conn.close()


def _seed(db) -> None:
    from uepi_api.services.synthetic_payer_integration import _seed_access, _seed_policies

    _seed_access(db)
    _seed_policies(db)


def _freeze_predictions(db, seed: int) -> dict:
    from uuid import UUID

    from sqlalchemy import text

    from uepi_api.models.predicted_impact import PolicyPredictedImpact
    from uepi_api.services.database_baseline_computation import (
        compute_general_baseline_from_database,
        compute_policy_specific_baseline_from_database,
    )
    from uepi_api.services.enrollment_exposure import measured_enrollment_member_months
    from uepi_api.services.synthetic_lifecycle import build_payment_lifecycle
    from uepi_api.services.synthetic_payer_integration import POLICY_FACTS
    from uepi_api.storage_auth import DEFAULT_TENANT_ID
    from uepi_api.storage_baselines import create_baseline
    from uepi_common.synthetic_payer.generate import POLICIES, WINDOW_START

    pre_end = PRE_END
    general = compute_general_baseline_from_database(DEFAULT_TENANT_ID, WINDOW_START, pre_end, db)
    exposure = measured_enrollment_member_months(db, DEFAULT_TENANT_ID, WINDOW_START, pre_end)
    create_baseline(DEFAULT_TENANT_ID, {
        "baseline_id": f"longitudinal-pre-{seed}",
        "baseline_type": "FIXED",
        "window_start_date": "2024-01-01T00:00:00",
        "window_end_date": "2025-06-30T00:00:00",
        "baseline_metrics": general,
        "computed_by": "SYNTHETIC_LONGITUDINAL_V1",
        "refresh_reason": "PRE_POLICY_ONLY",
    })
    leaked = db.execute(text("SELECT COUNT(*) FROM claims_lines WHERE service_date >= :cut"), {"cut": POST_START}).scalar()
    if leaked:
        raise RuntimeError("Post-period claims were visible before prediction freeze")
    frozen = []
    for spec in POLICIES:
        key = spec["key"]
        facts = POLICY_FACTS[key]
        lines = _load_lines(db, key, "PRE")
        stock = compute_policy_specific_baseline_from_database(
            DEFAULT_TENANT_ID, UUID(spec["policy_id"]), WINDOW_START, pre_end,
            {"procedure_codes": facts["codes"], "lob": ["COMMERCIAL"]}, db,
            policy={"policy_metadata_json": {"policy_key": key}},
        )
        create_baseline(DEFAULT_TENANT_ID, {
            "baseline_id": f"longitudinal-pre-{key}-{seed}",
            "baseline_type": "FIXED",
            "policy_id": spec["policy_id"],
            "window_start_date": "2024-01-01T00:00:00",
            "window_end_date": "2025-06-30T00:00:00",
            "baseline_metrics": {"policy_key": key, "pre_lines": len(lines), "application_baseline_claims": stock.get("total_claims")},
            "computed_by": "SYNTHETIC_LONGITUDINAL_V1",
            "refresh_reason": "PRE_POLICY_ONLY",
        })
        if facts["execution"] != "SYNTHETIC_SIMULATION":
            frozen.append({"policy_key": key, "status": "NOT_MEASURABLE", "pre_lines": len(lines), "predicted_allowed": None, "predicted_impact": None})
            continue
        built = build_payment_lifecycle(key, lines)
        row = PolicyPredictedImpact(
            tenant_id=DEFAULT_TENANT_ID,
            policy_id=UUID(spec["policy_id"]),
            metrics_json={"metrics": {**built["prediction"], "cutoff": "2025-06-30", "inputs": "PRE claims only", "real_world_savings": False}},
            model_version="synthetic-longitudinal-v1",
            confidence=None,
            predicted_at=datetime(2026, 11, 6, 13, 0, 0),
            prediction_method="SYNTHETIC_PAYMENT_ENGINE_PRE_FREEZE",
        )
        db.add(row)
        frozen.append({
            "policy_key": key,
            "status": "FROZEN",
            "pre_lines": len(lines),
            "predicted_allowed": built["prediction"]["predicted_allowed"],
            "predicted_impact": built["prediction"]["payment_impact_dollars"],
            "oracle_match": built["oracle_match"],
        })
    db.commit()
    return {"cutoff": "2025-06-30", "post_claims_present": 0, "exposure_pre": exposure, "general": {k: general.get(k) for k in ("total_claims", "total_allowed", "total_paid", "member_months")}, "policies": frozen}


def _load_lines(db, policy_key: str, period: str):
    from sqlalchemy import text

    rows = db.execute(
        text(
            """
            SELECT claim_id, claim_line_id, member_id, cpt_code, service_date, allowed_amount, paid_amount,
                   member_cost_share, units, place_of_service, record_hash
            FROM claims_lines
            WHERE tenant_id = :tenant AND service_category = :key
              AND record_hash LIKE :period
            """
        ),
        {"tenant": TENANT, "key": policy_key, "period": f'%"period":"{period}"%'},
    ).mappings().all()
    loaded = []
    for row in rows:
        extra = json.loads(row["record_hash"] or "{}")
        extra = {key: value for key, value in extra.items() if value is not None}
        if extra.get("period") != period or extra.get("line_status") != "ACTIVE":
            continue
        loaded.append({
            "claim_id": row["claim_id"],
            "claim_line_id": row["claim_line_id"],
            "member_id": row["member_id"],
            "cpt_code": row["cpt_code"],
            "service_date": row["service_date"].isoformat(),
            "allowed_amount": float(row["allowed_amount"]),
            "paid_amount": float(row["paid_amount"]),
            "member_cost_share": float(row["member_cost_share"]),
            "units": float(row["units"]),
            "place_of_service": row["place_of_service"],
            **extra,
        })
    return loaded


def _observe(db, freeze: dict) -> list:
    from uuid import UUID

    from uepi_api.models.audit import AuditEvent
    from uepi_api.models.observation import Observation
    from uepi_api.services.enrollment_exposure import measured_enrollment_member_months
    from uepi_api.services.synthetic_lifecycle import build_payment_lifecycle
    from uepi_api.storage_auth import DEFAULT_TENANT_ID
    from uepi_common.synthetic_payer.generate import POLICIES

    post_exposure = measured_enrollment_member_months(db, DEFAULT_TENANT_ID, POST_START, POST_END)
    frozen_by_key = {row["policy_key"]: row for row in freeze["policies"]}
    results = []
    for spec in POLICIES:
        key = spec["key"]
        lines = _load_lines(db, key, "POST")
        prior = frozen_by_key[key]
        if prior["status"] != "FROZEN":
            payload = {
                "policy_key": key,
                "status": "NOT_MEASURABLE",
                "post_lines": len(lines),
                "pre_lines": prior["pre_lines"],
                "predicted_impact": None,
                "observed_impact": None,
                "difference": None,
            }
        else:
            built = build_payment_lifecycle(key, lines)
            observed_impact = built["prediction"]["payment_impact_dollars"]
            difference = round(observed_impact - prior["predicted_impact"], 2)
            gross = round(sum(row["allowed_amount"] for row in lines), 2)
            pre_gross_rate = None
            payload = {
                "policy_key": key,
                "status": "OBSERVED_FROM_POST_CLAIMS",
                "post_lines": len(lines),
                "pre_lines": prior["pre_lines"],
                "predicted_impact": prior["predicted_impact"],
                "predicted_allowed": prior["predicted_allowed"],
                "observed_impact": observed_impact,
                "observed_allowed": built["prediction"]["predicted_allowed"],
                "difference": difference,
                "forced_equal": False,
                "oracle_match": built["oracle_match"],
                "post_gross_allowed": gross,
            }
            per_mm = None if not post_exposure else (built["observation"]["allowed_difference"] / post_exposure)
            db.add(Observation(
                tenant_id=DEFAULT_TENANT_ID,
                observation_id=f"longitudinal-post-{key}",
                policy_id=UUID(spec["policy_id"]),
                observation_type="POST_PERIOD",
                observation_period_start=datetime(2025, 7, 1),
                observation_period_end=datetime(2026, 9, 30),
                metrics_json={
                    "denominator_basis": "ENROLLMENT",
                    "enrolled_rate_status": "MEASURED",
                    "member_months": post_exposure,
                    "outcome_status": "SYNTHETIC_OBSERVED",
                    "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
                },
                comparisons_json={
                    "vs_baseline": {
                        "cost_change": per_mm,
                        "cost_change_pmpm": per_mm,
                        "cost_change_kind": "observed_post_period_allowed_difference_per_enrolled_member_month",
                        "cost_change_meaning": "Post-period allowed after the payment rule, minus post-period gross allowed, per post-period enrolled member-month.",
                    },
                    "vs_predicted": {
                        "frozen_prediction_impact": prior["predicted_impact"],
                        "observed_impact": observed_impact,
                        "difference": difference,
                        "reconciliation_status": "MEASURED_DIFFERENCE",
                        "copied_from_prediction": False,
                        "real_world_evidence": False,
                    },
                },
                verdict_status="INCONCLUSIVE",
                verdict_reason="No policy endpoint contract is defined. A change in utilization or cost is not a verdict.",
                recommendation="Declare the required endpoints and their direction before scoring this policy.",
                verdict_rule_version="v1.1-endpoints",
                computed_at=datetime(2026, 11, 6, 14, 0, 0),
            ))
        if prior["status"] != "FROZEN":
            db.add(Observation(
                tenant_id=DEFAULT_TENANT_ID,
                observation_id=f"longitudinal-post-{key}",
                policy_id=UUID(spec["policy_id"]),
                observation_type="POST_PERIOD",
                observation_period_start=datetime(2025, 7, 1),
                observation_period_end=datetime(2026, 9, 30),
                metrics_json={"outcome_status": "NOT_MEASURABLE", "post_source_lines": len(lines), "evidence_class": "SYNTHETIC_ILLUSTRATIVE"},
                comparisons_json={"vs_predicted": {"reconciliation_status": "NOT_MEASURABLE", "copied_from_prediction": False}},
                verdict_status="INCONCLUSIVE",
                verdict_reason="No policy endpoint contract is defined. A population outcome is not measurable for this policy.",
                recommendation="Do not score a blocked clinical policy.",
                verdict_rule_version="v1.1-endpoints",
                computed_at=datetime(2026, 11, 6, 14, 0, 0),
            ))
        db.add(AuditEvent(
            tenant_id=DEFAULT_TENANT_ID,
            action="LIFECYCLE_STAGE",
            object_type="POLICY",
            object_id=UUID(spec["policy_id"]),
            diff_summary={"stage": "post_policy_observation", "status": payload["status"]},
            metadata_json={"worker": "synthetic_payer_longitudinal.py", "data_version": "synthetic-longitudinal-v1"},
        ))
        results.append(payload)
    db.commit()
    return results


def _catalog_count() -> int:
    root = ROOT / "docs" / "demo" / "bcbs-nc" / "policy_definitions" / "v1.2" / "catalog"
    return len(list(root.glob("*/*PACKAGE.json")))


def resume() -> None:
    """Finish observation after the load. Does not recreate the database."""
    from sqlalchemy.orm.attributes import flag_modified

    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import Policy
    from uepi_api.models.predicted_impact import PolicyPredictedImpact
    from uepi_api.services.synthetic_lifecycle import build_payment_lifecycle
    from uepi_api.storage_auth import DEFAULT_TENANT_ID
    from uepi_common.synthetic_payer.generate import POLICIES

    freeze_path = ROOT / "data" / "synthetic" / "longitudinal_prediction_freeze.json"
    freeze = json.loads(freeze_path.read_text())
    db = SessionLocal()
    try:
        lines = _load_lines(db, "mue", "PRE")
        built = build_payment_lifecycle("mue", lines)
        if not built["oracle_match"]:
            raise RuntimeError("MUE pre-period prediction still disagrees with the oracle")
        row = (
            db.query(PolicyPredictedImpact)
            .filter(PolicyPredictedImpact.policy_id == uuid.UUID(POLICIES[3]["policy_id"]))
            .one()
        )
        metrics = dict(row.metrics_json["metrics"])
        metrics["predicted_allowed"] = built["prediction"]["predicted_allowed"]
        metrics["payment_impact_dollars"] = built["prediction"]["payment_impact_dollars"]
        metrics["correction"] = "Null allowed_per_unit was omitted before observation. Pre-period lines only."
        row.metrics_json = {"metrics": metrics}
        flag_modified(row, "metrics_json")
        for item in freeze["policies"]:
            if item["policy_key"] == "mue":
                item["predicted_allowed"] = built["prediction"]["predicted_allowed"]
                item["predicted_impact"] = built["prediction"]["payment_impact_dollars"]
                item["oracle_match"] = True
                item["input_correction"] = "allowed_per_unit null key removed before observation"
        freeze_path.write_text(json.dumps(freeze, indent=2))
        nine = {spec["policy_id"] for spec in POLICIES}
        catalog_root = ROOT / "docs" / "demo" / "bcbs-nc" / "policy_definitions" / "v1.2" / "catalog"
        added = 0
        for package in sorted(catalog_root.glob("*/*PACKAGE.json")):
            policy_id = uuid.uuid5(uuid.NAMESPACE_URL, f"healthforesight-v1.2:{package.parent.name}")
            if str(policy_id) in nine or db.query(Policy.id).filter(Policy.id == policy_id).first():
                continue
            db.add(Policy(
                id=policy_id,
                tenant_id=DEFAULT_TENANT_ID,
                name=package.parent.name.replace("_", " "),
                policy_type="CATALOG_DEFINITION",
                description="v1.2 catalog definition. No execution engine is implemented for this policy.",
                status="ACTIVE",
                policy_metadata_json={
                    "definition_version": "v1.2",
                    "definition_path": str(package.relative_to(ROOT)),
                    "execution": "NOT_IMPLEMENTED",
                    "operational_activation": "PROHIBITED",
                    "evidence_class": "DEFINITION_ONLY",
                },
            ))
            added += 1
        db.commit()
        observed = _observe(db, freeze)
    finally:
        db.close()
    report = {
        "database": DATABASE,
        "reference_database_untouched": "synthetic_payer_500k",
        "freeze": freeze,
        "observed": observed,
        "catalog_policies_added": added,
        "staging_loaded": False,
        "staging_blocker": (
            "An isolated staging database would require a new Azure database or retargeting the existing "
            "hfleanstg apps. Neither is authorized. The existing lean-staging database was not changed."
        ),
    }
    out = ROOT / "data" / "synthetic" / "longitudinal_500000.json"
    out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(observed, indent=2, default=str))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "resume":
        resume()
    else:
        main()
