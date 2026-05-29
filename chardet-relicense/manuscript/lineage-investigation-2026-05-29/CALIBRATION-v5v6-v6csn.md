# Calibrating the per-method renaming-invariant trace across three pairs

Date: 2026-05-29. Tooling: Python 3.13 `ast`, pure-source descriptor (no RNG, no
network). Author harness: Claude Code. Companion to `FINDINGS.md` (the v6/v7 run).

**These numbers are SEPARATE corroborative research, NOT harness output.** They come
from `scripts/per_method_trace_cov_generic.py` over standalone clones in
`/srv/repos/public/lineage/`, not from `extract_signals.py`. Per the CLAUDE.md
load-bearing invariant they must stay out of the 8-signal bundle tables/figures.

---

## 0. The question

The v6/v7 run established that **0 of the 14 load-bearing v6 methods (cyclomatic ≥ 8)
have a strict structural twin in v7**, invariant across coverage (50/80/100%) and
direction. By itself that is a *one-pair diagnostic*: a 0% could mean "AI re-architected
the core" or it could simply be what the metric *always* reports for any two encoding
libraries. The only way to know is to run the identical trace on two calibration pairs:

- **v5→v6** — routine same-project release evolution. Prediction: **HIGH** load-bearing
  twin (the detection core should survive a point-release structurally; paper C06f = 64.0%).
- **v6→charset_normalizer** — independent same-domain reimplementation (different design
  paradigm: mess/coherence probing). Prediction: **LOW/~0** (paper C06f within-match low).

If load-bearing twin is HIGH for v5/v6 and ~0 for both v6/v7 and v6/csn, the metric
separates structural evolution from non-evolution and earns a provisional **C06g**. If
v5/v6 is *also* ~0, it discriminates nothing and stays a v6/v7-only diagnostic.

## 1. Method (identical to the v6/v7 run)

Descriptor and gates are **byte-for-byte the v6/v7 matcher** — only the
implementation-package paths/labels became arguments. Verified by re-running the
generalized script on v6→v7 fwd 50%: it reproduces naive 80%, strict 14/74 = 19%,
load-bearing 0/14, and the exact same matched-name list as `FINDINGS.md` §4.3.

- Identifier-blind per-function descriptor: control-flow histogram over
  {If,For,While,Try,ExceptHandler,With,Return,Raise,Break,Continue,Call,BoolOp,Compare,
  ListComp,Assign} + arity + cyclomatic (= 1+If+For+While+ExceptHandler+BoolOp) + max
  nesting depth + return count + loop count + total CF nodes. Pure `ast`; tests excluded.
- **NAIVE** gate: cf-cosine ≥ 0.90, arity ±1, size 0.5–2.0×.
- **STRICT** gate: also loop-count equal, depth ±1, returns ±1, cf-cosine ≥ 0.95, size 0.67–1.5×.
- Complexity bands: load-bearing cyc ≥ 8, substantive 5–7, minor 3–4, trivial ≤ 2.
- Both directions × coverage 50/80/100%. Both pairs are Python↔Python (no cross-language caveat).

Packages: v5 `chardet-5.0.0/chardet` (151 methods) · v6 `chardet-6.0.0/chardet` (148) ·
csn `csn-3.4.7/src/charset_normalizer` (116). csn 3.4.7 matches the paper's v6/csn pin.

---

## 2. Pair A — v5→v6 (routine release evolution)

### 2.1 Per-band matrices

**Forward v5→v6** (src = v5, ranked by cyclomatic):

| coverage | mapped | naive twin | strict twin | load-bearing (cyc≥8) | substantive 5–7 | minor 3–4 | trivial ≤2 |
|---|--:|--:|--:|--:|--:|--:|--:|
| 50%  | 76  | 73/76 = 96% | 65/76 = 86%  | **13/15 = 87%** | 7/7 = 100% | 15/24 = 62% | 30/30 = 100% |
| 80%  | 121 | 118/121 = 98% | 109/121 = 90% | **13/15 = 87%** | 7/7 = 100% | 15/24 = 62% | 74/75 = 99% |
| 100% | 151 | 148/151 = 98% | 139/151 = 92% | **13/15 = 87%** | 7/7 = 100% | 15/24 = 62% | 104/105 = 99% |

