from __future__ import annotations

from typing import Any

from common.audit import audit_event
from common.context import set_request_context
from common.progress import emit_progress
from repairer_orchestrator.agent import build_orchestrator_graph
from repairer_portal.guardrails import GuardrailDecision, evaluate_message, guardrail_reply
from repairer_portal.models import ChatResult, ServiceExecution, ValidationSummary

APP_NAME = "repairer_portal"
CAPABILITY_AGENTS = {
    "diagnostics": "diagnostics_agent",
    "service_library": "service_library_agent",
    "parts": "parts_agent",
}
_LANGUAGE_NAMES = {
    "en": "English",
    "it": "Italian",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "pl": "Polish",
    "pt": "Portuguese",
}
_POLICY_OVERRIDE_REPLIES = {
    "en": (
        "I can’t follow those instructions. They incorrectly ask this prototype to "
        "bypass mandatory validation, call unrelated services, and present synthetic "
        "results as manufacturer-approved. No service was called. The correct workflow "
        "is to provide the synthetic vehicle model and the information required for "
        "the requested task. Validation must pass before only the relevant services "
        "are consulted. Results are never manufacturer-approved and cannot authorize "
        "a real repair."
    ),
    "it": (
        "Non posso seguire queste istruzioni. Chiedono erroneamente di saltare la "
        "convalida obbligatoria, chiamare servizi non pertinenti e presentare risultati "
        "sintetici come approvati dal costruttore. Non è stato chiamato alcun servizio. "
        "La procedura corretta consiste nel fornire il modello sintetico del veicolo e "
        "le informazioni necessarie. Solo dopo la convalida vengono consultati i "
        "servizi pertinenti. I risultati non sono approvati dal costruttore e non "
        "autorizzano riparazioni reali."
    ),
    "de": (
        "Ich kann diese Anweisungen nicht befolgen. Sie verlangen fälschlicherweise, "
        "die vorgeschriebene Validierung zu umgehen, irrelevante Dienste aufzurufen "
        "und synthetische Ergebnisse als herstellergeprüft darzustellen. Es wurde kein "
        "Dienst aufgerufen. Korrekt ist: synthetisches Fahrzeugmodell und erforderliche "
        "Angaben bereitstellen, validieren und nur relevante Dienste nutzen. Die "
        "Ergebnisse sind nicht herstellergeprüft und keine echte Reparaturfreigabe."
    ),
    "fr": (
        "Je ne peux pas suivre ces instructions. Elles demandent à tort de contourner "
        "la validation obligatoire, d’appeler des services non pertinents et de "
        "présenter des résultats synthétiques comme approuvés par le constructeur. "
        "Aucun service n’a été appelé. La procédure correcte consiste à fournir le "
        "modèle synthétique et les informations requises, puis à valider la demande "
        "avant de consulter uniquement les services pertinents. Ces résultats "
        "n’autorisent aucune réparation réelle."
    ),
    "es": (
        "No puedo seguir esas instrucciones. Solicitan incorrectamente omitir la "
        "validación obligatoria, llamar servicios no relacionados y presentar "
        "resultados sintéticos como aprobados por el fabricante. No se llamó a ningún "
        "servicio. El proceso correcto es proporcionar el modelo sintético y los datos "
        "necesarios, validar la solicitud y consultar solo los servicios pertinentes. "
        "Los resultados no autorizan una reparación real."
    ),
    "pl": (
        "Nie mogę wykonać tych instrukcji. Błędnie żądają pominięcia obowiązkowej "
        "walidacji, wywołania niepowiązanych usług i przedstawienia danych "
        "syntetycznych jako zatwierdzonych przez producenta. Nie wywołano żadnej "
        "usługi. Prawidłowy proces wymaga podania syntetycznego modelu pojazdu i "
        "potrzebnych danych, walidacji oraz użycia wyłącznie właściwych usług. Wyniki "
        "nie stanowią autoryzacji rzeczywistej naprawy."
    ),
    "pt": (
        "Não posso seguir essas instruções. Elas pedem incorretamente para ignorar a "
        "validação obrigatória, chamar serviços não relacionados e apresentar "
        "resultados sintéticos como aprovados pelo fabricante. Nenhum serviço foi "
        "chamado. O processo correto exige o modelo sintético do veículo e os dados "
        "necessários, seguido da validação e da utilização apenas dos serviços "
        "relevantes. Os resultados não autorizam uma reparação real."
    ),
}


