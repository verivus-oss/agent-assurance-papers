# Lineage + per-method renaming-invariant trace — granular record (input to next version)

Date: 2026-05-29. Tooling: `sqry 16.0.6` (indexed with `--include-high-cost`),
`git 2.51.0`, Python 3.13 `ast`. Author harness: Claude Code.

Purpose: capture every datum from the universalchardet→chardet→charset_normalizer
lineage investigation and the per-method renaming-invariant structural trace, at
maximum granularity, so a next version of the paper / harness / sqry can build on
it without re-deriving. **No number here is from memory; each is from a tool run
recorded in this session.** Scripts that reproduce the per-method results are in
`scripts/`.

---

## 0. Headline findings (TL;DR)

1. **chardet IS a port of Mozilla `universalchardet`** — confirmed against the
   *genuine Mozilla C++ source* (not just a proxy): class taxonomy is identical
   modulo the `ns` prefix; several analysis classes byte-identical; LGPL inherited.
2. **charset_normalizer is independent of that lineage** — 0 shared taxonomy
   symbols at first release and today; different paradigm (mess/coherence probing).
   Its only chardet contact is a `legacy detect()` API shim + benchmarks.
3. **chardet conserved the Mozilla architecture for 20 years (1.0→6.0) then broke
   it at the v7 LLM rewrite** — taxonomy markers 26→26→22→**1**; call-graph
   connectivity density 1.60→2.17→**1.20**; flat package → layered `pipeline/`.
4. **Per-method (top 50% of v6 methods, identifier-blind): the v7 rewrite is a
   genuine re-architecture, not a paraphrase.** Of the 14 load-bearing v6 methods
   (cyclomatic ≥ 8 — `feed`, `close`, `get_confidence`, distribution `feed`,
   prober feeds), **0 have a structural twin in v7.** Strict-gated twin rate 19%
   (all trivial boilerplate); naive CF-cosine gives a **false** 80%. **Invariant
   across coverage (50/80/100%) AND direction: load-bearing-band twin = 0% in both
   v6->v7 and v7->v6** — v7's new pipeline functions have no v6 origin either.
5. **Methodological lesson (load-bearing for the next harness): gating is
   everything.** Same per-method trace yields **80% / 19% / 0%** as the gate
   tightens from histogram-cosine → shape-gated → load-bearing-only. Domain
   saturation makes naive per-method matching produce ~80% false "derivation."
6. Independent convergence: strict per-method twin rate **19%** ≈ the paper's
   **C06f 17.5%** (31/177 at 0.913) — and this trace shows that matched minority
   is trivial/shape-stable functions, not the detection core.

---

## 1. Artifacts & reproducibility

All repos cloned full-history into `/srv/repos/public/lineage/`:

| dir | origin | HEAD | notes |
|---|---|---|---|
| `chardet/` | github.com/chardet/chardet | `b5b2aa5` | tags 1.0 … 7.4.3 |
| `charset_normalizer/` | github.com/jawah/charset_normalizer | `49cf8d3` | |
| `uchardet/` | github.com/BYVoid/uchardet | `4e68575` | C++ extraction of Mozilla universalchardet |
| `gecko-uchardet/` | github.com/mozilla/gecko-dev (sparse/treeless) | `108c0d2` | branch `GECKO450esr_2016030414_RELBRANCH` (Firefox 45 ESR, 2016); sparse path `extensions/universalchardet` = **28 .cpp/.h** = the genuine Mozilla C++ original |

Gecko sparse fetch (efficient — avoids cloning all of gecko-dev):
```
git init gecko-uchardet && cd gecko-uchardet
git remote add origin https://github.com/mozilla/gecko-dev.git
git sparse-checkout init --cone && git sparse-checkout set extensions/universalchardet
git fetch --depth 1 --filter=tree:0 origin GECKO450esr_2016030414_RELBRANCH
git checkout FETCH_HEAD
```

First-release / key worktrees under `/srv/repos/public/lineage/_v/`:

