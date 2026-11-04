"""Read-only surfacing of v1.2 policy definition packages (docs) into the platform.

These packages are definition/review artifacts — not operative activation.
They live under docs/demo/bcbs-nc/policy_definitions/v1.2/ and were previously
invisible in the UI because workspace reads DB + enterprise fixtures only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

# Representative nine — folder name under v1.2/ (always preferred / frozen)
POLICY_ID_TO_FOLDER: Dict[str, str] = {
    "d403f101-08dd-45c9-ab83-d42e37c62018": "mri",
    "d0eeb370-df14-4478-8755-dad6c3a35a47": "mppr",
    "d7441dd9-3bfe-405e-ae6c-0377204bbb7e": "sos",
    "58b839b5-b6e0-59e0-9406-d817877c3ce8": "ptp",
    "e11b049d-fcce-55cc-bcd7-71329038383b": "mue",
    "f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b": "therapy",
    "11218053-bdc0-569f-a415-fb61c5dcda37": "infusion",
    "4f8c34e3-015b-509d-90ba-521261464258": "ncd_study",
    "649b4ac8-ca82-5b84-aa87-84834490731a": "lcd_study",
}


def _v12_root() -> Path:
    # .../apps/api/src/uepi_api/services/this.py → repo root is parents[5]
    return Path(__file__).resolve().parents[5] / "docs" / "demo" / "bcbs-nc" / "policy_definitions" / "v1.2"


def _load_json(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _resolve_folder(policy_id: str) -> Optional[str]:
    """Nine freeze map first, then POLICY_PACKAGE_REGISTRY.json for catalog packages."""
    pid = str(policy_id)
    if pid in POLICY_ID_TO_FOLDER:
        return POLICY_ID_TO_FOLDER[pid]
    reg = _load_json(_v12_root() / "POLICY_PACKAGE_REGISTRY.json") or {}
    packages = reg.get("packages") or {}
    folder = packages.get(pid)
    return str(folder) if folder else None


def _md_excerpt(path: Optional[Path], max_chars: int = 1800) -> Optional[str]:
    if not path or not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    # drop HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return text[:max_chars].strip()


def _board_row(folder: str) -> Optional[Dict[str, Any]]:
    board = _load_json(_v12_root() / "NINE_POLICY_TECHNICAL_CLOSURE_BOARD.json") or {}
    for row in board.get("policies") or []:
        if row.get("folder") == folder:
            return row
    return None


def load_definition_package(policy_id: str) -> Dict[str, Any]:
    """Return definition-package payload for UI. Never claims operational activation."""
    folder_name = _resolve_folder(policy_id)
    root = _v12_root()
    if not folder_name:
        return {
            "available": False,
            "policy_id": policy_id,
            "reason": "No v1.2 definition package mapped for this catalog policy",
            "package_root": str(root),
            "operational_activation": None,
        }

    folder = root / folder_name
    if not folder.exists():
        return {
            "available": False,
            "policy_id": policy_id,
            "folder": folder_name,
            "reason": f"Package folder missing: {folder}",
            "operational_activation": "PROHIBITED",
        }

    blockers_path = next(iter(sorted(folder.glob("*RELEASE_BLOCKERS.json"))), None)
    codeset_path = next(
        (
            p
            for p in sorted(folder.glob("*CODESET*.json"))
            if "schema" not in p.name.lower()
        ),
        None,
    )
    definition_md = next(iter(sorted(folder.glob("*POLICY_DEFINITION*.md"))), None)
    freeze_md = next(iter(sorted(folder.glob("*FREEZE*.md"))), None)
    scope_md = next(iter(sorted(folder.glob("*SCOPE*.md"))), None)

    blockers = _load_json(blockers_path) if blockers_path else None
    codeset = _load_json(codeset_path) if codeset_path else None
    board = _board_row(folder_name)

    artifact_names = sorted(p.name for p in folder.iterdir() if p.is_file())

    # codeset summary for cards — only INCLUDE candidates, never EXCLUDE/defect rows
    codeset_summary: Dict[str, Any] = {}
    if isinstance(codeset, dict):
        raw_codes = (
            codeset.get("candidate_codes")
            or codeset.get("codes")
            or codeset.get("platform_codes")
            or (codeset.get("schedule") or {}).get("codes")
            or []
        )
        include_statuses = {
            "CANDIDATE_INCLUDE",
            "APPROVED_INCLUDE",
            "INCLUDE",
            "IN_SCOPE",
        }
        candidate_codes: list[Any] = []
        if isinstance(raw_codes, list):
            for row in raw_codes:
                if isinstance(row, str):
                    candidate_codes.append(row)
                    continue
                if not isinstance(row, dict):
                    continue
                status = str(row.get("inclusion_status") or row.get("status") or "").upper()
                if status and status not in include_statuses:
                    continue
                if not status and str(row.get("evidence_class") or "").upper() in {
                    "CONFIG_DEFECT",
                    "EXCLUDE",
                }:
                    continue
                code = row.get("code") or row.get("cpt")
                if code:
                    candidate_codes.append(code)
        codeset_summary = {
            "document_id": codeset.get("document_id") or codeset.get("id"),
            "version": codeset.get("version") or codeset.get("package_version"),
            "intended_scope": codeset.get("intended_anatomy")
            or codeset.get("intended_scope")
            or codeset.get("anatomical_scope")
            or codeset.get("scope"),
            "candidate_codes": candidate_codes,
            "notes": codeset.get("notes") or codeset.get("summary"),
            "exclude_codes_omitted": True,
        }

    activation = (
        (blockers or {}).get("blocks_operational_activation")
        if isinstance(blockers, dict)
        else None
    )
    if board and board.get("operational_activation"):
        activation_label = board.get("operational_activation")
    elif activation is True or activation is None:
        activation_label = "PROHIBITED"
    else:
        activation_label = "PROHIBITED" if activation else "UNKNOWN"

    return {
        "available": True,
        "policy_id": policy_id,
        "folder": folder_name,
        "package_version": (blockers or {}).get("package_version")
        if isinstance(blockers, dict)
        else "v1.2",
        "definition_status": "DEFINITION_REVIEW_REQUIRED",
        "operational_activation": activation_label,
        "clinical_product_approval": (board or {}).get("clinical_product_approval") or "WITHHELD",
        "structural_technical_closure": (board or {}).get("structural_technical_closure"),
        "release_blocker_count": (blockers or {}).get("blocker_count")
        if isinstance(blockers, dict)
        else (board or {}).get("release_blocker_count"),
        "release_blockers": (blockers or {}).get("blockers") if isinstance(blockers, dict) else [],
        "board_row": board,
        "codeset_summary": codeset_summary,
        "codeset": codeset,
        "definition_excerpt": _md_excerpt(definition_md),
        "freeze_excerpt": _md_excerpt(freeze_md, 900),
        "scope_migration_excerpt": _md_excerpt(scope_md, 900),
        "artifacts": artifact_names,
        "paths": {
            "folder": str(folder),
            "blockers": str(blockers_path) if blockers_path else None,
            "codeset": str(codeset_path) if codeset_path else None,
            "definition": str(definition_md) if definition_md else None,
        },
        "ui_rules": [
            "Definition package is review-only — not operative payer criteria",
            "Synthetic Dec 4 analytics may remain FULLY_VALIDATED_DEMO independently",
            "Do not treat this panel as clinical or legal authority",
            "Operational activation remains prohibited while release blockers stand",
        ],
    }
