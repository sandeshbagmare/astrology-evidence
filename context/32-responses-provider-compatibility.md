# Responses provider compatibility contract

Prepared 2026-11-15. This document is a design and verification plan, not evidence that FreeGG supports every OpenAI or LangChain feature. The only FreeGG facts in scope are the user's report: `https://freegg.app/v1` with model alias `gpt-6.1-sol`; Responses requests reportedly work and Chat Completions returned HTTP 410. No live request was made in this research, no credential was copied, and upstream model identity, retention, quotas, pricing, reliability, and service terms remain unverified.

## What the official specifications establish

LangChain's `ChatOpenAI` integration targets official OpenAI request and response specifications. Its documentation says non-standard third-party fields such as `reasoning_content`, `reasoning`, and `reasoning_details` are not extracted or preserved by the integration. The integration accepts an explicit `base_url`; `use_responses_api=True` forces Responses routing, and Responses routing is also selected when Responses-only features are used. The documented minimum for Responses support is `langchain-openai>=0.3.9`; the application must pin an exact tested version rather than tracking latest. LangChain exposes ordinary text through `AIMessage.text`, structured content through `content_blocks`, response metadata, refusal fields, tool calls, and usage metadata when supplied by the provider. Pin and test the selected LangChain output representation; `output_version` changes must not silently alter extraction. These are client-library capabilities, not guarantees for an OpenAI-compatible server.

OpenAI's official Responses migration guide shows the wire request as `POST /v1/responses` with `model` and `input`, and presents `output_text` as a convenience accessor. The Responses model is a list of output items rather than one Chat Completions message. Items can include message text, refusal, reasoning, tool calls and tool results; applications must select user-visible message text and retain other metadata only for validation or diagnostics. OpenAI documents native structured outputs, tools, reasoning output and usage on its own service. Compatibility with those features must be proved separately for FreeGG.

LiteLLM's official documentation describes two materially different paths. For generic OpenAI-compatible deployments, `/v1/responses` is bridged to `/v1/chat/completions` by default; Responses-only fields may be converted, approximated or dropped. Native passthrough requires declaring `/v1/responses` in `model_info.supported_endpoints` (documented since LiteLLM v1.101.0) or using a deployment mode that is explicitly native. A gateway test must inspect its outbound request, because a successful proxy response alone does not prove native routing.

