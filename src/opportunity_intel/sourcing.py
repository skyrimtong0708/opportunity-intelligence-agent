from __future__ import annotations

import math

from .models import MediaSignal, Opportunity, ProductCandidate


PRODUCT_WEIGHTS = {
    "pain_fit": 0.25,
    "demand_signal": 0.20,
    "repeat_purchase": 0.15,
    "gross_margin_potential": 0.15,
    "supplier_reliability": 0.10,
    "differentiation": 0.10,
    "ease_of_test": 0.05,
}


def score_product_dimensions(dimensions: dict[str, float]) -> float:
    missing = set(PRODUCT_WEIGHTS) - set(dimensions)
    if missing:
        raise ValueError(f"Missing product dimensions: {sorted(missing)}")
    invalid = {key: value for key, value in dimensions.items() if key in PRODUCT_WEIGHTS and not 0 <= value <= 10}
    if invalid:
        raise ValueError(f"Product dimensions must be between 0 and 10: {invalid}")
    return round(sum(dimensions[key] * weight for key, weight in PRODUCT_WEIGHTS.items()), 2)


class ProductSourcingAgent:
    """Ranks candidate offers without equating marketplace popularity with demand."""

    role = "sourcing"

    def run(self, candidates: list[ProductCandidate], opportunities: list[Opportunity]) -> list[ProductCandidate]:
        for candidate in candidates:
            candidate.sourcing_score = score_product_dimensions(candidate.dimensions)
            haystack = " ".join(candidate.problem_tags).lower()
            linked = [
                opportunity.id for opportunity in opportunities
                if any(tag.lower() in f"{opportunity.title} {opportunity.problem} {opportunity.proposed_offer}".lower() for tag in candidate.problem_tags)
            ]
            candidate.linked_opportunity_ids = linked or ([opportunities[0].id] if opportunities else [])
            risks = []
            if candidate.source_type in {"synthetic_sample", "manual_marketplace_export"}:
                risks.append("Listing data is unverified; confirm price, availability and authorization at source")
            if candidate.rating is None or candidate.review_count < 20:
                risks.append("Supplier reliability signal is thin")
            if candidate.min_order_quantity > 20:
                risks.append("MOQ is high for a smoke test")
            risks.append("Validate landed cost, compliance, warranty and IP before purchase")
            candidate.risks = risks
        return sorted(candidates, key=lambda item: (-item.sourcing_score, item.id))


class ContentSignalAgent:
    """Ranks video metadata for human review; it does not treat views as proof of pain."""

    role = "content_signal"

    def run(self, signals: list[MediaSignal]) -> list[MediaSignal]:
        for signal in signals:
            engagement = signal.like_count + signal.comment_count * 3
            scale = min(7.0, math.log10(max(signal.view_count, 1)) * 1.2)
            rate = min(3.0, engagement / max(signal.view_count, 1) * 100)
            signal.relevance_score = round(min(10.0, scale + rate), 2)
        return sorted(signals, key=lambda item: (-item.relevance_score, item.id))
