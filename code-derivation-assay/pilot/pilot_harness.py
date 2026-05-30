#!/usr/bin/env python3
"""
CDA PILOT harness (P0 pilot; SPECIFICATION.md §16 P0, power/POWER-ANALYSIS.md §7).

Iteration 2: STRENGTHENED BH with a *discriminating* workload (the cheapest
high-impact change after iteration 1 showed BH on an easy corpus doesn't
separate anything — correct independent detectors agree on clear inputs).

Goal: a first real within-domain signal read on the chardet trio, testing the
M1 prediction and producing a directional AUC. n=6 pairs, one domain — a
direction/sanity pilot, NOT a powered estimate.

Clean-slate (shares no code with the predecessor harness). Deterministic, offline.
Signals:
  ST   — per-function AST node-type 5-gram shingle overlap (renaming-invariant)
  PBt  — data-table literal carryover (big numeric/bytes literals → hashed → overlap)
  PBi  — import-boundary (external dependency set) Jaccard
  BH   — encoding agreement over the easy 64-file corpus (baseline, ~uninformative)
  BHd  — encoding agreement over the DISCRIMINATING subset of a hard workload
         (short/ambiguous bytes where detectors diverge → behavioural lineage shows)
Scope = package (mechanically resolved; handles v7's src/ layout vs v5/v6 top-level).
"""
import ast, os, sys, json, glob, math, io, re, tokenize, tempfile, subprocess, hashlib
from collections import Counter

# generic words filtered from comment/docstring/identifier quirk signals
_STOP = {'self', 'none', 'true', 'false', 'return', 'returns', 'true', 'this', 'that',
         'with', 'from', 'into', 'list', 'dict', 'type', 'value', 'data', 'name',
         'args', 'kwargs', 'param', 'params', 'default', 'object', 'string', 'bytes',
         'index', 'result', 'using', 'used', 'will', 'when', 'each', 'also', 'they',
         'class', 'method', 'function', 'number', 'count', 'length', 'size'}

# control-flow node types for the coarse structural histogram (predecessor C06c analog)
_CF = {'If', 'For', 'While', 'Try', 'ExceptHandler', 'Raise', 'With', 'AsyncWith',
       'AsyncFor', 'Return', 'Yield', 'YieldFrom', 'Match'}

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, '_detect_runner.py')
sys.path.insert(0, HERE)
import structural as S   # noqa: E402  (fuller-envelope call-graph / per-function measures)
CHARDET = '/srv/repos/public/spec-poc/chardet-relicense/chardet'
CSN = '/srv/repos/public/spec-poc/chardet-relicense/charset_normalizer'
CORPUS = '/srv/repos/external/verivus-oss/agent-assurance-papers/chardet-relicense/proof-bundle/corpora/items'
HARD = os.path.join(tempfile.gettempdir(), 'cda_hard_corpus')

IMPLS = [  # (id, repo, tag, pkgname, bh_kind)
    ('v5',  CHARDET, '5.0.0', 'chardet', 'chardet'),
    ('v6',  CHARDET, '6.0.0', 'chardet', 'chardet'),
    ('v7',  CHARDET, '7.0.0', 'chardet', 'chardet'),
    ('csn', CSN,     '3.4.7', 'charset_normalizer', 'csn'),
]
PAIRS = [
    ('v5', 'v6', 'EVOLVED'),
    ('v6', 'v7', 'DERIVED-airewrite'),
    ('v5', 'v7', 'DERIVED-distant'),
    ('v5', 'csn', 'INDEPENDENT'),
    ('v6', 'csn', 'INDEPENDENT'),
    ('v7', 'csn', 'INDEPENDENT'),
]


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True, capture_output=True)


def extract(repo, tag):
    d = tempfile.mkdtemp(prefix=f'cda_{tag}_')
    sh(f'git -C {repo} archive {tag} | tar -x -C {d}')
    return d


