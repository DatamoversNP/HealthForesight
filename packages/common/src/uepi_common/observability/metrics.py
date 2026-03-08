"""OpenTelemetry metrics setup"""
from typing import Optional
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


def setup_metrics(
    service_name: str = "uepi",
    service_version: str = "1.0.0",
    otlp_endpoint: Optional[str] = None,
    enabled: bool = True,
    export_interval_seconds: int = 60,
) -> None:
    """Setup OpenTelemetry metrics
    
    Args:
        service_name: Service name for metrics
        service_version: Service version
        otlp_endpoint: OTLP endpoint URL (e.g., "http://localhost:4317")
        enabled: Whether metrics are enabled (default: True)
        export_interval_seconds: Export interval in seconds (default: 60)
    """
    if not enabled:
        # Use NoOpMeterProvider if disabled
        metrics.set_meter_provider(metrics.NoOpMeterProvider())
        return
    
    # Create resource
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
    })
    
    # Create metric reader if OTLP endpoint is configured
    reader = None
    if otlp_endpoint:
        exporter = OTLPMetricExporter(endpoint=otlp_endpoint)
        reader = PeriodicExportingMetricReader(
            exporter,
            export_interval_millis=export_interval_seconds * 1000,
        )
    
    # Create meter provider
    provider = MeterProvider(resource=resource, metric_readers=[reader] if reader else [])
    metrics.set_meter_provider(provider)


def get_meter(name: str) -> metrics.Meter:
    """Get OpenTelemetry meter
    
    Args:
        name: Meter name (typically module name)
        
    Returns:
        Meter instance
    """
    provider = metrics.get_meter_provider()
    return provider.get_meter(name)

