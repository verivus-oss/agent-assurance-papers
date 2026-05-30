# Independent Spec/Design Assessment — Code Derivation Assay (CDA)

- **Reviewer:** claude-code (Claude Opus 4.8, `claude-opus-4-8`), independent design reviewer — sixth pass, written *after* reading the five prior assessments in `spec-reviews/`.
- **Date:** 2026-05-30 (UTC).
- **Under review:** `code-derivation-assay/SPECIFICATION.md` (DRAFT v0, pre-registration target), plus the five existing assessments (`claude`, `codex`, `grok`, `gemini`, `mistral`).
- **Mode:** Design review of a not-yet-built study. No harness, data, or results exist; all findings are design-level and cite `SPECIFICATION.md` sections. Unlike the other five, this pass also **adjudicates contradictions between the reviews** and concentrates on what they collectively under-weighted, to avoid re-deriving consensus that is already settled.
- **Tools actually used:** local filesystem (Read/Bash) only. No gateway/LLM dispatch, no `sqry`/`exa`; a spec review needs no code navigation.
- **Bottom line:** **Approve with substantial changes — not yet pre-registration-ready.** The §2 lessons→requirements→§17 chain is a genuine methodological advance and the architecture is the right one. But the benchmark's construct validity and the statistical plan are under-specified in ways that would let a precise-looking AUC stand on an ill-posed target. I land closest to **codex** (the sharpest review) and **grok**; well away from **gemini**, which is too lenient and contains a factual error (§2 below).

---

## 0. Summary judgment

CDA correctly diagnoses that the predecessor failed on *architecture*, not execution, and the §2 traceability table converts post-mortem defects into mechanical CI gates — the best property in this repo lineage. The fail-closed `make validate`, macro-binding, mandatory multi-scope reporting, hermetic/no-SKIP BH, and harness-running adversarial reproduction are all worth preserving.

The design is not yet ready to freeze for two reasons. First, a cluster of **must-fix-before-freeze** items that the five reviews already name and largely agree on (resampling unit, power/target ordering, baseline comparator, constructed-derivative circularity, labeling protocol/IRR, P0/P1 timing, the §17.3 gate). Second — and not crisply named by any prior review — an **architectural** mismatch: the instrument measures *retention* while the headline contrast (DERIVED vs INDEPENDENT) is a *copying/provenance* question, and the two come apart precisely on the INDEPENDENT class that RQ1 hinges on (M1 below).

---

## 1. Settled consensus — confirmed, not re-litigated

These were raised independently by three or more of the prior reviewers and I concur with each. I list them compactly because they are already well-argued upstream; the spec author should treat them as decided.

