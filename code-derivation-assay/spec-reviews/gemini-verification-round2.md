# Gemini Verification Round 2

B) REMAINING concrete blockers

1. The chardet residual cleanup fails the exact command check: `grep -rn "~8" SPECIFICATION.md pilot/PILOT-RESULTS.md` returns matches.

   Actual command output:
   ```text
   SPECIFICATION.md:11:- **v0.8 → v0.8.1 (2026-05-30).** Corrections ... corrected the chardet residual from "~8" to **13** ...
   pilot/PILOT-RESULTS.md:77:**But the distinctiveness inspection found what the score dilutes.** v6 and v7 share **18 distinctive identifiers absent from csn**: some are public API (`UniversalDetector, detect_all, EncodingEra, LanguageFilter, encoding_era`) which **AFC filters out** as compatibility-dictated — but also **arbitrary internal names** (`LEGACY_ISO/MAC/MAP/REGIONAL, MODERN_WEB, NON_CJK, MINIMUM_THRESHOLD, ignore_threshold`) a clean-room author would invent differently. In a Jaccard over thousands of identifiers these ~8 vanish to 0.02; to a court they are **"striking similarity."**
   ```

   - **SPECIFICATION.md:11**: Contains `~8` in the changelog entry. The requirement stated the grep should return nothing.
   - **pilot/PILOT-RESULTS.md:77**: Still contains `~8` ("these ~8 vanish to 0.02") and incorrectly states "18 distinctive identifiers", which contradicts the "13" stated in §5.4 and Iteration 7.

2. The renaming-invariance claim remains uncorrected in the pilot source code, contradicting the disclosure in the specification.

   Still-wrong text at **pilot/structural.py:6**:
   ```python
   6:not a single number. Renaming-invariant: names are never used for matching."""
   ```

   Actual implementation at **pilot/structural.py:39**:
   ```python
   39:                defined.add(n.name)
   ```

   Why still wrong: While `SPECIFICATION.md` (§5.2, §5.4) and `pilot/PILOT-RESULTS.md` correctly disclose that the name-based call-graph is NOT renaming-invariant, the source file `pilot/structural.py` still asserts it is renaming-invariant in its docstring.

Verified corrections:
- **3. AI rewrite spread**: `pilot/PILOT-RESULTS.md:65` correctly states "within the independent spread (v7-csn 0.072 … v6-csn 0.430)".
- **4. jellyfish baseline**: `pilot/residual.py:170` correctly uses `[fz['levenshtein']]` as the 1-lib baseline.
- **5. Cluster bootstrap**: `SPECIFICATION.md:188` correctly describes first-order cluster bootstrap and states that within-family resampling is "not yet implemented".
- **6. Implementation status**: `SPECIFICATION.md:8-10` contains the prominent "Implementation status (P0)" block correctly scoping cross-language, MANIFEST-copyleft, etc., as DESIGNED but NOT yet built.
