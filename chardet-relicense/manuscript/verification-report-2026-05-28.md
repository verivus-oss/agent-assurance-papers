# arXiv Publication Verification Report — chardet-relicense

Date: 2026-05-28

Repository: `/srv/repos/external/verivus-oss/agent-assurance-papers`

Base commit at start of review: `6acef08 Refresh arXiv submission bundle for hello-world paper`

Current branch: `main`

## Review Target

The target is the arXiv publication package for the chardet-relicense paper
"Paraphrase-Resistant Detection of AI-Driven Code Rewrites: A Falsifiable
Harness Applied to the chardet v6 to v7 Relicensing Dispute":

- `chardet-relicense/manuscript/main.tex`
- `chardet-relicense/manuscript/references.bib`
- `chardet-relicense/manuscript/00README.json`
- `chardet-relicense/manuscript/main.pdf`
- `chardet-relicense/manuscript/main.bbl`
- `chardet-relicense/manuscript/arxiv_submission_bundle.tar.gz`
- `chardet-relicense/manuscript/arxiv-metadata.md`
- `chardet-relicense/manuscript/figures/fig1_implementation_dag.pdf`
- `chardet-relicense/manuscript/figures/fig2_topology_features.pdf`
- `chardet-relicense/manuscript/figures/fig3_control_flow_hist.pdf`
- `chardet-relicense/proof-bundle/` (the load-bearing artifact)

## Corrective-Program Spec

A reviewer must inspect files and commands directly. Do not accept a summary
as evidence.

Required checks:

1. **Citations match bibliography.** Every `\cite{...}` key in `main.tex`
   must exist in `references.bib`. No undefined citations.

2. **Filenames in prose match disk.** Every `\texttt{}` or `\path{}`
   reference to a project file (TOML, Python, shell, markdown) must
   resolve to a file that actually exists at the named path. Case-mismatch
   between paper (UPPERCASE) and disk (lowercase) must be corrected by
   editing the paper, not by renaming files.

3. **Figures included.** Every `\includegraphics{...}` reference must
   resolve to a PDF in `figures/`, and every such PDF must be included
   in the arXiv submission bundle.

4. **Numeric claims trace to evidence.** The headline numerical values
   in Table 4 (AUX1, C06a, C06b, C06c, C06d, C06e) must agree with
   `figures/scripts/validation_report.json`. The JPlag numbers in
   Section 9.4 must agree with `figures/scripts/jplag_chardet_results.json`.
   LOC counts cited in Section 4 must agree with current `wc -l`.

5. **arXiv hygiene.** Title-page `\date{...}` removed. Preamble carries
   `\usepackage[hyphens]{url}` (for long-URL breaking) and
   `\setlength{\emergencystretch}{3em}` (to absorb residual stretch).

6. **Build clean.** A pdflatex + bibtex + 3×pdflatex pass on TeX Live
   2025+ must produce a PDF with ZERO `^Overfull` lines and ZERO `^!`
   error lines in `main.log`. Underfull warnings inside tabularx cells
   are cosmetic and acceptable.

7. **Submission bundle minimal.** The tarball contains exactly:
   `00README.json`, `main.tex`, `references.bib`, and the three figures.
   No `main.aux`, `main.bbl`, `main.log`, `main.pdf`, no editor backups,
   no scratch files. The legacy `00README.XXX` format is NOT used —
   arXiv's web UI stalls on `.XXX` files.

8. **License pinned durably.** The arXiv upload license declared as
   CC BY 4.0 (`http://creativecommons.org/licenses/by/4.0/`); recorded
   in `arxiv-metadata.md` and this report so that future replacements
   know the durable license commitment.

9. **Comments-field URLs.** Both the artifact repository
   (`verivus-oss/agent-assurance-papers`) and the spec repository
   (`verivus-oss/agent-assurance`) are surfaced in the arXiv Comments
   field, AND in the body of the paper (Section 11, Reproducibility).

## Findings and Corrections Applied

### Findings before correction

