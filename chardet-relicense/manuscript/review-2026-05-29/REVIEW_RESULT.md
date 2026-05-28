# Multi-LLM review result — chardet-relicense manuscript veracity fixes

Date: 2026-05-29. Base commit (HEAD): `6dfade93a121797d2b6a54459c5ede8a204b13df`.
Subject: working-tree edits to `chardet-relicense/manuscript/main.tex` (+ regenerated
`main.pdf` and `arxiv_submission_bundle.tar.gz`).
Corrective-program spec: `proof-bundle/verification_report.toml`,
`manuscript/verification-report-2026-05-28-v2.md`, and the load-bearing invariant in
`CLAUDE.md` ("every number taken verbatim from a single harness run").
Packet + diff + deterministic proof: this directory (`REVIEW_PACKET.md`,
`main.tex.diff`, `proof_numbers.py`).

Three independent LLM CLI reviewers, each run with full filesystem access, MCP tools
(sqry, exa, ref_tools), and a verify-against-source mandate (no summaries accepted as
evidence). Permission posture: Codex `--dangerously-bypass-approvals-and-sandbox`;
Gemini `--yolo --skip-trust`; Grok `--bypassPermissions --always-approve`.

## Outcome by round (claims C1–C11; see REVIEW_PACKET.md)

| Round | Gemini | Grok | Codex | Action taken |
|------|--------|------|-------|--------------|
| 1 | APPROVE | APPROVE | BLOCKER C8 | conclusion `(17.5\%)` → `($31/177=17.5\%$)` (verbatim witness fraction; 17.5% already at abstract:99, table:1074) |
| 2 | APPROVE | APPROVE | BLOCKER C11 | `proof_numbers.py` parsed displayed calibration tokens from `multi_pair_comparison.tex` instead of hard-coded expecteds |
| 3 | APPROVE | APPROVE | BLOCKER C11 | removed remaining hard-coded JPlag/`17.5` literals; precision now taken from the displayed token |
| 4 | APPROVE | APPROVE | APPROVE | — (final, identical state) |

Every Codex blocker was legitimate (and rounds 2–3 caught a gap the other two
reviewers missed) and was resolved with a code/doc-backed change, never an assertion.

## Final verdict (round 4, identical artifact state)

- **Codex — FINAL: UNCONDITIONAL APPROVAL** (C1–C11 PASS; ran `proof_numbers.py`
  → 59 checks 0 failed; `grep 'Decimal("[0-9]'` no hits; bundle `main.tex`
  SHA-256 `a39a68407903950413736fb9f794508e9e7c0ed3f470a145d9e4a4b4b0bd0946`
  equals working tree). job `819f367e-eaed-466d-bf72-c9593d539ee8`.
- **Gemini — FINAL: UNCONDITIONAL APPROVAL** (C1–C11 PASS; build 34 pages clean).
  job `96cb5d24-b4ef-4e95-9b0f-93a5c6f0a03c`.
- **Grok — FINAL: UNCONDITIONAL APPROVAL** (C1–C11 PASS; re-read full proof script,
  confirmed non-circular, no hard-coded expecteds). job `911e75ef-eaaf-4eab-8fa5-66c3099491b5`.

## What was verified

C1 conclusion now matches the v2 thesis (no v1 contradiction); C2 corpus digest
`c37637f0956d7a7e` (witness == validation_report == main.tex; stale `58e5…` gone);
C3 C06b rise credited to `datasets` (shared `{cchardet,datasets}`), not
setuptools/sphinx; C4 JPlag file-count contradiction removed, raw JPlag numbers
unchanged; C5 C06a node/edge phrasing correct (v7 denser, not "smaller"); C6 "Return
rises ~⅓, others ~double" matches witness counts; C7 eight-signal consistency sweep;
C8 no harness number changed; C9 LaTeX build clean (34 pp, no undefined refs/cites);
C10 bundle propagation byte-identical; C11 deterministic proof (`proof_numbers.py`,
fractions.Fraction + decimal.Decimal, 59 checks, displayed-token-vs-artifact, no
hard-coded expecteds).