def find_pkg(root, pkgname):
    best = None
    for r, _, fs in os.walk(root):
        if os.path.basename(r) == pkgname and '__init__.py' in fs and 'test' not in r.lower():
            if best is None or len(r) < len(best):
                best = r
    return best


def pkg_py_files(pkg_dir):
    out = []
    for r, _, fs in os.walk(pkg_dir):
        if 'test' in r.lower():
            continue
        out += [os.path.join(r, f) for f in fs if f.endswith('.py')]
    return out


# ---------- static ----------
def struct_sig(node):
    out = []
    def visit(n):
        out.append(type(n).__name__)
        for c in ast.iter_child_nodes(n):
            visit(c)
    visit(node)
    return tuple(out)


def extract_static(pkg_dir, pkgname):
    func_sigs, tables, imports = Counter(), Counter(), set()
    cfg_hist, node_hist = Counter(), Counter()
    floats, messages = set(), set()
    for path in pkg_py_files(pkg_dir):
        try:
            tree = ast.parse(open(path, 'rb').read())
        except Exception:
            continue
        for n in ast.walk(tree):
            tn = type(n).__name__
            node_hist[tn] += 1
            if tn in _CF:
                cfg_hist[tn] += 1
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stream = struct_sig(n)
                K = 5
                for i in range(len(stream) - K + 1):
                    func_sigs[hashlib.blake2b(repr(stream[i:i + K]).encode(), digest_size=8).hexdigest()] += 1
            if isinstance(n, (ast.List, ast.Tuple, ast.Set)):
                vals = [e.value for e in n.elts
                        if isinstance(e, ast.Constant) and isinstance(e.value, (int, float))]
                if len(vals) >= 16:
                    tables[hashlib.blake2b(repr(tuple(vals)).encode(), digest_size=12).hexdigest()] += 1
            if isinstance(n, ast.Dict):
                vals = [k.value for k in n.keys
                        if isinstance(k, ast.Constant) and isinstance(k.value, (int, float))]
                if len(vals) >= 16:
                    tables[hashlib.blake2b(repr(tuple(vals)).encode(), digest_size=12).hexdigest()] += 1
            if isinstance(n, ast.Constant) and isinstance(n.value, (bytes, str)) and len(n.value) >= 64:
                tables[hashlib.blake2b(repr(n.value).encode(), digest_size=12).hexdigest()] += 1
            if isinstance(n, ast.Constant):           # provenance-quirk source features
                v = n.value
                if isinstance(v, float) and v not in (0.0, 1.0):
                    floats.add(round(v, 6))           # arbitrary tuning constants/thresholds
                elif isinstance(v, str) and 8 <= len(v) <= 200 and ' ' in v and v.isprintable():
                    messages.add(' '.join(v.lower().split()))   # human-readable messages
            if isinstance(n, ast.Import):
                for a in n.names:
                    imports.add(a.name.split('.')[0])
            if isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                imports.add(n.module.split('.')[0])
    imports.discard(pkgname)
    return func_sigs, tables, imports, cfg_hist, node_hist, floats, messages


def _words(text):
    return {w for w in re.findall(r'[a-zA-Z]{4,}', text.lower()) if w not in _STOP}


def extract_quirks(pkg_dir):
    """Legally-probative 'golden nugget' features (AFC) — arbitrary expression a
    clean reimplementation has no functional reason to share: identifiers,
    distinctive compound names, docstring words, comment words."""
    idents, doc_words, comment_words = set(), set(), set()
    for path in pkg_py_files(pkg_dir):
        try:
            src = open(path, 'rb').read()
            tree = ast.parse(src)
        except Exception:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Name):
                idents.add(n.id)
            elif isinstance(n, ast.Attribute):
                idents.add(n.attr)
            elif isinstance(n, ast.arg):
                idents.add(n.arg)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                idents.add(n.name)
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                d = ast.get_docstring(n)
                if d:
                    doc_words |= _words(d)
        try:
            for tok in tokenize.tokenize(io.BytesIO(src).readline):
                if tok.type == tokenize.COMMENT:
                    comment_words |= _words(tok.string)
        except Exception:
            pass
    # distinctive identifiers: compound (snake/camel), length≥6, not dunder — the
    # idiosyncratic naming a clean-room author would invent differently
    distinctive = {x for x in idents if len(x) >= 6 and not x.startswith('__')
                   and ('_' in x or re.search(r'[a-z][A-Z]', x))}
    return idents, distinctive, doc_words, comment_words


