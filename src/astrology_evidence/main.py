"""FastAPI composition; capabilities are configured explicitly at startup."""

from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from astrology_evidence.answers.provider import ResponsesProvider
from astrology_evidence.answers.routes import router as answers_router
from astrology_evidence.calculations.adapter import calculator
from astrology_evidence.config import Settings
from astrology_evidence.corpus.routes import router as corpus_router
from astrology_evidence.db import create_db
from astrology_evidence.identity import router as identity_router
from astrology_evidence.privacy import router as privacy_router
from astrology_evidence.profiles import router as profiles_router
from astrology_evidence.web import router as web_router
from astrology_evidence.web.app import STATIC_DIR


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    if settings.database_url.startswith("sqlite:///"):
        database_path = settings.database_url.removeprefix("sqlite:///")
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    database = create_db(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.app_env != "production":
            database.initialize()
        yield
        if getattr(app.state, "index", None) is not None:
            app.state.index.client.close()
        database.engine.dispose()

    app = FastAPI(title="Astrology Evidence", lifespan=lifespan)
    app.state.settings = settings
    app.state.db = database
    app.state.retriever = None
    app.state.provider = None
    app.state.calculator = calculator(settings)
    if settings.ai_enabled:
        assert settings.openai_api_key is not None
        app.state.provider = ResponsesProvider(settings.openai_api_key)
    if settings.embedding_enabled:
        assert settings.embedding_revision is not None
        from qdrant_client import QdrantClient

        from astrology_evidence.retrieval import E5Encoder, QdrantIndex, RetrievalService

        client = (
            QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key.get_secret_value()
                if settings.qdrant_api_key
                else None,
            )
            if settings.qdrant_url
            else QdrantClient(path=settings.qdrant_path)
        )
        app.state.index = QdrantIndex(client)
        app.state.encoder = E5Encoder(settings.embedding_revision)
        app.state.retriever = RetrievalService(database, app.state.index, app.state.encoder)
    app.include_router(identity_router)
    app.include_router(answers_router)
    app.include_router(corpus_router)
    app.include_router(profiles_router)
    app.include_router(privacy_router)
    app.include_router(web_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.middleware("http")
    async def security_headers(request, call_next):
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        response.headers["Cache-Control"] = "no-store"
        if settings.secure_cookies:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.get("/health/live")
    def live():
        return {"status": "alive"}

    @app.get("/health/ready")
    def ready():
        try:
            with database.session() as session:
                session.execute(text("SELECT 1"))
        except Exception:
            return JSONResponse({"status": "unavailable"}, status_code=503)
        return {"status": "ready"}

    return app
