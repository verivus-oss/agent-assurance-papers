# Stateful I/O Proof Paper

A standalone paper package for the `non-trivial-proof/proof-bundle`
proof (the stateful HTTP echo-service follow-up to the `hello-world`
stdout proof).

## Files

- `main.tex` — paper source.
- `references.bib` — BibTeX references used by the paper.
- `README.md` — build, verification, and packaging notes.

## Build

From this directory:

```sh
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

If TeX is unavailable (as on the authoring runner), syntax-check the
source enough to confirm that every citation key in `main.tex` exists in
`references.bib` and that every `\path{...}` file reference resolves
relative to the repository root. Both checks pass for this package
(11 cite keys resolve; all referenced bundle files exist; LaTeX
environments balance).

**Containerized build (recommended).** `../build-and-run.sh` builds the
podman image (`../Containerfile`) and reproduces the whole proof *and*
compiles this paper inside it, dropping the freshly-built `main.pdf` into
this directory. **`main.pdf` is not committed** — it is a build product of
this reproduction (the previously committed PDF predated this rewrite and
was removed rather than left stale). Run the container to regenerate it.
Pinning is partial and honestly so: the base image is digest-pinned and
go 1.26.3 / node 24.15.0 / rust 1.90.0 are sha256-pinned, but the
zypper-provided tools (gcc, gawk, python3, java-25-openjdk, TeX, networkx)
track live Tumbleweed repos and drift on rebuild. Versions observed in the
authoring build (snapshot, not a guarantee): JDK 25.0.3, python 3.13.13,
gcc 15.2.1 (host 15.2.0), gawk 5.4.0 (host 5.3.2). See the `Containerfile`
header for the full pinned-vs-unpinned breakdown.

## Verification commands

Run these from the repository root (`agent-assurance-papers`):

```sh
bash   non-trivial-proof/proof-bundle/run_service_contract.sh
bash   non-trivial-proof/proof-bundle/detect_graceful_shutdown.sh
bash   non-trivial-proof/proof-bundle/detect_awk_boundary.sh
python3 non-trivial-proof/proof-bundle/differential_echo.py
bash   non-trivial-proof/proof-bundle/detect_java_reuseaddr.sh

V=../agent-assurance/validators ; B=non-trivial-proof/proof-bundle
python3 $V/validate_implementation_dag.py  $B/implementation_dag.toml   --repo-root . --check-paths-exist
python3 $V/validate_traceability.py        $B/traceability.toml         --repo-root . --check-paths-exist
python3 $V/validate_review_readiness.py    $B/contract_declaration.toml --repo-root . --check-paths-exist
python3 $V/validate_review_readiness.py    $B/review_readiness.toml     --repo-root . --check-paths-exist
python3 $V/validate_review_readiness.py    $B/evidence_matrix.toml      --repo-root . --check-paths-exist
```

The path-existence flags are mandatory: path checking is opt-in in the
validators, so a bare invocation would not enforce that the witness
scripts and source files actually exist on disk.

## Observed outcome on the authoring runner (2026-06-01)

`run_service_contract.sh` reported 7 PASS / 1 SKIP (AWK, the C06
boundary) / 0 FAIL; `detect_graceful_shutdown.sh` caught both
non-graceful controls; `detect_awk_boundary.sh` confirmed the C06
boundary (SIGTERM yields exit 143); `differential_echo.py` found 0
divergences among the seven servers and caught the broken calibration
control on 6 of 10 inputs (non-vacuous); `detect_java_reuseaddr.sh`
confirmed the corrected Java finding (started `HttpServer` tolerates
`TIME_WAIT` and releases; never-started `stop()` leaks the listener). All
five DAG-TOML files validate with path checks enabled. The MEASURED
timings in the paper are one representative run and vary slightly between
runs by design.

## arXiv packaging

A source package should include only `main.tex`, `references.bib`, and a
precomputed `main.bbl`; logs, `aux`, and unrelated repository files
should be excluded. The bundle code can be linked from the paper or
attached as ancillary material.
