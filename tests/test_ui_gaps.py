from datetime import timedelta
from html.parser import HTMLParser

from fastapi.testclient import TestClient
from sqlalchemy import select

from astrology_evidence.config import Settings
from astrology_evidence.corpus import CorpusService, EvidencePassage
from astrology_evidence.main import create_app
from astrology_evidence.models import (
    ActiveCorpus,
    Chart,
    CorpusGeneration,
    Passage,
    Reading,
    ReadingRequest,
    utcnow,
)


def client(*, signed_in: bool = False) -> TestClient:
    app = create_app(
        Settings(
            _env_file=None,
            authentication_enabled=True,
            app_env="test",
            database_url="sqlite://",
            dev_login_enabled=True,
            app_public_origin="http://testserver",
        )
    )
    app.state.db.initialize()
    value = TestClient(app)
    if signed_in:
        bootstrap = value.get("/auth/dev/start").json()
        value.post(
            "/auth/dev",
            headers={"Origin": "http://testserver", "X-CSRF-Token": bootstrap["csrf_token"]},
        )
    return value


def api_headers(value: TestClient) -> dict[str, str]:
    return {
        "Origin": "http://testserver",
        "X-CSRF-Token": value.get("/api/me").json()["csrf_token"],
    }


def post_form(value: TestClient, **fields):
    return value.post(
        "/web/action",
        data={"csrf_token": value.cookies["ae_csrf"], **fields},
        headers={"Origin": "http://testserver"},
        follow_redirects=False,
    )


def input_values(html: str) -> dict[str, str]:
    class Inputs(HTMLParser):
        values: dict[str, str] = {}

        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            if tag == "input" and attributes.get("name"):
                self.values[attributes["name"]] = attributes.get("value", "")

    parser = Inputs()
    parser.feed(html)
    return parser.values


def profile_fields(**overrides):
    return {
        "action": "profile",
        "alias": "Synthetic profile",
        "birth_date": "2024-11-03",
        "local_time": "01:30",
        "time_precision": "exact",
        "latitude": "40.7",
        "longitude": "-74.0",
        "timezone": "America/New_York",
        "timezone_history": "confirmed",
        "storage_consent": "true",
        **overrides,
    }


def source_fixture(value: TestClient) -> tuple[str, str, str]:
    from test_corpus import payload

    edition_id = CorpusService(value.app.state.db).import_edition(payload())
    with value.app.state.db.session() as db:
        passage = db.scalar(select(Passage).where(Passage.edition_id == edition_id))
        generation = CorpusGeneration(
            physical_collection_name="ui-test-collection",
            manifest_hash="a" * 64,
            manifest={
                "passage_hashes": {passage.id: passage.text_hash},
                "indexed_ids": [passage.id],
            },
            status="published",
            expected_count=1,
            indexed_count=1,
        )
        db.add(generation)
        db.flush()
        db.add(ActiveCorpus(id=1, generation_id=generation.id))
        return passage.id, generation.id, passage.text_hash


def reading_fixture(value: TestClient, passage_id: str, generation_id: str, text_hash: str):
    response = value.post(
        "/api/profiles",
        json={
            "alias": "Synthetic",
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
        },
        headers=api_headers(value),
    )
    profile = response.json()
    with value.app.state.db.session() as db:
        chart = Chart(
            owner_id=profile["owner_id"],
            profile_revision_id=profile["profile_revision_id"],
            input_hash="b" * 64,
            settings_hash="c" * 64,
            settings={},
            manifest={},
            facts=[],
        )
        db.add(chart)
        db.flush()
        request = ReadingRequest(
            owner_id=profile["owner_id"],
            profile_revision_id=profile["profile_revision_id"],
            question="Synthetic question",
            idempotency_key="ui-test-reading",
            request_hash="d" * 64,
            deadline=utcnow() + timedelta(minutes=1),
            status="succeeded",
        )
        db.add(request)
        db.flush()
        reading = Reading(
            owner_id=profile["owner_id"],
            request_id=request.id,
            chart_id=chart.id,
            answer={
                "concise_summary": "A synthetic answer.",
                "status": "supported",
                "computed_facts": [],
                "traditional_claims": [],
                "interpretation": [],
                "limitations": [],
                "disagreements": [],
                "evidence_manifest": [
                    {
                        "citation_id": "[1]",
                        "quoted_text": "Synthetic qualification fixture",
                        "locators": {"verse": "1"},
                        "passage_id": passage_id,
                    }
                ],
            },
            evidence_manifest={
                "passages": [
                    {"id": passage_id, "generation_id": generation_id, "text_hash": text_hash}
                ]
            },
            versions={},
        )
        db.add(reading)
        db.flush()
        return reading.id


