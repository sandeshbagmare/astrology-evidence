"""Conservative extractive answers: source matching is not semantic entailment."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Literal

import regex
from pydantic import BaseModel, ConfigDict, Field

SUMMARY = "Source evidence is provided; applicability is not established."
SCOPE = "Source excerpt; chart applicability is not established."
LIMITATIONS = {
    "No rights-approved passages matched the question.",
    "AI generation is disabled.",
    "Traditional interpretations are not scientific predictions.",
    "Chart applicability has not been established.",
    "Birth-time uncertainty limits available chart facts.",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Citation(StrictModel):
    citation_id: str = Field(min_length=1, max_length=80)
    passage_id: str = Field(min_length=1, max_length=80)
    passage_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    quoted_text: str = Field(min_length=1, max_length=20000)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    locators: dict[str, Any]


class TraditionalClaim(StrictModel):
    claim_id: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=20000)
    citation_ids: list[str] = Field(min_length=1, max_length=8)
    chart_fact_ids: list[str] = Field(default_factory=list, max_length=100)
    applicability_status: Literal["reviewed_rule", "model_inference", "not_established"]
    scope_note: str


class ReadingAnswer(StrictModel):
    status: Literal["supported", "partial", "insufficient_evidence"]
    concise_summary: str = Field(min_length=1, max_length=1000)
    computed_facts: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    traditional_claims: list[TraditionalClaim] = Field(default_factory=list, max_length=8)
    interpretation: list[str] = Field(default_factory=list, max_length=8)
    disagreements: list[str] = Field(default_factory=list, max_length=8)
    limitations: list[str] = Field(default_factory=list, max_length=8)
    suggested_questions: list[str] = Field(default_factory=list, max_length=8)
    evidence_manifest: list[Citation] = Field(default_factory=list, max_length=8)


def neutral_answer(facts: list[dict], reason: str) -> ReadingAnswer:
    disabled = reason == "ai_disabled"
    return ReadingAnswer(
        status="insufficient_evidence",
        concise_summary=(
            "Reviewed evidence is available, but AI generation is unavailable."
            if disabled
            else "There is not enough reviewed evidence to answer this question."
        ),
        computed_facts=facts,
        limitations=[
            "AI generation is disabled."
            if disabled
            else "No rights-approved passages matched the question."
        ],
    )


def _boundary(text: str, offset: int) -> bool:
    return offset == 0 or any(match.end() == offset for match in regex.finditer(r"\X", text))


def _same_json(left: Any, right: Any) -> bool:
    # Python equality conflates booleans and numbers, including inside containers.
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _same_json(value, right[key]) for key, value in left.items()
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _same_json(a, b) for a, b in zip(left, right, strict=True)
        )
    return bool(left == right)


def validate_answer(value: Any, passages: list[Any], facts: list[dict]) -> ReadingAnswer:
    answer = ReadingAnswer.model_validate(value)
    by_id = {p.id: p for p in passages}
    citations = {c.citation_id: c for c in answer.evidence_manifest}
    if len(citations) != len(answer.evidence_manifest):
        raise ValueError("duplicate citation")
    if any(not any(_same_json(fact, saved) for saved in facts) for fact in answer.computed_facts):
        raise ValueError("invented chart fact")
    fact_ids = {fact["fact_id"] for fact in facts}
    for citation in citations.values():
        p = by_id.get(citation.passage_id)
        if p is None:
            raise ValueError("unknown passage")
        if (
            citation.passage_hash != p.text_hash
            or sha256(p.text.encode()).hexdigest() != p.text_hash
        ):
            raise ValueError("source hash mismatch")
        if citation.start != 0 or citation.end != len(p.text):
            raise ValueError("Only complete evidence units may be quoted")
        if not 0 <= citation.start < citation.end <= len(p.text):
            raise ValueError("invalid span")
        if p.text[citation.start : citation.end] != citation.quoted_text:
            raise ValueError("quote mismatch")
        if not _boundary(p.text, citation.start) or not _boundary(p.text, citation.end):
            raise ValueError("grapheme split")
        if not _same_json(citation.locators, p.locators):
            raise ValueError("invented locator")
    if len({c.claim_id for c in answer.traditional_claims}) != len(answer.traditional_claims):
        raise ValueError("duplicate claim")
    for claim in answer.traditional_claims:
        if any(ref not in citations for ref in claim.citation_ids):
            raise ValueError("unknown citation")
        if any(ref not in fact_ids for ref in claim.chart_fact_ids):
            raise ValueError("unknown chart fact")
        # No expert-reviewed registry is installed. Exact excerpts are the only admitted claims.
        if claim.applicability_status != "not_established" or claim.scope_note != SCOPE:
            raise ValueError("applicability is not reviewed")
        if claim.text not in [citations[ref].quoted_text for ref in claim.citation_ids]:
            raise ValueError("claim is not an exact supported excerpt")
    if answer.interpretation or answer.disagreements or answer.suggested_questions:
        raise ValueError("unreviewed narrative")
    if any(note not in LIMITATIONS for note in answer.limitations):
        raise ValueError("unreviewed limitation")
    if (
        answer.concise_summary != SUMMARY
        or answer.status != "partial"
        or not answer.traditional_claims
    ):
        raise ValueError("unreviewed summary or unsupported answer")
    return answer
