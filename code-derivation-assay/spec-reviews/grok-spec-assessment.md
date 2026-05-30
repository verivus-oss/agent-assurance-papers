# Grok 4.3 — Code Derivation Assay (CDA) Specification Assessment

**Date:** 2026-05-29 08:28:15 UTC  
**Reviewer:** Grok 4.3 (xAI, April 2026 release) — acting as **independent** expert reviewer with full permissions and tool access. This is my sole judgment; I did not read, consult, or coordinate with any other spec-review (claude-spec-assessment.md, codex-spec-assessment.md, gemini-spec-assessment.md, or mistral-spec-assessment.md) or any other reviewer.  
**Artifact under review:** `/srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay/SPECIFICATION.md` (DRAFT v0, 295 lines, 2026-05-29). This is a **pre-build spec/design review**, not a paper review. No implementation, data, harness, or results exist yet.  
**Background used (for defect context only; not re-reviewed):**  
- Predecessor confirmed defects (scope confound on C06b: repo-scope 0.667 vs package-scope 0.000 from benchmark scripts only; validator drift: `validate_numbers.py` + `make validate` exited non-zero on stale v1 literals 0.333/1000/etc.): `/srv/repos/external/verivus-oss/agent-assurance-papers/chardet-relicense/manuscript/reviews/SYNTHESIS.md` (reconciliation via independent re-runs) + `claude-review.md` + `codex-review.md` + `grok-review.md` excerpts + `main.tex` (0.667 claims, scope paragraphs, validation sections) + `CLAUDE.md`.  
- Rubric: `/srv/repos/external/verivus-oss/agent-assurance-papers/chardet-relicense/RESEARCH-QUALITY-GUIDE.md` (dimensions A–H, red flags, SIGSOFT Empirical Standards — Engineering Research primary + Benchmarking + General).  

**Method:** Adversarial, depth-first reading of the full SPEC against the predecessor’s two load-bearing defects, the L1–L10 traceability table, the rubric’s first principles (falsifiability, claims ≤ evidence, reproducibility as unit of trust, adversarial self-review), and the nine explicit assessment axes in the query. Every claim in the spec was pressure-tested for enforceability, researcher degrees of freedom (DoF), falsifiability, circularity, and implementation gaps. No rubber-stamping.

**Tools/MCPs actually used:** Direct filesystem tools only — `read_file` (full SPECIFICATION.md + RESEARCH-QUALITY-GUIDE.md + CLAUDE.md + main.tex targeted sections + SYNTHESIS.md + key excerpts from claude/codex/grok predecessor reviews), `grep` (cross-ref tracing of L1–L10, scope, validate, drift, 0.667, package/repo in SPEC + predecessor files), `list_dir` + `run_terminal_command` (find to confirm code-derivation-assay/ contains *only* the SPEC + five placeholder review stubs; no harness, data, or supporting code exists). No edits performed. Available MCPs (sqry, gtwy LLM gateway, exa, ref, cloudflare-docs) were not invoked; this review required no external search or LLM orchestration beyond the local documents and the documented predecessor defects.

---

## Executive Summary

The CDA specification is the most self-aware, defect-traceable research design I have reviewed in this lineage. It explicitly treats the predecessor’s two confirmed, undisclosed defects (L1 scope confound on the “strongest retained structural claim”; L2 validator drift on the advertised “every number is mechanically re-derived” path) as first-class engineering requirements rather than post-hoc lessons. The §2 table + §17 “operational negation” acceptance criteria are a genuine methodological advance.

However, the design does not yet close the root cause of those defects — **researcher degrees of freedom in scope definition, data composition, and measurement construction that occur after the claimed pre-registration freeze**. Several load-bearing elements (family selection timing, package-scope operationalization, BH workload, pair-level bootstrap despite family-level splits, numeric target deferral, and a data-dependent §17.3 acceptance gate) re-introduce the same class of problems the spec was written to prevent. The statistical plan contains a clear pseudoreplication error. The feasibility of the adversarial reproduction requirement (R-ADVERSARIAL) is asserted without cost or contingency analysis.

