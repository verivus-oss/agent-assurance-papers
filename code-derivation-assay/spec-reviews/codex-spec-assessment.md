# codex (GPT-5 Codex) — UTC 2026-05-29T08:25:44Z

## Scope And Method

I reviewed `/srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay/SPECIFICATION.md` as a study design, not as a completed paper or implementation. I read the predecessor synthesis and five reviews under `chardet-relicense/manuscript/reviews/`, the rubric at `chardet-relicense/RESEARCH-QUALITY-GUIDE.md`, and predecessor context in `chardet-relicense/CLAUDE.md` and `chardet-relicense/manuscript/main.tex` only to verify whether the new spec really addresses the two confirmed failures: the scope confound and stale validator.

Tools/MCPs actually used: local filesystem and shell via `exec_command`, parallel shell reads via `multi_tool_use.parallel`, and `apply_patch` to write this file. I did not use web search, GitHub, sqry, exa, or any MCP resource/tool for this assessment.

## Recommendation

**Recommendation: major redesign needed before pre-registration.**

The spec gets the right high-level direction: multi-family benchmark, explicit scope, pre-registration, controls in the main tables, hermetic behavioral measurement, and a fail-closed validation path. It is a real improvement over the predecessor’s architecture.

I would not approve it as-is because several load-bearing parts are still aspirational rather than enforceable: the label ontology does not cleanly match the proposed "derivation likelihood" construct, the statistical plan uses the wrong resampling unit and is not credible at the proposed floor of 40 pairs / 8 families, constructed derivatives risk becoming both the source of labels and the thing the metrics are tuned to detect, and the preregistration/blinding protocol is not realistic while major design choices remain open.

The single most important thing the spec gets right: **it makes scope a first-class data dimension and rejects silent single-scope reporting** (`SPECIFICATION.md:§2 L1`, `SPECIFICATION.md:§5.3`, `SPECIFICATION.md:§8`, `SPECIFICATION.md:§17`).

The single most dangerous gap: **the benchmark labels and sampling plan are not yet strong enough to support a calibrated classifier, so the study could produce a precise-looking AUC for an ill-defined target** (`SPECIFICATION.md:§5.1`, `SPECIFICATION.md:§6`, `SPECIFICATION.md:§9`).

## What Would Make Me Not Approve As-Is

I would not approve pre-registration until all of these are fixed:

1. A written label adjudication protocol defines what evidence is sufficient for `DERIVED`, `EVOLVED`, `INDEPENDENT`, and `UNRELATED`, including multiple raters, disagreement handling, provenance evidence tiers, and exclusion criteria (`SPECIFICATION.md:§6.1`).
2. The target prediction problem is fixed: binary derivation, ordinal retention, or multi-class lineage. Right now the construct says ordinal retention, the RQs say DERIVED vs INDEPENDENT AUC, the benchmark includes EVOLVED and UNRELATED, and the thesis promises "derivation likelihood" (`SPECIFICATION.md:§0`, `SPECIFICATION.md:§4`, `SPECIFICATION.md:§5.1`, `SPECIFICATION.md:§6.1`).
3. Power and sample-size calculations are done before freezing the minimum benchmark; `≥40 pairs across ≥8 families` is not accepted as a floor unless it is shown to support family-level test CIs, calibration, and dose-response analyses (`SPECIFICATION.md:§6.2`, `SPECIFICATION.md:§9.6`, `SPECIFICATION.md:§17.4`).
4. The resampling and inference unit is changed from pair-level to family-level or hierarchical resampling, with sensitivity analyses for within-family correlation (`SPECIFICATION.md:§6.3`, `SPECIFICATION.md:§9.1`).
5. Constructed derivatives are insulated from circularity: generation methods, depth labels, and metrics must be developed independently enough that the classifier cannot learn transform artifacts; natural and constructed positives must be reported separately with a pre-set ratio (`SPECIFICATION.md:§6.4`, `SPECIFICATION.md:§13`, `SPECIFICATION.md:§18.5`).
6. The behavioral measurement plan includes family-specific adapter/workload protocols. "BH agreement" is not operational enough for independent implementations with different APIs (`SPECIFICATION.md:§5.2`, `SPECIFICATION.md:§10.2`, `SPECIFICATION.md:§18.4`).
7. The preregistration protocol is made realistic: final families, metrics, thresholds, score model, ECE/Brier bounds, ablation grids, and split rules must be frozen or explicitly staged; "single unblinding" cannot be claimed while the same team constructs and inspects all candidate families (`SPECIFICATION.md:§11`, `SPECIFICATION.md:§18`).
8. Scope policy is generalized beyond "package is headline" so the object of dispute is predeclared per family/pair; otherwise scope remains a researcher degree of freedom even though it is reported (`SPECIFICATION.md:§5.3`, `SPECIFICATION.md:§8`, `SPECIFICATION.md:§17.3`).

## Lessons-To-Requirements Audit

