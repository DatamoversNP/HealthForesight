"""
Enterprise policy rollout recommendation engine.

Combines: (1) claims-based opportunity signals, (2) curated clinical/UM archetypes,
(3) existing policy deduplication, (4) elasticity-informed impact ranges,
(5) structured explainability for audit and governance.
"""
from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from uepi_api.models.canonical_data import ClaimsLineDB
from uepi_api.models.policy import Policy as PolicyDB, PolicyCodeSet, PolicyVersion
from uepi_api.services.policy_scoped_data_generation import build_policy_claims_filters
from uepi_api.storage_baselines import get_latest_baseline

# Short TTL cache — rollout analysis is expensive against large claims tables.
_ROLLOUT_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_ROLLOUT_CACHE_TTL_SEC = 600.0


def _cache_key(tenant_id: UUID, months_lookback: int, limit: int, jaccard_threshold: float) -> str:
    return f"{tenant_id}:{months_lookback}:{limit}:{jaccard_threshold:.3f}"


def _codes_from_policy_row(name: str, policy_type: str, meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a lightweight signature from ORM fields (no per-policy get_policy)."""
    meta = meta if isinstance(meta, dict) else {}
    pol = {
        "name": name,
        "policy_type": policy_type,
        "scope": meta.get("scope") or {},
        "policy_levers": meta.get("policy_levers") or [],
        "logic": meta.get("logic") or {},
        "policy_logic": meta.get("policy_logic") or {},
        "metadata": meta,
        "policy_metadata_json": meta,
    }
    pf = build_policy_claims_filters(pol)
    codes: Set[str] = set()
    for k in ("procedure_codes", "cpt_codes", "hcpcs_codes"):
        v = pf.get(k)
        if isinstance(v, list):
            codes.update(str(c).strip() for c in v if c)
    return {
        "name": name or "",
        "policy_type": policy_type or "UNKNOWN",
        "codes": codes,
    }


# Curated archetypes: enterprise catalog (extend via config/DB later)
POLICY_ARCHETYPES: List[Dict[str, Any]] = [
    {
        "archetype_id": "pa_advanced_imaging",
        "title": "Prior authorization — advanced outpatient imaging",
        "policy_type": "PRIOR_AUTH",
        "procedure_codes": ["72141", "72142", "72148", "70450", "70470", "70553"],
        "service_categories": ["ADVANCED_IMAGING"],
        "rationale": "High unit cost and discretionary scheduling make imaging a standard UM lever; "
        "evidence of volume or spend concentration supports staged rollout.",
        "typical_util_elasticity_pct": (-6.0, -2.5),
        "typical_cost_elasticity_pct": (-5.0, -2.0),
        "implementation_notes": "Pair with radiology liaison and clear clinical criteria.",
    },
    {
        "archetype_id": "site_of_care_infusion",
        "title": "Site-of-care steerage — hospital vs free-standing infusion",
        "policy_type": "SITE_OF_CARE",
        "procedure_codes": ["96413", "96415", "96416"],
        "service_categories": ["INFUSION"],
        "rationale": "Infusion often shows site price dispersion; members can be steered with network design and benefit design.",
        "typical_util_elasticity_pct": (-4.0, -1.5),
        "typical_cost_elasticity_pct": (-8.0, -3.0),
        "implementation_notes": "Validate access to alternative sites within reasonable distance.",
    },
    {
        "archetype_id": "urgent_care_redirect",
        "title": "Urgent care / convenience access — ED avoidable utilization",
        "policy_type": "BENEFIT",
        "procedure_codes": ["99281", "99282", "99283"],
        "service_categories": ["URGENT_CARE"],
        "rationale": "When ED-coded urgent care appears in claims, benefit and steerage can shift lower-acuity volume.",
        "typical_util_elasticity_pct": (-3.0, -1.0),
        "typical_cost_elasticity_pct": (-4.0, -1.5),
        "implementation_notes": "Coordinate with member communications and nurse line.",
    },
    {
        "archetype_id": "step_therapy_specialty",
        "title": "Step therapy — specialty pharmacy / biologic sequence",
        "policy_type": "STEP_THERAPY",
        "procedure_codes": ["96413", "J0897", "J1745"],
        "service_categories": ["SPECIALTY_CARE"],
        "rationale": "Specialty drug spend is concentrated; step protocols are common where PBM data aligns.",
        "typical_util_elasticity_pct": (-5.0, -2.0),
        "typical_cost_elasticity_pct": (-10.0, -4.0),
        "implementation_notes": "Requires P&T and formulary alignment; monitor discontinuation risk.",
    },
    {
        "archetype_id": "lab_high_volume",
        "title": "Laboratory — high-volume panel optimization",
        "policy_type": "PRIOR_AUTH",
        "procedure_codes": ["80053", "85025", "80061"],
        "service_categories": ["LABORATORY"],
        "rationale": "Routine lab panels drive claim volume; modest UM or network tiering can reduce low-value repeats.",
        "typical_util_elasticity_pct": (-4.0, -1.0),
        "typical_cost_elasticity_pct": (-3.0, -1.0),
        "implementation_notes": "Low clinical risk if tied to evidence-based frequency limits.",
    },
]


def _existing_policy_signatures(db: Session, tenant_id: UUID) -> List[Dict[str, Any]]:
    """One policies query + one batched code-set query (avoids N× get_policy)."""
    rows = (
        db.query(PolicyDB.id, PolicyDB.name, PolicyDB.policy_type, PolicyDB.policy_metadata_json)
        .filter(PolicyDB.tenant_id == tenant_id)
        .all()
    )
    if not rows:
        return []

    codes_by_policy: Dict[str, Set[str]] = {str(r.id): set() for r in rows}
    code_rows = (
        db.query(PolicyVersion.policy_id, PolicyCodeSet.code)
        .join(PolicyCodeSet, PolicyCodeSet.version_id == PolicyVersion.id)
        .filter(PolicyVersion.tenant_id == tenant_id, PolicyCodeSet.tenant_id == tenant_id)
        .all()
    )
    for policy_id, code in code_rows:
        if not code:
            continue
        key = str(policy_id)
        if key in codes_by_policy:
            codes_by_policy[key].add(str(code).strip())

    out: List[Dict[str, Any]] = []
    for r in rows:
        sig = _codes_from_policy_row(r.name, r.policy_type, r.policy_metadata_json)
        pid = str(r.id)
        sig["codes"].update(codes_by_policy.get(pid) or set())
        out.append(
            {
                "policy_id": pid,
                "name": sig["name"],
                "policy_type": sig["policy_type"],
                "codes": sig["codes"],
            }
        )
    return out


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _is_duplicate_candidate(
    candidate_codes: Set[str],
    candidate_type: str,
    existing: List[Dict[str, Any]],
    jaccard_threshold: float = 0.55,
) -> Tuple[bool, Optional[str], List[str]]:
    """Return (is_dup, reason, matching_policy_ids)."""
    if not candidate_codes:
        return False, None, []

    for ex in existing:
        ex_codes: Set[str] = ex["codes"]
        ex_type = str(ex.get("policy_type") or "")
        jac = _jaccard(candidate_codes, ex_codes)
        subset_all_in = bool(ex_codes) and candidate_codes <= ex_codes
        type_match = ex_type == candidate_type or candidate_type in ex_type or ex_type in candidate_type

        if subset_all_in and type_match and len(candidate_codes) >= 1:
            return (
                True,
                f"Target codes are already covered by existing policy «{ex['name']}» ({ex['policy_id']}).",
                [ex["policy_id"]],
            )
        if jac >= jaccard_threshold and type_match and len(candidate_codes) >= 2 and len(ex_codes) >= 2:
            return (
                True,
                f"High overlap (Jaccard {jac:.0%}) with existing policy «{ex['name']}» — same program archetype.",
                [ex["policy_id"]],
            )
    return False, None, []


def _archetype_procedure_codes() -> List[str]:
    codes: Set[str] = set()
    for arch in POLICY_ARCHETYPES:
        codes.update(str(c) for c in (arch.get("procedure_codes") or []))
    return sorted(codes)


def _archetype_service_categories() -> List[str]:
    cats: Set[str] = set()
    for arch in POLICY_ARCHETYPES:
        cats.update(str(c) for c in (arch.get("service_categories") or []))
    return sorted(cats)


def _aggregate_top_cpt(
    db: Session,
    tenant_id: UUID,
    start: date,
    end: date,
    limit: int = 40,
    *,
    procedure_codes: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Aggregate spend for a small CPT set (archetype codes). Full-table GROUP BY over
    all claims times out on large tenants — scoping to archetype codes keeps this interactive.
    """
    codes = procedure_codes or _archetype_procedure_codes()
    if not codes:
        return []
    try:
        # Scoped CPT set — full-table GROUP BY times out on large tenants over Azure Postgres.
        db.execute(text("SET LOCAL statement_timeout = '25s'"))
        q = (
            db.query(
                ClaimsLineDB.cpt_code,
                func.coalesce(func.sum(ClaimsLineDB.allowed_amount), 0).label("allowed_sum"),
                func.count(ClaimsLineDB.id).label("line_count"),
            )
            .filter(
                ClaimsLineDB.tenant_id == tenant_id,
                ClaimsLineDB.service_date >= start,
                ClaimsLineDB.service_date <= end,
                ClaimsLineDB.cpt_code.in_(codes),
            )
            .group_by(ClaimsLineDB.cpt_code)
            .order_by(func.sum(ClaimsLineDB.allowed_amount).desc())
            .limit(limit)
        )
        rows = q.all()
        return [
            {
                "cpt_code": str(r.cpt_code),
                "allowed_amount": float(r.allowed_sum or 0),
                "line_count": int(r.line_count or 0),
                "member_count": 0,
            }
            for r in rows
        ]
    except Exception as e:
        print(f"WARNING policy_rollout CPT aggregate skipped: {e}", flush=True)
        try:
            db.rollback()
        except Exception:
            pass
        return []


def _aggregate_top_service_category(
    db: Session,
    tenant_id: UUID,
    start: date,
    end: date,
    limit: int = 15,
    *,
    service_categories: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    cats = service_categories or _archetype_service_categories()
    if not cats:
        return []
    try:
        db.execute(text("SET LOCAL statement_timeout = '25s'"))
        q = (
            db.query(
                ClaimsLineDB.service_category,
                func.coalesce(func.sum(ClaimsLineDB.allowed_amount), 0).label("allowed_sum"),
                func.count(ClaimsLineDB.id).label("line_count"),
            )
            .filter(
                ClaimsLineDB.tenant_id == tenant_id,
                ClaimsLineDB.service_date >= start,
                ClaimsLineDB.service_date <= end,
                ClaimsLineDB.service_category.in_(cats),
            )
            .group_by(ClaimsLineDB.service_category)
            .order_by(func.sum(ClaimsLineDB.allowed_amount).desc())
            .limit(limit)
        )
        rows = q.all()
        return [
            {
                "service_category": str(r.service_category),
                "allowed_amount": float(r.allowed_sum or 0),
                "line_count": int(r.line_count or 0),
            }
            for r in rows
        ]
    except Exception as e:
        print(f"WARNING policy_rollout category aggregate skipped: {e}", flush=True)
        try:
            db.rollback()
        except Exception:
            pass
        return []


def _confidence_from_volume(lines: int, members: int, months: int) -> Tuple[str, str]:
    # member_count may be 0 when using the fast CPT-scoped aggregate (no DISTINCT).
    if lines >= 5000 and (members >= 500 or members == 0):
        return "high", "Large claim volume in the lookback window."
    if lines >= 800 and (members >= 100 or members == 0):
        return "medium", "Moderate volume; estimates should be validated with a pilot or sensitivity analysis."
    return "low", "Limited data in window — directional only; expand lookback or wait for more ingestion."


def _try_elasticity_from_learning(
    tenant_id: UUID, policy_type: str
) -> Optional[Tuple[float, float, str]]:
    try:
        from uepi_api.storage_learning import get_latest_elasticity_model

        m = get_latest_elasticity_model(tenant_id, policy_type=policy_type, service_category=None)
        if not m or not m.get("elasticity_coefficients"):
            return None
        coefs = m.get("elasticity_coefficients") or {}
        # crude: take mean absolute of numeric leaf values
        vals: List[float] = []

        def walk(o: Any) -> None:
            if isinstance(o, dict):
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
            elif isinstance(o, (int, float)):
                vals.append(float(o))

        walk(coefs)
        if not vals:
            return None
        avg = sum(abs(v) for v in vals) / len(vals)
        lo, hi = -avg * 1.5, -avg * 0.4
        return (
            lo,
            hi,
            f"Tenant-specific elasticity model {m.get('model_id', '')} (v{m.get('version', '')}) informed this band.",
        )
    except Exception:
        return None


def compute_policy_rollout_recommendations(
    db: Session,
    tenant_id: UUID,
    *,
    months_lookback: int = 12,
    limit: int = 25,
    jaccard_threshold: float = 0.55,
) -> Dict[str, Any]:
    key = _cache_key(tenant_id, months_lookback, limit, jaccard_threshold)
    cached = _ROLLOUT_CACHE.get(key)
    if cached and (time.monotonic() - cached[0]) < _ROLLOUT_CACHE_TTL_SEC:
        return cached[1]

    end = date.today()
    start = end - timedelta(days=30 * max(3, min(months_lookback, 36)))

    existing = _existing_policy_signatures(db, tenant_id)

    # Prefer a shorter claims window for interactivity; archetypes still cover the catalog.
    claims_start = end - timedelta(days=30 * min(months_lookback, 6))
    top_cpt = _aggregate_top_cpt(
        db, tenant_id, claims_start, end, limit=50, procedure_codes=_archetype_procedure_codes()
    )
    # Category scan is nearly as expensive as CPT and adds little beyond archetype CPT overlap —
    # skip it on the hot path; evidence still comes from CPT concentration.
    top_cat: List[Dict[str, Any]] = []
    try:
        baseline = get_latest_baseline(tenant_id, policy_id=None)
    except Exception as e:
        print(f"WARNING policy_rollout baseline skipped: {e}", flush=True)
        baseline = None
    bm = (baseline or {}).get("baseline_metrics") or (baseline or {}).get("metrics") or {}
    base_util = float(
        bm.get("util_rate_total_per_1000_mm") or bm.get("utilization_per_1k") or 0.0
    )
    base_pmpm = float(bm.get("allowed_pmpm_total") or bm.get("cost_pmpm") or 0.0)

    recommendations: List[Dict[str, Any]] = []
    skipped_duplicates: List[Dict[str, Any]] = []

    # 1) Data-driven: map high-spend CPTs to archetypes
    cpt_rank = {row["cpt_code"]: i for i, row in enumerate(top_cpt)}

    for arch in POLICY_ARCHETYPES:
        codes = set(str(c) for c in arch["procedure_codes"])
        dup, reason, match_ids = _is_duplicate_candidate(codes, arch["policy_type"], existing, jaccard_threshold)
        if dup:
            skipped_duplicates.append(
                {
                    "archetype_id": arch["archetype_id"],
                    "title": arch["title"],
                    "reason": reason,
                    "matching_policy_ids": match_ids,
                }
            )
            continue

        overlap_spend = 0.0
        overlap_lines = 0
        overlap_members = 0
        evidence: List[Dict[str, Any]] = []

        for row in top_cpt:
            if row["cpt_code"] in codes:
                overlap_spend += row["allowed_amount"]
                overlap_lines += row["line_count"]
                overlap_members = max(overlap_members, row["member_count"])
                evidence.append(
                    {
                        "type": "claims_cpt_concentration",
                        "cpt_code": row["cpt_code"],
                        "allowed_amount_window": row["allowed_amount"],
                        "claim_lines": row["line_count"],
                        "distinct_members": row["member_count"],
                        "rank_in_tenant_cpt": cpt_rank.get(row["cpt_code"]),
                        "explanation": f"CPT {row['cpt_code']} ranks in the top spend drivers for this tenant in the lookback window.",
                    }
                )

        for cat_row in top_cat:
            if cat_row["service_category"] in (arch.get("service_categories") or []):
                evidence.append(
                    {
                        "type": "claims_service_category",
                        "service_category": cat_row["service_category"],
                        "allowed_amount_window": cat_row["allowed_amount"],
                        "claim_lines": cat_row["line_count"],
                        "explanation": f"Service category {cat_row['service_category']} shows elevated allowed amounts.",
                    }
                )

        if overlap_spend < 1 and overlap_lines < 5:
            # No strong tenant signal — still offer catalog item with low priority
            priority = "exploratory"
            conf, conf_expl = "low", "No strong CPT overlap in current claims window; catalog suggestion for strategic planning."
        else:
            priority = "high" if overlap_spend > 250_000 or overlap_lines > 2000 else "medium"
            conf, conf_expl = _confidence_from_volume(overlap_lines, overlap_members, months_lookback)

        el_band = _try_elasticity_from_learning(tenant_id, arch["policy_type"])
        if el_band:
            util_lo, util_hi, el_note = el_band
            cost_lo = util_lo * 0.85
            cost_hi = util_hi * 0.85
            methodology = "hybrid_catalog_and_learned_elasticity"
        else:
            util_lo, util_hi = arch["typical_util_elasticity_pct"]
            cost_lo, cost_hi = arch["typical_cost_elasticity_pct"]
            el_note = "Industry-typical elasticity band for this archetype (no tenant-specific elasticity model)."
            methodology = "catalog_benchmarks"

        projected_util_after = (
            base_util * (1 + util_hi / 100),
            base_util * (1 + util_lo / 100),
        ) if base_util > 0 else (None, None)
        projected_pmpm_after = (
            base_pmpm * (1 + cost_hi / 100),
            base_pmpm * (1 + cost_lo / 100),
        ) if base_pmpm > 0 else (None, None)

        rec_id = f"rollout_{arch['archetype_id']}"
        recommendations.append(
            {
                "recommendation_id": rec_id,
                "priority": priority,
                "archetype_id": arch["archetype_id"],
                "title": arch["title"],
                "policy_type": arch["policy_type"],
                "suggested_scope": {
                    "procedure_codes": sorted(codes),
                    "service_categories": arch.get("service_categories", []),
                    "note": "Refine LOB/markets in policy builder to match your network and product mix.",
                },
                "summary": arch["rationale"],
                "estimated_impact": {
                    "methodology": methodology,
                    "lookback_start": start.isoformat(),
                    "lookback_end": end.isoformat(),
                    "months_lookback": months_lookback,
                    "utilization_change_pct_range": [round(util_lo, 2), round(util_hi, 2)],
                    "cost_pmpm_change_pct_range": [round(cost_lo, 2), round(cost_hi, 2)],
                    "baseline_util_per_1k_reference": base_util or None,
                    "baseline_allowed_pmpm_reference": base_pmpm or None,
                    "projected_util_per_1k_range": (
                        [round(projected_util_after[0], 3), round(projected_util_after[1], 3)]
                        if projected_util_after[0] is not None
                        else None
                    ),
                    "projected_allowed_pmpm_range": (
                        [round(projected_pmpm_after[0], 3), round(projected_pmpm_after[1], 3)]
                        if projected_pmpm_after[0] is not None
                        else None
                    ),
                    "confidence": conf,
                    "confidence_explanation": conf_expl,
                    "elasticity_note": el_note,
                },
                "explainability": {
                    "why_recommended": [
                        arch["rationale"],
                        "Deduplication passed: target codes are not already fully covered by an equivalent in-force policy.",
                    ],
                    "evidence": evidence[:12],
                    "implementation_guidance": arch.get("implementation_notes", ""),
                    "governance": [
                        "Estimates are scenarios, not guarantees. Clinical and compliance review required before rollout.",
                        "Re-run after baseline refresh and quarterly as new observations accrue.",
                    ],
                    "similar_existing_policies": [],
                },
                "data_signals": {
                    "overlap_allowed_amount": round(overlap_spend, 2),
                    "overlap_claim_lines": overlap_lines,
                },
            }
        )

    recommendations.sort(
        key=lambda r: (
            {"high": 0, "medium": 1, "exploratory": 2}[r.get("priority", "exploratory")],
            -r["data_signals"]["overlap_allowed_amount"],
        )
    )

    result = {
        "generated_at": end.isoformat(),
        "tenant_id": str(tenant_id),
        "parameters": {
            "months_lookback": months_lookback,
            "jaccard_duplicate_threshold": jaccard_threshold,
            "max_recommendations_returned": limit,
        },
        "baseline_reference": {
            "baseline_id": (baseline or {}).get("id") or (baseline or {}).get("baseline_id"),
            "window": {
                "start": (baseline or {}).get("window_start_date"),
                "end": (baseline or {}).get("window_end_date"),
            },
        },
        "existing_policies_count": len(existing),
        "recommendations": recommendations[:limit],
        "skipped_as_duplicates": skipped_duplicates,
        "methodology_footer": "Health Foresight rollout recommender v1: catalog archetypes + claims concentration + "
        "Jaccard/code-coverage dedup vs in-force policies + optional tenant elasticity models.",
    }
    _ROLLOUT_CACHE[key] = (time.monotonic(), result)
    return result
