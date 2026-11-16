from fastapi.testclient import TestClient

from astrology_evidence.config import Settings
from astrology_evidence.main import create_app


def test_corpus_endpoints_require_authentication(tmp_path):
    app = create_app(
        Settings(
            database_url=f"sqlite:///{tmp_path}/db",
            app_env="test",
            authentication_enabled=True,
            _env_file=None,
        )
    )
    with TestClient(app) as client:
        assert client.get("/api/sources/missing").status_code == 401
        assert client.post("/api/search", json={"question": "source?"}).status_code == 401


def test_runtime_wires_reading_and_corpus_routes(tmp_path):
    app = create_app(
        Settings(database_url=f"sqlite:///{tmp_path}/db", app_env="test", _env_file=None)
    )
    paths = set(app.openapi()["paths"])
    assert "/api/readings" in paths
    assert "/api/admin/editions" in paths
