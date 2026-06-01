# Design: The Stateful I/O Proof — a Multi-Language HTTP Echo Server

**Status:** DESIGN (measure-first rebuild). This document is the normative design
record for a from-scratch rebuild of the stateful-I/O proof. The previous set was
retired because it asserted a **false** Java `SO_REUSEADDR` finding (flipped twice,
resting on an un-rerun spike) and carried a §12 review record with documented
fabrications. The old set is recoverable at git branch
`pre-rewrite-nontrivial-2026-06-01`.
**Discipline:** *measure-first*. Nothing here asserts a runtime fact that is not
recorded in `MEASUREMENTS.md` (Phase-0 ground truth) or established by the Phase-2
witness run. Every green result is paired with a calibration control that proves
the test can fail. The cross-model gate (§12) records only reviewer output
retrieved by job ID.
**Working dir:** `non-trivial-proof/` (this `DESIGN.md`, `MEASUREMENTS.md`,
`DIFFERENTIAL-AGREEMENT.md`, `proof-bundle/`, `manuscript/`, the container files).
**Companion to:** `hello-world/` (the trivial proof this follow-up answers).
**Author target:** Werner Kasselman / Verivus OSS.
**Date:** 2026-06-01.

> **Provenance note.** Every engineering decision below is the author's own.
> §12 records only genuine cross-model review output retrieved by job ID; it
> must never contain summarized, assumed, or fabricated reviewer content. This
> rebuild exists because two earlier drafts violated that rule and because a
> runtime fact was asserted without a reproducible measurement — see the
> **Measured Runtime Correction** (§3.1) and the §12 integrity note.

---

## 0. One-paragraph thesis

The hello-world proof governs an **instant, deterministic, stdout-only**
contract. A real assurance framework has to govern **long-lived, stateful,
network-facing** programs too. This follow-up keeps the exact same DAG-TOML
machinery (contract declaration → implementation DAG → traceability →
review-readiness gate → evidence matrix → executable witnesses) but points it at
a contract that *cannot* be checked by running a program to completion and
diffing stdout. The program must **bind a port, stay alive, answer over the
network, and die gracefully on a signal**. The contribution is showing that the
same inspectable, falsifiable proof structure survives the jump from a 14-byte
print to a process *lifecycle* — and naming precisely which parts of the
framework had to grow (a lifecycle-aware witness harness, the MEASURED result
word, a port-as-shared-resource discipline, and a cross-implementation
behavioural-equivalence channel) and which parts the static validators still
cannot see.

---

## 1. The contract (what the program must do)

> **C01 (load-bearing).** The program, when started, MUST bind a TCP listener on
> `127.0.0.1:8080`, accept an HTTP `POST /` carrying a request body, and return
> `200 OK` whose response body is the **exact byte sequence** of the request body
> (a faithful echo). On receipt of `SIGTERM` it MUST stop accepting connections,
> finish any in-flight request, release the port, and exit with code `0`.

That single sentence hides several separable obligations. As in hello-world (C01
load-bearing, C02–C04 narrowings, C05–C06 boundary witnesses), we decompose so
each obligation has its own witness and its own non-claim:

| ID  | Domain                  | Obligation (exact, testable)                                                                                   | Result words in play |
|-----|-------------------------|--------------------------------------------------------------------------------------------------------------|----------------------|
| C01 | `service_lifecycle`     | Full lifecycle: becomes ready → echoes byte-exact → exits 0 on SIGTERM → releases port. Load-bearing.        | PASS / SKIP / FAIL   |
| C02 | `readiness`             | Becomes connectable on `127.0.0.1:8080` within a **readiness deadline** (default 5000 ms).                    | PASS/FAIL + MEASURED time-to-ready |
| C03 | `echo_fidelity`         | Response status is exactly `200`; response body `cmp`-equal to the request body; `Content-Length` == body length. | PASS / FAIL |
| C04 | `signal_handling`       | After SIGTERM: any **in-flight request completes** (no dropped/truncated response), the process exits `0` within a **shutdown deadline** (default 3000 ms), and the port is **re-bindable** afterward — verified by an **independent re-bind probe that itself sets SO_REUSEADDR** plus a bounded retry absorbing TIME_WAIT. SIGKILL fallback, a dropped in-flight response, or a non-re-bindable port ⇒ FAIL. **Well-formedness rule:** the test-injected in-flight delay MUST be strictly less than the shutdown deadline (we use 1000 ms ≪ 3000 ms) so a *correct* graceful server can both finish the request and exit in time. | PASS/FAIL + MEASURED time-to-shutdown |
| C05 | `statefulness`          | A single long-lived process answers **≥2 sequential requests** (proves it is a daemon, not a one-shot exec). | PASS / FAIL          |
| C06 | `signal_boundary`       | Declared boundary: a runtime that can serve C01/C03 but cannot install a clean SIGTERM handler is recorded as a **SKIP-with-rationale**, not a PASS and not a FAIL. (This is AWK.) | SKIP (declared)      |

Why this decomposition matters: it lets the gate distinguish "the toolchain
isn't here" (SKIP) from "the server bound but never answered" (C02/C03 FAIL) from
"the server answered but had to be SIGKILLed" (C04 FAIL). hello-world could
collapse everything into one stdout `cmp`; a service cannot.

---

## 2. Why this "breaks the trap" — mapped to spec mechanics

Each bullet is a concrete capability the proof *forces* that hello-world never
exercised, with the spec hook it lands on.

1. **Process-lifecycle orchestration (not run-to-completion).**
   hello-world's `run_all.sh` ran each program to exit and diffed stdout. Here
   the verify unit must *background* the server, capture its PID, **poll for
   readiness** (the server is not ready the instant `fork` returns), drive it
   over the network, then **signal** it and capture the post-signal exit status.
   New harness primitives: PID capture, readiness polling with timeout, signal
   delivery, exit-after-signal capture, guaranteed teardown.

2. **Port 8080 is a global, mutable, singleton resource.**
   hello-world units were embarrassingly parallel (independent temp dirs). A
   bound port is shared mutable state on the runner. The DAG's layer-1 verify
   unit must **serialize** language runs (never two servers on 8080 at once),
   **fail fast / SKIP** if 8080 is already occupied, and **prove the port is
   released** between languages. This is the first proof where the
   implementation-DAG's "fan-in to one verifier" shape is *load-bearing for
   correctness*, not just tidy.

3. **Asynchronous timing ⇒ the MEASURED result word.**
   The four-word result vocabulary (PASS / SKIP / FAIL / **MEASURED**) is defined
   in the hello-world paper's "PASS, SKIP, FAIL, and MEASURED" section, not in a
   numbered `spec.md` clause — `spec.md` §10 is the IJB foundation and never
   mentions MEASURED. time-to-ready and time-to-shutdown are MEASURED numbers;
   "within the deadline" is a *separate* PASS/FAIL contract (C02, C04). The
   hello-world paper explicitly reported **no MEASURED values**. This proof is
   the first in this **stdout-to-lifecycle proof arc** to use the fourth result
   word for **timing**, and it honors that paper's rule that a measurement is not
   promoted to a PASS. **Scoped (per the chardet-relicensing bundle):** the
   claim is *not* "first MEASURED use in the papers repo" — that bundle already
   reports MEASURED *static-signal* values (similarity numbers,
   `chardet-relicense/proof-bundle/README.md`). What is new here is MEASURED used
   for *timed lifecycle* observations, not static magnitudes.

4. **Inter-process communication via signals (SIGTERM vs SIGKILL).**
   Graceful shutdown is only meaningful against a negative control. A server that
   *ignores* SIGTERM, or one killed with SIGKILL, must be **caught** by the gate.
   The proof includes a negative-control witness whose PASS means "the gate
   correctly identified a non-graceful server as FAIL" — the lifecycle analog of
   hello-world's `divergent_implementation_would_fail`.

