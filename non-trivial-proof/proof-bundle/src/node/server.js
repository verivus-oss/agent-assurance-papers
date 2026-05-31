// Smallest-reasonable HTTP echo server (Node.js) for the Stateful I/O proof.
// C01/C03: POST / -> 200 echoing exact bytes with Content-Length. C04: SIGTERM
// stops accepting, finishes in-flight, exits 0 (Node sets SO_REUSEADDR). The
// `?delay_ms=N` query is TEST-ONLY: flushHeaders() commits the status line +
// Content-Length immediately, then the body is written after N ms — the
// witness's race-free sync point (DESIGN.md §5.1 step 6 / §5.2).
const http = require('http');
const { URL } = require('url');

const port = process.env.PROOF_PORT || '8080';

const server = http.createServer((req, res) => {
  if (req.method !== 'POST') { res.writeHead(405); res.end(); return; }
  const chunks = [];
  req.on('data', (c) => chunks.push(c));
  req.on('end', () => {
    const body = Buffer.concat(chunks);
    const delay = parseInt(new URL(req.url, 'http://x').searchParams.get('delay_ms') || '0', 10);
    res.writeHead(200, {
      'Content-Type': 'application/octet-stream',
      'Content-Length': body.length,
    });
    res.flushHeaders(); // commit headers before any delay
    if (delay > 0) { setTimeout(() => res.end(body), delay); } else { res.end(body); }
  });
});

server.listen(Number(port), '127.0.0.1');

process.on('SIGTERM', () => {
  // stop accepting new connections; close() callback fires once in-flight done
  server.close(() => process.exit(0));
});
