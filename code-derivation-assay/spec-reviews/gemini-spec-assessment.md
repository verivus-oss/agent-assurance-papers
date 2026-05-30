# gemini Spec Review: `code-derivation-assay`
**Model:** gemini (independent reviewer)
**Date:** 2026-05-29 08:30:38 UTC

This document constitutes a comprehensive, independent assessment of the `code-derivation-assay` (CDA) study specification. The review was conducted against the provided `SPECIFICATION.md`, the `RESEARCH-QUALITY-GUIDE.md` rubric, and the full context of the predecessor `chardet-relicense` study, including its reviews and confirmed defects.

---

## 1. Overall Assessment & Recommendation

**Recommendation: Approve to proceed to pre-registration**

The CDA specification is an exceptionally well-designed and rigorous plan for a study in empirical software engineering. It not only proposes a valuable contribution but also serves as a model for how to conduct reproducible, falsifiable, and transparent research. It systematically identifies every major failing of its predecessor and proposes a specific, robust, and verifiable engineering solution for each one. The design's emphasis on a ground-truth benchmark, scope-explicit metrics, statistical rigor, and non-negotiable reproducibility (`R-NODRIFT`, `R-HERMETIC`) is exemplary.

The few issues identified are not fundamental design flaws but rather opportunities to further tighten an already strong specification, primarily by reducing researcher degrees of freedom and strengthening the construct validity of the benchmark. There are no blocking issues that would prevent this study from proceeding.

---

## 2. Detailed Findings by Section

This assessment is structured to follow the specification's own sections and the explicit requirements of the review prompt.

### Finding 1: Design Soundness & Lessons→Requirements (§2)
**Severity: [nit]**
**Location:** `/srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay/SPECIFICATION.md:§2`

The lessons-to-requirements table (§2) is the intellectual core of this spec, and it is overwhelmingly successful. The requirements `R-SCOPE`, `R-NODRIFT`, `R-BENCH`, `R-HERMETIC`, and `R-ADVERSARIAL` are direct and potent fixes for the confirmed defects L1, L2, L3, L8, and L10 of the predecessor study.

The only minor ambiguity lies in `R-SCOPE`'s `custom-glob` option (§5.3). While the spec wisely defaults the headline classifier to the `package` scope, a researcher could still introduce degrees of freedom by performing exploratory analysis on a hand-picked `custom-glob`. This is a very minor concern, as the spec's transparency requirements would likely make such cherry-picking obvious.

**Recommendation:** Consider adding a sentence to §5.3 or §11 requiring that any use of `custom-glob` for a confirmatory claim must be justified and pre-registered with the exact glob pattern.

### Finding 2: Benchmark Design (§6)
**Severity: [major]**
**Location:** `/srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay/SPECIFICATION.md:§6`, `§13`, `§18`

The move to a multi-family, multi-class benchmark is the single biggest improvement over the predecessor. However, the study's external validity for claims about "AI rewrites" hinges critically on the composition of this benchmark.

The spec correctly identifies the threat: "Constructed derivatives could be unrepresentative of real AI rewrites" (§13). The mitigation is to include *natural* DERIVED pairs (forks, ports) alongside the constructed ones. However, the *ratio* of natural vs. constructed pairs is left as an open decision for the principal investigator (§18.5). This is a significant researcher degree of freedom. If the benchmark ends up with, for example, 38 constructed pairs and only 2 natural ones, any conclusions about "AI rewrites" would be weak, resting almost entirely on the potentially unrepresentative construction pipeline.

**Recommendation:** The specification should be strengthened to require a minimum number or proportion of *natural* derivation pairs within the DERIVED class. For example, require that at least 25% of the DERIVED pairs (or a minimum of 5, whichever is greater) be from natural, documented forks or ports. This would provide a much stronger foundation for generalizing findings to real-world phenomena.

### Finding 3: Construct Validity (§5)
**Severity: [minor]**
**Location:** `/srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay/SPECIFICATION.md:§6.4`

