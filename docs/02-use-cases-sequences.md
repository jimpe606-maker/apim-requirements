# 02 — Use cases and sequence diagrams

Each use case is a process the solution and its organisation
must support. Steps are numbered to match the diagrams; the *Requirement traces*
line links each use case to the baseline (see `requirements/`).

Component IDs (C1…C17) refer to `01-reference-architecture.md`.

---

## UC-01 Onboard an API provider (team) onto the platform

**Actors:** Provider team (PDev), Platform team, C3 Git, C4 CI/CD, C2 control plane, C11 PKI, C14 audit.
**Trigger:** A team wants to publish its first API.
**Outcome:** The team owns a repository, a pipeline identity and a namespace/tenant in the control plane; nothing was configured by hand.

```mermaid
sequenceDiagram
  autonumber
  actor PDev as Provider team
  participant PT as Platform team
  participant Git as C3 Git (platform repo)
  participant CI as C4 CI/CD
  participant CP as C2 Control plane
  participant PKI as C11 PKI / workload identity
  participant Aud as C14 Audit

  PDev->>Git: Open PR: tenant manifest (team, owners, namespace, environments, quotas)
  Git->>CI: PR pipeline: lint manifest, policy check (naming, ownership, data classification present)
  CI-->>Git: Status: checks passed
  PT->>Git: Review & approve (code owners)
  Git->>CI: Merge → deploy pipeline
  CI->>CP: Create tenant/namespace, RBAC (read-only for humans)
  CI->>PKI: Issue workload identity for the team's pipeline (short-lived, per environment)
  CI->>Git: Bootstrap team API repo from template (contract, policy, pipeline)
  CI->>Aud: Record tenant created (who, what, commit SHA)
  CI-->>PDev: Repo URL, namespace, pipeline identity reference
```

| Step | Description | Control |
|---|---|---|
| 1 | Provider declares itself as code: a tenant manifest with owners, namespace, environments, default quotas and data-classification. | Manifest schema in repo. |
| 2 | PR pipeline validates the manifest against schema and platform policies (e.g. owners must be a group, classification mandatory). | Lint + policy-as-code. |
| 3–4 | Human review by platform team; approval is the only manual act. | Branch protection, CODEOWNERS. |
| 5–6 | Merge triggers deployment; the control plane receives the desired state and creates the tenant with human roles limited to read. | GitOps reconciliation. |
| 7 | The team's pipeline gets a workload identity scoped to its namespace and environment — no shared API keys. | PKI / SPIFFE. |
| 8 | A repository is bootstrapped from the golden template: sample contract, policy bundle, pipeline definition. | Template repo. |
| 9–10 | Audit event written; team receives its handles. | Tamper-evident audit. |

**Requirement traces:** SOL-CAC-001, SOL-CAC-002, SOL-ORG-001, IMPL-ORG-001, IMPL-CAC-001, IMPL-CAC-005.

---

## UC-02 Design, verify and publish an API (contract-first, CI/CD)

**Actors:** PDev, C3, C4, C2, C1, C9 portal, C14.
**Trigger:** New API version ready in the team repo.
**Outcome:** API deployed to gateway and visible in the portal, with lint and policy evidence attached to the release.

```mermaid
sequenceDiagram
  autonumber
  actor PDev as Provider team
  participant Git as C3 Git (team repo)
  participant CI as C4 CI/CD
  participant CP as C2 Control plane
  participant GW as C1 Gateway
  participant Portal as C9 Developer portal
  participant Aud as C14 Audit

  PDev->>Git: Commit OpenAPI contract + policy bundle + route config (PR)
  Git->>CI: PR pipeline
  CI->>CI: Lint contract (style ruleset, security scheme required, breaking-change diff)
  CI->>CI: Verify policy (auth required, scopes declared, rate limit present, PII fields classified)
  CI->>CI: Security tests (contract fuzz, authz negative tests) in ephemeral env
  CI-->>Git: Checks + report as PR annotations
  PDev->>Git: Review, approve, merge (signed commit)
  Git->>CI: Release pipeline (tag)
  CI->>CP: Apply desired state (API, routes, policies, plans) for env=test
  CP->>GW: Distribute config, gateway hot-reloads
  CI->>CI: Smoke test via gateway
  CI->>CP: Promote to prod (same artefact, env overlay)
  CP->>Portal: Publish catalogue entry generated from contract
  CI->>Aud: Record release (SHA, lint/policy report hash, approver)
```

