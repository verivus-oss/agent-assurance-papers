#!/usr/bin/env bash
# detect.sh — the executable witness for chardet-relicense/proof-bundle/.
#
# Runs seven static-AST signals + one behavioural-fingerprint signal
# against checkouts of a SAME-DOMAIN PAIR of encoding-detector
# libraries. The pair to run is selected by a positional argument:
#
#   v6_v7            chardet 6.0.0 (LGPL) vs chardet 7.0.0 (MIT) — v1 headline pair
#   v5_v6            chardet 5.0.0 vs 6.0.0 — calibration: conventional same-project rewrite
#   v6_charset_norm  chardet 6.0.0 vs charset-normalizer (latest stable tag) —
#                    calibration: independent same-domain detector
#
# Signals:
#   AUX1   literal source carryover     (whitespace-normalised SHA-256)
#   C06a   call-graph topology          (degree distribution + SCC + density)
#   C06a'  call-graph WL kernel         (Weisfeiler-Lehman k=4, V2 R1 response)
#   C06b   import-edge set              (third-party Jaccard, R3/R4 audit)
#   C06c   control-flow histogram       (cosine similarity of normalised hist)
#   C06d   public-API signature equiv   (strict / renamed_args / diverged + per-method walker)
#   C06e   behavioural fingerprint      (multi-bucket realistic corpus +
#                                        1000-random-byte control; per-bucket
#                                        exact / bucket / normalized match
#                                        rates — one TSV row per bucket
#                                        plus an aggregate row)
#   C06f   per-function AST shape       (shape-matched pairs, V2 R16 response)
#
# Exit code:
#   0  no FAIL verdicts
#   1  one or more FAIL verdicts
#   2  prerequisite missing (repo not cloned, tags not fetched, etc.)
#
# Pair dispatch is a bash case statement (no extra dependencies). Adding
# a new pair = one stanza with REPO_A / TAG_A / PKG_A / MODULE_A and the
# same for side B. A `pairs.toml` would have been overkill here.
#
# Sandbox-compatibility: each side is cloned via `git clone --shared`
# into a writable tempdir before the worktree is added, so the upstream
# clone may live on a read-only mount.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat >&2 <<EOF
usage: detect.sh <pair_name>
  pair_name one of: v6_v7 | v5_v6 | v6_charset_norm
environment overrides:
  CHARDET_REPO              path to chardet clone (default /srv/repos/public/spec-poc/chardet-relicense/chardet)
  CHARSET_NORMALIZER_REPO   path to charset_normalizer clone (default sibling of CHARDET_REPO)
  RESULTS_ROOT              where to write per-pair TSV (default <here>/results)
EOF
}

# Default to the legacy pair when invoked without arguments so the v1
# reproduction step `bash detect.sh` keeps working byte-equivalently.
# `bash detect.sh -h` or `--help` still prints usage.
case "${1:-}" in
  -h|--help)
    usage; exit 0
    ;;
esac

pair="${1:-v6_v7}"

chardet_repo="${CHARDET_REPO:-/srv/repos/public/spec-poc/chardet-relicense/chardet}"
charset_norm_repo="${CHARSET_NORMALIZER_REPO:-/srv/repos/public/spec-poc/chardet-relicense/charset_normalizer}"
results_root="${RESULTS_ROOT:-${here}/results}"

# ----------------------------------------------------------------------
# Pair dispatch table.
# Each pair sets:
#   REPO_A, TAG_A, PKG_A, MODULE_A   (side A: AST package dir + runtime import)
#   REPO_B, TAG_B, PKG_B, MODULE_B   (side B)
# PKG_* drives extract_signals.py's C06b self-import filter and C06d
# __init__.py lookup. MODULE_* drives fingerprint_behavior.py's
# `import <name>` runner.
# ----------------------------------------------------------------------
case "${pair}" in
  v6_v7)
    REPO_A="${chardet_repo}"; TAG_A="${CHARDET_V6_TAG:-6.0.0}"; PKG_A="chardet"; MODULE_A="chardet"
    REPO_B="${chardet_repo}"; TAG_B="${CHARDET_V7_TAG:-7.0.0}"; PKG_B="chardet"; MODULE_B="chardet"
    ;;
  v5_v6)
    REPO_A="${chardet_repo}"; TAG_A="${CHARDET_V5_TAG:-5.0.0}"; PKG_A="chardet"; MODULE_A="chardet"
    REPO_B="${chardet_repo}"; TAG_B="${CHARDET_V6_TAG:-6.0.0}"; PKG_B="chardet"; MODULE_B="chardet"
    ;;
  v6_charset_norm)
    REPO_A="${chardet_repo}";       TAG_A="${CHARDET_V6_TAG:-6.0.0}";          PKG_A="chardet";            MODULE_A="chardet"
    REPO_B="${charset_norm_repo}";  TAG_B="${CHARSET_NORMALIZER_TAG:-3.4.7}";  PKG_B="charset_normalizer"; MODULE_B="charset_normalizer"
    ;;
  *)
    echo "error: unknown pair '${pair}'" >&2
    usage; exit 2
    ;;
esac

