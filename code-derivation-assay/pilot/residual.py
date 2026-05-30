#!/usr/bin/env python3
"""
CDA §5.4 measure — AFC-operationalized "filter then score the residual".

For a candidate pair (A,B) and a baseline pool of INDEPENDENT same-spec impls:
  1. enumerate arbitrary-expression features (distinctive identifiers, message
     strings, magic constants, docstring words);
  2. FILTER: drop features also present in the independent baseline (domain /
     standards-dictated — the AFC 'filtration' step) AND features that are part
     of A's or B's public API surface (compatibility-dictated — interface
     reproduction is fair use, Sega/Sony);
  3. the RESIDUAL = arbitrary, non-functional, non-API shared expression. Its
     size + the actual feature list is the legally-probative "striking
     similarity" signal.

Run on two families: chardet (AI rewrite v6→v7) and fuzzy-matching
(human GPL→MIT reimplementation fuzzywuzzy→RapidFuzz, plus the thefuzz fork).
Deterministic, offline (sources already on disk). Names never used for ST-style
matching — here we WANT identifier text (it is the arbitrary expression).
"""
import ast, os, re, glob, tempfile, subprocess
from collections import Counter

CHARDET = '/srv/repos/public/spec-poc/chardet-relicense/chardet'
CSN = '/srv/repos/public/spec-poc/chardet-relicense/charset_normalizer'
FZSRC = '/tmp/fzsrc'

_STOP = {'self', 'none', 'true', 'false', 'return', 'with', 'from', 'this', 'that',
         'list', 'dict', 'type', 'value', 'data', 'name', 'args', 'kwargs', 'param',
         'default', 'object', 'string', 'bytes', 'index', 'result', 'using', 'used',
         'will', 'when', 'each', 'also', 'class', 'method', 'function', 'number',
         'count', 'length', 'size', 'text', 'char', 'characters', 'sequence'}


def _words(t):
    return {w for w in re.findall(r'[a-zA-Z]{4,}', t.lower()) if w not in _STOP}


def py_files(pkg_dir):
    out = []
    for r, _, fs in os.walk(pkg_dir):
        if 'test' in r.lower():
            continue
        out += [os.path.join(r, f) for f in fs if f.endswith('.py')]
    return out


def find_pkg(root, pkgname=None):
    best = None
    for r, _, fs in os.walk(root):
        if '__init__.py' in fs and 'test' not in r.lower() and '.dist-info' not in r:
            if pkgname and os.path.basename(r) != pkgname:
                continue
            if best is None or len(r) < len(best):
                best = r
    return best


def features(pkg_dir):
    idents, messages, docw, api = set(), set(), set(), set()
    floats = set()
    for path in py_files(pkg_dir):
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
                    docw.update(_words(d))
            if isinstance(n, ast.Constant):
                v = n.value
                if isinstance(v, float) and v not in (0.0, 1.0):
                    floats.add(round(v, 6))
                elif isinstance(v, str) and 8 <= len(v) <= 200 and ' ' in v and v.isprintable():
                    messages.add(' '.join(v.lower().split()))
        # public API surface (compatibility-dictated)
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith('_'):
                api.add(n.name)
                if isinstance(n, ast.ClassDef):
                    for m in n.body:
                        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and not m.name.startswith('_'):
                            api.add(m.name)
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name) and t.id == '__all__' and isinstance(n.value, (ast.List, ast.Tuple)):
                        for e in n.value.elts:
                            if isinstance(e, ast.Constant) and isinstance(e.value, str):
                                api.add(e.value)
    idist = {x for x in idents if len(x) >= 6 and not x.startswith('__')
             and ('_' in x or re.search(r'[a-z][A-Z]', x))}
    return dict(idents=idents, idist=idist, messages=messages, docw=docw, api=api, floats=floats)


def chardet_extract(tag, pkgname):
    d = tempfile.mkdtemp(prefix=f'res_{tag}_')
    repo = CHARDET if pkgname == 'chardet' else CSN
    subprocess.run(f'git -C {repo} archive {tag} | tar -x -C {d}', shell=True, check=True,
                   capture_output=True)
    return features(find_pkg(d, pkgname))


