// Smallest-reasonable HTTP echo server (Java) for the Stateful I/O proof.
// Source-launched: `java Server.java` (JEP 330/477; no javac on this runner).
// HTTP via the bundled jdk.httpserver module (com.sun.net.httpserver), NOT
// java.net proper. C01/C03: POST / -> 200 echoing exact bytes with
// Content-Length. C04: SIGTERM runs the shutdown hook, which stop(2)s the
// server (waits up to 2s for the in-flight exchange to finish) then halt(0)s
// for a deterministic exit code 0.
//
// NOTE (DESIGN.md §3.1, Measured Runtime Correction): Java is an ORDINARY
// PASS-candidate with no special port-ordering or pre-flight. The retired
// design's claim that HttpServer cannot set SO_REUSEADDR / cannot re-bind a
// TIME_WAIT'd port was FALSE: a start()ed HttpServer (NIO ServerSocketChannel,
// SO_REUSEADDR on by default) tolerates a prior TIME_WAIT and releases its port
// immediately on stop(0). The true, measured footgun — a never-start()ed
// stop() leaking the listener — does not apply here because this server always
// start()s, and proof-side port release is verified cross-process anyway.
// `?delay_ms=N` is TEST-ONLY: sendResponseHeaders commits the status line +
// Content-Length before the sleep, giving the witness a sync point.
import com.sun.net.httpserver.HttpServer;
import java.io.OutputStream;
import java.net.InetSocketAddress;

public class Server {
    public static void main(String[] args) throws Exception {
        int port = Integer.parseInt(System.getenv().getOrDefault("PROOF_PORT", "8080"));
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", port), 0);
        server.createContext("/", ex -> {
            if (!"POST".equals(ex.getRequestMethod())) {
                ex.sendResponseHeaders(405, -1);
                ex.close();
                return;
            }
            byte[] body = ex.getRequestBody().readAllBytes();
            int delay = 0;
            String q = ex.getRequestURI().getQuery();
            if (q != null && q.startsWith("delay_ms=")) {
                delay = Integer.parseInt(q.substring("delay_ms=".length()));
            }
            ex.getResponseHeaders().set("Content-Type", "application/octet-stream");
            // length>0 => fixed Content-Length and headers are flushed now
            ex.sendResponseHeaders(200, body.length == 0 ? -1 : body.length);
            if (delay > 0) {
                try { Thread.sleep(delay); } catch (InterruptedException ignored) {}
            }
            try (OutputStream os = ex.getResponseBody()) {
                os.write(body);
            }
        });
        server.setExecutor(null);
        server.start();
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            server.stop(2);               // wait up to 2s for in-flight exchange
            Runtime.getRuntime().halt(0); // deterministic exit code 0 on SIGTERM
        }));
    }
}
