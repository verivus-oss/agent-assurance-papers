UNCONDITIONAL APPROVAL

B1 verified against live files. `grep -rn "~8" SPECIFICATION.md pilot/PILOT-RESULTS.md` returned nothing. `pilot/PILOT-RESULTS.md:77` now reconciles "18 distinctive identifiers absent from csn (`resDom`)" to "13 remain (`resApi`, per `pilot/residual.py`)", consistent with live `python3 pilot/residual.py` output:

```text
DERIVED  v6->v7 (AI rewrite)            25      18      13       1
```

B2 verified against live file. The false "Renaming-invariant: names are never used for matching" claim is gone. The corrected `pilot/structural.py` module docstring states:

```text
8  NOT renaming-invariant (verification round 1): `build_call_graph` uses function
9  NAMES as node identity (`defined.add(n.name)`, edges by name), so the topology and
10 WL measures here are confounded by shared identifier vocabulary — the WL AUC=1.0 on
11 chardet is largely a name-vocabulary artifact, NOT a faithful WL kernel and NOT a
12 defensible structural signal (see PILOT-RESULTS.md envelope section + SPEC §5.2/§5.4).
13 Only `per_function_similarity`'s body-histogram is type-based (renaming-invariant);
14 the call-graph measures use names. The §7.3 invariance test is not implemented here.
```
