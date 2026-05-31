# Research Quality Guide & Scoring Rubric

A reusable, evidence-grounded checklist for measuring the quality of the research artifacts in
this repository (chardet-relicensing, the CDA, hello-world, non-trivial-proof, and future cs.SE
work). It was first written for one genre — **falsifiable measurement/detection harnesses** that
emit deterministic numbers from source and back claims with calibration controls — but the
repo holds a second genre too (**executable assurance proofs / engineering artifacts**), so
**§0.1 below tells you which items apply to which genre.** The §1 first principles are
genre-invariant; only the applicability of individual §2 items shifts.

It distills the consensus from the cs.SE / empirical-software-engineering and ML-evaluation
methodology literature (see **References**) into a rubric you can *apply* in another session:
load this file, score the artifact against §2's dimensions using §4's procedure, and report the
scorecard. It is descriptive of good practice, not a substitute for thinking — the threats-to-validity
literature is explicit that checklists applied "blindly in a check-list fashion" are an anti-pattern
(Verdecchia et al.). Use the items to *prompt* contextual judgment, not to replace it.

---

## 0. How to use this in another session

> **Prompt to paste:** "Read `RESEARCH-QUALITY-GUIDE.md`. Score `<artifact / manuscript / harness>`
> against every dimension in §2. For each item give a verdict (✅ pass / ⚠️ partial / ❌ fail / N/A),
> one sentence of evidence citing a file:line or a measured number, and a fix if not passing. Then
> fill the §4 scorecard, list every §3 red-flag that fires, and give an overall grade. Do not
> rubber-stamp — actively try to falsify each claim."

Score **the artifact as it is**, against **what it claims**. A modest, correctly-scoped claim with
clean evidence beats an ambitious claim with hand-waving. The grader's job is adversarial: assume
each headline number is wrong until the harness, the controls, and the trace say otherwise.

---

## 0.1 Two genres in this repo — adapt the rubric, do not force it

This repo holds two genres of artifact. **State which genre you are grading, then apply the §2
items accordingly.** The mistake to avoid in both directions: forcing a statistical item onto a
categorical proof (inventing a "null distribution" where there is none), or waving through an
engineering item because "it's just a demo." When an item does not apply, mark it **N/A with a
one-line reason** — never silently skip it (silent skipping reads as a pass it did not earn).

**Genre A — falsifiable measurement / detection harness** *(chardet-relicensing, the CDA)*: emits
deterministic numbers and backs claims with calibration controls. **Every dimension applies at full
weight.** D (baselines/controls/calibration) and E (statistics) are the core — a positive number is
meaningless without a null/negative/positive-control panel (D1–D3) and an effect size with
uncertainty (E1–E3). The §6.3 Benchmarking standard applies to any corpus/behavioural arm.

**Genre B — executable assurance proof / engineering artifact** *(hello-world, non-trivial-proof)*:
emits **categorical** witness outcomes (PASS / SKIP / FAIL) plus descriptive MEASURED engineering
numbers, governed by contracts + executable witnesses. Adapt as follows:

- **E1–E6 (statistics): N/A.** There are no hypothesis tests, p-values, effect sizes, or
  distributions — the "measurements" are engineering observations (e.g. time-to-ready) checked
  against declared deadlines, not statistical estimates. Say so explicitly per item.
- **D3 (null/chance baseline), D4 (fair baselines), D5 (dose-response): usually N/A.** There is no
  random-input null distribution or continuous dose variable. Do **not** manufacture one by
  relabelling a single design fact as a "null" — that is a worse error than marking N/A. (A reviewer
  who scores D3–D5 "pass" for a categorical proof is over-fitting the rubric; prefer N/A-with-reason.)
- **D1/D2 (negative + positive control) STILL APPLY, and are the heart of this genre.** The analogue
  of a null is a **deliberately-broken control the gate MUST catch** (e.g. a server that ignores
  SIGTERM, or exits 0 while dropping an in-flight request). Score D1/D2 on: does the control actually
  *fire* (the gate FAILs it), and does the positive case still PASS? A gate that cannot fail is
  vacuous — the §3 red flags about missing controls apply unchanged.
