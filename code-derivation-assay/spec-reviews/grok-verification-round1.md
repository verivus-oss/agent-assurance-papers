# ADVERSARIAL VERIFICATION REVIEW — Grok Round 1 (Code, Data, Re-execution)

**Reviewer:** Grok 4.3 (xAI)  
**Date:** 2026-05-30  
**Scope:** Entire directory `/srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay/` treated as the "diff" (SPECIFICATION.md v0.8 + pilot/ + power/ + family-census.md + legal-framework.md + prior reviews in spec-reviews/ for context only).  
**Method:** (1) `cd` to dir; (2) direct inspection of every load-bearing script; (3) re-execution of the three cited reproduction commands with full stdout capture; (4) every numeric claim traced to file:line + quoted code or exact command output; (5) no prose accepted as evidence; (6) prior reviews read only for context, never as authority.  
**Reproduction commands executed (all succeeded):**
- `python3 pilot/pilot_harness.py` (19.8s; chardet sources present at hardcoded paths; CORPUS present)
- `python3 pilot/residual.py` (/tmp/fzsrc present with 6 fuzzy dirs; ran cleanly)
- `python3 power/power_analysis.py` (220.5s / ~3.7min; seeded, deterministic)

**Verdict format per instructions:** Numbered list of CONCRETE BLOCKERS only. Each is a specific code/doc/data defect with file:line + verbatim quote or output + why it falsifies the claim. No approval on intent, plan, or "will be fixed." Verified positive evidence is noted per claim but does not override blockers.

---

## Verified Claims (Evidence Cited)

### 1. power_analysis.py: genuinely family-clustered bootstrap (BCa + family jackknife), implements K_test/θ_LB analysis in POWER-ANALYSIS.md

**Code (power/power_analysis.py:97-121):**
```python
def bca_lower(rng, fam_auc, n_boot, lb_pct):
    K = len(fam_auc)
    theta_hat = fam_auc.mean()
    idx = rng.integers(0, K, size=(n_boot, K))  # FAMILY resample (clusters)
    boot = fam_auc[idx].mean(axis=1)
    ...
    jack = np.array([np.delete(fam_auc, i).mean() for i in range(K)])  # FAMILY jackknife accel
    ...
    return float(np.quantile(boot, adj)), float(theta_hat)
```
(See also: `naive_pair_lower:124` (pools pairs — the wrong one, for comparison); `power_cell:147` calls bca_lower; `main:261` sweeps K=2..8, mean_auc, tau, theta_lbs=[0.60,0.65,0.70]; RQ4 at 177; calibration at 208.)

**Re-run output (exact match to POWER-ANALYSIS.md tables within documented sim variance for reduced cells):**
```
=== H1 AUC power (theta_LB=0.70), family-clustered BCa lower bound ===
-- moderate_het, pairs=5v5 --
   0.86   | 0.75  0.65  0.65  0.67  0.70  0.75   (K=2,3,4,5,6,8)
   0.90   | 0.87  0.82  0.81  0.85  0.89  0.93
=== Naive pair-level bootstrap INFLATION (theta_LB=0.70, 5v5, tau=0.35) ===
   0.90   5      0.83            0.93
=== RQ4 Spearman ... ===
    3     0.25   0.00
    6     0.25   0.33
=== Calibration ... N=40 ===
  40    0.031      0.156            0.037   (fixed-10 ECE bias)
```
**Matches:** POWER-ANALYSIS.md:24-34 (K>=5-6 required, K=2 anomaly, θ_LB=0.65 provisional), :44-49 (theta sensitivity), :69-74 (naive inflates), :79-86 (RQ4 needs >=6-8), :91-99 (ECE 0.156 at N=40), :321-353 (exact console format and values). The bootstrap is family-clustered exactly as §9.1 of SPEC and §1 of POWER-ANALYSIS require; pair-level is only the diagnostic "wrong" comparator.

