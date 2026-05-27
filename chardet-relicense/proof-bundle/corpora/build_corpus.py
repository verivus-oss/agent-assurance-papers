#!/usr/bin/env python3
"""build_corpus.py — assemble the realistic-input corpus for C06e.

This script materialises the files referenced by MANIFEST.tsv into
`./items/<bucket>/<id>.bin` and re-computes their sha256 digests.

Sources (all public-domain or permissively licensed; see MANIFEST.tsv
for per-item attribution):

  html_latin   Wikipedia article HTML (English), CC BY-SA 4.0,
               truncated to <= 8 KiB so the bytes can be committed.
  html_cjk     Wikipedia article HTML (Japanese, Chinese), CC BY-SA 4.0,
               same truncation policy.
  email_mime   Synthetic RFC 822 / MIME messages constructed by this
               script. The headers follow RFC 2822; the bodies embed
               short public-domain text (UDHR Article 1, several
               languages) so the bytes are 100% redistributable.
  multilingual_utf8 / _gb18030 / _shiftjis / _windows1252 / _iso88591
               UDHR Article 1 translations (United Nations, public
               domain), encoded into each target encoding by Python's
               codecs. The Unicode source is hard-coded below.
  short_snippets
               Hand-written short fragments (< 100 bytes) in mixed
               encodings.
  malformed    Concatenations and re-encodings designed to produce
               mojibake-like byte sequences.
  random_control
               The legacy 1000-input random-bytes corpus (seed
               20260522, max_len 4096) from fingerprint_behavior.py
               v1, materialised here as a single .bin per item so the
               same harness path can iterate it.

CRITICAL: This script does NOT include any fixture from chardet's own
`tests/` or `test/` directories. Using the project's test data to
test the project is circular; the entire point of C06e v2 is to feed
v6 and v7 inputs they have never been tuned against.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import pathlib
import random
import sys
import urllib.request

# ---------------------------------------------------------------------
# UDHR Article 1 — public-domain text published by the UN. Used by
# Unicode CLDR as its canonical multilingual sample. Plain English
# attribution: "All human beings are born free and equal in dignity
# and rights ..."
#
# Multiple languages give the chardet detectors something to chew on
# in each of the encodings we want to exercise.
# ---------------------------------------------------------------------

UDHR_TEXTS: dict[str, str] = {
    # Latin script
    "en": (
        "All human beings are born free and equal in dignity and rights. "
        "They are endowed with reason and conscience and should act towards "
        "one another in a spirit of brotherhood."
    ),
    "fr": (
        "Tous les êtres humains naissent libres et égaux en dignité "
        "et en droits. Ils sont doués de raison et de conscience et "
        "doivent agir les uns envers les autres dans un esprit de fraternité."
    ),
    "de": (
        "Alle Menschen sind frei und gleich an Würde und Rechten geboren. "
        "Sie sind mit Vernunft und Gewissen begabt und sollen einander im "
        "Geiste der Brüderlichkeit begegnen."
    ),
    "es": (
        "Todos los seres humanos nacen libres e iguales en dignidad y derechos "
        "y, dotados como están de razón y conciencia, deben comportarse "
        "fraternalmente los unos con los otros."
    ),
    # CJK
    "zh": (
        "人人生而自由，在尊严和权利上一律平等。"
        "他们赋有理性和良心，并应以兄弟关系的精神相对待。"
    ),
    "ja": (
        "すべての人間は、生まれながらにして自由であり、"
        "かつ、尊厳と権利とについて平等である。"
        "人間は、理性と良心とを授けられており、"
        "互いに同胞の精神をもって行動しなければならない。"
    ),
    "ko": (
        "모든 인간은 태어날 때부터 자유롭고 "
        "그 존엄과 권리에 있어 동등하다. "
        "인간은 천부적으로 이성과 양심을 "
        "부여받았으며 서로 형제애의 정신으로 "
        "행동하여야 한다."
    ),
    # Cyrillic
    "ru": (
        "Все люди рождаются "
        "свободными и равными "
        "в своем достоинстве и правах."
    ),
    # Arabic
    "ar": (
        "يولد جميع الناس "
        "أحرارًا متساوين "
        "في الكرامة والحقوق."
    ),
}

WIKIPEDIA_ARTICLES = [
    # (bucket, item_id, lang_code, title)
    ("html_latin",  "wikipedia_en_hello",      "en", "Hello"),
    ("html_latin",  "wikipedia_en_unicode",    "en", "Unicode"),
    ("html_latin",  "wikipedia_fr_bonjour",    "fr", "Bonjour"),
    ("html_latin",  "wikipedia_de_guten_tag",  "de", "Guten_Tag"),
    ("html_cjk",    "wikipedia_zh_hanzi",      "zh", "%E6%BC%A2%E5%AD%97"),   # Hanzi
    ("html_cjk",    "wikipedia_ja_aisatsu",    "ja", "%E6%8C%A8%E6%8B%B6"),   # Aisatsu
    ("html_cjk",    "wikipedia_ko_hangeul",    "ko", "%ED%95%9C%EA%B8%80"),   # Hangeul
]

# Tail-truncate fetched HTML so we keep individual files modest. The
# detector should already be saturated on 8 KiB of body content.
HTML_TRUNCATE_BYTES = 8192

# Public-domain RFCs (RFC 5378 declares pre-1991 RFCs available to be
# extracted into derivative works; RFC bodies themselves carry an IETF
# trust copyright that permits redistribution. We pick small ones.)
RFC_FILES = [
    ("rfc822",  822,   2048),
    ("rfc2822", 2822,  4096),
    ("rfc1939", 1939,  4096),  # POP3 — short, ASCII, line-folded
    ("rfc3501", 3501,  4096),  # IMAP4rev1 — ASCII, formal grammar
]

USER_AGENT = (
    "agent-assurance-papers/0.1 corpus-builder "
    "(research; chardet-relicense paper v2; werner@verivus.com)"
)


def _http_get(url: str, timeout: float = 20.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _write(path: pathlib.Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _make_email_mime(text: str, charset: str, content_xfer_encoding: str = "8bit") -> bytes:
    """Construct a small RFC 2822 / MIME message with body text in the
    given charset. Headers are pure ASCII; body is encoded into the
    requested charset."""
    body = text.encode(charset)
    # CRLF line endings — what real mail relays produce.
    headers = (
        "From: corpus-builder@example.invalid\r\n"
        "To: chardet-fingerprint@example.invalid\r\n"
        "Subject: UDHR Article 1 sample\r\n"
        "Date: Thu, 28 May 2026 00:00:00 +0000\r\n"
        "MIME-Version: 1.0\r\n"
        f"Content-Type: text/plain; charset={charset}\r\n"
        f"Content-Transfer-Encoding: {content_xfer_encoding}\r\n"
        "\r\n"
    ).encode("ascii")
    return headers + body


def _build_html_corpus(items_dir: pathlib.Path) -> list[tuple[str, str, str, str, str, str, int, str]]:
    """Fetch a small set of Wikipedia articles and store truncated HTML.
    Returns rows for the manifest."""
    rows: list[tuple[str, str, str, str, str, str, int, str]] = []
    today = dt.date.today().isoformat()
    for bucket, item_id, lang, title in WIKIPEDIA_ARTICLES:
        url = f"https://{lang}.wikipedia.org/wiki/{title}"
        try:
            raw = _http_get(url)
        except Exception as e:
            print(f"  SKIP {item_id}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        # Truncate at a UTF-8 boundary by decoding lossily then re-
        # encoding the prefix. Wikipedia is always UTF-8.
        text = raw.decode("utf-8", errors="replace")
        truncated = text.encode("utf-8")[:HTML_TRUNCATE_BYTES]
        # Snap to UTF-8 boundary: drop any trailing continuation bytes.
        while truncated and (truncated[-1] & 0xC0) == 0x80:
            truncated = truncated[:-1]
        path = items_dir / bucket / f"{item_id}.html"
        _write(path, truncated)
        rows.append((
            bucket, item_id, "http_fetch", url, "CC-BY-SA-4.0",
            today, len(truncated), _sha256(truncated),
        ))
        print(f"  ok   {bucket}/{item_id}  {len(truncated)} bytes")
    return rows


def _build_email_corpus(items_dir: pathlib.Path) -> list[tuple]:
    """Synthesize a handful of RFC 822 / MIME messages, each carrying
    a UDHR Article 1 body in a different charset."""
    rows: list[tuple] = []
    today = dt.date.today().isoformat()
    mime_specs = [
        ("email_utf8_fr",       "fr", "utf-8",        "8bit"),
        ("email_utf8_zh",       "zh", "utf-8",        "8bit"),
        ("email_iso88591_de",   "de", "iso-8859-1",   "8bit"),
        ("email_windows1252_es","es", "windows-1252", "8bit"),
        ("email_gb18030_zh",    "zh", "gb18030",      "8bit"),
        ("email_shiftjis_ja",   "ja", "shift_jis",    "8bit"),
        ("email_ascii_en",      "en", "ascii",        "7bit"),
    ]
    for item_id, lang, charset, cte in mime_specs:
        try:
            text = UDHR_TEXTS[lang]
            msg = _make_email_mime(text, charset, cte)
        except UnicodeEncodeError as e:
            print(f"  SKIP {item_id}: encode error {e}", file=sys.stderr)
            continue
        path = items_dir / "email_mime" / f"{item_id}.eml"
        _write(path, msg)
        rows.append((
            "email_mime", item_id, "synthesized",
            "constructed from UDHR Art.1 (UN public-domain text) + RFC 2822 headers",
            "public-domain (UDHR text) + Apache-2.0 (this synthesis script)",
            today, len(msg), _sha256(msg),
        ))
        print(f"  ok   email_mime/{item_id}  {len(msg)} bytes")
    return rows


def _build_multilingual_corpus(items_dir: pathlib.Path) -> list[tuple]:
    """Encode UDHR Article 1 in each target encoding. One file per
    (encoding, language) pair where the language is representable."""
    rows: list[tuple] = []
    today = dt.date.today().isoformat()
    plan = [
        # (bucket, encoding, [lang_codes...])
        ("multilingual_utf8",       "utf-8",        ["en", "fr", "de", "es", "zh", "ja", "ko", "ru", "ar"]),
        ("multilingual_gb18030",    "gb18030",      ["zh", "en", "ja", "ko", "ru"]),
        ("multilingual_shiftjis",   "shift_jis",    ["ja", "en"]),
        ("multilingual_windows1252","windows-1252", ["en", "fr", "de", "es"]),
        ("multilingual_iso88591",   "iso-8859-1",   ["en", "fr", "de", "es"]),
    ]
    for bucket, encoding, langs in plan:
        for lang in langs:
            text = UDHR_TEXTS[lang]
            try:
                payload = text.encode(encoding)
            except UnicodeEncodeError as e:
                print(f"  SKIP {bucket}/{lang}: {e}", file=sys.stderr)
                continue
            item_id = f"udhr_art1_{lang}_{encoding.replace('-', '').replace('_', '')}"
            path = items_dir / bucket / f"{item_id}.txt"
            _write(path, payload)
            rows.append((
                bucket, item_id, "synthesized",
                "UDHR Article 1 (UN public-domain text); encoded by build_corpus.py",
                "public-domain (UDHR text)",
                today, len(payload), _sha256(payload),
            ))
            print(f"  ok   {bucket}/{item_id}  {len(payload)} bytes")
    return rows


def _build_rfc_corpus(items_dir: pathlib.Path) -> list[tuple]:
    """Fetch a few small RFC bodies — pure ASCII, line-folded, plenty
    of structure for an encoding detector to chew on. Cap file size."""
    rows: list[tuple] = []
    today = dt.date.today().isoformat()
    for name, num, cap in RFC_FILES:
        url = f"https://www.rfc-editor.org/rfc/rfc{num}.txt"
        try:
            raw = _http_get(url)
        except Exception as e:
            print(f"  SKIP {name}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        snippet = raw[:cap]
        path = items_dir / "rfc_ascii" / f"{name}.txt"
        _write(path, snippet)
        rows.append((
            "rfc_ascii", name, "http_fetch", url,
            "RFC-public-domain (RFC 5378 + IETF Trust Legal Provisions; redistribution allowed)",
            today, len(snippet), _sha256(snippet),
        ))
        print(f"  ok   rfc_ascii/{name}  {len(snippet)} bytes")
    return rows


def _build_short_snippets(items_dir: pathlib.Path) -> list[tuple]:
    """Hand-curated short fragments under 100 bytes each. These probe
    the regime where the detector has very little signal."""
    rows: list[tuple] = []
    today = dt.date.today().isoformat()
    snippets: list[tuple[str, bytes]] = [
        ("hi_ascii",         b"hi"),
        ("hello_world",      b"hello, world!"),
        ("digits",           b"1234567890"),
        ("html_tag",         b"<p>hello</p>"),
        ("subject_ascii",    b"Subject: tea\r\n"),
        ("utf8_bom_ascii",   b"\xef\xbb\xbfBOM-prefixed UTF-8."),
        ("utf16le_bom",      b"\xff\xfeh\x00i\x00"),
        ("utf16be_bom",      b"\xfe\xff\x00h\x00i"),
        ("french_iso88591",  "café et croissant".encode("iso-8859-1")),
        ("german_iso88591",  "Straße und Würde".encode("iso-8859-1")),
        ("spanish_w1252",    "mañana señora".encode("windows-1252")),
        ("japanese_sjis",    "こんにちは".encode("shift_jis")),
        ("chinese_gb18030",  "你好世界".encode("gb18030")),
        ("russian_utf8",     "Привет".encode("utf-8")),
        ("arabic_utf8",      "مرحبا".encode("utf-8")),
        ("korean_utf8",      "안녕하세요".encode("utf-8")),
    ]
    for item_id, payload in snippets:
        assert len(payload) < 100, f"{item_id} is {len(payload)} bytes, over 100"
        path = items_dir / "short_snippets" / f"{item_id}.bin"
        _write(path, payload)
        rows.append((
            "short_snippets", item_id, "synthesized",
            "hand-curated short fragments (greetings, BOMs, headers)",
            "Apache-2.0 (this synthesis script)",
            today, len(payload), _sha256(payload),
        ))
    print(f"  ok   short_snippets/* x {len(snippets)}")
    return rows


def _build_malformed(items_dir: pathlib.Path) -> list[tuple]:
    """Concatenated mojibake / mixed-encoding inputs. Realistic for the
    'mailing-list archive ate someone's resume' scenario."""
    rows: list[tuple] = []
    today = dt.date.today().isoformat()
    en = UDHR_TEXTS["en"]
    fr = UDHR_TEXTS["fr"]
    zh = UDHR_TEXTS["zh"]
    ja = UDHR_TEXTS["ja"]
    samples: list[tuple[str, bytes]] = [
        # UTF-8 text decoded as Latin-1 then re-encoded as UTF-8 — the
        # classic 'double-encoded' mojibake.
        ("utf8_double_encoded_fr",
            fr.encode("utf-8").decode("latin-1").encode("utf-8")),
        # GB18030 zh chunk concatenated with Shift_JIS ja chunk.
        ("mixed_gb18030_then_shiftjis",
            zh.encode("gb18030") + ja.encode("shift_jis")),
        # Latin-1 mixed with UTF-8 mid-stream.
        ("latin1_then_utf8_then_latin1",
            "café ".encode("iso-8859-1") +
            "你好 ".encode("utf-8") +
            "Straße".encode("iso-8859-1")),
        # Truncated UTF-8 — chop a multibyte sequence in half.
        ("utf8_truncated_midcodepoint",
            zh.encode("utf-8")[:-2] + b"\xe4\xb8"),
        # ASCII English with a single random high byte planted in.
        ("ascii_with_random_high_byte",
            en.encode("ascii") + b"\xc3" + en.encode("ascii")),
        # Windows-1252 quotes plus UTF-8 emoji-like sequence.
        ("w1252_smartquotes_plus_utf8",
            b"He said \x93hello\x94. " + "Smile \U0001f603!".encode("utf-8")),
    ]
    for item_id, payload in samples:
        path = items_dir / "malformed" / f"{item_id}.bin"
        _write(path, payload)
        rows.append((
            "malformed", item_id, "synthesized",
            "constructed mojibake / mixed-encoding via build_corpus.py",
            "public-domain (UDHR text) + Apache-2.0 (script)",
            today, len(payload), _sha256(payload),
        ))
    print(f"  ok   malformed/* x {len(samples)}")
    return rows