- **B4 (invariances): often N/A** unless the artifact claims an invariance (renaming, load, ordering).
- **A, B1–B3, C2/C4/C5, F, G, H, and the §6.2 Engineering Research standard apply at full weight.**
  Hold reproducibility (F) hard: the witnesses/validators must re-run from a clean checkout, the
  prose numbers must be the artifact's actual output (categorical verdicts and validator aggregates,
  not hand-transcribed), and a second execution path (e.g. a container) strengthens F5. Hold claims
  ≤ evidence (A2) on the explicit non-claims list, and threats (G) on the static-vs-runtime gap.

If an artifact spans both genres (a proof with a measured detection arm), grade each arm in its own
genre. When in doubt about an item, the §1 first principles are the tie-breaker — they hold for both.

---

## 1. First principles (the spirit behind every item)

1. **Falsifiability.** Every headline claim must have a stated condition under which it would be
   *false*, and that condition must have been tested. A result that cannot fail is not evidence.
2. **Claims ≤ evidence.** The scope of every sentence in the abstract/conclusion must be covered by
   what was actually measured. "Don't generalise beyond the data" (Lones 6.3).
3. **Reproducibility is the unit of trust.** A number nobody else can regenerate is an anecdote. In a
   study of 100 ICSE artifacts only **40 were executable and 14 reproduced** the original results
   (Siddiq et al.) — availability ≠ executability ≠ reproducibility.
4. **A signal needs a null.** "High" means nothing without "high compared to what." Every positive
   result needs a baseline / negative control / null distribution it is shown to beat.
5. **Practical significance over statistical significance.** Report effect sizes and what the number
   *means in context*, not just whether p < 0.05 (Kitchenham, Madeyski; SE effect-size review).
6. **Adversarial self-review.** The most valuable section is the one that argues against the paper.
   Threats-to-validity must be a design concern, not an "enforced afterthought / laundry list"
   (Verdecchia et al.; SIGSOFT distinguished-paper review).

---

## 2. The dimensions (score each item)

### A. Claims & framing
- [ ] **A1. Each claim is falsifiable** with a pre-stated failure condition that was tested.
      *(Our genre: e.g. "if the paraphrase control did not light up the structural metric, the v6/v7 0% would be uninformative" — and that control was run.)*
- [ ] **A2. Claims are scoped to the evidence** — no silent generalisation to other languages,
      projects, model families, or to a legal/normative verdict the method does not support.
- [ ] **A3. The research questions / hypotheses are stated before the results**, not reverse-engineered
      from whatever came out (HARKing). Distinguish confirmatory from exploratory findings.
- [ ] **A4. Necessary-vs-sufficient is explicit** for every signal: what a positive proves, and —
      crucially — what it does *not* prove (false-positive and false-negative modes named).

### B. Construct validity (are we measuring what we claim?)
- [ ] **B1. Each metric is defined operationally and deterministically** (exact formula / code path),
      not by an intuitive label. The "macro-F1 without saying what you expect from it" anti-pattern
      (Opitz & Burst) generalises: name the property the metric is supposed to have.
- [ ] **B2. The metric actually captures the construct** — a mismatch between metric and the question
      of interest is a top cause of wrong conclusions (Kapoor & Narayanan; Opitz & Burst).
- [ ] **B3. Metric choice is justified, not convenient.** Metric selection alone flips which method
      "wins" on ~31% of datasets (Larsen et al.) — report the metrics that could change the verdict,
      not just the flattering one.
