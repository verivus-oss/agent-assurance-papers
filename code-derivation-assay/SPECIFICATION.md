# Code Derivation Assay (CDA) — Study Specification

**Status:** DRAFT v0.8 (pre-registration target). Clean-slate design. **Not** a continuation of, and **does not reuse content from**, the predecessor `chardet-relicense/` study. The predecessor is referenced *only* as a source of lessons-learned (§2); none of its prose, signal definitions (`C06a–f`), corpora, harness code, or numbers carry over.
**Codename:** CDA.
**Target venue:** empirical software-engineering (cs.SE); ACM SIGSOFT Empirical Standards — *Engineering Research* (primary) + *Benchmarking* + *General* + *Data Science*.
**License:** CC BY 4.0 (paper); permissive (harness, benchmark metadata, manifests). **Benchmark *inputs* retain their own upstream licenses** — copyleft (LGPL/GPL/AGPL) and license-*disputed* inputs are **first-class**, because they are the disputes CDA exists to study (§14). Each input is redistributed **verbatim with its original license texts and notices preserved**, as a segregated **mere-aggregation** corpus that is read as data and never linked into the harness (so no copyleft obligation propagates to CDA's own code); inputs whose license forbids redistribution, or whose provenance is under active dispute, are included by **metadata-only reference** (URL + tag + SHA, fetched at build time) — a *fallback*, no longer load-bearing. The chardet v6 (LGPL) / v7 (MIT) pair is included on these terms.
**Date:** 2026-05-30.
**Implementation status (P0) — read before treating any claim as "built."** This repository is at milestone **P0**: a *frozen design* (this spec) plus a *pilot* (`pilot/`) and a *seeded simulation power analysis* (`power/`). **The spec is normative for the future build, not a description of shipped software.** Actually implemented today: the Python-only pilot harness; the structural/behavioral/provenance/quirk signals on the chardet trio; the §5.4 residual *prototype* (identifiers/messages/constants only) on **three families (chardet + fuzzy + toml)** via `pilot/multi_family_pilot.py` (`pilot/MULTI-FAMILY-RESULTS.md`); the power simulation. **Designed but NOT yet built:** cross-language ST/PB (§5.2, §18.4 — the pilot is Python-`ast` only); the redistributed, MANIFEST-backed, notice-preserving corpus (§6, §10.4 — the pilot reads external local checkouts at hardcoded paths); `make validate` / R-NODRIFT / R-HERMETIC / R-FIG and the `harness/ validate/ benchmark/ container/ Makefile` tree (§10, §15, §17); and the full §5.4 measure (calibrated improbability + CI + comment/dead-code/data-table/behavioral feature types). Claims about those are **design commitments** (verify them against this spec), not against current code. The independent verification reviews in `spec-reviews/*-verification-round1.md` flagged exactly these design-vs-code gaps; this block is the standing disclaimer.

**Revision history.**
- **v0.8 → v0.8.1 (2026-05-30).** Corrections from the round-1 verification reviews (codex/gemini/grok, all code-grounded): added the Implementation-status disclaimer above; corrected the stale chardet residual count to **13** (script output; ~5 stdlib/param false positives) (§5.4); qualified "no aggregate measure separates" to "no measure *robustly* separates," disclosing that the WL AUC 1.0 is a **name-based-graph vocabulary artifact** and not renaming-invariant (§5.2, §5.4); aligned §9.1 wording with the implemented first-order cluster bootstrap.
- **v0.7 → v0.8 (2026-05-30).** Pilot iterations 4–6 + **case-law grounding** (`legal-framework.md`: Sega/Sony fair-use reimplementation; Altai **Abstraction–Filtration–Comparison**; access + striking-similarity + fingerprint evidence). Findings: no aggregate similarity score (15 tried, ST/BH/PB/quirk) *robustly* separates the AI rewrite — it sits within the independent spread; the same structural concept spans [0.42,0.99] and the one apparent exception (a name-based WL variant, AUC 1.0) is a shared-vocabulary artifact (§5.2, §5.4). So the **primary measure is reframed as an AFC-operationalized filter-then-score-residual test (new §5.4)**: enumerate distinctive shared features → filter the functionally/compatibility-dictated ones (= subtract the independent baseline, the AFC *filtration* step, §9) → score the residual's improbability under independence ("striking similarity"). PB gains the legally-probative quirk signals (§5.2); construct mirrors AFC (§3); Related Work adds the doctrine (§19). For chardet v6→v7 the residual is 13 raw identifiers (script output), ~5 of them stdlib/parameter false positives, leaving a handful of genuinely arbitrary names — genuinely contestable.
- **v0.6 → v0.7 (2026-05-30).** Ran a **minimal pilot** (`pilot/`) on the real chardet trio (v5/v6/v7 + charset_normalizer, package scope). First real within-domain read: the **AI rewrite v6→v7 is statically indistinguishable from an independent reimplementation** — ST at the independent baseline, PBt = 0 (tables regenerated), BH in the independent band; naive signals give the hard DERIVED-vs-INDEPENDENT contrast AUC ≈ 0.33–0.5 (below H1). Empirically confirms: baseline-panel necessity, the PB-defeated blind spot (§13), the need for a discriminating BH workload, and the M1 estimand framing. Mechanical package scope correctly handled v7's `src/` layout. (§4, §13, §15.)
- **v0.5 → v0.6 (2026-05-30).** **PI decision: cross-language ST/PB enabled** (was Python-only) — the harness compares an edge cross-language *where the derivation actually spans languages* (e.g. JS→Python port), via per-language AST walkers + a language-agnostic structural-descriptor layer; cross-language and within-language pairs are **separate strata, never pooled in the headline**, with BH the more robust cross-language signal and a stated weaker-construct threat (§5.2, §5.3, §10.2, §13, §18.4). Unlocks cross-language port edges (markdown-it→py, node-semver→py, hashids→py) for the benchmark.
- **v0.4 → v0.5 (2026-05-30).** Added **§19 Related work & prior art** (AI-code-provenance survey, code-similarity-benchmarking precedent, birthmarking/clone canon, clean-room copyright theory, LLM-rewrite studies, and the chardet prior analyses). Named concrete **baselines** — JPlag + the Ragkhitwetsagul tool set — in §9 item 8. Added the **training-data-mediated retention** threat to §13 (retention ≠ copying: chardet reproduced the original's design from training data, not source). Also made the original **Mozilla `universalchardet` → chardet** rewrite first-class in §6.2 and the family census.
- **v0.3 → v0.4 (2026-05-30).** **Changed the input-licensing rule** (supersedes the v0.2 "metadata-only reference" framing): benchmark inputs now **retain their own upstream license** and copyleft / license-disputed inputs are **first-class**, redistributed **verbatim with notices preserved** as a segregated mere-aggregation corpus (read as data, never linked into the harness). Metadata-only reference is demoted to a **fallback** for genuinely non-redistributable / disputed cases — it is no longer load-bearing for including the LGPL chardet pair. Also: **reimplementations of proprietary or leaked code are out of scope as inputs** (e.g. leaked-Claude-Code clones excluded from candidates). (Header License, §6.2, §10.4, §13, §14.)
- **v0.2 → v0.3 (2026-05-30).** Ran the first (simulation-based, assumed-effect-size) power analysis — `power/POWER-ANALYSIS.md`, the gating P0 input (§9.6, §11.1). Findings folded in: the family-clustered design needs **≥6 well-behaved test families** (cluster bootstrap is unreliable at ≤3); the **≥40/≥8 floors are ~4–5× too small** (realistic **≈18–24 families / ≈150–220 pairs**); θ_LB = 0.70 is underpowered unless true AUC ≥ 0.90, so the **provisional target is θ_AUC = 0.85 / θ_LB = 0.65** (§4, §2 L3, §6.2, §9.6, §18.2); RQ4 needs **≥6–8 seed families** (a sign test cannot reach significance below ~5) (§9.5); fixed-bin ECE is biased at realistic N, so calibration is reported **descriptively** with a binless estimator (§9.2). All values are **provisional pending a real pilot** that locates the true AUC and confirms family availability before the freeze (§7 of the power doc).
- **v0 → v0.2 (2026-05-30).** Revised against the six independent spec reviews in `spec-reviews/`. The reviews split on the recommendation (codex: major redesign; claude/grok/mistral: approve-with-substantial-changes; gemini: approve) but converged on a concrete must-fix set, all now folded in below.
  - **Estimand / headline contrast (architectural).** The headline is now **within-domain DERIVED-vs-INDEPENDENT** (same spec/domain), because both classes are high-retention and only copying/provenance separates them; **UNRELATED is excluded from the headline AUC** and kept as a chance-floor row. The spec now states that ST/BH measure *retention* and are confounded on same-spec INDEPENDENT, so **PB (provenance) is expected to carry the separation**, and the analysis reports PB-only vs ST/BH-only so a high AUC cannot be silent domain-shape convergence (§4 RQ1, §5.2, §9.1, §17.4; red-team §12e).
  - **Statistics.** Family-clustered (not pair-level) bootstrap (§9.1); power calculation **runs first** and sets `θ_AUC/θ_LB`/calibration bounds, never frozen independently of n (§4, §9.6, §11, §18.2); binning-robust calibration error (§9.2); comparison family enumerated and grouped by estimand (§9.4); **mandatory baseline panel** + single-family ablations (§9 item 8); under-powered/under-2-metric outcomes pre-declared as valid results (§9 items 6, 9).
  - **Benchmark.** Pre-registered selection criteria + boundary-pair quota + easy/hard strata + datasheet (§6.2); INDEPENDENT graded by independence confidence with evidence tiers (§6.1); **labeling protocol** with ≥2 raters and κ (§6.5); two constructed tracks — mechanical *and* LLM-rewrite-as-content-addressed-fixture — resolving the determinism-vs-AI-representativeness conflict, with **depth graded independently** of the pipeline and the score fit on the binary label only (§6.4, §5.2); minimum natural-edge quota (§18.5).
  - **Scope.** `package` resolved **mechanically** from packaging metadata; per-pair claim-object pre-declared; `custom` scopes pre-registered before execution (§5.3); BH carries no source scope, so R-SCOPE binds ST/PB only (§2 L1, §5.2).
  - **Reproducibility.** `make validate` **regenerates results from raw pinned inputs** (never a committed object), centralizes formatting (no float-tolerance hole), and the manuscript **forbids bare numerals** (§10.1); BH-undefined pairs **retained ST/PB-only as N/A** rather than dropped, removing buildability selection bias (§7.5, §8, §10.2).
  - **Process / coverage.** Family list + scope rules pulled into the **P0 frozen artifact** with mechanical test-family sealing and a precommitted split seed (§11, §16, §18.1); post-unblinding **sealed-amendment** procedure (§11.5a); ≥1 **out-of-container** reproduction + construct-validity and registry-tampering red-team charges (§12); §17.3 is now a **reporting rule**, not a pass/fail gate; copyleft/disputed pairs admissible by metadata-only reference (§6.2, §14); §5.1 ordinal demoted to a tested hypothesis. Nits: `custom`, `ci/`, expanded §15 deliverables.

---

## 0. One-paragraph thesis

Disputes about whether one body of code is a *derivative* of another — relicensing fights, clean-room claims, AI-rewrite provenance — currently turn on assertion. CDA builds a **falsifiable, scope-explicit, calibrated classifier** that takes a pair of code artifacts and emits a *graded derivation likelihood with a confidence interval*, validated against a **multi-family labeled ground-truth benchmark** of known-derived, known-evolved, known-independent, and known-unrelated pairs. The chardet v6→v7 relicensing case is one held-out test instance, not the whole study. CDA renders **no legal verdict**; it produces measurements and the calibration needed to interpret them, and it is engineered so that every published number is regenerated by CI that fails closed.

---

## 1. Why a clean build (and what "clean" means here)

The predecessor study was a single-case artifact whose central numbers reproduced exactly, but whose external validity rested on one library and whose two load-bearing claims each carried a confirmed, undisclosed defect (see §2). Patching it (a "v3") would inherit:

- a signal taxonomy whose scope (full-repo vs package) was implicit and, once made explicit, inverted a headline;
- an "independent re-derivation" path that had silently drifted out of agreement with the numbers it claimed to certify;
- an n=1 design that cannot support any claim about *AI rewrites in general*.

These are architectural, not cosmetic. CDA therefore starts from constructs and a benchmark, not from a harness. "Clean" means: **new constructs, new metric names, new corpus, new harness, new pre-registration, and a ground-truth-first design** in which calibration precedes and gates interpretation.

---

## 2. Lessons → hard requirements (traceability)

Every requirement below is traceable to a *confirmed* predecessor shortcoming. This table is the spec's spine; §§5–12 implement it. (Requirements are normative: **MUST**/**SHOULD**.)

| # | Predecessor shortcoming (confirmed) | CDA requirement |
|---|---|---|
| L1 | **Scope confound.** A boundary metric scored 0.667 at repo-scope but 0.000 at package-scope; only repo-root benchmark/training scripts produced the overlap, and the scope was undisclosed. | **R-SCOPE.** Every ST/PB metric is a function of an *explicit declared scope* (`package` \| `module` \| `repo` \| `custom`). The scope is a required field in the run manifest and in every reported number. Each **ST/PB** metric **MUST** be reported at **≥2 scopes** (minimum `package` and `repo`); a single-scope number is rejected by the schema. `package` is resolved mechanically from packaging metadata (BH has no source scope; §5.2, §5.3, §8). |
| L2 | **Validator drift.** The advertised `make validate` exited non-zero against the published numbers because expected constants were hardcoded v1 values that went stale. The "every number is re-derived" invariant was false in practice. | **R-NODRIFT.** No *published numeric result* is hardcoded as an expected value. `make validate` **regenerates results from raw pinned inputs in the same run** (never trusting a committed results object), centralizes number formatting, and asserts the paper's rendered numbers equal the freshly recomputed ones (formatted-string equality). The manuscript forbids bare numerals. CI **MUST** fail closed on any mismatch; a green CI is a precondition for "results" status. (§10) |
| L3 | **External validity (n=1).** One library; no basis for any general claim. | **R-BENCH.** Ground-truth benchmark of **≥40 labeled pairs across ≥8 library families** spanning 4 label classes (§6) — a *lower floor*; the P0 power calc raises it to **≈18–24 families / ≈150–220 pairs** for the family-clustered test design (`power/POWER-ANALYSIS.md`). Headline results are *classifier performance with CIs on a held-out test split*, not a single pair's numbers. (§6, §9) |
| L4 | **Matcher-dependence.** The discriminating signal flipped under an annotation-blind matcher; the dependence was disclosed but the headline still rode one matcher key. | **R-ABLATE.** Every metric with a tunable internal choice (matcher key, normalization, granularity) ships a **pre-registered ablation grid**; the headline is reported as the *envelope across the grid*, and any metric whose sign flips within the grid is demoted from "discriminating" to "exploratory." (§7.4, §9.4) |
| L5 | **Positive controls lived outside the paper.** The proof-that-it-can-fire was in side notes, not the manuscript. | **R-CONTROLS-IN.** Positive (known-derived), negative (independent), and null (unrelated) controls are **first-class rows in the main results tables**, computed by the same harness path as the focus case. (§6, §9) |
| L6 | **No standardized effect sizes; no multiplicity control.** Cross-pair comparisons rested on eyeballed disjoint CIs. | **R-STATS.** Cliff's δ / Vargha–Delaney Â₁₂ (or rank-biserial) for every pairwise contrast; BCa bootstrap CIs; pre-declared family-wise error control (Holm) over the declared comparison family. Decision rules pre-registered. (§9) |
| L7 | **No confirmatory/exploratory boundary; HARKing risk.** v1→v2 narrative inverted post hoc. | **R-PREREG.** Hypotheses, metrics, scopes, thresholds, ablation grids, and decision rules are frozen in a signed pre-registration **before** the test split is touched. Anything decided after unblinding is labeled exploratory in the paper. (§4, §11) |
| L8 | **Behavioral fingerprint SKIPped in sandboxes** (PyPI build backend unavailable), making a key signal non-reproducible offline. | **R-HERMETIC.** Behavioral measurement runs in a **fully hermetic, offline container** with vendored build backends and pinned wheels; "SKIP" is a CI failure, not an accepted state, for any pair in the benchmark. (§10.2) |
| L9 | **Figures unfinished; some panels missing the discriminating signal.** | **R-FIG.** Figures are generated by the same `validate` path that gates numbers; a missing/blank panel fails CI. No figure is hand-edited. (§10.3) |
| L10 | **Review depth, not breadth, found the real defects.** Generous reviews that didn't reproduce missed both confirmed defects. | **R-ADVERSARIAL.** Acceptance requires **≥3 independent reproductions that each re-run the harness** (not read-only reviews), including one red-team tasked specifically with scope and validator-drift attacks. (§12) |

If a future reviewer cannot point to the requirement that prevents each of L1–L10 from recurring, the spec has failed.

---

## 3. Scope of claims (what CDA will and will not say)

**In scope.** (a) A measurement instrument that maps a code-pair to a graded derivation likelihood + CI at declared scopes. (b) Calibration of that instrument on a labeled multi-family benchmark, with honest classifier performance. (c) Application to held-out real disputes (incl. chardet v6/v7) reported *as test instances with their benchmark-calibrated interpretation*.

**Explicitly out of scope.** Any legal verdict or claim about whether a relicensing is valid. Training-data provenance of any model. Claims about "AI rewrites in general" beyond the sampled families and the constructed-derivative depth range. Authorship attribution of individuals. Non-source artifacts (binaries, weights).

**Necessary-vs-sufficient.** CDA is explicit that high derivation likelihood is *evidence consistent with* derivation, not proof; low likelihood is *evidence consistent with* independence, not proof of clean-room. The benchmark quantifies the false-positive/false-negative rates that bound these statements. This mirrors the legal frame (§19): reproducing *function* is fair-use reimplementation, so functional/structural/behavioral similarity is **filtered out**; only retention of *arbitrary protectable expression* is probative of copying. CDA measures the latter via the filter-then-score-residual test (§5.4).

---

## 4. Research questions & hypotheses (pre-registered)

Confirmatory (frozen before test split is unblinded). **All numeric thresholds below are placeholders set by the P0 power calculation (§9.6) before the freeze, not free-standing targets (§11).**

- **RQ1 (discrimination — the hard, dispute-relevant contrast).** Does the CDA score separate DERIVED from INDEPENDENT pairs **of the same specification/domain** on held-out families? The headline contrast is **within-domain DERIVED-vs-INDEPENDENT**, because both classes are high-retention and only *copying/provenance* separates them; cross-domain UNRELATED pairs are an easy separation and are **excluded from the headline AUC** (reported separately as the chance-floor sanity check, §9). Because ST/BH retention is by construction confounded on same-spec INDEPENDENT pairs, the **PB provenance family is expected to carry this separation** (§5.2); a headline that rode only ST/BH on this contrast would be measuring domain shape, not derivation. **H1:** within-domain test-set AUC ≥ θ_AUC with BCa 95% CI lower bound > θ_LB, where (θ_AUC, θ_LB) are fixed by the power calc at P0. (`power/POWER-ANALYSIS.md` gives the provisional operating point **θ_AUC = 0.85, θ_LB = 0.65, K_test ≥ 6 families at ≥5×5 pairs**, pending pilot confirmation of the true AUC; the original θ_LB = 0.70 is likely infeasible unless true AUC ≥ 0.90.)
- **RQ2 (scope sensitivity).** Do conclusions depend on declared scope? **H2:** for each ST/PB metric, report the score at `package` and `repo`; pre-declare that any metric whose within-domain DERIVED-vs-INDEPENDENT sign flips between scopes is reported as scope-confounded and excluded from the headline classifier.
- **RQ3 (calibration transfer).** Do thresholds fit on the train families generalize? **H3:** test-set Brier score and a binning-robust calibration error (§9.2) ≤ pre-declared bounds (set by the power calc); for every family-held-out fold that contains both classes, AUC > 0.5 (folds lacking a class are reported descriptively, not scored).
- **RQ4 (dose-response).** Does the score degrade monotonically with **independently-graded** constructed-derivation depth (§6.4)? **H4:** Spearman ρ between depth and score < 0 at p<0.05 (Holm-corrected), with seed-family as the resampling unit. RQ4 is explicitly limited to *constructed* fixtures and does not generalize to all derivation; the depth labels are graded by a process independent of the transform pipeline, so a negative ρ is a genuine test, not an artifact of construction.

Exploratory (declared as such, no confirmatory weight): **the chardet v6/v7 placement** on the calibrated scale — a single held-out pair whose per-pair interval is *expected to be wide and possibly inconclusive* at this benchmark scale; the contribution is the calibrated instrument, not a chardet verdict — plus per-family difficulty and which signal family carries the most discriminative load. (A minimal **pilot** (`pilot/`) already finds v6→v7 reads *independent-like* on ST/PB/BH, consistent with an "inconclusive / independent" placement and the §13 blind spot.)

**Falsification conditions are pre-stated:** if positive controls (DERIVED) do not score high, or null (UNRELATED) pairs score high, or the within-domain DERIVED-vs-INDEPENDENT AUC is at chance, the instrument is uninformative for the dispute-relevant contrast and the study reports that as the result.

---

## 5. Constructs & operationalization

### 5.1 The target construct
"Derivation" is operationalized as retention of structure/behavior. We **hypothesize** (not assume) an ordinal in expected retention, roughly `UNRELATED < INDEPENDENT < {EVOLVED, DERIVED-deep} < DERIVED-moderate < DERIVED-paraphrase`; the placement of EVOLVED relative to DERIVED-deep is **tested, not asserted into the labels** (an exploratory comparison, §4). The **class label** and, where constructed, the **depth label** — not the conjectured ordinal — are the ground truth the benchmark assigns each pair. CDA never claims to measure the legal construct "derivative work"; it measures retention of structure/behavior and reports calibrated likelihoods.

### 5.2 Signal families (fresh; not the predecessor's C06a–f)
Three orthogonal families, each metric defined by: *construct*, *declared scope parameter*, *granularity*, *invariances claimed*, *pre-registered failure mode*. Concrete metric set is frozen at pre-registration; the families are:

- **ST — Structural retention.** Graph/shape descriptors that survive identifier renaming and reformatting (call/import structure, control-flow shape distributions, per-unit AST shape matching). Each ST metric is scope-parametric and renaming-invariant *by design* — tested, not assumed (§7.3). **Pilot caveat (verification round 1):** only the *type*-based pilot measures (AST node-type shingles/histograms) are renaming-invariant; the pilot's *call-graph* topology/WL (`pilot/structural.py`, node identity = function **name**) are **not** renaming-invariant and are confounded by shared identifier vocabulary, and the §7.3 invariance test is a design requirement **not yet implemented**. **Cross-language capable** (PI decision, §18.4; *designed, not yet built — the pilot is Python-only, see Implementation status*): descriptors are computed over a language-agnostic normalized form so a cross-language port can be compared; cross-language structural equivalence is a *weaker* construct than within-language and is reported as its own stratum (§13), with BH as the more robust cross-language signal.
- **BH — Behavioral equivalence.** Black-box input→output agreement over a specified workload, measured in a hermetic container (§10.2). Granularity: exact, bucketed, and task-level agreement. This family does not read source and is therefore robust to source-level paraphrase. BH requires a **per-family adapter protocol** (§7.5): canonical I/O format, an input generator with a declared coverage floor (≥ pre-registered branch/path coverage on both sides), error/timeout normalization, and nondeterminism handling. Adapter authorship rules and adapter LOC/complexity are recorded as a possible confound. BH has **no source-file scope**, so the multi-scope rule (R-SCOPE) binds ST and PB only.
- **PB — Provenance & boundary (the copying-specific family; AFC "golden nugget").** Dependency/import boundary and literal/data-table carryover, **plus arbitrary-expression fingerprints a clean reimplementation has no functional reason to share**: distinctive identifiers, comments, docstrings, error/message strings, magic constants, **dead/unreachable code, shared bugs/defects, typos, watermarks** — the evidence courts treat as probative of copying (§19). Always reported at every declared scope. **This is the family that separates copying from independent reimplementation**: the pilot (`pilot/`) shows ST/BH similarity is shared by independent same-spec libraries (domain convergence — the AFC-filtered part), so they are *not* the copying signal. Reported as a **baseline-subtracted, filtered residual** (§5.4), never a raw overlap fraction.

Each metric outputs a value in a fixed range plus the inputs needed to recompute it. The **CDA score** is a calibrated combination (regularized logistic model fit on train families to the **binary DERIVED-vs-INDEPENDENT label only** — depth is held entirely out of fitting so RQ4 is an out-of-model test (§6.4, §9.5); coefficients are an artifact, never hardcoded — §10). Because ST and BH measure *retention*, they are confounded on same-spec INDEPENDENT pairs (clean-room implementations of one spec are high-retention by design); the **PB family is the one that can separate same-spec DERIVED from same-spec INDEPENDENT**. The pre-registered analysis therefore reports the **PB-only and ST/BH-only contrast separately**, so the paper can show whether the headline separation is provenance-driven (derivation) or shape-driven (domain convergence). This is the construct-validity core of RQ1 and a standing item in the red-team charter (§12).

### 5.3 The scope contract (R-SCOPE, the L1 fix)
- A **scope** is a declared, version-controlled file-set selector: `package` (importable shipped modules only — resolved **mechanically** from that ecosystem's packaging metadata (`pyproject.toml`/`setup.cfg`, or `package.json`/`Cargo.toml` for cross-language pairs, §18.4): the distribution's declared packages / entry points, i.e. the tree of the shipped top-level module, with the resolved file-set recorded verbatim in the manifest so "what is the package" is never a post-hoc choice), `module` (a named submodule), `repo` (whole worktree minus tests/build), or `custom` (explicit glob, recorded verbatim **and pre-registered before metric execution** — a `custom` scope chosen after seeing results is exploratory, never confirmatory).
- Every metric value is a triple `(metric, scope, value)`. The schema **rejects** any value lacking a scope.
- Every PB and ST metric **MUST** be reported at `package` and `repo`; the **scope-delta** `value@repo − value@package` is computed and surfaced. A large scope-delta is a published diagnostic, not a hidden artifact.
- Pre-registered rule: the headline classifier is fit and reported at `package` scope; `repo` scope is reported alongside as a sensitivity analysis. (Rationale: for an *importable shipped library* the package is the object of a derivation dispute; build/benchmark tooling is reported but never silently folded into the headline.) This "headline = package" convention is a **deliberate, falsifiable, P0-frozen choice (§11), not a neutral fact**: for any pair whose contested object is genuinely the whole repo (vendoring, tooling, bundled data), the pair's **claim-object scope is pre-declared per pair** in the manifest and reported as that pair's headline, with package/repo as sensitivity.

---

### 5.4 The derivation test (AFC-operationalized; the primary measure)
Pilot evidence (`pilot/PILOT-RESULTS.md`) shows **no aggregate similarity score robustly separates** an AI rewrite from independent reimplementation: the rewrite sits within the *independent spread* on every measure, and the same structural concept scores anywhere in [0.42, 0.99] by choice of measure. The one apparent exception — a WL-kernel variant at AUC 1.0 — is a **shared-identifier-vocabulary artifact**: `pilot/structural.py` builds call-graph node identity from function *names* (not renaming-invariant), so it merely detects that the chardet lineage shares method names while charset_normalizer does not; it also contradicts the predecessor's WL, so it is not a defensible structural signal. The instrument therefore does **not** rest on a raw similarity score. Mirroring the legal **Abstraction–Filtration–Comparison** test (§19), the primary CDA measure is:
1. **Enumerate** distinctive shared features across ST/BH/PB (identifiers, constants, comments, dead code, error strings, data-table fingerprints, behavioral quirks).
2. **Filter** features dictated by function, efficiency, compatibility/API, standards, or domain — operationalized as *features also shared by independent same-spec implementations* (subtract the baseline, §9). This is AFC **filtration** in code.
3. **Score the residual** of arbitrary, non-functional shared features by its **improbability under independent creation** ("striking similarity") — a count + calibrated improbability with CI, never an overlap fraction.

A large residual is evidence consistent with copying; a near-zero residual is the clean-reimplementation region. (chardet v6→v7: **13** identifiers survive API filtering per `pilot/residual.py` — but ~5 are stdlib/parameter false positives the current filtration does not remove, e.g. `ascii_letters`, `max_bytes`; the genuinely arbitrary remainder is a handful, e.g. `LEGACY_MAC`, `MODERN_WEB`, `NON_CJK`, `encoding_era` — small but non-zero, which is why the case is genuinely contestable, not clear-cut.) The benchmark calibrates the residual's distribution under each label class; aggregate ST/BH/PB scores become *inputs to the filter*, not the headline. **Empirical requirement (pilot iteration 7, `pilot/residual.py`):** the filtration must be *comprehensive* — language builtins, standard-library names, and **algorithm-canonical identifiers** must be filtered, and the independent baseline pool must be large; a thin baseline false-positived an independent pair (jellyfish↔textdistance) at residual 12 on textbook Jaro variable names. Directionally the measure already ranks correctly where filtration is adequate (EVOLVED 228 ≫ AI-rewrite 13; fork 7 > clean-reimpl 2), but it is **not validated** until filtration completeness + baseline size are pre-registered and the false-positive rate is measured on the benchmark's INDEPENDENT class.

---

## 6. The labeled lineage benchmark (R-BENCH, R-CONTROLS-IN)

The benchmark is the contribution that fixes external validity. It is a **versioned, content-addressed dataset of labeled code-pairs**.

### 6.1 Label classes (ground truth)
1. **DERIVED** — true derivation with known provenance: (a) *natural*: vendored copies, documented forks, and ports with a recorded lineage edge; (b) *constructed*: controlled rewrites of a seed library at graded depth (paraphrase / moderate / deep / re-architected), generated by a documented transform pipeline, carrying provenance banners and original license. Depth is a recorded label (enables RQ4).
2. **EVOLVED** — same project across adjacent releases (true derivation, conventional human evolution).
3. **INDEPENDENT** — implementations of the *same specification* by different authors/projects (e.g., multiple parsers for one wire format), graded by **independence confidence** (disjoint authorship, no shared VCS lineage, ideally different runtime). Because "clean-room" (author never read the reference) is the *dual* of the derivation problem and rarely verifiable for OSS, INDEPENDENT labels carry an evidence tier and a confidence grade; weakly-independent pairs are reported as a sensitivity subset, not folded silently into the headline. These are the hard negatives — same-spec, high-retention, no copying — the contrast on which RQ1 turns (§4).
4. **UNRELATED** — different domains entirely. Null/chance floor.

### 6.2 Family coverage (floor ≥8 families / ≥40 pairs; power-revised ≈18–24 families / ≈150–220 pairs, `power/`)
Families are chosen so that each label class is populated from *multiple* domains, breaking the n=1 problem. Indicative families (final set frozen at pre-registration; inputs retain their own upstream licenses — copyleft and disputed pairs are first-class, redistributed verbatim with notices or, where non-redistributable, by reference, §14):
- character-encoding detection (Mozilla `universalchardet` → `chardet` Python port → {chardet v7, `charset_normalizer`} — the motivating lineage, incl. the original Mozilla→non-Mozilla rewrite; held out as TEST);
- a wire-format parser family with many independent implementations (e.g., one config/serialization format);
- a hashing/encoding utility family;
- a small numeric/stats utility family;
- a CLI-argument or semver-style family;
- plus families selected to provide natural DERIVED edges (documented forks/ports) and clear UNRELATED pairs.

**Pre-registered selection criteria (frozen at P0, §11):** families must span ≥3 distinct domains; each of the 4 label classes must be populated from ≥2 families; the headline within-domain DERIVED-vs-INDEPENDENT contrast requires ≥2 domains that each contain *both* a DERIVED and an INDEPENDENT pair; a minimum **boundary-pair quota** (deep/re-architected constructed derivatives and high-overlap same-spec INDEPENDENT pairs) is set by the power calc, and AUC is reported separately on an "easy" vs "hard/boundary" stratum so a high score cannot be an artifact of easy pairs; ≥2 pairs per family for family-level splitting. **Excluded as inputs:** reimplementations of *proprietary or leaked* code (e.g. leaked-Claude-Code clones) — their provenance is proprietary, not a clean copyleft/permissive lineage that can be labeled. The candidate-family shortlist + scope rules are part of the P0 frozen artifact (§11, §18.1), with fallback families identified, and the benchmark ships a **datasheet** (motivation, composition, collection/labeling process, recommended uses, limitations, maintenance/governance, and the test-contamination policy once the benchmark is public).

Each pair records: family, label class, depth (if constructed), source URLs + tags + commit SHAs, accession date, upstream license + redistribution mode (verbatim-with-notices | metadata-only reference) + preserved notice files (§14), label evidence tier + independence/agreement grade (§6.5), and the exact file-set under each scope.

### 6.3 Splits (leakage control)
- **Family-level split**, not pair-level: entire families are assigned to train or test, so no library appears in both. This is the leakage guard (a pair-level split would let the model see a family's idiom in training and "recognize" it at test).
- The **chardet v6/v7** pair is a TEST instance and is **never** used to fit thresholds/coefficients.
- A pre-registered **k-fold leave-one-family-out** CV on the train set produces the calibration; the test set is unblinded once.

### 6.4 Constructed-derivative pipeline
The benchmark uses **two kinds of constructed positives, reported separately**: (a) **mechanical** derivatives from a documented, deterministic transform pipeline (paraphrase → re-architecture), reproducible byte-for-byte from a seed; and (b) **LLM-rewrite** fixtures that are representative of the "AI rewrite" use case but are **not seed-deterministic** — these are frozen as **content-addressed input artifacts** (here "determinism" means a fixed, hashed artifact, not regeneration from a seed), with the generation prompt + model + decoding params recorded. (No single artifact can be both a faithful AI rewrite and byte-regenerable; the spec keeps the two tracks distinct rather than conflating them — the predecessor never confronted this.) Both pipelines are built **only from the seed** (never see the negative/independent side), emit a per-fixture TRANSFORM-MANIFEST, retain the seed's license + a synthetic-artifact banner, and must include transforms that are **not trivially invertible by the ST metrics** (more than the renaming/reformatting the metrics already ignore — genuine semantics-preserving refactors). To break circularity, **depth labels are graded by a process independent of the transform pipeline** (human raters and/or a separate model rating retention depth) and used in confirmatory analysis only where the independent grade agrees; the score is never fit on depth (§5.2). These are the in-paper positive controls (R-CONTROLS-IN).

### 6.5 Labeling protocol (ground-truth credibility)
Natural DERIVED/EVOLVED/INDEPENDENT labels are evidence-backed adjudicated judgments, not raw "ground truth"; "ground truth" is reserved for constructed fixtures and directly documented vendoring/forks. Every natural pair is labeled by **≥2 independent labelers** against a written evidence rubric (minimum documentation per class: recorded lineage edge / fork graph / vendored directory for DERIVED; release ancestry for EVOLVED; independence evidence tier for INDEPENDENT). Inter-rater agreement (Cohen's/Fleiss' κ) is reported; disagreements are adjudicated; low-agreement or ambiguous pairs are labeled `ambiguous` and **excluded from confirmatory training/testing** (and the exclusion is logged). Label adjudicators do **not** see the CDA metric outputs, so labels recover provenance evidence rather than the features under test.

---

## 7. Measurement framework details

### 7.1 Determinism
All ST/PB metrics are deterministic functions of source bytes under a declared scope. BH metrics are deterministic given pinned dependency wheels + seed + hermetic container. Every run records input SHAs, tool versions, container digest, and seeds.

### 7.2 Pairwise symmetry & directionality
Metrics declare whether they are symmetric or directional; directional metrics are reported in both directions and the asymmetry is surfaced (denominator choice is a recorded parameter, never implicit).

### 7.3 Invariance testing (not assertion)
For each ST metric claiming renaming/reformatting invariance, the harness applies a renaming+reformatting transform to one side and asserts the metric moves < ε. An invariance that fails its own test is downgraded. (Avoids the predecessor's reliance on asserted invariances.)

### 7.4 Ablation grids (R-ABLATE, the L4 fix)
Every metric with an internal tunable (matcher key, granularity, normalization, threshold) ships a pre-registered grid. Results are reported as the **min/median/max envelope across the grid**. Ablation screening (incl. the demotion of sign-flipping metrics) is performed **on the train families only, before test unblinding**, so it is model selection on train, never feature selection on the test set; the included metric set is frozen before unblinding and the test ablation envelope is reported without changing the confirmatory classifier. Any metric whose DERIVED-vs-INDEPENDENT ordering flips inside its grid is reclassified as *exploratory* and removed from the confirmatory classifier. The envelope, not a single cell, is the published number.

### 7.5 BH adapter protocol (operationalizing behavioral equivalence)
For each family a pre-registered adapter defines: the input generator and its coverage floor (declared branch/path coverage required on both sides), the canonical output format, the agreement/oracle decision, the timeout policy, nondeterminism handling, and error normalization. Independent same-spec implementations with different APIs are reconciled through the adapter, not by reading source. Adapters are authored under a declared rule (ideally not by the metric authors), and adapter LOC/complexity is reported as a candidate confound. A pair with **no fair adapter** is retained ST/PB-only with BH **N/A** (§8, §10.2) — not dropped — so benchmark composition is not silently shaped by which libraries are easy to adapt.

---

## 8. Reporting discipline

- Every number in the paper is rendered from a single machine-readable results object (`results.json`) keyed by `(pair, metric, scope, granularity, ablation-cell)`.
- Scope is always shown. Scope-deltas are always shown for ST/PB.
- Negative, null, and SKIP-would-have-been results are reported. A genuine BH **SKIP** (the harness ran but could not measure) is a CI failure and cannot appear. A pair for which **no fair BH adapter or hermetic build exists** is **retained with ST/PB only and BH marked N/A** (not dropped), so the benchmark is not biased toward easy-to-build/easy-to-adapt libraries; the count and characteristics of N/A pairs are reported as a benchmark-validity threat (§13).
- No aggregate is reported without the per-pair rows that compose it being available in the artifact.

---

## 9. Statistical analysis plan (R-STATS)

1. **Primary classifier metric:** ROC-AUC for the **within-domain DERIVED-vs-INDEPENDENT** contrast on the held-out test families, BCa 95% CI (≥10k resamples, seeded), resampling at the **family (cluster) level** (the power sim implements a *first-order* cluster bootstrap — resample families, per-family AUC as the cluster observation; within-family resampling is a documented refinement **not yet implemented**, `power/POWER-ANALYSIS.md` §6) — because pairs within a family share idiom/dependencies/ancestry and are not independent; pair-level resampling would understate CI width. UNRELATED-vs-anything is reported separately as a chance-floor check and excluded from the headline AUC (§4).
2. **Calibration:** reliability diagram + Brier score + a **binning-robust calibration error** (adaptive-binning ECE with a declared bin rule, or a binless estimator) so the calibration bound is not an artifact of bin choice; isotonic or Platt scaling fit on **train only**. Calibration is to the *assigned* label, so its credibility is bounded by label quality (§6.5) — stated explicitly in the paper. The power calc (`power/`) shows fixed-bin ECE is positively **biased at realistic N** (≈0.16 at N=40 even when perfectly calibrated), so with a few dozen test pairs calibration is reported **descriptively** (binless estimator, wide intervals), not as a tight confirmatory bound.
3. **Effect sizes:** Cliff's δ and Vargha–Delaney Â₁₂ for every pre-declared pairwise class contrast (DERIVED vs INDEPENDENT, EVOLVED vs INDEPENDENT, etc.), with BCa CIs.
4. **Multiplicity:** the comparison family is **enumerated exhaustively at P0** (the RQ1 within-domain AUC, each pre-declared class contrast's δ/Â₁₂, the RQ3 calibration bounds, RQ4's ρ), grouped by estimand; Holm–Bonferroni control is applied within the declared family. No post-hoc comparisons enter the confirmatory set.
5. **Dose-response (RQ4):** Spearman ρ between **independently-graded** constructed depth (§6.4) and score, with **seed-family as the resampling unit**; depth curves reported per seed rather than as a single pooled p-value unless the power calc supports pooling. Constructed fixtures only. The power calc (`power/`) finds a seed-family sign test is **structurally incapable of p<0.05 below ~5 seeds**, so RQ4 needs **≥6–8 constructed seed families** (or a seed-clustered pooled-ρ bootstrap); the aggregation and seed count are fixed at P0.
6. **Power / sample size (runs *before* targets are frozen).** The pre-registered power calculation is performed **first**, at P0, and sets: the minimum number of **test** families, minimum pairs-per-class per test fold, the boundary-pair quota, and the achievable (θ_AUC, θ_LB) and calibration bounds of §4. The ≥40/≥8 figures are *lower* floors the power calc may raise; targets are never frozen independently of n. If the power calc shows the achievable floors cannot be met under the public/permissive + adapter constraints, the confirmatory outcome is pre-declared as "instrument under-powered for the declared families" — itself a valid, falsifiable result. **First power run** (`power/POWER-ANALYSIS.md`; simulation-based, assumed effect sizes): the family-clustered design needs **≥6 well-behaved test families** (the cluster bootstrap is unreliable at ≤3), and the **≥40/≥8 floors are ~4–5× too small** — a realistic benchmark is **≈18–24 families / ≈150–220 pairs**; θ_LB = 0.70 is underpowered unless true AUC ≥ 0.90, so the provisional target is θ_LB = 0.65. These figures are confirmed or replaced by the pilot before the P0 freeze.
7. **Small-n honesty:** any per-family or per-metric n below the power floor is reported as descriptive/exploratory with rule-of-three intervals, never as a population inference.
8. **Baseline comparator panel (mandatory).** At least one **trivial** baseline (token/MinHash/file-hash overlap) and one or more **established** clone/similarity detectors are run on the **identical splits** and appear as rows in every results table. Concrete panel: **JPlag** (already applied to the chardet case, §19) plus a token-based and a tree/PDG-based tool drawn from the Ragkhitwetsagul et al. comparison of code-similarity analysers (§19). The headline CDA result must beat the baseline panel by a pre-registered margin to count as discriminating (AUC 0.85 means little if MinHash scores 0.83). Single-family ablations (ST-only, BH-only, PB-only, size/domain-only) are reported so the paper shows the combined score adds value beyond trivial confounds. The baseline is also the **AFC filtration step** (§5.4, §19): features shared with independent same-spec implementations are the functionally/compatibility-dictated ones the law filters out, so the discriminating residual is *baseline-subtracted by construction*.
9. **Classifier floor.** If §7.4 demotion leaves <2 metrics in the confirmatory classifier, the pre-declared outcome is "instrument under-powered for the declared families," not a forced headline.

---

## 10. Reproducibility & artifact engineering

### 10.1 No-drift invariant (R-NODRIFT, the L2 fix)
- `make validate` **regenerates `results.json` from raw pinned inputs in the same run** (in a temp dir; it never trusts a committed results object), then asserts `rendered_number == recomputed_number` for **every** number in the manuscript, where `recomputed_number` is derived from that fresh run — **no published numeric result is ever a literal constant** (schema constants, thresholds, and test fixtures may be literals; published results may not). All number formatting is centralized in one renderer and the comparison is on the **formatted string**, so float/BCa equality is well-defined and there is no ad-hoc "close enough" tolerance.
- A registry maps each manuscript token (macro) to its source key in `results.json`. The manuscript body **forbids bare numerals**: every reported quantity *must* be a registered macro, and CI fails on any non-macro digit outside a small whitelist (years, reference numbers, equation constants). (Detecting "which numerals are claims" is unsolved; forbidding bare numerals is enforceable.) Stale and unmapped macros fail CI. Any prose comparison word ("same", "preserved", "different") adjacent to a macro must inherit and display that macro's **scope** and be backed by a declared threshold on the bound number — so a misleading sentence on a correct number (the predecessor's L1) also fails CI.
- `make validate` exits 0 **iff** all of: numbers match, figures regenerate non-empty, schema validates (scopes present), invariance tests pass, BH ran with no SKIP **for every pair with a defined adapter** (BH-N/A pairs are accounted, not skipped — §8). A non-zero exit blocks the "results" milestone.
- CI runs `make validate` on every commit touching harness, data, or manuscript. Green CI is a precondition for any reproduction/acceptance claim.

### 10.2 Hermetic behavioral measurement (R-HERMETIC, the L8 fix)
- BH metrics run inside a pinned container image (digest recorded, **architecture declared**) with all build backends + dependency wheels **and the language runtimes needed for cross-language pairs (e.g. Node, Rust toolchain, §18.4)** vendored; **no network at run time**, enforced by test; running third-party historical code is sandboxed with CPU/memory/time limits and filesystem isolation.
- The image is rebuilt reproducibly from a lockfile (explicit pinned wheels, `--no-deps`); the lockfile and image digest are artifacts.
- For every pair **with a defined BH adapter (§7.5)**, BH **MUST** produce MEASURED; a SKIP (harness ran but could not measure) is a CI failure. A pair with **no fair adapter/hermetic build** is retained ST/PB-only with BH **N/A** (§8) — not dropped — and the N/A set's size/characteristics are reported as a selection-bias threat (§13). A minimum retained benchmark size (set by the power calc) is a P1 gate.

### 10.3 Figures (R-FIG, the L9 fix)
- All figures are generated by the `validate` path from `results.json`. A figure with a missing series, blank panel, or a series not present in `results.json` fails CI.

### 10.4 Provenance & licensing
- Every input carries source URL, tag, SHA, **upstream license, redistribution mode (verbatim-with-notices | reference), preserved notice files**, accession date, size, content hash in a `MANIFEST` validated by schema.
- Constructed derivatives carry the seed's license + synthetic-artifact banner + transform manifest.

---

## 11. Pre-registration & blinding protocol (R-PREREG)

1. Author this spec → **run the power calculation first**, then freeze, in one P0-tagged artifact: RQs/hypotheses, the concrete **candidate-family shortlist + per-family scope rules + claim-object**, metrics + the **CDA score skeleton** (model family, eligible feature/scope/granularity/ablation universe), ablation grids, decision rules, the **enumerated comparison family**, the power-calc-derived numeric targets (θ_AUC, θ_LB, calibration bounds), and the labeling rubric. Nothing that determines the estimand, population, or power is left to P1.
2. Build the benchmark and assign **family-level** splits **by a precommitted random seed (or independent data steward)**. The **test families (incl. chardet) are sealed**: hashes recorded and escrowed with a third party at P1, and the training/calibration harness **physically cannot read paths under the test families** (enforced by the run harness, not by discipline), broken only by the single unblinding step. An audit log records every excluded candidate and why.
3. Fit calibration + classifier on train families via leave-one-family-out CV. All modeling decisions are made here, on train only.
4. **Single unblinding** of the test set → compute confirmatory results exactly as pre-registered.
5. Everything decided after step 4 is reported as exploratory.
5a. **Sealed-amendment procedure (post-unblinding bugs).** If a harness bug is found after unblinding, the change is logged, the **original frozen result is reported alongside the corrected one**, and the correction is labeled exploratory — so reality intruding does not silently burn the pre-registration.
6. The pre-registration document + git tag of the frozen state are artifacts cited in the paper.

---

## 12. Adversarial validation protocol (R-ADVERSARIAL, the L10 fix)

Acceptance requires **reproductions that run the harness**, not read-only reviews. Minimum:
- **≥3 independent reproducers**, each executing `make validate` from a clean checkout and confirming green + headline numbers; **≥1 must run outside the canonical container** (different base image / host Python) so a container-encoded error can surface (BH may differ there and must be reconciled). Coverage is assigned, not ad hoc: one reproducer validates label/split manifests, one the scope file-sets, one no-drift/macro scanning, one the statistics/calibration, one BH hermeticity.
- **≥1 dedicated red-team** with a written charter to attack specifically: (a) scope confounds (recompute every PB/ST metric at an alternate scope and look for sign flips), (b) validator drift (mutate a published number and confirm CI fails closed), (c) leakage (verify no family spans train/test, and check leakage channels: seed library, transform generator, language, spec, adapter author, shared deps), (d) matcher/ablation cherry-picking (recompute the envelope), (e) **construct validity** (is the within-domain DERIVED-vs-INDEPENDENT separation carried by PB/provenance, or is it ST/BH domain-shape convergence? recompute the contrast PB-only vs ST/BH-only), (f) registry tampering (re-point a macro at a favorable cell and confirm it is detectable).
- Each reproduction records what was re-run vs taken on trust. A review that does not re-run the harness does not count toward acceptance.
- The multi-model review is structured so depth is mandatory: each reviewer must reproduce ≥1 confirmatory number and ≥1 control, and must report the scope and ablation envelope they observed.

---

## 13. Threats to validity (designed-in)

- **Construct.** Structural/behavioral retention is a proxy for the legal construct; the benchmark quantifies its error rates and the paper states the gap explicitly. Mitigation: report calibrated likelihoods + CIs, never a verdict.
- **Internal / leakage.** Family-level splits; sealed test; thresholds fit on train only; invariance + scope tests. Mitigation surfaced as artifacts.
- **External.** ≥8 families across 4 classes; still bounded to the sampled domains and the constructed depth range — stated as the generalization bound.
- **Conclusion.** Effect sizes + multiplicity control + power floor; small-n cells flagged.
- **Construct (benchmark).** Constructed derivatives could be unrepresentative of real AI rewrites; mitigated by including *natural* DERIVED edges (forks/ports/vendored) alongside constructed ones, and reporting both separately.
- **Label noise (first-class threat).** Natural labels are adjudicated judgments with measured κ (§6.5); residual noise in INDEPENDENT (true-but-unlabeled influence) suppresses AUC, and calibration is only as good as the labels. Reported as a bound, with sensitivity to the weakly-independent subset.
- **Buildability / adapter selection bias.** Retaining BH-N/A pairs (rather than dropping them, §8) avoids shaping the population by buildability; the N/A set's size and characteristics are reported. The hermetic-build intersection still bounds the sampled population (small, modern, mostly-Python libraries), stated as the generalization population. Copyleft and license-disputed inputs are admitted as **first-class** (verbatim-with-notices, or by reference where non-redistributable), so the benchmark is **not** restricted to the permissive population and includes the dispute type CDA targets (§14).
- **Cross-language structural construct (weaker; PI-enabled, §18.4).** Comparing structure across languages (ST/PB on ports) is more assumption-laden than within-language: idiom and runtime differences can depress ST even for a true port, and PB carryover differs by ecosystem. **BH is the more robust cross-language signal.** Mitigation: cross-language and within-language pairs are **separate strata, never pooled in the headline**; the cross-language ST descriptor is validated on *known* ports (should score high) vs independent cross-language same-spec pairs (should score lower) before confirmatory use.
- **Training-data-mediated retention (retention ≠ copying).** Structural/behavioral retention can arise because the *model* was trained on the original, not because the new code was copied from it — demonstrated by the chardet case, where Claude reproduced the original's two-table state-machine design from training-data memory with no source read (§19). CDA scopes out a model's training-data provenance (§3), so a high ST/BH score is *evidence consistent with* derivation but cannot by itself distinguish direct copying from training-data transmission. The paper states this explicitly and leans on **PB** (literal/data-table carryover, which a model is far less likely to regenerate verbatim) to separate the two.
- **Known blind spot (stated as a bound).** Deep re-architecture + regenerated data tables can defeat structural and provenance signals; BH is the backstop, and where BH is also defeated CDA will (correctly) report low likelihood and the paper states this is the instrument's floor — and that the chardet v6/v7 case may land in exactly this blind spot. **The pilot confirms this empirically** (`pilot/`): on real chardet, v6→v7 scores ST at the *independent baseline*, PBt = 0 (tables regenerated), and BH in the independent band — statically indistinguishable from an independent reimplementation.

---

## 14. Ethics & legal posture

No legal advice or verdict. Code-only inputs; no human subjects. **Inputs retain their own upstream licenses; CDA never relicenses an input.** Copyleft (LGPL/GPL/AGPL) and license-*disputed* inputs are **first-class** benchmark inputs — they are the disputes CDA exists to study, so a permissive-only corpus would gut external validity and exclude the motivating case. Each input is redistributed **verbatim, with all original license texts and notices preserved**, as a segregated, separately-licensed corpus (**mere aggregation**): inputs are inert data/fixtures, read but never linked into or combined with the CDA harness, so no copyleft obligation propagates to CDA's own permissively-licensed code. Inputs whose license forbids redistribution, or whose license/provenance is unclear or under active legal dispute, are included by **metadata-only reference** (URL + tag + SHA, fetched at build time, not vendored) — a fallback, no longer the only path for copyleft. The motivating **chardet v6 (LGPL) / v7 (MIT)** pair is included as a redistributed, notice-preserving input. **Reimplementations of proprietary or leaked code are out of scope as inputs.** Constructed derivatives are clearly labeled synthetic and retain their seed's license. LLM/tool assistance in authoring and review is disclosed in full. The instrument is framed as decision-support evidence, with its error rates published.

---

## 15. Deliverables & repository layout

```
code-derivation-assay/
  SPECIFICATION.md            ← this file
  PREREGISTRATION.md          ← frozen RQs/metrics/scopes/grids/decision rules (git-tagged)
  power/                      ← P0 power analysis: power_analysis.py + POWER-ANALYSIS.md + results.json (§9.6)
  pilot/                      ← P0 pilot harness + PILOT-RESULTS.md + results.json (first real signal read on chardet)
  legal-framework.md          ← clean-room case law (Sega/Sony/Altai-AFC) → what to measure (§5.4, §19)
  family-census.md            ← P0 family-availability scouting (≥6 test families feasibility)
  benchmark/
    MANIFEST.schema.json      ← scope-aware, schema-validated
    DATASHEET.md              ← composition, collection/labeling, limits, governance (§6.2)
    families/<family>/<pair>/ ← labels, source refs (SHAs), scope file-sets, claim-object
    constructed/              ← mechanical + LLM-rewrite tracks + TRANSFORM-MANIFESTs (§6.4)
    adapters/<family>/        ← per-family BH adapter + coverage floor (R-BH, §7.5)
    labels/                   ← evidence tiers, ≥2-rater grades, κ, ambiguous-exclusion log (§6.5)
    splits.json               ← family-level train/test assignment (precommitted seed; test sealed)
  harness/
    scope.py                  ← the scope contract (R-SCOPE), mechanical package resolution
    signals_st.py             ← structural metrics (scope-parametric)
    signals_bh.py             ← hermetic behavioral metrics
    signals_pb.py             ← provenance/boundary (multi-scope mandatory)
    score.py                  ← calibrated classifier (binary fit; coeffs are artifacts)
    baseline.py               ← trivial + established comparators on identical splits (§9, item 8)
    run.py                    ← emits results.json keyed (pair,metric,scope,gran,ablation)
  validate/
    no_drift.py               ← R-NODRIFT: rendered == recomputed, fail-closed
    macro_registry.json       ← manuscript token → results key
    figures.py                ← R-FIG: figures from results.json
  container/                  ← hermetic image lockfile + build (R-HERMETIC)
  manuscript/
    main.tex                  ← numbers come only from macros bound to results.json
  Makefile                    ← `make benchmark | calibrate | test | validate | figures`
  ci/                         ← CI config (e.g. `.github/workflows/`); runs `make validate`; green gates "results"
```

---

## 16. Milestones (phased; each phase has a CI gate)

- **P0 — Spec & pre-registration.** This doc + PREREGISTRATION (incl. power calc, concrete family shortlist + scope rules, score skeleton, enumerated comparison family, power-derived targets) frozen + git tag. Gate: **independent peer sign-off** (a required, recorded gate, not advisory) on the lessons→requirements table (§2) and the power calc.
- **P1 — Benchmark construction.** ≥8 families, ≥40 labeled pairs (or the power-calc floor, whichever is larger), labeling protocol + κ reported, schema-valid MANIFESTs, family-level splits (precommitted seed), test sealed + hashes escrowed, both constructed tracks + manifests, baseline panel wired. Gate: schema + provenance CI green; **power floor and minimum retained size met after BH-N/A accounting**.
- **P2 — Harness + hermetic container.** ST/BH/PB metrics, scope contract, invariance + ablation grids; BH never SKIPs. Gate: `make test` green in container; invariance tests pass.
- **P3 — Calibration (train only).** LOFO-CV fit, calibration curves, coefficients as artifacts. Gate: no test-family bytes read; calibration metrics within pre-declared bounds on train.
- **P4 — Single unblinding + confirmatory results.** Compute RQ1–RQ4 exactly as pre-registered. Gate: `make validate` green (R-NODRIFT).
- **P5 — Manuscript + figures.** All numbers macro-bound; figures from results.json. Gate: no-drift + figure CI green.
- **P6 — Adversarial reproduction.** ≥3 harness-running reproductions + red-team charter (§12). Gate: all reproductions green; red-team attacks fail to break scope/drift/leakage.

---

## 17. Definition of done (acceptance criteria)

A reviewer must be able to verify **all** of:
1. `make validate` exits 0 from a clean checkout in the hermetic container; mutating any published number makes it exit non-zero (drift guard demonstrated).
2. Every manuscript number is macro-bound to `results.json`; no hardcoded expectations anywhere in `validate/`.
3. Every ST/PB metric is reported at ≥2 scopes with the scope-delta shown. Sign-flipping metrics are **reported and demoted per R-ABLATE** (a reporting/classifier-construction rule, not a pass/fail gate on the study); the study is "done" with the surviving classifier so long as **≥2 metrics survive demotion** and the headline **beats the baseline panel by the pre-registered margin** (§9, item 8). If <2 survive, the pre-declared "under-powered" outcome is reported as the result.
4. Headline result is the **within-domain DERIVED-vs-INDEPENDENT** test-set AUC with **family-clustered** BCa CIs across the held-out families, reported beside the baseline panel and the easy/hard strata; UNRELATED is a separate chance-floor row. chardet v6/v7 appears only as a sealed, **exploratory** TEST placement whose interval may be inconclusive.
5. Positive/negative/null controls are rows in the main tables, computed by the same path.
6. BH produced MEASURED (not SKIP) for every pair with a defined BH adapter; pairs with no fair adapter are retained ST/PB-only with BH N/A and counted (§7.5, §8).
7. Pre-registration tag predates the test unblinding commit; exploratory analyses are labeled as such.
8. ≥3 independent harness-running reproductions (≥1 out-of-container) + a red-team report on file (§12).
9. Labeling protocol executed with κ reported and ambiguous pairs excluded (§6.5); power calc on file and met; baseline panel present in every results table.

If any of 1–9 fails, the study is not done. These criteria are the operational negation of the predecessor's confirmed defects.

---

## 18. Open decision points for the principal investigator

1. **Final family list & seed libraries** — **resolved into the P0 frozen artifact (§11), not deferred to P1**: the concrete shortlist + per-family scope/claim-object rules + selection criteria (§6.2) are part of the pre-registration, with fallbacks; copyleft/disputed pairs are first-class inputs — verbatim-with-notices, or by reference where non-redistributable (§14); proprietary/leaked-code reimplementations are excluded.
2. **Confirmatory thresholds** (θ_AUC, θ_LB, calibration bounds) — **set by the power calculation, which runs first**, then frozen at P0 (§9.6, §11; first run in `power/POWER-ANALYSIS.md`, provisional θ_AUC=0.85/θ_LB=0.65 pending pilot); never frozen independently of n.
3. **Score model form** (logistic vs monotone GAM vs simple rule ensemble) — fix at P3 *on train only*; default: regularized logistic for interpretability.
4. **Container base + language coverage** — **cross-language ST/PB enabled (PI decision, v0.6; P0-frozen).** The harness ships per-language AST walkers + a language-agnostic structural-descriptor layer, so an edge that **actually crosses languages** (e.g. a JS original → Python port) is compared cross-language; within-language edges use the native walker, and cross-language is used *only where a derivation edge spans languages*. The chardet case remains Python↔Python. Cross-language and within-language results are reported as **separate strata** and never pooled in the headline (§13). The container carries the needed language runtimes (§10.2).
5. **Natural vs constructed DERIVED ratio** — include both, report separately; **minimum natural derivation edges = max(5, 25% of DERIVED)** so "AI rewrite" claims do not rest entirely on the constructed pipeline; mechanical vs LLM-rewrite constructed tracks reported separately (§6.4). Frozen at P0.

---

## 19. Related work & prior art (seeds the paper's Related Work)

CDA sits at the intersection of software birthmarking / clone detection, code provenance, and the new AI-relicensing debate. The eventual paper positions against at least:

- **AI-code provenance survey.** Fahad & Fuad, "Can we trust the source? A systematic review of watermarking and attribution for AI-generated code" (*Information & Software Technology*, 2026) — active (watermarking) vs passive (attribution/provenance) taxonomy. CDA is a passive, calibrated instrument.
- **Code-similarity benchmarking.** Ragkhitwetsagul et al., "A comparison of code similarity analysers" (*Empirical Software Engineering*) — 30 clone/plagiarism/provenance tools under obfuscation/modification; the methodological template for CDA's baseline panel (§9 item 8) and easy/hard strata.
- **Birthmarking & clone detection** (CDA's ST/BH families are modern source-level birthmarks): static/dynamic API birthmarks, behavior-based theft detection via system-call dependence graphs, multi-level reuse detection (ISRD), PDG-based semantic clone detection, and learning-based clone detection.
- **Clean-room copyright theory.** "Blameless Users in a Clean Room: Defining Copyright Protection for Generative Models" (2025) — formalizes clean-room copy protection for generative models; grounds CDA's necessary-vs-sufficient framing (§3).
- **LLM rewrite behaviour.** Studies of LLM robustness to semantics-preserving transforms (informs ST invariance testing, §7.3) and of memorization-vs-generalization via code rewriting (informs constructed-derivative representativeness, §6.4).
- **The motivating case, with prior analyses.** The chardet v7 dispute is documented from both sides: the maintainer's transcript-level account ("Everything Claude Saw") reporting **three near-zero similarity measures (token, JPlag, structural)** alongside disclosed source exposure and training-data knowledge, and critics' analyses pointing to **data-table / era-mapping carryover** from v6's `metadata/charsets.py`. CDA's contribution over these dueling ad-hoc analyses is a calibrated, scope-explicit, **PB-vs-ST-separated** measurement: the chardet pair in fact reads as **matcher-dependent ST [0.42–0.99] (not ≈0), PB literal carryover ~0, and a small non-zero arbitrary-name residual (13 raw)** — i.e. indistinguishable from independent on aggregate measures (`pilot/PILOT-RESULTS.md`), the structure-vs-provenance split these analyses talk past.

- **Legal doctrine (mirrored by the construct — `legal-framework.md`).** *Sega v. Accolade* (9th Cir. 1992) and *Sony v. Connectix* (9th Cir. 2000): reimplementing unprotected functional/interface elements, even with full access, is **fair use**. *Computer Associates v. Altai* (2d Cir. 1992): the **Abstraction–Filtration–Comparison** test — filter ideas / efficiency- and compatibility-dictated elements / standards / public-domain, then compare only the protectable **"golden nugget."** Copying is proven by **access + substantial/striking similarity**, with **fingerprint** evidence (shared bugs, comments, dead code, idiosyncratic naming, typos, watermarks) most probative. CDA's filter-then-score-residual primitive (§5.4) is AFC operationalized; the baseline panel (§9) is its **filtration** step.

(Full citations are assembled in the manuscript; this section fixes the prior-art set the design is positioned against.)

---

*This specification is a clean-slate design. It deliberately shares no signal definitions, corpora, harness code, prose, or numbers with the predecessor `chardet-relicense/` study; the predecessor informs only the lessons-to-requirements traceability in §2.*