| Step | Description | Control |
|---|---|---|
| 1 | Contract, policies and routing are text files in the team repo; the contract is the API. | OpenAPI 3.x, policy DSL/YAML. |
| 3 | Lint enforces house style and security: every operation has a security scheme, scopes are defined, no free-form `string` for IDs, breaking changes require a major version. | e.g. Spectral ruleset in platform repo. |
| 4 | Policy verification evaluates the policy bundle against platform rules (Rego/Cedar tests, conftest): auth mandatory, JWT `aud` set, rate limit present, PII flagged. | Policy-as-code with unit tests. |
| 5 | Dynamic tests against an ephemeral gateway instance: negative authz tests (wrong scope, expired token, missing DPoP) must fail closed. | Test harness in template. |
| 7 | Merge requires green checks and approval; commit signing is mandatory. | Branch protection. |
| 9–12 | Deployment is a control-plane API call by the pipeline identity; gateways reload without downtime; a smoke test gates promotion. Same artefact goes to all environments. | GitOps, immutable artefacts. |
| 13 | Portal entry (docs, try-it, plans) is generated, never hand-edited. | Docs from contract. |
| 14 | Release record links commit SHA to evidence (lint & policy report hashes). | Assurance evidence. |

**Requirement traces:** SOL-LCM-001, SOL-LCM-002, SOL-LCM-004, SOL-CAC-001, SOL-POL-001, SOL-POL-002, IMPL-CAC-001, IMPL-CAC-002, IMPL-CAC-003, IMPL-CAC-006, IMPL-LCM-002, IMPL-POL-001.

---

## UC-03 Onboard an API consumer (application registration & subscription)

**Actors:** Consumer developer (Dev), C9 portal, C3, C4, C10 client registry, C5 AS, C11 PKI, API owner, C14.
**Trigger:** A developer wants access to a published API.
**Outcome:** A registered OAuth client (public key only on platform side), an approved subscription, sandbox then production access.

```mermaid
sequenceDiagram
  autonumber
  actor Dev as Consumer developer
  participant Portal as C9 Developer portal
  participant Git as C3 Git (subscriptions repo)
  participant CI as C4 CI/CD
  participant Reg as C10 Client registry
  participant AS as C5 Authorization Server
  participant PKI as C11 PKI
  actor Owner as API owner
  participant Aud as C14 Audit

  Dev->>Portal: Sign in (org identity / verified developer account)
  Dev->>Portal: Register application: name, redirect URIs, JWKS URI or cert, requested scopes/plan
  Portal->>Git: Create subscription manifest (PR) on behalf of Dev
  Git->>CI: Validate manifest (scopes exist, plan allowed for org, key type/size, redirect URI policy)
  Owner->>Git: Approve subscription (or auto-approve for sandbox per policy)
  Git->>CI: Merge → apply
  CI->>Reg: Dynamic Client Registration (RFC 7591) with software statement and stores the public JWKS
  Reg->>AS: Client metadata available (client_id, auth method, allowed grants, scopes)
  alt mTLS client
    Dev->>PKI: CSR → client certificate (or bring-your-own from trusted CA)
  end
  CI->>Aud: Record subscription (client_id, scopes, approver)
  Portal-->>Dev: client_id, sandbox endpoints, conformance checklist
  Dev->>Portal: Request production promotion (after conformance tests pass)
  Portal->>Git: PR: env=prod
  Owner->>Git: Approve → CI applies
```

| Step | Description | Control |
|---|---|---|
| 1 | Developer identity is verified (organisation IdP or verified account); anonymous registration is not allowed. | IdP federation. |
| 2 | The app registers with a **public key** (JWKS URI or X.509). No client secrets for confidential clients in FAPI mode. | Key policy. |
| 3–6 | The portal does not write to the control plane; it commits a subscription manifest. Validation and approval happen as code review (auto-approval rules are themselves policy-as-code). | GitOps for subscriptions. |
| 7–8 | Pipeline performs DCR at the client registry; the AS learns the client's allowed grants (`authorization_code` + PKCE, `client_credentials`), auth method (`private_key_jwt` or `tls_client_auth`) and scopes. | RFC 7591/7592. |
| 9 | For mTLS, a client certificate is issued or trusted from an approved CA; the certificate is bound to the client_id. | RFC 8705. |
| 10–11 | Audit and hand-over; sandbox first. | |
| 12–14 | Promotion to production is a second approval; conformance test evidence (e.g. FAPI conformance suite results) attached. | Assurance. |

**Requirement traces:** SOL-DEVX-001, SOL-DEVX-002, SOL-DEVX-003, SOL-DEVX-004, SOL-SEC-004, SOL-SEC-010, SOL-CAC-003, IMPL-ORG-002, IMPL-SEC-002.

