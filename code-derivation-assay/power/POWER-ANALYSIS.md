# CDA Power Analysis (P0 pre-registration input)

**Artifact:** `power/power_analysis.py` (deterministic, seed=20260530) → `power/results.json`.
**Date:** 2026-05-30. **Status:** provisional — see the loud caveat in §0.
**Spec hooks:** `SPECIFICATION.md` §9.6 (power runs first), §11.1 (P0 freeze), §4 (H1 targets), §6.2 (floors).

---

## 0. What this is, and the caveat that governs everything below

This is a **simulation-based** power analysis run **before any harness or benchmark data exists**. It therefore uses **assumed** effect sizes, not measured ones. Its output is a **power map** — how power varies with the true effect and the design — plus a **provisional operating point** that is **conditional on a real pilot** landing in the assumed region. The pilot (a handful of real within-domain DERIVED/INDEPENDENT pairs run through a draft harness) is **still required before the P0 freeze**; this document tells the pilot what to look for and what the design must deliver once the true AUC is known.

Reproduce: `python3 power/power_analysis.py` (≈3.5 min, no network). Re-running regenerates `results.json` identically.

## 1. Model and the one decision that drives the result

- **Estimand (H1).** Macro-averaged **within-domain** AUC = mean over test families of the within-family DERIVED-vs-INDEPENDENT AUC (`SPECIFICATION.md` §4 RQ1, §9.1).
- **Inferential unit = family**, not pair (the reviewers' fix). Uncertainty is a **family-clustered BCa** bootstrap (resample families; jackknife-over-families acceleration). Per-family AUC is the cluster-level observation (a first-order cluster bootstrap — see limitations §6).
- **Generative model.** Binormal within family; per-family true AUC drawn around the mean on the logit-AUC scale with heterogeneity `tau` (`tau=0.35` moderate, `0.70` high). `n_pos`×`n_neg` pairs per family.
- Power = P(BCa 95% **lower** bound > `theta_LB`) over 2000 simulated test sets × 2000 bootstraps.

## 2. Headline result — H1 feasibility (θ_LB = 0.70, the spec's original value)

Power to achieve "lower CI bound > 0.70", **5 vs 5 pairs/family, moderate heterogeneity**, by true mean AUC × number of test families `K`:

| mean AUC | K=2† | K=3† | K=4 | K=5 | K=6 | K=8 |
|---|---|---|---|---|---|---|
| 0.78 | 0.50 | 0.35 | 0.28 | 0.29 | 0.30 | 0.31 |
| 0.82 | 0.63 | 0.50 | 0.45 | 0.47 | 0.49 | 0.50 |
| 0.86 | 0.75 | 0.65 | 0.65 | 0.67 | 0.70 | 0.75 |
| 0.90 | 0.87 | 0.82 | 0.81 | **0.85** | **0.89** | **0.93** |
| 0.94 | 0.96 | 0.94 | 0.94 | 0.95 | 0.98 | 0.99 |

**† K=2 and K=3 are NOT trustworthy** and must be ignored. Power *rises* as K falls to 2 — the opposite of how power behaves — because a cluster bootstrap with 2–3 clusters is **degenerate**: the leave-one-out jackknife and the cluster resample produce spuriously narrow / mis-located intervals (poor coverage), not genuine confidence. The median realized lower bound is anomalously high at K=2 (0.72 at AUC 0.78 vs ~0.65 at K≥4). **Lesson: ≥~5–6 well-behaved test families are required for the cluster bootstrap to have honest coverage at all; 2–4 test families (the likely yield of an ≥8-family benchmark with family-level splits) is in the unreliable zone.**

Reading only the trustworthy region (K≥5): to reach conventional **power ≥ 0.80 at θ_LB=0.70** you need **true mean AUC ≥ ~0.90 with K_test ≥ 5–6**, or **AUC ≥ 0.86 with K_test ≥ 8**. If the true within-domain AUC is ~0.82–0.85 — entirely plausible for this deliberately *hard*, boundary-relevant contrast — **H1 at θ_LB=0.70 is underpowered even at K=8.** This confirms the reviewers (claude B4, mistral): the original "CI lower bound > 0.70" target is likely infeasible at the benchmark floor.

High heterogeneity (`tau=0.70`) costs ~5–10 power points throughout; 3v3 pairs/family costs a similar amount vs 5v5.

## 3. θ_LB sensitivity — the cheapest lever

Same config (5v5, moderate het), power at relaxed lower-bound targets (K≥5 trustworthy region):

| | AUC 0.82 | AUC 0.86 | AUC 0.90 |
|---|---|---|---|
| **θ_LB = 0.60** | 0.77–0.90 | 0.88–0.96 | 0.96–0.99 |
| **θ_LB = 0.65** | 0.62–0.76 | 0.78–0.91 | 0.93–0.98 |
| **θ_LB = 0.70** | 0.47–0.50 | 0.67–0.75 | 0.85–0.93 |

Lowering θ_LB from 0.70 → 0.65 buys ~15–25 power points; → 0.60 makes even AUC≈0.82 adequately powered at K≥6. The decision-relevant question is **how high a lower bound the use case actually needs** — a 0.65 lower bound is still "clearly better than chance with margin," and is far more attainable.

## 4. Provisional operating point (FREEZE ONLY AFTER PILOT)

Given that the within-domain contrast is the *hard* one and a true AUC of 0.90 is optimistic, the defensible, falsifiable pre-registration is:

- **θ_AUC (point target) = 0.85; θ_LB = 0.65** (not 0.70).
- **K_test ≥ 6** well-behaved test families, each with **both** a within-domain DERIVED and INDEPENDENT pair; **≥ 5 vs 5** pairs/family.
- Powered at ≥0.80 if the pilot shows true mean AUC ≥ ~0.86–0.88. **If the pilot shows AUC ~0.82–0.85**, either accept **θ_LB = 0.60** or raise **K_test to 8–10**.
- Pre-declare the **under-powered fallback** (already in §9 item 6): if neither is achievable, report "instrument under-powered for the declared families" as the result.

### Consequence for the benchmark floors — the biggest planning takeaway
A family-level split needing **K_test ≥ 6** implies a **total family count far above the spec's ≥8 floor**. With a ~⅓ test fraction (train families also needed for LOFO-CV calibration), the realistic floor is **≈18–24 families total**, and the within-domain contrast specifically needs **≥6 test domains that each contain both a documented derivation edge and an independent same-spec implementation** — the hardest cells to source (claude B5/grok availability risk land exactly here). Pair count likewise: 6 test families × 10 pairs = 60 test pairs for the contrast alone, plus train, plus EVOLVED/UNRELATED control rows, plus ≥8 constructed seeds for RQ4 → **a realistic benchmark is ≈150–220 pairs, ~4–5× the "≥40" floor.** The ≥40/≥8 figures in `SPECIFICATION.md` are not merely floors to be "refined upward" — for the family-clustered design they are **substantially too small**, and the spec's R-BENCH / §6.2 / §9.6 numbers should be revised to the power-driven figures once the pilot fixes the AUC.

## 5. Secondary results

### 5.1 Naive pair-level bootstrap inflates power (why the family-clustering fix matters)
At the trustworthy K=5 (5v5, moderate het), comparing the correct family-clustered power to the pseudoreplicated pair-level bootstrap:

| mean AUC (at **K=5**) | family-clustered | naive pair-level |
|---|---|---|
| 0.86 | 0.66 | 0.71 |
| 0.90 | 0.83 | **0.93** |

(These are the **K=5 rows** of the `power_analysis.py` naive block; the full console also prints K=2,3,4,6,8 — read the K=5 line here. K≤4 is degenerate per §2.)

The naive bootstrap over-declares H1 by ~5–10 points, and the gap **widens with more pairs/family** (more pooled "independent" data → falsely narrow CI). This is the pseudoreplication error the design exists to avoid; it would have manufactured a passing H1 from a non-passing one. (At K≤3 the comparison is muddied by the degenerate small-cluster interval inflating the clustered side too — read this only at K≥5.)

### 5.2 RQ4 dose-response needs many seed families
Power for "Spearman ρ<0 at p<0.05", seed-family as the unit, 4 depth levels, via a sign test across seeds:

| n_seed | slope 0.25 | slope 0.40 |
|---|---|---|
| 3 | 0.00 | 0.00 |
| 4 | 0.00 | 0.00 |
| 6 | 0.33 | 0.73 |
| 8 | 0.61 | 0.92 |

The **0.00 at ≤4 seeds is structural**: a one-sided sign test on ≤4 seeds cannot reach p<0.05 even if every seed agrees (binomial floor). RQ4 therefore needs **≥6–8 constructed seed families**, *or* a more powerful aggregation (seed-clustered pooled-ρ bootstrap rather than a sign test) — a method choice to fix at P0. Either way, RQ4 cannot ride on 3–4 seeds.

### 5.3 Calibration (RQ3) is the most sample-hungry; fixed-bin ECE is biased
SD of Brier and **fixed-10-bin ECE on perfectly-calibrated data** vs test size N:

| N | Brier SD | ECE mean (fixed-10) | ECE SD |
|---|---|---|---|
| 20 | 0.044 | 0.208 | 0.051 |
| 40 | 0.031 | **0.156** | 0.037 |
| 80 | 0.022 | 0.111 | 0.027 |
| 160 | 0.016 | 0.079 | 0.019 |
| 320 | 0.011 | 0.056 | 0.013 |

Fixed-bin ECE carries a large **positive bias from binning noise alone** — 0.156 at N=40 for *perfect* calibration — so any fixed-bin ECE threshold below ~0.15 is unmeetable at realistic test sizes regardless of true calibration. This concretely justifies the §9.2 **binning-robust / binless** mandate and N-aware bounds. Brier is better behaved; with a few dozen test pairs, **report calibration descriptively (binless estimator, wide intervals)** rather than as a tight confirmatory bound.

## 6. Limitations of this analysis (read before trusting any number)

1. **Assumed effect sizes** — no pilot data. The whole map is conditional; the pilot must locate the true AUC before the freeze.
2. **First-order cluster bootstrap**: per-family AUC treated as the cluster observation; within-family sampling noise is not re-injected inside the bootstrap (captured across simulated datasets but not in each CI). This is mildly **anti-conservative** on CI width → a faithful two-stage bootstrap would need **equal-or-more** families, never fewer. So the §4 recommendation (K_test ≥ 6) is a floor, not a ceiling.
3. **Small-K unreliability** (K≤3) is visible as the K=2 anomaly and is excluded from all recommendations.
4. **Model simplification**: binormal scores, logit-normal family heterogeneity, macro-averaged estimand. If the frozen estimand is pooled (not macro-averaged), or score distributions are skewed, numbers shift.
5. The naive-inflation comparison used a smaller inner bootstrap (500) and fewer sims (600) for runtime; treat it as directional.

## 7. What the pilot must produce before P0 freeze

1. A **draft ST/PB/BH harness** run on **≥2 real within-domain DERIVED/INDEPENDENT family pairs** → a first estimate of the true within-domain AUC and the between-family heterogeneity `tau`. This locates the operating column in §2/§3. **DONE (first pass):** the full ST/PB/BH harness ran on the chardet trio — **one** family (`pilot/PILOT-RESULTS.md`) — and found the *AI-rewrite-vs-independent* contrast at **AUC ≈ 0.33–0.5 (near/below chance)**; the **static** measures were then extended to **three** families (`pilot/multi_family_pilot.py`, `pilot/MULTI-FAMILY-RESULTS.md`), confirming the finding generalizes (the human GPL→MIT reimplementation RapidFuzz is equally indistinguishable; a vendored copy is clearly detected). The full BH harness remains single-family. The operating column is the pessimistic one unless signals are materially improved. This is the single most important input the freeze now has: either improve ST/PB/BH and re-pilot, or pre-declare H1 likely-falsified for AI rewrites (a valid §4 outcome).
2. A **family-availability census**: can ≥18–24 qualifying families (≥6 test) actually be sourced under the public/permissive-or-metadata-only constraint, with the within-domain both-classes requirement? If not, the confirmatory design must shrink its claim (fewer test families → wider CIs → lower θ_LB or descriptive-only) — decided *before* freezing, in the open.
3. The **frozen** (θ_AUC, θ_LB, K_test, pairs/family, RQ4 seed count, calibration estimator + bounds), chosen from this map given the pilot AUC, recorded in `PREREGISTRATION.md` and git-tagged.
