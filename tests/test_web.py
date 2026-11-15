from fastapi.testclient import TestClient

from astrology_evidence.config import Settings
from astrology_evidence.main import create_app


def client():
    app = create_app(
        Settings(
            _env_file=None,
            app_env="test",
            database_url="sqlite://",
            dev_login_enabled=True,
            app_public_origin="http://testserver",
        )
    )
    app.state.db.initialize()
    return TestClient(app)


def test_public_home_and_login_are_server_rendered():
    c = client()
    assert c.get("/").status_code == 200
    assert "Synthetic example" in c.get("/").text
    assert c.get("/login").status_code == 200
    assert "Continue with Google" in c.get("/login").text


def test_private_page_redirects_to_login():
    response = client().get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_dev_login_page_exposes_state_without_leaking_markup():
    c = client()
    response = c.get("/login")
    assert response.status_code == 200
    assert 'value="dev_login"' in response.text
    assert 'src="/static/app.js"' in response.text


def test_template_escapes_untrusted_profile_alias():
    c = client()
    bootstrap = c.get("/auth/dev/start").json()
    c.post(
        "/auth/dev",
        headers={"Origin": "http://testserver", "X-CSRF-Token": bootstrap["csrf_token"]},
    )
    csrf = c.get("/api/me").json()["csrf_token"]
    payload = {
        "alias": "<script>alert(1)</script>",
        "birth_input": {
            "birth_date": "2000-01-01",
            "local_time": "12:00",
            "time_precision": "exact",
            "latitude": 28.6,
            "longitude": 77.2,
            "timezone": "Asia/Kolkata",
            "timezone_history": "confirmed",
        },
        "storage_consent": True,
        "notice_version": "privacy-1",
    }
    c.post(
        "/api/profiles", json=payload, headers={"Origin": "http://testserver", "X-CSRF-Token": csrf}
    )
    page = c.get("/dashboard")
    assert page.status_code == 200
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page.text
    assert "<script>alert(1)</script>" not in page.text


def signed_client():
    c = client()
    bootstrap = c.get("/auth/dev/start").json()
    c.post(
        "/auth/dev",
        headers={"Origin": "http://testserver", "X-CSRF-Token": bootstrap["csrf_token"]},
    )
    return c


def post_form(c, **data):
    return c.post(
        "/web/action",
        data={"csrf_token": c.cookies.get("ae_csrf", ""), **data},
        headers={"Origin": "http://testserver"},
        follow_redirects=False,
    )


def profile_form():
    return dict(
        action="profile",
        alias="No JS profile",
        birth_date="2000-01-01",
        local_time="12:00",
        time_precision="exact",
        latitude="28.6",
        longitude="77.2",
        timezone="Asia/Kolkata",
        timezone_history="confirmed",
        storage_consent="true",
    )


def test_nojs_profile_create_and_update():
    c = signed_client()
    assert post_form(c, **profile_form()).status_code == 303
    profile = c.get("/api/profiles").json()[0]
    data = profile_form() | {
        "profile_id": profile["id"],
        "expected_version": "1",
        "alias": "Updated",
    }
    assert post_form(c, **data).status_code == 303
    assert c.get("/api/profiles").json()[0]["version"] == 2


def test_nojs_profile_rejects_cross_site_origin():
    c = signed_client()
    result = c.post(
        "/web/action",
        data={**profile_form(), "csrf_token": c.cookies["ae_csrf"]},
        headers={"Origin": "https://evil.example"},
    )
    assert result.status_code == 403
    assert c.get("/api/profiles").json() == []


def test_nojs_profile_requires_csrf():
    c = signed_client()
    result = c.post("/web/action", data=profile_form(), headers={"Origin": "http://testserver"})
    assert result.status_code == 403


def test_nojs_unknown_time_drops_unused_clock_input():
    c = signed_client()
    assert post_form(c, **(profile_form() | {"time_precision": "unknown"})).status_code == 303
    assert c.get("/api/profiles").json()[0]["birth_input"]["local_time"] is None


def test_nojs_invalid_input_preserves_escaped_value():
    c = signed_client()
    result = post_form(
        c, **(profile_form() | {"latitude": "invalid", "alias": "<script>bad()</script>"})
    )
    assert result.status_code == 422
    assert "&lt;script&gt;bad()&lt;/script&gt;" in result.text


