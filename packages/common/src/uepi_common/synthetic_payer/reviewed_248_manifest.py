"""Parse reviewed-248 PDF pack into a measurement manifest.

Exported E/M dumps (99213/99214/…) are rejected as non-executable per PDF text.
Remaining exported codes are CANDIDATE only — not certified payer includes.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pypdf import PdfReader

BAD_EM: Set[str] = {"99213", "99214", "99215", "99203", "99204", "99205", "99212", "99211"}
CODE_LINE = re.compile(
    r"Original exported category:\s*([A-Z_]+);\s*lever:\s*([A-Z_]+);\s*codes:\s*([A-Z0-9|]+)",
    re.I,
)
TYPE_LINE = re.compile(
    r"Policy ID:\s*([0-9a-f-]+)\s*\|\s*Catalog #(\d+)\s*\|\s*Family:\s*([^|]+)\|\s*Type:\s*(\S+)",
    re.I,
)


def _allowed_band(code: str) -> tuple[float, float]:
    c = code.upper()
    if c.startswith("A04") or c.startswith("A043"):
        return (500.0, 3500.0)
    if c.startswith("J") or c.startswith("S"):
        return (80.0, 2500.0)
    if c.startswith("97"):
        return (70.0, 220.0)
    if c.startswith("7"):
        return (400.0, 2500.0)
    if c.startswith("2") or c.startswith("4") or c.startswith("3"):
        return (800.0, 6000.0)
    if c.startswith("G") or c.startswith("99"):
        return (50.0, 400.0)
    return (100.0, 900.0)


def _service_category(family: str, exported_category: str, codes: List[str]) -> str:
    fam = (family or "").upper()
    cat = (exported_category or "").upper()
    if fam in {"PHARMACY", "LIMIT"} and any(c[:1] in "JS" for c in codes):
        return "pharmacy"
    if cat == "THERAPY" or fam == "LIMIT":
        return "therapy"
    if cat == "SURGERY" or fam in {"NETWORK_SOC", "PAYMENT"}:
        return "surgery"
    if any(c.startswith("7") for c in codes):
        return "imaging"
    if any(c.startswith("A") for c in codes):
        return "ambulance"
    return (cat or fam or "general").lower()[:32]


def parse_pdf(path: Path) -> Dict[str, Any]:
    text = "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    exported_category = ""
    exported_lever = ""
    raw_codes: List[str] = []
    m = CODE_LINE.search(text.replace("\n", " "))
    if m:
        exported_category, exported_lever, raw = m.group(1), m.group(2), m.group(3)
        raw_codes = [c.strip() for c in raw.split("|") if c.strip()]
    policy_id = None
    catalog_num = None
    family = ""
    policy_type = ""
    tm = TYPE_LINE.search(text.replace("\n", " "))
    if tm:
        policy_id, catalog_num, family, policy_type = (
            tm.group(1),
            int(tm.group(2)),
            tm.group(3).strip(),
            tm.group(4).strip(),
        )
    # Drop known-bad E/M dump codes; keep any remaining as candidates.
    candidate = [c for c in raw_codes if c not in BAD_EM]
    only_bad = bool(raw_codes) and not candidate
    if only_bad:
        decision = "CONFIG_ONLY_BAD_EXPORT"
    elif candidate:
        decision = "CANDIDATE_MEASURE"
    else:
        decision = "CONFIG_ONLY_NO_CODES"
    return {
        "policy_id": policy_id,
        "catalog_num": catalog_num,
        "family": family,
        "policy_type": policy_type,
        "exported_category": exported_category,
        "exported_lever": exported_lever,
        "exported_codes_raw": raw_codes,
        "candidate_codes": candidate,
        "decision": decision,
        "service_category": _service_category(family, exported_category, candidate),
        "allowed_bands": {c: _allowed_band(c) for c in candidate},
        "pdf_path": str(path),
    }


def build_manifest(pack_dir: Path) -> Dict[str, Any]:
    index_path = pack_dir / "POLICY_INDEX.csv"
    policies_dir = pack_dir / "policies"
    rows = list(csv.DictReader(index_path.open()))
    catalog: List[Dict[str, Any]] = []
    for row in rows:
        pdf = policies_dir / row["filename"]
        parsed = parse_pdf(pdf) if pdf.exists() else {}
        # Prefer stable IDs from index
        item = {
            "register_index": int(row["index"]),
            "policy_id": row["policy_id"],
            "name": row["name"],
            "family": row.get("family") or parsed.get("family"),
            "mechanism": row.get("mechanism"),
            "filename": row["filename"],
            "source_status": row.get("source_status"),
            "certified": str(row.get("certified", "")).lower() == "true",
            **{k: v for k, v in parsed.items() if k not in {"policy_id", "family", "policy_type"}},
            "policy_type": parsed.get("policy_type")
            or _map_family_to_type(row.get("family") or "", row.get("mechanism") or ""),
        }
        catalog.append(item)
    summary = {
        "total": len(catalog),
        "candidate_measure": sum(1 for c in catalog if c["decision"] == "CANDIDATE_MEASURE"),
        "config_only_bad_export": sum(1 for c in catalog if c["decision"] == "CONFIG_ONLY_BAD_EXPORT"),
        "config_only_no_codes": sum(1 for c in catalog if c["decision"] == "CONFIG_ONLY_NO_CODES"),
    }
    return {"pack_dir": str(pack_dir), "summary": summary, "policies": catalog}


def _map_family_to_type(family: str, mechanism: str) -> str:
    fam = family.upper()
    mech = mechanism.upper()
    if "PRIOR_AUTH" in mech or "PRIOR AUTH" in mech:
        return "PRIOR_AUTH"
    if "STEP_THERAPY" in mech:
        return "STEP_THERAPY"
    if "QUANTITY" in mech:
        return "QUANTITY_LIMIT"
    if "SITE" in mech or fam == "NETWORK_SOC":
        return "SITE_OF_CARE"
    if "PAYMENT" in mech or fam == "PAYMENT":
        return "PAYMENT_POLICY"
    if "COST_SHARING" in mech:
        return "COST_SHARING"
    if "DURATION" in mech or fam == "LIMIT":
        return "DURATION_FREQUENCY_LIMIT"
    if "COVERAGE" in mech:
        return "COVERAGE"
    if fam == "PHARMACY":
        return "BENEFIT"
    if fam == "ADMIN_COMPLIANCE":
        return "ADMINISTRATIVE_REQUIREMENT"
    return "ADMINISTRATIVE_REQUIREMENT"


def batch_slice(manifest: Dict[str, Any], batch_num: int, batch_size: int = 10) -> List[Dict[str, Any]]:
    """1-indexed batch number."""
    policies = manifest["policies"]
    start = (batch_num - 1) * batch_size
    return policies[start : start + batch_size]