| Lesson | Severity | Assessment |
|---|---|---|
| L1 / R-SCOPE | **[major]** | Mostly real prevention. Required scope fields, `package`+`repo` reporting, and scope-deltas would have exposed the predecessor's C06b inversion (`SPECIFICATION.md:§2 L1`, `SPECIFICATION.md:§5.3`, `SPECIFICATION.md:§8`). But it still leaves scope choice as a design degree of freedom: `custom` scopes can be cherry-picked, and "package as headline" is not always the correct dispute object. |
| L2 / R-NODRIFT | **[major]** | Directionally strong: no hardcoded expectations, macro registry, fail-closed CI, and mutation testing address the predecessor validator drift (`SPECIFICATION.md:§2 L2`, `SPECIFICATION.md:§10.1`, `SPECIFICATION.md:§17.1`). Remaining weakness: deriving "expected" values from artifacts of the same run can become circular unless validation regenerates `results.json` from raw pinned inputs and separately verifies the manuscript against that fresh run. |
| L3 / R-BENCH | **[blocker]** | Multi-family benchmarking is the right fix for n=1, but the proposed minimum is not justified and the labels are not yet credible enough to be "ground truth" (`SPECIFICATION.md:§2 L3`, `SPECIFICATION.md:§6`). A benchmark can be larger than n=1 and still be underpowered, leaky, or mislabeled. |
| L4 / R-ABLATE | **[major]** | Pre-registered ablation grids and demotion on sign flip would have reduced the predecessor's matcher-dependence problem (`SPECIFICATION.md:§2 L4`, `SPECIFICATION.md:§7.4`). But "sign flip" is underspecified for a calibrated multimetric classifier, and demoting metrics after seeing instability can itself become a model-selection step unless the rule is applied train-only or before test unblinding. |
| L5 / R-CONTROLS-IN | **[minor]** | This is a real fix. Positive, negative, and null controls as first-class rows computed by the same path directly address the predecessor's hidden positive controls (`SPECIFICATION.md:§2 L5`, `SPECIFICATION.md:§6`, `SPECIFICATION.md:§8`, `SPECIFICATION.md:§17.5`). |
| L6 / R-STATS | **[major]** | Effect sizes, BCa intervals, Holm correction, and preregistered comparison families are the right ingredients (`SPECIFICATION.md:§2 L6`, `SPECIFICATION.md:§9`). The current plan still has statistical errors: pair-level bootstrap is the wrong unit, calibration metrics need much larger samples, and the target comparison family is not fully defined. |
| L7 / R-PREREG | **[major]** | The confirmatory/exploratory split is conceptually correct (`SPECIFICATION.md:§2 L7`, `SPECIFICATION.md:§4`, `SPECIFICATION.md:§11`). But the spec still defers final families, thresholds, score model, bounds, and natural-vs-constructed ratio to future decisions (`SPECIFICATION.md:§18`), so it is not yet a preregistration-ready design. |
| L8 / R-HERMETIC | **[major]** | Hermetic, offline BH with no accepted `SKIP` would close the predecessor's sandbox failure (`SPECIFICATION.md:§2 L8`, `SPECIFICATION.md:§10.2`). Feasibility is the concern: many public libraries will not build hermetically without nontrivial adapters, old toolchains, system packages, or networked fixtures, and dropping unbuildable pairs creates selection bias. |
| L9 / R-FIG | **[minor]** | Generating figures from `results.json` and failing blank/missing panels is a real fix (`SPECIFICATION.md:§2 L9`, `SPECIFICATION.md:§10.3`). The spec should define concrete figure validation checks, not only "non-empty"; otherwise a plot can be nonblank but semantically wrong. |
| L10 / R-ADVERSARIAL | **[major]** | Harness-running reproduction and a red-team charter are much stronger than read-only review (`SPECIFICATION.md:§2 L10`, `SPECIFICATION.md:§12`, `SPECIFICATION.md:§17.8`). But "each reviewer reproduces ≥1 number and ≥1 control" is too shallow to guarantee depth, and reproducing the harness does not validate labels, split integrity, construct choice, or statistical power. |

## Severity-Ranked Findings

### Blockers

**[blocker] The benchmark label ontology does not support the promised target without redesign.**  
Citation: `SPECIFICATION.md:§0`, `SPECIFICATION.md:§4`, `SPECIFICATION.md:§5.1`, `SPECIFICATION.md:§6.1`.

The thesis promises a "graded derivation likelihood"; the construct defines an ordinal scale of expected structural/behavioral retention; RQ1 tests DERIVED vs INDEPENDENT AUC; the benchmark includes DERIVED, EVOLVED, INDEPENDENT, and UNRELATED. These are not the same target.

`EVOLVED` is also true derivation in a causal/provenance sense. `DERIVED` includes natural forks, ports, vendored copies, and constructed rewrites. `INDEPENDENT` is "clean-room implementations of the same specification", but for public OSS projects that is often an inference, not a known fact. `UNRELATED` is a null/chance class that can make classifier performance look better without answering the hard DERIVED-vs-INDEPENDENT question.

