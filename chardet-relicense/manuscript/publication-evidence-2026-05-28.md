# Publication Evidence — chardet-relicense

Date: 2026-05-28

Repository: `/srv/repos/external/verivus-oss/agent-assurance-papers`

## Review Findings Addressed

- Title-page date removed (`\date{May 22, 2026}` → `\date{}`).
- Preamble hardened: `\usepackage[hyphens]{url}` and
  `\setlength{\emergencystretch}{3em}` added.
- Five filename case mismatches in prose corrected to match disk:
  `CONTRACT_DECLARATION.toml`, `IMPLEMENTATION_DAG.toml`,
  `VERIFICATION_REPORT.toml`, `USER_PROMPTS.md` → lowercase.
- Repository URL claim corrected: bundle path moved from
  `verivus-oss/agent-assurance` (which does not contain
  `chardet-relicense/`) to `verivus-oss/agent-assurance-papers`
  (which does). Reproduction recipe updated to clone both repos
  so the sibling `validators/` directory is also available.
- Validator invocation paths in Section 11.1 prefixed with
  `../agent-assurance/` to reflect the two-repo layout.
- LLM-authoring attribution rewritten: removed
  vendor/model-specific naming and updated the commit pin from
  the unresolvable `220cff4` to the current papers-repo HEAD
  `6acef08`.
- LOC counts updated: `extract_signals.py` still 589 (matches);
  `fingerprint_behavior.py` updated 228 → 232.
- Layers table (Table 1), validation-report-path prose
  (Section 4), and Results table (Table 4) re-laid-out with
  `tabularx` / `\path{}` to eliminate three Overfull \hbox
  warnings. Final build: 0 Overfull, 0 errors.
- License selected at arXiv upload: Creative Commons
  Attribution 4.0 International (CC BY 4.0,
  `http://creativecommons.org/licenses/by/4.0/`). This is
  durable per arXiv policy — future replacements may not
  downgrade the license. Recorded in `arxiv-metadata.md` and
  in this evidence record so replacement workflows do not
  silently lose the durable license commitment.
