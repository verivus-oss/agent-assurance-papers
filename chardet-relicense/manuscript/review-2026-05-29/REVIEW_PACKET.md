# Review packet — chardet-relicense manuscript veracity fixes (2026-05-29)

## Subject under review

Working-tree changes to **`chardet-relicense/manuscript/main.tex`** (the arXiv
manuscript), plus two regenerated derived artifacts:
- `chardet-relicense/manuscript/main.pdf` (rebuilt from the edited `main.tex`)
- `chardet-relicense/manuscript/arxiv_submission_bundle.tar.gz` (repackaged with the edited `main.tex`)

Base commit (HEAD): `6dfade93a121797d2b6a54459c5ede8a204b13df`
Exact diff under review: **`review-2026-05-29/main.tex.diff`** (261 lines, `git diff HEAD -- main.tex`).
You may also regenerate it yourself:
`git -C /srv/repos/external/verivus-oss/agent-assurance-papers diff HEAD -- chardet-relicense/manuscript/main.tex`

These edits correct **prose, stale enumerations, one wrong digest, and a
self-contradicting conclusion**. The claim is that **none of them altered a
harness-derived number** — they only made the manuscript consistent with its
own ground-truth artifacts and its own v2 thesis.

## Your role and the rules of engagement

You are an independent reviewer with full filesystem and MCP-tool access to this
repository. Verify against source. **Do not accept this packet's summary, or the
author's claims, as evidence.** Every verdict you issue must be backed by a file
path and line/field you inspected yourself.

1. For each CLAIM below, open the cited ground-truth artifact and the cited
   `main.tex` location and confirm the post-edit text matches the artifact.
2. A fix is only "verified" if the **new** prose matches the ground-truth data
   **and** the **old** prose (see the diff) did not. Check both sides.
3. If you find a defect, state it as a concrete blocker: the file, the line, the
   exact wrong token, and the correct value from the artifact.
4. Do **not** approve based on intent, plan-compliance, or "should be fixed"
   language. Approve only on inspected text + inspected artifact.
5. Output a per-CLAIM verdict table (PASS / FAIL with evidence), then a final
   line: either `UNCONDITIONAL APPROVAL` or `BLOCKER: <concrete description>`.

## Corrective-program spec (the contract this review is held to)

The governing spec is the bundle's verification report and the paper's
load-bearing invariant (see `chardet-relicense/CLAUDE.md`):

> Every number in the paper is taken **verbatim** from a single run of the proof
> harness. Do not edit a number to "fix" it.

- `chardet-relicense/proof-bundle/verification_report.toml` — the V01–V15 contract set.
- `chardet-relicense/manuscript/verification-report-2026-05-28-v2.md` — v2 verification narrative.
- The canonical post-integration numbers: `chardet-relicense/manuscript/v2-numeric-shifts.md` §7.

The corrective-program test for THIS review: **does each edited sentence now
agree with the witness/validation artifacts, without changing any number that
the artifacts pin?**

## Ground-truth artifacts (verify against these, not against prose)

- Witness TSVs (the single source of every signal number):
  - `chardet-relicense/proof-bundle/results/v6_v7/witness.tsv`
  - `chardet-relicense/proof-bundle/results/v5_v6/witness.tsv`
  - `chardet-relicense/proof-bundle/results/v6_charset_norm/witness.tsv`
- `chardet-relicense/manuscript/figures/scripts/validation_report.v2.json`
  (bootstrap CIs, `corpus_digest_manifest`)
- `chardet-relicense/manuscript/figures/scripts/jplag_chardet_results.json` (JPlag numbers)
- `chardet-relicense/manuscript/figures/scripts/c06b_imports_audit.tex` (C06b R1–R5 classification)
- `chardet-relicense/manuscript/figures/scripts/multi_pair_comparison.tex` (the calibration table, \input by main.tex)

## Claims to verify (each is one edit in main.tex.diff)

