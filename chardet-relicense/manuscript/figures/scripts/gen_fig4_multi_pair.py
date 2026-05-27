#!/usr/bin/env python3
"""gen_fig4_multi_pair.py — produce fig4_multi_pair.pdf.

Reads `chardet-relicense/proof-bundle/results/<pair>/witness.tsv` for the
three calibration pairs and renders a 4-signal x 3-pair grouped bar chart
(C06a, C06b, C06c, C06e). C06d is left to the table — it has multiple
sub-counts and doesn't compress well into a bar.

The figure exists because the headline visual finding — that v6/v7 is
NOT the highest bar on C06a/C06c, and that C06e separates "evolutionary
rewrite" from "replacement" in the opposite direction the v1 narrative
predicts — is much easier to see as bars than as a table.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

_REPO = pathlib.Path(__file__).resolve().parents[4]
RESULTS = _REPO / "chardet-relicense" / "proof-bundle" / "results"
FIG_OUT = _REPO / "chardet-relicense" / "manuscript" / "figures" / "fig4_multi_pair.pdf"

PAIRS = ("v6_v7", "v5_v6", "v6_charset_norm")
PAIR_LABEL = {
    "v6_v7": "chardet 6 vs 7\n(v1 headline)",
    "v5_v6": "chardet 5 vs 6\n(calibration: same-project)",
    "v6_charset_norm": "chardet 6 vs charset-norm 3.4.7\n(calibration: independent)",
}


def _read_number(pair: str, contract: str, key: str) -> float:
    tsv = (RESULTS / pair / "witness.tsv").read_text()
    for line in tsv.splitlines():
        if not line or line.startswith("#") or line.startswith("signal\t"):
            continue
        cells = line.split("\t")
        if len(cells) < 6 or cells[1] != contract:
            continue
        m = re.search(rf"{re.escape(key)}=([0-9.eE+-]+)", cells[3])
        if m:
            return float(m.group(1))
    return float("nan")


def main() -> int:
    signals = [
        ("C06a: call-graph topology similarity", "C06a", "similarity"),
        ("C06b: import-edge Jaccard", "C06b", "jaccard"),
        ("C06c: control-flow cosine", "C06c", "cosine"),
        ("C06e: behavioural exact-match rate", "C06e", "exact_match_rate"),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(13.5, 3.6), sharey=True)
    colors = ["#4c72b0", "#dd8452", "#55a868"]  # consistent per-pair colors

    for ax, (title, contract, key) in zip(axes, signals):
        values = [_read_number(p, contract, key) for p in PAIRS]
        bars = ax.bar(range(len(PAIRS)), values, color=colors, edgecolor="black", linewidth=0.6)
        ax.set_xticks(range(len(PAIRS)))
        ax.set_xticklabels([PAIR_LABEL[p] for p in PAIRS], fontsize=7.5, rotation=0)
        ax.set_title(title, fontsize=9.5)
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.6)
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.02, f"{v:.3f}",
                    ha="center", va="bottom", fontsize=8.5)

    axes[0].set_ylabel("Similarity / rate (0--1)", fontsize=9.5)
    fig.suptitle(
        "Multi-pair calibration of structural and behavioural similarity signals.\n"
        "v6 vs v7 (the v1 headline) is NOT the highest bar on C06a or C06c; "
        "C06e separates evolutionary rewrites from replacements.",
        fontsize=10.5, y=1.04,
    )
    fig.tight_layout()
    FIG_OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_OUT, bbox_inches="tight")
    print(f"wrote {FIG_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