**Recommendation: approve with changes.** The core spine is strong enough that a major redesign is not required, but the blockers below must be resolved *before* P0 pre-registration freeze. Proceeding as written risks publishing another study whose headline claims rest on undisclosed scope/benchmark-construction choices and whose “green CI + independent repro” story is weaker than advertised.

---

## 1. Design Soundness & §2 Lessons→Requirements Table (L1–L10)

The table (SPECIFICATION.md:33–44) is the spec’s spine. Each L maps to an R that is *intended* to be normative (MUST/SHOULD). I evaluated each for actual preventive power vs. unenforceable/unfalsifiable/circular/papering.

**L1 / R-SCOPE (scope confound — the 0.667@repo vs 0.000@package C06b defect)** [major]  
SPECIFICATION.md:§5.3, §8, §2:35. The requirement is the strongest in the table on paper: every metric value is a `(metric, scope, value)` triple; schema rejects missing scope; every ST/PB metric **MUST** be reported at ≥2 scopes (min package + repo); scope-delta is a published diagnostic; headline classifier fixed at package scope with repo as sensitivity.  
**Problem:** Scope *definition* (what files constitute “package” for a given family) and scope *choice* (custom-glob, which families use which scope for training) remain researcher DoF. The schema enforcement appears to be a *reporting-time* check (§8), not a *computation-time* contract enforced by scope.py. A researcher can still compute single-scope runs, curate results.json, and only later satisfy the schema. The predecessor defect was not merely “undisclosed scope” — it was that the walk included non-library tooling and the construct claim (“third-party boundary of the shipped library”) did not match the measured object. R-SCOPE makes the delta visible but does not prevent the researcher from redefining “the shipped library” per family after seeing which definition produces the desired headline. This is a partial fix that papers over the deeper problem of scope-as-DoF.

**L2 / R-NODRIFT (validator drift — make validate exited 1 on stale v1 literals 0.333/1000/etc.)** [major]  
SPECIFICATION.md:§10.1, §2:36. Excellent intent: “No expected value is ever hardcoded. The validator derives expected values *from the artifacts of the same run*”; macro_registry.json maps manuscript tokens to results.json keys; unmapped numbers or stale macros fail CI; green CI is precondition for “results” status. This directly targets the `validate_numbers.py` failure mode.  
**Problems (two):** (1) The registry itself is a new mapping layer that can be edited post-hoc to point a macro at a “favorable” ablation cell or scope variant in results.json. (2) “Byte-for-byte” exact match on BCa CIs, floats, and seeded artifacts is brittle; any tolerance introduced creates a “close enough” regime where small drifts hide. The validator imports “the *same* extraction code” — shared bugs validate wrong numbers. R-NODRIFT closes the *literal constant* hole but opens a *curated-artifacts + registry* attack surface. Not yet sufficient to make the “every published number is regenerated by CI that fails closed” claim unfalsifiable.

**L3 / R-BENCH (n=1 external validity)** [minor]  
SPECIFICATION.md:§6, §2:37. Family-level split + ≥40 pairs / ≥8 families + 4 label classes + held-out chardet as TEST is a clear improvement. Positive/negative/null controls as first-class rows (R-CONTROLS-IN, L5) is also strong.  
**Risk:** The floor numbers are declared before the power calculation that is supposed to set them (§9.6 vs §6.2). See §4/§9 and consistency findings below.

**L4 / R-ABLATE (matcher-dependence — C06f flipped under annotation-blind matcher)** [minor]  
SPECIFICATION.md:§7.4, §2:38. Pre-registered ablation grid + envelope reporting + automatic demotion of flipping metrics to exploratory is a direct and enforceable response. Strong if the grid is frozen at P0 and exhaustive.

**L5 / R-CONTROLS-IN** [minor]  
SPECIFICATION.md:§6, §2:39. Positive controls (constructed + natural DERIVED) must appear in main tables via the same path. Good. Risk is that constructed controls are tautological (see §3 construct validity).

**L6 / R-STATS** [minor]  
SPECIFICATION.md:§9, §2:40. Cliff’s δ / Â₁₂ + BCa + Holm over pre-declared family is the correct upgrade from “eyeballed disjoint CIs.” See statistical plan section for the resampling-unit error.