5. **Same observable contract, radically different runtimes.**
   The cross-language claim moves up from "same stdout bytes" to "same
   *behavioral lifecycle*" across:
   - **event loop** (Node.js: `http` + `process.on('SIGTERM')` + `server.close`),
   - **green threads** (Go: `net/http` + `signal.Notify` + `http.Server.Shutdown`),
   - **OS threads / blocking accept** (Python: `http.server` + `signal`; C: raw
     BSD sockets + `sigaction`),
   - **FFI signal handling with no runtime help** (Rust: `std::net::TcpListener`
     + hand-declared `libc` `signal`/`setsockopt` via `extern "C"`, **no external
     crates**),
   - **JDK module** (Java: `com.sun.net.httpserver` from the bundled
     `jdk.httpserver` module, source-launched),
   - **interpreter with no signal API** (AWK/gawk `/inet`: the declared boundary).

   **Counting rule — the headline is "eight languages."** The firm, directly
   verifiable number is the one in the §3 table: **eight languages**. Everything
   else is a derived gloss. Of the eight, seven are PASS-candidates (Go,
   JavaScript/Node, TypeScript, Python, C, Rust, Java); AWK is the declared C06
   boundary and is **not** counted as a passing runtime. "Six runtimes" is then a
   *defined* sub-count, where **"runtime" means a distinct language execution
   stack**: TypeScript shares the V8/Node stack with JavaScript (so they collapse
   to one), leaving **six** — Go, V8/Node (JS + TS), CPython, the JVM, and C and
   Rust counted **separately**. We flag the soft edge honestly: C and Rust are
   both bare natively-compiled binaries over libc with no managed VM, so under a
   stricter "managed-runtime" definition one could collapse them into a single
   "native" bucket and reach five; we count them separately because they are
   distinct toolchains and execution stacks. The title therefore *leads with eight
   languages* and treats "six runtimes, one boundary" as the explained
   derivative, not the load-bearing claim.

6. **Cross-implementation behavioural equivalence under adversarial inputs.**
   The §10 contract witness checks each server against **one fixed payload**, so
   it cannot reveal where hand-rolled HTTP parsers (C, Rust) *diverge* on edge
   cases. A fourth witness (`differential_echo.py`, §5.4) runs all seven
   PASS-candidate servers on a shared **adversarial** corpus and demonstrates they
   are byte-exact-equivalent — with a deliberately-broken calibration control
   proving the equivalence test can fail. This is the methodology of the
   code-derivation-assay behavioural channel applied to *strengthen* the proof,
   and the natural multi-implementation generalisation of the single-payload
   witness (`DIFFERENTIAL-AGREEMENT.md`).

---

## 3. Language set (broad, per request) and runner reality

Toolchain confirmed on this runner (`MEASUREMENTS.md`, 2026-06-01): `go` 1.26.3,
`node` v24.15.0, `python3` 3.13.13, `cc` (gcc 15.2.0), `rustc` 1.90.0, `java`
25.0.3 (`25.0.3+9-suse`, **runtime only — no `javac`**), `gawk` 5.3.2 (with
`/inet`), plus `curl`/`jq`/`ss`/`lsof`/`nc`. **Missing:** `javac`, `tsc`,
`semgrep`. Port 8080 free; `tcp_fin_timeout = 60`.

| Lang        | Build/run path                                              | Lifecycle support | Verdict (intended) |
|-------------|------------------------------------------------------------|-------------------|--------------------|
| Go 1.26     | `go build`; `net/http`, `signal.Notify`, `Server.Shutdown` | first-class       | flagship PASS      |
| Node 24     | `node server.js`; `http`, `process.on('SIGTERM')`          | first-class       | PASS               |
| TypeScript  | `node --experimental-strip-types server.ts` (no `tsc` here)| via Node          | PASS (strip-types) |
| Python 3.13 | `python3 server.py`; `http.server`, `signal`               | first-class       | PASS               |
| C (gcc 15)  | `cc -O2`; sockets + `sigaction` + explicit `setsockopt(SO_REUSEADDR)` + minimal HTTP parse | manual, clean | PASS  |
| Rust 1.x    | `rustc -O` stdlib only + `extern "C"` FFI for `signal` **and** `socket`/`setsockopt`/`bind`/`listen` (std `TcpListener::bind` cannot set SO_REUSEADDR pre-bind), then `from_raw_fd` | manual via FFI | PASS (no crates) |
| Java 25     | `java Server.java` source-launch (JEP 330/477; `javac` absent); HTTP via the **bundled `jdk.httpserver` module** (`com.sun.net.httpserver`), auto-resolved in single-file mode — **not** `java.net` proper | JDK-module | PASS (source-launch) |
| AWK (gawk 5.3) | `gawk` `/inet/tcp/8080/0/0` echo loop                   | **no clean SIGTERM** | **C06 boundary SKIP**; echo itself UNASSESSABLE until built |

All "PASS" cells are **intended/predicted** outcomes; the real verdicts come only
from the §10 build-and-run step, not from this table.

Notes that change the design from a naive "just SKIP what's missing":
- **Java has no `javac` here but Java 25 runs `.java` directly** — so Java is a
  PASS-candidate, not a SKIP. The HTTP server is
  `com.sun.net.httpserver.HttpServer` from the **`jdk.httpserver` module**
  (shipped with the JDK, auto-resolved by single-file source launch); it is a
  bundled JDK module, *not* part of `java.net`. We name that dependency
  explicitly rather than implying bare stdlib. **Java carries no special
  port-ordering or pre-flight requirement** — see §3.1.
- **gawk can open a TCP listener** via `/inet` special files, so AWK is a
  plausible C01/C03 server — **but** byte-exact echo with correct `Content-Length`
  framing over `/inet` (record-separator driven, binary-safe) is materially
  harder than a one-line claim suggests; a naive `RS/ORS` echo returned no
  response (`MEASUREMENTS.md` M2). Therefore the AWK **echo (C01/C03) is
  `UNASSESSABLE — no artifact yet`** until a working gawk server is built and run;
  the *firm* declared claim is only the **C06 boundary SKIP** (gawk exposes no
  clean script-level POSIX SIGTERM handler; SIGTERM → exit 143). This mirrors
  hello-world's AWK-as-boundary, with the boundary at *runtime/signal* rather than
  *AST analysis*.
