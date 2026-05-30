# Grok Verification — Round 4 (FULL fresh adversarial, entire artifact)

**Date:** 2026-05-30 (round performed).  
**Artifact:** /srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay (SPECIFICATION.md v0.8.1 + pilot/ + power/ + family-census.md + legal-framework.md + all supporting code/data).  
**Method:** Zero-trust re-examination from scratch. Re-ran every executable, extracted every numeric/claim, cross-checked file:line against actual script output, results.json, and source. Did not consult or rely on prior round approvals for any claim. Judged every claim against the explicit "Implementation status (P0)" framing at SPECIFICATION.md:8 (only flag as blocker if presented as already-built or internally inconsistent with that scoping).

**Commands re-executed (fresh, in this workspace):**
- `python3 pilot/residual.py` (verified §5.4 residual counts, filtration examples, false-positive case)
- `python3 pilot/pilot_harness.py` (full run: git-archive extracts of chardet v5/v6/v7 + csn, structural envelope, BH on 223-discriminating hard workload, quirk signals, AUCs; overwrote pilot/results.json)
- `python3 power/power_analysis.py` (full 2000×2000 sims + RQ4 + calibration; deterministic SEED=20260530; overwrote power/results.json; ~3.5 min)

**Files inspected in full or targeted extracts (all load-bearing sections + every table/numeral):**
- SPECIFICATION.md (entire; P0 block lines 8-8, revision history 10-25, §4 RQs 77-89, §5.2/5.4 signals+residual 97-122, §9 stats 188-199, §6 benchmark 124-159, §13 threats 246-258, §19 related 345-362, etc.)
- pilot/PILOT-RESULTS.md (entire; all iteration tables, AUCs, distinctiveness, caveats)
- power/POWER-ANALYSIS.md (entire; all tables in §2/3/5, limitations §6, pilot requirements §7)
- pilot/pilot_harness.py (entire; PAIRS, extract_static, BHd, auc(), structural calls, quirk extraction)
- pilot/residual.py (entire; features(), residual(), chardet+fuzzy scenarios, thin-baseline calls)
- pilot/structural.py (entire; build_call_graph:47 `defined.add(n.name)`, wl_cosine, per_function_similarity, docstring caveats)
- pilot/_detect_runner.py (entire; BH adapter)
- power/power_analysis.py (entire; bca_lower first-order, simulate_test_set, rq4_power sign test, calibration_se, main sweep + console rendering)
- pilot/results.json + power/results.json (post-run; every cited row/AUC/power value spot-checked)
- family-census.md (entire; evidence tiers, tally §2, VERIFY flags, cross-lang §1)
- legal-framework.md (entire; AFC mapping, no numeric claims requiring code verification)
- spec-reviews/round1-corrections.md (for traceability of prior fixes only; re-verified independently)

**Verification summary (all inspected claims).** Every numeric/claim in the three primary docs traces to one of:
- Direct script output from the re-runs above (exact or correctly rounded).
- Explicitly labeled "pilot / simulation / provisional / draft / scouting / designed-not-built".
- The P0 status block + inline qualifiers ("not yet implemented", "Python-only", "first-order ... refinement not yet implemented", "thin n=1 baseline", "name-based ... artifact", "external citation not reproducible here").
No claim presented a future design element as already-built. No unsupported/fabricated number survived cross-check except the one documented below. No methodological error in the implemented pilot/power logic (Mann-Whitney AUC, family-clustered BCa first-order, AFC filtration, thin-baseline false-positive demonstration, SEED determinism, etc.). Internal consistency holds under the P0 framing.

**Specific evidence verified (commands + file:line):**

