"""OpenTelemetry tracing setup"""
from typing import Optional
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource


def setup_tracing(
    service_name: str = "uepi",
    service_version: str = "1.0.0",
    otlp_endpoint: Optional[str] = None,
    enabled: bool = True,
) -> None:
    """Setup OpenTelemetry tracing
    
    Args:
        service_name: Service name for traces
        service_version: Service version
        otlp_endpoint: OTLP endpoint URL (e.g., "http://localhost:4317")
        enabled: Whether tracing is enabled (default: True)
    """
    if not enabled:
        # Use NoOpTracerProvider if disabled
        trace.set_tracer_provider(trace.NoOpTracerProvider())
        return
    
    # Create resource
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # Add span processor if OTLP endpoint is configured
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
    
    # For development, also add console exporter if no OTLP endpoint
    if not otlp_endpoint:
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        console_exporter = ConsoleSpanExporter()
        console_processor = BatchSpanProcessor(console_exporter)
        provider.add_span_processor(console_processor)


def get_tracer(name: str) -> trace.Tracer:
    """Get OpenTelemetry tracer
    
    Args:
        name: Tracer name (typically module name)
        
    Returns:
        Tracer instance
    """
    provider = trace.get_tracer_provider()
    return provider.get_tracer(name)

