"""Evaluate recorded rankings and reviewer labels; never calls a model or search service."""

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Identifier = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]
Grade = Annotated[int, Field(ge=0, le=3, strict=True)]


class EvaluationItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: Identifier
    split: Literal["calibration", "development", "test"]
    expected_evidence_units: dict[Identifier, Grade]
    ranked_ids: list[Identifier] = Field(max_length=1000)
    status: Literal["ok", "error"]
    abstained: bool
    claim_count: int = Field(ge=0)
    supported_claim_count: int = Field(ge=0)

    @field_validator("ranked_ids")
    @classmethod
    def unique_ranks(cls, ids: list[str]) -> list[str]:
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate ranked evidence ID")
        return ids

    @model_validator(mode="after")
    def valid_counts(self):
        if self.supported_claim_count > self.claim_count:
            raise ValueError("supported claim count exceeds claim count")
        return self


class EvaluationSet(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal[1]
    synthetic: bool
    items: list[EvaluationItem] = Field(min_length=1, max_length=10000)


def _ratio(numerator: int, denominator: int) -> dict:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator if denominator else None,
    }


def evaluate(payload: dict, *, allow_small_synthetic: bool = False, split: str = "test") -> dict:
    dataset = EvaluationSet.model_validate(payload)
    if split not in {"calibration", "development", "test"}:
        raise ValueError("unknown split")
    if len({item.id for item in dataset.items}) != len(dataset.items):
        raise ValueError("duplicate question ID across splits")
    counts = Counter(item.split for item in dataset.items)
    if allow_small_synthetic:
        if not dataset.synthetic:
            raise ValueError("small sets must be explicitly labeled synthetic")
    elif counts != {"calibration": 20, "development": 30, "test": 100}:
        raise ValueError("release split counts must be 20 calibration / 30 development / 100 test")
    if not allow_small_synthetic:
        supported_test = sum(
            any(v > 0 for v in item.expected_evidence_units.values())
            for item in dataset.items
            if item.split == "test"
        )
        if supported_test != 86:
            raise ValueError("test split must contain 86 supported and 14 unsupported questions")
    items = [item for item in dataset.items if item.split == split]
    if not items:
        raise ValueError("selected split contains no questions")
    results: list[dict] = []
    for item in items:
        grades = item.expected_evidence_units
        relevant = {key for key, grade in grades.items() if grade > 0}
        ranking = item.ranked_ids[:10] if item.status == "ok" else []
        hits = len(relevant.intersection(ranking))
        dcg = sum(
            (2 ** grades.get(key, 0) - 1) / math.log2(rank + 2) for rank, key in enumerate(ranking)
        )
        ideal = sum(
            (2**grade - 1) / math.log2(rank + 2)
            for rank, grade in enumerate(sorted(grades.values(), reverse=True)[:10])
        )
        results.append(
            {
                "id": item.id,
                "status": item.status,
                "supported": bool(relevant),
                "recall_at_10": hits / len(relevant) if relevant else None,
                "hit_at_10": int(hits > 0) if relevant else None,
                "ndcg_at_10": dcg / ideal if ideal else None,
            }
        )
    supported = [row for row in results if row["supported"]]
    unsupported = [item for item in items if not any(item.expected_evidence_units.values())]
    return {
        "schema_version": 1,
        "synthetic": dataset.synthetic,
        "split": split,
        "split_counts": dict(counts),
        "questions": len(items),
        "supported_questions": len(supported),
        "unsupported_questions": len(unsupported),
        "errors": sum(item.status == "error" for item in items),
        **{
            metric: sum(row[metric] for row in supported) / len(supported) if supported else None
            for metric in ("recall_at_10", "hit_at_10", "ndcg_at_10")
        },
        "claim_support": _ratio(
            sum(item.supported_claim_count for item in items if item.status == "ok"),
            sum(item.claim_count for item in items),
        ),
        "abstention": _ratio(
            sum(item.abstained and item.status == "ok" for item in unsupported), len(unsupported)
        ),
        "per_input": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--allow-small-synthetic", action="store_true")
    parser.add_argument("--split", choices=["calibration", "development", "test"], default="test")
    args = parser.parse_args()
    try:
        with args.input.open("rb") as source:
            data = source.read(10_000_001)
        if len(data) > 10_000_000:
            raise ValueError("evaluation input exceeds 10 MB")
        report = evaluate(
            json.loads(data), allow_small_synthetic=args.allow_small_synthetic, split=args.split
        )
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
