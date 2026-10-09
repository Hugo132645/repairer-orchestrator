from __future__ import annotations

import logging
from typing import Any

from common.config import settings

logger = logging.getLogger(__name__)
_initialized_services: set[str] = set()


def configure_tracing(service_name: str) -> None:
    """Configure optional local OpenTelemetry tracing."""

    if not settings.enable_otel or service_name in _initialized_services:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )
    except ImportError:
        logger.warning(
            "OpenTelemetry packages are unavailable; tracing is disabled",
            extra={
                "event_type": "tracing.unavailable",
                "service_name": service_name,
            },
        )
        return

    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):
        provider = TracerProvider(
            resource=Resource.create(
                {
                    "service.name": service_name,
                    "service.namespace": settings.otel_service_namespace,
                    "deployment.environment": settings.app_env,
                }
            )
        )
        trace.set_tracer_provider(provider)

    if settings.otel_console_exporter:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except Exception:
        logger.exception(
            "Failed to instrument HTTPX",
            extra={
                "event_type": "tracing.httpx_instrumentation_failed",
                "service_name": service_name,
            },
        )

    _initialized_services.add(service_name)


def instrument_asgi_app(app: Any) -> Any:
    if not settings.enable_otel:
        return app
    try:
        from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

        return OpenTelemetryMiddleware(app)
    except Exception:
        logger.exception(
            "Failed to instrument ASGI application",
            extra={"event_type": "tracing.asgi_instrumentation_failed"},
        )
        return app


def get_tracer(name: str):
    from opentelemetry import trace

    return trace.get_tracer(name)
