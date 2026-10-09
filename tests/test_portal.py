from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from repairer_portal.app import COOKIE_NAME, create_app
from repairer_portal.models import ChatResult, ServiceExecution, ValidationSummary
from repairer_portal.storage import PortalRepository


class FakeChat:
    def __init__(self) -> None:
        self.created: list[tuple[str, str]] = []
        self.deleted: list[tuple[str, str]] = []
        self.messages: list[str] = []
        self.languages: list[str] = []
        self.histories: list[list[dict[str, str]]] = []

    async def create_conversation(self, user_id: str, conversation_id: str) -> None:
        self.created.append((user_id, conversation_id))

    async def delete_conversation(self, user_id: str, conversation_id: str) -> None:
        self.deleted.append((user_id, conversation_id))

    async def send(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        request_id: str,
        language: str,
        history: list[dict[str, str]],
    ) -> ChatResult:
        self.messages.append(message)
        self.languages.append(language)
        self.histories.append(history)
        return ChatResult(
            reply="Synthetic response",
            request_id=request_id,
            completion_status="complete",
            validation=ValidationSummary(status="success", validated=True),
            services=[
                ServiceExecution(
                    capability="diagnostics",
                    agent_name="diagnostics_agent",
                    status="success",
                    called=True,
                    message="Completed.",
                )
            ],
        )


async def fake_health() -> list[dict[str, object]]:
    return [
        {
            "name": "diagnostics_agent",
            "display_name": "Diagnostics",
            "status": "available",
            "latency_ms": 4,
            "advertised_name": "diagnostics_agent",
        }
    ]


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/login",
        json={"username": "demo.repairer", "password": "Synthetic123!"},
    )
    assert response.status_code == 200


def test_login_is_required_for_chat() -> None:
    client = TestClient(create_app(FakeChat(), fake_health))
    page = client.get("/")
    assert page.status_code == 200
    assert page.headers["x-frame-options"] == "DENY"
    assert page.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
    assert 'data-i18n="welcome_message"' in page.text
    assert '<option value="pt">Português</option>' in page.text
    assert "/static/styles.css?v=20260730-4" in page.text
    assert "/static/themes/tech.css?v=20260731-1" in page.text
    assert "/static/app.js?v=20260731-3" in page.text
    app_script = client.get("/static/app.js").text
    technology_theme = client.get("/static/themes/tech.css")
    classic_snapshot = client.get("/static/themes/classic/styles.css")
    assert technology_theme.status_code == 200
    assert "body.theme-tech" in technology_theme.text
    assert classic_snapshot.status_code == 200
    assert "Process details" in app_script
    assert "usageChart(data.usage)" in app_script
    assert "repairerPortalTheme" in app_script
    assert "completionStatusText(record.completion_status)" in app_script
    assert "metadataText(fieldLabels[key])" in app_script
    assert "Avviare una nuova conversazione?" in app_script
    assert "Iniciar uma nova conversa?" in app_script
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 401


def test_login_rejects_invalid_credentials() -> None:
    client = TestClient(create_app(FakeChat(), fake_health))
    response = client.post(
        "/api/login",
        json={"username": "demo.repairer", "password": "wrong"},
    )
    assert response.status_code == 401
    assert COOKIE_NAME not in response.cookies


