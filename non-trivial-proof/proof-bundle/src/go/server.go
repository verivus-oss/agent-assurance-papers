// Smallest-reasonable HTTP echo server (Go) for the Stateful I/O proof.
// Contract C01/C03: POST / with a body -> 200 OK echoing the exact bytes,
// Content-Length == body length. C04: SIGTERM stops accepting, finishes the
// in-flight request, releases the port (Go's net.Listen sets SO_REUSEADDR by
// default on Linux), and exits 0. The `?delay_ms=N` query is a TEST-ONLY
// affordance: it flushes the status line + Content-Length headers immediately,
// then sleeps N ms before writing the body, giving the witness a race-free
// synchronization point (see DESIGN.md §5.1 step 6 / §5.2).
package main

import (
	"context"
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
	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		body, _ := io.ReadAll(r.Body)
		delay := 0
		if d := r.URL.Query().Get("delay_ms"); d != "" {
			delay, _ = strconv.Atoi(d)
		}
		w.Header().Set("Content-Type", "application/octet-stream")
		w.Header().Set("Content-Length", strconv.Itoa(len(body)))
		w.WriteHeader(http.StatusOK)
		if f, ok := w.(http.Flusher); ok {
			f.Flush() // commit headers before any delay
		}
		if delay > 0 {
			time.Sleep(time.Duration(delay) * time.Millisecond)
		}
		_, _ = w.Write(body)
	})

	srv := &http.Server{Handler: mux}
	ln, err := net.Listen("tcp", "127.0.0.1:"+port())
	if err != nil {
		os.Exit(1)
	}

	idle := make(chan struct{})
	go func() {
		sig := make(chan os.Signal, 1)
		signal.Notify(sig, syscall.SIGTERM)
		<-sig
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		_ = srv.Shutdown(ctx) // stop accepting; wait for in-flight to finish
		close(idle)
	}()

	if err := srv.Serve(ln); err != http.ErrServerClosed {
		os.Exit(1)
	}
	<-idle
	os.Exit(0)
}