Primary source access log, 2026-11-15: direct HTTP 200 retrieval and targeted text inspection for LangChain ChatOpenAI integration (https://docs.langchain.com/oss/python/integrations/chat/openai), OpenAI Responses migration guide (https://developers.openai.com/api/docs/guides/migrate-to-responses), and LiteLLM native Responses passthrough (https://docs.litellm.ai/docs/response_api_native_passthrough). The LiteLLM overview (https://docs.litellm.ai/docs/response_api) also returned HTTP 200 and confirmed the bridge default. The OpenAI API reference URL https://platform.openai.com/docs/api-reference/responses/create returned HTTP 403; its contents were not inspected. The readable official migration guide provides the OpenAI evidence here. Web-tool retrieval returned no usable text, so direct HTTPS retrieval supplied inspection evidence. Neither OpenAI documentation nor LangChain documentation verifies FreeGG.

## MVP adapter contract

The application owns one adapter boundary. It constructs a `ChatOpenAI` instance with `model="gpt-6.1-sol"`, `base_url="https://freegg.app/v1"`, `use_responses_api=True`, a runtime-injected `OPENAI_API_KEY`, a bounded timeout of at most 120 seconds, and `max_retries=0`. The endpoint builder must append exactly `/responses` to a base that ends in `/v1`; configuration validation rejects a base already ending in `/responses` and rejects accidental `/v1/v1`. The adapter logs a redacted endpoint, requested alias, library version and request ID where available, never the key, prompt, birth data or raw response.

For wire controls, test Responses `max_output_tokens` and `text.format` explicitly; Chat Completions names must not leak through unexamined adapter mappings. Require a completed response and completed message status; incomplete, failed, empty, or truncated results cannot publish. `output_text` is an SDK convenience, not a required top-level wire field.

The MVP sends a minimized input: system policy, question, computed facts, and authorized evidence passages. It does not send name, email, Google tokens, raw place labels, or coordinates when derived facts suffice. `store=false` is requested only if the server accepts it. Acceptance proves request compatibility, not retention behavior; provider privacy policy and operational evidence are still required before real-user data. Unknown privacy semantics fail closed for real-user mode.

Output normalization handles at least these forms: a plain string; a message containing text content blocks; a Responses item list containing one or more text blocks; an explicit refusal; and a response with reasoning or tool metadata plus final text. Only completed assistant message text can become a draft answer. Refusal is a terminal provider result, not an empty answer. Reasoning summaries and tool metadata are excluded from displayed answers; hidden reasoning is never requested or logged. Provider annotations and IDs are not treated as validated application citations. The server then applies the existing citation, chart-fact and prohibited-claim validators. A malformed or ambiguous output becomes `provider_invalid_output`.

Native structured output is a capability gate, not an MVP assumption. If a provider accepts a JSON schema, the adapter may use `with_structured_output(..., method="json_schema")`; otherwise the application uses ordinary text plus local parsing and validation, or disables structured generation. A schema-looking JSON string is not evidence of schema enforcement. Tools are disabled in MVP: Python owns chart calculation, retrieval and persistence, and FreeGG tool support is unknown. Do not bind tools merely because LangChain supports them. Streaming is also disabled until event ordering, disconnect behavior and usage trailers are tested.

## Failure, timeout and accounting rules

The total request deadline is 150 seconds, including admission, one generation and at most one validation repair. The provider timeout is reduced to remaining deadline. Browser disconnect stops delivery; the browser can later poll the persisted request. If the bounded server operation survives, it may finish within its original deadline; an explicit cancellation fences publication. Transport loss or process failure is classified separately. If transmission may have reached FreeGG but the response is lost, the request enters `unknown`; the system does not automatically resend. A user-initiated retry creates a new idempotency key and warns that duplicate provider processing is possible. There is no automatic retry at the LangChain, OpenAI SDK, application, or LiteLLM layers.

Classify HTTP 401/403 as configuration/authentication failure, 404/410 as endpoint incompatibility, 408/timeout/disconnect as unknown when send state is uncertain, 429 as rate or budget exhaustion, and 5xx/network errors as unavailable or unknown according to send evidence. Preserve chart snapshots and citations during provider failure. `response.usage` or LangChain `usage_metadata` is parsed when present. Missing usage never disables limits: reserve a conservative maximum allowance before sending and retain the reservation when usage is absent or uncertain. No FreeGG price or quota is assumed; cost displays remain unavailable or explicitly estimated only after an administrator records verified pricing.

Optional provider parameters are allowlisted. `temperature`, `max_tokens`/`max_completion_tokens`, reasoning controls, metadata, `store`, stream flags and response format are each contract-tested; a provider rejection is surfaced as unsupported configuration. Do not forward arbitrary kwargs from a browser. A changed parameter or model alias requires a compatibility run and manifest version update.

## Gateway and deployment boundaries

Direct LangChain to FreeGG is the initial path. LiteLLM remains disabled until a wire-level test proves native `/v1/responses` passthrough and preservation of required fields. Browser requests go to FastAPI; only SSR/backend code can access the gateway. If LiteLLM is enabled, FastAPI holds a virtual gateway key while the upstream FreeGG key exists only in gateway secrets. The browser receives neither credential. Only administrators configure the endpoint: validate HTTPS, exact allowlisted hostname/port and path, reject embedded credentials and unexpected query strings, and prevent redirects or DNS resolution to loopback, private, link-local or metadata destinations. Production egress policy reinforces this SSRF boundary; local fake-server exceptions belong only in isolated tests. Gateway administration is private, and logs exclude prompts, birth data, keys and raw completions. `ALLOW_PROVIDER_FALLBACK=false` is mandatory: no silent switch to another vendor, endpoint family or Chat Completions after a failure.

## Fake-server contract matrix

Before enabling FreeGG or LiteLLM, a local fake OpenAI-compatible server must record method, path, headers, JSON body and cancellation. The suite contains at least these 18 cases:

1. Minimal request reaches exactly `/v1/responses`.
2. Base URL ending `/v1` does not produce `/v1/v1`.
3. Base URL ending `/responses` is rejected at startup.
4. Bearer auth is sent; the key is absent from logs.
5. Plain string output normalizes.
6. Text content-block output normalizes.
7. Multiple output items select message text only.
8. Refusal is surfaced distinctly.
9. Reasoning metadata is classified without logging their raw content and not displayed.
10. Unknown block types fail closed.
11. Structured schema accepted and validated.
12. Structured schema rejected produces unsupported capability, with no text fallback unless explicitly configured.
13. `store=false` accepted; unsupported privacy option fails closed.
14. Tools are rejected in MVP and never retried as chat.
15. Usage present is parsed; usage absent retains conservative allowance.
16. 401/403/404/410/429/5xx map to distinct failure codes.
17. Timeout and dropped response become unknown without automatic resend.
18. Browser disconnect preserves polling state; explicit cancellation and elapsed deadline prevent late publication.

Add a proxy recording test that proves LiteLLM's outbound path is `/v1/responses` with an unchanged Responses body. A separate negative test must demonstrate that missing `supported_endpoints` causes the documented chat bridge, and therefore blocks gateway enablement.

## Upgrade protocol

Pin Python, `langchain-openai`, `openai`, LiteLLM (if enabled), and prompt/schema versions. Record requested and reported model identifiers, endpoint mode, capability matrix, fake-server results and date in the release manifest. On every dependency or provider alias change, rerun the matrix, compare serialized request shapes and normalized outputs, inspect retry behavior, and review privacy/logging. A failed native-route, privacy, schema, timeout or no-duplicate test blocks release. Compatibility with official OpenAI specifications must be labeled separately from compatibility verified against FreeGG; neither implies the other.


