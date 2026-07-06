// Smallest-reasonable HTTP echo server (Rust) for the Stateful I/O proof.
// Hermetic: std only, NO external crates (this is the stateful test, not the
// dependency test). std has no signal API and TcpListener::bind does not set
// SO_REUSEADDR, so we declare the needed libc symbols through a small extern "C"
// block — signal/SIGTERM (handler flips an AtomicBool) AND
// socket/setsockopt(SO_REUSEADDR)/bind/listen — then wrap the fd with
// TcpListener::from_raw_fd. C01/C03: POST / -> 200 echoing exact bytes with
// Content-Length. C04: a non-blocking accept loop polls the stop flag and exits
// 0; an in-flight response (set blocking) completes before the loop notices.
// `?delay_ms=N` is TEST-ONLY: the head is written+flushed before the sleep.
// Build: rustc -O server.rs

use std::env;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::os::unix::io::FromRawFd;
use std::process;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time::Duration;

#[allow(non_camel_case_types)]
mod libc {
    extern "C" {
        pub fn socket(domain: i32, ty: i32, protocol: i32) -> i32;
        pub fn setsockopt(fd: i32, level: i32, optname: i32, optval: *const u8, optlen: u32) -> i32;
        pub fn bind(fd: i32, addr: *const u8, addrlen: u32) -> i32;
        pub fn listen(fd: i32, backlog: i32) -> i32;
        pub fn signal(signum: i32, handler: extern "C" fn(i32)) -> usize;
    }
}

static STOP: AtomicBool = AtomicBool::new(false);

extern "C" fn on_term(_sig: i32) {
    STOP.store(true, Ordering::SeqCst);
}

// linux/x86_64 socket constants
const AF_INET: i32 = 2;
const SOCK_STREAM: i32 = 1;
const SOL_SOCKET: i32 = 1;
const SO_REUSEADDR: i32 = 2;
const SIGTERM: i32 = 15;

fn main() {
    let port: u16 = env::var("PROOF_PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8080);

    let listener = unsafe {
        libc::signal(SIGTERM, on_term);
        let fd = libc::socket(AF_INET, SOCK_STREAM, 0);
        if fd < 0 {
            process::exit(1);
        }
        let one: i32 = 1;
        libc::setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one as *const i32 as *const u8, 4);

        // struct sockaddr_in: family(2) port(2,big-endian) addr(4) pad(8) = 16
        let mut sa = [0u8; 16];
        sa[0] = (AF_INET as u16 & 0xff) as u8;
        sa[1] = ((AF_INET as u16 >> 8) & 0xff) as u8;
        sa[2] = (port >> 8) as u8;
        sa[3] = (port & 0xff) as u8;
        sa[4] = 127;
        sa[5] = 0;
        sa[6] = 0;
        sa[7] = 1;
        if libc::bind(fd, sa.as_ptr(), 16) < 0 {
            process::exit(1);
        }
        if libc::listen(fd, 16) < 0 {
            process::exit(1);
        }
        TcpListener::from_raw_fd(fd)
    };
    listener.set_nonblocking(true).ok();

    loop {
        if STOP.load(Ordering::SeqCst) {
            break;
        }
        match listener.accept() {
            Ok((mut stream, _)) => {
                stream.set_nonblocking(false).ok();
                handle(&mut stream);
            }
            Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                thread::sleep(Duration::from_millis(10));
            }
            Err(_) => {
                thread::sleep(Duration::from_millis(10));
            }
        }
    }
    process::exit(0);
}

fn handle(stream: &mut TcpStream) {
    let mut buf: Vec<u8> = Vec::new();
    let mut byte = [0u8; 1];
    loop {
        match stream.read(&mut byte) {
            Ok(0) => return,
            Ok(_) => {
                buf.push(byte[0]);
                let len = buf.len();
                if len >= 4 && &buf[len - 4..] == b"\r\n\r\n" {
                    break;
                }
            }
            Err(_) => return,
        }
    }
    let head = String::from_utf8_lossy(&buf).to_lowercase();
    let clen: usize = field_digits(&head, "content-length:");
    let delay: u64 = field_digits(&head, "delay_ms=") as u64;

    let mut body = vec![0u8; clen];
    let mut got = 0;
    while got < clen {
        match stream.read(&mut body[got..]) {
            Ok(0) => break,
            Ok(n) => got += n,
            Err(_) => break,
        }
    }
    body.truncate(got);

    let resp_head = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
        got
    );
    let _ = stream.write_all(resp_head.as_bytes());
    let _ = stream.flush(); // commit headers (sync point)
    if delay > 0 {
        thread::sleep(Duration::from_millis(delay));
    }
    let _ = stream.write_all(&body);
    let _ = stream.flush();
}

// first run of ASCII digits immediately after `key` (after optional spaces)
fn field_digits(haystack: &str, key: &str) -> usize {
    if let Some(i) = haystack.find(key) {
        let rest = haystack[i + key.len()..].trim_start();
        let digits: String = rest.chars().take_while(|c| c.is_ascii_digit()).collect();
        digits.parse().unwrap_or(0)
    } else {
        0
    }
}
