# Ground-Truth Measurements — Stateful I/O Proof (from-scratch rebuild)

**Date:** 2026-06-01. **Runner:** Linux, OpenJDK build `25.0.3+9-suse`.
**Discipline:** measure-first. Nothing in DESIGN.md / the manuscript may assert a
runtime fact that is not measured here (or measured by the Phase-2 witness run).
This record exists because the previous set asserted a Java SO_REUSEADDR finding
that direct measurement proved **false** (it had been flipped twice and rested on
an un-rerun spike). Old set is recoverable at git branch
`pre-rewrite-nontrivial-2026-06-01`.

## Toolchain (measured 2026-06-01, not trusted from prior notes)

| Tool | Version | Notes |
|------|---------|-------|
| go | 1.26.3 | |
| node | v24.15.0 | `--experimental-strip-types` available (TS path) |
| python3 | 3.13.13 | |
| cc (gcc) | 15.2.0 (SUSE) | |
| rustc | 1.90.0 | |
| java | 25.0.3 (`25.0.3+9-suse`) | runtime only — **`javac` ABSENT** (source-launch) |
| gawk | 5.3.2 | `/inet` TCP support present |
| — | — | **`tsc` ABSENT**; port 8080 free; `tcp_fin_timeout` = 60 |

## M1 — Java `com.sun.net.httpserver.HttpServer`: the prior finding is FALSE

The previous set claimed `HttpServer` "sets no SO_REUSEADDR and cannot re-bind a
`TIME_WAIT`'d port," forcing Java-first ordering + a no-reuse pre-flight. Direct
measurement on this runner overturns it. The committed spike (`ReuseSpike.java`),
6/6 runs, already shows `HttpServer.create rebind: OK` over a live `TIME_WAIT`.

**Behavior matrix** — *can the same port be re-bound immediately after
`HttpServer.stop()`?* (6 trials each, fresh ports, no timing slack):

| HttpServer state before `stop(0)` | rebind via `ServerSocket(reuse)` | rebind via `HttpServer.create` |
|---|---|---|
| **`start()`ed** | **6/6 OK** | **6/6 OK** |
| **never `start()`ed** | **0/6** (port leaked) | **0/6** (port leaked) |
| **`start()`ed + served a real request** (the real lifecycle) | **6/6 OK** | **6/6 OK** |

**Root cause of the old false finding (deterministic, 6/6):** `HttpServer.create()`
binds the port; calling `stop()` on a server that was **never `start()`ed does not
release the listener socket** (the old spike's `httpBind()` did exactly
`create()` + `stop(0)` with no `start()`). The leaked listener — not any
SO_REUSEADDR deficiency — is what made subsequent binds fail. `HttpServer` in fact
tolerates a prior `TIME_WAIT` (its NIO `ServerSocketChannel` has SO_REUSEADDR on by
default), and a properly-`start()`ed server releases its port immediately on
`stop(0)`, even after serving a connection.

**Design implications:**
- **No Java special-casing.** Drop Java-first run ordering and the no-reuse
  pre-flight probe. Java behaves like the other runtimes in the real lifecycle.
- **Keeper finding (true, deterministic, defensible):** a never-`start()`ed
  `HttpServer.stop()` leaks its bound listener. This is an in-process API footgun.
  It does **not** affect the proof: (a) the real server calls `start()`, and
  (b) port release in the proof is **cross-process** — the server exits on SIGTERM
  and the OS reclaims the socket regardless. Worth a corrected, re-pointed
  reproducer + an honest "we mis-measured; the reproducer caught it" note.

## M2 — AWK (gawk 5.3.2) `/inet`

- `/inet` TCP listener support is present.
- **SIGTERM → exit 143** (128+15), **no script-level trap** ran (2/2). gawk exposes
  no clean POSIX SIGTERM handler at script level → **firm C06 boundary**
  (SKIP-with-rationale for the signal contract), same shape as before.
- Byte-exact HTTP echo with correct `Content-Length` framing over `/inet` is
  **non-trivial** — a naive `RS/ORS` echo attempt returned no response. Whether a
  correct gawk echo server is buildable is a **Phase-2 build measurement**, not a
  design-time claim. Until a working artifact runs, AWK echo (C01/C03) stays
  `UNASSESSABLE`; only the C06 signal boundary is firm.

## M3 — Design principle confirmed by M1

Port release in this proof is verified **cross-process** by an independent re-bind
probe that sets SO_REUSEADDR itself + a bounded `TIME_WAIT` retry. Therefore the
individual server's own SO_REUSEADDR setting is **not load-bearing** for the C04
port-release check. Over-focusing on per-server SO_REUSEADDR is what produced the
Java mis-finding (an in-process API quirk treated as if it governed a cross-process
proof). The witness's own probe is the authority.

## Deferred to Phase 2 (will be MEASURED by the witness run, never pre-asserted)

Full per-runtime lifecycle — bind, byte-exact echo (≥2 requests), in-flight
completion on SIGTERM, exit 0, port re-bindable — for Go, Node(JS), TypeScript,
Python, C, Rust, Java. These are established by running the actual witness against
the freshly-built servers and recording the Observed Execution table, not by
asserting "X sets SO_REUSEADDR by default" in the design.
