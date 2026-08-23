from __future__ import annotations

from dataclasses import dataclass


DEFAULT_WEIGHTS = {
    "frequency": 0.18,
    "severity": 0.18,
    "willingness_to_pay": 0.16,
    "evidence_strength": 0.14,
    "market_reach": 0.10,
    "repeatability": 0.10,
    "data_moat": 0.08,
    "ease_of_test": 0.06,
}


@dataclass(frozen=True)
class ScoreResult:
    total: float
    contributions: dict[str, float]
    weights: dict[str, float]
    version: str = "v1"


def score_dimensions(
    dimensions: dict[str, float], overrides: dict[str, float] | None = None
) -> ScoreResult:
    weights = DEFAULT_WEIGHTS | (overrides or {})
    if set(weights) != set(DEFAULT_WEIGHTS):
        unknown = set(weights) - set(DEFAULT_WEIGHTS)
        raise ValueError(f"Unknown scoring dimensions: {sorted(unknown)}")
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError("Scoring weights must sum to 1.0")
    missing = set(DEFAULT_WEIGHTS) - set(dimensions)
    if missing:
        raise ValueError(f"Missing dimensions: {sorted(missing)}")
    invalid = {k: v for k, v in dimensions.items() if not 0 <= v <= 10}
    if invalid:
        raise ValueError(f"Dimension values must be between 0 and 10: {invalid}")
    contributions = {key: round(dimensions[key] * weight, 4) for key, weight in weights.items()}
    return ScoreResult(round(sum(contributions.values()), 2), contributions, weights)

