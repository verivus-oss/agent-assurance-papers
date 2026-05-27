# Proof: Hello, world! across multiple languages

A worked end-to-end example showing the DAG-TOML spec governing a
single observable contract across **Rust, Go, C, Java, TypeScript,
and AWK**.
Read in order, it walks from intent to enforceable byte-level
guarantee. Every TOML file in this directory validates against the
reference validators shipped with the spec.

The example is intentionally as small as a real spec application can
get: six smallest-possible Hello-World programs, one normative
runtime requirement, one cross-language run harness, and two sidecar
source-analysis witnesses for rewrite detection. Everything bigger is
a matter of scale, not new spec mechanics.

```
hello-world/proof-bundle/
├── README.md                       (this file)
├── implementation_dag.toml         (the build graph)
├── traceability.toml               (INT → REQ → IMP → CODE×6 plus rewrite witnesses)
├── contract_declaration.toml       (C01..C06 observable/source contracts)
├── review_readiness.toml           (the single gate keyed to the witness pack)
├── evidence_matrix.toml            (claims linked to evidence files)
├── run_all.sh                      (executable witness for C01)
├── detect_semantic_rewrite.sh      (sqry witness for AST-level rewrite detection)
├── detect_awk_rewrite.sh           (AWK witness for source-profile detection)
└── src/
    ├── rust/hello.rs
    ├── go/hello.go
    ├── go_convoluted/hello.go
    ├── c/hello.c
    ├── java/Hello.java
    ├── awk/hello.awk
    ├── awk_convoluted/hello.awk
    └── typescript/hello.ts
```

## What the proof actually proves

The contract is one paragraph (`contract_declaration.toml` C01):

> Each implementation MUST write the exact UTF-8 byte sequence
> `Hello, world!\n` (14 bytes: H e l l o COMMA SPACE w o r l d
> EXCLAMATION LF) to stdout, write zero bytes to stderr, and exit
> with code 0.

The six canonical source files under `src/` each satisfy that
contract using their language's smallest-possible program. The run harness
`run_all.sh` enforces the contract by building and executing each
one, then comparing stdout byte-for-byte, asserting stderr is empty,
and asserting exit code is zero.

Running locally (PASS / SKIP / FAIL per language):

```
$ bash hello-world/proof-bundle/run_all.sh
proof-hello-world: enforcing contract_declaration.toml C01 on each language

  PASS  rust       stdout=$'Hello, world!\n' exit=0 stderr=empty
  PASS  go         stdout=$'Hello, world!\n' exit=0 stderr=empty
  PASS  c          stdout=$'Hello, world!\n' exit=0 stderr=empty
  SKIP  java       javac/java not on PATH
  PASS  typescript stdout=$'Hello, world!\n' exit=0 stderr=empty
  PASS  awk        stdout=$'Hello, world!\n' exit=0 stderr=empty

summary: 5 pass, 1 skip, 0 fail
```

A missing toolchain downgrades that language to SKIP (the test
cannot be performed on this runner). Any divergence between the
captured stdout / stderr / exit code and the contract is a hard
FAIL.

## Semantic-AST rewrite witness

The folder also contains one deliberately convoluted Go rewrite at
`src/go_convoluted/hello.go`. It avoids the contiguous source literal
`Hello, world!` by assembling the bytes indirectly, then calling
`fmt.Println` through a helper. That defeats a simple text search for
the literal, but it does not hide the semantic structure of the source:
sqry still resolves the function symbols `concealedBytes`,
`renderLine`, `emit`, and `main` from the parsed Go AST, plus the
caller edge from `main` to `renderLine` and the `fmt` import edge.

The witness script checks both sides of that claim:

```bash
$ bash hello-world/proof-bundle/detect_semantic_rewrite.sh
proof-hello-world: semantic AST rewrite witness

  PASS  plain greeting literal is absent from source text
  PASS  convoluted implementation still satisfies CONTRACT C01
  PASS  sqry resolved AST function symbol: concealedBytes
  PASS  sqry resolved AST function symbol: renderLine
  PASS  sqry resolved AST function symbol: emit
  PASS  sqry resolved AST function symbol: main
  PASS  sqry resolved caller edge: main -> renderLine
  PASS  sqry resolved import edge: fmt

summary: 8 pass, 0 skip, 0 fail
```

This is intentionally not a claim that AST tooling can infer every
semantic property from arbitrary obfuscated code. It is a precise
detectability claim: byte construction and helper indirection can hide
intent from token-level review, but declared code symbols and simple
graph edges remain machine-checkable through a parser.

## AWK rewrite witness

AWK is not covered by the sqry symbol validator in this repository, so
the AWK rewrite witness makes a different, narrower claim. It tests
whether the spec can still define and check an intent/similarity
surface for an unsupported language.

The fixture at `src/awk_convoluted/hello.awk` avoids the contiguous
source literal `Hello, world!` by storing decimal character codes, then
expanding them through a `render` function using `split`, a `for` loop,
and `sprintf("%c", ...)`.

The C06 contract declares two levels of profile. The shared intent
profile says the canonical and rewritten AWK implementations both use a
`BEGIN` entry point and print to stdout. The rewrite source profile says
the indirect version must expose `render`, `split`, a loop, and
`sprintf("%c", ...)`. The witness script checks both levels:

