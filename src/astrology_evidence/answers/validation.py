from __future__ import annotations
from hashlib import sha256
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class Citation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    citation_id: str = Field(min_length=1)
    passage_id: str = Field(min_length=1)
    passage_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    quoted_text: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    locators: dict[str, Any] = Field(default_factory=dict)

class TraditionalClaim(BaseModel):
    model_config = ConfigDict(extra='forbid')
    claim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    citation_ids: list[str] = Field(default_factory=list)
    chart_fact_ids: list[str] = Field(default_factory=list)
    applicability_status: Literal['reviewed_rule', 'model_inference', 'not_established']
    scope_note: str = ''

class ReadingAnswer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Literal['supported', 'partial', 'insufficient_evidence']
    concise_summary: str = Field(min_length=1)
    computed_facts: list[dict[str, Any]] = Field(default_factory=list)
    traditional_claims: list[TraditionalClaim] = Field(default_factory=list)
    interpretation: list[str] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    evidence_manifest: list[Citation] = Field(default_factory=list)

def validate_answer(value: Any, passages: list[Any]) -> ReadingAnswer:
    answer = value if isinstance(value, ReadingAnswer) else ReadingAnswer.model_validate(value)
    by_id = {str(p.id): p for p in passages}
    citations = {c.citation_id: c for c in answer.evidence_manifest}
    if len(citations) != len(answer.evidence_manifest): raise ValueError('duplicate citation id')
    for citation in answer.evidence_manifest:
        passage = by_id.get(citation.passage_id)
        if passage is None: raise ValueError('citation passage is not authorized')
        text = str(passage.text)
        if citation.end > len(text) or text[citation.start:citation.end] != citation.quoted_text: raise ValueError('citation span does not match source')
        if sha256(text.encode('utf-8')).hexdigest() != citation.passage_hash: raise ValueError('citation source hash mismatch')
    for claim in answer.traditional_claims:
        if any(cid not in citations for cid in claim.citation_ids): raise ValueError('claim cites an unknown citation')
        if claim.applicability_status == 'reviewed_rule' and not claim.chart_fact_ids: raise ValueError('reviewed rule requires chart facts')
    return answer