def test_nojs_logout_revokes_session():
    c = signed_client()
    assert post_form(c, action="logout").status_code == 303
    assert c.get("/api/me").status_code == 401


def test_nojs_export_returns_real_job_status_link():
    c = signed_client()
    result = post_form(c, action="export")
    assert result.status_code == 200
    assert "Refresh export status" in result.text


def test_nojs_admin_import_requires_curator():
    import json

    from test_corpus import payload

    c = signed_client()
    assert post_form(c, action="import", metadata=json.dumps(payload())).status_code == 403


def test_library_hides_unpublished_and_withdrawn_passages():
    from sqlalchemy import select
    from test_corpus import payload

    from astrology_evidence.corpus import CorpusService
    from astrology_evidence.models import ActiveCorpus, CorpusGeneration, Passage

    c = client()
    db = c.app.state.db
    edition = CorpusService(db).import_edition(payload())
    assert "Synthetic qualification fixture" not in c.get("/library").text
    with db.session() as session:
        passage = session.scalar(select(Passage))
        generation = CorpusGeneration(
            physical_collection_name="web-test",
            manifest_hash="a" * 64,
            manifest={"passage_hashes": {passage.id: passage.text_hash}},
            status="published",
        )
        session.add(generation)
        session.flush()
        session.add(ActiveCorpus(id=1, generation_id=generation.id))
    assert "Synthetic qualification fixture" in c.get("/library").text
    CorpusService(db).withdraw(edition)
    assert "Synthetic qualification fixture" not in c.get("/library").text


def test_reading_html_honors_withdrawn_evidence():
    from datetime import timedelta

    from astrology_evidence.models import Chart, Reading, ReadingRequest, utcnow

    c = signed_client()
    post_form(c, **profile_form())
    p = c.get("/api/profiles").json()[0]
    with c.app.state.db.session() as db:
        chart = Chart(
            owner_id=p["owner_id"],
            profile_revision_id=p["profile_revision_id"],
            input_hash="a" * 64,
            settings_hash="b" * 64,
            settings={},
            manifest={},
            facts=[],
        )
        db.add(chart)
        db.flush()
        req = ReadingRequest(
            owner_id=p["owner_id"],
            profile_revision_id=p["profile_revision_id"],
            question="fixture",
            idempotency_key="fixture",
            request_hash="a" * 64,
            deadline=utcnow() + timedelta(minutes=1),
            status="succeeded",
        )
        db.add(req)
        db.flush()
        reading = Reading(
            owner_id=p["owner_id"],
            request_id=req.id,
            chart_id=chart.id,
            answer={"concise_summary": "MUST NOT LEAK"},
            evidence_manifest={
                "passages": [{"id": "withdrawn", "generation_id": "old", "text_hash": "a" * 64}]
            },
            versions={},
        )
        db.add(reading)
        db.flush()
        identifier = reading.id
    response = c.get("/readings/" + identifier)
    assert response.status_code == 410
    assert "MUST NOT LEAK" not in response.text


def test_fact_table_names_rounding_and_escaping():
    from astrology_evidence.web import templates

    template = templates.env.from_string(
        "{% from 'facts.html' import fact_table %}{{ fact_table(facts) }}"
    )
    html = template.render(
        facts=[
            {"body": "sun", "kind": "sign", "value": 1, "unit": "index", "fact_id": "secret-id"},
            {"body": "moon", "kind": "nakshatra", "value": 27, "unit": "index"},
            {
                "body": "<script>bad()</script>",
                "kind": "longitude",
                "value": 1.123456789,
                "unit": "degrees",
            },
        ]
    )
    assert "Aries" in html
    assert "Revati" in html
    assert "1.123457" in html
    assert "secret-id" not in html
    assert "&lt;script&gt;" in html.lower()
    assert "<script>" not in html.lower()


def test_house_diagram_withholds_unknown_houses():
    from astrology_evidence.web import templates

    template = templates.env.from_string(
        "{% from 'facts.html' import house_diagram %}{{ house_diagram(facts) }}"
    )
    assert "<svg" not in template.render(facts=[])
    html = template.render(facts=[{"body": "sun", "kind": "house", "value": 3}])
    assert 'role="img"' in html
    assert "House 3: Sun" in html
    assert html.count('class="house-cell"') == 12
