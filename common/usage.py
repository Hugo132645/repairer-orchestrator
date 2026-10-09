from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from common.config import PROJECT_ROOT
from common.context import ensure_request_context


class LLMUsageStore:
    """Durable operational telemetry without prompt or response content."""

    def __init__(self, database: str | Path) -> None:
        if database != ":memory:":
            path = Path(database)
            path.parent.mkdir(parents=True, exist_ok=True)
            database = path
        self._connection = sqlite3.connect(database, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        with self._lock, self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_usage (
                    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    occurred_at TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    configured_model TEXT NOT NULL,
                    resolved_model TEXT,
                    status TEXT NOT NULL,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    cost_usd REAL,
                    cost_source TEXT,
                    latency_ms REAL NOT NULL
                )
                """
            )

    def record(
        self,
        *,
        service_name: str,
        provider: str,
        configured_model: str,
        resolved_model: str | None,
        status: str,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        total_tokens: int | None,
        cost_usd: float | None,
        cost_source: str | None,
        latency_ms: float,
    ) -> None:
        context = ensure_request_context()
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO llm_usage (
                    occurred_at, request_id, service_name, provider,
                    configured_model, resolved_model, status, prompt_tokens,
                    completion_tokens, total_tokens, cost_usd, cost_source,
                    latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(UTC).isoformat(),
                    context.request_id,
                    service_name,
                    provider,
                    configured_model,
                    resolved_model,
                    status,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    cost_usd,
                    cost_source,
                    latency_ms,
                ),
            )

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def summary(self) -> dict[str, Any]:
        with self._lock:
            totals = self._connection.execute(
                """
                SELECT
                    COUNT(*) AS calls,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successful_calls,
                    SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) AS failed_calls,
                    SUM(prompt_tokens) AS prompt_tokens,
                    SUM(completion_tokens) AS completion_tokens,
                    SUM(total_tokens) AS total_tokens,
                    SUM(cost_usd) AS cost_usd,
                    COUNT(cost_usd) AS costed_calls,
                    AVG(latency_ms) AS average_latency_ms,
                    MAX(occurred_at) AS last_call_at
                FROM llm_usage
                """
            ).fetchone()
            models = self._connection.execute(
                """
                SELECT
                    provider, configured_model, resolved_model,
                    COUNT(*) AS calls, SUM(total_tokens) AS total_tokens,
                    SUM(cost_usd) AS cost_usd
                FROM llm_usage
                GROUP BY provider, configured_model, resolved_model
                ORDER BY calls DESC
                """
            ).fetchall()
            timeline_rows = self._connection.execute(
                """
                SELECT
                    occurred_at AS bucket,
                    total_tokens AS tokens,
                    cost_usd,
                    CASE WHEN cost_usd IS NULL THEN 0 ELSE 1 END AS costed_calls
                FROM llm_usage
                ORDER BY occurred_at, usage_id
                """
            ).fetchall()
        result = dict(totals)
        result["models"] = [dict(row) for row in models]
        result["cost_coverage"] = (
            "unavailable"
            if result["calls"] == 0 or result["costed_calls"] == 0
            else "complete"
            if result["costed_calls"] == result["calls"]
            else "partial"
        )
        cumulative_tokens = 0
        cumulative_cost = 0.0
        timeline: list[dict[str, Any]] = []
        for row in timeline_rows:
            cumulative_tokens += int(row["tokens"] or 0)
            cumulative_cost += float(row["cost_usd"] or 0)
            timeline.append(
                {
                    "timestamp": row["bucket"],
                    "tokens": cumulative_tokens,
                    "cost_usd": cumulative_cost,
                    "has_cost": row["costed_calls"] > 0,
                }
            )
        result["timeline"] = timeline
        return result


usage_store = LLMUsageStore(PROJECT_ROOT / "data" / "llm_usage.db")


def usage_summary() -> dict[str, Any]:
    return usage_store.summary()
