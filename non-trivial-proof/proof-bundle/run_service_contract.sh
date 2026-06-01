#!/usr/bin/env bash
# run_service_contract.sh — the load-bearing witness (DESIGN.md §5.1).
# Enforces CONTRACT C01..C05 against every per-language echo server, ONE AT A
# TIME on 127.0.0.1:$PROOF_PORT (default 8080), in plain build order with NO
# privileged position (the retracted Java SO_REUSEADDR finding — DESIGN.md §3.1
# — is gone; Java is an ordinary PASS-candidate). Port release between languages
# is guaranteed by an INDEPENDENT re-bind probe that itself sets SO_REUSEADDR
# plus a bounded TIME_WAIT retry, uniformly for all runtimes. Prints
# PASS/SKIP/FAIL per language plus MEASURED ms, and exits non-zero on any FAIL.
set -u

BUNDLE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PROOF_PORT:-8080}"
HOST=127.0.0.1
PAYLOAD="$BUNDLE/payload.json"
TMP="$(mktemp -d)"
READY_DEADLINE_MS=5000
SHUTDOWN_DEADLINE_MS=3000
DELAY_MS=1000   # in-flight delay; MUST be < SHUTDOWN_DEADLINE_MS (§1 C04)

PASS=0; FAIL=0; SKIP=0
declare -a SUMMARY
RUN_PID=""

cleanup() { [ -n "$RUN_PID" ] && kill -9 -- -"$RUN_PID" 2>/dev/null; rm -rf "$TMP"; }
trap cleanup EXIT

now_ms() { date +%s%3N; }
port_listening() { ss -ltn 2>/dev/null | grep -q "[:.]$PORT\b"; }
wait_port_free() { for _ in $(seq 1 100); do port_listening || return 0; sleep 0.05; done; return 1; }

# C04 port-release probe (DESIGN.md §5.1 step 7): an INDEPENDENT re-bind probe
# that itself sets SO_REUSEADDR, retried for up to ~2 s to absorb TIME_WAIT.
# Returns 0 if the port becomes bindable. Uses python3 (the only faithful way to
# set SO_REUSEADDR from a shell witness); falls back to an ss listener-absence
# check only if python3 is unavailable.
rebind_probe() {
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$HOST" "$PORT" <<'PY'
import socket, sys, time
host, port = sys.argv[1], int(sys.argv[2])
deadline = time.time() + 2.0
while True:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((host, port)); s.close(); sys.exit(0)
    except OSError:
        s.close()
        if time.time() >= deadline:
            sys.exit(1)
        time.sleep(0.05)
PY
  else
    for _ in $(seq 1 40); do port_listening || return 0; sleep 0.05; done
    return 1
  fi
}

record() { # name result detail
  local n="$1" r="$2" d="$3"
  SUMMARY+=("$(printf '%-7s %-4s %s' "$n" "$r" "$d")")
  case "$r" in PASS) PASS=$((PASS+1));; FAIL) FAIL=$((FAIL+1));; SKIP) SKIP=$((SKIP+1));; esac
}