**Reverse v6→v5** (src = v6):

| coverage | mapped | naive twin | strict twin | load-bearing (cyc≥8) | substantive 5–7 | minor 3–4 | trivial ≤2 |
|---|--:|--:|--:|--:|--:|--:|--:|
| 50%  | 74  | 65/74 = 88% | 57/74 = 77%  | **10/14 = 71%** | 11/15 = 73% | 12/20 = 60% | 24/25 = 96% |
| 80%  | 118 | 106/118 = 90% | 98/118 = 83% | **10/14 = 71%** | 11/15 = 73% | 12/20 = 60% | 65/69 = 94% |
| 100% | 148 | 135/148 = 91% | 127/148 = 86% | **10/14 = 71%** | 11/15 = 73% | 12/20 = 60% | 94/99 = 95% |

The load-bearing band is constant across coverage because all cyc≥8 methods sit in the
top 50% by complexity (so widening coverage only adds lower bands), exactly as in v6/v7.

### 2.2 Load-bearing methods (cyc≥8) and their strict twins — forward v5→v6

| v5 method | cyc | verdict | best v6 match (cos) |
|---|--:|---|---|
| `UniversalDetector.feed` | 27 | **NONE** | — (grew to cyc 34 in v6) |
| `UniversalDetector.close` | 18 | TWIN 0.98 | `UniversalDetector.close` |
| `detect_all` | 13 | **NONE** | — |
| `SingleByteCharSetProber.feed` | 12 | TWIN 0.99 | `SingleByteCharSetProber.feed` |
| `UTF1632Prober.validate_utf16_characters` | 9 | TWIN 1.00 | `UTF1632Prober.validate_utf16_characters` |
| `EUCJPProber.feed` | 9 | TWIN 0.99 | `EUCJPProber.feed` |
| `SJISContextAnalysis.get_order` | 9 | TWIN 1.00 | `SJISContextAnalysis.get_order` |
| `SJISProber.feed` | 9 | TWIN 0.99 | `EUCJPProber.feed` |
| `MultiByteCharSetProber.feed` | 9 | TWIN 0.99 | `MultiByteCharSetProber.feed` |
| `HebrewProber.feed` | 9 | TWIN 1.00 | `HebrewProber.feed` |
| `UTF8Prober.feed` | 8 | TWIN 1.00 | `UTF8Prober.feed` |
| `EUCJPContextAnalysis.get_order` | 8 | TWIN 1.00 | `EUCJPContextAnalysis.get_order` |
| `EscCharSetProber.feed` | 8 | TWIN 0.99 | `EscCharSetProber.feed` |
| `CharSetGroupProber.feed` | 8 | TWIN 0.99 | `CharSetGroupProber.feed` |
| `CharSetGroupProber.get_confidence` | 8 | TWIN 0.99 | `CharSetGroupProber.get_confidence` |

**Eyeball confirmation these are real twins, not boilerplate:** the matcher is
identifier-blind, yet for 12 of the 13 load-bearing twins the best structural match is
the **same-identity method** (`UTF8Prober.feed`→`UTF8Prober.feed`, etc.) at cosine
0.98–1.00. An identifier-blind descriptor independently re-pairing same-named detection
methods is the strongest possible evidence the twin is genuine structural survival.
(The two NONEs — `UniversalDetector.feed`, `detect_all` — are the dispatch methods that
were genuinely revised between 5 and 6; `feed` grew cyc 27→34. Honest, not noise.)

---

## 3. Pair B — v6→charset_normalizer (independent same-domain reimplementation)

### 3.1 Per-band matrices

**Forward v6→csn** (src = v6):

