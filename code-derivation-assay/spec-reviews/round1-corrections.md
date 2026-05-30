# Round-1 verification → corrections log

Every round-1 blocker (codex/gemini/grok) was code-grounded and **accepted without dispute**. Fixes below; verify each against the cited file:line in the updated files. No finding was argued away.

## Substantive numeric / claim corrections
1. **Residual "~8" → "13"** (codex #5, grok #1). The script `pilot/residual.py` prints 13 idents after API filter for chardet v6→v7. Fixed: `SPECIFICATION.md` §5.4 ("**13** identifiers survive API filtering … ~5 are stdlib/parameter false positives"), the v0.8 revision-history line, and `pilot/PILOT-RESULTS.md` iter-6 + iter-7 ("**13 raw identifiers** … ~5 stdlib/param false positives").

2. **WL "faithful contradiction" / "renaming-invariant" overclaim** (codex #2, gemini #1, grok #3). Confirmed `pilot/structural.py:39` `defined.add(n.name)` → name-based node identity → not renaming-invariant; AUC 1.0 is a shared-vocabulary artifact; predecessor 0.587/0.872 are external, not reproducible in-repo. Fixed: `SPECIFICATION.md` §5.2 (pilot caveat: type-based measures invariant, call-graph topology/WL name-based and confounded; §7.3 invariance test not yet implemented) and §5.4 ("apparent exception … shared-identifier-vocabulary artifact … not a defensible structural signal"); `PILOT-RESULTS.md` envelope section (WL is *not* a faithful equivalent; matcher fragility, not two faithful kernels; predecessor numbers external).

3. **"AI rewrite below independent" (BHd) cherry-pick** (gemini #3). Confirmed `pilot/results.json`: v7-csn BHd=0.072 < AI-rewrite 0.135. Fixed: `PILOT-RESULTS.md` ("sits within the independent spread (v7-csn 0.072 … v6-csn 0.430) — below two of three independents but above v7-csn, at the independent baseline, not cleanly below"). Spec "sits at the independent baseline" → "within the independent spread / no measure *robustly* separates."

4. **§5.4 jellyfish↔textdistance control used 1-lib baseline, not 3** (grok #2). Confirmed `pilot/residual.py:170` passes `[fz['levenshtein']]`. Fixed: `PILOT-RESULTS.md` iter-7 ("1-lib baseline `[Levenshtein]` … thinner than the 3-lib pool").

5. **§9.1 "resample families, then pairs within" vs implemented first-order cluster bootstrap** (codex #3). Fixed: `SPECIFICATION.md` §9.1 now says "first-order cluster bootstrap … within-family resampling is a documented refinement **not yet implemented**, `power/POWER-ANALYSIS.md` §6."

## Design-vs-code scoping (the bulk: codex #4,#7,#8,#9; gemini #2; grok #4,#5)
These flagged that the spec *reads as built* while only a P0 pilot exists (cross-language, MANIFEST/copyleft redistribution, make-validate/no-drift/hermetic/figures, full §5.4 with CI/improbability). All **true**: those are designed, not built. Fixed by a standing **Implementation status (P0)** block at the top of `SPECIFICATION.md` that enumerates exactly what is built vs designed-only, states the spec is "normative for the future build, not a description of shipped software," and names the verification reviews. Per-claim markers added inline (e.g. §5.2 cross-language "*designed, not yet built — the pilot is Python-only*").

## Not disputed
No round-1 finding was contested. The pilot/power mechanics the reviewers verified as correct (family-clustered BCa, reproducible numbers, AFC filtration logic, no fabrication) are retained as-is.