def overlap_coeff(a, b):
    if not a or not b:
        return 0.0
    return sum((a & b).values()) / min(sum(a.values()), sum(b.values()))


def cosine_counter(a, b):
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def jaccard(a, b):
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------- behavioural ----------
ENCODINGS = ['windows-1252', 'iso-8859-1', 'iso-8859-2', 'iso-8859-5', 'iso-8859-7',
             'iso-8859-9', 'koi8-r', 'cp866', 'shift_jis', 'euc-jp', 'gb18030',
             'big5', 'utf-8', 'utf-16']
LENGTHS = [6, 10, 16, 24, 40, 64]


def generate_hard_workload(outdir):
    """Deterministic hard workload: short/ambiguous byte sequences where detectors
    diverge. Re-encode public-domain UDHR samples across legacy encodings and
    truncate, plus fixed adversarial high-byte patterns."""
    os.makedirs(outdir, exist_ok=True)
    for old in glob.glob(os.path.join(outdir, '*.bin')):
        os.remove(old)
    texts = {}
    for p in sorted(glob.glob(os.path.join(CORPUS, '*utf8*', '*'))):
        if p.endswith(('.md', '.tsv')):
            continue
        try:
            texts[os.path.basename(p)] = open(p, 'rb').read().decode('utf-8')
        except Exception:
            pass
    seen, n = set(), 0
    for tid, text in texts.items():
        for enc in ENCODINGS:
            try:
                raw = text.encode(enc, errors='ignore')
            except Exception:
                continue
            for L in LENGTHS:
                chunk = raw[:L]
                if len(chunk) < 4:
                    continue
                h = hashlib.blake2b(chunk, digest_size=8).hexdigest()
                if h in seen:
                    continue
                seen.add(h)
                open(os.path.join(outdir, f'{n:04d}_{enc}_{L}.bin'), 'wb').write(chunk)
                n += 1
    adv = ([bytes(range(0x80, 0x80 + k)) for k in (8, 16, 24)] +
           [bytes(range(0xA0, 0xA0 + k)) for k in (8, 16)] +
           [b'\xe9\xe8\xea' * 4, b'\xc0\xc1\xc2\xc3' * 3, b'\x92\x93\x94\x95' * 3])
    for i, b in enumerate(adv):
        open(os.path.join(outdir, f'adv_{i:02d}.bin'), 'wb').write(b)
        n += 1
    return n


def norm_enc(e):
    if not e or (isinstance(e, str) and e.startswith('ERR')):
        return e
    e = e.lower().replace('_', '-').replace(' ', '')
    al = {'utf8': 'utf-8', 'latin1': 'iso-8859-1', 'latin-1': 'iso-8859-1',
          'iso8859-1': 'iso-8859-1', 'cp1252': 'windows-1252', 'us-ascii': 'ascii',
          'gb2312': 'gb18030', 'gbk': 'gb18030', 'sjis': 'shift-jis',
          'shiftjis': 'shift-jis', 'shift-jis': 'shift-jis'}
    return al.get(e, e)


def run_bh(pkg_parent, kind, corpus_dir):
    env = dict(os.environ)
    env['PYTHONPATH'] = pkg_parent + os.pathsep + env.get('PYTHONPATH', '')
    r = subprocess.run([sys.executable, RUNNER, kind, corpus_dir],
                       capture_output=True, text=True, env=env, timeout=300)
    if r.returncode != 0:
        return {'__error__': r.stderr[-400:]}
    return json.loads(r.stdout)['results']


