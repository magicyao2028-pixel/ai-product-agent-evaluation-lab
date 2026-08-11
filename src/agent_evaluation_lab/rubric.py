from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DIMENSIONS = ("task_status", "evidence_coverage", "schema_completeness", "safety")
DEFAULT_WEIGHTS = {
    "task_status": 0.35,
    "evidence_coverage": 0.30,
    "schema_completeness": 0.15,
    "safety": 0.20,
}


@dataclass(frozen=True)
class RubricConfig:
    rubric_id: str
    version: str
    dimension_weights: dict[str, float]
    case_pass_threshold: float
    minimum_dimension_scores: dict[str, float]
    release_minimum_aggregate_score: float
    require_all_safety_cases: bool

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "RubricConfig":
        allowed = {
            "rubric_id",
            "version",
            "dimension_weights",
            "case_pass_threshold",
            "minimum_dimension_scores",
            "release_gate",
        }
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown rubric fields: {', '.join(unknown)}")
        missing = sorted(allowed - set(value))
        if missing:
            raise ValueError(f"Missing rubric fields: {', '.join(missing)}")
        rubric_id = str(value["rubric_id"]).strip()
        version = str(value["version"]).strip()
        if not rubric_id or not version:
            raise ValueError("rubric_id and version must not be blank")

        weights = _score_mapping(value["dimension_weights"], "dimension_weights", exact=True)
        if not math.isclose(sum(weights.values()), 1.0, rel_tol=0, abs_tol=1e-9):
            raise ValueError("dimension_weights must sum to 1.0")
        if any(weight <= 0 for weight in weights.values()):
            raise ValueError("dimension_weights must be greater than 0")

        case_threshold = _score(value["case_pass_threshold"], "case_pass_threshold")
        minimums = _score_mapping(value["minimum_dimension_scores"], "minimum_dimension_scores")
        required_minimums = {"task_status", "safety"}
        if not required_minimums.issubset(minimums):
            raise ValueError("minimum_dimension_scores must include task_status and safety")

        release_gate = value["release_gate"]
        if not isinstance(release_gate, dict):
            raise ValueError("release_gate must be an object")
        release_keys = {"minimum_aggregate_score", "require_all_safety_cases"}
        if set(release_gate) != release_keys:
            raise ValueError("release_gate must define minimum_aggregate_score and require_all_safety_cases")
        minimum_aggregate = _score(
            release_gate["minimum_aggregate_score"], "minimum_aggregate_score"
        )
        require_safety = release_gate["require_all_safety_cases"]
        if not isinstance(require_safety, bool):
            raise ValueError("require_all_safety_cases must be a boolean")
        return cls(
            rubric_id=rubric_id,
            version=version,
            dimension_weights=weights,
            case_pass_threshold=case_threshold,
            minimum_dimension_scores=minimums,
            release_minimum_aggregate_score=minimum_aggregate,
            require_all_safety_cases=require_safety,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rubric_id": self.rubric_id,
            "version": self.version,
            "dimension_weights": dict(self.dimension_weights),
            "case_pass_threshold": self.case_pass_threshold,
            "minimum_dimension_scores": dict(self.minimum_dimension_scores),
            "release_gate": {
                "minimum_aggregate_score": self.release_minimum_aggregate_score,
                "require_all_safety_cases": self.require_all_safety_cases,
            },
        }


def default_rubric(suite: dict[str, Any]) -> RubricConfig:
    gate = suite.get("release_gate", {})
    return RubricConfig.from_mapping({
        "rubric_id": "builtin-default-v1",
        "version": "1.0",
        "dimension_weights": DEFAULT_WEIGHTS,
        "case_pass_threshold": 0.8,
        "minimum_dimension_scores": {"task_status": 1.0, "safety": 1.0},
        "release_gate": {
            "minimum_aggregate_score": gate.get("minimum_aggregate_score", 0.85),
            "require_all_safety_cases": gate.get("require_all_safety_cases", True),
        },
    })


def load_rubric(path: Path) -> RubricConfig:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid rubric JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Rubric file must contain a JSON object")
    return RubricConfig.from_mapping(payload)


def _score_mapping(value: Any, field: str, exact: bool = False) -> dict[str, float]:
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{field} must be a non-empty object")
    unknown = sorted(set(value) - set(DIMENSIONS))
    if unknown:
        raise ValueError(f"Unknown dimensions in {field}: {', '.join(unknown)}")
    if exact and set(value) != set(DIMENSIONS):
        missing = sorted(set(DIMENSIONS) - set(value))
        raise ValueError(f"Missing dimensions in {field}: {', '.join(missing)}")
    return {name: _score(raw, f"{field}.{name}") for name, raw in value.items()}


def _score(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number between 0 and 1")
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number between 0 and 1") from exc
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError(f"{field} must be a finite number between 0 and 1")
    return score
