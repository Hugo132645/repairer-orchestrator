from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from uuid import uuid4

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


@dataclass(frozen=True, slots=True)
class RequestContext:
    request_id: str
    correlation_id: str


def new_request_context(correlation_id: str | None = None) -> RequestContext:
    request_id = str(uuid4())
    resolved_correlation_id = correlation_id or request_id
    _request_id.set(request_id)
    _correlation_id.set(resolved_correlation_id)
    return RequestContext(
        request_id=request_id,
        correlation_id=resolved_correlation_id,
    )


def ensure_request_context() -> RequestContext:
    request_id = _request_id.get()
    correlation_id = _correlation_id.get()
    if request_id and correlation_id:
        return RequestContext(request_id=request_id, correlation_id=correlation_id)
    return new_request_context()


def set_request_context(request_id: str, correlation_id: str) -> None:
    _request_id.set(request_id)
    _correlation_id.set(correlation_id)


def get_request_id() -> str | None:
    return _request_id.get()


def get_correlation_id() -> str | None:
    return _correlation_id.get()
