# LLM provider, LangChain, and optional LiteLLM gateway

Status: Responses provider and LangChain adapter implemented; offline wire and privacy tests pass. The user's reported FreeGG Responses call has not been repeated, and this project has not authenticated to FreeGG or established upstream model identity, terms, quotas, data retention or reliability. See [provider implementation evidence](../implementation/provider-report.md) and [implementation progress](../implementation/PROGRESS.md).

## Initial contract

| Setting | Proposed value | Meaning |
|---|---|---|
| Adapter | LangChain `langchain-openai` / `ChatOpenAI` | Typed application boundary |
| Model | `gpt-6.1-sol` | Provider alias, not verified upstream identity |
| Base URL | `https://freegg.app/v1` | Administrator-configured allowlisted host |
| Wire endpoint | `POST https://freegg.app/v1/responses` | Exactly one `/v1` |
| Routing | `use_responses_api=True` | Explicit Responses routing |
| Credential | Runtime `OPENAI_API_KEY` | Never copy the disclosed key into files |
| Timeout | 120 seconds | Initial per-request ceiling from user example |
| SDK retries | `max_retries=0` | No hidden duplicates/spend |
| Storage request | `store=false`, if supported | Contract-test; unsupported privacy-critical options fail closed |

LangChain documents explicit Responses routing [P1]. Third-party compatibility is a separately tested contract. Never append `/v1/responses` to a base already ending in `/v1`, or silently fall back to `/chat/completions` after failure.

Before deployment rotate the credential disclosed in conversation and inject its replacement through a secret store. Documentation planning needs no test call or personal-data submission.

## Capability gate

Use synthetic prompts in a small integration suite; record versions, endpoint, alias and date, never the key.

| Test | Acceptance |
|---|---|
| Minimal response | Exact wire endpoint `/v1/responses`, usable text |
| Content extraction | String and structured blocks handled; tool/reasoning metadata not displayed as answer |
| Errors | 401/403 configuration; 404/410 incompatible endpoint; 429 rate/budget; 5xx unavailable |
| Timeout/cancel | Terminates within deadline, retry action, no automatic resubmission |
| Privacy option | Verify acceptance/documented semantics; acceptance does not prove retention behavior |
| Structured output | Verify schema support; otherwise validate locally or disable feature |
| Streaming | Verify event/disconnect contract before enabling |
| Usage | Parse available usage; missing counts cannot bypass budgets |
| Tools | Test explicitly only if added; workflow can execute tools itself |
| Context limit | Verify supported bounds; never assume upstream context window |

Start nonstreaming; render completed answers after citation validation. Later streaming must label provisional text. Host request timeout must exceed or deliberately override provider deadline, with a clear timeout state. No live provider tests were run during planning.

## Bounded workflow

Use LangGraph stages: intake → chart → rule retrieval → evidence assembly → composition → citation/claim validation → answer or insufficient evidence. LangChain supplies adapters; it does not calculate planets. Application-controlled tools have no unrestricted shell, browser, filesystem or remote-fetch access.

Terminate after one generation and at most one repair, subject to total time/token budget. A repair never changes endpoint families. Durable graph checkpoints use the same ownership, encryption and deletion policy as conversations. Defer Deep Agents and autonomous research loops until a measured need exists.

## LiteLLM decision and routing trap

Default: direct LangChain → FreeGG Responses. Add LiteLLM only for multiple providers, central budgets or observability. Disable it in MVP until the exact route passes a wire-level contract test.

LiteLLM documents translating Responses requests to Chat Completions for provider types without native Responses support, including generic OpenAI-compatible types. Its current documentation describes native passthrough using `model_info.supported_endpoints` containing `/v1/responses` [P2]. Thus generic Responses support alone does not prove preservation of the required endpoint.

Gateway tests must inspect outbound requests and prove FreeGG `/v1/responses` routing, authorization, supported privacy options and correct content mapping, with no chat fallback. Pin LiteLLM and rerun tests on upgrades. Select provider-prefix configuration from that version's native Responses documentation, not from chat examples.

When enabled, browser → FastAPI → gateway remains the boundary. App uses a virtual gateway key; upstream key lives in gateway secrets. Keep gateway administration private and logs free of prompts/credentials. Avoid stacked retries in application, SDK and proxy.

## Failure and privacy boundaries

Provider failure returns unavailable; computed charts and saved citations remain viewable. Add fallback providers only after consent, privacy/capability/cost checks. Never silently send personal content to another vendor or fabricate uncited answers during outages.

Embedding generation is independent of text generation. Pin embedding revision/tokenizer/prefixes/normalization/dimensions in the index manifest. Changing encoder creates a new collection and reindex. Local embeddings do not make external answer generation private or local.

## Evidence contract

Pass immutable computed facts, retrieved source IDs/passages, selected tradition, source-quality flags, question and response policy. Returned claim references must belong to the supplied evidence set. Backend resolves page/verse metadata from the registry, validates quotes against canonical text, rejects invented citations and separates traditional interpretation from synthesis. Low temperature does not guarantee deterministic text or truthful future prediction. Reproducibility applies to versioned calculation inputs/results and evidence selection, while generated wording may vary.

## Sources

- [P1: LangChain ChatOpenAI](https://docs.langchain.com/oss/python/integrations/chat/openai) — direct HTTP 200 retrieval, 2026-11-15; explicit Responses flag documented.
- [P2: LiteLLM Responses API](https://docs.litellm.ai/docs/response_api) — direct HTTP 200 retrieval, 2026-11-15; bridge/native-endpoint behavior documented.
- FreeGG working endpoint/configuration: user-supplied observation, not an independently verified service guarantee. No provider retention/pricing policy was established.

## Provider and workflow research

[32 Provider compatibility](32-responses-provider-compatibility.md) and [33 workflow state](33-workflow-state-and-failure-design.md) are now detailed release inputs. They confirm the user-reported FreeGG behavior remains unverified; only a fake-server contract test and an opt-in synthetic smoke test can authorize provider enablement. LangGraph checkpoint replay can repeat external calls, so request admission and the no-automatic-replay policy remain authoritative.
