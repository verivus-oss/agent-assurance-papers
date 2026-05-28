#!/usr/bin/env bash
# gen_figures.sh — materialise the chardet v5/v6/v7 + charset_normalizer
# worktrees and invoke gen_figures.py so the paper's figures are
# reproduced from the exact same source the proof's signals run against.
#
# v2 update (Phase 2 / Agent K): Figure 2 now panels the C06a topology
# features across three calibration pairs (v6/v7, v5/v6,
# v6/charset_normalizer), so this wrapper now materialises four
# worktrees instead of two. Figures 1 and 3 are unchanged.
#
# Honours CHARDET_REPO, CHARSET_NORMALIZER_REPO and CHARDET_V5_TAG /
# CHARDET_V6_TAG / CHARDET_V7_TAG / CHARSET_NORMALIZER_TAG. Defaults
# match proof-bundle/detect.sh's pair dispatch (5.0.0 / 6.0.0 / 7.0.0
# / 3.4.7).

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
out_dir="$(cd "${here}/.." && pwd)"

chardet_repo="${CHARDET_REPO:-/srv/repos/public/spec-poc/chardet-relicense/chardet}"
csn_repo="${CHARSET_NORMALIZER_REPO:-/srv/repos/public/spec-poc/chardet-relicense/charset_normalizer}"
v5_tag="${CHARDET_V5_TAG:-5.0.0}"
v6_tag="${CHARDET_V6_TAG:-6.0.0}"
v7_tag="${CHARDET_V7_TAG:-7.0.0}"
csn_tag="${CHARSET_NORMALIZER_TAG:-3.4.7}"

if [[ ! -d "${chardet_repo}/.git" ]]; then
  echo "error: chardet repo not found at ${chardet_repo}" >&2
  echo "       set CHARDET_REPO or run:" >&2
  echo "       git clone https://github.com/chardet/chardet.git ${chardet_repo}" >&2
  exit 2
fi
if [[ ! -d "${csn_repo}/.git" ]]; then
  echo "error: charset_normalizer repo not found at ${csn_repo}" >&2
  echo "       set CHARSET_NORMALIZER_REPO or run:" >&2
  echo "       git clone https://github.com/jawah/charset_normalizer.git ${csn_repo}" >&2
  exit 2
fi

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

mirror="${tmp}/mirror"
git clone --quiet --shared "${chardet_repo}" "${mirror}"
git -C "${mirror}" worktree add --detach --force "${tmp}/v5" "${v5_tag}" >/dev/null
git -C "${mirror}" worktree add --detach --force "${tmp}/v6" "${v6_tag}" >/dev/null
git -C "${mirror}" worktree add --detach --force "${tmp}/v7" "${v7_tag}" >/dev/null

csn_mirror="${tmp}/csn_mirror"
git clone --quiet --shared "${csn_repo}" "${csn_mirror}"
git -C "${csn_mirror}" worktree add --detach --force "${tmp}/csn" "${csn_tag}" >/dev/null

python3 "${here}/gen_figures.py" \
  --v5-root "${tmp}/v5" \
  --v6-root "${tmp}/v6" \
  --v7-root "${tmp}/v7" \
  --csn-root "${tmp}/csn" \
  --out-dir "${out_dir}"