| worktree | tag | commit | lang |
|---|---|---|---|
| `chardet-1.0` | 1.0 (2006) | `7c2b6fe` | Python 2 |
| `chardet-6.0.0` | 6.0.0 | `8a4636b` | Python 3 (flat `chardet/`) |
| `chardet-7.0.0` | 7.0.0 | `4b89d62` | Python 3 (**`src/chardet/` + `pipeline/`,`models/`**) |
| `csn-1.0.0` | 1.0.0 (2019) | `d3996ce` | Python 3 |
| `uchardet-0.0.2` | v0.0.2 | `d0ccdd5` | C++ |

Indexing: `SQRY_INCLUDE_HIGH_COST=1 sqry index --force --include-high-cost <path>`.
Whole-worktree index sizes (nodes / files): chardet-1.0 633/36 · csn-1.0.0 2107/21
· uchardet-0.0.2 1115/53 · chardet-6.0.0 8859/130 · chardet-7.0.0 4292(5803 edges)/64
· mozilla-universalchardet 1553/67.

`active plugins` include `c, cpp, python, …` — sqry parses Python-2 (chardet 1.0)
and C++ (uchardet, gecko) fine.

---

## 2. Lineage: taxonomy-marker survival (renaming-VARIANT, names retained)

Marker regex: `Prober|CodingStateMachine|UniversalDetector|DistributionAnalysis|CharDistribution|ContextAnalysis|GroupProber|JpCntx|JapaneseContext`
(via `sqry search <regex> <path>`, distinct symbol names).

| node | distinct taxonomy symbols |
|---|--:|
| Mozilla `universalchardet` (FF45 C++) | **29** |
| uchardet 0.0.2 (C++) | 26 |
| chardet 1.0 (Py, 2006) | 26 |
| chardet 6.0.0 (Py, pre-rewrite) | 22 |
| **chardet 7.0.0 (LLM rewrite)** | **1** (only `UniversalDetector`, kept for public API) |
| charset_normalizer 1.0.0 | **0** |

Genuine Mozilla `ns*` names (gecko FF45): `nsUniversalDetector`, `nsCharSetProber`,
`nsCodingStateMachine`, `nsEscCharSetProber`, `nsEUCJPProber`, `nsMBCSGroupProber`,
`nsSJISProber`, `CharDistributionAnalysis`, `EUCJPContextAnalysis`,
`JapaneseContextAnalysis`, `JpCntx`; uchardet adds `nsSBCharSetProber`,
`nsEUCKRProber`, `nsEUCTWProber`. chardet 1.0 = same names, `ns` dropped; several
(`CharDistributionAnalysis`, `*DistributionAnalysis`, `*ContextAnalysis`) byte-identical.

---

## 3. Implementation topology trajectory (renaming-INVARIANT, names ignored)

Implementation-package-scoped (tests excluded), `sqry graph … stats`. `edges/node`
= call-graph connectivity density (a renaming-invariant shape proxy ≈ C06a).

| node | nodes | edges | edges/node | files | layout |
|---|--:|--:|:--:|--:|---|
| Mozilla universalchardet (C++) | 587 | 866 | 1.48 | 28 | flat `src/base` |
| uchardet 0.0.2 (C++) | 1105 | 1576 | 1.43 | 49 | flat `src` |
| chardet 1.0 (Py) | 627 | 1006 | **1.60** | 35 | flat `chardet/` |
| chardet 6.0.0 (Py) | 1871 | 4062 | **2.17** | 84 | flat `chardet/` |
| chardet 7.0.0 (Py) | 1306 | 1562 | **1.20** | 22 | layered `src/chardet/{pipeline×13, models}` |
| csn 1.0.0 (Py) | 1886 | 2380 | 1.26 | 11 | flat |

Reading: continuous densification universalchardet→1.0→6.0 (1.48→1.60→2.17), then
a structural break at v7 (density collapse to 1.20, re-layered into a pipeline,
node count drops). Cross-language counts are indicative only; the Python chardet
axis is the rigorous comparison. v7 `src/chardet/` subpackages: `pipeline/`
(13 modules: orchestrator, confusion, escape, utf1632, markup, ascii, statistical,
structural, validity, …), `models/`, plus `detector.py`, `registry.py`, `enums.py`,
`equivalences.py`, `cli.py`, `_utils.py`.

