from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from common.audit import audit_event
from common.context import ensure_request_context
from common.observability import get_tracer
from common.redaction import redact
from common.schemas import ToolError, ToolResponse

F = TypeVar("F", bound=Callable[..., Any])
logger = logging.getLogger(__name__)


def observed_tool(service_name: str, tool_name: str) -> Callable[[F], F]:
    """Add audit logging, tracing, timing and error normalization."""

    def decorator(function: F) -> F:
        @functools.wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            context = ensure_request_context()
            started = time.perf_counter()
            tracer = get_tracer(service_name)

            audit_event(
                event_type="tool.requested",
                service_name=service_name,
                outcome="started",
                target=tool_name,
                payload={"arguments": redact(kwargs)},
            )

            try:
                with tracer.start_as_current_span(f"tool.{tool_name}") as span:
                    span.set_attribute("app.request_id", context.request_id)
                    span.set_attribute("app.correlation_id", context.correlation_id)
                    span.set_attribute("app.tool.name", tool_name)
                    result = function(*args, **kwargs)

                duration_ms = round((time.perf_counter() - started) * 1000, 2)
                status = result.get("status", "success") if isinstance(result, dict) else "success"
                audit_event(
                    event_type="tool.completed",
                    service_name=service_name,
                    outcome=str(status),
                    target=tool_name,
                    payload={
                        "duration_ms": duration_ms,
                        "result_summary": redact(result),
                    },
                )
                return result

            except (ValueError, TypeError) as exc:
                logger.warning(
                    "Tool input validation failed",
                    exc_info=True,
                    extra={
                        "event_type": "tool.validation_failed",
                        "service_name": service_name,
                        "payload": {"tool": tool_name},
                    },
                )
                response = ToolResponse(
                    status="invalid_request",
                    message="The tool request was invalid.",
                    errors=[
                        ToolError(
                            code="INVALID_TOOL_REQUEST",
                            message=str(exc),
                            retryable=False,
                        )
                    ],
                )
            except (FileNotFoundError, TimeoutError, ConnectionError) as exc:
                logger.warning(
                    "Tool dependency failed",
                    exc_info=True,
                    extra={
                        "event_type": "tool.dependency_failed",
                        "service_name": service_name,
                        "payload": {"tool": tool_name},
                    },
                )
                response = ToolResponse(
                    status="temporary_failure",
                    message="A required local dependency was unavailable.",
                    errors=[
                        ToolError(
                            code="DEPENDENCY_UNAVAILABLE",
                            message=str(exc),
                            retryable=True,
                        )
                    ],
                )
            except Exception as exc:  # Keep one failed tool from crashing the graph.
                logger.exception(
                    "Unexpected tool failure",
                    extra={
                        "event_type": "tool.internal_error",
                        "service_name": service_name,
                        "payload": {"tool": tool_name},
                    },
                )
                response = ToolResponse(
                    status="internal_error",
                    message="The tool failed unexpectedly.",
                    errors=[
                        ToolError(
                            code="UNEXPECTED_TOOL_FAILURE",
                            message=type(exc).__name__,
                            retryable=False,
                        )
                    ],
                )

            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            payload = response.model_dump(mode="json")
            audit_event(
                event_type="tool.completed",
                service_name=service_name,
                outcome=response.status,
                target=tool_name,
                payload={"duration_ms": duration_ms, "result_summary": payload},
            )
            return payload

        return wrapper  # type: ignore[return-value]

    return decorator
