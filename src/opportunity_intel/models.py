from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Evidence:
    id: str
    niche_id: str
    source_type: str
    source_name: str
    source_url: str
    title: str
    content: str
    observed_at: str
    language: str = "vi"
    author: str | None = None
    engagement: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    collected_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PainPoint:
    id: str
    niche_id: str
    evidence_id: str
    statement: str
    actor: str
    workaround: str
    purchase_trigger: str
    frequency: float
    severity: float
    willingness_to_pay: float
    confidence: float
    tags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Cluster:
    id: str
    niche_id: str
    label: str
    description: str
    pain_point_ids: list[str]
    evidence_count: int
    keywords: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Opportunity:
    id: str
    niche_id: str
    cluster_id: str
    title: str
    problem: str
    target_customer: str
    proposed_offer: str
    business_model: str
    evidence_ids: list[str]
    dimensions: dict[str, float]
    score: float = 0.0
    score_version: str = "v1"
    risks: list[str] = field(default_factory=list)
    experiment: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProductCandidate:
    id: str
    niche_id: str
    source_type: str
    source_name: str
    source_url: str
    title: str
    supplier_name: str
    marketplace: str
    price: float
    currency: str
    min_order_quantity: int
    shipping_origin: str
    rating: float | None
    review_count: int
    sold_count: int
    problem_tags: list[str]
    dimensions: dict[str, float]
    sourcing_score: float = 0.0
    score_version: str = "sourcing_v1"
    linked_opportunity_ids: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    collected_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MediaSignal:
    id: str
    niche_id: str
    platform: str
    source_type: str
    source_url: str
    title: str
    description: str
    creator: str
    published_at: str
    query: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    relevance_score: float = 0.0
    problem_tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    collected_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
