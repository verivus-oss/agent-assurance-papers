#!/usr/bin/env python3
"""extract_signals.py — five AST-level signals + one auxiliary baseline
for the chardet v6 → v7 relicensing proof.

v2 calibration extension (Phase 1a agent Q): this script is now
pair-agnostic. It still defaults to comparing chardet 6.0.0 vs 7.0.0
when invoked with the legacy --v6-root / --v7-root flags, but accepts
--root-a / --root-b and --pkg-a / --pkg-b so the same harness can be
pointed at calibration pairs (chardet 5 vs 6, chardet 6 vs
charset-normalizer). The "package name" controls (a) the import-edge
self-exclusion set in C06b and (b) which `__init__.py` is treated as
the public-API surface in C06d.

This script is the substantive answer to the question "did the rewrite
preserve enough of the original's *structure* to be a derivative work,
even if every literal was renamed?". File-hash and name-set checks
collapse under paraphrase; the signals here do not, because they
compare AST-level *topology* (call graph), *boundary* (import edges),
*shape* (control-flow histograms), and *contract* (public API
signatures).

USAGE:
    extract_signals.py --v6-root <path> --v7-root <path>

OUTPUT:
    signal	contract	expected	actual	verdict	evidence

Signals:
    AUX1 (auxiliary, retained from v0.1)
        literal_source_carryover  — whitespace-normalized SHA-256
                                   file-hash overlap. Cheap baseline;
                                   does not survive paraphrase.

    C06a — call_graph_topology
            Build the directed call graph from each version's
            implementation. Compare topology features (node count,
            edge count, degree-distribution moments, strongly-
            connected-component count, density). A rewrite that
            preserves the original's control structure scores high on
            similarity even when every function is renamed.

    C06b — import_edge_set
            Set of third-party (non-stdlib, non-self) modules each
            version imports. Jaccard overlap. Preserved external
            dependencies are evidence the rewrite kept the same
            environmental contract.

    C06c — control_flow_histogram
            Per-version histogram of AST control-flow node types
            (If / For / While / Try / With / Raise / Return / Yield /
            ExceptHandler / Match). Cosine similarity of normalized
            histograms — survives renaming because node *types* are
            stable across function/identifier renaming.

    C06a' — call_graph_wl_kernel  (added in V2 revision, R1 response)
            A Weisfeiler-Lehman graph-kernel similarity over the same
            directed call graphs C06a operates on. Unlike C06a's coarse
            8-feature topology summary (which two non-isomorphic graphs
            can collide on), WL hashes a multi-scale rooted-subtree
            signature for every node and reports a cosine similarity
            over the multiset of refined labels. k iterations of label
            propagation distinguish graphs that agree on degree
            distribution but differ on neighbourhood structure.
            Implementation is pure-stdlib (hashlib + collections), no
            new dependency.

    C06f — per_function_ast_shape  (added in V2 revision, R16 response)
            Per-function AST shape features (node-type histogram,
            function-body depth, fan-in / fan-out in the call graph).
            Cross-version function matching is by signature-shape hash
            and call-graph position bucket, NOT by name (paraphrase
            often renames). The signal reports both an aggregate
            shape-distance over matched pairs AND an honest count of
            unmatched functions on either side.

    C06d — public_api_signature_equivalence
            For each public symbol exported by both versions (the
            intersection of the two `__all__` lists), compare the
            declared signature: positional arg count, keyword arg
            count, return annotation presence. Counts strict-equal
            signatures vs renamed-arg signatures.

The script is pure-stdlib + networkx. networkx is already pinned in
requirements.txt for the implementation-DAG validator.

Bugs from Round 1 review explicitly fixed:
    * Test exclusion now catches root-level `test*.py` and `*_test.py`
      files in addition to `tests/` / `test/` directories.
    * Module-level symbol extraction walks only the module body, not
      recursively via ast.walk (so locals inside functions don't leak).
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import math
import pathlib
import re
import sys
from collections import Counter, defaultdict
from typing import Iterable

try:
    import networkx as nx
except ImportError:  # pragma: no cover
    print("error: networkx is required (pip install networkx)", file=sys.stderr)
    sys.exit(2)


# ----------------------------------------------------------------------------
# File enumeration
# ----------------------------------------------------------------------------

# Test files: any of these patterns count as test code and are excluded.
_TEST_FILENAME_RE = re.compile(r"^(test_.*|.*_test|test)\.py$")


def iter_impl_py_files(root: pathlib.Path) -> Iterable[pathlib.Path]:
    """Iterate every .py file under `root` that is part of the *implementation*
    surface (not tests, not build/dist, not __pycache__).

    The exclusion is stricter than the v0.1 proof's: a file named
    `test.py` or `test_anything.py` at the *repository root* counts as
    test code and is excluded, not just files under tests/ directories.
    """
    for p in sorted(root.rglob("*.py")):
        parts = p.parts
        if any(seg in {"tests", "test", "__pycache__", "build", "dist", ".tox", ".venv"} for seg in parts):
            continue
        if _TEST_FILENAME_RE.match(p.name):
            continue
        yield p


def whitespace_normalised_text(path: pathlib.Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return "\n".join(line.rstrip() for line in text.splitlines() if line.strip())


# ----------------------------------------------------------------------------
# AUX1 — literal source carryover (cheap baseline)
# ----------------------------------------------------------------------------

def signal_aux1_literal_carry(v6: pathlib.Path, v7: pathlib.Path) -> dict:
    def hashes(root: pathlib.Path) -> dict[str, pathlib.Path]:
        out: dict[str, pathlib.Path] = {}
        for p in iter_impl_py_files(root):
            norm = whitespace_normalised_text(p)
            if not norm:
                continue
            out[hashlib.sha256(norm.encode()).hexdigest()] = p
        return out

    h6 = hashes(v6)
    h7 = hashes(v7)
    overlap = set(h6) & set(h7)
    return {
        "signal": "literal_source_carryover",
        "contract": "AUX1",
        "expected": "0 matching pairs",
        "actual": f"{len(overlap)} matches across {len(h6)} v6 / {len(h7)} v7 files",
        "verdict": "PASS" if not overlap else "FAIL",
        "evidence": "; ".join(f"{h6[h].relative_to(v6)} == {h7[h].relative_to(v7)}" for h in sorted(overlap)[:5]) or "no whitespace-normalised SHA-256 overlap",
    }


# ----------------------------------------------------------------------------
# C06a — call-graph topology
# ----------------------------------------------------------------------------

def _qualified_name(stack: list[str], name: str) -> str:
    return ".".join(stack + [name])


class _CallEdgeCollector(ast.NodeVisitor):
    """Collect (caller, callee) edges from a parsed module.

    Caller is a qualified name (module.func or module.Class.method);
    callee is the rightmost attribute name on the call (best-effort —
    full resolution requires symbol tables and the proof deliberately
    does NOT enter that complexity; a renamed callee in v7 still has
    a callee NAME in v7 because the AST records it).
    """

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.scope_stack: list[str] = [module_name]
        self.functions: set[str] = set()
        self.edges: list[tuple[str, str]] = []

    def _record_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qual = _qualified_name(self.scope_stack, node.name)
        self.functions.add(qual)
        self.scope_stack.append(node.name)
        for child in node.body:
            self._walk(child, caller=qual)
        self.scope_stack.pop()

    def _walk(self, node: ast.AST, caller: str | None) -> None:
        if isinstance(node, ast.Call):
            callee = self._callee_name(node.func)
            if callee and caller:
                self.edges.append((caller, callee))
        for child in ast.iter_child_nodes(node):
            self._walk(child, caller)

    @staticmethod
    def _callee_name(func: ast.AST) -> str | None:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None

    def visit_Module(self, node: ast.Module) -> None:
        for child in node.body:
            self.visit(child)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_function(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope_stack.append(node.name)
        for child in node.body:
            self.visit(child)
        self.scope_stack.pop()


def _build_call_graph(root: pathlib.Path) -> nx.DiGraph:
    g: nx.DiGraph = nx.DiGraph()
    for p in iter_impl_py_files(root):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        module_name = p.relative_to(root).with_suffix("").as_posix().replace("/", ".")
        collector = _CallEdgeCollector(module_name)
        collector.visit(tree)
        for func in collector.functions:
            g.add_node(func)
        for caller, callee in collector.edges:
            g.add_edge(caller, callee)
    return g


def _graph_topology(g: nx.DiGraph) -> dict[str, float]:
    if g.number_of_nodes() == 0:
        return {"nodes": 0.0, "edges": 0.0, "density": 0.0, "sccs": 0.0,
                "mean_in_degree": 0.0, "mean_out_degree": 0.0, "max_in_degree": 0.0, "max_out_degree": 0.0}
    in_deg = [d for _, d in g.in_degree()]
    out_deg = [d for _, d in g.out_degree()]
    return {
        "nodes": float(g.number_of_nodes()),
        "edges": float(g.number_of_edges()),
        "density": nx.density(g),
        "sccs": float(nx.number_strongly_connected_components(g)),
        "mean_in_degree": sum(in_deg) / len(in_deg),
        "mean_out_degree": sum(out_deg) / len(out_deg),
        "max_in_degree": float(max(in_deg)),
        "max_out_degree": float(max(out_deg)),
    }


def _relative_diff(a: float, b: float) -> float:
    """Symmetric relative difference; 0 = identical, 1 = wildly different."""
    if a == 0 and b == 0:
        return 0.0
    return abs(a - b) / (abs(a) + abs(b))


def signal_c06a_call_graph(v6: pathlib.Path, v7: pathlib.Path) -> dict:
    g6 = _build_call_graph(v6)
    g7 = _build_call_graph(v7)
    t6 = _graph_topology(g6)
    t7 = _graph_topology(g7)

    # Per-feature relative differences; average is the headline number.
    diffs = {k: _relative_diff(t6[k], t7[k]) for k in t6}
    mean_diff = sum(diffs.values()) / len(diffs)
    similarity = 1.0 - mean_diff  # 1 = identical topology, 0 = unrelated

    return {
        "signal": "call_graph_topology",
        "contract": "C06a",
        "expected": "report topology-feature similarity in [0,1] — higher = more isomorphic",
        "actual": f"similarity={similarity:.3f} v6_nodes={int(t6['nodes'])} v7_nodes={int(t7['nodes'])} v6_edges={int(t6['edges'])} v7_edges={int(t7['edges'])}",
        "verdict": "MEASURED",
        "evidence": "; ".join(f"{k}: v6={t6[k]:.3g} v7={t7[k]:.3g} reldiff={diffs[k]:.3f}" for k in ("density", "sccs", "mean_in_degree", "max_in_degree")),
    }


# ----------------------------------------------------------------------------
# C06a' — Weisfeiler-Lehman call-graph kernel (V2 revision, R1 response)
#
# C06a's 8-feature summary (n, m, density, |SCC|, mean/max in/out-degree)
# is a *coarse* topology fingerprint: two non-isomorphic graphs with very
# different connection patterns can still collide on those scalars. The
# Weisfeiler-Lehman graph-kernel test refines node labels by iteratively
# hashing each node's label together with the multiset of its neighbours'
# labels. After k iterations the label of a node is a rooted-subtree
# signature of depth k; the multiset of labels over the whole graph is
# its k-hop fingerprint. Comparing the two multisets by cosine similarity
# over the union of labels gives a graph-similarity score that is
# strictly stronger than the topology summary — graphs that agree on
# degree distribution but disagree on neighbourhood structure separate
# under WL whereas they collide under C06a.
#
# Reference: Shervashidze et al., "Weisfeiler-Lehman Graph Kernels",
# JMLR 2011. The standard formulation is for undirected labelled graphs;
# we apply it to the directed call graph by combining each node's
# in-neighbour-label-multiset and out-neighbour-label-multiset
# separately at the refinement step, so direction is preserved. The
# implementation is pure-stdlib (hashlib + collections.Counter) and adds
# no new pip dependency — the networkx digraph C06a already builds is
# all we need.
#
# k=4 chosen so the rooted subtree depth exceeds the typical call-chain
# depth in chardet's detector pipeline (UniversalDetector -> charset
# prober -> coding state machine -> distribution analyser is ~4 hops).
# Lower k undercounts deep paraphrase; k>4 saturates because most
# call-graph branches die out at depth 4 in this codebase.
# ----------------------------------------------------------------------------

# Number of WL refinement iterations. Documented above.
_WL_ITERATIONS = 4


def _wl_initial_label(g: nx.DiGraph, node: str) -> str:
    """Initial label is the (in-degree, out-degree) tuple. Names are
    NOT used: a renamed function in v7 still has the same degree
    profile, which is the whole point — WL refines from a renaming-
    invariant starting label."""
    return f"d:{g.in_degree(node)}|{g.out_degree(node)}"


def _wl_refine(g: nx.DiGraph, labels: dict[str, str]) -> dict[str, str]:
    """One round of WL label refinement on a directed graph.

    New label is sha256 of: (own label, sorted in-neighbour labels,
    sorted out-neighbour labels). Truncated to 16 hex chars (still
    collision-safe at this graph size) to keep the label dictionary
    small in memory.
    """
    new: dict[str, str] = {}
    for u in g.nodes():
        in_labels = sorted(labels[v] for v in g.predecessors(u))
        out_labels = sorted(labels[v] for v in g.successors(u))
        payload = (
            labels[u] + "|<|" + ",".join(in_labels) +
            "|>|" + ",".join(out_labels)
        ).encode("utf-8")
        new[u] = hashlib.sha256(payload).hexdigest()[:16]
    return new


def _wl_label_multiset(g: nx.DiGraph, k: int = _WL_ITERATIONS
                       ) -> Counter[str]:
    """Run k iterations of WL refinement on `g` and return the
    *bag-of-labels* over all iterations (including the initial label).
    The Shervashidze WL-subtree kernel feature map is exactly the
    multiset union over iterations, so cosine on these multisets
    matches the published kernel."""
    if g.number_of_nodes() == 0:
        return Counter()
    labels = {u: _wl_initial_label(g, u) for u in g.nodes()}
    bag: Counter[str] = Counter(labels.values())
    for _ in range(k):
        labels = _wl_refine(g, labels)
        bag.update(labels.values())
    return bag


def _multiset_cosine(a: Counter[str], b: Counter[str]) -> float:
    """Cosine similarity over two label multisets (sparse dot product)."""
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[k] * b[k] for k in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def signal_c06a_prime_wl_kernel(v6: pathlib.Path,
                                 v7: pathlib.Path) -> dict:
    """C06a' — Weisfeiler-Lehman kernel similarity over the v6 and v7
    call graphs. Reported alongside C06a so reviewers can see the
    coarse-vs-refined signal pair side by side."""
    g6 = _build_call_graph(v6)
    g7 = _build_call_graph(v7)
    bag6 = _wl_label_multiset(g6, _WL_ITERATIONS)
    bag7 = _wl_label_multiset(g7, _WL_ITERATIONS)
    cos = _multiset_cosine(bag6, bag7)

    # Per-iteration breakdown — useful diagnostic. We re-run iterations
    # separately so reviewers can see whether the similarity collapses
    # after the first refinement (indicating only degree-level
    # agreement) or holds up through deep refinement (indicating
    # genuine neighbourhood-structure agreement).
    per_iter_cos: list[float] = []
    if g6.number_of_nodes() and g7.number_of_nodes():
        l6 = {u: _wl_initial_label(g6, u) for u in g6.nodes()}
        l7 = {u: _wl_initial_label(g7, u) for u in g7.nodes()}
        per_iter_cos.append(_multiset_cosine(Counter(l6.values()),
                                             Counter(l7.values())))
        for _ in range(_WL_ITERATIONS):
            l6 = _wl_refine(g6, l6)
            l7 = _wl_refine(g7, l7)
            per_iter_cos.append(_multiset_cosine(Counter(l6.values()),
                                                 Counter(l7.values())))

    breakdown = ", ".join(f"iter{i}={c:.3f}" for i, c in
                          enumerate(per_iter_cos))
    return {
        "signal": "call_graph_wl_kernel",
        "contract": "C06a'",
        "expected": (
            "report WL-subtree kernel cosine similarity over the v6/v7 "
            f"call graphs, k={_WL_ITERATIONS} refinement iterations"
        ),
        "actual": (
            f"wl_cosine={cos:.3f} k={_WL_ITERATIONS} "
            f"v6_labels={sum(bag6.values())} v7_labels={sum(bag7.values())}"
        ),
        "verdict": "MEASURED",
        "evidence": (f"per-iteration cosine: {breakdown}" if breakdown
                     else "empty call graph(s)"),
    }


# ----------------------------------------------------------------------------
# C06f — per-function AST shape (V2 revision, R16 response)
#
# C06a / C06a' operate at module-level granularity: they ask "does the
# whole call graph have the same shape". That misses surgical
# per-function paraphrase — e.g. an AI rewrite where every function is
# individually renamed AND restructured but the module-level call graph
# is preserved end-to-end. C06f drops below the module to extract a
# *per-function* shape signature: the histogram of AST node types
# inside the function body, the maximum AST depth of the body, and the
# function's fan-in / fan-out in the call graph.
#
# Cross-version function matching is the hard part: paraphrase often
# renames functions, so matching by name is unsafe. Instead each
# function is keyed by:
#   (signature_shape_hash, fan_in_bucket, fan_out_bucket)
# where:
#   signature_shape_hash := (n_pos, n_kw_only, n_defaults, has_vararg,
#                            has_kwarg, n_annotations)
#   fan_in_bucket  := log-floor of in-degree   (0, 1, 2-3, 4-7, 8-15, ...)
#   fan_out_bucket := log-floor of out-degree  (same buckets)
# Functions with identical match keys are paired greedily by Hungarian
# (we use a simpler stable greedy here — sample is small). Unmatched
# functions on either side are reported as honest counts; we do NOT
# fall back to name-matching them.
# ----------------------------------------------------------------------------

# AST node types we score for the per-function shape histogram.
_FUNC_SHAPE_NODES = (
    ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler, ast.With,
    ast.AsyncWith, ast.AsyncFor, ast.Return, ast.Yield, ast.YieldFrom,
    ast.Raise, ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Call,
    ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare, ast.Lambda,
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
    ast.Subscript, ast.Attribute, ast.Name, ast.Constant,
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
)
if hasattr(ast, "Match"):
    _FUNC_SHAPE_NODES = (*_FUNC_SHAPE_NODES, ast.Match)


def _ast_depth(node: ast.AST) -> int:
    """Max depth of `node`'s AST subtree, counting the node itself as 1."""
    children = list(ast.iter_child_nodes(node))
    if not children:
        return 1
    return 1 + max(_ast_depth(c) for c in children)


