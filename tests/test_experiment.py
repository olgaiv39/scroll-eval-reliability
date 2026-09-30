import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import experiment


class TransformTests(unittest.TestCase):
    def setUp(self):
        self.raw = {"format": "xyz", "detector": "fixture", "alarms": {
            "points": [[2, 0, 0], [1, 0, 0], [2, 0, 0]], "empty": [], "null": None}}

    def test_permutation_is_deterministic_and_multiset_preserving(self):
        first = experiment.transform(self.raw, "permutation", 7)
        second = experiment.transform(self.raw, "permutation", 7)
        self.assertEqual(first, second)
        checks = experiment.equivalence(self.raw, first)
        self.assertTrue(checks["passed"])
        self.assertEqual(first["alarms"]["empty"], [])
        self.assertIsNone(first["alarms"]["null"])

    def test_duplicate_doubles_multiplicity_after_each_original(self):
        candidate = experiment.transform(self.raw, "duplicate")
        checks = experiment.equivalence(self.raw, candidate, duplicate=True)
        self.assertTrue(checks["passed"])
        self.assertIsNone(checks["point_multisets_identical"])
        self.assertIsNone(checks.get("original_order_preserved"))
        self.assertTrue(checks["multiplicity_exactly_doubled"])
        self.assertTrue(checks["adjacent_copy_after_each_original"])
        self.assertEqual(candidate["alarms"]["points"], [[2, 0, 0], [2, 0, 0], [1, 0, 0], [1, 0, 0], [2, 0, 0], [2, 0, 0]])

    def test_missing_empty_and_null_are_distinct_states(self):
        self.assertEqual(experiment.states(self.raw), {"points": "points", "empty": "empty", "null": "null"})
        missing = {"format": "xyz", "alarms": {"empty": [], "null": None}}
        self.assertNotEqual(experiment.states(self.raw), experiment.states(missing))

    def test_corrupted_result_metadata_is_rejected(self):
        spec = {"name": "original", "kind": "original"}
        row = {"name": "original", "transformation": "original", "seed": None, "status": "completed",
               "effective_settings": {**experiment.SETTINGS, "bootstrap": 0}, "geometry_check": "match",
               "geometry_sha256": experiment.GEOMETRY_SHA256, "hits": 24, "events": 213, "coverage": [237, 237],
               "false_alarms": 70, "negative_mm": 100.0, "rate_per_100mm": 70.0,
               "per_patch_false_alarms": {"patch": 70}}
        self.assertEqual(experiment.metadata_errors(row, spec, 0), [])
        row["false_alarms"] = 69
        self.assertTrue(experiment.metadata_errors(row, spec, 0))

    def test_multiset_preserving_wrong_transformation_is_rejected(self):
        raw = {"format": "xyz", "alarms": {"points": [[3, 0, 0], [1, 0, 0], [2, 0, 0]]}}
        candidate = experiment.transform(raw, "reverse")
        self.assertTrue(experiment.equivalence(raw, candidate)["passed"])
        self.assertTrue(experiment.transformation_errors(raw, candidate, {"name": "bad", "kind": "lexicographic_xyz"}))

    def test_changed_denominator_with_consistent_rate_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "variants.json"
            payload = json.loads(experiment.VARIANTS.read_text())
            row = payload["variants"][1]
            row["negative_mm"] = 2 * row["negative_mm"]
            row["rate_per_100mm"] = 100 * row["false_alarms"] / row["negative_mm"]
            path.write_text(json.dumps(payload))
            with self.assertRaises(RuntimeError):
                experiment.validate_saved(variants_path=path, validation_path=None)

    def test_saved_finalization_normalizes_historical_metadata_in_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            variants = directory / "variants.json"
            patch = directory / "patch.json"
            payload = json.loads(experiment.VARIANTS.read_text())
            for row in payload["variants"]:
                row["equivalence"] = {"historical": True}
            variants.write_text(json.dumps(payload))
            patch.write_bytes((experiment.OUT / "selected_real_patch_example.json").read_bytes())
            before = patch.read_bytes()
            outcome = experiment.finalize_saved_evidence(variants_path=variants, patch_path=patch, validation_path=None)
            self.assertEqual(outcome["status"], "passed")
            self.assertEqual(outcome["normalized_variants_in_memory"], 25)
            self.assertEqual(patch.read_bytes(), before)

    def test_saved_finalization_rejects_before_artifact_write(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            variants = directory / "variants.json"
            validation = directory / "validation.json"
            patch = directory / "patch.json"
            payload = json.loads(experiment.VARIANTS.read_text())
            payload["variants"][0]["negative_mm"] += 1
            payload["variants"][0]["rate_per_100mm"] = 100 * payload["variants"][0]["false_alarms"] / payload["variants"][0]["negative_mm"]
            variants.write_text(json.dumps(payload))
            patch.write_bytes((experiment.OUT / "selected_real_patch_example.json").read_bytes())
            with self.assertRaises(RuntimeError):
                experiment.finalize_saved_evidence(variants_path=variants, patch_path=patch, validation_path=validation)
            self.assertFalse(validation.exists())


if __name__ == "__main__":
    unittest.main()