**L7 / R-PREREG** [major]  
SPECIFICATION.md:§11, §4, §2:41. Single-unblinding protocol with sealed test families is the right structure. Undermined by post-prereg family selection and scope DoF (see consistency and benchmark sections).

**L8 / R-HERMETIC** [minor]  
SPECIFICATION.md:§10.2, §2:42. Vendored wheels + no-network container + “SKIP is CI failure” directly kills the predecessor’s sandbox excuse. Feasible for Python; execution risk for diversity.

**L9 / R-FIG** [nit]  
SPECIFICATION.md:§10.3, §2:43. Figures from validate path, blank panel fails CI. Good hygiene.

**L10 / R-ADVERSARIAL** [major]  
SPECIFICATION.md:§12, §2:44. Requiring ≥3 *harness-running* reproductions (not read-only) + dedicated red-team with charter explicitly attacking scope confounds, validator drift, leakage, and ablation cherry-picking is the correct meta-response to the SYNTHESIS finding that “review depth, not breadth, found the real defects.” This is one of the spec’s best ideas. Feasibility and timing (see below) are the gaps.

**Overall on the table:** The mapping is honest and the requirements are mostly the right *shape*. But L1, L2, L7, and L10 are only as strong as their *enforcement mechanisms* (scope.py computation contract, registry immutability + artifact provenance, P0 freeze on family list, and practical achievability of full harness repros). As written, several shift DoF rather than eliminate it.

---

## 2. Benchmark Design (§6)

**Labeling credibility (4 classes)** [major]  
SPECIFICATION.md:§6.1. The four classes (DERIVED natural+constructed, EVOLVED, INDEPENDENT same-spec clean-room, UNRELATED) are conceptually distinguishable. INDEPENDENT (multiple parsers for one wire format) is the best “true negative for copying while controlling domain-shape convergence.”  
**Gap:** No labeling protocol, no inter-annotator agreement procedure, no dispute-resolution process for *natural* DERIVED/INDEPENDENT edges. “Documented forks/ports” and “clean-room implementations” are exactly the contested claims in real relicensing disputes. If two experts disagree on whether a port counts as DERIVED or merely “inspired,” the ground-truth labels have unquantified noise. The benchmark (the stated contribution that fixes external validity) rests on an unstated assumption of unambiguous provenance. This is a construct-validity and credibility hole for the entire enterprise. The rubric’s Benchmarking standard (§6.3) and D1/D2 require the labels to be justified; here they are asserted.

**Family-level split adequacy vs leakage** [minor]  
SPECIFICATION.md:§6.3. Family-level (entire families to train or test) is the correct guard against the leakage the predecessor never had (pair-level would let the model see a family’s idiom). Chardet held out as TEST and never used for fitting. Good.

**Constructed-derivative representativeness** [major]  
SPECIFICATION.md:§6.4, §13. The pipeline is “built only from the seed (never sees the negative/independent side)”, seeded for determinism, emits TRANSFORM-MANIFEST, retains license + banner. Positive controls (R-CONTROLS-IN) are therefore in-paper.  
**Problems:** (1) The four depth levels (paraphrase → moderate → deep → re-architected) are defined by the researchers who also define the ST metrics. Even with good intent, the transforms can be (unconsciously) tuned so that ST fires on shallow ones and BH becomes the only backstop on deep ones — exactly the dose-response the study wants to publish for RQ4. (2) §13 acknowledges “could be unrepresentative of real AI rewrites” and mitigates with natural DERIVED edges reported separately. This is honest but does not solve the problem for the *constructed* portion that will dominate the positive class for power reasons. The benchmark’s claim to be a “ground-truth” for derivation likelihood is only as good as the claim that the synthetic pipeline distribution matches the real (LLM/agent) derivation distribution the instrument will later be applied to. No validation of that match is described.

**Sufficiency of ≥8 families / ≥40 pairs** [major]  
SPECIFICATION.md:§6.2, §9.6, §18.1. The numbers are floors; power calc will refine. With family-level split, effective sample size for generalization is the number of *families*, not pairs. 8 families total (some in train, chardet + others in test) is tiny for training a calibrated classifier (logistic on ST/BH/PB features + ablations + scopes), fitting isotonic/Platt scaling, LOFO-CV, and then claiming AUC 0.85 with BCa lower bound >0.70 on held-out families. The predecessor’s n=1 problem is “fixed” by moving to n=8 families, but 8 is still n=8 for external validity claims. The spec does not state a minimum number of *test* families or a minimum pairs-per-class after the power calc.

