# Error handling

This guide explains how the prototype reports invalid input, missing data,
service failures, and unexpected errors. All examples refer to synthetic data.

## Status contract

Service tools return `common.schemas.ToolResponse` with one of these statuses:

| Status | Meaning | Portal behavior |
|---|---|---|
| `success` | The service completed. | Shows the returned synthetic result. |
| `no_match` | Input was valid, but the dataset had no match. | Reports the absence without inventing data. |
| `missing_information` | Required or unambiguous information is missing. | Requests clarification and does not delegate. |
| `invalid_request` | Structured tool input failed validation. | Reports the invalid fields. |
| `temporary_failure` | A dependency could not be reached or timed out. | Keeps other results and marks the turn partial. |
| `internal_error` | An unexpected failure occurred. | Shows a generic failure without internal details. |

`no_match` is a valid outcome, not a service failure. A fault code that is not in
the synthetic diagnostic dataset is also reported as unrecognized rather than
being used to invent a diagnosis.

## Request flow

Error handling follows the same order as the graph:

1. The portal checks authentication, request shape, and concurrent activity.
2. Deterministic guardrails block clear security, unsafe-action, and out-of-scope
   requests before the model runs.
3. The extraction node identifies the requested workshop fields and capabilities.
4. The validation node checks the extraction against recent conversation context.
5. Programmatic checks enforce required fields and the capability allowlist.
6. Only validated requests can reach the remote-service node.
7. Each service validates its own payload and returns a structured status.
8. The orchestrator consolidates all returned statuses into one response.
9. The portal independently marks omitted or failed requested work as partial.

## Portal responses

| Situation | HTTP response |
|---|---|
| No valid browser session | `401 Authentication required.` |
| Incorrect synthetic credentials | `401 Invalid prototype credentials.` |
| Repairer requests an administrator endpoint | `403 Administrator access required.` |
| Account does not own the requested conversation | `404 Conversation not found.` |
| Empty or malformed request body | `422` |
| A request is already running in the session | `409 A request is already running.` |
| Orchestrator fails or returns no answer | `503` with a request reference |

If a chat request fails before an assistant response is produced, the portal
removes the pending user message instead of storing an incomplete turn.

## Guardrail blocks

Clear prompt injection, credential extraction, access to another user's records,
privilege escalation, unsafe vehicle-system bypass, and unrelated requests are
blocked in `repairer_portal/guardrails.py`.

A blocked request:

- has `completion_status: validation_not_run`;
- calls neither the model nor a remote service;
- creates no repair order;
- records only the guardrail category in audit telemetry;
- returns a localized, safe explanation.

Manual results and regression prompts are in
[GUARDRAIL_TESTS.md](GUARDRAIL_TESTS.md).

## Validation and clarification

The model performs extraction and a separate semantic review. The program then
checks the result again before routing.

Current requirements are:

| Capability | Required fields |
|---|---|
| Diagnostics | Fault code |
| Service Library | Vehicle model and fault code |
| Parts Inventory | Vehicle model and part name |

The market defaults to `EU` when omitted. Fault codes are normalized to uppercase.
Multiple unresolved vehicle models remain ambiguous. Missing or ambiguous data
produces `missing_information`, and no remote service is called.

The graph topology is the enforcement boundary:

```text
extract_request -> validate_request -> invoke_services -> respond
                                  \-> respond when clarification is required
```

There is no path from extraction directly to remote services.

## Service input errors

Each service creates a strict Pydantic query model before reading its synthetic
dataset. Unexpected fields, empty required strings, invalid lengths, and empty
fault-code lists return `invalid_request` with field-level details.

The shared `observed_tool` wrapper converts common dependency failures into
`temporary_failure` and unexpected exceptions into `internal_error`. User-facing
messages remain generic; exception class names may be retained for local
troubleshooting, but prompts and sensitive values are never logged.

## Partial results

Requested services run independently after validation. If one service fails, the
orchestrator preserves its status and the successful results from other services.
The portal then applies deterministic completion accounting:

- `success` and `no_match` count as completed service outcomes;
- any failed or omitted requested service makes the turn `partial`;
- missing or ambiguous input makes the turn `needs_clarification`;
- a guardrail block makes the turn `validation_not_run`.

The prototype does not automatically retry failed services.

## Registry and startup errors

The registry fails fast on missing or malformed JSON, duplicate agent names,
invalid URLs, unknown fields, or invalid protocol configuration. Disabled entries
are ignored.

`start_all.ps1` runs the preflight checks before opening the portal and gateway.
The preflight verifies Python, packages, model configuration, synthetic data,
registry loading, imports, and local port availability.

## Health checks

`scripts/check_services.py` checks each enabled A2A card and the MCP catalogue.
The portal uses the same discovery endpoints for its sidebar status:

- green: available with the expected identity;
- yellow: reachable but identity does not match;
- red: unavailable.

Health indicates discovery availability. It does not replace an end-to-end tool
test.

## Logging and redaction

Application and audit logs exclude prompts and generated responses. Redaction
covers common secret fields such as authorization headers, API keys, passwords,
tokens, secrets, and cookies. New code must still avoid sending sensitive content
to the logger; redaction is a fallback, not permission to log it.

## Verification

```powershell
python -m pytest -v
python -m ruff check .
python -m ruff format --check .
python scripts/check_services.py
```

When adding an error path, add a focused test that proves the expected status,
that prohibited delegation did not occur, and that no success data was invented.
