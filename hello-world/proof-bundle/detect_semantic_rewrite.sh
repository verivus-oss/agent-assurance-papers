#!/usr/bin/env bash
# detect_semantic_rewrite.sh — show that a source rewrite can hide from
# token-level inspection while still exposing AST-level symbols.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${here}/../.." && pwd)"
target_rel="hello-world/proof-bundle/src/go_convoluted/hello.go"
target="${repo_root}/${target_rel}"

passes=0
skips=0
fails=0

pass() {
  printf '  PASS  %s\n' "$1"
  passes=$((passes+1))
}

skip() {
  printf '  SKIP  %s\n' "$1"
  skips=$((skips+1))
}

fail() {
  printf '  FAIL  %s\n' "$1"
  fails=$((fails+1))
}

echo "proof-hello-world: semantic AST rewrite witness"
echo

if command -v rg >/dev/null 2>&1; then
  literal_search=(rg -n 'Hello, world!' "${target}")
else
  literal_search=(grep -n 'Hello, world!' "${target}")
fi

if "${literal_search[@]}" >/dev/null 2>&1; then
  fail "convoluted source still contains the plain greeting literal"
else
  pass "plain greeting literal is absent from source text"
fi

if command -v go >/dev/null 2>&1; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp:-}" "${sqry_tmp:-}"' EXIT
  # Materialise C01's exact 14-byte expected stdout (Hello, world!\n)
  # and check the convoluted Go implementation byte-exactly with cmp,
  # plus stderr-size for zero bytes. Matches the C01 trio enforced by
  # hello-world/proof-bundle/run_all.sh.
  printf 'Hello, world!\n' > "${tmp}/expected"
  set +e
  go run "${target}" >"${tmp}/out" 2>"${tmp}/err"
  code=$?
  set -e
  if [[ "${code}" == "0" ]] && cmp -s "${tmp}/out" "${tmp}/expected" && [[ ! -s "${tmp}/err" ]]; then
    pass "convoluted implementation still satisfies CONTRACT C01 (cmp-equal, exit 0, stderr 0 bytes)"
  else
    fail "convoluted implementation diverged from CONTRACT C01 (exit=${code}; cmp returned $(cmp -s "${tmp}/out" "${tmp}/expected" && echo equal || echo differ); stderr=$(wc -c < "${tmp}/err") bytes)"
  fi
else
  skip "go not on PATH; runtime equivalence not checked"
fi

if command -v sqry >/dev/null 2>&1; then
  sqry_tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp:-}" "${sqry_tmp:-}"' EXIT
  if ! sqry index --force "${repo_root}" >"${sqry_tmp}/sqry-index.out" 2>"${sqry_tmp}/sqry-index.err"; then
    skip "sqry index failed; AST symbol check not performed"
    echo
    echo "summary: ${passes} pass, ${skips} skip, ${fails} fail"
    exit $(( fails > 0 ? 1 : 0 ))
  fi
  sqry query --validate off --limit 50 \
    "lang:go AND kind:function" \
    "${repo_root}" >"${sqry_tmp}/symbols.txt" 2>"${sqry_tmp}/sqry.err"

  for symbol in concealedBytes renderLine emit main; do
    if grep -Eq "(^|[^[:alnum:]_])${symbol}([^[:alnum:]_]|$)" "${sqry_tmp}/symbols.txt"; then
      pass "sqry resolved AST function symbol: ${symbol}"
    else
      fail "sqry did not resolve AST function symbol: ${symbol}"
    fi
  done

  sqry query --validate off --limit 20 \
    "callers:renderLine" \
    "${repo_root}" >"${sqry_tmp}/callers-renderLine.txt" 2>"${sqry_tmp}/callers-renderLine.err"
  if grep -Eq 'function main$' "${sqry_tmp}/callers-renderLine.txt"; then
    pass "sqry resolved caller edge: main -> renderLine"
  else
    fail "sqry did not resolve caller edge: main -> renderLine"
  fi

  sqry query --validate off --limit 20 \
    "imports:fmt" \
    "${repo_root}" >"${sqry_tmp}/imports-fmt.txt" 2>"${sqry_tmp}/imports-fmt.err"
  if grep -Eq 'import fmt$' "${sqry_tmp}/imports-fmt.txt"; then
    pass "sqry resolved import edge: fmt"
  else
    fail "sqry did not resolve import edge: fmt"
  fi
else
  skip "sqry not on PATH; AST symbol check not performed"
fi

echo
echo "summary: ${passes} pass, ${skips} skip, ${fails} fail"
exit $(( fails > 0 ? 1 : 0 ))