def test_authenticated_conversation_health_reset_and_logout() -> None:
    backend = FakeChat()
    client = TestClient(create_app(backend, fake_health))
    _login(client)

    login_cookie = client.cookies[COOKIE_NAME]
    assert login_cookie

    health = client.get("/api/services/health")
    assert health.status_code == 200
    assert health.json()["services"][0]["status"] == "available"

    language = client.put("/api/language", json={"language": "it"})
    assert language.status_code == 200
    assert client.get("/api/session").json()["language"] == "it"

    chat = client.post("/api/chat", json={"message": "Assess synthetic P0301"})
    assert chat.status_code == 200
    payload = chat.json()
    assert payload["reply"] == "Synthetic response"
    assert payload["completion_status"] == "complete"
    assert payload["request_id"]
    assert payload["services"][0]["agent_name"] == "diagnostics_agent"
    assert backend.messages == ["Assess synthetic P0301"]
    assert backend.languages == ["it"]
    assert backend.histories[0][-1] == {
        "role": "user",
        "content": "Assess synthetic P0301",
    }
    progress = client.get("/api/chat/progress")
    assert progress.status_code == 200
    assert progress.json() == {
        "busy": False,
        "events": [{"event": "request_received"}],
    }

    session = client.get("/api/session").json()
    assert session["messages"][0] == {
        "role": "user",
        "text": "Assess synthetic P0301",
    }
    assert session["messages"][1]["metadata"]["request_id"] == payload["request_id"]

    repair_orders = client.get("/api/repair-orders").json()["repair_orders"]
    assert len(repair_orders) == 1
    assert repair_orders[0]["repair_order_id"] == "SYN-RO-DEMO-REPAIRER-0001"
    assert repair_orders[0]["request"] == "Assess synthetic P0301"
    assert repair_orders[0]["validation"]["validated"] is True

    service_history = client.get("/api/service-history").json()["service_history"]
    assert len(service_history) == 1
    assert service_history[0]["response"] == "Synthetic response"
    assert service_history[0]["language"] == "it"

    old_conversation_id = backend.created[0][1]
    new_session = client.post("/api/session/new")
    assert new_session.status_code == 200
    assert len(backend.created) == 2
    assert backend.created[0][1] != backend.created[1][1]
    assert backend.deleted == []
    assert client.get("/api/session").json()["messages"] == []
    assert len(client.get("/api/service-history").json()["service_history"]) == 1
    resumed = client.post(f"/api/service-history/{old_conversation_id}/resume")
    assert resumed.status_code == 200
    assert resumed.json()["conversation_id"] == old_conversation_id
    assert len(resumed.json()["messages"]) == 2
    assert client.get("/api/session").json()["messages"][0]["text"] == "Assess synthetic P0301"
    assert client.put("/api/language", json={"language": "pt"}).status_code == 200
    assert client.get("/api/session").json()["language"] == "pt"

    assert client.post("/api/logout").status_code == 200
    assert client.get("/api/session").status_code == 401
    _login(client)
    assert len(client.get("/api/repair-orders").json()["repair_orders"]) == 1


def test_chat_failure_has_support_reference_and_rolls_back_message() -> None:
    class FailingChat(FakeChat):
        async def send(
            self,
            user_id: str,
            conversation_id: str,
            message: str,
            request_id: str,
            language: str,
            history: list[dict[str, str]],
        ) -> ChatResult:
            raise ConnectionError("Synthetic backend unavailable")

    client = TestClient(create_app(FailingChat(), fake_health))
    _login(client)

    response = client.post("/api/chat", json={"message": "Assess P0301"})
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["message"] == "The orchestrator is temporarily unavailable."
    assert detail["request_id"]
    assert client.get("/api/session").json()["messages"] == []


