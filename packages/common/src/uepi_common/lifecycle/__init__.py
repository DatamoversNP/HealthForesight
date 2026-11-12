"""Policy lifecycle calculation contracts shared across mechanisms.

Orchestration is common: baseline → predictive impact → observations →
reconciliation → verdict/objectives → dashboards.

Calculators remain mechanism-specific. Continuation forecasts must never be
relabeled as policy-effect savings.
"""

from .continuation import (
    STATUS_AVAILABLE,
    STATUS_BLOCKED,
    STATUS_INCONCLUSIVE,
    STATUS_NOT_MEASURABLE,
    STATUS_NOT_SUPPORTED,
    STATUS_UNAVAILABLE,
    STATUS_UNESTIMATED,
    annualized_service_rate_per_1k,
    compute_continuation_forecast,
    compute_historical_rates,
    compute_observations,
    compute_policy_effect_prediction,
    compute_reconciliation,
    compute_verdict_prerequisites,
    compute_whatif_continuation,
    evaluate_claim_scope,
    pmpm,
)
from .mri_fixture import MRI_LIFECYCLE_FIXTURE, run_mri_lifecycle_fixture

__all__ = [
    "STATUS_AVAILABLE",
    "STATUS_BLOCKED",
    "STATUS_INCONCLUSIVE",
    "STATUS_NOT_MEASURABLE",
    "STATUS_NOT_SUPPORTED",
    "STATUS_UNAVAILABLE",
    "STATUS_UNESTIMATED",
    "MRI_LIFECYCLE_FIXTURE",
    "annualized_service_rate_per_1k",
    "compute_continuation_forecast",
    "compute_historical_rates",
    "compute_observations",
    "compute_policy_effect_prediction",
    "compute_reconciliation",
    "compute_verdict_prerequisites",
    "compute_whatif_continuation",
    "evaluate_claim_scope",
    "pmpm",
    "run_mri_lifecycle_fixture",
]
