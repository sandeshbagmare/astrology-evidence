# Authentication, privacy, and security

Status: proposed implementation contract; no authentication has been implemented. Research accessed 2026-11-15. Decisions below are project requirements, not claims that the application already enforces them.

## Account model and Google login

Use Google OpenID Connect authorization-code flow through the Python backend. Authlib is the proposed integration library; pin and validate its FastAPI/Starlette integration during implementation. Request only `openid email profile`; do not request Drive, contacts, calendar, or offline access.

Use `(issuer, sub)` as the unique external identity, never email alone. Validate ID token issuer, audience, expiration and signature against discovery/JWKS; validate a single-use nonce and state tied to the initiating browser. Use PKCE S256 where supported by the client. Register exact callback URLs separately for localhost, staging, and production. Google documents the flow, validation and `sub` identity [A1].

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant App as FastAPI backend
    participant Google
    participant DB as PostgreSQL
    User->>Browser: Sign in with Google
    Browser->>App: GET /auth/google/start
    App->>DB: Store expiring state, nonce, PKCE verifier
    App-->>Browser: Redirect to Google
    Browser->>Google: Consent
    Google-->>Browser: Redirect with code and state
    Browser->>App: GET /auth/google/callback
    App->>DB: Consume state once
    App->>Google: Exchange code and validate token
    App->>DB: Upsert issuer/sub; create opaque session
    App-->>Browser: Secure session cookie; onboarding
```

OAuth transaction expires after 10 minutes. An expired, replayed, mismatched, or rejected callback creates no session. Consent cancellation returns an explanatory sign-in screen. Authorization uses the internal user ID after token validation.

## Sessions and ownership

Project defaults: opaque random session identifier, only its hash stored server-side; rotate on sign-in; idle expiry 24 hours and absolute expiry 7 days; revoke immediately on logout/account deletion. Production cookie: `__Host-session`, `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/`, no Domain. Lax permits the top-level OAuth return. Use a distinct development cookie configuration, never weaken production implicitly. Require CSRF tokens on state-changing form/HTMX requests and validate Origin where available. OWASP treats SameSite as defense in depth, not a replacement for CSRF protection [A2].

Every profile, chart, conversation, report, job, export and deletion query must include ownership checks. Unauthenticated requests receive 401; another user's resource returns a nondisclosing 404. Never accept a user-supplied owner ID. Test cross-user access with two identities. Admin corpus routes require a separate role; never infer it from email domain alone.

## Data boundaries

- Collect birth date, time and uncertainty, birthplace coordinates/timezone, tradition and language only when needed. Display name is optional; gender is unnecessary for chart computation.
- Save profiles only after explicit storage consent. MVP charts require a saved owned profile revision; session-only charts are deferred and must not be promised in the UI. Explain third-party model processing before the first AI request.
- Send structured chart placements, the question and relevant passages to the model. Exclude Google tokens, email, exact birthplace, raw birth timestamp, profile names and unrelated history. User questions can themselves contain identifiers; allow editing and do not promise perfect redaction.
- Store birth records with application-level encryption where deployable, keys outside the database, HTTPS and encrypted database storage. Test key rotation/restore before production.
- FreeGG retention/training policy remains unverified. `store=false` is a request, not proof of no logging or deletion.
- General logs/traces contain IDs, duration, statuses, configuration versions and aggregate usage; exclude raw prompts, birth data, excerpts, answers and tokens. Diagnostic content capture is opt-in and expires.

## Retention and deletion contract

Proposed defaults: saved profiles/readings remain until deleted; unsaved form values are not persisted; operational logs 14 days; OAuth transactions 10 minutes; session expiry as above. Reports retain source-version references while the report exists.

Deletion immediately revokes sessions and hides user records. A durable deletion job removes profiles, reports, conversations, user objects and graph checkpoints within 24 hours. Backups expire within 30 days; restoration replays deletion tombstones before reopening access. These are targets requiring verification against host controls. Explain provider-side deletion limitations before collection. Exports contain user data and source references, not redistribution-prohibited books.

MVP uses an administrator-curated shared corpus only. Private user-uploaded books are deferred. If added, enforce `owner_id`/visibility filters on every retrieval/download and prove isolation before launch.

## Abuse and application controls

Initial demo defaults: 5 concurrent requests globally, 1 active answer per user, 10 AI questions/day/user, enforced in a shared store. Apply body/question size limits server-side. Tool access is allowlisted; prompts cannot choose hosts, execute code, read files, or mutate the corpus. Retrieved text cannot override instructions.

Escape rendered text, sanitize permitted Markdown, prohibit raw model HTML. Resolve citation links through source IDs; reject invented URLs. Enforce HTTPS, CSP and dependency audit gates. Administrator uploads require file/page limits, malformed archive/PDF handling and resource-limited parsing. Arbitrary user URL import is excluded; future import must block internal/private destinations and unsafe redirects.

No diagnosis, guaranteed outcomes, death dates, investment instructions, or fear-based paid remedies. Spiritual interpretation is visibly distinguished from factual claims. These are policy/evaluation requirements, not a claim of infallible filtering.

## Secrets and launch gate

Never copy the credential disclosed in conversation into this project. Rotate it before deployment. Use environment injection locally and host secret storage remotely. No keys in Markdown, browser scripts, screenshots, URLs, error messages or shell-history examples. Separate Google client secret, session material, database credentials and Qdrant API key; restrict Qdrant access to backend/worker.

Before public use: verify provider terms, select region, document export/deletion, configure OAuth branding/callbacks, test restores/rotation, and run ownership/CSRF/injection tests. Determine jurisdiction-specific obligations when launch regions/audience are selected; this document is not a legal compliance certification.

## Sources

- [A1: Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect) — official page retrieved HTTP 200 on 2026-11-15.
- [A2: OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) — primary guidance retrieved HTTP 200 on 2026-11-15.
- [A3: Authlib Starlette client](https://docs.authlib.org/en/latest/client/starlette.html) — retrieval returned HTTP 429; exact API signatures remain unverified.