def _build_random_control(items_dir: pathlib.Path, n: int = 1000, seed: int = 20260522, max_len: int = 4096) -> list[tuple]:
    """The original 1000-input random-bytes corpus — preserved as a
    robustness control bucket so v1 vs v2 numbers stay comparable."""
    rows: list[tuple] = []
    today = dt.date.today().isoformat()
    rng = random.Random(seed)
    bucket_dir = items_dir / "random_control"
    bucket_dir.mkdir(parents=True, exist_ok=True)
    # One file packs all 1000 inputs as a length-prefixed stream so we
    # don't explode the inode count on the filesystem. The harness
    # knows how to unpack this.
    packed = bytearray()
    for _ in range(n):
        length = rng.randint(0, max_len)
        b = bytes(rng.randint(0, 255) for _ in range(length))
        packed.extend(len(b).to_bytes(4, "big"))
        packed.extend(b)
    packed = bytes(packed)
    path = bucket_dir / "random_fuzz_1k.packed"
    _write(path, packed)
    rows.append((
        "random_control", "random_fuzz_1k", "synthesized",
        f"deterministic random bytes; rng=random.Random(seed={seed}); n={n}; max_len={max_len}; format=length(4-byte big-endian)+payload",
        "Apache-2.0 (this synthesis script)",
        today, len(packed), _sha256(packed),
    ))
    print(f"  ok   random_control/random_fuzz_1k  {len(packed)} bytes (packed {n} items)")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--items-dir", default=None, help="where to materialise items (default: ./items)")
    parser.add_argument("--manifest", default=None, help="manifest tsv path (default: ./MANIFEST.tsv)")
    parser.add_argument("--skip-network", action="store_true", help="skip http-fetched buckets (html_*, rfc_ascii)")
    args = parser.parse_args()

    base = pathlib.Path(__file__).resolve().parent
    items_dir = pathlib.Path(args.items_dir) if args.items_dir else base / "items"
    manifest_path = pathlib.Path(args.manifest) if args.manifest else base / "MANIFEST.tsv"

    print(f"building corpus into {items_dir}")
    all_rows: list[tuple] = []

    if not args.skip_network:
        print("[wikipedia html]")
        all_rows += _build_html_corpus(items_dir)
        print("[rfcs]")
        all_rows += _build_rfc_corpus(items_dir)
    else:
        print("[wikipedia html] SKIPPED (--skip-network)")
        print("[rfcs] SKIPPED (--skip-network)")
    print("[email mime]")
    all_rows += _build_email_corpus(items_dir)
    print("[multilingual plain text]")
    all_rows += _build_multilingual_corpus(items_dir)
    print("[short snippets]")
    all_rows += _build_short_snippets(items_dir)
    print("[malformed]")
    all_rows += _build_malformed(items_dir)
    print("[random control]")
    all_rows += _build_random_control(items_dir)

    # Write the manifest.
    header = (
        "bucket", "item_id", "source_type", "origin",
        "license", "accession_date", "size_bytes", "sha256",
    )
    with manifest_path.open("w", encoding="utf-8") as f:
        f.write("\t".join(header) + "\n")
        for row in sorted(all_rows, key=lambda r: (r[0], r[1])):
            f.write("\t".join(str(x) for x in row) + "\n")
    print(f"\nwrote {manifest_path}  ({len(all_rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
