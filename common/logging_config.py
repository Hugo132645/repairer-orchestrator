from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from common.config import settings
from common.context import get_correlation_id, get_request_id
from common.redaction import redact

_CONFIGURED = False


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None) or get_request_id(),
            "correlation_id": (getattr(record, "correlation_id", None) or get_correlation_id()),
            "service_name": getattr(record, "service_name", None),
            "event_type": getattr(record, "event_type", None),
        }

        extra_payload = getattr(record, "payload", None)
        if extra_payload is not None:
            payload["payload"] = redact(extra_payload)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            {key: value for key, value in payload.items() if value is not None},
            ensure_ascii=False,
            default=str,
        )


def _file_handler(path: Path) -> logging.Handler:
    handler = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    handler.setFormatter(JsonFormatter())
    return handler


def configure_logging(service_name: str) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.handlers.clear()

    if settings.enable_console_logs:
        console = logging.StreamHandler()
        console.setFormatter(JsonFormatter())
        root_logger.addHandler(console)

    if settings.enable_file_logs:
        root_logger.addHandler(
            _file_handler(settings.log_directory / settings.application_log_filename)
        )

    audit_logger = logging.getLogger("audit")
    audit_logger.handlers.clear()
    audit_logger.propagate = False
    audit_logger.setLevel(logging.INFO)
    if settings.enable_file_logs:
        audit_logger.addHandler(_file_handler(settings.log_directory / settings.audit_log_filename))
    if settings.enable_console_logs:
        audit_console = logging.StreamHandler()
        audit_console.setFormatter(JsonFormatter())
        audit_logger.addHandler(audit_console)

    logging.LoggerAdapter(
        logging.getLogger(__name__),
        {"service_name": service_name},
    ).info(
        "Logging configured",
        extra={
            "service_name": service_name,
            "event_type": "logging.configured",
            "payload": {
                "environment": settings.app_env,
                "log_directory": str(settings.log_directory),
            },
        },
    )
    _CONFIGURED = True
