# User Prompts — Session Record

This file records the verbatim user messages from Werner Kasselman across
the conversation in which the proof bundle and this manuscript were
produced. It is included so that any reader can reconstruct exactly which
human instructions shaped which artefact, and trace any subsequent
implementation decision back to the directive that motivated it.

Format: each prompt is reproduced verbatim, prefixed by an ordinal index
and a short label naming the closest matching action the agent took in
response. Where the user attached a long technical specification (the
v1.0 layering plan, the multi-LLM review rules, the source-analysis
profile proposal), only the user-authored text is reproduced here; the
referenced files are present at their original repository paths.

The session occurred in the working directory
`/srv/repos/external/verivus-oss/agent-assurance` on 2026-05-22.

---

## 01 — Multi-LLM review rules, v1.0 layering plan

> ask codex/gemini/grok for a detailed review, provide each with full
> access permissions and mcp tool access, on every iteration if
> permission grant is not durabe (only check on progress once every 90
> seconds), provide the verification report used as the
> corrective-program spec; the exact commit/diff or changed-file list
> being reviewed; codex/gemini/grok must verify claims against code and
> docs, not accept Claude's summary as evidence. If Claude disagrees
> with a codex/gemini/grok finding, Claude must respond with
> code/doc evidence, not assertion. Iterate until codex/gemini/grok
> gives unconditional approval or lists a concrete blocker that cannot
> be resolved. Do not ask codex/gemini/grok to approve based on
> intent, plan compliance claims, or "should be fixed" language.
> Approval must be based on inspected code, tests, docs, and
> persistent review evidence.
>
> artifacts must be in the spec toml formal
>
> [followed by the four-PR plan: profile-descriptor kind, namespacing,
> confidentiality/license/embargo, provenance.encryption, plus pre-1.0
> cleanups and rollout sequence — reproduced verbatim in commit
> messages and CHANGELOG entries for the v1.0 layering work]

## 02 — Safe-language constraint

> the .py can stay. HOWEVER safe rust only and golang must be the
> primary validators

## 03 — Status check

> check the status now

## 04 — Cleanup direction

> carefully analyse the uncommited work. ensure we commit and keep
> everything safe and merged and retain consistency

## 05 — Path lookup

> find this document follow-up-2/15-source-analysis-profile-proposal.md

## 06 — Path lookup follow-up

> give me the complete path

## 07 — Proof concept

> create a "proof" that shows an example of the spec applied to code -
> lets consider a / the hello world example in rust, golang, c, ja,
> typescript

## 08 — Real-world target research

> use exa and search for publicized ai clean room rewrites so we can
> test this on a real product

## 09 — Recent-period scoping

> include everything up to May 2026

## 10 — Repository selection

> yes, but clone them into our /srv/repos/public folder under spec-poc

## 11 — Scope narrowing (via question answers)

> I only want to stick to chardet and its derivatives

(via the same answer turn:)

> ask codex/gemini/grok for a detailed review, provide each with full
> access permissions and mcp tool access, on every iteration if
> permission grant is not durabe (only check on progress once every 90
> seconds), provide the verification report used as the
> corrective-program spec; the exact commit/diff or changed-file list
> being reviewed; codex/gemini/grok must verify claims against code
> and docs, not accept Claude's summary as evidence. If Claude
> disagrees with a codex/gemini/grok finding, Claude must respond
> with code/doc evidence, not assertion. Iterate until codex/gemini/grok
> gives unconditional approval or lists a concrete blocker that
> cannot be resolved. Do not ask codex/gemini/grok to approve based
> on intent, plan compliance claims, or "should be fixed" language.
> Approval must be based on inspected code, tests, docs, and
> persistent review evidence.

## 12 — Critique of the v0.1 (shallow) proof

> I don't know how this really tests the spec, semantic ast "framing"

## 13 — Path selection — option 3

>   2. Replace C06a with real call-graph topology comparison
>      (sqry-driven) and add an import-edge contract. Medium effort.
>      Genuinely tests the AST framing on two of the five candidate
>      signals above. Drops the misleading framing.
>   3. Full rewrite to C05/C06 as the spec intended. Build all five
>      signals above against the chardet pair. This is the proof the
>      spec actually deserves.

## 14 — Headline question

> what is the headline finding?

