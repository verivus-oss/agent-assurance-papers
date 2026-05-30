# Codex verification round 5

**B) BLOCKERS**

1. `legal-framework.md:38` still contains the round-4 legal-conclusion defect: it says an AI rewrite that reproduces behavior but not arbitrary expression is, under Sega/Sony/Altai, "**not a derivative work**."

   Actual file line:
   ```text
   38 | **Clean-room rulings: reproducing function ≠ infringement** | ... an AI rewrite that reproduces behavior but not arbitrary expression is, under *Sega/Sony/Altai*, **not a derivative work**.
   ```

   Why this blocks approval: the requested round-4 correction was "small but non-zero / contestable / no verdict, not ... not a derivative work." `legal-framework.md:39` now has the corrected chardet-specific statement, but line 38 still makes a categorical derivative-work legal conclusion. That conflicts with `SPECIFICATION.md:30` ("CDA renders no legal verdict") and `SPECIFICATION.md:95` ("CDA never claims to measure the legal construct 'derivative work'").

   Actual rerun output contradicting a zero/no-issue framing:
   ```text
   [DERIVED  v6→v7 (AI rewrite)] residual after API filter (13 idents):
   ['CHINESE_SIMPLIFIED', 'CHINESE_TRADITIONAL', 'LEGACY_ISO', 'LEGACY_MAC',
    'LEGACY_MAP', 'LEGACY_REGIONAL', 'MODERN_WEB', 'NON_CJK', 'ascii_letters',
    'encoding_era', 'ignore_threshold', 'lang_filter', 'max_bytes']
   residual messages: ['with confidence']
   ```

2. `pilot/MULTI-FAMILY-RESULTS.md:27` makes unsupported legal verdicts from the static pilot: clean reimplementation is "likely non-infringing" and vendoring/forking is "legally infringing."

   Actual file line:
   ```text
   27 | Clean reimplementation retains little *protectable expression* (so it is both undetectable here and, under Sega/Sony/Altai, likely non-infringing); vendoring/forking retains arbitrary expression (detectable, and legally infringing).
   ```

   Why this blocks approval: the multi-family script supports measurement claims, not legal outcomes. The artifact's own scope says "No legal advice or verdict" (`SPECIFICATION.md:30`, `SPECIFICATION.md:263`) and "CDA never claims to measure the legal construct 'derivative work'" (`SPECIFICATION.md:95`). Forking and vendoring can also be licensed or otherwise legally authorized; the script does not encode license permission, fair use, authorization, or infringement analysis.

   Actual rerun output supports detection only:
   ```text
   ############ FAMILY: toml ############
   tomli-tomllib         DERIVED-vendored              [0.76,1.00]      0.906  0.676     68
   ...
   AUC[ pqidist] (same-lineage vs independent) = 1.000
   AUC[  resApi] (same-lineage vs independent) = 1.000

   ############ FAMILY: fuzzy ############
   fuzzywuzzy-thefuzz    DERIVED-fork                  [0.45,0.99]      0.198  0.768      7
   ```

3. `pilot/PILOT-RESULTS.md:77` still overstates the legal interpretation of the chardet residual by saying the residual identifiers are, "to a court," striking similarity.

   Actual file line:
   ```text
   77 | ... In a Jaccard over thousands of identifiers these vanish to 0.02; to a court they are **"striking similarity."**
   ```

   Why this blocks approval: the code output establishes a small residual count, including known false positives, but does not establish what a court would conclude. The same document later says the residual leaves "a handful of genuinely arbitrary names — small but non-zero" and that the case is "genuinely contestable rather than clear-cut" (`pilot/PILOT-RESULTS.md:79`). The court-outcome phrasing is stronger than the measured evidence.

4. `SPECIFICATION.md:8` is stale against the new round-5 multi-family implementation and is no longer an accurate "Implementation status (P0)" block.

   Actual file line:
   ```text
   8 | Actually implemented today: ... the §5.4 residual *prototype* ... on the chardet + fuzzy families; the power simulation.
   ```

   Why this blocks approval: the new implemented artifact now includes `pilot/multi_family_pilot.py` and `pilot/MULTI-FAMILY-RESULTS.md`, including static measures plus §5.4 residual over a third TOML family. Because the P0 block is the rule for distinguishing built results from design commitments, this underreports the current implemented surface.

   Actual rerun output:
   ```text
   ############ FAMILY: toml ############
   tomli-tomllib         DERIVED-vendored              [0.76,1.00]      0.906  0.676     68
   tomli-tomlkit         INDEPENDENT                   [0.45,0.99]      0.013  0.089      1
   toml-tomlkit          INDEPENDENT                   [0.51,0.97]      0.014  0.107      1
   tomllib-toml          INDEPENDENT                   [0.48,0.98]      0.026  0.092      0
   ```

**Verified Reproduction Evidence**

The four requested commands ran successfully:

```text
python3 pilot/pilot_harness.py
python3 pilot/residual.py
python3 pilot/multi_family_pilot.py
python3 power/power_analysis.py
```

Round-4 numerical corrections that do reproduce:

- `pilot/PILOT-RESULTS.md:50` matches the fresh AUC table: the current per-measure AUC range is `0.11–1.00`, with high values including `ST_wl = 1.000`, `PQmsg = 1.000`, `QKidist = 0.889`, `QKdoc = 0.889`, and `QKcomm = 0.778`; the text labels the high values artifacts.
- `pilot/PILOT-RESULTS.md:51` matches `pilot/residual.py`: chardet v6→v7 has small but non-zero residual expression, not none.
- `pilot/PILOT-RESULTS.md:77` now has `encoding_era` in the 13-residual list and `MINIMUM_THRESHOLD` in the API-filtered list, matching the fresh `pilot/residual.py` output.
- `SPECIFICATION.md:354` now says `ST [0.42–0.99]`, PB literal carryover `~0`, and small non-zero arbitrary-name residual `13 raw`, matching the fresh pilot output:
  ```text
  ST envelope [0.416 … 0.986]  PBt=0.000  BHd=0.135
  ```
- `power/POWER-ANALYSIS.md:67-74` correctly labels the naive table as the `K=5` rows. Fresh output for `K=5` includes:
  ```text
  0.86   5      0.66            0.71
  0.90   5      0.83            0.93
  ```
- `power/POWER-ANALYSIS.md:113` correctly distinguishes the full ST/PB/BH harness as one family and the static extension as three families.

New multi-family numerical claims reproduce:

```text
fuzzywuzzy-rapidfuzz  DERIVED-reimpl(human GPL→MIT) [0.70,0.99]      0.046  0.200      2
fuzzywuzzy-thefuzz    DERIVED-fork                  [0.45,0.99]      0.198  0.768      7
tomli-tomllib         DERIVED-vendored              [0.76,1.00]      0.906  0.676     68
```

The leave-pair-out baseline logic is present in `pilot/multi_family_pilot.py:68-71` and implemented at `pilot/multi_family_pilot.py:110-112`:

```text
base_ids = [x for x in cfg['independents'] if x not in (a, b)]   # LEAVE-PAIR-OUT
res = R.residual(F[a]['rfeat'], F[b]['rfeat'],
                 [F[x]['rfeat'] for x in base_ids], label)
```
