#!/usr/bin/env bash
# detect.sh — the executable witness for chardet-relicense/proof-bundle/.
#
# Runs five static-AST signals + one behavioural-fingerprint signal
# against checkouts of chardet at tags 6.0.0 (last LGPL-era) and 7.0.0
# (Dan Blanchard's AI-rewritten MIT release):
#
#   AUX1  literal source carryover     (whitespace-normalised SHA-256)
#   C06a  call-graph topology          (degree distribution + SCC + density)
#   C06b  import-edge set              (third-party Jaccard)
#   C06c  control-flow histogram       (cosine similarity of normalised hist)
#   C06d  public-API signature equiv   (strict / renamed_args / diverged)
#   C06e  behavioural fingerprint      (1000 deterministic fuzz inputs)
#
# Exit code:
#   0  no FAIL verdicts
#   1  one or more FAIL verdicts
#   2  prerequisite missing (repo not cloned, tags not fetched, etc.)
#
# Sandbox-compatibility: the upstream chardet clone may live in a
# read-only path (e.g. /srv/repos/public mounted read-only inside a
# reviewer sandbox). To keep the witness reproducible in such sandboxes,
# detect.sh creates a local --shared mirror of the upstream in a
# writable tempdir before adding the two worktrees. The mirror shares
# git objects with the upstream (so it costs effectively zero disk and
# zero network) but has its own writable .git/worktrees directory.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

chardet_repo="${CHARDET_REPO:-/srv/repos/public/spec-poc/chardet-relicense/chardet}"
v6_tag="${CHARDET_V6_TAG:-6.0.0}"
v7_tag="${CHARDET_V7_TAG:-7.0.0}"

if [[ ! -d "${chardet_repo}/.git" ]]; then
  echo "error: chardet repo not found at ${chardet_repo}" >&2
  echo "       set CHARDET_REPO=/path/to/chardet or run:" >&2
  echo "       git clone https://github.com/chardet/chardet.git ${chardet_repo}" >&2
  exit 2
fi
for tag in "${v6_tag}" "${v7_tag}"; do
  if ! git -C "${chardet_repo}" rev-parse "${tag}" >/dev/null 2>&1; then
    echo "error: chardet tag '${tag}' not found in ${chardet_repo}" >&2
    echo "       try: git -C ${chardet_repo} fetch --tags" >&2
    exit 2
  fi
done

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

echo "proof-chardet-relicense: extracting AUX1 + C06a..C06e signals"
echo "  repo:   ${chardet_repo}"
echo "  v6 tag: ${v6_tag}"
echo "  v7 tag: ${v7_tag}"
echo

# Materialise a writable --shared mirror of the upstream so worktree
# metadata lands in a writable .git directory even if the upstream
# clone is on a read-only mount. --shared symlinks the upstream's
# objects/ so this is cheap.
mirror="${tmp}/mirror"
git clone --quiet --shared "${chardet_repo}" "${mirror}"

# Add worktrees inside the writable mirror's .git/worktrees/.
git -C "${mirror}" worktree add --detach --force "${tmp}/v6" "${v6_tag}" >/dev/null
git -C "${mirror}" worktree add --detach --force "${tmp}/v7" "${v7_tag}" >/dev/null

# Capture both analysers' output, then emit a single combined SUMMARY
# computed across the full row set (Codex round-1 review finding:
# emitting the summary inside extract_signals.py undercounted C06e).
static_out="$(python3 "${here}/extract_signals.py" \
  --v6-root "${tmp}/v6" \
  --v7-root "${tmp}/v7")"

set +e
fingerprint_out="$(python3 "${here}/fingerprint_behavior.py" \
  --v6-tree "${tmp}/v6" \
  --v7-tree "${tmp}/v7" 2>&1)"
set -e

# Header + 5 static rows (extract_signals.py's DELEGATED placeholder is
# replaced by the real C06e row from fingerprint_behavior.py).
echo "${static_out}" | grep -v $'\tDELEGATED\t'

# Real C06e row.
echo "${fingerprint_out}"

# Combined SUMMARY computed from every data row (everything except
# the header line and any blank line). Verdict is column 5 (1-indexed)
# in tab-separated rows.
echo
echo "# SUMMARY"
{
  echo "${static_out}" | grep -v $'\tDELEGATED\t'
  echo "${fingerprint_out}"
} | awk -F'\t' '
  NR == 1 || NF < 5 { next }    # skip header + non-data lines
  { counts[$5]++ }
  END {
    for (verdict in counts) print verdict "\t" counts[verdict]
  }
' | sort -k2,2nr -k1,1 | awk -F'\t' '{ print "# " $1 ": " $2 }'

# Exit non-zero iff any FAIL row landed.
combined="$(echo "${static_out}" | grep -v $'\tDELEGATED\t'; echo "${fingerprint_out}")"
if echo "${combined}" | awk -F'\t' 'NR > 1 && NF >= 5 && $5 == "FAIL" { exit 0 } END { exit 1 }'; then
  exit 1
fi
exit 0
