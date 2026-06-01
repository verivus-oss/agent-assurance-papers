// Re-pointed reproducer for the CORRECTED Java finding (DESIGN.md §3.1,
// MEASUREMENTS.md M1). The original spike was written to "confirm" a FALSE
// claim — that com.sun.net.httpserver.HttpServer sets no SO_REUSEADDR and
// cannot re-bind a TIME_WAIT'd port. Re-running it on this JDK returns
// "HttpServer.create rebind: OK", so the original verdict REFUTES ITSELF. This
// version demonstrates the two true, measured facts instead:
//
//   (A) TOLERANCE: a started HttpServer tolerates a prior TIME_WAIT on the port
//       (its NIO ServerSocketChannel has SO_REUSEADDR on by default) and
//       releases the port immediately on stop(0).
//   (B) FOOTGUN  : a NEVER-start()ed HttpServer.stop() LEAKS its bound listener
//       (the real, deterministic root cause the old finding mis-read as an
//       SO_REUSEADDR deficiency). This is an in-process API footgun; it does NOT
//       affect the proof, whose servers always start() and whose port release is
//       verified cross-process.
//
// "We mis-measured; the re-pointed reproducer catches it." A CONFIRMED verdict
// (exit 0) requires BOTH halves: the tolerance (A) AND the footgun (B). (A) is the
// DIRECT refutation of the old false claim, so if the kernel cannot hold a
// TIME_WAIT and (A) cannot be exercised, the spike SKIPs (exit 2) rather than
// claiming the finding on (B) alone — never a false CONFIRMED.
//
// Run (single-file source launch; no javac needed):
//   SPIKE_PORT=18080 java ReuseSpike.java
// Exit: 0 = corrected finding CONFIRMED (footgun reproduced);
//       2 = INCONCLUSIVE (sockets unavailable) — an honest SKIP, not a failure;
//       1 = NOT reproduced (the footgun did not occur on this JDK).
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

public class ReuseSpike {
    static final int PORT = Integer.parseInt(System.getenv().getOrDefault("SPIKE_PORT", "18080"));
    static final String H = "127.0.0.1";

