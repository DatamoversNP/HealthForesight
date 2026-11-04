"""Fine-grained source acquisition / readiness states.

INACCESSIBLE is deprecated as a catch-all. Prefer the states below so remediation
and completeness measurement stay actionable.
"""
from __future__ import annotations

# Ordered progression for reporting
ACQUISITION_STATES = (
    "NOT_ATTEMPTED",
    "ACCESS_BLOCKED",  # network / TLS / auth / permission failure on a retrieval attempt
    "SOURCE_UNAVAILABLE",  # content cannot currently be obtained (or not applicable to demo)
    "ACQUIRED",  # source files/API payloads retrieved
    "PARSED",  # records extracted
    "RECONCILED",  # inventory accounted for (discovered vs ingested/excluded)
    "CONFIGURED",  # rules + applicability validated on a policy version
    "ANALYTICALLY_READY",  # sufficient data for applicable analysis
)

# Demo-specific (representative payer catalog — not authoritative CMS)
DEMO_CATALOG_STATES = (
    "DEMO_SYNTHETIC_CATALOG",  # Representative Payer (Blue Cross NC-like) catalog present
    "DEMO_SYNTHETIC_ANALYTICS",  # synthetic claims drive labeled demo analytics
)


def normalize_legacy_status(status: str) -> str:
    s = (status or "").upper()
    if s == "INACCESSIBLE":
        return "ACCESS_BLOCKED"  # most prior uses were host/credential blocks
    if s in ("DROP_DIR_EMPTY",):
        return "NOT_ATTEMPTED"
    if s in ("INGESTED_FROM_DROP", "INGESTED_FROM_API"):
        return "RECONCILED"
    if s in ("API_FAILED",):
        return "ACCESS_BLOCKED"
    if s in ("API_EMPTY_OR_UNPARSED", "DROP_PARSE_FAILED"):
        return "SOURCE_UNAVAILABLE"
    if s in ("NOT_IMPLEMENTED", "NOT_IMPLEMENTED_REMOTE_FILTER"):
        return "NOT_ATTEMPTED"
    return s or "NOT_ATTEMPTED"