| coverage | mapped | naive twin | strict twin | load-bearing (cyc≥8) | substantive 5–7 | minor 3–4 | trivial ≤2 |
|---|--:|--:|--:|--:|--:|--:|--:|
| 50%  | 74  | 49/74 = 66% | 14/74 = 19% | **0/14 = 0%** | 0/15 = 0% | 2/20 = 10% | 12/25 = 48% |
| 80%  | 118 | 74/118 = 63% | 34/118 = 29% | **0/14 = 0%** | 0/15 = 0% | 2/20 = 10% | 32/69 = 46% |
| 100% | 148 | 98/148 = 66% | 58/148 = 39% | **0/14 = 0%** | 0/15 = 0% | 2/20 = 10% | 56/99 = 57% |

**Reverse csn→v6** (src = csn):

| coverage | mapped | naive twin | strict twin | load-bearing (cyc≥8) | substantive 5–7 | minor 3–4 | trivial ≤2 |
|---|--:|--:|--:|--:|--:|--:|--:|
| 50%  | 58 | 33/58 = 57% | 10/58 = 17% | **0/13 = 0%** | 0/19 = 0% | 2/15 = 13% | 8/11 = 73% |
| 80%  | 93 | 63/93 = 68% | 37/93 = 40% | **0/13 = 0%** | 0/19 = 0% | 2/15 = 13% | 35/46 = 76% |
| 100% | 116 | 83/116 = 72% | 53/116 = 46% | **0/13 = 0%** | 0/19 = 0% | 2/15 = 13% | 51/69 = 74% |

### 3.2 Load-bearing csn methods (cyc≥8) and their best v6 match — reverse csn→v6

| csn method | cyc | verdict | best v6 match (cos) |
|---|--:|---|---|
| `from_bytes` | 119 | NONE | — |
| `is_suspiciously_successive_range` | 37 | NONE | — |
| `cli_detect` | 33 | NONE | — |
| `SuperWeirdWordPlugin.feed_info` | 23 | NONE | — |
| `characters_popularity_compare` | 20 | NONE | — |
| `cut_sequence_chunks` | 17 | NONE | — |
| `alpha_unicode_split` | 15 | NONE | — |
| `ArchaicUpperLowerPlugin.feed_info` | 14 | weak 0.82 | `UTF1632Prober.validate_utf16_characters` (spurious cross-domain) |
| `mess_ratio` | 14 | NONE | — |
| `_character_flags` | 12 | weak 0.89 | `UTF8Prober.feed` (spurious cross-domain) |
| `detect` | 11 | NONE | — |
| `coherence_ratio` | 9 | NONE | — |
| `CharInfo.update` | 8 | NONE | — |

csn's entire mess/coherence detection core (`from_bytes` cyc 119, `mess_ratio`,
`coherence_ratio`, `is_suspiciously_successive_range`, `characters_popularity_compare`)
has **no v6 structural ancestor**. The two weak hits are different-named cross-domain
functions below the strict cosine threshold — i.e. domain saturation, not derivation.
Forward (v6→csn) is the mirror image: every v6 load-bearing method is NONE or weak.

---

## 4. Three-pair comparison — load-bearing-band strict-twin rate

The discriminating number. v6/v7 row is from `FINDINGS.md` §4.6.

| direction | coverage | **v5→v6** (evolution) | **v6→v7** (AI rewrite) | **v6→csn** (independent) |
|---|---|--:|--:|--:|
| fwd | 50%  | **87% (13/15)** | 0% (0/14) | 0% (0/14) |
| fwd | 80%  | **87% (13/15)** | 0% (0/14) | 0% (0/14) |
| fwd | 100% | **87% (13/15)** | 0% (0/14) | 0% (0/14) |
| rev | 50%  | **71% (10/14)** | 0% (0/15) | 0% (0/13) |
| rev | 80%  | **71% (10/14)** | 0% (0/15) | 0% (0/13) |
| rev | 100% | **71% (10/14)** | 0% (0/15) | 0% (0/13) |

Supporting context (naive vs strict aggregate — show why only the load-bearing band is trustworthy):

