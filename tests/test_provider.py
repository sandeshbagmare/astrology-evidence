import json

import httpx
import pytest

from astrology_evidence.answers.contracts import GenerationRequest, ProviderError
from astrology_evidence.answers.provider import ResponsesProvider, normalize_text


def response_body(output=None, **updates):
    body = {
        "id": "resp_synthetic",
        "object": "response",
        "created_at": 1,
        "model": "gpt-6.1-sol",
        "status": "completed",
        "error": None,
        "incomplete_details": None,
        "instructions": None,
        "max_output_tokens": 1800,
        "metadata": {},
        "parallel_tool_calls": False,
        "temperature": 1,
        "tool_choice": "auto",
        "tools": [],
        "top_p": 1,
        "store": False,
        "output": output
        if output is not None
        else [
            {
                "id": "msg_synthetic",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": "Supported text", "annotations": []}],
            }
        ],
        "usage": {
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens_details": {"reasoning_tokens": 0},
        },
    }
    return body | updates


def run_provider(body=None, status=200, request=None):
    calls = []

    def handle(req):
        calls.append(req)
        return httpx.Response(status, json=body if body is not None else response_body())

    provider = ResponsesProvider("synthetic-credential", transport=httpx.MockTransport(handle))
    return provider, calls, request or GenerationRequest(prompt="Synthetic facts only")


