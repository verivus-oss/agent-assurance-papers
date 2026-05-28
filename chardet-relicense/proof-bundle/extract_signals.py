#!/usr/bin/env python3
"""extract_signals.py — five AST-level signals + one auxiliary baseline
for the chardet v6 → v7 relicensing proof.

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


_PKG_SELF: frozenset[str] = frozenset({"chardet"})


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
                    if alias.name:
                        out.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue  # relative import — internal, not an edge
                if node.module:
                    out.add(node.module.split(".")[0])
    return {m for m in out if m}


def _module_resolves_inside(root: pathlib.Path, name: str) -> pathlib.Path | None:
    """Return the first on-disk path under `root` that an absolute import
    of `name` could resolve to as a Python module, or None.

    Resolution candidates considered, in order:
        1. Inside the chardet package directory itself (sibling submodule).
        2. As a top-level `.py` file or package directory at the repo
           root (sibling helper script).
        3. As a `.py` file or package directory inside any sibling
           top-level directory of the repo (e.g. `scripts/<name>.py`,
           `tools/<name>/__init__.py`).

    The check is a pure filesystem lookup; no import machinery is
    invoked, so the rule is re-derivable from the cloned source tree
    alone with no environment side-effects.
    """
    # Locate the chardet package directory if present, for R3 checks.
    chardet_pkg_candidates = [root / "chardet", root / "src" / "chardet"]
    chardet_pkg = next((d for d in chardet_pkg_candidates if d.is_dir()), None)

    # R3 — chardet sibling submodule.
    if chardet_pkg is not None:
        for suffix in (f"{name}.py", name):
            candidate = chardet_pkg / suffix
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
    # Bounded to depth-1 directories under root to keep the rule cheap
    # and deterministic. Skips dot-directories and known non-source
    # buckets so that worktree metadata cannot influence the result.
    skip = {"__pycache__", "build", "dist", ".tox", ".venv", "tests", "test", "docs"}
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name in skip:
            continue
        if chardet_pkg is not None and child == chardet_pkg.parent and child.name == "src":
            # src/chardet already covered above; skip plain src/ helper
            # files that aren't inside the chardet package.
            for sub_suffix in (f"{name}.py", name):
                sub_candidate = child / sub_suffix
                if sub_candidate == chardet_pkg:
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


def _classify_import(root: pathlib.Path, name: str) -> tuple[str, str, pathlib.Path | None]:
    """Classify `name` against the source tree at `root`.

    Returns (origin, rule_id, resolved_path):
        origin     — one of stdlib / first_party_chardet / sibling_package /
                     internal_helper / third_party
        rule_id    — R1_stdlib / R2_first_party_self / R3_first_party_sibling /
                     R4_internal_helper / R5_third_party_kept
        resolved_path — filesystem path the name resolved to inside `root`
                     for R3/R4, or None for R1/R2/R5.

    Rule precedence (first match wins):
        R1_stdlib              — `name in sys.stdlib_module_names`
        R2_first_party_self    — name == "chardet"
        R3_first_party_sibling — resolves inside `<root>/[src/]chardet/`
        R4_internal_helper     — resolves elsewhere inside the cloned tree
        R5_third_party_kept    — does not resolve anywhere in `root`

    Only R5 imports are kept for the Jaccard computation. R3 and R4 are
    re-derivable by re-running this filesystem check against any clone
    of the chardet repo at the relevant tag.
    """
    if name in _STDLIB_HINT:
        return ("stdlib", "R1_stdlib", None)
    if name in _PKG_SELF:
        return ("first_party_chardet", "R2_first_party_self", None)

    resolved = _module_resolves_inside(root, name)
    if resolved is not None:
        # R3 if the resolved path lives inside the chardet/ package dir
        # *within `root`*; otherwise R4 (sibling helper script). We use
        # path-relative-to-root + a fixed package-dir prefix rather than
        # an absolute-path segment scan, so a clone living under any
        # parent directory (including one called "chardet/") is
        # classified consistently. The package dir is either
        # `<root>/chardet/...` (the legacy layout) or
        # `<root>/src/chardet/...` (the src-layout used by v7).
        try:
            rel_parts = resolved.resolve().relative_to(root.resolve()).parts
        except ValueError:
            rel_parts = ()
        is_sibling = (
            (len(rel_parts) >= 1 and rel_parts[0] == "chardet")
            or (len(rel_parts) >= 2 and rel_parts[0] == "src" and rel_parts[1] == "chardet")
        )
        if is_sibling:
            return ("sibling_package", "R3_first_party_sibling", resolved)
        return ("internal_helper", "R4_internal_helper", resolved)

    return ("third_party", "R5_third_party_kept", None)


def _audit_imports(root: pathlib.Path, version_label: str) -> list[dict]:
    """Return one audit-row dict per imported module name in `root`.

    Each row is {module, version, origin, kept_for_jaccard, rule_id,
    resolved_path}. Sorted by module name (case-insensitive) so the
    appendix table is reproducible.
    """
    names = _collect_raw_imports(root)
    rows: list[dict] = []
    for name in sorted(names, key=str.lower):
        origin, rule_id, resolved = _classify_import(root, name)
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


def signal_c06b_import_edges(v6: pathlib.Path, v7: pathlib.Path) -> dict:
    audit6 = _audit_imports(v6, "v6")
    audit7 = _audit_imports(v7, "v7")
    i6 = _kept_set(audit6)
    i7 = _kept_set(audit7)
    inter = i6 & i7
    union = i6 | i7
    jaccard = len(inter) / len(union) if union else 0.0
    return {
        "signal": "import_edge_set",
        "contract": "C06b",
        "expected": "report Jaccard overlap of third-party imports under audit rules R1..R5",
        "actual": f"jaccard={jaccard:.3f} shared={len(inter)} v6_only={len(i6 - i7)} v7_only={len(i7 - i6)}",
        "verdict": "MEASURED",
        "evidence": f"shared: {sorted(inter)}; v6_only: {sorted(i6 - i7)}; v7_only: {sorted(i7 - i6)}",
    }


def _emit_debug_imports_tsv(v6: pathlib.Path, v7: pathlib.Path, out_path: pathlib.Path) -> None:
    """Write the full per-module classification trace as TSV.

    Columns: module | version | origin | kept_for_jaccard | rule_id |
    resolved_path. Rows are sorted by (module lower-case, version).
    """
    rows = _audit_imports(v6, "v6") + _audit_imports(v7, "v7")
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

def _collect_public_signatures(root: pathlib.Path) -> dict[str, dict]:
    """Return {public_symbol_name: signature_descriptor} for everything
    re-exported by chardet/__init__.py via `__all__`."""
    init_candidates = [
        root / "chardet" / "__init__.py",
        root / "src" / "chardet" / "__init__.py",
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


def signal_c06d_signature_equivalence(v6: pathlib.Path, v7: pathlib.Path) -> dict:
    s6 = _collect_public_signatures(v6)
    s7 = _collect_public_signatures(v7)
    common = sorted(set(s6) & set(s7))
    if not common:
        return {
            "signal": "public_api_signature_equivalence",
            "contract": "C06d",
            "expected": "report counts of strict / renamed_args / diverged matches across shared __all__ symbols",
            "actual": f"v6_public={len(s6)} v7_public={len(s7)} shared=0",
            "verdict": "INCONCLUSIVE",
            "evidence": "no public symbols are present in both versions' __all__",
        }
    breakdown = Counter(_signature_match(s6[name], s7[name]) for name in common)
    examples = [f"{name}={_signature_match(s6[name], s7[name])}" for name in common[:8]]
    return {
        "signal": "public_api_signature_equivalence",
        "contract": "C06d",
        "expected": "report strict / renamed_args / diverged counts across shared __all__ symbols",
        "actual": f"shared={len(common)} strict={breakdown.get('strict', 0)} renamed_args={breakdown.get('renamed_args', 0)} diverged={breakdown.get('diverged', 0)}",
        "verdict": "MEASURED",
        "evidence": "; ".join(examples),
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
    parser.add_argument("--v6-root", required=True, help="checkout of chardet 6.0.0")
    parser.add_argument("--v7-root", required=True, help="checkout of chardet 7.0.0")
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

    v6 = pathlib.Path(args.v6_root).resolve()
    v7 = pathlib.Path(args.v7_root).resolve()
    if not v6.is_dir():
        print(f"error: --v6-root {v6} is not a directory", file=sys.stderr)
        return 2
    if not v7.is_dir():
        print(f"error: --v7-root {v7} is not a directory", file=sys.stderr)
        return 2

    if args.debug_imports:
        _emit_debug_imports_tsv(v6, v7, pathlib.Path(args.debug_imports))

    signals = [
        signal_aux1_literal_carry(v6, v7),
        signal_c06a_call_graph(v6, v7),
        signal_c06b_import_edges(v6, v7),
        signal_c06c_control_flow(v6, v7),
        signal_c06d_signature_equivalence(v6, v7),
        signal_c06e_behavioural_skip(v6, v7),
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
