from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

GuardrailCategory = Literal["prompt_injection", "data_access", "unsafe_action", "out_of_scope"]


@dataclass(frozen=True, slots=True)
class GuardrailDecision:
    category: GuardrailCategory


_PROMPT_INJECTION = re.compile(
    r"\b(?:ignore|disregard|forget|override)\b.{0,45}\b(?:instructions?|rules?|prompt|policy|guardrails?)\b"
    r"|\b(?:skip|bypass|disable)\b.{0,35}"
    r"\b(?:validation|guardrails?|safety (?:rules?|checks?|controls?)|policy)\b"
    r"|\b(?:developer|jailbreak|unrestricted)\s+mode\b"
    r"|\bcall\s+(?:all|every)\s+(?:agent|service)s?\b"
    r"|\bmanufacturer[- ]approved\b",
    re.IGNORECASE | re.DOTALL,
)
_DATA_ACCESS = re.compile(
    r"\b(?:reveal|show|print|give|dump|extract|return)\b.{0,55}"
    r"\b(?:system prompt|hidden instructions?|api keys?|passwords?|"
    r"auth(?:entication)? tokens?|cookies?|"
    r"other users?'? (?:data|conversations?|orders?)|database)\b"
    r"|\b(?:conversations?|orders?|records?|data|repair histor(?:y|ies))\b.{0,45}"
    r"\b(?:belonging to|owned by|from|of)\s+(?:other users?|another user|"
    r"another repairer|someone else)\b"
    r"|\b(?:all|every)\s+users?(?:'s|')?\s+(?:data|conversations?|orders?|records?|"
    r"repair histor(?:y|ies))\b"
    r"|\b(?:show|open|list|export|give|grant|unlock)\b.{0,55}"
    r"\b(?:someone else's|another user's|another repairer's)\s+(?:\w+\s+){0,3}"
    r"(?:data|conversations?|orders?|records?|repair histor(?:y|ies))\b"
    r"|\b(?:pretend|act|pose)\b.{0,25}\b(?:admin|administrator)\b"
    r"|\b(?:elevate|upgrade|change|grant)\b.{0,35}\b(?:role|permissions?|access)\b"
    r".{0,35}\b(?:admin|administrator|all|every account)\b"
    r"|\b(?:give|grant|unlock)\b.{0,35}\b(?:access|permissions?)\b.{0,35}"
    r"\b(?:all|every)\s+accounts?\b"
    r"|\b(?:give|grant|assign|add)\b.{0,35}\b(?:admin|administrator)\b.{0,20}"
    r"\b(?:access|permissions?|role|privileges?)\b"
    r"|\b(?:admin|administrator)\s+(?:password|credentials?|token)\b",
    re.IGNORECASE | re.DOTALL,
)
_UNSAFE_ACTION = re.compile(
    r"\b(?:disable|bypass|defeat|remove|deactivate|tamper with)\b.{0,45}"
    r"\b(?:airbags?|brakes?|abs|esc|immobili[sz]er|emissions?|adblue|odometer|safety system)\b"
    r"|\b(?:roll back|alter)\b.{0,25}\bodometer\b"
    r"|\bauthori[sz]e\b.{0,30}\brepair\b",
    re.IGNORECASE | re.DOTALL,
)
_OUT_OF_SCOPE = re.compile(
    r"\b(?:write|compose)\b.{0,20}\b(?:poem|song|essay|story)\b"
    r"|\b(?:recipe|weather forecast|football score|stock price|political news|travel itinerary)\b"
    r"|\b(?:solve|do)\b.{0,20}\b(?:homework|math problem)\b"
    r"|\b(?:write|debug)\b.{0,20}\b(?:python|javascript|computer code|software)\b",
    re.IGNORECASE | re.DOTALL,
)


def evaluate_message(message: str) -> GuardrailDecision | None:
    """Block clear policy abuse before any LLM or remote-agent invocation."""

    for category, pattern in (
        ("prompt_injection", _PROMPT_INJECTION),
        ("data_access", _DATA_ACCESS),
        ("unsafe_action", _UNSAFE_ACTION),
        ("out_of_scope", _OUT_OF_SCOPE),
    ):
        if pattern.search(message):
            return GuardrailDecision(category=category)
    return None