| pair | naive aggregate | strict aggregate | naive verdict |
|---|--:|--:|---|
| v5→v6  | 88–98% | 77–92% | mostly **TRUE** (same codebase) |
| v6→v7  | 80–86% | 19–43% | mostly **FALSE** (domain saturation) |
| v6→csn | 57–72% | 17–46% | mostly **FALSE** (domain saturation) |

Note the naive/aggregate rates do **not** cleanly separate the pairs — v6/v7's naive
80–86% sits *above* v6/csn's 57–72%, and both are high enough to fabricate "derivation."
Only the load-bearing **strict** band cleanly splits 87/71% from 0%/0%. This re-confirms
the FINDINGS lesson: report per-band, never the aggregate, and never the naive rate.

---

## 4.1 Control — gate/cyclomatic threshold sweep (is cyc≥8 / cos≥0.95 tuned?)

A reviewer can ask whether the cyc≥8 floor and the strict cos≥0.95 twin cutoff were
chosen to produce the split. `scripts/control_gate_sweep.py` sweeps the load-bearing
floor over cyc≥{6,7,8,9,10} × the cosine threshold over {0.90,0.93,0.95,0.97} for all
six pair/direction cells. The 87/71% vs 0/0% separation is **robust across the grid**:

| pair·dir | cyc≥6 | cyc≥7 | cyc≥8 | cyc≥9 | cyc≥10 | cos-threshold dependence |
|---|--:|--:|--:|--:|--:|---|
| v5→v6 | 89% | 89% | 87% | 80% | 50% (n=4) | **flat 0.90→0.97** (real twins at 0.98–1.00) |
| v6→v5 | 75% | 76% | 71% | 67% | 33% (n=6) | flat (1 cell 75%→71% at 0.97) |
| v6→v7 | 8% | 0% | 0% | 0% | 0% | only nonzero at cos≥0.90 (29–46%, the naive trap) |
| v7→v6 | 4% | 4% | 0% | 0% | 0% | only nonzero at cos≥0.90 |
| v6→csn | 0% | 0% | 0% | 0% | 0% | only nonzero at cos≥0.90 (12–17%) |
| csn→v6 | 0% | 0% | 0% | 0% | 0% | only nonzero at cos≥0.90 (11–18%) |

(Body shows the value at the canonical cos≥0.95; full grid in the script output.)
Two takeaways: (1) **v5/v6 stays 67–89% at every cyc floor 6–9 and every cosine
0.90–0.97** — the HIGH result is not threshold-sensitive (the real twins sit at cosine
0.98–1.00, far above any cutoff). (2) For v6/v7 and v6/csn the *only* place a nonzero
load-bearing rate appears is the loosest cos≥0.90 — i.e. exactly the naive
domain-saturation regime FINDINGS already flagged; the cos≥0.95 cutoff is what removes
those false positives, and at cos≥0.95 both pairs are 0% across cyc≥7…10. The cyc≥10
drop for v5/v6 is small-n thinning (n=4–6), not a sign change. **The chosen gate is not
load-bearing for the conclusion** — only the cos≥0.90 "naive" corner reopens the trap.

## 4.2 Control — unrelated-codebase null baseline (how surprising is each rate?)

`scripts/control_null_baseline.py` matches each source's load-bearing methods (cyc≥8,
strict gate, cos≥0.95) against the real destination **and** against a fixed panel of 10
unrelated Python stdlib packages (`argparse, json, http, asyncio, logging, email, xml,
statistics, fractions, difflib`) — a no-relationship null.

| source (n cyc≥8) | REAL match | NULL: unrelated-stdlib mean | NULL max |
|---|--:|--:|--:|
| v5 (n=15) → v6 | **87% (13/15)** | 16% (2.4/15) | 27% (4/15) |
| v6 (n=14) → v7 | **0% (0/14)** | 11% (1.5/14) | 21% (3/14) |
| v6 (n=14) → csn | **0% (0/14)** | 11% (1.5/14) | 21% (3/14) |

**The no-relationship floor is ~11–16%, not 0%** — a few medium-complexity stdlib
methods (in `http`, `asyncio`, `email`, `xml`, `difflib`) coincidentally pass the strict
shape gate against simple prober loops. This sharpens the reading:

- **v5/v6's 87% is far above the null** (>3× the null *max* of 27%) — genuinely
  surprising, i.e. real structural preservation, not chance shape-collision.
- **v6/v7 and v6/csn's 0% sit *at or below* the null floor.** The real AI rewrite and the
  real independent reimplementation are *less* structurally similar to v6's load-bearing
  core than random stdlib packages are — because both deliberately re-architect into
  shapes (v7's flat pipeline guards, csn's `from_bytes` cyc-119 scanner) that do not
  match v6's deep-nested prober loops, whereas generic code has a wider shape spread.

So the discriminating power lives in **HIGH being far above the ~15% null floor**, not in
LOW being exactly zero. 0/14 is statistically indistinguishable from the null
(mean 1.5, max 3), which is the quantitative form of the one-sided caveat: a ~0 result
cannot separate "rewrite" from "independent" because both land in the null band.

---

## 5. Verdict

**Does the load-bearing-band strict-twin rate separate ordinary in-line release
evolution from cases where the load-bearing core is structurally disjoint?**
**Yes — sharply and one-sidedly.** It is HIGH for routine release evolution (v5→v6: 87%
fwd / 71% rev, invariant across all three coverages) and shows **no observed strict
twins (0/14, 0/15)** for both pairs whose cores are disjoint (v6→v7 and v6→csn) in all
six cells each. The v6/v7 0% is therefore **not an artifact of the metric** — the same
metric returns 71–87% when the detection core actually survives, far above the ~11–16%
unrelated-codebase null floor (§4.2). The result the reviewers flagged as a one-pair
diagnostic now behaves differently on the calibration pairs, which is precisely the test
it had to pass. (Note "non-evolution" is too broad a phrasing: an *intentional derivative
rewrite* can also be structurally disjoint, so a disjoint result is not by itself
evidence against derivation — see caveat 1.)

Statistical honesty on the 0%: with n=13–15 these are *observed* counts, not population
estimates. By the rule of three a single 0/14 cell has a ~95% upper bound near 21%; the
strength of the claim comes from **invariance across six cells (3 coverage × 2 direction)
and the cyc/cosine grid of §4.1**, not from any one cell's point estimate.

**Is a provisional C06g justified?** **Yes, but as a one-sided "structural-lineage
continuity" test, not a derivation/independence classifier.** Read it as:

- **HIGH load-bearing twin (≳70%, well above the ~15% null floor) ⇒ the detection core
  was structurally preserved** — the signature of in-place evolution / a derivative that
  keeps the architecture.
- **~0% load-bearing twin (at/below the null floor) ⇒ the cores are structurally
  disjoint** — consistent with an AI re-architecture (v6/v7) **and** with independent
  reimplementation (v6/csn) alike.