def test_profile_form_exposes_repeated_time_occurrence_choice():
    value = client(signed_in=True)
    response = value.get("/profiles/new")
    assert response.status_code == 200
    assert 'name="fold"' in response.text


def test_time_options_label_both_daylight_saving_offsets():
    value = client(signed_in=True)
    response = value.post(
        "/api/time-options",
        json={
            "birth_date": "2024-11-03",
            "local_time": "01:30",
            "timezone": "America/New_York",
        },
        headers=api_headers(value),
    )
    assert response.status_code == 200
    assert response.json() == {
        "ambiguous": True,
        "candidates": [
            {"fold": 0, "offset": "UTC-04:00", "label": "First occurrence (UTC-04:00)"},
            {"fold": 1, "offset": "UTC-05:00", "label": "Second occurrence (UTC-05:00)"},
        ],
    }


def test_no_js_profile_create_requires_a_fold_for_ambiguous_exact_time():
    value = client(signed_in=True)
    response = post_form(value, **profile_fields())
    assert response.status_code == 422
    assert "occurrence" in response.text.lower()
    assert "First occurrence (UTC-04:00)" in response.text
    assert "Second occurrence (UTC-05:00)" in response.text
    assert input_values(response.text)["alias"] == "Synthetic profile"
    assert input_values(response.text)["birth_date"] == "2024-11-03"
    assert input_values(response.text)["local_time"] == "01:30:00"
    assert input_values(response.text)["time_signature"]
    assert value.get("/api/profiles").json() == []


def test_no_js_profile_create_persists_the_selected_fold():
    value = client(signed_in=True)
    review = post_form(value, **profile_fields())
    signature = input_values(review.text).get("time_signature", "")
    response = post_form(value, **profile_fields(fold="1", time_signature=signature))
    assert response.status_code == 303
    assert value.get("/api/profiles").json()[0]["birth_input"]["fold"] == 1


def test_no_js_profile_edit_persists_the_selected_fold():
    value = client(signed_in=True)
    review = post_form(value, **profile_fields())
    signature = input_values(review.text).get("time_signature", "")
    assert post_form(
        value, **profile_fields(fold="0", time_signature=signature)
    ).status_code == 303
    profile = value.get("/api/profiles").json()[0]
    edited = profile_fields(
        action="profile",
        fold="1",
        profile_id=profile["id"],
        expected_version="1",
        time_signature=signature,
    )
    assert post_form(value, **edited).status_code == 303
    assert value.get("/api/profiles").json()[0]["birth_input"]["fold"] == 1


def test_no_js_generic_occurrence_without_offset_review_cannot_save():
    value = client(signed_in=True)
    result = post_form(value, **profile_fields(fold="1"))
    assert result.status_code == 422
    assert value.get("/api/profiles").json() == []


def test_no_js_changed_repeated_time_invalidates_reviewed_occurrence():
    value = client(signed_in=True)
    review = post_form(value, **profile_fields())
    signature = input_values(review.text).get("time_signature", "")
    result = post_form(
        value,
        **profile_fields(
            birth_date="2023-11-05", fold="1", time_signature=signature
        ),
    )
    assert result.status_code == 422
    assert value.get("/api/profiles").json() == []
    assert input_values(result.text).get("time_signature") != signature
    assert 'value="1" selected' not in result.text


