# arXiv Publication Verification Report

Date: 2026-05-27

Repository: `/srv/repos/external/verivus-oss/agent-assurance-papers`

Base commit: `3c9782e05d62 Initial papers workspace`

Current branch: `main`

Current local diff status before initial review: clean except this report, which was untracked.

Corrected publication state after reviewer findings: source paths and file
names were corrected, `arxiv-prep/` was made trackable, metadata was recorded,
and the PDF plus arXiv source bundle were regenerated from the corrected source.

## Review Target

The target is the arXiv publication package for the Hello-World proof paper:

- `arxiv-prep/main.tex`
- `arxiv-prep/references.bib`
- `arxiv-prep/00README.XXX`
- `arxiv-prep/arxiv_submission_bundle.tar.gz`
- `arxiv-prep/main.pdf`
- `arxiv-prep/README.md`
- `arxiv-prep/arxiv-metadata.md`
- `arxiv-prep-agent-dag.toml`
- `hello-world/proof-bundle/`

## Current Submission Artifact Hashes

```text
a29e0434b84a60d75bb938d6c164bf4d3a47e7ead02bc98a603d8e9bba8585f1  arxiv-prep/main.tex
5749f067db965cbcfda7003ca2b6775ba925a8fe3c4f868079a44962bf353cd0  arxiv-prep/references.bib
bf8c02acc101549eadb6d4f45207d55fe1dc0c1c73c6d8916dd0c16406f1eff5  arxiv-prep/00README.XXX
511565b094a49829cb74a64c95e04204170e0b6c90ec2eea0b6c6bf72de2f830  arxiv-prep/arxiv_submission_bundle.tar.gz
e3e3753368be8dafe1aa810b443d2bcd74a60a12ded3e605e67d312093fa9d46  arxiv-prep/main.pdf
ecd9adb02c22d2b06f68b3958b58a60fcf9e4eab112294fb733a5f5c144edf61  arxiv-prep/arxiv-metadata.md
```

## Corrective-Program Spec

A reviewer must inspect files and commands directly. Do not accept a summary as evidence.

Required checks:

1. Verify the manuscript does not publish stale paths from the old spec repo layout.
   The current papers repo stores the proof at `hello-world/proof-bundle/`.
   The old path `examples/proof-hello-world` must not remain in publishable source.

2. Verify the manuscript names actual files on disk:
   `implementation_dag.toml`, `traceability.toml`, `contract_declaration.toml`,
   `review_readiness.toml`, `evidence_matrix.toml`, `run_all.sh`,
   `detect_semantic_rewrite.sh`, and `detect_awk_rewrite.sh`.

3. Verify arXiv package hygiene against current arXiv TeX guidance:
   source bundle should contain only needed source inputs, no build logs, no PDF,
   no hidden files, no unused figures, no unrelated repository files, and no
   local scratch artifacts.

4. Verify the TeX source can compile under a reasonable TeX Live container or,
   if compilation cannot run, identify the missing runtime as a concrete blocker.
   The intended processor is `pdflatex`; bibliography uses BibTeX and `plainnat`.

5. Verify references are complete: every `\cite{...}` key in `main.tex` exists in
   `references.bib`; no unused bibliography entry should be treated as a blocker
   unless it affects arXiv compilation or reviewer trust.

6. Verify publication metadata is ready:
   title, author, abstract, category recommendation, comments, and license choice.
   Flag any metadata that needs explicit human confirmation.

7. Verify the paper is not framed as a survey or position paper. It should read as
   a small executable artifact report for `cs.SE`; if this is not defensible, state
   the arXiv moderation risk and the exact text that causes it.

8. Verify the package submitted to arXiv matches the checked source files. If any
   source file changes, the tarball and hashes must be regenerated.

## Approval Standard

Approval must be unconditional and based on inspected files, command outputs,
and persistent evidence. If a finding is raised, it must cite the exact file and
line or command output. If the reviewer cannot inspect enough local context, that
is a blocker, not an approval.