---

## 4. Per-method renaming-invariant trace (the finest level)

Method: Python `ast` → per-function identifier-blind structural descriptor
(control-flow histogram over `If/For/While/Try/Except/With/Return/Raise/Break/
Continue/Call/BoolOp/Compare/ListComp/Assign`, arity, max nesting depth, return
count, loop count, total CF nodes). Reproduce with `scripts/per_method_trace.py`
and `scripts/per_method_astshape.py`.

### 4.1 Deep dive — the #1 method (v6 `UniversalDetector.feed`, the dispatch loop)

| | v6 `UniversalDetector.feed` | v7 `_run_pipeline_core` | v7 `run_pipeline` |
|---|---|---|---|
| lines | 195 | 106 | 28 |
| CF histogram | Call37 Assign36 If29 Compare22 Return6 BoolOp3 For1 Break1 | Call22 Assign17 If17 Return13 Compare12 BoolOp3 For1 | Call5 Assign3 If1 Return1 Raise1 ListComp1 Compare1 |
| skeleton shape | **deep nested if/else cascade** (6+ levels), 1 prober loop, 6 returns | **flat early-return ladder** (≤2 levels), 13 returns | thin wrapper |
| CF cosine vs v6.feed | — | **0.960** | 0.882 |

Key point: histogram cosine = 0.96 (looks similar) but the control-flow *topology*
is inverted — deep-nested dispatcher vs flat guard pipeline. The cosine is domain
saturation; the skeleton shows re-architecture.

### 4.2 Top-50% trace, three gates

v6 implementation methods total: **148**. v7: **75**. Top 50% of v6 by cyclomatic
(`1+If+For+While+Except+BoolOp`) = **74 methods** traced individually v6→best v7.

| matcher / gate | TWIN | weak | NONE | interpretation |
|---|--:|--:|--:|---|
| **Naive** (CF-cos ≥0.90 + arity±1 + size 0.5–2×) | **59 (80%)** | 13 (18%) | 2 (3%) | **false positives** (domain saturation): e.g. `get_order`→`done`, `feed`→`_fill_language`, `next_state`→`_is_valid_utf7_b64` |
| **Strict** (also loop==, depth±1, ret±1, cos ≥0.95, size 0.67–1.5×) | **14 (19%)** | 47 (63%) | 13 (18%) | the 14 twins are **all trivial boilerplate** (cyc ≤ 6) |
| **Strict, load-bearing only (cyc ≥ 8, n=14)** | **0 (0%)** | 8 | 6 | **the detection logic has no v7 structural twin** |

### 4.3 Load-bearing v6 methods (cyclomatic ≥ 8) — strict verdicts

| v6 method | cyc | strict verdict (best v7, cos) |
|---|--:|---|
| `SBCSGroupProber.get_confidence` | 83 | NONE |
| `UniversalDetector.feed` | 34 | NONE |
| `UniversalDetector.close` | 25 | NONE |
| `detect_all` | 18 | NONE |
| `SingleByteCharSetProber.feed` | 17 | weak `_analyze_euc_jp` 0.90 (spurious) |
| `UniversalDetector._apply_encoding_heuristic` | 12 | NONE |
| `UTF1632Prober.validate_utf16_characters` | 9 | NONE |
| `EUCJPProber.feed` | 9 | weak `_gate_cjk_candidates` 0.94 (spurious) |
| `SJISContextAnalysis.get_order` | 9 | weak `get_candidates` 0.70 |
| `SJISProber.feed` | 9 | weak `_gate_cjk_candidates` 0.94 (spurious) |
| `MultiByteCharSetProber.feed` | 9 | weak `_gate_cjk_candidates` 0.94 (spurious) |
| `HebrewProber.feed` | 9 | weak `_gate_cjk_candidates` 0.91 (spurious) |
| `UTF8Prober.feed` | 8 | weak `_gate_cjk_candidates` 0.89 (spurious) |
| `EUCJPContextAnalysis.get_order` | 8 | weak `get_candidates` 0.74 |

