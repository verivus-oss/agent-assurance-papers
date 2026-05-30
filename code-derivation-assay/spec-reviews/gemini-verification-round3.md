# Gemini CLI Spec Verification: Round 3 (FINAL)

This report documents the final verification of the two remaining blockers identified in Round 2 (`spec-reviews/gemini-verification-round2.md`).

## Verification Results

### B1: Stale "~8" and Count Reconciliation
**Status: RESOLVED**

1. **Stale References:** Running `grep -rn "~8" SPECIFICATION.md pilot/PILOT-RESULTS.md` returned **NOTHING**, confirming all stale approximate counts have been removed or updated.
2. **Count Reconciliation:** `pilot/PILOT-RESULTS.md` (lines 77-80) now correctly reconciles the identifier overlap counts:
   - "18 distinctive identifiers absent from csn (`resDom`)"
   - "13 remain (`resApi`, per `pilot/residual.py`)"
3. **Live Script Verification:** Running `python3 pilot/residual.py` in the workspace confirmed these numbers are live and accurate:
   ```
   scenario                           shared  resDom  resAPI  resMsg
   DERIVED  v6→v7 (AI rewrite)            25      18      13       1
   ```
   The previous contradiction (18 vs 13) is resolved by clearly distinguishing between the raw residual (`resDom`) and the API-filtered residual (`resApi`).

### B2: structural.py Docstring Correctness
**Status: RESOLVED**

1. **Docstring Update:** The module docstring for `pilot/structural.py` has been updated to correctly describe its invariance properties:
   > "NOT renaming-invariant (verification round 1): `build_call_graph` uses function NAMES as node identity (`defined.add(n.name)`, edges by name), so the topology and WL measures here are confounded by shared identifier vocabulary..."
2. **Implementation Alignment:** Confirmed line 39 in `pilot/structural.py` matches this description:
   ```python
   defined.add(n.name)
   ```
   The false claim that the measure was "Renaming-invariant: names are never used for matching" has been removed.

## UNCONDITIONAL APPROVAL

Both blockers are verified resolved against the live codebase.

- `grep` for "~8" returned nothing.
- `pilot/PILOT-RESULTS.md` matches `pilot/residual.py` output (18/13).
- `pilot/structural.py` docstring correctly identifies its name-dependence.

Verification completed on 2026-05-30.
