from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol

from fastapi import Cookie, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from common.config import settings
from common.context import new_request_context
from common.llm import configured_model_name
from common.progress import capture_progress
from common.usage import usage_summary
from repairer_portal.models import ChatResult
from repairer_portal.storage import AccountRole, PortalRepository

STATIC_DIR = Path(__file__).with_name("static")
COOKIE_NAME = "repairer_portal_session"
LanguageCode = Literal["en", "it", "de", "fr", "es", "pl", "pt"]


class ChatBackend(Protocol):
    async def create_conversation(self, user_id: str, conversation_id: str) -> None: ...

    async def delete_conversation(self, user_id: str, conversation_id: str) -> None: ...

    async def send(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        request_id: str,
        language: LanguageCode,
        history: list[dict[str, str]],
    ) -> ChatResult: ...


@dataclass(slots=True)
class PortalSession:
    user_id: str
    role: AccountRole
    display_name: str
    conversation_id: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    language: LanguageCode = "en"
    busy: bool = False
    progress: list[dict[str, Any]] = field(default_factory=list)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)
    language: LanguageCode = "en"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class LanguageRequest(BaseModel):
    language: LanguageCode


def _error_detail(message: str, request_id: str) -> dict[str, str]:
    return {"message": message, "request_id": request_id}


