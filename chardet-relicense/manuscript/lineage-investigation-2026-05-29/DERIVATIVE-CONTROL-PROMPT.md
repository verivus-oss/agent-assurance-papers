# Generator prompt — build a KNOWN derivative/paraphrase of chardet v6 (positive control)

Date: 2026-05-29. Purpose: the missing **true-positive** control for the detection
methodology. The calibration so far has only *negatives* and *evolution*:

| pair | what it is | load-bearing twin | role |
|---|---|--:|---|
| v5→v6 | routine release evolution | 87/71% | positive-ish (in-line evolution) |
| v6→v7 | disputed AI rewrite | 0% | the case under test |
| v6→csn | independent reimplementation | 0% | true negative |
| **v6→DERIV** | **synthetic KNOWN derivative** | **?** | **the missing true positive** |

Every Threats section says the structural metric is **necessary-but-not-sufficient**: a
paraphrase that *also* re-architects would read 0% (a false negative), and we have never
fed the detector a *known* derivative to confirm it fires on a real positive. This prompt
builds that artifact at three derivation depths so you can map the **detection curve** —
where the load-bearing twin rate falls from "caught" through the ~11–16% null floor
(§4.2 of `CALIBRATION-v5v6-v6csn.md`), and which *other* signals catch a derivative once
the structural one goes blind.

## Honesty / provenance framing (read first)

This produces a **self-labeled, derived test fixture** to measure the detector's
true-positive sensitivity — the legitimate inverse of the independence calibration. It is
**not** for laundering a license or passing derived code off as original: the generated
package must carry a provenance banner declaring it a mechanical derivative of chardet
6.0.0 and must retain chardet's LGPL-2.1 license. Generate it **only from v6 source** — do
**not** show the generator chardet 7.0.0 or charset_normalizer, so the rewrite's
architecture is not contaminated by how v7 actually reorganized.

---

## THE PROMPT (paste into a coding agent with repo access)

> You are producing a **known-derivative test fixture** of the `chardet` 6.0.0 encoding
> detector, to validate a structural-derivation detector. This is detector-validation
> research; the output is explicitly a derivative work and must be labeled as such.
>
> **Source (read only this — do NOT open chardet 7.x or charset_normalizer):**
> `/srv/repos/public/lineage/_v/chardet-6.0.0/chardet` (79 `.py` files; ~29 are detection
> *logic*, ~50 are hardcoded statistical data tables `lang*model.py` / `*freq.py`).
>
> **Output:** a complete, installable Python package at
> `/srv/repos/public/lineage/_v/chardet-DERIV-<LEVEL>/<pkgname>/` plus a minimal
> `pyproject.toml`/`setup.py` so `pip install <worktree>` builds (needed for the
> behavioral signal). It must expose the **same public API** — `detect()`, `detect_all()`,
> `UniversalDetector`, `EncodingEra`, `VERSION`, `__version__` — and pass a smoke test:
> `detect()` returns the same `{encoding, confidence, language}` shape and the same
> verdicts as v6 on a handful of sample byte strings (UTF-8, Windows-1251 Cyrillic,
> Shift-JIS, GB2312, a Hebrew snippet, ASCII, and random bytes).
>
> **Provenance banner** at the top of the package `__init__.py` (verbatim, fill the date):
> ```
> # SYNTHETIC DERIVATIVE — detector-validation fixture, NOT an original work.
> # Mechanically derived from chardet 6.0.0 (LGPL-2.1) on <DATE> to test a
> # paraphrase-resistant structural-derivation detector. Inherits chardet's
> # LGPL-2.1 license and copyright. Do not distribute as an independent library.
> ```
> Copy chardet's `LICENSE` into the output unchanged.
>
> **Derivation level = `<LEVEL>`** (pick one; see the per-level rules below). Apply the
> transformation **uniformly to every logic file**. Then handle the data tables per
> **`TABLES = <verbatim | transformed>`**.
>
> **Deliverables in the output dir:**
> 1. the working package;
> 2. `TRANSFORM-MANIFEST.md` — for each logic file, the list of transformations applied,
>    so the derivation level is documented and the result is reproducible;
> 3. a one-paragraph self-assessment of what you changed vs. preserved.
>
> Be deterministic and meaning-preserving within the level's rules. Do not add new
> detection capabilities or remove encodings — it must stay behaviorally chardet v6.

### Per-level rules (these are the experiment — follow exactly)

The detector's descriptor per function is identifier-blind: a control-flow histogram over
`{If,For,While,Try,ExceptHandler,With,Return,Raise,Break,Continue,Call,BoolOp,Compare,
ListComp,Assign}` + arity + cyclomatic + max nesting depth + return count + loop count.
The STRICT twin gate needs: arity ±1, size 0.67–1.5×, depth ±1, **loop count equal**,
returns ±1, cosine ≥ 0.95. Each level is defined by what it does to that descriptor.

**LEVEL = `paraphrase`** — cosmetic, meaning-AND-structure preserving. *Prediction: the
detector should flag this as a near-100% load-bearing twin. If it doesn't, the detector is
broken.*
- **MUST change:** rename every identifier (modules/files, classes, methods, params,
  locals); rewrite every comment and docstring; reformat whitespace/line-wrapping; reorder
  top-level definitions and imports; reorder provably independent (side-effect-free)
  statements; swap trivially-equal literals (`0x80`↔`128`, `"a"`↔`'a'`).
