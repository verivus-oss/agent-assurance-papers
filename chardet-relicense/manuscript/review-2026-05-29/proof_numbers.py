#!/usr/bin/env python3
"""Prove every numeric claim touched by the 2026-05-29 main.tex edits (and the
headline calibration table) using ONLY deterministic stdlib math modules
(fractions.Fraction + decimal.Decimal with explicit ROUND_HALF_UP). No floating
point round(); no RNG; no network.

Discipline (so the proof is not circular and contains no prose literals as truth
values): for every claim we PARSE the value displayed in the manuscript
(main.tex, or the rendered figures/scripts/multi_pair_comparison.tex that main.tex
\\input's) AND PARSE the base value from a ground-truth artifact
(witness TSV / validation_report.v2.json / jplag JSON), then assert that the
displayed value EQUALS the value computed from the artifact with exact
Fraction/Decimal arithmetic. The only bare numeric constants in this file are the
mathematical thresholds that encode QUALITATIVE prose claims (e.g. "doubles" ->
ratio >= 2; "about a third" -> |ratio - 4/3| < 1/20); these are labelled inline.

Run:
    python3 proof_numbers.py        # exit 0 == every numeric claim proven
"""
import json, re, sys, pathlib
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP

ROOT = pathlib.Path(__file__).resolve().parents[3]   # repo root (agent-assurance-papers)
CR   = ROOT / "chardet-relicense"
PB   = CR / "proof-bundle"
MS   = CR / "manuscript"
SC   = MS / "figures" / "scripts"

fails, checks = [], 0
def prove(name, ok, got, expected):
    global checks
    checks += 1
    if not ok:
        fails.append(name)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: displayed/computed={got!r} source={expected!r}")

def q(value_fraction, template):
    """Quantize a Fraction to the precision of a displayed Decimal `template`,
    half-up. Precision is taken from the artifact's own displayed token, never a
    hard-coded number of places."""
    return (Decimal(value_fraction.numerator) / Decimal(value_fraction.denominator)
            ).quantize(template, rounding=ROUND_HALF_UP)

def witness(pair):
    rows = {}
    for line in (PB / "results" / pair / "witness.tsv").read_text().splitlines():
        if line.startswith("#") or line.startswith("signal\t") or not line.strip():
            continue
        c = line.split("\t")
        if len(c) >= 6:
            rows.setdefault(c[0], {"actual": c[3], "evidence": c[5]})
    return rows

MAIN = (MS / "main.tex").read_text()
MPTX = (SC / "multi_pair_comparison.tex").read_text()
VREP = (SC / "validation_report.v2.json").read_text()
jpl  = json.loads((SC / "jplag_chardet_results.json").read_text())[0]["similarities"]
v67  = witness("v6_v7"); v56 = witness("v5_v6"); vcn = witness("v6_charset_norm")
WMAP = {"v6_v7": v67, "v5_v6": v56, "v6_charset_norm": vcn}
PAIRS = ["v6_v7", "v5_v6", "v6_charset_norm"]   # = multi_pair table column order

def dmain(pattern, text=None):
    """Parse a displayed token from the manuscript (raises if absent)."""
    m = re.search(pattern, text if text is not None else MAIN)
    if not m:
        raise ValueError(f"display token {pattern!r} not found")
    return m.groups()

# ---- C2 / corpus digest: displayed (main.tex) == witness == validation_report --
wd = re.search(r"corpus_digest=([0-9a-f]+)", v67["behavioural_fingerprint"]["actual"]).group(1)
vd = re.search(r'"corpus_digest_manifest"\s*:\s*"([0-9a-f]+)"', VREP).group(1)
md = dmain(r"\\texttt\{([0-9a-f]{16})\} to the validator")[0]
prove("C2 digest: main.tex == witness == validation_report", wd == vd == md, md, f"{wd}/{vd}")
prove("C2 stale v1 digest 58e54831f84183c7 absent from main.tex", "58e54831f84183c7" not in MAIN, True, "absent")

