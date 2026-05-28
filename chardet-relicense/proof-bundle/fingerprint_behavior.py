#!/usr/bin/env python3
"""fingerprint_behavior.py — C06e behavioural-equivalence signal.

Installs chardet at two tags (default 6.0.0 and 7.0.0) into two
isolated venvs, runs each version against a multi-bucket corpus
(`corpora/MANIFEST.tsv`), and reports how often the two versions
return the same `(encoding, confidence-bucket)` tuple — per corpus
bucket and in aggregate.

v2 (revised in response to reviewer R3): the corpus is no longer just
1000 random byte strings. It now includes HTML pages (Wikipedia, Latin
and CJK), RFC 822 / MIME messages, multilingual plain text in UTF-8,
GB18030, Shift_JIS, Windows-1252 and ISO-8859-1, short snippets,
malformed / mixed-encoding bytes, and the legacy 1000-random-byte
distribution as a robustness control. The corpus is built by
`corpora/build_corpus.py` and described per item in
`corpora/MANIFEST.tsv`. The random-bytes-only result from v1 is
preserved as the `random_control` bucket.

Behavioural equivalence is the strongest form of contract-preservation
evidence available: an AI rewrite that is *operationally
indistinguishable* from the original on a representative input
distribution is preserving the original's behavioural contract by any
reasonable test.

If install fails for either version (no internet, no compiler, missing
pip toolchain) the script emits a SKIP row with the literal reason —
distinguished from a FAIL the way the proof-hello-world C01 harness
distinguishes SKIP from FAIL.

USAGE:
    fingerprint_behavior.py \\
        --v6-tree <git-worktree-of-chardet-at-6.0.0> \\
        --v7-tree <git-worktree-of-chardet-at-7.0.0> \\
        [--corpus-dir <path-to-corpora-dir>] \\
        [--report-json <path-to-write-per-bucket-json>]

OUTPUT (TSV, multiple rows appended to extract_signals.py's output):
    signal                       contract  expected  actual  verdict  evidence
    behavioural_fingerprint      C06e      ...       ...     ...      ...
    behavioural_fingerprint:<b>  C06e      ...       ...     ...      ...

The first row is the aggregate. The remaining rows are one per corpus
bucket present in MANIFEST.tsv.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import pathlib
import random
import subprocess
import sys
import tempfile

# Legacy random-control parameters — frozen so the v1 number remains
# directly comparable inside the random_control bucket.
RANDOM_SEED = 20260522
RANDOM_N_INPUTS = 1000
RANDOM_MAX_LEN = 4096

DEFAULT_CORPUS_DIR_REL = "corpora"
DEFAULT_MANIFEST_NAME = "MANIFEST.tsv"


# ---------------------------------------------------------------------
# venv + install helpers (unchanged from v1).
# ---------------------------------------------------------------------

def _make_venv(target: pathlib.Path) -> pathlib.Path | None:
    target.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        [sys.executable, "-m", "venv", str(target)],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        return None
    py = target / "bin" / "python"
    return py if py.is_file() else None


def _pip_install(py: pathlib.Path, target: str) -> str | None:
    res = subprocess.run(
        [str(py), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", target],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        return (res.stderr.strip() or res.stdout.strip() or "pip install failed").splitlines()[-1][:200]
    return None


# ---------------------------------------------------------------------
# Corpus loaders.
# ---------------------------------------------------------------------

def _load_random_control_packed(path: pathlib.Path) -> list[bytes]:
    """Unpack the length-prefixed random_control file produced by
    build_corpus.py. Format: repeated [4-byte big-endian length][payload]."""
    buf = path.read_bytes()
    out: list[bytes] = []
    i = 0
    while i < len(buf):
        if i + 4 > len(buf):
            break
        n = int.from_bytes(buf[i:i + 4], "big")
        i += 4
        out.append(buf[i:i + n])
        i += n
    return out


def _make_legacy_random_control() -> list[bytes]:
    """Reproduce the v1 corpus from the original RNG params — used as
    a fallback if the packed file is absent from the build (e.g.
    `random_fuzz_1k.packed` is gitignored)."""
    rng = random.Random(RANDOM_SEED)
    out: list[bytes] = []
    for _ in range(RANDOM_N_INPUTS):
        length = rng.randint(0, RANDOM_MAX_LEN)
        out.append(bytes(rng.randint(0, 255) for _ in range(length)))
    return out


def _load_corpus(corpus_dir: pathlib.Path) -> tuple[dict[str, list[tuple[str, bytes]]], str | None]:
    """Read MANIFEST.tsv and return {bucket: [(item_id, bytes), ...]}.
    On failure returns ({}, error_message)."""
    manifest = corpus_dir / DEFAULT_MANIFEST_NAME
    items_root = corpus_dir / "items"
    if not manifest.is_file():
        return {}, f"manifest not found at {manifest}"
    by_bucket: dict[str, list[tuple[str, bytes]]] = {}
    with manifest.open(encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        if header[:2] != ["bucket", "item_id"]:
            return {}, f"manifest header malformed: {header}"
        try:
            sha_col = header.index("sha256")
        except ValueError:
            return {}, "manifest missing sha256 column"
        for lineno, raw in enumerate(f, start=2):
            row = raw.rstrip("\n").split("\t")
            if len(row) < len(header):
                continue
            bucket, item_id = row[0], row[1]
            expected_sha = row[sha_col]
            # Locate the file by scanning items/<bucket>/<item_id>.*
            bucket_dir = items_root / bucket
            if not bucket_dir.is_dir():
                # random_control's packed file may be gitignored; rebuild it
                # from seed on the fly.
                if bucket == "random_control" and item_id == "random_fuzz_1k":
                    payloads = _make_legacy_random_control()
                    by_bucket.setdefault(bucket, []).extend(
                        (f"random_{i:04d}", p) for i, p in enumerate(payloads)
                    )
                    continue
                return {}, f"items dir for bucket {bucket!r} missing at {bucket_dir}"
            candidates = sorted(bucket_dir.glob(f"{item_id}.*"))
            if not candidates:
                if bucket == "random_control" and item_id == "random_fuzz_1k":
                    payloads = _make_legacy_random_control()
                    by_bucket.setdefault(bucket, []).extend(
                        (f"random_{i:04d}", p) for i, p in enumerate(payloads)
                    )
                    continue
                return {}, f"no file matching {bucket}/{item_id}.* (line {lineno})"
            content = candidates[0].read_bytes()
            actual_sha = hashlib.sha256(content).hexdigest()
            if expected_sha and actual_sha != expected_sha:
                return {}, (
                    f"sha256 mismatch for {bucket}/{item_id}: "
                    f"manifest={expected_sha[:16]} on-disk={actual_sha[:16]}"
                )
            if bucket == "random_control" and item_id == "random_fuzz_1k":
                # Unpack the length-prefixed stream into individual inputs.
                payloads = _load_random_control_packed(candidates[0])
                by_bucket.setdefault(bucket, []).extend(
                    (f"random_{i:04d}", p) for i, p in enumerate(payloads)
                )
            else:
                by_bucket.setdefault(bucket, []).append((item_id, content))
    return by_bucket, None


# ---------------------------------------------------------------------
# Runner: detect a list of inputs inside a venv'd subprocess.
# ---------------------------------------------------------------------

def _detect_one(
    py: pathlib.Path, corpus_path: pathlib.Path, module_name: str = "chardet",
) -> list[dict] | str:
    """Run <module>.detect() on each input. Module must expose a
    chardet-compatible detect() returning {"encoding": str|None,
    "confidence": float|None, ...}. charset-normalizer ships a compat
    shim in `charset_normalizer.legacy.detect` re-exported at the
    package root (Q×C integration for v6_charset_norm pair)."""
    runner = f"""
