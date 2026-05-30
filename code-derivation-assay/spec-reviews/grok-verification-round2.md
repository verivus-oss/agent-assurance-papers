# ADVERSARIAL VERIFICATION REVIEW — Grok Round 2 (Corrections Verification)

**Reviewer:** Grok 4.3 (xAI)  
**Date:** 2026-05-30 (post-correction)  
**Scope:** Re-verify the six specific corrections listed in the round-2 query against the *live files* (SPECIFICATION.md, pilot/PILOT-RESULTS.md, pilot/residual.py, pilot/structural.py) only. Round-1 blockers read for reference; round1-corrections.md read for mapping but **never accepted as evidence**. Every claim re-checked by (a) direct file reads with line numbers, (b) exact `grep` / command output capture, (c) re-execution of `pilot/residual.py` (stdout captured), (d) no prose or "fixed in log" accepted.  
**Method per query:** For each of the 6 items, either (A) cite the verified file:line + verbatim new text / command output, OR (B) cite the still-wrong text + why it remains a defect. Verdict format: numbered REMAINING BLOCKERS only for anything still failing; positives noted but do not override.  

**Reproduction / evidence commands (this round):**  
- `grep -rn "~8" SPECIFICATION.md pilot/PILOT-RESULTS.md` (exact output captured below)  
- `python3 pilot/residual.py` (full stdout captured; chardet v6→v7 = 13 post-API; jellyfish row uses 1-lib `[levenshtein]`)  
- Direct reads of SPECIFICATION.md:8 (P0 block), :100 (§5.2), :115+120 (§5.4), :190 (§9.1); pilot/PILOT-RESULTS.md:26 (WL caveat), :46 (AI spread), :92 (jellyfish baseline), :77+79 (residual count).  

---

## VERIFICATION PER THE 6 REQUESTED ITEMS (file:line + evidence)

**1. chardet residual stated as 13 (not ~8) everywhere.**  
**Command executed (per query instruction):**  
```
cd /srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay && grep -rn "~8" SPECIFICATION.md pilot/PILOT-RESULTS.md
```
**Actual output:**
```
SPECIFICATION.md:11:- **v0.8 → v0.8.1 (2026-05-30).** Corrections from the round-1 verification reviews (codex/gemini/grok, all code-grounded): added the Implementation-status disclaimer above; corrected the chardet residual from "~8" to **13** (script output; ~5 stdlib/param false positives) (§5.4); qualified "no aggregate measure separates" to "no measure *robustly* separates," disclosing that the WL AUC 1.0 is a **name-based-graph vocabulary artifact** and not renaming-invariant (§5.2, §5.4); aligned §9.1 wording with the implemented first-order cluster bootstrap.
pilot/PILOT-RESULTS.md:77:**But the distinctiveness inspection found what the score dilutes.** v6 and v7 share **18 distinctive identifiers absent from csn**: some are public API (`UniversalDetector, detect_all, EncodingEra, LanguageFilter, encoding_era`) which **AFC filters out** as compatibility-dictated — but also **arbitrary internal names** (`LEGACY_ISO/MAC/MAP/REGIONAL, MODERN_WEB, NON_CJK, MINIMUM_THRESHOLD, ignore_threshold`) a clean-room author would invent differently. In a Jaccard over thousands of identifiers these ~8 vanish to 0.02; to a court they are **"striking similarity."**
```
**Confirmed "13" locations (good):**  
- SPECIFICATION.md:120 (in §5.4): "(chardet v6→v7: **13** identifiers survive API filtering per `pilot/residual.py` — but ~5 are stdlib/parameter false positives..."  
- PILOT-RESULTS.md:79: "For chardet v6→v7 that residual is **13 raw identifiers** (`pilot/residual.py` output), of which ~5 are stdlib/parameter false positives..."  
- PILOT-RESULTS.md:87 (table): "**13** | LEGACY_MAC, MODERN_WEB..."  
- PILOT-RESULTS.md:94: "chardet v6→v7 residual (13, dominated by the kept `EncodingEra`...)"  
- Re-run (`python3 pilot/residual.py`): "DERIVED  v6→v7 (AI rewrite) ... 13" + "residual after API filter (13 idents): ['CHINESE_SIMPLIFIED', ... 'max_bytes']"  

**Still wrong:** The explicit verification criterion ("grep ... should return nothing") is not met, and the active explanatory prose at PILOT-RESULTS.md:77 continues to state the pre-filter / Jaccard dilution using the stale "~8" value in the exact same paragraph that introduces the AFC residual measure. This is the identical defect as round-1 blocker #1, incompletely corrected.

**2. WL AUC-1.0 now disclosed as NAME-BASED call-graph shared-vocabulary artifact (NOT faithful-WL contradiction); predecessor 0.587/0.872 acknowledged external/not-in-repo.**  
**Verified locations (per query):**  
- SPECIFICATION.md:100 (§5.2): "**Pilot caveat (verification round 1):** only the *type*-based pilot measures (AST node-type shingles/histograms) are renaming-invariant; the pilot's *call-graph* topology/WL (`pilot/structural.py`, node identity = function **name**) are **not** renaming-invariant and are confounded by shared identifier vocabulary, and the §7.3 invariance test is a design requirement **not yet implemented**."  
- SPECIFICATION.md:115 (§5.4): "The one apparent exception — a WL-kernel variant at AUC 1.0 — is a **shared-identifier-vocabulary artifact**: `pilot/structural.py` builds call-graph node identity from function *names* (not renaming-invariant), so it merely detects that the chardet lineage shares method names while charset_normalizer does not; it also contradicts the predecessor's WL, so it is not a defensible structural signal."  
- PILOT-RESULTS.md:26 (envelope section): "**Caveat (verification round 1):** my WL is *not* a faithful equivalent of the predecessor's — `pilot/structural.py` builds call-graph node identity from function **names** (so it is **not** renaming-invariant; codex/gemini/grok confirmed `defined.add(n.name)` at `structural.py:39`), aggregates successors only, and omits the predecessor's predecessor-labels + qualified names. So the AUC 1.0 is largely a **shared-identifier-vocabulary artifact** (chardet versions share method names; csn does not), not a profound structural finding — and the predecessor's 0.587/0.872 are **external citations not reproducible from any file in this repo**."  

**Code confirmation (re-read + re-run via harness path):** `pilot/structural.py:39`: `defined.add(n.name)` (name-based node identity for the WL + topology call graphs that produce the AUC 1.0 row); `pilot_harness.py` + `structural.py:91-110` (wl_cosine) exercised on real chardet artifacts → AUC[ST_wl]=1.000. No 0.587/0.872 anywhere in tree except the now-qualified prose citation.  

**Verdict for item 2 (docs):** The required disclosure language is present at the cited §5.2 / §5.4 / PILOT envelope locations. (Separate source-docstring defect noted in blockers below.)

**3. "AI rewrite below independent" corrected to "within the independent spread (v7-csn 0.072 … 0.430)" in PILOT-RESULTS.md.**  
**Verified (exact text):**  
PILOT-RESULTS.md:46: "My strengthened BHd agrees in direction: EVOLVED 0.605, and the AI rewrite at **0.135 sits within the independent spread** (v7-csn **0.072** … v6-csn 0.430) — below two of the three independent pairs but above v7-csn, i.e. at the independent baseline, not cleanly below it."  

**Matches** the required correction language. (Re-run of pilot_harness.py path in prior round produced BHd=0.135 and the v7-csn / v6-csn values; the prose now uses them correctly.)

**4. jellyfish↔textdistance control baseline corrected to 1-lib [Levenshtein] in PILOT-RESULTS.md, matching residual.py:170.**  
**Verified (exact text + code):**  
- PILOT-RESULTS.md:92: "the independent control false-positived at 12 because Python **builtins/stdlib** and **algorithm-canonical variable names** (the textbook Jaro variables) were not filtered — for this control `pilot/residual.py:170` passes a **1-lib baseline `[Levenshtein]`** (thinner than the 3-lib pool used for the fuzzy DERIVED rows), and no builtin/stdlib stoplist was applied."  
- pilot/residual.py:170 (exact): `residual(fz['jellyfish'], fz['textdistance'], [fz['levenshtein']], 'INDEPENDENT  jellyfish↔textdistance'),`  
- Re-run output (2026-05-30): "INDEPENDENT  jellyfish↔textdistance     12      12      12       0" under the "fuzzy-matching family (baseline pool = {jellyfish, Levenshtein, textdistance})" header, with the call explicitly using the 1-element list for that row.  

**Matches** round-1 blocker #2 correction requirement.

**5. SPECIFICATION.md §9.1 first-order cluster bootstrap, within-family resampling NOT implemented.**  
**Verified (exact text):**  
SPECIFICATION.md:190 (§9.1 item 1): "resampling at the **family (cluster) level** (the power sim implements a *first-order* cluster bootstrap — resample families, per-family AUC as the cluster observation; **within-family resampling is a documented refinement not yet implemented**, `power/POWER-ANALYSIS.md` §6) — because pairs within a family share idiom/dependencies/ancestry and are not independent; pair-level resampling would understate CI width."  

**Matches** the required wording. (Power analysis code was already confirmed family-clustered in round 1; this is the doc alignment.)

