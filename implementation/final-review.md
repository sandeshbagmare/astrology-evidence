# Independent final branch review â€” 2026-11-15

What this change does: The branch adds a Python application with opaque browser sessions, private revisioned birth profiles, deterministic chart snapshots, rights-controlled retrieval, bounded source-excerpt readings, and durable privacy jobs. AI processing and public production use remain explicitly gated.

Reviewed application paths: main/configuration, identity, profile/chart ownership, reading admission and publication, workflow, corpus import/publication/withdrawal, privacy purge/export, web form dispatch, worker wiring, and Python CI. Assumed load: a multi-user service with one or more ordinary Uvicorn processes. This was a focused independent review, not certification of every branch line.

## Must fix

1. **Ordinary browser forms block the web server event loop** (`src/astrology_evidence/web/__init__.py:188`, chart dispatch at line 245 and reading dispatch at line 250).
   - **What this is:** The asynchronous form endpoint parses a form, then directly calls synchronous database, calculator, retrieval, and provider handlers. The dashboard Calculate chart button uses this endpoint even with JavaScript enabled.
   - **Problem:** A slow chart subprocess or a reading submitted without JavaScript runs on the event-loop thread. Other requests assigned to that worker, including cancellation, consent withdrawal and health checks, cannot proceed until the call returns. A calculation may wait 15 seconds and a reading may consume the 150-second deadline.
   - **Fix:** Parse the form asynchronously, then dispatch the synchronous form work with Starlette's `run_in_threadpool`. Add a focused concurrency regression showing another scheduled coroutine continues while calculation is blocked.
   - **If we skip it:** A normal authenticated browser operation can make a worker unresponsive and delay user privacy controls. Additional workers reduce frequency but do not fix the blocking behavior.
   - **Reproduction:** Called the actual `form_action` with a chart form and a mocked synchronous calculator that sleeps 300 ms; ran a concurrent coroutine scheduled after 20 ms. The timer ran after **0.308 seconds**, confirming event-loop blocking. No application code was modified for this probe.

## Positive checks and boundaries

- Session identifiers are opaque and hashed in storage; mutating API handlers enforce origin and CSRF checks. OAuth transactions bind state to the browser and are consumed once before token exchange.
- Reading admission serializes through a database row, tracks idempotency, rechecks ownership and current evidence rights, and fences publication on cancellation, consent, expiry and execution token.
- The answer workflow bounds model calls and validates exact full-passage quotations. It does not advertise unreviewed applicability as established interpretation.
- Rights withdrawal immediately denies serving, retains a durable vector-purge obligation, and removes local excerpt copies. Account/profile deletion revokes access before asynchronous purge; exports omit source text.
- Production settings reject development login, insecure cookies, missing identity configuration and unresolved privacy/ephemeris gates. CI declares PostgreSQL/Qdrant services; that declaration is not evidence that remote CI passed.

Verdict: Fix 1 before calling the application ready for multi-user operation. The local build can be described as an implemented, gated MVP; external release gates remain separate.

Not checked: live Google sign-in, real provider credentials, licensed production corpus, production embeddings, live PostgreSQL/Qdrant or hosted CI in this review. Those external gates are not reported as implementation defects. Existing planning-era status text is being reconciled by the coordinator.

## Resolution

Form submissions now await Starlette run_in_threadpool for synchronous service work. The regression test asserts the dispatch boundary. Cross-platform CREATE_NO_WINDOW access uses getattr so Linux type checking also succeeds. Final CI evidence is recorded in PROGRESS.md after the integration commit.