The ordinal claim `UNRELATED < INDEPENDENT < EVOLVED ≈ DERIVED-deep < DERIVED-moderate < DERIVED-paraphrase` is plausible only for retention, not for legal/causal derivation. Adjacent releases can retain more than paraphrase derivatives; ports can preserve behavior but not structure; independent implementations of a strict spec can have identical behavior. Unless the study chooses one target and makes all labels serve that target, AUC and calibration will be uninterpretable.

Required fix: define the estimand explicitly. If the target is causal lineage, EVOLVED belongs with positives. If the target is "copying-like derivation" distinct from ordinary evolution, EVOLVED is neither a simple positive nor a negative. If the target is retention, stop calling the output derivation likelihood and model an ordinal retention score.

**[blocker] The proposed sample size and statistical unit are not adequate for the planned claims.**  
Citation: `SPECIFICATION.md:§6.2`, `SPECIFICATION.md:§6.3`, `SPECIFICATION.md:§9.1`, `SPECIFICATION.md:§9.2`, `SPECIFICATION.md:§9.6`, `SPECIFICATION.md:§17.4`.

The spec states `≥40` pairs across `≥8` families, family-level train/test splits, LOFO-CV on train, held-out test AUC with BCa CI, ECE, Brier score, no family-held-out fold worse than chance, and dose-response tests. That is too much inference for the proposed floor.

The plan says to bootstrap AUC at the pair level within the test set (`SPECIFICATION.md:§9.1`). That contradicts the leakage logic that families are the independent unit (`SPECIFICATION.md:§6.3`). Pairs within one family share domain, APIs, dependencies, authorship conventions, and often source ancestry; bootstrapping them as independent will give overconfident CIs. The correct unit is family-level, or a hierarchical bootstrap that preserves family clustering.

Calibration is even more fragile. ECE and reliability diagrams are sample-hungry; with a held-out test set of perhaps a few families and a few dozen pairs, ECE can be dominated by arbitrary binning. "No family-held-out fold worse than chance" is undefined for families that lack both classes. Brier score is valid but will be noisy and class-prevalence-sensitive.

Required fix: run the power calculation now, before accepting the `≥40/≥8` floor. Specify expected test-family count, class balance per family, minimum positives/negatives per test fold, family-level resampling, calibration binning or binless calibration assessment, and what happens if a family lacks a class.

**[blocker] Constructed derivatives risk circular label-generation/measurement coupling.**  
Citation: `SPECIFICATION.md:§5.2`, `SPECIFICATION.md:§6.1`, `SPECIFICATION.md:§6.4`, `SPECIFICATION.md:§9.5`, `SPECIFICATION.md:§13`, `SPECIFICATION.md:§18.5`.

Constructed derivatives are useful positive controls, but the spec leans on them for class labels and dose-response. The transform pipeline produces the derivative depth labels, and the metrics are explicitly designed to measure structural, behavioral, and provenance retention. This can become circular: the study may prove that metrics detect artifacts created by the study's own transform pipeline.

The representativeness problem is not a minor threat. Real AI rewrites, human ports, mechanical transpiles, vendored copies, and clean-room implementations fail in different ways. A deterministic transform pipeline may leave exactly the invariants ST/PB metrics look for, or may erase them in a stylized way that no real rewrite does. If constructed derivatives dominate DERIVED positives, the classifier can learn transform signatures rather than derivation.

Required fix: predefine natural-vs-constructed counts and report them separately. Hold out transform families as well as library families. Use at least one constructed-derivative generator that is not designed by the metric authors, or have a data steward generate constructed fixtures before metric finalization. State that RQ4 applies to constructed depth only, not to all derivation.

**[blocker] The preregistration and single-unblinding story is not credible while core decisions remain open.**  
Citation: `SPECIFICATION.md:§4`, `SPECIFICATION.md:§6.2`, `SPECIFICATION.md:§11`, `SPECIFICATION.md:§16`, `SPECIFICATION.md:§18`.

The spec says hypotheses, metrics, scopes, thresholds, ablation grids, decision rules, comparison family, and power calculation are frozen before the test split is touched (`SPECIFICATION.md:§11`). But `SPECIFICATION.md:§18` still leaves final family list, seed libraries, confirmatory thresholds, ECE/Brier bounds, score model form, language coverage, and natural-vs-constructed ratio open. Those are not implementation details; they determine the study's estimand, power, and results.

The "single unblinding" protocol is also too neat. The same team will build the benchmark, choose candidate families, know chardet is a test instance, write family-specific BH adapters, and see enough source to make inclusion/exclusion decisions. That is not blind in the sense needed to prevent sequential overfitting. Sealing hashes after benchmark construction does not erase knowledge gained during construction.