def bh_agree(a, b, keys=None):
    ks = (set(a) & set(b)) if keys is None else {k for k in keys if k in a and k in b}
    ks = {k for k in ks if not k.startswith('__')}
    if not ks:
        return float('nan')
    return sum(1 for k in ks if norm_enc(a[k]['enc']) == norm_enc(b[k]['enc'])) / len(ks)


def vocab(impl):
    """set of RAW encoding labels an impl emits across easy+hard inputs — its
    known-encoding vocabulary + exact spelling (a provenance fingerprint)."""
    s = set()
    for src in ('bh', 'bh_hard'):
        for k, v in impl[src].items():
            if k.startswith('__'):
                continue
            e = v['enc']
            if e and not (isinstance(e, str) and e.startswith('ERR')):
                s.add(e)
    return s


def conf_agree(a, b, tol=0.05):
    """exact-confidence agreement on inputs where both emit the same encoding
    (chardet-lineage only; csn exposes no comparable confidence → nan)."""
    use = [(a['bh'][k], b['bh'][k]) for k in a['bh']
           if not k.startswith('__') and k in b['bh']]
    use = [(x, y) for x, y in use
           if x['conf'] is not None and y['conf'] is not None
           and norm_enc(x['enc']) == norm_enc(y['enc'])]
    if not use:
        return float('nan')
    return sum(1 for x, y in use if abs(x['conf'] - y['conf']) <= tol) / len(use)


def auc(pos, neg):
    if not pos or not neg:
        return float('nan')
    c = sum((1.0 if p > n else 0.5 if p == n else 0.0) for p in pos for n in neg)
    return c / (len(pos) * len(neg))


