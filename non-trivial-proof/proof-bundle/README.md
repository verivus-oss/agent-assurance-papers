# The Stateful I/O Proof — a multi-language HTTP echo service

This bundle is the follow-up to [`hello-world/`](../../hello-world/proof-bundle/).
hello-world governed an **instant, deterministic, stdout-only** contract. This
proof points the *same* DAG-TOML machinery (contract declaration → implementation
DAG → traceability → review-readiness gate → evidence matrix → executable
witnesses) at a contract that cannot be checked by running a program to
completion and diffing stdout: the program must **bind a port, stay alive, answer
over the network, and die gracefully on a signal**.

The design rationale lives in [`../DESIGN.md`](../DESIGN.md); this README is the
worked walkthrough plus the **Observed Execution** captured on this runner.

## The contract (C01 is load-bearing)

> **C01.** When started, each server MUST bind `127.0.0.1:8080`, accept an HTTP
> `POST /` carrying a body, and return `200 OK` whose body is the **exact byte
> sequence** of the request body. On `SIGTERM` it MUST stop accepting, finish any
> in-flight request, release the port, and exit `0`.

C02–C06 narrow separable obligations so the gate can tell "the toolchain isn't
here" (SKIP) from "the server bound but never answered" (FAIL) from "the server
answered but had to be SIGKILLed" (FAIL):

| ID  | Domain            | Obligation | Result words |
|-----|-------------------|------------|--------------|
| C01 | service_lifecycle | Full lifecycle (load-bearing) | PASS / SKIP / FAIL |
| C02 | readiness         | Connectable within 5000 ms | PASS/FAIL + MEASURED |
| C03 | echo_fidelity     | status 200, body `cmp`-equal, correct Content-Length | PASS / FAIL |
| C04 | signal_handling   | In-flight completes, exit 0 within 3000 ms, port re-bindable | PASS/FAIL + MEASURED |
| C05 | statefulness      | One process answers ≥2 sequential requests | PASS / FAIL |
| C06 | signal_boundary   | AWK: no clean SIGTERM handler ⇒ declared SKIP | SKIP (declared) |

## Eight languages, six runtimes, one boundary

The headline number is **eight languages**. "Six runtimes" is a defined gloss
(see DESIGN.md §2): TypeScript folds into the V8/Node runtime, AWK is the C06
boundary (not a passing runtime), leaving six distinct execution stacks —
Go, V8/Node (JS + TS), CPython, the JVM, natively-compiled C, natively-compiled
Rust.

| Lang | Build/run | Lifecycle support |
|------|-----------|-------------------|
| Go | `go build`; `net/http` + `signal.Notify` + `Server.Shutdown` | first-class |
| Node | `node server.js`; `http` + `process.on('SIGTERM')` + `server.close` | first-class |
| TypeScript | `node --experimental-strip-types server.ts` (no `tsc` here) | via Node |
| Python | `python3 server.py`; `http.server` + `signal` | first-class |
| C | `cc -O2`; raw sockets + `sigaction` + `setsockopt(SO_REUSEADDR)` | manual, clean |
| Rust | `rustc -O` stdlib only + `extern "C"` FFI (signal + socket/setsockopt/bind/listen), no crates | manual via FFI |
| Java | `java Server.java` source-launch; `com.sun.net.httpserver` (`jdk.httpserver` module) | JDK-module |
| AWK | gawk `/inet/tcp/8080/0/0` echo loop | **no clean SIGTERM** — C06 boundary |

**Java runs first.** Verified by a pre-build spike (DESIGN.md §3), `com.sun`
`HttpServer` sets no `SO_REUSEADDR` and exposes no API to set it, so it cannot
bind over a `TIME_WAIT` left by a prior server. The witness therefore runs Java
first on a pristine port; the other six set `SO_REUSEADDR` and tolerate a prior
`TIME_WAIT`.

## Bundle layout

```
proof-bundle/
  payload.json                  fixed 56-byte deterministic echo payload
  src/{go,node,typescript,python,c,rust,java,awk}/   the eight echo servers
  src/controls/                 control_ignore.go, control_drop.go (negative controls)
  run_service_contract.sh       load-bearing witness: C01..C05, serialized, Java first
  detect_graceful_shutdown.sh   C04 negative control: catches both non-graceful servers
  detect_awk_boundary.sh        C06 boundary witness
  *.toml                        the five DAG-TOML files
```

## How to run

```bash
cd non-trivial-proof/proof-bundle
./run_service_contract.sh        # C01..C05 across all servers (exits non-zero on any FAIL)
./detect_graceful_shutdown.sh    # C04 negative control
./detect_awk_boundary.sh         # C06 boundary
# PROOF_PORT=18080 ./run_service_contract.sh   # override the port for CI
```