Required fix: use a staged preregistration. Freeze the label protocol and candidate-family inclusion rules before collection; freeze metrics and modeling before split assignment; assign splits by a reproducible random seed or independent data steward; maintain an audit log of every excluded candidate and why. Treat chardet as a known, predeclared external case rather than pretending it can be sealed from design influence.

### Major Findings

**[major] R-SCOPE fixes the predecessor failure, but still leaves scope as a researcher degree of freedom.**  
Citation: `SPECIFICATION.md:§2 L1`, `SPECIFICATION.md:§5.3`, `SPECIFICATION.md:§8`, `SPECIFICATION.md:§17.3`.

Mandatory `package` and `repo` reporting would have caught the predecessor's repo-vs-package inversion. That is a meaningful fix. The remaining problem is interpretive: the spec declares package scope as the headline because "the shipped library is the object of a derivation dispute" (`SPECIFICATION.md:§5.3`). That will be true for some disputes and false for others. CLI tools, plugins, code generators, benchmark suites, training scripts, language models, data tables, and packaging metadata can all be part of the contested work.

The `custom` scope also needs stronger governance. A custom glob recorded verbatim is transparent, but transparency is not the same as preventing cherry-picking. A researcher can choose a custom scope after seeing where a signal fires.

Required fix: for each pair, predeclare the object of comparison and all admissible scopes before metric execution. Report package, repo, and dispute-object scopes separately. Do not use a universal package headline unless the benchmark family truly consists of importable libraries.

**[major] R-NODRIFT is a strong invariant, but "same-run artifacts" can become circular.**  
Citation: `SPECIFICATION.md:§2 L2`, `SPECIFICATION.md:§8`, `SPECIFICATION.md:§10.1`, `SPECIFICATION.md:§15`, `SPECIFICATION.md:§17.1`.

The predecessor failure was not that the harness could not produce numbers; it was that the advertised validator compared against stale constants and exited nonzero. CDA's macro registry and no-hardcoded-values rule are the right response. The weak point is "derives expected values from the artifacts of the same run" (`SPECIFICATION.md:§2 L2`).

If `results.json` is committed and both macros and figures read from it, then rendered numbers can always match stale `results.json`. That proves no transcription drift, but not that published numbers still regenerate from source inputs. The validator must have two layers: regenerate fresh results from raw pinned inputs, then compare committed/rendered artifacts to the fresh results.

Required fix: define `make validate` as raw inputs -> fresh results in a temp directory -> compare to committed `results.json` -> render paper -> scan manuscript/PDF for numeric literals -> compare all macros/tables/figures. Include mutation tests for both the manuscript and `results.json`.

**[major] Behavioral equivalence is under-operationalized and likely the largest build risk.**  
Citation: `SPECIFICATION.md:§5.2`, `SPECIFICATION.md:§6.2`, `SPECIFICATION.md:§8`, `SPECIFICATION.md:§10.2`, `SPECIFICATION.md:§18.4`.

BH is presented as a black-box input/output agreement family. That is easy for two versions of the same package with stable APIs, but hard for independent implementations of the same specification and for ports across languages. You need adapters, canonical output formats, input generators, oracle decisions, timeout policies, nondeterminism handling, and error normalization. These choices can dominate the BH score.

The spec says Python-only by default through P5 (`SPECIFICATION.md:§18.4`) while also proposing families such as wire-format parsers, hashing utilities, CLI argument parsers, and semver-style libraries (`SPECIFICATION.md:§6.2`). Restricting to Python may make the benchmark feasible, but it also narrows external validity and may bias the family list toward easy-to-adapt packages.

Required fix: add a BH adapter protocol with acceptance tests. For each family, predefine workloads, canonicalization rules, error handling, timeouts, dependency policy, and adapter authorship rules. Report adapter LOC/complexity as a possible confound.

**[major] "No SKIP" plus dropping unbuildable pairs creates selection bias.**  
Citation: `SPECIFICATION.md:§8`, `SPECIFICATION.md:§10.2`, `SPECIFICATION.md:§13`.

Failing CI on BH `SKIP` is a valid reproducibility standard. But `SPECIFICATION.md:§8` says natural pairs that cannot be built hermetically are dropped at benchmark-construction time and logged. That changes the population. Old, messy, legally interesting projects are exactly the ones likely to have obsolete build systems, missing wheels, networked tests, or system dependencies. Removing them may produce a benchmark of unusually clean, small, Python-only libraries.

Required fix: define candidate enumeration before buildability filtering, publish the excluded-candidate list, and quantify how exclusions change family/domain/license/age distributions. Consider a separate "static-only" track rather than dropping high-value natural pairs entirely.

**[major] Family-level split is necessary but not sufficient to prevent leakage.**  
Citation: `SPECIFICATION.md:§6.3`, `SPECIFICATION.md:§6.4`, `SPECIFICATION.md:§9`, `SPECIFICATION.md:§11`.

