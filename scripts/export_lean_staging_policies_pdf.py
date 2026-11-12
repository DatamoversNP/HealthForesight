#!/usr/bin/env python3
"""Export all lean-staging policies (scope/levers/assumptions/guardrails) to a review PDF."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api" / "src"))
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))

TENANT = UUID("00000000-0000-0000-0000-000000000001")


def esc(s: object) -> str:
    text = "" if s is None else str(s)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def short_json(obj: object, limit: int = 1200) -> str:
    try:
        raw = json.dumps(obj, indent=2, default=str, ensure_ascii=False)
    except Exception:
        raw = str(obj)
    if len(raw) > limit:
        return raw[: limit - 20] + "\n… (truncated)"
    return raw


def load_policies(tenant: UUID) -> list[dict]:
    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import Policy

    db = SessionLocal()
    try:
        rows = (
            db.query(Policy)
            .filter(Policy.tenant_id == tenant)
            .order_by(Policy.name.asc())
            .all()
        )
        out = []
        for p in rows:
            meta = p.policy_metadata_json if isinstance(p.policy_metadata_json, dict) else {}
            out.append(
                {
                    "id": str(p.id),
                    "name": p.name or "",
                    "policy_type": p.policy_type or "",
                    "owner_role": p.owner_role or "",
                    "status": p.status or "",
                    "description": p.description or "",
                    "metadata": meta,
                }
            )
        return out
    finally:
        db.close()


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverSub",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#333333"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Warn",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#7A2E0B"),
            backColor=colors.HexColor("#FFF4E5"),
            borderPadding=6,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="PolTitle",
            parent=styles["Heading1"],
            fontSize=13,
            leading=16,
            spaceBefore=4,
            spaceAfter=6,
            textColor=colors.HexColor("#0B3D5C"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SecHead",
            parent=styles["Heading2"],
            fontSize=10,
            leading=12,
            spaceBefore=8,
            spaceAfter=3,
            textColor=colors.HexColor("#1F4E79"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Mono",
            parent=styles["Code"],
            fontSize=7.5,
            leading=9.5,
            fontName="Courier",
            backColor=colors.HexColor("#F5F7FA"),
            borderPadding=4,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TOCEntry",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            leftIndent=0,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Footer",
            parent=styles["Normal"],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey,
        )
    )
    return styles


def meta_bits(m: dict) -> dict:
    scope = m.get("scope") if isinstance(m.get("scope"), dict) else {}
    return {
        "scope": scope,
        "codes": scope.get("procedure_codes") or [],
        "levers": m.get("policy_levers") or [],
        "assumptions": m.get("assumptions") or [],
        "guardrails": m.get("guardrails") or [],
        "enforcement": m.get("enforcement"),
        "exceptions": m.get("global_exceptions") or [],
        "effective_period": m.get("effective_period"),
        "domain": m.get("domain") or (m.get("ui_hints") or {}).get("domain"),
        "subdomain": m.get("subdomain") or (m.get("ui_hints") or {}).get("subdomain"),
        "quality": m.get("configuration_quality"),
    }


def add_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(0.75 * inch, 0.5 * inch, "HealthForesight lean staging — expert policy review")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(policies: list[dict], out_path: Path) -> None:
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.7 * inch,
        title="Lean Staging Policy Catalog — Expert Review",
        author="HealthForesight",
    )
    story: list = []
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Cover
    story.append(Spacer(1, 1.2 * inch))
    story.append(Paragraph("Lean Staging Policy Catalog", styles["CoverTitle"]))
    story.append(Paragraph("Expert Review Pack — Full Configuration Export", styles["CoverSub"]))
    story.append(Paragraph(f"{len(policies)} policies · generated {generated}", styles["CoverSub"]))
    story.append(Paragraph(
        "Environment: rg-healthforesight-enterprise-staging (hfleanstg)<br/>"
        "Brands: HealthForesight + Data Voyager (shared API/DB)",
        styles["CoverSub"],
    ))
    story.append(Spacer(1, 0.3 * inch))
    story.append(
        Paragraph(
            "<b>Reviewer notice:</b> These definitions are <b>illustrative / Blues-aligned demo configurations</b> "
            "for staging product demos. They are <b>not</b> verbatim Blue Cross NC medical policies, clinical "
            "guidelines, or formulary rows. Codes, levers, assumptions, and guardrails are structured to look "
            "operationally real for expert critique — they are not client-signed content. Please mark gaps, "
            "wrong code sets, unsafe assumptions, and missing exceptions.",
            styles["Warn"],
        )
    )

    # Summary counts
    type_counts: dict[str, int] = {}
    complete = 0
    for p in policies:
        type_counts[p["policy_type"]] = type_counts.get(p["policy_type"], 0) + 1
        b = meta_bits(p["metadata"])
        if b["codes"] and b["levers"] and b["assumptions"] and b["guardrails"]:
            complete += 1
    story.append(Paragraph("Catalog summary", styles["SecHead"]))
    summary_rows = [
        [Paragraph("<b>Metric</b>", styles["BodySmall"]), Paragraph("<b>Value</b>", styles["BodySmall"])],
        [Paragraph("Total policies", styles["BodySmall"]), Paragraph(str(len(policies)), styles["BodySmall"])],
        [
            Paragraph("Fully configured (codes+levers+assumptions+guardrails)", styles["BodySmall"]),
            Paragraph(str(complete), styles["BodySmall"]),
        ],
    ]
    for t, n in sorted(type_counts.items(), key=lambda x: (-x[1], x[0])):
        summary_rows.append(
            [Paragraph(esc(t), styles["BodySmall"]), Paragraph(str(n), styles["BodySmall"])]
        )
    t = Table(summary_rows, colWidths=[4.8 * inch, 1.5 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C5D0DE")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(t)
    story.append(PageBreak())

    # TOC (compact)
    story.append(Paragraph("Table of contents", styles["PolTitle"]))
    story.append(
        Paragraph(
            "Policies are listed alphabetically. Page numbers in the PDF footer; use PDF search for a policy name.",
            styles["BodySmall"],
        )
    )
    toc_lines = []
    for i, p in enumerate(policies, 1):
        toc_lines.append(f"{i}. {esc(p['name'])} <font color='#666'>({esc(p['policy_type'])})</font>")
    # chunk TOC into columns via simple paragraphs
    for line in toc_lines:
        story.append(Paragraph(line, styles["TOCEntry"]))
    story.append(PageBreak())

    # Policies
    for i, p in enumerate(policies, 1):
        m = p["metadata"]
        b = meta_bits(m)
        block = []
        block.append(
            Paragraph(
                f"{i}. {esc(p['name'])}",
                styles["PolTitle"],
            )
        )
        meta_line = (
            f"<b>Type:</b> {esc(p['policy_type'])} &nbsp;|&nbsp; "
            f"<b>Status:</b> {esc(p['status'])} &nbsp;|&nbsp; "
            f"<b>Owner:</b> {esc(p['owner_role'])} &nbsp;|&nbsp; "
            f"<b>ID:</b> {esc(p['id'])}"
        )
        if b["domain"] or b["subdomain"]:
            meta_line += (
                f"<br/><b>Domain:</b> {esc(b['domain'] or '—')} &nbsp;|&nbsp; "
                f"<b>Subdomain:</b> {esc(b['subdomain'] or '—')}"
            )
        block.append(Paragraph(meta_line, styles["BodySmall"]))
        if p["description"]:
            block.append(Paragraph("<b>Description</b>", styles["SecHead"]))
            block.append(Paragraph(esc(p["description"]), styles["BodySmall"]))

        block.append(Paragraph("Scope", styles["SecHead"]))
        scope = b["scope"] or {}
        scope_bits = [
            f"<b>LOB:</b> {esc(', '.join(scope.get('lob') or []) or '—')}",
            f"<b>Markets:</b> {esc(', '.join(scope.get('markets') or []) or '—')}",
            f"<b>States:</b> {esc(', '.join(scope.get('states') or []) or '—')}",
            f"<b>Network:</b> {esc(', '.join(scope.get('network') or []) or '—')}",
            f"<b>Service categories:</b> {esc(', '.join(scope.get('service_categories') or []) or '—')}",
            f"<b>Procedure / HCPCS codes:</b> {esc(', '.join(b['codes']) or '—')}",
        ]
        if b["effective_period"]:
            scope_bits.append(f"<b>Effective period:</b> {esc(short_json(b['effective_period'], 200))}")
        block.append(Paragraph("<br/>".join(scope_bits), styles["BodySmall"]))

        block.append(Paragraph("Policy levers", styles["SecHead"]))
        if not b["levers"]:
            block.append(Paragraph("<i>None</i>", styles["BodySmall"]))
        else:
            for li, lev in enumerate(b["levers"], 1):
                if not isinstance(lev, dict):
                    block.append(Paragraph(esc(lev), styles["BodySmall"]))
                    continue
                targets = lev.get("targets") or {}
                codes = targets.get("codes") or targets.get("procedure_codes") or []
                block.append(
                    Paragraph(
                        f"<b>Lever {li} — {esc(lev.get('lever_type'))}</b><br/>"
                        f"Targets codes: {esc(', '.join(codes) if isinstance(codes, list) else codes)}<br/>"
                        f"Parameters: <font face='Courier' size='7'>{esc(json.dumps(lev.get('parameters') or {}, default=str))}</font>",
                        styles["BodySmall"],
                    )
                )

        block.append(Paragraph("Assumptions", styles["SecHead"]))
        if not b["assumptions"]:
            block.append(Paragraph("<i>None</i>", styles["BodySmall"]))
        else:
            for a in b["assumptions"]:
                if not isinstance(a, dict):
                    block.append(Paragraph(esc(a), styles["BodySmall"]))
                    continue
                block.append(
                    Paragraph(
                        f"• <b>{esc(a.get('assumption_type') or 'ASSUMPTION')}</b> "
                        f"(value={esc(a.get('value'))}, confidence={esc(a.get('confidence'))})<br/>"
                        f"{esc(a.get('description'))}<br/>"
                        f"<font color='#555'>Source: {esc(a.get('source'))}</font>",
                        styles["BodySmall"],
                    )
                )

        block.append(Paragraph("Guardrails", styles["SecHead"]))
        if not b["guardrails"]:
            block.append(Paragraph("<i>None</i>", styles["BodySmall"]))
        else:
            for g in b["guardrails"]:
                if not isinstance(g, dict):
                    block.append(Paragraph(esc(g), styles["BodySmall"]))
                    continue
                block.append(
                    Paragraph(
                        f"• <b>{esc(g.get('metric_name'))}</b> "
                        f"{esc(g.get('threshold_type'))} {esc(g.get('threshold_value'))} "
                        f"→ action <b>{esc(g.get('action'))}</b><br/>"
                        f"{esc(g.get('description'))}",
                        styles["BodySmall"],
                    )
                )

        if b["enforcement"] or b["exceptions"]:
            block.append(Paragraph("Enforcement &amp; exceptions", styles["SecHead"]))
            if b["enforcement"]:
                block.append(
                    Paragraph(
                        f"<font face='Courier' size='7'>{esc(short_json(b['enforcement'], 500))}</font>",
                        styles["BodySmall"],
                    )
                )
            if b["exceptions"]:
                block.append(
                    Paragraph(
                        f"<font face='Courier' size='7'>{esc(short_json(b['exceptions'], 500))}</font>",
                        styles["BodySmall"],
                    )
                )

        block.append(Paragraph("Raw configuration excerpt (for auditors)", styles["SecHead"]))
        excerpt = {
            "scope": b["scope"],
            "policy_levers": b["levers"],
            "assumptions": b["assumptions"],
            "guardrails": b["guardrails"],
            "enforcement": b["enforcement"],
            "global_exceptions": b["exceptions"],
            "effective_period": b["effective_period"],
            "configuration_quality": b["quality"],
        }
        block.append(Paragraph(f"<font face='Courier' size='6.5'>{esc(short_json(excerpt, 2200))}</font>", styles["BodySmall"]))
        block.append(Spacer(1, 0.08 * inch))
        # Light separator line via table
        sep = Table([[""]], colWidths=[7 * inch], rowHeights=[1])
        sep.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#D0D7E2"))]))
        block.append(sep)
        block.append(Spacer(1, 0.12 * inch))

        story.extend(block)
        # page break every policy keeps review readable for expert pack
        if i < len(policies):
            story.append(PageBreak())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        default=str(
            REPO
            / "docs"
            / "production"
            / "releases"
            / f"LEAN_STAGING_POLICY_CATALOG_EXPERT_REVIEW_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
        ),
    )
    ap.add_argument("--also-json", action="store_true", help="Also write companion JSON next to PDF")
    args = ap.parse_args()

    url = os.environ.get("DATABASE_URL") or ""
    if "lean" not in url.lower() and "hfleanstg" not in url.lower() and os.environ.get("LEAN_STAGING_OK") != "1":
        raise SystemExit("Refusing: DATABASE_URL does not look like lean staging. Set LEAN_STAGING_OK=1 to override.")

    policies = load_policies(TENANT)
    if len(policies) < 1:
        raise SystemExit("No policies found")
    out = Path(args.out)
    print(f"Exporting {len(policies)} policies → {out}")
    build_pdf(policies, out)
    print(f"PDF_OK bytes={out.stat().st_size} path={out}")

    if args.also_json:
        jpath = out.with_suffix(".json")
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tenant_id": str(TENANT),
            "count": len(policies),
            "disclaimer": "Illustrative staging demo configs; not verbatim payer medical policy text.",
            "policies": policies,
        }
        jpath.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        print(f"JSON_OK bytes={jpath.stat().st_size} path={jpath}")


if __name__ == "__main__":
    main()
