# Calibration control for the differential-agreement witness (DESIGN.md §5.4).
# A deliberately-UNFAITHFUL echo: it returns 200 but TRUNCATES the response body
# to 16 bytes. The differential harness MUST flag it on every adversarial body
# longer than 16 B; if it does not, the cross-implementation equivalence test is
# vacuous. This is the differential channel's analog of the graceful-vs-kill
# negative controls — it proves the equivalence test can fail.
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        broken = body[:16]                       # <-- the deliberate bug: truncate to 16 B
        self.send_response(200)
        self.send_header("Content-Length", str(len(broken)))
        self.end_headers()
        self.wfile.write(broken)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PROOF_PORT", "8080"))
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
