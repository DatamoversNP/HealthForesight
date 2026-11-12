#!/usr/bin/env python3
"""Read-only independent audit of lean-staging observations.

Does not call the observation writer. Does not update claims, baselines,
observations, policies, or Azure. Writes local evidence files only.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/production/releases/corrections/observation_audit"
TENANT = "00000000-0000-0000-0000-000000000001"
AUDIT_AS_OF = date(2026, 11, 6)
RATE_TOL = 0.02
MONEY_TOL = 0.05


def _assert_staging(url: str) -> None:
    u = url.lower()
    if "healthforesight-db" in u or "healthforesight-rg" in u:
        raise SystemExit("Refusing demo database")
    if "lean" not in u and "hfleanstg" not in u:
        raise SystemExit("Refusing non-staging database")


def _num(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _round2(v: float) -> float:
    return round(float(v), 2)


def mechanism_of(name: str, policy_type: str, domain: str) -> str:
    """Name overrides catch NCCI and MPPR. Otherwise the stored policy type is the domain."""
    blob = f"{name} {domain}".lower()
    if "medically unlikely" in blob or " mue" in blob:
        return "ncci_mue"
    if "procedure-to-procedure" in blob or "procedure to procedure" in blob:
        return "ncci_ptp"
    if "multiple procedure" in blob or "mppr" in blob:
        return "payment_mppr"
    by_type = {
        "PRIOR_AUTH": "prior_authorization",
        "SITE_OF_CARE": "site_of_care",
        "PAYMENT_POLICY": "payment_policy",
        "STEP_THERAPY": "pharmacy",
        "QUANTITY_LIMIT": "quantity_limit",
        "DURATION_FREQUENCY_LIMIT": "frequency_limit",
        "COST_SHARING": "benefit_cost_share",
        "BENEFIT": "benefit_design",
        "NETWORK_RESTRICTION": "network",
        "ACCESS_AVAILABILITY_RULE": "access",
        "CLINICAL_CRITERIA": "clinical_criteria",
        "COVERAGE": "coverage",
        "ADMINISTRATIVE_REQUIREMENT": "admin",
        "COMPOSITE": "care_management",
        "CODING_AND_BILLING": "coding_edit",
        "REFERRAL_REQUIREMENT": "referral",
        "PROVIDER_ELIGIBILITY": "provider_eligibility",
    }
    return by_type.get((policy_type or "").upper(), "unclassified")


MECHANISM_MEASURE = {
    "prior_authorization": (
        "Approval rate, denial rate, and units with an authorization decision. "
        "Claim volume alone does not measure prior authorization.",
        "auth_requests, decisions",
    ),
    "coverage": (
        "Share of scoped services meeting coverage criteria, including diagnosis and benefit limits.",
        "diagnosis, benefit decision",
    ),
    "site_of_care": (
        "Site share (POS) among eligible services or drugs, before and after the policy.",
        "place_of_service on eligible lines",
    ),
    "payment_mppr": (
        "Allowed amount after ranking same-day procedure lines and applying the reduction schedule.",
        "same-day line groups, modifier, rank",
    ),
    "ncci_ptp": (
        "Column 1 / column 2 pair frequency and whether a bypass modifier is present.",
        "PTP edit table, modifiers",
    ),
    "ncci_mue": (
        "Units above the medically unlikely edit for the code and date-of-service grain.",
        "MUE table, units, date of service",
    ),
    "pharmacy": (
        "Drug product, days supply, and fill sequence for the management rule (step, quantity, site).",
        "NDC or drug HCPCS, pharmacy event",
    ),
    "benefit_cost_share": (
        "Member cost share per eligible member-month, not raw claim counts.",
        "enrollment and member_cost_share",
    ),
    "network": (
        "In-network share of eligible services.",
        "in_network flag and eligible population",
    ),
    "clinical_criteria": (
        "Services meeting published clinical criteria versus services that do not.",
        "diagnosis and clinical criteria",
    ),
    "admin": (
        "Process evidence (documentation, turnaround, compliance), not claim volume.",
        "operational events",
    ),
    "payment_policy": (
        "Paid or allowed amount after the payment rule, against a priced baseline on the same lines.",
        "fee schedule, modifiers, grouping key",
    ),
    "quantity_limit": (
        "Units or days supply above the limit, at the member and period grain the limit uses.",
        "limit value, units or days supply",
    ),
    "frequency_limit": (
        "Services above the allowed count in the lookback window.",
        "limit value and prior services for the member",
    ),
    "benefit_design": (
        "Whether the benefit was applied: covered services, cost share, and excluded services.",
        "benefit decision and enrollment",
    ),
    "access": (
        "Share of members meeting the access standard (appointment wait, distance, availability).",
        "access events or network adequacy data",
    ),
    "care_management": (
        "Enrollment in the program and the outcome the program states, not raw claim volume.",
        "program enrollment and outcome definition",
    ),
    "coding_edit": (
        "Lines that fail the edit versus lines that pass, using the edit table.",
        "edit table, modifiers, units",
    ),
    "referral": (
        "Scoped services that have a required referral on file.",
        "referral records",
    ),
    "provider_eligibility": (
        "Share of scoped services rendered by an eligible provider.",
        "provider credential or eligibility flag",
    ),
    "unclassified": (
        "No mechanism-specific measure is defined for this policy.",
        "policy objective",
    ),
}


def codes_from_meta(meta: dict) -> tuple[list[str], str]:
    scope = meta.get("scope") if isinstance(meta.get("scope"), dict) else {}
    codes = [str(c) for c in (scope.get("procedure_codes") or []) if c]
    if codes:
        return codes, "scope.procedure_codes"
    for lev in meta.get("policy_levers") or []:
        targets = (lev or {}).get("targets") or {}
        found = [str(c) for c in (targets.get("codes") or targets.get("procedure_codes") or []) if c]
        if found:
            return found, "policy_levers.targets"
    return [], "none"


def index_claims(rows):
    by_code = defaultdict(list)
    for r in rows:
        item = r
        for code in (r["cpt_code"], r["hcpcs_code"]):
            if code:
                by_code[code].append(item)
    return by_code


def select_lines(by_code, codes, year, month=None):
    """Lines whose CPT or HCPCS is in the policy code set. Count each line once."""
    chosen = {}
    for code in codes:
        for line in by_code.get(code, []):
            sd = line["service_date"]
            if isinstance(sd, datetime):
                sd = sd.date()
            if sd.year != year:
                continue
            if month is not None and sd.month != month:
                continue
            chosen[line["id"]] = line
    return list(chosen.values())


def stored_rate_formula(n: int, members: int, allowed: float, months: int) -> tuple[float, float]:
    """Independent copy of the formula that was written onto staging.

    utilization = (claim_lines / distinct_claimants) * (1000 / months)
    cost = allowed_amount / (distinct_claimants * months)
    Denominator is claimants with a matching line, not enrolled member-months.
    """
    mem = max(members, 1)
    util = _round2((n / mem) * (1000 / months))
    cost = _round2(allowed / (mem * months))
    return util, cost


def close(a, b, tol) -> bool:
    return abs(_num(a) - _num(b)) <= tol


def main() -> None:
    url = os.environ.get("DATABASE_URL") or ""
    _assert_staging(url)
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://") :]
    eng = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 30})
    OUT.mkdir(parents=True, exist_ok=True)

    with eng.connect() as c:
        claims = c.execute(
            text(
                """
                SELECT id::text AS id, claim_id, claim_line_id, service_date, paid_date,
                       cpt_code, hcpcs_code, member_id, provider_id,
                       allowed_amount, paid_amount, units, member_cost_share,
                       source_system, lob, place_of_service, in_network, market
                FROM claims_lines WHERE tenant_id=:t
                """
            ),
            {"t": TENANT},
        ).mappings().all()
        policies = c.execute(
            text(
                """
                SELECT id::text AS id, name, policy_type, status, policy_metadata_json
                FROM policies WHERE tenant_id=:t ORDER BY name
                """
            ),
            {"t": TENANT},
        ).mappings().all()
        baselines = c.execute(
            text(
                """
                SELECT id::text AS id, policy_id::text AS policy_id,
                       window_start_date::date AS ws, window_end_date::date AS we,
                       baseline_metrics_json
                FROM baselines WHERE tenant_id=:t
                """
            ),
            {"t": TENANT},
        ).mappings().all()
        observations = c.execute(
            text(
                """
                SELECT id::text AS id, policy_id::text AS policy_id,
                       baseline_version_id::text AS baseline_version_id,
                       prediction_id::text AS prediction_id,
                       policy_version_id::text AS policy_version_id,
                       observation_period_start, observation_period_end,
                       metrics_json, comparisons_json, verdict_status, verdict_reason,
                       verdict_rule_version
                FROM observations WHERE tenant_id=:t
                """
            ),
            {"t": TENANT},
        ).mappings().all()
        versions = c.execute(
            text(
                """
                SELECT policy_id::text, count(*) n, max(version_number) max_v
                FROM policy_versions WHERE tenant_id=:t GROUP BY policy_id
                """
            ),
            {"t": TENANT},
        ).mappings().all()
        try:
            enrollment_rows = c.execute(
                text("SELECT count(*) FROM enrollment_records WHERE tenant_id=:t"),
                {"t": TENANT},
            ).scalar()
        except Exception:
            enrollment_rows = None
        demo_copy = c.execute(
            text("SELECT count(*) FROM claims_lines WHERE tenant_id=:t AND source_system='DEMO_SUBSET_COPY'"),
            {"t": TENANT},
        ).scalar()

    # Structure
    def year_of(r):
        sd = r["service_date"]
        return sd.year if not isinstance(sd, datetime) else sd.date().year

    n_2025 = sum(1 for r in claims if year_of(r) == 2025)
    n_2026 = sum(1 for r in claims if year_of(r) == 2026)
    other_year = len(claims) - n_2025 - n_2026
    general = [b for b in baselines if b["policy_id"] is None and b["ws"] == date(2025, 1, 1) and b["we"] == date(2025, 12, 31)]
    policy_annual = [b for b in baselines if b["policy_id"] and b["ws"] == date(2025, 1, 1) and b["we"] == date(2025, 12, 31)]
    other_baselines = len(baselines) - len(general) - len(policy_annual)
    obs_by_policy = defaultdict(list)
    months_seen = set()
    for o in observations:
        start = o["observation_period_start"]
        if isinstance(start, datetime):
            start = start.date()
        months_seen.add(start.strftime("%Y-%m"))
        obs_by_policy[o["policy_id"]].append(o)
    per_policy_counts = [len(v) for v in obs_by_policy.values()]
    outside = sorted(m for m in months_seen if m < "2026-01" or m > "2026-09")

    structure = {
        "claims_total": len(claims),
        "claims_2025": n_2025,
        "claims_2026": n_2026,
        "claims_other_year": other_year,
        "demo_subset_copy": int(demo_copy or 0),
        "general_baselines_cy2025": len(general),
        "policy_baselines_cy2025": len(policy_annual),
        "other_baselines": other_baselines,
        "observations": len(observations),
        "policies_with_obs": len(obs_by_policy),
        "obs_per_policy_min": min(per_policy_counts) if per_policy_counts else 0,
        "obs_per_policy_max": max(per_policy_counts) if per_policy_counts else 0,
        "observation_months": sorted(months_seen),
        "months_outside_jan_sep": outside,
        "enrollment_rows": enrollment_rows,
        "policies": len(policies),
    }
    structure_ok = (
        structure["claims_total"] == 53949
        and structure["claims_2025"] == 25692
        and structure["claims_2026"] == 28257
        and structure["general_baselines_cy2025"] == 1
        and structure["policy_baselines_cy2025"] == 250
        and structure["other_baselines"] == 0
        and structure["observations"] == 2250
        and structure["obs_per_policy_min"] == 9
        and structure["obs_per_policy_max"] == 9
        and not outside
        and structure["demo_subset_copy"] == 0
    )

    # Integrity
    null_allowed = sum(1 for r in claims if r["allowed_amount"] is None)
    neg_allowed = sum(1 for r in claims if r["allowed_amount"] is not None and float(r["allowed_amount"]) < 0)
    neg_paid = sum(1 for r in claims if r["paid_amount"] is not None and float(r["paid_amount"]) < 0)
    future = 0
    feb29 = 0
    day15 = 0
    sources = defaultdict(int)
    line_keys = defaultdict(int)
    for r in claims:
        sources[r["source_system"] or "(null)"] += 1
        sd = r["service_date"]
        if isinstance(sd, datetime):
            sd = sd.date()
        if sd > AUDIT_AS_OF:
            future += 1
        if sd.month == 2 and sd.day == 29:
            feb29 += 1
        if sd.day == 15:
            day15 += 1
        line_keys[(r["claim_id"], r["claim_line_id"])] += 1
    dup_lines = sum(1 for n in line_keys.values() if n > 1)

    by_code = index_claims(claims)
    version_by_policy = {v["policy_id"]: v for v in versions}
    baseline_by_policy = {b["policy_id"]: b for b in policy_annual}

    baseline_rows = []
    semantic_rows = []
    obs_rows = []
    status_rows = []
    arith_fail = 0
    baseline_arith_fail = 0
    status_mismatch = 0
    scope_fail = 0
    not_measurable = 0

    for pol in policies:
        meta = pol["policy_metadata_json"] if isinstance(pol["policy_metadata_json"], dict) else {}
        if isinstance(meta, str):
            meta = json.loads(meta)
        codes, code_source = codes_from_meta(meta)
        rem = meta.get("remediation") if isinstance(meta.get("remediation"), dict) else {}
        exec_state = str(rem.get("execution_eligibility") or "")
        code_state = str(rem.get("code_mapping_state") or "")
        domain = str(meta.get("domain") or (meta.get("ui_hints") or {}).get("domain") or "")
        mech = mechanism_of(pol["name"] or "", pol["policy_type"] or "", domain)
        measure_text, required_data = MECHANISM_MEASURE[mech]
        scope_ok = bool(codes) and exec_state.upper() in {"CLAIMS_EXECUTABLE", "DIRECTIONALLY_VALID", "ALLOWED"} and code_state.upper() not in {"UNVERIFIED_CODE_MAPPING", "CLEARED_PENDING_REMAP"}
        if not scope_ok:
            scope_validity = "FAIL"
            scope_fail += 1
            scope_reason = (
                f"codes={code_source}:{len(codes)}; execution_eligibility={exec_state or 'absent'}; "
                f"code_mapping_state={code_state or 'absent'}"
            )
        else:
            scope_validity = "UNVALIDATED"
            scope_reason = "Executable flag present but code set was not clinically certified in this audit"
        metric_validity = "NOT_MEASURABLE"
        metric_reason = (
            f"Persisted metric is generic claimant-denominated volume/cost. "
            f"Mechanism '{mech}' requires: {measure_text} Missing: {required_data}."
        )
        ver = version_by_policy.get(pol["id"])
        config_version = f"v{ver['max_v']}" if ver else "ABSENT"

        b = baseline_by_policy.get(pol["id"])
        metrics = b["baseline_metrics_json"] if b else {}
        if isinstance(metrics, str):
            metrics = json.loads(metrics)
        lines_2025 = select_lines(by_code, codes, 2025) if codes else []
        members_2025 = {ln["member_id"] for ln in lines_2025}
        allowed_2025 = sum(float(ln["allowed_amount"] or 0) for ln in lines_2025)
        paid_2025 = sum(float(ln["paid_amount"] or 0) for ln in lines_2025)
        n_2025_p = len(lines_2025)
        re_util, re_cost = stored_rate_formula(n_2025_p, len(members_2025), allowed_2025, 12)
        stored_n = int(_num(metrics.get("claim_count")))
        stored_util = _num(metrics.get("utilization_per_1k"))
        stored_cost = _num(metrics.get("cost_pmpm"))
        count_ok = stored_n == n_2025_p
        rate_ok = close(stored_util, re_util, RATE_TOL) and close(stored_cost, re_cost, MONEY_TOL)
        base_pass = "PASS" if b and count_ok and rate_ok else "FAIL"
        if base_pass == "FAIL":
            baseline_arith_fail += 1
        # Supported comparison is claim volume only. Do not invent member-months.
        monthly_eq = n_2025_p / 12 if n_2025_p else 0
        baseline_rows.append(
            {
                "policy_id": pol["id"],
                "policy_name": pol["name"],
                "configuration_version": config_version,
                "code_source": code_source,
                "code_count": len(codes),
                "codes": "|".join(codes),
                "stored_claim_count": stored_n,
                "recomputed_claim_count": n_2025_p,
                "claim_count_diff": stored_n - n_2025_p,
                "stored_distinct_claimants": metrics.get("unique_members"),
                "recomputed_distinct_claimants": len(members_2025),
                "stored_utilization_per_1k": stored_util,
                "recomputed_stored_formula_util": re_util,
                "util_diff": _round2(stored_util - re_util),
                "stored_cost_pmpm": stored_cost,
                "recomputed_stored_formula_cost": re_cost,
                "cost_diff": _round2(stored_cost - re_cost),
                "recomputed_allowed_sum": _round2(allowed_2025),
                "recomputed_paid_sum": _round2(paid_2025),
                "monthly_equivalent_claim_count": _round2(monthly_eq),
                "enrollment_member_months": "NOT_AVAILABLE",
                "utilization_rate_status": "NOT_MEASURABLE",
                "arithmetic_vs_stored_formula": base_pass,
                "scope_validity": scope_validity,
                "defect": "" if base_pass == "PASS" else "Stored baseline does not match independent code-filtered recount",
            }
        )
        semantic_rows.append(
            {
                "policy_id": pol["id"],
                "policy_name": pol["name"],
                "policy_type": pol["policy_type"],
                "domain": domain,
                "mechanism": mech,
                "required_measure": measure_text,
                "required_data": required_data,
                "persisted_measure": "utilization_per_1k and cost_pmpm from matching claim lines / distinct claimants",
                "scope_validity": scope_validity,
                "scope_reason": scope_reason,
                "metric_validity": metric_validity,
                "metric_reason": metric_reason,
                "effectiveness_claim": "NOT_SUPPORTED",
                "data_character": "SYNTHETIC_PLUS_LIGHT_SEED",
            }
        )

        for obs in obs_by_policy.get(pol["id"], []):
            start = obs["observation_period_start"]
            if isinstance(start, datetime):
                start = start.date()
            end = obs["observation_period_end"]
            if isinstance(end, datetime):
                end = end.date()
            ym = start.strftime("%Y-%m")
            om = obs["metrics_json"] if isinstance(obs["metrics_json"], dict) else json.loads(obs["metrics_json"] or "{}")
            comp = obs["comparisons_json"] if isinstance(obs["comparisons_json"], dict) else json.loads(obs["comparisons_json"] or "{}")
            month_lines = select_lines(by_code, codes, start.year, start.month) if codes else []
            # Period boundary: service date must fall inside the stored window.
            in_window = []
            for ln in month_lines:
                sd = ln["service_date"]
                if isinstance(sd, datetime):
                    sd = sd.date()
                if start <= sd <= end:
                    in_window.append(ln)
            leaked = len(month_lines) - len(in_window)
            mems = {ln["member_id"] for ln in in_window}
            allowed_m = sum(float(ln["allowed_amount"] or 0) for ln in in_window)
            n_m = len(in_window)
            if n_m == 0:
                re_ou, re_oc = 0.0, 0.0
            else:
                re_ou, re_oc = stored_rate_formula(n_m, len(mems), allowed_m, 1)
            st_ou = _num(om.get("utilization_per_1k"))
            st_oc = _num(om.get("cost_pmpm"))
            st_n = int(_num(om.get("claim_count")))
            st_bu = _num(om.get("baseline_utilization_per_1k"))
            st_bc = _num(om.get("baseline_cost_pmpm"))
            st_pu = _num(om.get("predicted_utilization_per_1k"))
            st_pc = _num(om.get("predicted_cost_pmpm"))
            exp_pu, exp_pc = _round2(st_bu * 0.95), _round2(st_bc * 0.97)
            if exp_pu and re_ou <= exp_pu * 1.05:
                exp_status = "ON_TRACK"
            elif st_bu and re_ou > st_bu * 1.1:
                exp_status = "BACKFIRE"
            else:
                exp_status = "AT_RISK"
            count_match = st_n == n_m
            rate_match = close(st_ou, re_ou, RATE_TOL) and close(st_oc, re_oc, MONEY_TOL)
            pred_match = close(st_pu, exp_pu, RATE_TOL) and close(st_pc, exp_pc, MONEY_TOL)
            arith = "PASS" if count_match and rate_match and pred_match and leaked == 0 else "FAIL"
            if arith == "FAIL":
                arith_fail += 1
            if obs["verdict_status"] != exp_status:
                status_mismatch += 1
            # Claim-volume comparison only. Annual raw count is not compared to the month.
            base_month_eq = n_2025_p / 12 if n_2025_p else None
            if base_month_eq:
                volume_pct = _round2((n_m - base_month_eq) / base_month_eq * 100)
            else:
                volume_pct = ""
            vs_b = (comp.get("vs_baseline") or {})
            stored_util_delta = _num(vs_b.get("utilization_change"))
            re_util_delta = _round2(re_ou - st_bu)
            # The persisted rate delta mixes an annual claimant rate with a monthly claimant rate.
            rate_comparison = "FAIL"
            status_validity = "INSUFFICIENT_EVIDENCE"
            overall = "NOT_MEASURABLE" if arith == "PASS" else "FAIL"
            if overall == "NOT_MEASURABLE":
                not_measurable += 1
            defect_bits = []
            if not count_match:
                defect_bits.append(f"claim_count stored {st_n} vs recomputed {n_m}")
            if not rate_match:
                defect_bits.append(f"rate stored util {st_ou} cost {st_oc} vs recomputed {re_ou} {re_oc}")
            if not pred_match:
                defect_bits.append("prediction is not -5% util / -3% cost of the stored baseline")
            if leaked:
                defect_bits.append(f"{leaked} lines outside the observation window")
            defect_bits.append("utilization rate uses distinct claimants, not enrolled member-months")
            defect_bits.append("annual baseline rate compared with monthly rate on a different claimant set")
            defect_bits.append("status uses a hardcoded -5% stub, not a policy objective")
            defect_bits.append(metric_reason)
            obs_rows.append(
                {
                    "policy_id": pol["id"],
                    "policy_name": pol["name"],
                    "configuration_version": config_version,
                    "observation_month": ym,
                    "data_snapshot_id": "ABSENT",
                    "baseline_claim_count": n_2025_p,
                    "baseline_monthly_equivalent_claims": "" if base_month_eq is None else _round2(base_month_eq),
                    "observed_claim_count": n_m,
                    "stored_claim_count": st_n,
                    "claim_count_diff": st_n - n_m,
                    "stored_utilization_per_1k": st_ou,
                    "recomputed_utilization_per_1k": re_ou,
                    "util_abs_diff": _round2(st_ou - re_ou),
                    "stored_cost_pmpm": st_oc,
                    "recomputed_cost_pmpm": re_oc,
                    "cost_abs_diff": _round2(st_oc - re_oc),
                    "stored_vs_baseline_util_delta": stored_util_delta,
                    "recomputed_vs_baseline_util_delta": re_util_delta,
                    "claim_volume_change_pct_vs_monthly_equivalent": volume_pct,
                    "stored_predicted_util": st_pu,
                    "formula_predicted_util": exp_pu,
                    "scope_validity": scope_validity,
                    "metric_validity": metric_validity,
                    "rate_comparison_validity": rate_comparison,
                    "status_validity": status_validity,
                    "stored_status": obs["verdict_status"],
                    "status_implied_by_stored_rule": exp_status,
                    "arithmetic_reconciliation": arith,
                    "result": overall,
                    "defect": "; ".join(defect_bits),
                }
            )
            status_rows.append(
                {
                    "policy_id": pol["id"],
                    "policy_name": pol["name"],
                    "observation_month": ym,
                    "stored_status": obs["verdict_status"],
                    "verdict_rule_version": obs["verdict_rule_version"],
                    "product_verdict_module": "NOT_USED",
                    "rule_actually_applied": "ON_TRACK if monthly util <= 1.05 * (baseline_util * 0.95); else BACKFIRE if monthly util > 1.10 * baseline_util; else AT_RISK",
                    "policy_objective": "ABSENT",
                    "directional_expectation_source": "hardcoded demo stub -5% utilization and -3% cost",
                    "threshold_source": "hardcoded 5% and 10% bands in the staging writer",
                    "status_implied_by_that_rule": exp_status,
                    "matches_stored_status": obs["verdict_status"] == exp_status,
                    "status_validity": status_validity,
                    "result": "INSUFFICIENT_EVIDENCE",
                }
            )

    def write_csv(name, rows):
        path = OUT / name
        if not rows:
            path.write_text("", encoding="utf-8")
            return path
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        return path

    write_csv("POLICY_BASELINE_RECONCILIATION_250.csv", baseline_rows)
    write_csv("POLICY_METRIC_SEMANTICS_250.csv", semantic_rows)
    write_csv("OBSERVATION_RECOMPUTATION_2250.csv", obs_rows)
    write_csv("OBSERVATION_STATUS_AUDIT.csv", status_rows)

    # One real synthetic example for the formula catalog: first policy with claims.
    example = next((r for r in baseline_rows if r["recomputed_claim_count"] > 0), None)
    example_obs = next((r for r in obs_rows if r["policy_id"] == (example or {}).get("policy_id") and r["observation_month"] == "2026-01"), None)

    summary = {
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "environment": "lean_staging",
        "read_only": True,
        "structure_matches_expected": structure_ok,
        "structure": structure,
        "integrity": {
            "null_allowed": null_allowed,
            "negative_allowed": neg_allowed,
            "negative_paid": neg_paid,
            "duplicate_claim_line_keys": dup_lines,
            "future_service_dates_after_2026_11_06": future,
            "feb_29_lines": feb29,
            "service_dates_on_day_15": day15,
            "sources": dict(sources),
        },
        "baseline_arithmetic_fail": baseline_arith_fail,
        "baseline_rows": len(baseline_rows),
        "observation_arithmetic_fail": arith_fail,
        "observation_rows": len(obs_rows),
        "status_rule_mismatches": status_mismatch,
        "scope_fail_policies": scope_fail,
        "observations_not_measurable": not_measurable,
        "observations_fail": len(obs_rows) - not_measurable,
        "enrollment_used": False,
        "example_policy": example["policy_name"] if example else None,
    }
    (OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    write_narratives(summary, example, example_obs, sources)
    print(json.dumps({k: summary[k] for k in (
        "structure_matches_expected", "baseline_arithmetic_fail", "observation_arithmetic_fail",
        "status_rule_mismatches", "scope_fail_policies", "observations_not_measurable", "observations_fail",
        "observation_rows", "baseline_rows",
    )}, indent=2))


def write_narratives(summary, example, example_obs, sources) -> None:
    s = summary["structure"]
    integ = summary["integrity"]
    audit = f"""# Observation calculation audit — lean staging

Audited at {summary['audited_at']}. Read-only. No claims, baselines, observations, policies, or Azure objects were changed. The December 4 demo environment was not used.

This audit separates three questions.

| Question | Result |
|---|---|
| Were the expected records created? | {"Yes" if summary["structure_matches_expected"] else "No — see differences below"} |
| Do the stored numbers match an independent recount of the same formula? | Baselines failing recount: {summary["baseline_arithmetic_fail"]} of {summary["baseline_rows"]}. Observations failing recount: {summary["observation_arithmetic_fail"]} of {summary["observation_rows"]}. |
| Do those numbers measure the intended policy impact? | No. {summary["observations_not_measurable"]} of {summary["observation_rows"]} observations are NOT_MEASURABLE. {summary["observations_fail"]} are FAIL. |

A matching recount means the stored figure is what that formula produces from these claim lines. It does not mean the formula is the right measure, and it does not mean the policy caused the change.

## 1. Record check

| Check | Expected | Found | Match |
|---|---:|---:|---|
| Staging claims | 53949 | {s["claims_total"]} | {s["claims_total"] == 53949} |
| Claims with service date in 2025 | 25692 | {s["claims_2025"]} | {s["claims_2025"] == 25692} |
| Claims with service date in 2026 | 28257 | {s["claims_2026"]} | {s["claims_2026"] == 28257} |
| Claims outside 2025–2026 | 0 | {s["claims_other_year"]} | {s["claims_other_year"] == 0} |
| Demo warehouse copies (`DEMO_SUBSET_COPY`) | 0 | {s["demo_subset_copy"]} | {s["demo_subset_copy"] == 0} |
| General 2025 baseline | 1 | {s["general_baselines_cy2025"]} | {s["general_baselines_cy2025"] == 1} |
| Policy 2025 baselines | 250 | {s["policy_baselines_cy2025"]} | {s["policy_baselines_cy2025"] == 250} |
| Other baselines | 0 | {s["other_baselines"]} | {s["other_baselines"] == 0} |
| Observations | 2250 | {s["observations"]} | {s["observations"] == 2250} |
| Observations per policy | 9 | {s["obs_per_policy_min"]}–{s["obs_per_policy_max"]} | {s["obs_per_policy_min"] == 9 and s["obs_per_policy_max"] == 9} |
| Months outside Jan–Sep 2026 | none | {s["months_outside_jan_sep"] or "none"} | {not s["months_outside_jan_sep"]} |
| Enrollment rows used as a denominator | required for a utilization rate | {s["enrollment_rows"]} | not used |

