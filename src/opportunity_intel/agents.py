from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict

from .adapters import SourceAdapter
from .config import NicheConfig
from .models import Cluster, Evidence, Opportunity, PainPoint
from .scoring import score_dimensions


def stable_id(prefix: str, *values: str) -> str:
    digest = hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def clamp(value: float, low: float = 0, high: float = 10) -> float:
    return max(low, min(high, value))


class ScoutAgent:
    role = "scout"

    def run(self, niche_id: str, adapters: list[SourceAdapter]) -> list[Evidence]:
        dedup: dict[str, Evidence] = {}
        for adapter in adapters:
            for item in adapter.collect(niche_id):
                fingerprint = stable_id("dedup", item.source_url, item.content.lower().strip())
                dedup[fingerprint] = item
        return sorted(dedup.values(), key=lambda x: (x.observed_at, x.id))


class ExtractorAgent:
    role = "extractor"

    def run(self, evidence: list[Evidence], config: NicheConfig) -> list[PainPoint]:
        results = []
        all_keywords = [k for words in config.pain_keywords.values() for k in words]
        for item in evidence:
            text = f"{item.title}. {item.content}"
            lower = text.lower()
            hits = [word for word in all_keywords if word.lower() in lower]
            if not hits:
                continue
            frequency = clamp(3 + min(len(hits), 4) + min(item.engagement / 20, 3))
            severity_words = ["hỏng", "mất", "kẹt", "ẩm", "mốc", "fail", "jam", "damage", "return"]
            severity = clamp(3.5 + sum(word in lower for word in severity_words) * 1.2)
            wtp_words = ["mua", "giá", "thay", "dịch vụ", "kit", "buy", "replace"]
            wtp = clamp(2.5 + sum(word in lower for word in wtp_words) * 1.4)
            actor = next((actor for actor in config.actors if actor.lower() in lower), config.actors[0])
            results.append(PainPoint(
                id=stable_id("pain", item.id, ",".join(sorted(hits))),
                niche_id=config.id,
                evidence_id=item.id,
                statement=item.title,
                actor=actor,
                workaround="Manual/ad-hoc workaround inferred; validate by interview",
                purchase_trigger="Problem recurrence or asset/order at risk",
                frequency=round(frequency, 1),
                severity=round(severity, 1),
                willingness_to_pay=round(wtp, 1),
                confidence=round(clamp(4 + len(hits) + min(item.engagement / 25, 2)) / 10, 2),
                tags=sorted(set(hits)),
            ))
        return results


class ClusteringAgent:
    role = "clustering"

    def run(self, pains: list[PainPoint], config: NicheConfig) -> list[Cluster]:
        buckets: dict[str, list[PainPoint]] = defaultdict(list)
        for pain in pains:
            scores = {
                label: sum(keyword.lower() in " ".join(pain.tags).lower() for keyword in keywords)
                for label, keywords in config.clusters.items()
            }
            label = max(scores, key=lambda k: (scores[k], k))
            buckets[label].append(pain)
        clusters = []
        for label, members in sorted(buckets.items()):
            keywords = [tag for tag, _ in Counter(t for p in members for t in p.tags).most_common(8)]
            clusters.append(Cluster(
                id=stable_id("cluster", config.id, label),
                niche_id=config.id,
                label=label,
                description=f"Recurring {label.replace('_', ' ')} problems for {config.name}",
                pain_point_ids=[p.id for p in members],
                evidence_count=len({p.evidence_id for p in members}),
                keywords=keywords,
            ))
        return clusters


class OpportunityAgent:
    role = "opportunity"

    def run(self, clusters: list[Cluster], pains: list[PainPoint], config: NicheConfig) -> list[Opportunity]:
        pain_by_id = {p.id: p for p in pains}
        results = []
        for cluster in clusters:
            members = [pain_by_id[pid] for pid in cluster.pain_point_ids]
            if not members:
                continue
            avg = lambda attr: sum(getattr(p, attr) for p in members) / len(members)
            dimensions = {
                "frequency": round(avg("frequency"), 2),
                "severity": round(avg("severity"), 2),
                "willingness_to_pay": round(avg("willingness_to_pay"), 2),
                "evidence_strength": round(clamp(3 + cluster.evidence_count * 1.2), 2),
                "market_reach": round(clamp(4 + len(members) * 0.7), 2),
                "repeatability": round(clamp(5 + avg("frequency") * 0.35), 2),
                "data_moat": round(clamp(4 + cluster.evidence_count * 0.5), 2),
                "ease_of_test": 8.0,
            }
            offer = config.offer_templates.get(cluster.label, f"Diagnostic + starter kit for {cluster.label}")
            score = score_dimensions(dimensions, config.scoring_overrides)
            results.append(Opportunity(
                id=stable_id("opp", config.id, cluster.id),
                niche_id=config.id,
                cluster_id=cluster.id,
                title=f"{config.name}: {cluster.label.replace('_', ' ').title()}",
                problem="; ".join(p.statement for p in members[:3]),
                target_customer=members[0].actor,
                proposed_offer=offer,
                business_model="Starter kit + recurring consumables + optional workflow software/service",
                evidence_ids=sorted({p.evidence_id for p in members}),
                dimensions=dimensions,
                score=score.total,
            ))
        return sorted(results, key=lambda x: (-x.score, x.id))


class SkepticAgent:
    role = "skeptic"

    def run(self, opportunities: list[Opportunity]) -> list[Opportunity]:
        for opp in opportunities:
            risks = []
            if len(opp.evidence_ids) < 3:
                risks.append("Thin evidence: fewer than 3 independent observations")
            if opp.dimensions["willingness_to_pay"] < 5:
                risks.append("Weak willingness-to-pay signal; do not infer demand from complaints")
            if opp.dimensions["evidence_strength"] < 6:
                risks.append("Source diversity and sample size need validation")
            risks.extend([
                "Heuristic extraction may misread context; review evidence manually",
                "Check unit economics, substitutes and platform dependency before build",
            ])
            opp.risks = risks
        return opportunities


class ExperimentAgent:
    role = "experiment"

    def run(self, opportunities: list[Opportunity]) -> list[Opportunity]:
        for opp in opportunities:
            opp.experiment = {
                "hypothesis": f"{opp.target_customer} will pay for: {opp.proposed_offer}",
                "method": "10 problem interviews + smoke-test landing page + manual concierge fulfillment",
                "sample_size": 10,
                "duration_days": 7,
                "success_metrics": {
                    "qualified_interview_problem_rate": ">= 60%",
                    "landing_page_lead_rate": ">= 8%",
                    "paid_or_deposit_commitments": ">= 3",
                },
                "stop_rule": "Stop or revise after 10 qualified interviews if fewer than 4 report the problem unprompted",
            }
        return opportunities