Family-level splits prevent the obvious pair-level leakage. They do not prevent leakage through constructed-derivative generators, shared adapters, common specs, common authors, common test fixtures, or repeated domains. For example, multiple parsers for related serialization formats can share grammar idioms; generated derivatives across families can share transform artifacts; Python packaging conventions can dominate PB/ST metrics.

Required fix: track leakage channels explicitly: seed library, transform generator, language, specification, adapter author, source organization, shared dependencies, and corpus source. Add split constraints or sensitivity analyses for these fields.

**[major] AUC target and calibration targets are arbitrary and partly inconsistent with the multi-class design.**  
Citation: `SPECIFICATION.md:§4`, `SPECIFICATION.md:§6.1`, `SPECIFICATION.md:§9.1`, `SPECIFICATION.md:§9.2`, `SPECIFICATION.md:§18.2`.

RQ1 asks whether CDA separates DERIVED from INDEPENDENT with AUC ≥ 0.85 and lower CI > 0.70. RQ3 asks for Brier/ECE below a predeclared bound. But `SPECIFICATION.md:§18.2` says the exact AUC/ECE/Brier bounds are still open. More importantly, if the classifier outputs "derivation likelihood", what are EVOLVED and UNRELATED during training and calibration? Are they ignored, auxiliary classes, positives/negatives, or ordinal anchors?

Required fix: define the training label vector and calibration target. If binary, specify which classes enter and why. If ordinal/multiclass, use ordinal/multiclass metrics and calibration methods. Justify thresholds using decision costs or benchmark utility, not round numbers.

**[major] RQ4's monotonicity test is too narrow and likely underpowered.**  
Citation: `SPECIFICATION.md:§4 RQ4`, `SPECIFICATION.md:§6.4`, `SPECIFICATION.md:§9.5`.

Spearman ρ between constructed depth and score is reasonable as a descriptive check, but p<0.05 with Holm correction is unlikely to be meaningful unless there are many independent constructed derivatives per depth across many seed families. The depth labels are produced by the transform pipeline itself, not by independently observed real-world derivation depth. Monotonicity on constructed depth should not be allowed to validate the entire derivation construct.

Required fix: make RQ4 explicitly about constructed fixtures only. Use family/seed as the independent unit, report depth curves per seed, and avoid a single p-value as the confirmatory result unless the power calculation supports it.

**[major] Ablation demotion rules can leak test information.**  
Citation: `SPECIFICATION.md:§4 RQ2`, `SPECIFICATION.md:§7.4`, `SPECIFICATION.md:§9.4`, `SPECIFICATION.md:§11`.

The spec says any metric whose DERIVED-vs-INDEPENDENT ordering flips inside the grid is reclassified as exploratory and removed from the confirmatory classifier. That rule is sensible if applied during metric development on train only. If applied after seeing test labels, it is feature selection on the test set. The spec does not say where instability is assessed.

Required fix: predefine train-only ablation screening, freeze included metrics before test unblinding, and report test ablation envelopes without changing the confirmatory classifier.

**[major] Label credibility is asserted rather than operationalized.**  
Citation: `SPECIFICATION.md:§6.1`, `SPECIFICATION.md:§6.2`, `SPECIFICATION.md:§10.4`, `SPECIFICATION.md:§14`.

"Known provenance", "documented forks", "ports with a recorded lineage edge", and "clean-room implementations" need evidence standards. A README saying "inspired by X", a fork graph, a vendored directory, a package rename, or a port can imply different levels of derivation. Conversely, independent implementations of a public spec may copy examples, tables, tests, or generated code.

Required fix: add a label evidence rubric with minimum documentation, independent adjudicators, conflicts-of-interest policy, and uncertainty labels. Some pairs should be labeled "ambiguous" and excluded from confirmatory training/testing.

**[major] The spec lacks a clear baseline model plan.**  
Citation: `SPECIFICATION.md:§5.2`, `SPECIFICATION.md:§5.3`, `SPECIFICATION.md:§9`, `SPECIFICATION.md:§13`.

A classifier AUC has little meaning without simple baselines: file/token overlap, size/domain features, dependency overlap only, behavior only, structure only, family/domain heuristics, and maybe existing clone detectors where feasible. Otherwise CDA may beat chance but not beat trivial confounds.

Required fix: pre-register baseline models and ablations: ST-only, BH-only, PB-only, size/domain-only, lexical baseline, and simple rule baseline. Report whether the combined CDA score adds value beyond them.

**[major] Acceptance criteria do not fully enforce the body.**  
Citation: `SPECIFICATION.md:§16`, `SPECIFICATION.md:§17`.

The definition of done checks CI, macro binding, scopes, benchmark size, controls, BH measured, prereg tag, and reproductions. It does not explicitly require label adjudication quality, power calculation adequacy, family-level resampling, train-only ablation screening, baseline comparison, or exclusion-bias reporting. Several of the study's riskiest claims could pass §17 while remaining invalid.