**Selection / confound / availability risks** [blocker-level risk]  
SPECIFICATION.md:§6.2, §18.1. “Indicative families” listed; “final set frozen at pre-registration.” But §16 P0 = spec + prereg freeze; P1 = benchmark construction (family list, pairs, splits, test sealed); §18.1 “Proposed shortlist to be drafted in P1.” This is a direct contradiction. Family composition — which domains, which natural DERIVED edges exist and are includable under permissive licenses, which families are easy vs hard for the signal families — is one of the largest researcher DoFs in a benchmark study. Selecting it *after* hypotheses, metrics, scopes, ablation grids, and numeric targets are frozen re-creates the exact selection problem the predecessor had with its single library. Availability (public + permissive only) further constrains the sample to whatever happens to be findable, not a principled sample of derivation disputes. No datasheet (rubric Benchmarking standard) is mentioned.

---

## 3. Construct Validity (§5)

**Is “derivation” operationalized defensibly?** [major]  
SPECIFICATION.md:§5.1. Latent ordinal UNRELATED < INDEPENDENT < EVOLVED ≈ DERIVED-deep < … < DERIVED-paraphrase “in expected structural+behavioral retention.” The paper never claims to measure the *legal* “derivative work” construct; it measures retention and reports calibrated likelihoods. This is correctly scoped (A2/A4 in the rubric).  
**Weakness:** The operationalization is still circular for the *constructed* positive class. The labels are generated by a transform pipeline whose depth axis is defined by the same researchers who define which structural changes ST metrics detect. High ST scores on shallow constructed pairs and low scores on deep ones can be partly tautological. BH (black-box, source-blind) is the honest backstop, but the CDA score is a “calibrated combination” of ST/BH/PB. If ST dominates the fit on train (because constructed labels were generated from structural transforms), the headline classifier can still be largely a structural-shape grader dressed up as a derivation grader.

**Is the ordinal-latent justified?** [minor]  
SPECIFICATION.md:§5.1. Reasonable proxy for the use cases (relicensing fights, clean-room claims, AI-rewrite provenance). Not justified beyond assertion + the benchmark labels themselves. The threats section (§13) does not treat label noise in the ordinal as a first-class threat.

**Do ST/BH/PB capture it? Circularity between label generation and measurement?** [major]  
SPECIFICATION.md:§5.2, §6.4. ST (structural retention, renaming-invariant by construction + tested), BH (behavioral equivalence in hermetic container, robust to source paraphrase), PB (provenance/boundary, explicitly multi-scope to fix L1). Orthogonal families are a good design.  
**Circularity risk (not fully mitigated):** Constructed DERIVED pairs are generated by transforms that *are* structural and provenance-preserving operations. ST and PB will fire on them by construction of the labels. The “ground truth” for the positive class is partly defined in the language of the metrics. The spec’s mitigation (natural DERIVED edges + separate reporting) is necessary but not sufficient unless the natural edges are numerous enough to dominate the positive class in the train set — which §18.5 leaves to the PI with no minimum. The benchmark quantifies error rates *conditional on its own labeling process*; applying those rates to real disputes assumes transportability of the label-measurement relationship.

---

## 4. Statistical Plan (§9) + RQs (§4)

**AUC/ECE/Brier/ρ targets appropriate/achievable/correctly pre-registered?** [blocker]  
SPECIFICATION.md:§4 (H1–H4), §9, §18.2. H1 (test AUC ≥0.85, BCa 95% lower >0.70) is ambitious but falsifiable. H4 (Spearman ρ <0 for depth vs score) is appropriate for dose-response. H3 (calibration transfer: Brier/ECE ≤ pre-declared bound) is the right RQ.  
**Fatal problems:**  
- The exact numeric bounds for H3 and the power-calc parameters that set the ≥40/≥8 floors are “set jointly at pre-registration” (§18.2) but P0 pre-reg precedes P1 benchmark construction and any data-driven power analysis. The confirmatory hypotheses are therefore not fully numeric at the claimed freeze point. This is HARKing-adjacent: the targets can be tuned after seeing pilot data or family difficulty in P1 while still claiming they were “pre-registered.”  
- No pre-declared sensitivity analysis for the power assumptions themselves.

