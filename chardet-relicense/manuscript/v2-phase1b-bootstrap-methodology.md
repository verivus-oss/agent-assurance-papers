# Phase 1b: bootstrap confidence-interval methodology

**Status:** drop-in paragraph for Section 5 of the v2 chardet-relicense
manuscript. Phase 4's editor should integrate this into the prose
adjacent to Table 4 (the multi-pair calibration table).

**Branch:** `v2-phase1b-n` (worktree
`/srv/repos/external/verivus-oss/agent-assurance-papers/.claude/worktrees/agent-ab2ffb6d7365fe71d`).
**Seed:** `BOOTSTRAP_SEED = 20260528` (pin date 2026-05-28). Re-running
`validate_numbers.py --bootstrap-all-pairs` with this seed reproduces
the published CIs byte-for-byte.

---

## Drop-in paragraph (LaTeX-ready)

> All four structural-similarity headline numbers (C06a 8-feature
> call-graph similarity, C06a$'$ Weisfeiler-Lehman kernel cosine, C06c
> control-flow histogram cosine, C06f per-function shape similarity) are
> reported with 95\% percentile-bootstrap confidence intervals computed
> from 1000 resamples and the pinned random seed
> $20260528$. For C06a, C06a$'$, and C06c the resampling unit is the
> implementation file: on each bootstrap draw we sample $|A|$ files
> with replacement from side A's implementation file list, $|B|$ from
> side B's list (the two sides resampled independently), reconstruct
> each side's structural object (call graph, WL label multiset, or
> normalised control-flow histogram) from the union of sampled file
> contributions, and recompute the similarity score; the CI is the
> $\{2.5,97.5\}$ percentiles of the 1000 resampled scores. For C06f
> the resampling unit is the matched function pair: we resample
> $n_{\text{matched}}$ pairs with replacement from the post-matching
> pair list and recompute the mean pair distance. The C06d strict-rate
> CI from the v1 anchor is preserved unchanged
> (5-shared-symbols bootstrap; see Section~4); the four new CIs use
> the same percentile-bootstrap machinery. Choice of unit follows the
> structure of each signal: C06a/C06a$'$/C06c report per-codebase
> aggregates and the natural noise model is "which files happened to
> end up in this snapshot"; C06f reports a per-pair mean and the
> natural noise model is "which functions happened to match". A
> caveat applies to C06a$'$ on the two calibration pairs (v5/v6 and
> v6/charset\_normalizer): the WL multiset is sensitive to whole-file
> dropout, and bootstrap-with-replacement at $N=1000$ leaves
> $\approx 0.63N$ unique files per resample, biasing the CI's upper
> tail slightly below the point estimate. We retain the wider CI
> rather than tighten by switching to a subsample-without-replacement
> scheme; the qualitative ranking of pairs (v6/v7 lowest, v5/v6
> highest) is preserved across point estimates, lower bounds, and
> upper bounds. The percentile-bootstrap procedure inherits known
> small-sample limitations: for C06f the resampling unit is the
> matched function pair (n=31 for v6/v7), and for C06d the
> resampling unit is the shared-symbol set (n=5), both regimes
> where percentile CIs are known to under-cover the true
> confidence level near the [0,1] boundary; we use the percentile
> interval throughout for consistency rather than switching to BCa,
> and treat overlapping CIs as "not separated at 95%" rather than
> as a precise inference about the underlying signal.

---

## Implementation notes (for reviewers)

- All four bootstrap routines live in
  `chardet-relicense/manuscript/figures/scripts/validate_numbers.py`,
  alongside the pre-existing C06d strict-rate bootstrap and the in-line
  C06f v6/v7 CI from Phase 1a (B+P). The new functions follow the same
  pattern: `np.random.default_rng(seed)`, integer-index resampling with
  `rng.integers(0, n, size=n)`, percentile via `np.percentile`. The
  Phase-1a C06f v6/v7 CI is bit-equivalent to the Phase-1b CI for the
  same pair (both seeded `20260528`), confirming the new machinery
  reproduces the existing CI.

