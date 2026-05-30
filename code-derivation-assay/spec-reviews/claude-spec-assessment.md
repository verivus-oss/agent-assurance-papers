# Independent Spec/Design Assessment — Code Derivation Assay (CDA)

- **Reviewer:** claude (Claude Opus 4.8, `claude-opus-4-8`), independent design reviewer.
- **Date:** 2026-05-29 (UTC).
- **Under review:** `code-derivation-assay/SPECIFICATION.md` (DRAFT v0, pre-registration target).
- **Mode:** Design review of a not-yet-built study. I judge whether the design will hold up, not results (none exist).
- **Tools actually available:** local filesystem (Read/Grep/Bash), the spec + predecessor reviews/`SYNTHESIS.md` + `RESEARCH-QUALITY-GUIDE.md` in context. The `gtwy` gateway MCP was **down** during this review, so this is an in-session direct assessment by the claude model rather than a gateway-dispatched job; `sqry`/`exa` were not used (a spec review needs no code navigation).
- **Bottom line:** **Approve with changes (substantial).** The architecture is sound and the lessons→requirements traceability is the best thing here, but there are ~10 [major] issues and one near-blocker omission (no baseline comparator) that must be resolved *before* pre-registration freezes, because several touch the frozen objects (targets, comparison family, scope definition).

---

## 0. Summary judgment

CDA correctly diagnoses that the predecessor failed on *architecture*, not execution, and it attacks the right two defects (scope confound, validator drift) plus the real external-validity hole (n=1). The fail-closed CI + macro-binding + mandatory multi-scope reporting are genuinely good and would make L1/L2 structurally hard to repeat **for numbers**. But the spec's weakest region is exactly the part the whole study now rests on — **benchmark ground-truth quality** — and it under-defends it. A high test-set AUC is currently uninterpretable (no baseline) and could be an artifact of an easy, biased benchmark. There is also an internal contradiction between the frozen §4 targets and the §9.6 deferred power calc that must be resolved before pre-registration, or the pre-registration is incoherent.

---

## 1. Design soundness & the fix table (§2, L1–L10)

**L2 / R-NODRIFT — strong, but two holes. [major]**
- §10.1 says expected values are "derived live from artifacts — never a literal constant." Ambiguous whether "artifacts" means a *committed* `results.json` or one *regenerated from inputs in the same CI invocation*. If `validate` reads a committed `results.json`, the whole chain can pass against a stale committed artifact — the drift just moves up one layer. **Fix:** mandate that `make validate` regenerates `results.json` from pinned inputs in the same run and forbids reading any committed results object.
- **R-NODRIFT guards numbers, not prose.** The predecessor's L1 defect was a *prose interpretation* ("external boundary largely the same") riding on a number whose scope was hidden — not a mistyped digit. R-NODRIFT alone would **not** have caught L1. The numeric macro could have been correct-and-bound while the sentence was misleading. **Fix:** require that any prose claim adjacent to a macro inherit and display that macro's scope, and that qualitative comparison words ("same", "different", "preserved") be backed by a declared threshold on a bound number. As written, L1 and L2 are sold as a package but are largely independent; only the §5.3 scope contract addresses L1, and it is weaker than R-NODRIFT (see §7 below).

**L7 / R-PREREG "single unblinding" — no provision for the bug-at-unblinding case. [major]** Pre-registered work routinely discovers a harness bug *after* unblinding. §11 step 4 ("Single unblinding … compute confirmatory results exactly as pre-registered") has no escape valve. If a bug is found post-unblinding, the spec gives you two bad options: ship known-wrong confirmatory numbers, or silently re-run (burning the pre-registration). **Fix:** define a "sealed amendment" procedure — any post-unblinding change is logged, the original frozen result is reported alongside the corrected one, and the correction is labeled exploratory. Without this, the protocol will be violated the first time reality intrudes.

