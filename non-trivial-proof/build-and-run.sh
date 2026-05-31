#!/usr/bin/env bash
# build-and-run.sh — build the hermetic proof image and reproduce everything.
#
# Assembles a minimal build context (the non-trivial-proof tree + the spec
# validators, which live in a sibling repo), builds the image, then runs it with
# the manuscript dir bind-mounted so the freshly-compiled main.pdf lands on the
# host. Prints the in-container Observed Execution and exits with its status.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"          # .../non-trivial-proof
PAPERS="$(cd "$HERE/.." && pwd)"                              # .../agent-assurance-papers
VALIDATORS="$(cd "$PAPERS/../agent-assurance/validators" && pwd)"
IMAGE="${IMAGE:-stateful-io-proof:latest}"

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

# proof + paper + witnesses (exclude VCS and regenerable build crud)
cp -r "$HERE" "$stage/non-trivial-proof"
rm -rf "$stage/non-trivial-proof/.git" 2>/dev/null || true
find "$stage/non-trivial-proof" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
# the spec validators (sibling repo) flattened under ./validators
mkdir -p "$stage/validators"
cp "$VALIDATORS"/*.py "$stage/validators/"
cp "$HERE/Containerfile" "$stage/Containerfile"

echo ">>> building $IMAGE (pinned toolchains + TeX; first build downloads ~hundreds of MB)"
podman build -t "$IMAGE" -f "$stage/Containerfile" "$stage"

echo ">>> running the reproduction (manuscript dir mounted for main.pdf output)"
podman run --rm --init --volume "$HERE/manuscript:/out:Z" "$IMAGE"
echo ">>> main.pdf -> $HERE/manuscript/main.pdf"
