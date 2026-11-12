"""Run an isolated synthetic pilot. Writes local files only when asked."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from uepi_common.synthetic_payer.exposure import CONVENTION, covers
from uepi_common.synthetic_payer.generate import (
    GENERATOR_VERSION,
    POLICIES,
    REFERENCE_DATE,
    SEED,
    WINDOW_END,
    WINDOW_START,
    exposure_summary,
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
    rate_per_exposure,
)

CLINICAL_REASONS = {
    "mri": "No population prior-authorization outcome engine. Authorization decisions are not adjudicated.",
    "ncd": "NCD 220.2 is a coverage study. No approved outcome engine.",
    "lcd": "LCD L34425 is an orbit, face, and neck study. It is not the lumbar MRI policy and has no outcome engine.",
}


def active_lines(lines: List[Mapping[str, Any]], key: str) -> List[Mapping[str, Any]]:
    return [row for row in lines if row.get("policy_key") == key and row.get("line_status") == "ACTIVE"]


def oracle_for_population(lines: List[Mapping[str, Any]]) -> Dict[str, Any]:
    return {
        "mppr_favorable": oracle_mppr(active_lines(lines, "mppr"), secondary_pct=0.5),
        "sos_policy": oracle_sos(active_lines(lines, "sos"), hospital_pct=0.8),
        "sos_neutral": oracle_sos(active_lines(lines, "sos"), hospital_pct=1.0),
        "sos_adverse": oracle_sos(active_lines(lines, "sos"), hospital_pct=1.1),
        "ptp": oracle_ptp(active_lines(lines, "ptp")),
        "mue": oracle_mue(active_lines(lines, "mue"), mue_value=4),
        "therapy": oracle_therapy(active_lines(lines, "therapy")),
        "infusion": oracle_infusion_by_claim(active_lines(lines, "infusion"), steer_hopd_count=1, office_allowed=3200.0),
        "mri": oracle_not_measurable("mri", len(active_lines(lines, "mri")), CLINICAL_REASONS["mri"]),
        "ncd": oracle_not_measurable("ncd", len(active_lines(lines, "ncd")), CLINICAL_REASONS["ncd"]),
        "lcd": oracle_not_measurable("lcd", len(active_lines(lines, "lcd")), CLINICAL_REASONS["lcd"]),
    }


def check_integrity(population: Dict[str, Any], lines: List[Mapping[str, Any]], exposure: Dict[str, Any], lives: int) -> List[str]:
    failures: List[str] = []
    members = {row["member_id"] for row in population["members"]}
    providers = {row["provider_id"] for row in population["providers"]}
    enrolled = sum(1 for row in population["members"] if row["reference_enrolled"])
    if enrolled != lives or len(members) != lives:
        failures.append(f"reference census {enrolled} distinct {len(members)} expected {lives}")
    if exposure["member_months"] <= 0:
        failures.append("member-months are not positive")
    if exposure["denominator_basis"] != "ENROLLMENT" or exposure["enrolled_rate_status"] != "MEASURED":
        failures.append("exposure is not a measured enrollment denominator")
    coverage: Dict[str, List] = {}
    for row in population["coverage"]:
        from datetime import date
        coverage.setdefault(row["member_id"], []).append((date.fromisoformat(row["start_date"]), date.fromisoformat(row["end_date"])))
    from datetime import date
    for line in lines:
        if line["member_id"] not in members:
            failures.append("claim member is not in the population")
            break
        if line["provider_id"] not in providers:
            failures.append("claim provider is not in the network file")
            break
        day = date.fromisoformat(line["service_date"])
        if not covers(coverage[line["member_id"]], day):
            failures.append(f"service date {line['service_date']} is outside coverage for {line['member_id']}")
            break
        allowed = round(float(line["allowed_amount"]), 2)
        paid = round(float(line["plan_paid_amount"]), 2)
        share = round(float(line["member_cost_share"]), 2)
        if round(allowed - paid - share, 2) != 0:
            failures.append("allowed does not equal plan paid plus member cost share")
            break
        if line.get("paid_amount") != line.get("plan_paid_amount"):
            failures.append("paid_amount was copied from allowed")
            break
    for line in lines:
        if line.get("line_status") == "REVERSAL":
            original_id = line["reverses_line_id"]
            original = next(row for row in lines if row["claim_line_id"] == original_id)
            if round(original["allowed_amount"] + line["allowed_amount"], 2) != 0:
                failures.append("reversal does not net the original allowed amount to zero")
                break
    lumbar = {row["member_id"] for row in lines if row.get("policy_key") == "mri"}
    lcd_members = {row["member_id"] for row in lines if row.get("policy_key") == "lcd"}
    if lumbar & lcd_members:
        failures.append("LCD orbit events were assigned to lumbar MRI members")
    for row in lines:
        if row.get("policy_key") == "lcd" and row.get("cpt_code") == "72148":
            failures.append("LCD study used the lumbar MRI code")
        if row.get("policy_key") == "lcd" and row.get("anatomical_region") != "ORBIT_FACE_NECK_ONLY":
            failures.append("LCD event is not orbit, face, or neck")
        if any(key in row for key in ("ssn", "name", "address", "dob")):
            failures.append("direct identifier present")
    if rate_per_exposure(100.0, 0) is not None or rate_per_exposure(None, 10) is not None:
        failures.append("missing exposure or amount became a rate")
    return failures


def journey_records(oracle: Dict[str, Any], lines: List[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    records = []
    for policy in POLICIES:
        key = policy["key"]
        result = oracle[key] if key in oracle else oracle.get(f"{key}_favorable") or oracle.get(f"{key}_policy")
        if key == "mppr":
            result = oracle["mppr_favorable"]
        elif key == "sos":
            result = oracle["sos_policy"]
        records.append(
            {
                "policy_id": policy["policy_id"],
                "document_id": policy["document_id"],
                "policy_key": key,
                "execution_status": result["execution_status"],
                "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
                "event_count": result.get("event_count", len(active_lines(lines, key))),
                "screen_verdict": result["verdict"]["screen_verdict"],
                "payment_impact": result.get("payment_impact"),
                "real_world_savings": False,
                "cms_adjudication": False,
                "customer_label": _customer_label(result),
            }
        )
    return records


def _customer_label(result: Mapping[str, Any]) -> str:
    if result["execution_status"] == "NOT_MEASURABLE":
        return "Not measurable. No population outcome is shown."
    impact = result.get("payment_impact")
    return (
        f"Synthetic payment difference ${impact:,.2f}. "
        "Not real-world savings and not enrolled-population proof."
    )


def run_pilot(lives: int, seed: int = SEED, out_dir: Optional[Path] = None) -> Dict[str, Any]:
    population = generate_population(lives, seed)
    lines = generate_events(population, seed)
    exposure = exposure_summary(population)
    failures = check_integrity(population, lines, exposure, lives)
    oracle = oracle_for_population(lines)
    journeys = journey_records(oracle, lines)
    status = "FAIL" if failures else "PASS"
    report = {
        "status": status,
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "lives_enrolled_on_reference_date": lives,
        "reference_date": REFERENCE_DATE.isoformat(),
        "window_start": WINDOW_START.isoformat(),
        "window_end_exclusive": WINDOW_END.isoformat(),
        "partial_month_convention": CONVENTION,
        "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
        "exposure": exposure,
        "member_count": len(population["members"]),
        "coverage_rows": len(population["coverage"]),
        "claim_rows": len(lines),
        "active_claim_rows": sum(1 for row in lines if row["line_status"] == "ACTIVE"),
        "non_user_members": sum(1 for row in population["members"] if row["cohort"] == "none"),
        "failures": failures,
        "oracle": {key: _public_oracle(value) for key, value in oracle.items()},
        "journeys": journeys,
        "scenarios": {
            "favorable_to_payer": "mppr secondary percent 50",
            "neutral": "site of service hospital percent 100",
            "adverse_to_payer": "site of service hospital percent 110",
        },
        "not_claimed": [
            "Real-world savings",
            "CMS adjudication",
            "Clinical certification",
            "Causal effect",
        ],
    }
    if out_dir and status == "PASS":
        _write(Path(out_dir), population, lines, report)
        report["output_dir"] = str(out_dir)
    return report


def _public_oracle(result: Mapping[str, Any]) -> Dict[str, Any]:
    hidden = {"lines"}
    return {key: value for key, value in result.items() if key not in hidden}


def _write(out_dir: Path, population: Dict[str, Any], lines: List[Mapping[str, Any]], report: Dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    _csv(out_dir / "members.csv", population["members"])
    _csv(out_dir / "coverage_intervals.csv", population["coverage"])
    _csv(out_dir / "providers.csv", population["providers"])
    _csv(out_dir / "claim_lines.csv", lines)
    (out_dir / "reconciliation.json").write_text(json.dumps(report, indent=2, default=str))


def _csv(path: Path, rows: List[Mapping[str, Any]]) -> None:
    if not rows:
        path.write_text("")
        return
    fieldnames: List[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