**Power, multiplicity, resampling unit, calibration** [blocker]  
SPECIFICATION.md:§9.1, §9.4, §9.6, §6.3.  
- **Resampling unit error (pseudoreplication):** Primary AUC CI and all contrasts use BCa bootstrap “at the *pair* level within the test set.” But the design unit of generalization is the *family* (family-level split, LOFO-CV, claims about “AI rewrites in general” bounded to sampled families). Pairs within a family share domain, size, idiom, and (for constructed) transform lineage — they are not exchangeable. Pair-level bootstrap will understate variance and produce overconfident intervals for H1/H3. Clustered/family-block bootstrap or declaring the limitation and treating inference as descriptive is required. This is a clear statistical error against the rubric’s E2/E3/E6 and the predecessor’s small-n honesty lesson.  
- Multiplicity: Holm over “the declared comparison family” is good *if* the family is exhaustively enumerated at P0 (all RQ contrasts + all signal families + all scopes that enter the headline classifier). Not stated.  
- Small-n honesty (§9.7) is present but will be triggered often given 8 families.

**Overall statistical plan soundness:** The *shape* (effect sizes, BCa, pre-declared multiplicity, calibration diagrams) is the correct upgrade from the predecessor. The *execution details* (resampling unit, target timing, power-before-data-collection contradiction) contain errors and DoF that must be closed before P0.

---

## 5. Reproducibility Engineering (§10)

**Does R-NODRIFT genuinely close the drift hole or can it still go stale?** [major]  
SPECIFICATION.md:§10.1. Stronger than predecessor: no literals, derives expectations from same-run artifacts, macro_registry + fail-closed CI, “green CI precondition for results.”  
**Remaining attack surfaces (still open):**  
- Registry edits or post-hoc addition of mappings after seeing which ablation/scope cell “looks best.”  
- Selective curation of results.json (e.g., only BH runs that succeeded, only scope variants that support headline) before CI runs. The validator trusts the committed artifacts.  
- Shared-bug validation (validator imports same extraction code).  
- Float/CI exact-match brittleness (no tolerance policy stated).  
- “Unmapped numbers in the manuscript fail CI” assumes perfect registry maintenance; a forgotten macro can be the new drift vector.  
R-NODRIFT is a genuine improvement but is not yet “CI that fails closed” in the strong sense the spec advertises. It can still ratify a curated snapshot.

**Is hermetic/no-SKIP feasible?** [major execution risk]  
SPECIFICATION.md:§10.2. “BH MUST produce MEASURED; SKIP is CI failure; pair is fixed or removed at construction time (logged).” Vendored build backends + pinned wheels + no network + reproducible image digest.  
**Feasibility gaps:** For Python packages with only pure-Python or simple native deps, yes. For families with complex build systems, GPU requirements, or non-Python languages (future per §18.4), the container may be impossible or the “no SKIP” rule may force dropping the most interesting families. No cost/runtime model; no contingency if >X% of candidate pairs cannot be made hermetic. The predecessor’s C06e SKIP was accepted because the build backend was unavailable in sandboxes; here the rule is inverted, but the engineering burden is pushed to benchmark construction time. This may silently select for “easy to containerize” families — a new confound.

**Macro-registry / fail-closed failure modes** [major]  
See R-NODRIFT analysis above. The registry is the new single point of trust that the spec does not sufficiently harden (immutability after P0, cryptographic binding to results.json + harness version, red-team attack on registry tampering per §12 charter).

---

## 6. Pre-registration (§11) + Adversarial Validation (§12)

