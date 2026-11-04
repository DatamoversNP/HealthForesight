"""CMS Medicare Coverage Database (MCD) adapters for NCD / LCD / articles.

Primary path: Coverage API *report* endpoints (no permanent API key) via
cms_coverage_api, with results persisted under data/policy_sources/.

Fallback: operator file-drop exports. Optional CMS_COVERAGE_API_TOKEN still
used only for licensed data/* detail calls when explicitly configured.
"""
from __future__ import annotations

import os
from typing import Optional

from uepi_api.services.policy_sources.base import AdapterResult
from uepi_api.services.policy_sources.cms_coverage_api import (
    discover_all_ncds,
    discover_articles_for_state,
    discover_lcds_for_state,
)
from uepi_api.services.policy_sources.file_drop import load_family_from_drop


def _live_preferred() -> bool:
    return (os.environ.get("POLICY_SOURCE_LIVE_API") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _drop_looks_complete(drop: AdapterResult, *, min_docs: int) -> bool:
    if not drop.discovered:
        return False
    # Stub-only drops are small; full Coverage API catalogs are hundreds+.
    return len(drop.discovered) >= min_docs


def discover_cms_ncd() -> AdapterResult:
    drop = load_family_from_drop("cms_ncd", authority="CMS")
    if _drop_looks_complete(drop, min_docs=100) and not _live_preferred():
        drop.acquisition_state = "RECONCILED"
        return drop
    try:
        api = discover_all_ncds()
        if api.discovered:
            return api
    except Exception as e:
        if drop.discovered:
            drop.acquisition_state = "RECONCILED"
            drop.notes = (drop.notes or "") + f"; live API failed ({e}), using drop"
            return drop
        return AdapterResult(
            family_id="cms_ncd",
            adapter_status="API_FAILED",
            acquisition_state="ACCESS_BLOCKED",
            failed=[{"reason": str(e)}],
            notes="Coverage API NCD report failed and no usable drop",
            scope={"catalog_class": "AUTHORITATIVE_PUBLIC"},
        )
    if drop.discovered:
        drop.acquisition_state = "RECONCILED"
        return drop
    return AdapterResult(
        family_id="cms_ncd",
        adapter_status="NOT_ATTEMPTED",
        acquisition_state="NOT_ATTEMPTED",
        inaccessible=[
            {
                "reason": "No NCD drop and Coverage API returned empty",
                "endpoint": "https://api.coverage.cms.gov/v1/reports/national-coverage-ncd/",
            }
        ],
        notes="Authoritative public CMS NCD acquisition incomplete",
        scope={"program": "ORIGINAL_MEDICARE_FFS", "catalog_class": "AUTHORITATIVE_PUBLIC"},
    )


def discover_mac_lcd_nc(state: Optional[str] = None) -> AdapterResult:
    state_abbrev = (state or os.environ.get("POLICY_SOURCE_LCD_STATE") or "NC").upper()
    drop = load_family_from_drop("mac_lcd_nc", authority="Palmetto GBA (JM)")
    if _drop_looks_complete(drop, min_docs=100) and not _live_preferred():
        for d in drop.discovered:
            d.jurisdiction = d.jurisdiction or "A/B MAC Jurisdiction M"
            d.state = d.state or state_abbrev
            d.program = d.program or "ORIGINAL_MEDICARE_FFS"
        drop.acquisition_state = "RECONCILED"
        return drop
    try:
        api = discover_lcds_for_state(state_abbrev)
        if api.discovered:
            return api
    except Exception as e:
        if drop.discovered:
            drop.acquisition_state = "RECONCILED"
            drop.notes = (drop.notes or "") + f"; live API failed ({e}), using drop"
            return drop
        return AdapterResult(
            family_id="mac_lcd_nc",
            adapter_status="API_FAILED",
            acquisition_state="ACCESS_BLOCKED",
            failed=[{"reason": str(e)}],
            notes="Coverage API LCD report failed and no usable drop",
            scope={
                "jurisdiction": "A/B MAC Jurisdiction M",
                "state": state_abbrev,
                "catalog_class": "AUTHORITATIVE_PUBLIC",
            },
        )
    if drop.discovered:
        for d in drop.discovered:
            d.jurisdiction = d.jurisdiction or "A/B MAC Jurisdiction M"
            d.state = d.state or state_abbrev
            d.program = d.program or "ORIGINAL_MEDICARE_FFS"
        drop.acquisition_state = "RECONCILED"
        return drop
    return AdapterResult(
        family_id="mac_lcd_nc",
        adapter_status="NOT_ATTEMPTED",
        acquisition_state="NOT_ATTEMPTED",
        inaccessible=[{"reason": "No LCD drop and Coverage API returned empty", "state": state_abbrev}],
        notes="Authoritative NC/Palmetto JM LCD acquisition incomplete",
        scope={
            "jurisdiction": "A/B MAC Jurisdiction M",
            "state": state_abbrev,
            "catalog_class": "AUTHORITATIVE_PUBLIC",
        },
    )


def discover_lcd_articles(state: Optional[str] = None) -> AdapterResult:
    state_abbrev = (state or os.environ.get("POLICY_SOURCE_LCD_STATE") or "NC").upper()
    drop = load_family_from_drop("lcd_billing_coding_articles", authority="MAC")
    if _drop_looks_complete(drop, min_docs=100) and not _live_preferred():
        drop.acquisition_state = "RECONCILED"
        return drop
    try:
        api = discover_articles_for_state(state_abbrev)
        if api.discovered:
            return api
    except Exception as e:
        if drop.discovered:
            drop.acquisition_state = "RECONCILED"
            drop.notes = (drop.notes or "") + f"; live API failed ({e}), using drop"
            return drop
        return AdapterResult(
            family_id="lcd_billing_coding_articles",
            adapter_status="API_FAILED",
            acquisition_state="ACCESS_BLOCKED",
            failed=[{"reason": str(e)}],
            notes="Coverage API article report failed and no usable drop",
            scope={"state": state_abbrev, "catalog_class": "AUTHORITATIVE_PUBLIC"},
        )
    if drop.discovered:
        drop.acquisition_state = "RECONCILED"
        return drop
    return AdapterResult(
        family_id="lcd_billing_coding_articles",
        adapter_status="NOT_ATTEMPTED",
        acquisition_state="NOT_ATTEMPTED",
        inaccessible=[{"reason": "No article drop and Coverage API returned empty"}],
        notes="Place MCD article exports or run acquire_cms_coverage_catalogs.py",
        scope={"catalog_class": "AUTHORITATIVE_PUBLIC", "state": state_abbrev},
    )