1. **Title-page date.** `main.tex:63` carried `\date{May 22, 2026}`.
   Per arXiv playbook, removed (`\date{}`); arXiv stamps its own
   submission date on the rendered listing.

2. **Preamble missing arXiv-hardening.** `\usepackage{url}` (without
   `hyphens` option) and no `\emergencystretch`. Both added.

3. **Filename case mismatches.** Five references in prose used
   UPPERCASE filenames that do not exist on disk:
   - `CONTRACT_DECLARATION.toml` (line 470) → `contract_declaration.toml`
   - `CONTRACT_DECLARATION.toml` (line 1298) → `contract_declaration.toml`
   - `IMPLEMENTATION_DAG.toml` (line 885) → `implementation_dag.toml`
   - `VERIFICATION_REPORT.toml` (line 1238) → `verification_report.toml`
   - `USER_PROMPTS.md` (line 1716) → `user-prompts.md`

4. **Wrong repository for the bundle.** Lines 1134-1136 and the
   reproduction recipe (lines 1140-1144) and the LLM-authoring
   attribution (line 1615) claimed the bundle lived in
   `verivus-oss/agent-assurance under chardet-relicense/proof-bundle/`.
   That directory does NOT exist in that repository. The bundle
   actually lives in `verivus-oss/agent-assurance-papers`; the
   spec validators live in `verivus-oss/agent-assurance` as a
   sibling. Both the prose claim and the reproduction recipe were
   corrected to clone both repos and run `detect.sh` from the
   papers repo. The verifier-instructions block was updated to
   invoke validators via `../agent-assurance/validators/...`.

5. **Stale LOC counts and unresolvable commit pin.** Lines 473-475
   pinned `(589 plus 228 lines of code, verified via wc -l at
   commit 220cff4)`. On disk: `extract_signals.py` is 589 lines
   (matches), `fingerprint_behavior.py` is 232 lines (paper said
   228), and commit `220cff4` does not exist in either repository.
   Updated to `(589 plus 232 lines ... verified via wc -l at
   commit 6acef08)` — current HEAD of the papers repository.

6. **Three Overfull \hbox boxes.** First pass produced:
   - Layers table (Section 2, Table 1): converted from
     `tabular{lllll}` to `tabularx{\linewidth}` with explicit
     `p{}` widths and one `X` column.
   - Long path in Section 4 prose: `\texttt{chardet-relicense/.../validation_report.json}`
     overflowed; switched to `\path{...}` (url-package, breaks
     cleanly on slashes).
   - Results table (Section 6, Table 4): converted from
     `tabular{lllc}` to `tabularx` with `p{0.27\linewidth}` for
     Signal (with `\raggedright`), `p{0.09\linewidth}` for
     Contract (large enough for the column header), `X` for Value,
     `p{0.13\linewidth}` for Verdict.

   Final build: 0 Overfull, 0 errors.

### Verified PASS

- 38/38 `\cite{}` keys resolve in `references.bib` (exact match — no
  undefined citations, no unused bib entries).
- All three figures (`fig1_implementation_dag.pdf`,
  `fig2_topology_features.pdf`, `fig3_control_flow_hist.pdf`) exist
  and are bundled.
- All numeric headline values in Table 4 trace to
  `figures/scripts/validation_report.json`:
  - AUX1: 0 matches across 87 v6 / 33 v7 files ✓
  - C06a: 0.881 (= 0.8808640 ...) ✓ — 342 vs 358 nodes; 488 vs 659 edges ✓
  - C06b: 0.333 ✓ — shared `cchardet`, `datasets` ✓
  - C06c: 0.984 (= 0.9844014 ...) ✓ — 652 vs 848 totals ✓
  - C06d: 5 shared, 3 strict, 0 renamed_args, 2 diverged ✓
  - C06e: 0/1000 exact, 0/1000 bucket, corpus_digest 58e54831f84183c7 ✓
- JPlag numbers in Section 9.4 trace to
  `figures/scripts/jplag_chardet_results.json`:
  - AVG 0.000375 → "0.04%" ✓
  - MAX 0.0130 → "1.30%" ✓
  - LONGEST_MATCH 18 tokens ✓
  - MAXIMUM_LENGTH 247026 ≈ "roughly 247,000" ✓