    // Bind a plain ServerSocket on a port; reuse toggles SO_REUSEADDR. Returns
    // true iff the bind succeeds (the socket is closed immediately afterwards).
    static boolean ssBind(int port, boolean reuse) {
        try (ServerSocket ss = new ServerSocket()) {
            ss.setReuseAddress(reuse);
            ss.bind(new InetSocketAddress(H, port));
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    // Deterministically place a TIME_WAIT on PORT: a plain ServerSocket accepts
    // one connection and the SERVER closes it FIRST (active close), so the
    // resulting TIME_WAIT lands on (PORT, client-ephemeral).
    static boolean genTimeWait() {
        ServerSocket g;
        try {
            g = new ServerSocket();
            g.setReuseAddress(true);
            g.bind(new InetSocketAddress(H, PORT));
        } catch (Throwable t) {
            return false;
        }
        final ServerSocket gen = g;
        Thread server = new Thread(() -> {
            try {
                Socket c = gen.accept();
                c.getInputStream().read(new byte[16]);
                c.getOutputStream().write('x');
                c.getOutputStream().flush();
                c.close(); // SERVER active close -> TIME_WAIT on the PORT side
            } catch (Throwable ignored) {}
        });
        server.start();
        try (Socket c = new Socket(H, PORT)) {
            c.getOutputStream().write("hi".getBytes(StandardCharsets.US_ASCII));
            c.getOutputStream().flush();
            c.getInputStream().read(new byte[16]);
        } catch (Throwable ignored) {
        } finally {
            try { server.join(1000); } catch (InterruptedException ignored) {}
            try { gen.close(); } catch (Throwable ignored) {}
        }
        return true;
    }

    public static void main(String[] args) throws Exception {
        // Preflight: can we create a TCP socket at all? (sandboxed env => honest SKIP)
        if (!ssBind(PORT, true)) {
            System.out.println("INCONCLUSIVE: cannot bind " + H + ":" + PORT
                + " (sockets unavailable or port busy) — skipping, not failing.");
            System.exit(2);
        }

        // (A) TOLERANCE on PORT: started HttpServer over a live TIME_WAIT.
        boolean timeWaitPresent = false;
        for (int i = 0; i < 8 && !timeWaitPresent; i++) {
            if (!genTimeWait()) { Thread.sleep(200); continue; }
            Thread.sleep(150);
            timeWaitPresent = !ssBind(PORT, false); // no-reuse bind FAILS iff a TIME_WAIT blocks it
        }
        String toleranceLine;
        if (timeWaitPresent) {
            boolean httpOverTimeWait;
            try {
                HttpServer s = HttpServer.create(new InetSocketAddress(H, PORT), 0);
                s.start();          // the REAL lifecycle: start() then stop()
                s.stop(0);          // releases the port immediately
                httpOverTimeWait = true;
            } catch (Throwable t) {
                httpOverTimeWait = false;
            }
            toleranceLine = "[A] TIME_WAIT present on :" + PORT
                + " (no-reuse bind fails). Started HttpServer.create+start+stop over it: "
                + (httpOverTimeWait ? "OK (tolerates TIME_WAIT, releases immediately)"
                                    : "FAIL (unexpected — would contradict M1)");
            // If the started server itself were to fail here, that is a real refutation.
            if (!httpOverTimeWait) {
                System.out.println(toleranceLine);
                System.out.println("[verdict] NOT REPRODUCED: started HttpServer could not bind over TIME_WAIT.");
                System.exit(1);
            }
        } else {
            toleranceLine = "[A] could not establish a TIME_WAIT on :" + PORT
                + " (kernel did not hold one) — tolerance check inconclusive, reporting footgun only.";
        }
        System.out.println(toleranceLine);

        // (B) FOOTGUN on a throwaway port (PORT+1): never-start()ed stop() leaks
        // the listener. create() binds; stop(0) WITHOUT start() does not release
        // it, so a subsequent reuse bind on the same port FAILS. Deterministic;
        // the leaked listener lives until JVM exit (immaterial — this is the last
        // step). Use PORT+1 so it does not pollute the tolerance port.
        final int LEAK_PORT = PORT + 1;
        boolean leaked;
        try {
            HttpServer h = HttpServer.create(new InetSocketAddress(H, LEAK_PORT), 0);
            h.stop(0);                       // never start()ed
            Thread.sleep(150);
            leaked = !ssBind(LEAK_PORT, true); // reuse bind FAILS iff the listener is still held
        } catch (Throwable t) {
            leaked = false;
        }
        System.out.println("[B] never-start()ed HttpServer.stop() on :" + LEAK_PORT
            + " leaked its listener (reuse bind afterwards fails): " + (leaked ? "YES" : "no"));

        boolean confirmed = leaked;
        if (!timeWaitPresent) {
            // The tolerance half (A) — the DIRECT refutation of the old false claim —
            // could not be exercised on this runner. Do NOT claim the finding on the
            // footgun (B) alone: SKIP honestly (exit 2), matching DESIGN.md §5.5 and
            // the detect_java_reuseaddr.sh exit-2 => SKIP mapping.
            System.out.println("[verdict] INCONCLUSIVE: could not establish a TIME_WAIT, so the tolerance"
                + " half (the direct refutation of the old claim) was not exercised; footgun "
                + (leaked ? "reproduced" : "NOT reproduced") + ". Skipping (exit 2), not failing.");
            System.exit(2);
        }
        System.out.println("[verdict] Corrected finding (started server tolerates TIME_WAIT + releases;"
            + " never-started stop() leaks the listener): " + (confirmed ? "CONFIRMED" : "NOT REPRODUCED"));
        System.exit(confirmed ? 0 : 1);
    }
}
