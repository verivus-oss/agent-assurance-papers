# Verification Report — Round 4 (Gemini)

I performed a full, fresh, adversarial verification of the entire `code-derivation-assay` artifact (SPECIFICATION.md v0.8.1, pilot/, power/, family-census.md, legal-framework.md) by re-running the test scripts (`pilot_harness.py`, `residual.py`, `power_analysis.py`) and rigorously checking every numeric claim and qualitative finding against the live script outputs.

While the vast majority of the claims and values have been correctly updated to match the latest script outputs (and the implementation scope properly disclaimed), I cannot issue an unconditional approval because I found a specific, verifiable doc-vs-code gap that remains.

**(B) Concrete Blockers:**

1. **`pilot/PILOT-RESULTS.md:77` — Doc-vs-code gap and internal inconsistency regarding the 13 residual identifiers.**
   - **Why:** The prose explicitly claims that `encoding_era` was removed by API filtering (`"...after removing the public-API names (..., encoding_era...)"`) and that `MINIMUM_THRESHOLD` remains in the residual (`"...including arbitrary internal names (..., MINIMUM_THRESHOLD...)"`). 
   - However, the output of `python3 pilot/residual.py` directly contradicts this: `encoding_era` is actually INCLUDED in the list of 13 remaining identifiers, while `MINIMUM_THRESHOLD` was FILTERED OUT (it is one of the 5 removed from the original 18).
   - This creates an internal inconsistency within `PILOT-RESULTS.md` itself, as Iteration 7 text (line 87) correctly lists `encoding_era` as part of the residual, and it also contradicts `SPECIFICATION.md` v0.8.1, which correctly places `encoding_era` in the remainder. Line 77 needs to be corrected to match the script's actual filtration behavior.