## Observed Execution (this runner, 2026-05-31)

Toolchain: `go` 1.26.3, `node` v24.15.0, `python3` 3.13.13, `cc` (gcc) 15.2.0,
`rustc` 1.90.0, `java` 25.0.3 (runtime; no `javac`), `gawk` 5.3.2. Port 8080 free.

**`run_service_contract.sh` → PASS=7, SKIP=1, FAIL=0:**

| Lang | Result | time-to-ready | time-to-shutdown | bytes |
|------|--------|--------------:|-----------------:|------:|
| java   | **PASS** | 468 ms | 26 ms † | 56 |
| go     | **PASS** | 25 ms | 1111 ms | 56 |
| node   | **PASS** | 24 ms | 1024 ms | 56 |
| ts     | **PASS** | 69 ms | 1024 ms | 56 |
| python | **PASS** | 46 ms | 1023 ms | 56 |
| c      | **PASS** | 3 ms | 1002 ms | 56 |
| rust   | **PASS** | 2 ms | 1002 ms | 56 |
| awk    | **SKIP** | — | — | C06 boundary; echo UNASSESSABLE |

The `time-to-ready` and `time-to-shutdown` columns are **MEASURED** numbers, not
PASS/FAIL: a measurement is never promoted to a PASS (the deadline is the
separate PASS/FAIL contract). The ~1000 ms shutdown for six runtimes is the
injected 1000 ms in-flight delay being honoured — the server finishes the
delayed request before exiting.

† **Java 26 ms:** `server.stop(2)` interrupts the handler's `Thread.sleep(1000)`,
so Java writes the full body immediately rather than waiting out the artificial
delay. The in-flight response still arrives **complete and byte-exact** and the
exit is **0**, so C04 holds; Java simply shuts down faster. This is honest
graceful completion, not a dropped request — contrast the drop-in-flight control
below.

**`detect_graceful_shutdown.sh` → OK (the C04 check is non-vacuous):**

| Control | Behaviour | Gate verdict |
|---------|-----------|--------------|
| A — ignores SIGTERM | never exits | **CAUGHT**: SIGKILL needed ⇒ C04 FAIL |
| B — drops in-flight | exit 0 but truncated body (0/56 bytes) | **CAUGHT**: clean exit ≠ graceful ⇒ C04 FAIL |

PASS here means the gate discriminates graceful from non-graceful on **both** the
exit-code axis and the in-flight-completion axis — a clean exit code alone is not
accepted as graceful.

**`detect_awk_boundary.sh` → OK:** the gawk `/inet` listener comes up; its echo is
**UNASSESSABLE** (0/56 bytes on this run — byte-exact Content-Length framing over
`/inet` is materially harder than a one-liner, as designed); SIGTERM yields exit
status **143** (128+15), confirming gawk has **no clean script-level SIGTERM
handler**. AWK C04 is therefore a declared **SKIP-with-rationale** — the firm C06
claim.

## How to validate the DAG-TOML

Path existence is **opt-in** in the validators, so every invocation passes
`--check-paths-exist --repo-root` (DESIGN.md §7/§10):

```bash
cd ..   # repo root: agent-assurance-papers
V=../agent-assurance/validators ; B=non-trivial-proof/proof-bundle
python3 $V/validate_implementation_dag.py $B/implementation_dag.toml --repo-root . --check-paths-exist
python3 $V/validate_traceability.py       $B/traceability.toml       --repo-root . --check-paths-exist
python3 $V/validate_review_readiness.py   $B/contract_declaration.toml --repo-root . --check-paths-exist
python3 $V/validate_review_readiness.py   $B/review_readiness.toml    --repo-root . --check-paths-exist
python3 $V/validate_review_readiness.py   $B/evidence_matrix.toml     --repo-root . --check-paths-exist
```

All five **PASS** on this runner. `implementation_dag.toml` reports 10 units,
layers `{0: 9, 1: 1}`, and node-weighted `critical_path_loc: 327` (U05 rust →
U08).

## What the static validators do NOT check (and non-claims)

The five validators check **structure**, not **runtime**: they confirm C01 is
declared, wired to a TEST, and that the witness scripts exist — they cannot
confirm a server ever bound, echoed, or shut down. Every dynamic guarantee lives
only in the shell witnesses above, surfaced into the Observed Execution table.
This is not a benchmark, not RFC-conformant HTTP, POSIX-signals only, and 8080 is
a runner-global assumption (a hostile environment racing for the port yields a
legitimate SKIP). The AWK echo is not asserted. See DESIGN.md §8–§9 for the full
list.
