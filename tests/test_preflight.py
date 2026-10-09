from __future__ import annotations

from common.preflight import (
    PreflightCheck,
    _valid_openai_v1_base_url,
    preflight_succeeded,
)


def test_preflight_requires_every_check_to_pass() -> None:
    assert preflight_succeeded(
        [
            PreflightCheck("python", "pass", "ok"),
            PreflightCheck("registry", "pass", "ok"),
        ]
    )
    assert not preflight_succeeded(
        [
            PreflightCheck("python", "pass", "ok"),
            PreflightCheck("ports", "fail", "occupied"),
        ]
    )


def test_openai_v1_base_url_accepts_azure_foundry_endpoint() -> None:
    assert _valid_openai_v1_base_url("https://example.services.ai.azure.com/openai/v1/")


def test_openai_v1_base_url_rejects_completion_and_query_paths() -> None:
    assert not _valid_openai_v1_base_url(
        "https://example.services.ai.azure.com/openai/v1/chat/completions"
    )
    assert not _valid_openai_v1_base_url(
        "https://example.services.ai.azure.com/openai/v1/?api-version=2025-01-01"
    )
