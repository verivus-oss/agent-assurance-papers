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

**No privileged run position (Measured Runtime Correction, DESIGN.md §3.1).**
The retired design ran Java *first* on a pristine port on the claim that `com.sun`
`HttpServer` "cannot set `SO_REUSEADDR` / cannot re-bind a `TIME_WAIT`'d port."
Direct re-measurement (MEASUREMENTS.md M1; the committed `ReuseSpike.java`, re-run
6/6) **overturned that**: a `start()`ed `HttpServer` (NIO `ServerSocketChannel`,
`SO_REUSEADDR` on by default) tolerates a prior `TIME_WAIT` and releases its port
immediately on `stop(0)`. The witness therefore runs **all seven PASS-candidates
in plain build order, with no privileged position**. Port release between
languages is guaranteed uniformly by an independent re-bind probe that itself sets
`SO_REUSEADDR` plus a bounded TIME_WAIT retry. The true, deterministic footgun — a
*never-`start()`ed* `stop()` leaking the listener — is kept falsifiable by the
re-pointed reproducer (`detect_java_reuseaddr.sh` + `src/spikes/ReuseSpike.java`)
and does not affect the proof.

## Bundle layout

```
proof-bundle/
  payload.json                  fixed 56-byte deterministic echo payload
  src/{go,node,typescript,python,c,rust,java,awk}/   the eight echo servers
  src/controls/                 control_ignore.go, control_drop.go (C04 negative controls),
                                broken_echo.py (differential calibration control)
  src/spikes/ReuseSpike.java    re-pointed Java reproducer (corrected finding, §3.1)
  run_service_contract.sh       load-bearing witness: C01..C05, serialized, plain build order
  detect_graceful_shutdown.sh   C04 negative control: catches both non-graceful servers
  detect_awk_boundary.sh        C06 boundary witness
  differential_echo.py          cross-implementation behavioural-equivalence witness (E06)
  detect_inflight_window.py     C04 in-flight timing guard (E07, §5.6)
  detect_java_reuseaddr.sh      re-pointed Java reproducer witness (§3.1)
  *.toml                        the five DAG-TOML files
```

## How to run

```bash
cd non-trivial-proof/proof-bundle
./run_service_contract.sh        # C01..C05 across all servers (exits non-zero on any FAIL)
./detect_graceful_shutdown.sh    # C04 negative control
./detect_awk_boundary.sh         # C06 boundary
python3 differential_echo.py     # cross-implementation behavioural equivalence (E06)
python3 detect_inflight_window.py # C04 in-flight timing guard (E07, §5.6)
./detect_java_reuseaddr.sh       # re-pointed Java reproducer (corrected finding, §3.1)
# PROOF_PORT=18080 ./run_service_contract.sh   # override the port for CI
```

## Observed Execution (this runner, 2026-06-01)

Toolchain: `go` 1.26.3, `node` v24.15.0, `python3` 3.13.13, `cc` (gcc) 15.2.0,
`rustc` 1.90.0, `java` 25.0.3 (runtime; no `javac`), `gawk` 5.3.2. Port 8080 free.

**`run_service_contract.sh` → PASS=7, SKIP=1, FAIL=0** (plain build order, no
privileged position):

| Lang | Result | time-to-ready | time-to-shutdown | bytes |
|------|--------|--------------:|-----------------:|------:|
| go     | **PASS** | 3 ms | 1089 ms | 56 |
| node   | **PASS** | 26 ms | 1026 ms | 56 |
| ts     | **PASS** | 69 ms | 1025 ms | 56 |
| python | **PASS** | 48 ms | 1024 ms | 56 |
| c      | **PASS** | 2 ms | 1001 ms | 56 |
| rust   | **PASS** | 3 ms | 1001 ms | 56 |
| java   | **PASS** | 474 ms | 1024 ms † | 56 |
| awk    | **SKIP** | — | — | C06 boundary; echo UNASSESSABLE |

The `time-to-ready` and `time-to-shutdown` columns are **MEASURED** numbers, not
PASS/FAIL: a measurement is never promoted to a PASS (the deadline is the
separate PASS/FAIL contract). The ~1000 ms shutdown across **all seven** runtimes
is the injected 1000 ms in-flight delay being honoured — the server completes the
delayed request before exiting.

† **Java (measured correction):** an earlier run reported Java at **27 ms** and
explained it as `server.stop(2)` interrupting the sleep. A referee-driven
measurement overturned that: `com.sun` `HttpServer` buffers its response headers
until body bytes flow, so the witness's header-flush sync point silently failed
for Java and SIGTERM landed on an **already-complete** request — the in-flight
window was never exercised, and the sleep actually completed normally. The Java
handler now flushes a sync byte before the delay (forcing headers onto the wire),
so the remainder is genuinely in flight and Java honours the delay like the other
six. The new `detect_inflight_window.py` guard asserts this for every
PASS-candidate (DESIGN.md §5.6).

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

**`differential_echo.py` → 0 divergences / control caught 6/10 (non-vacuous):**
the seven PASS-candidate servers each return status `200` with body byte-equal to
the request for **all 10** adversarial inputs (NUL/full-byte-range data, 1 MiB
bodies, embedded fake-HTTP, UTF-8, etc.) — **zero divergences**. The committed
broken calibration control (`src/controls/broken_echo.py`, truncates to 16 B) is
flagged on **6/10** requests (every body > 16 B), proving the equivalence test is
**non-vacuous**. This upgrades the single-payload contract to a calibrated
cross-implementation byte-exact-equivalence result (DESIGN.md §5.4,
`../DIFFERENTIAL-AGREEMENT.md`).

**`detect_inflight_window.py` → OK (C04 in-flight window genuine for all 7):**
a referee-driven timing guard. For each PASS-candidate it records the SIGTERM
timestamp against the client-side body-**completion** timestamp and requires
completion **strictly after SIGTERM** by ≥ 500 ms — proving the in-flight window
is genuinely exercised, not collapsed by response-header buffering. All seven
complete ~1000 ms after SIGTERM (incl. Java, via the header-flush fix); a server
whose window collapsed would finish in ~0 ms and FAIL. The contrast is measured:
Go's body arrives ~1001 ms after SIGTERM, Java *pre-fix* arrived 0 ms (already
sent). DESIGN.md §5.6.

**`detect_java_reuseaddr.sh` → OK (corrected finding CONFIRMED):** the re-pointed
spike confirms the **measured** facts (DESIGN.md §3.1): `[A]` a `start()`ed
`HttpServer` binds over a live `TIME_WAIT` and releases its port immediately on
`stop(0)`; `[B]` a *never-`start()`ed* `stop()` leaks its listener (the real
footgun). The retired design's false "HttpServer cannot re-bind a TIME_WAIT'd
port" claim is thereby retracted and kept falsifiable on the record.

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

All five **PASS** on this runner. `implementation_dag.toml` reports 12 units,
layers `{0: 11, 1: 1}`, and node-weighted `critical_path_loc: 327` (U05 rust →
U08); `traceability.toml` reports 43 entities (the five chains).

## What the static validators do NOT check (and non-claims)

The five validators check **structure**, not **runtime**: they confirm C01 is
declared, wired to a TEST, and that the witness scripts exist — they cannot
confirm a server ever bound, echoed, or shut down. Every dynamic guarantee lives
only in the shell witnesses above, surfaced into the Observed Execution table.
This is not a benchmark, not RFC-conformant HTTP, POSIX-signals only, and 8080 is
a runner-global assumption (a hostile environment racing for the port yields a
legitimate SKIP). The AWK echo is not asserted. See DESIGN.md §8–§9 for the full
list.