Claim sources: {json.dumps(integ["sources"])}.

`data_snapshot_id` is absent on every observation. `policy_version_id` was not stored on the observation rows. Configuration version in the CSV is the latest `policy_versions.version_number` when one exists, not a version pinned to the calculation.

## 2. Formula that was actually stored

The staging writer did not call `compute_metrics_from_database_claims` or `compute_verdict`.

Policy baseline, calendar year 2025, codes on the policy:

```
claimants = distinct member_id on matching lines
utilization_per_1k = (claim_lines / claimants) * (1000 / 12)
cost_pmpm = sum(allowed_amount) / (claimants * 12)
```

January–September 2026 observation, same codes, service date inside that month:

```
claimants_m = distinct member_id on matching lines that month
utilization_per_1k = (claim_lines / claimants_m) * 1000
cost_pmpm = sum(allowed_amount) / claimants_m
predicted_utilization = baseline_utilization * 0.95
predicted_cost = baseline_cost * 0.97
```

Status rule actually applied (`v1.0-scoped-month`), not `uepi_api.verdict.compute_verdict`:

```
ON_TRACK  if observed_util <= predicted_util * 1.05
BACKFIRE  if observed_util > baseline_util * 1.10
AT_RISK   otherwise
```

Cost is stored and is not an input to the status.

