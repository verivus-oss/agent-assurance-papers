# Differential behavioural-agreement — the CDA methodology applied to the echo proof

**Date:** 2026-06-01. Harness: `proof-bundle/differential_echo.py`.

## The methodology transfer

The code-derivation-assay (`code-derivation-assay/treesitter-spike/`) found that the
load-bearing derivation signal across an AI rewrite was **behavioural**: run several
implementations of one contract on a shared input corpus and compare their *decisions*, with a
**calibration control** proving the test is non-vacuous. The non-trivial-proof is the dual
situation — *seven* implementations (C, Go, Java, Node, Python, Rust, TypeScript) of **one** HTTP
echo contract. So the same methodology applies directly: instead of detecting derivation by
*agreement*, we strengthen the proof by demonstrating cross-implementation **behavioural
equivalence** under adversarial inputs — and we prove the test can fail with a broken control.

This closes a real gap. The §10 contract witness (`run_service_contract.sh`) checks each server
against **one fixed payload**. That cannot reveal where implementations *diverge* on edge cases —
exactly where hand-rolled HTTP parsers (C, Rust) tend to differ.

## The harness

`differential_echo.py`: builds/launches each echo server in turn (serialised on one port, as the
witness does), sends a corpus of **adversarial** request bodies, and records `(status, body)` per
server. A faithful echo must return `200` with `body == request` for **every** input. Divergence
= a real bug in one implementation the others do not share.

**Corpus (10):** `simple-json`, `empty`, `no-trailing-newline`, `nul-bytes` (full 0–255 byte
range), `utf8-multibyte`, `embedded-crlf-http` (a fake HTTP request as the body), `long-line-100k`,
`large-1mib`, `whitespace-only`, `json-with-nul`.

**Calibration control (`zctrl-broken`):** a deliberately-unfaithful echo that truncates the body
to 16 bytes. If the harness does not flag it, the differential test is vacuous.

## Result

```
                 c   go  java node pyth rust   ts  zctrl   real?
simple-json      ok  ok   ok   ok   ok   ok   ok  body!   ALL ok
nul-bytes        ok  ok   ok   ok   ok   ok   ok  body!   ALL ok
large-1mib       ok  ok   ok   ok   ok   ok   ok  body!   ALL ok
embedded-crlf    ok  ok   ok   ok   ok   ok   ok  body!   ALL ok
... (10 requests total)
```

- **Calibration: control flagged on 6/10 requests** (every body > 16 bytes) → the harness
  **demonstrably detects divergence** (NON-VACUOUS).
- **0 divergences among the 7 real servers** — all return byte-identical `200` echoes on every
  adversarial input, including full-byte-range NUL data, 1 MiB bodies, and embedded fake-HTTP.

## What this adds to the proof

The proof previously asserted each server passes a single-payload contract. The differential
channel upgrades that to a **calibrated, multi-implementation behavioural-equivalence** result:
seven independent implementations are byte-exact-equivalent across an adversarial corpus, and the
equivalence test is proven able to fail (the broken control is caught 6/10). This is the same
discipline the CDA behavioural channel uses (shared corpus + accuracy/divergence control), applied
to strengthen rather than to detect — and it is the natural multi-implementation generalisation of
the §10 witness.

## Honest limitations

- Echo is a near-identity contract, so behavioural equivalence is expected; the value is in
  exercising the edge cases (binary, large, framing) the single payload skips and proving the
  servers genuinely agree there. AWK is excluded (the declared C06 boundary).
- The corpus is hand-chosen, not exhaustive; a fuzzing front-end (random bodies + property
  oracle `body_out == body_in`) would extend coverage. The harness already provides the oracle.
- Differential agreement proves the implementations *agree*, not that the shared decision is
  *correct* against an external spec — for echo the oracle (`out == in`) is the spec, so here they
  coincide.
