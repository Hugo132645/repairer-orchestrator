from __future__ import annotations

import importlib
import os
import socket
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from urllib.parse import urlparse

from common.config import PROJECT_ROOT, settings
from repairer_orchestrator.registry import load_service_agent_definitions

EXPECTED_PYTHON = (3, 12)
REQUIRED_MODULES = (
    "repairer_portal.app",
    "repairer_orchestrator.agent",
    "agent_gateway.server",
)
REQUIRED_FILES = (
    PROJECT_ROOT / "service_agents" / "service_library" / "data" / "repair_procedures.json",
)
REQUIRED_PORTS = (8000, 8004)


@dataclass(frozen=True, slots=True)
class PreflightCheck:
    name: str
    status: str
    message: str


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _valid_openai_v1_base_url(value: str) -> bool:
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.path.rstrip("/").endswith("/openai/v1")
        and not parsed.query
        and not parsed.fragment
    )


def run_preflight(*, check_ports: bool = True) -> list[PreflightCheck]:
    checks: list[PreflightCheck] = []

    python_ok = sys.version_info[:2] == EXPECTED_PYTHON
    checks.append(
        PreflightCheck(
            name="python",
            status="pass" if python_ok else "fail",
            message=(
                f"Python {sys.version_info.major}.{sys.version_info.minor}"
                if python_ok
                else "Python 3.12 is required."
            ),
        )
    )

    try:
        langgraph_version = version("langgraph")
        langgraph_ok = langgraph_version.startswith("1.")
    except PackageNotFoundError:
        langgraph_version = "not installed"
        langgraph_ok = False
    checks.append(
        PreflightCheck(
            name="langgraph",
            status="pass" if langgraph_ok else "fail",
            message=f"LangGraph {langgraph_version}; expected a supported 1.x release.",
        )
    )

    env_path = PROJECT_ROOT / ".env"
    checks.append(
        PreflightCheck(
            name="environment-file",
            status="pass" if env_path.is_file() else "fail",
            message=".env is present." if env_path.is_file() else ".env is missing.",
        )
    )

    if settings.llm_provider == "azure_openai_v1":
        azure_variables = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "AGENT_MODEL")
        missing = [
            name
            for name in azure_variables
            if not os.getenv(name, "").strip() or "your_" in os.getenv(name, "").casefold()
        ]
        base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        if base_url and not _valid_openai_v1_base_url(base_url):
            missing.append("OPENAI_BASE_URL (must be an HTTPS /openai/v1/ base URL)")
        checks.append(
            PreflightCheck(
                name="azure-openai-v1-configuration",
                status="pass" if not missing else "fail",
                message=(
                    "Azure OpenAI v1 configuration is present."
                    if not missing
                    else f"Invalid or missing Azure setting(s): {', '.join(missing)}."
                ),
            )
        )
    else:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        key_ok = bool(api_key) and "your_" not in api_key.casefold()
        checks.append(
            PreflightCheck(
                name="gemini-credential",
                status="pass" if key_ok else "fail",
                message=(
                    "GOOGLE_API_KEY is configured."
                    if key_ok
                    else "GOOGLE_API_KEY is missing or still a placeholder."
                ),
            )
        )

    try:
        definitions = load_service_agent_definitions()
        registry_message = f"Registry contains {len(definitions)} enabled service agent(s)."
        registry_ok = bool(definitions)
    except Exception as exc:
        registry_message = f"Registry validation failed: {type(exc).__name__}."
        registry_ok = False
    checks.append(
        PreflightCheck(
            name="service-registry",
            status="pass" if registry_ok else "fail",
            message=registry_message,
        )
    )

    failed_modules: list[str] = []
    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except Exception as exc:
            failed_modules.append(f"{module} ({type(exc).__name__}: {exc})")
    checks.append(
        PreflightCheck(
            name="service-modules",
            status="pass" if not failed_modules else "fail",
            message=(
                "All portal and service modules import successfully."
                if not failed_modules
                else f"Module import failures: {', '.join(failed_modules)}."
            ),
        )
    )

    missing_files = [
        str(path.relative_to(PROJECT_ROOT)) for path in REQUIRED_FILES if not path.is_file()
    ]
    checks.append(
        PreflightCheck(
            name="synthetic-data",
            status="pass" if not missing_files else "fail",
            message=(
                "Required synthetic data files are present."
                if not missing_files
                else f"Missing files: {', '.join(missing_files)}."
            ),
        )
    )

    if check_ports:
        occupied = [str(port) for port in REQUIRED_PORTS if not _port_available(port)]
        checks.append(
            PreflightCheck(
                name="ports",
                status="pass" if not occupied else "fail",
                message=(
                    "Ports 8000 and 8004 are available."
                    if not occupied
                    else f"Ports already in use: {', '.join(occupied)}. Run .\\stop_all.ps1."
                ),
            )
        )

    return checks


def preflight_succeeded(checks: list[PreflightCheck]) -> bool:
    return all(check.status == "pass" for check in checks)