The 14 strict "TWIN"s all sit in the cyc ≤ 6 tail: one-line getters, `__init__`,
`reset`, `get_order` table-lookups — e.g. `UTF1632Prober.language`→
`UniversalDetector.done` (1.00), `*.reset`→`UniversalDetector.reset` (0.96–0.99).
Trivial methods have identical shapes in any codebase; no derivation signal.

### 4.4 Convergence with the paper's C06f
Strict per-method twin rate **19%** ≈ C06f **17.5%** (31/177 at within-match 0.913),
reached by an independently-built matcher. This trace additionally identifies *what*
the matched minority is — trivial/shape-stable functions — and that the load-bearing
detection methods are unmatched.

### 4.5 Coverage extension to 80% (top 118 of 148 v6 methods)

Re-run via `scripts/per_method_trace_cov.py 0.8` (adds the 51–80% lower-complexity band):

| matcher | top-50% (74) | top-80% (118) |
|---|--:|--:|
| Naive (CF-cosine) twin | 80% | **86%** |
| Strict (shape-gated) twin | 19% | **38%** |

The aggregate rose, but it is **entirely trivial-method inflation**. Strict verdicts by band:

| complexity band | n | TWIN / weak / NONE | twin% |
|---|--:|---|--:|
| **load-bearing (cyc ≥ 8)** | 14 | 0 / 8 / 6 | **0%** |
| substantive (5–7) | 15 | 2 / 10 / 3 | 13% |
| minor (3–4) | 20 | 3 / 15 / 2 | 15% |
| **trivial (≤ 2)** | 69 | 40 / 26 / 3 | **58%** |

The added ranks 75–118 are overwhelmingly `cyc=1` one-liners (`__init__`, `reset`,
`charset_name`/`language` returning a constant) twinning to v7 one-liners at
0.95–1.00 — e.g. `Big5Prober.language`→`UniversalDetector.done` (1.00). Nonsense
pairings, zero derivation signal.

**Coverage-invariance result:** widening coverage raises the *aggregate* twin rate
(corpus tilts toward trivial methods) but the **load-bearing band stays 0% twin at
both 50% and 80%**. The aggregate is a coverage-dependent artifact; the per-band
rate (esp. load-bearing = 0%) is the coverage-invariant truth. **Report per-band,
never aggregate.**

### 4.6 Full coverage (100%) + reverse direction (v7->v6)

Run via `per_method_trace_cov.py 1.0 fwd` and `per_method_trace_cov.py 1.0 rev`.

Full coverage x direction matrix (`per_method_trace_cov.py <cov> <fwd|rev>`):

| direction | coverage | src methods | naive twin | strict twin | load-bearing twin |
|---|---|--:|--:|--:|:--:|
| v6->v7 | 50% | 74 | 80% | 19% | **0% (0/14)** |
| v6->v7 | 80% | 118 | 86% | 38% | **0% (0/14)** |
| v6->v7 | 100% | 148 | 83% | 43% | **0% (0/14)** |
| v7->v6 | 50% | 38 | 89% | 5% | **0% (0/15)** |
| v7->v6 | 80% | 60 | 87% | 15% | **0% (0/15)** |
| v7->v6 | 100% | 75 | 85% | 23% | **0% (0/15)** |

**load-bearing-band twin = 0% in all SIX cells.** Aggregate strict twin only tracks
the proportion of trivial methods in the covered set (trivial band ~55-60% twin in
every cell) -- not a derivation signal. v7's 15 load-bearing functions (cyc>=8) are
all within its top 50% by complexity, so the reverse load-bearing band is fully
covered (0/5/10) at 50/80/100% alike. Reverse aggregate strict rises 5%->15%->23% as
coverage adds v7's trivial tail; forward rises 19%->38%->43% for the same reason.

