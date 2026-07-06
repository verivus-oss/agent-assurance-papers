# Future studies: the four-scenario "escape the triviality trap" arc

The `hello-world` proof governs an instant, deterministic, stdout-only contract.
To show the DAG-TOML assurance framework is a real software-engineering tool and
not a party trick, each follow-up escalates the baseline contract from a static
string into a dynamic, environment-interacting behaviour that breaks a standard
verification assumption. Four scenarios make up the arc; **#1 is complete**
(this directory's `DESIGN.md`, `proof-bundle/`, `manuscript/`, and container),
#2–#4 are recorded here as future studies.

| # | Scenario | Breaks | Status |
|---|----------|--------|--------|
| 1 | Stateful I/O — HTTP echo server | run-to-completion ⇒ process lifecycle | **Complete** — bundle built and green (7 PASS / 1 SKIP / 0 FAIL + 6 witnesses + 5 validators), manuscript written, container reproduction green; cross-model gate satisfied across rounds (`DESIGN.md` §12) |
| 2 | Non-determinism — concurrent sort | deterministic stdout ⇒ races + filesystem state | Future study |
| 3 | Dependency graph — third-party ecosystems | stdlib-only ⇒ hermetic external deps | Future study |
| 4 | Semantic verification — Semgrep/CodeQL | bespoke AST scripts ⇒ enterprise SAST hand-off | Future study |

---

## #1 — The Stateful I/O Test: an HTTP echo server (COMPLETE)

**Contract.** Bind `127.0.0.1:8080`, accept `POST /` with a JSON body, return
`200 OK` echoing the exact bytes, and on `SIGTERM` stop accepting, finish
in-flight, release the port, exit `0`.

**Why it breaks the trap.** "Hello, world!" runs to completion and diffs stdout.
A server must be daemonized, polled for readiness, driven over the network,
signalled, and reaped — forcing PID capture, readiness/shutdown deadlines (the
**MEASURED** result word), port-as-singleton-resource serialization, and a
graceful-vs-`SIGKILL` negative control. Fully designed in `DESIGN.md`.

---

## #2 — The Non-Determinism Test: concurrent sorting (FUTURE STUDY)

**Contract.** Ingest an array of 100,000 integers, spawn ≥2 concurrent
threads/goroutines to sort it, and write the sorted array to a **file**.

**Why it breaks the trap.** Verification hates non-determinism. Forcing
concurrent execution means the traceability chain must prove the proof does not
fail *randomly* under race conditions in the test runner. Checking a **file**
output (not stdout) forces the framework to manage filesystem state,
permissions, and cleanup across languages.

**What it would stress in the framework (open design questions):**
- A determinism discipline: the *output* (sorted array) is deterministic even
  though the *execution* (thread interleaving) is not — the witness must assert
  the invariant (sorted + permutation-of-input), not a fixed trace.
- A new MEASURED axis (wall-time / thread count) without promoting it to PASS.
- A flake-control protocol: repeat-N runs, and a negative control that proves a
  genuinely racy implementation (e.g. unsynchronized shared-array write) is
  *caught* as FAIL — the concurrency analog of the graceful-vs-kill control.
- Filesystem-as-shared-resource discipline (temp dirs, cleanup traps), echoing
  the §2 "port is a singleton" lesson from #1.

**Artifacts needed to make it assessable:** per-language concurrent sorters, a
race negative-control variant, a witness that checks the file invariant + repeat
runs, and the five DAG-TOML files.

---

## #3 — The Dependency Graph Test: third-party ecosystems (FUTURE STUDY)

**Contract.** Parse an ISO-8601 timestamp, add exactly 30 days, output the new
timestamp — **using an external library** (not stdlib).

**Why it breaks the trap.** `hello-world` and #1 are deliberately stdlib-only /
hermetic. Real repositories are webs of npm / Cargo / Maven / Go-module
dependencies. This proves the DAG-TOML build graph can **hermetically pull,
compile, and trace** contracts *through* external packages without breaking
reproducibility of the executable proof.

**What it would stress in the framework (open design questions):**
- Provenance through a dependency: the traceability chain must extend across a
  package boundary (lockfile + pinned version + integrity hash as first-class
  `CODE`/provenance nodes), not just first-party source.
- Hermeticity vs. network: vendoring / offline caches / lockfile pinning so the
  proof is reproducible without a live registry; SKIP semantics when the cache
  is absent.
- This is the natural place to relax #1's deliberate "no crates / no external
  deps" constraint (cf. `DESIGN.md` §3 Rust note, §11.3).
- Direct tie-in to the existing **CDA** work (see repo memory): dependency
  provenance, licensing of pulled inputs, and supply-chain edges.

**Artifacts needed:** per-language date programs each using a real third-party
lib, the lockfiles/manifests, a hermetic fetch+build step, and DAG-TOML that
traces the external-dep provenance.

---

## #4 — The Semantic Verification Test: Semgrep / CodeQL integration (FUTURE STUDY)

**Contract.** Implement a small SQL query builder whose **source structurally
prevents SQL injection** (e.g. the AST bans raw string concatenation into
queries; parameterization is enforced).

**Why it breaks the trap.** In `hello-world` the author fell back to brittle
bespoke scripts (the AWK fallback) when the primary AST parser (`sqry`) fell
short. A robust follow-up integrates **industry-standard SAST** (Semgrep /
GitHub CodeQL) into the review gate, proving the DAG-TOML traceability chain can
**hand verification off to enterprise-grade, multi-language analyzers** instead
of relying on unmaintainable one-off scripts.

**What it would stress in the framework (open design questions):**
- A real bridge from the static layer to an external analyzer: the review-gate
  must consume Semgrep/CodeQL findings as evidence (SARIF → evidence_matrix),
  closing the `DESIGN.md` §8 "validators check structure, not semantics" gap.
- A *semantic* negative control: an injection-prone builder variant that the
  SAST rule must flag, proving the rule is not vacuous (the SAST analog of the
  graceful-vs-kill and race controls).
- Cross-language rule portability: one structural property, N languages, one
  analyzer — the static-analysis analog of #1's "same lifecycle, N runtimes."
- Toolchain reality on the runner: Semgrep/CodeQL availability ⇒ SKIP-with-
  rationale when absent (`semgrep` is currently **missing**, per `DESIGN.md` §3).

**Artifacts needed:** per-language query builders (safe + injection-prone
control), the Semgrep/CodeQL ruleset, a gate step that ingests SARIF, and
DAG-TOML wiring the analyzer output into `review_readiness` / `evidence_matrix`.

---

### Cross-cutting note

Each scenario adds exactly one new stressor while reusing the proven DAG-TOML
machinery (contract declaration → implementation DAG → traceability →
review-readiness gate → evidence matrix → executable witnesses) and the
PASS/SKIP/FAIL/MEASURED result vocabulary. The recurring design move is a
**non-vacuous negative control** — a deliberately broken variant the gate must
catch (dropped-in-flight server #1, data race #2, missing-provenance dep #3,
injection-prone builder #4) — so each proof demonstrates discrimination, not
just a green checkmark.
