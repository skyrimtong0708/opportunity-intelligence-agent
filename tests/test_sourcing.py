import unittest
from pathlib import Path
from unittest.mock import patch

from opportunity_intel.adapters import (
    JsonlMediaAdapter,
    JsonlProductAdapter,
    ShopeeOpenPlatformAdapter,
    TikTokDisplayApiAdapter,
    YouTubeDataApiAdapter,
)
from opportunity_intel.config import load_configs
from opportunity_intel.pipeline import OpportunityPipeline
from opportunity_intel.sourcing import PRODUCT_WEIGHTS, score_product_dimensions
from opportunity_intel.adapters import JsonlSampleAdapter


ROOT = Path(__file__).resolve().parents[1]


class SourcingTests(unittest.TestCase):
    def test_product_score_midpoint(self):
        self.assertEqual(score_product_dimensions({key: 5 for key in PRODUCT_WEIGHTS}), 5.0)

    def test_product_score_rejects_missing_dimensions(self):
        with self.assertRaises(ValueError):
            score_product_dimensions({"pain_fit": 8})

    def test_sample_sourcing_runs_for_reference_niche(self):
        config = load_configs(ROOT / "configs" / "niches")["seller_packing_os"]
        result = OpportunityPipeline().run(
            config,
            [JsonlSampleAdapter(ROOT / "data" / "sample" / "evidence.jsonl")],
            [JsonlProductAdapter(ROOT / "data" / "sample" / "products.jsonl")],
            [JsonlMediaAdapter(ROOT / "data" / "sample" / "media_signals.jsonl")],
        )
        self.assertEqual(len(result.product_candidates), 3)
        self.assertEqual(len(result.media_signals), 2)
        self.assertGreater(result.product_candidates[0].sourcing_score, 0)
        self.assertTrue(result.product_candidates[0].linked_opportunity_ids)
        self.assertGreater(result.media_signals[0].relevance_score, 0)

    def test_official_adapters_are_inert_without_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(YouTubeDataApiAdapter(["test"]).collect_media("n1"), [])
            self.assertEqual(TikTokDisplayApiAdapter(["test"]).collect_media("n1"), [])
            self.assertEqual(ShopeeOpenPlatformAdapter(["test"]).collect_products("n1"), [])


if __name__ == "__main__":
    unittest.main()
