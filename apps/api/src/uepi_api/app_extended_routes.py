"""Heavy FastAPI routers — registered on first request (not at import).

Azure App Service small SKUs often OOM or timeout while importing polars/pandas/scipy via
``datasets``, ``analyses_file``, etc. Deferring this keeps ``/api/v1/ping`` and auth working.
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


def path_skips_extended_loading(path: str) -> bool:
    if path in ("/health", "/metrics", "/api/v1/ping"):
        return True
    if path.startswith("/api/v1/health"):
        return True
    if path.startswith("/api/v1/auth"):
        return True
    if path.startswith("/api/v1/access"):
        return True
    if path in ("/docs", "/openapi.json", "/redoc"):
        return True
    return False


def register_extended_routes(app: FastAPI) -> None:
    if getattr(app.state, "extended_routes_loaded", False):
        return
    if not hasattr(app.state, "_extended_routes_lock"):
        app.state._extended_routes_lock = threading.Lock()
    with app.state._extended_routes_lock:
        if getattr(app.state, "extended_routes_loaded", False):
            return
        print("uepi_api: loading extended routers (polars/pandas-heavy modules)...", flush=True)

        # Eager-load ORM classes once string-based relationships (e.g. DataPeriod → DatasetSnapshot)
        # resolve; lazy ``uepi_api.models`` avoids this at process start but extended routes need it.
        import uepi_api.models as _models_pkg

        for _name in _models_pkg.__all__:
            getattr(_models_pkg, _name)

        from uepi_api.routers import (
            analyses,
            exports,
            lineage,
            notifications,
            policy_import,
            scorecards,
        )
        from uepi_api.routers import policy_workspace
        from uepi_api.routers import decisions_workspace
        from uepi_api.routers import uncertainty_visualization
        from uepi_api.routers import behavior_detection
        from uepi_api.routers import collaboration
        from uepi_api.routers import narratives

        from uepi_api.routers import policies
        from uepi_api.routers import ingestions, datasets

        app.include_router(policies.router, prefix="/api/v1", tags=["Policies"])
        if ingestions is not None:
            app.include_router(ingestions.router, prefix="/api/v1", tags=["Ingestions"])
        if datasets is not None:
            app.include_router(datasets.router, prefix="/api/v1", tags=["Datasets"])

        app.include_router(policy_import.router, prefix="/api/v1", tags=["Policy Import"])
        try:
            from uepi_api.routers import analyses_file

            app.include_router(analyses_file.router, prefix="/api/v1", tags=["Analyses (Sync)"])
        except ImportError:
            pass
        app.include_router(analyses.router, prefix="/api/v1", tags=["Analyses"])
        app.include_router(scorecards.router, prefix="/api/v1", tags=["Scorecards"])
        app.include_router(exports.router, prefix="/api/v1", tags=["Exports"])
        from uepi_api.routers import cohorts_file

        app.include_router(cohorts_file.router, prefix="/api/v1", tags=["Cohorts"])
        app.include_router(lineage.router, prefix="/api/v1", tags=["Lineage"])

        try:
            from uepi_api.routers import data_periods

            app.include_router(data_periods.router, prefix="/api/v1", tags=["Data Periods"])
        except ImportError:
            pass

        try:
            from uepi_api.routers import policy_versions

            app.include_router(policy_versions.router, prefix="/api/v1", tags=["Policy Versions"])
        except ImportError as e:
            print(f"Warning: Could not import policy_versions router: {e}")

        from uepi_api.routers import pipelines

        app.include_router(pipelines.router, prefix="/api/v1", tags=["Pipelines"])

        from uepi_api.routers import pipeline_monitoring

        if pipeline_monitoring is not None:
            app.include_router(pipeline_monitoring.router, prefix="/api/v1", tags=["Pipeline Monitoring"])

        from uepi_api.routers import data_explorer

        app.include_router(data_explorer.router, prefix="/api/v1", tags=["Data Explorer"])

        from uepi_api.routers import policy_stage2

        app.include_router(policy_stage2.router, prefix="/api/v1", tags=["Policy Stage 2"])

        from uepi_api.routers import baselines

        app.include_router(baselines.router, prefix="/api/v1", tags=["Baselines"])

        from uepi_api.routers import observations

        app.include_router(observations.router, prefix="/api/v1", tags=["Observations"])

        from uepi_api.routers import analytics_runs

        app.include_router(analytics_runs.router, prefix="/api/v1", tags=["Analytics Runs"])

        from uepi_api.routers import learning

        app.include_router(learning.router, prefix="/api/v1", tags=["Learning"])

        from uepi_api.routers import traceability

        app.include_router(traceability.router, prefix="/api/v1", tags=["Traceability"])

        from uepi_api.routers import data_quality

        app.include_router(data_quality.router, prefix="/api/v1", tags=["Data Quality"])

        from uepi_api.routers import daily_jobs

        app.include_router(daily_jobs.router, prefix="/api/v1", tags=["Daily Jobs"])

        from uepi_api.routers import scenario_accuracy

        app.include_router(scenario_accuracy.router, prefix="/api/v1", tags=["Scenario Accuracy"])

        from uepi_api.routers import dashboard

        app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])

        from uepi_api.routers import schedules

        app.include_router(schedules.router, prefix="/api/v1", tags=["Schedules"])
        app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])

        from uepi_api.routers import dashboards_persona

        app.include_router(dashboards_persona.router, prefix="/api/v1", tags=["Persona Dashboards"])
        app.include_router(policy_workspace.router, prefix="/api/v1", tags=["Policy Workspace"])
        app.include_router(decisions_workspace.router, prefix="/api/v1", tags=["Decision Workspace"])
        app.include_router(uncertainty_visualization.router, prefix="/api/v1", tags=["Uncertainty Visualization"])
        app.include_router(behavior_detection.router, prefix="/api/v1", tags=["Behavior Detection"])
        app.include_router(collaboration.router, prefix="/api/v1", tags=["Collaboration"])
        app.include_router(narratives.router, prefix="/api/v1", tags=["Narratives"])

        from uepi_api.routers import conversational_ai

        app.include_router(conversational_ai.router, prefix="/api/v1", tags=["Conversational AI"])

        from uepi_api.routers import database_viewer

        app.include_router(database_viewer.router, prefix="/api/v1", tags=["Database Viewer"])

        from uepi_api.routers import data_generation

        app.include_router(data_generation.router, prefix="/api/v1", tags=["Data Generation"])

        app.state.extended_routes_loaded = True
        print("uepi_api: extended routers registered", flush=True)
