"""Responses-only, nonstreaming boundary with no retries or fallback."""

import math
from typing import Any

import httpx
from langchain_openai import ChatOpenAI
from langsmith import tracing_context
from openai import APIConnectionError, APIStatusError, APITimeoutError
from pydantic import SecretStr

from astrology_evidence.answers.contracts import GenerationRequest, GenerationResult, ProviderError

BASE_URL = "https://freegg.app/v1"
MODEL = "gpt-6.1-sol"


def normalize_text(value: Any) -> str:
    """Select text explicitly; unknown blocks cannot silently become an answer."""
    if isinstance(value, str):
        if value.strip():
            return value
        raise ProviderError("provider_invalid_output")
    if not isinstance(value, list):
        raise ProviderError("provider_invalid_output")
    parts = []
    for block in value:
        if not isinstance(block, dict):
            raise ProviderError("provider_invalid_output")
        kind = block.get("type")
        if kind == "refusal":
            raise ProviderError("provider_refused")
        if kind not in {"text", "output_text"} or not isinstance(block.get("text"), str):
            raise ProviderError("provider_invalid_output")
        parts.append(block["text"])
    return normalize_text("\n".join(parts))


def _validate_response(body: Any) -> GenerationResult:
    if not isinstance(body, dict) or body.get("status") != "completed" or body.get("error"):
        raise ProviderError("provider_invalid_output")
    output = body.get("output")
    if not isinstance(output, list):
        raise ProviderError("provider_invalid_output")
    texts = []
    for item in output:
        if not isinstance(item, dict):
            raise ProviderError("provider_invalid_output")
        if item.get("type") == "reasoning":
            continue
        if (
            item.get("type") != "message"
            or item.get("role") != "assistant"
            or item.get("status") != "completed"
        ):
            raise ProviderError("provider_invalid_output")
        texts.append(normalize_text(item.get("content")))
    content = normalize_text("\n".join(texts))
    usage = body.get("usage")
    counts = None
    if isinstance(usage, dict):
        keys = ("input_tokens", "output_tokens", "total_tokens")
        if all(type(usage.get(key)) is int and usage[key] >= 0 for key in keys):
            counts = {key: usage[key] for key in keys}
    return GenerationResult(content=content, usage=counts)


class ResponsesProvider:
    """Own the HTTP client per call; transport injection permits offline contract tests."""

    def __init__(
        self,
        api_key: str | SecretStr,
        *,
        base_url: str = BASE_URL,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        secret = api_key.get_secret_value() if isinstance(api_key, SecretStr) else api_key
        if base_url != BASE_URL or not secret or not secret.strip():
            raise ProviderError("provider_configuration")
        self._api_key = SecretStr(secret)
        self._transport = transport

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not math.isfinite(request.timeout_seconds) or request.timeout_seconds <= 0:
            raise ProviderError("deadline_exceeded")
        if (
            not request.prompt.strip()
            or type(request.max_output_tokens) is not int
            or not 1 <= request.max_output_tokens <= 1800
        ):
            raise ProviderError("provider_configuration")
        captured: list[Any] = []

        def capture(response: httpx.Response) -> None:
            if response.is_success:
                response.read()
                try:
                    captured.append(response.json())
                except ValueError:
                    captured.append(None)

        failure = None
        with httpx.Client(
            transport=self._transport, follow_redirects=False, event_hooks={"response": [capture]}
        ) as client:
            try:
                model = ChatOpenAI(
                    api_key=self._api_key,
                    base_url=BASE_URL,
                    model=MODEL,
                    use_responses_api=True,
                    max_retries=0,
                    timeout=min(120, request.timeout_seconds),
                    http_client=client,
                    max_tokens=request.max_output_tokens,
                    store=False,
                )
                with tracing_context(enabled=False):
                    model.invoke(request.prompt)
            except APIStatusError as exc:
                code = {
                    400: "provider_unsupported_configuration",
                    401: "provider_authentication",
                    403: "provider_authentication",
                    404: "provider_incompatible_endpoint",
                    410: "provider_incompatible_endpoint",
                    408: "provider_unknown",
                    429: "provider_rate_limited",
                    422: "provider_unsupported_configuration",
                }.get(exc.status_code, "provider_unavailable")
                failure = ProviderError(code, unknown=exc.status_code == 408)
            except (APITimeoutError, APIConnectionError):
                failure = ProviderError("provider_unknown", unknown=True)
            except Exception:
                failure = ProviderError("provider_invalid_output")
        if captured:
            # The SDK can drop unknown items; validate original wire data before publishing.
            result = _validate_response(captured[0])
            if failure is None:
                return result
        if failure is not None:
            raise failure from None
        raise ProviderError("provider_invalid_output")
