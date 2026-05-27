# arXiv Metadata

Title: Paraphrase-Resistant Detection of AI-Driven Code Rewrites: A Falsifiable Harness Applied to the chardet v6 to v7 Relicensing Dispute

Authors: Werner Kasselman

Primary category: `cs.SE`

Cross-list categories: none (account is endorsed for cs.SE only)

Comments: 27 pages, 3 figures; falsifiable detection harness for AI-driven code rewrites, applied to the chardet v6/v7 relicensing dispute. Code: https://github.com/verivus-oss/agent-assurance-papers Spec: https://github.com/verivus-oss/agent-assurance

License: Creative Commons Attribution 4.0 International (CC BY 4.0) — http://creativecommons.org/licenses/by/4.0/

Artifact repository (surfaced in Comments and in section "Reproducibility"): https://github.com/verivus-oss/agent-assurance-papers

Specification repository (surfaced in Comments and in section "Reproducibility"): https://github.com/verivus-oss/agent-assurance

Abstract:

In March 2026 the maintainer of the Python `chardet` library released version 7.0.0 as an MIT-licensed "ground-up rewrite," produced with an LLM-driven coding agent, of a codebase that had carried an LGPL licence since 2008. The relicensing drew objection immediately, with critics arguing that any rewrite informed by an LLM that had seen the original cannot be a clean-room reimplementation and therefore cannot strip the original's copyleft (an argument that is going to come up again, repeatedly, as more production codebases get the same treatment). I am not trying to adjudicate the chardet dispute, and this paper does not take a position on whether v7's relicensing is valid; what I am trying to do is move the conversation from assertion to evidence, by shipping a detection harness that produces six structural, falsifiable, reproducible signals comparing v6.0.0 and v7.0.0 of the library, five of which are explicitly designed to survive identifier renaming and module restructuring, and one of which (AUX1, the file-hash baseline) is retained as a continuity check with naive prior approaches. On the actual artefacts, literal source carryover is zero, v7's call-graph topology is 0.881 similar to v6's, the normalised AST control-flow histogram cosine is 0.984, three of five shared public-API signatures are byte-identical ("strict"), v7 imports a substantially different third-party dependency set (Jaccard 0.333), and the two versions never agree on encoding or confidence over 1000 random byte inputs. The combined picture is internally consistent but legally ambiguous, with the honest summary being that v7 preserves the *shape of v6's thinking* while replacing what v6 actually *does*. The contribution is the methodology and the bundle, not a verdict on chardet specifically (a self-contained, multi-LLM-reviewed artefact that any reviewer, lawyer, or court can re-run and inspect), sitting in a lineage of prior Verivus work on Verifiable AI Governance (the "AI You Can Prove" thesis, of which the DAG-TOML specification this proof bundle conforms to is the current open-source instantiation, and of which sqry, the AST-graph code-search tool used to corroborate the call-graph findings, is a sibling instantiation).
