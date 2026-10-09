# Known limitations

This project is a local, synthetic prototype. It demonstrates orchestration and
portal behavior; it is not a production workshop, vehicle, warranty, inventory,
or repair-authorization system.

## What is implemented

- Repairer and administrator accounts with role-based API checks.
- Durable SQLite storage for profiles, language preferences, conversations,
  messages, service history, and synthetic repair orders.
- LangGraph request extraction, validation, routing, and response consolidation.
- Three synthetic specialists behind one A2A/MCP gateway.
- Request-scoped progress, structured service statuses, and partial results.
- Administrator usage, cost, health, routing, and conversation views.
- Deterministic guardrails for common prompt-injection, data-access,
  privilege-escalation, unsafe-action, and out-of-scope requests.

## Identity and access

- Accounts are seeded locally and use synthetic credentials.
- Passwords are salted and hashed, but there is no enterprise identity provider,
  federation, MFA, password reset, or account lifecycle management.
- Browser sessions live in process memory and end when the portal restarts.
- Local HTTP cookies do not use the production-only `Secure` setting.
- The prototype has account-level authorization, not production tenant isolation.

## Data and integrations

- All vehicles, procedures, diagnostics, parts, users, and orders are fictional.
- SQLite is suitable for the local demo, not for a multi-instance deployment.
- There is no backup, retention, archival, legal-hold, or disaster-recovery policy.
- There are no real workshop, customer, vehicle, warranty, inventory, billing,
  or authorization integrations.
- Conversation context uses recent stored messages; there is no semantic search,
  vector store, or long-term profile inference.

## Orchestration and model behavior

- Extraction, ambiguity detection, and response wording depend on the configured
  model and can vary between runs.
- Programmatic checks enforce required fields and keep remote calls behind the
  validation node, but they do not prove that every natural-language edge case
  has been anticipated.
- Service calls have timeouts but no automatic retry, circuit breaker, durable
  queue, compensation workflow, or human approval step.
- LangGraph checkpoints are in memory. Conversation messages are durable in
  SQLite, but an in-flight graph execution cannot resume after a process crash.
- Adding a capability is registry-driven, but still requires a domain schema,
  payload mapping, tests, and appropriate portal labels.

## Security

- A2A and MCP traffic is local, unauthenticated HTTP.
- There is no service-to-service identity, gateway authorization, TLS, managed
  secret store, rate limiting, brute-force protection, or production CSRF design.
- The guardrails reduce common misuse; they are not a complete security boundary
  and should be supplemented with authorization, policy enforcement, monitoring,
  threat modelling, and penetration testing.
- Operational logs exclude prompts and generated responses, but production use
  would still need formal privacy, retention, and access-review controls.

## Reliability and operations

- The portal and gateway run as local processes without a supervisor or cluster.
- A machine restart stops the demo and clears active browser sessions.
- Health checks verify discovery endpoints, not every end-to-end tool path.
- Usage cost is an estimate when the model provider supplies enough metadata; it
  is not an invoice.
- There is no alerting, on-call integration, service-level objective, or disaster
  recovery procedure.

## Repair safety

- A fault code is never treated as proof that a component failed.
- Results are informational, synthetic, and cannot authorize a repair,
  replacement, warranty claim, purchase, or safety-critical action.
- A qualified person and authoritative systems must remain responsible for real
  decisions.

## User experience

- The portal has not received a formal accessibility or usability audit.
- The Markdown renderer supports the subset required for assistant responses.
- Translation coverage is hand-maintained and has not been professionally reviewed.

## Before production use

A production design would need confirmed user journeys, regional business rules,
real agent contracts, enterprise identity, tenant boundaries, managed data and
secrets, authenticated service traffic, deployment infrastructure, monitoring,
security testing, privacy review, and human approval rules.