def _union(pool, key):
    out = set()
    for p in pool:
        out |= p[key]
    return out


def residual(A, B, baseline, label):
    base_idist, base_msg, base_flt = _union(baseline, 'idist'), _union(baseline, 'messages'), _union(baseline, 'floats')
    api = A['api'] | B['api']
    sh_id = A['idist'] & B['idist']
    res_dom = sh_id - base_idist                 # AFC filtration: drop domain-shared
    res_api = res_dom - api                       # drop compatibility/API-dictated
    sh_msg = (A['messages'] & B['messages']) - base_msg
    sh_flt = (A['floats'] & B['floats']) - base_flt
    return dict(label=label, shared_idist=len(sh_id), res_dom=sorted(res_dom),
                res_api=sorted(res_api), res_msg=sorted(sh_msg)[:8], res_flt=len(sh_flt),
                n_res_dom=len(res_dom), n_res_api=len(res_api), n_res_msg=len(sh_msg))


def report(title, scenarios):
    print(f'\n############ {title} ############')
    print(f'{"scenario":<34}{"shared":>7}{"resDom":>8}{"resAPI":>8}{"resMsg":>8}')
    for s in scenarios:
        print(f'{s["label"]:<34}{s["shared_idist"]:>7}{s["n_res_dom"]:>8}'
              f'{s["n_res_api"]:>8}{s["n_res_msg"]:>8}')
    print('  resDom = distinctive idents shared by the pair but NOT any independent baseline (AFC filtration)')
    print('  resAPI = resDom minus the pair\'s public-API names (compatibility-dictated → fair use)')
    for s in scenarios:
        if s['n_res_api'] or s['n_res_msg']:
            print(f'\n  [{s["label"]}] residual after API filter ({s["n_res_api"]} idents): {s["res_api"][:30]}')
            if s['res_msg']:
                print(f'      residual messages: {s["res_msg"]}')


def main():
    # ---- chardet family ----
    v5 = chardet_extract('5.0.0', 'chardet')
    v6 = chardet_extract('6.0.0', 'chardet')
    v7 = chardet_extract('7.0.0', 'chardet')
    csn = chardet_extract('3.4.7', 'charset_normalizer')
    report('chardet family (baseline pool = {charset_normalizer} — thin, n=1)', [
        residual(v6, v7, [csn], 'DERIVED  v6→v7 (AI rewrite)'),
        residual(v5, v6, [csn], 'EVOLVED  v5→v6 (human)'),
        residual(v5, v7, [csn], 'DERIVED  v5→v7 (distant)'),
    ])

    # ---- fuzzy-matching family ----
    fz = {n: features(find_pkg(os.path.join(FZSRC, d)))
          for n, d in [('fuzzywuzzy', 'fuzzywuzzy'), ('thefuzz', 'thefuzz'),
                       ('rapidfuzz', 'rapidfuzz'), ('jellyfish', 'jellyfish'),
                       ('levenshtein', 'levenshtein'), ('textdistance', 'textdistance')]}
    indep = [fz['jellyfish'], fz['levenshtein'], fz['textdistance']]
    report('fuzzy-matching family (baseline pool = {jellyfish, Levenshtein, textdistance})', [
        residual(fz['fuzzywuzzy'], fz['rapidfuzz'], indep, 'DERIVED  fuzzywuzzy→RapidFuzz (GPL→MIT reimpl)'),
        residual(fz['fuzzywuzzy'], fz['thefuzz'], indep, 'DERIVED  fuzzywuzzy→thefuzz (fork)'),
        residual(fz['jellyfish'], fz['textdistance'], [fz['levenshtein']], 'INDEPENDENT  jellyfish↔textdistance'),
        residual(fz['levenshtein'], fz['textdistance'], [fz['jellyfish']], 'INDEPENDENT  Levenshtein↔textdistance'),
    ])


if __name__ == '__main__':
    main()