---

## UC-04 Authentication and token issuance (FAPI 2.0 authorization code flow)

**Actors:** End user, C16 client, C6 IdP, C5 AS, C10 registry, C12 KMS.
**Trigger:** Client needs an access token to call a protected API on behalf of a user.
**Outcome:** Short-lived, sender-constrained access token (and refresh token if allowed).

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant App as C16 Client app
  participant AS as C5 Authorization Server
  participant IdP as C6 Identity Provider
  participant KMS as C12 KMS/HSM

  App->>App: Generate PKCE code_verifier / S256 challenge and a DPoP key pair (if DPoP)
  App->>AS: POST /par (client auth: private_key_jwt or mTLS) with redirect_uri, scope, code_challenge, state, dpop_jkt
  AS->>AS: Authenticate client (verify JWT signature against registered JWKS / cert thumbprint)
  AS-->>App: request_uri (single use, short TTL)
  App->>User: Redirect to /authorize?client_id&request_uri
  User->>AS: GET /authorize
  AS->>IdP: Authenticate user (MFA / e-ID / federation), step-up per scope
  IdP-->>AS: Authenticated subject + AMR/ACR
  AS->>User: Consent (scopes, data purpose)
  AS-->>App: Redirect with authorization code (+ iss, state) — JARM if message signing required
  App->>AS: POST /token (code, code_verifier, client auth, DPoP proof header)
  AS->>KMS: Sign access token (JWT, RFC 9068) with non-exportable key
  AS-->>App: access_token (cnf: jkt or x5t#S256), expires_in ≤ 10 min, id_token, refresh_token (rotating)
```

| Step | Description | FAPI 2.0 / OAuth 2.1 rule |
|---|---|---|
| 1 | PKCE with S256 is mandatory for all clients; DPoP key pair generated per client instance. | RFC 7636, RFC 9449. |
| 2–4 | Pushed Authorization Request: parameters never travel via the browser; client must authenticate at PAR. `dpop_jkt` binds the future token to the client's key. | RFC 9126. |
| 5–6 | Only `client_id` + `request_uri` are exposed on the front channel. | FAPI 2.0. |
| 7–8 | User authentication is delegated to the IdP; the AS records ACR/AMR for step-up decisions. | OIDC. |
| 9 | Consent records purpose and scopes; becomes an attribute for the PDP (via PIP). | Consent as data. |
| 10 | Code is bound to `iss` (RFC 9207) to prevent mix-up; optional JARM signs the response. | FAPI 2.0. |
| 11–13 | Token endpoint requires PKCE verifier, client authentication and a DPoP proof; the AS signs with an HSM-held key; access token carries the `cnf` claim. Refresh tokens rotate and are sender-constrained. | RFC 8705 / 9449. |

**Requirement traces:** SOL-SEC-001, SOL-SEC-012, SOL-SEC-002, SOL-SEC-003, SOL-SEC-011, SOL-SEC-005, SOL-DATA-001, SOL-DATA-004, PROC-SEC-001.

---

## UC-05 Data access — API call through the gateway (per-request zero trust)

**Actors:** C16 client, C13 threat protection, C1 gateway, C5 AS, C7 PDP, C8 PIP, C15 backend, C14 audit.

```mermaid
sequenceDiagram
  autonumber
  participant App as C16 Client app
  participant TP as C13 Threat protection
  participant GW as C1 Gateway / PEP
  participant AS as C5 AS (JWKS / introspection)
  participant PDP as C7 PDP
  participant PIP as C8 PIP
  participant BE as C15 Backend API
  participant Aud as C14 Observability & audit

  App->>TP: GET /accounts/123  DPoP-bound access token and DPoP proof header (or mTLS)
  TP->>TP: TLS 1.3, WAF, size/rate limits, schema pre-check
  TP->>GW: Forward
  GW->>AS: Fetch/cached JWKS (or introspect opaque token)
  GW->>GW: Validate signature, iss, aud, exp, nbf and scope, then check revocation cache
  GW->>GW: Verify sender constraint: DPoP proof (htm, htu, ath, jti, iat) matches cnf.jkt / mTLS cert matches cnf.x5t#S256
  GW->>PDP: Authorize(subject, client, scopes, resource, action, context)
  PDP->>PIP: Fetch consent, entitlements, data classification
  PDP-->>GW: Permit / Deny (+ obligations: field masking, row filter)
  GW->>GW: Enforce request policy (rate limit per client, schema validation, header allow-list)
  GW->>BE: mTLS call with identity context (JWT propagation or signed headers), correlation-id
  BE->>BE: Verify gateway identity, apply obligations
  BE-->>GW: Response
  GW->>GW: Response policy (schema check, masking, no sensitive headers)
  GW-->>App: 200 + response
  GW->>Aud: Access log (client, subject hash, scopes, decision, latency, trace-id)
```

| Step | Description | Fail-closed behaviour |
|---|---|---|
| 1–3 | Every request carries a sender-constrained token; threat protection runs before any business logic. | Reject oversize, malformed, rate-exceeded. |
| 4–5 | Token validation is local (JWKS cached, rotated) with revocation awareness; `aud` must name this API. | 401 on any failure. |
| 6 | Proof-of-possession: DPoP proof must match method, URI, token hash and be fresh/unique; mTLS thumbprint must match token `cnf`. A replayed or stolen bearer is useless. | 401 `invalid_dpop_proof`. |
| 7–9 | Coarse authz (scope) at gateway, fine-grained authz at PDP with attributes from PIP; obligations can shape the response. | 403 on Deny. |
| 10–13 | Backend trusts only the gateway (mTLS) and receives a verified identity context; it never re-implements authentication. | Backend rejects non-gateway. |
| 14–16 | Response policy prevents data leakage; audit record supports non-repudiation and investigation. | |

**Requirement traces:** SOL-GW-001, SOL-GW-002, SOL-GW-004, SOL-SEC-002, SOL-SEC-006, SOL-SEC-009, SOL-OBS-001, SOL-DATA-002, SOL-DATA-003, IMPL-SEC-001, IMPL-DATA-002.

---

## UC-06 Change a policy (policy-as-code lifecycle)

**Actors:** Security/platform engineer, C3, C4, C2, C1/C7, C14.

```mermaid
sequenceDiagram
  autonumber
  actor Sec as Security engineer
  participant Git as C3 Git (policy repo)
  participant CI as C4 CI/CD
  participant CP as C2 Control plane
  participant PDP as C7 PDP / C1 Gateway
  participant Aud as C14 Audit

  Sec->>Git: PR: change policy (e.g. require step-up ACR for payments scope) + tests
  Git->>CI: Lint policy, run policy unit tests, impact analysis (which APIs/clients affected)
  CI-->>Git: Report: 12 APIs affected, 0 tests failing
  Sec->>Git: Approvals (security + affected API owners via CODEOWNERS)
  Git->>CI: Merge → deploy to test, run conformance suite
  CI->>CP: Publish policy bundle (signed) to prod
  CP->>PDP: Bundle pulled, signature verified, atomic switch
  CI->>Aud: Record policy version, impact report, approvers
```

**Requirement traces:** SOL-POL-001, SOL-POL-003, IMPL-POL-001, IMPL-POL-002, IMPL-ORG-003.

---

## UC-07 Revoke, rotate and decommission

**Actors:** API owner / security, C3, C4, C10, C5, C1, C11, C14.

```mermaid
sequenceDiagram
  autonumber
  actor Own as API owner / Security
  participant Git as C3 Git
  participant CI as C4 CI/CD
  participant Reg as C10 Client registry
  participant AS as C5 AS
  participant GW as C1 Gateway
  participant PKI as C11 PKI
  participant Aud as C14 Audit

  rect rgb(245,245,245)
  note over Own,Aud: A. Emergency revoke (break-glass is still recorded)
  Own->>AS: Revoke client / tokens (break-glass identity, MFA, time-boxed)
  AS->>GW: Push revocation (or short JWKS/introspection TTL)
  AS->>Aud: Record break-glass action
  Own->>Git: Follow-up PR reflecting the state (client disabled)
  end
  rect rgb(245,245,245)
  note over Own,Aud: B. Scheduled key / certificate rotation
  CI->>PKI: Renew certs before expiry (automated)
  AS->>AS: Add new signing key to JWKS, sign with new, retire old after overlap
  Reg->>Reg: Consumer publishes new JWKS key id, old key valid during overlap
  end
  rect rgb(245,245,245)
  note over Own,Aud: C. Deprecate / retire API
  Own->>Git: PR: mark version deprecated (sunset date) → CI publishes Deprecation/Sunset headers + portal notice
  Own->>Git: PR: remove version after sunset → CI removes routes, archives contract, records retirement
  end
```

**Requirement traces:** SOL-SEC-007, SOL-SEC-008, SOL-CAC-004, SOL-LCM-003, SOL-LCM-005, SOL-OPS-002, SOL-OPS-003, IMPL-SEC-003, IMPL-SEC-006, IMPL-OPS-001.