def test_roles_are_enforced_for_administrator_overview() -> None:
    usage = {
        "calls": 7,
        "successful_calls": 6,
        "failed_calls": 1,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "cost_usd": 0.0123,
        "costed_calls": 7,
        "average_latency_ms": 250.0,
        "last_call_at": "2026-07-30T10:00:00+00:00",
        "models": [],
        "cost_coverage": "complete",
    }
    client = TestClient(create_app(FakeChat(), fake_health, usage_backend=lambda: usage))
    _login(client)
    assert client.get("/api/admin/overview").status_code == 403
    assert client.get("/api/admin/conversations?q=P0301").status_code == 403
    assert (
        client.post(
            "/api/chat",
            json={"message": "Investigate synthetic code P0301 for search"},
        ).status_code
        == 200
    )

    client.post("/api/logout")
    login = client.post(
        "/api/login",
        json={"username": "demo.admin", "password": "AdminSynthetic123!"},
    )
    assert login.status_code == 200
    assert login.json()["role"] == "administrator"
    overview = client.get("/api/admin/overview")
    assert overview.status_code == 200
    assert client.get("/api/repair-orders").json()["repair_orders"] == []
    assert overview.json()["usage"]["total_tokens"] == 150
    assert overview.json()["usage"]["cost_usd"] == 0.0123
    assert overview.json()["model"]["configured_model"]
    assert overview.json()["services"][0]["name"] == "diagnostics_agent"
    assert {account["username"] for account in overview.json()["accounts"]} == {
        "demo.admin",
        "demo.repairer",
    }
    search = client.get("/api/admin/conversations?q=P0301")
    assert search.status_code == 200
    assert len(search.json()["conversations"]) == 1
    match = search.json()["conversations"][0]
    assert match["username"] == "demo.repairer"
    assert "P0301" in match["match_text"]
    detail = client.get(f"/api/admin/conversations/{match['conversation_id']}")
    assert detail.status_code == 200
    assert detail.json()["conversation"]["messages"][0]["role"] == "user"
    repairer_reference = "SYN-RO-DEMO-REPAIRER-0001"
    assert detail.json()["conversation"]["repair_orders"][0]["repair_order_id"] == (
        repairer_reference
    )
    assert (
        detail.json()["conversation"]["service_history"][0]["services"][0]["agent_name"]
        == "diagnostics_agent"
    )
    assert client.get("/api/admin/conversations?q=%25").json()["conversations"] == []
    reference_search = client.get(f"/api/admin/conversations?q={repairer_reference}")
    assert reference_search.status_code == 200
    assert len(reference_search.json()["conversations"]) == 1
    reference_match = reference_search.json()["conversations"][0]
    assert reference_match["username"] == "demo.repairer"
    assert reference_match["match_repair_order"] == repairer_reference

    admin_chat = client.post(
        "/api/chat",
        json={"message": "Assess synthetic P0301 from the administrator account"},
    )
    assert admin_chat.status_code == 200
    admin_orders = client.get("/api/repair-orders").json()["repair_orders"]
    assert admin_orders[0]["repair_order_id"] == "SYN-RO-DEMO-ADMIN-0001"
    assert admin_orders[0]["repair_order_id"] != repairer_reference

    client.post("/api/logout")
    _login(client)
    repairer_orders = client.get("/api/repair-orders").json()["repair_orders"]
    assert repairer_orders[0]["repair_order_id"] == repairer_reference


def test_conversation_memory_survives_portal_restart() -> None:
    database = Path("tests") / f".portal-memory-{uuid4().hex}.db"
    first_repository = PortalRepository(database)
    second_repository = None
    try:
        first_backend = FakeChat()
        first_client = TestClient(create_app(first_backend, fake_health, first_repository))
        _login(first_client)
        response = first_client.post("/api/chat", json={"message": "Remember synthetic P0301"})
        assert response.status_code == 200

        second_backend = FakeChat()
        second_repository = PortalRepository(database)
        second_client = TestClient(create_app(second_backend, fake_health, second_repository))
        _login(second_client)
        restored = second_client.get("/api/session").json()["messages"]
        assert [message["role"] for message in restored] == ["user", "assistant"]
        assert restored[0]["text"] == "Remember synthetic P0301"
        assert second_backend.created == []

        assert second_client.post("/api/chat", json={"message": "Continue"}).status_code == 200
        assert second_backend.histories[0][-3:] == [
            {"role": "user", "content": "Remember synthetic P0301"},
            {"role": "assistant", "content": "Synthetic response"},
            {"role": "user", "content": "Continue"},
        ]
    finally:
        first_repository.close()
        if second_repository is not None:
            second_repository.close()
        database.unlink(missing_ok=True)
