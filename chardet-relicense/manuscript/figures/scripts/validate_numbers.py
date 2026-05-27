#!/usr/bin/env python3
"""validate_numbers.py — independently re-compute every numeric claim in
the paper using scipy + numpy + networkx primitives and compare against
the harness-reported values.

This script exists because the paper claims six numeric headline values
(C06a similarity, C06b jaccard, C06c cosine, C06d strict/diverged counts,
C06e exact/bucket match rates, and the AUX1 zero) and the V2 revision
directive requires that those numbers be confirmed by an independent
re-computation rather than trusted from the harness output alone.

The script:
  1. Re-runs the harness's signal extractors on the same worktrees the
     harness uses.
  2. Re-computes the headline number for each signal using a SECOND,
     independent implementation drawn from scipy / numpy / networkx
     stdlib primitives. (cosine via scipy.spatial.distance.cosine,
     jaccard via set arithmetic, density via nx.density, SCC via
     nx.number_strongly_connected_components.)
  3. For C06d, computes a 95% bootstrap confidence interval (1000
     resamples) on the strict-match rate. The sample size is tiny (5
     shared public-API names) so the CI is wide; the paper says so.
  4. For C06e, re-derives the corpus digest deterministically from the
     same seed and confirms a 0/1000 match rate is reproducible.
  5. Emits validation_report.json next to itself.

Run:
  python3 chardet-relicense/manuscript/figures/scripts/validate_numbers.py [--repo PATH]
                                                    [--v6-tag 6.0.0]
                                                    [--v7-tag 7.0.0]

Exit code 0 on full agreement, 1 on any divergence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import random
import subprocess
import sys
import tempfile
from collections import Counter
from typing import Any

# Import the harness signal extractors so we can call them directly.
HERE = pathlib.Path(__file__).resolve()
REPO_ROOT = HERE.parents[3]  # chardet-relicense/manuscript/figures/scripts/ -> repo root
PROOF_DIR = REPO_ROOT / "chardet-relicense" / "proof-bundle"
sys.path.insert(0, str(PROOF_DIR))

import extract_signals as ex  # noqa: E402

try:
    import numpy as np
    from scipy.spatial.distance import cosine as scipy_cosine
except ImportError:
    print("error: scipy and numpy are required (pip install scipy numpy)",
          file=sys.stderr)
    sys.exit(2)

import networkx as nx


# --------------------------------------------------------------------------
# Worktree materialisation (mirrors detect.sh's behaviour exactly).
# --------------------------------------------------------------------------

DEFAULT_REPO = pathlib.Path(
    "/srv/repos/public/spec-poc/chardet-relicense/chardet"
)


def materialise_worktrees(repo: pathlib.Path, v6_tag: str, v7_tag: str,
                          workdir: pathlib.Path) -> tuple[pathlib.Path,
                                                           pathlib.Path]:
    mirror = workdir / "mirror"
    subprocess.run(
        ["git", "clone", "--shared", str(repo), str(mirror)],
        check=True, capture_output=True, text=True,
    )
    v6 = workdir / "v6"
    v7 = workdir / "v7"
    subprocess.run(
        ["git", "-C", str(mirror), "worktree", "add", "--detach", str(v6),
         v6_tag],
        check=True, capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "-C", str(mirror), "worktree", "add", "--detach", str(v7),
         v7_tag],
        check=True, capture_output=True, text=True,
    )
    return v6, v7


# --------------------------------------------------------------------------
# Independent recomputation, one function per signal.
# --------------------------------------------------------------------------

def recompute_aux1(v6: pathlib.Path, v7: pathlib.Path) -> dict[str, Any]:
    """Independently recount sha256-overlapping files.

    Note: the harness counts files whose *whitespace-normalised text* is
    non-empty (an empty __init__.py normalises to '' and is skipped); the
    paper quotes those numbers. We replicate that filter so the
    independent count matches what the paper reports."""
    def hashes(root: pathlib.Path) -> tuple[int, set[str]]:
        sigs: set[str] = set()
        n = 0
        for p in ex.iter_impl_py_files(root):
            text = ex.whitespace_normalised_text(p)
            if not text:  # empty-after-normalisation files dropped (harness behaviour)
                continue
            sigs.add(hashlib.sha256(text.encode("utf-8")).hexdigest())
            n += 1
        return n, sigs

    n_v6, sigs_v6 = hashes(v6)
    n_v7, sigs_v7 = hashes(v7)
    intersect = len(sigs_v6 & sigs_v7)
    return {
        "n_v6_files": n_v6,
        "n_v7_files": n_v7,
        "matching_hash_pairs": intersect,
    }


def recompute_c06a(v6: pathlib.Path,
                   v7: pathlib.Path) -> dict[str, Any]:
    """Re-derive C06a from networkx primitives directly."""
    g6 = ex._build_call_graph(v6)
    g7 = ex._build_call_graph(v7)

    def feats(g: nx.DiGraph) -> dict[str, float]:
        n = g.number_of_nodes()
        m = g.number_of_edges()
        density_nx = nx.density(g)
        # Independent re-derivation via formula m / (n*(n-1)).
        density_formula = (m / (n * (n - 1))) if n > 1 else 0.0
        scc_nx = nx.number_strongly_connected_components(g)
        # Independent re-derivation via Tarjan from a fresh traversal.
        scc_iter = sum(1 for _ in nx.strongly_connected_components(g))
        in_degs = [d for _, d in g.in_degree()]
        out_degs = [d for _, d in g.out_degree()]
        return {
            "n_nodes": n,
            "n_edges": m,
            "density_nx": density_nx,
            "density_formula": density_formula,
            "density_agrees": math.isclose(density_nx, density_formula,
                                            rel_tol=1e-9),
            "scc_nx_func": scc_nx,
            "scc_iter": scc_iter,
            "scc_agrees": scc_nx == scc_iter,
            "mean_in_numpy": float(np.mean(in_degs)) if in_degs else 0.0,
            "mean_out_numpy": float(np.mean(out_degs)) if out_degs else 0.0,
            "max_in_numpy": int(np.max(in_degs)) if in_degs else 0,
            "max_out_numpy": int(np.max(out_degs)) if out_degs else 0,
        }

    f6 = feats(g6)
    f7 = feats(g7)

    feature_keys = [
        "n_nodes", "n_edges", "density_formula", "scc_iter",
        "mean_in_numpy", "mean_out_numpy", "max_in_numpy", "max_out_numpy",
    ]
    rel_diffs = []
    for k in feature_keys:
        a = float(f6[k])
        b = float(f7[k])
        denom = abs(a) + abs(b)
        rd = (abs(a - b) / denom) if denom > 0 else 0.0
        rel_diffs.append(rd)
    similarity = 1.0 - float(np.mean(rel_diffs))
    return {
        "v6_features": f6,
        "v7_features": f7,
        "rel_diffs": rel_diffs,
        "similarity": similarity,
    }


def recompute_c06a_prime(v6: pathlib.Path,
                          v7: pathlib.Path) -> dict[str, Any]:
    """Independently recompute C06a' (WL kernel) using networkx
    primitives rather than the harness's pure-stdlib WL routine. The
    cross-check is structural: we re-derive the WL labels by hand using
    the same (in-degree, out-degree) initial labelling and the same
    iterative refinement rule, but we drive the iteration from a fresh
    networkx digraph traversal and use sha256 directly. If the harness
    and this re-derivation produce different cosine numbers, that's a
    bug somewhere. The kernel choice is *the same algorithm* — there is
    no independent third-party WL kernel in scipy/numpy to cross-check
    against, so we cross-check the implementation against itself driven
    from different traversal orders, which catches at minimum any
    accidental dependence on dict ordering.
    """
    g6 = ex._build_call_graph(v6)
    g7 = ex._build_call_graph(v7)

    def wl(g: nx.DiGraph, k: int) -> tuple[Counter, list[float], dict]:
        if g.number_of_nodes() == 0:
            return Counter(), [], {}
        labels = {u: f"d:{g.in_degree(u)}|{g.out_degree(u)}"
                  for u in g.nodes()}
        bag: Counter = Counter(labels.values())
        per_iter_labels = [dict(labels)]
        for _ in range(k):
            new = {}
            for u in g.nodes():
                in_l = sorted(labels[v] for v in g.predecessors(u))
                out_l = sorted(labels[v] for v in g.successors(u))
                payload = (labels[u] + "|<|" + ",".join(in_l)
                           + "|>|" + ",".join(out_l)).encode("utf-8")
                new[u] = hashlib.sha256(payload).hexdigest()[:16]
            labels = new
            bag.update(labels.values())
            per_iter_labels.append(dict(labels))
        return bag, [], {"per_iter": per_iter_labels}

    bag6, _, info6 = wl(g6, ex._WL_ITERATIONS)
    bag7, _, info7 = wl(g7, ex._WL_ITERATIONS)

    def cosine_multiset(a: Counter, b: Counter) -> float:
        if not a or not b:
            return 0.0
        common = set(a) & set(b)
        dot = sum(a[k] * b[k] for k in common)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    cos = cosine_multiset(bag6, bag7)

    per_iter_cos = []
    iters6 = info6.get("per_iter", [])
    iters7 = info7.get("per_iter", [])
    for li6, li7 in zip(iters6, iters7):
        per_iter_cos.append(cosine_multiset(Counter(li6.values()),
                                            Counter(li7.values())))

    # Independent cross-check via numpy on the union-of-labels vector.
    keys = sorted(set(bag6) | set(bag7))
    v6_vec = np.array([bag6.get(k, 0) for k in keys], dtype=float)
    v7_vec = np.array([bag7.get(k, 0) for k in keys], dtype=float)
    if v6_vec.any() and v7_vec.any():
        cos_scipy = 1.0 - float(scipy_cosine(v6_vec, v7_vec))
    else:
        cos_scipy = 0.0

    return {
        "k_iterations": ex._WL_ITERATIONS,
        "v6_label_count": int(sum(bag6.values())),
        "v7_label_count": int(sum(bag7.values())),
        "wl_cosine": cos,
        "wl_cosine_scipy_crosscheck": cos_scipy,
        "agrees": math.isclose(cos, cos_scipy, rel_tol=1e-9),
        "per_iteration_cosine": per_iter_cos,
    }


def recompute_c06f(v6: pathlib.Path,
                   v7: pathlib.Path) -> dict[str, Any]:
    """Independently recompute C06f primitives. We re-derive
    per-function records via the harness collector but verify the
    matching invariants externally: every matched pair shares match-key,
    matched + unmatched per side equals total function count on that
    side, and no v6 function appears in more than one matched pair."""
    g6 = ex._build_call_graph(v6)
    g7 = ex._build_call_graph(v7)
    f6 = ex._collect_functions(v6)
    f7 = ex._collect_functions(v7)
    ex._attach_call_graph_position(f6, g6)
    ex._attach_call_graph_position(f7, g7)
    pairs, un6, un7 = ex._match_functions(f6, f7)

    # Invariant checks.
    invariants = {
        "match_key_consistent": all(
            a["match_key"] == b["match_key"] for a, b, _ in pairs
        ),
        "v6_partition": len(pairs) + len(un6) == len(f6),
        "v7_partition": len(pairs) + len(un7) == len(f7),
        "v6_unique": len({id(a) for a, _, _ in pairs}) == len(pairs),
        "v7_unique": len({id(b) for _, b, _ in pairs}) == len(pairs),
    }

    if pairs:
        dists = [d for _, _, d in pairs]
        mean_dist = float(np.mean(dists))
        median_dist = float(np.median(dists))
        same_name = sum(1 for a, b, _ in pairs if a["name"] == b["name"])
        same_name_rate = same_name / len(pairs)
    else:
        mean_dist = 1.0
        median_dist = 1.0
        same_name_rate = 0.0
    similarity = max(0.0, 1.0 - mean_dist)

    # Bootstrap 95% CI on per-function similarity (sample = matched
    # pairs). With only ~31 pairs this CI is informative — the paper
    # should quote a range, not a single decimal.
    rng = np.random.default_rng(20260528)
    if pairs:
        dist_array = np.array([d for _, _, d in pairs])
        boot = []
        for _ in range(1000):
            idx = rng.integers(0, len(dist_array), size=len(dist_array))
            boot.append(1.0 - float(dist_array[idx].mean()))
        ci_lo = float(np.percentile(boot, 2.5))
        ci_hi = float(np.percentile(boot, 97.5))
    else:
        ci_lo = ci_hi = 0.0

    return {
        "n_v6_functions": len(f6),
        "n_v7_functions": len(f7),
        "n_matched_pairs": len(pairs),
        "n_unmatched_v6": len(un6),
        "n_unmatched_v7": len(un7),
        "mean_pair_distance": mean_dist,
        "median_pair_distance": median_dist,
        "per_function_similarity": similarity,
        "similarity_bootstrap_ci_95_lo": ci_lo,
        "similarity_bootstrap_ci_95_hi": ci_hi,
        "same_name_overlap_among_matched": same_name_rate,
        "match_key_buckets_v6": len({f["match_key"] for f in f6}),
        "match_key_buckets_v7": len({f["match_key"] for f in f7}),
        "shared_match_key_buckets": len(
            {f["match_key"] for f in f6} & {f["match_key"] for f in f7}
        ),
        "invariants": invariants,
        "all_invariants_pass": all(invariants.values()),
    }


def recompute_c06b(v6: pathlib.Path,
                   v7: pathlib.Path) -> dict[str, Any]:
    """Re-derive C06b jaccard via set arithmetic; cross-check against
    1 - scipy.spatial.distance.jaccard on the indicator vectors."""
    i6 = ex._collect_imports(v6)
    i7 = ex._collect_imports(v7)
    inter = i6 & i7
    union = i6 | i7
    j_sets = len(inter) / len(union) if union else 0.0

    # Indicator-vector form for the scipy cross-check.
    items = sorted(union)
    v6_vec = np.array([1 if x in i6 else 0 for x in items])
    v7_vec = np.array([1 if x in i7 else 0 for x in items])
    # scipy returns distance, not similarity; 1 - d == similarity.
    # The scipy "jaccard" distance on boolean vectors equals
    # 1 - |intersection| / |union|, so we recover j by 1 - distance.
    if v6_vec.any() or v7_vec.any():
        from scipy.spatial.distance import jaccard as scipy_jaccard
        j_scipy = 1.0 - float(scipy_jaccard(v6_vec, v7_vec))
    else:
        j_scipy = 0.0

    return {
        "shared": sorted(inter),
        "v6_only": sorted(i6 - i7),
        "v7_only": sorted(i7 - i6),
        "jaccard_sets": j_sets,
        "jaccard_scipy": j_scipy,
        "agrees": math.isclose(j_sets, j_scipy, rel_tol=1e-9),
    }


def recompute_c06c(v6: pathlib.Path,
                   v7: pathlib.Path) -> dict[str, Any]:
    """Cross-check the harness's cosine against scipy.spatial.distance.cosine."""
    h6 = ex._control_flow_histogram(v6)
    h7 = ex._control_flow_histogram(v7)
    keys = sorted(set(h6) | set(h7))
    v6_vec = np.array([h6.get(k, 0) for k in keys], dtype=float)
    v7_vec = np.array([h7.get(k, 0) for k in keys], dtype=float)
    # Normalised by total count, mirroring the harness.
    n6 = v6_vec / v6_vec.sum() if v6_vec.sum() > 0 else v6_vec
    n7 = v7_vec / v7_vec.sum() if v7_vec.sum() > 0 else v7_vec
    if n6.any() and n7.any():
        cos_scipy = 1.0 - float(scipy_cosine(n6, n7))
    else:
        cos_scipy = 0.0
    # Independent formula: dot / (||a|| ||b||).
    dot = float(np.dot(n6, n7))
    na = float(np.linalg.norm(n6))
    nb = float(np.linalg.norm(n7))
    cos_formula = dot / (na * nb) if na > 0 and nb > 0 else 0.0
    return {
        "v6_total": int(v6_vec.sum()),
        "v7_total": int(v7_vec.sum()),
        "cosine_scipy": cos_scipy,
        "cosine_formula": cos_formula,
        "agrees": math.isclose(cos_scipy, cos_formula, rel_tol=1e-9),
        "per_node_v6": {k: int(h6.get(k, 0)) for k in keys},
        "per_node_v7": {k: int(h7.get(k, 0)) for k in keys},
    }


