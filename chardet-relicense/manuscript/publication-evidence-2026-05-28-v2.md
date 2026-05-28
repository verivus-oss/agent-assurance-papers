# Publication Evidence (v2) — chardet-relicense

Date: 2026-05-28 (v2 revision)

Repository: `/srv/repos/external/verivus-oss/agent-assurance-papers`

This file is the v2 analogue of `publication-evidence-2026-05-28.md` (v1).
The v1 note remains the v1 anchor and is NOT replaced; this v2 note
supersedes only for the v2 arXiv version replacement.

## Audit chain pointing back to v1

- v1 commit on `main`: `c5073123 Prepare arXiv submission package for
  chardet-relicense paper` (this is the commit pinned by `v2-baseline.md`
  as the v1 arXiv preview).
- v1 bundle SHA256: `4c882da2bc1d731cc1f199adc5be3f41f128cd01292b130d7fa23a1451411ce6`
  (unchanged; preserved at
  `chardet-relicense/manuscript/arxiv_submission_bundle.v1.tar.gz`).
- v1 audit pair (`verification-report-2026-05-28.md`,
  `publication-evidence-2026-05-28.md`) unchanged on disk; this v2 note
  does not edit them.
- v2 work tip: branch `v2-phase6-n` (v2.1 after round-1 red-team
  patch — see the v2-phase6-n commit for the 12 fixes F1-F12).
  Phase 5 parent: `5d6a522 v2 Phase 5 (agent M): refresh arXiv bundle
  + v2 audit-trail pair`.
- v2 bundle SHA256:
  `f21d91430d274649ec88dfbf4f389c3d8c8061620e30503c87bee60b3f5b95fb`
  (v2.1; rebuilt with the corrected `--format=ustar` recipe — see
  `Source bundle command (v2)` below. The Phase 5 v2.0 SHA
  `25f757e6...` is superseded; it was produced before the PAX-header
  diagnosis. The v1 bundle SHA `4c882da2...` remains the v1
  anchor and is preserved on disk.).

## Build command (unchanged container, unchanged recipe)

The v2 source was rebuilt with the same TeX Live container as v1.

```sh
cd chardet-relicense/manuscript
rm -f main.aux main.bbl main.blg main.log main.out main.pdf main.toc
podman run --rm -v "$PWD:/work:Z" -w /work ghcr.io/xu-cheng/texlive-full:latest \
  sh -lc 'export PATH=/opt/texlive/texdir/bin/x86_64-linuxmusl:$PATH; \
    pdflatex -interaction=nonstopmode -halt-on-error main.tex && \
    bibtex main && \
    pdflatex -interaction=nonstopmode -halt-on-error main.tex && \
    pdflatex -interaction=nonstopmode -halt-on-error main.tex && \
    pdflatex -interaction=nonstopmode -halt-on-error main.tex'
```

Container ID (verified):
`1c1639677099e11724ad314695476cac297bab5dc913b2d1638778ac2a6b0c3a`
(same image hash as v1, per `v2-baseline.md`).

Observed output (v2.1 after round-1 red-team patch; page count
rose from 32 to 33 to accommodate the new C06f matcher-ablation,
training-contamination, realistic-corpus-independence, and
cross-pair-comparability paragraphs):

```text
This is BibTeX, Version 0.99e (TeX Live 2026)
The top-level auxiliary file: main.aux
The style file: plain.bst
Database file #1: references.bib
Output written on main.pdf (33 pages, 533932 bytes).
Transcript written on main.log.
```

Post-build sanity:

```text
$ grep -c '^Overfull' main.log
0
$ grep -c '^!' main.log
0
```

Cleveref settled in 4 passes; final pass reported no "Label(s) may have
changed" message.

## Citation sanity (v2.1)

```text
$ grep -oE '\\cite[a-z]*\{[^}]+\}' main.tex | sed 's/\\cite[a-z]*{//;s/}//' \
    | tr ',' '\n' | sort -u | wc -l
36
$ grep -oE '^@[a-zA-Z]+\{[^,]+' references.bib | sed 's/^@[a-zA-Z]*{//' \
    | sort -u | wc -l
36
$ diff <(grep -oE '\\cite[a-z]*\{[^}]+\}' main.tex | sed 's/\\cite[a-z]*{//;s/}//' \
        | tr ',' '\n' | sed 's/^ *//' | sort -u) \
       <(grep -oE '^@[a-zA-Z]+\{[^,]+' references.bib | sed 's/^@[a-zA-Z]*{//' | sort -u)
(no output: every bib entry has at least one cite, every cite has a bib entry).
```