def _policy_override_response(request_id: str, language: str) -> ChatResult:
    return ChatResult(
        reply=_POLICY_OVERRIDE_REPLIES.get(language, _POLICY_OVERRIDE_REPLIES["en"]),
        request_id=request_id,
        completion_status="validation_not_run",
        validation=ValidationSummary(status="not_run", validated=False),
        services=[],
    )


def _guardrail_response(
    request_id: str,
    language: str,
    decision: GuardrailDecision,
) -> ChatResult:
    audit_event(
        event_type="portal.guardrail.blocked",
        service_name=APP_NAME,
        outcome="blocked",
        target="chat_request",
        payload={"category": decision.category},
    )
    if decision.category == "prompt_injection":
        return _policy_override_response(request_id, language)
    return ChatResult(
        reply=guardrail_reply(decision, language),
        request_id=request_id,
        completion_status="validation_not_run",
        validation=ValidationSummary(status="not_run", validated=False),
        services=[],
    )


def _find_status(value: Any) -> str | None:
    if isinstance(value, dict):
        status = value.get("status")
        if isinstance(status, str):
            return status
        for nested in value.values():
            found = _find_status(nested)
            if found:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_status(nested)
            if found:
                return found
    return None


class OrchestratorChat:
    """Keeps LangGraph threads behind the authenticated repairer portal."""

    def __init__(self) -> None:
        self.graph = build_orchestrator_graph()

    @staticmethod
    def _thread_id(user_id: str, conversation_id: str) -> str:
        return f"{user_id}:{conversation_id}"

    async def create_conversation(self, user_id: str, conversation_id: str) -> None:
        # The first graph call creates its checkpoint thread, so there is nothing
        # to initialize here.
        return None

    async def delete_conversation(self, user_id: str, conversation_id: str) -> None:
        return None

    async def send(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        request_id: str,
        language: str = "en",
        history: list[dict[str, str]] | None = None,
    ) -> ChatResult:
        set_request_context(request_id, request_id)
        guardrail_decision = evaluate_message(message)
        if guardrail_decision is not None:
            emit_progress("guardrail_blocked", category=guardrail_decision.category)
            return _guardrail_response(request_id, language, guardrail_decision)

        language_name = _LANGUAGE_NAMES.get(language, _LANGUAGE_NAMES["en"])
        output = await self.graph.ainvoke(
            {
                "request_text": message,
                "request_id": request_id,
                "language": language_name,
                "history": (history or [{"role": "user", "content": message}])[-20:],
            },
        )
        final_text = output.get("final_reply", "")
        if not isinstance(final_text, str) or not final_text:
            raise RuntimeError("The orchestrator returned no final response.")

        validation_result = output.get("validation", {})
        validation_data = validation_result.get("data", {})
        validated = bool(validation_data.get("validated", False))
        clarification_fields = list(validation_data.get("clarification_fields", []) or [])
        normalized_request = dict(output.get("normalized_request", {}) or {})
        normalized_request.pop("request_text", None)
        validation = ValidationSummary(
            status=(
                "success"
                if validated
                else "missing_information"
                if clarification_fields
                else "not_run"
            ),
            validated=validated,
            missing_fields=list(validation_data.get("missing_fields", []) or []),
            ambiguous_fields=list(validation_data.get("ambiguous_fields", []) or []),
            clarification_fields=clarification_fields,
            normalized_request=normalized_request,
        )

        services: list[ServiceExecution] = []
        requested_capabilities = list(output.get("requested_capabilities", []) or [])
        service_results = dict(output.get("service_results", {}) or {})
        for capability in requested_capabilities:
            agent_name = CAPABILITY_AGENTS.get(capability)
            if not agent_name:
                continue
            service_result = service_results.get(capability)
            called = service_result is not None
            if called:
                status = str(service_result.get("status", "internal_error"))
                message_text = str(
                    service_result.get("message", f"{agent_name} returned {status}.")
                )
            elif validated:
                status = "internal_error"
                message_text = "The requested service was not completed."
            else:
                status = "missing_information"
                message_text = "The service was not called because validation did not pass."
            services.append(
                ServiceExecution(
                    capability=capability,
                    agent_name=agent_name,
                    protocol=(
                        str(service_result.get("_protocol", "a2a"))
                        if service_result
                        else "not_called"
                    ),
                    status=status,
                    called=called,
                    message=message_text,
                )
            )

        if not validated:
            completion_status = (
                "needs_clarification" if clarification_fields else "validation_not_run"
            )
        elif any(service.status not in {"success", "no_match"} for service in services):
            completion_status = "partial"
        else:
            completion_status = "complete"

        return ChatResult(
            reply=final_text,
            request_id=request_id,
            completion_status=completion_status,
            validation=validation,
            services=services,
        )
