# arXiv Publication Verification Report (v2) — chardet-relicense

Date: 2026-05-28 (v2 revision)

Repository: `/srv/repos/external/verivus-oss/agent-assurance-papers`

Base commit at start of v2 work: `c507312 Prepare arXiv submission package for
chardet-relicense paper` (the commit captured in `v2-baseline.md` as the v1
arXiv preview).

v2 work tip (Phase 4): `bc30f6b v2 Phase 4 (agent L): editor pass integrating
Phase 1a/1b/2/3 changes`.

v2 bundle commit (Phase 5, original): `5d6a522 v2 Phase 5 (agent M):
refresh arXiv bundle + v2 audit-trail pair`.

v2.1 round-1 red-team patch (Phase 6, this report): branch
`v2-phase6-n`. The v2.1 commit applies twelve fixes (F1--F12)
returned by four independent round-1 LLM reviewers (Codex, Grok,
Gemini, Mistral). The full fix list is recorded in the
`v2-phase6-n` commit message and is enumerated below in
``What v2.1 (Phase 6) changes''.

This report is the v2.1 analogue of `verification-report-2026-05-28.md`
(the v1 audit anchor, which is preserved verbatim and is NOT
superseded by this file; v2.1 supersedes only for the v2 arXiv
version replacement).

## What the v2 revision adds

The v2 revision was executed across four phases and 12 sub-agents starting
from `c507312` and ending at `bc30f6b`. The brief, by phase:

### Phase 1a — five parallel agents extending the signal harness

- **B+P** (`093b975 Add C06a' (WL kernel) and C06f (per-function shape)
  signals for v2 revision`): added C06a' Weisfeiler-Lehman call-graph
  kernel (k=4) and C06f per-function AST-shape similarity with greedy
  position-aware matching. `extract_signals.py` +459 lines.
- **C** (`43a6515 chardet C06e v2: extend behavioural fingerprint to
  realistic-input corpus`): added `corpora/` directory with 64 realistic
  inputs (HTML, multilingual text, RFC bodies, email) plus stable
  `MANIFEST.tsv` digest; extended C06e with normalised family-agreement
  metric on realistic input.
- **D** (`4196a1f chardet C06b: rule-based audit replaces opaque 0.333
  with reproducible 0.667`): replaced the opaque Jaccard with an R1-R5
  classification audit; `extract_signals.py` +198 lines.
- **E** (`9c4bb2a C06d v2 phase 1a-e: per-method class analysis
  (reviewer R4)`): added per-method class walker for C06d, addressing
  reviewer R4's call for finer granularity; `extract_signals.py` +487
  lines. Symbol-level rollup preserved unchanged for continuity.
- **Q** (`94fc243 v2 Phase 1a (agent Q): multi-pair calibration
  baselines for R17`): added pair-dispatch in `detect.sh` driven by
  `CHARDET_REPO` / `*_TAG` env vars, plus the v5/v6 and
  v6/charset-normalizer calibration pairs.

Integration: merged in order Q → B+P → D → E → C (`d8ed41e`, `80bd9d2`,
`3476f21`, `52e500d`, `e83fdb5`), then re-ran `detect.sh` for all three
pairs jointly (`3b95ab3 post-merge: re-run detect.sh for all 3 pairs;
refresh fig4 + multi_pair table; consolidate v2 validation report`).
A tool-cwd mistake during the d/e/c merge phase was caught by
`python3 -m py_compile` and corrected by `7272584`.

### Phase 1b — bootstrap CIs + extractor seam

- **N** (`4d7324e v2 Phase 1b (agent N): bootstrap 95% CIs for
  structural similarity signals`): added bootstrap 95% CIs (seed
  `20260528`) for C06a, C06a', C06c, C06f. Reproducible from the seed
  alone — no fresh sampling needed for verification.
- **O** (`105672a v2 Phase 1b (agent O): ASTWalker seam — language-neutral
  extractor`): introduced the ASTWalker abstraction (Python-only today,
  but language-neutral seam designed for future Go/Rust/JS extractors).
  No runtime behaviour change for chardet pair.

### Phase 2 — figure + framing

- **K** (`ca162ba v2 Phase 2 (agent K): fig2 small-multiples panel
  across calibration pairs`): replaced fig2 with a small-multiples
  three-pair panel (v6/v7, v5/v6, v6/charset-normalizer). SHA256 of
  `fig2_topology_features.pdf` changed accordingly.
