# Codex Verification Round 1

Verdict: BLOCKED. I re-ran the requested scripts from `/srv/repos/external/verivus-oss/agent-assurance-papers/code-derivation-assay` and verified the code, data, and prose against each other. The pilot and power scripts run, and `/tmp/fzsrc` is present, but the corrective-program spec is not approvable because several load-bearing claims are stronger than, or inconsistent with, the actual code.

Commands run:

```text
$ python3 pilot/pilot_harness.py
generated hard workload: 245 short/ambiguous inputs
...
hard workload: 245 inputs scored by all impls, 223 DISCRIMINATING (non-unanimous) → BHd uses these
...
v6-v7   DERIVED-airewrite    0.42  0.99  0.88  0.86  0.89  0.88   0.42   0.99
...
  AUC[   ST_wl] = 1.000
...
=== disputed AI-rewrite v6-v7 ===
  ST envelope [0.416 … 0.986]  PBt=0.000  BHd=0.135
```

```text
$ python3 pilot/residual.py
############ fuzzy-matching family (baseline pool = {jellyfish, Levenshtein, textdistance}) ############
scenario                           shared  resDom  resAPI  resMsg
DERIVED  fuzzywuzzy→RapidFuzz (GPL→MIT reimpl)     14       8       2       0
DERIVED  fuzzywuzzy→thefuzz (fork)     18      16       7       0
INDEPENDENT  jellyfish↔textdistance     12      12      12       0
...
############ chardet family (baseline pool = {charset_normalizer} — thin, n=1) ############
DERIVED  v6→v7 (AI rewrite)            25      18      13       1
```

```text
$ python3 power/power_analysis.py
=== H1 AUC power (theta_LB=0.70), family-clustered BCa lower bound ===
-- moderate_het, pairs=5v5 --
  meanAUC | K=2  K=3  K=4  K=5  K=6  K=8
   0.90   | 0.87  0.82  0.81  0.85  0.89  0.93
...
=== Naive pair-level bootstrap INFLATION (theta_LB=0.70, 5v5, tau=0.35) ===
   0.86   5      0.66            0.71
   0.90   5      0.83            0.93
...
Wrote power/results.json
```

1. SPECIFICATION overclaims that the AI rewrite sits at the independent baseline across the pilot; the actual pilot has a WL structural measure that separates same-lineage perfectly in this tiny dataset.

   SPECIFICATION.md:9 claims: "no aggregate similarity score (15 tried, ST/BH/PB/quirk) separates the AI rewrite - it sits at the independent baseline". SPECIFICATION.md:112 similarly claims: "no single aggregate similarity score ... separates an AI rewrite from independent reimplementation: the rewrite sits at the *independent baseline*".

   The run output contradicts that broad claim:

   ```text
   v6-v7   DERIVED-airewrite    0.42  0.99  0.88  0.86  0.89  0.88   0.42   0.99
   v5-csn  INDEPENDENT          0.46  0.99  0.59  0.83  0.50  0.88   0.46   0.99
   v6-csn  INDEPENDENT          0.45  1.00  0.93  0.86  0.57  0.90   0.45   1.00
   v7-csn  INDEPENDENT          0.51  0.98  0.97  0.86  0.59  0.94   0.51   0.98
     AUC[   ST_wl] = 1.000
   ```

   The code computes that AUC directly from same-lineage positives vs independent negatives: `pilot/pilot_harness.py:393-396` says `aucs = {s: auc(col(s, POS), col(s, NEG)) ... ('ST_sh', ... 'ST_wl', ... 'combined')}`. PILOT-RESULTS.md is internally more honest than the spec: `pilot/PILOT-RESULTS.md:28` says "some measures (WL-mine, AUC 1.0) *do* separate same-lineage from independent". The SPECIFICATION.md revision-history and section 5.4 claim need to be narrowed; as written, they are false against the actual pilot output.