_REPLIES = {
    "en": {
        "prompt_injection": (
            "I can’t follow instructions that attempt to change or bypass the "
            "assistant’s validation, safety rules, or agent-routing controls. No "
            "service was called. I can help with a synthetic workshop request when "
            "you provide the relevant vehicle and service information."
        ),
        "data_access": (
            "I can’t disclose system instructions, credentials, tokens, private "
            "records, or another user’s data. No service was called. Administrators "
            "must use the authorized, read-only dashboard for account-level oversight."
        ),
        "unsafe_action": (
            "I can’t help disable, bypass, or authorize changes to safety, security, "
            "emissions, or odometer systems. No service was called. I can support a "
            "synthetic diagnostic or procedure lookup that preserves manufacturer "
            "safety controls and requires qualified review."
        ),
        "out_of_scope": (
            "That request is outside this workshop assistant’s scope. No service was "
            "called. I can help with synthetic vehicle diagnostics, repair-procedure "
            "lookup, and parts availability."
        ),
    },
    "it": {
        "prompt_injection": (
            "Non posso seguire istruzioni che tentano di modificare o aggirare la "
            "convalida, le regole di sicurezza o l’instradamento degli agenti. Non è "
            "stato chiamato alcun servizio. Posso aiutarti con una richiesta sintetica "
            "di officina fornendo veicolo e informazioni di assistenza pertinenti."
        ),
        "data_access": (
            "Non posso divulgare istruzioni di sistema, credenziali, token, registri "
            "privati o dati di altri utenti. Non è stato chiamato alcun servizio. Gli "
            "amministratori devono usare il pannello autorizzato in sola lettura."
        ),
        "unsafe_action": (
            "Non posso aiutare a disattivare, aggirare o autorizzare modifiche ai "
            "sistemi di sicurezza, protezione, emissioni o contachilometri. Non è "
            "stato chiamato alcun servizio. Posso supportare una ricerca sintetica "
            "che preservi i controlli di sicurezza e richieda una verifica qualificata."
        ),
        "out_of_scope": (
            "La richiesta non rientra nell’ambito di questo assistente d’officina. "
            "Non è stato chiamato alcun servizio. Posso aiutare con diagnostica "
            "sintetica, ricerca di procedure e disponibilità ricambi."
        ),
    },
    "de": {
        "prompt_injection": (
            "Ich kann keine Anweisungen befolgen, die Validierung, Sicherheitsregeln "
            "oder Agentensteuerung umgehen. Es wurde kein Dienst aufgerufen."
        ),
        "data_access": (
            "Ich kann keine Systemanweisungen, Zugangsdaten, Token, privaten Datensätze "
            "oder Daten anderer Benutzer offenlegen. Es wurde kein Dienst aufgerufen."
        ),
        "unsafe_action": (
            "Ich kann nicht beim Deaktivieren oder Umgehen von Sicherheits-, Abgas- "
            "oder Kilometerzählersystemen helfen. Es wurde kein Dienst aufgerufen."
        ),
        "out_of_scope": (
            "Diese Anfrage liegt außerhalb des Werkstattumfangs. Es wurde kein Dienst "
            "aufgerufen. Ich helfe bei synthetischer Diagnose, Verfahren und Teilen."
        ),
    },
    "fr": {
        "prompt_injection": (
            "Je ne peux pas suivre des instructions visant à contourner la validation, "
            "les règles de sécurité ou le routage des agents. Aucun service n’a été appelé."
        ),
        "data_access": (
            "Je ne peux pas divulguer les instructions système, identifiants, jetons, "
            "dossiers privés ou données d’un autre utilisateur. Aucun service n’a été appelé."
        ),
        "unsafe_action": (
            "Je ne peux pas aider à désactiver ou contourner les systèmes de sécurité, "
            "d’émissions ou de kilométrage. Aucun service n’a été appelé."
        ),
        "out_of_scope": (
            "Cette demande sort du périmètre de l’assistant d’atelier. Aucun service "
            "n’a été appelé. Je peux aider pour diagnostics, procédures et pièces synthétiques."
        ),
    },
    "es": {
        "prompt_injection": (
            "No puedo seguir instrucciones para eludir la validación, las reglas de "
            "seguridad o el enrutamiento de agentes. No se llamó a ningún servicio."
        ),
        "data_access": (
            "No puedo revelar instrucciones del sistema, credenciales, tokens, registros "
            "privados ni datos de otro usuario. No se llamó a ningún servicio."
        ),
        "unsafe_action": (
            "No puedo ayudar a desactivar o eludir sistemas de seguridad, emisiones o "
            "kilometraje. No se llamó a ningún servicio."
        ),
        "out_of_scope": (
            "La solicitud queda fuera del ámbito del asistente de taller. No se llamó a "
            "ningún servicio. Puedo ayudar con diagnósticos, procedimientos y piezas sintéticas."
        ),
    },
    "pl": {
        "prompt_injection": (
            "Nie mogę wykonać poleceń omijających walidację, zasady bezpieczeństwa lub "
            "sterowanie agentami. Nie wywołano żadnej usługi."
        ),
        "data_access": (
            "Nie mogę ujawniać instrukcji systemowych, danych logowania, tokenów, "
            "prywatnych rekordów ani danych innych użytkowników. Nie wywołano usługi."
        ),
        "unsafe_action": (
            "Nie mogę pomagać w wyłączaniu ani obchodzeniu systemów bezpieczeństwa, "
            "emisji lub licznika przebiegu. Nie wywołano żadnej usługi."
        ),
        "out_of_scope": (
            "To żądanie wykracza poza zakres asystenta warsztatowego. Nie wywołano "
            "usługi. Pomagam w syntetycznej diagnostyce, procedurach i częściach."
        ),
    },
    "pt": {
        "prompt_injection": (
            "Não posso seguir instruções para contornar a validação, as regras de "
            "segurança ou o encaminhamento de agentes. Nenhum serviço foi chamado."
        ),
        "data_access": (
            "Não posso divulgar instruções do sistema, credenciais, tokens, registos "
            "privados ou dados de outro utilizador. Nenhum serviço foi chamado."
        ),
        "unsafe_action": (
            "Não posso ajudar a desativar ou contornar sistemas de segurança, emissões "
            "ou quilometragem. Nenhum serviço foi chamado."
        ),
        "out_of_scope": (
            "O pedido está fora do âmbito do assistente de oficina. Nenhum serviço foi "
            "chamado. Posso ajudar com diagnósticos, procedimentos e peças sintéticas."
        ),
    },
}


def guardrail_reply(decision: GuardrailDecision, language: str) -> str:
    translations = _REPLIES.get(language, _REPLIES["en"])
    return translations.get(decision.category, _REPLIES["en"][decision.category])