Required fix: add acceptance criteria for label adjudication, statistical unit, power, calibration sample size, train/test leakage audit, excluded-candidate manifest, and baseline comparisons.

### Minor Findings

**[minor] The spec contradicts itself on whether every metric or only ST/PB metrics are multi-scope.**  
Citation: `SPECIFICATION.md:§2 L1`, `SPECIFICATION.md:§5.3`, `SPECIFICATION.md:§8`, `SPECIFICATION.md:§17.3`.

L1 says every metric must be reported at ≥2 scopes. §5.3 and §17.3 narrow this to PB and ST metrics. BH may not naturally have a source-file scope, so the narrower rule is defensible, but the normative language must be consistent.

**[minor] "Ground truth" is too strong for many labels.**  
Citation: `SPECIFICATION.md:§0`, `SPECIFICATION.md:§6.1`, `SPECIFICATION.md:§6.2`.

Natural lineage labels are often evidence-backed judgments, not ground truth. The spec should reserve "ground truth" for constructed fixtures and directly documented vendoring/forks, and call other labels "adjudicated labels" with evidence tiers.

**[minor] Logistic regression may not respect the ordinal structure or family heterogeneity.**  
Citation: `SPECIFICATION.md:§5.2`, `SPECIFICATION.md:§18.3`.

The default regularized logistic model is interpretable, but the construct is ordinal and family-clustered. A hierarchical model, ordinal model, or monotone constrained model may be more consistent. If logistic remains the default, specify regularization, feature scaling, class weights, and coefficient uncertainty.

**[minor] Confidence intervals for per-pair "derivation likelihood" are not defined.**  
Citation: `SPECIFICATION.md:§0`, `SPECIFICATION.md:§5.2`, `SPECIFICATION.md:§9`.

The thesis promises a likelihood with CI. The statistical plan describes AUC CIs and effect-size CIs, not per-pair prediction intervals or uncertainty decomposition. A per-pair CI should distinguish metric sampling uncertainty, model-parameter uncertainty, family transfer uncertainty, and calibration uncertainty.

**[minor] Figure validation should be semantic, not only non-empty.**  
Citation: `SPECIFICATION.md:§10.3`, `SPECIFICATION.md:§17.1`.

Blank-panel detection is necessary but weak. Require tests that each planned panel has the expected series, labels, axis ranges, nonzero data rows, and source keys. Ideally compare figure metadata or generated data tables rather than pixels alone.

**[minor] Reproduction depth requirement is better than before but still gameable.**  
Citation: `SPECIFICATION.md:§12`, `SPECIFICATION.md:§17.8`.

Each reviewer reproducing one confirmatory number and one control does not ensure the deeper defects will be found. The predecessor showed that spot-checks can miss the important failure. Require assigned coverage: one reproducer validates label/split manifests, one validates scope calculations, one validates no-drift/macro scanning, one validates statistics/calibration, and one validates BH hermeticity.

**[minor] Security and safety of running arbitrary historical code are missing.**  
Citation: `SPECIFICATION.md:§10.2`, `SPECIFICATION.md:§14`, `SPECIFICATION.md:§15`.

Hermetic containers reduce network drift but not all risk. The benchmark will run old third-party code. Add sandbox restrictions, no-network enforcement tests, CPU/memory/time limits, filesystem isolation, artifact retention policy, and dependency vulnerability handling.

**[minor] Licensing constraints may bias the benchmark.**  
Citation: `SPECIFICATION.md:§6.2`, `SPECIFICATION.md:§10.4`, `SPECIFICATION.md:§14`.

Permissive/public-domain-only inputs simplify redistribution but may exclude many natural derivative cases involving copyleft, dual licensing, or unclear provenance. Since relicensing disputes often involve copyleft, this creates an external-validity bound. State it explicitly and consider metadata-only references for non-redistributed inputs if legally acceptable.

### Nits

**[nit] `custom-glob` and `custom` are named inconsistently.**  
Citation: `SPECIFICATION.md:§2 L1`, `SPECIFICATION.md:§5.3`.

The table uses `custom-glob`; §5.3 uses `custom`. Pick one schema value.

**[nit] "No expected value is ever hardcoded" is too absolute.**  
Citation: `SPECIFICATION.md:§2 L2`, `SPECIFICATION.md:§10.1`.

Schema expectations, thresholds, and test fixtures will contain constants. The intended rule is "no published numeric result is hardcoded as an expected value." State that precisely.

**[nit] `CI/` as a repository directory is unusual.**  
Citation: `SPECIFICATION.md:§15`.

Prefer `.github/workflows/`, `.gitlab-ci.yml`, or a generic `ci/` unless there is a specific reason.

**[nit] The phrase "no family-held-out fold worse than chance" needs a formal definition.**  
Citation: `SPECIFICATION.md:§4 RQ3`.

Define the metric, class set, chance level, and what happens for single-class folds.

## Benchmark Design Assessment

