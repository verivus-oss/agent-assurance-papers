#!/usr/bin/env python3
"""
CDA power analysis (pre-registration input for P0; SPECIFICATION.md §9.6, §11.1).

WHAT THIS IS / IS NOT
---------------------
This is a *simulation-based* power analysis run BEFORE any harness or benchmark
data exists. It therefore uses ASSUMED effect sizes, not measured ones. Its
output is a power MAP: how many held-out test families (and pairs-per-family)
are needed for the confirmatory H1 ("within-domain DERIVED-vs-INDEPENDENT AUC
lower CI bound > theta_LB") as a function of the true mean AUC and the
between-family heterogeneity. The recommended operating point is CONDITIONAL on
a real pilot landing in the assumed cell; the pilot is still required before the
P0 freeze. See POWER-ANALYSIS.md for interpretation and caveats.

KEY DESIGN DECISION (the reviewers' fix, SPECIFICATION.md §9.1):
the inferential unit is the FAMILY, not the pair. The primary estimand is the
macro-averaged within-family AUC; uncertainty is a family-level (cluster) BCa
bootstrap. We also compute the NAIVE pair-level bootstrap to quantify how badly
it inflates power (pseudoreplication), which is exactly the error this design
exists to avoid.

Deterministic: single seeded numpy Generator; no network; no Date/random outside
the seeded RNG. Re-running reproduces results.json byte-for-byte.
"""

from __future__ import annotations
import json
import math
import numpy as np
from scipy.stats import norm

SEED = 20260530
N_SIM = 2000          # simulated test sets per cell
N_BOOT = 2000         # bootstrap resamples per simulated test set
CI_ALPHA = 0.05       # 95% CI -> one-sided lower bound at 2.5%? H1 uses the
                      # BCa 95% interval's LOWER bound, i.e. the 2.5% percentile.
LB_PCT = 2.5          # lower bound percentile for a two-sided 95% CI


# ----------------------------------------------------------------------------
# AUC machinery (binormal model)
# ----------------------------------------------------------------------------
def auc_to_mu(auc: float) -> float:
    """Binormal: positives ~ N(mu,1), negatives ~ N(0,1) => AUC = Phi(mu/sqrt2)."""
    return math.sqrt(2.0) * norm.ppf(auc)