Reverse load-bearing v7 functions (cyc>=8) -> best v6 origin: `_run_pipeline_core`(22),
`detect_utf8`(21), `detect_escape_encoding`(16), `_check_utf16`(13), `_text_quality`(13),
`resolve_by_bigram_rescore`(13), `_has_valid_utf7_sequences`(12), `_check_utf32`(10),
`load_models`(9), `get_enc_index`(8) -> **NONE**; `_fill_language`/`_analyze_euc_jp`/
`_gate_cjk_candidates`/`_analyze_johab`/`_analyze_shift_jis` -> weak-spurious.

**Bidirectional conclusion:** v6 and v7's substantive logic is structurally DISJOINT
both ways - no v6 detection method survives into v7, and no v7 pipeline function
originates from a v6 method. The reverse adds that v7's distinctive capabilities
(UTF-8/16/32 validation, escape/UTF-7 detection, bigram-rescore confusion resolution,
model scoring) have **no v6 structural ancestor** = genuine new construction. The
**load-bearing 0% twin is invariant across coverage (50/80/100%) AND direction
(fwd/rev)** - that is the trustworthy, artifact-free number; aggregate rates
(23-43% strict, 83-85% naive) are coverage/direction artifacts dominated by trivial methods.

---

## 5. sqry as the instrument — capabilities & limits (measured this session)

**Worked well (identity / coarse structure):**
- Taxonomy/derivation via `sqry search` over `ns*`-class regex (§2).
- Topology trajectory via `sqry graph stats` (§3).
- Parses Python-2 and C++ (with caveats below).

**Limits found (and why per-method needs more):**
- **`sqry similar` = fuzzy NAME matching** (per its `--help`). Demo: `similar
  get_confidence` returned **11 v6 `get_confidence` methods at 100%**, **0 v7** —
  renaming-blind, useless for the renaming-invariant question.
- **Per-function node schema lacks body shape.** Stored keys:
  `name, qualified_name, kind, language, location, byte_range, is_async,
  is_static, signature, visibility, doc`. No control-flow histogram / body shape.
  `signature` often `null` (e.g. for `feed`); `byte_range` observed `{0,0}` on
  some Python methods.
- **Degree+complexity descriptor too coarse.** Matching v6→v7 on
  `(fan_in, fan_out, complexity)`: 90.7% "twin" at complexity ±1 = false positives
  (`feed`↔`__init__`). Call-edge resolution incomplete: fan-out populated for only
  **43/75** v6 methods.
- **C++ class-*kind* extraction shallow.** uchardet `kind:class` returned only 5
  class/struct nodes; the full `ns*` taxonomy is recoverable via `sqry search`
  (name regex) but not `kind:class`. `--include-high-cost` did not fix this.
- **MCP `name~=/regex/` predicate** returned 0 candidates on some indexes (a
  combinator quirk); CLI `sqry search` was the reliable name-regex path.

---

## 6. What sqry must add to make per-method derivation detection a first-class query

(Design spec for a next sqry version — additive, no re-architecture; the AST is
already walked for symbols/edges, the body shape is just discarded.)

1. **Index/fact layer — per-function body-shape descriptor**, computed in the
   existing AST walk and stored on the node:
   - canonical, language-neutral **control-flow histogram** (`If/For/While/Try/
     Except/With/Return/Raise/Yield/Match/…`);
   - **signature shape** `(positional, kw-only, defaults, *args/**kwargs,
     return-annotation)` — populate the existing (currently-null) `signature` slot
     structurally;
   - **callee multiset / fan-out shape** (count + shapes, not names);
   - **normalized AST-shingle / subtree hash** (identifiers erased) + WL local label.
   Fix data quality: complete intra-function call resolution; populate
   `byte_range`/spans reliably.
2. **Graph layer** — store the descriptor as a node attribute + build a
   **structural-similarity index** (LSH/MinHash/k-d) alongside the existing
   CSR/SCC/2-hop analyses.
3. **Query layer** — a `shape-match`/`structural-similar` op distinct from the
   name-based `similar`: match by descriptor distance **gated on `(signature_shape,
   fan_in_bucket, fan_out_bucket)`** + greedy NN; report **match-rate AND
   within-match similarity** (two numbers, like C06f); support **cross-ref /
   structural-diff** (A-vs-B), since lineage matching is inherently cross-version.