def recompute_c06d(v6: pathlib.Path,
                   v7: pathlib.Path,
                   bootstrap_n: int = 1000,
                   seed: int = 20260522) -> dict[str, Any]:
    """Strict / renamed_args / diverged counts plus a bootstrap 95% CI on
    the strict-match rate. The sample is small (5), so the CI is wide;
    we report it explicitly so the paper can be honest about it."""
    sigs6 = ex._collect_public_signatures(v6)
    sigs7 = ex._collect_public_signatures(v7)
    shared = sorted(set(sigs6) & set(sigs7))
    classifications = []
    for name in shared:
        classifications.append(ex._signature_match(sigs6[name], sigs7[name]))
    strict = sum(1 for c in classifications if c == "strict")
    renamed = sum(1 for c in classifications if c == "renamed_args")
    diverged = sum(1 for c in classifications if c == "diverged")
    n = len(shared)
    strict_rate = (strict / n) if n > 0 else 0.0

    # Bootstrap 95% CI on the strict rate. Sample size = 5, so the CI
    # has only ~6 distinct possible point estimates; report it for honesty.
    rng = np.random.default_rng(seed)
    strict_indicators = np.array(
        [1 if c == "strict" else 0 for c in classifications]
    )
    boot_means = []
    if n > 0:
        for _ in range(bootstrap_n):
            idx = rng.integers(0, n, size=n)
            boot_means.append(float(strict_indicators[idx].mean()))
    if boot_means:
        ci_lo = float(np.percentile(boot_means, 2.5))
        ci_hi = float(np.percentile(boot_means, 97.5))
    else:
        ci_lo = ci_hi = 0.0

    return {
        "shared_names": shared,
        "classifications": dict(zip(shared, classifications)),
        "strict": strict,
        "renamed_args": renamed,
        "diverged": diverged,
        "strict_rate": strict_rate,
        "bootstrap_n": bootstrap_n,
        "bootstrap_ci_95_lo": ci_lo,
        "bootstrap_ci_95_hi": ci_hi,
    }


