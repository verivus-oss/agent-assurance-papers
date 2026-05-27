#!/usr/bin/env python3
"""gen_figures.py — produce the figures used in the chardet-relicense paper.

This script intentionally re-runs the same AST analysers the proof bundle
uses (extract_signals.py), so the figures' data is byte-for-byte the same
data the paper's tables cite. It is NOT a copy of those analysers: it
imports them.

Outputs (under chardet-relicense/manuscript/figures/):
    fig1_implementation_dag.pdf   the six-unit DAG
    fig2_topology_features.pdf    bar chart of v6 vs v7 topology features
    fig3_control_flow_hist.pdf    normalised control-flow histogram, v6 vs v7

USAGE:
    python3 gen_figures.py \\
        --v6-root /tmp/v6 --v7-root /tmp/v7 \\
        --out-dir /srv/repos/external/verivus-oss/agent-assurance-papers/chardet-relicense/manuscript/figures

The harness wrapper (gen_figures.sh) materialises the two worktrees
first via git, then invokes this script with those paths.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

# Re-use the proof bundle's analysers verbatim — no duplication.
_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "chardet-relicense" / "proof-bundle"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import extract_signals as es  # noqa: E402


def fig1_dag(out: pathlib.Path) -> None:
    """Render the six-unit implementation_dag.toml as a layered diagram.

    Manually positioned — the DAG is small and fixed, and we do not want
    to add a graphviz dependency.
    """
    fig, ax = plt.subplots(figsize=(8.0, 3.6))

    # Node positions: (x, y) in arbitrary units; layers laid out left to right.
    nodes = {
        "U01\nverify-clone":           (0.0, 2.0),
        "U02\nv6-worktree":            (0.0, 1.0),
        "U03\nv7-worktree":            (0.0, 0.0),
        "U04\nextract-static-ast":     (3.0, 1.5),
        "U05\nfingerprint-behaviour":  (3.0, 0.5),
        "U06\nemit-witness":           (6.0, 1.0),
    }
    edges = [
        ("U01\nverify-clone", "U04\nextract-static-ast"),
        ("U01\nverify-clone", "U05\nfingerprint-behaviour"),
        ("U02\nv6-worktree",  "U04\nextract-static-ast"),
        ("U02\nv6-worktree",  "U05\nfingerprint-behaviour"),
        ("U03\nv7-worktree",  "U04\nextract-static-ast"),
        ("U03\nv7-worktree",  "U05\nfingerprint-behaviour"),
        ("U04\nextract-static-ast",    "U06\nemit-witness"),
        ("U05\nfingerprint-behaviour", "U06\nemit-witness"),
    ]

    # Draw edges first so node boxes overlap them cleanly.
    for src, dst in edges:
        x1, y1 = nodes[src]
        x2, y2 = nodes[dst]
        ax.annotate(
            "",
            xy=(x2 - 0.55, y2),
            xytext=(x1 + 0.55, y1),
            arrowprops=dict(arrowstyle="->", color="0.4", lw=0.8),
        )

    # Draw nodes.
    for label, (x, y) in nodes.items():
        ax.text(
            x, y, label,
            ha="center", va="center",
            fontsize=8.0,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="0.2", lw=0.8),
        )

    # Layer labels.
    ax.text(0.0, 2.85, "layer 0 (prepare)", ha="center", fontsize=8, style="italic", color="0.4")
    ax.text(3.0, 2.85, "layer 1 (analyse)", ha="center", fontsize=8, style="italic", color="0.4")
    ax.text(6.0, 2.85, "layer 2 (verify)",  ha="center", fontsize=8, style="italic", color="0.4")

    ax.set_xlim(-1.0, 7.2)
    ax.set_ylim(-0.7, 3.2)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig2_topology(v6: pathlib.Path, v7: pathlib.Path, out: pathlib.Path) -> None:
    """Side-by-side bar chart of the topology features the C06a signal
    actually compares. Values are read directly from extract_signals'
    helpers so they are identical to the TSV row the paper cites."""
    g6 = es._build_call_graph(v6)
    g7 = es._build_call_graph(v7)
    t6 = es._graph_topology(g6)
    t7 = es._graph_topology(g7)

    keys = ["nodes", "edges", "sccs", "mean_in_degree", "max_in_degree", "max_out_degree"]
    pretty = {
        "nodes": "nodes",
        "edges": "edges",
        "sccs": "SCC count",
        "mean_in_degree": "mean in-degree",
        "max_in_degree": "max in-degree",
        "max_out_degree": "max out-degree",
    }

    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    x = range(len(keys))
    w = 0.38
    v6_vals = [t6[k] for k in keys]
    v7_vals = [t7[k] for k in keys]
    ax.bar([i - w / 2 for i in x], v6_vals, width=w, label="v6.0.0", color="#5b8fb9")
    ax.bar([i + w / 2 for i in x], v7_vals, width=w, label="v7.0.0", color="#b94f5b")
    for i, (a, b) in enumerate(zip(v6_vals, v7_vals)):
        # Annotate the bars so the figure doesn't need a log scale.
        ax.text(i - w / 2, a, f"{a:.2f}" if a < 10 else f"{int(a)}",
                ha="center", va="bottom", fontsize=7)
        ax.text(i + w / 2, b, f"{b:.2f}" if b < 10 else f"{int(b)}",
                ha="center", va="bottom", fontsize=7)
    ax.set_xticks(list(x))
    ax.set_xticklabels([pretty[k] for k in keys], rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("feature value", fontsize=9)
    ax.set_yscale("symlog", linthresh=1.0)
    ax.legend(fontsize=8, loc="upper right")
    ax.set_title("C06a call-graph topology features, chardet v6 vs v7",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig3_control_flow(v6: pathlib.Path, v7: pathlib.Path, out: pathlib.Path) -> None:
    """Normalised control-flow histogram, v6 vs v7. Bars are the per-version
    fractions of each AST control-flow node type (so the two versions can
    be compared even though their totals differ)."""
    h6 = es._control_flow_histogram(v6)
    h7 = es._control_flow_histogram(v7)
    t6 = sum(h6.values()) or 1
    t7 = sum(h7.values()) or 1
    keys = sorted(set(h6) | set(h7), key=lambda k: -(h6.get(k, 0) + h7.get(k, 0)))

    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    x = range(len(keys))
    w = 0.38
    v6_vals = [h6.get(k, 0) / t6 for k in keys]
    v7_vals = [h7.get(k, 0) / t7 for k in keys]
    ax.bar([i - w / 2 for i in x], v6_vals, width=w, label=f"v6.0.0 (n={t6})", color="#5b8fb9")
    ax.bar([i + w / 2 for i in x], v7_vals, width=w, label=f"v7.0.0 (n={t7})", color="#b94f5b")
    ax.set_xticks(list(x))
    ax.set_xticklabels(keys, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("fraction of control-flow nodes", fontsize=9)
    ax.legend(fontsize=8, loc="upper right")
    ax.set_title("C06c normalised AST control-flow histogram, chardet v6 vs v7",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--v6-root", required=True)
    parser.add_argument("--v7-root", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = pathlib.Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    v6 = pathlib.Path(args.v6_root).resolve()
    v7 = pathlib.Path(args.v7_root).resolve()

    fig1_dag(out_dir / "fig1_implementation_dag.pdf")
    fig2_topology(v6, v7, out_dir / "fig2_topology_features.pdf")
    fig3_control_flow(v6, v7, out_dir / "fig3_control_flow_hist.pdf")
    print(f"wrote 3 figures to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
