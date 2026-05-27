# Proof: chardet v6 → v7 relicensing dispute (semantic-AST framing)

A worked, real-world application of the DAG-TOML spec to an
**active legal dispute**: did `chardet 7.0.0` (Dan Blanchard's
AI-rewritten MIT-licensed release, March 2026) carry enough of
`chardet 6.0.0`'s LGPL-licensed expression forward to remain a
derivative work?

The proof does **not** answer that legal question. It produces six
structural, falsifiable, **paraphrase-resistant** numbers that make
the conversation evidence-based instead of assertion-based.

Why "paraphrase-resistant" matters: a file-hash diff (the v0.1 of
this proof) collapses the moment any identifier is renamed. A
**semantic-AST** comparison — call-graph topology, import-edge
boundary, control-flow shape, signature equivalence, runtime
behaviour — does not. An adversary who restructures every file but
keeps the original's logical contract still leaves these fingerprints.

## Background — the dispute

| Date | Source | Position |
|---|---|---|
| 2026-03-04 | [chardet#325 "Nullified License"](https://github.com/chardet/chardet/issues/325) | GitHub user @gooba42 argues the LLM-generated rewrite cannot validly carry a new license (verified via GitHub REST API: `user.login = gooba42`). |
| 2026-03-05 | [Simon Willison](https://simonwillison.net/2026/Mar/5/chardet/) | Quotes Blanchard's "empty repository, instructed Claude not to base anything on LGPL/GPL code" defence; flags the committed rewrite plan as interesting. |
| 2026-03-06 | [The Register](https://www.theregister.com/2026/03/06/ai_kills_software_licensing) | FSF Executive Director Zoë Kooyman: *"There is nothing 'clean' about a Large Language Model which has ingested the code it is being asked to reimplement."* |
| 2026-03-10 | [Ars Technica](https://arstechnica.com/ai/2026/03/ai-can-rewrite-open-source-code-but-can-it-rewrite-the-license-too/) | Mainstream coverage. |
| 2026-04-09 | [Heather Meeker — Copyleft Currents](https://heathermeeker.com/2026/04/09/the-chardet-controversy-open-source-and-the-ai-clean-room/) | IP lawyer's analysis. |

## What the proof actually measures

One cheap baseline (kept as auxiliary) plus five semantic-AST signals:

| Contract | Signal | What survives paraphrase? | First-run output |
|---|---|---|---|
| **AUX1** | literal source carryover (file SHA-256, whitespace-normalised) | No — defeated by any rename | **PASS** (0 matches / 87 v6 × 33 v7) |
| **C06a** | call-graph topology similarity (degree distribution, SCCs, density) | **Yes** — graph shape survives identifier renaming | **similarity=0.881** (342 vs 358 nodes; 488 vs 659 edges) |
| **C06b** | third-party import-edge Jaccard | **Yes** — the dependency set is the same regardless of how internal code is restructured | **jaccard=0.333** (shared: `cchardet`, `datasets`; v7-only: `charset_normalizer`, `confusion_training`, `utils`) |
| **C06c** | control-flow histogram cosine | **Yes** — `If`/`For`/`Try` node *types* are AST grammar, stable across renames | **cosine=0.984** |
| **C06d** | public-API signature equivalence (strict / renamed_args / diverged) | **Yes** — call-shape is the contract | **3 strict / 0 renamed / 2 diverged** out of 5 shared |
| **C06e** | behavioural fingerprint over 1000-input deterministic fuzz | **Yes — the strongest signal**; runtime behaviour is the ultimate contract | **exact=0/1000, bucket=0/1000** |

## What the numbers actually say

Read together, the pattern is the *opposite* of what the shallow proof
showed:

- **Internal structure is highly preserved.** Call-graph topology
  similarity 0.881 and control-flow histogram cosine 0.984 say the
  rewrite kept v6's branching/looping/exception shape almost
  intact. This is the "shape of the thinking" inherited even though
  the identifiers and file layout are gone.
- **External boundary is genuinely different.** Import-edge jaccard
  0.333 says v7 pulls in a different dependency set (adds
  `charset_normalizer` plus the `confusion_training` / `utils`
  sibling-package imports). This is consistent with a re-platform
  onto modern Python ML tooling.
- **Public API is mostly preserved by signature.** Of the 5 names
  shared between v6's and v7's `__all__`, 3 (`__version__`, `detect`,
  `detect_all`) have byte-identical signatures. (The 2 "diverged"
  are classes; the comparison here is shallow on class kinds — see
  the EVIDENCE_MATRIX `known_exclusions`.)
- **Behaviour is operationally distinct.** 0/1000 exact match on
  random byte inputs. v6 and v7 *behave differently* on the same
  bytes — the rewrite is a genuine reimplementation, not a refactor
  whose output is bit-for-bit equivalent.

A reviewer can now formulate a position with paraphrase-resistant
evidence:

- *"v7 is genuinely independent expression that nevertheless
  preserves the shape and contract of v6"* — supported by
  AUX1 PASS + C06a 0.881 + C06c 0.984 + C06d 3/5 strict.
- *"v7 is a re-platform with a different dependency footprint and
  different runtime behaviour"* — supported by C06b 0.333 + C06e
  0/1000.
- *"the rewrite's internal call structure is too similar to v6's to
  be coincidence; the AI looked at v6's structure when planning the
  rewrite"* — supported by C06a 0.881 + C06c 0.984.
- *"the rewrite is an independent ML-based reimplementation that
  happens to share basic algorithm shape with all heuristic-based
  encoding detectors"* — also supported by the same C06a/C06c
  numbers; the proof cannot distinguish these two readings.

The proof exposes the numbers; the reviewer applies the legal theory.

## File map

```
chardet-relicense/proof-bundle/
├── README.md                       this file
├── implementation_dag.toml         six-unit layered DAG (3 prepare → 2 analyse → 1 verify)
├── traceability.toml               INT → FEAT → REQ → IMP → CODE x3 → TEST
├── contract_declaration.toml       AUX1 (baseline) + C06a..C06e (semantic-AST contracts)
├── review_readiness.toml           single G01 gate keyed to the witness pack
├── evidence_matrix.toml            3 claims, 7 evidence, 8-row matrix
├── verification_report.toml        the corrective-program spec for multi-LLM review
├── detect.sh                       executable witness driver
├── extract_signals.py              static-AST analyser (AUX1 + C06a..C06d)
└── fingerprint_behavior.py         behavioural fingerprint runner (C06e)
```

## Prerequisites

```bash
# One-time clone (the proof reads from this path by default):
git clone https://github.com/chardet/chardet.git \
  /srv/repos/public/spec-poc/chardet-relicense/chardet
# (override with CHARDET_REPO=/path/to/your/clone)

# Python deps: stdlib + networkx (already pinned in requirements.txt)
python3 -m pip install -r requirements.txt
```

## Run the proof

```bash
$ bash chardet-relicense/proof-bundle/detect.sh
proof-chardet-relicense: extracting AUX1 + C06a..C06e signals
  repo:   /srv/repos/public/spec-poc/chardet-relicense/chardet
  v6 tag: 6.0.0
  v7 tag: 7.0.0

signal	contract	expected	actual	verdict	evidence
literal_source_carryover	AUX1	0 matching pairs	0 matches across 87 v6 / 33 v7 files	PASS	no whitespace-normalised SHA-256 overlap
call_graph_topology	C06a	report topology-feature similarity in [0,1] — higher = more isomorphic	similarity=0.881 v6_nodes=342 v7_nodes=358 v6_edges=488 v7_edges=659	MEASURED	density: v6=0.00418 v7=0.00516 reldiff=0.104; sccs: v6=342 v7=358 reldiff=0.023; mean_in_degree: v6=1.43 v7=1.84 reldiff=0.127; max_in_degree: v6=34 v7=44 reldiff=0.128
import_edge_set	C06b	report Jaccard overlap of third-party (non-stdlib, non-self) imports	jaccard=0.333 shared=2 v6_only=1 v7_only=3	MEASURED	shared: ['cchardet', 'datasets']; v6_only: ['create_language_model']; v7_only: ['charset_normalizer', 'confusion_training', 'utils']
control_flow_histogram	C06c	report cosine similarity of normalised AST control-flow histograms	cosine=0.984 v6_total=652 v7_total=848	MEASURED	If: v6=346 v7=355; Return: v6=191 v7=253; For: v6=72 v7=135; Try: v6=12 v7=33; ExceptHandler: v6=12 v7=32; Raise: v6=10 v7=12
public_api_signature_equivalence	C06d	report strict / renamed_args / diverged counts across shared __all__ symbols	shared=5 strict=3 renamed_args=0 diverged=2	MEASURED	EncodingEra=diverged; UniversalDetector=diverged; __version__=strict; detect=strict; detect_all=strict
behavioural_fingerprint	C06e	report exact-match rate AND (encoding, confidence-bucket) match rate over N_INPUTS deterministic fuzz inputs	exact_match_rate=0.000 bucket_match_rate=0.000 n_inputs=1000 corpus_digest=58e54831f84183c7	MEASURED	exact=0/1000 bucket=0/1000 seed=20260522 input_max_len=4096

# SUMMARY
# MEASURED: 5
# PASS: 1
```

## Validate the spec artifacts

```bash
python3 ../agent-assurance/validators/validate_implementation_dag.py \
  chardet-relicense/proof-bundle/implementation_dag.toml
python3 ../agent-assurance/validators/validate_traceability.py \
  chardet-relicense/proof-bundle/traceability.toml --repo-root . --check-paths-exist
python3 ../agent-assurance/validators/validate_review_readiness.py \
  chardet-relicense/proof-bundle/review_readiness.toml
python3 ../agent-assurance/validators/validate_review_readiness.py \
  chardet-relicense/proof-bundle/contract_declaration.toml
python3 ../agent-assurance/validators/validate_review_readiness.py \
  chardet-relicense/proof-bundle/evidence_matrix.toml

for f in chardet-relicense/proof-bundle/*.toml; do
  python3 ../agent-assurance/validators/validate_ijb_conformance.py "$f" \
    --repo-root ../agent-assurance --check-references-exist
done

../agent-assurance/tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root ../agent-assurance \
  chardet-relicense/proof-bundle/*.toml
/tmp/dagtoml-validate-go --repo-root ../agent-assurance \
  chardet-relicense/proof-bundle/*.toml
```

## What this proof deliberately does NOT do

- It does **not** render a legal verdict on the dispute. The verdict
  belongs to the reviewer who weights the contracts; the proof
  produces the numbers.
- It does **not** measure training-data provenance. If Claude saw
  chardet 6.x during training, no structural inspection of the v7
  output can prove or disprove that. The FSF position is not
  addressable by this proof's signal set.
- It does **not** address Mozilla's upstream copyright claim against
  v6. The v6 ↔ v7 comparison is downstream of the Mozilla → v6
  question.
- It does **not** copy chardet source into this repository. The
  detection harness reads from a separate clone under
  `/srv/repos/public/spec-poc/chardet-relicense/chardet/`. The
  bundle is genuinely standalone.
- It does **not** generalise to other rewrites. The signal set is
  tuned to Python; a `proof-rust-relicense` or `proof-go-relicense`
  would need its own AST-walker. The DAG-TOML scaffolding generalises;
  the static-AST extractor does not.
- It does **not** catch surgical per-function paraphrase that
  preserves module boundaries. A rewrite that replaces every
  function body one-by-one with an equivalent reformulation can
  still score high on C06a/C06c if the module-level call graph is
  unchanged. That's a known limitation; addressing it requires
  function-level rather than module-level graph features.

## Versus the prior shallow proof

The v0.1 of this proof tested file hashing and symbol-name set
overlap. It produced a verdict (3 PASS / 3 MEASURED) but the verdict
was misleading because every signal collapsed under paraphrase. This
v0.2 replaces every contract with one that is invariant to
identifier renaming and module restructuring; the only retained
shallow signal is AUX1, which is now explicitly labelled as a cheap
baseline, not load-bearing evidence.
