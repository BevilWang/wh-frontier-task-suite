#!/usr/bin/env python3
"""Tests for the per-reference runnability report."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import runnability_report

BUNDLE = Path(__file__).resolve().parents[3] / "fb"


class RunnabilityReportTest(unittest.TestCase):
    def test_real_bundle_profiles_all_references(self) -> None:
        profiles = [
            runnability_report.profile_reference(BUNDLE, reference)
            for reference in runnability_report.TASKS
        ]
        self.assertEqual(len(profiles), 7)
        self.assertTrue(all(profile.compute in ("cpu", "gpu") for profile in profiles))
        self.assertTrue(all(profile.dockerfiles for profile in profiles))

    def test_ks_known_gap_is_surfaced(self) -> None:
        profile = runnability_report.profile_reference(BUNDLE, "ks-solver-cpp")
        self.assertTrue(any("wheels" in gap for gap in profile.known_gaps))
        self.assertEqual(profile.verifier["tooling"], "plain")
        self.assertGreater(profile.validation_hint_sec, 0)

    def test_vllm_classified_very_large_cpu(self) -> None:
        profile = runnability_report.profile_reference(BUNDLE, "vllm-deepseek-streaming")
        self.assertEqual(profile.image_size_class, "very-large")
        self.assertEqual(profile.compute, "cpu")

    def test_biped_flagged_large_and_pytest_ctrf(self) -> None:
        profile = runnability_report.profile_reference(BUNDLE, "biped-contact-dynamics")
        self.assertEqual(profile.image_size_class, "large")
        self.assertEqual(profile.verifier["tooling"], "pytest-ctrf")

    def test_profiles_serialize_to_json(self) -> None:
        profile = runnability_report.profile_reference(BUNDLE, "wal-recovery-ordering")
        payload = runnability_report.asdict(profile)
        json.dumps(payload)
        self.assertEqual(payload["reference"], "wal-recovery-ordering")

    def test_missing_copy_source_is_reported_in_profile(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for sub in ("t", "c", "d", "r"):
                (root / sub).mkdir(parents=True, exist_ok=True)
            task = root / "t" / "wr"
            (task / "environment").mkdir(parents=True)
            (task / "environment" / "Dockerfile").write_text(
                "FROM example/image\nCOPY missing.bin /app/missing.bin\n",
                encoding="utf-8",
            )
            profile = runnability_report.profile_reference(root, "wal-recovery-ordering")
            dockerfile = next(
                entry for entry in profile.dockerfiles if entry.path == "environment/Dockerfile"
            )
            self.assertFalse(dockerfile.copy_sources[0].exists)
            self.assertIn("missing", dockerfile.copy_sources[0].note)


if __name__ == "__main__":
    unittest.main()
