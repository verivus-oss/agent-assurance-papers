# Round-4 verification → corrections log

Round 4 was a FULL unscoped re-review; it surfaced stale claims left over from early iterations that the focused rounds 2–3 didn't re-examine. Six are valid (fixed); one (grok #1) is a misread (rebutted with evidence + the doc clarified anyway).

## Fixed (conceded, code-grounded)
1. **PILOT-RESULTS.md:50 — "AUCs 0.11–0.67 / near chance across entire ensemble"** (codex #1). Stale: actual per-measure AUC spans 0.11–1.00. Fixed → "no measure *robustly* separates; per-measure AUC spans 0.11–1.00 but the high values are artifacts (WL vocabulary, PQmsg generic-phrase)."
2. **PILOT-RESULTS.md:51 — "chardet v7 has none [carryover]"** (codex #2). Stale: residual is 13. Fixed → "small but non-zero (residual 13 raw…)."
3. **PILOT-RESULTS.md:77 — `encoding_era`/`MINIMUM_THRESHOLD` mislabeled** (gemini #1). `python3 pilot/residual.py` shows `encoding_era` IS in the 13-residual and `MINIMUM_THRESHOLD` is NOT. Fixed → swapped: API-removed list now has `MINIMUM_THRESHOLD`; residual list now has `encoding_era`, `lang_filter` (+ stdlib false positives `ascii_letters`, `max_bytes`).
4. **legal-framework.md:39,47 — "quirks ≈0 / PB≈0 / likely not a derivative work"** (codex #3). Stale (residual 13, not ≈0) and stronger than the no-verdict posture. Fixed → "small but non-zero… genuinely contestable — CDA renders no verdict (§14)."
5. **SPECIFICATION.md §19 (:354) — "chardet pair expected to read ST≈0 / PB-elevated"** (codex #4). Actual: ST envelope [0.42–0.99] (not ≈0), PBt=0, small residual. Fixed → "matcher-dependent ST [0.42–0.99], PB literal ~0, small non-zero residual — indistinguishable from independent on aggregate measures."
6. **POWER-ANALYSIS.md:111 — "≥2-family ST/BH/PB pilot DONE" on chardet only** (codex #5). Fixed → "full ST/PB/BH on **one** family (chardet); STATIC measures extended to **three** families (`multi_family_pilot.py`, `MULTI-FAMILY-RESULTS.md`); full BH still single-family." (The new multi-family work also *resolves* the substance — the finding generalizes.)

## Disputed with evidence (NOT a defect) — grok round-4 blocker #1
**Claim:** the POWER-ANALYSIS.md §5.1 naive-inflation table values don't match the script, citing a "0.82 row: 0.66/0.71."
**Evidence against:** the doc table has **no 0.82 row** — it has the **0.86** and **0.90** rows, both at **K=5**, and they match the actual `power_analysis.py` naive output exactly:
```
0.86   5      0.66            0.71      ← doc: | 0.86 | 0.66 | 0.71 |
0.90   5      0.83            0.93      ← doc: | 0.90 | 0.83 | 0.93 |
```
grok mis-attributed the console's separate `0.82  5  0.44  0.46` row to the doc table. The doc table is correct. **However**, because the table lacked an explicit K column (the cause of the misread), I added "(at **K=5**)" to the header and a clarifying note. Defended with output evidence, and the ambiguity removed.

## Round-3 items
Items 2–6 of round 2 were verified resolved in round 3 (unconditional on those); the round-4 finds are *additional* stale claims from earlier iterations, now also fixed.