def main():
    nhard = generate_hard_workload(HARD)
    print(f'generated hard workload: {nhard} short/ambiguous inputs\n')

    data = {}
    for iid, repo, tag, pkgname, kind in IMPLS:
        d = extract(repo, tag)
        pkg = find_pkg(d, pkgname)
        parent = os.path.dirname(pkg)
        vf, init = os.path.join(pkg, '_version.py'), os.path.join(pkg, '__init__.py')
        if not os.path.exists(vf) and os.path.exists(init) and \
           '_version' in open(init, encoding='utf-8', errors='ignore').read():
            open(vf, 'w').write(f'__version__ = "{tag}"\n')   # setuptools-scm shim
        fs, tb, im, cfg, nh, floats, msgs = extract_static(pkg, pkgname)
        graph = S.build_call_graph(pkg)
        funcs = S.collect_functions(pkg)
        idents, idist, docw, commw = extract_quirks(pkg)
        bh_easy = run_bh(parent, kind, CORPUS)
        bh_hard = run_bh(parent, kind, HARD)
        layout = 'src/' if os.path.basename(parent) == 'src' else 'top-level'
        data[iid] = dict(func_sigs=fs, tables=tb, imports=im, cfg=cfg, node=nh,
                         floats=floats, messages=msgs, graph=graph, funcs=funcs,
                         idents=idents, idist=idist, docw=docw, commw=commw,
                         bh=bh_easy, bh_hard=bh_hard,
                         layout=layout, nfiles=len(pkg_py_files(pkg)))
        ne = len([k for k in bh_easy if not k.startswith('__')])
        nh = len([k for k in bh_hard if not k.startswith('__')])
        print(f'[{iid}] tag={tag} layout={layout} pyfiles={data[iid]["nfiles"]} '
              f'funcsig5grams={sum(fs.values())} tables={sum(tb.values())} '
              f'bh_easy={ne} bh_hard={nh}', flush=True)

    # discriminating subset of the hard workload: inputs where impls are NOT unanimous
    ids = list(data)
    common = set.intersection(*[{k for k in data[i]['bh_hard'] if not k.startswith('__')} for i in ids])
    disc = {k for k in common if len({norm_enc(data[i]['bh_hard'][k]['enc']) for i in ids}) > 1}
    print(f'\nhard workload: {len(common)} inputs scored by all impls, '
          f'{len(disc)} DISCRIMINATING (non-unanimous) → BHd uses these\n')

    POS = ('EVOLVED', 'DERIVED-airewrite', 'DERIVED-distant')
    NEG = ('INDEPENDENT',)
    rows = []
    for a, b, label in PAIRS:
        st_sh = overlap_coeff(data[a]['func_sigs'], data[b]['func_sigs'])   # fine shingle
        st_cfg = cosine_counter(data[a]['cfg'], data[b]['cfg'])             # control-flow hist (C06c)
        st_nh = cosine_counter(data[a]['node'], data[b]['node'])           # node-type hist
        st_topo = S.topology_similarity(data[a]['graph'], data[b]['graph']) # call-graph topology (C06a)
        st_wl = S.wl_cosine(data[a]['graph'], data[b]['graph'])            # WL kernel (C06a')
        st_pf = S.per_function_similarity(data[a]['funcs'], data[b]['funcs'])[0]  # per-function (C06f)
        env = sorted([st_sh, st_cfg, st_nh, st_topo, st_wl, st_pf])         # 6-measure envelope
        pbt = overlap_coeff(data[a]['tables'], data[b]['tables'])
        pbi = jaccard(data[a]['imports'], data[b]['imports'])
        bh = bh_agree(data[a]['bh'], data[b]['bh'])
        bhd = bh_agree(data[a]['bh_hard'], data[b]['bh_hard'], disc)
        pq_const = jaccard(data[a]['floats'], data[b]['floats'])
        pq_msg = jaccard(data[a]['messages'], data[b]['messages'])
        pq_vocab = jaccard(vocab(data[a]), vocab(data[b]))
        pq_conf = conf_agree(data[a], data[b])
        # AFC 'golden nugget' quirks — arbitrary expression
        qk_ident = jaccard(data[a]['idents'], data[b]['idents'])
        qk_idist = jaccard(data[a]['idist'], data[b]['idist'])
        qk_doc = jaccard(data[a]['docw'], data[b]['docw'])
        qk_comm = jaccard(data[a]['commw'], data[b]['commw'])
        vals = [v for v in (env[1], pbt, bhd, pq_const, pq_msg, pq_vocab) if v == v]
        combined = sum(vals) / len(vals) if vals else float('nan')
        rows.append(dict(pair=f'{a}-{b}', label=label, ST_sh=st_sh, ST_cfg=st_cfg,
                         ST_nh=st_nh, ST_topo=st_topo, ST_wl=st_wl, ST_pf=st_pf,
                         ST_lo=env[0], ST_hi=env[-1], PBt=pbt, PBi=pbi,
                         BH=bh, BHd=bhd, PQconst=pq_const, PQmsg=pq_msg,
                         PQvocab=pq_vocab, PQconf=pq_conf,
                         QKident=qk_ident, QKidist=qk_idist, QKdoc=qk_doc, QKcomm=qk_comm,
                         combined=combined))

    col = lambda name, labels: [r[name] for r in rows if r['label'] in labels]
    aucs = {s: auc(col(s, POS), col(s, NEG)) for s in
            ('ST_sh', 'ST_cfg', 'ST_nh', 'ST_topo', 'ST_wl', 'ST_pf', 'PBt', 'BHd',
             'PQconst', 'PQmsg', 'PQvocab', 'QKident', 'QKidist', 'QKdoc', 'QKcomm', 'combined')}

    print('=== STRUCTURAL ENVELOPE — 6 measures (exposes matcher-dependence, L4) ===')
    print(f'{"pair":<8}{"label":<19}{"sh":>6}{"cfg":>6}{"nh":>6}{"topo":>6}{"wl":>6}{"pf":>6}'
          f'{"[lo":>7}{"hi]":>7}')
    for r in rows:
        print(f'{r["pair"]:<8}{r["label"]:<19}{r["ST_sh"]:>6.2f}{r["ST_cfg"]:>6.2f}'
              f'{r["ST_nh"]:>6.2f}{r["ST_topo"]:>6.2f}{r["ST_wl"]:>6.2f}{r["ST_pf"]:>6.2f}'
              f'{r["ST_lo"]:>7.2f}{r["ST_hi"]:>7.2f}')
    print('  (sh=5-gram shingle, cfg=control-flow hist[C06c], nh=node-type hist, '
          'topo=call-graph topology[C06a], wl=WL kernel[C06a′], pf=per-function shape[C06f])')
    print('\n=== PROVENANCE-QUIRK signals (a clean reimpl should NOT reproduce these) ===')
    print(f'{"pair":<8}{"label":<19}{"PQconst":>8}{"PQmsg":>7}{"PQvocab":>8}{"PQconf":>8}{"comb":>7}')
    for r in rows:
        cf = f'{r["PQconf"]:.3f}' if r['PQconf'] == r['PQconf'] else 'n/a'
        print(f'{r["pair"]:<8}{r["label"]:<19}{r["PQconst"]:>8.3f}{r["PQmsg"]:>7.3f}'
              f'{r["PQvocab"]:>8.3f}{cf:>8}{r["combined"]:>7.3f}')
    print('  (PQconst=arbitrary float constants; PQmsg=message strings; PQvocab=emitted-label set;'
          ' PQconf=exact-confidence agreement, chardet-only)')
    print('\n=== AFC "golden nugget" quirks — arbitrary expression (legally-probative family) ===')
    print(f'{"pair":<8}{"label":<19}{"QKident":>8}{"QKidist":>8}{"QKdoc":>7}{"QKcomm":>8}')
    for r in rows:
        print(f'{r["pair"]:<8}{r["label"]:<19}{r["QKident"]:>8.3f}{r["QKidist"]:>8.3f}'
              f'{r["QKdoc"]:>7.3f}{r["QKcomm"]:>8.3f}')
    print('  (QKident=all identifiers; QKidist=distinctive compound identifiers; '
          'QKdoc=docstring words; QKcomm=comment words)')
    # distinctiveness check — is the signal real provenance or generic? (the PQmsg lesson)
    s67 = data['v6']['idist'] & data['v7']['idist']
    s6c = data['v6']['idist'] & data['csn']['idist']
    only67 = sorted(s67 - data['csn']['idist'])
    print(f'\n  distinctiveness: v6∩v7 distinctive idents={len(s67)}, v6∩csn={len(s6c)}')
    print(f'  v6∩v7 but NOT in csn (lineage-specific, {len(only67)}): {only67[:24]}')
    print('\n=== directional AUC (same-lineage 3 pos vs INDEPENDENT 3 neg) ===')
    for s, v in aucs.items():
        print(f'  AUC[{s:>8}] = {v:.3f}')
    air = next(r for r in rows if r['label'] == 'DERIVED-airewrite')
    print('\n=== disputed AI-rewrite v6-v7 ===')
    print(f'  ST envelope [{air["ST_lo"]:.3f} … {air["ST_hi"]:.3f}]  PBt={air["PBt"]:.3f}  BHd={air["BHd"]:.3f}')
    print(f'  PQconst={air["PQconst"]:.3f}  PQmsg={air["PQmsg"]:.3f}  PQvocab={air["PQvocab"]:.3f}  '
          f'PQconf={air["PQconf"]:.3f}')

    with open(os.path.join(HERE, 'results.json'), 'w') as f:
        json.dump({'rows': rows, 'aucs': aucs, 'n_hard': nhard,
                   'n_discriminating': len(disc)}, f, indent=2)
    print('\nWrote pilot/results.json')


if __name__ == '__main__':
    main()
