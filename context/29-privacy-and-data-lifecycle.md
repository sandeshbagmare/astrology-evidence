# Privacy and data lifecycle

Prepared 2026-11-15. This engineering contract is partially implemented through owned sessions, consent, exports, deletion and durable purge jobs; see [implementation progress](../implementation/PROGRESS.md) for evidence and remaining work. It is not legal advice. Read with [authentication](08-authentication-and-security.md), [deployment](10-deployment-and-costs.md), [data contracts](12-data-and-api-contracts.md), and [configuration](43-configuration-reference.md). Jurisdictions, applicable legal bases, transfer requirements and notification duties remain unresolved launch decisions; this document does not invent statutory deadlines.

## Privacy model and decision boundaries

NIST's voluntary Privacy Framework helps organizations identify and manage privacy risks [P1]. Our proposed inventory records data elements, purposes, operators, processing locations and supplier risks. We apply that approach to birth inputs, derived charts and intimate questions. Treat these as private even when no direct name is present; removing email is minimization, not a claim of anonymity. A chart or narrative can remain attributable through account linkage or the person's own words.

Three permissions have distinct meanings: Google sign-in, saving birth profiles, and external AI processing. Google consent does not authorize every later application purpose. Google's policy requires clear disclosures, minimum relevant permissions and renewed consent for changed Google-data use [P2]. Request only the core document's `openid email profile`; use issuer/subject for identity, discard unnecessary claims and avoid storing reusable Google tokens [P3].

Explicit profile-storage consent is mandatory before creating a saved profile. Declining AI still permits deterministic charts from consented saved profiles and licensed library search. Declining storage permits library use but no personalized MVP chart: session-only charts are deferred. Separate unchecked choices and versioned notices must describe recipients, retention and withdrawal. Changing provider or materially expanding purpose requires another decision and notice, not a silent fallback.

Proposed adult beta policy: allow another adult's profile only with their permission, record a minimal owner attestation, and prohibit covert profiling. Do not collect identity documents to prove this automatically. Third-party correction/deletion requests need a reviewed verification process that does not reveal whether a profile exists. Permission claims are not proof of legal authority; support responsibility and handling rules must be settled before enabling this use. No children's profiles in the initial beta.

## Field-level inventory

The following are project retention proposals. “Delete” means immediate serving denial followed by active-store purge within 24 hours; backup exceptions follow below. App recipients include authorized application processes and hosting/storage operators under reviewed arrangements. Administrators have audited, least-privilege access rather than routine access to private content.