The product dictionary formula, which was not used, is:

```
util_rate_target_per_1000_mm = (target_claim_lines / policy_eligible_member_months) * 1000
allowed_pmpm_target = target_allowed_amount / policy_eligible_member_months
```

`policy_eligible_member_months` requires enrollment. Staging enrollment row count is {s["enrollment_rows"]}. This audit does not invent that denominator. Where a rate would need it, the result is NOT_MEASURABLE.

A supported alternative, reported in the CSV as `claim_volume_change_pct_vs_monthly_equivalent`, is:

```
baseline_month_equivalent = 2025 matching claim lines / 12
change_pct = (month_claim_lines - baseline_month_equivalent) / baseline_month_equivalent * 100
```

That is a time-normalized claim-count comparison. It is not a utilization rate and it is not a policy effect.

## 3. Independent recount

Each policy's 2025 lines are the distinct claim-line ids whose CPT or HCPCS is in that policy's current scope codes. A line that carries both a CPT and an HCPCS in the same code set is counted once. The same line may appear in more than one policy. That overlap is expected and is not double-counting inside one policy.

Baseline rows whose stored claim count and stored rates match this recount: {summary["baseline_rows"] - summary["baseline_arithmetic_fail"]} of {summary["baseline_rows"]}.
Observation rows whose stored claim count, rates, and −5%/−3% prediction match this recount, with no line outside the month window: {summary["observation_rows"] - summary["observation_arithmetic_fail"]} of {summary["observation_rows"]}.
Stored status values that match the hardcoded rule above: {summary["observation_rows"] - summary["status_rule_mismatches"]} of {summary["observation_rows"]}.