2. The claimed "WL contradiction" is not established as a real contradiction between faithful WL kernels; the reimplementation is materially non-equivalent and partly name-dependent despite claiming otherwise.

   The pilot output does reproduce the current WL AUC:

   ```text
   AUC[   ST_wl] = 1.000
   ```

   The predecessor number is also real in the adjacent artifact: `/srv/repos/external/verivus-oss/agent-assurance-papers/chardet-relicense/manuscript/figures/scripts/validation_report.v2.json:239-244` records `"wl_cosine": 0.5873578287111396`, and lines 1257-1262 record the independent comparator `"actual": "wl_cosine=0.872 k=4 v6_labels=1710 v7_labels=1650"`.

   But `pilot/structural.py` is not a faithful C06a' reimplementation. It says names are not used: `pilot/structural.py:1-6` claims "Renaming-invariant: names are never used for matching." The code then builds the call graph from simple function names: `pilot/structural.py:35-41` says `defined.add(n.name)` and `g.add_nodes_from(defined)`, and `pilot/structural.py:53-57` says `callee = f.id ... else f.attr ...; if callee in defined ... g.add_edge(self.stack[-1], callee)`. Function names therefore define node identity and edge existence.

   It also omits half of the predecessor directed-WL refinement. The pilot WL only uses successors: `pilot/structural.py:99-101` says `nb = '|'.join(sorted(lab[m] for m in g.successors(n)))` and `new[n] = f'{lab[n]}>{nb}'`. The predecessor uses both predecessor and successor label multisets and hashes them: `/srv/repos/external/verivus-oss/agent-assurance-papers/chardet-relicense/proof-bundle/extract_signals.py:376-393` says `in_labels = sorted(labels[v] for v in g.predecessors(u))`, `out_labels = sorted(labels[v] for v in g.successors(u))`, and `new[u] = hashlib.sha256(payload).hexdigest()[:16]`.

   The pilot call graph is also less qualified than the predecessor graph. The predecessor records qualified caller names: `/srv/repos/external/verivus-oss/agent-assurance-papers/chardet-relicense/proof-bundle/extract_signals.py:193-201` says "Caller is a qualified name (module.func or module.Class.method)", and lines 209-221 record `qual = _qualified_name(...)` and append `(caller, callee)`.

   Therefore the prose in `pilot/PILOT-RESULTS.md:26` that "Two faithful-looking 'WL call-graph kernels' reach opposite verdicts" is over-supported. What is shown is that this pilot's non-equivalent, simple-name/successor-only WL variant flips the predecessor result. That is evidence of matcher fragility, but not evidence of a real contradiction between faithful implementations of the same WL kernel.

3. The power script is family-clustered BCa at the cluster level, but it does not implement the SPECIFICATION.md §9.1 "resample families, then pairs within" method.

   The family-clustered part is real. `power/power_analysis.py:97-108` computes `theta_hat = fam_auc.mean()`, samples `idx = rng.integers(0, K, size=(n_boot, K))`, computes `boot = fam_auc[idx].mean(axis=1)`, and uses `jack = np.array([np.delete(fam_auc, i).mean() for i in range(K)])`. That is family resampling plus a family-level jackknife acceleration, not pair-level resampling. The script also implements the K/theta_LB sweeps: `power/power_analysis.py:250-280` defines `Ks = [2, 3, 4, 5, 6, 8]`, `theta_lbs = [0.60, 0.65, 0.70]`, and appends `K_test_families`/`theta_LB` rows.

   The defect is that SPECIFICATION.md claims a stronger bootstrap than the code implements. `SPECIFICATION.md:187` says the primary CI resamples "at the **family (cluster) level** - resample families, then pairs within". The code never resamples pairs within a family in `bca_lower`; it treats each per-family AUC as the observation. POWER-ANALYSIS.md admits this limitation: `power/POWER-ANALYSIS.md:103-104` says "First-order cluster bootstrap: per-family AUC treated as the cluster observation; within-family sampling noise is not re-injected inside the bootstrap". The spec and the implemented/reporting method are therefore inconsistent.

