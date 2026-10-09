# A2A identity and agent-card profile

The local gateway publishes a centralized discovery catalogue at:

```text
http://127.0.0.1:8004/.well-known/agent-catalog.json
```

Each catalogue entry links to an A2A 0.3.0 agent card. Cards declare:

- a stable machine identifier and semantic service version;
- provider and documentation metadata;
- the preferred JSON-RPC interface and all supported MIME modes;
- precise skills, examples, tags, and structured input/output modes;
- streaming capability and authenticated-extended-card support;
- the synthetic-only and non-authorizing scope.

## Prototype security declaration

The cards deliberately publish an empty `security` requirement. The local
gateway does not enforce OAuth, mTLS, or signed workload identity, so declaring
those schemes would be misleading.

Before a production or brand deployment, add and enforce all of the following:

1. TLS at every advertised interface.
2. Federated workload identity and audience-bound access tokens.
3. Capability-specific authorization scopes.
4. Signed cards with managed key rotation and verification.
5. Durable task storage, idempotency, quotas, rate limits, and abuse controls.
6. A governed agent registry with ownership, lifecycle, certification, and
   deprecation metadata.
7. Private documentation URLs and authenticated extended cards where needed.

The live prototype documentation endpoint is:

```text
http://127.0.0.1:8004/docs/a2a
```
