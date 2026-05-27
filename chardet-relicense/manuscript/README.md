# chardet-relicense/manuscript/

Source for the manuscript *"Paraphrase-Resistant Detection of AI-Driven
Code Rewrites: A Falsifiable Harness Applied to the chardet v6 to v7
Relicensing Dispute"*.

## Contents

| File | Purpose |
|---|---|
| `main.tex` | The manuscript. |
| `references.bib` | BibTeX entries, every one confirmed by web search at writing time. |
| `Makefile` | Build target: three `pdflatex` passes + one `bibtex`. |
| `figures/fig1_implementation_dag.pdf` | The six-unit DAG, layered. |
| `figures/fig2_topology_features.pdf` | C06a call-graph topology feature comparison. |
| `figures/fig3_control_flow_hist.pdf` | C06c normalised AST control-flow histogram. |
| `figures/scripts/gen_figures.py` | Regenerates the figures from `extract_signals.py` directly. |
| `figures/scripts/gen_figures.sh` | Wrapper that materialises the worktrees and invokes `gen_figures.py`. |
| `README.md` | This file. |

## Build

You need a TeX Live install with `pdflatex` and `bibtex`, and you need
matplotlib if you want to regenerate the figures (the figures are
checked in, so you do not strictly need matplotlib just to build the
PDF):

```bash
# Stock TeX Live on most distros. On openSUSE this would be e.g.
#   sudo zypper install texlive-latex texlive-latex-recommended \
#                       texlive-bibtex texlive-collection-fontsrecommended
# On Debian/Ubuntu:
#   sudo apt install texlive texlive-latex-extra texlive-bibtex-extra
# On Fedora:
#   sudo dnf install texlive-scheme-medium

cd chardet-relicense/manuscript/
make
# -> main.pdf
```

The `Makefile` uses only `pdflatex` and `bibtex` and only the standard
packages `graphicx`, `booktabs`, `xcolor`, `listings`, `enumitem`,
`hyperref`, `cleveref`, `microtype`, `lmodern`, and `geometry`. Every
one of these is in `texlive-latex-recommended` or
`texlive-latex-extra`. There is no `acmart`, `IEEEtran`, or `arxiv.sty`
dependency.

## Regenerate the figures

The figures are produced from the same AST analysers the proof bundle
uses, so the data in the figures is identical to the data in the
paper's tables.

Prerequisite: the upstream `chardet` clone with tags `6.0.0` and
`7.0.0` checked out (the same prerequisite as the proof bundle's
`detect.sh`):

```bash
git clone https://github.com/chardet/chardet.git \
    /srv/repos/public/spec-poc/chardet-relicense/chardet
# (or set CHARDET_REPO=/path/to/your/clone before running gen_figures.sh)

python3 -m pip install matplotlib networkx

make figures
```

`gen_figures.sh` materialises both tags via `git worktree add` into a
temporary directory, imports `chardet-relicense/proof-bundle/extract_signals.py`
to re-derive the topology and histogram values, and writes
`figures/fig*.pdf`. Two consecutive runs produce byte-identical output.

## Reproduce the numbers in the paper

Every number in the paper is taken verbatim from a single run of
`bash chardet-relicense/proof-bundle/detect.sh` on the
`verivus-oss/agent-assurance` repository at HEAD `220cff4`, against a
checkout of `https://github.com/chardet/chardet` with tags `6.0.0` and
`7.0.0` present. To re-derive:

```bash
git clone https://github.com/verivus-oss/agent-assurance.git
git clone https://github.com/chardet/chardet.git \
    /srv/repos/public/spec-poc/chardet-relicense/chardet

cd agent-assurance/
python3 -m pip install -r requirements.txt

bash chardet-relicense/proof-bundle/detect.sh
```

Expected output (modulo the `Preparing worktree` informational lines
git emits and the `repo: / v6 tag: / v7 tag:` precheck preamble):

```
signal  contract  expected  actual                                    verdict   evidence
literal_source_carryover  AUX1    0 matching pairs            0 matches across 87 v6 / 33 v7 files  PASS  ...
call_graph_topology       C06a    report topology-feature similarity in [0,1] ...  similarity=0.881 v6_nodes=342 v7_nodes=358 v6_edges=488 v7_edges=659  MEASURED  ...
import_edge_set           C06b    report Jaccard overlap of third-party ...  jaccard=0.333 shared=2 v6_only=1 v7_only=3  MEASURED  ...
control_flow_histogram    C06c    report cosine similarity of normalised AST control-flow histograms  cosine=0.984 v6_total=652 v7_total=848  MEASURED  ...
public_api_signature_equivalence  C06d  report strict / renamed_args / diverged counts across shared __all__ symbols  shared=5 strict=3 renamed_args=0 diverged=2  MEASURED  ...
behavioural_fingerprint   C06e    report exact-match rate AND (encoding, confidence-bucket) match rate over N_INPUTS deterministic fuzz inputs  exact_match_rate=0.000 bucket_match_rate=0.000 n_inputs=1000 corpus_digest=58e54831f84183c7  MEASURED  ...

# SUMMARY
# MEASURED: 5
# PASS: 1
```

If your numbers differ on AUX1, C06a, C06b, C06c, or C06d, you are
either running against different chardet tags or against a different
version of `extract_signals.py`. The static signals are deterministic
functions of the source bytes.

C06e is deterministic given the fixed random seed (`20260522`) and the
installed chardet versions, but a runner where `pip install` from the
local worktrees fails will emit `SKIP` with the literal failure reason
rather than `MEASURED`. The most common reason this happens in
sandboxed environments is that `pip install <worktree-path>` is NOT
fully offline: while the chardet *library* code is taken from the
worktree, the *PEP 517 build backend* (`setuptools`, `wheel`) is
still resolved through `pip`, which by default fetches it from PyPI
when it is not present in the runner's `~/.cache/pip`. A sandbox that
blocks outbound PyPI traffic will see the install fail with an error
like `Failed to build [worktree] when installing build dependencies`
and C06e will degrade to `SKIP`. This is the documented behaviour, not
a regression. To run C06e fully offline:

* Prepopulate `~/.cache/pip` with `setuptools` and `wheel` before
  invoking the harness, or
* Set `PIP_INDEX_URL` to a local mirror that carries them, or
* Skip C06e on this runner and re-run on one with PyPI access.

Missing native build tools (a working `cc`, the Python development
headers) can also cause SKIP; the failure reason in the SKIP message
will distinguish the two cases. The paper's reported C06e values are
from a runner where both venvs installed successfully.

## What to expect on first run

* The worktree preparation step writes two temporary directories
  under `$TMPDIR`. They are removed on harness exit.
* The behavioural-fingerprint step creates two virtual environments
  (~30 MB each) and `pip install`s the worktrees. This takes 30--90
  seconds on a typical workstation.
* The total runtime is around 60--120 seconds.

## Author and review

The paper is authored by Verivus OSS. The manuscript was drafted by
Claude Opus 4.7 (Anthropic) through the Claude Code agent harness;
the proof bundle was authored by the same agent and reviewed
independently by Codex, Gemini, and Grok using
`chardet-relicense/proof-bundle/verification_report.toml` as the
verification rubric. See section 10 of the manuscript for the review
process.

## Licence

The paper, the figures, and the build scripts are released under
Apache-2.0, the same licence the surrounding repository uses.
