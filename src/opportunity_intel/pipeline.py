from __future__ import annotations

from dataclasses import dataclass

from .adapters import MediaSourceAdapter, ProductSourceAdapter, SourceAdapter
from .agents import (
    ClusteringAgent,
    ExperimentAgent,
    ExtractorAgent,
    OpportunityAgent,
    ScoutAgent,
    SkepticAgent,
)
from .config import NicheConfig
from .models import Cluster, Evidence, MediaSignal, Opportunity, PainPoint, ProductCandidate
from .sourcing import ContentSignalAgent, ProductSourcingAgent


@dataclass
class PipelineResult:
    evidence: list[Evidence]
    pain_points: list[PainPoint]
    clusters: list[Cluster]
    opportunities: list[Opportunity]
    product_candidates: list[ProductCandidate]
    media_signals: list[MediaSignal]


class OpportunityPipeline:
    def __init__(self) -> None:
        self.scout = ScoutAgent()
        self.extractor = ExtractorAgent()
        self.clustering = ClusteringAgent()
        self.opportunity = OpportunityAgent()
        self.skeptic = SkepticAgent()
        self.experiment = ExperimentAgent()
        self.sourcing = ProductSourcingAgent()
        self.content_signal = ContentSignalAgent()

    def run(
        self,
        config: NicheConfig,
        adapters: list[SourceAdapter],
        product_adapters: list[ProductSourceAdapter] | None = None,
        media_adapters: list[MediaSourceAdapter] | None = None,
    ) -> PipelineResult:
        evidence = self.scout.run(config.id, adapters)
        pains = self.extractor.run(evidence, config)
        clusters = self.clustering.run(pains, config)
        opportunities = self.opportunity.run(clusters, pains, config)
        opportunities = self.skeptic.run(opportunities)
        opportunities = self.experiment.run(opportunities)
        products = [item for adapter in (product_adapters or []) for item in adapter.collect_products(config.id)]
        media = [item for adapter in (media_adapters or []) for item in adapter.collect_media(config.id)]
        products = self.sourcing.run(products, opportunities)
        media = self.content_signal.run(media)
        return PipelineResult(evidence, pains, clusters, opportunities, products, media)