# ---- C4 / JPlag table: displayed % == 100 * raw-JSON ratio (exact Decimal) ------
avg_disp = Decimal(dmain(r"AVG token-string overlap & ([\d.]+)\\%")[0])
avg_src = (Decimal(repr(jpl["AVG"])) * 100).quantize(avg_disp, ROUND_HALF_UP)   # quantize to displayed precision
prove("C4 JPlag AVG: displayed == 100*AVG", avg_disp == avg_src, f"{avg_disp}%", f"{avg_src}% from {jpl['AVG']}")
mx_disp = Decimal(dmain(r"MAX token-string overlap & ([\d.]+)\\%")[0])
mx_src = (Decimal(repr(jpl["MAX"])) * 100).quantize(mx_disp, ROUND_HALF_UP)
prove("C4 JPlag MAX: displayed == 100*MAX", mx_disp == mx_src, f"{mx_disp}%", f"{mx_src}% from {jpl['MAX']}")
lon_disp = int(dmain(r"longest token match & (\d+) tokens")[0])
prove("C4 JPlag longest: displayed == LONGEST_MATCH", lon_disp == int(jpl["LONGEST_MATCH"]), lon_disp, int(jpl["LONGEST_MATCH"]))
th, hu = dmain(r"token-stream length of roughly (\d+)\{,\}(\d+)")
len_disp = int(th + hu)                                            # "247{,}000" -> 247000
len_src  = (int(jpl["MAXIMUM_LENGTH"]) + 500) // 1000 * 1000       # nearest 1000, integer math
prove("C4 JPlag length: displayed 'roughly N' == MAXIMUM_LENGTH to nearest 1000",
      len_disp == len_src, len_disp, f"{int(jpl['MAXIMUM_LENGTH'])}->{len_src}")

# ---- C4 / file counts: tab:results displayed 87/33 == witness AUX1 row ----------
wa, wb = (int(x) for x in re.search(r"across (\d+) v6 / (\d+) v7 files", v67["literal_source_carryover"]["actual"]).groups())
da, db = (int(x) for x in dmain(r"across (\d+) v6 / (\d+) v7 files"))
prove("C4 file counts: main.tex tab:results == witness", (da, db) == (wa, wb), (da, db), (wa, wb))
# JPlag-side counts differ from the extractor's (the corrected claim), and the
# old false 'higher than the extractor' wording is gone:
ja, jb = (int(x) for x in dmain(r"\((\d+) v6 \\texttt\{\.py\} files plus (\d+) v7"))
prove("C4 JPlag counts (84/22) DIFFER from extractor (87/33)", (ja, jb) != (wa, wb), (ja, jb), f"!= {(wa, wb)}")
prove("C4 false 'higher than the extractor' removed", "higher than the extractor" not in MAIN, True, "absent")

# ---- C5 / C06a node & edge counts: displayed phrasing == witness ---------------
c = v67["call_graph_topology"]["actual"]
n6 = int(re.search(r"v6_nodes=(\d+)", c).group(1)); n7 = int(re.search(r"v7_nodes=(\d+)", c).group(1))
e6 = int(re.search(r"v6_edges=(\d+)", c).group(1)); e7 = int(re.search(r"v7_edges=(\d+)", c).group(1))
de7, de6, dn7, dn6 = (int(x) for x in dmain(r"\((\d+) vs\.\\ v6's (\d+)\) onto a comparable node count \((\d+) vs\.\\ (\d+)\)"))
prove("C5 C06a edges/nodes: main.tex == witness",
      (de7, de6, dn7, dn6) == (e7, e6, n7, n6), (de7, de6, dn7, dn6), (e7, e6, n7, n6))
prove("C5 v7 nodes NOT smaller than v6 (math: 358 > 342)", n7 > n6, f"{n7}>{n6}", "v7>v6")
prove("C5 v7 denser (math: more edges, 659 > 488)", e7 > e6, f"{e7}>{e6}", "v7>v6")
prove("C5 false 'smaller node count (358)' removed", "smaller node count (358)" not in MAIN, True, "absent")

# ---- C6 / C06c growth: displayed caption counts == witness; ratios encode prose -
ev = v67["control_flow_histogram"]["evidence"]
def wcf(node):  # witness counts
    g = re.search(rf"{node}: v6=(\d+) v7=(\d+)", ev).groups(); return int(g[0]), int(g[1])
def dcf(node):  # displayed counts in fig:cfhist caption
    g = dmain(rf"\\texttt\{{{node}\}}: v6 = (\d+), v7 = (\d+)"); return int(g[0]), int(g[1])
