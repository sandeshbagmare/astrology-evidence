"""Data-only predicates. No real traditional rules are activated without expert review."""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    kind: str = Field(min_length=1, max_length=80)
    body: str | None = None
    equals: str | int | float | bool


class ReviewedRule(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    rule_id: str = Field(min_length=1, max_length=80)
    reviewer: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=80)
    tradition: str = Field(min_length=1, max_length=80)
    passage_ids: list[str] = Field(min_length=1, max_length=8)
    conditions: list[Condition] = Field(min_length=1, max_length=20)


@dataclass(frozen=True)
class Applicability:
    truth: Literal["true", "false", "unknown"]
    fact_ids: tuple[str, ...] = ()


def evaluate(rule: ReviewedRule, facts: list[dict]) -> Applicability:
    matched = []
    unknown = False
    for condition in rule.conditions:
        candidates = [
            fact
            for fact in facts
            if fact.get("kind") == condition.kind
            and (condition.body is None or fact.get("body") == condition.body)
        ]
        if len(candidates) != 1 or candidates[0].get("stability") != "stable":
            unknown = True
            continue
        fact = candidates[0]
        if (
            type(fact.get("value")) is not type(condition.equals)
            or fact["value"] != condition.equals
        ):
            return Applicability("false")
        if not isinstance(fact.get("fact_id"), str):
            unknown = True
            continue
        matched.append(fact["fact_id"])
    return Applicability("unknown" if unknown else "true", tuple(matched))


# Populated only through a separately reviewed code change with edition-specific provenance.
REVIEWED_RULES: tuple[ReviewedRule, ...] = ()
