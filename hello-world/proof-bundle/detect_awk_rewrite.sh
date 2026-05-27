#!/usr/bin/env bash
# detect_awk_rewrite.sh — show that a constrained AWK rewrite can hide
# the greeting literal while still exposing a declared static profile.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${here}/../.." && pwd)"
target="${repo_root}/hello-world/proof-bundle/src/awk_convoluted/hello.awk"
canonical="${repo_root}/hello-world/proof-bundle/src/awk/hello.awk"
contract="${repo_root}/hello-world/proof-bundle/contract_declaration.toml"

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

echo "proof-hello-world: AWK rewrite detection witness"
echo

if command -v rg >/dev/null 2>&1; then
  literal_search=(rg -n 'Hello, world!' "${target}")
else
  literal_search=(grep -n 'Hello, world!' "${target}")
fi

if "${literal_search[@]}" >/dev/null 2>&1; then
  fail "AWK rewrite still contains the plain greeting literal"
else
  pass "plain greeting literal is absent from AWK rewrite source"
fi

if grep -q 'id          = "C06"' "${contract}" &&
   grep -q 'TEST:hello-world-proof::awk-rewrite-detection' "${contract}"; then
  pass "contract_declaration.toml declares C06 and its witness"
else
  fail "contract_declaration.toml does not declare C06 and its witness"
fi

if command -v awk >/dev/null 2>&1; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp:-}"' EXIT

  set +e
  # Materialise C01's exact 14-byte expected stdout (Hello, world!\n)
  # and check both the canonical AWK implementation and the convoluted
  # rewrite byte-exactly with cmp, plus stderr-size for zero bytes.
  # Matches the C01 trio enforced by hello-world/proof-bundle/run_all.sh.
  printf 'Hello, world!\n' > "${tmp}/expected"

  awk -f "${canonical}" >"${tmp}/canonical.out" 2>"${tmp}/canonical.err"
  canonical_code=$?
  set -e
  if [[ "${canonical_code}" == "0" ]] && cmp -s "${tmp}/canonical.out" "${tmp}/expected" && [[ ! -s "${tmp}/canonical.err" ]]; then
    pass "canonical AWK implementation satisfies CONTRACT C01 (cmp-equal, exit 0, stderr 0 bytes)"
  else
    fail "canonical AWK implementation diverged from CONTRACT C01 (exit=${canonical_code}; cmp $(cmp -s "${tmp}/canonical.out" "${tmp}/expected" && echo equal || echo differ); stderr=$(wc -c < "${tmp}/canonical.err") bytes)"
  fi

  set +e
  awk -f "${target}" >"${tmp}/out" 2>"${tmp}/err"
  code=$?
  set -e
  if [[ "${code}" == "0" ]] && cmp -s "${tmp}/out" "${tmp}/expected" && [[ ! -s "${tmp}/err" ]]; then
    pass "AWK rewrite still satisfies CONTRACT C01 (cmp-equal, exit 0, stderr 0 bytes)"
  else
    fail "AWK rewrite diverged from CONTRACT C01 (exit=${code}; cmp $(cmp -s "${tmp}/out" "${tmp}/expected" && echo equal || echo differ); stderr=$(wc -c < "${tmp}/err") bytes)"
  fi

  profile_ok=1
  for profile_target in "${canonical}" "${target}"; do
    if awk '
      {
        line = $0
        sub(/[[:space:]]*#.*/, "", line)
        text = text "\n" line
      }
      END {
        ok = 1
        if (text !~ /BEGIN[[:space:]]*\{/) {
          print "missing BEGIN intent marker"
          ok = 0
        }
        if (text !~ /print[[:space:]]+/) {
          print "missing print-to-stdout intent marker"
          ok = 0
        }
        exit ok ? 0 : 1
      }
    ' "${profile_target}" >"${tmp}/intent.out" 2>"${tmp}/intent.err"; then
      :
    else
      fail "AWK intent profile missing from ${profile_target}"
      profile_ok=0
    fi
  done
  if [[ "${profile_ok}" == "1" ]]; then
    pass "canonical and rewritten AWK share the declared intent profile"
  fi

  if awk '
    {
      line = $0
      sub(/[[:space:]]*#.*/, "", line)
      text = text "\n" line
    }
    END {
      ok = 1
      if (text !~ /BEGIN[[:space:]]*\{/) {
        print "missing BEGIN profile marker"
        ok = 0
      }
      if (text !~ /function[[:space:]]+render[[:space:]]*\(/) {
        print "missing render function profile marker"
        ok = 0
      }
      if (text !~ /split[[:space:]]*\(/) {
        print "missing split call profile marker"
        ok = 0
      }
      if (text !~ /for[[:space:]]*\(/) {
        print "missing for loop profile marker"
        ok = 0
      }
      if (text !~ /sprintf[[:space:]]*\([[:space:]]*"%c"/) {
        print "missing sprintf character assembly profile marker"
        ok = 0
      }
      if (text !~ /print[[:space:]]+render[[:space:]]*\(/) {
        print "missing print-render call profile marker"
        ok = 0
      }
      exit ok ? 0 : 1
    }
  ' "${target}" >"${tmp}/profile.out" 2>"${tmp}/profile.err"; then
    pass "AWK static source profile matches C06"
  else
    fail "AWK static source profile does not match C06"
  fi
else
  skip "awk not on PATH; runtime and static profile checks not performed"
fi

echo
echo "summary: ${passes} pass, ${skips} skip, ${fails} fail"
exit $(( fails > 0 ? 1 : 0 ))
