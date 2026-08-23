from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import (
    JsonlMediaAdapter,
    JsonlProductAdapter,
    JsonlSampleAdapter,
    ShopeeOpenPlatformAdapter,
    TikTokDisplayApiAdapter,
    YouTubeDataApiAdapter,
)
from .config import load_configs
from .pipeline import OpportunityPipeline
from .storage import SqliteRepository, write_snapshot


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_pipeline(niche_ids: list[str] | None = None, live_sources: bool = False) -> dict:
    root = project_root()
    configs = load_configs(root / "configs" / "niches")
    selected = niche_ids or list(configs)
    unknown = set(selected) - set(configs)
    if unknown:
        raise SystemExit(f"Unknown niche(s): {', '.join(sorted(unknown))}")
    adapter = JsonlSampleAdapter(root / "data" / "sample" / "evidence.jsonl")
    product_adapter = JsonlProductAdapter(root / "data" / "sample" / "products.jsonl")
    media_adapter = JsonlMediaAdapter(root / "data" / "sample" / "media_signals.jsonl")
    pipeline = OpportunityPipeline()
    repository = SqliteRepository(root / "data" / "runtime" / "oia.db")
    results = {}
    for niche_id in selected:
        config = configs[niche_id]
        product_adapters = [product_adapter]
        media_adapters = [media_adapter]
        if live_sources:
            tags = sorted({keyword for words in config.pain_keywords.values() for keyword in words})
            product_adapters.append(ShopeeOpenPlatformAdapter(tags))
            media_adapters.extend([
                YouTubeDataApiAdapter(config.seed_queries),
                TikTokDisplayApiAdapter(config.seed_queries),
            ])
        result = pipeline.run(config, [adapter], product_adapters, media_adapters)
        repository.save(result)
        results[niche_id] = result
    write_snapshot(results, root / "data" / "runtime" / "latest.json")
    web_snapshot = root / "dashboard-web" / "app" / "snapshot.json"
    if web_snapshot.parent.exists():
        write_snapshot(results, web_snapshot)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Opportunity Intelligence Agent MVP")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run deterministic pipeline")
    run.add_argument("--niche", action="append", help="Niche ID; repeat to run several")
    run.add_argument("--all", action="store_true", help="Run all configured niches")
    run.add_argument("--live-sources", action="store_true", help="Enable credential-gated official source adapters")
    args = parser.parse_args()
    if args.command == "run":
        results = run_pipeline(None if args.all or not args.niche else args.niche, live_sources=args.live_sources)
        summary = {
            key: {
                "evidence": len(value.evidence),
                "pain_points": len(value.pain_points),
                "clusters": len(value.clusters),
                "opportunities": len(value.opportunities),
                "products": len(value.product_candidates),
                "media_signals": len(value.media_signals),
                "top_score": value.opportunities[0].score if value.opportunities else None,
            }
            for key, value in results.items()
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
