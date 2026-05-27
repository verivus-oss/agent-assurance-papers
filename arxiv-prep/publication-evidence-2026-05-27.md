# Publication Evidence

Date: 2026-05-27

Repository: `/srv/repos/external/verivus-oss/agent-assurance-papers`

## Review Findings Addressed

- Stale publishable paths were removed from `arxiv-prep/main.tex`.
- Uppercase proof bundle filenames in `arxiv-prep/main.tex` were changed to the lowercase files on disk.
- `arxiv-prep/README.md` now points to `hello-world/proof-bundle/` and the sibling validator repo.
- `arxiv-prep/00README.XXX` records category, comments, license, and repository metadata.
- `arxiv-prep/arxiv-metadata.md` records the metadata to enter in the arXiv UI.
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
Output written on main.pdf (8 pages, 213366 bytes).
Transcript written on main.log.
```

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
  --mtime='2026-05-27 00:00Z' \
  -czf arxiv_submission_bundle.tar.gz \
  00README.XXX main.tex references.bib
```

Bundle contents:

```text
00README.XXX
main.tex
references.bib
```

## Final Hashes

```text
a29e0434b84a60d75bb938d6c164bf4d3a47e7ead02bc98a603d8e9bba8585f1  arxiv-prep/main.tex
5749f067db965cbcfda7003ca2b6775ba925a8fe3c4f868079a44962bf353cd0  arxiv-prep/references.bib
bf8c02acc101549eadb6d4f45207d55fe1dc0c1c73c6d8916dd0c16406f1eff5  arxiv-prep/00README.XXX
e3e3753368be8dafe1aa810b443d2bcd74a60a12ded3e605e67d312093fa9d46  arxiv-prep/main.pdf
2244abc915f18fe1779d4710fa1fd4d5646cbfb9164eb24892e6c7a2e52aaad9  arxiv-prep/main.bbl
511565b094a49829cb74a64c95e04204170e0b6c90ec2eea0b6c6bf72de2f830  arxiv-prep/arxiv_submission_bundle.tar.gz
ecd9adb02c22d2b06f68b3958b58a60fcf9e4eab112294fb733a5f5c144edf61  arxiv-prep/arxiv-metadata.md
```