for node in ("Return", "For", "Try", "ExceptHandler"):
    prove(f"C6 {node} caption counts == witness", dcf(node) == wcf(node), dcf(node), wcf(node))
r6, r7 = wcf("Return"); f6, f7 = wcf("For"); t6, t7 = wcf("Try"); x6, x7 = wcf("ExceptHandler")
# prose claims, encoded as exact-Fraction thresholds (the only bare constants here):
prove("C6 'Return rises by about a third' (|253/191 - 4/3| < 1/20)",
      abs(Fraction(r7, r6) - Fraction(4, 3)) < Fraction(1, 20), str(Fraction(r7, r6)), "~4/3, not 2")
prove("C6 'For roughly doubles' (135/72 >= 9/5)", Fraction(f7, f6) >= Fraction(9, 5), str(Fraction(f7, f6)), ">=9/5")
prove("C6 'Try (or more)' (33/12 >= 2)", Fraction(t7, t6) >= 2, str(Fraction(t7, t6)), ">=2")
prove("C6 'ExceptHandler (or more)' (32/12 >= 2)", Fraction(x7, x6) >= 2, str(Fraction(x7, x6)), ">=2")
prove("C6 false 'doubles ... Return' wording removed",
      "doubles the absolute count of\n\\texttt{Return}" not in MAIN, True, "absent")

# ---- C3 / C06b: displayed shared set + Jaccard (main.tex) == witness ------------
def jacc(w):
    e = w["import_edge_set"]["evidence"]
    g = lambda k: re.findall(r"'([^']+)'", re.search(rf"{k}: \[([^\]]*)\]", e).group(1))
    sh, v6o, v7o = g("shared"), g("v6_only"), g("v7_only")
    u = len(sh) + len(v6o) + len(v7o)
    jw = Decimal(re.search(r"jaccard=([\d.]+)", w["import_edge_set"]["actual"]).group(1))
    return sh, v6o, v7o, Fraction(len(sh), u) if u else Fraction(0), jw
sh67, _, v7o67, j67, jw67 = jacc(v67)
# displayed shared set parsed from the C06b interpretation sentence in main.tex:
span = MAIN[MAIN.index("shared third-party set is therefore"):MAIN.index("against a union")]
disp_shared = sorted(re.findall(r"\\texttt\{([a-z_]+)\}", span))
prove("C3 shared set: main.tex == witness", disp_shared == sorted(sh67), disp_shared, sorted(sh67))
prove("C3 computed |shared|/|union| == witness Jaccard field", q(j67, jw67) == jw67, str(q(j67, jw67)), str(jw67))
prove("C3 v7-only is the charset_normalizer comparator", v7o67 == ["charset_normalizer"], v7o67, ["charset_normalizer"])
sh56, v6o56, _, j56, jw56 = jacc(v56)
prove("C3 v5/v6 sole shared cchardet; setuptools+sphinx v6_only",
      sh56 == ["cchardet"] and {"setuptools", "sphinx_rtd_theme"} <= set(v6o56), (sh56, v6o56), "as witness")
prove("C3 v5/v6 computed Jaccard == witness field", q(j56, jw56) == jw56, str(q(j56, jw56)), str(jw56))
prove("C3 main.tex credits datasets, not setuptools/sphinx, for the rise",
      "classify \\texttt{datasets}" in MAIN
      and "setuptools}, \\texttt{sphinx\\_rtd\\_theme}) that the v1" not in MAIN, True, "datasets")

# ---- C1 / narrative: old assertions retracted, not asserted --------------------
prove("C1 abstract says C06b boundary framing inverts",
      "is genuinely different'' framing inverts" in MAIN, True, "inverts")
prove("C1 'shape of v6's thinking' only as retracted v1 reading",
      "preserves the shape of v6's thinking.'' That reading\ndoes not survive" in MAIN
      or "preserves the shape of v6's thinking.'' That reading does not survive" in MAIN, True, "retraction")

# ---- C7 / signal-count consistency: no stale counts; v2 lists present -----------
for stale in ("six signals", "six-signal", "five C06 signals", "seven-line TSV", "C06a..C06e"):
    prove(f"C7 stale phrase absent: {stale!r}", stale not in MAIN, True, "absent")