def empirical_auc(pos: np.ndarray, neg: np.ndarray) -> float:
    """Mann-Whitney AUC = P(pos > neg) with 0.5 for ties."""
    # rank-based, O(n log n)
    n_pos, n_neg = len(pos), len(neg)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    allv = np.concatenate([pos, neg])
    order = allv.argsort(kind="mergesort")
    ranks = np.empty(len(allv), dtype=float)
    ranks[order] = np.arange(1, len(allv) + 1)
    # average ranks for ties
    # (cheap tie handling: values are continuous floats, ties ~ impossible)
    r_pos = ranks[:n_pos].sum()
    return (r_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


# ----------------------------------------------------------------------------
# One simulated test set: K families, each with a per-family AUC drawn around
# the true mean with heterogeneity tau (on the logit-AUC scale).
# ----------------------------------------------------------------------------
def simulate_test_set(rng, K, n_pos, n_neg, mean_auc, tau):
    """Return (per_family_auc[K], pos_scores list, neg_scores list)."""
    logit_mean = math.log(mean_auc / (1 - mean_auc))
    z = rng.standard_normal(K)
    fam_auc_true = 1.0 / (1.0 + np.exp(-(logit_mean + tau * z)))
    fam_auc_true = np.clip(fam_auc_true, 0.50, 0.999)
    per_family_auc = np.empty(K)
    pos_all, neg_all, fam_id = [], [], []
    for f in range(K):
        mu = auc_to_mu(float(fam_auc_true[f]))
        pos = rng.standard_normal(n_pos) + mu
        neg = rng.standard_normal(n_neg)
        per_family_auc[f] = empirical_auc(pos, neg)
        pos_all.append(pos)
        neg_all.append(neg)
        fam_id.append(f)
    return per_family_auc, pos_all, neg_all


# ----------------------------------------------------------------------------
# Family-clustered BCa lower bound on the macro-averaged AUC.
# Statistic theta = mean over families of within-family AUC.
# Cluster bootstrap: resample families (with replacement); BCa correction uses a
# leave-one-family-out jackknife for acceleration. This treats the per-family
# AUC point estimate as the cluster-level observation (a first-order cluster
# bootstrap); within-family sampling noise is captured across simulated test
# sets but not re-injected inside the bootstrap (documented caveat).
# ----------------------------------------------------------------------------
def bca_lower(rng, fam_auc, n_boot, lb_pct):
    K = len(fam_auc)
    theta_hat = fam_auc.mean()
    # bootstrap distribution
    idx = rng.integers(0, K, size=(n_boot, K))
    boot = fam_auc[idx].mean(axis=1)
    # bias correction z0
    prop_less = np.mean(boot < theta_hat)
    prop_less = min(max(prop_less, 1.0 / (2 * n_boot)), 1 - 1.0 / (2 * n_boot))
    z0 = norm.ppf(prop_less)
    # acceleration via jackknife over families
    jack = np.array([np.delete(fam_auc, i).mean() for i in range(K)])
    jbar = jack.mean()
    num = ((jbar - jack) ** 3).sum()
    den = 6.0 * (((jbar - jack) ** 2).sum() ** 1.5)
    a = num / den if den != 0 else 0.0
    # adjusted lower percentile
    zl = norm.ppf(lb_pct / 100.0)
    denom = 1 - a * (z0 + zl)
    if denom == 0:
        adj = lb_pct / 100.0
    else:
        adj = norm.cdf(z0 + (z0 + zl) / denom)
    adj = min(max(adj, 0.0), 1.0)
    return float(np.quantile(boot, adj)), float(theta_hat)


def naive_pair_lower(rng, pos_all, neg_all, n_boot, lb_pct):
    """Pseudoreplicated pair-level percentile bootstrap (the WRONG unit).
    Pool all pairs, resample positives and negatives independently."""
    pos = np.concatenate(pos_all)
    neg = np.concatenate(neg_all)
    np_, nn_ = len(pos), len(neg)
    boot = np.empty(n_boot)
    for b in range(n_boot):
        p = pos[rng.integers(0, np_, np_)]
        n = neg[rng.integers(0, nn_, nn_)]
        boot[b] = empirical_auc(p, n)
    return float(np.quantile(boot, lb_pct / 100.0))


# ----------------------------------------------------------------------------
# Power for one cell.
# ----------------------------------------------------------------------------
def power_cell(rng, K, n_pos, n_neg, mean_auc, tau, theta_lb,
               n_sim=N_SIM, n_boot=N_BOOT, lb_pct=LB_PCT, with_naive=False):
    hits = 0
    naive_hits = 0
    lbs = np.empty(n_sim)
    for s in range(n_sim):
        fam_auc, pos_all, neg_all = simulate_test_set(
            rng, K, n_pos, n_neg, mean_auc, tau)
        lb, _ = bca_lower(rng, fam_auc, n_boot, lb_pct)
        lbs[s] = lb
        if lb > theta_lb:
            hits += 1
        if with_naive:
            nlb = naive_pair_lower(rng, pos_all, neg_all,
                                   n_boot=500, lb_pct=lb_pct)
            if nlb > theta_lb:
                naive_hits += 1
    out = {
        "power": hits / n_sim,
        "lb_median": float(np.median(lbs)),
        "lb_p10": float(np.quantile(lbs, 0.10)),
    }
    if with_naive:
        out["naive_power"] = naive_hits / n_sim
    return out


# ----------------------------------------------------------------------------
# RQ4 dose-response: Spearman rho between depth and score, seed-family as unit.
# Score at depth d (0=paraphrase shallow .. D-1=re-architected deep) declines
# with a slope; per-seed noise. Confirmatory direction: rho < 0.
# We test power for "rho < 0 at p<0.05" using seed as the unit (one rho per
# seed averaged? -> better: a per-seed Spearman, then sign test / aggregate).
# Operationalization: compute one Spearman per seed across its depth points;
# require the median across seeds to be < 0 AND a sign test across seeds sig.
# ----------------------------------------------------------------------------
def rq4_power(rng, n_seed, depths, slope, noise, reps_per_cell=1,
              n_sim=1000):
    from scipy.stats import spearmanr, binomtest
    D = len(depths)
    sig = 0
    for s in range(n_sim):
        per_seed_rho = np.empty(n_seed)
        for i in range(n_seed):
            seed_off = rng.standard_normal() * 0.5
            x, y = [], []
            for d_idx, d in enumerate(depths):
                for _ in range(reps_per_cell):
                    score = 1.0 - slope * d_idx + seed_off + \
                        rng.standard_normal() * noise
                    x.append(d_idx)
                    y.append(score)
            rho, _ = spearmanr(x, y)
            per_seed_rho[i] = rho
        # sign test across seeds: how many seeds show rho<0
        n_neg = int((per_seed_rho < 0).sum())
        bt = binomtest(n_neg, n_seed, 0.5, alternative="greater")
        if bt.pvalue < 0.05 and np.median(per_seed_rho) < 0:
            sig += 1
    return sig / n_sim


# ----------------------------------------------------------------------------
# Calibration sample-size note: SE of Brier and of fixed-bin ECE vs N.
# Demonstrates fixed-bin ECE is noise-dominated at small N -> motivates the
# binning-robust estimator already mandated in §9.2.
# ----------------------------------------------------------------------------
def calibration_se(rng, N, n_bins=10, n_rep=3000, true_auc=0.85):
    """Well-calibrated scores: p ~ U(0,1) prob of positive; label ~ Bern(p).
    Report SD of Brier and of fixed-bin ECE across replicates."""
    briers, eces = np.empty(n_rep), np.empty(n_rep)
    for r in range(n_rep):
        p = rng.uniform(0, 1, N)
        y = (rng.uniform(0, 1, N) < p).astype(float)
        briers[r] = np.mean((p - y) ** 2)
        # fixed-bin ECE
        bins = np.linspace(0, 1, n_bins + 1)
        idx = np.clip(np.digitize(p, bins) - 1, 0, n_bins - 1)
        ece = 0.0
        for b in range(n_bins):
            m = idx == b
            if m.any():
                ece += (m.mean()) * abs(p[m].mean() - y[m].mean())
        eces[r] = ece
    return {"N": N, "brier_sd": float(briers.std()),
            "ece_mean": float(eces.mean()), "ece_sd": float(eces.std())}


# ----------------------------------------------------------------------------
# Main sweep.
# ----------------------------------------------------------------------------
def main():
    rng = np.random.default_rng(SEED)
    results = {
        "meta": {
            "seed": SEED, "n_sim": N_SIM, "n_boot": N_BOOT,
            "lb_pct": LB_PCT,
            "model": "binormal within-family AUC; family = inferential unit; "
                     "between-family heterogeneity tau on logit-AUC scale; "
                     "family-clustered BCa lower bound (jackknife accel).",
            "caveat": "ASSUMED effect sizes (no pilot data yet). Output is a "
                      "power map; operating point conditional on pilot.",
        },
        "h1_auc_power": [],
        "naive_inflation": [],
        "rq4_spearman_power": [],
        "calibration_se": [],
    }

    # ---- Primary H1 power sweep ----
    Ks = [2, 3, 4, 5, 6, 8]
    mean_aucs = [0.78, 0.82, 0.86, 0.90, 0.94]
    taus = {"moderate_het": 0.35, "high_het": 0.70}
    pairs = {"3v3": (3, 3), "5v5": (5, 5)}
    theta_lbs = [0.60, 0.65, 0.70]

    for tau_name, tau in taus.items():
        for pair_name, (np_, nn_) in pairs.items():
            for A in mean_aucs:
                for K in Ks:
                    cell = power_cell(rng, K, np_, nn_, A, tau,
                                      theta_lb=0.70)
                    # also record power at the other theta_LBs cheaply by
                    # re-thresholding the same lbs is not stored; recompute
                    # only for the headline theta_LB=0.70 here, and a focused
                    # theta_LB sweep below.
                    results["h1_auc_power"].append({
                        "tau": tau_name, "pairs": pair_name,
                        "mean_auc": A, "K_test_families": K,
                        "theta_LB": 0.70,
                        "power": cell["power"],
                        "lb_median": cell["lb_median"],
                        "lb_p10": cell["lb_p10"],
                    })

    # ---- theta_LB sensitivity at a representative config ----
    for A in mean_aucs:
        for K in Ks:
            for tlb in theta_lbs:
                cell = power_cell(rng, K, 5, 5, A, 0.35, theta_lb=tlb)
                results["h1_auc_power"].append({
                    "tau": "moderate_het", "pairs": "5v5",
                    "mean_auc": A, "K_test_families": K,
                    "theta_LB": tlb,
                    "power": cell["power"],
                    "lb_median": cell["lb_median"],
                    "lb_p10": cell["lb_p10"],
                })

    # ---- Naive pair-level inflation demonstration ----
    for A in [0.82, 0.86, 0.90]:
        for K in [3, 4, 5]:
            cell = power_cell(rng, K, 5, 5, A, 0.35, theta_lb=0.70,
                              n_sim=600, with_naive=True)
            results["naive_inflation"].append({
                "mean_auc": A, "K_test_families": K, "pairs": "5v5",
                "theta_LB": 0.70,
                "family_clustered_power": cell["power"],
                "naive_pair_level_power": cell["naive_power"],
            })

    # ---- RQ4 Spearman power ----
    for n_seed in [3, 4, 6, 8]:
        for slope in [0.25, 0.40]:
            p = rq4_power(rng, n_seed, depths=[0, 1, 2, 3],
                          slope=slope, noise=0.5, reps_per_cell=1)
            results["rq4_spearman_power"].append({
                "n_seed_families": n_seed, "depth_levels": 4,
                "slope_per_level": slope, "noise_sd": 0.5,
                "power": p,
            })

    # ---- Calibration SE vs N ----
    for N in [20, 40, 80, 160, 320]:
        results["calibration_se"].append(calibration_se(rng, N))

    with open("power/results.json", "w") as f:
        json.dump(results, f, indent=2)

    # ---- console summary ----
    print("=== H1 AUC power (theta_LB=0.70), family-clustered BCa lower bound ===")
    print("Power to achieve CI-lower-bound > 0.70, by true mean AUC x #test families")
    for tau_name in taus:
        for pair_name in pairs:
            print(f"\n-- {tau_name}, pairs={pair_name} --")
            print("  meanAUC | " + " ".join(f"K={k:<2}" for k in Ks))
            for A in mean_aucs:
                row = []
                for K in Ks:
                    hit = next(r for r in results["h1_auc_power"]
                               if r["tau"] == tau_name and r["pairs"] == pair_name
                               and r["mean_auc"] == A and r["K_test_families"] == K
                               and r["theta_LB"] == 0.70)
                    row.append(f"{hit['power']:.2f}")
                print(f"   {A:.2f}   | " + "  ".join(f"{v:>4}" for v in row))

    print("\n=== Naive pair-level bootstrap INFLATION (theta_LB=0.70, 5v5, tau=0.35) ===")
    print("  meanAUC  K  family-clustered  naive-pair-level")
    for r in results["naive_inflation"]:
        print(f"   {r['mean_auc']:.2f}   {r['K_test_families']}      "
              f"{r['family_clustered_power']:.2f}            "
              f"{r['naive_pair_level_power']:.2f}")

    print("\n=== RQ4 Spearman (depth vs score) power, seed-family as unit ===")
    print("  n_seed  slope  power")
    for r in results["rq4_spearman_power"]:
        print(f"    {r['n_seed_families']}     {r['slope_per_level']:.2f}   {r['power']:.2f}")

    print("\n=== Calibration estimator SE vs N (well-calibrated truth) ===")
    print("   N    Brier_SD   ECE_mean(fixed10)  ECE_SD")
    for r in results["calibration_se"]:
        print(f"  {r['N']:>3}    {r['brier_sd']:.3f}      "
              f"{r['ece_mean']:.3f}            {r['ece_sd']:.3f}")

    print("\nWrote power/results.json")


if __name__ == "__main__":
    main()
