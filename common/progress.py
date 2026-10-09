from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

ProgressSink = Callable[[dict[str, Any]], None]
_progress_sink: ContextVar[ProgressSink | None] = ContextVar("progress_sink", default=None)


@contextmanager
def capture_progress(sink: ProgressSink) -> Iterator[None]:
    token = _progress_sink.set(sink)
    try:
        yield
    finally:
        _progress_sink.reset(token)


def emit_progress(event: str, **details: Any) -> None:
    """Send non-sensitive operational progress to the active portal request."""

    sink = _progress_sink.get()
    if sink is not None:
        sink({"event": event, **details})
