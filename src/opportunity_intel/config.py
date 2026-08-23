from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class NicheConfig:
    id: str
    name: str
    description: str
    actors: list[str]
    seed_queries: list[str]
    pain_keywords: dict[str, list[str]]
    clusters: dict[str, list[str]]
    offer_templates: dict[str, str]
    legal_sources: list[dict[str, Any]]
    scoring_overrides: dict[str, float]


def load_config(path: str | Path) -> NicheConfig:
    """Load JSON-compatible YAML without requiring PyYAML at runtime."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return NicheConfig(**data)


def load_configs(directory: str | Path) -> dict[str, NicheConfig]:
    configs = {}
    for path in sorted(Path(directory).glob("*.yaml")):
        config = load_config(path)
        configs[config.id] = config
    return configs