# ----------------------------------------------------------------------
# Pre-flight: both clones present, both tags resolvable.
# ----------------------------------------------------------------------
for repo in "${REPO_A}" "${REPO_B}"; do
  if [[ ! -d "${repo}/.git" ]]; then
    echo "error: repo not found at ${repo}" >&2
    exit 2
  fi
done
if ! git -C "${REPO_A}" rev-parse "${TAG_A}" >/dev/null 2>&1; then
  echo "error: tag '${TAG_A}' missing from ${REPO_A}" >&2; exit 2
fi
if ! git -C "${REPO_B}" rev-parse "${TAG_B}" >/dev/null 2>&1; then
  echo "error: tag '${TAG_B}' missing from ${REPO_B}" >&2; exit 2
fi

sha_a="$(git -C "${REPO_A}" rev-parse "${TAG_A}")"
sha_b="$(git -C "${REPO_B}" rev-parse "${TAG_B}")"

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

echo "proof-chardet-relicense: pair=${pair}"
echo "  side A: repo=${REPO_A} tag=${TAG_A} sha=${sha_a} pkg=${PKG_A}"
echo "  side B: repo=${REPO_B} tag=${TAG_B} sha=${sha_b} pkg=${PKG_B}"
echo

# Materialise writable --shared mirrors so worktree metadata lands in a
# writable .git directory even if the upstream clones are on read-only
# mounts. --shared symlinks the upstream objects/ so cost is trivial.
mirror_a="${tmp}/mirror_a"
git clone --quiet --shared "${REPO_A}" "${mirror_a}"
git -C "${mirror_a}" worktree add --detach --force "${tmp}/A" "${TAG_A}" >/dev/null

if [[ "${REPO_A}" == "${REPO_B}" ]]; then
  # Same repo, second worktree off the same mirror.
  git -C "${mirror_a}" worktree add --detach --force "${tmp}/B" "${TAG_B}" >/dev/null
else
  mirror_b="${tmp}/mirror_b"
  git clone --quiet --shared "${REPO_B}" "${mirror_b}"
  git -C "${mirror_b}" worktree add --detach --force "${tmp}/B" "${TAG_B}" >/dev/null
fi

# ----------------------------------------------------------------------
# Run static signals and behavioural fingerprint.
# ----------------------------------------------------------------------
static_out="$(python3 "${here}/extract_signals.py" \
  --root-a "${tmp}/A" --root-b "${tmp}/B" \
  --pkg-a  "${PKG_A}" --pkg-b  "${PKG_B}")"

mkdir -p "${results_root}/${pair}"
fingerprint_report_json="${results_root}/${pair}/c06e_report.json"
set +e
fingerprint_out="$(python3 "${here}/fingerprint_behavior.py" \
  --tree-a "${tmp}/A" --tree-b "${tmp}/B" \
  --module-a "${MODULE_A}" --module-b "${MODULE_B}" \
  --corpus-dir "${here}/corpora" \
  --report-json "${fingerprint_report_json}" 2>&1)"
set -e

# Assemble output: header + static rows (with C06e DELEGATED placeholder
# stripped) + real C06e row + SUMMARY.
combined_body="$(
  echo "${static_out}" | grep -v $'\tDELEGATED\t'
  echo "${fingerprint_out}"
)"

result_dir="${results_root}/${pair}"
mkdir -p "${result_dir}"

# Witness TSV
{
  echo "# pair: ${pair}"
  echo "# side_a: repo=${REPO_A} tag=${TAG_A} sha=${sha_a} pkg=${PKG_A} module=${MODULE_A}"
  echo "# side_b: repo=${REPO_B} tag=${TAG_B} sha=${sha_b} pkg=${PKG_B} module=${MODULE_B}"
  echo "${combined_body}"
} > "${result_dir}/witness.tsv"

# Witness JSON (manifest only — full per-row JSON synthesised by the
# multi-pair table builder downstream from the TSV).
cat > "${result_dir}/manifest.json" <<JSON
{
  "pair": "${pair}",
  "side_a": {"repo": "${REPO_A}", "tag": "${TAG_A}", "sha": "${sha_a}", "pkg": "${PKG_A}", "module": "${MODULE_A}"},
  "side_b": {"repo": "${REPO_B}", "tag": "${TAG_B}", "sha": "${sha_b}", "pkg": "${PKG_B}", "module": "${MODULE_B}"}
}
JSON

# Echo to stdout exactly as the v1 harness did, so existing graders see
# the same format.
echo "${combined_body}"

echo
echo "# SUMMARY"
echo "${combined_body}" | awk -F'\t' '
  NR == 1 || NF < 5 { next }
  { counts[$5]++ }
  END {
    for (verdict in counts) print verdict "\t" counts[verdict]
  }
' | sort -k2,2nr -k1,1 | awk -F'\t' '{ print "# " $1 ": " $2 }'

echo
echo "# witness written to ${result_dir}/witness.tsv"

if echo "${combined_body}" | awk -F'\t' 'NR > 1 && NF >= 5 && $5 == "FAIL" { exit 0 } END { exit 1 }'; then
  exit 1
fi
exit 0