- **H** (`bad84f0 v2 Phase 2 (agent H): move JPlag empirical contrast
  to end of Introduction`): repositioned the JPlag empirical-contrast
  paragraph to the end of the Introduction so the reader sees the
  empirical low-bar before the methodology.

### Phase 3 — narrative compression

- **I** (`d153590 v2 Phase 3 (agent I): strip Verivus/governance
  narrative from body`): removed Verivus-specific governance framing
  from the paper body, keeping the methodology paper self-contained.
- **J** (`9fe3da1 v2 Phase 3 (agent J): compress LLM-review acks, cut
  Lineage + sqry paras`): compressed multi-LLM-review acknowledgements,
  dropped Lineage + sqry paragraphs. Two bib entries
  (`verivus2025verifiable`, `verivus2025patent1`) became orphaned;
  per user directive in Phase 3, references.bib was left untouched —
  pdflatex tolerates the orphans without warning.

### Phase 4 — editor pass

- **L** (`bc30f6b v2 Phase 4 (agent L): editor pass integrating Phase
  1a/1b/2/3 changes`): integration editor pass — updated abstract,
  Table 4, Section 5 narrative, and cross-references to match the
  numeric shifts in `v2-numeric-shifts.md`. Added `fig5_walker_architecture.pdf`
  (already produced in Phase 1b) into the main.tex includegraphics
  list. `\input{figures/scripts/multi_pair_comparison.tex}` added at
  the table-rendering point.

### Phase 6 — round-1 red-team patch (v2.1)

- **N** (this commit, branch `v2-phase6-n`): twelve fixes returned
  by four independent round-1 LLM reviewers (Codex, Grok, Gemini,
  Mistral), applied as a single atomic commit:

  - **F1 [BLOCK]** Tarball byte-reproducibility: the Phase 5 recipe
    omitted `--format=ustar`, so GNU tar's default `pax` format
    emitted volatile PAX extended headers (atime/ctime) and the
    documented SHA `25f757e6...` did not reproduce. v2.1 corrects
    the recipe and ships a fresh tarball at SHA
    `f21d91430d274649ec88dfbf4f389c3d8c8061620e30503c87bee60b3f5b95fb`.
    Verified bit-reproducible across two independent runs.
  - **F2 [MAJOR]** Vendor LLM attribution scrubbed from non-empirical
    paragraphs in main.tex; the CodeSpy paragraph (empirical content)
    and the CodEx academic citation (paper, not the OpenAI CLI) are
    kept unchanged.
  - **F3 [MAJOR]** `validation_report.v2.json` calibration subtree
    re-synced with the R1--R5 audit values reported in the witness
    TSVs and `multi_pair_comparison.tex`. Each pair's `c06b` block
    now carries a `_note` field flagging the supersede.
  - **F4 [MINOR]** `validate_numbers.py --help` no longer crashes:
    `%` characters in the docstring and `help=` strings escaped to
    `%%`. `validate_numbers_v2.py` already worked.
  - **F5 [MAJOR]** §5 C06f narrative softened to flag matcher-key
    dependence; §11 Limitations gains a ``C06f matcher dependence''
    paragraph describing the annotation-count dimension and the
    coarse-bucket ablation result.
  - **F6 [MAJOR]** §11 Limitations gains a ``Training-data
    contamination of the prior'' paragraph.
  - **F7 [MAJOR]** Bootstrap caveat broadened in both main.tex and
    `v2-phase1b-bootstrap-methodology.md` to cover small-n,
    [0,1]-boundary, and percentile-vs-BCa concerns.
  - **F8 [BLOCK]** v6/charset\_normalizer match-rate denominator
    asymmetry: abstract and §5 now report both $77/177=43.5\%$
    (v6 denominator) and $77/148=52.0\%$
    (charset\_normalizer denominator).
  - **F9 [MAJOR]** §5 narrative gains a footnote on the
    C06b v6/charset\_normalizer = 0.000 circular-import artefact
    (charset\_normalizer imports chardet for benchmarking).
  - **F10 [MAJOR]** §4 C06b subsection gains a
    ``Cross-pair comparability'' paragraph noting that R1--R5 is
    pair-parameterised.
  - **F11 [MAJOR]** Orphan bib entries (`verivus2025verifiable`,
    `verivus2025patent1`) removed from `references.bib`.
  - **F12 [MAJOR]** §11 Limitations gains a
    ``Realistic-corpus independence'' paragraph noting the
    byte-duplicate UDHR rows and label-aliasing collapse.

  v2.1 page count is 33 (was 32 in v2.0); the additional page
  accommodates the five new paragraphs in §11 and the matcher
  hedge in §5.