**6. A prominent "Implementation status (P0)" block scopes cross-language / MANIFEST-copyleft / make-validate / full-§5.4 as DESIGNED-NOT-BUILT.**  
**Verified (exact text at top of file):**  
SPECIFICATION.md:8 (prominent, immediately after license/date, before any claims):  
"**Implementation status (P0) — read before treating any claim as "built."** This repository is at milestone **P0**: a *frozen design* (this spec) plus a *pilot* (`pilot/`) and a *seeded simulation power analysis* (`power/`). **The spec is normative for the future build, not a description of shipped software.** Actually implemented today: the Python-only pilot harness; the structural/behavioral/provenance/quirk signals on the chardet trio; the §5.4 residual *prototype* (identifiers/messages/constants only) on the chardet + fuzzy families; the power simulation. **Designed but NOT yet built:** cross-language ST/PB (§5.2, §18.4 — the pilot is Python-`ast` only); the redistributed, MANIFEST-backed, notice-preserving corpus (§6, §10.4 — the pilot reads external local checkouts at hardcoded paths); `make validate` / R-NODRIFT / R-HERMETIC / R-FIG and the `harness/ validate/ benchmark/ container/ Makefile` tree (§10, §15, §17); and the full §5.4 measure (calibrated improbability + CI + comment/dead-code/data-table/behavioral feature types). Claims about those are **design commitments** (verify them against this spec), not against current code. The independent verification reviews in `spec-reviews/*-verification-round1.md` flagged exactly these design-vs-code gaps; this block is the standing disclaimer."  

Inline per-claim markers also present (e.g. SPECIFICATION.md:100: "Cross-language capable (PI decision, §18.4; *designed, not yet built — the pilot is Python-only, see Implementation status*)").  

**Matches** the required scoping for round-1 blockers #4 and #5.

---

## REMAINING CONCRETE BLOCKERS (items still wrong after claimed fixes)

**1. (Affects requested item 1 + the "13 everywhere" criterion)**  
   **Defect:** chardet residual still stated with stale "~8" value in active prose; the explicit verification command returns matches (not nothing).  
   **Files:lines:**  
   - `pilot/PILOT-RESULTS.md:77` (the still-wrong text in the load-bearing distinctiveness → AFC transition paragraph):  
     ```
     v6 and v7 share **18 distinctive identifiers absent from csn**: ... In a Jaccard over thousands of identifiers these ~8 vanish to 0.02; to a court they are **"striking similarity."**
     ```  
     (Immediately followed at :79 by the correct "that residual is **13 raw identifiers**", creating internal contradiction within the same section.)  
   - `SPECIFICATION.md:11` (changelog sentence describing the prior state): contains the literal substring `from "~8" to **13**`.  
   **Why still wrong:** Round-1 blocker #1 required the residual to be stated as 13 (not ~8) *everywhere* in the two documents, with the explicit test "grep -rn "~8" ... should return nothing". The active claim in PILOT-RESULTS.md:77 (the paragraph that justifies inventing the §5.4 residual measure) still uses the old approximate number. This is not a meta/history note; it is the same class of numeric claim-vs-code mismatch that round 1 blocked. Re-run of `pilot/residual.py` produces 13, not ~8. The correction is incomplete.

**2. (Affects the WL disclosure in requested item 2 at the implementation source)**  
   **Defect:** The pilot source that produces the WL AUC 1.0 still contains an internal claim that it *is* renaming-invariant, directly contradicting the disclosure now present in SPEC §5.2/§5.4 and PILOT-RESULTS.md:26.  
   **File:line:** `pilot/structural.py:6` (module docstring):  
     ```
     not a single number. Renaming-invariant: names are never used for matching."""
     ```  
   **Actual implementation (same file):**  
     ```python
     # ---------- call graph (name-based, approximate) ----------
     ...
     defined.add(n.name)   # line 39
     ```  
     (This name-based graph is exactly the one exercised for the WL row that yields AUC 1.0 and the "shared-identifier-vocabulary artifact" finding.)  
   **Why still wrong:** The round-2 query requires the WL AUC 1.0 to be *disclosed* as name-based / not renaming-invariant / a vocabulary artifact rather than a faithful contradiction. The md files now contain that disclosure (verified under item 2 above). However, the authoritative source file for the measure still asserts the opposite property in its own header comment. A reader who starts from the pilot code (as any reproducer must) sees a false claim of renaming-invariance for the exact construction that the spec/PILOT now correctly caveat. This is a live doc-vs-code defect in the artifact under review. (Re-execution via `pilot_harness.py` confirms the AUC 1.0 comes from this name-based path.)

---

## Summary

**Items 2–6 (as enumerated in the query):** All corrections verified at the cited file:line locations with matching verbatim text + supporting command / re-run output. The P0 block is prominent and correctly scopes the designed-not-built items; §9.1 correctly labels the bootstrap as first-order only; the AI-rewrite and jellyfish baseline corrections match the required language and the code at residual.py:170.

**Item 1 + related source consistency:** Fails the explicit "everywhere / grep returns nothing" test. One active prose location (PILOT-RESULTS.md:77) and the source docstring (structural.py:6) remain inconsistent with the corrected claims.

No other numeric or scoping claims among the six were found to be still wrong on direct inspection + re-execution. The pilot mechanics that were sound in round 1 (family-clustered BCa, AFC filtration producing the real 13/228/2/7/12, reproducible envelope) remain sound.

**End of review.** Persisted to `spec-reviews/grok-verification-round2.md`. All citations are from live file reads (with line numbers), the exact grep output above, and `python3 pilot/residual.py` stdout captured 2026-05-30 after the claimed fixes.
