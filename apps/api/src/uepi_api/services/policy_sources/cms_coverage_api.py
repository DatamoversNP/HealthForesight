"""CMS Coverage API acquisition — full public catalogs + optional licensed code details.

Report endpoints require no API key.
LCD/article *detail* and HCPCS code endpoints require a short-lived license-agreement token
from GET /v1/metadata/license-agreement/ (AMA/ADA/AHA terms).

Does not create payer policy catalog rows — only authoritative reference library documents.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from uepi_api.services.policy_sources.base import AdapterResult, SourceDocumentRecord

UA = "HealthForesight-PolicySourceAdapter/1.1"
BASE = "https://api.coverage.cms.gov/v1"


def _get(url: str, *, token: Optional[str] = None, timeout: int = 90) -> Dict[str, Any]:
    headers = {"Accept": "application/json", "User-Agent": UA}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_license_token() -> str:
    payload = _get(f"{BASE}/metadata/license-agreement/")
    data = payload.get("data") or []
    if not data:
        raise RuntimeError("license-agreement returned no token")
    token = data[0].get("Token") or data[0].get("token")
    if not token:
        raise RuntimeError(f"license-agreement missing Token: {data[0]}")
    return str(token)


def _paginate_report(path: str, *, params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """Fetch report data; follow next_token if present."""
    rows: List[Dict[str, Any]] = []
    next_token = ""
    while True:
        q = dict(params or {})
        if next_token:
            q["next_token"] = next_token
        url = f"{BASE}{path}"
        if q:
            url += "?" + urllib.parse.urlencode(q)
        payload = _get(url)
        chunk = payload.get("data") or []
        if isinstance(chunk, list):
            rows.extend([r for r in chunk if isinstance(r, dict)])
        meta = payload.get("meta") or {}
        next_token = str(meta.get("next_token") or "").strip()
        if not next_token:
            break
        # safety
        if len(rows) > 200_000:
            break
        time.sleep(0.05)
    return rows


def _parse_dt(s: Any) -> Optional[datetime]:
    if not s:
        return None
    raw = str(s).strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw[:19], fmt)
        except Exception:
            continue
    return None


def _hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def discover_all_ncds() -> AdapterResult:
    rows = _paginate_report("/reports/national-coverage-ncd/")
    docs: List[SourceDocumentRecord] = []
    for r in rows:
        sid = str(r.get("document_display_id") or "").strip()
        title = str(r.get("title") or "").strip()
        if not sid or not title:
            continue
        docs.append(
            SourceDocumentRecord(
                family_id="cms_ncd",
                authority="CMS",
                source_document_id=f"NCD{sid}" if not sid.upper().startswith("NCD") else sid,
                title=title,
                source_version=str(r.get("document_version") or ""),
                source_url=r.get("url"),
                program="ORIGINAL_MEDICARE_FFS",
                jurisdiction="NATIONAL",
                effective_start=_parse_dt(r.get("last_updated")),
                raw_payload={
                    **r,
                    "catalog_class": "AUTHORITATIVE_PUBLIC",
                    "verified": True,
                    "acquisition": "coverage_api_report_national-coverage-ncd",
                },
                content_hash=_hash(r),
            )
        )
    return AdapterResult(
        family_id="cms_ncd",
        adapter_status="INGESTED_FROM_API",
        acquisition_state="RECONCILED",
        discovered=docs,
        notes=f"Coverage API NCD report: {len(docs)} documents",
        scope={"endpoint": f"{BASE}/reports/national-coverage-ncd/", "catalog_class": "AUTHORITATIVE_PUBLIC"},
    )


def discover_lcds_for_state(state_abbrev: str = "NC") -> AdapterResult:
    rows = _paginate_report(
        "/reports/local-coverage-final-lcds/",
        params={"stateabbrev": state_abbrev.upper()},
    )
    docs: List[SourceDocumentRecord] = []
    for r in rows:
        sid = str(r.get("document_display_id") or "").strip()
        title = str(r.get("title") or "").strip()
        if not sid or not title:
            continue
        contractor = str(r.get("contractor_name_type") or "")
        is_palmetto = "palmetto" in contractor.lower()
        note = str(r.get("note") or "")
        docs.append(
            SourceDocumentRecord(
                family_id="mac_lcd_nc" if state_abbrev.upper() == "NC" else f"mac_lcd_{state_abbrev.lower()}",
                authority="Palmetto GBA" if is_palmetto else (contractor.split("\n")[0].strip() or "MAC"),
                source_document_id=sid,
                title=title,
                source_version=str(r.get("document_version") or ""),
                source_url=r.get("url"),
                program="ORIGINAL_MEDICARE_FFS",
                jurisdiction="A/B MAC Jurisdiction M" if is_palmetto else None,
                state=state_abbrev.upper(),
                effective_start=_parse_dt(r.get("effective_date")),
                effective_end=_parse_dt(r.get("retirement_date")),
                raw_payload={
                    **r,
                    "catalog_class": "AUTHORITATIVE_PUBLIC",
                    "verified": True,
                    "nc_applicable": is_palmetto and state_abbrev.upper() == "NC",
                    "status_note": note,
                    "acquisition": "coverage_api_report_local-coverage-final-lcds",
                },
                content_hash=_hash(r),
            )
        )
    return AdapterResult(
        family_id="mac_lcd_nc",
        adapter_status="INGESTED_FROM_API",
        acquisition_state="RECONCILED",
        discovered=docs,
        notes=f"Coverage API final LCDs for {state_abbrev}: {len(docs)} documents",
        scope={
            "endpoint": f"{BASE}/reports/local-coverage-final-lcds/",
            "state": state_abbrev.upper(),
            "catalog_class": "AUTHORITATIVE_PUBLIC",
        },
    )


def discover_articles_for_state(state_abbrev: str = "NC") -> AdapterResult:
    rows = _paginate_report(
        "/reports/local-coverage-articles/",
        params={"stateabbrev": state_abbrev.upper()},
    )
    docs: List[SourceDocumentRecord] = []
    for r in rows:
        sid = str(r.get("document_display_id") or "").strip()
        title = str(r.get("title") or "").strip()
        if not sid or not title:
            continue
        contractor = str(r.get("contractor_name_type") or "")
        docs.append(
            SourceDocumentRecord(
                family_id="lcd_billing_coding_articles",
                authority=(contractor.split("\n")[0].strip() or "MAC"),
                source_document_id=sid,
                title=title,
                source_version=str(r.get("document_version") or ""),
                source_url=r.get("url"),
                program="ORIGINAL_MEDICARE_FFS",
                state=state_abbrev.upper(),
                effective_start=_parse_dt(r.get("effective_date")),
                effective_end=_parse_dt(r.get("retirement_date")),
                raw_payload={
                    **r,
                    "catalog_class": "AUTHORITATIVE_PUBLIC",
                    "verified": True,
                    "acquisition": "coverage_api_report_local-coverage-articles",
                },
                content_hash=_hash(r),
            )
        )
    return AdapterResult(
        family_id="lcd_billing_coding_articles",
        adapter_status="INGESTED_FROM_API",
        acquisition_state="RECONCILED",
        discovered=docs,
        notes=f"Coverage API articles for {state_abbrev}: {len(docs)} documents",
        scope={
            "endpoint": f"{BASE}/reports/local-coverage-articles/",
            "state": state_abbrev.upper(),
            "catalog_class": "AUTHORITATIVE_PUBLIC",
        },
    )


def fetch_article_hcpc_codes(article_id: int, article_version: int, token: str) -> List[Dict[str, Any]]:
    """Licensed endpoint — CPT/HCPCS associated with an article version."""
    url = (
        f"{BASE}/data/article/hcpc-code/"
        f"?articleid={int(article_id)}&articlever={int(article_version)}"
    )
    try:
        payload = _get(url, token=token)
        data = payload.get("data") or []
        return data if isinstance(data, list) else []
    except Exception as e:
        return [{"error": str(e), "article_id": article_id, "article_version": article_version}]


def export_jsonl(docs: Iterable[SourceDocumentRecord], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for d in docs:
            row = {
                "source_document_id": d.source_document_id,
                "title": d.title,
                "source_version": d.source_version,
                "source_url": d.source_url,
                "authority": d.authority,
                "program": d.program,
                "jurisdiction": d.jurisdiction,
                "state": d.state,
                "effective_start": d.effective_start.isoformat() if d.effective_start else None,
                "effective_end": d.effective_end.isoformat() if d.effective_end else None,
                "catalog_class": "AUTHORITATIVE_PUBLIC",
                "content_hash": d.content_hash,
                **(d.raw_payload or {}),
            }
            f.write(json.dumps(row, default=str) + "\n")
            n += 1
    return n


def acquire_full_public_catalogs(
    drop_root: Path,
    *,
    state: str = "NC",
    enrich_codes_for_display_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Download full catalogs into data/policy_sources JSONL drops.

    Optionally enrich a small set of articles with HCPCS code lists (license token).
    """
    summary: Dict[str, Any] = {"state": state, "generated_at": datetime.utcnow().isoformat() + "Z"}

    ncd = discover_all_ncds()
    lcd = discover_lcds_for_state(state)
    art = discover_articles_for_state(state)

    summary["ncd_count"] = export_jsonl(ncd.discovered, drop_root / "cms_ncd" / "documents_api.jsonl")
    summary["lcd_count"] = export_jsonl(lcd.discovered, drop_root / "mac_lcd_nc" / "documents_api.jsonl")
    summary["article_count"] = export_jsonl(
        art.discovered, drop_root / "lcd_billing_coding_articles" / "documents_api.jsonl"
    )

    # Preserve curated verified examples alongside full inventory (separate files)
    # file_drop loader already loads all *.jsonl in the family folder.

    enrich_ids = set(enrich_codes_for_display_ids or ["A56729"])
    code_enrichment: Dict[str, Any] = {}
    try:
        token = fetch_license_token()
        # map display id -> row
        by_id = {str(d.source_document_id): d for d in art.discovered}
        for display_id in enrich_ids:
            doc = by_id.get(display_id)
            if not doc:
                code_enrichment[display_id] = {"status": "not_in_nc_article_catalog"}
                continue
            raw = doc.raw_payload or {}
            aid = raw.get("document_id")
            aver = raw.get("document_version")
            if aid is None or aver is None:
                code_enrichment[display_id] = {"status": "missing_ids"}
                continue
            codes = fetch_article_hcpc_codes(int(aid), int(aver), token)
            code_enrichment[display_id] = {
                "status": "ok",
                "code_count": len(codes) if codes and "error" not in (codes[0] or {}) else 0,
                "sample": codes[:20],
                "article_id": aid,
                "article_version": aver,
            }
            # write side-car codes file
            out = drop_root / "lcd_billing_coding_articles" / f"codes_{display_id}.json"
            out.write_text(json.dumps({"article": display_id, "codes": codes}, indent=2, default=str))
    except Exception as e:
        code_enrichment["error"] = str(e)[:300]

    summary["code_enrichment"] = code_enrichment
    summary["notes"] = [
        "Full catalogs from Coverage API report endpoints (no permanent API key).",
        "HCPCS code lists require license-agreement token and are fetched selectively.",
        "Does not create Representative Payer policy catalog rows.",
        "Historical LCD/NCD versions beyond current report snapshot require MCD archive/API other-versions.",
    ]
    (drop_root / "ACQUISITION_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary
