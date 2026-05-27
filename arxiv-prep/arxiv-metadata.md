# arXiv Metadata

Title: A Minimal Executable Proof for Multi-Language Contract Traceability

Authors: Werner Kasselman

Primary category: `cs.SE`

Cross-list categories: none

Comments: 8 pages, 0 figures; executable artifact report. Code: https://github.com/verivus-oss/agent-assurance-papers Spec: https://github.com/verivus-oss/agent-assurance

License: Creative Commons Attribution 4.0 International (CC BY 4.0) — http://creativecommons.org/licenses/by/4.0/

Artifact repository (surfaced in Comments and in section "arXiv and Artifact Packaging Notes"): https://github.com/verivus-oss/agent-assurance-papers

Specification repository (surfaced in Comments and in section "arXiv and Artifact Packaging Notes"): https://github.com/verivus-oss/agent-assurance

Abstract:

This paper reports a deliberately small executable proof for a DAG-TOML contract: six "Hello, world!" implementations in Rust, Go, C, Java, TypeScript, and AWK are linked to one observable-output contract, one implementation DAG, one traceability file, one readiness gate, and one evidence matrix. The load-bearing contract requires the exact UTF-8 byte sequence `Hello, world!\n`, zero stderr bytes, and exit code 0. On the runner used for this paper, the witness harness reported five PASS outcomes, one SKIP for Java because `javac/java` was not on `PATH`, and zero FAIL outcomes. Two sidecar witnesses exercise narrower source-analysis claims: a convoluted Go rewrite hides the contiguous greeting literal but remains visible to sqry at the declared AST symbol and simple-edge level, while an indirect AWK rewrite uses a declared source profile because AWK is not in the repository's sqry-backed validator language set. The contribution is not a benchmark, a claim of general semantic equivalence, or a production assurance system. It is a compact, falsifiable artifact that shows how a contract, implementation graph, traceability chain, and review gate can be checked against executable witnesses.