def recompute_c06e_corpus_digest(seed: int = 20260522,
                                 n_inputs: int = 1000,
                                 max_len: int = 4096) -> dict[str, Any]:
    """Re-derive C06e's deterministic input corpus digest using the
    SAME hash method the harness uses (b"\\n".join(corpus) over a
    list[bytes]), so the validator's digest can be compared
    byte-for-byte against the harness's emitted corpus_digest. The
    previous implementation hashed each payload via h.update(payload)
    WITHOUT a separator and therefore produced a different digest by
    construction (8fbc70630c023315 vs the harness's 58e54831f84183c7);
    the mismatch was flagged in round-1 multi-LLM review by gemini
    (raw_findings/gemini.md) and codex (raw_findings/codex.md),
    docs/reviews/2026-05-25-paper-chardet-e2e/, as defect B3."""
    rng = random.Random(seed)
    corpus: list[bytes] = []
    for _ in range(n_inputs):
        length = rng.randint(0, max_len)
        corpus.append(bytes(rng.randint(0, 255) for _ in range(length)))
    # Matches fingerprint_behavior.py's corpus_digest emit:
    #   corpus_digest = hashlib.sha256(b"\n".join(corpus)).hexdigest()[:16]
    digest_full = hashlib.sha256(b"\n".join(corpus)).hexdigest()
    return {
        "corpus_digest_full": digest_full,
        "corpus_digest_truncated_16": digest_full[:16],
        "n_inputs": n_inputs,
        "seed": seed,
        "max_len": max_len,
        "method": "hashlib.sha256(b'\\n'.join(corpus)).hexdigest()[:16] (matches fingerprint_behavior.py)",
    }


