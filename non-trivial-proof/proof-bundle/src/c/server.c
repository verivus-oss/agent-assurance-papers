/* Smallest-reasonable HTTP echo server (C) for the Stateful I/O proof.
 * Raw BSD sockets + sigaction + explicit setsockopt(SO_REUSEADDR) + a minimal
 * HTTP parse. C01/C03: POST / -> 200 echoing exact bytes with Content-Length.
 * C04: SIGTERM (no SA_RESTART) interrupts accept() so the loop checks a flag and
 * exits 0; a SIGTERM landing during an in-flight response lets that response
 * finish first. `?delay_ms=N` is TEST-ONLY: the response head is written (and
 * thus flushed, since this is an unbuffered socket) before the sleep, giving the
 * witness a race-free sync point. */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <errno.h>
#include <stdint.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>

static volatile sig_atomic_t g_stop = 0;
static void on_term(int sig) { (void)sig; g_stop = 1; }

static void msleep_full(long ms) {
    struct timespec ts;
    ts.tv_sec = ms / 1000;
    ts.tv_nsec = (ms % 1000) * 1000000L;
    while (nanosleep(&ts, &ts) == -1 && errno == EINTR) { /* finish the delay */ }
}

static int writen(int fd, const char *buf, size_t n) {
    size_t off = 0;
    while (off < n) {
        ssize_t w = write(fd, buf + off, n - off);
        if (w < 0) { if (errno == EINTR) continue; return -1; }
        off += (size_t)w;
    }
    return 0;
}

int main(void) {
    const char *ps = getenv("PROOF_PORT");
    int port = (ps && *ps) ? atoi(ps) : 8080;

    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_term; /* no SA_RESTART: accept()/read() return EINTR */
    sigaction(SIGTERM, &sa, NULL);

    int lfd = socket(AF_INET, SOCK_STREAM, 0);
    if (lfd < 0) return 1;
    int one = 1;
    setsockopt(lfd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_port = htons((uint16_t)port);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(lfd, (struct sockaddr *)&addr, sizeof addr) < 0) return 1;
    if (listen(lfd, 16) < 0) return 1;

    while (!g_stop) {
        int cfd = accept(lfd, NULL, NULL);
        if (cfd < 0) { if (errno == EINTR) continue; else break; }

        char hdr[8192];
        size_t n = 0;
        int got_hdr = 0;
        while (n < sizeof(hdr) - 1) {
            ssize_t r = read(cfd, hdr + n, 1);
            if (r <= 0) { if (r < 0 && errno == EINTR) continue; break; }
            n += (size_t)r;
            if (n >= 4 && memcmp(hdr + n - 4, "\r\n\r\n", 4) == 0) { got_hdr = 1; break; }
        }
        if (!got_hdr) { close(cfd); continue; }
        hdr[n] = 0;

        long clen = 0;
        char *cl = strcasestr(hdr, "content-length:");
        if (cl) clen = atol(cl + strlen("content-length:"));
        long delay = 0;
        char *dm = strstr(hdr, "delay_ms=");
        if (dm) delay = atol(dm + strlen("delay_ms="));

        char *body = malloc(clen > 0 ? (size_t)clen : 1);
        long bgot = 0;
        while (bgot < clen) {
            ssize_t r = read(cfd, body + bgot, (size_t)(clen - bgot));
            if (r <= 0) { if (r < 0 && errno == EINTR) continue; break; }
            bgot += r;
        }

        char head[160];
        int hl = snprintf(head, sizeof head,
            "HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\n"
            "Content-Length: %ld\r\nConnection: close\r\n\r\n", bgot);
        writen(cfd, head, (size_t)hl); /* commit headers (sync point) */
        if (delay > 0) msleep_full(delay);
        if (bgot > 0) writen(cfd, body, (size_t)bgot);
        free(body);
        close(cfd);
    }
    close(lfd);
    return 0; /* graceful: any in-flight response already completed above */
}
