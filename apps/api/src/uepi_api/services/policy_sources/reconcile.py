"""Reconcile declared source families into policy_source_* tables."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID, uuid4

from uepi_api.database import SessionLocal
from uepi_api.models.policy_source import (
    PolicySourceDocument,
    PolicySourceInventory,
)
from uepi_api.services.policy_sources.base import AdapterResult, declared_scopes
from uepi_api.services.policy_sources.bcbs_nc import discover_bcbs_family
from uepi_api.services.policy_sources.cms_mcd import (
    discover_cms_ncd,
    discover_lcd_articles,
    discover_mac_lcd_nc,
)
from uepi_api.services.policy_sources.file_drop import load_family_from_drop
from uepi_api.services.policy_sources.ncci import discover_ncci_mue, discover_ncci_ptp


def _run_adapter(family_id: str) -> AdapterResult:
    if family_id == "cms_ncd":
        return discover_cms_ncd()
    if family_id == "mac_lcd_nc":
        return discover_mac_lcd_nc()
    if family_id == "lcd_billing_coding_articles":
        return discover_lcd_articles()
    if family_id == "ncci_ptp":
        return discover_ncci_ptp()
    if family_id == "ncci_mue":
        return discover_ncci_mue()
    if family_id == "medicare_other_payment":
        drop = load_family_from_drop(family_id, authority="CMS")
        if drop.discovered:
            drop.acquisition_state = "RECONCILED"
            return drop
        return AdapterResult(
            family_id=family_id,
            adapter_status="NOT_ATTEMPTED",
            acquisition_state="NOT_ATTEMPTED",
            inaccessible=[{"reason": "No PFS/OPPS/MPPR/global surgery export drop"}],
            notes="Other Medicare payment rules require source file drop",
            scope={"catalog_class": "AUTHORITATIVE_PUBLIC"},
        )
    if family_id.startswith("bcnc_") or family_id == "payer_adaptations":
        return discover_bcbs_family(family_id)
    return AdapterResult(
        family_id=family_id,
        adapter_status="NOT_IMPLEMENTED",
        notes=f"No adapter registered for {family_id}",
    )


def reconcile_all_families(tenant_id: UUID) -> Dict[str, Any]:
    """Discover each declared family and upsert inventory + documents.

    Does not create Policy workspace rows automatically — population of
    configured policies is a separate preconfigure step after applicability.
    """
    batch_id = f"reconcile-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    db = SessionLocal()
    results: List[Dict[str, Any]] = []
    try:
        for scope in declared_scopes():
            family_id = scope["family_id"]
            adapter = _run_adapter(family_id)

            # Upsert inventory row
            inv = (
                db.query(PolicySourceInventory)
                .filter(
                    PolicySourceInventory.tenant_id == tenant_id,
                    PolicySourceInventory.family_id == family_id,
                )
                .one_or_none()
            )
            now = datetime.utcnow()
            if inv is None:
                inv = PolicySourceInventory(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    family_id=family_id,
                    scope_declaration_json=scope,
                    created_at=now,
                    updated_at=now,
                )
                db.add(inv)

            # Prefetch existing keys for this family once (avoids N+1 Azure round-trips
            # when ingesting full Coverage API catalogs of hundreds/thousands of docs).
            existing_rows = (
                db.query(PolicySourceDocument)
                .filter(
                    PolicySourceDocument.tenant_id == tenant_id,
                    PolicySourceDocument.family_id == family_id,
                )
                .all()
            )
            by_key = {
                (r.source_document_id, r.source_version or ""): r for r in existing_rows
            }

            ingested = 0
            for doc in adapter.discovered:
                key = (doc.source_document_id, doc.source_version or "")
                existing = by_key.get(key)
                if existing:
                    existing.title = doc.title
                    existing.source_url = doc.source_url
                    existing.program = doc.program
                    existing.jurisdiction = doc.jurisdiction
                    existing.state = doc.state
                    existing.effective_start = doc.effective_start
                    existing.effective_end = doc.effective_end
                    existing.document_relationships_json = doc.document_relationships
                    existing.raw_payload_json = doc.raw_payload
                    existing.content_hash = doc.content_hash
                    existing.updated_at = now
                    existing.ingest_batch_id = batch_id
                else:
                    row = PolicySourceDocument(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        family_id=doc.family_id,
                        authority=doc.authority,
                        source_document_id=doc.source_document_id,
                        source_version=doc.source_version,
                        title=doc.title,
                        source_url=doc.source_url,
                        program=doc.program,
                        jurisdiction=doc.jurisdiction,
                        state=doc.state,
                        effective_start=doc.effective_start,
                        effective_end=doc.effective_end,
                        document_relationships_json=doc.document_relationships,
                        raw_payload_json=doc.raw_payload,
                        ingest_batch_id=batch_id,
                        content_hash=doc.content_hash,
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(row)
                    by_key[key] = row
                ingested += 1
                if ingested % 500 == 0:
                    db.flush()

            acq = adapter.acquisition_state or adapter.adapter_status
            inv.scope_declaration_json = {
                **scope,
                **(adapter.scope or {}),
                "acquisition_state": acq,
                "catalog_class": (adapter.scope or {}).get("catalog_class")
                or scope.get("catalog_class"),
            }
            inv.discovered_count = len(adapter.discovered)
            inv.ingested_count = ingested
            inv.excluded_count = len(adapter.excluded)
            inv.inaccessible_count = len(adapter.inaccessible)
            inv.failed_count = len(adapter.failed)
            # Prefer fine-grained acquisition_state for inventory reporting
            inv.adapter_status = acq
            inv.last_reconciled_at = now
            inv.notes = adapter.notes
            inv.updated_at = now

            results.append(
                {
                    "family_id": family_id,
                    "label": scope.get("label"),
                    "catalog_class": scope.get("catalog_class"),
                    "adapter_status": acq,
                    "acquisition_state": acq,
                    "discovered": len(adapter.discovered),
                    "ingested": ingested,
                    "excluded": len(adapter.excluded),
                    "inaccessible": len(adapter.inaccessible),
                    "failed": len(adapter.failed),
                    "notes": adapter.notes,
                }
            )

        db.commit()
        return {
            "batch_id": batch_id,
            "tenant_id": str(tenant_id),
            "reconciled_at": datetime.utcnow().isoformat() + "Z",
            "families": results,
            "complete": False,  # Dec 4 authoritative+demo population not claimed here
            "demo_payer_catalog_ready": all(
                (r.get("catalog_class") != "DEMO_SYNTHETIC")
                or (
                    r.get("acquisition_state") == "DEMO_SYNTHETIC_CATALOG"
                    and r.get("discovered", 0) > 0
                )
                for r in results
            ),
            "authoritative_public_ready": all(
                (r.get("catalog_class") != "AUTHORITATIVE_PUBLIC")
                or (
                    r.get("acquisition_state") in ("RECONCILED", "ACQUIRED", "PARSED")
                    and r.get("discovered", 0) > 0
                )
                for r in results
            ),
            "honesty": {
                "representative_payer_is_blue_cross_nc_like_not_verbatim": True,
                "cms_ncci_remain_authoritative_public_when_acquired": True,
                "requires_bcbs_nc_authorization": False,
                "display_label_default": "Representative Payer Policies",
                "display_label_contextual": "Representative Payer Policies (Blue Cross NC-like)",
            },
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
