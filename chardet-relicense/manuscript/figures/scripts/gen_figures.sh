#!/usr/bin/env bash
# gen_figures.sh — materialise the chardet v6 + v7 worktrees and invoke
# gen_figures.py so the paper's figures are reproduced from the exact
# same source the proof's signals run against.
#
# Honours CHARDET_REPO (default: the path the proof bundle's detect.sh
# uses) and CHARDET_V6_TAG / CHARDET_V7_TAG (default: 6.0.0 / 7.0.0).

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
out_dir="$(cd "${here}/.." && pwd)"

chardet_repo="${CHARDET_REPO:-/srv/repos/public/spec-poc/chardet-relicense/chardet}"
v6_tag="${CHARDET_V6_TAG:-6.0.0}"
v7_tag="${CHARDET_V7_TAG:-7.0.0}"

if [[ ! -d "${chardet_repo}/.git" ]]; then
  echo "error: chardet repo not found at ${chardet_repo}" >&2
  echo "       set CHARDET_REPO or run:" >&2
  echo "       git clone https://github.com/chardet/chardet.git ${chardet_repo}" >&2
  exit 2
fi

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

mirror="${tmp}/mirror"
git clone --quiet --shared "${chardet_repo}" "${mirror}"
git -C "${mirror}" worktree add --detach --force "${tmp}/v6" "${v6_tag}" >/dev/null
git -C "${mirror}" worktree add --detach --force "${tmp}/v7" "${v7_tag}" >/dev/null

python3 "${here}/gen_figures.py" \
  --v6-root "${tmp}/v6" \
  --v7-root "${tmp}/v7" \
  --out-dir "${out_dir}"