October–December 2026 lines are excluded by the month filter. They do not enter the January–September recount.

## 4. Why a matching recount is still not a valid observation

1. The baseline rate divides by 12 and by the distinct claimants across the whole year. The monthly rate does not divide by 12 and uses only the claimants who had a matching line that month. Those are different exposure bases. Comparing them is not a normalized utilization change.
2. Distinct claimants are not eligible member-months. A member with no claim in the month is missing from the denominator, so the rate rises when the population shrinks. No enrollment denominator was available, and none was invented.
3. {summary["scope_fail_policies"]} of {summary["baseline_rows"]} policies do not have a claims-executable, verified code mapping. A correct count on the wrong codes is a scope failure.
4. Every policy is scored with the same volume formula. Prior authorization, MPPR, NCCI, site of care, pharmacy, and coverage policies need mechanism-specific inputs that are not on these rows. See `POLICY_METRIC_SEMANTICS_250.csv`.
5. The −5% prediction and the ON_TRACK band are hardcoded. They are not a documented policy objective. Status is INSUFFICIENT_EVIDENCE.
6. Almost all lines are `POLICY_MONTHLY_DENSIFY` (about eight lines per policy per month, twelve for the nine showcase policies), plus a light `DATA_GENERATOR` seed and `Q1_2026_DEMO`. The same generator fills the baseline year and the observation year. A difference between them is a property of that generator, not evidence the policy worked.

## 5. Integrity

| Check | Count |
|---|---:|
| Null allowed amount | {integ["null_allowed"]} |
| Negative allowed amount | {integ["negative_allowed"]} |
| Negative paid amount | {integ["negative_paid"]} |
| Duplicate claim_id + claim_line_id | {integ["duplicate_claim_line_keys"]} |
| Service date after 6 Nov 2026 | {integ["future_service_dates_after_2026_11_06"]} |
| 29 February lines | {integ["feb_29_lines"]} |
| Service date on the 15th of the month | {integ["service_dates_on_day_15"]} |