```bash
$ bash hello-world/proof-bundle/detect_awk_rewrite.sh
proof-hello-world: AWK rewrite detection witness

  PASS  plain greeting literal is absent from AWK rewrite source
  PASS  contract_declaration.toml declares C06 and its witness
  PASS  canonical AWK implementation satisfies CONTRACT C01
  PASS  AWK rewrite still satisfies CONTRACT C01
  PASS  canonical and rewritten AWK share the declared intent profile
  PASS  AWK static source profile matches C06

summary: 6 pass, 0 skip, 0 fail
```

This is not a general AWK AST-equivalence proof. It is a spec-backed
intent/profile proof: if a submitted AWK rewrite claims this C06 shape,
the witness can deterministically confirm whether the shared intent
profile and rewrite-specific source profile are present, even without
current sqry support for AWK.

## How each spec artifact maps to the proof

| DAG-TOML file | What it commits the proof to |
|---|---|
| `implementation_dag.toml` | The build graph: six layer-0 build/prepare units (one per C01 implementation) fan into a single layer-1 `verify-contract-c01` unit, with additional independent Go AST and AWK source-profile rewrite witnesses. `blocks` is the exact inverse of `depends_on`; the contract critical path runs from `U05` through `U06`. |
| `traceability.toml` | The C01 chain (`INT:` → `REQ:` → `IMP:` → six `CODE:` entries → `TEST:`) plus separate chains for the Go semantic-AST and AWK source-profile rewrite witnesses. |
| `contract_declaration.toml` | C01 declares the 14-byte stdout + exit-code semantics; C02..C04 declare three narrowings (locale-independent encoding, no ANSI escapes, no UTF-8 BOM prefix) that depend on C01; C05 declares the Go AST-level detectability boundary; C06 declares the AWK source-profile detectability boundary. |
| `review_readiness.toml` | A single G01 gate keyed to the contract-witness pack. Pass conditions require all per-language outcomes are PASS or SKIP; block conditions name FAIL. |
| `evidence_matrix.toml` | Five claims (`structurally_complete_pack`, `contract_enforced_across_all_languages`, `divergent_implementation_would_fail`, `semantic_ast_rewrite_detectable`, `awk_rewrite_source_profile_detectable`) backed by seven evidence entries; the M01..M10 matrix links them. |

The cross-reference rules from `spec.md §5` apply throughout:

- Every `REQ:` referenced from `[[implementations]]` or `[[tests]]`
  is declared in `[[requirements]]`.
- Every `consumes` entry under `[units.U06]` matches a `produces`
  entry on one of the six build/prepare units.
- Every `[[code]].path` exists on disk.
- Every `[[contracts]].verified_by` entry is either an entity-typed
  `TEST:` id or a free-form path (per the dual-form
  `verified_by` rule in `core/ontology.toml`).

## How to validate locally

```bash
# Spec validators
python3 validators/validate_implementation_dag.py \
  hello-world/proof-bundle/implementation_dag.toml

python3 validators/validate_traceability.py \
  hello-world/proof-bundle/traceability.toml \
  --repo-root . --check-paths-exist

python3 validators/validate_review_readiness.py \
  hello-world/proof-bundle/review_readiness.toml
python3 validators/validate_review_readiness.py \
  hello-world/proof-bundle/contract_declaration.toml
python3 validators/validate_review_readiness.py \
  hello-world/proof-bundle/evidence_matrix.toml

python3 validators/validate_ijb_conformance.py \
  hello-world/proof-bundle/traceability.toml \
  --repo-root . --check-references-exist
# (repeat IJB validator for the other four TOML files)

# Contract witness
bash hello-world/proof-bundle/run_all.sh

# Semantic-AST rewrite witness
bash hello-world/proof-bundle/detect_semantic_rewrite.sh

# AWK source-profile rewrite witness
bash hello-world/proof-bundle/detect_awk_rewrite.sh
```

If every command exits zero, `run_all.sh` reports `0 fail`, and
both rewrite witnesses report `0 fail`, the proof is intact: the spec
governs the same observable behaviour across every language whose
toolchain was present on the runner, and the source-analysis witnesses
demonstrate parser/profile-level detectability for the declared
rewrites.

## What this example deliberately does NOT prove

- It does **not** prove production readiness for arbitrary text I/O.
- It does **not** validate behaviour under platform-specific stdio
  buffering edge cases (the contract is the byte-level outcome a
  consumer of a non-tty pipe receives).
- It does **not** prove signature, supply-chain, or sandboxing
  properties — those live in the agent-assurance profile's
  `gate-decision`, `adapter-contract`, and `assertion-log-record`
  kinds. The multi-language proof intentionally stays at the
  smallest-possible scope so the spec mechanics are inspectable in a
  single sitting.
- It does **not** prove that arbitrary obfuscation can always be
  reduced to author intent. The Go semantic-AST witness only proves the
  declared function symbols remain parser-visible after that specific
  rewrite; the AWK witness only proves the C06 source profile is present
  for the AWK rewrite.

This example is the answer to "what does it actually look like to
apply DAG-TOML to code?" — not the answer to "what does a full
agent-assurance pipeline look like?".