**C1 — Conclusion rewritten to match the v2 thesis.** OLD conclusion asserted
"third-party dependency boundary is genuinely different" and "v7 preserves the
shape of v6's thinking". VERIFY: the abstract (`main.tex` ~line 117) says the
C06b "external boundary is genuinely different" framing **inverts**, and
§Interpretation (~line 1086) says the "preserves the shape of v6's thinking"
reading "does not survive the calibration". Confirm the NEW conclusion no longer
contradicts those, and that the old contradicting sentences are gone (grep
`main.tex` for "genuinely different" and "shape of v6's thinking" — every
remaining hit must be in a retraction context, not an assertion).

**C2 — corpus digest `58e54831f84183c7` → `c37637f0956d7a7e`.** VERIFY: the
witness TSVs' C06e aggregate row field `corpus_digest=` and
`validation_report.v2.json` field `corpus_digest_manifest` both equal
`c37637f0956d7a7e`. Confirm `58e54831f84183c7` no longer appears anywhere in
`main.tex`. (Note `58e5…` is the stale v1 random-only digest; it still legitimately
appears in the OLD `validation_report.json` — that file is not under review.)

**C3 — C06b attribution corrected.** OLD prose attributed v6/v7's Jaccard rise
to keeping `setuptools, sphinx_rtd_theme`. VERIFY against
`c06b_imports_audit.tex` and the v6/v7 witness `import_edge_set` row: the v6/v7
shared third-party set is `{cchardet, datasets}` (Jaccard 2/3 = 0.667), v7-only
is `charset_normalizer`. `setuptools`/`sphinx_rtd_theme` appear only in the
**v5/v6** pair (as `v6_only`). Confirm NEW prose credits `datasets`, not
setuptools/sphinx.

**C4 — JPlag file-count sentence.** OLD prose said "84 v6 .py files … higher than
the extractor's 87" (84 < 87, contradiction). VERIFY: extractor v6 file count is
87 (AUX1 row of all three witness TSVs shows "87 v6"), v7 is 33. Confirm NEW
prose no longer claims 84 > 87 and is directionally consistent. JPlag raw numbers
(AVG 3.75e-4 ≈ 0.04%, MAX 0.01296 ≈ 1.30%, LONGEST 18, length 247026) are in
`jplag_chardet_results.json` and must be UNCHANGED in the table (`tab:jplag-vs-c06`).

**C5 — sqry node-count sentence.** OLD prose said v7 has "more edges (659) on a
smaller node count (358)". VERIFY against the v6/v7 witness C06a row:
v6_nodes=342, v7_nodes=358, v6_edges=488, v7_edges=659 — so 358 > 342 (v7 is
NOT smaller on the C06a graph). Confirm NEW prose calls it a denser graph at a
comparable node count and reconciles with the sqry whole-graph counts (Table
`tab:sqry`: v6 7947 nodes, v7 4292) without asserting 358 < 342.

**C6 — "v7 doubles … Return".** OLD prose claimed v7 doubles Return/For/Try/
ExceptHandler. VERIFY against v6/v7 witness C06c evidence: Return 191→253
(≈ +32%, NOT doubled); For 72→135, Try 12→33, ExceptHandler 12→32 (≈ ×1.9–2.7).
Confirm NEW prose no longer says Return doubles.

**C7 — signal-count consistency sweep (v1→v2).** The paper has eight signals
(AUX1 + C06a, C06a′, C06b, C06c, C06d, C06e, C06f). VERIFY there are no remaining
stale "six signals", "six-signal", "five C06 signals", "seven-line TSV", or
"C06a..C06e" claims in `main.tex` (grep). Confirm the determinism list (~line 964)
now includes C06a′ and C06f, and the reproducibility gate (~line 1627) lists all
seven C06 signals.