4. The §5.4 residual measure is only a partial prototype, but SPECIFICATION.md describes it as the primary CDA measure with broader feature coverage and calibrated improbability/CI.

   SPECIFICATION.md:111-115 defines the primary measure as "AFC-operationalized" and says it will enumerate "distinctive shared features across ST/BH/PB (identifiers, constants, comments, dead code, error strings, data-table fingerprints, behavioral quirks)" and "Score the residual ... by its **improbability under independent creation** ... with CI".

   `pilot/residual.py` does not implement that measure. It extracts identifiers, messages, docstring words, API names, and floats in `pilot/residual.py:59-103`, but the residual calculation only uses distinctive identifiers, messages, and float counts: `pilot/residual.py:121-131` says `base_idist, base_msg, base_flt = ...`, `res_dom = sh_id - base_idist`, `res_api = res_dom - api`, `sh_msg = ...`, `sh_flt = ...`, and returns counts/lists. It does not score calibrated improbability, does not produce a CI, does not use comments, dead code, data-table fingerprints, behavioral quirks, or even the collected `docw` in the residual.

   The §5.4 prototype is useful and the docs note it is not validated, but the SPECIFICATION.md primary-measure prose is not backed by this harness code.

5. The chardet §5.4 residual count is inconsistent across SPECIFICATION.md and the actual script output.

   SPECIFICATION.md:117 says: "chardet v6→v7: ~8 arbitrary shared identifiers survive API filtering". SPECIFICATION.md:9 similarly says the residual is "small-but-non-zero (~8 arbitrary shared names after API filtering)".

   The actual run output is:

   ```text
   DERIVED  v6→v7 (AI rewrite)            25      18      13       1
   [DERIVED  v6→v7 (AI rewrite)] residual after API filter (13 idents): ['CHINESE_SIMPLIFIED', 'CHINESE_TRADITIONAL', 'LEGACY_ISO', 'LEGACY_MAC', 'LEGACY_MAP', 'LEGACY_REGIONAL', 'MODERN_WEB', 'NON_CJK', 'ascii_letters', 'encoding_era', 'ignore_threshold', 'lang_filter', 'max_bytes']
   ```

   `pilot/PILOT-RESULTS.md:87` and `pilot/PILOT-RESULTS.md:94` correctly report 13. The spec's "~8" is stale or based on the earlier iteration-6 manual interpretation, not the implemented `pilot/residual.py` output.

6. The residual filtration described in PILOT-RESULTS.md iteration 7 is implemented, and it also proves the measure currently false-positives an independent control; any stronger claim would be unsupported.

   The filtration code matches the high-level description: `pilot/residual.py:121-127` builds `base_idist`, `base_msg`, `base_flt`, computes `api = A['api'] | B['api']`, then subtracts baseline and API via `res_dom = sh_id - base_idist` and `res_api = res_dom - api`.

   The requested residual numbers reproduce:

   ```text
   DERIVED  fuzzywuzzy→RapidFuzz (GPL→MIT reimpl)     14       8       2       0
   DERIVED  fuzzywuzzy→thefuzz (fork)     18      16       7       0
   INDEPENDENT  jellyfish↔textdistance     12      12      12       0
   ```

   PILOT-RESULTS.md:92 honestly says the independent control "false-positived at 12". This is a blocker only for any claim that §5.4 is validated or trustworthy now. SPECIFICATION.md:117 says "it is **not validated** until filtration completeness + baseline size are pre-registered", which is correct; the primary-measure claim must keep that limitation attached everywhere it is invoked.