- Residual 13 for chardet v6→v7 (post-API filter), 228 EVOLVED, 7 fork, 2 clean-reimpl, 12 independent false-pos on thin baseline: `python3 pilot/residual.py` stdout exact match to PILOT-RESULTS.md:84-91 table + SPEC:120 examples (ascii_letters, max_bytes, encoding_era, LEGACY_*, MODERN_WEB, NON_CJK in the 13-list); residual.py:170 thin [levenshtein] call + 124-126 filtration logic. (Lines: residual.py:121-131, PILOT-RESULTS.md:77-79+84-94, SPECIFICATION.md:120+11.)
- Structural envelope [0.42…0.99] for v6-v7, per-measure AUCs (ST_sh=0.333, cfg=0.556, nh=0.111, topo=0.556, **WL=1.000**, pf=0.333, BHd=0.556, PQmsg=1.000 artifact, QKidist=0.889, combined=0.667), v6-v7 ST [0.416…0.986] / PBt=0 / BHd=0.135 within independent spread (v7-csn BHd=0.072): `python3 pilot/pilot_harness.py` stdout tables + AUC print + distinctiveness (25 shared distinctive, 18 lineage-specific) exact (within rounding) to PILOT-RESULTS.md:17-26+46+63-65+71-75 tables + SPEC:12+100+115. harness.py:362-396 (ST_* + auc), 334 (structural calls), 423-427 (distinctiveness). structural.py:41-70 (name-based `defined.add(n.name)`). pilot/results.json post-run rows match. (Lines: pilot_harness.py:362-439, structural.py:38-70+99-118, PILOT-RESULTS.md:17-28+43-47+74-79, SPECIFICATION.md:12+24+100+115+120.)
- Power H1 map (moderate_het 5v5 θ_LB=0.70 slice): K=5/6/8 powers for AUC 0.78/0.82/0.86/0.90/0.94 exactly as printed in POWER-ANALYSIS.md:26-33 table (e.g. 0.86 @ K=6 = 0.70, K=8=0.75; 0.90 @ K=5=0.85 etc.): `python3 power/power_analysis.py` console summary matched. (power_analysis.py:261-274+321-335, POWER-ANALYSIS.md:26-33.)
- θ_LB sensitivity ranges (K≥5 trustworthy): 0.60/0.65/0.70 for AUC 0.82/0.86/0.90 exactly match doc table (e.g. 0.65 @0.82 = 0.62–0.76): extracted from fresh power/results.json post-run. (power_analysis.py:277-288+340-353, POWER-ANALYSIS.md:43-49.)
- Calibration bias table (fixed-10-bin ECE 0.156 @N=40 etc.): exact match to fresh run print + doc. (power_analysis.py:208-226+349-353, POWER-ANALYSIS.md:91-99.)
- RQ4 sign-test power (0.00 at n_seed≤4; 0.33/0.73 at 6; 0.61/0.92 at 8 for slopes 0.25/0.40): exact. (power_analysis.py:177-200+302-311+344-347, POWER-ANALYSIS.md:79-86.)
- First-order cluster bootstrap (per-family AUC as cluster obs, no within-family re-injection in bca_lower): power_analysis.py:97-121 (jackknife accel, quantile on boot), matches POWER-ANALYSIS.md:18+103-104 caveat + SPECIFICATION.md:9.1+190.
- Naive inflation demo (K=3/4/5 reduced n_sim=600): code runs and prints per-K values; doc table at POWER-ANALYSIS.md:69-73 does **not** match any row (see blocker).
- P0 scoping + design-vs-built qualifiers: SPECIFICATION.md:8 (full block), 100 (cross-lang "designed, not yet built — pilot is Python-only"), 120 ("not yet validated"), 190 ("first-order ... not yet implemented"), 255 (cross-lang stratum), 257 (pilot confirms blind spot) — all accurate against implemented code (no cross-lang, no MANIFEST corpus, residual only idents/msgs/consts, no make-validate/R-NODRIFT/hermetic). No claim violated the framing.
- Family census tally / ~8 both-class (with cross-lang) + evidence tiers / VERIFY flags: family-census.md:16-30 table + 39-44 tally — consistent with listed domains; explicitly draft/scouting, not frozen pre-reg input. No numeric overclaim.
- Legal → AFC mapping (no executable numbers): legal-framework.md entire; correctly informs §5.4 filter-then-residual without claiming implementation completeness.
- Predecessor external citations (C06e 0.947/0.000/0.003, WL 0.587): explicitly labeled "corroboration; `chardet-relicense/proof-bundle`" or "external ... not reproducible from any file in this repo" — not asserted against local code. (PILOT-RESULTS.md:31-41+26.)
- All revision-history numbers (13, 0.42-0.99, 0.33-0.5, 18-24/150-220, θ_AUC=0.85/θ_LB=0.65, ≥6-8 seeds, first-order bootstrap): trace to the verified pilot/power outputs or power-derived provisional language. (SPECIFICATION.md:11-17.)

**Blockers (concrete, code-grounded, with file:line + why).** Only items that are either (a) presented as factual results but unsupported by the generating code/output, or (b) internal inconsistency in a load-bearing doc. Design elements labeled as such are **not** blockers per the P0 framing at SPECIFICATION.md:8.

1. **POWER-ANALYSIS.md:69-73 (the "Naive pair-level bootstrap INFLATION" table and surrounding text).**  
   The markdown table claims specific powers (e.g. 0.82 row: family-clustered 0.66 / naive 0.71; header asserts "At the trustworthy K=5 (5v5, moderate het)") that do not match the actual output of the script that generates power/results.json and the console summary. Fresh run (`python3 power/power_analysis.py`) prints for the naive block (n_sim=600 per code:294):  
   ```
   0.82   3      0.49            0.37
   0.82   4      0.46            0.38
   0.82   5      0.44            0.46
   ...
   0.86   5      0.66            0.71
   0.90   5      0.83            0.93
   ```  
   (power_analysis.py:291-300 + 337-342 rendering from results). The 0.66/0.71 values appear (for 0.86 K=3 or K=5 in reduced sims), but the 0.82 row and K=5 framing do not. The accompanying claim "over-declares H1 by ~5–10 points" and "gap widens with more pairs/family" is directionally true in some higher-AUC cells but not supported by the table as written. This is a doc-vs-output gap (stale transcription or copy-paste from an earlier run/config). Not a primary H1 number, but still an unsupported numeric claim in the power document that feeds pre-registration.

**No other blockers found after full re-inspection + re-runs.** All other numerals, tables, caveats, P0-scoped design commitments, and cross-references (including the 15+ measures, residual filtration logic/false-positive demo, BHd spread wording, WL name-based artifact, calibration bias justification, RQ4 seed floor, family-clustered first-order bootstrap, census tally, legal-AFC alignment) are either exactly reproducible from the three commands or accurately qualified as pilot/provisional/draft/not-yet-built. No overclaim, no fabricated number, no methodological error in the implemented artifact, no doc-vs-code gap outside the single table above, and no violation of the P0 honest framing.

**Final determination: CONDITIONAL — one concrete blocker (the naive table).** Fix the table (re-run the naive block or correct the transcription to the actual printed values + K column), then this artifact would meet unconditional approval on the inspected evidence. The core pilot + power machinery and the SPEC's self-consistent P0 scoping are sound and fully verified.

*(End of report. This file is the persisted artifact for round 4.)*