### 2. pilot_harness.py: PILOT-RESULTS.md numbers reproduce (v6→v7 ST envelope [0.42…0.99], BHd=0.135, AUCs, AI rewrite at INDEPENDENT baseline)

**Re-run (full key excerpts; pilot/results.json overwritten with identical values):**
```
=== STRUCTURAL ENVELOPE — 6 measures ...
v6-v7   DERIVED-airewrite    0.42  0.99  0.88  0.86  0.89  0.88   0.42   0.99
...
=== directional AUC (same-lineage 3 pos vs INDEPENDENT 3 neg) ===
  AUC[   ST_wl] = 1.000
  ...
  AUC[     BHd] = 0.556
  AUC[combined] = 0.667
=== disputed AI-rewrite v6-v7 ===
  ST envelope [0.416 … 0.986]  PBt=0.000  BHd=0.135
```
(See: pilot_harness.py:366-369 (envelope sort), 373 (bhd on disc=223), 394-396 (auc), 433 (print), 362 (PAIRS), structural import:40.)

**Matches PILOT-RESULTS.md:17-24 (table with 0.42/0.99/0.88/0.86/0.89/0.88 envelope [0.42…0.99], BHd=0.135), :24 (AUCs incl WL 1.00, combined 0.67, BHd 0.56), :46 (AI at/below independent baseline on ST/BH/PB/quirk).** Slight rounding in md (0.416→0.42, 0.986→0.99, 0.1345→0.135) but direction, envelope, and "sits at the INDEPENDENT baseline" claim hold exactly on re-execution.

### 3. structural.py: WL kernel gives AUC 1.0 and contradicts predecessor's WL (0.587 for v6→v7); real (different construction), not a reimplementation bug in this code

**Code exercised (pilot/structural.py:91-110 + harness call 367):**
```python
def wl_cosine(ga, gb, k=4):
    """C06a' analog: WL subtree kernel — cosine of the label multiset accumulated
    over k refinement iterations (degree-seeded, successor-aggregated)."""
    def labels(g):
        lab = {n: f'{g.in_degree(n)}_{g.out_degree(n)}' for n in g.nodes()}
        ...
        for _ in range(k):
            ... f'{lab[n]}>{nb}'  # successor labels only
    ...
    return dot / (na * nb) ...
```
**Run (via pilot_harness.py):** ST_wl v6-v7 = 0.8907; v6-csn=0.5039, v7-csn=0.59 → AUC[ST_wl]=1.000 (perfect separation on 3 pos vs 3 neg). Envelope includes it as the high end (0.99).

**Predecessor claim (PILOT-RESULTS.md:37,26,44):** "WL kernel, fine (C06a′) ... v6→v7 = 0.587" and "v6↔csn = 0.872"; "my WL-kernel reimplementation gives AUC 1.00 ... while the predecessor's WL gave the opposite (v6→v7 = 0.587 *below* v6↔csn = 0.872)".

**Finding:** This reimplementation (call-graph + degree-seeded k=4 WL on name-based approx graph from build_call_graph:33) produces the opposite ordering and AUC 1.0 on the real artifacts. No bug in the code (it is deterministic, exercised by the harness, produces consistent per-pair values that match the printed table). The contradiction is real and illustrates the L4 matcher-dependence lesson the doc draws. The specific 0.587/0.872 values are external (predecessor study) and not reproducible from any file in scope.

### 4. residual.py (§5.4): jellyfish↔textdistance false-positives at residual 12; fuzzywuzzy→RapidFuzz=2, →thefuzz=7; filtration (baseline + API) implemented as described

**Re-run output (exact):**
```
INDEPENDENT  jellyfish↔textdistance     12      12      12       0
  residual after API filter (12 idents): ['TypeError', 'ValueError', 'common_chars', 'long_tolerance', ..., 'zip_longest']
DERIVED  fuzzywuzzy→RapidFuzz (GPL→MIT reimpl)     14       8       2       0
  ... (2 idents): ['len_ratio', 'string_out']
DERIVED  fuzzywuzzy→thefuzz (fork)     18      16       7       0
  ... (7 idents): ['force_ascii', 'default_scorer', ...]
DERIVED  v6→v7 (AI rewrite)            25      18      13       1
  ... (13 idents): ['CHINESE_SIMPLIFIED', ..., 'ascii_letters', 'encoding_era', ...]
EVOLVED  v5→v6 (human)                292     281     228      15
```
**Code (pilot/residual.py:121-131,124-126):**
```python
def residual(A, B, baseline, label):
    base_idist, base_msg, base_flt = _union(baseline, 'idist'), ...
    api = A['api'] | B['api']
    sh_id = A['idist'] & B['idist']
    res_dom = sh_id - base_idist                 # AFC filtration: drop domain-shared
    res_api = res_dom - api                       # drop compatibility/API-dictated
    ...
```
**Matches PILOT-RESULTS.md:84-92 (table with 13/228/2/7/12 and examples), :92 (false-pos cause: "Python builtins/stdlib and algorithm-canonical variable names (the textbook Jaro variables) were not filtered"; _STOP:28 lacks TypeError etc.).** Filtration logic is exactly "baseline + API" as §5.4 describes. (Note: for the jelly-text row, code passes only `[levenshtein]` as baseline — see Blocker 2.)

### 5. Spec internal consistency (cross-language v0.6, copyleft-first-class v0.4, AFC §5.4) — mostly backed; one gap

- **Cross-lang (SPECIFICATION.md:11, §5.2, §18.4, §13; family-census.md:5,44):** PI decision documented; family-census updated for XLANG edges (markdown-it-py, node-semver-py, hashids-py) as separate stratum; BH called "more robust cross-language signal". **Backed in prose.** **Not backed in code:** pilot/structural.py:1-160 and pilot_harness.py:7-444 contain only Python `ast` + networkx; zero per-language walkers, zero xlang descriptor layer, zero stratum logic. Pilot data is chardet+csn only.
- **Copyleft-first-class (SPECIFICATION.md:6,14, §2, §6.2; family-census.md:4,20,51):** Explicit: "copyleft ... are **first-class** ... redistributed **verbatim with notices** as a segregated mere-aggregation". **Backed:** pilot/residual.py:162 and harness run successfully on GPL fuzzywuzzy/thefuzz + LGPL chardet sources (from /tmp/fzsrc and external checkouts); fuzzy GPL→MIT reimpl treated as DERIVED in residual table.
- **AFC §5.4 (SPECIFICATION.md:111-117; legal-framework.md:12-47; pilot/PILOT-RESULTS.md:81-94):** Full description of "enumerate → filter (baseline + API) → score residual"; legal mapping to Sega/Sony/Altai. **Backed in pilot code:** residual.py:59-131 (features + residual exactly as described); harness quirk extraction:151-185; legal-framework.md used to justify PB quirks. Pilot explicitly calls the measure "promising but not yet validated" due to thin filtration (honest).

### 6. Other overclaims / unsupported / methodological notes (from docs-vs-code)

- All three reproduction scripts run and regenerate their results.json + console numbers that match the cited .md tables (within documented rounding/variance).
- No evidence of fabricated data or hidden hardcoding of pilot numbers (re-runs produce the values from the sources).
- Hardcoded paths (pilot_harness.py:41-43, residual.py:24-26) mean "reproduce" is host-specific; works here only because /srv/repos/public/... and /tmp/fzsrc exist. Not a self-contained artifact.
- No top-level Makefile, validate/, harness/, benchmark/ dirs (SPECIFICATION.md:15, §10.1, §17 describe `make validate` regenerating from raw, no-drift, etc. as core gates). This is a design doc at pilot stage; the pilot scripts themselves are reproducible by direct invocation.

---

## CONCRETE BLOCKERS (defects that block approval)

**1. SPECIFICATION.md:117 (and PILOT-RESULTS.md:79) — "~8 arbitrary shared names after API filtering" for chardet v6→v7 residual.**

   **Evidence:**
   - SPEC: "For chardet v6→v7 the residual is small-but-non-zero (~8 arbitrary shared names after API filtering — small but non-zero...)"
   - PILOT-RESULTS.md:79: "For chardet v6→v7 that residual is **small but non-zero** (~8 arbitrary shared names)"
   - **Actual (pilot/residual.py:156 run, 2026-05-30):** "residual after API filter (13 idents): ['CHINESE_SIMPLIFIED', 'CHINESE_TRADITIONAL', 'LEGACY_ISO', 'LEGACY_MAC', 'LEGACY_MAP', 'LEGACY_REGIONAL', 'MODERN_WEB', 'NON_CJK', 'ascii_letters', 'encoding_era', 'ignore_threshold', 'lang_filter', 'max_bytes']"

   **Why blocker:** Direct numeric contradiction between the §5.4 claim (and the pilot it cites) and the output of the exact script (`python3 pilot/residual.py`) + data it reports. (PILOT table at line 87 correctly lists 13; the ~8 is stale prose that was never updated when the residual count changed. Violates "No unsupported assertions" and "verify against code/data".)

**2. pilot/PILOT-RESULTS.md:90 (report header) and :92 — "baseline pool = {jellyfish, Levenshtein, textdistance}" (3-lib) for the jellyfish↔textdistance INDEPENDENT false-positive at 12; "the 3-lib baseline was too thin".**

   **Evidence:**
   - PILOT-RESULTS.md:90: "INDEPENDENT  jellyfish↔textdistance | **12 (false pos)** ... (baseline pool = {jellyfish, Levenshtein, textdistance})"
   - :92: "the independent control false-positived at 12 because ... the 3-lib baseline was too thin and no builtin/stdlib stoplist was applied."
   - **Actual code (pilot/residual.py:166-170):**
     ```python
     indep = [fz['jellyfish'], fz['levenshtein'], fz['textdistance']]
     ...
     residual(fz['jellyfish'], fz['textdistance'], [fz['levenshtein']], 'INDEPENDENT  jellyfish↔textdistance'),
     ```
     (Only `[levenshtein]` — 1-lib — passed for this pair; the other two use full `indep`.)

   **Why blocker:** The experiment description in the doc that introduces the §5.4 measure mis-states the actual filtration applied to the key false-positive control row. The 12 is real (and includes the Jaro vars + builtins the doc correctly diagnoses), but the "3-lib" claim is false. This is a doc-vs-code defect in the load-bearing pilot evidence for "the measure is only as good as the filtration."

**3. pilot/PILOT-RESULTS.md:26,37,44 — specific predecessor WL numbers "v6→v7 = 0.587 *below* v6↔csn = 0.872" used to assert "genuinely CONTRADICT the predecessor's WL".**

   **Evidence:**
   - PILOT-RESULTS.md:37 (table): "WL kernel, fine (C06a′) | ... | 0.587" (v6-v7) and 0.872 (v6-csn).
   - :26,44: "while the predecessor's WL gave the opposite (v6→v7 = 0.587 *below* v6↔csn = 0.872)"; "cherry-pick ... WL-fine → 0.42 / 0.587 ('independent')".
   - **In scope:** zero files, scripts, or data under the assayed directory contain the predecessor's WL implementation or produce 0.587/0.872. (Grep for 0.587 finds only unrelated power json stats + this prose citation.)

   **Why blocker:** The central "even a single named measure (WL) is implementation-fragile" claim (used to justify R-ABLATE and the envelope) rests on a numeric assertion about external code that cannot be verified against any artifact in the reviewed scope. Per rules: "Every finding MUST cite file:line + quoted code or actual command output." The 0.587 is unsupported.

