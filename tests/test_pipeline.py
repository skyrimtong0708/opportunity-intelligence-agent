import tempfile
import unittest
from pathlib import Path

from opportunity_intel.adapters import JsonlSampleAdapter
from opportunity_intel.config import load_config, load_configs
from opportunity_intel.pipeline import OpportunityPipeline
from opportunity_intel.storage import SqliteRepository


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.configs = load_configs(ROOT / "configs" / "niches")
        self.adapter = JsonlSampleAdapter(ROOT / "data" / "sample" / "evidence.jsonl")

    def test_five_configs_load(self):
        self.assertEqual(len(self.configs), 5)
        self.assertIn("seller_packing_os", self.configs)

    def test_reference_niche_runs_all_outputs(self):
        result = OpportunityPipeline().run(self.configs["seller_packing_os"], [self.adapter])
        self.assertGreaterEqual(len(result.evidence), 5)
        self.assertTrue(result.pain_points)
        self.assertTrue(result.clusters)
        self.assertTrue(result.opportunities)
        self.assertTrue(all(o.risks and o.experiment for o in result.opportunities))

    def test_pipeline_is_deterministic(self):
        pipeline = OpportunityPipeline()
        first = pipeline.run(self.configs["seller_packing_os"], [self.adapter])
        second = pipeline.run(self.configs["seller_packing_os"], [self.adapter])
        self.assertEqual([o.to_dict() for o in first.opportunities], [o.to_dict() for o in second.opportunities])

    def test_all_niches_run_with_shared_engine(self):
        pipeline = OpportunityPipeline()
        for config in self.configs.values():
            with self.subTest(config=config.id):
                result = pipeline.run(config, [self.adapter])
                self.assertTrue(result.opportunities)

    def test_all_niches_have_sourcing_fixtures(self):
        from opportunity_intel.adapters import JsonlMediaAdapter, JsonlProductAdapter

        product_adapter = JsonlProductAdapter(ROOT / "data" / "sample" / "products.jsonl")
        media_adapter = JsonlMediaAdapter(ROOT / "data" / "sample" / "media_signals.jsonl")
        for config in self.configs.values():
            with self.subTest(config=config.id):
                result = OpportunityPipeline().run(config, [self.adapter], [product_adapter], [media_adapter])
                self.assertEqual(len(result.product_candidates), 3)
                self.assertEqual(len(result.media_signals), 2)

    def test_sqlite_persistence(self):
        result = OpportunityPipeline().run(self.configs["seller_packing_os"], [self.adapter])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oia.db"
            SqliteRepository(path).save(result)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