## 15 — Paper directive

> launch a new opus agent. we need to create arXiv quality paper
> that explains this, provides proof, and makes it testable by others

## 16 — Multi-LLM review of the paper

> ask codex/gemini/grok for a detailed review, provide each with full
> access permissions and mcp tool access, on every iteration if
> permission grant is not durabe (only check on progress once every 90
> seconds), provide the verification report used as the
> corrective-program spec; the exact commit/diff or changed-file list
> being reviewed; codex/gemini/grok must verify claims against code
> and docs, not accept Claude's summary as evidence. If Claude
> disagrees with a codex/gemini/grok finding, Claude must respond
> with code/doc evidence, not assertion. Iterate until codex/gemini/grok
> gives unconditional approval or lists a concrete blocker that
> cannot be resolved. Do not ask codex/gemini/grok to approve based
> on intent, plan compliance claims, or "should be fixed" language.
> Approval must be based on inspected code, tests, docs, and
> persistent review evidence.

## 17 — Reviewer attribution requirement

> you also need to credit Codex AND Grok AND Gemini with attibution
>
> You also need to be CLEAR on what the human contributed

## 18 — Commit decision (option 2)

> 2

(in response to a question offering: 1=commit and push, 2=commit but
don't hold, 3=wait for Gemini.)

## 19 — PDF freshness check

> the creation date on the pdf doesnt seem to have changed

## 20 — Toolchain direction

> install it locally OR get a podman container

## 21 — Push hold

> hold for further review

## 22 — V2 revision directive (this round)

> this needs to be omitted - "Manuscript drafted by Claude Opus 4.7
> (Anthropic), via the Claude Code agent harness; executable
> artefacts and review process described in Section 9."
>
> this flows off the visible area in the paper - 2026-03-04 chardet
> #325 [5] GitHub user @gooba42: "Nullified License" — argues the
> LLM-generated rewrite cannot
>
> add that dag-toml is the current consideration and that the
> representation may change based on active research - 2.4 The
> DAG-TOML specification, in one page
>
> refer to prior work of Verivus - and verifiable AI governance
> [internal path redacted: Verivus consolidated workspace]
> extract the thesis, and dag-toml as the first 'attempt' at
> instantiating a specification, used on real code, you need to
> also include this in acknowledgements, also the work in sqry, the
> thesis about sqry indexing of code to make it 'understandable' for
> llm agents via structured AST and how that differs from
> semantically similar analysis
>
> apply [internal path redacted: werner-voice style guide] -
> HOWEVER - follow strict scienific research norms precedent.
> author one copy in my voice style and one copy in the default
> style that was applied
>
> these need thourough proof, validation, logical assertion of why
> this is applied (C06a) specifically
>
> these numbers must be validated by using python scientific and
> calculators coding tools, i.e. test the veracity of the llm
> generated results against public available statistical measures -
> clearly explain the other layers - how do we satisfy (like
> symbolic execution, data-flow analysis, or deep AST structural
> comparisons)
>
> We don't do enough work with sqry and sqry analysis of the code,
> that must be incorporated
>
> this is FALSE and contradicts the actual prompt and the latter
> assertions - (90-second polling, no permission auto-grants)
>
> you need to include all the prompts that I entered throughout the
> session

---

## Provenance of the Acknowledgments contributor list

The four LLM contributors listed in the Acknowledgments
(Claude Opus 4.7 as manuscript drafter and proof-bundle
implementer; Codex, Grok, and Gemini as iterative reviewers) were
named at the user's direct request in prompt 17 above. Their
individual roles, iteration counts, and what each caught are
documented at the level of detail the user required, with the
explicit Gemini quota-exhaustion gap labelled rather than omitted.

## Provenance of the verification-report mechanism

The corrective-program-spec mechanism (a TOML
\texttt{contract-declaration} listing the items reviewers must
verify, named verbatim in their prompts, with rejection language
explicitly forbidding intent-based or plan-compliance approvals)
was specified in prompts 01, 11, and 16 above. The same paragraph
appears in three different prompts in this session because the
user re-stated it to scope it to three different review subjects:
the v1.0 layering bundle (prompt 01), the proof-chardet-relicense
bundle (prompt 11), and this paper (prompt 16). The wording is
substantially identical across the three.
