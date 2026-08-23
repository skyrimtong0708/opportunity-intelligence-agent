import json
import tempfile
import unittest
from pathlib import Path

from opportunity_intel.adapters import JsonlSampleAdapter, PublicApiAdapter, RssAdapter


class AdapterTests(unittest.TestCase):
    def test_network_stubs_are_inert(self):
        self.assertEqual(RssAdapter(["https://example.org/feed"]).collect("x"), [])
        self.assertEqual(PublicApiAdapter(["https://example.org/api"]).collect("x"), [])

    def test_sample_adapter_filters_niche(self):
        record = {
            "id": "e1", "niche_id": "n1", "source_type": "synthetic_sample",
            "source_name": "fixture", "source_url": "sample://1", "title": "t",
            "content": "c", "observed_at": "2026-01-01T00:00:00Z", "language": "vi"
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.jsonl"
            path.write_text(json.dumps(record), encoding="utf-8")
            self.assertEqual(len(JsonlSampleAdapter(path).collect("n1")), 1)
            self.assertEqual(JsonlSampleAdapter(path).collect("other"), [])


if __name__ == "__main__":
    unittest.main()

