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

Refreshed 2026-05-28 after (a) removing the title-page date from
`main.tex` (`\date{May 22, 2026}` → `\date{}`), (b) updating the
body-text run date from May 22 to May 27, 2026, (c) eliminating the
last Overfull \hbox warning by enabling `\usepackage[hyphens]{url}` and
`\setlength{\emergencystretch}{3em}` in the preamble, (d) dropping the
legacy `00README.XXX` from the upload bundle because the arXiv web UI
stalled on it during the first upload attempt, and (e) adding a
minimal `00README.json` to the bundle in the modern arXiv structured
format (spec: <https://info.arxiv.org/help/00README.html>) pinning
`compiler=pdflatex` and `main.tex` as the toplevel source. The legacy
`00README.XXX` file is preserved in the repository as a local
build-notes record but is no longer shipped to arXiv.

```text
768cd7aa73f7b02348ebdf0d4203e78d602698952056d0dda99556e1be281cfc  arxiv-prep/main.tex
5749f067db965cbcfda7003ca2b6775ba925a8fe3c4f868079a44962bf353cd0  arxiv-prep/references.bib
867b808493f78f39365fd8ade98854b14010c7bfdd24de6fb262bb5b158399b3  arxiv-prep/00README.json
a9aff3e4642eb6d5aa33418039ce6c5579975e63309387e5ec69537f55b4a327  arxiv-prep/00README.XXX  (local only; not in bundle; updated 2026-05-28 with CC BY 4.0 + repo URLs in Comments)
afa68651352203527ec292e9946f0a179cbcfbcfbeaca3c9a9fb95c79ea129f2  arxiv-prep/arxiv_submission_bundle.tar.gz  (00README.json + main.tex + references.bib)
b82e5c5ade164bb4df62d46180d86fc6c0296c863fc2b57e13ea129ca760bb2a  arxiv-prep/main.pdf
8dc9483d5a153e0663d6dc9810eda9cd5a552e23b9805b1204c867037a15518d  arxiv-prep/arxiv-metadata.md
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