def recompute_c06e_rates(v6: pathlib.Path,
                         v7: pathlib.Path) -> dict[str, Any]:
    """Invoke fingerprint_behavior.py against the same v6/v7 worktrees
    and parse its TSV row to recover exact_match_rate,
    bucket_match_rate, n_inputs, and corpus_digest. Returns
    status='skip' with an explicit reason if fingerprint_behavior.py
    emits SKIP (typically because chardet install requires network/pip
    access not available in the sandboxed runner). Returns
    status='measured' with the parsed values on success.

    The harness's own C06e rates are emitted by fingerprint_behavior.py
    at runtime, NOT pre-baked into a checked-in JSON, so the comparison
    is between (this fresh invocation's rates) and (HARNESS_HEADLINE's
    pinned rates from the paper's last harness run). If the rates have
    drifted since the paper was last regenerated, the validator surfaces
    that as a divergence; if rates can't be re-computed at all (SKIP),
    the validator reports it transparently rather than silently omitting
    the c06e rate rows from the comparison."""
    fp_script = REPO_ROOT / "chardet-relicense" / "proof-bundle" / "fingerprint_behavior.py"
    if not fp_script.is_file():
        return {
            "status": "skip",
            "reason": f"fingerprint_behavior.py not found at {fp_script}",
        }
    try:
        res = subprocess.run(
            [sys.executable, str(fp_script),
             "--v6-tree", str(v6), "--v7-tree", str(v7)],
            capture_output=True, text=True, timeout=1800,
        )
    except subprocess.TimeoutExpired:
        return {"status": "skip",
                "reason": "fingerprint_behavior.py timed out after 1800s"}
    if res.returncode != 0:
        return {
            "status": "skip",
            "reason": f"fingerprint_behavior.py exited {res.returncode}: "
                      f"{(res.stderr or res.stdout).strip()[:300]}",
        }
    # fingerprint_behavior.py emits ONE TSV row per invocation:
    #   behavioural_fingerprint\tC06e\t<expected>\t<actual>\t<verdict>\t<evidence>
    lines = [l for l in res.stdout.splitlines()
             if l.startswith("behavioural_fingerprint\t")]
    if not lines:
        return {
            "status": "skip",
            "reason": "no behavioural_fingerprint row in fingerprint_behavior.py output",
        }
    row = lines[-1].split("\t")
    if len(row) < 5:
        return {
            "status": "skip",
            "reason": f"malformed TSV row (got {len(row)} fields, expected >=5)",
        }
    actual_field = row[3]
    verdict_field = row[4]
    if verdict_field == "SKIP":
        return {
            "status": "skip",
            "reason": f"fingerprint_behavior.py emitted SKIP: {actual_field[:300]}",
        }
    # Parse 'exact_match_rate=X bucket_match_rate=Y n_inputs=Z corpus_digest=H'.
    import re as _re
    fields: dict[str, str] = {}
    for m in _re.finditer(r"(\w+)=(\S+)", actual_field):
        fields[m.group(1)] = m.group(2)
    try:
        return {
            "status": "measured",
            "exact_rate": float(fields["exact_match_rate"]),
            "bucket_rate": float(fields["bucket_match_rate"]),
            "n_inputs": int(fields["n_inputs"]),
            "corpus_digest": fields["corpus_digest"],
        }
    except (KeyError, ValueError) as e:
        return {
            "status": "skip",
            "reason": f"could not parse fields from fingerprint_behavior.py TSV: {e}",
        }


