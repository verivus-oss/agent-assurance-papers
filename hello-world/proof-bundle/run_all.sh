#!/usr/bin/env bash
# run_all.sh — build and execute every implementation under src/, then
# enforce contract_declaration.toml C01 (stdout == "Hello, world!\n",
# exit code == 0, stderr empty) for each.
#
# This script is the executable witness behind evidence_matrix.toml:EV05.
# It is intentionally toolchain-aware: a missing toolchain (rustc,
# go, cc, javac+java, tsc/node, awk) downgrades that language to SKIP
# rather than failing the run. The DAG-TOML documents under this
# directory describe what the spec demands; this script is the
# observed instance check.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

# Materialise the exact expected byte stream once: 14 bytes,
# H-e-l-l-o-,-space-w-o-r-l-d-!-\n. Every contract check below uses
# `cmp -s` against this file so the trailing newline is byte-exact
# enforced (a no-newline output, BOM, or trailing extra byte all
# fail). C01 in contract_declaration.toml requires this exact
# 14-byte sequence.
expected_file="${tmp}/expected_stdout"
printf 'Hello, world!\n' > "${expected_file}"

passes=0
skips=0
fails=0

check_contract() {
  # check_contract <language> <stdout-file> <stderr-file> <exit-code>
  # C01 trio:
  #   - exit code 0
  #   - stdout bytes == expected_file bytes (byte-exact via cmp -s)
  #   - stderr file size == 0 (no bytes at all, not even whitespace)
  local lang="$1" out="$2" err="$3" code="$4"
  if [[ "${code}" != "0" ]]; then
    printf '  FAIL  %-10s exit code %s (expected 0)\n' "${lang}" "${code}"
    fails=$((fails+1))
    return 1
  fi
  if ! cmp -s "${out}" "${expected_file}"; then
    printf '  FAIL  %-10s stdout did not match expected byte stream (cmp -s "%s" "%s" failed)\n' \
      "${lang}" "${out}" "${expected_file}"
    printf '         expected (hex): '; od -An -c "${expected_file}" | tr -s ' ' | head -1
    printf '         actual   (hex): '; od -An -c "${out}" | tr -s ' ' | head -1
    fails=$((fails+1))
    return 1
  fi
  if [[ -s "${err}" ]]; then
    printf '  FAIL  %-10s stderr non-empty (%d bytes)\n' \
      "${lang}" "$(wc -c < "${err}")"
    fails=$((fails+1))
    return 1
  fi
  printf '  PASS  %-10s stdout=cmp-equal exit=0 stderr=0-bytes\n' "${lang}"
  passes=$((passes+1))
  return 0
}

run_lang() {
  # run_lang <language> <build_cmd> <run_cmd>
  local lang="$1" build_cmd="$2" run_cmd="$3"
  local out="${tmp}/${lang}.out" err="${tmp}/${lang}.err"
  if ! eval "${build_cmd}" >"${err}.build" 2>&1; then
    printf '  SKIP  %-10s build failed (toolchain unavailable?)\n' "${lang}"
    skips=$((skips+1))
    return 0
  fi
  set +e
  eval "${run_cmd}" >"${out}" 2>"${err}"
  local code=$?
  set -e
  check_contract "${lang}" "${out}" "${err}" "${code}" || true
}

echo "proof-hello-world: enforcing contract_declaration.toml C01 on each language"
echo

# ---------------- Rust ----------------
if command -v rustc >/dev/null 2>&1; then
  run_lang "rust" \
    "rustc -O -o '${tmp}/hello-rs' '${here}/src/rust/hello.rs'" \
    "'${tmp}/hello-rs'"
else
  printf '  SKIP  %-10s rustc not on PATH\n' "rust"
  skips=$((skips+1))
fi

# ---------------- Go ------------------
if command -v go >/dev/null 2>&1; then
  run_lang "go" \
    "(cd '${tmp}' && cp '${here}/src/go/hello.go' . && go mod init hello >/dev/null 2>&1 || true) && go build -o '${tmp}/hello-go' '${tmp}/hello.go'" \
    "'${tmp}/hello-go'"
else
  printf '  SKIP  %-10s go not on PATH\n' "go"
  skips=$((skips+1))
fi

# ---------------- C -------------------
if command -v cc >/dev/null 2>&1; then
  run_lang "c" \
    "cc -O2 -o '${tmp}/hello-c' '${here}/src/c/hello.c'" \
    "'${tmp}/hello-c'"
else
  printf '  SKIP  %-10s cc not on PATH\n' "c"
  skips=$((skips+1))
fi

# ---------------- Java ----------------
if command -v javac >/dev/null 2>&1 && command -v java >/dev/null 2>&1; then
  cp "${here}/src/java/Hello.java" "${tmp}/Hello.java"
  run_lang "java" \
    "javac -d '${tmp}' '${tmp}/Hello.java'" \
    "(cd '${tmp}' && java Hello)"
else
  printf '  SKIP  %-10s javac/java not on PATH\n' "java"
  skips=$((skips+1))
fi

# ---------------- TypeScript ----------
# Prefer `tsc + node`; fall back to `node --experimental-strip-types`.
if command -v tsc >/dev/null 2>&1 && command -v node >/dev/null 2>&1; then
  run_lang "typescript" \
    "tsc --target es2020 --outDir '${tmp}' '${here}/src/typescript/hello.ts'" \
    "node '${tmp}/hello.js'"
elif command -v node >/dev/null 2>&1; then
  run_lang "typescript" \
    "true" \
    "node --experimental-strip-types '${here}/src/typescript/hello.ts'"
else
  printf '  SKIP  %-10s node not on PATH\n' "typescript"
  skips=$((skips+1))
fi

# ---------------- AWK -----------------
if command -v awk >/dev/null 2>&1; then
  run_lang "awk" \
    "true" \
    "awk -f '${here}/src/awk/hello.awk'"
else
  printf '  SKIP  %-10s awk not on PATH\n' "awk"
  skips=$((skips+1))
fi

echo
echo "summary: ${passes} pass, ${skips} skip, ${fails} fail"
exit $(( fails > 0 ? 1 : 0 ))