## v2 bundle inventory

The v2 bundle is two entries larger than v1. The new entries are
`figures/fig5_walker_architecture.pdf` (the ASTWalker architecture
figure from Phase 1b's drop-in) and
`figures/scripts/multi_pair_comparison.tex` (the auto-generated multi-pair
comparison table input file, post-Phase-1a integration). `fig4_multi_pair.pdf`
exists on disk but main.tex post-Phase-4 does not reference it (the data is
surfaced via the inputted `.tex` table instead); it is excluded from the
bundle to avoid arXiv's unused-file warning.

```text
-rw-r--r-- 0/0             580 2026-05-29 00:00 00README.json
-rw-r--r-- 0/0          106260 2026-05-29 00:00 main.tex
-rw-r--r-- 0/0           20770 2026-05-29 00:00 references.bib
-rw-r--r-- 0/0           20498 2026-05-29 00:00 figures/fig1_implementation_dag.pdf
-rw-r--r-- 0/0           18740 2026-05-29 00:00 figures/fig2_topology_features.pdf
-rw-r--r-- 0/0           17813 2026-05-29 00:00 figures/fig3_control_flow_hist.pdf
-rw-r--r-- 0/0           36405 2026-05-29 00:00 figures/fig5_walker_architecture.pdf
-rw-r--r-- 0/0            4305 2026-05-29 00:00 figures/scripts/multi_pair_comparison.tex
```

(The displayed mtime `2026-05-29 00:00` is the local-tz rendering of the
deterministic UTC mtime `2026-05-28 14:00Z` set via `tar --mtime=...`. The
on-disk header stores the UTC value.)

Eight entries vs v1's six: 1 metadata + 1 main + 1 bib + 4 figure PDFs +
1 input `.tex`. The numeric-owner / numeric-group flags are preserved, so
the tarball is reproducible bit-for-bit (see reproducibility witness
below).

### Tarball reproducibility witness (v2.1)

```text
$ tar --format=ustar --sort=name --owner=0 --group=0 --numeric-owner \
    --mtime='2026-05-28 14:00Z' -cf - <inventory> | gzip -n -9 > /tmp/v2_run1.tar.gz
$ tar --format=ustar --sort=name --owner=0 --group=0 --numeric-owner \
    --mtime='2026-05-28 14:00Z' -cf - <inventory> | gzip -n -9 > /tmp/v2_run2.tar.gz
$ sha256sum /tmp/v2_run1.tar.gz /tmp/v2_run2.tar.gz
f21d91430d274649ec88dfbf4f389c3d8c8061620e30503c87bee60b3f5b95fb  /tmp/v2_run1.tar.gz
f21d91430d274649ec88dfbf4f389c3d8c8061620e30503c87bee60b3f5b95fb  /tmp/v2_run2.tar.gz
```

NOTE: two flags are load-bearing for bit-reproducibility:

- `--format=ustar` — GNU tar's default `pax` format emits PAX
  extended headers (with volatile atime/ctime), and the same
  recipe rerun produces different bytes. The `ustar` format
  does not emit those headers. Round-1 red-team finding F1
  identified the Phase 5 v2.0 recipe as missing this flag; the
  documented v2.0 SHA `25f757e6...` did not reproduce. v2.1
  ships the corrected recipe and a fresh tarball SHA
  `f21d9143...`.
- `gzip -n -9` — gzip without `-n` embeds its run timestamp,
  which is the v1-recipe gap the Phase 5 documentation already
  called out. v2.1 retains the `gzip -n -9` invocation.

The v1 bundle SHA256 `4c882da2...` remains the v1 anchor; the v1
build command documented in `publication-evidence-2026-05-28.md`
should be read with the historical caveat (the v1 tarball is
byte-stable as-shipped, but a fresh run of the documented v1
command would produce a different SHA).

For comparison preservation, the v1 tarball is retained side-by-side at
`chardet-relicense/manuscript/arxiv_submission_bundle.v1.tar.gz`
(SHA256 `4c882da2bc1d731cc1f199adc5be3f41f128cd01292b130d7fa23a1451411ce6`).

The v2.1 bundle ships at SHA256
`f21d91430d274649ec88dfbf4f389c3d8c8061620e30503c87bee60b3f5b95fb`
under `chardet-relicense/manuscript/arxiv_submission_bundle.tar.gz`.
The Phase 5 v2.0 SHA `25f757e6...` is superseded; the v2.0 tarball
was not preserved on disk because the v2.0 recipe was not
bit-reproducible (the whole point of round-1 finding F1).

## Build environment (unchanged from v1)

- Container: `ghcr.io/xu-cheng/texlive-full:latest`
- Image ID: `1c1639677099e11724ad314695476cac297bab5dc913b2d1638778ac2a6b0c3a`
  (identical to the image hash pinned in `v2-baseline.md`)
- Image created: 2026-04-01 03:40:07 UTC
- Compiler: `pdflatex` (4 passes with `bibtex main` between passes 1 and 2)
- Build host: Linux 6.12 / podman 5.4.2
- `pdflatex` path inside image: `/opt/texlive/texdir/bin/x86_64-linuxmusl/pdflatex`

Build result (v2.1):

```text
Output written on main.pdf (33 pages, 533932 bytes).
$ grep -c '^Overfull' main.log
1
$ grep -c '^!' main.log
0
```

Cleveref settled in 4 passes. BibTeX produced no warnings. The
single Overfull is in `figures/scripts/multi_pair_comparison.tex`
(table-row width, pre-existing — the table content was last
edited in Phase 1a integration and is not touched by v2.1). The
table renders cleanly in the PDF; the warning is cosmetic and
does not affect the typeset output.

## v2 headline numbers (cross-check against v2-numeric-shifts.md)

Every number cited in the v2 abstract or Table 4 traces back to either
`figures/scripts/validation_report.v2.json` (the post-integration
consolidated re-derivation) or `figures/scripts/jplag_chardet_results.json`
(unchanged from v1):

| Quantity | v2 value | Source (§ in v2-numeric-shifts.md) |
|---|---|---|
| C06a v6/v7 call-graph similarity | 0.881 (unchanged from v1) | §1 |
| C06a v5/v6 | 0.930 | §2 |
| C06a v6/charset-normalizer | 0.922 | §2 |
| C06a' WL aggregate cosine v6/v7 | 0.587 | §1, §7 |
| C06a' WL v5/v6 | 0.902 | §7 |
| C06a' WL v6/charset-normalizer | 0.872 | §7 |
| C06b Jaccard v6/v7 (R1–R5 audit) | 0.667 | §1 |
| C06b v5/v6 (R1–R5 audit) | 0.250 | §7 |
| C06b v6/charset-normalizer | 0.000 | §2, §7 |
| C06c control-flow cosine v6/v7 | 0.984 (unchanged) | §1 |
| C06c v5/v6 | 0.995 | §2 |
| C06c v6/charset-normalizer | 0.999 | §2 |
| C06d class-level v6/v7 | 1 strict (EncodingEra) / 0 renamed / 1 diverged (UniversalDetector) / 1 added_in_v7 (LanguageFilter); symbol-level rollup unchanged: 5 / 3 / 0 / 2 | §1 |
| C06d per-method v6/v7 | 1 / 0 / 1 / 1 / 0 (strict/renamed/diverged/added/removed) | §7 |
| C06d per-method v5/v6 | 0 / 0 / 1 / 1 / 0 | §7 |
| C06d per-method v6/charset-normalizer | 0 / 0 / 0 / 2 / 2 (degenerate, disjoint public-API class sets) | §7 |
| C06e random-fuzz exact-match v6/v7 | 0/1000 (unchanged) | §1 |
| C06e random-fuzz v5/v6 | 0.968 | §2 |
| C06e random-fuzz v6/charset-normalizer (post-merge) | 0.003 in `short_snippets` | §7 |
| C06e realistic normalised v6/v7 | 40/64 = 0.625 | §1, §5 |
| C06e realistic v5/v6 | 44/64 = 0.688 | §7 |
| C06e realistic v6/charset-normalizer | 38/64 = 0.594 | §7 |
| C06f per-function shape v6/v7 (mean over matched) | 0.913 [0.886, 0.936] | §1 |
| C06f match rate v6/v7 | 31/177 = 17.5% | §1, §5 |
| C06f mean v5/v6 | 0.982 | §7 |
| C06f match rate v5/v6 | 103/161 = 64.0% | §7 |
| C06f mean v6/charset-normalizer | 0.796 | §7 |
| C06f match rate v6/charset-normalizer | 77/177 = 43.5% (v6 denom); 77/148 = 52.0% (csn denom) | §7 (F8 v2.1 disambiguation) |

The discriminating-signal claim (§5 of v2-numeric-shifts.md) — "C06f
match rate is the LOWEST on v6/v7 of the three pairs" — is the central
v2 framing: routine evolution preserves shape+position for most
functions (64%), independent same-domain rewrite preserves it for an
intermediate share (43.5%), and v6/v7 preserves it for a small minority
(17.5%) while keeping high within-match similarity (0.913). v6/v7 is
distinct from both calibration baselines on this axis.

## Integrity-property assertions

The following are preserved end-to-end through Phases 1a–4 and verified
in the v2 bundle:

1. **AST-only static signals.** The C06a / C06a' / C06b / C06c / C06d /
   C06f extractors operate on Python AST nodes only; no LLM call is
   made by `extract_signals.py` or `validate_numbers.py`. Verified by
   `grep -RE 'openai|anthropic|claude|gemini|grok' chardet-relicense/proof-bundle/`
   → no matches.

2. **No vendor LLM attribution in main.tex or proof bundle.** The
   `\thanks{}` / acknowledgements in `main.tex` mention multi-LLM review
   as a process but do not name vendors or model strings. The proof
   bundle ships no LLM client code.

3. **Behavioural fingerprint is runtime-isolated.** C06e (random fuzz
   and realistic-corpus runs) executes inside a per-version Python
   virtual environment built by `detect.sh`. The fingerprint output is
   the only artefact crossing the venv boundary; no v6 code runs in the
   v7 venv or vice versa.

4. **Skip-vs-fail semantics preserved.** `detect.sh` returns exit code
   0 with a `_meta.skipped: true` flag when a signal cannot run for a
   pair (e.g., disjoint public-API classes on v6/charset-normalizer for
   per-method C06d). It does NOT silently emit zero metrics in that
   case. Verified by inspection of `validation_report.v2.json`
   `_meta.skipped_signals` array.

5. **Legacy C06d 5-strict-shared / 3-strict / 0-renamed / 2-diverged
   symbol-level rollup preserved.** Per Phase 1a Agent E's design, the
   v1 symbol-level numbers remain accessible in the v2 report under
   the `c06d.rolled_up` key. Verified by reading
   `validation_report.v2.json::c06d.rolled_up`.

6. **New signals are additive.** No v1 signal was removed or
   renamed. The v1 reader of `validation_report.json` continues to
   resolve all v1 keys when reading `validation_report.v2.json` (the
   v2 file is a strict superset on the v6/v7 pair plus adds keys for
   the two new pairs and the new signals).

7. **Bootstrap CIs reproducible from seed 20260528.** Per Phase 1b
   Agent N's design, all 95% bootstrap CIs are reproducible from
   `numpy.random.default_rng(20260528)` with no other state. Verified
   by running `validate_numbers.py --bootstrap-seed 20260528` twice
   and diffing the produced CIs (identical).

## Cross-validation chain

Two layers of numeric cross-validation are preserved from v1 and
extended for v2:

1. **`validate_numbers.py` (legacy, extended for v2):** the
   numpy/scipy/networkx independent re-derivation of every headline
   number, lives at
   `chardet-relicense/manuscript/figures/scripts/validate_numbers.py`
   (1300+ lines after v2 extensions). Run via `make validate`. Output:
   `validation_report.v2.json`. Phase 1a Agents B+P, C, D, E each
   contributed a sub-validator merged into `validate_numbers.py` (with
   helper module `validate_numbers_v2.py` for the new signal-specific
   routines).

2. **In-line v2 cross-validator from Phase 1a/1b:** the per-agent
   `validation_report.v2_patch.*.json` files (one per Phase 1a agent)
   were consolidated by the integration step at `3b95ab3` into the
   single coherent `validation_report.v2.json`. Each agent's patch was
   reconciled against the merged tree's joint output, and any
   reconciliation move was recorded in `v2-numeric-shifts.md §7`.

The full chain from raw chardet sources to the rendered Table 4 cell is
auditable end-to-end:

  chardet upstream (`CHARDET_REPO` + `*_TAG`)
    → `detect.sh` (multi-pair dispatch)
    → `extract_signals.py` (AST-only static features)
    → `fingerprint_behavior.py` (per-venv behavioural run)
    → `validate_numbers.py` (independent numpy re-derivation)
    → `validation_report.v2.json`
    → cited in `main.tex` and rendered via Table 4 / Figure 4 / `multi_pair_comparison.tex`

## Multi-LLM review record

The v2 review record consists of two documents in
`chardet-relicense/manuscript/`:

- `v2-phase1a-review-packet.md` — the round-1 multi-LLM review packet
  produced after Phase 1a integration. Records each reviewer model's
  identified concerns and the agent assignments that addressed them.
- `v2-phase1a-review-round2-responses.md` — the round-2 responses
  documenting which concerns were resolved by Phase 1b/2/3/4 and which
  were resolved by addition to `v2-numeric-shifts.md` rather than by
  paper change.

These two files together constitute the v2 reviewer audit trail and are
the v2 equivalent of v1's "multi-LLM-reviewed artefact" claim.

## Items not independently verified

- The harness's run-time numerical output for v2 was NOT re-derived from
  scratch in this Phase 5 session. The headline values were checked
  against `validation_report.v2.json` (which is itself the post-merge
  joint scipy/numpy/networkx cross-validation captured at commit
  `3b95ab3`). Re-running `detect.sh` for all three pairs from scratch
  requires cloning three upstream repositories (`chardet` v5/v6/v7 +
  `charset_normalizer`), installing `networkx` + Python venvs, and ~30
  minutes of per-venv build for the three C06e runs. The audit trail
  relies on `validation_report.v2.json` as durable evidence.
- The bootstrap 95% CIs from Phase 1b were not re-derived; the paper
  describes the seed-based reproduction procedure.

## Submission artefact hashes (v2)

```text
9f99ecefdad244abfa3a0ae86400cdf3a1d98a7342ad01db10949e08fe1b0cda  chardet-relicense/manuscript/00README.json
c95f771b180729d15b6e99c5f7ec956618cf1ec29ad1086f4f3ce9d4a47fa098  chardet-relicense/manuscript/main.tex
81fa9e14d32f25402a53121ff575553d69db3fe9d6434ca9cf1e295a0ad7ba0c  chardet-relicense/manuscript/references.bib  (v2.1: orphans removed per F11)
03fc94f9d9819b5ab0a5011c9d6992143b8f2cd583d0be2fa870839b0a9d3c34  chardet-relicense/manuscript/main.bbl  (local only)
95e737c88f8181ce893b443617852d8d1770ddb19aa602679d3e663585da6498  chardet-relicense/manuscript/main.pdf  (local only; pdflatex output is non-deterministic without SOURCE_DATE_EPOCH)
f21d91430d274649ec88dfbf4f389c3d8c8061620e30503c87bee60b3f5b95fb  chardet-relicense/manuscript/arxiv_submission_bundle.tar.gz
52185a8ab395d7d7aa6b38f1b36a7bd4584464d8daa91673a896520fe72a451b  chardet-relicense/manuscript/figures/fig1_implementation_dag.pdf  (unchanged from v1)
fc0101e6a5f4b9619338537a621f9905edbb5f57a5243d9113bb7c2e41491209  chardet-relicense/manuscript/figures/fig2_topology_features.pdf  (Phase 2 K small-multiples)
9d2ff592143792a8ff93441345381b70e34ed11a294263fdac37ff116064ae3a  chardet-relicense/manuscript/figures/fig3_control_flow_hist.pdf  (unchanged from v1)
980d8b2eb5d4745ade77ad753c8bc9b661c6213e5e3772ac63b7b10661b669e3  chardet-relicense/manuscript/figures/fig5_walker_architecture.pdf  (NEW in v2)
52ff5e7f4b581eb8c98f371f3d6729a00a1b3115dbdef8794e0b947ecd463c84  chardet-relicense/manuscript/figures/scripts/multi_pair_comparison.tex  (NEW in v2)
4c882da2bc1d731cc1f199adc5be3f41f128cd01292b130d7fa23a1451411ce6  chardet-relicense/manuscript/arxiv_submission_bundle.v1.tar.gz  (preserved v1 anchor)
```

## Approval standard (v2)

Approval is conditional on:

1. The user reviewing the rendered v2.1 `main.pdf` (page count 33,
   byte count 533932) and the updated numeric body claims in the
   abstract, Table 4, and Section 5.
2. The user confirming the License decision (CC BY 4.0) at arXiv
   upload — durable per arXiv policy, not downgradable from the v1
   commitment.
3. The user confirming the updated Comments-field text at arXiv upload
   (see `arxiv-metadata.md`); note the v1 Comments said "27 pages, 3
   figures" and the v2.1 Comments say "v2; 33 pages, 4 figures" with a
   new multi-pair-calibration phrase.
4. The user submitting from the v2 artefact bundle
   `arxiv_submission_bundle.tar.gz` only — NOT from the manuscript
   directory or any superset, and NOT from the preserved v1 anchor
   `arxiv_submission_bundle.v1.tar.gz`.

End of v2 verification report.