| Data fields/artifacts | Purpose and recipients | Retention | Delete/export treatment |
|---|---|---|---|
| User ID, Google issuer/subject, verified-email snapshot, optional display name | Authentication; app/database and Google during login | Account lifetime | Delete identity linkage; export user-facing account fields |
| OAuth code, ID/access token, state, nonce, PKCE verifier | Login validation; app and Google only | Tokens transient; transaction maximum 10 minutes | Consume/delete transaction; never export credentials |
| Hashed session token, expiry, revoked timestamp | Session control; app/database | 24-hour idle, seven-day absolute maximum | Revoke synchronously; purge revoked rows within 24 hours; export session metadata only |
| Consent purpose, notice/provider version, grant/revoke timestamps | Explain and enforce choices; app/database | Account lifetime; deletion receipt exception below | Export choices; purge identity-linked history on account deletion |
| Profile alias, date, time/interval, precision, coordinates, timezone, fold, normalized revisions | Reproducible calculation; app/database and local calculation service | Until profile/account deletion, including old revisions | Export every retained revision; cascade deletion across revisions and dependent content |
| Chart facts, unavailable facts, settings, manifest, input digest | Display/reproduce charts; app/database; selected facts to approved AI | While associated profile exists | Export with provenance; delete derived facts/digests too |
| ReadingRequest question, request hash, idempotency key, deadline | Execute/recover request; app/database; question to approved AI | Successful records while reading exists; failed/cancelled request content proposed maximum 24 hours | Export retained question/status; delete on reading/profile/account deletion |
| Assembled prompts, selected evidence, repair payload, model output | Generate answer; transient app memory and approved provider | No separate prompt archive; answer stored only as Reading | Delete app copies; provider retention separately verified; no promise of provider erasure |
| Reading answer, citation spans, source IDs, versions, provider request ID | Saved history and evidence; app/database and owner | Until reading/profile/account deletion | Export permitted content and source references; remove withdrawn copyrighted spans |
| Feedback category and optional free text | Improve service; app/database, restricted support | Until feedback/reading/account deletion | Export and purge; no automatic training reuse |
| Trace/log request IDs, timings, statuses, usage, safe error codes | Operations/security; app and approved telemetry host | Maximum 14 days, including copies | No prompts, questions, answers, tokens or birth values; authorized investigation only |
| Private response caches, query embeddings, graph state/checkpoints | Request execution; app only | Prefer request lifetime; no persistent private answer cache in MVP | Cancel/clear on deletion; never place private vectors in shared Qdrant |
| Job ID, object reference, owner scope, lease, attempt/error state | Durable deletion/export execution; app/database/worker | Until completion plus bounded operational record | Payload references only, no duplicated birth/question text; purge failed/dead-letter payloads too |
| Export artifact, temporary file, download authorization | User portability; private object store and authenticated owner | Proposed maximum 24 hours after creation | Delete on expiry/account deletion; revoke downloads immediately |
| PostgreSQL backups, WAL/PITR history, object versions, local dumps | Recovery; restricted backup operators/storage | Maximum 30 days across all copies | Expire on schedule; restore only after tombstone replay |
| Tombstone object/account IDs, deletion time, scope, completion status | Prevent resurrection; separate restricted deletion ledger | Until all recoverable pre-deletion copies expire and replay verified | No names, questions, tokens or Google subjects; then erase linked identifiers |
| Licensed scans, passages, vectors, rights evidence and source copyrights | Shared library; approved storage/index, restricted editors; permitted excerpts to users/provider | Edition-specific rights schedule | User export excludes prohibited books; rights withdrawal blocks service immediately and purges restricted derivatives |

Unsaved form values stay in the browser/request and must not enter analytics, crash capture or server drafts. Local development uses synthetic records; production database exports are not development fixtures. Optional external geocoding receives only the place query after its own review, never birth time/date or the user's question.

## Generation and supplier review

Build provider input from an allowlist: required chart facts, bounded question, permitted excerpts and schema. Exclude profile names, email, Google tokens, raw birth timestamp, exact birthplace and unrelated history. Show an editable question preview; warn contextually that typed identifiers travel with the question. Redaction cannot guarantee anonymity.

FreeGG's retention, training, subcontractor and deletion practices remain unverified in this package. `store=false` neither establishes those practices nor proves successful deletion. Before real-user generation, the operational owner must record supplier identity/contact, processing regions, downstream model providers, training use, content/abuse-log retention, deletion/export support, incident notification commitments and contractual terms. Unknown answers block real-user AI, even if a synthetic request works. Reassess any gateway, telemetry vendor or fallback as an additional recipient.

Local query embeddings reduce external transmission but do not make an externally generated answer local. A fully local generative model would avoid that provider transfer, while requiring hardware, quality, security and operational evaluation. Neither alternative removes cloud hosting, backup or operator exposure. Keep chart/library capability available when AI approval is absent.

## Deletion, revocation and export execution

Account deletion commits session revocation, a deny state, tombstone and durable purge request together. Profile deletion similarly denies all revisions and dependent charts/readings. Authorize every read, export download and job publication against current state. A delayed provider response arriving after deletion is discarded; an already transmitted request cannot be recalled. Provider-consent revocation blocks new sends synchronously and cancels pending generation, while existing readings remain until the user deletes them. Storage-consent withdrawal initiates profile deletion.

Purge jobs are idempotent and cover database children, request bodies, feedback, caches, checkpoints, temporary exports, object versions and dead-letter records. Track each store's completion without copying the deleted content. Three transient attempts lead to operator escalation, not abandonment of the obligation. An outage does not reset the original 24-hour target. Report incomplete deletion honestly and preserve denial while recovering.

Tombstones belong outside the ordinary restore rollback boundary. Retain minimal opaque identifiers until the last eligible backup expires, then verify replay and erase them; this is an operational exception, not indefinite retention of a deleted account. Restore into an isolated environment, replay account/profile/reading deletions and rights withdrawals, remove expired exports, invalidate all restored sessions, then run denial checks before opening traffic. Include provider-managed snapshots, WAL, object versions and operator downloads in the 30-day inventory. A backup inaccessible to the application is still retained data.

