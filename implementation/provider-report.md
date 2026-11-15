# Provider implementation evidence — 2026-11-15

Files: answers/contracts.py, answers/provider.py, answers/__init__.py, tests/test_provider.py.

API: ResponsesProvider(api_key: str | SecretStr, *, base_url="https://freegg.app/v1", transport=None).generate(GenerationRequest(prompt, timeout_seconds=120, max_output_tokens=1800)) returns GenerationResult(content, usage=None, model="gpt-6.1-sol"). ProviderError exposes safe code and unknown boolean; never upstream body, secret or exception. Constructor injection has no global credential lookup.

Real LangChain ChatOpenAI serializes POST /v1/responses, store=false, max_output_tokens, no tools, no streaming, max_retries=0. Exact destination validation and disabled redirects prevent alternate hosts. Timeouts reduce to remaining allowance, capped120; known expired deadlines do not send. Raw wire response validation rejects incomplete messages/responses, unknown blocks, tools, refusal, empty output; reasoning summaries are excluded. Usage missing/invalid remains None. Local tracing_context(enabled=False) prevents ambient LangSmith tracing. JSON/citation validation and conservative budget reservation belong to the workflow.

Verification:
- First missing-provider assertion failed before implementation. Added privacy tracing regression failed (observed None instead of False), then passed with explicit context.
- 42 provider tests passed with global Python3.14, langchain-openai1.7.0, openai3.28.0, httpx0.28.1.
- 42 provider tests passed with project .runtime314 langchain-openai1.8.0/openai3.51.0 after preloading ONLY already-installed global jiter native module. No provider code difference was necessary. The runtime314 jiter DLL and Python3.12 stdlib _ssl are blocked by Windows Application Control; this is an execution-environment limitation, not a passing clean locked-environment claim.
- ruff check src/astrology_evidence/answers tests/test_provider.py passed.
- Full pytest attempted during concurrent implementation: tests/test_calculations.py missing swisseph, tests/test_config.py missing unfinished config, tests/test_database.py missing alembic in global3.14; coordinator must run combined locked suite.

No live FreeGG request or real user key used. Synthetic offline HTTP transport only. FreeGG retention/privacy/model identity/capability gates remain unverified. HTTPX timeouts bound individual network phases, not the complete150s workflow wall clock: orchestrator must fence late publication and elapsed deadlines. Native structured output, streaming, gateway, automatic retry and fallback are intentionally disabled/unimplemented.