**L8 / R-HERMETIC no-SKIP — fixes a reproducibility hole by creating a selection bias. [major]** §10.2/§8 require BH=MEASURED for every pair and drop pairs that can't build hermetically ("logged"). This biases the benchmark toward *easy-to-build* libraries (recent, pure-Python, light deps) and against old/native-extension/heavy-dep libraries — which are disproportionately the *interesting* lineage cases. Logging the drop does not neutralize the bias. **Fix:** report drop counts and characteristics as a benchmark-validity threat, and pre-register that BH-undefined pairs are retained with ST/PB only (BH marked N/A) rather than dropped, so the benchmark composition isn't silently shaped by buildability.

**L10 / R-ADVERSARIAL — "independent" reproductions in one container aren't independent. [major]** §12 requires ≥3 reproductions "in the hermetic container." Three runs of the same container reproduce the same hidden container-encoded error three times and all agree. That is replication, not independent validation. **Fix:** require ≥1 reproduction *outside* the canonical container (different base image / host Python) so a container-level bug can surface, accepting that BH may differ there and must be reconciled.

**L4 / R-ABLATE — the demotion rule can empty the classifier. [minor→major]** §7.4 auto-demotes any metric that flips DERIVED-vs-INDEPENDENT sign across its grid. Good for honesty, but there is no floor: if most signals flip, the confirmatory classifier could be left with one or zero metrics, and §4's H1 becomes unmeetable. **Fix:** pre-register a fallback (e.g., if <2 metrics survive, the confirmatory result is "instrument under-powered for the declared families" — itself a valid, falsifiable outcome).

**L1, L3 — assessed in §§2.7, 2.2 below.** L5 (R-CONTROLS-IN), L6 (R-STATS), L9 (R-FIG) are sound as stated (L6 has a resampling error — see §4).

---

## 2. Benchmark design (§6) — the weakest and most load-bearing region

**B1. No baseline comparator. [major, near-blocker]** Nothing in §6/§9 requires comparing CDA's classifier to (a) a trivial baseline (token/MinHash similarity, file-hash overlap) or (b) an off-the-shelf clone detector. The predecessor at least ran JPlag. "Test-set AUC ≥ 0.85" is **uninterpretable** without knowing what a dumb baseline scores on the *same* benchmark — if MinHash gets 0.83, CDA's structural machinery is barely earning its keep; if MinHash gets 0.55, 0.85 is meaningful. The rubric weights baselines heavily (dimension D). **Fix:** add a required baseline panel to §9 and a row to every results table; pre-register at least one trivial and one established baseline on the identical splits.

**B2. INDEPENDENT negatives are weakly grounded. [major]** §6.1.3 defines INDEPENDENT as "clean-room implementations of the same specification." Establishing that an implementation is *actually* clean-room (its author never read the reference) is the **dual of the derivation problem** — i.e., the very thing CDA claims to measure. Some "independent" parsers are written by people who read the canonical one. The benchmark's negative labels are therefore noisy in a direction that *suppresses* AUC (true-but-unlabeled influence looks like a false positive) or, worse, are curated to look independent and inflate it. **Fix:** define operational independence criteria (disjoint authorship, no shared lineage in VCS, ideally different language/runtime), grade negatives by independence confidence, and report sensitivity to the weakly-independent subset.

**B3. Easy-positive / easy-negative bias inflates AUC. [major]** Natural DERIVED edges (forks, vendored copies, ports) are *high-retention, easy* positives; UNRELATED pairs are *easy* negatives. Real disputed cases (and chardet v6/v7 itself) live near the **boundary** — exactly the region §6 under-samples. A benchmark dominated by easy pairs yields a high AUC that does not transfer to the hard cases the instrument exists for. **Fix:** pre-register a minimum quota of *boundary* pairs (deep/re-architected constructed derivatives; INDEPENDENT pairs with high domain-shape overlap) and report AUC separately on an "easy" vs "hard" stratum.

