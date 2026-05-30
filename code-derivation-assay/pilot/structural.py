"""Fuller-envelope structural measures for the CDA pilot — clean reimplementations
of call-graph topology, a Weisfeiler-Lehman call-graph kernel, and per-function
AST-shape matching (analogous to the predecessor's C06a / C06a' / C06f). Together
with the harness's shingle + control-flow + node-type histograms, these give a
6-measure structural envelope so the matcher-dependence is reported as a range,
not a single number.

NOT renaming-invariant (verification round 1): `build_call_graph` uses function
NAMES as node identity (`defined.add(n.name)`, edges by name), so the topology and
WL measures here are confounded by shared identifier vocabulary — the WL AUC=1.0 on
chardet is largely a name-vocabulary artifact, NOT a faithful WL kernel and NOT a
defensible structural signal (see PILOT-RESULTS.md envelope section + SPEC §5.2/§5.4).
Only `per_function_similarity`'s body-histogram is type-based (renaming-invariant);
the call-graph measures use names. The §7.3 invariance test is not implemented here."""
import ast
import math
import os
from collections import Counter, defaultdict

import networkx as nx


def _py_files(pkg_dir):
    out = []
    for r, _, fs in os.walk(pkg_dir):
        if 'test' in r.lower():
            continue
        out += [os.path.join(r, f) for f in fs if f.endswith('.py')]
    return out


def _trees(pkg_dir):
    for p in _py_files(pkg_dir):
        try:
            yield ast.parse(open(p, 'rb').read())
        except Exception:
            continue


# ---------- call graph (name-based, approximate) ----------
def build_call_graph(pkg_dir):
    trees = list(_trees(pkg_dir))
    defined = set()
    for t in trees:
        for n in ast.walk(t):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined.add(n.name)
    g = nx.DiGraph()
    g.add_nodes_from(defined)

    class V(ast.NodeVisitor):
        def __init__(self):
            self.stack = []

        def visit_FunctionDef(self, node):
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()
        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Call(self, node):
            f = node.func
            callee = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if callee in defined and self.stack:
                g.add_edge(self.stack[-1], callee)
            self.generic_visit(node)

    for t in trees:
        V().visit(t)
    return g


_FEATURES = ('density', 'scc_ratio', 'mean_in', 'max_in', 'mean_out', 'max_out')


def _topo_features(g):
    if g.number_of_nodes() == 0:
        return {f: 0.0 for f in _FEATURES}
    ind = [d for _, d in g.in_degree()]
    outd = [d for _, d in g.out_degree()]
    return {
        'density': nx.density(g),
        'scc_ratio': nx.number_strongly_connected_components(g) / g.number_of_nodes(),
        'mean_in': sum(ind) / len(ind), 'max_in': float(max(ind)),
        'mean_out': sum(outd) / len(outd), 'max_out': float(max(outd)),
    }


def _reldiff(a, b):
    return 0.0 if a == 0 and b == 0 else abs(a - b) / (abs(a) + abs(b))


def topology_similarity(ga, gb):
    """C06a analog: 1 - mean symmetric relative diff over topology features."""
    fa, fb = _topo_features(ga), _topo_features(gb)
    return 1.0 - sum(_reldiff(fa[f], fb[f]) for f in _FEATURES) / len(_FEATURES)


def wl_cosine(ga, gb, k=4):
    """C06a' analog: WL subtree kernel — cosine of the label multiset accumulated
    over k refinement iterations (degree-seeded, successor-aggregated)."""
    def labels(g):
        lab = {n: f'{g.in_degree(n)}_{g.out_degree(n)}' for n in g.nodes()}
        multiset = Counter(lab.values())
        for _ in range(k):
            new = {}
            for n in g.nodes():
                nb = '|'.join(sorted(lab[m] for m in g.successors(n)))
                new[n] = f'{lab[n]}>{nb}'
            lab = new
            multiset.update(lab.values())
        return multiset
    a, b = labels(ga), labels(gb)
    keys = set(a) | set(b)
    dot = sum(a.get(x, 0) * b.get(x, 0) for x in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


# ---------- per-function shape (C06f analog) ----------
def _sig_shape(node):
    a = node.args
    n_pos = len(a.args) + len(getattr(a, 'posonlyargs', []))
    return (n_pos, len(a.kwonlyargs), a.vararg is not None, a.kwarg is not None)


def collect_functions(pkg_dir):
    funcs = []
    for t in _trees(pkg_dir):
        for n in ast.walk(t):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                hist = Counter()
                for child in n.body:
                    for x in ast.walk(child):
                        hist[type(x).__name__] += 1
                funcs.append((_sig_shape(n), hist))
    return funcs


def _cos(a, b):
    keys = set(a) | set(b)
    dot = sum(a.get(x, 0) * b.get(x, 0) for x in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def per_function_similarity(fa, fb, thresh=0.5):
    """Greedy match functions across sides within the same signature-shape bucket,
    by body-histogram cosine; report mean cosine over matched pairs (names unused)."""
    bucket = defaultdict(list)
    for j, (s, h) in enumerate(fb):
        bucket[s].append(j)
    used, sims = set(), []
    for s, h in fa:
        best, bestj = -1.0, None
        for j in bucket.get(s, []):
            if j in used:
                continue
            c = _cos(h, fb[j][1])
            if c > best:
                best, bestj = c, j
        if bestj is not None and best >= thresh:
            used.add(bestj)
            sims.append(best)
    return (sum(sims) / len(sims) if sims else 0.0), len(sims), len(fa), len(fb)
