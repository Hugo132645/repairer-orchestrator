from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _as_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, received {raw!r}") from exc


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "local")
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    model_name: str = os.getenv("AGENT_MODEL", "gemini-3.6-flash")
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_directory: Path = Path(os.getenv("LOG_DIRECTORY", str(PROJECT_ROOT / "logs")))
    audit_log_filename: str = os.getenv("AUDIT_LOG_FILENAME", "audit.jsonl")
    application_log_filename: str = os.getenv("APPLICATION_LOG_FILENAME", "application.jsonl")

    enable_console_logs: bool = _as_bool("ENABLE_CONSOLE_LOGS", True)
    enable_file_logs: bool = _as_bool("ENABLE_FILE_LOGS", True)
    enable_otel: bool = _as_bool("ENABLE_OTEL", True)
    otel_console_exporter: bool = _as_bool("OTEL_CONSOLE_EXPORTER", False)
    otel_service_namespace: str = os.getenv(
        "OTEL_SERVICE_NAMESPACE", "repairer-orchestrator-prototype"
    )

    max_text_log_chars: int = _as_int("MAX_TEXT_LOG_CHARS", 500)
    tool_timeout_seconds: int = _as_int("TOOL_TIMEOUT_SECONDS", 20)
    orchestrator_port: int = _as_int("ORCHESTRATOR_PORT", 8000)
    service_registry_path: Path = Path(
        os.getenv(
            "SERVICE_REGISTRY_PATH",
            str(PROJECT_ROOT / "repairer_orchestrator" / "service_agents.json"),
        )
    )


settings = Settings()

if settings.llm_provider not in {"azure_openai_v1", "gemini"}:
    raise ValueError("LLM_PROVIDER must be either 'azure_openai_v1' or 'gemini'")

settings.log_directory.mkdir(parents=True, exist_ok=True)