4. **Determinism** (descriptor = deterministic function of source bytes; seed any
   hashing) + incremental invalidation on body edit.
5. **Cross-language canonicalization** — each plugin emits the same descriptor
   schema (fixes the C++ shallowness and enables universalchardet↔chardet body
   comparison).

---

## 7. Methodological lessons (must carry into the next harness/paper)

- **Gating is everything.** The identical per-method trace gives **80% → 19% → 0%**
  as the gate tightens (histogram-cosine → shape-gated → load-bearing-only). A
  naive matcher manufactures an 80% "derivation" rate that is entirely domain
  saturation. Any per-method derivation claim MUST state its gate.
- **Exclude trivial methods.** Getters/`__init__`/`reset`/one-liners match
  trivially across unrelated codebases; counting them inflates "twin" rates.
- **Report per-complexity-band, never an aggregate twin rate.** Aggregate scales
  with coverage: 50%→80% coverage raised strict twin 19%→38% and naive 80%→86%
  purely by adding trivial methods, while the load-bearing-band twin stayed 0%.
  The load-bearing band is the coverage-invariant signal.
- **Histogram/aggregate similarity = domain, not derivation** (re-confirmed at
  function granularity: feed↔pipeline cosine 0.96 yet different architecture).
  The discriminating evidence is **structural-niche + shape**, and **whether the
  load-bearing methods have twins**.
- **The right production flow:** C06f (gated structural matching) over *all* pairs,
  trivial methods filtered, surfacing the handful of real candidates as
  human-auditable side-by-side skeleton diagrams.

---

## 8. Honest limits / threats to validity

- Method-level structural **divergence is necessary-but-not-sufficient** for
  "independent": a sufficiently thorough paraphrase that *also* re-architects would
  produce the same picture. Structural **similarity**, conversely, is consistent
  with both derivation and domain convergence — which is why the multi-pair
  calibration (v5/v6, v6/csn) remains essential.
- "NONE/weak" verdicts come from the structural gate, not semantic understanding
  of each method's role; borderline pairs (e.g. prober feeds at ~0.9) warrant human
  eyeballing via skeleton diagrams.
- Cross-language node/edge counts (C++ vs Python) are indicative only.
- universalchardet proxy used the genuine Mozilla FF45 C++ (`gecko-uchardet`) and
  the BYVoid C++ extraction; both preserve the `ns*` taxonomy. The mozilla-central
  original at chardet 1.0's exact 2006 fork point was not pinned (FF45=2016 used);
  taxonomy stability over that span makes the conclusion robust.

---

## 9. Recommendations for the next version

- **Paper (chardet v6/v7):** add the per-method renaming-invariant trace as a
  refinement of C06f — report the load-bearing-method twin count (0/14) and the
  three-gate sensitivity (80/19/0) as an explicit "gating discipline" result; it
  strengthens the "structural reorganization" finding and pre-empts the naive-80%
  misuse. Add the universalchardet→chardet→csn lineage (taxonomy + topology
  trajectory) as context that validates the `v6/charset_normalizer` independence
  baseline.
- **Harness (`extract_signals.py`):** make C06f's matcher report the gate
  explicitly, exclude trivial methods (cyclomatic floor), and emit the per-method
  side-by-side skeleton diagram for matched/near-matched pairs as reviewable
  artifacts.
- **sqry:** implement §6 (body-shape descriptor + structural-similarity index +
  gated `shape-match`/structural-diff). That single addition turns "sqry pointed
  toward 17.5%" into "sqry computes it."

---

### Appendix — scripts (in `scripts/`)
- `per_method_astshape.py` — extract a single method's identifier-blind CF skeleton
  + histogram + signature, and CF-cosine between two methods (the §4.1 deep dive).
- `per_method_trace.py` — collect all impl methods per package, rank v6 by
  cyclomatic, match top 50% v6→v7 under both naive and strict gates, emit the
  per-method table and verdict summary (§4.2–4.3). Paths are pinned to
  `/srv/repos/public/lineage/_v/`.
</content>