prove("C7 determinism list includes C06a' and C06f",
      "AUX1, C06a, C06a$'$, C06b, C06c, C06d, C06f" in MAIN, True, "present")

# ---- C8 / conclusion match rate: displayed 31/177=17.5% == witness+arithmetic ---
matched, total = (int(x) for x in re.search(
    r"matched/v6=(\d+)/(\d+)", v67["per_function_ast_shape"]["evidence"]).groups())
cnum, cden, cpct = dmain(r"\(\$(\d+)/(\d+)=([\d.]+)\\%\$\) combined")
prove("C8 conclusion fraction == witness matched/total",
      (int(cnum), int(cden)) == (matched, total), (cnum, cden), (matched, total))
prove("C8 conclusion percent == 100*matched/total (Fraction->Decimal)",
      Decimal(cpct) == q(Fraction(matched, total) * 100, Decimal(cpct)), cpct,
      str(q(Fraction(matched, total) * 100, Decimal(cpct))))

# ---- C8/table headline: displayed token (multi_pair_comparison.tex) == witness --
def displayed_row(label_re):
    for line in MPTX.splitlines():
        if re.search(label_re, line):
            return [Decimal(re.search(r"(\d+\.\d+)", c).group(1)) for c in line.split("&")[1:4]]
    raise ValueError(f"row {label_re!r} not in multi_pair_comparison.tex")
HEAD = {
    "C06a":  (r"^C06a: ",       "call_graph_topology",    r"similarity=([\d.]+)"),
    "C06a'": (r"^C06a\$'\$: ",  "call_graph_wl_kernel",   r"wl_cosine=([\d.]+)"),
    "C06b":  (r"^C06b: ",       "import_edge_set",        r"jaccard=([\d.]+)"),
    "C06c":  (r"^C06c: ",       "control_flow_histogram", r"cosine=([\d.]+)"),
    "C06f":  (r"^C06f: ",       "per_function_ast_shape", r"per_function_similarity=([\d.]+)"),
}
for sig, (label_re, row, pat) in HEAD.items():
    disp = displayed_row(label_re)
    for i, pair in enumerate(PAIRS):
        wit = Decimal(re.search(pat, WMAP[pair][row]["actual"]).group(1))
        prove(f"table {sig} {pair}: displayed == witness", disp[i] == wit, str(disp[i]), str(wit))

# ---- C06e realistic: displayed token == computed sum(normalized)/64 -------------
def realistic(pairkey):
    nm = dn = 0
    for line in (PB / "results" / pairkey / "witness.tsv").read_text().splitlines():
        m = re.match(r"behavioural_fingerprint:(\w+)\t", line)
        if not m or m.group(1) == "random_control":
            continue
        gg = re.search(r"normalized=(\d+)/(\d+)", line.split("\t")[5]).groups()
        nm += int(gg[0]); dn += int(gg[1])
    return nm, dn, Fraction(nm, dn)
disp_real = displayed_row(r"normalized-match rate \(realistic")
for i, pairkey in enumerate(PAIRS):
    nm, dn, fr = realistic(pairkey)
    prove(f"C06e realistic {pairkey}: displayed == computed {nm}/{dn}", disp_real[i] == q(fr, disp_real[i]),
          str(disp_real[i]), f"{q(fr, disp_real[i])} ({nm}/{dn})")

# ---- C06e random-fuzz exact: displayed token == witness random_control rate -----
disp_rand = displayed_row(r"exact-match rate \(random-fuzz")
for i, pairkey in enumerate(PAIRS):
    for line in (PB / "results" / pairkey / "witness.tsv").read_text().splitlines():
        if line.startswith("behavioural_fingerprint:random_control\t"):
            wit = Decimal(re.search(r"exact_match_rate=([\d.]+)", line).group(1))
            prove(f"C06e random-fuzz exact {pairkey}: displayed == witness", disp_rand[i] == wit,
                  str(disp_rand[i]), str(wit))

print(f"\n{checks} checks, {len(fails)} failed.")
if fails:
    print("FAILED:", ", ".join(fails)); sys.exit(1)
print("ALL NUMERIC CLAIMS PROVEN FROM ARTIFACTS (deterministic Fraction/Decimal; "
      "displayed tokens parsed from main.tex / multi_pair_comparison.tex, no hard-coded expecteds).")
