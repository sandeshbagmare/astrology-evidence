from fastapi.testclient import TestClient

from astrology_evidence.config import Settings
from astrology_evidence.main import create_app


def test_health_and_home(tmp_path):
    app = create_app(
        Settings(database_url=f"sqlite:///{tmp_path}/app.db", app_env="test", _env_file=None)
    )
    with TestClient(app) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 200
        response = client.get("/")
        assert response.status_code == 200
        assert "Evidence" in response.text
        assert response.headers["x-content-type-options"] == "nosniff"