1. **Resampling unit is statistically wrong (pseudoreplication).** §9.1 bootstraps at the *pair* level; §6.3 makes the *family* the independent unit. Pairs within a family share idiom/dependencies/ancestry → overconfident CIs exactly where H1's lower bound lives. Require family-clustered/hierarchical bootstrap. (claude S2, codex, grok §4.)
2. **Frozen §4 targets contradict the deferred power calc.** §4 freezes "AUC ≥ 0.85, CI lower bound > 0.70" at P0; §9.6/§18.2 defer the power calc and call ≥40/≥8 a refinable floor. Order it: power calc → n → achievable targets, all inside the freeze. (claude S1, codex, grok, mistral.)
3. **Constructed-derivative circularity.** The pipeline generates both the derivatives and their depth labels, authored by the same people who define ST/PB; RQ4 is partly tautological. Grade depth independently; fit the score on binary DERIVED-vs-INDEPENDENT only and hold depth out of fitting. (codex blocker, mistral blocker, claude C2, grok §3, gemini F3.)
4. **No baseline comparator.** AUC ≥ 0.85 is uninterpretable without a trivial (token/MinHash) and an established (clone-detector) baseline on the *identical* splits; the predecessor at least ran JPlag. (claude B1 near-blocker, codex major.)
5. **No labeling protocol / inter-rater reliability** for natural pairs. Unmeasured label noise undermines every downstream metric. (claude B6, codex, grok, mistral.)
6. **§17.3 is a circular, data-dependent acceptance gate.** "No headline metric flips sign" is automatically true via §7.4 demotion, yet can fail the whole DoD if the data don't cooperate. Make it a reporting/classifier-construction rule, not pass/fail. (grok consistency, claude §9.)
7. **Family list and per-family `package` scope are defined in P1, after the P0 freeze** (§16 vs §18.1). The sealed test set protects *labels*, not the *population definition* or the scope glob, both of which remain researcher DoF. (grok's "single most dangerous gap," codex blocker #7.)

If items 1–7 are not folded into the frozen P0 artifact, the pre-registration is incoherent or under-powered before any data is collected.

---

## 2. Adjudicating the contradictions between the five reviews

The author will see a split and needs a tiebreak.

**2.1 Resampling unit — the reviews directly conflict; the majority is correct.**
- **claude, codex, grok** identify pair-level bootstrap as a pseudoreplication error.
- **mistral explicitly endorses the error**: "Pair-level resampling — correct (avoids pseudo-replication)" (§4.2). That is backwards.
- **gemini** calls the statistical plan "exemplary" and misses it entirely.

Adjudication: **the three are right.** With a family-level split and claims bounded to sampled families, the exchangeable unit is the family; pair-level resampling understates variance. Discard the mistral/gemini reading on this point.

**2.2 Overall recommendation spread — gemini is the unreliable outlier.** Recommendations run: codex (*major redesign*), claude/grok/mistral (*approve with substantial changes*), gemini (*approve to proceed, no blocking issues*). gemini both rates the flawed statistics "exemplary" and rates R-NODRIFT a complete fix without noting the macro-detection and same-run-artifact holes the others found. Weight codex/grok/claude/mistral over gemini wherever they disagree.

**2.3 Severity of R-NODRIFT residual risk — codex/grok/claude are right that "same-run artifacts" is not yet airtight.** gemini/mistral call R-NODRIFT a clean fix; codex, grok, and claude note it can still ratify a *curated/committed* `results.json` unless `make validate` regenerates results from raw pinned inputs in the same run and the macro layer forbids bare numerals. The stricter reading should win — it is the difference between guarding transcription and guarding regeneration.

---

## 3. What all five reviews under-weighted or missed

These are the findings that justify a sixth pass.

**M1 — [major, architectural] The construct (retention) is the wrong instrument for the headline contrast (DERIVED vs INDEPENDENT).** No prior review states this crisply. INDEPENDENT is defined (§6.1.3) as clean-room implementations of the *same specification* — i.e. **high structural and behavioral retention, zero copying**. The CDA score measures *retention* (ST + BH dominate; §5.2). A faithful retention instrument should therefore score INDEPENDENT pairs **high** — the wrong answer for RQ1. The only family that can separate high-retention-independent from high-retention-derived is **PB** (literal/data-table carryover, dependency-boundary provenance) — and PB is exactly the family §13 admits is defeated by re-derivation and regenerated tables. So the headline contrast leans on the most easily-defeated signal, while ST/BH are *confounded by design* on the INDEPENDENT class. The benchmark conflates two different tasks — "are A and B similar?" (retention, what is measured) vs "is B copied from A?" (provenance, what is labeled) — and they diverge precisely where RQ1 is decided. The reviews touch the symptom (mistral's ST domain-convergence, claude's B3 easy/hard strata) but not the root: a retention instrument pointed at a copying question. **Fix:** either redefine the estimand to "retention" and stop calling the output a derivation likelihood, or elevate a provenance-first signal to carry the DERIVED-vs-INDEPENDENT separation and report that contrast **within-domain** (DERIVED vs INDEPENDENT for the *same* spec/family) as the real test, with cross-domain UNRELATED excluded from the headline so it cannot inflate AUC.

**M2 — [major] Determinism vs AI-representativeness is a true contradiction, not merely a representativeness threat.** §6.4/§7.1 require the constructed pipeline be "seeded for determinism" and byte-reproducible under R-NODRIFT/R-HERMETIC; §0/§13 motivate constructed derivatives as proxies for **AI rewrites**. A deterministic mechanical transform is reproducible but is *not* an AI rewrite; an LLM rewrite is representative but not seed-deterministic in the byte-exact sense the reproducibility requirements demand. One artifact cannot hold both properties. **Fix:** pick one — mechanical transforms (honest that they are non-AI and bound RQ4 to "constructed depth," not "AI derivation"), *or* LLM-generated fixtures frozen as content-addressed inputs (representative, but "determinism" means "fixed artifact," not "regenerable from seed"). The spec currently claims both implicitly.

**M3 — [major] The permissive-only input rule excludes the disputes the instrument exists to adjudicate.** §6/§6.2/§14 require inputs be public-domain / permissively licensed only. But relicensing and derivation fights — the stated use case — are disproportionately **copyleft** (that is why they are fought). chardet itself sits in an LGPL→MIT relicensing context; whether it even qualifies under the benchmark's own input rule is unclear. The benchmark would then calibrate on a population (permissive) systematically different from the population it adjudicates (copyleft disputes), and the motivating TEST case may be inadmissible under the study's own constraint. codex flags copyleft exclusion as a *minor*; given the use case it is a headline-aimed external-validity hole and a possible internal inconsistency. **Fix:** state the population bound explicitly, and decide (and justify) whether metadata-only references to non-redistributable copyleft pairs are admissible so the benchmark can include the dispute type it targets.

**M4 — [major] The motivating case collapses to a single test pair with an uninterpretably wide interval.** chardet v6/v7 is **one pair**, held out, reported as a per-pair likelihood + CI on a scale calibrated from a few test families. Given every reviewer's power concerns, that CI will be wide; the study's narrative reason for existing (place chardet on a calibrated scale) may yield "inconclusive." That is an honest outcome, but §0 still leans on chardet as the hook. **Fix:** state up front that the motivating case is *expected* to be inconclusive at this scale, that the contribution is the instrument + benchmark rather than a chardet verdict, and reconcile this with §4 (which lists chardet as exploratory) vs §6 (a sealed confirmatory TEST instance) — those two framings currently disagree.

**M5 — [minor] Byte-for-byte equality over floats has no tolerance/formatting policy.** §10.1 asserts exact `rendered == recomputed` over BCa floats and seeded artifacts with no centralized rounding/format authority; this will produce false CI failures, and any ad-hoc tolerance reintroduces a "close enough" regime that hides small drift. grok half-touched this. **Fix:** centralize all number formatting in one renderer and compare formatted strings, or declare a single tolerance policy as a frozen artifact.

---

## 4. Net assessment

The §2→§17 "operational negation" chain is a real advance and should be preserved verbatim. But the design has one architectural problem the prior reviews circle without naming (M1: a retention instrument pointed at a copying question), plus the cluster of freeze-blocking items in §1 that they do name. I would **not** proceed to P0 until:

1. **M1 is answered** — redefine the estimand or elevate a provenance-first signal, and report the DERIVED-vs-INDEPENDENT contrast within-domain.
2. **Items 1–7 of §1** are resolved inside the frozen artifact (especially the resampling unit, the power-calc-before-targets ordering, the baseline panel, and moving the family list + per-family scope rules into the P0 seal).
3. **M2–M4** are reconciled (determinism vs AI proxy; permissive-only vs copyleft use case; the single-test-pair expectation for chardet).

**Single most important thing the spec gets right:** the §2 lessons→requirements→§17-acceptance chain with fail-closed CI and mandatory multi-scope reporting — it makes the two *confirmed* predecessor defects (numeric drift, hidden scope) structurally hard to repeat and ties acceptance to demonstrably negating them.

**Single most dangerous gap:** the instrument measures structural/behavioral *retention*, but the headline label task is *copying/derivation*, and these diverge exactly on the INDEPENDENT (clean-room, same-spec) class on which RQ1 turns — so a high AUC could reflect easy UNRELATED/natural-fork separability while the instrument remains blind to the hard, dispute-relevant contrast it was built for. Fix the estimand-vs-label mismatch first; the benchmark, statistics, and calibration are all downstream of it.

---

*Independent design assessment by reviewer `claude-code` (Claude Opus 4.8), 2026-05-30 UTC. Sixth pass; written after reading the five prior `spec-reviews/` assessments, with which it concurs on §1 and which it adjudicates in §2. No harness exists to execute; all findings cite `SPECIFICATION.md` sections.*
