# Phase 1b: language-neutral walker seam (R15 response)

**Status:** drop-in paragraph for an appendix or Section 11 of the v2
chardet-relicense manuscript ("Toward language-neutral extraction").
Phase 4's editor should insert this next to Figure 5
(`figures/fig5_walker_architecture.pdf`).

**Branch:** `v2-phase1b-o` (worktree
`/srv/repos/external/verivus-oss/agent-assurance-papers/.claude/worktrees/agent-aba1876b9e5383019`).
**Reference commit:** the Phase-1b-o tip.

---

## Drop-in paragraph (LaTeX-ready)

> The structural-similarity signals C06a, C06a$'$, C06b, C06c, C06d and
> C06f all consume one specific view of the implementation under test
> (a call graph, an import edge set, a control-flow node histogram, a
> public-API signature surface, or a per-function shape record). In the
> v1 paper these views were extracted directly via Python's `ast`
> module, hard-coding the implementation language into the signal
> definitions even though the signal *contracts* are language-agnostic
> (a call graph is a call graph in any language). Phase 1b of the v2
> revision restructures the extractor around an `ASTWalker` protocol
> (Figure~5): each signal calls only `walker.iter_call_edges()`,
> `walker.iter_control_flow_nodes()`, `walker.iter_public_api()`,
> `walker.iter_imports()`, `walker.iter_class_methods()`, or
> `walker.iter_function_signatures()`, with no signal touching an
> `ast.*` type or any other language-specific parser API directly.
> The reference instance, `PythonASTWalker`, satisfies the protocol via
> the existing Python `ast` traversals (each protocol method maps to a
> well-defined set of AST node classes; the diagram annotates the
> mapping). Two hypothetical sibling instances, `TreeSitterRustWalker`
> (Rust via `syn` or tree-sitter) and `GoASTWalker` (Go via `go/ast`),
> are shown as un-implemented stubs alongside the Python walker; each
> protocol method is annotated with the language-native construct
> (`syn::ExprCall`, `go/ast.CallExpr`, etc.) a plugin author would
> need to wire up. We do **not** ship Rust or Go implementations; the
> claim being verified is structural, not empirical: that the signal
> definitions, as a body of code, no longer entangle the choice of
> implementation language with the choice of similarity contract. The
> refactor preserves every numeric output byte-for-byte against the
> pre-refactor harness — the same point estimates, the same
> percentile-bootstrap CIs, and the same per-method verdict counts —
> so it is a purely structural intervention. Reviewer concern R15 (the
> v1 "language-neutral spec" claim was unverified in code) is thereby
> answered by exhibiting the seam; the v1 prose is preserved unchanged
> and is now substantiated by the code structure.

---

## Honest disclaimers (for Phase 4 / reviewers)

Three seams in the abstraction resisted full language-neutrality and
deserve flagging:

1. **`iter_public_api` is Python-flavoured in its discovery mechanism.**
   Python re-exports a public surface via the `__all__` convention,
   resolved through `from <module> import <name>` aliasing. Rust and Go
   have no direct equivalent: a Rust walker would walk `pub` items and
   `pub use` re-exports out of `lib.rs`; a Go walker would walk
   capitalised identifiers across a package directory. The *signature
   descriptor* returned by the method (positional-arg count, kw-only
   count, default count, annotation presence) is language-neutral; the
   *discovery* of which symbols to describe is not. A naming refactor
   to `iter_public_surface` would not change this; the asymmetry is in
   the languages, not the protocol method.

2. **`iter_call_edges` returns `(caller_qualname, callee_simple_name)`
   pairs with no name resolution.** This is what survives paraphrase
   across languages (the rightmost attribute name on a call site is
   stable under module-level renaming) but it forfeits richer
   path-qualified callee information that Rust and Go compilers would
   surface natively. We retain the simple-name convention because it
   is the lowest common denominator across the three languages; a
   future revision could expose a `(caller, resolved_callee_path)`
   pair when the walker is plumbed into a language's name resolver.

3. **`iter_class_methods` assumes nominal-type-grouped methods.**
   Python and Rust have classes / structs+impls; Go has methods bound
   to receiver types but no classes. The Go walker would group methods
   by receiver type and the contract still works ("methods of a named
   type"), but the protocol method name `iter_class_methods` is
   Python-centric. We considered `iter_methods_by_type` as a renaming
   and rejected it in this iteration only because Phase 1b's scope is
   the structural seam, not naming-bike-shedding; Phase 4 may rename.

These are documented inside `_walker.py`'s module docstring so they
travel with the code, not only with the manuscript.

---

## What the refactor changed (mechanical summary)

- New module `chardet-relicense/proof-bundle/_walker.py` (~310 lines)
  defines the `ASTWalker` Protocol, the `FileContribution` and
  `FunctionRecord` dataclasses (language-neutral data holders that
  cross the seam), the `PythonASTWalker` reference instance, and a
  helper `build_call_graph_from_contribs()` that the bootstrap
  machinery already needed.

- Each of the six structural signal functions in `extract_signals.py`
  has gained a walker-typed sibling
  (`_signal_c06a_walker(walker_a, walker_b)`, etc.) carrying the
  substantive logic; the original path-typed function
  (`signal_c06a_call_graph(v6, v7)`) is now a legacy shim that
  instantiates a `PythonASTWalker` and delegates, so the CLI surface
  and the bootstrap machinery in `validate_numbers.py` continue to
  work unchanged. `main()` constructs the walker pair once and feeds
  the walker-typed entry points directly, exhibiting the seam at the
  driver level.

- All pre-existing module-level helpers (`_build_call_graph`,
  `_collect_functions`, `_attach_call_graph_position`,
  `_match_functions`, `_wl_label_multiset`, `_multiset_cosine`,
  `_control_flow_histogram`, `_audit_imports`,
  `_collect_public_signatures`, etc.) are preserved unchanged so the
  bootstrap-CI code that imports them by name continues to function
  bit-equivalently.

- No new pip dependencies. Python stdlib + the existing
  `networkx` / `numpy` / `scipy` / `matplotlib` set.

Witness TSVs across all three calibration pairs (v6/v7, v5/v6,
v6/charset\_normalizer) reproduce byte-for-byte across the refactor on
the static signal rows. A small ancillary fix to C06c's evidence-string
ordering (alphabetical secondary key when two control-flow node classes
tie on summed count) was applied because the legacy code had a
PYTHONHASHSEED-dependent ordering of tied evidence terms — two
consecutive runs of the unmodified v1 harness already produced
different orderings of those tied terms. This fix changes the order of
two terms in v5/v6 and v6/charset\_normalizer (`ExceptHandler` and
`Try`, both tied at the same count) without affecting any numeric
output: cosine similarity, totals, and the per-iteration values are
identical. The twelve bootstrap CIs in
`validation_report.v2_patch.n.json` reproduce bit-identically against
Phase-1b-n's baseline.
