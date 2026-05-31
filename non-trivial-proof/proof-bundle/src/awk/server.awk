# Best-effort HTTP echo server (gawk /inet) for the Stateful I/O proof.
#
# DESIGN.md §5.3 / C06: the FIRM claim about this server is only the signal
# BOUNDARY — gawk exposes no clean script-level POSIX SIGTERM handler, so AWK is
# a declared SKIP-with-rationale for the C04 signal contract. Whether this
# server also achieves byte-exact C01/C03 echo with correct Content-Length
# framing over /inet is reported honestly by the witness as
# "UNASSESSABLE — no artifact guarantee", not asserted here. Run:
#   PROOF_PORT=8080 gawk -f server.awk
BEGIN {
    port = (ENVIRON["PROOF_PORT"] != "") ? ENVIRON["PROOF_PORT"] : "8080"
    conn = "/inet/tcp/" port "/0/0"
    RS = "\r\n"
    while (1) {
        clen = 0
        # read request line + headers until the blank line
        while ((conn |& getline line) > 0) {
            if (line == "") break
            if (tolower(line) ~ /^content-length:[ \t]*[0-9]+/) {
                n = line
                sub(/^[^0-9]*/, "", n)
                clen = n + 0
            }
        }
        # read one body record (sufficient for the single-line proof payload)
        body = ""
        if (clen > 0) {
            if ((conn |& getline body) <= 0) body = ""
        }
        # echo back with a Content-Length matching the bytes we send
        printf "HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s", length(body), body |& conn
        close(conn)
    }
}