- **Rust stdlib has no signal API and `TcpListener::bind` does not set
  `SO_REUSEADDR`.** To stay hermetic (no crates — this is the stateful test, not
  the dependency test #3) Rust declares the needed `libc` symbols through a small
  `extern "C"` block: `signal`/`SIGTERM` (handler flips an `AtomicBool`) **and**
  `socket`/`setsockopt(SO_REUSEADDR)`/`bind`/`listen`, then wraps the fd with
  `TcpListener::from_raw_fd`. The whole `unsafe` surface is small and inspected
  inline.
- **SO_REUSEADDR is set by every PASS-candidate runtime, but it is *not*
  load-bearing for the C04 port-release check** — see §3.1 and §5.1 step 7. Go
  (`net.Listen`) and Node (`http.Server`) set it by default; C sets it via
  `setsockopt`; Rust via the FFI path above; Python's `http.server` sets
  `allow_reuse_address = True`; and Java's `HttpServer` rebinds over a `TIME_WAIT`
  in measurement (the likely mechanism is that its NIO `ServerSocketChannel` has
  `SO_REUSEADDR` enabled on this JDK build, but the JDK documents channel option
  defaults as implementation-specific, so that is an inference, not a contract).
  Port release is nevertheless verified **cross-process** by an independent probe (§5.1 step 7)
  that sets `SO_REUSEADDR` *itself* plus a bounded TIME_WAIT retry, so the proof
  never depends on any one server's socket-option choice.

### 3.1 Measured Runtime Correction — the retracted Java SO_REUSEADDR finding

**The previous set was wrong about Java, and direct measurement overturned it.**
The retired design claimed `com.sun.net.httpserver.HttpServer` "sets no
`SO_REUSEADDR` and cannot re-bind a `TIME_WAIT`'d port," and built a load-bearing
mitigation on top of it: Java was scheduled **first** on a pristine port, given a
special no-reuse bind pre-flight, and any foreign `TIME_WAIT` at Java's turn was a
SKIP. **None of that is needed, because the premise is false.** The committed
spike (`proof-bundle/src/spikes/ReuseSpike.java`), re-run 6/6 on this runner,
shows `HttpServer.create rebind: OK` over a live `TIME_WAIT` (`MEASUREMENTS.md`
M1). A properly-`start()`ed HttpServer **tolerates a prior `TIME_WAIT` and
releases its port immediately on `stop(0)`** — even after serving a connection.
The measured rebind is what carries the claim; the *mechanism* is an inference:
HttpServer likely binds via an NIO `ServerSocketChannel` whose `SO_REUSEADDR` is
enabled on this JDK build, but since the JDK documents channel option defaults as
implementation-specific (and a plain `ServerSocket`'s initial setting as
undefined), this is reported as an inference about the observed implementation,
not a contractual guarantee — a retraction of an over-confident causal Java claim
must not reintroduce one in the opposite direction.

**Root cause of the old false finding (deterministic, 6/6):**
`HttpServer.create()` binds the port; calling `stop()` on a server that was
**never `start()`ed does not release the listener socket**. The old spike's
`httpBind()` did exactly `create()` + `stop(0)` with no `start()`, so the leaked
listener — not any `SO_REUSEADDR` deficiency — is what made the subsequent bind
fail. The finding had been flipped twice and rested on that un-rerun spike; it was
never a property of the real lifecycle (which always `start()`s).

**Design consequences:**
- **No Java special-casing.** Drop Java-first run ordering and the no-reuse
  pre-flight probe entirely. Java behaves like the other runtimes in the real
  lifecycle; the serialized run order in §4 is plain build order, with no
  privileged position.
- **The C04 port-release check is uniform across all seven PASS-candidates**,
  including Java, precisely because the *probe* socket sets `SO_REUSEADDR` and
  bounded-retries TIME_WAIT (§5.1 step 7) — it does not depend on the server.
- **Keeper finding (true, deterministic, defensible).** A never-`start()`ed
  `HttpServer.stop()` leaks its bound listener. This is a real in-process API
  footgun, worth a corrected, **re-pointed reproducer**
  (`detect_java_reuseaddr.sh` + `ReuseSpike.java`, §5.5) and an honest "we
  mis-measured; the reproducer caught it" note. It does **not** affect the proof:
  (a) the real server calls `start()`, and (b) port release in the proof is
  **cross-process** — the server exits on SIGTERM and the OS reclaims the socket
  regardless of any in-process quirk.

This correction is the reason for the whole rebuild, and it is the design's
central honesty lesson: a runtime fact that drives load-bearing behaviour
(run-ordering, a SKIP path) must rest on a committed, re-runnable measurement —
not on narrative carried across drafts.

---

## 4. Implementation DAG (fan-in, lifecycle-aware)

```
U01 go-server     \
U02 node/ts-server \
U03 python-server   \
U04 c-server         > U08 verify-service-contract  (layer 1, critical leaf)
U05 rust-server     /     enforces C01..C05 per language, serialized on :8080
U06 java-server    /
U07 awk-server    /

U09 verify-graceful-vs-kill        (independent leaf: negative control for C04)
U10 verify-awk-boundary            (independent leaf: C06 SKIP-with-rationale witness)
U11 verify-differential-agreement  (independent leaf: cross-impl behavioural equivalence)
U12 verify-inflight-window         (independent leaf: C04 in-flight timing guard, §5.6)
```

- Layer 0: seven build/prepare units. Six are one-language units (Go, Python, C,
  Rust, Java, AWK); **`U02` is the single Node/V8 unit that prepares both the
  JavaScript and the TypeScript servers** (they share the runtime — see the §2
  counting rule). Compiled langs emit a binary `ART:`; interpreted/source-launched
  langs emit a runnable `ART:`. **Unit-vs-CODE count:** the traceability lifecycle
  chain (§7) has **eight `CODE:` entries** (one per language source file,
  including JS and TS as distinct files), even though there are only seven layer-0
  units — `U02` realizes two `CODE:` entries. The DAG-TOML keeps this mapping
  explicit so the validators see consistent counts.
- Layer 1: `U08` consumes every server `ART:`, runs the full lifecycle harness
  against each **one at a time** (port serialization), and produces
  `OUT:service-contract-witness`. **Run order is plain build order** (Go, Node,
  TS, Python, C, Rust, Java; AWK is the declared SKIP). There is **no privileged
  position** — the §3.1 correction removed the old Java-first constraint. Port
  release between languages is guaranteed by the §5.1-step-7 probe, uniformly.
- Independent leaves `U09`/`U10`/`U11`/`U12` are the behavioural sidecars (the
  analog of hello-world's source-analysis sidecars, extended with the differential
  channel and the C04 in-flight timing guard).
- **Validator-exactness note.** `validate_implementation_dag.py` recomputes the
  node-weighted longest path by `estimated_loc` (`longest_path_loc`) and checks
  `entry_points` == units with empty `depends_on`, `leaf_nodes` == units with
  empty `blocks`, and strictly-increasing `layer` along every `depends_on` edge.
  So **every** unit MUST carry an `estimated_loc`, and `critical_path` /
  `critical_path_loc` are declared explicitly (mirroring
  `hello-world/proof-bundle/implementation_dag.toml`) to match the computed
  values. `U09`/`U10`/`U11`/`U12` have empty `depends_on` **and** empty `blocks`, so
  they are **simultaneously `entry_points` and `leaf_nodes`** (the validator allows
  a node to be both); the TOML lists them in both computed sets. `entry_points` =
  all layer-0 units + `U09` + `U10` + `U11` + `U12`; `leaf_nodes` =
  `{U08, U09, U10, U11, U12}`; `critical_path` = the longest layer-0 build → `U08`
  (12 units, layers `{0: 11, 1: 1}`, node-weighted critical-path LOC 327).

---

## 5. Witness scripts (the part that actually grew)

### 5.1 `run_service_contract.sh` (enforces C01–C05; the load-bearing witness)

Per language, **serialized** in plain build order (no privileged position):

1. **Pre-flight:** assert `127.0.0.1:8080` is free (`ss`/`/dev/tcp` probe). If
   occupied → SKIP the entire run with rationale (a real resource gap, exactly
   like a missing toolchain). Honor `PROOF_PORT` override for CI but default to
   8080 to keep the contract literal. **No language-specific pre-flight** — every
   PASS-candidate uses the same ordinary connectivity probe (the §3.1 correction
   removed the old Java no-reuse special case).
2. **Start:** launch the server in its own process group (`set -m`) in the
   background; capture `PID`, redirect its stdout/stderr to files. Install a
   `trap` that `kill -9`s the **whole process group** (`kill -9 -- -$PID`) on
   **any** script exit path so a failed assertion never orphans the daemon *or its
   child workers* (e.g. a Node server's spawned children) on 8080.
3. **Readiness (C02):** poll TCP connect in a loop until connectable or the
   readiness deadline; record `time-to-ready` as **MEASURED**; FAIL if the
   deadline passes.
4. **Echo (C01/C03):** `curl -s -D <hdr> -X POST --data-binary @payload.json
   http://127.0.0.1:8080/`; capture status + body + headers; assert status `200`;
   `cmp -s` body against the exact `payload.json` bytes; assert `Content-Length`
   equals the payload byte length.
5. **Statefulness (C05):** repeat the POST a second time on the same PID; assert
   identical echo (proves long-lived, not one-shot). Record `bytes echoed` as
   MEASURED.
6. **Graceful shutdown WITH a real in-flight request (C04):** this step exercises
   C04's in-flight clause **against the actual server under test**, not only
   against the synthetic controls in §5.2. Open a `?delay_ms=1000` request and use
   an **explicit synchronization point** to guarantee the request is genuinely in
   flight before signalling: the delayed handler flushes the HTTP **status line +
   `Content-Length` headers**, then sleeps 1000 ms before writing the body. The
   witness blocks on reading those headers (proof the handler has been entered — no
   timing guess), and only **then** sends `SIGTERM`. It asserts (a) the in-flight
   response body arrives **complete and byte-exact** (not reset/truncated), (b) the
   process exits `0`, and (c) shutdown happens within the deadline; record
   `time-to-shutdown` as MEASURED. Not-exited-in-time ⇒ escalate to `SIGKILL` and
   mark **FAIL**; a truncated/dropped in-flight body ⇒ **FAIL** even if the exit
   code is `0`.
   **Header-flush caveat (MEASURED, referee-driven — see §5.6):** this sync point
   assumes the server transmits its response headers to the client *before* writing
   the body. Six runtimes do; `com.sun.net.httpserver.HttpServer` does **not** — it
   buffers the headers until body bytes flow, so the witness would receive
   headers+body together only *after* the Java handler returned and the in-flight
   window would silently **collapse** (the body already complete when SIGTERM
   lands). The Java handler therefore flushes the first body byte before the delay
   to force its headers onto the wire; the remainder stays genuinely in flight. The
   `time-to-shutdown` this step records for Java is consequently ~1000 ms like the
   others (not the spuriously fast figure an un-synced run produces), and the
   independent timing guard of §5.6 asserts the in-flight window is genuine for
   every PASS-candidate.
7. **Port release (C04):** after exit, assert 8080 is re-bindable via an
   **independent probe that itself sets `SO_REUSEADDR`** and bounded-retries for up
   to ~2 s to absorb TIME_WAIT. The probe sets the option **itself** — otherwise
   a fresh socket can hit TIME_WAIT even when the server set it, so testing the
   *server's* `SO_REUSEADDR` is not enough. Because the probe owns the option,
   this check is valid and **uniform for all seven runtimes including Java**: it
   does not depend on any server's socket-option choice (§3.1), and the retry
   covers the residual TIME_WAIT window.
8. Tally PASS/SKIP/FAIL; print MEASURED numbers separately; exit nonzero on any
   FAIL.

Fixed, deterministic payload (no non-determinism): a known JSON file
(`payload.json`), echoed byte-for-byte.

### 5.2 `detect_graceful_shutdown.sh` (negative control for C04 — analog of E03)

The graceful definition is the **stronger** one: a PASS requires not only "exit 0
on SIGTERM within deadline + port released" but also that an **in-flight request
completes** rather than being dropped. The witness drives **two** negative
controls, and PASS means the gate catches both:

- **Control A — ignores SIGTERM:** a server that never installs a handler (or
  blocks forever). The harness must classify it FAIL and fall back to SIGKILL.
- **Control B — drops in-flight request:** a server that, on SIGTERM, `exit(0)`s
  immediately while a slow request is still being served (so the client gets a
  reset/truncated body even though the exit code looks clean). The witness opens a
  deliberately slow request, fires SIGTERM mid-flight, and asserts the harness
  detects the **dropped/truncated response** as a C04 FAIL — i.e. a clean exit
  code alone is **not** accepted as graceful.

PASS here means "the gate discriminates graceful from non-graceful on both the
exit-code axis *and* the in-flight-completion axis," i.e. the C04 check is not
vacuous. This is the single most important honesty witness in the bundle.

**Reproducible "in-flight" without races, and without polluting C01.** Control B
needs a deterministic mid-flight window. The canonical servers expose a
**test-only** delay affordance (a `?delay_ms=` query the witness controls); this
path is explicitly **excluded from the C01/C03 byte-exact echo accounting** — the
canonical "smallest reasonable" server is the *no-delay* echo, and the delay
branch exists solely so the negative-control witness can open a request that is
provably still in flight when SIGTERM arrives. The injected delay is fixed at
**1000 ms**, **strictly less than the 3000 ms shutdown deadline** (C04
well-formedness rule, §1): a correct graceful server therefore finishes the
delayed request *and* exits inside the deadline, so the only way to FAIL Control B
is to actually drop the in-flight response.

"Without races" is made concrete by the **same synchronization point used in §5.1
step 6**: the delayed handler flushes status + `Content-Length` headers *before*
sleeping, and the witness sends `SIGTERM` only after it has read those headers off
the socket. So "the request is in flight" is an observed fact (the server has
entered the handler and committed headers), not an assumption about how fast the
SIGTERM arrives relative to connection setup.

### 5.3 `detect_awk_boundary.sh` (C06 boundary witness)

Starts the gawk `/inet` echo server and records the **C06 boundary**: gawk exposes
no clean script-level POSIX SIGTERM handler (SIGTERM → exit 143, `MEASUREMENTS.md`
M2), so AWK is a declared **SKIP-with-rationale** for the signal contract — not
silently dropped, not falsely passed. Direct parallel to hello-world's "AWK is
outside the sqry validator's language set" boundary.

Whether the gawk server *also* satisfies C01/C03 (byte-exact echo with correct
`Content-Length` framing over `/inet`) is **`UNASSESSABLE — no artifact yet`**: it
is plausible but non-trivial, and the witness reports the echo result honestly
once the gawk server is actually built and run, rather than asserting it in the
design. The *firm* C06 claim is the signal boundary alone.

### 5.4 `differential_echo.py` (cross-implementation behavioural equivalence)

The single-payload witness (§5.1) cannot reveal where the hand-rolled HTTP parsers
(C, Rust) *diverge* on edge cases. `differential_echo.py` closes that gap: it
launches each PASS-candidate server in turn (serialised on one port, exactly as
§5.1 does), sends a corpus of **adversarial** request bodies, and records
`(status, body)` per server. A faithful echo must return `200` with
`body == request` for **every** input; any divergence is a real bug in one
implementation the others do not share.

**Corpus (10):** `simple-json`, `empty`, `no-trailing-newline`, `nul-bytes` (full
0–255 byte range), `utf8-multibyte`, `embedded-crlf-http` (a fake HTTP request as
the body), `long-line-100k`, `large-1mib`, `whitespace-only`, `json-with-nul`.

**Calibration control (`zctrl-broken`):** a deliberately-unfaithful echo that
truncates the body to 16 bytes. The control is a **committed, inspectable
artifact** (`src/controls/broken_echo.py`) — a single source of truth, the
differential channel's analog of the graceful-vs-kill controls — which the
harness loads by its fixed bundle-relative path each run, so the calibration is
reproducible and traceable. If the harness does not flag the control, the
differential test is vacuous.

**Result (`DIFFERENTIAL-AGREEMENT.md`, 2026-06-01):** the control is flagged on
**6/10** requests (every body > 16 bytes) → the harness **demonstrably detects
divergence** (NON-VACUOUS); and **0 divergences among the 7 real servers** — all
return byte-identical `200` echoes on every adversarial input, including
full-byte-range NUL data, 1 MiB bodies, and embedded fake-HTTP. This upgrades the
proof from "each server passes a single payload" to "seven independent
implementations are byte-exact-equivalent across an adversarial corpus, and the
equivalence test is proven able to fail." AWK is excluded (the declared C06
boundary). This is the code-derivation-assay behavioural channel (shared corpus +
calibration control) applied to *strengthen* the proof.

### 5.5 `detect_java_reuseaddr.sh` + `ReuseSpike.java` (the re-pointed reproducer)

These exist to make the §3.1 correction **independently re-executable**, and they
are the honesty centrepiece of the rebuild. The original pair was written to
"confirm" the false finding (HttpServer cannot re-bind a TIME_WAIT'd port);
re-running the committed spike on this runner returns `HttpServer.create rebind:
OK`, so the original verdict **refutes itself**. The pair is re-pointed to the
**true, deterministic** finding (`MEASUREMENTS.md` M1):

- A properly-`start()`ed `HttpServer` **tolerates a prior TIME_WAIT** and releases
  its port immediately on `stop(0)` (the rebind succeeds), and
- A **never-`start()`ed** `HttpServer.stop()` **leaks its bound listener** (the
  in-process footgun that produced the old mis-reading).

The reproducer asserts both, SKIPs honestly when the environment cannot hold a
TIME_WAIT or sockets are unavailable (never a false FAIL), and carries the "we
mis-measured; the reproducer caught it" note inline. It is an auxiliary witness,
not part of the load-bearing C01..C05 gate — its purpose is to keep the retracted
finding falsifiable and on the record.

### 5.6 `detect_inflight_window.py` (C04 in-flight timing guard — referee-driven)

The §5.1-step-6 in-flight check asserts the in-flight body arrives **complete and
byte-exact**, which is necessary but **not sufficient**: it silently assumes the
server flushes its response headers *before* the body, so that "the request is in
flight" is an observed fact when SIGTERM is sent. A pre-submission referee read
demanded that assumption be measured rather than narrated, and the measurement
**overturned a confident claim**: `com.sun.net.httpserver.HttpServer` (default
null executor) does **not** transmit the response headers until body bytes flow.
Without a work-around the witness receives Java's headers+body together only after
the handler returns, so SIGTERM lands on an **already-complete** request and the
in-flight window **collapses** — C04's in-flight clause was, for Java, *vacuous*.
A Go control confirmed the contrast: with the header-flush sync working, Go's body
arrives ~1001 ms after SIGTERM (genuinely in flight); Java's arrived 0 ms after
(already sent). The earlier "Java shuts down in ~27 ms because `stop(2)` interrupts
the handler's sleep" reading was doubly wrong — the sleep **completes normally**,
and the fast exit was only because the handler had finished before the witness
could signal.

Two things came out of that measurement. First, the Java server's test-only delay
path now **flushes the first body byte before sleeping** (§5.1 step 6), forcing the
headers onto the wire so the remainder is genuinely in flight; Java's measured
shutdown is now ~1000 ms like the others. Second, this witness makes the in-flight
window an **explicit timed assertion**: for each PASS-candidate it records the
SIGTERM-delivery timestamp against the client-side body-**completion** timestamp
and requires completion **strictly after SIGTERM by a margin** (≥ half the injected
delay). A server whose window collapses (body already sent) finishes in ~0 ms and
**FAILs**; a genuine in-flight finishes ~`delay` ms later and **PASSes** — so the
guard is non-vacuous by construction (Java *pre-fix* would fail it). AWK is
excluded (the C06 boundary). This is the measure-first discipline (§3.1) applied
one more time, to the place it had not been: a runtime fact that the proof's
correctness depends on must rest on a committed, re-runnable measurement.

---

## 6. New result-word semantics for stateful services

| Word     | Meaning in this proof                                                                                           |
|----------|----------------------------------------------------------------------------------------------------------------|
| PASS     | Server became ready, echoed byte-exact over ≥2 requests, exited `0` on SIGTERM within deadline, released port.  |
| SKIP     | Toolchain genuinely absent **or** port 8080 occupied on the runner **or** declared boundary (AWK on C04).       |
| FAIL     | Bind failure, readiness/shutdown deadline exceeded, non-200, body mismatch, dropped in-flight response, nonzero exit on SIGTERM, or port not released. |
| MEASURED | `time-to-ready` (ms), `time-to-shutdown` (ms), `bytes echoed`. Evidence only; never promoted to PASS (per the hello-world paper's result-word discipline). |

This is the table the paper will lead with, because it is the concrete way the
framework absorbed asynchrony and timing.

---

## 7. The five DAG-TOML files (mirroring hello-world's proven-valid shapes)

All five carry the empty-closure sentinel `sha256:e3b0…b855` and validate against
the same reference validators in `../agent-assurance/validators/`.
**Path-existence is opt-in in those validators** (`validate_traceability.py` and
`validate_review_readiness.py` only stat `CODE`/`TEST`/`required_documents` paths
when invoked with `--check-paths-exist --repo-root <root>`). So §7's "every `path`
resolves on disk" guarantee is **only real if the build/validate step passes
`--check-paths-exist --repo-root` explicitly** — the default invocation checks
structure and links but not on-disk existence. The build harness (§10 step 3)
therefore runs every validator with those flags; a bare run is treated as
not-yet-validated.

- `contract_declaration.toml` — C01..C06 as in §1. New free-form domains
  (`service_lifecycle`, `readiness`, `echo_fidelity`, `signal_handling`,
  `statefulness`, `signal_boundary`). The `domain` field is free-form: the
  hello-world bundle already uses bespoke strings and
  `validate_review_readiness.py` does not constrain the vocabulary, so new domains
  validate without spec changes. `verified_by` points at the witness scripts + a
  TEST: id.
- `implementation_dag.toml` — the §4 graph (**12 units**, fan-in, **five leaf
  nodes** = the fan-in verifier `U08` + four independent sidecars
  `U09`/`U10`/`U11`/`U12`, matching the validator-computed `leaf_nodes` set in §4),
  with `estimated_loc` on every unit and an explicit `[computed]` block.
  (hello-world's three-leaf shape is the precedent; this proof adds the
  differential and in-flight-timing sidecars.)
- `traceability.toml` — five chains: the service-lifecycle chain
  (INT→FEAT→REQ→IMP→**8×CODE**→TEST; one CODE per language source file, JS and TS
  distinct even though they share build unit `U02`), the graceful-vs-kill
  negative-control chain, the AWK-boundary chain, the differential-equivalence
  chain, and the in-flight-window chain (§5.6). Every `path` resolves on disk.
- `review_readiness.toml` — one gate `G01` with the `required_documents` field
  (the field the validator actually requires) listing the service-witness pack.
  Its `pass_conditions`/`block_conditions` are **human-facing narrative the static
  validator does not check** (see §8); they are enforced only by actually running
  the witnesses.
- `evidence_matrix.toml` — claims E01 structural, E02 contract-enforced-across-
  languages, E03 non-graceful-server-is-caught, E04 readiness/shutdown-within-
  deadline (MEASURED→gated), E05 awk-boundary-is-declared, **E06
  cross-implementation-behavioural-equivalence**, **E07 C04-in-flight-window-
  genuinely-exercised** (§5.6) — each linked to the witness evidence files.

---

## 8. Validator gaps (the honest section the paper must contain)

The five static validators check **structure**, not **runtime**. Concretely:

- They confirm C01 is *declared*, *wired* to a TEST, and that the script *exists*
  — they cannot confirm the server ever bound, echoed, or shut down. All dynamic
  guarantees live **only** in the bespoke shell/python witnesses, exactly as in
  hello-world. The static layer's job is provenance and wiring; the runtime truth
  is the witness exit code surfaced into the paper's *Observed Execution* table.
- `contract_declaration` accepts free-form domains but has **no semantics** for
  `signal_handling` or `readiness` — it cannot know a deadline was met.
- `review_readiness` (`validate_review_readiness.py`) requires each gate to have
  an `id`, an `artifact_class`, and **one of**
  `checks`/`required_documents`/`criteria`/`summary`, and it resolves the
  `artifact_class` link. It does **not** inspect `pass_conditions` or
  `block_conditions` at all — those fields are unvalidated free narrative — and it
  never evaluates any condition against a run. The gate's actual decision logic
  therefore lives entirely outside the static layer.
- There is **no validator hook for MEASURED** — it is a paper-level reporting
  discipline (from hello-world), not a checked rule; the timing numbers live in
  evidence/prose.
- `validate_code_symbols.py` (sqry) is source-analysis and largely orthogonal
  here: this proof's sidecars are **behavioral** (graceful-vs-kill, awk boundary,
  differential equivalence), not AST-based like hello-world's. So symbol
  validation is out-of-scope rather than partially-skipped.

This gap is the natural bridge to the *next* follow-ups in the four-scenario arc —
especially #4 (handing verification to Semgrep/CodeQL) — which we note as future
work without overclaiming here.

---

## 9. Threats to validity / explicit non-claims

- **Not a benchmark / load test.** No throughput, p99, or concurrency-under-load
  claims. The only numbers are MEASURED readiness/shutdown times against declared
  deadlines on one runner.
- **Minimal HTTP, not RFC conformance.** The echo handler parses just enough HTTP
  to satisfy C01/C03; it is not a conformant HTTP/1.1 server, no TLS, no keep-alive
  guarantees beyond the test.
- **POSIX signals only.** SIGTERM/SIGKILL semantics assume a POSIX runner; Windows
  is out of scope.
- **8080 is a runner-global assumption.** The proof serializes and checks
  freeness, but a hostile environment that races for the port can still cause a
  legitimate SKIP. Documented, not hidden.
- **Graceful = "exit 0 within deadline + in-flight request (≤1000 ms) completes +
  port released (independent SO_REUSEADDR probe + bounded re-bind retry)."** It is
  *not* a proof of zero connection drops under arbitrary concurrency, nor of
  graceful behaviour for requests longer than the shutdown deadline.
- **AWK echo is not asserted.** Only the AWK C06 signal boundary is a firm claim;
  whether gawk `/inet` achieves byte-exact C01/C03 echo is reported from the actual
  run, not promised here.
- **Differential equivalence proves agreement, not external correctness.** Echo is
  a near-identity contract, so behavioural equivalence is expected; the value is in
  exercising the edge cases (binary, large, framing) the single payload skips and
  proving the servers genuinely agree there. For echo the oracle (`out == in`) *is*
  the spec, so agreement and correctness coincide; the corpus is hand-chosen, not
  exhaustive (a property-based fuzz front-end would extend it).
- **The retracted Java finding is recorded, not hidden.** §3.1 retracts the false
  SO_REUSEADDR claim and the re-pointed reproducer (§5.5) keeps the true finding
  falsifiable. No port-ordering or pre-flight behaviour depends on Java specifics.
- **No production-readiness, security, or supply-chain claim.** Those are the other
  three scenarios (#2 concurrency, #3 dependencies, #4 SAST).

---

## 10. Deliverables (build order)

1. `non-trivial-proof/proof-bundle/src/{go,node,typescript,python,c,rust,java,awk}/…`
   — eight smallest-reasonable echo servers (+ the non-graceful control variants in
   `src/controls/`, + the re-pointed Java spike in `src/spikes/`).
2. `run_service_contract.sh`, `detect_graceful_shutdown.sh`,
   `detect_awk_boundary.sh`, `differential_echo.py`, `detect_inflight_window.py`,
   `detect_java_reuseaddr.sh` — executable witnesses.
3. The five `*.toml` DAG-TOML files (§7), each validating against
   `../agent-assurance/validators/` — invoked with **`--check-paths-exist
   --repo-root <repo>`** so the on-disk existence of every `CODE`/`TEST`/
   `required_documents` path is actually enforced, not just structure/links.
4. `proof-bundle/README.md` — the worked walkthrough (hello-world style).
5. A real `run` on this runner → an **Observed Execution** table with actual
   PASS/SKIP/FAIL + MEASURED ms numbers (not invented), plus the differential-run
   table.
6. `manuscript/main.tex` + `references.bib` — the paper, only after the bundle runs
   green.
7. The container files (`Containerfile`, `reproduce.sh`, `build-and-run.sh`) with an
   honest partial-pinning disclosure.

The cross-model review gate (§12) runs after each milestone, recording only
reviewer output retrieved by job ID.

---

## 11. Sign-off decisions (carried forward, re-confirmed for the rebuild)

1. **Title / framing.** *"A Stateful Executable Proof: Governing an HTTP Echo
   Service Lifecycle Across Eight Languages (Six Runtimes, One Boundary)."* The
   headline noun is **eight languages** (directly verifiable from the §3 table);
   "six runtimes, one boundary" is the derived gloss defined by the §2 counting
   rule.
2. **Deadlines.** readiness = 5000 ms, shutdown = 3000 ms.
3. **Rust `unsafe` libc FFI.** Stay crate-free/hermetic via a small `extern "C"`
   block declaring `signal`/`SIGTERM` **and** `socket`/`setsockopt`/`bind`/`listen`
   (needed for SO_REUSEADDR pre-bind); real third-party deps are deferred to
   scenario #3. The `unsafe` block is documented inline.
4. **Negative control (stronger definition).** Graceful requires in-flight
   completion, not just a clean exit code. Two negative controls (ignores-SIGTERM
   and drops-in-flight); see §5.2 and the C04 clause in §1.
5. **Layout.** Build at `non-trivial-proof/proof-bundle/` so the sibling scenarios
   (#2 concurrency, #3 dependencies, #4 SAST) can live beside it later.
6. **No Java special-casing (new — §3.1).** The retired design's Java-first
   ordering and no-reuse pre-flight are removed; the false SO_REUSEADDR finding is
   retracted and replaced by the measured, re-pointed reproducer.

---

## 12. Cross-model review record (rebuild)

Reviewers run via the `gtwy` gateway against this document and the rebuilt bundle
with read access to both repos, instructed to verify every claim against the files
and the live toolchain (not against a summary). This record will cite **only**
output actually retrieved by job ID; failed, pending, or non-retrievable runs are
labelled as such and never counted as approvals. No reviewer verdict or finding is
recorded here before its job output has been retrieved by ID.

**Status: SATISFIED** (2026-06-01) across five rounds: the design+bundle round
(§12.1), the manuscript+container round (§12.2), a holistic pre-merge round over the
integrated PR (§12.3), the manuscript-expansion round (§12.4), and an external
referee-driven round that measured and fixed a vacuous Java in-flight check
(§12.5). Each rests on Codex's blocker(s)→fix→evidence-backed unconditional
approval, with Gemini corroborating; only output retrieved by job ID is recorded.

### 12.0 Integrity note (why the prior §12 was discarded)

The retired set's §12 recorded six "rounds" of cross-model review. Two earlier
drafts of that record **fabricated** reviewer findings and approvals before the
corresponding job output had been retrieved (including a false "Codex unconditional
approval" when the actual verdict was a blocker), and the substantive Java
SO_REUSEADDR finding those rounds were "confirming" was itself false (§3.1). The
entire prior review record is therefore **void** and is not carried forward. This
rebuild re-opens the gate with no inherited approvals: the only valid evidence is
reviewer output retrieved by job ID *after* this DESIGN.md and the rebuilt bundle
exist on disk.

### 12.1 Round 1 (rebuild): the rewritten DESIGN.md + the rebuilt proof-bundle

Reviewers had read/exec access to both repos and were asked to re-run the five
validators and five witnesses themselves, grep for any live (non-retraction) Java
SO_REUSEADDR / Java-first assertion, verify §3.1 against MEASUREMENTS.md M1, check
the differential-witness wiring + non-vacuity, and confirm the load-bearing
witness genuinely enforces C03/C04/C05. The review packet is
`REBUILD-REVIEW-PACKET.md`. Only output retrieved by job ID is recorded.

| Reviewer (model) | Job IDs | Verdict |
|------------------|---------|---------|
| Codex (`gpt-5.x`) | `b5517357` → `1fd1d249` | **BLOCKER** (`ReuseSpike.java`) → after fix: **UNCONDITIONAL APPROVAL** (evidence-backed; re-read file + re-ran all witnesses/validators) |
| Gemini (`gemini-2.5-pro`) | `3bed660d` | **UNCONDITIONAL APPROVAL** (evidence-backed; ran validators + witnesses itself) |

**Codex (`b5517357`) — genuine blocker.** Codex re-ran everything (5 validators +
5 witnesses green, counts confirmed) and found one real honesty defect: the
re-pointed `ReuseSpike.java` claimed the corrected finding **CONFIRMED (exit 0)**
on the footgun half alone when the environment could not establish a `TIME_WAIT`,
instead of the honest **exit-2 SKIP** that §5.5 promises — the tolerance half (the
*direct* refutation of the old false claim) had not been exercised. Fixed: the
`!timeWaitPresent` branch now prints INCONCLUSIVE and `System.exit(2)`; exit-0
CONFIRMED is reachable only when the tolerance test passed **and** the footgun
leaked. The header comment was corrected to stop calling the footgun
"load-bearing." Re-review `1fd1d249` re-read the file (`ReuseSpike.java:146`),
confirmed the exit-2 SKIP path and the both-halves-required verdict, re-ran
`detect_java_reuseaddr.sh` (still CONFIRMED on this runner), and re-ran the full
witness + validator suite as a regression check — then gave unconditional approval.

**Gemini (`3bed660d`) — evidence-backed approval.** Gemini independently ran the
five validators and five witnesses (matching counts and the 7 PASS/1 SKIP/0 FAIL +
differential 0-divergence / control-caught-6/10 results), confirmed no live
Java-first assertions remain, verified §3.1 against M1 and the differential wiring,
and approved unconditionally. (Gemini did not catch the `ReuseSpike` honest-SKIP
defect that Codex blocked on; recorded honestly — this round's blocker rests on
Codex.)

**Round-1 gate status: SATISFIED** on Codex's blocker→fix→evidence-backed
approval (`1fd1d249`), with Gemini's evidence-backed approval corroborating. The
`ReuseSpike` fix lands in the same change set as this record.

### 12.2 Round 2 (rebuild): the rewritten manuscript + container

The Phase-3 manuscript (`manuscript/main.tex`, `README.md`, `references.bib`) and
container files (`Containerfile`, `reproduce.sh`, `build-and-run.sh`) were rewritten
to match the corrected design, then submitted to the gate (packet
`REBUILD-REVIEW-PACKET-R2.md`). The container build (podman) and PDF build (no TeX
on the runner) were declared UNASSESSABLE-by-execution and verified by reading;
reviewers re-ran the validators and witnesses themselves.

| Reviewer (model) | Job IDs | Verdict |
|------------------|---------|---------|
| Codex (`gpt-5.5`) | `9d06f351` → `efd12727` → `06951dc2` → `894dd9ec` | **3 sequential BLOCKERs → UNCONDITIONAL APPROVAL** (evidence-backed; per-file validators re-run) |
| Gemini (`gemini-2.5-pro`) | `1b9da564` | **UNCONDITIONAL APPROVAL** (evidence-backed; ran validators + five witnesses) |

**Codex — three genuine blockers, each a retraction-trigger phrase or a stale count
surviving outside the correction section:**

| # | Job | Blocker | Fix |
|---|-----|---------|-----|
| 1 | `9d06f351` | A "pristine port" retraction mention in the Implementation-DAG section (`main.tex`, then ~line 264), outside §"A Measured Runtime Correction" | reworded generically; the paragraph now states plain build order + points to §java |
| 2 | `efd12727` | "special Java-first run order" in the **abstract** (`main.tex:81`) — a hyphenated form a space-only grep missed | abstract reworded to "a socket-option limitation … a special run order", no trigger phrases |
| 3 | `06951dc2` | Stale "Ten-unit"/"two sidecar" prose in `evidence_matrix.toml` (EV01 summary + M01/M02 scope) — a latent inconsistency predating round 1 that BOTH reviewers had missed | corrected to eleven-unit/three-sidecar; EV02 completed with the differential chain |

After blocker 2 the author also ran a wrap-aware sweep and proactively fixed a
fourth instance the line-based greps missed (a `cannot set SO_REUSEADDR` restatement
in the Claim Audit table). Re-review `894dd9ec` inspected `evidence_matrix.toml`
line by line, ran each TOML's matching validator (impl-DAG 11 units/{0:10,1:1}/327;
traceability 36 entities; evidence-matrix 23 = 6 claims + 8 evidence + 9 matrix),
and confirmed via an in-section check that every surviving trigger phrase in
`main.tex` (lines 439/441/464) lies inside §"A Measured Runtime Correction" — then
gave unconditional approval.

**Gemini (`1b9da564`) — evidence-backed approval, non-penetrating.** Gemini
independently ran the five validators and all five witnesses (matching the reported
results) and approved up front, but caught **none** of Codex's three blockers.
Recorded honestly: the round rests on Codex.

This round's change set also includes the stale `manuscript/main.pdf` removal (it
predated the rewrite and there is no TeX on the runner to rebuild it; it is a
container build product), the `differential_echo.py` exit-code addition (0 only if
0 divergences AND the calibration control is caught), and the container's five-witness
gating.

**Round-2 gate status: SATISFIED** on Codex's blockers→fixes→evidence-backed
approval (`894dd9ec`), with Gemini's evidence-backed approval corroborating.

### 12.3 Round 3 (final pre-merge): the integrated PR

After the rebuild was committed (`2b694a9`) and opened as a pull request, the
**entire committed PR diff** (base `origin/main` `6e88d91` … head `2b694a9`, 37
files) was submitted to the gate one final time — a holistic pass over the
integrated whole, re-verifying from scratch rather than resting on §12.1/§12.2.
Reviewers were asked to check whole-study consistency across DESIGN.md, the five
TOMLs, the witnesses, the manuscript, and the container; the absence of any live
false-Java assertion; green + non-vacuous witnesses/validators; and that the
commit-message and PR-body claims hold against the actual diff.

| Reviewer (model) | Job IDs | Verdict |
|------------------|---------|---------|
| Codex (`gpt-5.5`) | `49a4a78f` → `9c318530` | **BLOCKER** (`DESIGN.md` §5.4) → after fix: **UNCONDITIONAL APPROVAL** (evidence-backed) |
| Gemini (`gemini-2.5-pro`) | `02eaadeb` | **UNCONDITIONAL APPROVAL** (evidence-backed; ran validators + five witnesses, checked cross-document counts) |

**Codex (`49a4a78f`) — one genuine cross-document contradiction.** §5.4 still
described the differential calibration control as "materialized by the harness
itself (embedded + written to a temp path each run)" — the *original* approach,
abandoned mid-build in favour of a **committed** `src/controls/broken_echo.py`
that the harness loads by its fixed bundle-relative path. The harness,
traceability (`CODE:diff-broken-control`), evidence matrix (`E06`/`EV08`), and the
manuscript had all been updated to the committed-control model; only §5.4 was
stale. Fixed: §5.4 now describes the committed, inspectable control. Re-review
`9c318530` confirmed §5.4 matches `differential_echo.py` (`BROKEN_CONTROL =
BUNDLE / "src/controls/broken_echo.py"`), found no remaining
materialized/embedded/temp-path description, re-ran the differential witness (exit
0, 0 divergences, control caught 6/10), and re-confirmed the counts — then
approved unconditionally. (Both prior rounds had missed this stale §5.4 line; the
holistic integrated pass is what surfaced it.)

**Gemini (`02eaadeb`) — evidence-backed approval.** Gemini independently re-ran
the five validators and five witnesses, verified the counts across DESIGN.md /
README / `main.tex` / the TOMLs, confirmed the Java retraction is correction-context
only, and approved; it did not catch the §5.4 contradiction. The round rests on
Codex.

**Round-3 gate status: SATISFIED** on Codex's blocker→fix→evidence-backed approval
(`9c318530`), with Gemini's evidence-backed approval corroborating. The §5.4 fix
and this record land in a follow-up commit on the PR branch.

### 12.4 Round 4 (manuscript expansion): two new sections

The manuscript was then expanded with two sections that surfaced contributions
previously confined to the design docs: §"Differential Behavioural Equivalence
Across Implementations" (with a results table) and §"Keeping the Proof Honest:
Measure-First and Adversarial Cross-Model Review". The paper grew from 11 to 13
pages; the container reproduction stayed green and the PDF compiled. The expansion
was re-submitted to the gate.

| Reviewer (model) | Job IDs | Verdict |
|------------------|---------|---------|
| Codex (`gpt-5.5`) | `610175e4` → `c7fd3345` | **BLOCKER** (`main.tex` review-scope overclaim) → after fix: **UNCONDITIONAL APPROVAL** (evidence-backed) |
| Gemini (`gemini-2.5-pro`) | `01e67988` | **UNCONDITIONAL APPROVAL** (evidence-backed; verified the differential table byte-lengths + every §12 blocker reference) |

**Self-caught before the gate.** The new honesty section's example-blocker list
first mixed in defects from the *voided* pre-rebuild review log (a Content-Length
omission, a listener-absence port check, a synthetic-only in-flight clause) rather
than the documented §12.1–§12.3 rebuild-gate blockers. This was caught and
corrected before dispatch — the list now cites only real, recorded rebuild-round
blockers — so a section about honesty would not itself overclaim.

**Codex (`610175e4`) — genuine overclaim.** The "Adversarial cross-model review"
paragraph said "Before each milestone the design, the bundle, the manuscript, and
the container were submitted…", implying all four artifacts were reviewed every
round — but §12.1 reviewed design+bundle, §12.2 manuscript+container, and §12.3 the
integrated PR. Fixed to state the accurate per-round scoping. Re-review
`c7fd3345` confirmed the wording matches §12.1/§12.2/§12.3, re-ran the differential
and Java witnesses, and re-verified the honesty section's blocker list,
"approval-is-not-evidence" point, and §12.0 fabrication note — then approved
unconditionally.

**Gemini (`01e67988`) — evidence-backed approval.** Gemini re-ran the differential
witness, checked the table's flagged-vs-≤16-byte rows against the actual corpus
byte lengths and the committed control's truncation, and verified every honesty
section blocker against §12.1–§12.3 — but did not catch the review-scope overclaim.
The round rests on Codex.

**Round-4 gate status: SATISFIED** on Codex's blocker→fix→evidence-backed approval
(`c7fd3345`), with Gemini's evidence-backed approval corroborating.

### 12.5 Round 5 (external referee): the Java in-flight measured correction

An external pre-submission referee report raised two BLOCKERs (M1a, M1b): the
paper made **un-measured Java runtime claims**, the very sin the measure-first
discipline exists to prevent. The response was to **measure**, and the
measurement was significant.

**M1a — C04's in-flight clause was vacuous for Java.** The Table-3 footnote
claimed Java shut down in 27 ms because `server.stop(2)` "interrupts the handler's
sleep." Direct measurement (instrumented server + a Go control) overturned both
the figure and the mechanism: `com.sun` `HttpServer` (default null executor) does
**not** transmit response headers to the client until body bytes flow, so the
witness's header-flush sync point silently failed for Java — SIGTERM landed on an
*already-complete* request and the in-flight window never opened (Java body 0 ms
after SIGTERM vs. Go's ~1001 ms; the sleep completed normally). The fix:
`src/java/Server.java`'s test-only delay path now flushes the first body byte
before sleeping, forcing the headers onto the wire so the remainder is genuinely
in flight; Java's measured shutdown is now ~1000 ms like the others. A new
permanent guard, `detect_inflight_window.py` (U12 / chain 5 / E07), asserts each
PASS-candidate's in-flight body completes **strictly after SIGTERM** by ≥ half the
delay — non-vacuous by construction (Java *pre-fix* would fail it). This is §3.1's
discipline applied one more time, to the place it had not been (§5.6).

**M1b — causal hedge.** §3.1 and the manuscript's §"A Measured Runtime Correction"
no longer assert HttpServer's NIO `ServerSocketChannel` "has `SO_REUSEADDR` on by
default" as fact; the measured rebind carries the claim and the mechanism is
reported as an inference about this JDK build (the JDK documents channel option
defaults as implementation-specific). **M3** — §1 now defines "proof" narrowly
(executable falsifiable evidence artifact, not a formal/machine-checked proof).
**M2** — the "critical path" framing is corrected (the DAG is depth-1; 327 is the
heaviest leaf, not a scheduling claim) and the section now states what the
declarative layer adds over a bare test suite. **M5** — the paper now reports the
podman container reproduction as a second, mostly-pinned environment. Plus minors
(JEP 330 clause for "no javac", softened Rust/libc phrasing).

| Reviewer (model) | Job IDs | Verdict |
|------------------|---------|---------|
| Codex (`gpt-5.5`) | `c122fe8c` → `3a4dcdda` | **BLOCKER** (stale §2 artifact counts) → after fix: **UNCONDITIONAL APPROVAL** (ran the full podman reproduction itself: 6 witnesses + 5 validators + 14-page PDF) |
| Gemini (`gemini-2.5-pro`) | `8088a07e` | **BLOCKER** (same §2 counts + a stale `FUTURE-STUDIES.md` status) → both fixed; evidence-backed verification of the core fix |

**Both reviewers independently confirmed the core fix** — `detect_inflight_window.py`
all 7 PASS with Java ~1000 ms after SIGTERM, `run_service_contract.sh` 7/1/0 with
Java shutdown ~1024 ms, differential still 0 divergences / control 6/10, the Java
source correct. This round each then caught the **same** live stale count (the §2
Artifact inventory still read 11 units / four chains / six claims / eight evidence
and omitted the new witness) — notable because for once Gemini penetrated as well,
and additionally flagged `FUTURE-STUDIES.md` marking scenario #1 "in progress."
Both were corrected; the historical §12.1–§12.4 counts are intentionally
point-in-time and unchanged.

**Round-5 gate status: SATISFIED** on Codex's blocker→fix→evidence-backed approval
(`3a4dcdda`), with Gemini's evidence-backed verification corroborating. The
container reproduction stays green with all six witnesses and a 14-page PDF.
