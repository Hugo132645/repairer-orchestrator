# Prototype Demo Guide

This guide provides a repeatable presentation flow for the synthetic Repairer
Orchestrator prototype. It is designed for an internal manager or an early
client conversation, not for real repair operations.

## Before the demonstration

From the repository root:

```powershell
.\stop_all.ps1
.\start_all.ps1
```

`start_all.ps1` runs the environment preflight before opening any service.
Confirm that every check reports `PASS`.

After the portal and gateway windows are running:

```powershell
.\verify_demo.ps1
```

Open `http://127.0.0.1:8000` and sign in:

```text
Username: demo.repairer
Password: Synthetic123!
```

Confirm that Diagnostics, Service library, and Parts inventory show green
availability indicators in the sidebar.

## What to explain

The demonstration has three layers:

1. The portal provides authentication, conversation management, validation
   summaries, workflow status, and live service health.
2. The Repairer Orchestrator uses the LLM for language understanding, field
   extraction, ambiguity detection, service selection, and response wording.
3. Deterministic Python validates required fields and blocks remote calls until
   validation succeeds. Remote A2A agents return structured synthetic results.

The service agents remain tools controlled by the orchestrator. They are not
embedded subgraphs or handoff destinations.

## Scenario 1: Complete diagnostic request

Prompt:

```text
For Demo Compact Hatchback in the EU, assess fault code P0301.
```

Expected:

- Validation succeeds.
- The request summary shows Demo Compact Hatchback, P0301, and EU.
- Diagnostics is marked as called.
- The response treats findings as possibilities, not confirmed failure.
- The result is labeled synthetic and not repair authorization.

Demonstrates: hybrid extraction, deterministic validation, and narrow routing.

## Scenario 2: Missing information

Start a new conversation, then enter:

```text
Demo Compact Hatchback has a warning light. Please diagnose it.
```

Expected:

- Validation returns `missing_information`.
- `fault_codes` is identified as missing.
- Diagnostics is not called.
- The assistant asks only for the fault code.

Then enter:

```text
The fault code is P0301.
```

Expected: validation succeeds and Diagnostics is called.

Demonstrates: multi-turn clarification and deterministic delegation blocking.

## Scenario 3: Ambiguous information

Start a new conversation, then enter:

```text
For Demo Compact Hatchback, the code may be P0301 or P0302. Diagnose it and find the procedure.
```

Expected:

- `fault_codes` is visibly marked ambiguous.
- Diagnostics and Service library are not called.
- The assistant asks which code is correct.

Then enter:

```text
I confirm the code is P0301.
```

Expected: validation succeeds and the relevant services are called.

Demonstrates: LLM ambiguity detection with deterministic enforcement.

## Scenario 4: Complete multi-agent request

Start a new conversation, then enter:

```text
For Demo Compact Hatchback in the EU, assess P0301, find the matching repair procedure, and check availability of a synthetic ignition coil.
```

Expected:

- Validation succeeds.
- Diagnostics, Service library, and Parts inventory are all accounted for.
- Each service status appears in the request panel.
- The assistant returns one consolidated response.

Demonstrates: call-and-return multi-agent orchestration through official A2A messages.

## Scenario 5: Valid request with no match

Start a new conversation, then enter:

```text
For Demo Executive Saloon in the EU, find the repair procedure for P0301 and check availability of a synthetic ignition coil.
```

Expected:

- Validation succeeds because the request is structurally complete.
- Service library and Parts inventory return `no_match`.
- The assistant does not invent a procedure, compatible part, or substitute.

Demonstrates: the distinction between invalid input, system failure, and valid
input with no synthetic match.

## Scenario 6: Unavailable gateway and structured failure

Stop the Agent Gateway process listening on port 8004. Refresh the service
indicators and confirm that the connected services turn red.

Enter:

```text
For Demo Compact Hatchback in the EU, assess P0301 and check availability of a synthetic ignition coil.
```

Expected:

- Validation still completes because it runs inside the orchestrator.
- Selected remote services are shown as unavailable or failed.
- The request is labeled partial rather than complete.
- Each failure keeps its structured `temporary_failure` status.
- The assistant explains that remote results could not be retrieved and does not
  invent diagnostic or inventory data.

Restart the full stack after this scenario:

```powershell
.\stop_all.ps1
.\start_all.ps1
```

Demonstrates: live health, service isolation, and deterministic completion
accounting.

## Closing the demonstration

Emphasize:

- All vehicle, procedure, diagnostic, and inventory content is synthetic.
- The prototype demonstrates orchestration patterns, not production security or
  real repair authorization.
- Additional agents follow the documented registry and A2A integration pattern.
- Client identity, persistent storage, integrations, and approval rules require
  client requirements before implementation.

See:

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)
- [ERROR_HANDLING.md](ERROR_HANDLING.md)
- [ADDING_SERVICE_AGENTS.md](ADDING_SERVICE_AGENTS.md)