**C8 — NO NUMBER CHANGED, AND ALL MATH IS PROVABLE.** The strongest check: every
numeric token in the diff's `+` lines must already be present in a ground-truth
artifact, OR be an exact arithmetic derivation of one. Confirm the diff
introduces no new numeric value that is not in the witness TSVs /
validation_report.v2.json / jplag JSON. Headline values to re-confirm are
unchanged in `tab:results` and `tab:multi-pair-calibration`: C06a 0.881/0.930/0.922,
C06a′ 0.587/0.902/0.872, C06b 0.667/0.250/0.000, C06c 0.984/0.995/0.999,
C06e random 0.000/0.968/0.000, realistic 0.625/0.688/0.594, C06f 0.913@17.5% /
0.982@64.0% / 0.796@43.5%.

ROUND-1 RESOLUTION (Codex): the conclusion previously wrote the match rate as
`(17.5\%)`. `17.5` is not a literal token in any artifact — it is the exact
percentage of the witness value `matched/v6=31/177` (31/177 = 17.51% → 17.5%),
and it already appears at HEAD in the abstract (`main.tex:99`) and Table 1
(`main.tex:1074`) as `31/177=17.5\%`. The conclusion now writes
`($31/177=17.5\%$)`, matching the paper's own convention and putting the verbatim
witness fraction in the sentence. Verify the conclusion token is `31/177=17.5\%`.

**C11 — ALL MATH IS PROVEN BY A DETERMINISTIC MODULE.** Run
`python3 review-2026-05-29/proof_numbers.py` and confirm it exits 0 with
"ALL NUMERIC CLAIMS PROVEN". This script uses ONLY deterministic stdlib math
(`fractions.Fraction`, `decimal.Decimal` with ROUND_HALF_UP) — no float
`round()`, no RNG, no network. INSPECT the script: confirm every base value is
PARSED from a witness TSV / JSON artifact (not hard-coded from prose) and every
derived figure (percentages, Jaccard = |shared|/|union|, growth ratios, digest
equality) is computed and asserted against the token parsed from `main.tex`. A
PASS here means the math is reproducible, not merely asserted. If you believe any
check is circular or mis-parses an artifact, name the line of `proof_numbers.py`
and the artifact field it should read instead.

ROUND-2/3 RESOLUTION (Codex): earlier revisions of the script compared an
artifact-derived value against a hard-coded expected literal (e.g. the calibration
table `"0.881"`, then JPlag `Decimal("0.04")`, `18`, `Decimal("17.5")`). All such
literals are now removed: every check parses the DISPLAYED token from `main.tex`
or the rendered `multi_pair_comparison.tex` AND the base value from a witness/JSON
artifact, asserts `displayed == computed`, and even takes rounding precision from
the displayed token's own exponent. The only bare numeric constants left are the
three labeled qualitative-threshold ratios in the C06c block (`4/3`, `1/20`,
`9/5`) that encode the prose claims "about a third" / "roughly doubles". Confirm
by grep that no `Decimal("<number>")` value literal remains.

**C9 — build integrity.** The edited `main.tex` compiles. VERIFY by building
(TeX Live is available via `podman run --rm -v <repo>:/work:z -w /work/chardet-relicense/manuscript ghcr.io/xu-cheng/texlive-full:latest sh -c 'pdflatex -interaction=nonstopmode -halt-on-error main.tex && bibtex main && pdflatex ... && pdflatex ...'`).
Confirm no errors, no Undefined-reference / Undefined-citation warnings. Author
reports: 31 pages, clean. Re-derive independently.

**C10 — bundle propagation.** VERIFY `arxiv_submission_bundle.tar.gz`'s `main.tex`
member is byte-identical to the edited working-tree `main.tex`
(`tar xzO … main.tex | diff - main.tex`), and the other members (references.bib,
multi_pair_comparison.tex, fig1/2/3/5) are unchanged from HEAD.

## Output format

```
| Claim | Verdict | Evidence (file:line / field inspected) |
| C1 | PASS/FAIL | ... |
...
| C11 | PASS/FAIL | proof_numbers.py exit code + inspection note |

FINAL: UNCONDITIONAL APPROVAL
   — or —
FINAL: BLOCKER: <file>:<line> <wrong token> should be <artifact value from ...>
```
