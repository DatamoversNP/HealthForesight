"""Load source documents from an operator-provided drop directory.

Expected layout (JSONL or JSON array per family):
  data/policy_sources/
    cms_ncd/documents.jsonl
    mac_lcd_nc/documents.jsonl
    lcd_billing_coding_articles/documents.jsonl
    ncci_ptp/documents.jsonl
    ncci_mue/documents.jsonl
    bcnc_medical/documents.jsonl
    ...

Each record minimally:
  source_document_id, title
Optional: source_version, source_url, program, jurisdiction, state,
  effective_start, effective_end, document_relationships, raw
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from uepi_api.services.policy_sources.base import AdapterResult, SourceDocumentRecord


def drop_root() -> Path:
    env = (os.environ.get("POLICY_SOURCE_DROP_DIR") or "").strip()
    if env:
        return Path(env)
    # repo-relative default
    # .../apps/api/src/uepi_api/services/policy_sources/file_drop.py → repo root = parents[6]
    return Path(__file__).resolve().parents[6] / "data" / "policy_sources"


def _parse_dt(v: Any) -> Optional[datetime]:
    if not v:
        return None
    if isinstance(v, datetime):
        return v
    s = str(v).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _load_file(path: Path) -> List[Dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        rows = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        return rows
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("documents"), list):
        return data["documents"]
    raise ValueError(f"Unsupported document file shape: {path}")


def load_family_from_drop(family_id: str, *, authority: str) -> AdapterResult:
    root = drop_root() / family_id
    if not root.exists():
        return AdapterResult(
            family_id=family_id,
            adapter_status="DROP_DIR_EMPTY",
            notes=f"No drop directory at {root}. Place export files to ingest.",
            scope={"drop_dir": str(root)},
        )

    # Only document inventories — ignore codes/ sidecars and acquisition summaries.
    document_files = sorted(
        {*(root.glob("documents*.jsonl")), *(root.glob("documents*.json"))}
    )
    if document_files:
        files = document_files
    else:
        files = sorted(
            f
            for f in root.glob("*.jsonl")
            if not f.name.startswith("codes_")
            and not f.name.startswith("ACQUISITION")
            and not f.name.startswith("examples_")
        )
    if not files:
        return AdapterResult(
            family_id=family_id,
            adapter_status="DROP_DIR_EMPTY",
            notes=f"Directory exists but contains no documents*.jsonl: {root}",
            scope={"drop_dir": str(root)},
        )

    discovered: List[SourceDocumentRecord] = []
    failed: List[Dict[str, Any]] = []
    by_id: Dict[str, SourceDocumentRecord] = {}
    for fpath in files:
        try:
            for row in _load_file(fpath):
                sid = str(row.get("source_document_id") or row.get("id") or "").strip()
                title = str(row.get("title") or row.get("name") or "").strip()
                if not sid or not title:
                    failed.append({"file": str(fpath), "reason": "missing source_document_id or title", "row": row})
                    continue
                raw = row.get("raw") if isinstance(row.get("raw"), dict) else row
                payload = json.dumps(raw, sort_keys=True, default=str)
                rec = SourceDocumentRecord(
                    family_id=family_id,
                    authority=str(row.get("authority") or authority),
                    source_document_id=sid,
                    title=title,
                    source_version=str(row.get("source_version") or row.get("version") or "") or None,
                    source_url=row.get("source_url") or row.get("url"),
                    program=row.get("program"),
                    jurisdiction=row.get("jurisdiction"),
                    state=row.get("state"),
                    effective_start=_parse_dt(row.get("effective_start") or row.get("effective_from")),
                    effective_end=_parse_dt(row.get("effective_end") or row.get("effective_to")),
                    document_relationships=row.get("document_relationships")
                    if isinstance(row.get("document_relationships"), dict)
                    else None,
                    raw_payload=raw if isinstance(raw, dict) else {"value": raw},
                    content_hash=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
                )
                # Dedupe: prefer verified / API-acquired rows over stubs
                prev = by_id.get(sid)
                if prev is None:
                    by_id[sid] = rec
                else:
                    prev_v = bool((prev.raw_payload or {}).get("verified"))
                    new_v = bool((raw or {}).get("verified")) if isinstance(raw, dict) else False
                    prev_api = "coverage_api" in str((prev.raw_payload or {}).get("acquisition") or "")
                    new_api = isinstance(raw, dict) and "coverage_api" in str(raw.get("acquisition") or "")
                    if (new_api and not prev_api) or (new_v and not prev_v):
                        by_id[sid] = rec
        except Exception as e:
            failed.append({"file": str(fpath), "reason": str(e)})

    discovered = list(by_id.values())
    status = "INGESTED_FROM_DROP" if discovered else "DROP_PARSE_FAILED"
    return AdapterResult(
        family_id=family_id,
        adapter_status=status,
        discovered=discovered,
        failed=failed,
        notes=f"Loaded {len(discovered)} unique documents from {len(files)} file(s) under {root}",
        scope={"drop_dir": str(root), "files": [str(f) for f in files]},
    )