- [ ] **B4. Invariances are stated and tested.** If the method claims to be invariant to something
      (renaming, formatting, reordering), there is a control proving the invariance and a control
      proving it still *fires* on a real positive (so the invariance isn't just numbness).

### C. Internal validity / leakage (is the result an artifact of the setup?)
- [ ] **C1. No data/estimation/selection leakage.** Nothing from the test/holdout informs training,
      feature selection, scaling, calibration, or thresholds. Selection/"peeking" leakage is the most
      common and most inflating type (Larsen et al.; Kapoor & Narayanan taxonomy).
- [ ] **C2. No threshold / hyperparameter cherry-picking.** Decision thresholds (gates, cutoffs) were
      not tuned on the same data that reports the headline. *(Our genre: show the gate-sweep — the
      verdict must be robust across a neighbourhood of thresholds, not balanced on one.)*
- [ ] **C3. No sequential overfitting** to the evaluation set across many iterations of the method
      (Lones 4.3); if the eval set was reused, say so and discount accordingly.
- [ ] **C4. Determinism / seed control.** Stochastic steps are seeded and the seed is recorded; a
      re-run reproduces the numbers bit-for-bit (or within a stated tolerance). *(Our invariant:
      numbers are deterministic functions of source bytes / a fixed seed.)*
- [ ] **C5. Confounds controlled.** Differences attributed to the treatment aren't explained by
      package size, corpus composition, tooling versions, or measurement root choice (e.g. comparing
      package-to-package, not package-to-full-repo).

### D. Baselines, controls & calibration (the heart of our genre)
- [ ] **D1. A true negative control** (independent / unrelated input the method should *not* fire on)
      and its rate is reported. *(chardet: v6→csn independent reimplementation; an unrelated-package null panel.)*
- [ ] **D2. A true positive control** (a known-positive the method *must* catch) and its rate is
      reported. *(chardet: the synthetic known-derivative fixtures.)* Without this you cannot tell
      "0% = clean" from "0% = blind metric."
- [ ] **D3. A null / chance baseline** is quantified, and positives are shown to clear it; chance-corrected
      where possible (Opitz & Burst, Property V). *(chardet: the stdlib null-panel floor.)*
- [ ] **D4. Baselines are meaningful and fair** — strong, well-tuned, and the obvious simple baseline is
      included (Lones 5.2). A win over a strawman is not a win.
- [ ] **D5. A graceful-degradation / dose-response curve** exists where applicable (monotone behaviour
      between the positive and null extremes is evidence the metric tracks the construct, not noise).

### E. Statistical analysis
- [ ] **E1. Effect sizes are always reported**, not just significance (SE effect-size review; Lones 6.4).
      Prefer robust / non-parametric measures for small or non-normal SE data: **Cliff's δ**, **Vargha-Delaney Â₁₂**,
      or the probability-of-superiority **p̂** (Kitchenham et al. small-sample recommendations).
- [ ] **E2. Distributional assumptions are checked**, not assumed. Use robust/non-parametric methods
      (trimmed means, Cliff's δ, rank-based ANOVA-like) when normality is doubtful; visualise with
      kernel-density plots, not just box plots (Kitchenham & Madeyski, *Robust Statistical Methods*).
- [ ] **E3. Uncertainty is quantified** — confidence intervals or, where useful, full posterior
      distributions (Bayesian estimation) rather than a lone p-value (Furia, Feldt, Torkar).
- [ ] **E4. Multiple comparisons are corrected** (Bonferroni/Holm/etc.) when many tests/configs are run
      (Lones 5.4) — otherwise some "significant" result is expected by chance.
- [ ] **E5. p-values are not over-read.** No "p < 0.05 ⇒ important"; no treating non-significance as
      proof of no effect; report practical significance in the practitioner's context.
- [ ] **E6. Sample size / power is adequate** and stated; for tiny n, prefer estimation over testing and
      say the analysis is exploratory.

### F. Reproducibility & artifact quality
- [ ] **F1. Code + data + exact environment are available** (versions pinned: language, libs, OS,
      seeds). The dominant reproduction failures are environment/dependency/versioning, not logic
      (Siddiq et al.; LLM-SE reproducibility study).
- [ ] **F2. The artifact executes from clean checkout** with documented commands and exits with a clear
      status; the path from "run this" to "the paper's numbers" is explicit. An ACM "Available" badge
      signals presence, **not** execution fidelity (LLM-SE reproducibility study) — hold to the higher bar.
- [ ] **F3. Numbers in the prose are mechanically derived from the artifact**, never hand-transcribed;
      a regeneration/validation path exists. *(Our CLAUDE.md invariant: every number is taken verbatim
      from one harness run; `make validate` re-derives the headlines independently.)*
- [ ] **F4. Provenance & licensing are clean** — inputs' sources/licenses recorded; derived test fixtures
      labelled as such; no leakage of disallowed data.
- [ ] **F5. Independent re-derivation** of at least the headline numbers by a second tool/path/person
      (the "Results Validated/Reproduced" bar, not just "Available").

### G. Threats to validity (the adversarial section)
- [ ] **G1. Threats are contextual, not a laundry list** — each is tied to a specific design decision in
      *this* study, with its plausible direction and magnitude, and a mitigation or an honest "couldn't"
      (Verdecchia et al.; SIGSOFT distinguished-paper review).
- [ ] **G2. Threats are prioritised by evidence**, not intuition — lean on known evidence about which
      threats actually bite in this subfield ("Evidence Tetris", Baltes et al.).
- [ ] **G3. Construct, internal, external, and conclusion validity are each addressed** (or explicitly
      argued irrelevant), and the headline's single biggest weakness is named, not buried.
- [ ] **G4. Known blind spots are stated as bounds**, with what would be needed to defeat the method
      (e.g. "re-architecture + retrained tables would slip every signal").

### H. Reporting & transparency
- [ ] **H1. Performance reported multiple ways** (per-bucket and aggregate; multiple metrics; the
      distribution, not just the mean) (Lones 6.2).
- [ ] **H2. Negative / null / failed results are reported**, not buried; SKIPs and dropped cases are
      logged with reasons (no silent truncation / silent caps).
- [ ] **H3. Full transparency of method** — enough detail (or code) to reproduce; deviations from
      pre-registration/plan disclosed; LLM/tool assistance disclosed where relevant.
- [ ] **H4. Figures/tables are honest** — axes, n, error bars, and the exact gate/threshold shown; no
      truncated axes or cherry-picked slices.

---

## 3. Red flags (each firing one is a serious mark-down; some are auto-fail)

- 🚩 **A headline with no failure condition** ever tested → not falsifiable (auto-fail A1).
- 🚩 **A positive result with no baseline/null/negative control** → "high vs nothing" (auto-fail D1/D3).
- 🚩 **A "0%" / "no match" reported without a positive control** proving the metric *can* fire (auto-fail D2).
- 🚩 **Threshold/metric chosen post-hoc to make the result look best**; no robustness sweep (C2/B3).
- 🚩 **Numbers in prose ≠ numbers the artifact produces** (or can't be regenerated) (F3) → auto-fail.
- 🚩 **Significance claimed with no effect size**, or non-significance read as "no effect" (E1/E5).
- 🚩 **Laundry-list threats section** disconnected from the study's actual decisions (G1).
- 🚩 **Claim generalised beyond the tested inputs** (one project → "in general") (A2).
- 🚩 **Leakage**: test data touched training/feature-selection/threshold-tuning (C1) → auto-fail.
- 🚩 **Comparison root/scope mismatch** inflating a difference (e.g. full-repo vs package) (C5).
- 🚩 **Benchmark taken at face value** without checking its construct/leakage (Lones 5.5; "don't always
   believe community benchmarks").

---

## 4. Scorecard template (fill this in when grading)

```
Artifact: <name / commit / file>
Claim under test: <the headline sentence>

Dimension                         Items pass/partial/fail   Weight   Notes
A Claims & framing                 _/_/_                     15%
B Construct validity               _/_/_                     15%
C Internal validity / leakage      _/_/_                     20%   ← leakage items can auto-fail
D Baselines, controls, calibration _/_/_                     20%   ← our genre's core
E Statistical analysis             _/_/_                     10%
F Reproducibility / artifact       _/_/_                     10%
G Threats to validity              _/_/_                      5%
H Reporting & transparency         _/_/_                      5%

Red flags fired: <list>
Auto-fail triggered? <yes/no — which>
Single biggest weakness: <one sentence>
Overall grade: <A–F>  Verdict: <publishable as-is / minor revision / major revision / not credible>
```

Grading guidance: any **auto-fail** red flag caps the grade at "major revision" regardless of the
weighted score. A strong artifact in our genre typically shows: a falsifiable headline (A1), matched
positive+negative+null controls with a monotone curve between them (D1–D5), a threshold-robustness
sweep (C2), deterministic regeneration (C4/F3), and a contextual threats section that names its own
blind spot as a bound (G1/G4).

---

## 5. Worked mapping to *this* repo (chardet-relicensing)

How the rubric lands on our own harness — use these as exemplars of "✅ looks like":

- **D1/D2/D3 (controls & null):** v5→v6 (evolution), v6→v7 (disputed), v6→csn (independent negative),
  the synthetic known-derivative fixtures (positive), and the unrelated-stdlib null panel — the
  positive controls (100%/79%) clear the ~11% null floor; the disputed and independent pairs sit at it.
- **D5 (dose-response):** paraphrase 100% → moderate 79% → deep ~0% is a monotone detection curve.
- **C2 (threshold robustness):** the gate-sweep over cyc∈{6..10} × cos∈{0.90..0.97} shows the verdict
  isn't balanced on the canonical (cyc≥8, cos≥0.95) cell.
- **C4/F3 (determinism & mechanical numbers):** static signals are deterministic functions of source
  bytes; C06e is seeded; `make validate` re-derives the headlines — "do not edit a number in main.tex."
- **B4 (invariance both ways):** the renaming-invariant structural metric is shown to *fire* on a real
  paraphrase (not numb) **and** to stay quiet on independent code.
- **A4/G4 (necessary-not-sufficient + blind-spot bound):** the structural signal is explicitly
  necessary-but-not-sufficient; the "deep + retrained tables defeats everything" boundary is stated.
- **A2 (scope):** the paper renders structural numbers and deliberately **no legal verdict**.

When a future change moves a canonical number, re-derive every dependent table/figure/abstract
sentence from the *same* harness run (don't hand-patch) — that discipline is itself item F3.

---

## 6. ACM SIGSOFT Empirical Standards — verbatim attribute lists (authoritative anchor)

These are the SE community's official, method-specific expectations (Ralph et al.,
arXiv:2010.03525; site: www2.sigsoft.org/EmpiricalStandards). Our genre is primarily
**Engineering Research** (we propose & evaluate a technological artifact — a detection
harness), with **Benchmarking** applying to the corpus/behavioural arm (C06e), both sitting
on top of the **General** standard. Score against these as hard requirements; **Essential**
attributes are necessary conditions for publication. The *Invalid Criticisms* lists are as
important as the attributes — they tell the grader what **not** to penalise (avoids bogus
rejections, the failure mode the standards were built to stop).

### 6.1 General Standard — Essential (applies to all empirical work)
- [ ] states a purpose / problem / objective / research question, and **why it matters** (motivation)
- [ ] names the methodology, and it is **appropriate** (not necessarily optimal) for that purpose
- [ ] defines jargon, acronyms, key concepts
- [ ] describes **in detail** what/where/when/how data were collected, and **how they were analysed**
- [ ] **enumerates and validates the assumptions of any statistical tests used**
- [ ] presents results that **directly address** the research questions; discusses implications
- [ ] states clear conclusions **linked to the RQ and supported by explicit evidence/arguments**
- [ ] **discloses all major limitations**
- [ ] visualizations/graphs are **not misleading**; language is not misleading
- [ ] acknowledges/mitigates risks, harms, or unintended consequences; complies with applicable standards
- *Desirable:* statistical power/saturation demonstrated; realism/assumptions & sensitivity discussed;
  registered-report (plan-then-results) split; multiple raters for subjective judgments.

### 6.2 Engineering Research Standard (our primary) — Essential
- [ ] describes the proposed artifact in **adequate detail** (workflow, how components fit, novel parts singled out)
- [ ] **justifies the need / usefulness / relevance** of the artifact (why state-of-the-art isn't enough)
- [ ] **conceptually evaluates** the artifact — discusses its **strengths, weaknesses, and limitations**
- [ ] **empirically evaluates** it via a named method (action research / case study / controlled experiment /
      quantitative simulation / **benchmarking** / other with rationale), and **says which**
- [ ] EITHER discusses state-of-the-art alternatives (with their strengths/weaknesses) OR explains none exist
      OR argues direct comparison is impractical
- [ ] EITHER empirically compares to ≥1 state-of-the-art alternative/benchmark OR gives a convincing rationale
      why comparative evaluation is impractical
- [ ] assumptions are explicit, plausible, mutually consistent, and don't contradict the contribution's goals
- *Desirable:* supplementary source/artifact + input datasets; correctness arguments (complexity/proofs);
  running example(s); evaluation in an **industry-relevant context**.
- *General quality:* **less innovative artifacts require more rigorous evaluation** (innovativeness ↔ rigor trade-off).
- **Antipatterns (mark down if present):** overstates novelty; focuses on incidental implementation while
  omitting key conceptual aspects; evaluation is *only* user opinions; evaluation is *only* performance data
  **not compared** to baselines/alternatives; **non-experimental single-group / non-repeated design**;
  **toy examples misrepresented as "case studies."**
- **Invalid criticisms (do NOT penalise for):** a less-ambitious empirical study when the artifact is highly
  innovative + conceptually well-evaluated; "too few subjects" when few exist in the domain or formal arguments
  carry part of the load; no replication package when there are genuine practical/ethical reasons; not comparing
  to tools that aren't publicly available/functional; not being the first solution (must beat prior on *some*
  dimension); no explicit RQ when a clear problem/objective is stated instead; the contribution "not being complicated."

### 6.3 Benchmarking Standard (our corpus / C06e arm) — Essential
- [ ] EITHER justifies use of an existing public/standard benchmark OR **defines a new benchmark** specifying:
      (i) the **quality** measured, (ii) the **metric(s)**, (iii) the **measurement method**, (iv) the
      **workload / usage profile / task sample** — and justifies the design and reuses established components
- [ ] describes the **experimental setup** in enough detail for **independent replication**
- [ ] specifies the **workload/usage profile** in enough detail for independent replication
- [ ] **allows different configurations to compete on their merits without artificial limitations**
- [ ] **assesses stability/reliability** with sufficient repetitions and execution duration
- [ ] **discusses the construct validity** of the benchmark — does it measure what it's supposed to?
- *Desirable:* supplementary datasets/scripts; benchmark in usable form; open-source; transparently reports
  problems executing runs.
- **Antipatterns:** **tailoring the benchmark to the method being evaluated**; using irrelevant benchmarks to
  obfuscate weaknesses; insufficient repetitions/duration; **persisting only aggregated measurements instead of
  all raw results** (keep raw results, analyse offline).
- **Invalid criticisms (do NOT penalise for):** the benchmark not being widely used (a proto-benchmark is a valid
  start); no independent replication reported; no independent maintaining organization.
- *General quality:* fairness of measurements, reproducibility across repetitions, benchmarking the **right**
  aspects, realistic/representative workload.

> Mapping to our harness: our paper must (6.2) describe the eight signals + driver in detail, justify why a
> paraphrase-resistant structural detector is needed, conceptually state each signal's strengths/limits
> (necessary-not-sufficient), name its empirical method (benchmarking + quantitative comparison across pairs),
> and compare to the v6/v7, v5/v6, v6/csn, and known-derivative alternatives. The C06e corpus must (6.3) define
> quality/metric/measurement/workload, support replication, assess stability, and discuss construct validity —
> and must **not** be tailored to make v6/v7 look any particular way (antipattern), which our pre-registered
> deterministic gates and null panel guard against. Keep **raw** witness results, not just aggregates.

---

## References (consult these when an item is contested)

**Standards & threats to validity**
- ACM SIGSOFT *Empirical Standards for Software Engineering Research* — method-specific checklists.
  arXiv:2010.03525; site www2.sigsoft.org/EmpiricalStandards. Raw standard bodies (use these to re-fetch):
  General `…/raw/master/docs/standards/GeneralStandard.md`, Engineering Research `…/EngineeringResearch.md`,
  Benchmarking `…/Benchmarking.md`, Replication `…/Replication.md`, plus Experiments / DataScience /
  RepositoryMining / OptimizationStudies / QuantitativeSimulation (list via the GitHub contents API at
  `api.github.com/repos/acmsigsoft/EmpiricalStandards/contents/docs/standards`). The §6 attribute lists above
  are quoted verbatim from the General, Engineering Research, and Benchmarking standards.
- Verdecchia, Engström, Lago et al., *Threats to validity in SE research: a critical reflection*,
  JSS 2023 (TTV must be contextual, not laundry lists).
- *Threats to Validity in SE — hypocritical section or essential analysis?* (review of 91 SIGSOFT
  distinguished papers), 2024 — TTV is mostly an "enforced afterthought."
- Baltes et al., *Evidence Tetris* — prioritise threats by synthesized evidence, not intuition.
- Feldt & Magazinius, *Validity Threats in Empirical SE: an Initial Survey*.

**Statistics**
- Kitchenham, Madeyski et al., *Robust Statistical Methods for Empirical SE* (trimmed means, Cliff's δ,
  kernel-density plots, rank-based methods).
- Kitchenham et al., *Recommendations for analysing small sample-size SE experiments*, EMSE 2024 (p̂,
  Cliff's d, Brunner-Munzel).
- *Evolution of statistical analysis in ESE: current state and steps forward*, arXiv:1706.00933
  (effect sizes, pitfalls, workflow).
- *A systematic review of effect size in SE experiments* (always report effect size; standardized + unstandardized).
- Furia, Feldt, Torkar, *Bayesian data analysis in empirical SE* / *Bayesian vs p-values*, arXiv:1811.05422.

**ML / detector evaluation pitfalls**
- Lones, *How to avoid machine learning pitfalls: a guide for academic researchers*, arXiv:2108.02497
  (the Do/Don't catalog: leakage, baselines, statistical tests, multiple-comparison correction,
  metric choice, don't believe benchmarks, report multiple ways, don't generalise).
- Kapoor & Narayanan, *Leakage and the Reproducibility Crisis in ML-based Science*, arXiv:2207.07048
  (leakage taxonomy; metric-choice issues; adopt the common-task framework).
- Larsen et al., *Which Leakage Types Matter? A Quantitative Landscape across 2,047 datasets*,
  arXiv:2604.04199 (selection/peeking leakage dominant; metric selection flips 31% of rankings).
- Opitz & Burst, *A Closer Look at Classification Evaluation Metrics*, TACL 2024 (define what you
  expect from a metric; chance correction).
- *Evaluating Supervised ML Models: Principles, Pitfalls, and Metric Selection*, arXiv:2604.13882.

**Reproducibility & artifacts**
- ACM *Artifact Review and Badging* (Available / Evaluated / Reproduced / Replicated).
- Siddiq et al., *The State of Open Science in SE: a Case Study of ICSE Artifacts* (2015–2024) —
  40/100 executable, 14/40 reproduced.
- *Reproducibility in LLM-based SE research* / Reproducibility Maturity Model — badges signal presence,
  not execution fidelity.
- *Lessons Learned from Five Years of Artifact Evaluations at EuroSys* (badge checklists).
