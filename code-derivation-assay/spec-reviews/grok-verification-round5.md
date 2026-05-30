# Grok Verification — Round 5 (FULL fresh re-verification post round-4 fixes; zero-trust)

**Date:** 2026-05-30 (round performed).  
**Artifact:** /srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay (SPECIFICATION.md v0.8.1 + pilot/ + power/ + family-census.md + legal-framework.md + MULTI-FAMILY-RESULTS.md + all supporting code).  
**Method:** Zero-trust re-examination from scratch. Did **not** consult or rely on prior round approvals, correction logs, or previous verdicts for any claim. Verified exclusively against the **FILES** (source, docs, results.json) and **fresh script output**. Re-ran every executable listed. Cross-checked every numeric/claim at explicit file:line against actual output. Judged **all design claims** strictly against the "Implementation status (P0)" block at SPECIFICATION.md:8 (pilot only; full harness/MANIFEST/validate/§5.4-complete/cross-lang "designed but NOT yet built").

**Commands re-executed (fresh, in this workspace, in order):**
- `python3 pilot/pilot_harness.py` (git-archive extracts of chardet v5/v6/v7 + csn at package scope; full 6-measure ST envelope + BH on 223-discriminating hard workload + all quirk signals + AUCs; overwrote pilot/results.json)
- `python3 pilot/residual.py` (§5.4 AFC filter-then-residual on chardet + fuzzy families; 13/228/2/7/12 counts + exact residual lists + thin-baseline false-positive; overwrote? no, stdout only)
- `python3 pilot/multi_family_pilot.py` (NEW: static ensemble + leave-pair-out §5.4 residual on **three** families: encoding/fuzzy/toml; exact PQidist/resApi/ST envelopes for reimpl/fork/vendored vs indep bands; overwrote? no, stdout only)
- `python3 power/power_analysis.py` (full seeded simulation: H1 power map, naive pair-level inflation demo at K=5, RQ4, calibration SE; ~3.5 min; overwrote power/results.json)

**Files inspected in full or targeted extracts (load-bearing + every table/numeral cited in the query):**
- All four primary docs: PILOT-RESULTS.md (entire), MULTI-FAMILY-RESULTS.md (entire), POWER-ANALYSIS.md (entire, focus §5.1/§7), SPECIFICATION.md (entire, focus P0 block:8, §5.2/5.4:97-122, §19:345-362, revision history, design qualifiers)
- legal-framework.md (entire; AFC mapping at 39/47)
- family-census.md (entire; draft status + power-tally)
- All pilot scripts: pilot_harness.py, residual.py, multi_family_pilot.py, structural.py, _detect_runner.py
- power/power_analysis.py (naive block + seeding)
- pilot/results.json + power/results.json (post-run spot-checks of every cited row)
- spec-reviews/round4-corrections.md (only for identifying the six claimed fixes; **not** for trusting their resolution)

---

## (a) The six round-4 corrections — verified against files + fresh output

1. **PILOT-RESULTS.md:50** ("No measure *robustly* separates... per-measure AUC spans 0.11–1.00, but the high values are artifacts (WL=1.00 is a name-vocabulary artifact; PQmsg=1.00 is a generic-phrase artifact)"):  
   Exact text present. Fresh `python3 pilot/pilot_harness.py` confirms: per-measure AUCs include ST_wl=1.000 (artifact), PQmsg=1.000 (artifact, only generic "with confidence"), others 0.11–0.89; combined 0.667; WL name-based per structural.py:47 `defined.add(n.name)`. Matches PILOT-RESULTS.md:24-28 + 50-51.

2. **PILOT-RESULTS.md:51** ("...chardet v7's is small but non-zero (residual 13 raw, mostly kept era-enum naming + stdlib false positives)"):  
   Exact text present. Fresh `python3 pilot/residual.py` + `pilot_harness.py` confirm residual 13 for v6→v7 post-API (list includes encoding_era, lang_filter, ascii_letters, max_bytes, LEGACY_*, NON_CJK, MODERN_WEB, CHINESE_*; MINIMUM_THRESHOLD/UniversalDetector/etc. filtered as API). Matches 51 + 77-79 + 87.

3. **PILOT-RESULTS.md:77** (API-removed list now correctly has MINIMUM_THRESHOLD; residual list has encoding_era, lang_filter + stdlib false positives):  
   Exact: "after removing the public-API names (`UniversalDetector, detect_all, EncodingEra, LanguageFilter, MINIMUM_THRESHOLD` ... 13 remain ... `LEGACY_ISO/MAC/MAP/REGIONAL, MODERN_WEB, NON_CJK, encoding_era, ignore_threshold, lang_filter` (plus stdlib false positives `ascii_letters, max_bytes`)". Fresh residual.py stdout: the 13-list contains encoding_era/lang_filter/ascii_letters/max_bytes but **not** MINIMUM_THRESHOLD. Matches harness distinctiveness (18 lineage-specific incl. MINIMUM) → residual filter. Correct swap per round-4 correction.

4. **legal-framework.md:39,47** ("small but non-zero… genuinely contestable — CDA renders no verdict (§14)"; "calibrated read ... is **contestable** — stated as measurement, never a verdict (§14)"):  
   Exact text at 39 ("residual 13 raw identifiers, mostly kept era-enum naming + stdlib false positives; data tables regenerated. **Under AFC this is genuinely contestable — CDA renders no verdict**") and 47. Matches pilot output + P0 framing. No stronger "≈0 / likely not derivative" claim remains.

5. **SPECIFICATION.md §19:354** ("the chardet pair in fact reads as **matcher-dependent ST [0.42–0.99] (not ≈0), PB literal ~0, and a small non-zero arbitrary-name residual (13 raw)** — i.e. indistinguishable from independent on aggregate measures"):  
   Exact text present. Fresh `pilot_harness.py`: ST envelope [0.416…0.986] (doc rounds), PBt=0.000 for v6-v7, residual 13. Matches. No "ST≈0 / PB-elevated" language remains.

6. **POWER-ANALYSIS.md §7:111** ("full ST/PB/BH on **one** family (chardet); STATIC measures extended to **three** families (`pilot/multi_family_pilot.py`, `pilot/MULTI-FAMILY-RESULTS.md`); full BH still single-family"):  
   Exact text present at 111 (and 113). Fresh multi_family_pilot.py run confirms static-only on three families (encoding/fuzzy/toml); BH requires per-family adapters (explicit in MULTI-FAMILY-RESULTS.md:31 and multi_family_pilot.py:5). Matches.

**All six corrections are present in the files at the cited lines and match fresh code/output exactly.**

---

## (b) §5.1 naive-inflation table (POWER-ANALYSIS.md:69-73) — K=5 rows confirmed

Doc table (with explicit "(at **K=5**)" header per correction):

| mean AUC (at **K=5**) | family-clustered | naive pair-level |
| 0.86 | 0.66 | 0.71 |
| 0.90 | 0.83 | 0.93 |

Fresh `python3 power/power_analysis.py` console (naive block, 5v5, tau=0.35):

```
   0.86   5      0.66            0.71
   0.90   5      0.83            0.93
```

power/results.json post-run naive_inflation K=5 rows: family_clustered 0.66/0.83, naive 0.7067/0.9317 (print rounds to 0.71/0.93). Exact match to doc table rows. The 0.82 K=5 (0.44/0.46) row is **not** in the doc table (was the prior misread). **Confirmed; no defect.**

---

## (c) NEW multi-family claims (pilot/multi_family_pilot.py + MULTI-FAMILY-RESULTS.md) — reproduce exactly

Fresh `python3 pilot/multi_family_pilot.py` output (leave-pair-out baseline):

**encoding (chardet v6→v7 AI reimpl):** ST [0.42,0.99], PQidist 0.020 (indep band 0.013–0.020), resApi 13 (11–16) → **inside band, indistinguishable (NO)**

**fuzzy (fuzzywuzzy→RapidFuzz human GPL→MIT reimpl):** ST [0.70,0.99], PQidist 0.046 (indep 0.000–0.072), resApi 2 (0–12) → **inside, indistinguishable (NO)**

**fuzzy (fuzzywuzzy→thefuzz fork):** PQidist 0.198 (>0.072), res 7 → **detected (yes)**

**toml (tomli→tomllib vendored copy):** ST [0.76,1.00], PQidist **0.906** (indep 0.013–0.026), resApi **68** (0–1) → **strongly detected (YES)**; all AUC=1.000

**MULTI-FAMILY-RESULTS.md tables + findings 1-5 + bottom line** match the stdout **exactly** (including 0.906/68, RapidFuzz 2, leave-pair-out false-pos 12/1 for thin baselines, "clean reimplementation indistinguishable... vendoring/forking detected", "the blind spot coincides with the legal 'fair-use reimplementation' region"). Code: multi_family_pilot.py:110 (leave-pair-out), 124-129 (reimpl vs band), 136-138 (reading). **All claims reproduce from the script.**

---

## (d) Any remaining overclaim/inconsistency/doc-vs-code gap anywhere?

**Full scan (docs + code + fresh runs + results.json + P0 framing):**

- **No numeric mismatches.** Every cited value (ST envelopes [0.42,0.99]/[0.70,0.99]/[0.76,1.00], residuals 13/228/2/7/12/68, PQidist 0.020/0.046/0.198/0.906, AUCs 0.11-1.00 with WL/PQmsg=1.0 artifacts, power K=5 naive 0.66/0.71 + 0.83/0.93, BHd 0.135 inside indep spread 0.072-0.430, etc.) matches fresh stdout or correctly rounded from pilot/results.json + power/results.json.
- **No stale claims.** The six pre-fix phrases appear **only** in review logs (round4-corrections.md, codex-verification-round4.md), not in current artifact docs.
- **P0 scoping enforced.** SPECIFICATION.md:8 (full block) + 100/120/190/255/257 + POWER §7:111 + MULTI-FAMILY-RESULTS:31 + PILOT-RESULTS:99-100 + structural.py:8-14 (WL name-based artifact disclosure) + pilot_harness.py:41-43 (hardcoded external paths) + multi_family_pilot.py:27-31 (/tmp + /usr/lib64 tomllib) all correctly label: pilot only; Python-ast only; no MANIFEST/redistributed corpus; §5.4 is prototype (idents/msgs/consts only, no calibrated improb + CI + full quirk types); full harness/validate/R-NODRIFT/hermetic/cross-lang "designed but NOT yet built"; family-census is "DRAFT... VERIFY... scouting"; power is "provisional... assumed effect sizes... conditional on pilot". Design claims are **not** presented as current facts.
- **No internal inconsistencies.** legal-framework.md AFC mapping (39/47) aligns with pilot residual 13 + "contestable, no verdict". POWER naive table now has explicit K=5 + matches code. MULTI-FAMILY correctly exposes thin-baseline false-pos (jellyfish-textdistance res=12) as caveat, not hidden. Harness + structural + residual + multi all consistent on filtration, name-based WL, leave-pair-out, package-scope handling of v7 src/.
- **No scope violations or fabricated results.** n=6/3-families explicitly "direction/sanity pilot, not powered". BH only on chardet (single-family). No claim of full §5.4 / make validate / 18-24 families built. External citations (predecessor C06 numbers) labeled as such.
- **Hardcoded paths / env assumptions:** Present in pilot scripts (CHARDET=/srv/repos/public/..., FZSRC=/tmp/fzsrc, TOMLLIB=/usr/lib64/python3.13/tomllib). **Disclosed** in P0 block ("pilot reads external local checkouts at hardcoded paths"), PILOT-RESULTS header, MULTI-FAMILY-RESULTS:32 caveats. Runs succeed in this env and produce documented numbers; not presented as portable production code.
- **Other:** family-census evidence tiers/VERIFY flags remain (explicitly draft); no overclaim of frozen pre-reg input. All revision-history numbers trace to verified pilot/power outputs.

**Zero remaining overclaims, inconsistencies, or doc-vs-code gaps under the P0 framing.**

---

## Judgment against "Implementation status (P0)" block (SPECIFICATION.md:8)

**Actually implemented (matches code):** Python-only pilot harness (pilot_harness + structural + residual + multi_family); 6 ST + BHd + PBt/PBi + 4+4 quirk signals on chardet trio; §5.4 residual *prototype* (idents/msgs/consts, AFC filter + API subtraction, leave-pair-out) on chardet + fuzzy + toml (3-family); seeded power simulation (first-order cluster BCa, naive demo, RQ4 sign-test, calibration SE); results.json artifacts; all docs' numeric claims.

**Designed but NOT yet built (correctly labeled as such, not claimed as current):** cross-language ST/PB (pilot Python-ast only); redistributed MANIFEST-backed corpus (pilot uses external hardcoded checkouts); make validate / R-NODRIFT / R-HERMETIC / R-FIG + harness/validate/benchmark/container/Makefile tree; full §5.4 (calibrated improbability + CI + comment/dead-code/data-table/behavioral types); full BH adapters for >1 family; ≥18-24 families / 150-220 pairs benchmark; confirmatory results.

**Verdict:** Every claim in the artifact respects the P0 boundary. No design element is presented as shipped code. The pilot + power + docs are internally consistent and reproducible from the re-run commands.

---

## Final Determination

**(A) UNCONDITIONAL APPROVAL of the whole artifact.**

**Specific evidence (reproducible today):**

- Re-ran `python3 pilot/pilot_harness.py ; python3 pilot/residual.py ; python3 pilot/multi_family_pilot.py ; python3 power/power_analysis.py` — all exit 0, outputs match every cited table/numeral/claim at file:line in PILOT-RESULTS.md, MULTI-FAMILY-RESULTS.md, POWER-ANALYSIS.md §5.1/§7, SPECIFICATION.md §19, legal-framework.md:39/47.
- All six round-4 corrections are present and accurate (verified at exact lines + output).
- Naive K=5 table (0.86→0.66/0.71, 0.90→0.83/0.93) matches fresh power run + results.json exactly.
- NEW 3-family claims (RapidFuzz residual ~2 / PQidist 0.046 inside band; tomli→tomllib 0.906/68 detected; fork detected; leave-pair-out) match multi_family_pilot.py stdout + MULTI-FAMILY-RESULTS.md tables verbatim.
- Zero doc-vs-code gaps or overclaims under P0 scoping (SPECIFICATION.md:8 is accurate and enforced everywhere).
- Pilot mechanics (name-based WL artifact disclosed, thin-baseline false-pos exposed, package-scope v7 src/ handled, deterministic git-archive + seeded power) are sound and match their own caveats.

The artifact is clean, reproducible, and honest about its P0/pilot scope. Ready for next phase.

**Persisted:** this file (spec-reviews/grok-verification-round5.md).