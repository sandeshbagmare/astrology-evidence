"""Independent review regressions: profile-bound charts and interrupted requests."""

from datetime import timedelta
from types import SimpleNamespace

from sqlalchemy import select
from test_profiles import client as client
from test_profiles import create as create_profile
from test_profiles import headers
from test_readings import create as create_reading
from test_readings import env as env

from astrology_evidence.models import Profile, ReadingRequest, utcnow


def test_identical_birth_data_keeps_chart_bound_to_requested_revision(client):
    client.app.state.calculator = lambda birth, settings: SimpleNamespace(
        model_dump=lambda **kwargs: {
            "manifest": {"input_hash": "a" * 64, "settings_hash": "b" * 64},
            "settings": {},
            "facts": [],
            "unavailable_facts": [],
        }
    )
    first = create_profile(client, alias="First").json()
    second = create_profile(client, alias="Second").json()
    for profile in (first, second):
        response = client.post(
            "/api/charts",
            json={"profile_revision_id": profile["profile_revision_id"]},
            headers=headers(client),
        )
        assert response.status_code == 201
        assert response.json()["profile_revision_id"] == profile["profile_revision_id"]


def test_deleted_profile_chart_cannot_be_returned_for_new_profile(client):
    client.app.state.calculator = lambda birth, settings: SimpleNamespace(
        model_dump=lambda **kwargs: {
            "manifest": {"input_hash": "a" * 64, "settings_hash": "b" * 64},
            "settings": {},
            "facts": [],
            "unavailable_facts": [],
        }
    )
    first = create_profile(client).json()
    client.post(
        "/api/charts",
        json={"profile_revision_id": first["profile_revision_id"]},
        headers=headers(client),
    )
    with client.app.state.db.session() as session:
        session.get(Profile, first["id"]).deleted_at = utcnow()
    second = create_profile(client).json()
    response = client.post(
        "/api/charts",
        json={"profile_revision_id": second["profile_revision_id"]},
        headers=headers(client),
    )
    assert response.status_code == 201
    assert client.get("/api/charts/" + response.json()["id"]).status_code == 200


def test_idempotency_replay_recovers_expired_interrupted_request(env):
    create_reading(env)
    with env.db.session() as session:
        row = session.scalar(select(ReadingRequest))
        row.status = "generating"
        row.execution_token = "abandoned-token"
        row.deadline = utcnow() - timedelta(seconds=1)
    env.provider.calls.clear()
    replay = create_reading(env)
    assert replay["status"] == "unknown"
    assert replay["failure_code"] == "deadline_exceeded"
    assert env.provider.calls == []


def test_extractive_claim_cannot_drop_source_negation():
    import pytest
    from test_validation import answer, passage

    from astrology_evidence.answers.validation import validate_answer

    source = passage("The source rejects the claim that calm practice guarantees success.")
    excerpt = "calm practice guarantees success"
    data = answer()
    data["computed_facts"] = []
    data["traditional_claims"][0]["text"] = excerpt
    citation = data["evidence_manifest"][0]
    citation.update(
        passage_hash=source.text_hash,
        quoted_text=excerpt,
        start=source.text.index(excerpt),
        end=source.text.index(excerpt) + len(excerpt),
    )
    with pytest.raises(ValueError):
        validate_answer(data, [source], [])
