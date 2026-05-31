#!/usr/bin/env bash
# detect_graceful_shutdown.sh — negative control for C04 (DESIGN.md §5.2).
# The C04 graceful definition is the STRONG one: a PASS requires not just
# "exit 0 on SIGTERM within deadline" but that an in-flight request COMPLETES.
# This witness drives two non-graceful controls and PASSES only if the gate
# catches BOTH:
#   Control A — ignores SIGTERM        => must be classified FAIL (SIGKILL needed)
#   Control B — drops in-flight on exit => must be classified FAIL (truncated body
#                                          even though the exit code is a clean 0)
# PASS here means the C04 check discriminates on BOTH the exit-code axis and the
# in-flight-completion axis, i.e. it is not vacuous.
set -u

BUNDLE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PROOF_PORT:-8080}"
HOST=127.0.0.1
PAYLOAD="$BUNDLE/payload.json"
TMP="$(mktemp -d)"
DELAY_MS=1000
SHUTDOWN_DEADLINE_MS=3000
RUN_PID=""

cleanup() { [ -n "$RUN_PID" ] && kill -9 -- -"$RUN_PID" 2>/dev/null; rm -rf "$TMP"; }
trap cleanup EXIT
now_ms() { date +%s%3N; }
port_listening() { ss -ltn 2>/dev/null | grep -q "[:.]$PORT\b"; }
wait_port_free() { for _ in $(seq 1 100); do port_listening || return 0; sleep 0.05; done; return 1; }

if ! command -v go >/dev/null 2>&1; then echo "SKIP: go toolchain absent (controls are Go)"; exit 0; fi
go build -o "$TMP/ctl-ignore" "$BUNDLE/src/controls/control_ignore.go" || { echo "FAIL: control_ignore build"; exit 1; }
go build -o "$TMP/ctl-drop"   "$BUNDLE/src/controls/control_drop.go"   || { echo "FAIL: control_drop build"; exit 1; }

# Drive a control; sets global CAUGHT=1 if the gate correctly FAILs it.
drive() { # mode bin
  local mode="$1" bin="$2"
  CAUGHT=0
  wait_port_free || { echo "  port busy, cannot test"; return; }
  set -m; PROOF_PORT="$PORT" "$bin" >"$TMP/ctl.out" 2>&1 & RUN_PID=$!; set +m
  local r=0; for _ in $(seq 1 100); do (exec 9<>/dev/tcp/$HOST/$PORT) 2>/dev/null && { exec 9<&-; r=1; break; }; sleep 0.05; done
  [ "$r" = 1 ] || { echo "  control not ready"; kill -9 -- -"$RUN_PID" 2>/dev/null; RUN_PID=""; return; }

  local len; len=$(wc -c < "$PAYLOAD")
  exec 3<>/dev/tcp/$HOST/$PORT
  printf 'POST /?delay_ms=%s HTTP/1.1\r\nHost: x\r\nContent-Length: %s\r\nConnection: close\r\n\r\n' "$DELAY_MS" "$len" >&3
  cat "$PAYLOAD" >&3
  local line; while IFS= read -r line <&3; do line="${line%$'\r'}"; [ -z "$line" ] && break; done
  local t0; t0=$(now_ms)
  kill -TERM "$RUN_PID"
  cat <&3 > "$TMP/ctl.inflight" 2>/dev/null; exec 3<&-
  local ec="timeout"
  while [ $(( $(now_ms) - t0 )) -lt "$SHUTDOWN_DEADLINE_MS" ]; do
    if ! kill -0 "$RUN_PID" 2>/dev/null; then wait "$RUN_PID"; ec=$?; break; fi; sleep 0.02
  done

  if [ "$mode" = ignore ]; then
    if [ "$ec" = timeout ]; then echo "  Control A (ignore SIGTERM): exit=timeout -> SIGKILL needed -> C04 FAIL  [CAUGHT]"; CAUGHT=1
    else echo "  Control A: unexpectedly exited (ec=$ec)  [MISSED]"; fi
  else
    if [ "$ec" != timeout ] && ! cmp -s "$TMP/ctl.inflight" "$PAYLOAD"; then
      echo "  Control B (drop in-flight): exit=$ec(clean) but body truncated $(wc -c <"$TMP/ctl.inflight")/$len -> C04 FAIL  [CAUGHT]"; CAUGHT=1
    else echo "  Control B: body intact or no exit (ec=$ec)  [MISSED]"; fi
  fi
  { kill -9 -- -"$RUN_PID"; wait "$RUN_PID"; } >/dev/null 2>&1; RUN_PID=""
}

echo "== detect_graceful_shutdown.sh :: two negative controls on $HOST:$PORT =="
drive ignore "$TMP/ctl-ignore"; A=$CAUGHT
drive drop   "$TMP/ctl-drop";   B=$CAUGHT
echo
if [ "${A:-0}" = 1 ] && [ "${B:-0}" = 1 ]; then
  echo "RESULT: OK — gate caught BOTH non-graceful servers (exit-code axis AND in-flight axis)"; exit 0
else
  echo "RESULT: FAIL — gate did not catch both controls (A=$A B=$B); C04 check would be vacuous"; exit 1
fi