**Credible? Gameable? Is “single unblinding” realistic?** [major]  
SPECIFICATION.md:§11. Classic registered-report structure: freeze RQs/hypotheses/metrics/scopes/grids/decision rules/power at P0; build + seal test families in P1; calibrate on train only (P3); single unblinding (P4); everything after is exploratory. Pre-reg document + git tag are artifacts.  
**Gameability vectors (not closed):**  
- Family list, natural DERIVED edge selection, per-family “package” scope definitions, and constructed pipeline details all occur in P1 (§16, §18.1) *after* the P0 freeze. These choices determine which phenomena the benchmark can detect and which scope deltas will appear. The “test families are sealed” protects the *labels* of the held-out set but not the *definition of the population* from which both train and test are drawn.  
- Power calc and exact H3 bounds deferred to “pre-registration” but logically require P1 data or pilot runs.  
- In a small-team or solo-PI setting, the person who “seals” the test families in P1 is the same person who will later “unblind.” Social and procedural enforcement (independent sealer, hash published to a third party at P1, etc.) is not described.

**Does harness-running reproduction fix the depth problem (L10)?** [major practical risk]  
SPECIFICATION.md:§12. The requirement (≥3 independent full `make validate` runs from clean checkout in the hermetic container + dedicated red-team with written charter attacking exactly scope confounds, drift, leakage, and ablation cherry-picking) is the correct response to the SYNTHESIS finding that generous read-only reviews missed both defects. Depth is mandatory; each reviewer must reproduce ≥1 confirmatory number + ≥1 control and report scope/ablation envelope observed.  
**Problems:** No resource model. Building the container, vendoring wheels for 8+ families, and running BH (potentially minutes per pair × 40+ pairs) is non-trivial work. Volunteer reviewers (even motivated ones) may do spot-checks or take the container on trust — exactly the failure mode that produced the A/A+ grades in the predecessor reviews. The red-team charter is excellent on paper; whether anyone will actually perform the “mutate a published number and confirm CI fails closed” and “recompute every PB/ST at alternate scope” attacks at the required depth is unproven. R-ADVERSARIAL is only as good as its practical uptake.

---

## 7. Scope Contract (§5.3/§8)

**Does mandatory multi-scope reporting truly fix L1?** [major]  
SPECIFICATION.md:§5.3, §8. Every metric is scope-parametric; PB/ST **MUST** report package + repo + delta; schema rejects single-scope numbers; headline at package (rationale: “the shipped library is the object of a derivation dispute”); repo is sensitivity. Scope-delta is a published diagnostic.  
**It makes the problem visible; it does not eliminate the DoF.** The predecessor’s C06b 0.667 was produced entirely by repo-root benchmark/training scripts that were never part of the shipped package. R-SCOPE forces the delta to be shown, but:  
- Defining “package” (importable shipped modules only) for each family is itself a researcher choice. For Python packages with src/ layout, scripts/, data/, entry points, etc., reasonable people can disagree on the exact glob.  
- “custom-glob” is allowed and recorded verbatim — a researcher who wants a particular result can choose the glob that includes or excludes the problematic files and still satisfy the letter of the contract.  
- The headline classifier scope is declared as package, but if during P3 train calibration the researcher observes that repo-scope gives a cleaner separation (or avoids a flip), nothing in the spec *prevents* a quiet change of headline scope before P4 unblinding, as long as both are reported.  
- For some derivation disputes the object of interest *is* the whole repo (vendoring, tooling, build system). Forcing package scope for the headline may be the wrong construct for those cases.  
Multi-scope reporting is necessary and an improvement, but it converts an undisclosed confound into a disclosed researcher choice. The spec does not contain a pre-registered decision rule for when a large scope-delta invalidates a metric for the headline classifier (beyond “report it”).

**Edge cases (scope choice as researcher DoF)** [major]  
See above + L1 analysis. The contract is silent on how “package” is operationalized in the benchmark MANIFEST per family and who audits that the declared scope file-sets actually match the prose definition.

---

## 8. Feasibility & Cost — Buildable? Biggest Execution Risks, Underspecified/Hand-Waved, Missing Entirely

**Buildable?** Conditionally yes for a Python-only scope with motivated authors and access to permissive public code. The phased milestones (§16) with CI gates at each step are realistic scaffolding.

**Biggest execution risks:**  
- Acquiring 8+ permissive families with unambiguous natural DERIVED edges and clean-room INDEPENDENT pairs (legal review, maintainer contact, license compatibility).  
- Defining and implementing a single, fair, construct-valid BH workload that makes sense for parsers *and* hashers *and* semver libs *and* CLI arg libs *and* stats utilities. This is a research problem in its own right.  
- Hermetic container for BH across the full diversity without forcing SKIP or dropping families.  
- Achieving the power floor with family-level n.  
- Securing ≥3 independent *full* harness-running reproductions (container build + complete BH + red-team attacks) from non-authors who have no funding or career incentive.  
- The constructed pipeline producing a difficulty curve that is not an artifact of the ST metrics’ blind spots.