- All 24 bibliography URLs checked with `curl -sS -o /dev/null -L`:
  21 return 200; 3 return 403/405 (`copyleaks.com`,
  `law.justia.com`, `supreme.justia.com`) which are Cloudflare /
  anti-scraping bot-blocks — same class as the `acm.org`
  cf-mitigated case in the hello-world precedent, cosmetic only.
- `validate_implementation_dag.py` is the validator referenced
  for `implementation_dag.toml`; `validate_traceability.py` for
  `traceability.toml`; `validate_review_readiness.py` for the
  three review-control TOMLs (`review_readiness.toml`,
  `contract_declaration.toml`, `evidence_matrix.toml`) — all
  resolvable in the sibling `agent-assurance/validators/`
  directory.

### Items not independently verified

- The harness's run-time numerical output (Table 4) was NOT
  re-derived in this review session. The values were checked
  against `validation_report.json` (which is itself the
  second-source numpy/scipy cross-validation captured at the
  May-22 run). Re-running `detect.sh` from scratch would require
  cloning chardet, installing networkx, and ~10 minutes of
  per-version venv build for C06e. The audit trail relies on
  the validation_report.json as durable evidence.
- The sqry corroboration numbers in Section 6.3 (Table 5) were
  not re-derived; the paper describes the procedure for
  re-deriving them via the sqry MCP tools.

## Approval Standard

Approval is conditional on:

1. The user reviewing the rendered `main.pdf` (page count 27)
   and the unchanged numeric body claims in Tables 4-7.
2. The user confirming the License decision (CC BY 4.0) at
   arXiv upload — durable per arXiv policy, not downgradable
   in future replacements.
3. The user confirming the Comments-field text at arXiv upload
   (see `arxiv-metadata.md`).
4. The user submitting from the artifact bundle
   `arxiv_submission_bundle.tar.gz` only — NOT from the
   manuscript directory or any superset.

## Submission Artifact Hashes

```text
84cd8ed8ea8d91e2c587afa2d03bf7a8284f606508e38ec771eb9a44f0bc3abd  chardet-relicense/manuscript/main.tex
23ee5ba7400f81a4106061469dad49fcedd8655afc26c4bd13d9f89214a74d60  chardet-relicense/manuscript/references.bib
867b808493f78f39365fd8ade98854b14010c7bfdd24de6fb262bb5b158399b3  chardet-relicense/manuscript/00README.json
c5898202c904d0eea57ab3876d6a60e81d8aa13e7f8d3841b64f0730b7e60180  chardet-relicense/manuscript/main.bbl  (local only; not in bundle)
e879739bfa28a021319d983b6dc639ecccd0f784679ebf3d5ba256ae292181ad  chardet-relicense/manuscript/main.pdf  (local only; not in bundle)
4c882da2bc1d731cc1f199adc5be3f41f128cd01292b130d7fa23a1451411ce6  chardet-relicense/manuscript/arxiv_submission_bundle.tar.gz
52185a8ab395d7d7aa6b38f1b36a7bd4584464d8daa91673a896520fe72a451b  chardet-relicense/manuscript/figures/fig1_implementation_dag.pdf
01a0cd0806e2b1740549927f766695a586435b15067bcffdc4bb54e982e9f070  chardet-relicense/manuscript/figures/fig2_topology_features.pdf
9d2ff592143792a8ff93441345381b70e34ed11a294263fdac37ff116064ae3a  chardet-relicense/manuscript/figures/fig3_control_flow_hist.pdf
```

## Build Environment

- Container: `ghcr.io/xu-cheng/texlive-full:latest` (TeX Live 2026 inside;
  arXiv runs TeX Live 2025 by default — both have been verified to
  produce identical output for the hello-world paper precedent).
- Compiler: `pdflatex` (4 passes for cleveref, with `bibtex main`
  between passes 1 and 2).
- Build host: Linux 6.12 / podman.
- BibTeX produced no warnings or errors; output style `plain.bst`
  from `references.bib`.