def test_library_search_form_uses_the_existing_search_path():
    value = client(signed_in=True)

    class StubRetriever:
        def search(self, question: str, action: str):
            if question != "moon signs" or action != "display":
                return []
            return [
                EvidencePassage(
                    id="fixture-passage",
                    edition_id="fixture-edition",
                    text="Synthetic search result for moon signs.",
                    title="Synthetic test edition",
                    locators={"chapter": "1"},
                    text_hash="e" * 64,
                    attributed_author="Synthetic author",
                    layer_type="commentary",
                    permission={"display": True},
                    attribution="Synthetic test material",
                    max_chars=100,
                    generation_id="fixture-generation",
                )
            ]

    value.app.state.retriever = StubRetriever()
    response = value.post("/library/search", data={"question": "moon signs"})
    assert response.status_code == 200
    assert "Synthetic search result for moon signs." in response.text
    assert (
        'name="question" required maxlength="2000" rows="3">moon signs</textarea>'
        in response.text
    )


def test_source_detail_page_has_permitted_text_and_a_library_back_link():
    value = client()
    passage_id, _, _ = source_fixture(value)
    response = value.get(f"/library/sources/{passage_id}")
    assert response.status_code == 200
    assert "Synthetic qualification fixture" in response.text
    assert 'href="/library"' in response.text


def test_reading_citation_opens_contextual_source_page():
    value = client(signed_in=True)
    passage_id, generation_id, text_hash = source_fixture(value)
    reading_id = reading_fixture(value, passage_id, generation_id, text_hash)
    page = value.get(f"/readings/{reading_id}")
    assert page.status_code == 200
    assert f'href="/library/sources/{passage_id}?reading_id={reading_id}"' in page.text
    source = value.get(f"/library/sources/{passage_id}?reading_id={reading_id}")
    assert source.status_code == 200
    assert f'href="/readings/{reading_id}"' in source.text


def test_saved_reading_delete_requires_confirmation_and_preserves_reading():
    value = client(signed_in=True)
    passage_id, generation_id, text_hash = source_fixture(value)
    reading_id = reading_fixture(value, passage_id, generation_id, text_hash)
    page = value.get(f"/readings/{reading_id}")
    assert 'name="confirm_delete"' in page.text
    result = post_form(value, action="delete_reading", reading_id=reading_id)
    assert result.status_code == 422
    assert value.get(f"/readings/{reading_id}").status_code == 200
    confirmed = post_form(
        value, action="delete_reading", reading_id=reading_id, confirm_delete="DELETE"
    )
    assert confirmed.status_code == 303
    assert value.get(f"/readings/{reading_id}").status_code == 404


def test_profile_delete_requires_confirmation_before_revoking_linked_data():
    value = client(signed_in=True)
    passage_id, generation_id, text_hash = source_fixture(value)
    reading_id = reading_fixture(value, passage_id, generation_id, text_hash)
    profile = value.get("/api/profiles").json()[0]
    chart_id = value.get(f"/api/readings/{reading_id}").json()["chart_id"]
    resources = [
        f"/api/profiles/{profile['id']}",
        f"/api/charts/{chart_id}",
        f"/api/readings/{reading_id}",
    ]
    assert [value.get(path).status_code for path in resources] == [200, 200, 200]

    for confirmation in ({}, {"confirm_delete": ""}, {"confirm_delete": "delete"}):
        rejected = post_form(
            value, action="delete_profile", profile_id=profile["id"], **confirmation
        )
        assert rejected.status_code == 422
        assert [value.get(path).status_code for path in resources] == [200, 200, 200]

    page = value.get(f"/profiles/{profile['id']}/edit")
    assert 'name="confirm_delete"' in page.text
    confirmed = post_form(
        value, action="delete_profile", profile_id=profile["id"], confirm_delete="DELETE"
    )
    assert confirmed.status_code == 303
    assert [value.get(path).status_code for path in resources] == [404, 404, 404]
