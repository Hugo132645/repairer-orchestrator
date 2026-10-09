from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from common.context import ensure_request_context
from common.redaction import redact

audit_logger = logging.getLogger("audit")


def audit_event(
    *,
    event_type: str,
    service_name: str,
    outcome: str,
    actor: str = "system",
    target: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    context = ensure_request_context()
    audit_logger.info(
        event_type,
        extra={
            "event_type": event_type,
            "service_name": service_name,
            "request_id": context.request_id,
            "correlation_id": context.correlation_id,
            "payload": {
                "occurred_at": datetime.now(UTC).isoformat(),
                "actor": actor,
                "target": target,
                "outcome": outcome,
                **redact(payload or {}),
            },
        },
    )