7. Cross-language support is a design claim, not supported by the current harness code under review.

   SPECIFICATION.md:97 claims ST is "Cross-language capable" via "a language-agnostic normalized form", and SPECIFICATION.md:337 claims "The harness ships per-language AST walkers + a language-agnostic structural-descriptor layer".

   The actual pilot harness is Python-only. `pilot/pilot_harness.py:81-87` selects only files ending in `.py`: `out += [os.path.join(r, f) for f in fs if f.endswith('.py')]`. `pilot/structural.py:24-28` parses files with Python `ast.parse(open(p, 'rb').read())`. There are no per-language walkers or language-agnostic descriptors in the changed directory. Therefore the cross-language v0.6 claim is internally a future requirement, not something supported by the current code.

8. The copyleft-first-class input rule is not backed by any manifest, redistributed input corpus, or notice-preservation machinery in this directory.

   SPECIFICATION.md:6 claims benchmark inputs are redistributed "verbatim with its original license texts and notices preserved" and that the chardet v6/v7 pair "is included on these terms". SPECIFICATION.md:260 repeats that inputs are redistributed "verbatim, with all original license texts and notices preserved". SPECIFICATION.md:215-216 requires every input to carry source URL, tag, SHA, upstream license, redistribution mode, preserved notice files, accession date, size, and content hash in a validated MANIFEST.

   The actual pilot code uses external local source checkouts, not a manifest-backed redistributed corpus. `pilot/pilot_harness.py:41-44` hardcodes:

   ```python
   CHARDET = '/srv/repos/public/spec-poc/chardet-relicense/chardet'
   CSN = '/srv/repos/public/spec-poc/chardet-relicense/charset_normalizer'
   CORPUS = '/srv/repos/external/verivus-oss/agent-assurance-papers/chardet-relicense/proof-bundle/corpora/items'
   ```

   `pilot/residual.py:24-26` similarly hardcodes `CHARDET`, `CSN`, and `FZSRC = '/tmp/fzsrc'`. The changed-file list under review contains `SPECIFICATION.md`, `family-census.md`, `legal-framework.md`, `pilot/`, `power/`, and `spec-reviews/`; it does not contain the `benchmark/MANIFEST.schema.json`, preserved notices, or corpus files described in `SPECIFICATION.md:274-281`. The copyleft rule may be a future design requirement, but it is not evidenced by the current code/data.

   Actual existence check:

   ```text
   $ for p in Makefile validate benchmark/MANIFEST.schema.json benchmark; do if test -e "$p"; then echo "present $p"; else echo "absent $p"; fi; done
   absent Makefile
   absent validate
   absent benchmark/MANIFEST.schema.json
   absent benchmark
   ```

9. The no-drift / macro-bound publishing discipline is a specification promise, not implemented in the reviewed directory.

   SPECIFICATION.md:201-205 requires `make validate` to regenerate results and fail closed, and SPECIFICATION.md:318-319 makes that part of "done": "`make validate` exits 0" and every number is macro-bound to `results.json`. But the reviewed directory contains no `Makefile`, no `validate/`, no macro registry, and no manuscript renderer. The actual reproducible units are direct scripts (`pilot/pilot_harness.py`, `pilot/residual.py`, `power/power_analysis.py`) that write `pilot/results.json` and `power/results.json`.

   Actual existence check:

   ```text
   $ for p in Makefile validate benchmark/MANIFEST.schema.json benchmark; do if test -e "$p"; then echo "present $p"; else echo "absent $p"; fi; done
   absent Makefile
   absent validate
   absent benchmark/MANIFEST.schema.json
   absent benchmark
   ```

   This is not a defect in those scripts, but it is an unsupported doc claim if the corrective-program spec is read as describing the current artifact rather than future P1-P5 work.

Summary: the three requested scripts run, and many headline numbers reproduce. The blockers are overclaim and method mismatch: the spec overstates the pilot's "independent baseline" result, treats a non-equivalent WL variant as if it were a faithful contradiction, describes a fuller §5.4 and bootstrap procedure than the code implements, and claims cross-language/licensing/no-drift infrastructure that is not present in this changed directory.