Day-15 concentration is the synthetic generator's midpoint date, not a natural service-date distribution.

## 6. Verdict

Record structure: {"consistent with the expected counts" if summary["structure_matches_expected"] else "not consistent — see the table above"}.
Stored-formula recount: see the fail counts above. Any fail is an arithmetic defect. A pass is only a recount.
Policy impact: not established. Do not read these observations as payer outcomes.

Files:

- `POLICY_BASELINE_RECONCILIATION_250.csv`
- `OBSERVATION_RECOMPUTATION_2250.csv`
- `POLICY_METRIC_SEMANTICS_250.csv`
- `OBSERVATION_STATUS_AUDIT.csv`
- `OBSERVATION_CALCULATION_DEFECTS.md`
- `MEASURES_FORMULAS_AND_EXAMPLES.md`
"""
    (OUT / "OBSERVATION_CALCULATION_AUDIT.md").write_text(audit, encoding="utf-8")

    defects = f"""# Observation calculation defects — lean staging

Ordered by severity. Counts are from the read-only audit at {summary['audited_at']}.

## P0 — Annual baseline rate compared with a monthly rate

The stored baseline utilization divides claim lines by distinct annual claimants and by 12. The stored monthly utilization divides that month's claim lines by that month's distinct claimants and does not divide by 12.

Those denominators are not the same exposure. The persisted `vs_baseline.utilization_change` is the difference of those two rates. It is not a time-normalized change in services per eligible member-month.

Affected rows: all {summary['observation_rows']} observations. Classification: `rate_comparison_validity = FAIL`.

The CSV column `claim_volume_change_pct_vs_monthly_equivalent` is the only time-normalized comparison this audit will stand behind, and it is a claim-count comparison, not a utilization rate.

## P0 — No eligible-member denominator

Enrollment rows on staging: {summary['structure']['enrollment_rows']}.

The dictionary formula needs `policy_eligible_member_months`. The stored formula uses distinct `member_id` values on matching claims. Members with no matching claim drop out of the denominator. This audit does not fill in an enrollment number.

Utilization and PMPM cost on these rows: NOT_MEASURABLE.
Claim-line counts: reconcilable, and labeled as counts.

## P0 — Code scope is not a certified policy scope

Policies whose remediation state is missing or not claims-executable with a verified code map: {summary['scope_fail_policies']} of {summary['baseline_rows']}.

A line is included when its CPT or HCPCS is in `scope.procedure_codes` (or lever targets if scope codes are empty). Place of service, line of business, diagnosis, modifiers, provider, and site restrictions on the policy are not applied.

Scope result on the observation CSV: FAIL for those policies. A numerically matching count on an uncertified code list is not a valid policy observation.

## P0 — Synthetic lines are not policy-effect evidence

Source mix: {json.dumps(integ['sources'])}.

`DEMO_SUBSET_COPY` count is {summary['structure']['demo_subset_copy']}. The legacy demo warehouse (about 3.5 million lines) was not loaded.

`POLICY_MONTHLY_DENSIFY` builds both the 2025 baseline window and the 2026 observation window. Observed differences follow that generator. They are not an estimate of what the policy did.

Effectiveness column on every policy: NOT_SUPPORTED.

## P1 — One generic formula for every mechanism

All 250 policies persist `utilization_per_1k` and `cost_pmpm`. Mechanism-specific measures (authorization decisions, MPPR ranking, NCCI edits, site share, pharmacy sequence, member cost share against enrollment) are not calculated.

Metric validity on every observation: NOT_MEASURABLE. See `POLICY_METRIC_SEMANTICS_250.csv` for the measure each mechanism actually needs.

## P1 — Status is a hardcoded stub

`uepi_api.verdict.compute_verdict` was not called. The writer compared observed utilization with `baseline * 0.95` and used fixed 5% and 10% bands. Cost does not affect the status. There is no stored policy objective.

Status validity: INSUFFICIENT_EVIDENCE on all {summary['observation_rows']} rows.
Rows whose stored label disagrees with even that hardcoded rule: {summary['status_rule_mismatches']}.

## P1 — Future-dated and collapsed service dates

Service dates after 6 Nov 2026: {integ['future_service_dates_after_2026_11_06']}. Those lines sit in October–December observations, which were not created, so they do not enter the 2,250 recomputations. They remain in the 2026 claim total of {summary['structure']['claims_2026']}.

Lines with a service date on the 15th: {integ['service_dates_on_day_15']} of {summary['structure']['claims_total']}. That is the generator midpoint, so within-month runout and partial-month timing cannot be tested on these lines.

## P2 — Arithmetic recount

Baseline rows that do not match an independent code-filtered recount: {summary['baseline_arithmetic_fail']} of {summary['baseline_rows']}.
Observation rows that do not match: {summary['observation_arithmetic_fail']} of {summary['observation_rows']}.

Null allowed amounts: {integ['null_allowed']}. Negative allowed: {integ['negative_allowed']}. Duplicate claim-line keys: {integ['duplicate_claim_line_keys']}.

A zero in the P2 counts means the stored figures are the output of the stored formula. It does not close the P0 defects.

## What this audit does not claim

Measurement correctness and policy effectiveness are different. An observation can match its formula and still provide no evidence that a policy caused the change. These staging rows can show that a record was stored. They cannot be presented as payer outcomes.
"""
    (OUT / "OBSERVATION_CALCULATION_DEFECTS.md").write_text(defects, encoding="utf-8")

    ex_name = example["policy_name"] if example else "(none)"
    ex_block = "No policy with claims was available for a worked staging example."
    if example and example_obs:
        ex_block = f"""Policy: {ex_name}
2025 matching claim lines: {example['recomputed_claim_count']}
2025 distinct claimants: {example['recomputed_distinct_claimants']}
Stored baseline utilization: {example['stored_utilization_per_1k']}
Recount of the stored formula: {example['recomputed_stored_formula_util']}
Formula: ({example['recomputed_claim_count']} / {example['recomputed_distinct_claimants']}) * (1000 / 12) = {example['recomputed_stored_formula_util']}

January 2026 matching claim lines: {example_obs['observed_claim_count']}
Stored January utilization: {example_obs['stored_utilization_per_1k']}
Recount: {example_obs['recomputed_utilization_per_1k']}
Stored minus baseline rate: {example_obs['stored_vs_baseline_util_delta']}

Time-normalized claim-count change, which is the supported comparison:
baseline month equivalent = {example['recomputed_claim_count']} / 12 = {example['monthly_equivalent_claim_count']}
January lines = {example_obs['observed_claim_count']}
change = {example_obs['claim_volume_change_pct_vs_monthly_equivalent']}%

These lines are synthetic. The percentage is not a policy effect.
"""

    measures = f"""# Measures, formulas, and examples

Two layers are listed on purpose.

1. The product dictionary in `packages/common/src/uepi_common/metrics/metric_dictionary.py`. These are the measures HealthForesight defines.
2. The formula that actually produced the 2,250 lean-staging observations. It is a narrower, different calculation.

