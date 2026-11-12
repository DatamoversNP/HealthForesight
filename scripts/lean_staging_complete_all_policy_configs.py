#!/usr/bin/env python3
"""
Fill every lean-staging policy with demo-credible configuration:
  - scope.procedure_codes (real CPT/HCPCS-looking sets)
  - policy_levers (typed, targeted to those codes)
  - assumptions (elasticity / cost / substitution / lag)
  - guardrails (utilization / denial / redirect thresholds)

Does NOT invent client-verbatim medical policy text.
Skips policies that already have all four populated (protects Dec4 fixtures).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api" / "src"))
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))

TENANT_DEFAULT = UUID("00000000-0000-0000-0000-000000000001")

# Keyword → CPT/HCPCS sets (illustrative but clinically recognizable)
CODE_BANK: list[tuple[tuple[str, ...], list[str], str]] = [
    (("mri", "magnetic resonance"), ["70551", "70553", "72148", "72149", "72158", "73721"], "ADVANCED_IMAGING"),
    (("ct / cta", "cta", "ct angio", "computed tomography"), ["70450", "70496", "71250", "71275", "74177"], "ADVANCED_IMAGING"),
    (("pet",), ["78811", "78812", "78813", "78814", "78815", "78816"], "ADVANCED_IMAGING"),
    (("nuclear cardiology", "myocardial perfusion"), ["78451", "78452", "78453", "78454"], "CARDIOLOGY"),
    (("cardiac ct", "ccta"), ["75574", "75571", "75572"], "CARDIOLOGY"),
    (("breast mri",), ["77046", "77047", "77048", "77049"], "ADVANCED_IMAGING"),
    (("stress test", "cardiac stress"), ["93015", "93016", "93017", "93018"], "CARDIOLOGY"),
    (("pacemaker", "icd", "crt", "implantable"), ["33206", "33207", "33208", "33249"], "CARDIOLOGY"),
    (("cardiac rehab",), ["93797", "93798"], "CARDIOLOGY"),
    (("sleep", "polysomn", "cpap", "home sleep"), ["95800", "95806", "95810", "95811", "E0601"], "PULMONARY"),
    (("pulmonary rehab", "pulm rehab"), ["G0424", "94625", "94626"], "PULMONARY"),
    (("bronchoscop",), ["31622", "31623", "31625"], "PULMONARY"),
    (("radiation", "imrt", "sbrt", "proton", "brachy"), ["77301", "77427", "77385", "77386", "77761"], "ONCOLOGY"),
    (("chemo", "oncology drug", "antineoplastic"), ["96413", "96415", "J9999", "J2505"], "ONCOLOGY"),
    (("genetic", "molecular", "ngs", "biomarker"), ["81445", "81455", "81479", "81301"], "LABORATORY"),
    (("lab", "laboratory", "pathology"), ["80053", "85025", "80061", "84443"], "LABORATORY"),
    (("infusion", "site-of-care", "site of care", "home infusion"), ["96413", "96415", "96365", "J1745", "J2357"], "INFUSION"),
    (("specialty pharmacy", "specialty drug", "specialty fill"), ["J1745", "J2357", "J9312", "J1300"], "PHARMACY"),
    (("ms ", "multiple sclerosis", "dmt"), ["J1826", "J2350", "J1595", "J2323"], "PHARMACY"),
    (("hepatitis", "hcv"), ["J3490", "S0145"], "PHARMACY"),
    (("rheumat", "biologic", "tnf"), ["J0135", "J1438", "J1745", "J9312"], "PHARMACY"),
    (("growth hormone", "somatropin"), ["J2941", "J2940", "J3590"], "PHARMACY"),
    (("glucose", "test strip", "diabetic supply"), ["A4253", "A4259", "E0607"], "PHARMACY"),
    (("insulin",), ["J1815", "J1817", "S5560"], "PHARMACY"),
    (("specialty tier", "coinsurance", "copay design", "benefit design"), ["99213", "99214", "J3490"], "PHARMACY"),
    (("step therapy", "step-edit"), ["J1745", "J2357", "J0135"], "PHARMACY"),
    (("quantity limit", "days' supply", "days supply", "ql "), ["J3490", "S5000"], "PHARMACY"),
    (("opioid", "pain contract"), ["J0592", "J2270", "J3010"], "PHARMACY"),
    (("unbundling", "incidental", "payment integrity", "claim edit"), ["27447", "29881", "43239", "45380"], "PAYMENT"),
    (("bluecard", "guest membership", "away-from-home", "inter-plan"), ["99213", "99214", "99215"], "ADMIN"),
    (("spine", "lumbar fusion", "cervical fusion", "discectomy"), ["22612", "22630", "22551", "63030"], "SURGERY"),
    (("joint", "arthroplast", "knee replace", "hip replace", "tka", "tha"), ["27447", "27130", "27446"], "SURGERY"),
    (("bariatric", "gastric"), ["43644", "43775", "43846"], "SURGERY"),
    (("cataract",), ["66984", "66982"], "SURGERY"),
    (("hernia",), ["49505", "49507", "49650"], "SURGERY"),
    (("site-of-service", "site of service", "asc ", "ambulatory surgery"), ["27447", "29827", "43239", "45378"], "SURGERY"),
    (("freestanding imaging", "imaging steerage"), ["70553", "72148", "71260", "74177"], "ADVANCED_IMAGING"),
    (("physical therapy", "pt visit", "outpatient therapy", "occupational therapy", "speech therapy"),
     ["97110", "97112", "97140", "97530", "92507"], "THERAPY"),
    (("chiropract",), ["98940", "98941", "98942"], "THERAPY"),
    (("acu puncture", "acupuncture"), ["97810", "97811"], "THERAPY"),
    (("dme", "wheelchair", "prosthetic", "orthotic", "cpap supply"),
     ["E0143", "E1390", "K0001", "L4360", "E0601"], "DME"),
    (("home health", "skilled nursing", "private duty"), ["G0151", "G0154", "99500"], "HOME"),
    (("hospice",), ["Q5001", "Q5002", "G0299"], "HOME"),
    (("snf", "skilled nursing facility", "inpatient rehab", "irf", "ltach"),
     ["99304", "99305", "99306", "99307"], "POST_ACUTE"),
    (("inpatient", "admission", "concurrent review", "observation", "drg"),
     ["99221", "99222", "99223", "99231", "99232", "99233"], "INPATIENT"),
    (("emergency", "ed ", "frequent utiliz"), ["99284", "99285", "G0380", "G0381"], "ED"),
    (("urgent care",), ["99202", "99203", "99213", "S9083"], "ED"),
    (("behavioral", "psych", "mental health", "sud", "substance"),
     ["90834", "90837", "90853", "H0031", "H2011"], "BEHAVIORAL"),
    (("maternity", "obstetric", "neonatal", "nicu"), ["59400", "59510", "99223", "99468"], "MATERNITY"),
    (("telehealth", "telemedicine", "virtual visit", "digital"), ["99441", "99442", "99443", "G2012"], "DIGITAL"),
    (("ambulance", "air ambulance"), ["A0425", "A0426", "A0427", "A0430"], "ANCILLARY"),
    (("dialysis", "esrd"), ["90935", "90937", "90999"], "ANCILLARY"),
    (("wound care",), ["97597", "97598", "11042"], "ANCILLARY"),
    (("hyperbaric",), ["99183", "G0277"], "ANCILLARY"),
    (("peer-to-peer", "p2p"), ["70553", "72148", "71260"], "ADVANCED_IMAGING"),
    (("ncci", "mue", "bundling", "mppr", "multiple procedure"),
     ["27447", "29881", "43239", "45380"], "PAYMENT"),
    (("referral",), ["99213", "99214", "99215"], "PRIMARY_CARE"),
]


DEFAULT_CODES = ["99213", "99214", "99215", "99203"]
DEFAULT_CATEGORY = "OTHER"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def _key_hit(blob: str, key: str) -> bool:
    """Word-boundary-ish match; multi-word keys match as phrases."""
    k = key.strip().lower()
    if not k:
        return False
    if " " in k or "/" in k or "-" in k:
        return k in blob
    return re.search(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])", blob) is not None


def infer_codes(name: str, domain: str = "", subdomain: str = "", description: str = "") -> tuple[list[str], str]:
    # Prefer name/domain/subdomain over long generic description text (avoids false hits).
    primary = _norm(" | ".join([name, domain, subdomain]))
    secondary = _norm(description[:160])
    generic_keys = {
        "step therapy", "step-edit", "quantity limit", "days' supply", "days supply",
        "ql ", "site of care", "site-of-care", "prior auth",
    }
    best: tuple[int, list[str], str] | None = None
    for keys, codes, cat in CODE_BANK:
        for k in keys:
            if _key_hit(primary, k):
                # Prefer clinical/product phrases over generic UM mechanism words.
                score = 100 + len(k) + (0 if k in generic_keys else 40)
                if best is None or score > best[0]:
                    best = (score, list(codes), cat)
            elif len(k) >= 8 and _key_hit(secondary, k):
                score = len(k) + (0 if k in generic_keys else 20)
                if best is None or score > best[0]:
                    best = (score, list(codes), cat)
    if best:
        return best[1], best[2]
    # domain fallbacks
    d = _norm(domain)
    sd = _norm(subdomain)
    if "pharmacy" in d or "channel" in sd:
        return ["J1745", "J2357", "J9312", "J0135"], "PHARMACY"
    if "imaging" in d or "radiology" in sd:
        return ["70553", "72148", "71260", "74177"], "ADVANCED_IMAGING"
    if "payment" in d or "integrity" in sd:
        return ["27447", "29881", "43239"], "PAYMENT"
    if "behavioral" in d:
        return ["90834", "90837", "H0031"], "BEHAVIORAL"
    if "network" in d or "access" in d:
        return ["99213", "99214", "99203", "99204"], "PRIMARY_CARE"
    if "site of care" in d or "site of care" in sd:
        return ["96413", "96365", "J1745"], "INFUSION"
    if "surgery" in sd or "orthopedic" in sd:
        return ["27447", "29827", "63030"], "SURGERY"
    if "cardiology" in sd:
        return ["93015", "78452", "33208"], "CARDIOLOGY"
    if "oncology" in sd:
        return ["96413", "77427", "78815"], "ONCOLOGY"
    if "therap" in sd:
        return ["97110", "97140", "97530"], "THERAPY"
    if "dme" in sd or "prosthetic" in sd:
        return ["E0143", "E1390", "L4360"], "DME"
    if "visit limit" in d or "therap" in d:
        return ["97110", "97112", "97530"], "THERAPY"
    if "benefit" in d or "cost sharing" in sd:
        return ["99213", "99214", "99203"], "PRIMARY_CARE"
    if "admin" in d or "regulatory" in d or "blues" in d:
        return ["99213", "99214", "99215"], "ADMIN"
    return list(DEFAULT_CODES), DEFAULT_CATEGORY

# Fixture policies with known-answer / Dec4 configs — never force-overwrite.
PROTECTED_NAMES = {
    "Outpatient MRI Prior Authorization",
    "Infusion Site-of-Care Optimization",
    "Freestanding Imaging Steerage",
    "Multiple Procedure Payment Reduction",
    "NCCI Medically Unlikely Units",
    "NCCI Procedure-to-Procedure Bundling",
    "LCD L34425 NC MRI Coverage Criteria",
    "NCD 220.2 MRI Coverage Change Study",
    "Outpatient Therapy Coverage and Payment",
}


def build_lever(policy_type: str, codes: list[str], name: str) -> list[dict[str, Any]]:
    pt = (policy_type or "PRIOR_AUTH").upper()
    targets = {"code_type": "CPT", "codes": codes[:6], "code_groups": []}
    if pt in ("PRIOR_AUTH", "PA", "CLINICAL_CRITERIA", "ADMINISTRATIVE_REQUIREMENT", "REFERRAL_REQUIREMENT"):
        return [{
            "lever_type": "PRIOR_AUTH",
            "targets": targets,
            "parameters": {
                "requires_pa": True,
                "pa_touchpoint": "PA_WORKFLOW",
                "clinical_review_required": True,
                "override_allowed": False,
                "expedited_review_hours": 72,
            },
        }]
    if pt in ("SITE_OF_CARE",):
        return [{
            "lever_type": "SITE_OF_CARE",
            "targets": targets,
            "parameters": {
                "preferred_sites": ["FREESTANDING", "ASC_OR_OFFICE", "OFFICE"],
                "discouraged_sites": ["HOSPITAL_OP", "HOPD"],
                "redirect_to": "FREESTANDING",
                "deny_if_disallowed": False,
                "hospital_allowed_when": "clinical_exception",
            },
        }]
    if pt in ("STEP_THERAPY",):
        return [{
            "lever_type": "STEP_THERAPY",
            "targets": targets,
            "parameters": {
                "requires_step_therapy": True,
                "steps": [
                    {"step": 1, "requirement": "preferred_agent_trial", "min_days": 30},
                    {"step": 2, "requirement": "documented_failure_or_intolerance"},
                ],
            },
        }]
    if pt in ("QUANTITY_LIMIT",):
        return [{
            "lever_type": "QUANTITY_LIMIT",
            "targets": targets,
            "parameters": {
                "max_quantity": 30,
                "quantity_unit": "DAYS_SUPPLY",
                "per_period": "FILL",
                "exception_path": "PA_WORKFLOW",
            },
        }]
    if pt in ("DURATION_FREQUENCY_LIMIT", "VISIT_LIMIT"):
        return [{
            "lever_type": "DURATION_FREQUENCY_LIMIT",
            "targets": targets,
            "parameters": {
                "max_visits": 20,
                "time_period": "CALENDAR_YEAR",
                "accumulate_across_providers": True,
                "reset_date": "CALENDAR_YEAR",
            },
        }]
    if pt in ("COST_SHARING", "BENEFIT"):
        return [{
            "lever_type": "COST_SHARING",
            "targets": targets,
            "parameters": {
                "copay": 75.0,
                "coinsurance": 0.2,
                "deductible_applies": True,
                "out_of_pocket_applies": True,
            },
        }]
    if pt in ("NETWORK_RESTRICTION", "PROVIDER_ELIGIBILITY", "ACCESS_AVAILABILITY_RULE"):
        return [{
            "lever_type": "NETWORK_RESTRICTION",
            "targets": targets,
            "parameters": {
                "allowed_network": ["IN"],
                "oon_allowed": False,
                "tier_preference": "PREFERRED",
            },
        }]
    if pt in ("PAYMENT_POLICY",):
        return [{
            "lever_type": "PAYMENT_EDIT",
            "targets": targets,
            "parameters": {
                "edit_type": "BUNDLING_OR_REDUCTION",
                "apply_at": "CLAIM_ADJUDICATION",
                "appeal_allowed": True,
            },
        }]
    if pt in ("COVERAGE",):
        return [{
            "lever_type": "COVERAGE_CRITERIA",
            "targets": targets,
            "parameters": {
                "covered": True,
                "coverage_level": "STANDARD",
                "medical_necessity_required": True,
            },
        }]
    if pt in ("COMPOSITE",):
        return [
            {
                "lever_type": "PRIOR_AUTH",
                "targets": targets,
                "parameters": {"requires_pa": True, "pa_touchpoint": "PA_WORKFLOW"},
            },
            {
                "lever_type": "SITE_OF_CARE",
                "targets": targets,
                "parameters": {
                    "preferred_sites": ["FREESTANDING", "OFFICE"],
                    "discouraged_sites": ["HOSPITAL_OP"],
                },
            },
        ]
    # default
    return [{
        "lever_type": "PRIOR_AUTH",
        "targets": targets,
        "parameters": {"requires_pa": True, "pa_touchpoint": "PA_WORKFLOW", "note": name[:80]},
    }]


def build_assumptions(name: str, category: str, policy_type: str) -> list[dict[str, Any]]:
    short = name if len(name) < 60 else name[:57] + "..."
    base = [
        {
            "assumption_type": "ELASTICITY",
            "description": f"PA/UM friction for {short} expected to reduce avoidable utilization 4–12% in first year",
            "value": "-0.08",
            "unit": "utilization_change_pct",
            "source": "Illustrative Blues-aligned UM benchmark (staging demo)",
            "confidence": 0.65,
        },
        {
            "assumption_type": "COST",
            "description": f"Allowed PMPM impact for {short} driven by code set {category}",
            "value": "-1.50_to_-4.00",
            "unit": "cost_change_pmpm",
            "source": "Synthetic staging cost model",
            "confidence": 0.6,
        },
        {
            "assumption_type": "LAG",
            "description": "Behavioral response and claim lag before observed impact stabilizes",
            "value": "90",
            "unit": "days",
            "source": "Typical UM observation window",
            "confidence": 0.7,
        },
    ]
    pt = (policy_type or "").upper()
    if pt in ("SITE_OF_CARE",) or category in ("INFUSION", "ADVANCED_IMAGING", "SURGERY"):
        base.append({
            "assumption_type": "SUBSTITUTION",
            "description": "Share of volume steerable from HOPD/hospital to freestanding/ASC/office when clinically appropriate",
            "value": "0.25_to_0.45",
            "unit": "steerable_share",
            "source": "Site-of-care program experience (illustrative)",
            "confidence": 0.55,
        })
    if pt in ("STEP_THERAPY", "QUANTITY_LIMIT") or category == "PHARMACY":
        base.append({
            "assumption_type": "ADHERENCE",
            "description": "Step/QL edits shift starts to preferred agents without material therapy abandonment",
            "value": "abandonment_lt_5pct",
            "source": "Pharmacy UM illustrative assumption",
            "confidence": 0.55,
        })
    return base[:4]


def build_guardrails(name: str, category: str, policy_type: str) -> list[dict[str, Any]]:
    short = name if len(name) < 50 else name[:47] + "..."
    guards = [
        {
            "metric_name": "utilization_change_pct",
            "threshold_type": "max",
            "threshold_value": 15.0,
            "action": "alert",
            "description": f"Alert if {short} utilization rises >15% vs baseline after go-live",
        },
        {
            "metric_name": "pa_denial_rate",
            "threshold_type": "max",
            "threshold_value": 0.25,
            "action": "alert",
            "description": f"Alert if denial rate for {short} exceeds 25% (access risk)",
        },
    ]
    pt = (policy_type or "").upper()
    if pt in ("SITE_OF_CARE",) or category in ("INFUSION", "ADVANCED_IMAGING", "SURGERY"):
        guards.append({
            "metric_name": "hospital_op_share",
            "threshold_type": "max",
            "threshold_value": 0.40,
            "action": "alert",
            "description": "Alert if hospital outpatient share remains above 40% of eligible episodes",
        })
    if category == "PHARMACY" or pt in ("STEP_THERAPY", "QUANTITY_LIMIT"):
        guards.append({
            "metric_name": "preferred_agent_start_rate",
            "threshold_type": "min",
            "threshold_value": 0.60,
            "action": "alert",
            "description": "Alert if preferred-agent start rate falls below 60%",
        })
    if category in ("BEHAVIORAL", "ED", "INPATIENT"):
        guards.append({
            "metric_name": "readmission_or_ed_bounce_pct",
            "threshold_type": "max",
            "threshold_value": 0.12,
            "action": "escalate",
            "description": "Escalate if downstream ED bounce / readmission signal exceeds 12%",
        })
    return guards[:3]


def is_complete(meta: dict) -> bool:
    scope = meta.get("scope") if isinstance(meta.get("scope"), dict) else {}
    codes = scope.get("procedure_codes") or []
    levers = meta.get("policy_levers") or []
    assum = meta.get("assumptions") or []
    guard = meta.get("guardrails") or []
    if not (isinstance(codes, list) and len(codes) > 0):
        return False
    if not (isinstance(levers, list) and len(levers) > 0):
        return False
    if not (isinstance(assum, list) and len(assum) > 0):
        return False
    if not (isinstance(guard, list) and len(guard) > 0):
        return False
    # Reject TBD-only assumption stubs as incomplete
    real_assum = [
        a for a in assum
        if isinstance(a, dict) and str(a.get("value") or "").upper() not in ("TBD", "TODO", "")
    ]
    return len(real_assum) > 0


def _assumptions_need_fill(assum: Any) -> bool:
    if not isinstance(assum, list) or not assum:
        return True
    real = [
        a for a in assum
        if isinstance(a, dict) and str(a.get("value") or "").upper() not in ("TBD", "TODO", "NULL", "")
    ]
    return len(real) == 0


def enrich_policy(meta: dict, name: str, policy_type: str, description: str, *, force: bool = False) -> dict:
    """Fill missing config fields. Preserves existing non-empty fixture content unless force=True."""
    m = deepcopy(meta) if isinstance(meta, dict) else {}
    ui = m.get("ui_hints") if isinstance(m.get("ui_hints"), dict) else {}
    domain = m.get("domain") or ui.get("domain") or ""
    subdomain = m.get("subdomain") or ui.get("subdomain") or ""
    inferred_codes, category = infer_codes(name, str(domain), str(subdomain), description or "")

    scope = m.get("scope") if isinstance(m.get("scope"), dict) else {}
    scope = dict(scope)
    if not scope.get("lob"):
        scope["lob"] = ["COMMERCIAL", "MA"]
    if not scope.get("markets"):
        scope["markets"] = ["NC"]
    if not scope.get("states"):
        scope["states"] = ["NC"]
    if not scope.get("network"):
        scope["network"] = ["IN"]

    existing_codes = scope.get("procedure_codes") if isinstance(scope.get("procedure_codes"), list) else []
    # Also accept codes already on levers
    if not existing_codes:
        for lev in (m.get("policy_levers") or []):
            if isinstance(lev, dict):
                t = lev.get("targets") or {}
                c = t.get("codes") or t.get("procedure_codes") or []
                if isinstance(c, list) and c:
                    existing_codes = list(c)
                    break
    codes = list(existing_codes) if (existing_codes and not force) else inferred_codes
    scope["procedure_codes"] = codes
    cats = scope.get("service_categories")
    if not (isinstance(cats, list) and cats):
        scope["service_categories"] = [category]
    m["scope"] = scope

    if force or not (isinstance(m.get("policy_levers"), list) and m.get("policy_levers")):
        m["policy_levers"] = build_lever(policy_type, codes, name)
    if force or _assumptions_need_fill(m.get("assumptions")):
        m["assumptions"] = build_assumptions(name, category, policy_type)
    if force or not (isinstance(m.get("guardrails"), list) and m.get("guardrails")):
        m["guardrails"] = build_guardrails(name, category, policy_type)

    if not m.get("effective_period"):
        m["effective_period"] = {"start_date": "2024-01-01T00:00:00", "end_date": None}
    if "apply_when" not in m:
        m["apply_when"] = []
    if "global_exceptions" not in m:
        m["global_exceptions"] = [
            {
                "exception_type": "CLINICAL",
                "description": "Urgent / emergent services and documented clinical exceptions remain exempt",
            }
        ]
    if not m.get("enforcement"):
        touch = (
            ["PA_WORKFLOW"]
            if (policy_type or "").upper() in ("PRIOR_AUTH", "PA", "CLINICAL_CRITERIA", "STEP_THERAPY", "SITE_OF_CARE")
            else ["CLAIM_ADJUDICATION"]
        )
        m["enforcement"] = {
            "mechanism": "HARD" if (policy_type or "").upper() in ("PRIOR_AUTH", "SITE_OF_CARE", "STEP_THERAPY") else "SOFT",
            "touchpoint": touch,
            "override_allowed": False,
        }
    m["configuration_quality"] = {
        "tier": "demo_complete_v1",
        "filled_at": datetime.now(timezone.utc).isoformat(),
        "code_category": category,
        "note": "Illustrative complete config for staging demos; not client-signed medical policy text",
    }
    return m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tenant-id", default=str(TENANT_DEFAULT))
    ap.add_argument("--force", action="store_true", help="Rewrite even if already complete")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    tenant = UUID(args.tenant_id)

    url = os.environ.get("DATABASE_URL") or ""
    if "lean" not in url.lower() and "hfleanstg" not in url.lower() and "staging" not in url.lower():
        # soft guard — still allow if LEAN_STAGING_OK=1
        if os.environ.get("LEAN_STAGING_OK") != "1":
            raise SystemExit("Refusing: DATABASE_URL does not look like lean staging. Set LEAN_STAGING_OK=1 to override.")

    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import Policy

    db = SessionLocal()
    updated = skipped = 0
    try:
        policies = db.query(Policy).filter(Policy.tenant_id == tenant).order_by(Policy.name).all()
        print(f"policies={len(policies)} force={args.force} dry_run={args.dry_run}")
        for pol in policies:
            meta = pol.policy_metadata_json if isinstance(pol.policy_metadata_json, dict) else {}
            protected = (pol.name or "").strip() in PROTECTED_NAMES
            # Force refreshes catalog configs; never clobber Dec4 / known-answer fixtures.
            do_force = bool(args.force) and not protected
            if protected and is_complete(meta):
                # Still repair TBD-only assumptions without replacing levers/codes.
                if _assumptions_need_fill(meta.get("assumptions")):
                    new_meta = enrich_policy(
                        meta, pol.name or "", pol.policy_type or "PRIOR_AUTH", pol.description or "", force=False
                    )
                else:
                    skipped += 1
                    continue
            elif not do_force and is_complete(meta):
                skipped += 1
                continue
            else:
                new_meta = enrich_policy(
                    meta,
                    pol.name or "",
                    pol.policy_type or "PRIOR_AUTH",
                    pol.description or "",
                    force=do_force,
                )
            if not is_complete(new_meta):
                raise SystemExit(f"enrich failed completeness for {pol.name}")
            if args.dry_run:
                print(
                    f"DRY {pol.name} codes={new_meta['scope']['procedure_codes'][:4]} "
                    f"levers={len(new_meta['policy_levers'])} "
                    f"assum={len(new_meta['assumptions'])} guard={len(new_meta['guardrails'])}"
                )
            else:
                pol.policy_metadata_json = new_meta
                pol.updated_at = datetime.utcnow()
            updated += 1
            if updated % 50 == 0:
                print(f"… updated {updated}", flush=True)
        if not args.dry_run:
            db.commit()
        # verify
        complete = 0
        for pol in db.query(Policy).filter(Policy.tenant_id == tenant).all():
            m = pol.policy_metadata_json if isinstance(pol.policy_metadata_json, dict) else {}
            if is_complete(m):
                complete += 1
        print(json.dumps({
            "updated": updated,
            "skipped_already_complete": skipped,
            "complete_after": complete,
            "total": len(policies),
            "pass": complete == len(policies),
        }))
        if complete != len(policies):
            raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