**Underspecified / hand-waved (critical):**  
- Exact “package” / “module” scope definition and per-family file-set rule (MANIFEST.schema.json will need this).  
- BH workload / task sample for non-parser families (§6, §7.2, §10.2).  
- CDA score model form, feature set (which ST/BH/PB metrics at which scopes/granularities/ablation cells enter the logistic?), regularization, and fitting procedure — even at the level of “we will pre-declare the skeleton at P0 and fit coefficients on train only.”  
- Power calculation assumptions and minimum test-family count.  
- Inter-annotator protocol or justification for natural label certainty.  
- Resource / runtime / cost model for full benchmark + one reproduction run.

**Missing entirely (should have been in a spec of this ambition):**  
- Benchmark datasheet (motivation, composition, collection process, labeling process, recommended uses, limitations, maintenance plan) per modern standards the rubric cites.  
- Contingency plan: what happens if power calc shows the floors are insufficient, or if <8 qualifying families can be found under the public+permissive constraint?  
- Pre-specification of how label noise (if any) in natural pairs will be propagated into the calibration and CIs.  
- Statistical handling of within-family dependence beyond the (incorrect) pair-level bootstrap.  
- Cost/sustainability model for the “macro-registry + hermetic container + full adversarial repro” reproducibility bar — who pays for the reviewer time and compute in perpetuity?  
- Explicit threat that the entire enterprise (ST + BH + PB calibrated on constructed + natural labels) may still be defeated by “deep re-architecture + regenerated data tables” (already named in §13) and that the chardet v6/v7 case may land in exactly that blind spot.

---

## 9. Internal Consistency

**Contradictions and misalignments (file:section):**  
- **Family freeze timing (blocker):** §6.2 “final set frozen at pre-registration” vs §16 (P0 = prereg freeze; P1 = benchmark construction, family list, splits, test sealed) vs §18.1 “Proposed shortlist to be drafted in P1.” The benchmark composition that determines external validity and the population to which AUC claims generalize is post-prereg. This contradicts the R-PREREG claim and the “single unblinding” protocol.  
- **Numeric targets timing (major):** §4 H3 “≤ pre-declared bound” and §9 power calc vs §18.2 “Confirmatory thresholds (the exact AUC/ECE/Brier bounds…) — set jointly at pre-registration with the power calculation.” P0 precedes the data needed for the power calc.  
- **§17.3 data-dependent gate (major):** “no metric used in the headline classifier flips sign across scope or its ablation grid” is an *acceptance criterion* for the study being “done.” This makes publication contingent on the data producing no flips for the metrics the team wants to keep. If flips occur (entirely possible, given L1/L4 history), the study either fails its own DoD or the team must retroactively demote signals and change the headline classifier — exactly the post-hoc narrative risk L7 was meant to kill. This should be a *reporting rule*, not a pass/fail gate on the entire study.  
- Minor: §6.2 states ≥40/≥8 as the requirement; §9.6 calls them “floors, refined by that calculation before data collection.” The power calc is supposed to come before data collection but is described as occurring in P1.  
- §5.3 declares a “pre-registered rule” for headline scope at package; it is not listed among the P0-frozen items in §11.  
- §13 treats the benchmark as quantifying the instrument’s error rates while §5/§6 leave the label-generation circularity and natural-label ambiguity unquantified.

**§16/§17 vs body enforcement:** The milestones and DoD are mostly consistent with the body and correctly position the adversarial gate (P6) as the final acceptance filter. The problem is that several DoD items (especially 17.3) can only be satisfied if the *data* cooperate with design assumptions that were not stress-tested for robustness to scope/family choice.

---

## Explicit List of What Would Make Me NOT Approve As-Is

I would **not** sign off on proceeding to pre-registration (P0) if any of the following remain open:

1. The P0/P1 timing contradiction on family list, splits, and per-family package-scope definitions is not resolved by moving the *concrete* family shortlist + rationale + scope operationalization rules into the P0 pre-registration artifact itself (with a “no changes after this tag” seal), before any construction or pilot measurement begins.

2. The statistical plan is not corrected to use family-aware / clustered resampling for all primary CIs and contrasts (or the limitation is explicitly declared and all confirmatory claims are downgraded to descriptive with rule-of-three intervals).

3. The BH workload definition, the precise “package” scope rule per family (with concrete glob examples in the MANIFEST schema), and the CDA score skeleton (model family, feature universe, which scopes/granularities/ablation cells are eligible) are not pre-specified at P0 before any train-family data is seen.

4. A documented labeling protocol + inter-annotator agreement procedure (or a justified claim that natural labels are unambiguous with audit trail) for all natural DERIVED/EVOLVED/INDEPENDENT pairs is not added to §6 and the benchmark deliverables.

5. A realistic resource/cost/contingency model demonstrates that R-ADVERSARIAL (≥3 independent full harness runs in the hermetic container + red-team attacks on scope, drift, leakage, and ablation) is achievable by non-authors, or an explicit fallback (e.g., funded reproduction bounty, reduced pair count for repros, or staged adversarial review) is adopted.

6. §17.3 is rewritten as a *reporting and classifier-construction rule* (flips are reported, affected metrics are demoted per R-ABLATE, headline refit is disclosed as exploratory if it changes the claim) rather than a pass/fail gate that can cause the entire study to fail its own definition of done if the data do not cooperate.

---

## Recommendation

**approve with changes**

The specification’s §2 traceability table, the clean-slate principle, the family-level leakage guard, the hermetic BH rule, the red-team charter, and the “operational negation” framing in §17 are genuine methodological contributions that directly address the predecessor’s failure modes. A major redesign is not required.

However, the blockers and major issues enumerated above (especially family-selection timing, scope DoF, statistical resampling error, BH workload underspecification, label credibility, R-NODRIFT gameability, and the data-dependent §17.3 gate) must be closed *before* the P0 pre-registration freeze. Proceeding without those fixes risks delivering another study whose central claims are later shown (by a sufficiently deep reproduction) to rest on undisclosed construction choices — exactly the pattern the spec was written to break.

If the six non-approval conditions are met, I would recommend proceeding to P0.

---

## Single Most Important Thing the Spec Gets Right

The explicit, falsifiable, one-to-one mapping in §2 of every confirmed predecessor defect (L1 scope confound, L2 validator drift, L3 n=1, L4 matcher-dependence, L5 hidden controls, L6 missing effect sizes, L7 HARKing, L8 hermetic SKIP, L9 unfinished figures, L10 insufficient review depth) to a hard, auditable requirement (R-SCOPE through R-ADVERSARIAL), with §17 DoD written as the operational negation of those exact defects. This is the first design in this repo lineage that treats post-mortem defects as *pre-build engineering constraints* rather than retrospective narrative. A future reviewer can point to a specific line in the spec and say “this requirement was supposed to prevent L1; it did not; here is the violation.” That property alone is worth preserving and strengthening.

---

## Single Most Dangerous Gap

The benchmark family list, train/test split assignment, natural DERIVED edge selection, and per-family “package” scope definitions are all P1 activities that occur *after* the P0 pre-registration freeze (§16, §18.1), while the confirmatory hypotheses (RQ1–RQ4), numeric targets, ablation grids, and headline classifier scope are claimed to be frozen at P0 (§4, §11). This re-creates — at the level of study *design* rather than post-hoc metric tweaking — the exact researcher degrees of freedom in scope choice and data composition that produced the predecessor’s two confirmed, load-bearing defects and the four-grade review spread. The “sealed test families” and single-unblinding protocol protect the *labels* of the held-out instances; they do not protect the *definition of the population* or the *measurement contract* from post-prereg researcher choice. Until the concrete families, splits, and scope rules are themselves part of the P0 frozen artifact, the spec’s claim to have eliminated the root cause of L1 and L2 is not yet credible.

---

*End of assessment. All citations are to the reviewed SPECIFICATION.md unless otherwise noted as predecessor background files. This review was performed in a single continuous session with no external coordination.*