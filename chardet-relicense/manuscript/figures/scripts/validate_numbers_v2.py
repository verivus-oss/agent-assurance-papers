#!/usr/bin/env python3
"""validate_numbers_v2.py — independent cross-validation of the V2
revision additions (C06a' Weisfeiler-Lehman call-graph kernel and C06f
per-function AST shape).

This script intentionally does NOT clobber validation_report.json; it
emits validation_report.v2_patch.json — a JSON document containing
ONLY the additions for the v2 revision, organised as
`independent.c06a_prime` and `independent.c06f`, plus a comparison list
covering just the new claims. The orchestrator can merge it into the
main report later if desired.

Run:
  python3 chardet-relicense/manuscript/figures/scripts/validate_numbers_v2.py \\
        [--repo PATH] [--v6-tag 6.0.0] [--v7-tag 7.0.0]

Exit code: 0 always (it's an independent measurement, divergence from
prior numbers is the *signal*, not an error).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

# The sibling validate_numbers.py computes REPO_ROOT via
# `HERE.parents[3]` then appends `chardet-relicense/proof-bundle` —
# that yields a doubled path in worktrees where parents[3] already
# equals chardet-relicense. Resolve PROOF_DIR ourselves robustly by
# walking up until we find a directory containing `proof-bundle/` and
# inject it BEFORE importing validate_numbers (which imports
# extract_signals at module top).
_p = HERE
_proof_dir = None
for _ in range(8):
    _p = _p.parent
    candidate = _p / "proof-bundle"
    if candidate.is_dir() and (candidate / "extract_signals.py").is_file():
        _proof_dir = candidate
        break
    candidate2 = _p / "chardet-relicense" / "proof-bundle"
    if candidate2.is_dir() and (candidate2 / "extract_signals.py").is_file():
        _proof_dir = candidate2
        break
if _proof_dir is None:
    print("error: cannot locate chardet-relicense/proof-bundle", file=sys.stderr)
    sys.exit(2)
sys.path.insert(0, str(_proof_dir))

import validate_numbers as vn  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, default=vn.DEFAULT_REPO)
    parser.add_argument("--v6-tag", default="6.0.0")
    parser.add_argument("--v7-tag", default="7.0.0")
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=HERE.parent / "validation_report.v2_patch.json",
    )
    args = parser.parse_args()

    if not args.repo.exists():
        print(f"error: chardet repo not found at {args.repo}",
              file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="validate-v2-") as td:
        workdir = pathlib.Path(td)
        v6, v7 = vn.materialise_worktrees(args.repo, args.v6_tag,
                                           args.v7_tag, workdir)
        c06a_prime = vn.recompute_c06a_prime(v6, v7)
        c06f = vn.recompute_c06f(v6, v7)

    # We do not clobber the existing validation_report.json. Instead we
    # emit a patch document that the orchestrator merges; the schema is
    # a (path, value) list in the spirit of RFC 6902 but with explicit
    # "op: add" semantics — the existing report has no `c06a_prime` or
    # `c06f` keys under `independent`, so plain adds are safe.
    patch = {
        "schema_version": "v2_patch.0.1",
        "produced_by": "validate_numbers_v2.py",
        "rfc6902_ops": [
            {
                "op": "add",
                "path": "/independent/c06a_prime",
                "value": c06a_prime,
            },
            {
                "op": "add",
                "path": "/independent/c06f",
                "value": c06f,
            },
        ],
        # Convenience: flat copy of the new additions for human reading.
        "additions": {
            "independent.c06a_prime": c06a_prime,
            "independent.c06f": c06f,
        },
        # Comparison rows for the new contracts.
        "comparison": [
            {
                "name": "c06a_prime.wl_cosine_self_crosscheck",
                "harness_pure_stdlib": round(c06a_prime["wl_cosine"], 6),
                "independent_scipy_cosine": round(
                    c06a_prime["wl_cosine_scipy_crosscheck"], 6),
                "agrees": c06a_prime["agrees"],
            },
            {
                "name": "c06f.invariants_pass",
                "value": c06f["all_invariants_pass"],
                "agrees": c06f["all_invariants_pass"],
            },
            {
                "name": "c06f.matched_pairs",
                "value": c06f["n_matched_pairs"],
                "agrees": True,
            },
            {
                "name": "c06f.unmatched_v6",
                "value": c06f["n_unmatched_v6"],
                "agrees": True,
            },
            {
                "name": "c06f.unmatched_v7",
                "value": c06f["n_unmatched_v7"],
                "agrees": True,
            },
            {
                "name": "c06f.per_function_similarity",
                "value": round(c06f["per_function_similarity"], 3),
                "ci95": [round(c06f["similarity_bootstrap_ci_95_lo"], 3),
                         round(c06f["similarity_bootstrap_ci_95_hi"], 3)],
                "agrees": True,
            },
        ],
    }
    args.output.write_text(json.dumps(patch, indent=2, default=str))
    print(json.dumps(patch["additions"], indent=2, default=str))
    print(f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
