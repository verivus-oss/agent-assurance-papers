# Figure 2 caption proposal (v2, Phase 2 / Agent K)

For Phase 4's editor: a drop-in replacement for the `figures/fig2_topology_features.pdf`
caption currently in `main.tex` (around line 893–897).

## Proposed caption

> C06a call-graph topology features across the three v2 calibration pairs.
> Each subplot shows one of six topology features on its own linear y-axis,
> with grouped bars for v6/v7 (the headline pair), v5/v6 (routine same-project
> evolution), and v6/charset_normalizer (independent same-domain
> reimplementation); the left bar of each pair is side A, the right bar is
> side B. v7 is uniformly larger than v6 on every feature (more nodes, more
> edges, higher mean and max degree, slightly higher density), v5 is uniformly
> smaller than v6 on the same axes, and charset_normalizer sits below v6 on
> every feature except max out-degree. The per-feature pattern is consistent
> with the calibration narrative: structural growth between consecutive
> chardet majors looks similar in *shape* to a from-scratch independent
> rewrite of the same domain — neither pair shows a discriminating
> topology-feature signature on its own, which is precisely why C06f's
> per-function match rate, not C06a's bulk topology, ends up doing the
> discriminating work.

## Provenance & design notes (not for the printed caption)

**Path chosen: A (live extractor on all three pair worktrees).**

Reason: the `validation_report.v2.json` evidence string for C06a exposes only
four of the eight `_graph_topology()` features for v5/v6 and
v6/charset_normalizer (`density`, `sccs`, `mean_in_degree`, `max_in_degree`),
plus `nodes_a/b` and `edges_a/b` as separate JSON fields — six features
total. Materialising the four worktrees (chardet 5.0.0=21bc6be tag /
fbb2ec6 peeled, 6.0.0=8a4636b, 7.0.0=4b89d62, charset_normalizer 3.4.7=0f07891)
and re-running `extract_signals._build_call_graph` + `_graph_topology`
yields all eight features directly, byte-equivalent to the proof bundle's
own C06a path. This keeps the figure pipeline consistent with the v1
fig2 (which already shelled out to a live v6/v7 extractor run) and avoids
any reliance on parsing an evidence-string-formatted prose blob.

**Features rendered (6) and per-feature data ranges across the six graphs:**

| Feature        | Range          | Notes                                                                       |
|----------------|---------------:|------------------------------------------------------------------------------|
| nodes          | 288 – 358      | v5 < csn < v6 < v7                                                          |
| edges          | 348 – 659      | clean monotone for chardet majors; csn lower than v6                        |
| density        | 0.00403 – 0.00516 | narrow band (~28 % spread), shown to 4 decimals                          |
| mean degree    | 1.21 – 1.84    | one panel, see below                                                        |
| max in-degree  | 23 – 44        | v7 highest; csn lowest                                                      |
| max out-degree | 24 – 42        | v7 and csn ~tied at top; v5/v6 ~tied at bottom                              |

**Features dropped (2):**

* `sccs` — equals `nodes` for all six graphs (every function is its own SCC
  in a call graph with no recursion cycles), so the panel would visually
  duplicate the `nodes` panel without adding information.
* `mean_out_degree` — equals `mean_in_degree` by construction (sum of
  in-degrees = sum of out-degrees = |E|). The figure plots a single
  `mean degree` panel for both.

No feature value was fabricated. Every value in the figure is the direct
output of `extract_signals._graph_topology()` against the worktree
identified by the tag/SHA in `proof-bundle/witness.tsv` and reproduced
under `gen_figures.sh`'s tempdir.

## Phase 4 attention notes

* The `max out-degree` panel shows a striking asymmetry: v6 vs v7 jumps
  24→42 and v6 vs charset_normalizer jumps 24→40, but v5 vs v6 barely
  moves (25→24). This is the only feature where charset_normalizer
  *exceeds* chardet v6 — worth a sentence in the narrative if Section 4
  has room.
* No panel suffered axis-domination by one pair: every feature's range is
  within ~2× across the six graphs, so the per-subplot linear scaling
  reads cleanly. No log compression was needed.
* `density` is shown to four decimals because the cross-pair spread is
  ~28 % of the smallest value but the absolute numbers are tiny
  (~4–5e-3); the four-decimal labels preserve the v6/v7 0.0042 → 0.0052
  jump without rounding it to 0.00.