The operationalization of "derivation" and the signal families (ST, BH, PB) are well-conceived. The primary risk to construct validity is the potential for circularity between the *constructed*-derivative pipeline (§6.4) and the `ST` (Structural) metrics. For instance, if the pipeline's "paraphrase" step only renames identifiers and the ST metrics are designed to be invariant to identifier renaming, the study would simply be confirming its own setup.

The spec mitigates this by including source-blind `BH` (Behavioral) metrics and `natural` derived pairs. However, the "constructed-derivative pipeline" itself is underspecified. To further de-risk circularity, the spec should elaborate on the nature of the transforms.

**Recommendation:** Add a requirement in §6.4 that the documented transform pipeline must include a variety of transforms, and that the set of transforms must not be trivially invertible by the `ST` metrics. For example, it should do more than just apply transformations that the metrics are explicitly designed to ignore. It should also include more complex, semantics-preserving refactorings.

### Finding 4: Statistical Plan (§9) & Reproducibility (§10)
**Severity: [nit]**
**Location:** `/srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay/SPECIFICATION.md:§9`, `§10`

The statistical plan and reproducibility engineering are both exemplary. They are models of best practice, directly incorporating the recommendations of the `RESEARCH-QUALITY-GUIDE.md`.
- **Stats (§9):** The use of appropriate effect sizes (Cliff's δ), multiplicity correction (Holm-Bonferroni), bootstrap CIs, and pre-registered power analysis is excellent.
- **Repro (§10):** `R-NODRIFT` is the perfect solution to the predecessor's validator drift. The "rendered number == recomputed number" CI check is a powerful invariant. `R-HERMETIC`'s intolerance for `SKIP` verdicts on behavioral metrics is another critical, robust fix.

There are no findings of concern in these sections. They are the strongest parts of an already strong specification.

### Finding 5: Feasibility & Missing Pieces
**Severity: [minor]**
**Location:** `/srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay/SPECIFICATION.md:§6.2`

The biggest execution risk is the construction of the benchmark itself. Identifying and curating ≥8 suitable library families, each with the necessary instances for the 4 label classes (especially `INDEPENDENT` clean-room pairs and `DERIVED` natural forks), is a significant undertaking. The spec acknowledges this by listing "Final family list" as a PI decision point (§18.1), but the difficulty of this task should not be underestimated. This is not a flaw in the spec, but a pragmatic risk to the project's timeline and feasibility.

**Recommendation:** No change to the spec is required, but the Principal Investigator should treat benchmark curation as a high-risk, high-effort task critical to the entire study's success.

---

## 3. Issues That Would Prevent Approval

As of this review, there are **no blocking issues**. The specification is sound. My recommendation would change to **major redesign needed** if the following were true:
1.  If the `R-NODRIFT` or `R-HERMETIC` requirements were removed or significantly weakened, as this would re-introduce the fatal flaws of the predecessor study.
2.  If the study were to revert to a single-case (n=1) design without the multi-family benchmark.
3.  If the `R-SCOPE` requirement were dropped, allowing for undisclosed scope-hacking.

None of these are the case. The current design is robust.

---

## 4. Summary of Strengths and Weaknesses

**Single Most Important Thing the Spec Gets Right:**
The specification's greatest strength is its profound and effective response to the failings of prior work. The `R-NODRIFT` invariant (§10.1), which ensures that every number in the paper is mechanically and continuously validated by the CI pipeline, is a powerful and definitive solution to the "validator drift" problem that delegitimized the predecessor. It sets a new standard for computational reproducibility.

**Single Most Dangerous Gap:**
The most dangerous gap is the potential for the "constructed derivatives" to be unrepresentative of real-world AI-generated code, coupled with the specification leaving the ratio of *natural* to *constructed* derivatives as a PI decision (§18.5). This creates a risk that the study, despite its methodological rigor, could produce a precise-but-wrong result, making strong claims about "AI rewrites" based on a benchmark that doesn't reflect them realistically. This is why the finding on benchmark composition (§6) is rated [major].

---

## 5. Tool Usage

The following tools were available and used for this assessment:
- `read_file`: To read all specification and context documents.
- `run_shell_command`: To get the current UTC date for the report header.

No other specialized tools or MCPs were necessary to complete this specification review.