**4. SPECIFICATION.md:11 (v0.6), §5.2, §18.4, §13 + family-census.md:5 — "cross-language ST/PB enabled ... the harness compares an edge cross-language *where the derivation actually spans languages* ... via per-language AST walkers + a language-agnostic structural-descriptor layer".**

   **Evidence:**
   - SPEC: "PI decision: cross-language ST/PB enabled (was Python-only) — the harness compares ... via per-language AST walkers + a language-agnostic structural-descriptor layer; cross-language and within-language pairs are **separate strata, never pooled in the headline**."
   - family-census.md:5,44: "Cross-language ST/PB is ENABLED (PI decision, spec v0.6)"; "~3 cross-language ... add ~3 more both-class domains as a separate cross-language stratum".
   - **Actual code:** pilot/structural.py:1-160 (and pilot_harness.py:334-368 calls) are 100% Python `import ast` + networkx call graphs on `.py` files only. No JS/TS/Rust/etc parsers, no xlang normalization, no stratum handling. Power/ is pure simulation.

   **Why blocker:** The spec presents cross-language capability as a resolved, harness-supported feature (v0.6 decision folded into design). No such code exists in the assayed tree. This is an overclaim of implementation status in a "corrective-program spec" whose credibility rests on "claims backed by code."

**5. SPECIFICATION.md:6,14, §10.1, §15 (layout), §17 (acceptance), §10.2 etc. — `make validate` regenerates results from raw pinned inputs, no-drift, hermetic BH, figures from results.json, R-NODRIFT/R-HERMETIC/R-FIG as core gates.**

   **Evidence:**
   - SPEC §15 shows full tree with `Makefile`, `validate/no_drift.py`, `harness/`, `benchmark/`, `container/`.
   - §10.1: "`make validate` **regenerates results from raw pinned inputs in the same run** (never trusting a committed results object)"; "CI **MUST** fail closed".
   - §17: "A reviewer must be able to verify **all** of: 1. `make validate` exits 0 ..."
   - **Actual tree (ls + find):** No Makefile at root; no validate/, harness/, benchmark/, container/ directories or .py files implementing the described machinery. Only the ad-hoc pilot/*.py + power/*.py + results.json (plus docs).

   **Why blocker:** The "corrective-program spec" repeatedly presents a full reproducibility/automation apparatus (the L2/L8/L9/L10 fixes) as already-architected and normative. The assayed code contains none of it — only two standalone pilot scripts whose reproducibility depends on host-specific external git checkouts at hardcoded paths. This is a structural mismatch between claimed corrective engineering and delivered code at the P0 stage.

---

## Summary of Verified Positives (Does Not Override Blockers)

- Family-clustered BCa + jackknife in power_analysis.py is correctly implemented and matches its own design doc on re-run.
- pilot_harness.py + structural.py + residual.py all re-execute and reproduce the exact numeric claims in PILOT-RESULTS.md (within rounding) for the chardet + fuzzy cases.
- AFC filtration logic (baseline subtraction + API filter) is present in residual.py:124-126 and produces the reported 13/228/2/7/12 values.
- WL variant in structural.py produces the AUC 1.0 / opposite-to-cited-predecessor behavior on real data; supports the matcher-dependence narrative without code bug.
- Copyleft inputs (fuzzy GPL) are successfully processed by the pilot scripts; AFC/legal framing is consistently reflected in pilot/residual.py + legal-framework.md.
- No evidence of data fabrication or post-hoc number hardening in the three scripts (re-runs match committed results.json and md tables).

The pilot/power mechanics that *are* implemented are sound and reproducible. The blockers are documentation/code mismatches, unsupported external citations, and a gap between the full "corrective infrastructure" described in SPECIFICATION.md and the actual delivered pilot-stage code.

**End of review.** Persisted to spec-reviews/grok-verification-round1.md. All citations are from direct file reads + the three re-execution outputs captured 2026-05-30.