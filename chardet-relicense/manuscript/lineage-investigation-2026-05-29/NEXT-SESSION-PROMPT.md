# Next-session prompt — calibrate the per-method trace across v5/v6 and v6/csn

Paste the fenced block below into a fresh session. It extends the per-method
renaming-invariant structural trace (done for chardet v6→v7 in `FINDINGS.md`) to the two
calibration pairs, to test whether the **load-bearing-band structural-twin rate** discriminates
an AI rewrite from routine evolution and from independent reimplementation — the gate that
decides whether the metric earns promotion to a provisional paper signal ("C06g").

Status: prompt only — not yet run.

---

```
Extend the per-method renaming-invariant structural trace (already done for chardet
v6→v7) to the two calibration pairs v5→v6 and v6→charset_normalizer, to test whether
the "load-bearing-band structural-twin rate" actually discriminates an AI rewrite from
(a) routine release evolution and (b) independent same-domain reimplementation.

== READ FIRST (context; do not trust this prompt over the files) ==
- chardet-relicense/manuscript/lineage-investigation-2026-05-29/FINDINGS.md
    (v6/v7 results + full methodology; §4 per-method trace, §7 lessons)
- chardet-relicense/manuscript/lineage-investigation-2026-05-29/INCORPORATION-RECOMMENDATION.md
- chardet-relicense/manuscript/lineage-investigation-2026-05-29/scripts/
    per_method_trace_cov.py  (the gated matcher; currently HARDCODED to v6 vs v7)
    per_method_trace.py, per_method_astshape.py (templates)
- chardet-relicense/manuscript/main.tex  (C06f: paper's per-function signal; reported
    match rates v5/v6=64.0%, v6/v7=17.5%, v6/csn=43.5%)
- chardet-relicense/CLAUDE.md  (load-bearing invariant: harness numbers come from
    extract_signals.py only; this trace is SEPARATE corroborative research — keep it so)

== REPOS / WORKTREES ==
Clones + worktrees live in /srv/repos/public/lineage/ . Existing worktrees in _v/:
chardet-1.0, chardet-6.0.0, chardet-7.0.0, csn-1.0.0, uchardet-0.0.2.
Materialize the two missing ones (use absolute paths; `git -C <repo> worktree add` resolves
relative paths against the repo, so always pass absolute targets):
  git -C /srv/repos/public/lineage/chardet            worktree add --detach /srv/repos/public/lineage/_v/chardet-5.0.0 5.0.0
  git -C /srv/repos/public/lineage/charset_normalizer worktree add --detach /srv/repos/public/lineage/_v/csn-3.4.7   3.4.7
(csn 3.4.7 matches the paper's v6/charset_normalizer calibration pin.)
Then LOCATE each implementation package (the dir with __init__.py NOT under a tests/ path)
with `find <worktree> -name __init__.py -not -path '*/test*'`. Expect: chardet 5.0.0 &
6.0.0 = flat chardet/ ; csn 3.4.7 = likely src/charset_normalizer/. Verify, don't assume.

== METHOD (keep IDENTICAL to the v6/v7 run) ==
Generalize per_method_trace_cov.py to accept src and dst implementation-package paths as
args (it currently hardcodes V6/V7). Do NOT change the descriptor or gates:
- identifier-blind descriptor per function: control-flow histogram over
  {If,For,While,Try,ExceptHandler,With,Return,Raise,Break,Continue,Call,BoolOp,Compare,
  ListComp,Assign} + arity + cyclomatic(=1+If+For+While+ExceptHandler+BoolOp) + max nesting
  depth + return count + loop count + total CF nodes. Pure Python `ast`; exclude test files.
- NAIVE gate: cf-cosine>=0.90, arity±1, size 0.5–2.0×.
- STRICT gate: also loop-count equal, depth±1, returns±1, cf-cosine>=0.95, size 0.67–1.5×.
- complexity bands: load-bearing cyc>=8, substantive 5–7, minor 3–4, trivial <=2.
- BOTH directions (src→dst and dst→src) at coverage 50%/80%/100%.
This is Python↔Python for both pairs (no cross-language caveat).

== RUN ==
Pair A  v5→v6 : src=chardet-5.0.0/<pkg>      dst=chardet-6.0.0/chardet
Pair B  v6→csn: src=chardet-6.0.0/chardet    dst=csn-3.4.7/<pkg>
For each pair: 2 directions × 3 coverages, with the per-band TWIN/weak/NONE breakdown
each, plus the list of load-bearing (cyc>=8) methods and their best matches.

== THE HYPOTHESIS TO TEST (this is the point) ==
Compare the LOAD-BEARING-band strict-twin rate across all three pairs:
  - v5→v6  (routine evolution)        : EXPECT HIGH (methods survive structurally; C06f=64%)
  - v6→v7  (AI rewrite)               : 0% in all 6 cells (already established — the baseline)
  - v6→csn (independent same-domain)  : EXPECT LOW/~0 (different design; C06f within-match low)
If load-bearing twin is HIGH for v5/v6 and ~0 for BOTH v6/v7 and v6/csn, the metric
separates evolution from non-evolution and the gated per-method trace is a legitimate
discriminator → provisional "C06g" is justified. If v5/v6 is ALSO low, it does NOT
discriminate and must remain a v6/v7-only diagnostic. State which, with the numbers.

== GUARDRAILS (don't repeat known traps) ==
- Report PER-BAND, never headline the aggregate twin rate (it scales with coverage purely
  by adding trivial one-liners; v6/v7 aggregate ran 19/38/43% fwd, 5/15/23% rev while
  load-bearing stayed 0%).
- Naive cf-cosine is domain-saturated (~80% FALSE twins on v6/v7); only the STRICT,
  load-bearing band is meaningful. Eyeball a few "TWIN"s to confirm they're not boilerplate.
- Structural divergence is necessary-but-not-sufficient for independence; structural
  similarity is consistent with derivation OR domain convergence.
- Determinism: descriptor is a pure function of source bytes; no RNG, no network.
- Keep these numbers clearly SEPARATE from the harness's 8-signal bundle (CLAUDE.md invariant).

== OUTPUT ==
1. Per-band matrices for both new pairs (markdown), + load-bearing method lists.
2. A 3-pair comparison table: load-bearing strict-twin rate (v5/v6, v6/v7, v6/csn) ×
   direction × coverage, with the v6/v7 row taken from FINDINGS.md.
3. Verdict: does load-bearing twin rate discriminate evolution from non-evolution? Is a
   provisional C06g justified? What stays caveated?
4. Save the write-up to
   chardet-relicense/manuscript/lineage-investigation-2026-05-29/CALIBRATION-v5v6-v6csn.md
   and the generalized script to that dir's scripts/. Do NOT edit main.tex. Do NOT commit
   unless asked.
```

---

Expected outcomes and how to read them:
- **Discriminating result** (v5/v6 load-bearing HIGH; v6/v7 and v6/csn ~0): promote the gated
  per-method trace to a provisional signal (C06g) — it cleanly separates evolution from
  non-evolution at the method-body level.
- **Null result** (v5/v6 load-bearing also low): keep it a v6/v7 diagnostic; report the null
  honestly. Either way it strengthens the paper's calibration discipline.
