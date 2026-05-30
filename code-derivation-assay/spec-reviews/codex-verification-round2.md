# Codex Verification Round 2

B) REMAINING concrete blockers

1. The required residual cleanup still fails the exact command check: `grep -rn "~8" SPECIFICATION.md pilot/PILOT-RESULTS.md` returns matches, not nothing.

   Actual command output:

   ```text
   SPECIFICATION.md:11:- **v0.8 -> v0.8.1 (2026-05-30).** Corrections from the round-1 verification reviews (codex/gemini/grok, all code-grounded): added the Implementation-status disclaimer above; corrected the chardet residual from "~8" to **13** (script output; ~5 stdlib/param false positives) (§5.4); qualified "no aggregate measure separates" to "no measure *robustly* separates," disclosing that the WL AUC 1.0 is a **name-based-graph vocabulary artifact** and not renaming-invariant (§5.2, §5.4); aligned §9.1 wording with the implemented first-order cluster bootstrap.
   pilot/PILOT-RESULTS.md:77:**But the distinctiveness inspection found what the score dilutes.** v6 and v7 share **18 distinctive identifiers absent from csn**: some are public API (`UniversalDetector, detect_all, EncodingEra, LanguageFilter, encoding_era`) which **AFC filters out** as compatibility-dictated — but also **arbitrary internal names** (`LEGACY_ISO/MAC/MAP/REGIONAL, MODERN_WEB, NON_CJK, MINIMUM_THRESHOLD, ignore_threshold`) a clean-room author would invent differently. In a Jaccard over thousands of identifiers these ~8 vanish to 0.02; to a court they are **"striking similarity."**
   exit=0
   ```

   Why still wrong: the requested verification condition was that this grep return nothing. The old residual value is still present in `SPECIFICATION.md:11`, and `pilot/PILOT-RESULTS.md:77` still contains a residual-adjacent "~8" statement in the same distinctiveness discussion. The corrected "13" text does appear elsewhere (`SPECIFICATION.md:120`, `pilot/PILOT-RESULTS.md:79`, `pilot/PILOT-RESULTS.md:87`), but the stale `~8` occurrences remain.

2. The WL/name-based correction is documented in `SPECIFICATION.md` and `pilot/PILOT-RESULTS.md`, but the actual pilot source still contains a contradictory renaming-invariance claim.

   Still-wrong text:

   ```text
   pilot/structural.py:6:not a single number. Renaming-invariant: names are never used for matching."""
   ```

   Contradicting implementation:

   ```text
   pilot/structural.py:32:# ---------- call graph (name-based, approximate) ----------
   pilot/structural.py:39:                defined.add(n.name)
   ```

   Why still wrong: the round-2 correction requires the renaming-invariance claim to be corrected and the name-based artifact to be honestly labeled. The prose now does that (`SPECIFICATION.md:100`, `SPECIFICATION.md:115`, `pilot/PILOT-RESULTS.md:26`), but the source file still asserts "Renaming-invariant: names are never used for matching" while constructing call-graph node identity from function names.
