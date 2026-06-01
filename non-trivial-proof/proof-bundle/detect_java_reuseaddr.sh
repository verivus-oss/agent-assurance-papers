#!/usr/bin/env bash
# detect_java_reuseaddr.sh — committed reproducer witness for the CORRECTED Java
# finding (DESIGN.md §3.1, MEASUREMENTS.md M1). Runs the re-pointed source-launched
# spike (src/spikes/ReuseSpike.java) on a spike port and reports the verdict.
#
# HONESTY NOTE: the original of this pair was written to "confirm" a FALSE claim
# (HttpServer cannot set SO_REUSEADDR / cannot re-bind a TIME_WAIT'd port). Direct
# re-measurement overturned it: a started HttpServer tolerates a prior TIME_WAIT
# and releases its port immediately on stop(0); the real, deterministic footgun is
# that a NEVER-start()ed stop() leaks the listener. We mis-measured; this
# re-pointed reproducer catches it. The footgun does not affect the proof (servers
# always start(); port release is verified cross-process).
#
# Honest SKIP when java is absent or sockets are unavailable — never a false FAIL.
set -u
BUNDLE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPIKE="$BUNDLE/src/spikes/ReuseSpike.java"
PORT="${SPIKE_PORT:-18080}"
HOST=127.0.0.1

echo "== detect_java_reuseaddr.sh :: corrected Java finding spike on $HOST:$PORT =="

if ! command -v java >/dev/null 2>&1; then echo "RESULT: SKIP — java toolchain absent"; exit 0; fi

# Socket preflight: if we cannot even bind the spike port, this environment cannot
# exercise the finding — SKIP rather than report a false negative.
if ! python3 - "$HOST" "$PORT" <<'PY' 2>/dev/null
import socket, sys
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try: s.bind((sys.argv[1], int(sys.argv[2]))); s.close(); sys.exit(0)
except OSError: sys.exit(1)
PY
then echo "RESULT: SKIP — cannot bind $HOST:$PORT (sockets unavailable or port busy)"; exit 0; fi

SPIKE_PORT="$PORT" java "$SPIKE"; rc=$?
case "$rc" in
  0) echo "RESULT: OK — corrected finding CONFIRMED (started HttpServer tolerates TIME_WAIT + releases on stop(0); never-start()ed stop() leaks the listener)"; exit 0 ;;
  2) echo "RESULT: SKIP — environment could not exercise the finding (sockets limited)"; exit 0 ;;
  *) echo "RESULT: FAIL — corrected finding NOT reproduced on this JDK (exit $rc); DESIGN §3.1 would need revisiting"; exit 1 ;;
esac