Phase 6 N removed the two orphan entries (`verivus2025verifiable`,
`verivus2025patent1`) per round-1 red-team finding F11: arXiv's
guidance is that every bib entry be cited, and the citing
paragraphs were already gone (Phase 3 J's Lineage+sqry trim).

## URL status check (v2)

The v2.1 references.bib differs from v1 only in the removal of two
orphan entries (`verivus2025verifiable`, `verivus2025patent1`)
per round-1 red-team finding F11. No URL changes were made. The
v2.1 references.bib sha256 is
`81fa9e14d32f25402a53121ff575553d69db3fe9d6434ca9cf1e295a0ad7ba0c`;
the v1 references.bib sha256 was
`23ee5ba7400f81a4106061469dad49fcedd8655afc26c4bd13d9f89214a74d60`.
The v1 URL-status table in
`publication-evidence-2026-05-28.md` applies unchanged: 24 URLs, 21 of
which return 200, 3 of which return 403/405 from known anti-scrape
endpoints (`copyleaks.com`, `law.justia.com`, `supreme.justia.com`,
`researchrepository.ucd.ie`) — all cosmetic, links live to a human
browser.

## Numeric validation cross-check

The v2.1 headline numbers cross-checked against
`figures/scripts/validation_report.v2.json` (the post-merge joint
re-derivation captured at `3b95ab3`, then patched by Phase 6 N to
synchronise the C06b calibration subtree with the R1--R5 audit
values reported in the witness TSVs and `multi_pair_comparison.tex`
— round-1 red-team finding F3):

```text
== validation_report.v2.json (v6/v7 pair) ==
c06a_similarity         = 0.881    (paper: 0.881)
c06a_prime_wl_aggregate = 0.587    (paper: 0.587)
c06b_jaccard_r1r5       = 0.667    (paper: 0.667)
c06c_cosine             = 0.984    (paper: 0.984)
c06d_class_strict / renamed / diverged / added_in_v7 = 1 / 0 / 1 / 1   (paper: 1 strict EncodingEra / 0 / 1 diverged UniversalDetector / 1 added LanguageFilter)
c06d_rolled_up          = 5 / 3 / 0 / 2                                (paper: legacy symbol-level rollup unchanged)
c06d_per_method (strict/renamed/diverged/added/removed) = 1 / 0 / 1 / 1 / 0
c06e_random_exact_rate  = 0.000    (paper: 0/1000)
c06e_realistic_normalised = 40/64 = 0.625   (paper: 62.5%)
c06f_mean_similarity     = 0.913    (paper: 0.913 [0.886, 0.936])
c06f_match_rate          = 31/177 = 0.175   (paper: 17.5%)

== validation_report.v2.json (v5/v6 pair) ==
c06a = 0.930; c06a' = 0.902; c06b = 0.250; c06c = 0.995; c06e_random = 0.968;
c06e_realistic = 44/64 = 0.688; c06f_mean = 0.982; c06f_rate = 103/161 = 0.640;
c06d_per_method = 0 / 0 / 1 / 1 / 0

== validation_report.v2.json (v6/charset-normalizer pair) ==
c06a = 0.922; c06a' = 0.872; c06b = 0.000; c06c = 0.999; c06e_random = 0.003 (short_snippets);
c06e_realistic = 38/64 = 0.594; c06f_mean = 0.796; c06f_rate = 77/177 = 0.435;
c06d_per_method = 0 / 0 / 0 / 2 / 2 (degenerate — disjoint class sets)
```

JPlag numbers (Section "JPlag Comparison") unchanged from v1; sourced
from `figures/scripts/jplag_chardet_results.json`:

```text
similarities.AVG              = 0.0003751...      (paper: 0.04%)
similarities.MAX              = 0.01295...        (paper: 1.30%)
similarities.LONGEST_MATCH    = 18.0              (paper: "longest token match: 18 tokens")
similarities.MAXIMUM_LENGTH   = 247026.0          (paper: "roughly 247,000")
```

## Source bundle command (v2.1)

```sh
cd chardet-relicense/manuscript
tar --format=ustar --sort=name --owner=0 --group=0 --numeric-owner \
  --mtime='2026-05-28 14:00Z' \
  -cf - \
  00README.json main.tex references.bib \
  figures/fig1_implementation_dag.pdf \
  figures/fig2_topology_features.pdf \
  figures/fig3_control_flow_hist.pdf \
  figures/fig5_walker_architecture.pdf \
  figures/scripts/multi_pair_comparison.tex \
  | gzip -n -9 > arxiv_submission_bundle.tar.gz
```

Two flags are load-bearing for byte-reproducibility:

- `--format=ustar` — GNU tar's default `pax` format emits PAX
  extended headers that include volatile `atime`/`ctime` fields,
  so the same recipe run twice produces different bytes. The
  `ustar` format does not emit those headers and is bit-stable.
  (Round-1 red-team finding F1 surfaced this: the Phase 5 v2.0
  recipe omitted `--format=ustar` and the documented v2.0 SHA
  `25f757e6...` did not reproduce; the v2.1 SHA below does.)
- `gzip -n -9` — gzip without `-n` embeds its run timestamp,
  which is the v1-recipe gap the Phase 5 documentation already
  called out.

## Tarball reproducibility witness (v2.1)

```text
$ INV="00README.json main.tex references.bib \
       figures/fig1_implementation_dag.pdf \
       figures/fig2_topology_features.pdf \
       figures/fig3_control_flow_hist.pdf \
       figures/fig5_walker_architecture.pdf \
       figures/scripts/multi_pair_comparison.tex"
$ tar --format=ustar --sort=name --owner=0 --group=0 --numeric-owner \
    --mtime='2026-05-28 14:00Z' -cf - $INV | gzip -n -9 > /tmp/v2_run1.tar.gz
$ tar --format=ustar --sort=name --owner=0 --group=0 --numeric-owner \
    --mtime='2026-05-28 14:00Z' -cf - $INV | gzip -n -9 > /tmp/v2_run2.tar.gz
$ sha256sum /tmp/v2_run1.tar.gz /tmp/v2_run2.tar.gz
f21d91430d274649ec88dfbf4f389c3d8c8061620e30503c87bee60b3f5b95fb  /tmp/v2_run1.tar.gz
f21d91430d274649ec88dfbf4f389c3d8c8061620e30503c87bee60b3f5b95fb  /tmp/v2_run2.tar.gz
```

## Bundle contents

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

Eight entries (1 metadata + 1 main + 1 bib + 4 figure PDFs + 1 input
`.tex`). Displayed mtime `2026-05-29 00:00` is the local-tz rendering
(host is on a +10 tz offset) of the deterministic UTC mtime
`2026-05-28 14:00Z` set via `tar --mtime=...`; the on-disk header
stores the UTC value.

`fig4_multi_pair.pdf` exists on disk (Phase 1a Q produced it,
Phase 1a integration refreshed it) but main.tex post-Phase-4 does
not reference it — the multi-pair data is surfaced via the inputted
`multi_pair_comparison.tex` table — so it is EXCLUDED from the
bundle to avoid arXiv's unused-file warning.

`00README.json` is in the modern arXiv structured format
(<https://info.arxiv.org/help/00README.html>), not the legacy
`.XXX` format. The v2 file lists all eight bundle entries, with the
new entries marked `"usage": "include"` so arXiv's autotex driver
picks them up.

## Integrity-property assertions (publication-evidence form)

A reader who downloads `arxiv_submission_bundle.tar.gz` (SHA256
`f21d91430d274649ec88dfbf4f389c3d8c8061620e30503c87bee60b3f5b95fb`) can
externally verify the following without trusting this document:

1. **Tarball reproducibility.** Running the v2.1 tar command above on
   the in-bundle source files (cloned at this commit) reproduces the
   bundle SHA bit-for-bit. The `--format=ustar` flag is load-bearing;
   omitting it causes GNU tar's default `pax` format to emit
   volatile PAX extended headers and break bit-reproducibility (the
   v2.0 documentation regression that round-1 red-team finding F1
   identified).

2. **PDF reproducibility.** Running the documented `podman run ... pdflatex`
   sequence on the bundle source (with the same TeX Live image hash
   `1c1639677099e1...`) reproduces a 33-page, 533932-byte PDF.

3. **Numeric headline traceability.** Every number cited in the abstract
   and Table 4 can be checked against the public
   `figures/scripts/validation_report.v2.json` in the artefact repository
   (the bundle itself does not ship the JSON, to keep the bundle minimal,
   but the JSON is a checked-in artefact in the papers repo and is
   reproducible by running `make validate` against `validate_numbers.py`).

4. **No vendor LLM dependency.** The bundle contains no LLM client code
   and no API keys. The signal extractors (`extract_signals.py`,
   `validate_numbers.py`) operate on Python AST nodes only.

5. **Bootstrap CI reproducibility.** All 95% bootstrap CIs in the v2
   text are reproducible from `numpy.random.default_rng(20260528)`. No
   fresh sampling is required to verify them.

6. **Symbol-level C06d rollup preservation.** A v1 reader can still find
   the "5 strict-shared / 3 strict / 0 renamed / 2 diverged" symbol-level
   numbers in `validation_report.v2.json` under `c06d.rolled_up`, so the
   v1 numeric anchor for that signal remains externally verifiable.

## arXiv upload metadata (v2)

To enter at the arXiv UI for the v2 replacement (recorded in
`arxiv-metadata.md`):

- **Title**: Paraphrase-Resistant Detection of AI-Driven Code Rewrites:
  A Falsifiable Harness Applied to the chardet v6 to v7 Relicensing
  Dispute (UNCHANGED FROM v1).
- **Authors**: Werner Kasselman (UNCHANGED).
- **Primary category**: `cs.SE` (UNCHANGED).
- **Cross-list**: none (UNCHANGED).
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0),
  `http://creativecommons.org/licenses/by/4.0/` (UNCHANGED — durable per
  arXiv policy).
- **Comments**: `v2; 33 pages, 4 figures; falsifiable detection harness
  for AI-driven code rewrites, applied to the chardet v6/v7 relicensing
  dispute, now with multi-pair calibration (v5/v6, v6/v7,
  v6/charset-normalizer) and four new signals (C06a' Weisfeiler-Lehman,
  C06f per-function shape, per-method C06d, realistic-corpus C06e).
  Code: https://github.com/verivus-oss/agent-assurance-papers
  Spec: https://github.com/verivus-oss/agent-assurance`
- **Abstract**: see `arxiv-metadata.md` (v2 abstract; plain-text
  rendering of the paper's `\begin{abstract}...\end{abstract}` block at
  commit `bc30f6b`).

## Final hashes (v2.1)

```text
9f99ecefdad244abfa3a0ae86400cdf3a1d98a7342ad01db10949e08fe1b0cda  chardet-relicense/manuscript/00README.json
c95f771b180729d15b6e99c5f7ec956618cf1ec29ad1086f4f3ce9d4a47fa098  chardet-relicense/manuscript/main.tex
81fa9e14d32f25402a53121ff575553d69db3fe9d6434ca9cf1e295a0ad7ba0c  chardet-relicense/manuscript/references.bib  (v2.1: orphans removed per F11)
03fc94f9d9819b5ab0a5011c9d6992143b8f2cd583d0be2fa870839b0a9d3c34  chardet-relicense/manuscript/main.bbl   (local only)
95e737c88f8181ce893b443617852d8d1770ddb19aa602679d3e663585da6498  chardet-relicense/manuscript/main.pdf   (local only; pdflatex output is non-deterministic without SOURCE_DATE_EPOCH, so this hash is for the final build of the v2.1 commit and will differ on re-runs by reader)
f21d91430d274649ec88dfbf4f389c3d8c8061620e30503c87bee60b3f5b95fb  chardet-relicense/manuscript/arxiv_submission_bundle.tar.gz
52185a8ab395d7d7aa6b38f1b36a7bd4584464d8daa91673a896520fe72a451b  chardet-relicense/manuscript/figures/fig1_implementation_dag.pdf  (unchanged from v1)
fc0101e6a5f4b9619338537a621f9905edbb5f57a5243d9113bb7c2e41491209  chardet-relicense/manuscript/figures/fig2_topology_features.pdf  (Phase 2 K small-multiples)
9d2ff592143792a8ff93441345381b70e34ed11a294263fdac37ff116064ae3a  chardet-relicense/manuscript/figures/fig3_control_flow_hist.pdf  (unchanged from v1)
980d8b2eb5d4745ade77ad753c8bc9b661c6213e5e3772ac63b7b10661b669e3  chardet-relicense/manuscript/figures/fig5_walker_architecture.pdf  (NEW in v2)
52ff5e7f4b581eb8c98f371f3d6729a00a1b3115dbdef8794e0b947ecd463c84  chardet-relicense/manuscript/figures/scripts/multi_pair_comparison.tex  (NEW in v2)
4c882da2bc1d731cc1f199adc5be3f41f128cd01292b130d7fa23a1451411ce6  chardet-relicense/manuscript/arxiv_submission_bundle.v1.tar.gz  (preserved v1 anchor)
```

End of v2 publication evidence.
