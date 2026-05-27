#!/usr/bin/env bash
# Reproduce the JPlag comparison of chardet v6 vs v7 reported in
# Section 9 (Related Work, Tool Comparison subsection) of the paper.
#
# Output:
#   chardet-relicense/manuscript/figures/scripts/jplag_chardet_results.json  — top-pair similarities
#   chardet-relicense/manuscript/figures/scripts/jplag_options.json          — invocation options
#   chardet-relicense/manuscript/figures/scripts/jplag_runinfo.json          — JPlag version + execution time
#
# Requires:
#   - java (17+); tested with OpenJDK 25
#   - the chardet clone at CHARDET_REPO with tags 6.0.0 and 7.0.0
#   - network access to fetch the JPlag jar from GitHub Releases
#
# JPlag version pinned to v6.3.0 for reproducibility.

set -euo pipefail

CHARDET_REPO="${CHARDET_REPO:-/srv/repos/public/spec-poc/chardet-relicense/chardet}"
JPLAG_VERSION="${JPLAG_VERSION:-6.3.0}"
JPLAG_URL="https://github.com/jplag/JPlag/releases/download/v${JPLAG_VERSION}/jplag-${JPLAG_VERSION}-jar-with-dependencies.jar"

work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT

# Fetch the jar (one-time per work dir; in a real loop you'd cache it).
echo "fetching JPlag ${JPLAG_VERSION} ..."
curl -fsSL -o "${work}/jplag.jar" "${JPLAG_URL}"

# Materialise both tags as detached worktrees.
git -C "${CHARDET_REPO}" worktree add --detach --force "${work}/v6" 6.0.0 >/dev/null
git -C "${CHARDET_REPO}" worktree add --detach --force "${work}/v7" 7.0.0 >/dev/null

# JPlag expects one subdir per "submission" under a root. We submit the
# chardet/ implementation tree from v6 and the src/chardet/ implementation
# tree from v7 as two sibling submissions.
mkdir -p "${work}/submissions/chardet_v6" "${work}/submissions/chardet_v7"
cp -r "${work}/v6/chardet/."     "${work}/submissions/chardet_v6/"
cp -r "${work}/v7/src/chardet/." "${work}/submissions/chardet_v7/"

cd "${work}"

# Run JPlag. The Python3 grammar bundled in this JPlag release predates
# PEP 515 underscore numeric literals (e.g. `1_536`) used in v6's
# metadata/languages.py frequency tables. JPlag emits ANTLR parse errors
# on those data files but still completes the comparison; the token-level
# similarity is computed across all files JPlag could tokenize. We
# accept the parse-error noise on data files because the signal of
# interest is logic-file similarity, which JPlag tokenizes successfully.
java -jar jplag.jar -l python3 --mode RUN -r chardet_jplag_report submissions \
  >jplag_stdout.log 2>jplag_stderr.log || true

# Unpack the .jplag bundle (it's a ZIP).
unzip -o chardet_jplag_report.jplag -d report_extracted/ >/dev/null

# Copy results to the paper directory.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp report_extracted/topComparisons.json "${script_dir}/jplag_chardet_results.json"
cp report_extracted/options.json        "${script_dir}/jplag_options.json"
cp report_extracted/runInformation.json "${script_dir}/jplag_runinfo.json"

echo
echo "JPlag results captured to ${script_dir}/jplag_chardet_results.json:"
python3 -c "
import json, pathlib
with open('${script_dir}/jplag_chardet_results.json') as f:
    rows = json.load(f)
for r in rows:
    s = r['similarities']
    print(f\"  {r['firstSubmission']} vs {r['secondSubmission']}\")
    print(f\"    AVG similarity  : {s['AVG']:.6f}  ({s['AVG']*100:.3f}%)\")
    print(f\"    MAX similarity  : {s['MAX']:.6f}  ({s['MAX']*100:.3f}%)\")
    print(f\"    longest match   : {int(s['LONGEST_MATCH'])} tokens\")
"
