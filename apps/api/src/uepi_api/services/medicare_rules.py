"""Medicare rules as first-class entities + applicability into policy lifecycle.

NCD/LCD = independent coverage determinations (also linkable to payer policies).
NCCI PTP/MUE = reusable coding/payment rules (not medical-necessity policies).
Articles = supporting documents linked to LCDs/NCDs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from uepi_api.services.enterprise_intelligence_fixtures import resolve_applicability

MRI_POLICY_ID = UUID("d403f101-08dd-45c9-ab83-d42e37c62018")

LINK_ROLES = (
    "REFERENCES_NCD",
    "REFERENCES_LCD",
    "HAS_RELATED_ARTICLE",
    "USES_CODING_EDIT",
    "USES_PAYMENT_RULE",
    "ADAPTS",
    "DEFINITION",
)

FAMILY_TO_KIND = {
    "cms_ncd": "NCD",
    "mac_lcd_nc": "LCD",
    "lcd_billing_coding_articles": "BILLING_CODING_ARTICLE",
    "ncci_ptp": "NCCI_PTP",
    "ncci_mue": "NCCI_MUE",
    "medicare_other_payment": "MEDICARE_PAYMENT_RULE",
}


def _serialize_doc(d) -> Dict[str, Any]:
    raw = d.raw_payload_json or {}
    return {
        "id": str(d.id),
        "family_id": d.family_id,
        "kind": FAMILY_TO_KIND.get(d.family_id, d.family_id),
        "authority": d.authority,
        "source_document_id": d.source_document_id,
        "source_version": d.source_version,
        "title": d.title,
        "source_url": d.source_url,
        "program": d.program,
        "jurisdiction": d.jurisdiction,
        "state": d.state,
        "effective_start": d.effective_start.isoformat() if d.effective_start else None,
        "effective_end": d.effective_end.isoformat() if d.effective_end else None,
        "relationships": d.document_relationships_json or [],
        "catalog_class": raw.get("catalog_class") or "AUTHORITATIVE_PUBLIC",
        "verified": bool(raw.get("verified", False)),
        "notes": raw.get("notes"),
        "entity_role": _entity_role(d.family_id),
    }


def _entity_role(family_id: str) -> str:
    if family_id in ("cms_ncd", "mac_lcd_nc"):
        return "COVERAGE_DETERMINATION"
    if family_id == "lcd_billing_coding_articles":
        return "SUPPORTING_ARTICLE"
    if family_id in ("ncci_ptp", "ncci_mue"):
        return "CODING_PAYMENT_RULE"
    if family_id == "medicare_other_payment":
        return "PAYMENT_RULE"
    return "OTHER"


def list_medicare_rules(
    tenant_id: UUID,
    *,
    kind: Optional[str] = None,
    q: Optional[str] = None,
) -> Dict[str, Any]:
    from uepi_api.database import SessionLocal
    from uepi_api.models.policy_source import PolicySourceDocument

    db = SessionLocal()
    try:
        rows = (
            db.query(PolicySourceDocument)
            .filter(
                PolicySourceDocument.tenant_id == tenant_id,
                PolicySourceDocument.family_id.in_(list(FAMILY_TO_KIND.keys())),
            )
            .order_by(PolicySourceDocument.family_id, PolicySourceDocument.source_document_id)
            .all()
        )
        items = [_serialize_doc(r) for r in rows]
        if kind:
            ku = kind.upper()
            items = [i for i in items if i["kind"] == ku or i["family_id"] == kind]
        if q:
            ql = q.lower()
            items = [
                i
                for i in items
                if ql in (i["title"] or "").lower()
                or ql in (i["source_document_id"] or "").lower()
                or ql in (i["authority"] or "").lower()
            ]
        return {
            "tenant_id": str(tenant_id),
            "count": len(items),
            "rules": items,
            "honesty": {
                "default_label": "Public Medicare sources (demo ingest)",
                "not_complete_inventory": True,
                "ncd_lcd_are_coverage_determinations": True,
                "ncci_are_coding_payment_rules_not_medical_policies": True,
                "articles_are_supporting_documents": True,
            },
        }
    finally:
        db.close()


def seed_mri_medicare_links(tenant_id: UUID) -> Dict[str, Any]:
    """Link Outpatient MRI PA to NCD/LCD/article/NCCI docs when present in inventory."""
    from uepi_api.database import SessionLocal
    from uepi_api.models.policy_source import PolicySourceDocument, PolicySourceLink

    # Verified NC chain: NCD220.2 (national) + L34425 (Palmetto JM) + A56729.
    # L35175 is Noridian J-F — NOT linked (wrong jurisdiction).
    desired = [
        ("cms_ncd", "NCD220.2", "REFERENCES_NCD"),
        ("mac_lcd_nc", "L34425", "REFERENCES_LCD"),
        ("lcd_billing_coding_articles", "A56729", "HAS_RELATED_ARTICLE"),
        ("ncci_ptp", "NCCI-PTP-PAIR-70553-70551", "USES_CODING_EDIT"),
    ]
    db = SessionLocal()
    created = []
    try:
        # Remove prior incorrect NC links (L35175 is Noridian J-F, not Palmetto JM)
        bad_ids = ("L35175", "A54118", "NCCI-PTP-2024Q4-EXAMPLE")
        bad_docs = (
            db.query(PolicySourceDocument)
            .filter(
                PolicySourceDocument.tenant_id == tenant_id,
                PolicySourceDocument.source_document_id.in_(bad_ids),
            )
            .all()
        )
        for bd in bad_docs:
            for link in (
                db.query(PolicySourceLink)
                .filter(
                    PolicySourceLink.policy_id == MRI_POLICY_ID,
                    PolicySourceLink.source_document_id == bd.id,
                )
                .all()
            ):
                created.append(
                    {
                        "role": link.link_role,
                        "source": bd.source_document_id,
                        "status": "removed_not_nc_applicable",
                    }
                )
                db.delete(link)

        # Enrich LCD↔article relationship on documents
        lcd = (
            db.query(PolicySourceDocument)
            .filter(
                PolicySourceDocument.tenant_id == tenant_id,
                PolicySourceDocument.family_id == "mac_lcd_nc",
                PolicySourceDocument.source_document_id == "L34425",
            )
            .first()
        )
        art = (
            db.query(PolicySourceDocument)
            .filter(
                PolicySourceDocument.tenant_id == tenant_id,
                PolicySourceDocument.family_id == "lcd_billing_coding_articles",
                PolicySourceDocument.source_document_id == "A56729",
            )
            .first()
        )
        if lcd and art:
            lcd.document_relationships_json = [
                {
                    "relationship": "HAS_RELATED_ARTICLE",
                    "target_source_document_id": art.source_document_id,
                    "target_family_id": art.family_id,
                    "provenance": "demo_seed_mri_medicare_links",
                    "effective_start": "2023-03-01",
                }
            ]
            art.document_relationships_json = [
                {
                    "relationship": "ARTICLE_OF",
                    "target_source_document_id": lcd.source_document_id,
                    "target_family_id": lcd.family_id,
                    "provenance": "demo_seed_mri_medicare_links",
                }
            ]
            db.add(lcd)
            db.add(art)

        for family, sid, role in desired:
            doc = (
                db.query(PolicySourceDocument)
                .filter(
                    PolicySourceDocument.tenant_id == tenant_id,
                    PolicySourceDocument.family_id == family,
                    PolicySourceDocument.source_document_id == sid,
                )
                .first()
            )
            if not doc:
                continue
            # Prefer single link per (role, source_document_id string) even if multiple versions exist
            already = False
            for existing_link, existing_doc in (
                db.query(PolicySourceLink, PolicySourceDocument)
                .join(
                    PolicySourceDocument,
                    PolicySourceDocument.id == PolicySourceLink.source_document_id,
                )
                .filter(
                    PolicySourceLink.policy_id == MRI_POLICY_ID,
                    PolicySourceLink.link_role == role,
                    PolicySourceDocument.source_document_id == sid,
                )
                .all()
            ):
                already = True
                break
            if already:
                created.append({"role": role, "source": sid, "status": "exists"})
                continue
            link = PolicySourceLink(
                tenant_id=tenant_id,
                policy_id=MRI_POLICY_ID,
                source_document_id=doc.id,
                link_role=role,
                created_at=datetime.utcnow(),
            )
            db.add(link)
            created.append({"role": role, "source": sid, "status": "created"})
        db.commit()
        return {
            "policy_id": str(MRI_POLICY_ID),
            "links": created,
            "catalog_class": "DEMO_SYNTHETIC_POLICY_WITH_PUBLIC_MEDICARE_LINKS",
            "analytical_outcomes": "SYNTHETIC",
        }
    finally:
        db.close()


def applicable_medicare_rules_for_policy(
    tenant_id: UUID,
    policy_id: UUID,
    *,
    program: str = "Original Medicare FFS",
    state: str = "North Carolina",
    as_of: str = "2024-06-01",
) -> Dict[str, Any]:
    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import Policy
    from uepi_api.models.policy_source import PolicySourceDocument, PolicySourceLink

    db = SessionLocal()
    try:
        policy = (
            db.query(Policy)
            .filter(Policy.id == policy_id, Policy.tenant_id == tenant_id)
            .first()
        )
        if not policy:
            return {"error": "policy_not_found", "policy_id": str(policy_id)}

        links = (
            db.query(PolicySourceLink, PolicySourceDocument)
            .join(
                PolicySourceDocument,
                PolicySourceDocument.id == PolicySourceLink.source_document_id,
            )
            .filter(
                PolicySourceLink.tenant_id == tenant_id,
                PolicySourceLink.policy_id == policy_id,
            )
            .all()
        )
        linked = []
        excluded = []
        seen_keys = set()
        for link, doc in links:
            dedupe_key = (link.link_role, doc.source_document_id)
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            item = _serialize_doc(doc)
            item["link_role"] = link.link_role
            # Reject wrong-jurisdiction LCDs for NC FFS demos
            raw = doc.raw_payload_json or {}
            if (
                doc.family_id == "mac_lcd_nc"
                and "north carolina" in (state or "").lower()
                and (
                    raw.get("nc_applicable") is False
                    or raw.get("applicability_flag") == "NOT_APPLICABLE_OTHER_JURISDICTION"
                    or (doc.jurisdiction or "").upper().find("JURISDICTION F") >= 0
                    or doc.source_document_id == "L35175"
                )
            ):
                item["why_excluded"] = (
                    f"{doc.source_document_id} is not applicable to North Carolina / Palmetto JM."
                )
                excluded.append(item)
                continue
            item["why_applicable"] = _why(link.link_role, doc, program, state)
            # Clinical applicability (beyond jurisdiction) for MRI PA
            if "MRI" in (policy.name or "").upper() and "PRIOR" in (policy.name or "").upper():
                from uepi_api.services.clinical_applicability import (
                    assess_mri_pa_medicare_clinical_match,
                )

                clinical = assess_mri_pa_medicare_clinical_match(
                    source_document_id=doc.source_document_id, as_of=as_of
                )
                item["clinical_applicability"] = clinical
                if clinical.get("clinical_match") == "PARTIAL_SERVICE_SCOPE":
                    item["clinical_caveat"] = clinical.get("rationale")
            linked.append(item)

        applicability = resolve_applicability(
            program=program, state=state, service_category=_service_hint(policy.name), as_of=as_of
        )

        clinical_bundle = None
        if "MRI" in (policy.name or "").upper() and "PRIOR" in (policy.name or "").upper():
            from uepi_api.services.clinical_applicability import mri_pa_clinical_bundle

            clinical_bundle = mri_pa_clinical_bundle(as_of=as_of)

        # Persistable rule-set identity for analytics lineage
        primary_ids = [
            x["source_document_id"]
            for x in linked
            if (x.get("clinical_applicability") or {}).get("present_as_mri_authority")
            or x.get("clinical_applicability") is None
        ]
        # For MRI PA, prefer NCD-only as primary authorities in rule_set when clinical bundle exists
        if clinical_bundle:
            primary_ids = [
                a["source_document_id"] for a in clinical_bundle.get("primary_medicare_authorities") or []
            ]
        rule_set_id = (
            f"medicare-ruleset:{policy_id}:"
            f"{program.replace(' ', '_')}:{state.replace(' ', '_')}:{as_of}:"
            f"{len(primary_ids)}"
        )

        return {
            "policy_id": str(policy_id),
            "policy_name": policy.name,
            "policy_type": policy.policy_type,
            "display_label": "Representative Payer Policies",
            "catalog_class": "DEMO_SYNTHETIC",
            "query": {"program": program, "state": state, "as_of": as_of},
            "linked_source_rules": linked,
            "excluded_source_rules": excluded,
            "clinical_applicability_bundle": clinical_bundle,
            "applicability_resolution": applicability,
            "rule_set": {
                "rule_set_id": rule_set_id,
                "version": "medicare-applicable-rules-v3",
                "source_document_ids": primary_ids
                or [x["source_document_id"] for x in linked],
                "linked_including_partial": [x["source_document_id"] for x in linked],
                "program_family": applicability.get("program_family"),
                "status": applicability.get("status"),
                "nc_mac": "Palmetto GBA Jurisdiction M",
                "note": (
                    "rule_set primary IDs are clinically applicable authorities; "
                    "partial-scope LCD/articles remain linked with clinical_match flags."
                ),
            },
            "analytics_guidance": {
                "informs_configuration": True,
                "informs_cohort_selection": linked != [],
                "blocks_if_unresolved_required_rule": applicability.get("status")
                in ("NO_MATCH_JURISDICTION", "SUPERSEDED_DOCUMENT"),
                "synthetic_outcomes_only": True,
                "note": (
                    "Public Medicare provenance (when linked) informs applicability; "
                    "financial/causal demo results remain synthetic known-answer or labeled fixtures."
                ),
            },
            "honesty": {
                "not_blue_cross_nc_proprietary": True,
                "ncd_lcd_independent_and_linkable": True,
                "ncci_not_medical_necessity": True,
            },
        }
    finally:
        db.close()


def _service_hint(name: Optional[str]) -> str:
    n = (name or "").upper()
    if "MRI" in n or "IMAGING" in n:
        return "Advanced imaging / MRI"
    return "General"


def _why(role: str, doc, program: str, state: str) -> str:
    kind = FAMILY_TO_KIND.get(doc.family_id, doc.family_id)
    if role == "REFERENCES_NCD":
        return f"Payer policy references NCD {doc.source_document_id} for coverage context under {program}."
    if role == "REFERENCES_LCD":
        return (
            f"LCD {doc.source_document_id} linked for {state} / {doc.jurisdiction or 'jurisdiction'} "
            f"Original Medicare localization — does not auto-apply to MA/commercial."
        )
    if role == "HAS_RELATED_ARTICLE":
        return f"Billing/coding article {doc.source_document_id} supports documentation/coding for the linked LCD/NCD."
    if role == "USES_CODING_EDIT":
        return f"NCCI {kind} {doc.source_document_id} is a coding/payment edit — not a medical-necessity determination."
    return f"Linked as {role} ({kind})."
