#!/usr/bin/env python3
"""differential_echo.py — apply the CDA behavioural/differential-agreement methodology
to the multi-language HTTP echo proof.

The §10 contract witness checks each server against ONE fixed payload. That cannot reveal
where implementations DIVERGE on adversarial inputs. This harness runs every echo server on
a shared corpus of edge-case request bodies and measures cross-implementation agreement:
for a faithful echo, every server must return status 200 with body == request bytes, for
ALL inputs. A divergence (wrong status, altered/truncated body, hang) is a real bug in one
implementation that the others do not share — the multi-implementation analog of the
behavioural channel (here we WANT agreement; disagreement is the finding).

Serialised on one port (like run_service_contract.sh). Run from proof-bundle/.
"""
import http.client
import os
import signal
import socket
import subprocess
import sys
import time
import pathlib

BUNDLE = pathlib.Path(__file__).resolve().parent
PORT = int(os.environ.get("PROOF_PORT", "8080"))
CONTROL = {"zctrl-broken"}    # deliberately-unfaithful echo; MUST be flagged (non-vacuity)
HOST = "127.0.0.1"
TMP = pathlib.Path("/tmp/diff_echo"); TMP.mkdir(exist_ok=True)

# The calibration control is a COMMITTED, inspectable artifact (single source of
# truth), the differential channel's analog of the graceful-vs-kill controls.
BROKEN_CONTROL = BUNDLE / "src/controls/broken_echo.py"


def build():
    """Compile the compiled-language servers; return {name: run_argv} for all echo servers."""
    servers = {}
    # interpreted / source-launched
    servers["python"] = ["python3", str(BUNDLE / "src/python/server.py")]
    servers["node"] = ["node", str(BUNDLE / "src/node/server.js")]
    servers["ts"] = ["node", "--experimental-strip-types", str(BUNDLE / "src/typescript/server.ts")]
    servers["java"] = ["java", str(BUNDLE / "src/java/Server.java")]
    # compiled
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
    # calibration control (broken echo that truncates to 16 bytes) — proves the harness
    # can detect a divergence; if it is NOT flagged, the differential test is vacuous.
    # Loaded from the COMMITTED src/controls/broken_echo.py (single source of truth).
    if BROKEN_CONTROL.exists():
        servers["zctrl-broken"] = ["python3", str(BROKEN_CONTROL)]
    else:
        print(f"  [warn] calibration control missing: {BROKEN_CONTROL} — non-vacuity NOT proven")
    return servers


def wait_ready(timeout=8.0):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.3):
                return True
        except OSError:
            time.sleep(0.05)
    return False


def port_free(timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        try:
            s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT)); s.close(); return True
        except OSError:
            time.sleep(0.05)
    return False


def corpus():
    """Adversarial echo bodies: (label, bytes)."""
    return [
        ("simple-json", b'{"proof":"stateful-io","n":42}'),
        ("empty", b""),
        ("no-trailing-newline", b"abcdef"),
        ("nul-bytes", bytes(range(256))),                      # full byte range incl NUL
        ("utf8-multibyte", "héllo 世界 🌍 Ω".encode("utf-8")),
        ("embedded-crlf-http", b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 5\r\n\r\nhello"),
        ("long-line-100k", b"A" * 100_000),
        ("large-1mib", b"Z" * (1 << 20)),
        ("whitespace-only", b"   \t\r\n  "),
        ("json-with-nul", b'{"k":"a\x00b"}'),
    ]


def run_server(name, argv, reqs):
    """Launch one server, send every request, return {label: (status, body)|('ERR',msg)}."""
    if not port_free():
        return {lbl: ("ERR", "port-busy") for lbl, _ in reqs}
    env = dict(os.environ, PROOF_PORT=str(PORT))
    proc = subprocess.Popen(argv, env=env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
    out = {}
    try:
        if not wait_ready():
            return {lbl: ("ERR", "no-ready") for lbl, _ in reqs}
        for lbl, body in reqs:
            try:
                conn = http.client.HTTPConnection(HOST, PORT, timeout=10)
                conn.request("POST", "/", body=body)
                resp = conn.getresponse()
                data = resp.read()
                out[lbl] = (resp.status, data)
                conn.close()
            except Exception as e:
                out[lbl] = ("ERR", type(e).__name__)
    finally:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass
        proc.wait()
        time.sleep(0.2)
    return out


def main():
    servers = build()
    reqs = corpus()
    print(f"servers: {sorted(servers)}  |  requests: {[l for l,_ in reqs]}\n")
    results = {}
    for name in sorted(servers):
        results[name] = run_server(name, servers[name], reqs)
        oks = sum(1 for lbl, body in reqs
                  if results[name].get(lbl) == (200, body))
        print(f"  ran {name:7} — faithful echoes: {oks}/{len(reqs)}")

    print("\n=== DIFFERENTIAL AGREEMENT (faithful echo = status 200 AND body==request) ===")
    names = sorted(servers)
    real = [n for n in names if n not in CONTROL]
    header = f"{'request':22}" + "".join(f"{n[:5]:>7}" for n in names) + "   real servers?"
    print(header); print("-" * len(header))
    real_divergences = []
    ctrl_caught = 0
    for lbl, body in reqs:
        cells = []
        verdicts = {}
        for n in names:
            r = results[n].get(lbl)
            if r == (200, body):
                cells.append("  ok"); verdicts[n] = "ok"
            elif isinstance(r, tuple) and r[0] == "ERR":
                cells.append(f" {r[1][:5]}"); verdicts[n] = "ERR"
            elif isinstance(r, tuple) and r[0] == 200:
                cells.append(" body!"); verdicts[n] = "body-mismatch"   # 200 but wrong bytes
            else:
                cells.append(f" {r[0]}"); verdicts[n] = f"status-{r[0]}"
        real_ok = all(verdicts[n] == "ok" for n in real)
        if not real_ok:
            real_divergences.append((lbl, {n: verdicts[n] for n in real if verdicts[n] != "ok"}))
        if any(verdicts[n] != "ok" for n in CONTROL if n in verdicts):
            ctrl_caught += 1
        tag = "ALL ok" if real_ok else "DIVERGE"
        print(f"{lbl:22}" + "".join(f"{c:>7}" for c in cells) + f"   {tag}")

    print(f"\nCALIBRATION: control 'zctrl-broken' flagged on {ctrl_caught}/{len(reqs)} requests "
          f"({'NON-VACUOUS — harness detects divergence' if ctrl_caught else 'VACUOUS — harness FAILED to catch the broken control!'})")
    print(f"\n=== {len(real_divergences)} divergent requests among the {len(real)} real servers "
          f"(implementation bugs the single-payload witness misses) ===")
    for lbl, bad in real_divergences:
        print(f"  {lbl}: " + ", ".join(f"{n}={v}" for n, v in bad.items()))
    if not real_divergences:
        print("  none — all real implementations behaviourally agree on every adversarial input.")

    # Exit status: 0 only if the equivalence holds AND is proven non-vacuous —
    # zero real-server divergences AND the broken calibration control was caught
    # at least once. A missing/uncaught control means non-vacuity is unproven => fail.
    ok = (not real_divergences) and ("zctrl-broken" in servers) and (ctrl_caught > 0)
    if not ok:
        print("\nRESULT: FAIL — "
              + ("real-server divergences present; " if real_divergences else "")
              + ("calibration control not caught (test would be vacuous)" if ctrl_caught == 0 else ""))
    else:
        print(f"\nRESULT: OK — 0 divergences across {len(real)} servers; control caught {ctrl_caught}/{len(reqs)} (non-vacuous)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
