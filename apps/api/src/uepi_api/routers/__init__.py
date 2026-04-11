"""API routers — lazy package.

Previously this module did ``from . import analyses, policies, …`` at import time, so any
``from uepi_api.routers import auth`` (as used by ``main.py``) still loaded analyses,
policies, optional datasets (Polars), etc. That defeats lazy startup and OOMs small Azure SKUs.

Submodules load on first access via :func:`__getattr__` (PEP 562).
"""
from __future__ import annotations

import importlib
from typing import Any

# Match legacy try/except: these may fail import; expose as None
_OPTIONAL_SUBMODULES = frozenset(
    {
        "datasets",
        "cohorts",
        "ingestions",
        "pipeline_monitoring",
        "policies_file",
    }
)


def __getattr__(name: str) -> Any:
    if name.startswith("_"):
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        mod = importlib.import_module(f"{__name__}.{name}")
    except (ImportError, PermissionError, OSError):
        if name in _OPTIONAL_SUBMODULES:
            globals()[name] = None
            return None
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    globals()[name] = mod
    return mod


def __dir__() -> list[str]:
    return sorted(
        {k for k in globals() if not k.startswith("_")}
        | set(_OPTIONAL_SUBMODULES)
        | {
            "analyses",
            "auth",
            "decisions",
            "exports",
            "lineage",
            "notifications",
            "policies",
            "policy_import",
            "scorecards",
            "admin",
            "access",
            "data_health",
            "policy_rollout_recommendations",
        }
    )
