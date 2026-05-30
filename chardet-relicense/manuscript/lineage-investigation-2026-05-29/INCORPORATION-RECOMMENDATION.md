# How to incorporate the lineage + per-method trace into the paper — multi-LLM recommendation

Date: 2026-05-29. Status: **RECOMMENDATION ONLY — not yet implemented in main.tex, not yet
re-submitted for review.** Input findings: `FINDINGS.md` (this directory).

## Question posed to the reviewers
"Given the lineage + bidirectional per-method renaming-invariant trace in FINDINGS.md, give a
concrete, prioritized recommendation for how to incorporate it into `main.tex` to BROADEN the
analysis: placement, calibrated claims, narrative/legal-framing impact, what not to overclaim,
and reviewer objections to preempt. Ground every point in the actual files."

## Provenance (three independent LLM advisors, full repo read access)
- Codex (`latest`, dangerously-bypass sandbox) — job `f5065b8c-1f7d-4381-a40d-aa26dba4635c`
- Gemini (`latest`/gemini-3.1-pro-preview, yolo+skip-trust) — job `9281eb7b-92fc-44ea-a66f-693c7a2deb6d` (completed despite Google-side 429 capacity retries)
- Grok (`grok-build`, bypassPermissions+always-approve) — job `dae52660-b8b4-47ae-8e35-bdace9d7d506`

All three read FINDINGS.md + main.tex; recommendations cite specific paths/sections. They
converged strongly. This file records the synthesis plus per-model emphases.

---

## CONSENSUS RECOMMENDATION

### Core decision (unanimous)
Incorporate as **independent corroboration of C06f + calibration context — NOT a new bundled
signal (no "C06g") and NOT new harness numbers.** Rationale: the lineage/per-method work used
separate clones (`/srv/repos/public/lineage/`) + custom Python `ast` scripts, not
`extract_signals.py`. Under the paper's load-bearing invariant (every bundle number verbatim
from one harness run; see `CLAUDE.md`), these results must stay **out of the main 8-signal
tables/figures** and be presented as triangulating research. Promoting to a signal is premature
until run across v5/v6 and v6/charset_normalizer too, and would force a full re-validation cycle.

### Placement
1. **New Results subsection** by the sqry corroboration block (main.tex ~§1395 / §results-calibration
   ~§1224). Suggested title: *"Per-method renaming-invariant structural trace and gating
   sensitivity (corroboration of C06f)."* Contents: three-gate sensitivity (naive 80% → strict
   19% → load-bearing 0%); bidirectional load-bearing matrix (0/14 ↔ 0/15, invariant across
   50/80/100%); deep-dive (`UniversalDetector.feed` deep-nested cascade vs `_run_pipeline_core`
   flat guard-ladder — cosine 0.960 yet inverted topology); convergence with C06f 17.5%.
2. **Lineage/provenance paragraph** after the multi-pair calibration (or in Background §dispute
   ~§308). Taxonomy survival table (29→26→26→22→1→0) + density trajectory (1.48→1.60→2.17→1.20).
   Purpose: validates the v6/charset_normalizer independence baseline (0 shared markers) AND
   shows v6 was a stable 20-year Mozilla port that v7 structurally broke. Cite genuine FF45 C++.
3. **Future Work** (§Toward language-neutral extraction ~§1985): the §6 sqry design spec
   (body-shape descriptor + structural index + gated `shape-match` + cross-language
   canonicalization); frame `sqry similar` as name-based and the missing primitive as a contribution.
4. **Appendix**: full per-method tables + the three reproducible scripts.
5. **Minimal cross-refs**: one calibrated sentence each into abstract (after the C06f 17.5%
   clause) and §Legal; one per-band-reporting note into Threats (construct validity).

### Claims to add (calibrated phrasing)
- Lineage confirmed vs the **genuine Mozilla FF45 C++** (not just uchardet); charset_normalizer
  independent (0 markers, mess/coherence paradigm, only a `legacy detect()` shim + benchmarks).
- v7 **breaks** the 20-year architecture: markers 22→1, density 2.17→1.20, flat→layered `pipeline/`.
- **0/14** load-bearing v6 methods (cyc≥8) have a v7 structural twin; reverse **0/15**; invariant
  across coverage and direction.
