# Hello-World Proof Paper

This directory contains a standalone paper package for the
`hello-world/proof-bundle` proof.

## Files

- `main.tex` - paper source.
- `references.bib` - BibTeX references used by the paper.
- `README.md` - build, verification, and packaging notes.

## Build

From this directory:

```sh
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

If TeX is unavailable, syntax-check the source enough to confirm that
all citation keys in `main.tex` exist in `references.bib` and that all
referenced local paths exist relative to the repository root.

## Verification Commands

Run these from the repository root:

```sh
bash hello-world/proof-bundle/run_all.sh
bash hello-world/proof-bundle/detect_semantic_rewrite.sh
bash hello-world/proof-bundle/detect_awk_rewrite.sh
python3 ../agent-assurance/validators/validate_implementation_dag.py hello-world/proof-bundle/implementation_dag.toml
python3 ../agent-assurance/validators/validate_traceability.py hello-world/proof-bundle/traceability.toml --repo-root . --check-paths-exist
python3 ../agent-assurance/validators/validate_review_readiness.py hello-world/proof-bundle/review_readiness.toml
python3 ../agent-assurance/validators/validate_review_readiness.py hello-world/proof-bundle/contract_declaration.toml
python3 ../agent-assurance/validators/validate_review_readiness.py hello-world/proof-bundle/evidence_matrix.toml
for f in hello-world/proof-bundle/*.toml; do python3 ../agent-assurance/validators/validate_ijb_conformance.py "$f" --repo-root ../agent-assurance; done
python3 ../agent-assurance/validators/validate_code_symbols.py hello-world/proof-bundle/traceability.toml --repo-root .
```

The paper also reports that running `validate_ijb_conformance.py` on
the instance TOML files without `--repo-root` fails because the validator
requires the spec repository root for ontology resolution.

## arXiv Packaging Notes

For a minimal arXiv TeX source package, include `main.tex`,
`references.bib`, and, if desired, a generated `main.bbl`. Do not include
local build outputs such as `.aux`, `.log`, `.out`, `.blg`, or the PDF in
the TeX source package.

The paper relies on standard `pdflatex`, BibTeX, `natbib`, and the
URL-emitting `plainnat` bibliography style. arXiv's current guidance
says authors must inspect the generated submission PDF, include required
bibliography/figure inputs, and remove extraneous source-package files.

**Canonical process:** use the spec-grounded DAG at repo root
`arxiv-prep-agent-dag.toml` (10 units, explicit gates for every item on
Trevor Campbell / official mistakes / Ian Huston / current submit_tex
checklists). It produces the exact tarball, 00README.XXX, and local
publication evidence needed for arXiv submission hygiene. Run the units
(or have an agent execute them) against `hello-world/manuscript/` or any
paper tree.