- Per-file structural contributions (functions+edges for the call graph;
  control-flow node-class Counters) are pre-extracted once per side and
  cached, so each bootstrap resample is $\sim 1$ms rather than the
  $\sim 1.3$s a fresh AST walk would cost. The pre-extraction is in
  `_per_file_call_graph_contributions` and
  `_per_file_control_flow_contributions`; both mirror the harness's
  in-place walks (`ex._build_call_graph` and
  `ex._control_flow_histogram`) and confirm that the sum of per-file
  contributions equals the harness's monolithic count (verified during
  development: 652 control-flow nodes for v6 either way).

- For the v6/v7 pair the C06f bootstrap CI emitted by Phase-1b matches
  the in-line CI emitted by `recompute_c06f` at line $\sim 320$ of
  `validate_numbers.py` to all printed digits ($[0.8865, 0.9357]$ vs
  $[0.8864929436, 0.9357127763]$). This is the consistency check the
  directive asked for: same seed, same algorithm, same answer.

- All twelve CIs are written to
  `chardet-relicense/manuscript/figures/scripts/validation_report.v2.json`
  under `independent.<signal>.bootstrap_ci_95.<pair>` with fields
  `{lower, upper, n_resamples, seed}` plus `n_files_a / n_files_b`
  (file-based bootstraps) or `n_matched_pairs` (function-pair
  bootstrap). The patch sidecar
  `validation_report.v2_patch.n.json` retains the same data in the
  per-Phase-1a-agent format the orchestrator expects.

## Calibration question (Phase-1b reporting back)

Does the v6/v7 (LGPL$\to$MIT) point estimate sit inside or outside
the calibration baselines' CIs?

- **C06a (8-feature call graph):** v6/v7 = $0.881 \in [0.74, 0.95]$;
  v5/v6 CI = $[0.79, 0.97]$; v6/cn CI = $[0.75, 0.95]$.
  v6/v7's point IS inside both calibration CIs, AND all three CIs
  overlap heavily. C06a does not separate v6/v7 from baseline.

- **C06a$'$ (WL kernel cosine):** v6/v7 = $0.587 \in [0.43, 0.69]$;
  v5/v6 CI = $[0.75, 0.89]$; v6/cn CI = $[0.48, 0.86]$. v6/v7's CI
  does NOT overlap with v5/v6's CI (a clean separation: v5/v6 lower
  bound 0.75 is well above v6/v7 upper bound 0.69). v6/v7's CI DOES
  overlap with v6/cn's CI ($[0.48, 0.69] \cap [0.48, 0.86]$ is
  nonempty). Interpretation: WL kernel separates v6/v7 from
  conventional-evolution v5/v6 cleanly, but cannot distinguish v6/v7
  from independent-codebase v6/cn — exactly the calibration outcome
  the v2 revision predicted ("the v1 'structural similarity' framing
  conflates near-identical evolution with independent-but-domain-shared
  redevelopment").

- **C06c (control-flow histogram):** All three CIs span $[0.94, 1.00]$.
  Wildly overlapping; the signal saturates on this metric for any
  same-domain encoding library.

- **C06f (per-function shape):** v6/v7 = $0.913 \in [0.89, 0.94]$;
  v5/v6 CI = $[0.97, 0.99]$ (clearly higher; conventional rewrite
  preserves per-function shape); v6/cn CI = $[0.75, 0.84]$ (clearly
  lower; independent codebase has visibly different per-function
  shapes). v6/v7 sits BETWEEN the two calibration baselines, and its
  CI overlaps with NEITHER. This is the cleanest single-signal
  calibration result in the v2 paper: per-function shape similarity
  ranks the three pairs in the order
  ($v6/cn < v6/v7 < v5/v6$) and the CIs are tight enough to
  establish the ranking with statistical confidence at 95\%.

The v6/v7 pair's structural similarity is therefore "between
conventional rewrite and independent same-domain redevelopment" under
C06f, "ambiguous between v6/v7 and v6/cn" under C06a$'$, and
"indistinguishable from either calibration baseline" under C06a and
C06c. The v1 paper's "notably high similarity" framing does not
survive the multi-pair calibration with CIs.
