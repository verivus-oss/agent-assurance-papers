# Publication Evidence

Date: 2026-05-27

Repository: `/srv/repos/external/verivus-oss/agent-assurance-papers`

## Review Findings Addressed

- Stale publishable paths were removed from `arxiv-prep/main.tex`.
- Uppercase proof bundle filenames in `arxiv-prep/main.tex` were changed to the lowercase files on disk.
- `arxiv-prep/README.md` now points to `hello-world/proof-bundle/` and the sibling validator repo.
- `arxiv-prep/00README.XXX` records category, comments, license, and repository metadata.
- `arxiv-prep/arxiv-metadata.md` records the metadata to enter in the arXiv UI.
- License selected at arXiv upload on 2026-05-28: Creative Commons
  Attribution 4.0 International (CC BY 4.0,
  <http://creativecommons.org/licenses/by/4.0/>). This selection is
  durable per arXiv policy — future replacements may not downgrade the
  license, so both `arxiv-metadata.md` and `00README.XXX` were updated
  to pin the actual choice rather than leaving the conditional
  "default unless author chooses CC" phrasing.
- Comments field updated at arXiv upload to surface the artifact and
  specification repository URLs (`Code:` and `Spec:` prefixes) on the
  abstract listing page. The URLs are also present in the rendered PDF
  in section "arXiv and Artifact Packaging Notes".
- `.gitignore` no longer hides the entire `arxiv-prep/` tree.
- The repository README describes the moved paper/proof layout without
  preserving obsolete spec-repo path strings.
- `hello-world/manuscript/` was synced to the corrected arXiv source and PDF
  so the repo does not carry conflicting versions of the same paper.
- README validator commands now distinguish papers-root path checks from
  spec-root ontology checks.
- `arxiv-prep-agent-dag.toml` now describes local publication evidence rather
  than a removed companion evidence tarball.
- The manuscript command table now reports IJB conformance with
  `--repo-root ../agent-assurance`; the papers repo root `--repo-root .`
  remains a documented failing invocation because it does not contain
  `core/ontology.toml`.
- Obsolete generated arXiv evidence from the old path layout was removed.

## Build Command

The source was rebuilt with the existing TeX Live container. The TeX binaries
are under `/opt/texlive/texdir/bin/x86_64-linuxmusl` inside that image.

```sh
cd arxiv-prep
rm -f main.aux main.bbl main.blg main.log main.out main.pdf
podman run --rm -v "$PWD:/work:Z" -w /work ghcr.io/xu-cheng/texlive-full:latest \
  sh -lc 'export PATH=/opt/texlive/texdir/bin/x86_64-linuxmusl:$PATH; \
    pdflatex -interaction=nonstopmode -halt-on-error main.tex >/tmp/pass1.log && \
    bibtex main >/tmp/bibtex.log && \
    pdflatex -interaction=nonstopmode -halt-on-error main.tex >/tmp/pass2.log && \
    pdflatex -interaction=nonstopmode -halt-on-error main.tex >/tmp/pass3.log && \
    pdflatex -interaction=nonstopmode -halt-on-error main.tex >/tmp/pass4.log && \
    cat /tmp/bibtex.log && tail -n 20 /tmp/pass4.log'
```

Observed output included:

```text
This is BibTeX, Version 0.99e (TeX Live 2026)
The top-level auxiliary file: main.aux
The style file: plainnat.bst
Database file #1: references.bib
Output written on main.pdf (8 pages, 211700 bytes).
Transcript written on main.log.
```

The 2026-05-28 rebuilds produced a slightly smaller PDF than the
original May-27 build because the title block no longer renders a date
line; the page count is unchanged. A follow-up rebuild on 2026-05-28
also enabled `\usepackage[hyphens]{url}` and
`\setlength{\emergencystretch}{3em}` to remove the last Overfull \hbox
warning in `\section{arXiv and Artifact Packaging Notes}` (the long
`agent-assurance-papers` URL); the rebuilt `main.log` has no Overfull
\hbox warnings.

## Validation Commands

Run from the repository root:

```sh
python3 ../agent-assurance/validators/validate_implementation_dag.py arxiv-prep-agent-dag.toml
python3 ../agent-assurance/validators/validate_ijb_conformance.py arxiv-prep-agent-dag.toml --repo-root ../agent-assurance

python3 ../agent-assurance/validators/validate_implementation_dag.py hello-world/proof-bundle/implementation_dag.toml
python3 ../agent-assurance/validators/validate_traceability.py hello-world/proof-bundle/traceability.toml --repo-root . --check-paths-exist
python3 ../agent-assurance/validators/validate_review_readiness.py hello-world/proof-bundle/review_readiness.toml
python3 ../agent-assurance/validators/validate_review_readiness.py hello-world/proof-bundle/contract_declaration.toml
python3 ../agent-assurance/validators/validate_review_readiness.py hello-world/proof-bundle/evidence_matrix.toml
for f in hello-world/proof-bundle/*.toml; do python3 ../agent-assurance/validators/validate_ijb_conformance.py "$f" --repo-root ../agent-assurance; done

bash hello-world/proof-bundle/run_all.sh
bash hello-world/proof-bundle/detect_semantic_rewrite.sh
bash hello-world/proof-bundle/detect_awk_rewrite.sh
```

Observed proof results:

```text
arxiv-prep-agent-dag.toml: implementation DAG validation passed; IJB conformance passed.
hello-world implementation DAG validation passed: 9 units, critical_path_loc 138.
traceability validation passed: 30 entities; path existence checks enabled.
review_readiness.toml, contract_declaration.toml, and evidence_matrix.toml passed.
IJB conformance passed for all five hello-world proof TOML files with --repo-root ../agent-assurance.
run_all.sh: 5 pass, 1 skip, 0 fail. Java skipped because javac/java was not on PATH.
detect_semantic_rewrite.sh: 8 pass, 0 skip, 0 fail.
detect_awk_rewrite.sh: 6 pass, 0 skip, 0 fail.
```

Negative-control command:

```text
python3 ../agent-assurance/validators/validate_ijb_conformance.py hello-world/proof-bundle/traceability.toml --repo-root .
IJB CONFORMANCE VALIDATION FAILED
- core ontology not found at .../agent-assurance-papers/core/ontology.toml
exit: 1
```

## Source Bundle Command

```sh
cd arxiv-prep
tar --sort=name --owner=0 --group=0 --numeric-owner \
  --mtime='2026-05-28 00:00Z' \
  -czf arxiv_submission_bundle.tar.gz \
  main.tex references.bib
```

Bundle contents:

```text
main.tex
references.bib
```

The bundle originally included `00README.XXX`, but the arXiv web UI
stalled indefinitely on that file during the first upload attempt and
only progressed after it was deleted from the upload set. `00README.XXX`
is retained in the repository as a local build-notes record but is no
longer included in the shipped tarball.

## Final Hashes

Refreshed 2026-05-28 after the title-page date was removed, the body
run date was updated from May 22 to May 27, 2026, and the preamble was
adjusted to eliminate the last Overfull \hbox warning.

```text
768cd7aa73f7b02348ebdf0d4203e78d602698952056d0dda99556e1be281cfc  arxiv-prep/main.tex
5749f067db965cbcfda7003ca2b6775ba925a8fe3c4f868079a44962bf353cd0  arxiv-prep/references.bib
a9aff3e4642eb6d5aa33418039ce6c5579975e63309387e5ec69537f55b4a327  arxiv-prep/00README.XXX  (local only; not in bundle; updated 2026-05-28 with CC BY 4.0 + repo URLs in Comments)
b82e5c5ade164bb4df62d46180d86fc6c0296c863fc2b57e13ea129ca760bb2a  arxiv-prep/main.pdf
2244abc915f18fe1779d4710fa1fd4d5646cbfb9164eb24892e6c7a2e52aaad9  arxiv-prep/main.bbl
c9c6237c5e8210f5ad548db02d9b215ef7c74c590e3b6788c4993438894d8360  arxiv-prep/arxiv_submission_bundle.tar.gz  (main.tex + references.bib only)
8dc9483d5a153e0663d6dc9810eda9cd5a552e23b9805b1204c867037a15518d  arxiv-prep/arxiv-metadata.md
```