def create_app(
    chat_backend: ChatBackend | None = None,
    health_backend: Callable[[], Awaitable[list[dict[str, Any]]]] | None = None,
    repository: PortalRepository | None = None,
    usage_backend: Callable[[], dict[str, Any]] | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Synthetic Repairer Portal",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    sessions: dict[str, PortalSession] = {}
    started_at = datetime.now(UTC)
    if repository is None:
        database = ":memory:" if chat_backend is not None else Path("data") / "portal.db"
        repository = PortalRepository(database)
    if usage_backend is None:
        usage_backend = usage_summary

    if chat_backend is None:
        from repairer_portal.chat import OrchestratorChat

        chat_backend = OrchestratorChat()
    if health_backend is None:
        from repairer_portal.health import get_service_health

        health_backend = get_service_health

    @app.middleware("http")
    async def add_security_headers(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
            "base-uri 'self'; form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def require_session(token: str | None) -> PortalSession:
        if token is None or token not in sessions:
            raise HTTPException(status_code=401, detail="Authentication required.")
        return sessions[token]

    def require_administrator(token: str | None) -> PortalSession:
        session = require_session(token)
        if session.role != "administrator":
            raise HTTPException(status_code=403, detail="Administrator access required.")
        return session

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.post("/api/login")
    async def login(payload: LoginRequest, response: Response) -> dict[str, str]:
        account = repository.authenticate(payload.username, payload.password)
        if account is None:
            raise HTTPException(status_code=401, detail="Invalid prototype credentials.")

        token = secrets.token_urlsafe(32)
        username = account["username"]
        repository.set_language(username, payload.language)
        conversation_id = repository.latest_conversation(username)
        if conversation_id is None:
            conversation_id = secrets.token_urlsafe(18)
            repository.create_conversation(username, conversation_id)
            await chat_backend.create_conversation(username, conversation_id)
        conversation_messages = repository.messages(username, conversation_id)
        session = PortalSession(
            user_id=username,
            role=account["role"],
            display_name=account["display_name"],
            conversation_id=conversation_id,
            messages=conversation_messages,
            language=payload.language,
        )
        sessions[token] = session
        response.set_cookie(
            COOKIE_NAME,
            token,
            httponly=True,
            samesite="strict",
            secure=False,
            max_age=8 * 60 * 60,
        )
        return {
            "username": username,
            "display_name": session.display_name,
            "role": session.role,
            "language": session.language,
        }

    @app.post("/api/logout")
    async def logout(
        response: Response,
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, str]:
        if token:
            sessions.pop(token, None)
        response.delete_cookie(COOKIE_NAME, samesite="strict")
        return {"status": "success"}

    @app.get("/api/session")
    async def session_info(
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, object]:
        session = require_session(token)
        return {
            "username": session.user_id,
            "display_name": session.display_name,
            "role": session.role,
            "language": session.language,
            "messages": session.messages,
        }

    @app.put("/api/language")
    async def update_language(
        payload: LanguageRequest,
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, str]:
        session = require_session(token)
        if session.busy:
            raise HTTPException(status_code=409, detail="A request is already running.")
        session.language = payload.language
        repository.set_language(session.user_id, session.language)
        return {"status": "success", "language": session.language}

    @app.get("/api/services/health")
    async def service_health(
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, object]:
        require_session(token)
        return {"services": await health_backend()}

    @app.get("/api/repair-orders")
    async def repair_orders(
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, object]:
        session = require_session(token)
        return {"repair_orders": repository.records("repair_orders", session.user_id)}

    @app.get("/api/service-history")
    async def service_history(
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, object]:
        session = require_session(token)
        return {"service_history": repository.records("service_history", session.user_id)}

    @app.get("/api/admin/overview")
    async def admin_overview(
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, object]:
        require_administrator(token)
        now = datetime.now(UTC)
        return {
            "generated_at": now.isoformat(),
            "runtime": {
                "environment": settings.app_env,
                "started_at": started_at.isoformat(),
                "uptime_seconds": round((now - started_at).total_seconds()),
            },
            "model": {
                "provider": settings.llm_provider,
                "configured_model": configured_model_name(),
                "deployment": settings.model_name,
            },
            "usage": usage_backend(),
            "activity": repository.operational_summary(),
            "services": await health_backend(),
            "accounts": repository.admin_overview(),
            "cost_notice": (
                "Cost is shown only when LiteLLM/provider metadata supplies an estimate. "
                "It is not an invoice and may exclude provider discounts or platform charges."
            ),
        }

    @app.get("/api/admin/conversations")
    async def search_admin_conversations(
        query: str = Query(default="", alias="q", max_length=120),
        limit: int = Query(default=25, ge=1, le=100),
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, object]:
        require_administrator(token)
        return {
            "query": query,
            "conversations": repository.search_conversations(query, limit=limit),
        }

    @app.get("/api/admin/conversations/{conversation_id}")
    async def admin_conversation(
        conversation_id: str,
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, object]:
        require_administrator(token)
        conversation = repository.conversation_for_administrator(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return {"conversation": conversation}

    @app.post("/api/service-history/{conversation_id}/resume")
    async def resume_conversation(
        conversation_id: str,
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, object]:
        session = require_session(token)
        if session.busy:
            raise HTTPException(status_code=409, detail="A request is already running.")
        if not repository.owns_conversation(session.user_id, conversation_id):
            raise HTTPException(status_code=404, detail="Conversation not found.")
        conversation_messages = repository.messages(session.user_id, conversation_id)
        session.conversation_id = conversation_id
        session.messages = conversation_messages
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "messages": conversation_messages,
        }

    @app.post("/api/session/new")
    async def new_session(
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, str]:
        session = require_session(token)
        if session.busy:
            raise HTTPException(status_code=409, detail="A request is already running.")

        session.busy = True
        try:
            conversation_id = secrets.token_urlsafe(18)
            repository.create_conversation(session.user_id, conversation_id)
            await chat_backend.create_conversation(session.user_id, conversation_id)
            conversation_messages: list[dict[str, Any]] = []
            session.conversation_id = conversation_id
            session.messages = conversation_messages
        finally:
            session.busy = False
        return {"status": "success"}

    @app.post("/api/chat")
    async def chat(
        payload: ChatRequest,
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, object]:
        session = require_session(token)
        if session.busy:
            raise HTTPException(status_code=409, detail="A request is already running.")

        message = payload.message.strip()
        if not message:
            raise HTTPException(status_code=422, detail="Message cannot be empty.")

        request_id = new_request_context().request_id
        session.busy = True
        session.progress = [{"event": "request_received"}]
        user_message = {"role": "user", "text": message}
        session.messages.append(user_message)
        repository.append_message(session.conversation_id, "user", message)
        try:
            memory = [
                {"role": item["role"], "content": item["text"]} for item in session.messages[-20:]
            ]
            with capture_progress(session.progress.append):
                result = await chat_backend.send(
                    session.user_id,
                    session.conversation_id,
                    message,
                    request_id,
                    session.language,
                    memory,
                )
        except Exception as exc:
            session.messages.pop()
            repository.delete_last_user_message(session.conversation_id)
            raise HTTPException(
                status_code=503,
                detail=_error_detail(
                    "The orchestrator is temporarily unavailable.",
                    request_id,
                ),
            ) from exc
        finally:
            session.busy = False

        assistant_message = {
            "role": "assistant",
            "text": result.reply,
            "metadata": result.model_dump(exclude={"reply"}),
        }
        session.messages.append(assistant_message)
        repository.append_message(
            session.conversation_id,
            "assistant",
            result.reply,
            assistant_message["metadata"],
        )
        occurred_at = datetime.now(UTC).isoformat()
        history_entry = {
            "conversation_id": session.conversation_id,
            "request_id": result.request_id,
            "occurred_at": occurred_at,
            "request": message,
            "response": result.reply,
            "completion_status": result.completion_status,
            "language": session.language,
            "validation": result.validation.model_dump(),
            "services": [service.model_dump() for service in result.services],
        }
        repository.add_history(session.user_id, history_entry)
        if result.validation.validated and result.completion_status in {"complete", "partial"}:
            repository.add_repair_order(session.user_id, history_entry)
        return result.model_dump()

    @app.get("/api/chat/progress")
    async def chat_progress(
        token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    ) -> dict[str, object]:
        session = require_session(token)
        return {"busy": session.busy, "events": list(session.progress)}

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
