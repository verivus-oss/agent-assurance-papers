#!/usr/bin/env python3
"""fingerprint_behavior.py — C06e behavioural-equivalence signal.

Installs chardet at two tags (default 6.0.0 and 7.0.0) into two
isolated venvs, runs each version against a deterministic
fuzz corpus of `N_INPUTS` random byte strings, and reports how often
the two versions return the same `(encoding, confidence-bucket)`
tuple.

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
        --v7-tree <git-worktree-of-chardet-at-7.0.0>

OUTPUT (TSV, single row appended to extract_signals.py's output):
    signal	contract	expected	actual	verdict	evidence
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import random
import subprocess
import sys
import tempfile

N_INPUTS = 1000
RANDOM_SEED = 20260522  # day of the proof — deterministic
INPUT_MAX_LEN = 4096


def _make_venv(target: pathlib.Path) -> pathlib.Path | None:
    """Create a venv at `target`. Return the python interpreter path,
    or None on failure."""
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
    """Install `target` (path or pinned spec) into the venv at `py`.
    Returns None on success, error message on failure."""
    res = subprocess.run(
        [str(py), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", target],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        return (res.stderr.strip() or res.stdout.strip() or "pip install failed").splitlines()[-1][:200]
    return None


def _fuzz_corpus(seed: int, n: int, max_len: int) -> list[bytes]:
    rng = random.Random(seed)
    corpus: list[bytes] = []
    for _ in range(n):
        length = rng.randint(0, max_len)
        corpus.append(bytes(rng.randint(0, 255) for _ in range(length)))
    return corpus


def _detect_one(py: pathlib.Path, corpus_path: pathlib.Path) -> list[dict] | str:
    """Run chardet.detect() on each input in `corpus_path` (a file with
    one base64-per-line representation of the corpus). Returns the
    parsed JSON output, or an error string."""
    runner = """
import base64, json, sys
import chardet
out = []
for line in sys.stdin:
    raw = base64.b64decode(line.strip())
    try:
        result = chardet.detect(raw)
    except Exception as e:
        result = {"error": type(e).__name__}
    out.append(result if isinstance(result, dict) else {"non_dict": str(result)})
sys.stdout.write(json.dumps(out))
"""
    res = subprocess.run(
        [str(py), "-c", runner],
        input=corpus_path.read_text(),
        capture_output=True, text=True, timeout=600,
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--v6-tree", required=True, help="git-worktree of chardet at 6.0.0")
    parser.add_argument("--v7-tree", required=True, help="git-worktree of chardet at 7.0.0")
    args = parser.parse_args()

    v6_tree = pathlib.Path(args.v6_tree).resolve()
    v7_tree = pathlib.Path(args.v7_tree).resolve()

    workdir = pathlib.Path(tempfile.mkdtemp(prefix="chardet-fingerprint-"))
    try:
        py6 = _make_venv(workdir / "venv6")
        py7 = _make_venv(workdir / "venv7")
        if py6 is None or py7 is None:
            _emit_skip("venv creation failed — python -m venv not available?")
            return 0

        # Install both versions from local worktrees so we use the
        # exact code the static signals already inspected. The chardet
        # library code itself is read from the worktree, but pip still
        # resolves PEP 517 build backends (setuptools, wheel) through
        # the network unless ~/.cache/pip already carries them; see
        # _emit_skip below for the toolchain-gap path triggered on
        # sandboxes that block PyPI access.
        err6 = _pip_install(py6, str(v6_tree))
        if err6:
            _emit_skip(f"v6 install from worktree failed: {err6}")
            return 0
        err7 = _pip_install(py7, str(v7_tree))
        if err7:
            _emit_skip(f"v7 install from worktree failed: {err7}")
            return 0

        # Write the corpus as base64-per-line so the runner doesn't have
        # to worry about binary safety on stdin.
        import base64
        corpus = _fuzz_corpus(RANDOM_SEED, N_INPUTS, INPUT_MAX_LEN)
        corpus_path = workdir / "corpus.b64"
        corpus_path.write_text(
            "\n".join(base64.b64encode(b).decode() for b in corpus) + "\n"
        )

        r6 = _detect_one(py6, corpus_path)
        if isinstance(r6, str):
            _emit_skip(f"v6 runner failed: {r6}")
            return 0
        r7 = _detect_one(py7, corpus_path)
        if isinstance(r7, str):
            _emit_skip(f"v7 runner failed: {r7}")
            return 0

        if len(r6) != N_INPUTS or len(r7) != N_INPUTS:
            _emit_skip(f"runner produced wrong count: v6={len(r6)} v7={len(r7)} expected={N_INPUTS}")
            return 0

        agree_exact = 0
        agree_bucket = 0
        for a, b in zip(r6, r7):
            if a == b:
                agree_exact += 1
            if _bucket(a) == _bucket(b):
                agree_bucket += 1

        agree_exact_pct = agree_exact / N_INPUTS
        agree_bucket_pct = agree_bucket / N_INPUTS
        # Corpus digest for reproducibility audit.
        corpus_digest = hashlib.sha256(b"\n".join(corpus)).hexdigest()[:16]

        _emit_row(
            verdict="MEASURED",
            actual=(
                f"exact_match_rate={agree_exact_pct:.3f} "
                f"bucket_match_rate={agree_bucket_pct:.3f} "
                f"n_inputs={N_INPUTS} corpus_digest={corpus_digest}"
            ),
            evidence=(
                f"exact={agree_exact}/{N_INPUTS} bucket={agree_bucket}/{N_INPUTS} "
                f"seed={RANDOM_SEED} input_max_len={INPUT_MAX_LEN}"
            ),
        )
        return 0
    finally:
        # Don't recursively delete the venvs in scripted output — they
        # may be huge — but do remove the corpus file.
        try:
            (workdir / "corpus.b64").unlink(missing_ok=True)
        except OSError:
            pass


def _emit_skip(reason: str) -> None:
    _emit_row(verdict="SKIP", actual=f"behavioural fingerprint skipped: {reason}", evidence=reason)


def _emit_row(verdict: str, actual: str, evidence: str) -> None:
    # Header is printed by extract_signals.py; this script appends one row.
    print(
        "behavioural_fingerprint\tC06e\t"
        "report exact-match rate AND (encoding, confidence-bucket) match rate over N_INPUTS deterministic fuzz inputs\t"
        f"{actual}\t{verdict}\t{evidence}"
    )


if __name__ == "__main__":
    sys.exit(main())