Citation: `SPECIFICATION.md:§6`.

The benchmark is the proposed study's decisive contribution, and it is currently the most underdesigned part.

The four classes are directionally useful but not well-posed enough:

- `DERIVED` mixes vendored copies, forks, ports, and constructed rewrites. These are different mechanisms with different expected ST/BH/PB signatures.
- `EVOLVED` is true derivation but is separated from DERIVED. That can be justified if the study targets "copying/rewriting outside ordinary project evolution", but the spec does not say that clearly.
- `INDEPENDENT` controls for same-spec convergence, but "clean-room" is rarely verifiable for OSS. It needs evidence tiers and ambiguous-label handling.
- `UNRELATED` is a null class. It is useful for sanity checks but can inflate overall discrimination if folded into classifier training or performance summaries.

Family-level splitting is necessary and better than pair-level splitting. It is not sufficient by itself. Leakage can happen through generated derivatives, common specs, shared adapters, shared corpora, language ecosystems, package templates, and benchmark construction choices. The split manifest should include these fields and audit them.

The proposed family count and pair count are floors without justification. With 8 families and 40 pairs, a family-level test split can easily have too few independent units for a stable AUC CI. The relevant n is not just pair count; it is families per split, positives/negatives per family, natural positives per class, constructed positives per generator, and same-spec independent pairs per domain.

Selection/confound/availability risks are high. Public + permissive + hermetically buildable + behaviorally comparable + known provenance is a narrow slice of OSS. It will likely select for small, clean, modern, Python packages. That may be acceptable, but it must be stated as the population.

## Construct Validity Assessment

Citation: `SPECIFICATION.md:§5`, `SPECIFICATION.md:§13`.

The construct is better than the predecessor's signal-first framing because it starts with "retention of structure/behavior" and explicitly rejects legal verdicts. But it still slides between three concepts:

1. causal derivation or lineage,
2. legal derivative-work relevance,
3. measurable structural/behavioral/provenance retention.

Only the third is directly measured. The first is inferred through labels. The second is explicitly out of scope. The final paper must keep the output named accordingly. "Derivation likelihood" is too strong unless calibrated to actual lineage labels with credible error rates and no circularity.

ST, BH, and PB are sensible signal families, but they are not orthogonal. Generated code, vendored tables, API compatibility, common dependencies, and shared specs can move all three together without copying. Conversely, a genuine deep rewrite can erase ST/PB and preserve only BH. The design should expect correlated, family-dependent failures rather than treating the families as independent evidence streams.

The biggest construct-validity risk is circularity between benchmark construction and measurement. If labels are created using known structural/provenance cues, and the classifier uses structural/provenance metrics, performance can reflect label-evidence recovery rather than derivation detection. Label adjudicators should not use the exact metric outputs, and label evidence should be recorded separately from measured features.

## Statistical Plan Assessment

Citation: `SPECIFICATION.md:§4`, `SPECIFICATION.md:§9`.

The statistical plan has good instincts: AUC, calibration, Brier score, effect sizes, BCa intervals, multiplicity control, and power planning are all appropriate ingredients. The current version is not yet statistically valid.

Primary errors:

- Resampling at pair level conflicts with family-level split logic. Use family-level or hierarchical resampling.
- AUC target is defined only for DERIVED vs INDEPENDENT while the dataset has four classes and an ordinal construct.
- ECE is unstable at the likely test-set size and needs binning rules or an alternative.
- Power calculation is deferred even though it should determine the benchmark floor.
- RQ4's Spearman p-value over constructed depths is likely underpowered and construct-limited.
- Multiplicity correction is named but the comparison family is not enumerated.
- "No family-held-out fold worse than chance" is undefined for small or class-imbalanced folds.

The plan should move from "statistical ingredients list" to an analysis protocol: exact outcome variable, class inclusion, model form, feature preprocessing, regularization, split assignment, resampling unit, CI method for clustered data, calibration assessment, multiplicity family, missing-data handling, and failure rules.

## Reproducibility Engineering Assessment

Citation: `SPECIFICATION.md:§10`, `SPECIFICATION.md:§15`, `SPECIFICATION.md:§17`.

R-NODRIFT is one of the strongest parts of the spec. If implemented as a fresh end-to-end regeneration plus macro scan, it would close the predecessor's stale-validator hole. The acceptance criterion that mutating a published number must make validation fail is especially good.

The remaining failure modes are:

- stale `results.json` can become the shared source for both paper and validation unless regenerated from raw inputs;
- macro registries often miss prose numbers, axis labels, captions, percentages, rounded values, and counts embedded in text;
- generated figures can be non-empty but semantically wrong;
- CI triggers "on commits touching harness, data, or manuscript" can miss container, lockfile, dependency, or workflow changes unless broad enough;
- byte-for-byte numeric equality can cause false failures if formatting rules are not centralized.

Hermetic BH is desirable but costly. It should be prototyped before preregistration because it determines which families are feasible and how biased the benchmark will be.

