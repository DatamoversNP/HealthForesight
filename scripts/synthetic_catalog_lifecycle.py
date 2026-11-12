"""Lifecycle for the remaining catalog and clinical policies.

Predictions are a frozen continuation of the pre-period allowed rate.
Post-policy claims use a separate random stream and are not copied from the prediction.
Packages without a candidate code get a policy-tagged event and a null procedure code.
No procedure code is invented. What-if is not run.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import random
import sys
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "apps/api/src"), str(ROOT / "packages/common/src")]
os.environ["DATABASE_URL"] = "postgresql+psycopg2://synthetic:synthetic@127.0.0.1:55434/synthetic_payer_500k_longitudinal"
os.environ["PG_STATEMENT_TIMEOUT_MS"] = "600000"

TENANT = "00000000-0000-0000-0000-000000000001"
CATALOG = ROOT / "docs/demo/bcbs-nc/policy_definitions/v1.2/catalog"
CLINICAL = ("mri", "ncd", "lcd")


def main() -> None:
    from uepi_api.services.synthetic_payer_integration import assert_disposable_database

    assert_disposable_database(os.environ["DATABASE_URL"])
    from uepi_common.synthetic_payer.generate import SEED, WINDOW_END, WINDOW_START, generate_population, _money_split
    from uepi_common.synthetic_payer.longitudinal import HYPOTHETICAL_EFFECTIVE, _day

    population = generate_population(500_000, seed=SEED)
    intervals = {}
    for row in population["coverage"]:
        intervals.setdefault(row["member_id"], []).append(
            (datetime.fromisoformat(row["start_date"]).date(), datetime.fromisoformat(row["end_date"]).date())
        )
    members = population["members"]
    providers = [row["provider_id"] for row in population["providers"]]
    packages = _packages()
    print("packages", len(packages), flush=True)
    pre_totals = {}
    _generate_and_copy(packages, members, providers, intervals, "PRE", pre_totals, _day, WINDOW_START, HYPOTHETICAL_EFFECTIVE, _money_split)
    print("pre copied", sum(row["lines"] for row in pre_totals.values()), flush=True)
    freeze = _freeze(pre_totals)
    post_totals = {}
    _generate_and_copy(packages, members, providers, intervals, "POST", post_totals, _day, HYPOTHETICAL_EFFECTIVE, WINDOW_END, _money_split)
    print("post copied", sum(row["lines"] for row in post_totals.values()), flush=True)
    observed = _observe(freeze, post_totals)
    out = ROOT / "data" / "synthetic" / "catalog_lifecycle.json"
    out.write_text(json.dumps({"frozen": len(freeze), "observed": len(observed), "nonzero_differences": sum(1 for row in observed if row["difference"] not in (0, None))}, indent=2))
    print(out.read_text())


def _packages() -> list[dict]:
    found = []
    for path in sorted(CATALOG.glob("*/*PACKAGE.json")):
        data = json.loads(path.read_text())
        codes = []
        for item in (data.get("codeset") or {}).get("codes") or []:
            code = str(item.get("code") or "").strip()
            status = str(item.get("inclusion_status") or "")
            if code and "EXCLUDE" not in status:
                codes.append(code)
        found.append({
            "key": path.parent.name,
            "name": data.get("policy_name") or path.parent.name,
            "path": str(path.relative_to(ROOT)),
            "codes": codes,
            "package_policy_id": data.get("policy_id"),
        })
    return found


def _fee(token: str) -> float:
    digest = int(hashlib.sha256(token.encode()).hexdigest()[:6], 16)
    return round(40 + (digest % 760) + (digest % 100) / 100, 2)


def _generate_and_copy(packages, members, providers, intervals, period, totals, day_fn, start, end, money_split) -> None:
    import psycopg2

    conn = psycopg2.connect("host=127.0.0.1 port=55434 dbname=synthetic_payer_500k_longitudinal user=synthetic password=synthetic")
    cur = conn.cursor()
    ingestion = str(uuid.uuid4())
    now = datetime.utcnow().isoformat(sep=" ")
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter="\t", lineterminator="\n")
    pending = 0
    for ordinal, package in enumerate(packages):
        rng = random.Random(20261106 + (17 if period == "PRE" else 104729) + ordinal * 997)
        rate = 0.45 + (ordinal % 20) / 100
        code = package["codes"][0] if package["codes"] else None
        token = code or package["key"]
        allowed_base = _fee(token)
        lines = 0
        allowed_sum = 0.0
        for index in range(ordinal % 250, 500_000, 250):
            if period == "POST" and rng.random() >= rate:
                continue
            member = members[index]
            day = day_fn(rng, intervals.get(member["member_id"]) or [], start, end)
            if day is None:
                continue
            vary = 1.0 if period == "PRE" else (0.96 + rng.random() * 0.10)
            allowed = round(allowed_base * vary, 2)
            paid, share = money_split(allowed)
            claim = f"{period}-{package['key']}-{member['member_id']}"
            extras = {
                "policy_key": package["key"],
                "period": period,
                "line_status": "ACTIVE",
                "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
                "effective_date_label": "SYNTHETIC_HYPOTHETICAL_EFFECTIVE_DATE",
                "code_authority": "CANDIDATE_SCHEDULE" if code else "NO_CANDIDATE_CODE_IN_PACKAGE",
                "prediction_input": False,
            }
            writer.writerow([
                str(uuid.uuid4()), TENANT, claim, f"{claim}-1", member["member_id"], providers[index % len(providers)],
                day.isoformat(), (day).isoformat(), "COMMERCIAL", "SYNTHETIC", code or "\\N",
                package["key"], "11", 1, f"{allowed:.2f}", f"{paid:.2f}", f"{share:.2f}", "t", "f",
                "\\N", "SYNTHETIC_LONGITUDINAL_V1", f"synthetic-catalog-{period.lower()}",
                ingestion, json.dumps(extras, separators=(",", ":")), now, now,
            ])
            lines += 1
            allowed_sum += allowed
            pending += 1
            if pending >= 40000:
                _flush(cur, buf)
                buf = io.StringIO()
                writer = csv.writer(buf, delimiter="\t", lineterminator="\n")
                pending = 0
        totals[package["key"]] = {"lines": lines, "allowed": round(allowed_sum, 2), "code": code, "name": package["name"], "path": package["path"]}
        if ordinal % 40 == 0:
            print(period, ordinal, package["key"], lines, flush=True)
    if pending:
        _flush(cur, buf)
    conn.commit()
    conn.close()


def _flush(cur, buf) -> None:
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


def _policy_ids() -> dict[str, str]:
    from uepi_api.database import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    rows = db.execute(text("SELECT id::text, name, policy_metadata_json FROM policies WHERE tenant_id = :tenant"), {"tenant": TENANT}).mappings().all()
    db.close()
    by_key = {}
    for row in rows:
        meta = row["policy_metadata_json"] or {}
        if isinstance(meta, str):
            meta = json.loads(meta)
        path = str(meta.get("definition_path") or "")
        key = path.split("/")[-2] if path else None
        if key:
            by_key[key] = row["id"]
        if meta.get("policy_key"):
            by_key[meta["policy_key"]] = row["id"]
    return by_key


def _freeze(pre_totals: dict) -> dict:
    from uepi_api.database import SessionLocal
    from uepi_api.models.audit import AuditEvent
    from uepi_api.models.baseline import Baseline
    from uepi_api.models.predicted_impact import PolicyPredictedImpact
    from uepi_api.services.enrollment_exposure import measured_enrollment_member_months
    from uepi_api.storage_auth import DEFAULT_TENANT_ID
    from uepi_common.synthetic_payer.generate import POLICIES, WINDOW_START

    pre_mm = measured_enrollment_member_months(SessionLocal(), DEFAULT_TENANT_ID, WINDOW_START, datetime(2025, 6, 30).date())
    post_mm = measured_enrollment_member_months(SessionLocal(), DEFAULT_TENANT_ID, datetime(2025, 7, 1).date(), datetime(2026, 9, 30).date())
    ratio = post_mm / pre_mm if pre_mm else None
    ids = _policy_ids()
    db = SessionLocal()
    frozen = {}
    for key, spec in {row["key"]: row for row in POLICIES}.items():
        if key not in CLINICAL:
            continue
        from sqlalchemy import text
        allowed = db.execute(text("""
            SELECT COALESCE(SUM(allowed_amount), 0)
            FROM claims_lines
            WHERE tenant_id = :tenant AND service_category = :key AND service_date < DATE '2025-07-01'
        """), {"tenant": TENANT, "key": key}).scalar()
        predicted = round(float(allowed) * ratio, 2)
        change = round(predicted - float(allowed), 2)
        policy_id = spec["policy_id"]
        db.add(PolicyPredictedImpact(
            tenant_id=DEFAULT_TENANT_ID,
            policy_id=uuid.UUID(policy_id),
            metrics_json={"metrics": {
                "baseline_allowed": float(allowed),
                "predicted_allowed": predicted,
                "continuation_allowed_change": change,
                "method": "SYNTHETIC_EXPOSURE_CONTINUATION_PRE_FREEZE",
                "cutoff": "2025-06-30",
                "inputs": "PRE claims and enrollment exposure only",
                "clinical_outcome_engine": "NOT_RUN",
                "real_world_savings": False,
                "confidence": None,
            }},
            model_version="synthetic-continuation-v1",
            confidence=None,
            predicted_at=datetime(2026, 11, 6, 15, 0, 0),
            prediction_method="SYNTHETIC_EXPOSURE_CONTINUATION_PRE_FREEZE",
        ))
        db.add(AuditEvent(
            tenant_id=DEFAULT_TENANT_ID,
            action="LIFECYCLE_STAGE",
            object_type="POLICY",
            object_id=uuid.UUID(policy_id),
            diff_summary={"stage": "prediction_freeze", "cutoff": "2025-06-30", "clinical_outcome_engine": "NOT_RUN"},
            metadata_json={"worker": "synthetic_catalog_lifecycle.py", "post_claims_read": False},
        ))
        frozen[key] = {"policy_id": policy_id, "baseline_allowed": float(allowed), "predicted_allowed": predicted, "change": change}
    missing = [key for key in pre_totals if key not in ids]
    print("catalog policies matched", len(pre_totals) - len(missing), "missing", len(missing), flush=True)
    for key, totals in pre_totals.items():
        policy_id = ids.get(key)
        if not policy_id:
            continue
        predicted = round(totals["allowed"] * ratio, 2)
        change = round(predicted - totals["allowed"], 2)
        db.add(Baseline(
            tenant_id=DEFAULT_TENANT_ID,
            baseline_id=f"catalog-pre-{key}",
            version=1,
            baseline_type="FIXED",
            window_start_date=datetime(2024, 1, 1),
            window_end_date=datetime(2025, 6, 30),
            policy_id=uuid.UUID(policy_id),
            baseline_metrics_json={
                "policy_key": key,
                "total_claims": totals["lines"],
                "total_allowed": totals["allowed"],
                "member_months": pre_mm,
                "code_authority": "CANDIDATE_SCHEDULE" if totals["code"] else "NO_CANDIDATE_CODE_IN_PACKAGE",
                "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
            },
            computed_at=datetime(2026, 11, 6, 15, 0, 0),
            computed_by="SYNTHETIC_LONGITUDINAL_V1",
            shift_detected=False,
            refresh_reason="PRE_POLICY_ONLY",
        ))
        db.add(PolicyPredictedImpact(
            tenant_id=DEFAULT_TENANT_ID,
            policy_id=uuid.UUID(policy_id),
            metrics_json={"metrics": {
                "baseline_allowed": totals["allowed"],
                "predicted_allowed": predicted,
                "continuation_allowed_change": change,
                "method": "SYNTHETIC_EXPOSURE_CONTINUATION_PRE_FREEZE",
                "cutoff": "2025-06-30",
                "inputs": "PRE claims and enrollment exposure only",
                "real_world_savings": False,
                "confidence": None,
            }},
            model_version="synthetic-continuation-v1",
            confidence=None,
            predicted_at=datetime(2026, 11, 6, 15, 0, 0),
            prediction_method="SYNTHETIC_EXPOSURE_CONTINUATION_PRE_FREEZE",
        ))
        db.add(AuditEvent(
            tenant_id=DEFAULT_TENANT_ID,
            action="LIFECYCLE_STAGE",
            object_type="POLICY",
            object_id=uuid.UUID(policy_id),
            diff_summary={"stage": "prediction_freeze", "cutoff": "2025-06-30"},
            metadata_json={"worker": "synthetic_catalog_lifecycle.py", "post_claims_read": False},
        ))
        frozen[key] = {"policy_id": policy_id, "baseline_allowed": totals["allowed"], "predicted_allowed": predicted, "change": change}
    db.commit()
    db.close()
    frozen["_exposure"] = {"pre_member_months": pre_mm, "post_member_months": post_mm}
    path = ROOT / "data" / "synthetic" / "catalog_prediction_freeze.json"
    path.write_text(json.dumps({k: v for k, v in frozen.items() if k != "_exposure"} | {"exposure": frozen["_exposure"]}, indent=2))
    print("frozen", len(frozen) - 1, flush=True)
    return frozen


def _observe(freeze: dict, post_totals: dict) -> list:
    from uepi_api.database import SessionLocal
    from uepi_api.models.audit import AuditEvent
    from uepi_api.models.observation import Observation
    from uepi_common.synthetic_payer.generate import POLICIES
    from sqlalchemy import text

    post_mm = freeze["_exposure"]["post_member_months"]
    db = SessionLocal()
    results = []
    clinical_allowed = {
        row[0]: float(row[1] or 0)
        for row in db.execute(text("""
            SELECT service_category, SUM(allowed_amount)
            FROM claims_lines
            WHERE tenant_id = :tenant AND service_category = ANY(:keys) AND service_date >= DATE '2025-07-01'
            GROUP BY service_category
        """), {"tenant": TENANT, "keys": list(CLINICAL)})
    }
    for spec in POLICIES:
        if spec["key"] not in CLINICAL:
            continue
        post_totals[spec["key"]] = {"allowed": clinical_allowed.get(spec["key"], 0.0), "lines": None}
    for key, prior in freeze.items():
        if key == "_exposure" or key not in post_totals:
            continue
        observed_allowed = round(float(post_totals[key]["allowed"]), 2)
        difference = round(observed_allowed - prior["predicted_allowed"], 2)
        per_mm = None if not post_mm else difference / post_mm
        existing = db.query(Observation).filter(Observation.observation_id == f"longitudinal-post-{key}").one_or_none()
        payload = {
            "denominator_basis": "ENROLLMENT",
            "enrolled_rate_status": "MEASURED",
            "member_months": post_mm,
            "outcome_status": "SYNTHETIC_OBSERVED",
            "clinical_outcome_engine": "NOT_RUN" if key in CLINICAL else None,
            "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
            "copied_from_prediction": False,
        }
        comparisons = {
            "vs_baseline": {
                "cost_change": per_mm,
                "cost_change_pmpm": per_mm,
                "cost_change_kind": "observed_versus_frozen_continuation_per_enrolled_member_month",
                "cost_change_meaning": "Observed post-period allowed minus the frozen continuation prediction, per post-period enrolled member-month.",
            },
            "vs_predicted": {
                "frozen_predicted_allowed": prior["predicted_allowed"],
                "observed_allowed": observed_allowed,
                "difference": difference,
                "reconciliation_status": "MEASURED_DIFFERENCE",
                "copied_from_prediction": False,
                "real_world_evidence": False,
            },
        }
        if existing:
            existing.metrics_json = payload
            existing.comparisons_json = comparisons
            existing.verdict_status = "INCONCLUSIVE"
            existing.verdict_reason = "No policy endpoint contract is defined. A measured difference is not a verdict."
            existing.computed_at = datetime(2026, 11, 6, 16, 0, 0)
        else:
            db.add(Observation(
                tenant_id=uuid.UUID(TENANT),
                observation_id=f"catalog-post-{key}",
                policy_id=uuid.UUID(prior["policy_id"]),
                observation_type="POST_PERIOD",
                observation_period_start=datetime(2025, 7, 1),
                observation_period_end=datetime(2026, 9, 30),
                metrics_json=payload,
                comparisons_json=comparisons,
                verdict_status="INCONCLUSIVE",
                verdict_reason="No policy endpoint contract is defined. A measured difference is not a verdict.",
                recommendation="Declare the required endpoints and their direction before scoring this policy.",
                verdict_rule_version="v1.1-endpoints",
                computed_at=datetime(2026, 11, 6, 16, 0, 0),
            ))
        db.add(AuditEvent(
            tenant_id=uuid.UUID(TENANT),
            action="LIFECYCLE_STAGE",
            object_type="POLICY",
            object_id=uuid.UUID(prior["policy_id"]),
            diff_summary={"stage": "post_policy_observation", "difference": difference},
            metadata_json={"worker": "synthetic_catalog_lifecycle.py", "copied_from_prediction": False},
        ))
        results.append({"policy_key": key, "predicted_allowed": prior["predicted_allowed"], "observed_allowed": observed_allowed, "difference": difference})
    db.commit()
    db.close()
    return results


if __name__ == "__main__":
    main()
