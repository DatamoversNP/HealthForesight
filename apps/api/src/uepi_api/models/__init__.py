"""Database models (lazy package).

Previously this module imported every model at load time. Any ``from uepi_api.models.X import …``
first executed this ``__init__``, pulling in dozens of SQLAlchemy modules and spiking memory —
often OOM-killing the API on small Azure App Service plans before ``/api/v1/ping`` could run.

Submodules (e.g. ``uepi_api.models.tenant``) load independently. Names re-exported here resolve
on demand via :func:`__getattr__` (and work with ``from uepi_api.models import *`` in Alembic).
"""
from __future__ import annotations

import importlib
from typing import Any

# name -> (submodule under uepi_api.models, attribute name)
_NAME_TO_MODULE: dict[str, tuple[str, str]] = {
    "Tenant": ("tenant", "Tenant"),
    "User": ("tenant", "User"),
    "Role": ("tenant", "Role"),
    "AuditEvent": ("audit", "AuditEvent"),
    "Policy": ("policy", "Policy"),
    "PolicyVersion": ("policy", "PolicyVersion"),
    "PolicyCodeSet": ("policy", "PolicyCodeSet"),
    "PolicyAssumption": ("policy", "PolicyAssumption"),
    "PolicyGuardrail": ("policy", "PolicyGuardrail"),
    "PolicyChangelog": ("policy", "PolicyChangelog"),
    "PolicyPredictedImpact": ("predicted_impact", "PolicyPredictedImpact"),
    "Baseline": ("baseline", "Baseline"),
    "Observation": ("observation", "Observation"),
    "Scenario": ("scenario", "Scenario"),
    "ScenarioAccuracy": ("scenario", "ScenarioAccuracy"),
    "Pipeline": ("pipeline", "Pipeline"),
    "PipelineRun": ("pipeline", "PipelineRun"),
    "Risk": ("risk", "Risk"),
    "Forecast": ("forecast", "Forecast"),
    "DataPeriod": ("data_period", "DataPeriod"),
    "ElasticityModel": ("learning", "ElasticityModel"),
    "ModelAccuracyHistory": ("learning", "ModelAccuracyHistory"),
    "BehaviorProfile": ("behavior", "BehaviorProfile"),
    "BehaviorCluster": ("behavior", "BehaviorCluster"),
    "AlertRule": ("alert", "AlertRule"),
    "AlertEvent": ("alert", "AlertEvent"),
    "Comment": ("collaboration", "Comment"),
    "Task": ("collaboration", "Task"),
    "Approval": ("collaboration", "Approval"),
    "ActivityEvent": ("collaboration", "ActivityEvent"),
    "Evidence": ("evidence", "Evidence"),
    "Schedule": ("schedule", "Schedule"),
    "ExportTemplate": ("export_template", "ExportTemplate"),
    "ExportPack": ("export_template", "ExportPack"),
    "Ingestion": ("ingestion", "Ingestion"),
    "IngestionError": ("ingestion", "IngestionError"),
    "Dataset": ("ingestion", "Dataset"),
    "Analysis": ("analysis", "Analysis"),
    "AnalysisRun": ("analysis", "AnalysisRun"),
    "AnalysisResultIndex": ("analysis", "AnalysisResultIndex"),
    "AnalysisNarrative": ("analysis", "AnalysisNarrative"),
    "AnalysisConfig": ("analysis", "AnalysisConfig"),
    "BaselineAnalysisResult": ("analysis", "BaselineAnalysisResult"),
    "ImpactAnalysisResult": ("analysis", "ImpactAnalysisResult"),
    "WhatIfScenarioResult": ("analysis", "WhatIfScenarioResult"),
    "ElasticityAnalysisResult": ("analysis", "ElasticityAnalysisResult"),
    "DataQualityReport": ("data_quality", "DataQualityReport"),
    "DataQualityIssue": ("data_quality", "DataQualityIssue"),
    "Scorecard": ("scorecard", "Scorecard"),
    "ScorecardEntry": ("scorecard", "ScorecardEntry"),
    "ClaimsLineDB": ("canonical_data", "ClaimsLineDB"),
    "EnrollmentRecordDB": ("canonical_data", "EnrollmentRecordDB"),
    "ProviderRecordDB": ("canonical_data", "ProviderRecordDB"),
    "Export": ("export", "Export"),
    "Cohort": ("cohort", "Cohort"),
    "PolicyDecision": ("decision", "PolicyDecision"),
    "DecisionAttachment": ("decision", "DecisionAttachment"),
    "DatasetSnapshot": ("lineage", "DatasetSnapshot"),
    "Notification": ("notification", "Notification"),
    "NotificationPreference": ("notification", "NotificationPreference"),
    "Job": ("job", "Job"),
    "AnalyticsRun": ("analytics_run", "AnalyticsRun"),
}

__all__ = sorted(_NAME_TO_MODULE.keys())


def __getattr__(name: str) -> Any:
    if name not in _NAME_TO_MODULE:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    submodule, attr = _NAME_TO_MODULE[name]
    mod = importlib.import_module(f"{__name__}.{submodule}")
    val = getattr(mod, attr)
    globals()[name] = val
    return val


def __dir__() -> list[str]:
    return sorted(set(__all__) | {k for k in globals() if not k.startswith("_")})