- **MUST NOT change:** method/function boundaries (no extract/inline/merge/split); the
  control-flow structure (same `if/for/while/try/with` nesting and counts); the number of
  returns, branches, or loops; arity; loop↔comprehension form; the algorithm; any data
  value. Every function's descriptor must come out **identical** (cosine 1.00).

**LEVEL = `moderate`** — light refactor, behavior preserving. *Prediction: HIGH-but-reduced
load-bearing twin, clearly above the ~15% null floor; some methods drop to weak/NONE.*
- Everything `paraphrase` allows, **plus**: extract repeated blocks into helpers; inline
  one-line methods; convert simple `for`↔comprehension; invert some branch polarity
  (`if not x: A else: B`); swap some `for`↔`while`; add/remove intermediate variables;
  split or merge a *few* (≤20%) methods.
- **Keep:** the algorithm, the public API, and all data tables. This deliberately perturbs
  loop count / depth / boundaries on a minority of methods to probe metric robustness.

**LEVEL = `deep`** — full re-architecture, still a genuine derivative. *Prediction:
load-bearing twin → ~0%, indistinguishable from v6/v7 and v6/csn — the KNOWN blind spot.
Derivation must then be caught by the non-structural signals.*
- Re-architect dispatch into a flat pipeline / stage objects; replace the deep-nested
  `feed`/`close` cascade with early-return ladders; collapse or re-split the prober class
  hierarchy; reassign method boundaries wholesale.
- **But remain derived:** reuse chardet's detection algorithm and confidence math; keep the
  statistical data tables; preserve the public API and per-input behavior. (This is exactly
  the v7-shaped move, generated independently of v7.)

### TABLES knob (probes which signal is the backstop)
- **`verbatim`** — copy `lang*model.py`/`*freq.py` unchanged. Realistic: the tables are
  ~98% of the source and re-deriving them needs the original training corpora. → strong
  file-hash (AUX1) + import-edge (C06b) + behavioral (C06e) match even at `deep`.
- **`transformed`** — re-encode the *same numbers* differently (container syntax, key
  reordering with a consistent remap, integer base). Defeats raw-byte AUX1 but the values
  and thus the behavioral fingerprint (C06e) and confidence outputs still match.
- (Regenerating the tables from new training data is **not** a paraphrase — it would make
  the result genuinely independent. Note it as the boundary, don't do it.)

---

## How to evaluate the fixture (closed-loop test)

Let `RW=/srv/repos/public/lineage/_v/chardet-DERIV-<LEVEL>/<pkgname>` and
`V6=/srv/repos/public/lineage/_v/chardet-6.0.0/chardet`.

**1. Standalone per-method trace + both controls (no git needed):**
```bash
cd manuscript/lineage-investigation-2026-05-29/scripts
for d in fwd rev; do for c in 0.5 0.8 1.0; do
  python3 per_method_trace_cov_generic.py "$V6" "$RW" v6 rw $c $d
done; done
# add the new pair to the sweep/null scripts' PKG dict (one line each) and re-run:
python3 control_gate_sweep.py        # is the verdict threshold-robust for this fixture?
python3 control_null_baseline.py     # is its load-bearing rate above or at the null floor?
```

**2. Full 8-signal harness** (confirm the non-structural signals catch what the structural
one misses — especially at `deep`). `extract_signals.py` is pair-agnostic; confirm flags
with `--help`, then:
```bash
python3 proof-bundle/extract_signals.py --root-a "$V6/.." --root-b "$RW/.." \
        --pkg-a chardet --pkg-b <pkgname>
```
For the behavioral signal (C06e) and the headline SUMMARY, add a one-stanza pair to
`detect.sh`'s `case` block (per CLAUDE.md) pointing REPO/PKG/MODULE at the fixture, tag it
in a throwaway git repo so `git worktree add` works, and run `bash proof-bundle/detect.sh
v6_deriv`.

## What a PASS looks like (the hypothesis this control tests)

| level / tables | load-bearing twin (structural) | AUX1 file-hash | C06b imports | C06e behavioral | C06d API | reading |
|---|--:|--:|--:|--:|--:|---|
| `paraphrase` / verbatim | **~100% (caught)** | high | high | identical | identical | every signal fires → derivative obvious |
| `moderate` / verbatim | high-but-reduced, ≫ null | high | high | identical | identical | structural still fires, weaker |
| `deep` / verbatim | **~0% (structural MISS)** | **high** | **high** | **identical** | high | **non-structural signals carry it** |
| `deep` / transformed | ~0% | low | high | **identical** | high | **behavioral fingerprint is the backstop** |

**The methodology passes the true-positive test iff:**
1. `paraphrase` reads as a near-100% load-bearing twin — proving the renaming-invariant
   structural metric **does** catch a real paraphrase (the headline claim), and the v6/v7
   0% therefore means "not even paraphrase-level structure survived," not "metric is numb."
2. `moderate` stays well above the ~15% null floor — graceful degradation, not a cliff.
3. `deep` reads ~0% on the structural metric **but** is still flagged derivative by AUX1 /
   C06b / C06e / C06d — demonstrating *why the harness is multi-signal* and pinning the
   exact boundary where structure-only detection fails.

If `paraphrase` does **not** light up the load-bearing twin, that is a genuine
**falsification** of the structural metric — report it; it would mean the v6/v7 0% is less
informative than claimed. If `deep`+`transformed` slips *every* signal, that bounds what
the whole harness can detect and belongs in Threats.

## Keep separate from the harness bundle
Fixture numbers are corroborative/diagnostic, from standalone clones — never fold them into
the canonical 8-signal tables/figures (CLAUDE.md load-bearing invariant). `main.tex` is not
edited by this experiment.