The metric **separates v5/v6 from {v6/v7, v6/csn}**. It does **not** separate v6/v7 from
v6/csn — both are 0%. So the diagnostic earns promotion from a v6/v7-only result to a
*calibrated* one (it separates in-line evolution from structurally-disjoint cores across
three pairs), but its 0% must never be read as "independent" or "non-derivative" on its
own. (On the label "C06g": treat it as an **internal working name only**. It must not
appear as a "C06*" signal in the paper's prose or tables — that numbering belongs to the
8-signal harness bundle, and reusing it would imply harness status this trace does not
have. In the paper, call it "the calibrated per-method load-bearing structural-twin
diagnostic.")

**What stays caveated:**

1. **Necessary-but-not-sufficient for independence.** A 0% means the load-bearing core
   was not structurally preserved; it cannot distinguish a genuine rewrite from a
   thorough paraphrase that *also* re-architected, nor a rewrite from an independent
   build. Both v6/v7 and v6/csn land at 0% — the metric cannot tell them apart, and the
   legal "derivative vs. independent" question must rest on the other evidence
   (provenance, the plan document, public-API/import continuity), not on C06g.
2. **One-sided.** C06g detects *preservation* (HIGH), so it confirms continuity. A LOW
   value is the absence of that evidence, not positive evidence of independence.
3. **Report per-band, never aggregate.** Aggregate strict twin rises with coverage purely
   by adding trivial one-liners (v6/csn 19→29→39% fwd, v6/v7 19→38→43%); the load-bearing
   band is the coverage-invariant truth. Naive cf-cosine is domain-saturated and does not
   even rank the three pairs correctly.
4. **Trivial-band twins are meaningless.** They run 48–100% in every pair (highest in
   v5/v6 same-codebase, but still 46–76% in v6/csn between unrelated libraries).
5. **The fwd 87% / rev 71% asymmetry is expected directional behaviour, not noise.**
   Forward (v5→v6) traces v5's 15 load-bearing methods; the two NONEs (`UniversalDetector.feed`,
   `detect_all`) are dispatch methods genuinely revised in v6. Reverse (v6→v5) traces v6's
   14, which include high-complexity methods v6 *added or enlarged* (`SBCSGroupProber.get_confidence`
   cyc 83, `UniversalDetector._apply_encoding_heuristic`, the grown `feed`) that have no
   v5 ancestor — correctly NONE. A survival test *should* be directional; near-perfect
   symmetry across a real release boundary would be the surprise.
6. **The null floor is ~11–16%, not 0% (§4.2).** Use "no observed strict twins / 0 of 14",
   not absolute "zero" language. The signal is HIGH ≫ null, not LOW = 0.
7. **Determinism.** Descriptor is a pure function of source bytes; no RNG, no network
   (the null panel is a fixed list of stdlib packages).
8. **Keep separate from the 8-signal harness bundle** (CLAUDE.md invariant). These come
   from the standalone trace, not `extract_signals.py`.

**Bottom line:** the per-method load-bearing strict-twin rate is a legitimate,
calibrated discriminator of *structural-lineage continuity* — 87/71% for evolution
(far above the ~15% unrelated-codebase null) vs. 0% (at/below null) for both an AI
rewrite and an independent reimplementation. Both controls hold: the split survives the
cyc≥{6..9} × cos≥{0.90..0.97} grid (§4.1), and the null baseline shows HIGH is genuinely
surprising while 0% is the no-relationship floor (§4.2). Promote as a calibrated
*corroborative* diagnostic with the one-sided framing — not as a numbered harness signal.
The v6/v7 0% is corroborated as a real "the detection core was not preserved" result,
while the derivative-vs-independent distinction remains out of its reach and stays on the
other evidence lines.

---

## Appendix — reproduction

```bash
cd manuscript/lineage-investigation-2026-05-29/scripts
V5=/srv/repos/public/lineage/_v/chardet-5.0.0/chardet
V6=/srv/repos/public/lineage/_v/chardet-6.0.0/chardet
CSN=/srv/repos/public/lineage/_v/csn-3.4.7/src/charset_normalizer
for d in fwd rev; do for c in 0.5 0.8 1.0; do
  python3 per_method_trace_cov_generic.py "$V5"  "$V6"  v5 v6  $c $d   # Pair A
  python3 per_method_trace_cov_generic.py "$V6"  "$CSN" v6 csn $c $d   # Pair B
done; done
# faithfulness check (reproduces FINDINGS v6/v7 numbers exactly):
python3 per_method_trace_cov_generic.py "$V6" /srv/repos/public/lineage/_v/chardet-7.0.0/src/chardet v6 v7 0.5 fwd
# controls (§4.1, §4.2) — self-contained, paths pinned internally:
python3 control_gate_sweep.py        # cyc≥{6..10} × cos≥{0.90..0.97} grid, all 6 cells
python3 control_null_baseline.py     # real vs 10-package unrelated-stdlib null floor
```

Worktrees materialized this session:
`git -C /srv/repos/public/lineage/chardet worktree add --detach .../_v/chardet-5.0.0 5.0.0`;
`git -C /srv/repos/public/lineage/charset_normalizer worktree add --detach .../_v/csn-3.4.7 3.4.7`.