**B4. Cell counts are too thin for the §4 CI target. [major]** ≥40 pairs / ≥8 families / 4 classes ≈ 10 pairs/class total, and family-level splitting (§6.3) holds out *whole families*, so the TEST set may contain only a few families → perhaps ~10–15 test pairs total, a handful per class. A BCa 95% AUC CI on ~8 positives vs ~8 negatives is very wide; "CI lower bound > 0.70" (H1) is likely **infeasible** at the ≥40 floor. This collides with §9.6 (see §4/§9 below). **Fix:** raise the floor materially (the power calc must drive this *before* §4 targets are frozen), or relax H1 to a point-estimate threshold with a reported (wide) CI.

**B5. Availability risk is real and compounding. [major feasibility]** The family criteria conjoin: public + permissive + known lineage edge + multiple independent same-spec implementations + hermetically buildable + (default) Python-only (§18.4). That intersection is demanding; ≥8 such families with populated *boundary* strata may be hard to source. **Fix:** scout and list candidate families *before* pre-registration (it's already §18.1 but should gate P0→P1), with fallback families identified.

**B6. No inter-rater reliability for human labels. [major]** Natural-pair labels (DERIVED/EVOLVED/INDEPENDENT) are human judgments, yet §6 specifies no labeling protocol, no multiple raters, no agreement statistic. Ground truth with unmeasured label noise undermines every downstream metric (AUC, ECE, Brier all measured against it). **Fix:** ≥2 independent labelers, report Cohen's/Fleiss' κ, adjudicate disagreements, exclude or down-weight low-agreement pairs.

---

## 3. Construct validity (§5)

**C1. The ordinal-latent is an unvalidated assumption presented as ground truth. [major]** §5.1 asserts an order `UNRELATED < INDEPENDENT < EVOLVED ≈ DERIVED-deep < DERIVED-moderate < DERIVED-paraphrase`. Two problems: (i) `EVOLVED ≈ DERIVED-deep` is an *equivalence asserted into the ground truth*, not measured — if false, the labels are internally inconsistent; (ii) the order is a hypothesis, but it is also used to *construct* the benchmark and to motivate RQ4. **Fix:** state the ordinal as a hypothesis to be tested, not a labeling axiom; drop the `≈` claim or make it an explicitly exploratory comparison.

**C2. Circularity between label/score and RQ4. [major]** If the CDA score is a logistic model fit to the class labels (§5.2), and depth correlates with class, then "score decreases with depth" (RQ4/H4) is partly baked in by construction. The dose-response would be partially tautological. **Fix:** fit the score on the *binary* DERIVED-vs-INDEPENDENT task only, hold depth entirely out of fitting, and treat RQ4 as out-of-model generalization — then ρ(depth, score) is a genuine test.

**C3. "Derivation likelihood" vs "label-class probability." [minor→major]** Calibration (ECE/Brier) is measured against assigned labels, so CDA calibrates to "probability of the assigned class," not "probability of true latent derivation." Given B2/B6 label noise, the calibration story is only as good as the labels. Worth stating explicitly so the paper doesn't over-read calibration as truth-calibration.

---

## 4. Statistical plan (§9) + RQs/hypotheses (§4)

**S1. Frozen §4 targets contradict the deferred §9.6 power calc. [major, must fix before pre-reg]** §4 fixes H1 = "AUC ≥ 0.85, CI lower bound > 0.70"; §9.6 says the power calc (which sets n) comes *after* and the ≥40 figure is a floor "refined before data collection." You cannot pre-freeze a CI-lower-bound target independent of n while also saying n is determined later by power. Either order it (power calc → n → then set achievable targets, all before the freeze) or the pre-registration is internally incoherent. This is the single most important consistency fix.

**S2. Resampling unit is statistically wrong. [major]** §9.1 bootstraps "at the pair level within the test set." Pairs within a family share idiom and are **not independent**; pair-level bootstrap underestimates CI width when a test family contributes several correlated pairs. **Fix:** clustered/family-level bootstrap (resample families, then pairs within), matching the family-level split rationale.

**S3. Heterogeneous Holm family. [minor]** §9.4 applies Holm across "the comparison family," which mixes AUC, calibration, δ contrasts, and ρ — different estimands. Holm is valid but coarse here. Consider grouping by estimand or documenting why a single family is appropriate.

**S4. ECE under-specified. [minor]** ECE is binning-sensitive; specify adaptive vs fixed bins and bin count, or use a binning-robust calibration error. Otherwise the §3/§4 ECE bound is ambiguous.

---

## 5. Reproducibility engineering (§10)

**RE1. Macro-detection is an unsolved, brittle subproblem. [major]** §10.1/§10.3: "Unmapped numbers in the manuscript fail CI." Detecting which numerals in LaTeX are *claims* (vs years, version tags, equation constants, citation years, axis ticks) is a hard parsing problem. If detection misses a number, that number is unguarded and mutating it would *not* fail CI — which silently voids §17 acceptance item 1. **Fix:** invert the burden — forbid bare numerals in the manuscript body via a lint rule; every reported quantity *must* be a registered macro, and a CI check fails on any non-macro digit outside a whitelist (years, ref numbers). That is enforceable; "detect all claim-numbers" is not.

**RE2. Otherwise strong.** Fail-closed `make validate`, no-network BH, figures-from-results are all correct and directly negate L2/L8/L9 — provided RE1 and the "regenerate not read" fix (§1, L2) land.

---

## 6. Pre-registration (§11) & adversarial validation (§12)

Covered above: §11 needs the post-unblinding amendment procedure (L7 [major]); §12 needs an out-of-container reproduction (L10 [major]). Additionally:

**P1. "Sealed test families" integrity is asserted, not enforced. [minor]** §11.2 records hashes and says test families are "not inspected for tuning," but nothing *prevents* inspection — it's an honor-system claim. For a study whose whole point is verifiability, consider a mechanical guard: the training harness physically cannot read paths under `families/<test>/` (enforced by the run harness, not discipline), broken only by the single unblinding step.

---

## 7. Scope contract (§5.3, §8)

**SC1. `package` scope is not mechanically defined. [major]** §5.3 says `package` = "importable shipped modules only," but the predecessor's v7 used a `src/chardet` layout while v6 used top-level `chardet/`. Real repos have namespace packages, multiple top-level packages, vendored subpackages, and `src/` layouts. Without a deterministic rule for *what files are the package*, "package scope" reintroduces a researcher degree of freedom — the very L1 problem, relocated. **Fix:** define package scope mechanically (e.g., from declared entry points / `pyproject` packaging metadata / the directory containing the imported top-level `__init__.py`), and record the resolved file-set in the manifest.

**SC2. Mandatory multi-scope reporting mitigates but does not eliminate the confound. [minor]** Reporting at ≥2 scopes + a fixed "headline = package" rule (§5.3) is a real improvement over the predecessor (which hid the scope). But "headline = package" is itself a pre-registered *choice*; for a repo where the dispute genuinely concerns repo-level artifacts, package-scope could under-report. The rule is defensible and, crucially, *disclosed* — but call it a deliberate, falsifiable convention, not a neutral fact.

---

## 8. Feasibility, what's hand-waved, what's missing

- **Missing: baseline comparator (B1) — most important omission.**
- **Missing: labeling protocol / IRR (B6).**
- **Missing: cost/effort/compute budget.** §16 lists phases but no estimate of person-effort or compute; benchmark construction (P1) + hermetic BH for dozens of pairs is the long pole and is unscoped. [major feasibility]
- **Missing: benchmark governance.** No statement of how the benchmark versions over time, who may add pairs, or how test-set contamination is prevented once the benchmark is public (publishing the test families lets future models/tools train on them). [major for a benchmark contribution]
- **Hand-waved: the actual ST/BH/PB metrics.** §5.2 lists families but defers the concrete metric set to pre-registration. That's acceptable for v0, but the study's discriminative power lives entirely in those undefined metrics, so the spec cannot yet be judged on whether it *can* hit H1 — only on whether its scaffolding is sound. State this limitation explicitly.
- **Hand-waved: multi-language.** §18.4 defaults Python-only, but INDEPENDENT same-spec implementations and ports are often cross-language; Python-only further tightens B5 availability. The interaction isn't acknowledged.

---

## 9. Internal consistency

- **§4 ↔ §9.6 target/power ordering — contradiction. [major]** (See S1.)
- **§17 DoD item 3 is circular. [minor]** "No metric used in the headline flips sign across scope or its ablation grid" is *automatically* true because §7.4 demotes any flipping metric out of the headline. It restates a construction rule as if it were an independent acceptance test. Make it bite: e.g., "≥2 metrics survive demotion," or "the headline AUC exceeds the baseline panel by a pre-registered margin."
- **§17 item 1 depends on the unsolved RE1.** Its guarantee ("mutating any published number fails CI") holds only if every number is macro-bound, which depends on macro-detection (RE1). Fix RE1 and item 1 becomes real.
- **§16 milestones vs body — mostly consistent**; P3's "no test-family bytes read" gate is good but, per P1 above, is currently honor-system.

---

## 10. What would make me NOT approve as-is (must-fix before pre-registration freeze)

1. **Add a baseline comparator panel** (trivial + established) on the identical splits. [B1]
2. **Resolve the §4↔§9.6 ordering**: run the power calc first; set achievable, frozen targets after. [S1]
3. **Define `package` scope mechanically** and record the resolved file-set. [SC1]
4. **Fix the resampling unit** to family-clustered bootstrap. [S2]
5. **Specify the labeling protocol + IRR** for natural pairs; grade INDEPENDENT by independence confidence. [B2, B6]
6. **Pre-register a boundary-pair quota** and easy/hard stratified reporting. [B3]
7. **Add the post-unblinding amendment procedure.** [L7]
8. **Require ≥1 out-of-container reproduction.** [L10]
9. **Invert macro enforcement** (forbid bare numerals) so §17.1 is real. [RE1]
10. **Decide BH-undefined handling** (retain as N/A vs drop) to avoid buildability selection bias. [L8]

Items 2, 3, 5, 6 touch objects that §11 *freezes*, so they cannot be deferred to "after pre-registration" — they must land in the freeze.

---

## 11. Recommendation

**Approve with changes (substantial) — proceed to a revised pre-registration, not to building.** The architecture is the right one and the fix-traceability is genuinely strong; this is not a redesign. But the ten must-fixes above — especially the baseline comparator and the power/target ordering — are prerequisites to a *coherent* pre-registration, because freezing the current §4/§9/§6 as-is would lock in an incoherent and under-powered confirmatory plan.

**Single most important thing the spec gets right:** the §2 lessons→requirements→§17-acceptance chain with fail-closed CI and mandatory multi-scope reporting. It converts "we should be careful" into mechanical gates that make the two *confirmed* predecessor defects (numeric drift, hidden scope) structurally hard to repeat — and it ties acceptance to demonstrably negating them.

**Single most dangerous gap:** benchmark ground-truth quality is both the foundation of every headline number and the least-defended part of the design. With no baseline comparator, weakly-grounded INDEPENDENT negatives, an easy-pair bias, buildability-driven selection bias, and no inter-rater reliability, a high test-set AUC could be a property of an easy, biased, noisily-labeled benchmark rather than of the instrument. Fix the benchmark's construct validity first; everything else is downstream of it.

---

*Independent design assessment by reviewer `claude` (Claude Opus 4.8), 2026-05-29 UTC. Produced in-session because the `gtwy` gateway was unavailable; no harness exists to execute, so all findings are design-level and cite `SPECIFICATION.md` sections.*
