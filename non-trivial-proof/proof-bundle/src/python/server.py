#!/usr/bin/env python3
"""Smallest-reasonable HTTP echo server (Python) for the Stateful I/O proof.

C01/C03: POST / -> 200 echoing exact bytes with Content-Length. C04: SIGTERM
stops accepting, finishes in-flight (non-daemon worker threads outlive the
listener so the interpreter waits for them), exits 0. `allow_reuse_address`
sets SO_REUSEADDR. `?delay_ms=N` is TEST-ONLY: headers are flushed before the
sleep so the witness has a race-free sync point (DESIGN.md §5.1 step 6 / §5.2).
"""
import os
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        delay = int(parse_qs(urlparse(self.path).query).get('delay_ms', ['0'])[0])
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.flush()  # commit headers before any delay
        if delay > 0:
            time.sleep(delay / 1000.0)
        self.wfile.write(body)

    def log_message(self, *args):  # silence default stderr logging
        pass


class Server(ThreadingHTTPServer):
    allow_reuse_address = True   # SO_REUSEADDR
    daemon_threads = False       # in-flight requests finish before exit


def main():
    port = int(os.environ.get('PROOF_PORT', '8080'))
    srv = Server(('127.0.0.1', port), Handler)

    def on_term(signum, frame):
        # shutdown() must run off the serve_forever thread
        threading.Thread(target=srv.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, on_term)
    srv.serve_forever()
    srv.server_close()
    sys.exit(0)


if __name__ == '__main__':
    main()