- The C06f ~17.5% matched minority is **entirely trivial boilerplate** (cyc≤6 getters/inits/resets).
- Gating discipline: identical trace = **80% / 19% / 0%** by gate strength.
- Frame as **"structurally re-architected at the load-bearing level,"** never "legally independent."

### Legal framing (§Legal, two readings)
- Reading A (fair use / new expression): **strengthened** — even the shape layer shows no
  preservation of the load-bearing core.
- Reading B (derivative): **must move off "structural paraphrase"** onto training-data
  provenance, the plan document, public-API continuity, import-boundary continuity. Add (Gemini):
  *"Reading B can no longer rely on load-bearing structural paraphrase; it must argue the
  derivative taint survives a total re-architecture of the core logic."*
- universalchardet ancestor **broadens the protected-work frame** (Mozilla-derived LGPL lineage),
  but v7's taxonomy collapse cuts against a simple "same SSO survived" argument.

### What NOT to overclaim (unanimous guardrails)
Necessary-but-not-sufficient (a paraphrase that *also* re-architects yields the same 0%);
structural similarity = derivation OR domain convergence; taxonomy markers are name-retaining
lineage evidence (renaming-VARIANT), not paraphrase evidence; cross-language counts indicative
only (Python v6/v7 axis is rigorous); `sqry similar` is name-based ≠ C06f body-shape; aggregate
twin rate is a coverage artifact → report per-band; keep lineage numbers visibly separate from
the harness bundle (do not attribute to extract_signals.py / the proof DAG).

### Reviewer objections to preempt
- "FF45 ≠ exact 2006 fork" → use for lineage context, not dispositive legal proof.
- "0% is gate-tuned / cyc≥8 arbitrary" → publish 80→19→0 sensitivity + the per-band split +
  list the 14 load-bearing methods + invariance across coverage/direction.
- "Cherry-picked to v6/v7" → don't promote to a signal until run on v5/v6 + v6/csn.
- "Python-only / cross-language overstated" → taxonomy via preserved `ns*` names is robust;
  per-method is Python-Python only (stated).
- "Rewrites just differ by names" → the trace is renaming-invariant (CF histogram/arity/depth).
- "Ad-hoc metric" → independent descriptor converges on C06f's 17.5%; it *explains* that number.
- "Does it prove independence?" → no; load-bearing re-architecture, not legal independence.

### Recommended execution order
1. Draft the new Results subsection + lineage paragraph (quote FINDINGS tables; include script
   paths + reproducibility note; keep separate from harness tables).
2. Two calibrated sentences → abstract + §Legal; one per-band note → Threats.
3. Future-Work sqry design-spec paragraph.
4. Run the draft through the existing multi-LLM review loop (`review-2026-05-29/` packet +
   verification_report.toml), treating new prose as a *corroborative claim*, not a harness number.
5. Only later (v3): consider porting the gated trace into the proof-bundle as an optional C06f
   diagnostic mode — accepting the full re-validation cost per the CLAUDE.md invariant.

---

## Per-model emphases (where they added beyond the consensus)
- **Codex**: place the subsection *before* the sqry block; Reading-B should rely on
  provenance/plan/API/import/functional-target continuity; put long tables + sqry spec in an
  appendix; explicit preempts for FF45, gate-dependence, cyc≥8, cherry-pick, clean-room.
- **Grok**: most detailed; stresses the CLAUDE.md load-bearing invariant (lineage numbers are
  NOT harness output → cannot enter main tables without full re-harness); place subsection
  *after* the sqry block before "Independent numeric validation"; reframes the sqry section from
  "coarse corroboration" to "useful for taxonomy/topology + documented limits motivating the
  custom trace + a public design spec"; full execution order with a final "optional diagnostic
  mode in proof-bundle for v3" step.
- **Gemini**: augment C06f (§4.8) + interpretation (§5.2) directly with the gating discipline;
  add §5.3.1 "Lineage Validation: 20-Year Stability vs the v7 Break"; sharpest legal one-liner
  ("Reading B … must argue the derivative taint survives a total re-architecture"); strong
  emphasis on publishing the coverage-invariance matrix to preempt "gate-tuned" objections.

## Open decision for the human (Werner)
The one editorial call to confirm before drafting: **subsection vs. augmenting C06f in place**
(Codex/Grok favor a standalone corroboration subsection near sqry; Gemini favors enriching the
existing C06f + §5.2). Both are viable; standalone keeps the harness-vs-corroboration boundary
cleaner (preferred given the load-bearing invariant).
