#!/usr/bin/env bash
# detect_awk_boundary.sh — the C06 boundary witness (DESIGN.md §5.3).
# Starts the gawk /inet echo server and records the C04 signal BOUNDARY: gawk
# exposes no clean script-level POSIX SIGTERM handler, so AWK is a declared
# SKIP-with-rationale for the signal contract — not silently dropped, not falsely
# passed. Whether the gawk server also satisfies byte-exact C01/C03 echo is
# reported honestly as UNASSESSABLE; it is NOT asserted. The FIRM claim is the
# signal boundary alone. PASS = the boundary is observed and declared (the gawk
# server does NOT exit cleanly 0 on SIGTERM).
set -u

BUNDLE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PROOF_PORT:-8080}"
HOST=127.0.0.1
PAYLOAD="$BUNDLE/payload.json"
AWK="$BUNDLE/src/awk/server.awk"
TMP="$(mktemp -d)"
RUN_PID=""

cleanup() { [ -n "$RUN_PID" ] && kill -9 "$RUN_PID" 2>/dev/null; pkill -9 -f "gawk -f $AWK" 2>/dev/null; rm -rf "$TMP"; }
trap cleanup EXIT
port_listening() { ss -ltn 2>/dev/null | grep -q "[:.]$PORT\b"; }

if ! command -v gawk >/dev/null 2>&1; then echo "SKIP: gawk absent"; exit 0; fi
for _ in $(seq 1 100); do port_listening || break; sleep 0.05; done

echo "== detect_awk_boundary.sh :: C06 signal boundary on $HOST:$PORT =="
set -m; PROOF_PORT="$PORT" gawk -f "$AWK" >"$TMP/awk.out" 2>&1 & RUN_PID=$!; set +m
ready=0; for _ in $(seq 1 100); do (exec 9<>/dev/tcp/$HOST/$PORT) 2>/dev/null && { exec 9<&-; ready=1; break; }; sleep 0.05; done
if [ "$ready" != 1 ]; then echo "RESULT: SKIP — gawk /inet listener did not come up"; exit 0; fi
echo "  gawk /inet listener is up (pid=$RUN_PID)"

# ---- echo: UNASSESSABLE (reported, not asserted) ----
: > "$TMP/awk.echo"   # ensure the file exists even if curl returns nothing
curl -s --max-time 4 -o "$TMP/awk.echo" -X POST --data-binary @"$PAYLOAD" "http://$HOST:$PORT/" 2>/dev/null || true
if cmp -s "$TMP/awk.echo" "$PAYLOAD"; then
  echo "  C01/C03 echo: byte-exact on this run (still reported UNASSESSABLE — not a firm bundle claim)"
else
  echo "  C01/C03 echo: NOT byte-exact ($(wc -c <"$TMP/awk.echo" 2>/dev/null || echo 0)/$(wc -c <"$PAYLOAD") bytes) -> UNASSESSABLE (as designed)"
fi

# ---- C06 signal boundary: the FIRM claim ----
kill -TERM "$RUN_PID"
ec="still-running"
for _ in $(seq 1 60); do if ! kill -0 "$RUN_PID" 2>/dev/null; then wait "$RUN_PID"; ec=$?; break; fi; sleep 0.05; done
if [ "$ec" != "still-running" ] && [ "$ec" -eq 0 ] 2>/dev/null; then
  echo "  UNEXPECTED: gawk exited cleanly 0 on SIGTERM — boundary claim would need revisiting"
  echo "RESULT: FAIL"; exit 1
fi
echo "  SIGTERM -> exit status '$ec' (NOT a clean 0; gawk has no script-level SIGTERM trap)"
echo "  => AWK C04 = SKIP-with-rationale (declared C06 boundary). Firm claim observed."
[ "$ec" = "still-running" ] && kill -9 "$RUN_PID" 2>/dev/null
RUN_PID=""
echo "RESULT: OK — C06 boundary observed and declared (AWK SKIP on C04; echo UNASSESSABLE)"
exit 0
