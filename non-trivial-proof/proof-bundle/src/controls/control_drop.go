// Negative control B (DESIGN.md §5.2): a server that, on SIGTERM, exits(0)
// IMMEDIATELY while a slow request is still being served — so the client gets a
// reset/truncated body even though the exit code looks clean. The
// graceful-shutdown witness must detect the dropped in-flight response as a C04
// FAIL: a clean exit code alone is NOT accepted as graceful. This is the single
// most important honesty check in the bundle.
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
			f.Flush() // commit headers, then stall — so SIGTERM lands mid-flight
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
	go func() {
		sig := make(chan os.Signal, 1)
		signal.Notify(sig, syscall.SIGTERM)
		<-sig
		os.Exit(0) // drop everything in-flight; clean exit code, dirty behaviour
	}()
	_ = http.Serve(ln, mux)
}
