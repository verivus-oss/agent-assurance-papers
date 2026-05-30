#!/usr/bin/env python3
"""
Multi-family extension of the CDA pilot — IS THE chardet FINDING GENERAL?

Runs the STATIC measure ensemble (ST envelope: shingle/cfg/nodehist/topology/WL/
per-function + provenance-quirks + §5.4 residual) across THREE families, each with
a real DERIVED edge plus independent same-spec implementations, to test whether
"no measure separates a reimplementation from independent" is chardet-specific.

Static-only (BH needs per-family adapters). Deterministic, offline. Reuses the
audited pilot modules (pilot_harness, structural, residual) so the measures are
identical to the single-family pilot.

Families:
  encoding : chardet v5/v6/v7 + charset_normalizer  (DERIVED v6→v7 = AI rewrite)
  fuzzy    : fuzzywuzzy/thefuzz/rapidfuzz + jellyfish/Levenshtein/textdistance
             (DERIVED fuzzywuzzy→rapidfuzz = HUMAN GPL→MIT reimplementation; →thefuzz = fork)
  toml     : tomli/tomllib(stdlib)/tomlkit/toml  (DERIVED tomli→tomllib = vendored)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pilot_harness as PH    # extract_static, extract_quirks, overlap_coeff, cosine_counter, jaccard, auc, extract, find_pkg
import structural as S
import residual as R

CHARDET = '/srv/repos/public/spec-poc/chardet-relicense/chardet'
CSN = '/srv/repos/public/spec-poc/chardet-relicense/charset_normalizer'
FZSRC = '/tmp/fzsrc'
TOMLSRC = '/tmp/tomlsrc'
TOMLLIB = '/usr/lib64/python3.13/tomllib'


def chardet_pkg(tag, pkgname):
    repo = CHARDET if pkgname == 'chardet' else CSN
    d = PH.extract(repo, tag)
    pkg = PH.find_pkg(d, pkgname)
    vf, init = os.path.join(pkg, '_version.py'), os.path.join(pkg, '__init__.py')
    if not os.path.exists(vf) and os.path.exists(init) and \
       '_version' in open(init, encoding='utf-8', errors='ignore').read():
        open(vf, 'w').write(f'__version__ = "{tag}"\n')
    return pkg


def extract_all(pkg):
    fs, tb, im, cfg, nh, floats, msgs = PH.extract_static(pkg, '')
    idents, idist, docw, commw = PH.extract_quirks(pkg)
    return dict(func_sigs=fs, cfg=cfg, node=nh, idist=idist, docw=docw, commw=commw,
                graph=S.build_call_graph(pkg), funcs=S.collect_functions(pkg),
                rfeat=R.features(pkg))


def pair_measures(A, B):
    env = sorted([
        PH.overlap_coeff(A['func_sigs'], B['func_sigs']),          # shingle
        PH.cosine_counter(A['cfg'], B['cfg']),                      # control-flow hist
        PH.cosine_counter(A['node'], B['node']),                    # node-type hist
        S.topology_similarity(A['graph'], B['graph']),              # call-graph topology
        S.wl_cosine(A['graph'], B['graph']),                        # WL kernel
        S.per_function_similarity(A['funcs'], B['funcs'])[0],       # per-function
    ])
    return dict(env_lo=env[0], env_hi=env[-1], env_med=env[len(env)//2],
                pqidist=PH.jaccard(A['idist'], B['idist']),
                pqdoc=PH.jaccard(A['docw'], B['docw']),
                pqcomm=PH.jaccard(A['commw'], B['commw']))


# `independents` = the pool of independent same-spec impls used as the AFC-filtration
# baseline. For EVERY pair the baseline is LEAVE-PAIR-OUT (independents minus the two
# members), so an independent pair is NOT trivially zeroed by being in its own baseline
# and its residual reflects the measure's true false-positive behaviour.
FAMILIES = {
    'encoding': dict(
        impls=lambda: {'v5': chardet_pkg('5.0.0', 'chardet'), 'v6': chardet_pkg('6.0.0', 'chardet'),
                       'v7': chardet_pkg('7.0.0', 'chardet'), 'csn': chardet_pkg('3.4.7', 'charset_normalizer')},
        pairs=[('v5', 'v6', 'EVOLVED'), ('v6', 'v7', 'DERIVED-reimpl(AI)'),
               ('v5', 'csn', 'INDEPENDENT'), ('v6', 'csn', 'INDEPENDENT'), ('v7', 'csn', 'INDEPENDENT')],
        reimpl=('v6', 'v7'), independents=['csn']),  # only 1 independent → thin baseline
    'fuzzy': dict(
        impls=lambda: {n: R.find_pkg(os.path.join(FZSRC, n)) for n in
                       ['fuzzywuzzy', 'thefuzz', 'rapidfuzz', 'jellyfish', 'levenshtein', 'textdistance']},
        pairs=[('fuzzywuzzy', 'rapidfuzz', 'DERIVED-reimpl(human GPL→MIT)'),
               ('fuzzywuzzy', 'thefuzz', 'DERIVED-fork'),
               ('jellyfish', 'textdistance', 'INDEPENDENT'), ('levenshtein', 'textdistance', 'INDEPENDENT'),
               ('jellyfish', 'levenshtein', 'INDEPENDENT')],
        reimpl=('fuzzywuzzy', 'rapidfuzz'), independents=['jellyfish', 'levenshtein', 'textdistance']),
    'toml': dict(
        impls=lambda: {'tomli': R.find_pkg(os.path.join(TOMLSRC, 'tomli')), 'tomllib': TOMLLIB,
                       'tomlkit': R.find_pkg(os.path.join(TOMLSRC, 'tomlkit')),
                       'toml': R.find_pkg(os.path.join(TOMLSRC, 'toml'))},
        pairs=[('tomli', 'tomllib', 'DERIVED-vendored'),
               ('tomli', 'tomlkit', 'INDEPENDENT'), ('toml', 'tomlkit', 'INDEPENDENT'),
               ('tomllib', 'toml', 'INDEPENDENT')],
        reimpl=('tomli', 'tomllib'), independents=['tomli', 'tomlkit', 'toml']),  # tomllib is the derived one
}

POS = ('EVOLVED', 'DERIVED-reimpl(AI)', 'DERIVED-reimpl(human GPL→MIT)', 'DERIVED-fork', 'DERIVED-vendored')
NEG = ('INDEPENDENT',)


def main():
    summary = []
    for fam, cfg in FAMILIES.items():
        print(f'\n############ FAMILY: {fam} ############')
        impls = cfg['impls']()
        F = {k: extract_all(v) for k, v in impls.items()}
        rows = []
        for a, b, label in cfg['pairs']:
            m = pair_measures(F[a], F[b])
            base_ids = [x for x in cfg['independents'] if x not in (a, b)]   # LEAVE-PAIR-OUT
            res = R.residual(F[a]['rfeat'], F[b]['rfeat'],
                             [F[x]['rfeat'] for x in base_ids], label)
            rows.append(dict(pair=f'{a}-{b}', label=label, **m, resApi=res['n_res_api'],
                             nbase=len(base_ids)))
        print(f'{"pair":<22}{"label":<30}{"ST_env":>14}{"PQidist":>8}{"PQdoc":>7}{"resApi":>7}')
        for r in rows:
            print(f'{r["pair"]:<22}{r["label"]:<30}[{r["env_lo"]:.2f},{r["env_hi"]:.2f}]'.ljust(22 + 30 + 14)
                  + f'{r["pqidist"]:>8.3f}{r["pqdoc"]:>7.3f}{r["resApi"]:>7}')
        col = lambda k: ([r[k] for r in rows if r['label'] in POS], [r[k] for r in rows if r['label'] in NEG])
        for k in ('env_med', 'env_hi', 'pqidist', 'resApi'):
            p, n = col(k)
            print(f'  AUC[{k:>8}] (same-lineage vs independent) = {PH.auc(p, n):.3f}')
        # the reimplementation pair vs the independent band
        rp = next(r for r in rows if (r['pair'] == f"{cfg['reimpl'][0]}-{cfg['reimpl'][1]}"))
        ind = [r for r in rows if r['label'] in NEG]
        ind_idist = [r['pqidist'] for r in ind]
        ind_res = [r['resApi'] for r in ind]
        summary.append((fam, rp['label'], rp['env_lo'], rp['env_hi'], rp['pqidist'],
                        min(ind_idist), max(ind_idist), rp['resApi'], min(ind_res), max(ind_res)))

    print('\n\n######## CROSS-FAMILY SUMMARY: does the REIMPLEMENTATION look independent? ########')
    print(f'{"family":<10}{"reimpl pair label":<32}{"ST_env":>13}{"PQidist":>9}{"indep PQidist":>16}{"resApi":>8}{"indep resApi":>14}')
    for fam, lbl, lo, hi, idist, imn, imx, res, rmn, rmx in summary:
        print(f'{fam:<10}{lbl:<32}[{lo:.2f},{hi:.2f}]'.ljust(10 + 32 + 13)
              + f'{idist:>9.3f}{("%.3f-%.3f" % (imn, imx)):>16}{res:>8}{("%d-%d" % (rmn, rmx)):>14}')
    print('\nReading: if the reimplementation pair (chardet v6→v7 AI; fuzzy fuzzywuzzy→rapidfuzz human)')
    print('sits inside the independent PQidist / resApi band and has a WIDE ST envelope, the chardet')
    print('finding GENERALIZES. A near-copy (fork / vendored) should instead score clearly ABOVE the band.')


if __name__ == '__main__':
    main()
