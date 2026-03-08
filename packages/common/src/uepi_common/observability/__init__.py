"""OpenTelemetry instrumentation for UEPI"""
from uepi_common.observability.tracing import setup_tracing, get_tracer
from uepi_common.observability.metrics import setup_metrics, get_meter

__all__ = ["setup_tracing", "get_tracer", "setup_metrics", "get_meter"]

