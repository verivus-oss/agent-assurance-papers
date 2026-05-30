# Multi-family pilot — is the chardet finding chardet-specific?

**Harness:** `pilot/multi_family_pilot.py` (reuses the audited `pilot_harness` / `structural` / `residual` modules; static measures only — BH needs per-family adapters). Deterministic, offline.
**Question:** the single-family pilot found that *no measure separates the chardet AI rewrite (v6→v7) from independent reimplementation*. Is that **chardet-specific**, or general? Tested on **three families**, each with a real DERIVED edge + independent same-spec implementations.
**Filtration:** §5.4 residual uses a **leave-pair-out** baseline (the independent pool minus the two pair members), so independent pairs are not trivially zeroed and the false-positive behaviour is honest.

## Cross-family result (the answer)

| family | derivation edge | type | ST envelope | PQidist (indep band) | resApi (indep band) | distinguishable from independent? |
|---|---|---|---|---|---|---|
| encoding | chardet v6→v7 | **AI rewrite** | [0.42, 0.99] | 0.020 (0.013–0.020) | 13 (11–16) | **NO** |
| fuzzy | fuzzywuzzy→RapidFuzz | **human GPL→MIT reimpl** | [0.70, 0.99] | 0.046 (0.000–0.072) | 2 (0–12) | **NO** |
| fuzzy | fuzzywuzzy→thefuzz | **fork** | [0.45, 0.99] | 0.198 (>0.072) | 7 | **yes** (PQidist, PQdoc 0.77) |
| toml | tomli→tomllib | **vendored copy** | [0.76, 1.00] | **0.906** (0.013–0.026) | **68** (0–1) | **YES, strongly** |

## Findings

1. **NOT chardet-specific.** The *human* RapidFuzz reimplementation behaves exactly like the chardet *AI* rewrite: PQidist (0.046) inside the independent band, residual (2) inside the independent band, a wide ST envelope. Across **both** families, a **clean reimplementation — AI or human — is indistinguishable from independent** by these measures. The phenomenon is a property of *clean reimplementation*, not of chardet and not of AI.

2. **The measures are NOT blind — copying IS detected.** The vendored `tomli→tomllib` pair (tomllib is literally tomli vendored into CPython) is unmistakable: PQidist **0.906** vs an independent band of 0.013–0.026, residual **68** vs 0–1, every AUC = 1.000. This is the **positive control**: the failure to detect chardet v7 / RapidFuzz is *not* a measurement failure — it is that a clean reimplementation **retains little arbitrary expression to detect**.

3. **The discriminating variable is the TYPE of derivation, on a gradient:**
   - **vendored / copied** (tomli→tomllib): PQidist 0.91, residual 68 → strongly detected;
   - **fork** (fuzzywuzzy→thefuzz): PQidist 0.198 (> band), PQdoc 0.77, residual 7 → detected;
   - **clean reimplementation** (chardet v7 AI; RapidFuzz human): PQidist/residual inside the independent band → **undetectable**.

4. **This is exactly what the legal AFC framework predicts** (`legal-framework.md`). Clean reimplementation retains little *protectable expression* (so it is both undetectable here and, under Sega/Sony/Altai, the *clean-reimplementation* region those cases generally treat as fair-use reimplementation); vendoring/forking retains arbitrary expression (detectable here — though in practice it may be fully licensed). **CDA measures retention and renders no verdict.** The instrument's "blind spot" coincides with the legal "fair-use reimplementation" region — a measurement observation, not a legal conclusion.

5. **§5.4 baseline requirement re-confirmed.** With leave-pair-out, the *thin-baseline* families false-positive: the encoding independents score residual 11–16 (only 1 independent → near-empty leave-pair-out baseline) and fuzzy's jellyfish↔textdistance scores 12 (Jaro-canonical vars + builtins). The clean-baseline toml family (3 independents) gives independent residuals of 0–1 and detects the vendored pair perfectly. So the residual measure needs a **large independent baseline + builtin/stdlib/algorithm-canonical filtering** to be trustworthy — consistent with the single-family finding.

## Caveats
Static measures only (no BH). n is tiny per family (3–5 pairs). The encoding family has only 1 independent (thin baseline); fuzzy and toml have 3. `rapidfuzz` is a C++/Cython core with a Python API layer, so its static features are the API layer (the relevant surface for arbitrary-expression comparison). The headline finding — *clean reimplementation indistinguishable, vendoring/forking detected, across families* — rests on PQidist + ST envelope, which do not depend on the residual baseline; the residual column is shown with its leave-pair-out false-positive behaviour exposed.

## Bottom line
The chardet result generalizes: **structural/behavioral/provenance retention cannot distinguish a clean reimplementation (AI or human) from an independent implementation — but it reliably detects vendoring and forking.** Derivation detection is therefore feasible for *copying* (vendoring/forking) and infeasible for *clean reimplementation* — which mirrors the copying-vs-reimplementation distinction the law is concerned with. (CDA renders no verdict; §14.)