def test_real_langchain_uses_exact_responses_route_and_privacy_controls():
    provider, calls, request = run_provider()
    result = provider.generate(request)
    assert result.content == "Supported text"
    assert result.usage == {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
    assert len(calls) == 1
    assert str(calls[0].url) == "https://freegg.app/v1/responses"
    assert calls[0].method == "POST"
    assert calls[0].headers["authorization"] == "Bearer synthetic-credential"
    body = json.loads(calls[0].content)
    assert body["store"] is False
    assert body["model"] == "gpt-6.1-sol"
    assert body["max_output_tokens"] == 1800
    assert "tools" not in body
    assert "max_tokens" not in body
    assert body.get("stream", False) is False
    assert calls[0].extensions["timeout"]["read"] == 120


@pytest.mark.parametrize(
    "status,code,unknown",
    [
        (400, "provider_unsupported_configuration", False),
        (401, "provider_authentication", False),
        (403, "provider_authentication", False),
        (404, "provider_incompatible_endpoint", False),
        (410, "provider_incompatible_endpoint", False),
        (408, "provider_unknown", True),
        (429, "provider_rate_limited", False),
        (500, "provider_unavailable", False),
        (503, "provider_unavailable", False),
    ],
)
def test_http_errors_are_safe_and_never_retried(status, code, unknown):
    provider, calls, request = run_provider(
        {"error": {"message": "synthetic-credential private body", "type": "error"}}, status
    )
    with pytest.raises(ProviderError) as exc:
        provider.generate(request)
    assert exc.value.code == code
    assert exc.value.unknown is unknown
    assert "synthetic-credential" not in str(exc.value)
    assert "private body" not in str(exc.value)
    assert exc.value.__cause__ is None
    assert len(calls) == 1


@pytest.mark.parametrize("error", [httpx.ReadTimeout, httpx.ConnectError])
def test_transport_loss_is_unknown_without_resend(error):
    calls = []

    def handle(request):
        calls.append(request)
        raise error("private body", request=request)

    provider = ResponsesProvider("synthetic", transport=httpx.MockTransport(handle))
    with pytest.raises(ProviderError) as exc:
        provider.generate(GenerationRequest(prompt="Synthetic"))
    assert exc.value.unknown is True
    assert len(calls) == 1
    assert str(exc.value) == "provider_unknown"


@pytest.mark.parametrize(
    "url",
    [
        "https://freegg.app/v1/responses",
        "https://freegg.app/v1/v1",
        "https://freegg.app/v1?x=y",
        "https://evil.example/v1",
        "http://freegg.app/v1",
        "https://user:password@freegg.app/v1",
    ],
)
def test_invalid_provider_destinations_rejected_before_send(url):
    with pytest.raises(ProviderError, match="provider_configuration"):
        ResponsesProvider("synthetic", base_url=url)


def test_remaining_deadline_reduces_timeout():
    provider, calls, request = run_provider(request=GenerationRequest("Synthetic", 2.5))
    provider.generate(request)
    assert calls[0].extensions["timeout"]["read"] == 2.5


def test_expired_deadline_does_not_send():
    provider, calls, _ = run_provider()
    with pytest.raises(ProviderError, match="deadline_exceeded"):
        provider.generate(GenerationRequest("Synthetic", 0))
    assert calls == []


@pytest.mark.parametrize("updates", [{"status": "incomplete"}, {"status": "failed"}])
def test_incomplete_response_cannot_publish(updates):
    provider, _, request = run_provider(response_body(**updates))
    with pytest.raises(ProviderError, match="provider_invalid_output"):
        provider.generate(request)


@pytest.mark.parametrize(
    "item",
    [
        {
            "id": "tool1",
            "type": "function_call",
            "call_id": "c1",
            "name": "tool",
            "arguments": "{}",
        },
        {"id": "unknown1", "type": "future_unknown", "text": "hidden"},
    ],
)
def test_unexpected_tool_or_unknown_item_fails_closed(item):
    body = response_body()
    body["output"].append(item)
    provider, _, request = run_provider(body)
    with pytest.raises(ProviderError, match="provider_invalid_output"):
        provider.generate(request)


def test_reasoning_is_not_answer_text():
    body = response_body()
    body["output"].insert(
        0,
        {
            "id": "rs1",
            "type": "reasoning",
            "summary": [{"type": "summary_text", "text": "private reasoning"}],
        },
    )
    provider, _, request = run_provider(body)
    assert provider.generate(request).content == "Supported text"


def test_refusal_has_distinct_failure():
    body = response_body()
    body["output"][0]["content"] = [{"type": "refusal", "refusal": "Private refusal"}]
    provider, _, request = run_provider(body)
    with pytest.raises(ProviderError, match="provider_refused"):
        provider.generate(request)


def test_missing_usage_remains_unknown():
    provider, _, request = run_provider(response_body(usage=None))
    assert provider.generate(request).usage is None


@pytest.mark.parametrize(
    "value,expected",
    [
        (" plain ", " plain "),
        ([{"type": "text", "text": "First"}, {"type": "text", "text": "Second"}], "First\nSecond"),
    ],
)
def test_text_normalization(value, expected):
    assert normalize_text(value) == expected


@pytest.mark.parametrize("value", ["", "   ", [], [{"type": "future", "text": "bad"}]])
def test_empty_or_unknown_text_blocks_rejected(value):
    with pytest.raises(ProviderError, match="provider_invalid_output"):
        normalize_text(value)


@pytest.mark.parametrize("mutation", ["incomplete_message", "unknown_block", "wrong_role"])
def test_malformed_message_is_not_published(mutation):
    body = response_body()
    message = body["output"][0]
    if mutation == "incomplete_message":
        message["status"] = "in_progress"
    elif mutation == "wrong_role":
        message["role"] = "user"
    else:
        message["content"].append({"type": "unknown", "text": "Do not show"})
    provider, _, request = run_provider(body)
    with pytest.raises(ProviderError, match="provider_invalid_output"):
        provider.generate(request)


def test_redirect_does_not_send_secret_to_another_host():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(307, headers={"location": "https://evil.example/v1/responses"})

    provider = ResponsesProvider("synthetic", transport=httpx.MockTransport(handle))
    with pytest.raises(ProviderError):
        provider.generate(GenerationRequest("Synthetic"))
    assert len(calls) == 1
    assert calls[0].url.host == "freegg.app"


@pytest.mark.parametrize("tokens", [0, -1, 1801, True])
def test_invalid_token_budget_does_not_send(tokens):
    provider, calls, _ = run_provider()
    with pytest.raises(ProviderError, match="provider_configuration"):
        provider.generate(GenerationRequest("Synthetic", max_output_tokens=tokens))
    assert calls == []


def test_provider_disables_external_prompt_tracing():
    from langsmith.run_helpers import get_tracing_context

    observed = []

    def handle(request):
        observed.append(get_tracing_context()["enabled"])
        return httpx.Response(200, json=response_body())

    provider = ResponsesProvider("synthetic", transport=httpx.MockTransport(handle))
    provider.generate(GenerationRequest("Synthetic"))
    assert observed == [False]