- `00README.json` written in the modern arXiv structured format
  (NOT the legacy `00README.XXX` format that stalled the
  hello-world paper's first upload attempt).
- Comments field at arXiv upload includes `Code:` and `Spec:`
  prefixed URLs so the abstract-listing page surfaces both
  artifact repositories without requiring the reader to open
  the PDF.

## Build Command

The source was rebuilt with the same TeX Live container used for the
hello-world precedent. TeX binaries live under
`/opt/texlive/texdir/bin/x86_64-linuxmusl` inside that image.

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

Observed output:

```text
This is BibTeX, Version 0.99e (TeX Live 2026)
The top-level auxiliary file: main.aux
The style file: plain.bst
Database file #1: references.bib
Output written on main.pdf (27 pages, 395450 bytes).
Transcript written on main.log.
```

Post-build sanity:

```text
$ grep -c '^Overfull' main.log
0
$ grep -c '^!' main.log
0
```

Cleveref required 4 pdflatex passes to settle all cross-references;
final pass reported no "Label(s) may have changed" message.

## Citation Sanity

```text
$ grep -oE '\\cite[a-z]*\{[^}]+\}' main.tex | sed 's/\\cite[a-z]*{//;s/}//' \
    | tr ',' '\n' | sort -u | wc -l
38
$ grep -oE '^@[a-zA-Z]+\{[^,]+' references.bib | sed 's/^@[a-zA-Z]*{//' \
    | sort -u | wc -l
38
$ diff <(grep -oE '\\cite[a-z]*\{[^}]+\}' main.tex | sed 's/\\cite[a-z]*{//;s/}//' \
        | tr ',' '\n' | sed 's/^ *//' | sort -u) \
       <(grep -oE '^@[a-zA-Z]+\{[^,]+' references.bib | sed 's/^@[a-zA-Z]*{//' | sort -u)
(no output — exact match)
```

## URL Status Check

```text
200	https://arstechnica.com/ai/2026/03/...
200	https://arxiv.org/abs/2202.07646
200	https://codespy.ai
403	https://copyleaks.com/codeleaks                          (Cloudflare bot-block; cosmetic)
200	https://daringfireball.net/linked/2026/03/08/...
200	https://en.wikipedia.org/wiki/Phoenix_Technologies
200	https://github.blog/2021-06-30-github-copilot-research-recitation/
200	https://github.com/chardet/chardet/issues/325
200	https://github.com/chardet/chardet/issues/327
200	https://github.com/jplag/JPlag
200	https://github.com/verivus-oss/agent-assurance/blob/main/spec.md
200	https://github.com/verivus-oss/sqry
200	https://heathermeeker.com/2026/04/09/...
200	https://jmlr.org/papers/v12/shervashidze11a.html
403	https://law.justia.com/cases/federal/appellate-courts/F2/977/1510/305345/  (justia anti-scrape; cosmetic)
200	https://lwn.net/Articles/1061534/
200	https://networkx.org/
405	https://researchrepository.ucd.ie/...                    (HEAD/method blocked; URL is live)
200	https://shujisado.org/2026/03/10/...
200	https://simonwillison.net/2026/Mar/5/chardet/
403	https://supreme.justia.com/cases/federal/us/101/99/      (justia anti-scrape; cosmetic)
200	https://www.jucs.org/jucs_8_11/finding_plagiarisms_among_a
200	https://www.supremecourt.gov/opinions/20pdf/18-956_d18f.pdf
200	https://www.theregister.com/2026/03/06/ai_kills_software_licensing
```

The four non-200 results are all known bot-detection responses on
legal-text aggregators and a marketing site. The URLs are live to
human browsers; the references remain accurate.

## Numeric Validation Cross-Check

The headline numbers in Table 4 were cross-checked against
`figures/scripts/validation_report.json` (the harness's own
independent re-derivation, captured at the May-22, 2026
run):

```text
== validation_report.json ==
aux1_matches            = 0        (paper: 0)
aux1_v6_files           = 87       (paper: 87)
aux1_v7_files           = 33       (paper: 33)
c06a_similarity         = 0.881    (paper: 0.881; exact float 0.8808640269160583)
c06a_v6_nodes / v7_nodes = 342 / 358   (paper: 342 / 358)
c06a_v6_edges / v7_edges = 488 / 659   (paper: 488 / 659)
c06b_jaccard            = 0.333    (paper: 0.333; exact float 0.3333333333333333)
c06b_shared             = ['cchardet','datasets']  (paper: cchardet, datasets)
c06c_cosine             = 0.984    (paper: 0.984; exact float 0.9844014929937703)
c06c_v6_total / v7_total = 652 / 848   (paper: 652 / 848)
c06d_shared / strict / renamed / diverged = 5 / 3 / 0 / 2   (paper: 3 strict / 0 renamed / 2 diverged of 5 shared)
c06e_exact_rate / bucket_rate / n_inputs = 0.0 / 0.0 / 1000   (paper: 0/1000; 0/1000)
c06e_corpus_digest      = 58e54831f84183c7   (paper: 58e54831f84183c7)
```

JPlag numbers cross-checked against
`figures/scripts/jplag_chardet_results.json`:

```text
similarities.AVG              = 0.0003751...      (paper: 0.04%)
similarities.MAX              = 0.01295...        (paper: 1.30%)
similarities.LONGEST_MATCH    = 18.0              (paper: "longest token match: 18 tokens")
similarities.MAXIMUM_LENGTH   = 247026.0          (paper: "roughly 247,000")
```

LOC pin verified locally:

```text
$ wc -l chardet-relicense/proof-bundle/extract_signals.py
589
$ wc -l chardet-relicense/proof-bundle/fingerprint_behavior.py
232
$ git rev-parse --short HEAD
6acef08
```

## Source Bundle Command

```sh
cd chardet-relicense/manuscript
tar --sort=name --owner=0 --group=0 --numeric-owner \
  --mtime='2026-05-28 00:00Z' \
  -czf arxiv_submission_bundle.tar.gz \
  00README.json main.tex references.bib \
  figures/fig1_implementation_dag.pdf \
  figures/fig2_topology_features.pdf \
  figures/fig3_control_flow_hist.pdf
```

Bundle contents:

```text
-rw-r--r-- 0/0     122 2026-05-28 10:00 00README.json
-rw-r--r-- 0/0   87917 2026-05-28 10:00 main.tex
-rw-r--r-- 0/0   20770 2026-05-28 10:00 references.bib
-rw-r--r-- 0/0   20498 2026-05-28 10:00 figures/fig1_implementation_dag.pdf
-rw-r--r-- 0/0   15428 2026-05-28 10:00 figures/fig2_topology_features.pdf
-rw-r--r-- 0/0   17813 2026-05-28 10:00 figures/fig3_control_flow_hist.pdf
```

The bundle does NOT include `00README.XXX`. The hello-world precedent
established that arXiv's web UI stalls indefinitely on the legacy
`.XXX` format; the modern `00README.json` format
(<https://info.arxiv.org/help/00README.html>) is used here from the start.

## arXiv Upload Metadata

To enter at the arXiv UI (recorded in `arxiv-metadata.md`):

- **Title**: Paraphrase-Resistant Detection of AI-Driven Code Rewrites:
  A Falsifiable Harness Applied to the chardet v6 to v7 Relicensing
  Dispute
- **Authors**: Werner Kasselman
- **Primary category**: `cs.SE`
- **Cross-list**: none (account endorsed for cs.SE only)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0),
  `http://creativecommons.org/licenses/by/4.0/`
- **Comments**: `27 pages, 3 figures; falsifiable detection harness
  for AI-driven code rewrites, applied to the chardet v6/v7
  relicensing dispute. Code:
  https://github.com/verivus-oss/agent-assurance-papers Spec:
  https://github.com/verivus-oss/agent-assurance`
- **Abstract**: see `arxiv-metadata.md` (plain-text rendering of the
  paper's `\begin{abstract}...\end{abstract}` block).

## Final Hashes

```text
84cd8ed8ea8d91e2c587afa2d03bf7a8284f606508e38ec771eb9a44f0bc3abd  chardet-relicense/manuscript/main.tex
23ee5ba7400f81a4106061469dad49fcedd8655afc26c4bd13d9f89214a74d60  chardet-relicense/manuscript/references.bib
867b808493f78f39365fd8ade98854b14010c7bfdd24de6fb262bb5b158399b3  chardet-relicense/manuscript/00README.json
c5898202c904d0eea57ab3876d6a60e81d8aa13e7f8d3841b64f0730b7e60180  chardet-relicense/manuscript/main.bbl   (local only)
e879739bfa28a021319d983b6dc639ecccd0f784679ebf3d5ba256ae292181ad  chardet-relicense/manuscript/main.pdf   (local only)
4c882da2bc1d731cc1f199adc5be3f41f128cd01292b130d7fa23a1451411ce6  chardet-relicense/manuscript/arxiv_submission_bundle.tar.gz
52185a8ab395d7d7aa6b38f1b36a7bd4584464d8daa91673a896520fe72a451b  chardet-relicense/manuscript/figures/fig1_implementation_dag.pdf
01a0cd0806e2b1740549927f766695a586435b15067bcffdc4bb54e982e9f070  chardet-relicense/manuscript/figures/fig2_topology_features.pdf
9d2ff592143792a8ff93441345381b70e34ed11a294263fdac37ff116064ae3a  chardet-relicense/manuscript/figures/fig3_control_flow_hist.pdf
```
