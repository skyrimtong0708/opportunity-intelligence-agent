import unittest

from opportunity_intel.scoring import DEFAULT_WEIGHTS, score_dimensions


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.dimensions = {key: 5.0 for key in DEFAULT_WEIGHTS}

    def test_midpoint_score(self):
        result = score_dimensions(self.dimensions)
        self.assertEqual(result.total, 5.0)
        self.assertAlmostEqual(sum(result.contributions.values()), 5.0)

    def test_out_of_range_rejected(self):
        self.dimensions["severity"] = 11
        with self.assertRaises(ValueError):
            score_dimensions(self.dimensions)

    def test_invalid_weights_rejected(self):
        with self.assertRaises(ValueError):
            score_dimensions(self.dimensions, {"frequency": 0.5})


if __name__ == "__main__":
    unittest.main()

