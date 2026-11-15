import copy
import json
import subprocess
import sys

import pytest


def sample():
    return {
        "schema_version": 1,
        "synthetic": True,
        "items": [
            {
                "id": "a",
                "split": "test",
                "expected_evidence_units": {"p1": 3, "p2": 1},
                "ranked_ids": ["p1"],
                "status": "ok",
                "abstained": False,
                "claim_count": 2,
                "supported_claim_count": 1,
            },
            {
                "id": "b",
                "split": "test",
                "expected_evidence_units": {"p3": 2},
                "ranked_ids": [],
                "status": "error",
                "abstained": False,
                "claim_count": 0,
                "supported_claim_count": 0,
            },
            {
                "id": "c",
                "split": "test",
                "expected_evidence_units": {},
                "ranked_ids": [],
                "status": "ok",
                "abstained": True,
                "claim_count": 0,
                "supported_claim_count": 0,
            },
            {
                "id": "d",
                "split": "test",
                "expected_evidence_units": {},
                "ranked_ids": [],
                "status": "error",
                "abstained": True,
                "claim_count": 0,
                "supported_claim_count": 0,
            },
        ],
    }


def test_metrics_exact_denominators_and_errors():
    from astrology_evidence.retrieval.evaluation import evaluate

    report = evaluate(sample(), allow_small_synthetic=True)
    assert report["supported_questions"] == 2
    assert report["recall_at_10"] == 0.25
    assert report["hit_at_10"] == 0.5
    assert report["ndcg_at_10"] == pytest.approx(0.4586597064)
    assert report["claim_support"] == {"numerator": 1, "denominator": 2, "rate": 0.5}
    assert report["abstention"] == {"numerator": 1, "denominator": 2, "rate": 0.5}
    assert report["errors"] == 2
    assert len(report["per_input"]) == 4


def test_empty_metric_denominators_are_null():
    from astrology_evidence.retrieval.evaluation import evaluate

    payload = sample()
    payload["items"] = [payload["items"][2]]
    report = evaluate(payload, allow_small_synthetic=True)
    assert report["recall_at_10"] is None
    assert report["claim_support"]["rate"] is None


@pytest.mark.parametrize(
    "change",
    ["duplicate_question", "duplicate_rank", "bad_grade", "overcount", "empty_id", "boolean_grade"],
)
def test_invalid_evaluations_rejected(change):
    from astrology_evidence.retrieval.evaluation import evaluate

    payload = copy.deepcopy(sample())
    item = payload["items"][0]
    if change == "duplicate_question":
        payload["items"][1]["id"] = "a"
    elif change == "duplicate_rank":
        item["ranked_ids"] = ["p1", "p1"]
    elif change == "bad_grade":
        item["expected_evidence_units"]["p1"] = 4
    elif change == "overcount":
        item["supported_claim_count"] = 3
    elif change == "empty_id":
        item["ranked_ids"] = [""]
    else:
        item["expected_evidence_units"]["p1"] = True
    with pytest.raises(ValueError):
        evaluate(payload, allow_small_synthetic=True)


def test_small_sets_require_explicit_flag_and_synthetic_label():
    from astrology_evidence.retrieval.evaluation import evaluate

    with pytest.raises(ValueError, match="split"):
        evaluate(sample())
    payload = sample()
    payload["synthetic"] = False
    with pytest.raises(ValueError, match="synthetic"):
        evaluate(payload, allow_small_synthetic=True)


def test_cli_outputs_real_json_report(tmp_path):
    source = tmp_path / "eval.json"
    source.write_text(json.dumps(sample()))
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "astrology_evidence.retrieval.evaluation",
            str(source),
            "--allow-small-synthetic",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(run.stdout)["recall_at_10"] == 0.25


def test_rank_eleven_not_counted_and_error_claims_not_supported():
    from astrology_evidence.retrieval.evaluation import evaluate

    payload = sample()
    payload["items"][0]["ranked_ids"] = [f"irrelevant-{i}" for i in range(10)] + ["p1"]
    payload["items"][1]["claim_count"] = 2
    payload["items"][1]["supported_claim_count"] = 2
    report = evaluate(payload, allow_small_synthetic=True)
    assert report["recall_at_10"] == 0
    assert report["ndcg_at_10"] == 0
    assert report["claim_support"] == {"numerator": 1, "denominator": 4, "rate": 0.25}


def test_standard_release_split_counts_and_unsupported_allocation():
    from astrology_evidence.retrieval.evaluation import evaluate

    payload = {"schema_version": 1, "synthetic": True, "items": []}
    for split, count in [("calibration", 20), ("development", 30), ("test", 100)]:
        for index in range(count):
            item = copy.deepcopy(sample()["items"][0 if index < 86 else 2])
            item.update(id=f"{split}-{index}", split=split)
            payload["items"].append(item)
    assert evaluate(payload)["supported_questions"] == 86
    payload["items"][-1]["expected_evidence_units"] = {"p1": 1}
    with pytest.raises(ValueError, match="86 supported"):
        evaluate(payload)
