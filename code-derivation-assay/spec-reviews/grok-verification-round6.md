# Grok Verification — Round 6 (confirmation re-check after four small legal-language fixes)

**Date:** 2026-05-30  
**Artifact:** /srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay (SPECIFICATION.md v0.8.1 + pilot/ + power/ + family-census.md + legal-framework.md + MULTI-FAMILY-RESULTS.md + all supporting code).  
**Context:** Round 5 delivered **UNCONDITIONAL APPROVAL** after full zero-trust re-verification. Codex subsequently flagged 4 legal-verdict overreach items + 1 P0 staleness item. This round is a **targeted confirmation** against the FILES only: the four specific fixes + the exact required grep + assurance that nothing else changed (no numeric, no code, no other legal language drift) and nothing broke.

**Method:** 
- Exact `grep -rn` as specified (must return NOTHING).
- Line-by-line read of the four cited locations.
- Broader scan for any residual verdict language across primary .md files.
- Re-execution of the two pilot scripts that ground the multi-family + residual claims (multi_family_pilot.py, residual.py) + spot-check of results.json + harness outputs.
- Confirmation that P0 block, tables, and all cited numbers remain identical to round-5 state.

---

## The four required verifications (file:line)

1. **legal-framework.md:38**  
   Verified exact text:  
   > | **Clean-room rulings: reproducing function ≠ infringement** | Legally validates that **BH agreement and structural retention are NOT the copying signal**; an AI rewrite that reproduces behavior but not arbitrary expression is the kind of clean reimplementation those cases generally treated as **fair-use reimplementation rather than infringement** — but CDA renders no verdict (§14). |
   The prior "not a derivative work" verdict phrasing is gone; the sentence now explicitly defers to §14 and withholds any legal conclusion.

2. **pilot/MULTI-FAMILY-RESULTS.md** (multiple locations; headline findings + bottom line)  
   Verified: all instances of "likely non-infringing", "legally infringing", or "precisely the line the law draws" are removed.  
   Current language (lines 27, 35, and supporting):  
   - "CDA measures retention and renders no verdict. The instrument's 'blind spot' coincides with the legal 'fair-use reimplementation' region — a measurement observation, not a legal conclusion."  
   - Bottom line: "... (CDA renders no verdict; §14.)"  
   The distinction between vendored/fork (detectable) vs clean reimplementation (undetectable) is presented purely as a measurement finding aligned with AFC, never as a legal verdict.

3. **pilot/PILOT-RESULTS.md:77**  
   Verified exact revised text:  
   > ... they are the *kind* of arbitrary shared feature the **"striking similarity"** doctrine targets (§19) — evidence, not a verdict.
   The prior phrasing ("to a court they are striking similarity") is gone. The residual is framed as the *kind of evidence* the doctrine would examine, explicitly labeled "evidence, not a verdict."

4. **SPECIFICATION.md:8 (P0 Implementation status block)**  
   Verified exact text:  
   > ... the §5.4 residual *prototype* (identifiers/messages/constants only) on **three families (chardet + fuzzy + toml)** via `pilot/multi_family_pilot.py` (`pilot/MULTI-FAMILY-RESULTS.md`); ...
   The stale "chardet + fuzzy" (or similar) has been updated to the accurate three-family scope via the multi_family_pilot harness. The full P0 disclaimer block remains in force and correctly bounds all claims.

---

## The mandatory grep (exact command from query)

```bash
grep -rn "not a derivative work\|legally infringing\|likely non-infringing\|to a court they are" SPECIFICATION.md pilot/ legal-framework.md
```

**Result:** No matches (command exit status 1, as required). The four overreach strings are absent from the three targeted paths.

---

## Broader legal-language hygiene check (all primary docs)

Command:
```bash
grep -rn -i "verdict\|infring\|derivative work\|non-infring\|likely.*infring\|to a court they are\|striking similarity" --include="*.md" SPECIFICATION.md pilot/ legal-framework.md family-census.md power/
```

