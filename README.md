# Agent Assurance Papers

Publication material, proof bundles, and arXiv packaging workflow for
the DAG-TOML / Agent Assurance work. The sibling `agent-assurance/`
repository remains the public specification, validator, profile, and
minimal-example repository.

## Layout

```text
chardet-relicense/
  manuscript/     LaTeX paper package moved out of the spec repository
  proof-bundle/   Executable proof moved out of the spec repository

hello-world/
  manuscript/     LaTeX paper package moved out of the spec repository
  proof-bundle/   Executable proof moved out of the spec repository

arxiv-prep/       Generated arXiv staging/output workspace for the current submission
arxiv-prep-agent-dag.toml
                  DAG-TOML workflow for arXiv TeX pre-flight and packaging
```

## Validation

Run these from this repository root, with the sibling `agent-assurance/`
checkout available at `../agent-assurance/`:

```sh
python3 ../agent-assurance/validators/validate_implementation_dag.py \
  arxiv-prep-agent-dag.toml

python3 ../agent-assurance/validators/validate_implementation_dag.py \
  hello-world/proof-bundle/implementation_dag.toml
python3 ../agent-assurance/validators/validate_traceability.py \
  hello-world/proof-bundle/traceability.toml --repo-root . --check-paths-exist
python3 ../agent-assurance/validators/validate_review_readiness.py \
  hello-world/proof-bundle/review_readiness.toml
python3 ../agent-assurance/validators/validate_review_readiness.py \
  hello-world/proof-bundle/contract_declaration.toml
python3 ../agent-assurance/validators/validate_review_readiness.py \
  hello-world/proof-bundle/evidence_matrix.toml

python3 ../agent-assurance/validators/validate_implementation_dag.py \
  chardet-relicense/proof-bundle/implementation_dag.toml
python3 ../agent-assurance/validators/validate_traceability.py \
  chardet-relicense/proof-bundle/traceability.toml --repo-root . --check-paths-exist
python3 ../agent-assurance/validators/validate_review_readiness.py \
  chardet-relicense/proof-bundle/review_readiness.toml
python3 ../agent-assurance/validators/validate_review_readiness.py \
  chardet-relicense/proof-bundle/contract_declaration.toml
python3 ../agent-assurance/validators/validate_review_readiness.py \
  chardet-relicense/proof-bundle/evidence_matrix.toml
```

The proof witness scripts are run from this repository root:

```sh
bash hello-world/proof-bundle/run_all.sh
bash hello-world/proof-bundle/detect_awk_rewrite.sh
bash hello-world/proof-bundle/detect_semantic_rewrite.sh
```