Illustrative numbers in the dictionary section are invented so the arithmetic can be checked by hand. They are not staging results. The staging section uses one real staging policy and is labeled synthetic.

## How to read a result

| Label | Meaning |
|---|---|
| PASS | Independent recount matches the stored number under the formula named in that row |
| FAIL | Recount does not match, or the comparison is the wrong shape (annual rate versus monthly rate, wrong codes) |
| NOT_MEASURABLE | The required inputs are absent, so no rate should be published |
| INSUFFICIENT_EVIDENCE | A status was stored without a policy objective and a supported expected impact |
| NOT_SUPPORTED | Do not treat the number as evidence the policy worked |

## A. Denominators

### member_months

Formula: sum over members of months enrolled in the period.
Denominator: enrollment table.
Example: 100 members enrolled for all 12 months of 2025 = 1,200 member-months. 100 members enrolled for January only = 100 member-months.
Staging observations: not calculated. Enrollment rows = {summary['structure']['enrollment_rows']}.

### unique_members

Formula: count of distinct member_id with at least one eligible day in the period.
Denominator: enrollment.
Example: 100 people enrolled at any point in 2025 = 100 unique members, even if member-months are 1,200.
Staging: the stored field `unique_members` is distinct claimants on matching claims, not enrolled members.

### policy_eligible_member_months

Formula: member-months remaining after the policy's line of business, market, plan, and network filters.
Denominator: enrollment, filtered.
Example: 1,200 commercial member-months, policy limited to commercial HMO = only the HMO subset.
Staging: not calculated. Line of business on the claim was not applied as an eligibility filter.

## B. Primary outcomes

### util_rate_total_per_1000_mm

Formula: (all claim lines in period / member_months) * 1000.
Unit: lines per 1,000 member-months.
Example: 240 lines, 1,200 member-months. Rate = 240 / 1200 * 1000 = 200.
Staging general baseline uses claimants instead of member-months. See section H.

### util_rate_target_per_1000_mm

Formula: (claim lines in the policy code and eligibility scope / policy_eligible_member_months) * 1000.
Alias stored on observations: `utilization_per_1k`.
Example: 120 targeted lines, 1,000 eligible member-months. Rate = 120.
A later month with 90 targeted lines and 1,000 eligible member-months. Rate = 90.
Change = (90 - 120) / 120 * 100 = -25%.
Staging: the alias is filled with (matching lines / distinct claimants) times 1000, and the baseline further divides by 12. Eligible member-months are not in the denominator. Published utilization on these rows is NOT_MEASURABLE.

### allowed_pmpm_total

Formula: sum of allowed_amount for all lines / member_months.
Example: allowed $120,000, 1,200 member-months. PMPM = 100.
Staging general baseline divides by claimants times 12, not by enrolled member-months.

### allowed_pmpm_target

Formula: sum of allowed_amount on scoped lines / policy_eligible_member_months.
Alias stored on observations: `cost_pmpm`.
Example: scoped allowed $60,000, 1,000 eligible member-months. PMPM = 60.
Staging: divides scoped allowed by distinct claimants (and by 12 on the baseline). NOT_MEASURABLE as PMPM.

### paid_pmpm_total

Formula: sum of paid_amount / member_months.
Example: paid $90,000, 1,200 member-months. PMPM = 75.
Staging observations do not persist paid PMPM. Paid amount is on the claim line and is unused by the observation.

### member_cost_share_pmpm

Formula: sum of member cost share / member_months.
Example: cost share $12,000, 1,200 member-months. PMPM = 10.
Staging: the field exists on claim lines and is not a stored observation metric.

### allowed_total_annualized

Formula: (allowed dollars in the period / months in the period) * 12.
Example: $50,000 allowed in January. Annualized = 50,000 / 1 * 12 = $600,000. This is an extrapolation, not a year of experience.
Staging observations do not persist this. October–December dollars must not be folded into a September annualization. This audit's month filter keeps them out of the 2,250 rows.

## C. Mix

### Site-of-care shares

Formula: scoped lines with that site / all scoped lines.
Sites in the dictionary: ER, HOPD, ASC.
Example: 40 HOPD lines and 60 freestanding lines. HOPD share = 40%.
`soc_share_delta_target` = post share minus baseline share. Example: baseline 70% HOPD, observed 40% HOPD, delta = -30 percentage points.
Staging: place of service is on the line. Site share is not stored. A site-of-care policy scored only on total volume is NOT_MEASURABLE for its mechanism.

### inn_share_target

Formula: in-network scoped lines / all scoped lines.
Example: 80 in-network of 100 scoped lines = 80%.
Staging: `in_network` is on the line and is not an observation metric.

### oon_leakage_rate_target_per_1000_mm

Formula: (out-of-network scoped lines / policy_eligible_member_months) * 1000.
Example: 20 out-of-network lines, 1,000 member-months. Rate = 20.
Staging: not calculated.

### service_share_target

Formula: lines for one code or code group / all scoped lines.
Example: 72148 is 30 of 100 MRI lines = 30%.
Staging: not calculated.

### top10_provider_share_target

Formula: scoped lines from the ten providers with the most scoped lines / all scoped lines.
Example: top ten providers have 450 of 1,000 lines = 45%.
Staging: not calculated.

### provider_hhi_target

Formula: sum of squared provider shares. 0 is fully dispersed, 1 is a single provider.
Example: two providers at 50% each. HHI = 0.25 + 0.25 = 0.50.
Staging: not calculated.

## D. Substitution and timing

### substitution_uplift_per_1000_mm

Formula: observed rate of the substitute service minus the rate expected from baseline trend.
Example: baseline substitute rate 10 per 1,000, trend-expected 11, observed 18. Uplift = 7 per 1,000.
Staging: not calculated. No counterfactual series is stored.

### deferral_index_target

Formula: post 30-day targeted rate / baseline 30-day targeted rate, or a shift in time from the index date to the service.
Example: baseline 30-day rate 40, post 20. Index = 0.5, which is a delay only if the denominator is the same eligible population.
Staging: not calculated. Service dates are concentrated on the 15th, so timing shift cannot be seen.

## E. Behavior

### provider_archetype_share

Formula: providers in a class / providers in scope.
Example: 15 of 60 providers classed as resistant = 25%.
Staging: not calculated. No archetype assignment is on these rows.

### provider_ordering_intensity_target_per_1000_mm

