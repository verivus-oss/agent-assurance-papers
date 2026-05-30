# Codex Verification Round 4

Result: **BLOCKED — no unconditional approval.**

Fresh commands run from `/srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay`:

- `python3 pilot/pilot_harness.py` — completed; regenerated `pilot/results.json`.
- `python3 pilot/residual.py` — completed.
- `python3 power/power_analysis.py` — completed; regenerated `power/results.json`.

I treated `SPECIFICATION.md`'s P0 implementation-status block as controlling: designed-but-not-built future machinery is not a blocker merely for being unimplemented. The blockers below are current doc-vs-code/output inconsistencies or unsupported current conclusions.

## Blockers

1. **`pilot/PILOT-RESULTS.md:50` still makes a stale false numeric claim about the current ensemble.**

   The line says: "The hard within-domain contrast (AI-rewrite vs independent) is near chance across the *entire* measure ensemble (AUCs 0.11–0.67)." This is not true for the current `pilot/pilot_harness.py` output. The harness computes the current measure set at `pilot/pilot_harness.py:363-396` and prints the AUC table at `pilot/pilot_harness.py:428-430`. Fresh output includes AUC values above 0.67: `ST_wl = 1.000`, `PQmsg = 1.000`, `QKidist = 0.889`, `QKdoc = 0.889`, and `QKcomm = 0.778`; `pilot/results.json` contains the same values. This also contradicts `pilot/PILOT-RESULTS.md:24` and `pilot/PILOT-RESULTS.md:97`, which correctly state that current per-measure AUC spans `0.11–1.00`. The later caveats correctly label some high-AUC measures as artifacts, but that does not make the numeric range at line 50 true.

2. **`pilot/PILOT-RESULTS.md:51` says "only literal/provenance carryover separates copying from clean reimplementation, and chardet v7 has none," but the current residual prototype finds non-zero arbitrary-expression residual.**

   Fresh `python3 pilot/residual.py` reports for `DERIVED v6→v7 (AI rewrite)`: `shared=25`, `resDom=18`, `resAPI=13`, `resMsg=1`, including `LEGACY_ISO`, `LEGACY_MAC`, `LEGACY_MAP`, `LEGACY_REGIONAL`, `MODERN_WEB`, `NON_CJK`, `encoding_era`, `ignore_threshold`, `lang_filter`, plus false positives such as `ascii_letters` and `max_bytes`. The residual computation is at `pilot/residual.py:121-131`, and the chardet scenarios are run at `pilot/residual.py:149-159`. The current document itself later states the corrected version at `pilot/PILOT-RESULTS.md:77-79` and `pilot/PILOT-RESULTS.md:84-94`: residual `13`, small and contestable, not zero. Line 51 is therefore stale and overstates the absence of provenance/literal carryover.

3. **`legal-framework.md:39` and `legal-framework.md:47` render an unsupported legal/outcome conclusion and are stale relative to the residual output.**

   `legal-framework.md:39` says the pilot found protected-expression quirks "≈ 0" and that "Under AFC, chardet v7 likely reads 'not a derivative work'"; `legal-framework.md:47` says "PB ≈ 0" aligns with a "legal likely-outcome (not a derivative work)." The current residual output is not `≈0`: it reports `13` post-API-filter identifiers and `1` residual message for v6→v7. `SPECIFICATION.md:120` now correctly frames this as "small but non-zero" and "genuinely contestable, not clear-cut." These legal-framework lines are therefore both numerically stale and stronger than the artifact's own no-legal-verdict framing.

4. **`SPECIFICATION.md:354` contradicts the current pilot by saying the chardet pair is expected to read as `ST≈0 / PB-elevated`.**

   Fresh `python3 pilot/pilot_harness.py` reports for disputed `v6-v7`: `ST envelope [0.416 … 0.986]`, `PBt=0.000`, `BHd=0.135`, `PQconst=0.092`, `PQmsg=0.012`, `PQvocab=0.045`, `PQconf=0.588`. Fresh `python3 pilot/residual.py` reports a small, non-zero residual of `13` identifiers. That is not `ST≈0 / PB-elevated`; it is the mixed picture described elsewhere in the spec at `SPECIFICATION.md:115-120` and in the pilot caveats. As written, line 354 preserves an older expected split that no longer matches the actual code/output.

5. **`power/POWER-ANALYSIS.md:111` marks a `≥2`-family pilot requirement as "DONE" using only the chardet ST/PB/BH pilot.**

   The line says the pilot must run a draft ST/PB/BH harness on "≥2 real within-domain DERIVED/INDEPENDENT family pairs", then marks "DONE (first pass)" because `pilot/PILOT-RESULTS.md` ran on the chardet trio. The actual ST/PB/BH harness is only the chardet/charset-normalizer domain: `pilot/pilot_harness.py:46-59` defines `v5`, `v6`, `v7`, `csn` and six pairs within that one domain. The second family appears only in the residual prototype (`pilot/residual.py:161-172`), not in the ST/PB/BH pilot requested by the power doc. This is a completion overclaim: the current artifact may honestly say "first one-family pass complete", but not that the stated `≥2`-family ST/PB/BH pilot requirement is done.

Because these are present-tense/stale claims in the current artifact, I cannot give unconditional approval.
