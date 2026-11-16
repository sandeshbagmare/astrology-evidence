import asyncio

import pytest
from fastapi.testclient import TestClient

from astrology_evidence.config import Settings
from astrology_evidence.main import (
    MAX_EDITION_IMPORT_BYTES,
    RequestBodyLimitMiddleware,
    create_app,
)


class CaptureApp:
    def __init__(self):
        self.called = False
        self.body = b""

    async def __call__(self, scope, receive, send):
        self.called = True
        chunks = []
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                break
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        self.body = b"".join(chunks)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


def request_scope(path="/api/admin/editions", method="POST", headers=()):
    return {"type": "http", "asgi": {"version": "3.0"}, "method": method, "path": path,
            "query_string": b"", "headers": list(headers), "server": ("test", 80),
            "client": ("test", 1234), "scheme": "http", "http_version": "1.1"}


def run_asgi(app, scope, messages):
    sent = []
    iterator = iter(messages)

    async def receive():
        return next(iterator)

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    return sent


def test_edition_import_rejects_declared_oversize_before_fastapi_parsing(tmp_path):
    app = create_app(
        Settings(database_url=f"sqlite:///{tmp_path}/db", app_env="test", _env_file=None)
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/editions",
            content=b"not-json",
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(MAX_EDITION_IMPORT_BYTES + 1),
            },
        )
    assert response.status_code == 413


def test_chunked_oversize_body_is_rejected_before_downstream_parsing():
    downstream = CaptureApp()
    app = RequestBodyLimitMiddleware(downstream, max_bytes=10)
    sent = run_asgi(
        app,
        request_scope(headers=[(b"content-type", b"application/json")]),
        [
            {"type": "http.request", "body": b"123456", "more_body": True},
            {"type": "http.request", "body": b"78901", "more_body": True},
        ],
    )
    assert sent[0]["status"] == 413
    assert not downstream.called


def test_form_action_rejects_declared_oversize_before_form_parsing(tmp_path):
    app = create_app(
        Settings(database_url=f"sqlite:///{tmp_path}/db", app_env="test", _env_file=None)
    )
    with TestClient(app) as client:
        response = client.post(
            "/web/action",
            content=b"action=import&edition=not-json",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Content-Length": str(MAX_EDITION_IMPORT_BYTES + 1),
            },
        )
    assert response.status_code == 413


@pytest.mark.parametrize("declared_length", [None, b"1"])
def test_form_action_rejects_streamed_oversize_before_downstream_parsing(declared_length):
    downstream = CaptureApp()
    headers = [(b"content-type", b"application/x-www-form-urlencoded")]
    if declared_length is not None:
        headers.append((b"content-length", declared_length))
    sent = run_asgi(
        RequestBodyLimitMiddleware(downstream, max_bytes=10),
        request_scope(path="/web/action", headers=headers),
        [
            {"type": "http.request", "body": b"action=import", "more_body": True},
            {"type": "http.request", "body": b"&edition={}", "more_body": False},
        ],
    )
    assert sent[0]["status"] == 413
    assert not downstream.called


def test_under_limit_and_unprotected_routes_are_forwarded():
    for scope, chunks in (
        (
            request_scope(headers=[(b"content-type", b"application/json")]),
            [
                {"type": "http.request", "body": b"1234", "more_body": True},
                {"type": "http.request", "body": b"5678", "more_body": False},
            ],
        ),
        (
            request_scope(path="/health/live", headers=[(b"content-length", b"999")]),
            [{"type": "http.request", "body": b"unlimited", "more_body": False}],
        ),
    ):
        downstream = CaptureApp()
        sent = run_asgi(RequestBodyLimitMiddleware(downstream, max_bytes=10), scope, chunks)
        assert sent[0]["status"] == 200
        assert downstream.called
