# C06e v2 realistic-input corpus

This directory holds the multi-bucket input corpus the v2 revision of
contract C06e (behavioural fingerprint) runs `chardet.detect()` over,
in both v6.0.0 and v7.0.0, to compute per-bucket exact-match and
bucket-match rates.

The v1 paper exercised C06e on 1000 random byte strings only. Reviewer
R3 (round 1) flagged that as the wrong workload — encoding detectors
are deployed against HTML, mail bodies and multilingual plain text,
not random fuzz. v2 extends the harness to read this manifest and
emit a per-bucket row.

## Files

- `build_corpus.py` — deterministic build script. Fetches Wikipedia
  articles and RFC bodies from public URLs, synthesizes RFC 822 / MIME
  messages and multilingual plain text from public-domain UDHR text,
  hand-curates short snippets and mojibake, and packs the legacy random
  bytes into a single file. Writes `items/<bucket>/<id>.<ext>` and
  rewrites `MANIFEST.tsv`.
- `MANIFEST.tsv` — committed. One row per corpus item. Columns:
  `bucket  item_id  source_type  origin  license  accession_date  size_bytes  sha256`.
- `items/<bucket>/<id>.<ext>` — corpus bytes. Most are committed
  directly (every bucket totals <70 KiB on disk). The single exception
  is `items/random_control/random_fuzz_1k.packed` (1.9 MB), which is
  gitignored — it is fully deterministic from `seed=20260522` and is
  rebuilt by `build_corpus.py`.

## Buckets

| bucket                     | items | total bytes | content                                                                 |
| -------------------------- | ----- | ----------- | ----------------------------------------------------------------------- |
| `html_latin`               | 4     | 32 768      | Wikipedia article HTML (en, fr, de) — Latin-script body content         |
| `html_cjk`                 | 3     | 24 576      | Wikipedia article HTML (zh, ja, ko) — CJK body content                  |
| `rfc_ascii`                | 4     | 14 336      | First N bytes of RFC 822 / 2822 / 1939 / 3501 — pure ASCII              |
| `email_mime`               | 7     | 2 815       | Synthetic RFC 2822 messages, body in ascii / utf-8 / iso-8859-1 / windows-1252 / gb18030 / shift_jis |
| `multilingual_utf8`        | 9     | 1 522       | UDHR Article 1 in 9 languages, encoded UTF-8                            |
| `multilingual_gb18030`     | 5     | 834         | UDHR Article 1 in 5 languages, encoded GB18030                          |
| `multilingual_shiftjis`    | 2     | 340         | UDHR Article 1 in ja, en — encoded Shift_JIS                            |
| `multilingual_windows1252` | 4     | 692         | UDHR Article 1 in en, fr, de, es — encoded Windows-1252                 |
| `multilingual_iso88591`    | 4     | 692         | UDHR Article 1 in en, fr, de, es — encoded ISO-8859-1                   |
| `short_snippets`           | 16    | ~250        | Hand-curated fragments < 100 bytes (BOMs, greetings, short headers)     |
| `malformed`                | 6     | ~3 500      | Concatenated mojibake / double-encoded text / truncated UTF-8           |
| `random_control`           | 1000  | ~1.9 MB     | The original 1000-input random-bytes corpus, length-prefixed packed     |

Exact sizes are in `MANIFEST.tsv`.

## License audit

Every byte in this corpus is one of:

- **Public-domain text** — the UDHR (United Nations General Assembly
  resolution 217 A, 1948) is universally treated as public domain;
  RFC bodies pre-1991 are in the public domain per RFC 5378, and the
  IETF Trust Legal Provisions explicitly permit redistribution.
- **CC BY-SA 4.0** — Wikipedia article HTML (rendered MediaWiki output).
  Wikipedia attribution is included in each fetched file's `<meta>`
  tags; the per-item `origin` column in `MANIFEST.tsv` records the
  source URL.
- **Apache-2.0** — the synthesis script `build_corpus.py` and any
  bytes it constructs from scratch (RFC 822 headers around the UDHR
  bodies, mojibake concatenations, random_control).

`MANIFEST.tsv` has the license per item.

## Anti-circularity rule

We deliberately do **not** import from `chardet/tests/` or any
`*/test/` directory of the chardet repo. Using a project's own
fixtures to test that project's behaviour is circular: those fixtures
are exactly the inputs the maintainers tuned for. C06e is meant to
probe behaviour on inputs the rewrite has **not** been targeted at,
so the corpus is sourced independently.

## Re-fetching

```
python3 build_corpus.py                       # full rebuild
python3 build_corpus.py --skip-network        # skip Wikipedia + RFCs
```

`--skip-network` is the offline path for sandboxes / reviewers without
egress. The synthesized buckets (email_mime, multilingual_*,
short_snippets, malformed, random_control) cover most of the
operational range on their own.
