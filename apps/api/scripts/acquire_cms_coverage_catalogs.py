#!/usr/bin/env python3
"""Acquire full CMS Coverage API catalogs into data/policy_sources (reference library).

Does NOT seed Representative Payer policy catalog rows.
Standalone — no SQLAlchemy / package init required.

Usage:
  python3 scripts/acquire_cms_coverage_catalogs.py
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
DROP_ROOT = REPO_ROOT / "data" / "policy_sources"
EVIDENCE = REPO_ROOT / "docs" / "demo" / "bcbs-nc" / "evidence"

UA = "HealthForesight-PolicySourceAdapter/1.1"
BASE = "https://api.coverage.cms.gov/v1"


def _get(url: str, *, token: Optional[str] = None, timeout: int = 120) -> Dict[str, Any]:
    headers = {"Accept": "application/json", "User-Agent": UA}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _paginate_report(path: str, *, params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    next_token = ""
    page = 0
    while True:
        page += 1
        q = dict(params or {})
        if next_token:
            q["next_token"] = next_token
        url = f"{BASE}{path}"
        if q:
            url += "?" + urllib.parse.urlencode(q)
        print(f"  fetch page {page}: {path} ({len(rows)} so far)")
        payload = _get(url)
        chunk = payload.get("data") or []
        if isinstance(chunk, list):
            rows.extend([r for r in chunk if isinstance(r, dict)])
        meta = payload.get("meta") or {}
        next_token = str(meta.get("next_token") or "").strip()
        if not next_token:
            break
        if len(rows) > 200_000:
            break
        time.sleep(0.05)
    return rows


def _parse_dt(s: Any) -> Optional[str]:
    if not s:
        return None
    raw = str(s).strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw[:19], fmt).isoformat()
        except Exception:
            continue
    return None


def _hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def export_jsonl(rows: List[Dict[str, Any]], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, default=str) + "\n")
    return len(rows)


def map_ncds(raw_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in raw_rows:
        sid = str(r.get("document_display_id") or "").strip()
        title = str(r.get("title") or "").strip()
        if not sid or not title:
            continue
        if not sid.upper().startswith("NCD"):
            sid = f"NCD{sid}"
        out.append(
            {
                "source_document_id": sid,
                "title": title,
                "source_version": str(r.get("document_version") or ""),
                "source_url": r.get("url"),
                "authority": "CMS",
                "program": "ORIGINAL_MEDICARE_FFS",
                "jurisdiction": "NATIONAL",
                "state": None,
                "effective_start": _parse_dt(r.get("last_updated")),
                "effective_end": None,
                "catalog_class": "AUTHORITATIVE_PUBLIC",
                "verified": True,
                "acquisition": "coverage_api_report_national-coverage-ncd",
                "content_hash": _hash(r),
                **r,
            }
        )
    return out


def map_lcds(raw_rows: List[Dict[str, Any]], state: str) -> List[Dict[str, Any]]:
    out = []
    for r in raw_rows:
        sid = str(r.get("document_display_id") or "").strip()
        title = str(r.get("title") or "").strip()
        if not sid or not title:
            continue
        contractor = str(r.get("contractor_name_type") or "")
        is_palmetto = "palmetto" in contractor.lower()
        out.append(
            {
                "source_document_id": sid,
                "title": title,
                "source_version": str(r.get("document_version") or ""),
                "source_url": r.get("url"),
                "authority": "Palmetto GBA" if is_palmetto else (contractor.split("\n")[0].strip() or "MAC"),
                "program": "ORIGINAL_MEDICARE_FFS",
                "jurisdiction": "A/B MAC Jurisdiction M" if is_palmetto else None,
                "state": state.upper(),
                "effective_start": _parse_dt(r.get("effective_date")),
                "effective_end": _parse_dt(r.get("retirement_date")),
                "catalog_class": "AUTHORITATIVE_PUBLIC",
                "verified": True,
                "nc_applicable": is_palmetto and state.upper() == "NC",
                "status_note": str(r.get("note") or ""),
                "acquisition": "coverage_api_report_local-coverage-final-lcds",
                "content_hash": _hash(r),
                **r,
            }
        )
    return out


def map_articles(raw_rows: List[Dict[str, Any]], state: str) -> List[Dict[str, Any]]:
    out = []
    for r in raw_rows:
        sid = str(r.get("document_display_id") or "").strip()
        title = str(r.get("title") or "").strip()
        if not sid or not title:
            continue
        contractor = str(r.get("contractor_name_type") or "")
        out.append(
            {
                "source_document_id": sid,
                "title": title,
                "source_version": str(r.get("document_version") or ""),
                "source_url": r.get("url"),
                "authority": contractor.split("\n")[0].strip() or "MAC",
                "program": "ORIGINAL_MEDICARE_FFS",
                "jurisdiction": None,
                "state": state.upper(),
                "effective_start": _parse_dt(r.get("effective_date")),
                "effective_end": _parse_dt(r.get("retirement_date")),
                "catalog_class": "AUTHORITATIVE_PUBLIC",
                "verified": True,
                "acquisition": "coverage_api_report_local-coverage-articles",
                "content_hash": _hash(r),
                **r,
            }
        )
    return out


def fetch_license_token() -> str:
    payload = _get(f"{BASE}/metadata/license-agreement/")
    data = payload.get("data") or []
    token = (data[0].get("Token") or data[0].get("token")) if data else None
    if not token:
        raise RuntimeError("license-agreement returned no Token")
    return str(token)


def fetch_article_codes(article_id: int, article_ver: int, token: str) -> List[Dict[str, Any]]:
    url = f"{BASE}/data/article/hcpc-code/?articleid={article_id}&articlever={article_ver}"
    payload = _get(url, token=token)
    data = payload.get("data") or []
    return data if isinstance(data, list) else []


def main() -> int:
    state = "NC"
    DROP_ROOT.mkdir(parents=True, exist_ok=True)
    summary: Dict[str, Any] = {
        "state": state,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source": BASE,
        "catalog_class": "AUTHORITATIVE_PUBLIC",
        "creates_payer_catalog_rows": False,
    }

    print("=== NCD national catalog ===")
    ncd_raw = _paginate_report("/reports/national-coverage-ncd/")
    ncds = map_ncds(ncd_raw)
    summary["ncd_count"] = export_jsonl(ncds, DROP_ROOT / "cms_ncd" / "documents_api.jsonl")
    print(f"  wrote {summary['ncd_count']} NCDs")

    print(f"=== LCD final catalog ({state}) ===")
    lcd_raw = _paginate_report(
        "/reports/local-coverage-final-lcds/",
        params={"stateabbrev": state},
    )
    lcds = map_lcds(lcd_raw, state)
    summary["lcd_count"] = export_jsonl(lcds, DROP_ROOT / "mac_lcd_nc" / "documents_api.jsonl")
    summary["lcd_palmetto_count"] = sum(1 for d in lcds if d.get("nc_applicable"))
    print(f"  wrote {summary['lcd_count']} LCDs ({summary['lcd_palmetto_count']} Palmetto/NC applicable)")

    print(f"=== Article catalog ({state}) ===")
    art_raw = _paginate_report(
        "/reports/local-coverage-articles/",
        params={"stateabbrev": state},
    )
    arts = map_articles(art_raw, state)
    summary["article_count"] = export_jsonl(
        arts, DROP_ROOT / "lcd_billing_coding_articles" / "documents_api.jsonl"
    )
    print(f"  wrote {summary['article_count']} articles")

    # Selective HCPCS enrichment (license token) for demo-relevant articles
    enrich_ids = ["A56729"]
    by_id = {d["source_document_id"]: d for d in arts}
    code_enrichment: Dict[str, Any] = {}
    try:
        token = fetch_license_token()
        codes_dir = DROP_ROOT / "lcd_billing_coding_articles" / "codes"
        codes_dir.mkdir(parents=True, exist_ok=True)
        for display_id in enrich_ids:
            doc = by_id.get(display_id)
            if not doc:
                code_enrichment[display_id] = {"status": "not_in_nc_article_catalog"}
                continue
            aid, aver = doc.get("document_id"), doc.get("document_version")
            if aid is None or aver is None:
                code_enrichment[display_id] = {"status": "missing_ids"}
                continue
            codes = fetch_article_codes(int(aid), int(aver), token)
            (codes_dir / f"{display_id}.json").write_text(
                json.dumps({"article": display_id, "codes": codes}, indent=2, default=str)
            )
            code_enrichment[display_id] = {
                "status": "ok",
                "code_count": len(codes),
                "sample_hcpc": [
                    c.get("hcpc_code_id") or c.get("hcpc") or c.get("code")
                    for c in codes[:25]
                    if isinstance(c, dict)
                ],
            }
            print(f"  enriched {display_id}: {len(codes)} HCPCS rows")
    except Exception as e:
        code_enrichment["error"] = str(e)[:400]
        print(f"  code enrichment failed: {e}")

    summary["code_enrichment"] = code_enrichment
    summary["notes"] = [
        "Full catalogs from Coverage API report endpoints (no permanent API key).",
        "HCPCS code lists require short-lived license-agreement token; fetched selectively.",
        "Does not create Representative Payer policy catalog rows.",
        "cms.gov bulk ZIP downloads remain 403 on this host; Coverage API is the acquisition path.",
        "NCCI PTP/MUE quarterly files are separate (cms.gov) — not in Coverage API.",
    ]

    (DROP_ROOT / "ACQUISITION_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str))
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    evidence_path = EVIDENCE / "SOURCE_CODESET_ACQUISITION.json"
    evidence_path.write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({k: summary[k] for k in summary if k != "code_enrichment"}, indent=2))
    print(f"Wrote {evidence_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
