# Design: The Stateful I/O Proof — a Multi-Language HTTP Echo Server

**Status:** design draft, cross-model review gate SATISFIED (no bundle code written yet).
**Working dir:** `non-trivial-proof/` (holds this `DESIGN.md`; no `proof-bundle/`
yet. Note: an untracked `Hello.java` stub predates this work — a stray probe
artifact, not part of the bundle, to be removed before build.).
**Companion to:** `hello-world/` (the trivial proof this follow-up answers).
**Author target:** Werner Kasselman / Verivus OSS.
**Date:** 2026-05-31.

> **Provenance note.** Every engineering decision below is the author's own.
> §12 records only genuine cross-model review output retrieved by job ID; it
> must never contain summarized, assumed, or fabricated reviewer content. (Two
> earlier drafts violated this and were corrected — see the §12 integrity note.)

---

## 0. One-paragraph thesis

The hello-world proof governs an **instant, deterministic, stdout-only**
contract. A real assurance framework has to govern **long-lived, stateful,
network-facing** programs too. This follow-up keeps the exact same DAG-TOML
machinery (contract declaration → implementation DAG → traceability →
review-readiness gate → evidence matrix → executable witnesses) but points it
at a contract that *cannot* be checked by running a program to completion and
diffing stdout. The program must **bind a port, stay alive, answer over the
network, and die gracefully on a signal**. The contribution is showing that
the same inspectable, falsifiable proof structure survives the jump from a
14-byte print to a process *lifecycle* — and naming precisely which parts of
the framework had to grow (a lifecycle-aware witness harness, the MEASURED
result word, a port-as-shared-resource discipline) and which parts the static
validators still cannot see.

---

## 1. The contract (what the program must do)

> **C01 (load-bearing).** The program, when started, MUST bind a TCP listener
> on `127.0.0.1:8080`, accept an HTTP `POST /` carrying a JSON request body,
> and return `200 OK` whose response body is the **exact byte sequence** of
> the request body (a faithful echo). On receipt of `SIGTERM` it MUST stop
> accepting connections, finish any in-flight request, release the port, and
> exit with code `0`.

That single sentence hides several separable obligations. As in hello-world
(C01 load-bearing, C02–C04 narrowings, C05–C06 boundary witnesses), we
decompose so each obligation has its own witness and its own non-claim:

| ID  | Domain                  | Obligation (exact, testable)                                                                                   | Result words in play |
|-----|-------------------------|--------------------------------------------------------------------------------------------------------------|----------------------|
| C01 | `service_lifecycle`     | Full lifecycle: becomes ready → echoes byte-exact → exits 0 on SIGTERM → releases port. Load-bearing.        | PASS / SKIP / FAIL   |
| C02 | `readiness`             | Becomes connectable on `127.0.0.1:8080` within a **readiness deadline** (default 5000 ms).                    | PASS/FAIL + MEASURED time-to-ready |
| C03 | `echo_fidelity`         | Response status is exactly `200`; response body `cmp`-equal to the request body; `Content-Length` == body length. | PASS / FAIL |
| C04 | `signal_handling`       | After SIGTERM: any **in-flight request completes** (no dropped/truncated response), the process exits `0` within a **shutdown deadline** (default 3000 ms), and the port is **re-bindable** afterward — verified by an independent re-bind probe that sets **SO_REUSEADDR** plus a bounded retry absorbing TIME_WAIT (the *server's own* SO_REUSEADDR is set by six of seven runtimes; Java is the documented exception, §3). SIGKILL fallback, a dropped in-flight response, or a non-re-bindable port ⇒ FAIL. **Well-formedness rule:** the test-injected in-flight delay MUST be strictly less than the shutdown deadline (we use 1000 ms ≪ 3000 ms) so a *correct* graceful server can both finish the request and exit in time. | PASS/FAIL + MEASURED time-to-shutdown |
| C05 | `statefulness`          | A single long-lived process answers **≥2 sequential requests** (proves it is a daemon, not a one-shot exec). | PASS / FAIL          |
| C06 | `signal_boundary`       | Declared boundary: a runtime that can serve C01/C03 but cannot install a clean SIGTERM handler is recorded as a **SKIP-with-rationale**, not a PASS and not a FAIL. (This is AWK.) | SKIP (declared)      |

Why this decomposition matters: it lets the gate distinguish "the toolchain
isn't here" (SKIP) from "the server bound but never answered" (C02/C03 FAIL)
from "the server answered but had to be SIGKILLed" (C04 FAIL). hello-world
could collapse everything into one stdout `cmp`; a service cannot.

---

## 2. Why this "breaks the trap" — mapped to spec mechanics

Each bullet is a concrete capability the proof *forces* that hello-world never
exercised, with the spec hook it lands on.

1. **Process-lifecycle orchestration (not run-to-completion).**
   hello-world's `run_all.sh` ran each program to exit and diffed stdout. Here
   the verify unit must *background* the server, capture its PID, **poll for
   readiness** (the server is not ready the instant `fork` returns), drive it
   over the network, then **signal** it and capture the post-signal exit
   status. New harness primitives: PID capture, readiness polling with
   timeout, signal delivery, exit-after-signal capture, guaranteed teardown.

2. **Port 8080 is a global, mutable, singleton resource.**
   hello-world units were embarrassingly parallel (independent temp dirs).
   A bound port is shared mutable state on the runner. The DAG's layer-1
   verify unit must **serialize** language runs (never two servers on 8080 at
   once), **fail fast / SKIP** if 8080 is already occupied, and **prove the
   port is released** between languages. This is the first proof where the
   implementation-DAG's "fan-in to one verifier" shape is *load-bearing for
   correctness*, not just tidy.

3. **Asynchronous timing ⇒ the MEASURED result word.**
   The four-word result vocabulary (PASS / SKIP / FAIL / **MEASURED**) is
   defined in the hello-world paper's "PASS, SKIP, FAIL, and MEASURED"
   section, not in a numbered `spec.md` clause — `spec.md` §10 is the IJB
   foundation and never mentions MEASURED. time-to-ready and time-to-shutdown
   are MEASURED numbers; "within the deadline" is a *separate* PASS/FAIL
   contract (C02, C04). The hello-world paper explicitly reported **no
   MEASURED values**. This proof is the first in the **papers repo** to use the
   fourth result word for real, and to honor that paper's rule that a
   measurement is not promoted to a PASS. (Scope check before publication:
   audit `../agent-assurance/examples/` to confirm no prior MEASURED use there;
   the claim is currently scoped to `agent-assurance-papers`, not the whole org.)

4. **Inter-process communication via signals (SIGTERM vs SIGKILL).**
   Graceful shutdown is only meaningful against a negative control. A server
   that *ignores* SIGTERM, or one killed with SIGKILL, must be **caught** by
   the gate. The proof includes a negative-control witness whose PASS means
   "the gate correctly identified a non-graceful server as FAIL" — the
   lifecycle analog of hello-world's `divergent_implementation_would_fail`.

5. **Same observable contract, radically different runtimes.**
   The cross-language claim moves up from "same stdout bytes" to "same
   *behavioral lifecycle*" across:
   - **event loop** (Node.js: `http` + `process.on('SIGTERM')` + `server.close`),
   - **green threads** (Go: `net/http` + `signal.Notify` + `http.Server.Shutdown`),
   - **OS threads / blocking accept** (Python: `http.server` + `signal`; C: raw
     BSD sockets + `sigaction`),
   - **FFI signal handling with no runtime help** (Rust: `std::net::TcpListener`
     + hand-declared `libc` `signal`/`setsockopt` via `extern "C"`, **no
     external crates**),
   - **interpreter with no signal API** (AWK/gawk `/inet`: the declared
     boundary).

   **Counting rule — the headline is "eight languages."** The firm, directly
   verifiable number is the one in the §3 table: **eight languages**. Everything
   else is a derived gloss. Of the eight, seven are PASS-candidates (Go,
   JavaScript/Node, TypeScript, Python, C, Rust, Java); AWK is the declared C06
   boundary and is **not** counted as a passing runtime. "Six runtimes" is then
   a *defined* sub-count, where **"runtime" means a distinct language execution
   stack**: TypeScript shares the V8/Node stack with JavaScript (so they collapse
   to one), leaving **six** — Go, V8/Node (JS + TS), CPython, the JVM, and C and
   Rust counted **separately**. We flag the soft edge honestly: C and Rust are
   both bare natively-compiled binaries over libc with no managed VM, so under a
   stricter "managed-runtime" definition one could collapse them into a single
   "native" bucket and reach five; we count them separately because they are
   distinct toolchains and execution stacks. The title therefore *leads with
   eight languages* and treats "six runtimes, one boundary" as the explained
   derivative, not the load-bearing claim.

---

## 3. Language set (broad, per request) and runner reality

Toolchain confirmed on this runner (2026-05-31): `go` 1.26.3, `node` v24.15.0,
`python3` 3.13.13, `cc` (gcc 15.2.0), `rustc` 1.90.0, `java` 25.0.3 (runtime
only — **no `javac`**), `gawk` 5.3.2, plus `curl`/`jq`/`ss`/`lsof`/`nc`.
**Missing:** `javac`, `tsc`, `semgrep`. Port 8080 free. (All versions
independently re-verified by the §12 reviewers.)

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

All "PASS" cells are **intended/predicted** outcomes; the real verdicts come
only from the §10 build-and-run step, not from this table.

Notes that change the design from a naive "just SKIP what's missing":
- **Java has no `javac` here but Java 25 runs `.java` directly** — so Java is a
  PASS-candidate, not a SKIP. The HTTP server is
  `com.sun.net.httpserver.HttpServer` from the **`jdk.httpserver` module**
  (shipped with the JDK, auto-resolved by single-file source launch); it is a
  bundled JDK module, *not* part of `java.net`. We name that dependency
  explicitly rather than implying bare stdlib.
- **gawk can open a TCP listener** via `/inet` special files, so AWK is a
  plausible C01/C03 server — **but** byte-exact echo with correct
  `Content-Length` framing over `/inet` (record-separator driven, binary-safe)
  is materially harder than a one-line claim suggests. Therefore the AWK
  **echo (C01/C03) is `UNASSESSABLE — no artifact yet`** until a working gawk
  server is built and run; the *firm* declared claim is only the **C06 boundary
  SKIP** (gawk exposes no clean script-level POSIX SIGTERM handler). This still
  mirrors hello-world's AWK-as-boundary, with the boundary at *runtime/signal*
  rather than *AST analysis*.
- **Rust stdlib has no signal API and `TcpListener::bind` does not set
  `SO_REUSEADDR`.** To stay hermetic (no crates — this is the stateful test,
  not the dependency test #3) Rust declares the needed `libc` symbols through a
  small `extern "C"` block: `signal`/`SIGTERM` (handler flips an `AtomicBool`)
  **and** `socket`/`setsockopt(SO_REUSEADDR)`/`bind`/`listen`, then wraps the fd
  with `TcpListener::from_raw_fd`. Without this the port-release check (§1 C04)
  would flake on TIME_WAIT for Rust specifically. The whole `unsafe` surface is
  small and inspected inline.
- **SO_REUSEADDR is a cross-language C04 sub-requirement, not an afterthought.**
  Go (`net.Listen`) and Node (`http.Server`) set it by default; C sets it via
  `setsockopt`; Rust via the FFI path above; Python's `http.server` sets
  `allow_reuse_address = True`. **Java is the documented exception** — see the
  Java-specific note below. The witness additionally treats the post-exit
  re-bind as a **bounded retry** (poll for up to ~2 s) so a lingering TIME_WAIT
  socket never causes a false C04 FAIL *for the runtimes that set SO_REUSEADDR*.
- **Java cannot set SO_REUSEADDR (empirically verified 2026-05-31, OpenJDK
  25.0.3 / Linux `tcp_fin_timeout=60`).** A pre-build spike established that
  `com.sun.net.httpserver.HttpServer` sets **no** `SO_REUSEADDR` and exposes
  **no API to set it**: neither `HttpServer.create(addr, backlog)` nor the
  unbound `HttpServer.create()` + `bind(addr, 0)` path surfaces the underlying
  `ServerSocket`, so `setReuseAddress(true)`-before-`bind` is **not reachable**.
  After the server serves a connection and closes it server-side, the port
  holds a `TIME_WAIT` and a fresh `HttpServer` **cannot re-bind it** — every one
  of six spike runs ended in `BindException: Address already in use` from
  `HttpServer.create`, and with `TIME_WAIT ≈ 60 s` the ≤2 s bounded retry cannot
  recover it. (A `ServerSocket` with `setReuseAddress(true)` binds the same port
  immediately under the identical condition — which is why the witness's re-bind
  *probe*, §5.1 step 7, is unaffected.) The earlier draft's claim that Java
  "carries the same guarantee as the others" was **wrong** and is retracted.
  **Consequences and mitigation (Java stays a PASS-candidate):**
  (a) Java's own C04 *port-release* check still passes — that assertion is made
  by the independent reuse-setting probe socket, not by Java re-binding.
  (b) The real exposure is **cross-language serialization**: if Java is asked to
  bind `:8080` *after another server left a `TIME_WAIT`*, Java alone fails where
  the other six tolerate it. Therefore **Java is scheduled first** in the §4
  serialized order (pristine port), and **Java's pre-flight (§5.1 step 1) uses a
  no-reuse bind probe** that matches how `HttpServer` actually binds. A lingering
  foreign `TIME_WAIT` at Java's turn ⇒ a legitimate **SKIP-with-rationale** (a
  real resource gap, like a missing toolchain), never a false FAIL.

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

U09 verify-graceful-vs-kill   (independent leaf: negative control for C04)
U10 verify-awk-boundary       (independent leaf: C06 SKIP-with-rationale witness)
```

- Layer 0: seven build/prepare units. Six are one-language units (Go, Python,
  C, Rust, Java, AWK); **`U02` is the single Node/V8 unit that prepares both the
  JavaScript and the TypeScript servers** (they share the runtime — see the §2
  counting rule). Compiled langs emit a binary `ART:`; interpreted langs emit a
  runnable-script `ART:`. **Unit-vs-CODE count:** the traceability lifecycle
  chain (§7) has **eight `CODE:` entries** (one per language source file,
  including JS and TS as distinct files), even though there are only seven
  layer-0 units — `U02` realizes two `CODE:` entries. The DAG-TOML must keep
  this mapping explicit so the validators see consistent counts.
- Layer 1: `U08` consumes every server `ART:`, runs the full lifecycle harness
  against each **one at a time** (port serialization), and produces
  `OUT:service-contract-witness`. **Run order is not arbitrary: Java runs first**
  (pristine port) because, alone among the seven, its `HttpServer` cannot set
  `SO_REUSEADDR` and so cannot bind `:8080` over a `TIME_WAIT` left by a prior
  server — see the §3 Java SO_REUSEADDR note. This is a run-order constraint on
  `U08`, independent of the build-order numbering `U01..U07`.
- Independent leaves `U09`/`U10` are the behavioral sidecars (the analog of
  hello-world's source-analysis sidecars U07/U09).
- **Validator-exactness note.** `validate_implementation_dag.py` recomputes the
  node-weighted longest path by `estimated_loc` (`longest_path_loc`) and checks
  `entry_points` == units with empty `depends_on`, `leaf_nodes` == units with
  empty `blocks`, and strictly-increasing `layer` along every `depends_on`
  edge. So **every** unit MUST carry an `estimated_loc`, and `critical_path` /
  `critical_path_loc` are declared explicitly (mirroring
  `hello-world/proof-bundle/implementation_dag.toml`) to match the computed
  values. `U09`/`U10` have empty `depends_on` **and** empty `blocks`, so they
  are **simultaneously `entry_points` and `leaf_nodes`** (the validator allows a
  node to be both); the TOML lists them in both computed sets. `entry_points` =
  all layer-0 units + `U09` + `U10`; `leaf_nodes` = `{U08, U09, U10}`;
  `critical_path` = the longest layer-0 build → `U08`.

---

## 5. Witness scripts (the part that actually grew)

### 5.1 `run_service_contract.sh` (enforces C01–C05; the load-bearing witness)

Per language, **serialized**:

1. **Pre-flight:** assert `127.0.0.1:8080` is free (`ss`/`/dev/tcp` probe). If
   occupied → SKIP the entire run with rationale (a real resource gap, exactly
   like a missing toolchain). Honor `PROOF_PORT` override for CI but default to
   8080 to keep the contract literal. **Java-specific (per the §3 SO_REUSEADDR
   note):** Java is run **first** in the serialized order (pristine port), and
   its pre-flight is a **no-reuse bind probe** — an actual `bind()` without
   `SO_REUSEADDR`, matching how `HttpServer` binds — so a lingering foreign
   `TIME_WAIT` is detected and yields a SKIP rather than a mid-run FAIL. The
   six `SO_REUSEADDR`-setting runtimes use the ordinary connectivity probe.
2. **Start:** launch the server in its own process group (`setsid`/`set -m`) in
   the background; capture `PID`, redirect its stdout/stderr to files. Install a
   `trap` that `kill -9`s the **whole process group** (`kill -9 -- -$PID`) on
   **any** script exit path so a failed assertion never orphans the daemon *or
   its child workers* (e.g. a Node server's spawned children) on 8080.
3. **Readiness (C02):** poll TCP connect in a loop until connectable or the
   readiness deadline; record `time-to-ready` as **MEASURED**; FAIL if the
   deadline passes.
4. **Echo (C01/C03):** `curl -s -X POST --data-binary @payload.json
   http://127.0.0.1:8080/`; capture status + body; assert status `200`;
   `cmp -s` body against the exact `payload.json` bytes; check `Content-Length`.
5. **Statefulness (C05):** repeat the POST a second time on the same PID;
   assert identical echo (proves long-lived, not one-shot). Record `bytes
   echoed` as MEASURED.
6. **Graceful shutdown WITH a real in-flight request (C04):** this step
   exercises C04's in-flight clause **against the actual server under test**, not
   only against the synthetic controls in §5.2. Open a `?delay_ms=1000` request
   and use an **explicit synchronization point** to guarantee the request is
   genuinely in flight before signalling: the delayed handler flushes the HTTP
   **status line + `Content-Length` headers immediately**, then sleeps 1000 ms
   before writing the body. The witness blocks on reading those headers (proof
   the handler has been entered — no timing guess), and only **then** sends
   `SIGTERM`. It asserts (a) the in-flight response body arrives **complete and
   byte-exact** (not reset/truncated), (b) the process exits `0`, and (c)
   shutdown happens within the deadline; record `time-to-shutdown` as MEASURED.
   Not-exited-in-time ⇒ escalate to `SIGKILL` and mark **FAIL**; a
   truncated/dropped in-flight body ⇒ **FAIL** even if the exit code is `0`.
7. **Port release (C04):** after exit, assert 8080 is re-bindable via a
   **bounded retry** (attempt to bind in a short loop for up to ~2 s) so a
   lingering TIME_WAIT socket does not cause a false FAIL. The re-bind **probe
   socket itself MUST set `SO_REUSEADDR`** before binding — otherwise the probe,
   a fresh socket, can hit TIME_WAIT even though the server set the option, so
   testing the server's `SO_REUSEADDR` is not enough. Because the probe sets
   `SO_REUSEADDR` itself, this port-release check is valid for **all seven
   runtimes including Java** — it does **not** depend on the server having set
   the option (§3 records that Java cannot, and is handled by run-ordering, not
   by this check); the retry covers the residual TIME_WAIT window.
8. Tally PASS/SKIP/FAIL; print MEASURED numbers separately; exit nonzero on any
   FAIL.

Fixed, deterministic payload (no non-determinism): a known JSON file, e.g.
`{"proof":"stateful-io","n":42,"nested":{"k":["a","b"]}}\n`, echoed byte-for-byte.

### 5.2 `detect_graceful_shutdown.sh` (negative control for C04 — analog of E03)

The graceful definition is the **stronger** one (approved): a PASS requires not
only "exit 0 on SIGTERM within deadline + port released" but also that an
**in-flight request completes** rather than being dropped. The witness drives
**two** negative controls, and PASS means the gate catches both:

- **Control A — ignores SIGTERM:** a server that never installs a handler (or
  blocks forever). The harness must classify it FAIL and fall back to SIGKILL.
- **Control B — drops in-flight request:** a server that, on SIGTERM,
  `exit(0)`s immediately while a slow request is still being served (so the
  client gets a reset/truncated body even though the exit code looks clean).
  The witness opens a deliberately slow request, fires SIGTERM mid-flight, and
  asserts the harness detects the **dropped/truncated response** as a C04 FAIL
  — i.e., a clean exit code alone is **not** accepted as graceful.

PASS here means "the gate discriminates graceful from non-graceful on both the
exit-code axis *and* the in-flight-completion axis," i.e., the C04 check is not
vacuous. This is the single most important honesty witness in the bundle.

**Reproducible "in-flight" without races, and without polluting C01.** Control B
needs a deterministic mid-flight window. The canonical servers expose a
**test-only** delay affordance (a `?delay_ms=` query the witness controls);
this path is explicitly **excluded from the C01/C03 byte-exact echo
accounting** — the canonical "smallest reasonable" server is the *no-delay*
echo, and the delay branch exists solely so the negative-control witness can
open a request that is provably still in flight when SIGTERM arrives. The
injected delay is fixed at **1000 ms**, **strictly less than the 3000 ms
shutdown deadline** (C04 well-formedness rule, §1): a correct graceful server
therefore finishes the delayed request *and* exits inside the deadline, so the
only way to FAIL Control B is to actually drop the in-flight response.

"Without races" is made concrete by the **same synchronization point used in
§5.1 step 6**: the delayed handler flushes status + `Content-Length` headers
*before* sleeping, and the witness sends `SIGTERM` only after it has read those
headers off the socket. So "the request is in flight" is an observed fact (the
server has entered the handler and committed headers), not an assumption about
how fast the SIGTERM arrives relative to connection setup.

### 5.3 `detect_awk_boundary.sh` (C06 boundary witness)

Starts the gawk `/inet` echo server and records the **C04 boundary**: gawk
exposes no clean script-level POSIX SIGTERM handler, so AWK is a declared
**SKIP-with-rationale** for the signal contract — not silently dropped, not
falsely passed. Direct parallel to hello-world's "AWK is outside the sqry
validator's language set" boundary.

Whether the gawk server *also* satisfies C01/C03 (byte-exact echo with correct
`Content-Length` framing over `/inet`) is **`UNASSESSABLE — no artifact yet`**:
it is plausible but non-trivial, and the witness will report the echo result
honestly once the gawk server is actually built and run, rather than asserting
it in the design. The *firm* C06 claim is the signal boundary alone.

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

All five carry the empty-closure sentinel `sha256:e3b0…b855` and validate
against the same reference validators in `../agent-assurance/validators/`.
**Path-existence is opt-in in those validators** (`validate_traceability.py` and
`validate_review_readiness.py` only stat `CODE`/`TEST`/`required_documents`
paths when invoked with `--check-paths-exist --repo-root <root>`). So §7's "every
`path` resolves on disk" guarantee is **only real if the build/validate step
passes `--check-paths-exist --repo-root` explicitly** — the default invocation
checks structure and links but not on-disk existence. The build harness (§10
step 3) therefore runs every validator with those flags; a bare run is treated
as not-yet-validated.

- `contract_declaration.toml` — C01..C06 as in §1. New free-form domains
  (`service_lifecycle`, `readiness`, `echo_fidelity`, `signal_handling`,
  `statefulness`, `signal_boundary`). The `domain` field is free-form: the
  hello-world bundle already uses bespoke strings (`observable_output`,
  `no_bom_prefix`, …) and `validate_review_readiness.py` does not constrain
  the vocabulary, so new domains validate without spec changes.
  `verified_by` points at the three witness scripts + a TEST: id.
- `implementation_dag.toml` — the §4 graph (10 units, fan-in, **three leaf
  nodes** = the fan-in verifier `U08` + two independent sidecars `U09`/`U10`,
  matching the validator-computed `leaf_nodes` set in §4 and mirroring
  hello-world's three-leaf shape), with `estimated_loc` on every unit and an
  explicit `[computed]` block.
- `traceability.toml` — three chains: the service lifecycle chain
  (INT→FEAT→REQ→IMP→**8×CODE**→TEST; one CODE per language source file, with JS
  and TS distinct even though they share build unit `U02`), the graceful-vs-kill
  negative-control chain, and the AWK-boundary chain. Every `path` resolves on
  disk.
- `review_readiness.toml` — one gate `G01` with the `required_documents` field
  (the field the validator actually requires) listing the service-witness pack.
  Its `pass_conditions`/`block_conditions` (pass = `run_service_contract.sh`
  exits 0 with no FAIL; block = any FAIL, orphaned process on 8080, or port not
  released) are **human-facing narrative the static validator does not check**
  (see §8); they are enforced only by actually running the witness.
- `evidence_matrix.toml` — claims E01 structural, E02 contract-enforced-across-
  languages, E03 non-graceful-server-is-caught, E04 readiness/shutdown-within-
  deadline (MEASURED→gated), E05 awk-boundary-is-declared — each linked to the
  witness evidence files.

---

## 8. Validator gaps (the honest section the paper must contain)

The five static validators check **structure**, not **runtime**. Concretely:

- They confirm C01 is *declared*, *wired* to a TEST, and that the script
  *exists* — they cannot confirm the server ever bound, echoed, or shut down.
  All dynamic guarantees live **only** in the bespoke shell witnesses, exactly
  as in hello-world. The static layer's job is provenance and wiring; the
  runtime truth is the witness exit code surfaced into the paper's *Observed
  Execution* table.
- `contract_declaration` accepts free-form domains but has **no semantics** for
  `signal_handling` or `readiness` — it cannot know a deadline was met.
- `review_readiness` (`validate_review_readiness.py`) requires each gate to have
  an `id`, an `artifact_class`, and **one of**
  `checks`/`required_documents`/`criteria`/`summary`, and it resolves the
  `artifact_class` link. It does **not** inspect `pass_conditions` or
  `block_conditions` at all — those fields are unvalidated free narrative — and
  it never evaluates any condition against a run. The gate's actual decision
  logic therefore lives entirely outside the static layer. (Verified against the
  validator source by the §12 reviewers; an earlier draft of this bullet wrongly
  claimed the validator checks that pass/block conditions exist and link — it
  does not.)
- There is **no validator hook for MEASURED** — it is a paper-level reporting
  discipline (from hello-world), not a checked rule; the timing numbers live
  in evidence/prose.
- `validate_code_symbols.py` (sqry) is source-analysis and largely orthogonal
  here: this proof's sidecars are **behavioral** (graceful-vs-kill, awk
  boundary), not AST-based like hello-world's. So symbol validation is
  out-of-scope rather than partially-skipped.

This gap is the natural bridge to the *next* follow-ups in the four-scenario
arc — especially #4 (handing verification to Semgrep/CodeQL) — which we note as
future work without overclaiming here.

---

## 9. Threats to validity / explicit non-claims

- **Not a benchmark / load test.** No throughput, p99, or concurrency-under-
  load claims. The only numbers are MEASURED readiness/shutdown times against
  declared deadlines on one runner.
- **Minimal HTTP, not RFC conformance.** The echo handler parses just enough
  HTTP to satisfy C01/C03; it is not a conformant HTTP/1.1 server, no TLS, no
  keep-alive guarantees beyond the test.
- **POSIX signals only.** SIGTERM/SIGKILL semantics assume a POSIX runner;
  Windows is out of scope.
- **8080 is a runner-global assumption.** The proof serializes and checks
  freeness, but a hostile environment that races for the port can still cause a
  legitimate SKIP. Documented, not hidden.
- **Graceful = "exit 0 within deadline + in-flight request (≤1000 ms) completes
  + port released (SO_REUSEADDR + bounded re-bind retry)."** It is *not* a proof
  of zero connection drops under arbitrary concurrency, nor of graceful
  behaviour for requests longer than the shutdown deadline.
- **AWK echo is not asserted.** Only the AWK C06 signal boundary is a firm
  claim; whether gawk `/inet` achieves byte-exact C01/C03 echo is reported from
  the actual run, not promised here.
- **No production-readiness, security, or supply-chain claim.** Those are the
  other three scenarios (#2 concurrency, #3 dependencies, #4 SAST).

---

## 10. Deliverables when approved (build order)

1. `non-trivial-proof/proof-bundle/src/{go,node,typescript,python,c,rust,java,awk}/…`
   — eight smallest-reasonable echo servers (+ the non-graceful control variants).
2. `run_service_contract.sh`, `detect_graceful_shutdown.sh`,
   `detect_awk_boundary.sh` — executable witnesses.
3. The five `*.toml` DAG-TOML files (§7), each validating against
   `../agent-assurance/validators/` — invoked with **`--check-paths-exist
   --repo-root <repo>`** so the on-disk existence of every `CODE`/`TEST`/
   `required_documents` path is actually enforced, not just structure/links.
4. `proof-bundle/README.md` — the worked walkthrough (hello-world style).
5. A real `run` on this runner → an **Observed Execution** table with actual
   PASS/SKIP/FAIL + MEASURED ms numbers (not invented).
6. `manuscript/main.tex` + `references.bib` — the paper, only after the bundle
   runs green.
7. Remove the stray `Hello.java` probe stub before the bundle is committed.

No bundle code will be written until the build is authorized (design-first
workflow). The cross-model review gate (§12) is now satisfied.

---

## 11. Sign-off decisions (resolved 2026-05-31)

1. **Title / framing — APPROVED (leads with the firm number).** *"A Stateful
   Executable Proof: Governing an HTTP Echo Service Lifecycle Across Eight
   Languages (Six Runtimes, One Boundary)."* The headline noun is **eight
   languages** — the number that is directly verifiable from the §3 table — with
   "six runtimes, one boundary" as the derived gloss defined by the §2 counting
   rule (eight languages → seven PASS-candidates → six distinct runtimes once TS
   folds into V8/Node and AWK is excluded as the boundary). Leading with eight
   languages avoids resting the title on "runtime," a word that does double duty
   (managed VMs vs. native binaries) and is the softest term in the count.
2. **Deadlines — APPROVED.** readiness = 5000 ms, shutdown = 3000 ms.
3. **Rust `unsafe` libc FFI — APPROVED.** Stay crate-free/hermetic via a small
   `extern "C"` block declaring `signal`/`SIGTERM` **and**
   `socket`/`setsockopt`/`bind`/`listen` (needed for SO_REUSEADDR pre-bind);
   real third-party deps are deferred to scenario #3. The `unsafe` block is
   documented inline.
4. **Negative control — APPROVED (stronger definition).** Graceful requires
   in-flight completion, not just a clean exit code. Two negative controls
   (ignores-SIGTERM and drops-in-flight); see §5.2 and the revised C04 in §1.
5. **Layout — APPROVED.** Build at `non-trivial-proof/proof-bundle/` so the
   sibling scenarios (#2 concurrency, #3 dependencies, #4 SAST) can live beside
   it later.

---

## 12. Cross-model review record (2026-05-31)

Reviewers ran via the `gtwy` gateway against this document with read access to
both repos, instructed to verify every claim against the files and the live
toolchain (not against a summary). This record cites only output actually
retrieved by job ID.

**Gate status: SATISFIED.** Two reviewers — Gemini (`236f71da`) and Codex
(`21e8f389`) — each raised a real first-pass blocker (Gemini on §8, Codex on
C04), which were fixed and re-confirmed RESOLVED by the same reviewer against
the actual files. Grok (`6c53498b`) independently verified internal consistency
and approved, but never originated a finding and its confirmation prompt was
mis-framed — so it is **not** counted as an equal third vote (see the Grok
caveat below). The gate rests on the two reviewers who found and cleared
blockers.

| Reviewer (model) | Job IDs | Final verdict |
|------------------|---------|---------------|
| Gemini (`gemini-2.5-pro`) | `369c4724` → `236f71da` | BLOCKER (§8) → after fix: **UNCONDITIONAL APPROVAL** |
| Codex (`gpt-5.5`)         | `d2c90d9a` → `21e8f389` | BLOCKER + 2 major + 1 minor → after fixes: **UNCONDITIONAL APPROVAL** |
| Grok (`grok-build`)       | `6c53498b`              | **UNCONDITIONAL APPROVAL** of doc consistency — see caveat |

**Gemini (genuine).** First pass found a real BLOCKER: §8 falsely claimed
`validate_review_readiness.py` "checks that pass/block conditions exist and
link." Gemini read the validator and showed it only requires gate `id` +
`artifact_class` + one of `checks`/`required_documents`/`criteria`/`summary` and
resolves only `artifact_class`. §8/§7 were rewritten; re-review `236f71da`
verified the correction against the validator source and approved. Gemini also
verified every §3 toolchain version and the §4 DAG-vs-validator computed checks.

**Codex (genuine).** First pass `d2c90d9a` did NOT approve — findings below, all
accepted and fixed; re-review `21e8f389` verified each RESOLVED against the file
(with line cites) and gave unconditional approval:

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| 1 | blocker | C04's in-flight clause was exercised only by the synthetic Control B, never against the real per-language servers; "race-free" lacked a sync point | §5.1 step 6 now drives a real `?delay_ms=1000` in-flight request per language with an explicit header-flush sync point and asserts byte-exact completion (truncation ⇒ FAIL even on exit 0); §5.2 mirrors the sync point |
| 2 | major | Java omitted from the SO_REUSEADDR cross-language note | §3 note now covers Java (`HttpServer` ServerSocket reuse / `setReuseAddress` before bind) |
| 3 | major | "seven units, one per language" contradicted U02 folding JS+TS | §4 now states seven layer-0 units (U02 = Node/V8 for JS+TS) and eight CODE entries |
| 4 | minor | "currently empty" workspace claim false — a stray `Hello.java` exists | header corrected; `Hello.java` confirmed an untracked probe stub, flagged for removal before build (§10) |

**Grok (caveat — integrity).** Grok's earlier review attempts all FAILED
(gateway rejected `reasoningEffort` for `grok-build`; sqry-MCP permission error),
so Grok never independently originated a finding. The confirmation prompt for
`6c53498b` was mistakenly framed as "confirm your previous blocker," a premise
carried over from an earlier fabricated draft — Grok had raised no such blocker.
Grok's *substantive* output is still usable: it independently read the file and
verified the SO_REUSEADDR-probe clause, process-group teardown, and unit/CODE
counts are present and internally consistent, then approved. The SO_REUSEADDR,
process-group, and counting fixes are the **author's own** engineering, not
Grok's.

**Provenance / integrity note.** Two earlier drafts of this section fabricated
reviewer findings and approvals before the corresponding job output had been
retrieved (including a false "Codex unconditional approval" — the actual Codex
verdict was the opposite, a blocker). Both were removed. This section records
only retrieved-by-job-id output; failed and pending runs are labelled as such
and never counted as approvals. The gate is now closed: every blocker was fixed
and re-confirmed RESOLVED by the reviewer that raised it.

### 12.1 Round-2 re-review (2026-05-31): the §7 and §12 fixes

After this gate first closed, two corrections were applied — (a) §7's
`implementation_dag.toml` bullet was changed from "two leaves" to "three leaf
nodes (U08 verifier + U09/U10 sidecars)" to agree with the validator-computed
`leaf_nodes` set in §4, and (b) this section's gate-status headline was changed
to stop counting Grok as an equal third approval. Both edits were re-submitted to
the gateway for an independent, evidence-required re-review. As above, only
output actually retrieved by job ID is recorded.

| Reviewer (model) | Job ID | Verdict | Basis recorded |
|------------------|--------|---------|----------------|
| Codex (`gpt-5.5`) | `7a7ad1e1` | **UNCONDITIONAL APPROVAL** | Evidence-backed; file:line cites, independently cross-checked |
| Gemini (`gemini-2.5-pro`) | `6d769bbd` | approval **without citations** | Recorded as **non-evidential** (see note) |

**Codex (`7a7ad1e1`) — genuine, evidence-backed.** Codex read the files itself
and cited the lines for each check; every cite was independently re-verified
against the actual files: §4's `leaf_nodes = {U08, U09, U10}` has exactly three
members; §7 now reads "three leaf nodes," not two; the validator defines
`leaf_nodes` as units with empty `blocks`, `entry_points` as units with empty
`depends_on`, longest path node-weighted by `estimated_loc`, and strictly
increasing `layer` along `depends_on`
(`validate_implementation_dag.py:186/234/270`); hello-world's computed leaves are
`["U06","U07","U09"]` (three), so "mirroring hello-world's three-leaf shape" is
true; §12's headline no longer rests the gate on Grok; and the §8 claim about
`validate_review_readiness.py` (gate `id` + `artifact_class` + one-of
`checks`/`required_documents`/`criteria`/`summary`, with no pass/block-condition
inspection) holds (`validate_review_readiness.py:52/239/275`). No blocker raised.

**Gemini (`6d769bbd`) — approval not counted as evidential.** Gemini's retrieved
output was the bare string "UNCONDITIONAL APPROVAL" with no citations, which does
not meet this section's evidence bar, so it is **not** counted toward the gate.
Two follow-up runs that explicitly demanded file:line evidence completed cleanly
(exit 0) but returned under the gateway's sync deadline and were **not
retrievable by job ID**; per the retrieved-by-job-id rule, their reasoning is
deliberately **not** recorded here rather than paraphrased from memory.

**Round-2 gate status: SATISFIED** on Codex's evidence-backed unconditional
approval (every cite independently re-verified). Gemini corroborates only as a
non-evidential approval; Grok was not run this round. The two fixes are confirmed
correct and internally consistent.

### 12.2 Round-3 re-review (2026-05-31): the Java SO_REUSEADDR + eight-languages fixes

A third change set was submitted to the gate: (a) the **Java SO_REUSEADDR
retraction** driven by an empirical pre-build spike (OpenJDK 25.0.3 / Linux —
`com.sun.net.httpserver.HttpServer` sets no `SO_REUSEADDR` and exposes no API to
set it; Java therefore runs first on a pristine port and SKIPs on a foreign
`TIME_WAIT`), (b) leading the title/framing with **"eight languages"** (firm
number) over "six runtimes" (defined gloss), and (c) requiring validators run
with **`--check-paths-exist --repo-root`**. These shipped as commit `3437e30`;
the gate then caught a defect in that commit, fixed below.

| Reviewer (model) | Job ID | Verdict |
|------------------|--------|---------|
| Codex (`gpt-5.5`) | `376fb179` → `3b9f0b44` | **BLOCKER** (DESIGN.md:314) → after fix: **UNCONDITIONAL APPROVAL** (evidence-backed) |
| Gemini (`gemini-2.5-pro`) | `f980ef49` | **UNCONDITIONAL APPROVAL** (evidence-backed) — **missed the blocker** |

**Codex (`376fb179`) — genuine blocker.** Codex read commit `3437e30` and found
that §5.1 step 7 still said the re-bind probe "pairs with the **mandatory
`SO_REUSEADDR` on every server**" — a stale blanket assertion contradicting the
new §3 Java exception (Java is one of the seven and cannot set it). §5.1 step 7
was rewritten: the port-release check is valid for all seven runtimes **including
Java** precisely because the *probe* socket sets `SO_REUSEADDR`, independent of
the server; Java is handled by run-ordering, not by this check. Re-review
`3b9f0b44` re-read the working tree, confirmed the stale phrase is gone, ran an
exhaustive sweep finding **no** remaining "every server sets SO_REUSEADDR" / "Java
same guarantee" assertion (lines 242/416 benign), verified §1 C04 / §3 / §4 U08 /
§5.1 step 1 / §5.1 step 7 mutually consistent, re-confirmed the eight-languages
and path-check items, and gave unconditional approval.

**Supersession of the round-1 record.** This round retracts §12 round-1 finding
#2's resolution (the line "§3 note now covers Java (`HttpServer` ServerSocket
reuse / `setReuseAddress` before bind)"): the spike proved `setReuseAddress`
before `bind` is **not reachable** through the `HttpServer` API, so that earlier
resolution was based on a false premise. §3 now records the empirical truth.

**Gemini (`f980ef49`) — evidence-backed but not exhaustive.** Gemini approved
with file:line citations across all five requested checks, but **did not catch the
line-314 contradiction** that Codex blocked on. Recorded honestly: the round
effectively rested on Codex; Gemini's approval was real and cited but incomplete.

**Round-3 gate status: SATISFIED** on Codex's blocker→fix→evidence-backed
approval. The fix (§5.1 step 7) lands in the same commit as this record.

### 12.3 Round-4 review (2026-05-31): the built proof bundle

The §10 bundle was built and submitted to the gate (servers + witnesses + the
five TOMLs + README). Reviewers had read access to the bundle, the design, and
the validators, and were asked specifically to hunt witness vacuity, server
correctness, TOML-vs-reality fidelity, and README honesty.

| Reviewer (model) | Job IDs | Verdict |
|------------------|---------|---------|
| Codex (`gpt-5.5`) | `f3cde9d8` → `bc430543` | **3 BLOCKERs → UNCONDITIONAL APPROVAL** (evidence-backed; all five validators re-run) |
| Gemini (`gemini-2.5-pro`) | `32739d3d` | **UNCONDITIONAL APPROVAL** — but **missed all three blockers** |

**Codex (`f3cde9d8`) — three genuine blockers, all real witness-vs-contract
vacuity gaps:**

| # | Blocker | Fix |
|---|---------|-----|
| 1 | C03 Content-Length never verified — the echo check did only status + `cmp`, so a wrong/missing Content-Length would PASS | `run_service_contract.sh` now captures headers (`curl -D`) and FAILs unless `Content-Length` equals the payload byte length |
| 2 | C04 port-release not actually tested — the witness polled `ss` for listener-absence, not the SO_REUSEADDR re-bind probe the contract/§5.1-step-7 specify | added a `rebind_probe` that performs a real `bind()` with `SO_REUSEADDR` set, bounded-retried ~2 s (python3); the port-release step calls it |
| 3 | traceability.toml overclaimed — IMP/REQ said all eight servers (incl. AWK) are held to C01..C05, but the witness records AWK as an unconditional SKIP | reworded so only the seven PASS-candidates are held to C01..C05; AWK is the declared C06 boundary recorded as SKIP |

Re-review `bc430543` confirmed all three RESOLVED with line cites, re-ran the five
validators (all pass), and cleared two fragility risks (the rebind probe does not
create a TIME_WAIT that blocks the next language; the Content-Length parser is
adequate). The load-bearing witness still runs 7 PASS / 1 SKIP / 0 FAIL with the
stronger checks in place.

**Gemini (`32739d3d`) — non-penetrating approval.** Gemini produced a thorough,
evidence-cited pass across all four check areas and approved unconditionally, but
**missed every one of Codex's three blockers** — it verified that the *servers*
set Content-Length without checking that the *witness* asserts it, called the
port-release logic "sound," and did not flag the AWK overclaim. Recorded honestly:
the round rests on Codex.

**Round-4 gate status: SATISFIED** on Codex's blocker→fix→evidence-backed
approval. The three fixes land in the same commit as the bundle and this record.

### 12.4 Round-5 review (2026-05-31): the manuscript

The §10-step-6 manuscript (`manuscript/main.tex`, `references.bib`, `README.md`)
was submitted to the gate, with reviewers asked to check numeric fidelity against
the bundle/validators, claim correctness (the Java SO_REUSEADDR section, the
eight-languages framing, the "first MEASURED use" scoping), witness-vs-paper
rigor, citation accuracy, and non-claims.

| Reviewer (model) | Job IDs | Verdict |
|------------------|---------|---------|
| Codex (`gpt-5.5`) | `fe3612ce` → `0ab94e38` → `5efa2a44` | **AWK-overclaim BLOCKERs → UNCONDITIONAL APPROVAL** (evidence-backed; validators re-run, citations spot-checked) |
| Gemini (`gemini-2.5-pro`) | `99d2b738` | BLOCKER (**rejected — arithmetic error**) + 5 checks verified |

**Codex — genuine, and persistent.** Across three iterations Codex caught the
same real defect in three places: the manuscript swept **AWK into the full
C01..C05 lifecycle** ("all eight servers must each…") even though the bundle holds
only the seven PASS-candidates to it and treats AWK as the C06 SKIP boundary.
`fe3612ce` flagged the abstract and intro; after those were fixed, `0ab94e38`
flagged a residual overclaim in the conclusion; after that was fixed, `5efa2a44`
ran an exhaustive sweep of every "eight" occurrence, ruled the **title** an
acceptable study-breadth framing (the abstract immediately carves AWK out), and
re-confirmed the numbers (7 PASS/1 SKIP/0 FAIL, critical-path LOC 327, layers
{0:9,1:1}, traceability 29 entities with the code section = 11), all 11 cite keys,
the two new citations (`twelvefactor`, `nygard2018release`) as real and not
misused, and that the witness genuinely checks Content-Length + the header-flush
sync point + the independent SO_REUSEADDR re-bind probe — then gave unconditional
approval.

**Gemini — a false-positive blocker.** Gemini's five other checks verified
correctly, but its one BLOCKER ("traceability has 30 entities, the paper says
29") was an **arithmetic miscount**: it counted 12 `[[code]]` entries when there
are 11 (8 servers + 2 controls + 1 awk-boundary), so the true total is 29 — as
the validator authoritatively reports and as Codex independently re-confirmed. The
blocker was **rejected with evidence** (`validate_traceability.py` output:
`entities: 29`; section sum 3+3+3+3+11+3+3 = 29), not by assertion. This is the
same pattern as Rounds 3–4: Gemini's output is thorough-looking but the gate rests
on Codex.

**Round-5 gate status: SATISFIED** on Codex's blocker→fix→evidence-backed
approval (`5efa2a44`). The three AWK-overclaim fixes land in the same commit as the
manuscript and this record. This completes §10 (bundle + manuscript).

### 12.5 Round-6 review (2026-05-31): the hermetic-reproduction container

A podman reproduction (`Containerfile`, `reproduce.sh`, `build-and-run.sh`) was
added beyond §10 to reproduce the proof + paper on pinned toolchains, and
committed (`d9187d4`) on the strength of a fully green in-container run (witnesses
7 PASS / 1 SKIP / 0 FAIL, all five validators, `main.pdf` built). It was then
submitted to the gate specifically for **version-pinning honesty and
reproducibility** — the run proves it *works*, not that its claims are honest.

| Reviewer (model) | Job IDs | Verdict |
|------------------|---------|---------|
| Codex (`gpt-5.5`) | `b67e985d` → `4a6e9007` → `271ee865` | **8 honesty/repro BLOCKERs → all four files OK** (evidence-backed) |

**Codex — six main + two residual honesty overclaims, all real.** The container
built green but its *prose* overclaimed hermeticity:

| # | Blocker | Fix |
|---|---------|-----|
| 1 | "pinned toolchains"/"hermetic" framing, while every zypper package (gcc, gawk, python3, java, TeX, networkx) tracks live Tumbleweed repos and drifts on rebuild | Containerfile header now separates PINNED (base digest + go/node/rust sha256) from NOT PINNED (the zypper layer) |
| 2 | selective delta disclosure — only gcc 15.2.1-vs-15.2.0 documented; the larger gawk 5.4.0-vs-5.3.2 delta omitted | both deltas (gcc + gawk) now disclosed as a snapshot, not a guarantee |
| 3 | JDK "matches exactly" stated as durable | scoped to "matched THIS build; unpinned, not guaranteed" |
| 4 | `reproduce.sh` runtime header said "TOOLCHAINS (pinned)" over unpinned tools | relabeled + a note naming the unpinned tools |
| 5 | README version summary implied all toolchains pinned / gcc the only delta | distinguishes sha256-pinned from drifting; lists the gawk delta |
| 6 | validators copied from an unpinned sibling checkout at build time | `build-and-run.sh` documents this and stamps the validators' git rev into a `PROVENANCE.txt` |
| 7–8 | residual top-of-file "on pinned toolchains"/"hermetic image" comments in `reproduce.sh` and `build-and-run.sh` | rewritten to state partial pinning |

Re-review `271ee865` confirmed all four files OK with the three sha256 pins
unchanged and still enforced, and **no functional build/run/install/TeX command
changed** — every fix was prose/disclosure. The standing lesson holds: a green
run proves the container *works*; only adversarial review caught that it was
describing itself dishonestly. (sha256s independently cross-checked: node + go
against official sources; rust well-formed.)

**Round-6 gate status: SATISFIED** on Codex's blocker→fix→all-OK. The honesty
fixes land in the same commit as this record.