import base64, json, sys
import {module_name} as _det
out = []
for line in sys.stdin:
    raw = base64.b64decode(line.strip())
    try:
        result = _det.detect(raw)
    except Exception as e:
        result = {{"error": type(e).__name__}}
    out.append(result if isinstance(result, dict) else {{"non_dict": str(result)}})
sys.stdout.write(json.dumps(out))
"""
    res = subprocess.run(
        [str(py), "-c", runner],
        input=corpus_path.read_text(),
        capture_output=True, text=True, timeout=900,
    )
    if res.returncode != 0:
        return (res.stderr.strip() or "runner failed").splitlines()[-1][:200]
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError as e:
        return f"runner output not JSON: {e}"


def _bucket(result: dict) -> tuple[str | None, str | None]:
    """Reduce a detect() result to (encoding, confidence-bucket). Buckets:
    'high' >= 0.9, 'med' 0.5..0.9, 'low' < 0.5, 'none' if missing."""
    enc = result.get("encoding") if isinstance(result, dict) else None
    conf = result.get("confidence") if isinstance(result, dict) else None
    if conf is None:
        b = "none"
    elif conf >= 0.9:
        b = "high"
    elif conf >= 0.5:
        b = "med"
    else:
        b = "low"
    return (enc, b)


# Encoding-name normalization tables. v6 emits uppercase aliases
# (`WINDOWS-1252`, `SHIFT_JIS`); v7 emits lowercase canonical names
# (`windows-1252`, `cp932`). Operationally these are the same byte
# decoder, but the literal string labels diverge. The `_norm_enc`
# helper exists so we can also report a label-normalised match rate
# alongside the strict rate, distinguishing 'genuinely different
# decoder picked' from 'same decoder, different label'.
_ENCODING_ALIAS: dict[str, str] = {
    # Case-fold first, then collapse known aliases to a canonical
    # token. Right-hand side is the canonical token.
    "ascii": "ascii",
    "windows-1252": "windows-1252",
    "cp1252": "windows-1252",
    "iso-8859-1": "iso-8859-1",
    "latin-1": "iso-8859-1",
    "shift_jis": "shift_jis",
    "shift-jis": "shift_jis",
    "sjis": "shift_jis",
    "cp932": "shift_jis",  # cp932 is Windows' Shift_JIS variant — operationally compatible for our test text
    "gb18030": "gb18030",
    "gb2312": "gb18030",
    "gbk": "gb18030",
    "utf-8": "utf-8",
    "utf8": "utf-8",
    "utf-16": "utf-16",
    "utf-16le": "utf-16le",
    "utf-16be": "utf-16be",
    "euc-jp": "euc-jp",
    "euc-kr": "euc-kr",
    "big5": "big5",
}


def _norm_enc(name: str | None) -> str | None:
    """Case-fold + alias-collapse an encoding label. Also folds the
    well-known ASCII-vs-Windows-1252 case: when one detector returns
    'ascii' and the other returns 'windows-1252' (or 'iso-8859-1') on
    ASCII-only input, both decoders produce the same bytes, so we
    treat them as the same operational decision.

    NOTE: this folding is intentionally generous. The strict
    exact-match rate (and the (encoding, confidence-bucket) rate) are
    still reported separately, so callers can see both numbers and
    decide for themselves how to weigh label drift vs decoder drift.
    """
    if not name:
        return None
    key = name.strip().casefold()
    return _ENCODING_ALIAS.get(key, key)


def _norm_bucket(result: dict) -> tuple[str | None, str | None]:
    """Like `_bucket`, but with the encoding label normalised."""
    enc, b = _bucket(result)
    # Treat ascii as a special case: ascii is a strict subset of
    # windows-1252 and iso-8859-1, so when one detector picks ascii
    # and the other picks one of those supersets *and* both are at
    # 'high' confidence, that's operationally equivalent on
    # ASCII-only bytes. We collapse all three to 'ascii_or_w1252'
    # only when bucket=='high', which is the regime where the
    # detector means "I'm sure".
    norm = _norm_enc(enc)
    if b == "high" and norm in {"ascii", "windows-1252", "iso-8859-1"}:
        norm = "ascii_or_latin_family"
    return (norm, b)


# ---------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # Pair-agnostic flags (Q's multi-pair extension).
    parser.add_argument("--tree-a", dest="tree_a", help="worktree of side A")
    parser.add_argument("--tree-b", dest="tree_b", help="worktree of side B")
    parser.add_argument("--module-a", dest="module_a", default="chardet",
                        help="python module name to import on side A (default chardet)")
    parser.add_argument("--module-b", dest="module_b", default="chardet",
                        help="python module name to import on side B (default chardet)")
    # Legacy aliases.
    parser.add_argument("--v6-tree", dest="v6_tree", help="legacy alias for --tree-a")
    parser.add_argument("--v7-tree", dest="v7_tree", help="legacy alias for --tree-b")
    parser.add_argument(
        "--corpus-dir",
        default=None,
        help=f"path to the corpora/ dir (default: ./{DEFAULT_CORPUS_DIR_REL} next to this script)",
    )
    parser.add_argument(
        "--report-json",
        default=None,
        help="if set, write per-bucket exact/bucket rates as JSON to this path",
    )
    args = parser.parse_args()

    tree_a_str = args.tree_a or args.v6_tree
    tree_b_str = args.tree_b or args.v7_tree
    if not tree_a_str or not tree_b_str:
        parser.error("must supply --tree-a/--tree-b (or legacy --v6-tree/--v7-tree)")

    v6_tree = pathlib.Path(tree_a_str).resolve()
    v7_tree = pathlib.Path(tree_b_str).resolve()
    module_a = args.module_a
    module_b = args.module_b
    here = pathlib.Path(__file__).resolve().parent
    corpus_dir = pathlib.Path(args.corpus_dir).resolve() if args.corpus_dir else here / DEFAULT_CORPUS_DIR_REL

    by_bucket, err = _load_corpus(corpus_dir)
    if err:
        _emit_skip(f"corpus load failed: {err}")
        return 0
    if not by_bucket:
        _emit_skip("corpus load returned no buckets")
        return 0

    workdir = pathlib.Path(tempfile.mkdtemp(prefix="chardet-fingerprint-"))
    try:
        py6 = _make_venv(workdir / "venv6")
        py7 = _make_venv(workdir / "venv7")
        if py6 is None or py7 is None:
            _emit_skip("venv creation failed — python -m venv not available?")
            return 0

        err6 = _pip_install(py6, str(v6_tree))
        if err6:
            _emit_skip(f"v6 install from worktree failed: {err6}")
            return 0
        err7 = _pip_install(py7, str(v7_tree))
        if err7:
            _emit_skip(f"v7 install from worktree failed: {err7}")
            return 0

        # Run all buckets in a single batched runner invocation per
        # version, to amortise interpreter-startup cost.
        flat_inputs: list[bytes] = []
        flat_keys: list[tuple[str, str]] = []  # (bucket, item_id)
        for bucket, items in sorted(by_bucket.items()):
            for item_id, payload in items:
                flat_keys.append((bucket, item_id))
                flat_inputs.append(payload)

        corpus_path = workdir / "corpus.b64"
        corpus_path.write_text(
            "\n".join(base64.b64encode(b).decode() for b in flat_inputs) + "\n"
        )

        r6 = _detect_one(py6, corpus_path, module_a)
        if isinstance(r6, str):
            _emit_skip(f"side-A runner ({module_a}) failed: {r6}")
            return 0
        r7 = _detect_one(py7, corpus_path, module_b)
        if isinstance(r7, str):
            _emit_skip(f"side-B runner ({module_b}) failed: {r7}")
            return 0

        if len(r6) != len(flat_inputs) or len(r7) != len(flat_inputs):
            _emit_skip(
                f"runner produced wrong count: v6={len(r6)} v7={len(r7)} expected={len(flat_inputs)}"
            )
            return 0

        # Per-bucket aggregation.
        per_bucket: dict[str, dict] = {}
        total_exact = 0
        total_bucket = 0
        total_normalized = 0
        total_n = 0
        for (bucket, item_id), a, b in zip(flat_keys, r6, r7):
            slot = per_bucket.setdefault(bucket, {
                "exact": 0, "bucket": 0, "normalized": 0, "n": 0, "samples": []
            })
            same_exact = (a == b)
            same_bucket = (_bucket(a) == _bucket(b))
            same_normalized = (_norm_bucket(a) == _norm_bucket(b))
            slot["exact"] += int(same_exact)
            slot["bucket"] += int(same_bucket)
            slot["normalized"] += int(same_normalized)
            slot["n"] += 1
            total_exact += int(same_exact)
            total_bucket += int(same_bucket)
            total_normalized += int(same_normalized)
            total_n += 1
            # Keep up to 5 disagreement samples per bucket, for the
            # JSON report — useful when writing up the divergence story.
            if not same_bucket and len(slot["samples"]) < 5:
                slot["samples"].append({
                    "item_id": item_id,
                    "v6": {"encoding": a.get("encoding") if isinstance(a, dict) else None,
                            "confidence": a.get("confidence") if isinstance(a, dict) else None},
                    "v7": {"encoding": b.get("encoding") if isinstance(b, dict) else None,
                            "confidence": b.get("confidence") if isinstance(b, dict) else None},
                    "normalized_agree": same_normalized,
                })

        # Aggregate row (preserves v1 contract: one TSV row labelled C06e).
        agg_exact_rate = total_exact / total_n if total_n else 0.0
        agg_bucket_rate = total_bucket / total_n if total_n else 0.0
        agg_normalized_rate = total_normalized / total_n if total_n else 0.0
        # Corpus digest: hash of the manifest, so reproducers can verify
        # the input set without re-hashing each file.
        manifest_bytes = (corpus_dir / DEFAULT_MANIFEST_NAME).read_bytes()
        corpus_digest = hashlib.sha256(manifest_bytes).hexdigest()[:16]

        _emit_row(
            label="behavioural_fingerprint",
            verdict="MEASURED",
            actual=(
                f"exact_match_rate={agg_exact_rate:.3f} "
                f"bucket_match_rate={agg_bucket_rate:.3f} "
                f"normalized_match_rate={agg_normalized_rate:.3f} "
                f"n_inputs={total_n} corpus_digest={corpus_digest}"
            ),
            evidence=(
                f"exact={total_exact}/{total_n} bucket={total_bucket}/{total_n} "
                f"normalized={total_normalized}/{total_n} "
                f"buckets={len(per_bucket)} manifest={corpus_dir / DEFAULT_MANIFEST_NAME}"
            ),
        )

        # Per-bucket rows. Label = behavioural_fingerprint:<bucket>.
        for bucket in sorted(per_bucket):
            s = per_bucket[bucket]
            ex_rate = s["exact"] / s["n"] if s["n"] else 0.0
            bk_rate = s["bucket"] / s["n"] if s["n"] else 0.0
            nm_rate = s["normalized"] / s["n"] if s["n"] else 0.0
            _emit_row(
                label=f"behavioural_fingerprint:{bucket}",
                verdict="MEASURED",
                actual=(
                    f"exact_match_rate={ex_rate:.3f} "
                    f"bucket_match_rate={bk_rate:.3f} "
                    f"normalized_match_rate={nm_rate:.3f} "
                    f"n_inputs={s['n']}"
                ),
                evidence=(
                    f"exact={s['exact']}/{s['n']} bucket={s['bucket']}/{s['n']} "
                    f"normalized={s['normalized']}/{s['n']}"
                ),
            )

        # Optional JSON report.
        if args.report_json:
            report = {
                "aggregate": {
                    "exact": total_exact,
                    "bucket": total_bucket,
                    "normalized": total_normalized,
                    "n": total_n,
                    "exact_rate": agg_exact_rate,
                    "bucket_rate": agg_bucket_rate,
                    "normalized_rate": agg_normalized_rate,
                    "corpus_digest_manifest": corpus_digest,
                },
                "per_bucket": {
                    b: {
                        "exact": s["exact"],
                        "bucket": s["bucket"],
                        "normalized": s["normalized"],
                        "n": s["n"],
                        "exact_rate": (s["exact"] / s["n"]) if s["n"] else 0.0,
                        "bucket_rate": (s["bucket"] / s["n"]) if s["n"] else 0.0,
                        "normalized_rate": (s["normalized"] / s["n"]) if s["n"] else 0.0,
                        "disagreement_samples": s["samples"],
                    }
                    for b, s in per_bucket.items()
                },
            }
            pathlib.Path(args.report_json).write_text(json.dumps(report, indent=2, sort_keys=True))

        return 0
    finally:
        try:
            (workdir / "corpus.b64").unlink(missing_ok=True)
        except OSError:
            pass


def _emit_skip(reason: str) -> None:
    _emit_row(
        label="behavioural_fingerprint",
        verdict="SKIP",
        actual=f"behavioural fingerprint skipped: {reason}",
        evidence=reason,
    )


def _emit_row(label: str, verdict: str, actual: str, evidence: str) -> None:
    # Header is printed by extract_signals.py; this script appends rows.
    print(
        f"{label}\tC06e\t"
        "report exact-match rate AND (encoding, confidence-bucket) match rate per corpus bucket\t"
        f"{actual}\t{verdict}\t{evidence}"
    )


if __name__ == "__main__":
    sys.exit(main())