# Drive one server through C01..C05. Echoes the verdict line; returns 0 on PASS.
lifecycle() { # name run_cmd...
  local name="$1"; shift
  local -a run=("$@")
  local detail=""

  # --- pre-flight (§5.1 step 1): ordinary connectivity probe for EVERY runtime;
  #     no language-specific pre-flight (the retracted Java special case is gone, §3.1).
  wait_port_free || { record "$name" SKIP "port :$PORT occupied"; return 1; }

  # --- start in its own process group (set -m => PGID==PID) ---
  set -m
  PROOF_PORT="$PORT" "${run[@]}" >"$TMP/$name.out" 2>&1 &
  RUN_PID=$!
  set +m

  # --- C02 readiness (MEASURED time-to-ready) ---
  local t_start ready=0 tready=0
  t_start=$(now_ms)
  while [ $(( $(now_ms) - t_start )) -lt "$READY_DEADLINE_MS" ]; do
    if (exec 9<>/dev/tcp/$HOST/$PORT) 2>/dev/null; then exec 9<&-; ready=1; tready=$(( $(now_ms) - t_start )); break; fi
    sleep 0.02
  done
  if [ "$ready" != 1 ]; then record "$name" FAIL "C02 readiness: not connectable within ${READY_DEADLINE_MS}ms"; kill -9 -- -"$RUN_PID" 2>/dev/null; RUN_PID=""; return 1; fi

  # --- C01/C03 echo byte-exact + Content-Length == body length ---
  local status blen clen
  blen=$(wc -c < "$PAYLOAD")
  status=$(curl -s -D "$TMP/$name.hdr" -o "$TMP/$name.echo" -w '%{http_code}' -X POST --data-binary @"$PAYLOAD" "http://$HOST:$PORT/")
  clen=$(awk 'tolower($1)=="content-length:"{gsub(/\r/,"",$2); print $2}' "$TMP/$name.hdr" | tail -1)
  if [ "$status" != 200 ] || ! cmp -s "$TMP/$name.echo" "$PAYLOAD" || [ "$clen" != "$blen" ]; then
    record "$name" FAIL "C01/C03 echo: status=$status byte-exact=$(cmp -s "$TMP/$name.echo" "$PAYLOAD" && echo yes || echo no) content-length=${clen:-none} (expected $blen)"
    kill -9 -- -"$RUN_PID" 2>/dev/null; RUN_PID=""; return 1
  fi

  # --- C05 statefulness: a second request on the same PID ---
  curl -s -o "$TMP/$name.echo2" -X POST --data-binary @"$PAYLOAD" "http://$HOST:$PORT/"
  if ! cmp -s "$TMP/$name.echo2" "$PAYLOAD" || ! kill -0 "$RUN_PID" 2>/dev/null; then
    record "$name" FAIL "C05 statefulness: second request failed or process died"
    kill -9 -- -"$RUN_PID" 2>/dev/null; RUN_PID=""; return 1
  fi

  # --- C04 graceful shutdown WITH a real in-flight request + header sync point ---
  local len; len=$(wc -c < "$PAYLOAD")
  exec 3<>/dev/tcp/$HOST/$PORT
  printf 'POST /?delay_ms=%s HTTP/1.1\r\nHost: x\r\nContent-Length: %s\r\nConnection: close\r\n\r\n' "$DELAY_MS" "$len" >&3
  cat "$PAYLOAD" >&3
  local sawhdr=0 line
  while IFS= read -r line <&3; do line="${line%$'\r'}"; [ -z "$line" ] && { sawhdr=1; break; }; done
  local t0; t0=$(now_ms)
  kill -TERM "$RUN_PID"
  cat <&3 > "$TMP/$name.inflight" 2>/dev/null; exec 3<&-
  local ec="timeout"
  while [ $(( $(now_ms) - t0 )) -lt "$SHUTDOWN_DEADLINE_MS" ]; do
    if ! kill -0 "$RUN_PID" 2>/dev/null; then wait "$RUN_PID"; ec=$?; break; fi
    sleep 0.02
  done
  local tshut=$(( $(now_ms) - t0 ))

  if [ "$ec" = timeout ]; then
    record "$name" FAIL "C04: not exited within ${SHUTDOWN_DEADLINE_MS}ms; SIGKILL escalated"
    kill -9 -- -"$RUN_PID" 2>/dev/null; RUN_PID=""; return 1
  fi
  if [ "$sawhdr" != 1 ] || ! cmp -s "$TMP/$name.inflight" "$PAYLOAD"; then
    record "$name" FAIL "C04: in-flight response dropped/truncated ($(wc -c <"$TMP/$name.inflight")/$len bytes), exit=$ec"
    RUN_PID=""; return 1
  fi
  if [ "$ec" != 0 ]; then
    record "$name" FAIL "C04: non-zero exit on SIGTERM (exit=$ec)"
    RUN_PID=""; return 1
  fi

  # --- C04 port release: independent SO_REUSEADDR re-bind probe, bounded retry (§5.1 step 7)
  RUN_PID=""
  if ! rebind_probe; then record "$name" FAIL "C04: port :$PORT not re-bindable after exit (SO_REUSEADDR probe failed within retry)"; return 1; fi

  record "$name" PASS "ready=${tready}ms shutdown=${tshut}ms bytes=${len} (MEASURED)"
  return 0
}

# Build (toolchain absent => SKIP; build error with toolchain present => FAIL).
have() { command -v "$1" >/dev/null 2>&1; }

build_or_skip() { # name tool build_cmd...
  local name="$1" tool="$2"; shift 2
  if ! have "$tool"; then record "$name" SKIP "toolchain '$tool' absent"; return 1; fi
  if [ "$#" -gt 0 ]; then
    if ! "$@" >"$TMP/$name.build" 2>&1; then record "$name" FAIL "build failed ($tool): $(tail -1 "$TMP/$name.build")"; return 1; fi
  fi
  return 0
}

echo "== run_service_contract.sh :: C01..C05 on $HOST:$PORT (plain build order) =="

# Plain build order, no privileged position (DESIGN.md §3.1/§4).
# 1) Go
if build_or_skip go go go build -o "$TMP/go-echo" "$BUNDLE/src/go/server.go"; then
  lifecycle go "$TMP/go-echo"
fi
# 2) Node (JavaScript)
if build_or_skip node node; then
  lifecycle node node "$BUNDLE/src/node/server.js"
fi
# 3) TypeScript (same V8/Node runtime)
if build_or_skip ts node; then
  lifecycle ts node --experimental-strip-types "$BUNDLE/src/typescript/server.ts"
fi
# 4) Python
if build_or_skip python python3; then
  lifecycle python python3 "$BUNDLE/src/python/server.py"
fi
# 5) C
if build_or_skip c cc cc -O2 -o "$TMP/c-echo" "$BUNDLE/src/c/server.c"; then
  lifecycle c "$TMP/c-echo"
fi
# 6) Rust
if build_or_skip rust rustc rustc -O -o "$TMP/rust-echo" "$BUNDLE/src/rust/server.rs"; then
  lifecycle rust "$TMP/rust-echo"
fi
# 7) Java — ordinary PASS-candidate, source-launched (no javac); §3.1
if build_or_skip java java; then
  lifecycle java java "$BUNDLE/src/java/Server.java"
fi
# 8) AWK — declared C06 boundary; echo UNASSESSABLE. Delegated to detect_awk_boundary.sh.
record awk SKIP "C06 signal boundary (no clean SIGTERM); echo UNASSESSABLE — see detect_awk_boundary.sh"

echo
echo "-- per-language outcomes --"
for s in "${SUMMARY[@]}"; do echo "  $s"; done
echo
echo "TOT:  PASS=$PASS  SKIP=$SKIP  FAIL=$FAIL"
[ "$FAIL" -eq 0 ] || { echo "RESULT: FAIL"; exit 1; }
echo "RESULT: OK (no FAIL)"
exit 0
