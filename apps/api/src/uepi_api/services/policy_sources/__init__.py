"""Authoritative policy source adapters.

Adapters discover and ingest *source documents*. They do not invent BCBS NC
proprietary text, CMS contents, or financial outcomes.

Supported ingest modes (in priority order):
1. Local export drop directory (`POLICY_SOURCE_DROP_DIR` or data/policy_sources/)
2. Authenticated remote APIs when credentials are present (e.g. CMS_COVERAGE_API_TOKEN)
3. Explicit INACCESSIBLE / NOT_IMPLEMENTED inventory rows when neither is available
"""
from uepi_api.services.policy_sources.base import (
    AdapterResult,
    SourceDocumentRecord,
    declared_scopes,
)
from uepi_api.services.policy_sources.reconcile import reconcile_all_families

__all__ = [
    "AdapterResult",
    "SourceDocumentRecord",
    "declared_scopes",
    "reconcile_all_families",
]