Export rechecks ownership at request, generation and download. Include account choices, retained profile revisions, chart provenance, questions/readings and permitted citation metadata in a documented portable format. Never include secrets, other owners' data or redistribution-prohibited scans. Short-lived authenticated downloads receive no-store handling; deletion wins any export race. Explain that a user-downloaded file is outside app deletion control.

A sleeping web host and an intermittently available workstation cannot establish reliable deletion. Real-user mode requires an independent scheduled executor, monitored heartbeat, retries and alerts demonstrated within the target. A stale heartbeat disables new profile collection and exports and triggers recovery; existing deletion requests retain priority. Otherwise the demonstration uses synthetic data only. This applies even when AI is disabled.

## Protection, incidents and release evidence

OWASP recommends excluding tokens and sensitive personal content from logs and applying retention to copies and extracts [P4]. Adopt structured metadata-only logs, sanitize error fields, disable raw SDK/HTTP/LLM tracing, and inspect reverse-proxy, database and host logs too. Temporary diagnostic content capture requires specific opt-in, restricted access and a defined expiry; a general debug switch is insufficient.

OWASP frames encryption around the threat model and recommends authenticated encryption and separating keys from data [P5]. Proposed storage uses TLS, encrypted volumes/backups and application encryption for birth records where operationally supportable. Record key version with ciphertext; keep keys outside the database, rotate new writes, re-encrypt old records safely and test restore with retained old keys. Encryption complicates querying and recovery and does not stop an authorized compromised application. Destroying a shared key would also destroy unrelated records; do not label ordinary row deletion “cryptographic erasure.”

Assign an incident lead and privacy contact before launch. For suspected cross-user access or accidental prompt logging: contain the exposed path, stop affected transfers, revoke compromised credentials/sessions, preserve minimal restricted evidence, inventory affected fields/recipients/time window, and contact relevant suppliers. Determine notice obligations with jurisdiction-specific advice; do not assume a universal 72-hour deadline. Record corrective action and verify recovery before reopening. NIST SP 800-61r3 supports integrating preparation, detection, response and recovery into risk management [P6].

Release evidence must demonstrate: denied AI still permits consented charts/library; declined storage creates no profile; logs contain none of seeded private markers; delete/export/provider-response races cannot resurrect content; a stopped web process does not prevent timely purge; restoring the oldest eligible backup preserves deletions; and key rotation/restore succeeds if application-level encryption is selected. All are pending acceptance tests. Record executor owner, supplier review, backup expiry evidence and unresolved jurisdiction decisions before inviting real users.

## Primary sources inspected

Access date for all sources: 2026-11-15. References support principles; retention numbers above are project proposals, not vendor guarantees or statutory requirements.

- P1: NIST Privacy Framework overview, voluntary privacy-risk purpose and version navigation: https://www.nist.gov/privacy-framework . Overview inspected, HTTP 200; no claim that the detailed framework was audited.
- P2: Google API Services User Data Policy, disclosure and minimum-permissions sections, page dated February 15, 2024: https://developers.google.com/terms/api-services-user-data-policy . Google-data policy scope is not a blanket legal determination about birth records.
- P3: Google OpenID Connect, authentication/scopes/identity guidance: https://developers.google.com/identity/openid-connect/openid-connect . Login documentation does not establish downstream AI consent.
- P4: OWASP Logging Cheat Sheet, Data to exclude and Disposal of logs sections: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html . Does not prescribe this project's 14-day period.
- P5: OWASP Cryptographic Storage Cheat Sheet, architectural design/authenticated modes/key-management guidance: https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html . Implementation and key lifecycle remain untested.
- P6: NIST SP 800-61 Rev. 3 publication record and abstract, April 2025: https://csrc.nist.gov/pubs/sp/800/61/r3/final . Publication scope inspected; no claim of a completed organizational incident program.



Encryption policy authority: TLS in transit and encrypted deployed storage/backups are mandatory. Application-level field encryption is an explicit ADR decision before real-user mode; if selected, key separation, rotation and recovery tests become mandatory. If not selected, document the threat model and host controls; do not claim application-level protection.
