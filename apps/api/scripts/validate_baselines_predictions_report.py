#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate stored baselines vs recomputed DB aggregates and policy predictive-impact checks.

Fully executable from any directory:
  python3 apps/api/scripts/validate_baselines_predictions_report.py [--tenant UUID] [--json]

Azure DB example:
  DATABASE_URL='postgresql://...' python3 apps/api/scripts/validate_baselines_predictions_report.py --tenant <uuid>
  # or:
  python3 .../validate_baselines_predictions_report.py --database-url 'postgresql://...' --tenant <uuid>

Loads apps/api/.env if present (does not override existing env vars). --database-url wins after .env.
Requires: DATABASE_URL (postgresql://...) with sslmode if needed, same as the API.

Exit codes: 0 = all checks passed or skipped; 1 = at least one failed check; 2 = setup/DB error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

# ---------------------------------------------------------------------------
# Bootstrap: API package root and optional .env before importing uepi_api
# ---------------------------------------------------------------------------
_SCRIPT_FILE = Path(__file__).resolve()
_API_ROOT = _SCRIPT_FILE.parent.parent  # apps/api
_REPO_ROOT = _API_ROOT.parent.parent  # monorepo root

for _p in (_API_ROOT / "src", _REPO_ROOT / "packages" / "common" / "src"):
    sp = str(_p)
    if sp not in sys.path:
        sys.path.insert(0, sp)


def _load_env_file(path: Path) -> None:
    """Minimal KEY=VALUE loader; does not override existing os.environ."""
    if not path.is_file():
        return
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
            val = val[1:-1]
        if key not in os.environ:
            os.environ[key] = val


def _resolve_tenant_id(db: Any, explicit: Optional[str]) -> Optional[UUID]:
    from uepi_api.models.baseline import Baseline
    from uepi_api.models.policy import Policy

    if explicit:
        return UUID(explicit)
    row = db.query(Baseline.tenant_id).first()
    if row and row[0]:
        return row[0]
    row = db.query(Policy.tenant_id).distinct().first()
    if row and row[0]:
        return row[0]
    try:
        from uepi_api.storage_auth import DEFAULT_TENANT_ID

        return DEFAULT_TENANT_ID
    except Exception:
        return None


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    s = str(s).replace("Z", "+00:00")
    if "T" in s:
        return datetime.fromisoformat(s).date()
    return datetime.fromisoformat(s).date()


def _num(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _close(a: Optional[float], b: Optional[float], rel_tol: float = 0.02, abs_tol: float = 1e-3) -> bool:
    if a is None or b is None:
        return False
    if abs(a - b) <= abs_tol:
        return True
    if b == 0:
        return abs(a) <= abs_tol
    return abs(a - b) / max(abs(b), 1e-9) <= rel_tol


def _compare_baseline_block(
    stored: Dict[str, Any],
    fresh: Dict[str, Any],
    keys: List[Tuple[str, str]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for key_name, display in keys:
        sv = _num(stored.get(key_name))
        fv = _num(fresh.get(key_name))
        ok = _close(sv, fv) if sv is not None and fv is not None else (sv is None and fv is None)
        rows.append(
            {
                "metric": display,
                "key": key_name,
                "stored": sv,
                "recomputed": fv,
                "match": bool(ok) if sv is not None and fv is not None else None,
            }
        )
    return rows


def _baseline_metric_keys_general() -> List[Tuple[str, str]]:
    return [
        ("unique_members", "unique_members"),
        ("member_months", "member_months"),
        ("total_claims", "total_claims"),
        ("util_rate_total_per_1000_mm", "util_rate_total_per_1000_mm (claims per 1k MM)"),
        ("allowed_pmpm_total", "allowed_pmpm_total"),
        ("paid_pmpm_total", "paid_pmpm_total"),
    ]


def _baseline_metric_keys_policy() -> List[Tuple[str, str]]:
    return [
        ("unique_members", "unique_members"),
        ("member_months", "member_months"),
        ("total_claims", "total_claims"),
        ("util_rate_target_per_1000_mm", "util_rate_target_per_1000_mm"),
        ("allowed_pmpm_target", "allowed_pmpm_target"),
        ("paid_pmpm_target", "paid_pmpm_target"),
    ]


def validate_general_baseline(db: Any, tenant_id: UUID) -> Tuple[List[Dict[str, Any]], str]:
    from uepi_api.services.database_baseline_computation import compute_general_baseline_from_database
    from uepi_api.storage_baselines import get_latest_baseline

    rows: List[Dict[str, Any]] = []
    bl = get_latest_baseline(tenant_id, policy_id=None)
    if not bl:
        return rows, "No general baseline row found for tenant."
    ws, we = _parse_date(bl.get("window_start_date")), _parse_date(bl.get("window_end_date"))
    if not ws or not we:
        return rows, "General baseline missing parseable window dates."
    stored = bl.get("baseline_metrics") or {}
    fresh = compute_general_baseline_from_database(tenant_id, ws, we, db)
    if not fresh:
        rows.extend(
            [
                {**r, "section": "general"}
                for r in _compare_baseline_block(stored, {}, _baseline_metric_keys_general())
            ]
        )
        return rows, "Recompute returned empty (no claims in window)."
    rows.extend(
        [
            {**r, "section": "general"}
            for r in _compare_baseline_block(stored, fresh, _baseline_metric_keys_general())
        ]
    )
    mismatches = [r for r in rows if r.get("match") is False]
    summary = (
        f"General baseline window {ws} .. {we}: {len(mismatches)} metric(s) diverge from recomputation."
        if mismatches
        else f"General baseline window {ws} .. {we}: stored matches recomputation within tolerance."
    )
    return rows, summary


def validate_policy_baselines(db: Any, tenant_id: UUID) -> Tuple[List[Dict[str, Any]], List[str]]:
    from uepi_api.models.policy import Policy
    from uepi_api.services.database_baseline_computation import compute_policy_specific_baseline_from_database
    from uepi_api.storage_baselines import get_latest_baseline
    from uepi_api.storage_policies import get_policy

    all_rows: List[Dict[str, Any]] = []
    summaries: List[str] = []
    policies = db.query(Policy).filter(Policy.tenant_id == tenant_id).all()
    for pol in policies:
        bl = get_latest_baseline(tenant_id, policy_id=pol.id)
        if not bl:
            summaries.append(f"Policy {pol.id}: no policy-specific baseline.")
            continue
        ws, we = _parse_date(bl.get("window_start_date")), _parse_date(bl.get("window_end_date"))
        if not ws or not we:
            summaries.append(f"Policy {pol.id}: baseline window dates missing.")
            continue
        policy_dict = get_policy(pol.id, tenant_id)
        scope = None
        if policy_dict:
            scope = policy_dict.get("scope") or (policy_dict.get("metadata") or {}).get("scope")
        stored = bl.get("baseline_metrics") or {}
        fresh = compute_policy_specific_baseline_from_database(
            tenant_id=tenant_id,
            policy_id=pol.id,
            start_date=ws,
            end_date=we,
            policy_scope=scope or {},
            db=db,
            policy=policy_dict,
        )
        if not fresh:
            summaries.append(
                f"Policy {pol.id} ({getattr(pol, 'name', '') or 'unnamed'}): "
                f"recompute empty for window {ws}..{we}."
            )
            continue
        pr = _compare_baseline_block(stored, fresh, _baseline_metric_keys_policy())
        for r in pr:
            r["section"] = f"policy:{pol.id}"
        all_rows.extend(pr)
        mismatches = [r for r in pr if r.get("match") is False]
        name = getattr(pol, "name", "") or str(pol.id)[:8]
        if mismatches:
            summaries.append(f"Policy {name}: {len(mismatches)} baseline metric(s) diverge.")
        else:
            summaries.append(f"Policy {name}: policy baseline matches recomputation.")
    return all_rows, summaries


def _prediction_baseline_util(base: Dict[str, Any]) -> Optional[float]:
    for k in (
        "utilization_per_1k",
        "util_rate_target_per_1000_mm",
        "util_rate_total_per_1000_mm",
    ):
        v = _num(base.get(k))
        if v is not None:
            return v
    return None


def _prediction_baseline_cost_pmpm(base: Dict[str, Any]) -> Optional[float]:
    for k in (
        "cost_pmpm",
        "allowed_pmpm_target",
        "allowed_pmpm_total",
        "paid_pmpm_target",
        "paid_pmpm_total",
    ):
        v = _num(base.get(k))
        if v is not None:
            return v
    return None


def _prediction_baseline_members(base: Dict[str, Any]) -> Optional[float]:
    for k in ("member_count", "unique_members"):
        v = _num(base.get(k))
        if v is not None:
            return v
    return None


def validate_predictions(db: Any, tenant_id: UUID) -> Tuple[List[Dict[str, Any]], List[str]]:
    from sqlalchemy import desc

    from uepi_api.models.policy import Policy
    from uepi_api.models.predicted_impact import PolicyPredictedImpact

    rows: List[Dict[str, Any]] = []
    summaries: List[str] = []
    policies = db.query(Policy).filter(Policy.tenant_id == tenant_id).all()
    for pol in policies:
        pred = (
            db.query(PolicyPredictedImpact)
            .filter(
                PolicyPredictedImpact.tenant_id == tenant_id,
                PolicyPredictedImpact.policy_id == pol.id,
            )
            .order_by(desc(PolicyPredictedImpact.predicted_at))
            .first()
        )
        if not pred:
            summaries.append(f"Policy {pol.id}: no predicted_impact row.")
            continue
        raw = pred.metrics_json or {}
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = {}
        m = raw.get("metrics", raw) if isinstance(raw, dict) else {}
        if not isinstance(m, dict):
            m = {}
        base = raw.get("baseline_reference") if isinstance(raw, dict) else None
        if not isinstance(base, dict):
            base = {}

        util_base = _prediction_baseline_util(base)
        cost_base = _prediction_baseline_cost_pmpm(base)
        members = _prediction_baseline_members(base)

        pct_u = _num(m.get("utilization_change_pct"))
        pct_c = _num(m.get("cost_change_pct"))
        du = _num(m.get("utilization_change_per_1k"))
        dc = _num(m.get("cost_change_pmpm"))
        dtot = _num(m.get("cost_change_total"))

        exp_du = util_base * (pct_u / 100.0) if util_base is not None and pct_u is not None else None
        exp_dc = cost_base * (pct_c / 100.0) if cost_base is not None and pct_c is not None else None
        exp_tot = (dc * members * 12) if dc is not None and members is not None else None

        ok_all = True

        def _row(name: str, got: Any, exp: Any, match: Optional[bool]) -> None:
            nonlocal ok_all
            if match is False:
                ok_all = False
            rows.append(
                {
                    "section": f"prediction:{pol.id}",
                    "check": name,
                    "got": got,
                    "expected": exp,
                    "match": match,
                }
            )

        _row(
            "utilization_change_per_1k vs baseline×util_pct",
            du,
            exp_du,
            _close(du, exp_du, rel_tol=0.05, abs_tol=1e-2) if du is not None and exp_du is not None else None,
        )
        _row(
            "cost_change_pmpm vs baseline×cost_pct",
            dc,
            exp_dc,
            _close(dc, exp_dc, rel_tol=0.05, abs_tol=1e-2) if dc is not None and exp_dc is not None else None,
        )
        _row(
            "cost_change_total vs Δpmpm×members×12",
            dtot,
            exp_tot,
            _close(dtot, exp_tot, rel_tol=0.05, abs_tol=1e-2) if dtot is not None and exp_tot is not None else None,
        )

        # uepi_common.analytics.predicted_impact: cost_change_pct = utilization_change_pct * 0.9
        if pct_c is not None and pct_u is not None:
            exp_c = pct_u * 0.9
            _row(
                "cost_change_pct vs util_change_pct×0.9",
                pct_c,
                exp_c,
                _close(pct_c, exp_c, rel_tol=0.05, abs_tol=0.5),
            )

        prov = raw.get("provider_response") if isinstance(raw, dict) else None
        if isinstance(prov, dict):
            c1 = _num(prov.get("compliant_pct"))
            c2 = _num(prov.get("adaptive_pct"))
            c3 = _num(prov.get("resistant_pct"))
            c4 = _num(prov.get("circumvention_pct"))
            if all(x is not None for x in (c1, c2, c3, c4)):
                got_sum = float(c1 + c2 + c3 + c4)
                _row(
                    "provider_response_pct_sum vs 100",
                    got_sum,
                    100.0,
                    _close(got_sum, 100.0, rel_tol=0.02, abs_tol=2.0),
                )

        pat = raw.get("patient_response") if isinstance(raw, dict) else None
        if isinstance(pat, dict):
            for label, key in (
                ("patient_response defer_rate in [0,1]", "defer_rate"),
                ("patient_response substitute_rate in [0,1]", "substitute_rate"),
                ("patient_response er_fallback_rate in [0,1]", "er_fallback_rate"),
            ):
                rv = _num(pat.get(key))
                if rv is not None:
                    in_range = 0.0 <= rv <= 1.0
                    _row(label, rv, "[0,1]", in_range)

        pname = getattr(pol, "name", "") or str(pol.id)[:8]
        if base and util_base is not None:
            summaries.append(
                f"Policy {pname}: predictive impact checks {'PASS' if ok_all else 'FAIL'}."
            )
        else:
            summaries.append(
                f"Policy {pname}: partial/skip (missing baseline_reference or util baseline keys)."
            )
    return rows, summaries


def _count_failures(
    g_rows: List[Dict[str, Any]],
    p_rows: List[Dict[str, Any]],
    pred_rows: List[Dict[str, Any]],
) -> int:
    n = 0
    for r in g_rows:
        if r.get("match") is False:
            n += 1
    for r in p_rows:
        if r.get("match") is False:
            n += 1
    for r in pred_rows:
        if r.get("match") is False:
            n += 1
    return n


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate baselines and predicted impacts against DB recomputation and internal math.",
    )
    parser.add_argument(
        "--tenant",
        type=str,
        default=None,
        help="Tenant UUID (default: first tenant in baselines, else policies, else DEFAULT_TENANT_ID)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON only (stdout)")
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help=f"Path to .env (default: {_API_ROOT / '.env'})",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="PostgreSQL URL (overrides DATABASE_URL after .env load; use for Azure)",
    )
    args = parser.parse_args()

    env_path = Path(args.env_file) if args.env_file else (_API_ROOT / ".env")
    _load_env_file(env_path)
    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url.strip()

    if not (os.environ.get("DATABASE_URL") or "").strip():
        print(
            "ERROR: DATABASE_URL is not set. Export it, add to apps/api/.env, or pass --database-url.",
            file=sys.stderr,
        )
        return 2

    try:
        from uepi_api.database import SessionLocal
    except Exception as e:
        print(f"ERROR: cannot import API database module: {e}", file=sys.stderr)
        return 2

    db = SessionLocal()
    try:
        try:
            tenant_id = _resolve_tenant_id(db, args.tenant)
        except ValueError as e:
            print(f"ERROR: invalid --tenant UUID: {e}", file=sys.stderr)
            return 2

        if not tenant_id:
            print(
                "ERROR: no tenant_id. Pass --tenant <UUID> or ensure baselines/policies exist.",
                file=sys.stderr,
            )
            return 2

        g_rows, g_sum = validate_general_baseline(db, tenant_id)
        p_rows, p_sums = validate_policy_baselines(db, tenant_id)
        pred_rows, pred_sums = validate_predictions(db, tenant_id)
        failures = _count_failures(g_rows, p_rows, pred_rows)

        out: Dict[str, Any] = {
            "tenant_id": str(tenant_id),
            "env_file_loaded": str(env_path) if env_path.is_file() else None,
            "general_baseline": {"summary": g_sum, "metrics": g_rows},
            "policy_baselines": {"summaries": p_sums, "metrics": p_rows},
            "predictions": {"summaries": pred_sums, "checks": pred_rows},
            "failed_checks": failures,
            "overall_pass": failures == 0,
        }

        if args.json:
            print(json.dumps(out, indent=2, default=str))
            return 0 if failures == 0 else 1

        print("=" * 80)
        print("BASELINE & PREDICTION VALIDATION REPORT")
        print("Tenant:", tenant_id)
        print("API root:", _API_ROOT)
        print("Env file:", env_path if env_path.is_file() else "(not found; using process env only)")
        print("=" * 80)
        print("\n## General baseline\n")
        print(g_sum)
        for r in g_rows:
            if r.get("match") is not None:
                print(
                    f"  {r['metric']}: stored={r['stored']} recomputed={r['recomputed']} "
                    f"match={r['match']}"
                )

        print("\n## Policy baselines\n")
        for s in p_sums:
            print(f"  - {s}")
        for r in p_rows:
            if r.get("match") is not None:
                print(
                    f"  [{r['section']}] {r['metric']}: stored={r['stored']} "
                    f"recomputed={r['recomputed']} match={r['match']}"
                )

        print("\n## Predictive impact (policy-level)\n")
        for s in pred_sums:
            print(f"  - {s}")
        for r in pred_rows:
            if r.get("match") is not None:
                print(
                    f"  [{r['section']}] {r['check']}: got={r['got']} expected={r['expected']} "
                    f"match={r['match']}"
                )

        print("\n" + "=" * 80)
        print(f"Failed numeric checks: {failures}")
        print(
            "Note: Does not test real-world predictive accuracy—only DB reconciliation and "
            "stored prediction arithmetic."
        )
        print("=" * 80)
        return 0 if failures == 0 else 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
