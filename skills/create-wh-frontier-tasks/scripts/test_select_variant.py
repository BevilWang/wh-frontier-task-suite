#!/usr/bin/env python3
"""Tests for deterministic design-variant sampling."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import select_variant
from validate_reference_bundle import TASKS

POOLS = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "references"
        / "design-pools.json"
    ).read_text(encoding="utf-8")
)


class SelectVariantTest(unittest.TestCase):
    def test_all_references_have_valid_pools(self) -> None:
        self.assertEqual(set(POOLS), set(TASKS))
        for reference, data in POOLS.items():
            variants = [entry["id"] for entry in data["pool"]]
            self.assertGreaterEqual(len(variants), 3, reference)
            self.assertEqual(len(variants), len(set(variants)), reference)
            self.assertTrue(all(entry["id"] and entry["direction"] for entry in data["pool"]))

    def test_sampling_is_deterministic_and_in_pool(self) -> None:
        for reference in POOLS:
            first = select_variant.select_variant(reference, "abc123")
            second = select_variant.select_variant(reference, "abc123")
            self.assertEqual(first, second)
            pool_ids = [entry["id"] for entry in POOLS[reference]["pool"]]
            self.assertIn(first, pool_ids)

    def test_different_seeds_spread_across_pool(self) -> None:
        chosen = {
            select_variant.select_variant("wal-recovery-ordering", seed)
            for seed in ("s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8")
        }
        self.assertGreaterEqual(len(chosen), 2)

    def test_unknown_variant_is_rejected(self) -> None:
        variants = select_variant.variants_for(POOLS, "wal-recovery-ordering")
        with self.assertRaises(SystemExit):
            select_variant.describe(variants, "not-a-variant")

    def test_unknown_reference_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            select_variant.variants_for(POOLS, "no-such-reference")


if __name__ == "__main__":
    unittest.main()