## Pre-Registration And Adversarial Validation Assessment

Citation: `SPECIFICATION.md:§11`, `SPECIFICATION.md:§12`, `SPECIFICATION.md:§16`, `SPECIFICATION.md:§17`.

The design correctly recognizes that review depth matters and that reproductions must run the harness. That is a real lesson from the predecessor synthesis (`SYNTHESIS.md:§2`, `SYNTHESIS.md:§4`, `SYNTHESIS.md:§5`).

But harness-running reproduction fixes only one class of problem. It does not validate whether labels are correct, whether pairs are representative, whether the split leaked information, whether the statistical unit is right, or whether constructed derivatives are realistic. The red-team charter includes some of these concerns, but the acceptance checklist does not make them all enforceable.

"Single unblinding" is especially weak. The benchmark builders will necessarily inspect sources, build adapters, and know labels for many pairs. A better design is not perfect blindness, but auditable staged decision-making and split assignment by a precommitted procedure.

## Scope Contract Assessment

Citation: `SPECIFICATION.md:§5.3`, `SPECIFICATION.md:§8`, `SPECIFICATION.md:§17.3`.

The scope contract is a genuine improvement and would have exposed the predecessor's central scope defect. Mandatory scope-deltas are exactly the right diagnostic.

The edge cases need more work:

- monorepos with multiple packages;
- packages where CLI scripts or generated data are shipped but not importable modules;
- libraries whose behavior depends on bundled models/tables;
- disputes over build scripts, benchmarks, or training tools;
- ports where "package" scope differs by language ecosystem;
- generated code checked into repo but not handwritten;
- custom globs chosen after exploratory inspection.

Predeclare the "claim object" per pair, then report all standard scopes as sensitivity. Do not let package scope silently become the new unexamined default.

## Feasibility And Cost

Citation: `SPECIFICATION.md:§6`, `SPECIFICATION.md:§10`, `SPECIFICATION.md:§16`, `SPECIFICATION.md:§18`.

This is buildable only as a substantial benchmark-engineering project, not as a small follow-on study. The largest execution risks are:

- finding enough permissively licensed, well-documented natural DERIVED edges;
- verifying truly independent same-spec implementations;
- writing and validating BH adapters and workloads per family;
- making old projects build hermetically offline;
- avoiding selection bias from buildability and adapter feasibility;
- keeping family-level test sets large enough for calibration and AUC CIs;
- preventing constructed derivatives from dominating the positive class;
- maintaining macro/no-drift infrastructure across manuscript revisions.

What's underspecified or missing entirely:

- label adjudication protocol;
- candidate enumeration and exclusion log;
- family-specific BH adapter protocol;
- baseline models;
- family-level/hierarchical statistical analysis;
- governance for custom scopes;
- security model for executing third-party code;
- data/version archival plan for source snapshots;
- model-card/datasheet-style benchmark documentation;
- error budget for labels and measurement failures.

## Internal Consistency Check

Citation: `SPECIFICATION.md:§2`, `SPECIFICATION.md:§4`, `SPECIFICATION.md:§5`, `SPECIFICATION.md:§6`, `SPECIFICATION.md:§9`, `SPECIFICATION.md:§11`, `SPECIFICATION.md:§16`, `SPECIFICATION.md:§17`, `SPECIFICATION.md:§18`.

Notable contradictions or tensions:

- §2 L1 says every metric must be reported at ≥2 scopes; §5.3 and §17.3 say only ST/PB metrics.
- §4 contains confirmatory thresholds, but §18 says exact thresholds and ECE/Brier bounds remain open.
- §11 says metrics/scopes/thresholds/power are frozen before benchmark construction; §18 leaves final families and seed libraries open.
- §9 says pair-level bootstrap; §6 says family is the leakage unit.
- §6 calls chardet a sealed TEST instance; §4 calls chardet exploratory. That can be reconciled, but the spec should state whether chardet contributes to confirmatory test metrics or is only an external placement after calibration.
- §16 P3 gates on train calibration metrics being within bounds. If the gate fails, redesigning the model risks sequential overfitting unless a redesign protocol is specified.
- §10.2 says every benchmark pair must have BH measured; §8 allows unbuildable natural pairs to be dropped at construction time.
- §17 requires headline performance across ≥8 families, but §6 defines ≥8 families for the whole benchmark, not necessarily the held-out test set.

## Bottom Line

CDA is pointed in the right direction and correctly internalizes the predecessor's most concrete failures. The scope contract, controls-in-paper rule, hermetic/no-skip ambition, macro-bound paper, and adversarial reproduction requirement are all worthwhile.

But as a design for a not-yet-built study, it is not ready for preregistration. The benchmark and statistics are the study, and they are not yet specified tightly enough to make the eventual classifier credible. Fix the label ontology, sampling/power, family-level inference, constructed-derivative circularity, BH adapter protocol, and staged preregistration before proceeding.
