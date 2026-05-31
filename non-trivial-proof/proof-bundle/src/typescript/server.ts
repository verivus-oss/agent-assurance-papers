// Smallest-reasonable HTTP echo server (TypeScript) for the Stateful I/O proof.
// Identical observable behaviour to the Node server; runs on the same V8/Node
// runtime via `node --experimental-strip-types server.ts` (no tsc on this
// runner). The type annotations are the only difference — see DESIGN.md §2
// counting rule (TS folds into the V8/Node runtime).
import http from 'node:http';
import { URL } from 'node:url';
import process from 'node:process';

const port: string = process.env.PROOF_PORT || '8080';

const server = http.createServer((req: http.IncomingMessage, res: http.ServerResponse) => {
  if (req.method !== 'POST') { res.writeHead(405); res.end(); return; }
  const chunks: Buffer[] = [];
  req.on('data', (c: Buffer) => chunks.push(c));
  req.on('end', () => {
    const body: Buffer = Buffer.concat(chunks);
    const delay: number = parseInt(new URL(req.url ?? '/', 'http://x').searchParams.get('delay_ms') ?? '0', 10);
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
  server.close(() => process.exit(0));
});