def _signature_shape_key(node: ast.FunctionDef | ast.AsyncFunctionDef
                          ) -> tuple:
    a = node.args
    n_pos = len(a.args) + len(a.posonlyargs) if hasattr(a, "posonlyargs") else len(a.args)
    n_kw_only = len(a.kwonlyargs)
    n_defaults = len(a.defaults) + sum(1 for d in a.kw_defaults if d is not None)
    has_vararg = a.vararg is not None
    has_kwarg = a.kwarg is not None
    n_annotations = sum(1 for arg in (
        list(a.args) + list(a.kwonlyargs)
        + ([a.vararg] if a.vararg else [])
        + ([a.kwarg] if a.kwarg else [])
    ) if arg and arg.annotation is not None)
    return (n_pos, n_kw_only, n_defaults, has_vararg, has_kwarg,
            n_annotations)


def _degree_bucket(deg: int) -> int:
    """Log-floor bucket: 0 -> 0, 1 -> 1, 2..3 -> 2, 4..7 -> 3, ..."""
    if deg <= 0:
        return 0
    return int(math.floor(math.log2(deg))) + 1


class _FunctionShapeCollector(ast.NodeVisitor):
    """Walk a module and record every FunctionDef / AsyncFunctionDef.

    For each function we keep:
        qual_name       — module.path.Class.func (used only for evidence
                          strings, NEVER for cross-version matching)
        sig_shape       — signature-shape tuple (see above)
        body_hist       — Counter of AST node-type names within the body
        depth           — max AST depth of the function body
        n_stmts         — number of top-level body statements
    """

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.scope: list[str] = [module_name]
        self.functions: list[dict] = []

    def _record(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qual = _qualified_name(self.scope, node.name)
        hist: Counter[str] = Counter()
        for child in node.body:
            for n in ast.walk(child):
                for cls in _FUNC_SHAPE_NODES:
                    if isinstance(n, cls):
                        hist[cls.__name__] += 1
                        break
        depth = max((_ast_depth(s) for s in node.body), default=0)
        self.functions.append({
            "qual_name": qual,
            "name": node.name,
            "sig_shape": _signature_shape_key(node),
            "body_hist": hist,
            "depth": depth,
            "n_stmts": len(node.body),
        })
        # Recurse into nested defs.
        self.scope.append(node.name)
        for child in node.body:
            self.visit(child)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        for child in node.body:
            self.visit(child)
        self.scope.pop()


def _collect_functions(root: pathlib.Path) -> list[dict]:
    """Return list of per-function shape records across the whole tree."""
    out: list[dict] = []
    for p in iter_impl_py_files(root):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        module_name = p.relative_to(root).with_suffix("").as_posix().replace("/", ".")
        c = _FunctionShapeCollector(module_name)
        c.visit(tree)
        out.extend(c.functions)
    return out


def _attach_call_graph_position(functions: list[dict],
                                 g: nx.DiGraph) -> None:
    """Annotate each function with fan_in / fan_out / buckets, using
    qualified name to look up in the call graph (qual_name is how the
    call graph keys functions). If the function isn't a node in g
    (callee-only stubs may not be registered), we treat its in/out
    degree as 0 — same as a leaf."""
    for f in functions:
        qn = f["qual_name"]
        if qn in g.nodes:
            f["fan_in"] = g.in_degree(qn)
            f["fan_out"] = g.out_degree(qn)
        else:
            f["fan_in"] = 0
            f["fan_out"] = 0
        f["fan_in_bucket"] = _degree_bucket(f["fan_in"])
        f["fan_out_bucket"] = _degree_bucket(f["fan_out"])
        f["match_key"] = (f["sig_shape"], f["fan_in_bucket"],
                          f["fan_out_bucket"])


def _hist_cosine(a: Counter[str], b: Counter[str]) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _pair_distance(f6: dict, f7: dict) -> float:
    """Distance in [0,1]: lower = more similar. Components:
      - cosine on body histograms (weight 0.6)
      - relative diff on depth     (weight 0.2)
      - relative diff on n_stmts   (weight 0.2)
    """
    cos = _hist_cosine(f6["body_hist"], f7["body_hist"])
    rd_depth = _relative_diff(float(f6["depth"]), float(f7["depth"]))
    rd_stmts = _relative_diff(float(f6["n_stmts"]), float(f7["n_stmts"]))
    return 0.6 * (1.0 - cos) + 0.2 * rd_depth + 0.2 * rd_stmts


def _match_functions(v6_funcs: list[dict],
                     v7_funcs: list[dict]
                     ) -> tuple[list[tuple[dict, dict, float]],
                                list[dict], list[dict]]:
    """Greedy stable matching by (sig_shape, fan_in_bucket,
    fan_out_bucket). Within each match-key bucket, pairs are formed by
    smallest pair-distance first. Unmatched functions on either side
    are returned honestly — we do NOT fall back to name-based matching
    or to coarser buckets, because the whole point of C06f is to test
    cross-version shape preservation under paraphrase, and inflating
    the match count via name-based fallback would defeat that."""
    buckets_v6: defaultdict[tuple, list[dict]] = defaultdict(list)
    buckets_v7: defaultdict[tuple, list[dict]] = defaultdict(list)
    for f in v6_funcs:
        buckets_v6[f["match_key"]].append(f)
    for f in v7_funcs:
        buckets_v7[f["match_key"]].append(f)

    pairs: list[tuple[dict, dict, float]] = []
    used_v7: set[int] = set()
    used_v6: set[int] = set()
    for key, lst6 in buckets_v6.items():
        lst7 = buckets_v7.get(key, [])
        if not lst7:
            continue
        # Score every v6-v7 candidate pair in this bucket, sort, accept
        # in increasing-distance order (each side picked at most once).
        candidates: list[tuple[float, int, int]] = []
        for i, f6 in enumerate(lst6):
            for j, f7 in enumerate(lst7):
                candidates.append((_pair_distance(f6, f7), i, j))
        candidates.sort()
        taken_i: set[int] = set()
        taken_j: set[int] = set()
        for dist, i, j in candidates:
            if i in taken_i or j in taken_j:
                continue
            taken_i.add(i)
            taken_j.add(j)
            pairs.append((lst6[i], lst7[j], dist))
            used_v6.add(id(lst6[i]))
            used_v7.add(id(lst7[j]))

    unmatched_v6 = [f for f in v6_funcs if id(f) not in used_v6]
    unmatched_v7 = [f for f in v7_funcs if id(f) not in used_v7]
    return pairs, unmatched_v6, unmatched_v7


def signal_c06f_per_function_shape(v6: pathlib.Path,
                                    v7: pathlib.Path) -> dict:
    """C06f — per-function AST-shape signal.

    Reports:
      - total function counts (v6, v7)
      - matched-pair count (by signature-shape + call-graph position)
      - aggregate mean shape distance over matched pairs
      - unmatched-function counts on each side (honest — no
        name-based fallback)
      - same-name overlap as a *diagnostic* number (to expose how
        much of the matching is identifier-driven vs structural)
    """
    g6 = _build_call_graph(v6)
    g7 = _build_call_graph(v7)
    f6 = _collect_functions(v6)
    f7 = _collect_functions(v7)
    _attach_call_graph_position(f6, g6)
    _attach_call_graph_position(f7, g7)

    pairs, un6, un7 = _match_functions(f6, f7)

    if pairs:
        mean_dist = sum(d for _, _, d in pairs) / len(pairs)
        # Also expose what fraction of matches are name-identical, as
        # an honesty diagnostic — high overlap means name was implicitly
        # available to the matcher even though we didn't use it.
        same_name_overlap = sum(
            1 for a, b, _ in pairs if a["name"] == b["name"]
        ) / len(pairs)
    else:
        mean_dist = 1.0  # worst-case: nothing matched
        same_name_overlap = 0.0

    # The similarity figure inverts mean distance to align with C06a/C06c
    # convention (1.0 = identical, 0.0 = unrelated).
    similarity = max(0.0, 1.0 - mean_dist)

    return {
        "signal": "per_function_ast_shape",
        "contract": "C06f",
        "expected": (
            "report per-function shape similarity over functions matched "
            "by (signature-shape, fan-in-bucket, fan-out-bucket) and "
            "honest unmatched-function counts on both sides"
        ),
        "actual": (
            f"per_function_similarity={similarity:.3f} "
            f"matched_pairs={len(pairs)} "
            f"v6_functions={len(f6)} v7_functions={len(f7)} "
            f"unmatched_v6={len(un6)} unmatched_v7={len(un7)}"
        ),
        "verdict": "MEASURED",
        "evidence": (
            f"mean_pair_distance={mean_dist:.3f}; "
            f"same_name_overlap_among_matched={same_name_overlap:.3f}; "
            f"matched/v6={len(pairs)}/{len(f6)} "
            f"matched/v7={len(pairs)}/{len(f7)}"
        ),
    }



# ----------------------------------------------------------------------------
# C06b — import-edge set
# ----------------------------------------------------------------------------

# Authoritative stdlib hint set — derived from `sys.stdlib_module_names`
# at import time, which the cpython interpreter exposes as the complete
# top-level stdlib module name set for the running version. Falls back
# to a hand-curated set for older interpreters that lack the attribute
# (Codex round-1 quality note: the hand-curated set in v0.2 was missing
# atexit / cProfile / tracemalloc / concurrent / pstats / resource, so
# they leaked into C06b's "v7_only" diagnostic list).
_STDLIB_HINT: frozenset[str] = (
    frozenset(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names")
    else frozenset({
        "abc", "argparse", "ast", "asyncio", "atexit", "base64", "binascii",
        "builtins", "bz2", "calendar", "cProfile", "codecs", "collections",
        "concurrent", "contextlib", "copy", "csv", "ctypes", "dataclasses",
        "datetime", "decimal", "difflib", "dis", "email", "enum", "errno",
        "fcntl", "fileinput", "fnmatch", "fractions", "functools", "gc",
        "getopt", "getpass", "glob", "gzip", "hashlib", "heapq", "hmac",
        "html", "http", "importlib", "inspect", "io", "ipaddress",
        "itertools", "json", "keyword", "linecache", "locale", "logging",
        "lzma", "math", "mmap", "multiprocessing", "numbers", "operator",
        "os", "pathlib", "pickle", "platform", "pprint", "pstats", "queue",
        "random", "re", "resource", "select", "selectors", "shlex", "shutil",
        "signal", "site", "socket", "socketserver", "sqlite3", "ssl", "stat",
        "statistics", "string", "struct", "subprocess", "sys", "tarfile",
        "tempfile", "textwrap", "threading", "time", "tokenize", "tomllib",
        "traceback", "tracemalloc", "types", "typing", "unicodedata",
        "unittest", "urllib", "uuid", "venv", "warnings", "weakref", "xml",
        "zipfile", "zlib", "__future__",
    })
)


def _collect_raw_imports(root: pathlib.Path) -> set[str]:
    """Return the *raw* set of top-level module names imported by every
    implementation file under `root` (no filtering). Relative imports are
    skipped because they are internal.

    The audit trail (R5 reviewer complaint, v2 revision) classifies each
    name with `_classify_import`; the pre-v2 implementation pre-filtered
    against `_STDLIB_HINT` and `_PKG_SELF` here, which obscured the
    classification rule.
    """
    out: set[str] = set()
    for p in iter_impl_py_files(root):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    out.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue  # relative import — internal, not an edge
                if node.module:
                    out.add(node.module.split(".")[0])
    return {m for m in out if m}


def _module_resolves_inside(
    root: pathlib.Path, name: str, pkg_name: str = "chardet",
) -> pathlib.Path | None:
    """Return the first on-disk path under `root` that an absolute import
    of `name` could resolve to as a Python module, or None.

    The pkg_name parameter (v2 multi-pair extension, Q×D integration) is
    the top-level package directory the audit treats as "first-party
    self-sibling". For the v6/v7 pair it is "chardet"; for the
    v6/charset-normalizer pair side B is "charset_normalizer".

    Resolution candidates considered, in order:
        1. Inside the <pkg_name> package directory itself (sibling submodule).
        2. As a top-level `.py` file or package directory at the repo
           root (sibling helper script).
        3. As a `.py` file or package directory inside any sibling
           top-level directory of the repo (e.g. `scripts/<name>.py`,
           `tools/<name>/__init__.py`).
    """
    # Locate the package directory if present, for R3 checks.
    pkg_candidates = [root / pkg_name, root / "src" / pkg_name]
    pkg_dir = next((d for d in pkg_candidates if d.is_dir()), None)

    # R3 — <pkg_name> sibling submodule.
    if pkg_dir is not None:
        for suffix in (f"{name}.py", name):
            candidate = pkg_dir / suffix
            if candidate.exists():
                if candidate.is_file() or (candidate / "__init__.py").is_file():
                    return candidate

    # R4a — top-level repo script/package.
    for suffix in (f"{name}.py", name):
        candidate = root / suffix
        if candidate.is_file():
            return candidate
        if candidate.is_dir() and (candidate / "__init__.py").is_file():
            return candidate / "__init__.py"

    # R4b — file in any sibling top-level directory (e.g. scripts/).
    skip = {"__pycache__", "build", "dist", ".tox", ".venv", "tests", "test", "docs"}
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name in skip:
            continue
        if pkg_dir is not None and child == pkg_dir.parent and child.name == "src":
            for sub_suffix in (f"{name}.py", name):
                sub_candidate = child / sub_suffix
                if sub_candidate == pkg_dir:
                    continue
                if sub_candidate.is_file():
                    return sub_candidate
                if sub_candidate.is_dir() and (sub_candidate / "__init__.py").is_file():
                    return sub_candidate / "__init__.py"
            continue
        for sub_suffix in (f"{name}.py", name):
            sub_candidate = child / sub_suffix
            if sub_candidate.is_file():
                return sub_candidate
            if sub_candidate.is_dir() and (sub_candidate / "__init__.py").is_file():
                return sub_candidate / "__init__.py"

    return None


def _classify_import(
    root: pathlib.Path, name: str, pkg_name: str = "chardet",
) -> tuple[str, str, pathlib.Path | None]:
    """Classify `name` against the source tree at `root` for the package
    `pkg_name` (Q×D parametrisation).

    Returns (origin, rule_id, resolved_path):
        origin     — one of stdlib / first_party_self / sibling_package /
                     internal_helper / third_party
        rule_id    — R1_stdlib / R2_first_party_self / R3_first_party_sibling /
                     R4_internal_helper / R5_third_party_kept
        resolved_path — filesystem path the name resolved to inside `root`
                     for R3/R4, or None for R1/R2/R5.

    Rule precedence (first match wins):
        R1_stdlib              — `name in sys.stdlib_module_names`
        R2_first_party_self    — name == pkg_name
        R3_first_party_sibling — resolves inside `<root>/[src/]<pkg_name>/`
        R4_internal_helper     — resolves elsewhere inside the cloned tree
        R5_third_party_kept    — does not resolve anywhere in `root`

    Only R5 imports are kept for the Jaccard computation.
    """
    if name in _STDLIB_HINT:
        return ("stdlib", "R1_stdlib", None)
    if name == pkg_name:
        return ("first_party_self", "R2_first_party_self", None)

    resolved = _module_resolves_inside(root, name, pkg_name)
    if resolved is not None:
        try:
            rel_parts = resolved.resolve().relative_to(root.resolve()).parts
        except ValueError:
            rel_parts = ()
        is_sibling = (
            (len(rel_parts) >= 1 and rel_parts[0] == pkg_name)
            or (len(rel_parts) >= 2 and rel_parts[0] == "src" and rel_parts[1] == pkg_name)
        )
        if is_sibling:
            return ("sibling_package", "R3_first_party_sibling", resolved)
        return ("internal_helper", "R4_internal_helper", resolved)

    return ("third_party", "R5_third_party_kept", None)


def _audit_imports(
    root: pathlib.Path, version_label: str, pkg_name: str = "chardet",
) -> list[dict]:
    """Return one audit-row dict per imported module name in `root`.

    Each row is {module, version, origin, kept_for_jaccard, rule_id,
    resolved_path}. Sorted by module name (case-insensitive) so the
    appendix table is reproducible.
    """
    names = _collect_raw_imports(root)
    rows: list[dict] = []
    for name in sorted(names, key=str.lower):
        origin, rule_id, resolved = _classify_import(root, name, pkg_name)
        kept = rule_id == "R5_third_party_kept"
        rows.append({
            "module": name,
            "version": version_label,
            "origin": origin,
            "kept_for_jaccard": "yes" if kept else "no",
            "rule_id": rule_id,
            "resolved_path": resolved.relative_to(root).as_posix() if resolved else "",
        })
    return rows


def _kept_set(audit_rows: list[dict]) -> set[str]:
    return {r["module"] for r in audit_rows if r["kept_for_jaccard"] == "yes"}


def signal_c06b_import_edges(
    v6: pathlib.Path, v7: pathlib.Path,
    pkg_a: str = "chardet", pkg_b: str = "chardet",
) -> dict:
    audit_a = _audit_imports(v6, "v6", pkg_a)
    audit_b = _audit_imports(v7, "v7", pkg_b)
    i6 = _kept_set(audit_a)
    i7 = _kept_set(audit_b)
    inter = i6 & i7
    union = i6 | i7
    jaccard = len(inter) / len(union) if union else 0.0
    return {
        "signal": "import_edge_set",
        "contract": "C06b",
        "expected": "report Jaccard overlap of third-party (non-stdlib, non-self) imports",
        "actual": f"jaccard={jaccard:.3f} shared={len(inter)} v6_only={len(i6 - i7)} v7_only={len(i7 - i6)}",
        "verdict": "MEASURED",
        "evidence": f"shared: {sorted(inter)}; v6_only: {sorted(i6 - i7)}; v7_only: {sorted(i7 - i6)}",
    }


def _emit_debug_imports_tsv(
    v6: pathlib.Path, v7: pathlib.Path, out_path: pathlib.Path,
    pkg_a: str = "chardet", pkg_b: str = "chardet",
) -> None:
    """Write the full per-module classification trace as TSV.

    Columns: module | version | origin | kept_for_jaccard | rule_id |
    resolved_path. Rows are sorted by (module lower-case, version).
    """
    rows = _audit_imports(v6, "v6", pkg_a) + _audit_imports(v7, "v7", pkg_b)
    rows.sort(key=lambda r: (r["module"].lower(), r["version"]))
    header = ["module", "version", "origin", "kept_for_jaccard", "rule_id", "resolved_path"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        fh.write("\t".join(header) + "\n")
        for r in rows:
            fh.write("\t".join(r[k] for k in header) + "\n")


# ----------------------------------------------------------------------------
# C06c — control-flow histogram
# ----------------------------------------------------------------------------

_CONTROL_FLOW_NODES = (
    ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler, ast.Raise,
    ast.With, ast.AsyncWith, ast.AsyncFor, ast.Return, ast.Yield, ast.YieldFrom,
)
if hasattr(ast, "Match"):  # py 3.10+
    _CONTROL_FLOW_NODES = (*_CONTROL_FLOW_NODES, ast.Match)


def _control_flow_histogram(root: pathlib.Path) -> Counter[str]:
    hist: Counter[str] = Counter()
    for p in iter_impl_py_files(root):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            for cls in _CONTROL_FLOW_NODES:
                if isinstance(node, cls):
                    hist[cls.__name__] += 1
                    break
    return hist


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(v ** 2 for v in a.values()))
    nb = math.sqrt(sum(v ** 2 for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def signal_c06c_control_flow(v6: pathlib.Path, v7: pathlib.Path) -> dict:
    h6 = _control_flow_histogram(v6)
    h7 = _control_flow_histogram(v7)
    total6 = sum(h6.values()) or 1
    total7 = sum(h7.values()) or 1
    n6 = {k: v / total6 for k, v in h6.items()}
    n7 = {k: v / total7 for k, v in h7.items()}
    cos = _cosine(n6, n7)
    top_terms = sorted(set(h6) | set(h7), key=lambda k: -(h6.get(k, 0) + h7.get(k, 0)))[:6]
    return {
        "signal": "control_flow_histogram",
        "contract": "C06c",
        "expected": "report cosine similarity of normalised AST control-flow histograms",
        "actual": f"cosine={cos:.3f} v6_total={sum(h6.values())} v7_total={sum(h7.values())}",
        "verdict": "MEASURED",
        "evidence": "; ".join(f"{k}: v6={h6.get(k, 0)} v7={h7.get(k, 0)}" for k in top_terms),
    }


# ----------------------------------------------------------------------------
# C06d — public-API signature equivalence
# ----------------------------------------------------------------------------

def _collect_public_signatures(root: pathlib.Path, pkg_name: str = "chardet") -> dict[str, dict]:
    """Return {public_symbol_name: signature_descriptor} for everything
    re-exported by <pkg_name>/__init__.py via `__all__`."""
    init_candidates = [
        root / pkg_name / "__init__.py",
        root / "src" / pkg_name / "__init__.py",
    ]
    init = next((p for p in init_candidates if p.is_file()), None)
    if init is None:
        return {}
    try:
        init_tree = ast.parse(init.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, UnicodeDecodeError):
        return {}
    all_names: set[str] = set()
    import_origins: dict[str, str] = {}  # name -> module path (relative)
    for node in init_tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
            and isinstance(node.value, (ast.List, ast.Tuple))
        ):
            for elt in node.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    all_names.add(elt.value)
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                local_name = alias.asname or alias.name
                import_origins[local_name] = node.module

    sigs: dict[str, dict] = {}
    # Add signatures of locally-defined public names first.
    for node in init_tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in all_names:
            sigs[node.name] = _describe_signature(node)
        elif isinstance(node, ast.ClassDef) and node.name in all_names:
            sigs[node.name] = {"kind": "class", "args": [], "defaults": 0, "kw_only": 0, "returns": False}
    # For names that came from a submodule import, walk that submodule.
    for name in all_names - set(sigs):
        origin = import_origins.get(name)
        if not origin:
            sigs[name] = {"kind": "unknown", "args": [], "defaults": 0, "kw_only": 0, "returns": False}
            continue
        # Resolve origin (e.g. chardet._utils, chardet.detector) -> file path.
        rel = origin.replace(".", "/") + ".py"
        for base in (root / "src", root):
            candidate = base / rel
            if candidate.is_file():
                try:
                    sub_tree = ast.parse(candidate.read_text(encoding="utf-8", errors="replace"))
                except (SyntaxError, UnicodeDecodeError):
                    continue
                for node in sub_tree.body:
                    if isinstance(node, ast.FunctionDef) and node.name == name:
                        sigs[name] = _describe_signature(node)
                        break
                    if isinstance(node, ast.ClassDef) and node.name == name:
                        sigs[name] = {"kind": "class", "args": [], "defaults": 0, "kw_only": 0, "returns": False}
                        break
                if name in sigs:
                    break
        sigs.setdefault(name, {"kind": "unknown", "args": [], "defaults": 0, "kw_only": 0, "returns": False})
    return sigs


def _describe_signature(node: ast.FunctionDef) -> dict:
    args = node.args
    pos_arg_count = len(args.args)
    kw_only_count = len(args.kwonlyargs)
    defaults = len(args.defaults) + len([d for d in args.kw_defaults if d is not None])
    returns = node.returns is not None
    return {
        "kind": "function",
        "args": [a.arg for a in args.args],
        "kw_only": kw_only_count,
        "defaults": defaults,
        "returns": returns,
        "pos_arg_count": pos_arg_count,
    }


def _signature_match(a: dict, b: dict) -> str:
    if a == b:
        return "strict"
    if a.get("kind") != b.get("kind"):
        return "diverged"
    # Same kind, same arg count, same default count, same return annotation
    # presence, BUT different arg names — "renamed" (still preserves contract
    # shape).
    if (a.get("pos_arg_count") == b.get("pos_arg_count")
            and a.get("kw_only") == b.get("kw_only")
            and a.get("defaults") == b.get("defaults")
            and a.get("returns") == b.get("returns")):
        return "renamed_args"
    return "diverged"




# ----------------------------------------------------------------------------
# C06d (per-method extension) — walk class bodies and compare each method.
#
# Added in v2 in response to reviewer R4: "the class-level 'diverged' verdict
# without per-method inspection is a blind spot — a class might be 90% strict
# at the method level with a couple of signature shifts, and rolling that up
# to one 'diverged' label hides what is actually going on." The extension
# below walks every public class exported from `__all__` in both versions
# AND emits, for each name-equal method pair, a strict / renamed_args /
# diverged verdict computed from {signature, raised exception types,
# return annotation, documented public attributes}.
#
# AST-only. No runtime import. Method matching is name-equal (a renamed-
# method matcher is deferred to a future revision).
# ----------------------------------------------------------------------------


def _annotation_text(node: ast.AST | None) -> str | None:
    """Render an annotation AST back to source-style text for comparison.

    We use ast.unparse (py3.9+) which gives a stable textual form. The
    text comparison is the equivalence relation we use — two annotations
    are 'identical' iff their unparse strings match, modulo a small set
    of normalisations (Optional[X] vs X | None, Union[X, Y] vs X | Y)."""
    if node is None:
        return None
    try:
        raw = ast.unparse(node)
    except Exception:
        return None
    # Normalise the two common Optional / Union spellings so PEP-604 union
    # syntax in v7 doesn't look like a divergence from typing.Optional in v6.
    return _normalise_annotation(raw)


def _normalise_annotation(text: str) -> str:
    """Best-effort normalisation: Optional[X] -> X | None;
    Union[A, B] -> A | B; collapse whitespace.

    Done with string parsing because the goal is comparison stability for
    a small, well-known set of annotations in the chardet public API, not
    full type-theoretic equivalence."""
    s = " ".join(text.split())
    # Optional[X] -> X | None
    while True:
        i = s.find("Optional[")
        if i < 0:
            break
        # find matching ]
        depth = 0
        j = i + len("Optional[")
        start = j
        while j < len(s):
            if s[j] == "[":
                depth += 1
            elif s[j] == "]":
                if depth == 0:
                    break
                depth -= 1
            j += 1
        if j >= len(s):
            break
        inner = s[start:j]
        s = s[:i] + inner + " | None" + s[j + 1:]
    # Union[A, B, ...] -> A | B | ...
    while True:
        i = s.find("Union[")
        if i < 0:
            break
        depth = 0
        j = i + len("Union[")
        start = j
        while j < len(s):
            if s[j] == "[":
                depth += 1
            elif s[j] == "]":
                if depth == 0:
                    break
                depth -= 1
            j += 1
        if j >= len(s):
            break
        inner = s[start:j]
        # split inner on top-level commas
        parts: list[str] = []
        depth2 = 0
        buf = ""
        for ch in inner:
            if ch == "," and depth2 == 0:
                parts.append(buf.strip())
                buf = ""
            else:
                if ch == "[":
                    depth2 += 1
                elif ch == "]":
                    depth2 -= 1
                buf += ch
        if buf.strip():
            parts.append(buf.strip())
        s = s[:i] + " | ".join(parts) + s[j + 1:]
    return " ".join(s.split())


def _describe_method(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict:
    """Describe a single method for cross-version comparison.

    Returns a dict with:
      * positional arg names (excluding `self`),
      * positional arg count,
      * keyword-only arg names,
      * keyword-only arg count,
      * default counts (positional + kw-only),
      * vararg / kwarg presence,
      * normalised return annotation text (None if not annotated),
      * sorted tuple of statically-visible raised exception type names
        (best-effort: any `raise Foo(...)` or `raise Foo` in the body).
    """
    args = node.args
    pos_args = [a.arg for a in args.args]
    if pos_args and pos_args[0] in ("self", "cls"):
        pos_args = pos_args[1:]
    kw_only = [a.arg for a in args.kwonlyargs]
    pos_defaults = len(args.defaults)
    kw_defaults = len([d for d in args.kw_defaults if d is not None])
    has_vararg = args.vararg is not None
    has_kwarg = args.kwarg is not None
    return_anno = _annotation_text(node.returns)

    raised: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Raise) and child.exc is not None:
            exc = child.exc
            if isinstance(exc, ast.Call):
                exc = exc.func
            if isinstance(exc, ast.Name):
                raised.add(exc.id)
            elif isinstance(exc, ast.Attribute):
                raised.add(exc.attr)
        elif isinstance(child, ast.Raise) and child.exc is None:
            # bare `raise` (re-raise inside except) — record a sentinel
            raised.add("<bare-reraise>")

    return {
        "kind": "method",
        "name": node.name,
        "pos_args": pos_args,
        "pos_arg_count": len(pos_args),
        "kw_only_args": kw_only,
        "kw_only_count": len(kw_only),
        "pos_defaults": pos_defaults,
        "kw_defaults": kw_defaults,
        "has_vararg": has_vararg,
        "has_kwarg": has_kwarg,
        "return_annotation": return_anno,
        "raised": sorted(raised),
    }


def _describe_class_attributes(node: ast.ClassDef) -> list[str]:
    """Extract the names of attributes declared at class-body level or
    assigned inside `__init__` via `self.<name> = ...`.

    Public attributes only (not starting with underscore)."""
    attrs: set[str] = set()
    for child in node.body:
        # Class-body assignments: `name = value` or `name: T = value`.
        if isinstance(child, ast.Assign):
            for tgt in child.targets:
                if isinstance(tgt, ast.Name) and not tgt.id.startswith("_"):
                    attrs.add(tgt.id)
        elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
            if not child.target.id.startswith("_"):
                attrs.add(child.target.id)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == "__init__":
            for sub in ast.walk(child):
                if isinstance(sub, ast.Assign):
                    for tgt in sub.targets:
                        if (isinstance(tgt, ast.Attribute)
                                and isinstance(tgt.value, ast.Name)
                                and tgt.value.id == "self"
                                and not tgt.attr.startswith("_")):
                            attrs.add(tgt.attr)
                elif isinstance(sub, ast.AnnAssign):
                    tgt = sub.target
                    if (isinstance(tgt, ast.Attribute)
                            and isinstance(tgt.value, ast.Name)
                            and tgt.value.id == "self"
                            and not tgt.attr.startswith("_")):
                        attrs.add(tgt.attr)
    return sorted(attrs)


def _method_match(m6: dict, m7: dict) -> str:
    """Classify a (v6, v7) method pair.

    strict        — signature, return annotation, raised-exception set
                    are all identical (or both absent).
    renamed_args  — positional structure (count + defaults + vararg/kwarg
                    presence) is identical, return annotation matches,
                    raised-exception set matches, but positional or
                    kw-only arg NAMES differ.
    diverged      — anything else."""
    raised_eq = set(m6.get("raised", [])) == set(m7.get("raised", []))
    return_eq = (m6.get("return_annotation") == m7.get("return_annotation"))

    if m6 == m7:
        return "strict"

    structure_eq = (
        m6.get("pos_arg_count") == m7.get("pos_arg_count")
        and m6.get("kw_only_count") == m7.get("kw_only_count")
        and m6.get("pos_defaults") == m7.get("pos_defaults")
        and m6.get("kw_defaults") == m7.get("kw_defaults")
        and m6.get("has_vararg") == m7.get("has_vararg")
        and m6.get("has_kwarg") == m7.get("has_kwarg")
    )
    if structure_eq and return_eq and raised_eq:
        # Same shape but different identifier names — renamed_args.
        return "renamed_args"
    return "diverged"


def _aggregate_class_verdict(per_method: dict[str, str], removed: list[str], added: list[str]) -> str:
    """Roll up a per-method verdict map plus removed/added method lists
    into a single class-level verdict.

    Worst-of policy:
      * If any method is `diverged`, OR any method was removed in v7,
        OR any method was added in v7, the class is `diverged`.
        (We treat added v7 methods conservatively: a NEW public method
        in v7 IS a public-API contract change. However, see below: we
        only count public methods, so v7-internal helpers don't count.)
      * Else if any method is `renamed_args`, the class is `renamed_args`.
      * Else the class is `strict`."""
    if removed:
        return "diverged"
    if added:
        return "diverged"
    verdicts = set(per_method.values())
    if "diverged" in verdicts:
        return "diverged"
    if "renamed_args" in verdicts:
        return "renamed_args"
    return "strict"


def _resolve_module_path(root: pathlib.Path, dotted: str) -> pathlib.Path | None:
    """Resolve `chardet.detector` to an actual .py file under either
    `<root>/<module>.py` or `<root>/src/<module>.py`."""
    rel = dotted.replace(".", "/") + ".py"
    for base in (root, root / "src"):
        candidate = base / rel
        if candidate.is_file():
            return candidate
    return None


def _collect_public_classes(
    root: pathlib.Path, pkg_name: str = "chardet",
) -> dict[str, ast.ClassDef]:
    """For each class name in `__all__`, return its AST ClassDef.

    Looks under `<root>/<pkg_name>/__init__.py` and `<root>/src/<pkg_name>/__init__.py`
    (Q×E parametrisation for multi-pair calibration), parses the `__all__`
    list and follows `from <pkg_name>.<mod> import Name` edges to the
    defining module. Names with no resolvable definition (e.g. they refer
    to a re-export from a submodule that doesn't expose them as a class,
    or to a non-class symbol) are simply skipped.
    """
    init_candidates = [
        root / pkg_name / "__init__.py",
        root / "src" / pkg_name / "__init__.py",
    ]
    init = next((p for p in init_candidates if p.is_file()), None)
    if init is None:
        return {}
    try:
        init_tree = ast.parse(init.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, UnicodeDecodeError):
        return {}

    all_names: set[str] = set()
    import_origins: dict[str, str] = {}
    for node in init_tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
            and isinstance(node.value, (ast.List, ast.Tuple))
        ):
            for elt in node.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    all_names.add(elt.value)
        if isinstance(node, ast.ImportFrom) and node.module:
            # Relative imports (`from .enums import EncodingEra`) carry
            # node.level >= 1 and node.module == "enums"; we resolve them
            # under the chardet/ package directory. Absolute imports
            # (`from chardet.detector import UniversalDetector`) carry
            # node.level == 0 and node.module == "chardet.detector".
            level = node.level or 0
            if level > 0:
                # Resolve relative to the package containing __init__.py.
                module = f"{pkg_name}.{node.module}"
            else:
                module = node.module
            for alias in node.names:
                local_name = alias.asname or alias.name
                import_origins[local_name] = module

    out: dict[str, ast.ClassDef] = {}

    # Locally-defined classes in __init__.py.
    for node in init_tree.body:
        if isinstance(node, ast.ClassDef) and node.name in all_names:
            out[node.name] = node

    # Classes imported from submodules.
    for name in all_names - set(out):
        origin = import_origins.get(name)
        if not origin:
            continue
        mod_path = _resolve_module_path(root, origin)
        if mod_path is None:
            continue
        try:
            sub_tree = ast.parse(mod_path.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in sub_tree.body:
            if isinstance(node, ast.ClassDef) and node.name == name:
                out[name] = node
                break

    return out


def _enumerate_public_methods(cls: ast.ClassDef) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    """Return {method_name: FunctionDef} for every method defined directly
    in the class body. Public = does not start with `_` EXCEPT for the
    `__init__` / `__call__` / `__enter__` / `__exit__` / `__iter__` /
    `__next__` / `__len__` / `__repr__` dunder methods which are part of
    the documented public API."""
    PUBLIC_DUNDERS = {
        "__init__", "__call__", "__enter__", "__exit__",
        "__iter__", "__next__", "__len__", "__repr__",
        "__getitem__", "__setitem__", "__contains__",
    }
    out: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for child in cls.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if child.name.startswith("_") and child.name not in PUBLIC_DUNDERS:
                continue
            out[child.name] = child
    return out


def per_method_class_analysis(
    v6: pathlib.Path, v7: pathlib.Path,
    pkg_a: str = "chardet", pkg_b: str = "chardet",
) -> dict:
    """Per-method analysis of every public-API class in v6 vs v7.

    pkg_a / pkg_b name the top-level package on each side (Q×E
    parametrisation for multi-pair calibration).

    For each public class defined in v6's `__all__`:
      * Resolve the v7 class with the same name (if missing, the class is
        `removed` and skipped from the per-method comparison).
      * Enumerate public methods on both sides.
      * Classify every name-equal method pair as strict / renamed_args /
        diverged.
      * Roll up to a class-level verdict via worst-of.

    Returns the structured result described in v2 contract C06d:
        {
          "classes": [
            {
              "class_name": ...,
              "v6_methods": [...],
              "v7_methods": [...],
              "removed_in_v7": [...],
              "added_in_v7": [...],
              "per_method_verdicts": {name: verdict},
              "v6_attributes": [...],
              "v7_attributes": [...],
              "removed_attributes": [...],
              "added_attributes": [...],
              "class_aggregate": verdict,
            }, ...
          ],
          "rollup": {strict, renamed_args, diverged, removed_class}
        }
    """
    v6_classes = _collect_public_classes(v6, pkg_a)
    v7_classes = _collect_public_classes(v7, pkg_b)
    # Per task: walk every public class in v6 AND v7 (union by name).
    all_class_names = sorted(set(v6_classes) | set(v7_classes))

    classes_out: list[dict] = []
    rollup: Counter[str] = Counter()
    for name in all_class_names:
        c6 = v6_classes.get(name)
        c7 = v7_classes.get(name)
        if c6 is None:
            classes_out.append({
                "class_name": name,
                "v6_methods": [],
                "v7_methods": sorted(_enumerate_public_methods(c7) if c7 else {}),
                "removed_in_v7": [],
                "added_in_v7": sorted(_enumerate_public_methods(c7) if c7 else {}),
                "per_method_verdicts": {},
                "v6_attributes": [],
                "v7_attributes": _describe_class_attributes(c7) if c7 else [],
                "removed_attributes": [],
                "added_attributes": _describe_class_attributes(c7) if c7 else [],
                "class_aggregate": "added_in_v7",
            })
            rollup["added_in_v7"] += 1
            continue
        if c7 is None:
            classes_out.append({
                "class_name": name,
                "v6_methods": sorted(_enumerate_public_methods(c6)),
                "v7_methods": [],
                "removed_in_v7": sorted(_enumerate_public_methods(c6)),
                "added_in_v7": [],
                "per_method_verdicts": {},
                "v6_attributes": _describe_class_attributes(c6),
                "v7_attributes": [],
                "removed_attributes": _describe_class_attributes(c6),
                "added_attributes": [],
                "class_aggregate": "removed_class",
            })
            rollup["removed_class"] += 1
            continue

        m6 = _enumerate_public_methods(c6)
        m7 = _enumerate_public_methods(c7)
        removed = sorted(set(m6) - set(m7))
        added = sorted(set(m7) - set(m6))
        per_method_verdicts: dict[str, str] = {}
        for meth_name in sorted(set(m6) & set(m7)):
            d6 = _describe_method(m6[meth_name])
            d7 = _describe_method(m7[meth_name])
            per_method_verdicts[meth_name] = _method_match(d6, d7)

        a6 = _describe_class_attributes(c6)
        a7 = _describe_class_attributes(c7)
        agg = _aggregate_class_verdict(per_method_verdicts, removed, added)
        rollup[agg] += 1

        classes_out.append({
            "class_name": name,
            "v6_methods": sorted(m6),
            "v7_methods": sorted(m7),
            "removed_in_v7": removed,
            "added_in_v7": added,
            "per_method_verdicts": per_method_verdicts,
            "v6_attributes": a6,
            "v7_attributes": a7,
            "removed_attributes": sorted(set(a6) - set(a7)),
            "added_attributes": sorted(set(a7) - set(a6)),
            "class_aggregate": agg,
        })

    return {"classes": classes_out, "rollup": dict(rollup)}


def signal_c06d_signature_equivalence(
    v6: pathlib.Path, v7: pathlib.Path,
    pkg_a: str = "chardet", pkg_b: str = "chardet",
) -> dict:
    s6 = _collect_public_signatures(v6, pkg_a)
    s7 = _collect_public_signatures(v7, pkg_b)
    common = sorted(set(s6) & set(s7))

    # V2 extension (agent E): walk class bodies and classify per-method.
    # The class-level rollup is computed via worst-of over the per-method
    # verdicts. See per_method_class_analysis() docstring for the precise
    # definition. pkg_a/pkg_b parametrise the side-specific package name
    # (Q×E integration: charset_normalizer package on side B for the
    # v6_charset_norm pair).
    per_method = per_method_class_analysis(v6, v7, pkg_a, pkg_b)

    if not common:
        return {
            "signal": "public_api_signature_equivalence",
            "contract": "C06d",
            "expected": "report counts of strict / renamed_args / diverged matches across shared __all__ symbols",
            "actual": f"v6_public={len(s6)} v7_public={len(s7)} shared=0",
            "verdict": "INCONCLUSIVE",
            "evidence": "no public symbols are present in both versions' __all__",
            "per_method": per_method,
        }
    breakdown = Counter(_signature_match(s6[name], s7[name]) for name in common)
    examples = [f"{name}={_signature_match(s6[name], s7[name])}" for name in common[:8]]
    cls_rollup = per_method.get("rollup", {})
    cls_summary = (
        f"per_method_classes: strict={cls_rollup.get('strict', 0)} "
        f"renamed_args={cls_rollup.get('renamed_args', 0)} "
        f"diverged={cls_rollup.get('diverged', 0)}"
    )
    return {
        "signal": "public_api_signature_equivalence",
        "contract": "C06d",
        "expected": "report strict / renamed_args / diverged counts across shared __all__ symbols PLUS per-method verdicts for every public class",
        "actual": f"shared={len(common)} strict={breakdown.get('strict', 0)} renamed_args={breakdown.get('renamed_args', 0)} diverged={breakdown.get('diverged', 0)}; {cls_summary}",
        "verdict": "MEASURED",
        "evidence": "; ".join(examples + [
            f"class[{c['class_name']}]={c['class_aggregate']} "
            f"({sum(1 for v in c['per_method_verdicts'].values() if v == 'strict')}-strict/"
            f"{sum(1 for v in c['per_method_verdicts'].values() if v == 'renamed_args')}-renamed/"
            f"{sum(1 for v in c['per_method_verdicts'].values() if v == 'diverged')}-diverged"
            f"; removed={len(c['removed_in_v7'])}; added={len(c['added_in_v7'])})"
            for c in per_method["classes"]
        ]),
        "per_method": per_method,
    }



# ----------------------------------------------------------------------------
# C06e — behavioural fingerprint (placeholder; full implementation is in
# fingerprint_behavior.py which manages two venvs and shells out)
# ----------------------------------------------------------------------------

def signal_c06e_behavioural_skip(v6: pathlib.Path, v7: pathlib.Path) -> dict:
    """Static-AST signals don't measure runtime behaviour. The
    behavioural-fingerprint signal is delegated to fingerprint_behavior.py
    which installs both versions in isolated venvs and compares outputs
    on a deterministic fuzz corpus. This row is a placeholder so the
    six-row promise holds; the harness runs the real script alongside."""
    return {
        "signal": "behavioural_fingerprint",
        "contract": "C06e",
        "expected": "delegated to fingerprint_behavior.py — see SUMMARY block",
        "actual": "see fingerprint_behavior.py output appended below",
        "verdict": "DELEGATED",
        "evidence": "fingerprint_behavior.py installs both versions in isolated venvs and compares outputs on a deterministic 1000-input fuzz corpus",
    }


# ----------------------------------------------------------------------------
# driver
# ----------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # New pair-agnostic flags (preferred).
    parser.add_argument("--root-a", dest="root_a", help="checkout of side A of the pair")
    parser.add_argument("--root-b", dest="root_b", help="checkout of side B of the pair")
    parser.add_argument("--pkg-a", dest="pkg_a", default="chardet",
                        help="top-level package name on side A (for C06b self-exclusion + C06d API surface)")
    parser.add_argument("--pkg-b", dest="pkg_b", default="chardet",
                        help="top-level package name on side B")
    # Legacy aliases retained for v1-era invocations.
    parser.add_argument("--v6-root", dest="v6_root", help="alias for --root-a (legacy)")
    parser.add_argument("--v7-root", dest="v7_root", help="alias for --root-b (legacy)")
    parser.add_argument(
        "--debug-imports",
        metavar="TSV_PATH",
        help=(
            "Write the full C06b import-classification trace to TSV at "
            "TSV_PATH (columns: module, version, origin, kept_for_jaccard, "
            "rule_id, resolved_path). Each row's rule_id is one of "
            "R1_stdlib / R2_first_party_self / R3_first_party_sibling / "
            "R4_internal_helper / R5_third_party_kept, defined in the "
            "module-level _classify_import docstring."
        ),
    )
    args = parser.parse_args()

    root_a_str = args.root_a or args.v6_root
    root_b_str = args.root_b or args.v7_root
    if not root_a_str or not root_b_str:
        parser.error("must supply --root-a/--root-b (or legacy --v6-root/--v7-root)")

    v6 = pathlib.Path(root_a_str).resolve()
    v7 = pathlib.Path(root_b_str).resolve()
    if not v6.is_dir():
        print(f"error: --root-a {v6} is not a directory", file=sys.stderr)
        return 2
    if not v7.is_dir():
        print(f"error: --root-b {v7} is not a directory", file=sys.stderr)
        return 2

    pkg_a, pkg_b = args.pkg_a, args.pkg_b

    if args.debug_imports:
        _emit_debug_imports_tsv(v6, v7, pathlib.Path(args.debug_imports), pkg_a, pkg_b)

    signals = [
        signal_aux1_literal_carry(v6, v7),
        signal_c06a_call_graph(v6, v7),
        signal_c06a_prime_wl_kernel(v6, v7),
        signal_c06b_import_edges(v6, v7, pkg_a, pkg_b),
        signal_c06c_control_flow(v6, v7),
        signal_c06d_signature_equivalence(v6, v7, pkg_a, pkg_b),
        signal_c06e_behavioural_skip(v6, v7),
        signal_c06f_per_function_shape(v6, v7),
    ]

    print("signal\tcontract\texpected\tactual\tverdict\tevidence")
    for s in signals:
        print(
            f"{s['signal']}\t{s['contract']}\t{s['expected']}\t"
            f"{s['actual']}\t{s['verdict']}\t{s['evidence']}"
        )
    # NB: the SUMMARY block is intentionally NOT emitted here. detect.sh
    # appends the real C06e row from fingerprint_behavior.py after this
    # script returns, then computes the final SUMMARY across the
    # complete row set. Emitting a SUMMARY here would undercount C06e
    # (Codex round-1 review finding).
    return 1 if Counter(s["verdict"] for s in signals).get("FAIL", 0) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
