// Negative control A (DESIGN.md §5.2): a server that IGNORES SIGTERM and never
// shuts down gracefully. The graceful-shutdown witness must classify this as a
// C04 FAIL and fall back to SIGKILL. Its PASS means "the gate correctly caught a
// non-graceful server." Echo behaviour is identical to the canonical server so
// the only difference under test is the (absent) signal handling.
package main

import (
	"io"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"
)

func port() string {
	if p := os.Getenv("PROOF_PORT"); p != "" {
		return p
	}
	return "8080"
}

func main() {
	signal.Ignore(syscall.SIGTERM) // the whole point: never react to SIGTERM
	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		delay := 0
		if d := r.URL.Query().Get("delay_ms"); d != "" {
			delay, _ = strconv.Atoi(d)
		}
		w.Header().Set("Content-Length", strconv.Itoa(len(body)))
		w.WriteHeader(http.StatusOK)
		if f, ok := w.(http.Flusher); ok {
			f.Flush()
		}
		if delay > 0 {
			time.Sleep(time.Duration(delay) * time.Millisecond)
		}
		_, _ = w.Write(body)
	})
	ln, err := net.Listen("tcp", "127.0.0.1:"+port())
	if err != nil {
		os.Exit(1)
	}
	_ = http.Serve(ln, mux) // serves forever; SIGTERM is ignored
}
