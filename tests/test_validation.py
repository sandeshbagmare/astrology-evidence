from copy import deepcopy
from hashlib import sha256
from types import SimpleNamespace

import pytest

from astrology_evidence.answers.validation import neutral_answer, validate_answer

TEXT = "A calm practice supports reflection. Exceptions must be considered."
FACT = {"fact_id": "sun-sign", "kind": "sign", "value": "aries", "stability": "stable"}


def passage(text=TEXT):
    return SimpleNamespace(
        id="p1",
        edition_id="e1",
        text=text,
        text_hash=sha256(text.encode()).hexdigest(),
        locators={"verse": "1"},
        max_chars=200,
        generation_id="g1",
    )


def answer():
    p = passage()
    return {
        "status": "partial",
        "concise_summary": "Source evidence is provided; applicability is not established.",
        "computed_facts": [FACT],
        "traditional_claims": [
            {
                "claim_id": "c1",
                "text": TEXT,
                "citation_ids": ["q1"],
                "chart_fact_ids": [],
                "applicability_status": "not_established",
                "scope_note": "Source excerpt; chart applicability is not established.",
            }
        ],
        "interpretation": [],
        "disagreements": [],
        "limitations": [],
        "suggested_questions": [],
        "evidence_manifest": [
            {
                "citation_id": "q1",
                "passage_id": "p1",
                "passage_hash": p.text_hash,
                "quoted_text": TEXT,
                "start": 0,
                "end": len(TEXT),
                "locators": {"verse": "1"},
            }
        ],
    }


def validate(data, ps=None, facts=None):
    return validate_answer(data, ps or [passage()], [FACT] if facts is None else facts)


def test_valid_exact_source_claim():
    assert validate(answer()).traditional_claims[0].text == TEXT


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_passage",
        "bad_hash",
        "bad_quote",
        "bad_offset",
        "bad_locator",
        "duplicate_citation",
        "no_citation",
        "unknown_citation",
        "invented_fact",
        "unknown_fact_ref",
        "reviewed_without_rule",
        "unsupported_claim",
        "free_interpretation",
        "free_summary",
        "free_disagreement",
        "free_limit",
        "free_question",
        "unknown_field",
    ],
)
def test_unsupported_generated_content_fails_closed(mutation):
    data = answer()
    claim = data["traditional_claims"][0]
    citation = data["evidence_manifest"][0]
    if mutation == "unknown_passage":
        citation["passage_id"] = "evil"
    elif mutation == "bad_hash":
        citation["passage_hash"] = "0" * 64
    elif mutation == "bad_quote":
        citation["quoted_text"] = "Different words"
    elif mutation == "bad_offset":
        citation["start"] = 1
    elif mutation == "bad_locator":
        citation["locators"] = {"verse": "999"}
    elif mutation == "duplicate_citation":
        data["evidence_manifest"].append(deepcopy(citation))
    elif mutation == "no_citation":
        claim["citation_ids"] = []
    elif mutation == "unknown_citation":
        claim["citation_ids"] = ["q9"]
    elif mutation == "invented_fact":
        data["computed_facts"][0] = {**FACT, "value": "taurus"}
    elif mutation == "unknown_fact_ref":
        claim["chart_fact_ids"] = ["invented"]
    elif mutation == "reviewed_without_rule":
        claim["applicability_status"] = "reviewed_rule"
    elif mutation == "unsupported_claim":
        claim["text"] = "You will become rich."
    elif mutation == "free_interpretation":
        data["interpretation"] = ["You will become rich."]
    elif mutation == "free_summary":
        data["concise_summary"] = "You will become rich."
    elif mutation == "free_disagreement":
        data["disagreements"] = ["A different source disagrees."]
    elif mutation == "free_limit":
        data["limitations"] = ["Mars causes disease."]
    elif mutation == "free_question":
        data["suggested_questions"] = ["What surgery should I get?"]
    else:
        data["secret"] = "invented"
    with pytest.raises(ValueError):
        validate(data)


def test_exact_unicode_code_point_offsets():
    text = "A 🙂 देवनागरी."
    p = passage(text)
    data = answer()
    data["traditional_claims"][0]["text"] = text
    data["evidence_manifest"][0].update(quoted_text=text, end=len(text), passage_hash=p.text_hash)
    assert validate(data, [p]).evidence_manifest[0].end == len(text)


def test_grapheme_split_is_rejected():
    text = "a\u0301b"
    p = passage(text)
    data = answer()
    data["traditional_claims"][0]["text"] = "a"
    data["evidence_manifest"][0].update(quoted_text="a", end=1, passage_hash=p.text_hash)
    with pytest.raises(ValueError):
        validate(data, [p])


def test_neutral_answer_contains_only_server_facts():
    assert neutral_answer([FACT], "no_evidence").computed_facts == [FACT]


def test_hangul_grapheme_split_is_rejected():
    text = "\u1100\u1161"
    p = passage(text)
    data = answer()
    data["traditional_claims"][0]["text"] = text[0]
    data["evidence_manifest"][0].update(quoted_text=text[0], end=1, passage_hash=p.text_hash)
    with pytest.raises(ValueError):
        validate(data, [p])


@pytest.mark.parametrize(
    "facts,expected",
    [
        ([], "unknown"),
        ([{"fact_id": "s", "kind": "sign", "value": "aries", "stability": "uncertain"}], "unknown"),
        ([{"fact_id": "s", "kind": "sign", "value": "aries", "stability": "stable"}], "true"),
        ([{"fact_id": "s", "kind": "sign", "value": "taurus", "stability": "stable"}], "false"),
    ],
)
def test_reviewed_rule_predicate_is_three_valued(facts, expected):
    from astrology_evidence.answers.rules import ReviewedRule, evaluate

    rule = ReviewedRule(
        rule_id="synthetic",
        reviewer="reviewer",
        version="1",
        tradition="jyotish",
        passage_ids=["p1"],
        conditions=[{"kind": "sign", "equals": "aries"}],
    )
    assert evaluate(rule, facts).truth == expected


def test_rule_cannot_run_code_or_unknown_operations():
    from astrology_evidence.answers.rules import ReviewedRule

    with pytest.raises(ValueError):
        ReviewedRule(
            rule_id="bad",
            reviewer="reviewer",
            version="1",
            tradition="jyotish",
            passage_ids=["p1"],
            conditions=[{"kind": "sign", "equals": "aries", "eval": "danger"}],
        )
