#!/usr/bin/env python3
"""Deterministically select a design direction family for a reference.

Each reference has a pool of mutually distinct design-direction families (see
references/design-pools.json). Repeated runs of the same reference tend to
converge to the same ideas, so every run should pick one family and design
within it. This script samples a family deterministically from a seed, so a
run can be reproduced exactly, or validates an explicitly supplied family.

Usage:

    python scripts/select_variant.py --reference REFERENCE [--seed SEED]
    python scripts/select_variant.py --reference REFERENCE --variant ID
    python scripts/select_variant.py --reference REFERENCE --seed SEED --json

If --seed is omitted a fresh random seed is generated and printed, so the
caller can record it in the submission and pipeline state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import sys
from pathlib import Path

POOLS_PATH = Path(__file__).resolve().parents[1] / "references" / "design-pools.json"


def load_pools(path: Path = POOLS_PATH) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read design pools {path}: {exc}") from exc


def variants_for(pools: dict, reference: str) -> list[dict]:
    if reference not in pools:
        raise SystemExit(f"unsupported reference: {reference}")
    pool = pools[reference].get("pool", [])
    if not pool:
        raise SystemExit(f"design pool for {reference} is empty")
    return pool


def select_variant(reference: str, seed: str, pools: dict | None = None) -> str:
    variants = variants_for(pools or load_pools(), reference)
    digest = hashlib.sha256(f"{reference}:{seed}".encode("utf-8")).hexdigest()
    index = int(digest[:8], 16) % len(variants)
    return variants[index]["id"]


def describe(variants: list[dict], variant_id: str) -> dict:
    for variant in variants:
        if variant["id"] == variant_id:
            return variant
    raise SystemExit(
        f"unknown variant {variant_id!r}; choose from: {', '.join(v['id'] for v in variants)}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--seed", help="deterministic sampling seed; random if omitted")
    parser.add_argument("--variant", help="explicit family id instead of sampling")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    pools = load_pools()
    variants = variants_for(pools, args.reference)
    seed = args.seed
    if args.variant:
        variant = describe(variants, args.variant)
    else:
        if seed is None:
            seed = secrets.token_hex(8)
        variant = describe(variants, select_variant(args.reference, seed, pools))

    result = {
        "reference": args.reference,
        "seed": seed,
        "variant": variant["id"],
        "direction": variant["direction"],
        "pool": [entry["id"] for entry in variants],
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"reference : {result['reference']}")
        print(f"seed      : {result['seed']}")
        print(f"variant   : {result['variant']}")
        print(f"direction : {result['direction']}")
        print(f"pool      : {', '.join(result['pool'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
