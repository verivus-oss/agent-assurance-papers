#!/usr/bin/env python3
"""detect_inflight_window.py — timing guard for C04's in-flight clause (DESIGN.md §5.6).

The load-bearing contract witness (run_service_contract.sh) drives a delayed request,
syncs on the response headers, signals SIGTERM, and asserts the in-flight body arrives
COMPLETE and byte-exact. That is necessary but NOT sufficient: it assumes the server
flushes its response headers to the client BEFORE writing the body, so that "the request
is in flight" is an observed fact when SIGTERM is sent. A MEASURED counterexample exists —
com.sun's HttpServer buffers the response headers until body bytes flow, so without a
work-around the witness receives headers+body together only after the handler returns and
the in-flight window silently COLLAPSES (the body is already complete when SIGTERM lands;
see DESIGN.md §5.6 and src/java/Server.java).

This witness makes the in-flight window an explicit, timed assertion: for each PASS-candidate
it records the SIGTERM-delivery timestamp against the client-side timestamp of the body's
COMPLETION, and requires the body to complete STRICTLY AFTER SIGTERM by a margin (>= half the
injected delay). A server whose in-flight window collapses (body already sent at SIGTERM)
finishes in ~0 ms and FAILS this guard; a server that genuinely holds the body in flight
across the delay finishes ~delay ms later and PASSES. AWK is excluded (declared C06 boundary).

Serialised on one port, like the other witnesses. Run from proof-bundle/.
"""
import http.client  # noqa: F401 (kept for parity; raw sockets used below for timing)
import os
import signal
import socket
import subprocess
import sys
import time
import pathlib

BUNDLE = pathlib.Path(__file__).resolve().parent
PORT = int(os.environ.get("PROOF_PORT", "8080"))
HOST = "127.0.0.1"
DELAY_MS = 1000                      # injected in-flight delay (matches run_service_contract.sh)
MARGIN_MS = DELAY_MS / 2             # body must complete at least this long after SIGTERM
TMP = pathlib.Path("/tmp/inflight"); TMP.mkdir(exist_ok=True)
PAYLOAD = (BUNDLE / "payload.json").read_bytes()


def build():
    """Return {name: run_argv} for the seven PASS-candidate echo servers (AWK excluded)."""
    servers = {}
    servers["python"] = ["python3", str(BUNDLE / "src/python/server.py")]
    servers["node"] = ["node", str(BUNDLE / "src/node/server.js")]
    servers["ts"] = ["node", "--experimental-strip-types", str(BUNDLE / "src/typescript/server.ts")]
    servers["java"] = ["java", str(BUNDLE / "src/java/Server.java")]
    builds = {
        "go": (["go", "build", "-o", str(TMP / "go-echo"), str(BUNDLE / "src/go/server.go")], [str(TMP / "go-echo")]),
        "c": (["cc", "-O2", "-o", str(TMP / "c-echo"), str(BUNDLE / "src/c/server.c")], [str(TMP / "c-echo")]),
        "rust": (["rustc", "-O", "-o", str(TMP / "rust-echo"), str(BUNDLE / "src/rust/server.rs")], [str(TMP / "rust-echo")]),
    }
    for name, (cmd, run) in builds.items():
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            servers[name] = run
        else:
            print(f"  [skip {name}] build failed: {r.stderr.strip()[:80]}")
    return servers


def port_free(timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        try:
            s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT)); s.close(); return True
        except OSError:
            time.sleep(0.05)
    return False


def wait_ready(timeout=8.0):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.3):
                return True
        except OSError:
            time.sleep(0.05)
    return False


def measure(name, argv):
    """Drive a delayed request, SIGTERM after the header sync point, time body completion."""
    if not port_free():
        return {"ok": False, "detail": "port busy"}
    proc = subprocess.Popen(argv, env=dict(os.environ, PROOF_PORT=str(PORT)),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
    try:
        if not wait_ready():
            return {"ok": False, "detail": "never became ready"}
        s = socket.create_connection((HOST, PORT), timeout=10); s.settimeout(10)
        req = (b"POST /?delay_ms=%d HTTP/1.1\r\nHost: x\r\nContent-Length: %d\r\nConnection: close\r\n\r\n"
               % (DELAY_MS, len(PAYLOAD))) + PAYLOAD
        s.sendall(req)
        # sync point: block until the response headers are readable
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = s.recv(4096)
            if not chunk:
                return {"ok": False, "detail": "connection closed before headers"}
            buf += chunk
        _, _, body = buf.partition(b"\r\n\r\n")
        t_sigterm = time.monotonic()
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        # read the remainder of the body; time when it is COMPLETE
        while len(body) < len(PAYLOAD):
            chunk = s.recv(4096)
            if not chunk:
                break
            body += chunk
        t_complete = time.monotonic()
        s.close()
        ec = proc.wait()
        after_ms = (t_complete - t_sigterm) * 1000.0
        exact = body == PAYLOAD
        genuine = after_ms >= MARGIN_MS          # body held in flight across a real window
        ok = exact and genuine and ec == 0
        return {"ok": ok, "after_ms": after_ms, "exact": exact, "genuine": genuine,
                "exit": ec, "bytes": len(body)}
    finally:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass
        proc.wait()
        time.sleep(0.2)


def main():
    servers = build()
    print(f"== detect_inflight_window.py :: C04 in-flight timing guard on {HOST}:{PORT} "
          f"(delay={DELAY_MS}ms, margin={MARGIN_MS:.0f}ms) ==\n")
    fails = 0
    for name in sorted(servers):
        r = measure(name, servers[name])
        if r["ok"]:
            print(f"  {name:7} PASS  body completed {r['after_ms']:6.0f}ms AFTER SIGTERM "
                  f"(>= {MARGIN_MS:.0f}ms margin); byte-exact; exit {r['exit']} "
                  f"-> in-flight window GENUINELY exercised")
        else:
            fails += 1
            if "after_ms" in r:
                why = []
                if not r["genuine"]:
                    why.append(f"completed only {r['after_ms']:.0f}ms after SIGTERM (< {MARGIN_MS:.0f}ms "
                               f"=> in-flight window COLLAPSED; body was already sent)")
                if not r["exact"]:
                    why.append(f"body not byte-exact ({r['bytes']}/{len(PAYLOAD)})")
                if r["exit"] != 0:
                    why.append(f"exit {r['exit']}")
                print(f"  {name:7} FAIL  " + "; ".join(why))
            else:
                print(f"  {name:7} FAIL  {r['detail']}")
    print()
    if fails == 0:
        print(f"RESULT: OK — all {len(servers)} PASS-candidates genuinely exercise the C04 in-flight "
              f"window (body completes after SIGTERM by >= {MARGIN_MS:.0f}ms)")
        return 0
    print(f"RESULT: FAIL — {fails} server(s) did not genuinely exercise the in-flight window")
    return 1


if __name__ == "__main__":
    sys.exit(main())