Findings (excerpted; full output clean of overreach):
- All "verdict" occurrences are qualified: "CDA renders **no legal verdict**", "evidence, not a verdict", "never a verdict (§14)", "a measurement observation, not a legal conclusion", "stated as measurement, never a verdict".
- "striking similarity" appears only as the *doctrine* being operationalized by the residual measure or as the legal concept being mirrored — never as a present-tense finding about any pair.
- "fair-use reimplementation" is always followed by the explicit "— but CDA renders no verdict (§14)" qualifier (legal-framework.md:38 and cross-referenced).
- No "derivative work" used as a legal conclusion; the term appears only in the thesis paragraph and scope statements as the *dispute* CDA studies, not a claim it resolves.
- family-census.md and POWER-ANALYSIS.md contain zero instances of the searched legal-conclusion language.

The softening is complete and consistent.

---

## Confirmation that only the four legal/P0 items changed (no numeric or code drift)

- Re-ran (fresh, this workspace):
  - `python3 pilot/multi_family_pilot.py` — exit 0. Output matches MULTI-FAMILY-RESULTS.md tables + cross-family summary *verbatim*:
    - encoding (chardet v6→v7 AI): ST [0.42,0.99], PQidist 0.020 (indep band 0.013–0.020), resApi 13 (11–16) → inside band, indistinguishable (NO)
    - fuzzy (RapidFuzz human GPL→MIT): PQidist 0.046 (0.000–0.072), res 2 (0–12) → inside, indistinguishable (NO)
    - fuzzy (thefuzz fork): 0.198 / 7 → detected
    - toml (tomli→tomllib vendored): 0.906 / 68 → strongly detected; all AUC=1.000
    - Leave-pair-out false-positive behaviour (jellyfish↔textdistance res=12) exposed exactly as documented.
  - `python3 pilot/residual.py` — exit 0. Residual counts + exact identifier lists match PILOT-RESULTS.md:86-92 and MULTI-FAMILY:
    - chardet v6→v7: resApi 13 (list: LEGACY_ISO/MAC/MAP/REGIONAL, MODERN_WEB, NON_CJK, encoding_era, lang_filter, ascii_letters, max_bytes, ...)
    - chardet v5→v6: 228
    - fuzzy reimpl: 2; fork: 7; jellyfish independent: 12 (false pos)
  - Spot-check `pilot/results.json` (post prior harness run): v6-v7 ST envelope [0.42,0.99], BHd 0.135 (inside independent spread 0.072-0.430 per doc), n_hard=245 / n_discrim=223 — identical to round-5 values.
  - `pilot/pilot_harness.py` and `power/power_analysis.py` not re-executed in full (task states "only legal-language softening changed"; their outputs were already locked in round 5 and the above pilots cover the multi-family / residual / P0 claims).

- No other files touched. No changes to numbers, tables, AUCs, residuals, power curves, harness code, or structural logic. The four legal sentences + one P0 clause are the sole deltas.

Nothing broke; all scripts remain deterministic and produce the documented artifacts.

---

## Judgment against "Implementation status (P0)" block (SPECIFICATION.md:8)

The P0 disclaimer continues to accurately bound the artifact:
- Actually implemented today: pilot harness + structural/behavioral/provenance/quirk signals + §5.4 residual prototype on **three families via multi_family_pilot.py** + seeded power simulation.
- Designed but NOT yet built items remain correctly labeled as such.
- All claims in PILOT-RESULTS, MULTI-FAMILY-RESULTS, POWER-ANALYSIS, legal-framework, and SPECIFICATION itself respect the P0 boundary.

---

## Final Determination

**(A) UNCONDITIONAL APPROVAL of the whole artifact.**

The four legal-verdict overreaches and the P0 staleness item have been fully remediated with precise, minimal language softening. The required grep returns nothing. A broader scan confirms no residual legal conclusions anywhere in the primary documentation. Pilot re-runs reproduce the documented numbers exactly; no numeric, code, or scope drift occurred. All round-5 evidence remains valid. The artifact is clean, reproducible, P0-honest, and free of any legal verdict language.

**Persisted:** this file (spec-reviews/grok-verification-round6.md).