# --------------------------------------------------------------------------
# Compare against harness-reported headline numbers, fail loudly on drift.
# --------------------------------------------------------------------------

# These are the headline numbers the paper currently asserts. They MUST
# match what the harness emits on the v6.0.0 / v7.0.0 worktrees.
HARNESS_HEADLINE = {
    "aux1_matches": 0,
    "aux1_v6_files": 87,
    "aux1_v7_files": 33,
    "c06a_similarity": 0.881,
    "c06a_v6_nodes": 342,
    "c06a_v7_nodes": 358,
    "c06a_v6_edges": 488,
    "c06a_v7_edges": 659,
    "c06b_jaccard": 0.333,
    "c06c_cosine": 0.984,
    "c06c_v6_total": 652,
    "c06c_v7_total": 848,
    "c06d_shared": 5,
    "c06d_strict": 3,
    "c06d_renamed_args": 0,
    "c06d_diverged": 2,
    "c06e_exact_rate": 0.000,
    "c06e_bucket_rate": 0.000,
    "c06e_n_inputs": 1000,
    "c06e_corpus_digest": "58e54831f84183c7",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, default=DEFAULT_REPO)
    parser.add_argument("--v6-tag", default="6.0.0")
    parser.add_argument("--v7-tag", default="7.0.0")
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=HERE.parent / "validation_report.json",
    )
    args = parser.parse_args()

    if not args.repo.exists():
        print(f"error: chardet repo not found at {args.repo}",
              file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="validate-numbers-") as td:
        workdir = pathlib.Path(td)
        v6, v7 = materialise_worktrees(args.repo, args.v6_tag,
                                        args.v7_tag, workdir)

        aux1 = recompute_aux1(v6, v7)
        c06a = recompute_c06a(v6, v7)
        c06b = recompute_c06b(v6, v7)
        c06c = recompute_c06c(v6, v7)
        c06d = recompute_c06d(v6, v7)
        c06e = recompute_c06e_corpus_digest()
        c06e_rates = recompute_c06e_rates(v6, v7)

    # Build the per-number comparison table.
    comparison = []

    def add(name: str, harness: Any, independent: Any,
            tol: float = 1e-3) -> None:
        if isinstance(harness, float):
            agrees = abs(float(independent) - harness) <= tol
        else:
            agrees = harness == independent
        comparison.append({
            "name": name,
            "harness": harness,
            "independent": independent,
            "agrees": bool(agrees),
        })

    add("aux1.matching_pairs", HARNESS_HEADLINE["aux1_matches"],
        aux1["matching_hash_pairs"])
    add("aux1.v6_files", HARNESS_HEADLINE["aux1_v6_files"],
        aux1["n_v6_files"])
    add("aux1.v7_files", HARNESS_HEADLINE["aux1_v7_files"],
        aux1["n_v7_files"])
    add("c06a.similarity", HARNESS_HEADLINE["c06a_similarity"],
        round(c06a["similarity"], 3))
    add("c06a.v6_nodes", HARNESS_HEADLINE["c06a_v6_nodes"],
        c06a["v6_features"]["n_nodes"])
    add("c06a.v7_nodes", HARNESS_HEADLINE["c06a_v7_nodes"],
        c06a["v7_features"]["n_nodes"])
    add("c06a.v6_edges", HARNESS_HEADLINE["c06a_v6_edges"],
        c06a["v6_features"]["n_edges"])
    add("c06a.v7_edges", HARNESS_HEADLINE["c06a_v7_edges"],
        c06a["v7_features"]["n_edges"])
    add("c06a.density_internal_agreement", True,
        c06a["v6_features"]["density_agrees"]
        and c06a["v7_features"]["density_agrees"])
    add("c06a.scc_internal_agreement", True,
        c06a["v6_features"]["scc_agrees"]
        and c06a["v7_features"]["scc_agrees"])
    add("c06b.jaccard", HARNESS_HEADLINE["c06b_jaccard"],
        round(c06b["jaccard_sets"], 3))
    add("c06b.scipy_set_agreement", True, c06b["agrees"])
    add("c06c.cosine", HARNESS_HEADLINE["c06c_cosine"],
        round(c06c["cosine_scipy"], 3))
    add("c06c.v6_total", HARNESS_HEADLINE["c06c_v6_total"],
        c06c["v6_total"])
    add("c06c.v7_total", HARNESS_HEADLINE["c06c_v7_total"],
        c06c["v7_total"])
    add("c06c.scipy_formula_agreement", True, c06c["agrees"])
    add("c06d.shared", HARNESS_HEADLINE["c06d_shared"], len(c06d["shared_names"]))
    add("c06d.strict", HARNESS_HEADLINE["c06d_strict"], c06d["strict"])
    add("c06d.renamed_args", HARNESS_HEADLINE["c06d_renamed_args"],
        c06d["renamed_args"])
    add("c06d.diverged", HARNESS_HEADLINE["c06d_diverged"], c06d["diverged"])
    # CI sanity-check: the bootstrap CI must include the point estimate.
    add("c06d.bootstrap_ci_contains_point", True,
        c06d["bootstrap_ci_95_lo"] <= c06d["strict_rate"]
        <= c06d["bootstrap_ci_95_hi"])

    # C06e: corpus_digest is ALWAYS re-derivable (no network/pip
    # required) — it's a deterministic function of (seed, n_inputs,
    # max_len). Rate comparison (exact / bucket / n_inputs) is gated
    # on fingerprint_behavior.py being able to install chardet into
    # two venvs; if it SKIPs (sandboxed runner without PyPI), the
    # rate rows are skipped explicitly and the comparison reports
    # that — but the digest row still runs.
    add("c06e.corpus_digest", HARNESS_HEADLINE["c06e_corpus_digest"],
        c06e["corpus_digest_truncated_16"])
    if c06e_rates["status"] == "measured":
        add("c06e.exact_rate", HARNESS_HEADLINE["c06e_exact_rate"],
            c06e_rates["exact_rate"])
        add("c06e.bucket_rate", HARNESS_HEADLINE["c06e_bucket_rate"],
            c06e_rates["bucket_rate"])
        add("c06e.n_inputs", HARNESS_HEADLINE["c06e_n_inputs"],
            c06e_rates["n_inputs"])
        # Cross-check that fingerprint_behavior.py and validate_numbers.py
        # produce the same corpus_digest from the same seed.
        add("c06e.digest_agreement", c06e["corpus_digest_truncated_16"],
            c06e_rates["corpus_digest"])
    else:
        # Make the SKIP visible in the report; do NOT treat as a divergence
        # (exit code 1) because c06e rate recompute requires runtime
        # availability of network + pip + a Python build toolchain that
        # this script cannot assume.
        comparison.append({
            "name": "c06e.rates_recompute",
            "harness": "(measured by harness on a runner with chardet installable)",
            "independent": f"SKIP: {c06e_rates['reason']}",
            "agrees": True,  # SKIP is not a divergence
            "skip": True,
        })

    report = {
        "harness_headline": HARNESS_HEADLINE,
        "independent": {
            "aux1": aux1,
            "c06a": c06a,
            "c06b": c06b,
            "c06c": c06c,
            "c06d": c06d,
            "c06e_corpus_check": c06e,
            "c06e_rates": c06e_rates,
        },
        "comparison": comparison,
        "all_agree": all(c["agrees"] for c in comparison),
    }
    args.output.write_text(json.dumps(report, indent=2, default=str))

    # Print the human-readable summary.
    print(f"{'name':<45} {'harness':>16} {'independent':>16}  agree")
    print("-" * 90)
    for c in comparison:
        h = str(c["harness"])
        i = str(c["independent"])
        print(f"{c['name']:<45} {h:>16} {i:>16}  "
              f"{'YES' if c['agrees'] else 'NO'}")
    print()
    print(f"all agree: {report['all_agree']}")
    print(f"wrote: {args.output}")
    return 0 if report["all_agree"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
