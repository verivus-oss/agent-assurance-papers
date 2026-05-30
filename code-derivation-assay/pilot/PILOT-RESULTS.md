# CDA Pilot — signal read on the chardet trio (iterations 1–5)

**Harness:** `pilot/pilot_harness.py` + `pilot/_detect_runner.py` (deterministic, offline) → `pilot/results.json`.
**Sources (real):** `chardet` 5.0.0 / 6.0.0 / 7.0.0 + `charset_normalizer` 3.4.7, `git archive`, **package scope** (handled v7's `src/chardet/` vs top-level `chardet/`).
**Status:** n = 6 pairs, one domain — **direction/sanity pilot, not a powered estimate.**
**Iterations:** (1) ST+PB+easy-BH; (2) **strengthened BH** — a 223-input *discriminating* hard workload; (3) **ST measure ensemble**; (4) **provenance-quirk signals** (path a); (5) **fuller 6-measure structural envelope** — call-graph topology + WL kernel + per-function shape reimplemented (C06a/C06a′/C06f analogs). This doc supersedes earlier iterations.

## Signals
- **ST ensemble** — fine `ST_sh` (AST node-type 5-gram shingle overlap), coarse `ST_cfg` (control-flow node-type histogram cosine = predecessor C06c), `ST_nh` (full node-type histogram cosine).
- **PBt** — data-table literal carryover; **PBi** — import-boundary Jaccard.
- **BH** — encoding agreement over the easy 64-file corpus (≈uninformative); **BHd** — agreement over the **discriminating** subset (223 short/ambiguous bytes where detectors diverge).

## Structural envelope — 6 reimplemented measures (all 6 pairs)

| pair | label | shingle | cfg-hist | node-hist | topology | WL-kernel | per-fn | **envelope** |
|---|---|---|---|---|---|---|---|---|
| v5–v6 | EVOLVED | 0.91 | 1.00 | 0.56 | 0.96 | 0.95 | 0.98 | [0.56…1.00] |
| v6–v7 | **AI rewrite** | 0.42 | 0.99 | 0.88 | 0.86 | 0.89 | 0.88 | **[0.42…0.99]** |
| v5–v7 | DERIVED-distant | 0.30 | 0.99 | 0.40 | 0.84 | 0.88 | 0.86 | [0.30…0.99] |
| v5–csn | INDEPENDENT | 0.46 | 0.99 | 0.59 | 0.83 | 0.50 | 0.88 | [0.46…0.99] |
| v6–csn | INDEPENDENT | 0.45 | 1.00 | 0.93 | 0.86 | 0.57 | 0.90 | [0.45…1.00] |
| v7–csn | INDEPENDENT | 0.51 | 0.98 | 0.97 | 0.86 | 0.59 | 0.94 | [0.51…0.98] |

**Per-measure AUC** (same-lineage vs independent): structural — shingle 0.33 · cfg 0.56 · node-hist 0.11 · topology 0.56 · **WL 1.00** · per-fn 0.33; behavioral — BHd 0.56, BH-easy 0.44; provenance — PBt 0.67, PQconst 0.67, PQmsg 1.00 (artifact, §iter-4), PQvocab 0.78, PQconf (chardet-only) n/a; **combined 0.67**.

**Across 12 measures the AUC for the *same* contrast ranges 0.11 → 1.00.** The divergence is not only *across* measures but *within* one: my WL-kernel variant gives **AUC 1.00** (same-lineage 0.88–0.95 vs independent 0.50–0.59), while the predecessor's WL gave the **opposite** (v6→v7 = 0.587 *below* v6↔csn = 0.872). **Caveat (verification round 1):** my WL is *not* a faithful equivalent of the predecessor's — `pilot/structural.py` builds call-graph node identity from function **names** (so it is **not** renaming-invariant; codex/gemini/grok confirmed `defined.add(n.name)` at `structural.py:39`), aggregates successors only, and omits the predecessor's predecessor-labels + qualified names. So the AUC 1.0 is largely a **shared-identifier-vocabulary artifact** (chardet versions share method names; csn does not), not a profound structural finding — and the predecessor's 0.587/0.872 are **external citations not reproducible from any file in this repo**. What this shows is *matcher fragility* (a non-equivalent variant flips the result), not two faithful kernels disagreeing — still an L4 illustration, but a weaker one than first stated.

**What this does and does NOT establish.** It establishes that a single structural-similarity *number* for v6→v7 is meaningless (envelope [0.42 … 0.99]) and that even a single *named* measure (WL) is implementation-fragile enough to flip the verdict. It does **not** establish, on n=6, that the rewrite is "robustly indistinguishable" — some measures (WL-mine, AUC 1.0) *do* separate same-lineage from independent, but that may reflect architecture-family convergence rather than derivation, it contradicts the other WL variant, and a real determination needs the full pre-registered ablation grid + baselines + many families (per CDA's design). **The open question this raises — does *any stable, baseline-beating* measure separate AI-rewrite from independent? — is exactly what the benchmark exists to answer.**

## Predecessor's fuller suite (corroboration; `chardet-relicense/proof-bundle`)
The previous study computed 6 measures on the same artifacts (3 pairs). My ST_cfg=0.986 reproduces its C06c=0.984 — the reimplementation is faithful.

| measure | v5–v6 EVOLVED | v6–csn INDEP | v6–v7 AI-rewrite |
|---|---|---|---|
| control-flow hist (C06c) | 0.995 | **0.999** | 0.984 |
| call-graph topology (C06a) | 0.930 | 0.922 | 0.881 |
| WL kernel, fine (C06a′) | 0.902 | 0.872 | 0.587 |
| per-function shape (C06f, matched) | 0.982 | 0.796 | 0.913 |
| **behavioral exact (C06e)** | **0.947** | 0.003 | **0.000** |
| literal carryover (AUX1) | — | — | 0 |

## What the full ensemble shows

1. **Structural "similarity" for v6→v7 is wildly matcher-dependent — envelope [0.42 … 0.99].** Cherry-pick control-flow histogram → 0.986 ("clearly derived"); cherry-pick 5-gram shingle / WL-fine → 0.42 / 0.587 ("independent"). **This is the L4 matcher-dependence lesson, on the real motivating case** — and exactly why CDA mandates an **envelope across an ablation grid and demotes sign-flipping metrics** (R-ABLATE), and why a single published similarity number is meaningless.
2. **The high coarse-measure values are domain convergence, not derivation.** Control-flow histogram is **0.999 for the INDEPENDENT pair** (v6↔csn) — higher than for the AI rewrite. All Python encoding detectors share control-flow shape, so ST_cfg / topology are ~0.9–0.99 for *everyone* and discriminate nothing (AUC ≈ chance). This is the **baseline-panel** necessity (§9 item 8) made concrete: 0.98 "looks derived" but the independent baseline is also 0.98.
3. **The one clean discriminator is behavioral — and it reads the AI rewrite as independent.** Predecessor C06e exact-match: EVOLVED **0.947** vs AI-rewrite **0.000** ≈ INDEPENDENT **0.003**. My strengthened BHd agrees in direction: EVOLVED 0.605, and the AI rewrite at **0.135 sits within the independent spread** (v7-csn **0.072** … v6-csn 0.430) — below two of the three independent pairs but above v7-csn, i.e. at the independent baseline, not cleanly below it. On hard/ambiguous inputs v7 behaves like *neither* its ancestor nor csn.
4. **No *stable* measure provides defensible positive evidence of derivation for v6→v7.** Fine structural ≤ independent; coarse structural = domain baseline (high for everyone); behavioral = independent-or-below; literal/data-table carryover = 0. One measure *does* separate — my WL-kernel variant (AUC 1.0) — but it contradicts the predecessor's WL and may track architecture-family, not copying (see the fuller-envelope section). So the instrument **cannot defensibly certify v7 as derived on a single measure**; chardet sits in the §13 "deep re-architecture + regenerated data tables" region, and whether a *stable, baseline-beating* signal exists is the open question.

## Feed-forward
- **No measure robustly separates the AI-rewrite-vs-independent contrast: per-measure AUC spans 0.11–1.00, but the high values are artifacts** (WL=1.00 is a name-vocabulary artifact; PQmsg=1.00 is a generic-phrase artifact) — the rewrite sits within the independent spread on every defensible measure. Per `power/POWER-ANALYSIS.md`, H1 (lower bound > 0.65) is **infeasible for AI rewrites** with these signals. The richer predecessor suite does **not** rescue it — it sharpens *why*: coarse measures are non-discriminating (domain convergence), fine and behavioral measures place the rewrite at/below independent.
- **Two honest paths** (PI call): (a) invest in genuinely discriminating signals (provenance-first: data-flow/constant lineage, API-quirk fingerprints, error-message/edge-case behavioral fingerprints that a reimplementation wouldn't reproduce) and re-pilot; or **(b) adopt the finding** — *AI rewrites that regenerate data tables are indistinguishable from independent reimplementation by structural/behavioral retention; only literal/provenance carryover separates copying from clean reimplementation, and chardet v7's is small but non-zero (residual 13 raw, mostly kept era-enum naming + stdlib false positives).* This is the pre-stated §4 falsification outcome and a strong, defensible result aligned with Blanchard's three near-zero measures.
- **Validated CDA design choices, empirically:** R-ABLATE envelope/demotion (point 1), mandatory baseline panel (point 2), PB as the copying-specific signal (point 4), discriminating BH workloads (point 3, §7.5), and the M1 retention≠copying estimand framing.

## Iteration 4 — provenance-quirk signals (path a): also negative
Tried signals a clean reimplementation shouldn't reproduce: distinctive float constants (PQconst), message strings (PQmsg), emitted-label vocabulary (PQvocab), exact-confidence agreement (PQconf, chardet-only).

| signal | EVOLVED | v6→v7 | INDEPENDENT | AUC | verdict |
|---|---|---|---|---|---|
| PQmsg | 0.471 | 0.012 | ≤0.003 | 1.000 | **artifact** — the *only* v6∩v7 string is `"with confidence"` (generic); not provenance |
| PQvocab | 0.296 | 0.045 | 0.021–0.073 | 0.778 | weak; v7-csn (0.073) > v6-v7 (0.045) |
| PQconst | 0.143 | 0.092 | 0.058–0.227 | 0.667 | noisy |
| PQconf | 1.000 | 0.588 | n/a | — | suggestive but **unbaselined** (csn has no comparable confidence) |

**Outcome:** provenance-quirk signals do **not** rescue discrimination of the AI rewrite. PQmsg's perfect AUC is a generic-phrase + tiny-count artifact (caught only by inspecting the shared strings — a vivid case for mandatory distinctiveness/baseline checks). The one residual whiff is PQconf = 0.588 (v7's confidence values partially track v6's), but it is unbaselined and as consistent with *tuning v7 to match v6's test outputs* as with code derivation. Net: **across structural, behavioral, AND provenance-quirk signal classes, no measure reliably separates the chardet AI rewrite from independent reimplementation** — strengthening finding (b).

## Iteration 6 — AFC "golden-nugget" quirks, and the measure this points to
Added the legally-probative arbitrary-expression family (per `../legal-framework.md`): identifier overlap (QKident), **distinctive compound identifiers** (QKidist), docstring words (QKdoc), comment words (QKcomm).

| signal | EVOLVED | v6→v7 | INDEPENDENT | AUC |
|---|---|---|---|---|
| QKidist | 0.284 | **0.020** | 0.013–0.020 | 0.889 |
| QKdoc | 0.667 | 0.203 | 0.158–0.172 | 0.889 |
| QKcomm | 0.704 | 0.211 | 0.175–0.191 | 0.778 |

**The aggregate AUCs are driven by EVOLVED; the AI rewrite sits at the independent baseline on every one** (QKidist 0.020 ≈ independents 0.017–0.020). So *no aggregate overlap score* — structural, behavioral, or quirk (15 measures now) — separates the AI rewrite from independent.

**But the distinctiveness inspection found what the score dilutes.** v6 and v7 share **18 distinctive identifiers absent from csn** (`resDom`); after removing the public-API names (`UniversalDetector, detect_all, EncodingEra, LanguageFilter, MINIMUM_THRESHOLD` — AFC-filtered as compatibility-dictated) **13 remain** (`resApi`, per `pilot/residual.py`), including **arbitrary internal names** (`LEGACY_ISO/MAC/MAP/REGIONAL, MODERN_WEB, NON_CJK, encoding_era, ignore_threshold, lang_filter`) a clean-room author would invent differently (plus stdlib false positives `ascii_letters, max_bytes`). In a Jaccard over thousands of identifiers these vanish to 0.02; they are the *kind* of arbitrary shared feature the **"striking similarity"** doctrine targets (§19) — evidence, not a verdict.

**Conclusion / the measure to invent.** The right instrument is **not another similarity score** (all 15 are matcher-dependent and/or place the rewrite at baseline). It is an **AFC-operationalized test**: (1) *enumerate* distinctive shared features (identifiers, constants, comments, dead code, error strings); (2) *filter* the functionally/compatibility/standard-dictated ones (the AFC filtration step = subtracting the independent baseline); (3) test whether the *residual* set of arbitrary shared features is **improbable under independent creation** ("striking similarity"), reported as a count + an improbability estimate, not an overlap fraction. For chardet v6→v7 that residual is **13 raw identifiers** (`pilot/residual.py` output), of which ~5 are stdlib/parameter false positives the current filtration misses (e.g. `ascii_letters`, `max_bytes`), leaving a handful of genuinely arbitrary names — small but non-zero, which is why the case is genuinely contestable rather than clear-cut, and why a *graded, filtered, baseline-subtracted* measure (not a raw score) is the correct CDA primitive. This is the next signal to build and re-pilot across the benchmark.

## Iteration 7 — the §5.4 residual measure, run on two families (`pilot/residual.py`)
Built the filter-then-score-residual measure: enumerate distinctive shared features → filter (a) features in the independent baseline pool (AFC domain filtration) and (b) the pair's public-API names (compatibility) → residual = arbitrary non-functional shared expression.

| family | pair | residual after API filter | example residual |
|---|---|---|---|
| chardet | **EVOLVED** v5→v6 | **228** | BIG5_CHAR_LEN_TABLE, error msgs ("…we have a winner") |
| chardet | **AI-rewrite** v6→v7 | **13** | LEGACY_MAC, MODERN_WEB, NON_CJK, encoding_era (+ `ascii_letters` = false pos) |
| fuzzy | **fork** fuzzywuzzy→thefuzz | 7 | force_ascii, default_scorer, translation_table |
| fuzzy | **reimpl** fuzzywuzzy→RapidFuzz (GPL→MIT) | **2** | len_ratio, string_out |
| fuzzy | **INDEPENDENT** jellyfish↔textdistance | **12 (false pos)** | s1_len, search_range, common_chars (Jaro-canonical), TypeError (builtin) |

**Two findings.** (1) **Directional signal is real where filtration is adequate:** EVOLVED (228) ≫ AI-rewrite (13); fork (7) > clean reimpl (2). The clean reimplementations — chardet v7 (AI) and RapidFuzz (human) — both land **low**, and RapidFuzz's residual is just 2 names, i.e. the measure reads the human GPL→MIT reimplementation as *also* clean. (2) **The measure is only as good as the filtration:** the independent control false-positived at 12 because Python **builtins/stdlib** and **algorithm-canonical variable names** (the textbook Jaro variables) were not filtered — for this control `pilot/residual.py:170` passes a **1-lib baseline `[Levenshtein]`** (thinner than the 3-lib pool used for the fuzzy DERIVED rows), and no builtin/stdlib stoplist was applied. So §5.4 is the right shape but **requires comprehensive filtration (builtins + stdlib + a large independent baseline pool) before the residual is trustworthy** — exactly AFC's "filter *everything* unprotectable" step, and a concrete build requirement, not a solved measure.

**Honest status:** the §5.4 measure is **promising but not yet validated** — it produces a sensible ranking on these 5 scenarios, but the false-positive proves it is not yet reliable, and n is tiny. The chardet v6→v7 residual (13, dominated by the kept `EncodingEra` enum naming + a stdlib false positive) is *small and contestable*, consistent with every prior iteration.

## Iteration 8 — multi-family: is this chardet-specific? (`pilot/multi_family_pilot.py`, `MULTI-FAMILY-RESULTS.md`)
The static ensemble + §5.4 residual (leave-pair-out baseline) run on **three** families confirms the finding **generalizes**: the *human* GPL→MIT reimplementation **fuzzywuzzy→RapidFuzz** (PQidist 0.046 ∈ independent band, residual 2) is as indistinguishable from independent as the chardet *AI* rewrite — while a **vendored copy** (tomli→tomllib: PQidist **0.906**, residual **68**) and a **fork** (fuzzywuzzy→thefuzz: PQidist 0.198) are clearly detected. So the blind spot is *clean reimplementation* (AI or human), not chardet or AI specifically — and the measures reliably detect real copying. Full result + caveats in `MULTI-FAMILY-RESULTS.md`.

## Caveats
n=6, one domain, AUCs are extremely noisy (3×3 → AUC granularity 1/9). The C06a/C06a′/C06f measures are now reimplemented (this iteration), giving 6 structural + 2 behavioral + 4 provenance measures, but **the conclusion is not uniform across them** — per-measure AUC spans 0.11–1.00 and even the WL kernel flips verdict between two reasonable variants. So no single-measure claim about v6→v7 is defensible, and I am *not* asserting the rewrite is robustly derived or robustly independent on this evidence — that determination requires the pre-registered ablation grid + baselines + many families. EVOLVED is treated as a same-lineage positive. A real hermetic-build gotcha surfaced: v7's setuptools-scm `_version.py` is absent from `git archive` (the pilot shims it).