Formula: (scoped lines attributed to the provider / member-months of that provider's population) * 1000.
Example: 30 lines, 200 attributed member-months. Intensity = 150.
Staging: not calculated.

### patient_response_share

Formula: member-months in a segment who show the response / member-months in the segment.
Example: 100 of 500 member-months substitute to another site = 20%.
Staging: not calculated.

## F. Prediction and learning

### Absolute and percent change

```
absolute = observed - baseline
percent = (observed - baseline) / baseline * 100
```

Example: baseline 120 per 1,000 member-months, observed 108.
Absolute = -12. Percent = (108 - 120) / 120 * 100 = -10%.
Both numbers must already be rates on the same denominator and the same period length. An annual count minus a monthly count is not this formula.

### prediction_error_util_pp

Formula: observed percent change minus predicted percent change, in percentage points.
Example: predicted -8%, observed -10%. Error = -2 percentage points. The prediction was slightly too high.
Staging: predicted percent is hardcoded at -5% utilization. The stored comparison is a difference of rates, not this percentage-point error.

### prediction_error_cost_pmpm

Formula: observed PMPM change minus predicted PMPM change.
Example: predicted -$2.00 PMPM, observed -$1.00 PMPM. Error = +$1.00 PMPM.
Staging: predicted cost is hardcoded at 97% of the baseline rate. It is not an estimated effect.

### confidence_score

Formula: a weighted composite of data sufficiency, analog strength, and uncertainty width, from 0 to 100.
Example: thin data and a wide interval should score low even when the point estimate is large.
Staging observations: not stored. Do not treat a populated verdict as high confidence.

## G. Mechanism measures that staging did not calculate

These are the calculations a policy of that type needs. The staging rows do not contain them. Using the generic volume formula instead is NOT_MEASURABLE, not a simplified version of the same measure.

### Prior authorization

Approval rate = approvals / decisions.
Denial rate = denials / decisions.
Example: 70 approvals and 30 denials. Approval rate = 70%. A drop in MRI claim lines is not an approval rate.
Required data absent: authorization requests and decisions.

### Coverage and clinical criteria

Criteria met rate = scoped services meeting diagnosis, age, and frequency rules / scoped services.
Example: 40 of 100 lumbar MRI lines meet the criteria. Rate = 40%.
Required data absent: diagnosis and the criteria schedule.

### Site of care

Use the site-share formula in section C.
Example: infusion HOPD share moves from 80% to 50% on the same eligible drug codes, with member-months held constant.
Required for a valid share: eligible drug or service definition and place of service. Volume change alone is the wrong measure.

### MPPR and other payment policy

Identify same-day, same-provider procedure groups. Rank lines. Apply the reduction to the lower-ranked allowed amounts.
Example: two procedures the same day, allowed $1,000 and $600. Second line pays at 50% = $300. Reduction = $300.
A lower claim count is not this reduction.
Required data absent: grouping key, rank, and the fee schedule.

### NCCI procedure-to-procedure

Pair rate = column-2 lines billed with their column-1 partner on the same day / column-1 lines.
Example: 10 column-2 lines paired with the column-1 code, out of 100 column-1 lines. Pair rate = 10%.
Required data absent: the PTP edit table and modifiers.

### NCCI medically unlikely units

Excess units = max(0, units on the date of service - MUE value).
Example: MUE is 1, billed units are 3. Excess = 2.
Required data absent: the MUE table. Units exist on the claim and were not compared with an edit.

### Pharmacy

Step completion, quantity limit, and days supply are product-level.
Example: 25 of 100 first fills have a required prior product within 180 days. Step rate = 25%.
Required data absent: NDC or a drug-product history. A HCPCS J-code count is not a step-therapy result.

### Benefit and cost sharing

Use `member_cost_share_pmpm`.
Example: baseline member share $15 PMPM, observed $22 PMPM on the same eligible member-months. Change = +$7 PMPM.
Required data absent: the enrollment denominator. The cost-share field on the line is not enough.

### Network

Use `inn_share_target`.
Example: in-network share of scoped imaging moves from 90% to 84%.
Required data absent as a stored metric. The flag exists on the line.

### Administrative and compliance

These policies need process evidence: documentation rate, turnaround, audit pass rate.
Example: 92 of 100 sampled cases have the required attachment. Rate = 92%.
Claim counts do not measure this. Required data absent.

### Quantity limit

Excess = max(0, units or days supply in the limit window − allowed quantity).
Example: limit is 30 tablets / 30 days, fill is 90. Excess = 60.
A lower claim count is not evidence the limit was applied.

### Frequency or visit limit

Excess visits = max(0, services in the lookback − allowed visits).
Example: 12 chiropractic visits allowed per year, 15 billed. Excess = 3.
Required data absent: the limit value and the member's prior services.

### Payment policy other than MPPR

Allowed after the rule minus the allowed that would have been paid without the rule, on the same lines.
Example: a DRG case priced at $8,000 instead of $10,000. Reduction = $2,000.
Required data absent: the fee schedule and the grouping key.

### Benefit design

Covered-service rate and member cost share on the eligible population.
Example: 95 of 100 preventive services adjudicated at zero member cost share. Rate = 95%.
Required data absent: the benefit decision. Enrollment is empty.

### Access

Members meeting the standard / members in scope.
Example: 860 of 1,000 members have a behavioral-health appointment within 10 days. Rate = 86%.
Required data absent: appointment or adequacy events.

### Care management program

Program participants and the stated outcome, each with its own denominator.
Example: 400 members enrolled, 40% with a completed care plan. Claim volume in the same months is not the enrollment rate.
Required data absent: program enrollment.

### Coding and billing edit

Fail rate = lines failing the edit / lines subject to the edit.
Example: 12 of 200 lines fail the edit. Fail rate = 6%.
Required data absent: the edit table. NCCI PTP and MUE are the specific forms of this measure.

### Referral

Referral present rate = scoped services with a required referral / scoped services.
Example: 70 of 100 specialty visits have a referral. Rate = 70%.
Required data absent: referral records.

### Provider eligibility

Eligible-provider share = scoped services by an eligible provider / scoped services.
Example: 88 of 100 services are rendered by a credentialed provider. Share = 88%.
Required data absent: provider eligibility.

## H. Formula actually used on staging

```
baseline utilization = (2025 matching lines / 2025 distinct claimants) * (1000 / 12)
baseline cost = 2025 matching allowed / (2025 distinct claimants * 12)
month utilization = (month matching lines / month distinct claimants) * 1000
month cost = month matching allowed / month distinct claimants
predicted utilization = baseline utilization * 0.95
predicted cost = baseline cost * 0.97
```

Status:

```
ON_TRACK if month utilization <= predicted utilization * 1.05
BACKFIRE if month utilization > baseline utilization * 1.10
AT_RISK otherwise
```

Worked staging example. Synthetic data. Not a policy effect.

```
{ex_block}
```

## I. What may be compared

| Comparison | Valid when |
|---|---|
| 2025 claim-line count with January 2026 claim-line count | Only after dividing the 2025 count by 12, and only as a volume comparison |
| 2025 utilization rate with January utilization rate | Only when both use eligible member-months and the same scope filters |
| Either rate with a verdict | Only when the expected direction and the threshold come from the policy's own objective |
| A difference between 2025 and 2026 on these staging rows | As a check that the pipeline stored a number. Not as evidence of policy impact |

October–December 2026 claim lines stay out of January–September measures, out of any annualization of those months, and out of a current-period rate.
"""
    (OUT / "MEASURES_FORMULAS_AND_EXAMPLES.md").write_text(measures, encoding="utf-8")


if __name__ == "__main__":
    main()
