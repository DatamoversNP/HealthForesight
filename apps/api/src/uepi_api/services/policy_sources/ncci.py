"""NCCI PTP / MUE adapters — file-drop first; never fabricate confidential MUE values.

Full quarterly CMS ZIP releases are the authoritative source. Coverage API does not
serve NCCI edits. On hosts where cms.gov returns 403, acquisition stays ACCESS_BLOCKED
until an operator drops the quarterly export under data/policy_sources/ncci_*.
"""
from __future__ import annotations

from uepi_api.services.policy_sources.base import AdapterResult
from uepi_api.services.policy_sources.file_drop import load_family_from_drop


def _complete_quarterly(drop: AdapterResult) -> bool:
    """True only when a real quarterly inventory is present (not demo stubs)."""
    if not drop.discovered:
        return False
    # Demo stubs are intentionally tiny and labeled BOUNDED_DEMO_SUBSET / DEMO_SYNTHETIC.
    real = 0
    for d in drop.discovered:
        raw = d.raw_payload or {}
        if raw.get("completeness") == "BOUNDED_DEMO_SUBSET":
            continue
        if raw.get("catalog_class") == "DEMO_SYNTHETIC":
            continue
        if str(raw.get("verified")).lower() in {"1", "true"}:
            real += 1
            continue
        # Operator-dropped quarterly rows usually lack demo flags
        if "demo" not in str(d.source_document_id).lower() and "demo" not in str(
            d.source_version or ""
        ).lower():
            real += 1
    return real >= 10


def discover_ncci_ptp() -> AdapterResult:
    drop = load_family_from_drop("ncci_ptp", authority="CMS NCCI")
    if _complete_quarterly(drop):
        drop.acquisition_state = "RECONCILED"
        return drop
    # Stubs may exist — do not claim full quarterly reconcile
    return AdapterResult(
        family_id="ncci_ptp",
        adapter_status="ACCESS_BLOCKED" if drop.discovered else "NOT_ATTEMPTED",
        acquisition_state="ACCESS_BLOCKED",
        discovered=[],  # do not promote demo stubs as authoritative inventory
        inaccessible=[
            {
                "reason": (
                    "Full quarterly Medicare NCCI PTP ZIP not present; cms.gov downloads "
                    "return HTTP 403 on this host. Coverage API does not publish NCCI edits."
                ),
                "endpoint": "https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits",
                "action": "Download practitioner/outpatient hospital PTP quarterly ZIP on a host with CMS access; place parsed JSONL under data/policy_sources/ncci_ptp/documents_api.jsonl",
                "demo_stubs_present": bool(drop.discovered),
                "demo_stub_count": len(drop.discovered or []),
            }
        ],
        notes=(
            "PTP inventory incomplete until quarterly files are dropped and reconciled. "
            f"Ignored {len(drop.discovered or [])} demo-stub row(s)."
        ),
        scope={"catalog_class": "AUTHORITATIVE_PUBLIC", "completeness": "INCOMPLETE"},
    )


def discover_ncci_mue() -> AdapterResult:
    drop = load_family_from_drop("ncci_mue", authority="CMS NCCI")
    if _complete_quarterly(drop):
        drop.acquisition_state = "RECONCILED"
        return drop
    return AdapterResult(
        family_id="ncci_mue",
        adapter_status="ACCESS_BLOCKED" if drop.discovered else "NOT_ATTEMPTED",
        acquisition_state="ACCESS_BLOCKED",
        discovered=[],
        inaccessible=[
            {
                "reason": (
                    "Full quarterly Medicare NCCI MUE release not present; cms.gov 403 on this host. "
                    "Confidential MUE values must never be fabricated from public subsets."
                ),
                "endpoint": "https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits",
                "action": "Drop authorized/complete MUE practitioner (and facility) release JSONL under data/policy_sources/ncci_mue/",
                "demo_stubs_present": bool(drop.discovered),
                "demo_stub_count": len(drop.discovered or []),
            }
        ],
        notes=(
            "MUE adapter waits for authorized/complete release files. "
            f"Ignored {len(drop.discovered or [])} demo-stub row(s)."
        ),
        scope={"catalog_class": "AUTHORITATIVE_PUBLIC", "completeness": "INCOMPLETE"},
    )
