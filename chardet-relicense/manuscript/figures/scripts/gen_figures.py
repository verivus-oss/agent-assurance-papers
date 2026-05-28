#!/usr/bin/env python3
"""gen_figures.py — produce the figures used in the chardet-relicense paper.

This script intentionally re-runs the same AST analysers the proof bundle
uses (extract_signals.py), so the figures' data is byte-for-byte the same
data the paper's tables cite. It is NOT a copy of those analysers: it
imports them.

Outputs (under chardet-relicense/manuscript/figures/):
    fig1_implementation_dag.pdf   the six-unit DAG
    fig2_topology_features.pdf    small-multiples panel: per-feature
                                  grouped bars across the three v2
                                  calibration pairs
    fig3_control_flow_hist.pdf    normalised control-flow histogram, v6 vs v7

USAGE:
    python3 gen_figures.py \\
        --v5-root /tmp/v5 --v6-root /tmp/v6 --v7-root /tmp/v7 \\
        --csn-root /tmp/csn \\
        --out-dir /srv/repos/external/verivus-oss/agent-assurance-papers/chardet-relicense/manuscript/figures

The harness wrapper (gen_figures.sh) materialises the four worktrees
first via git, then invokes this script with those paths.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

# Re-use the proof bundle's analysers verbatim — no duplication.
# Upward search for `chardet-relicense/proof-bundle` so the script is
# robust to being run from a worktree or via a symlink (the historical
# `parents[3] / "chardet-relicense" / "proof-bundle"` doubled the
# `chardet-relicense/` segment in worktrees — same fix as
# validate_numbers.py).
def _find_proof_dir(start: pathlib.Path) -> pathlib.Path:
    for ancestor in [start, *start.parents]:
        candidate = ancestor / "chardet-relicense" / "proof-bundle"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        f"could not locate chardet-relicense/proof-bundle above {start}")
sys.path.insert(0, str(_find_proof_dir(pathlib.Path(__file__).resolve())))

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


def fig2_topology(v5: pathlib.Path, v6: pathlib.Path, v7: pathlib.Path,
                  csn: pathlib.Path, out: pathlib.Path) -> None:
    """Small-multiples panel of the C06a call-graph topology features,
    rendered for all three v2 calibration pairs side by side.

    Path A (live extractor): we materialise four worktrees (chardet
    5.0.0 / 6.0.0 / 7.0.0 and charset_normalizer 3.4.7), call
    ``extract_signals._build_call_graph`` + ``_graph_topology`` on each,
    and plot the resulting feature dicts. All eight ``_graph_topology``
    features are available; we drop two as uninformative under this
    multi-pair view and document the drop in the caption file
    ``manuscript/v2-phase2-fig2-caption.md``:

      * ``sccs`` — equals ``nodes`` for all six graphs (every function
        is its own SCC in a call graph with no recursion cycles), so the
        panel would duplicate the ``nodes`` panel.
      * ``mean_out_degree`` — equals ``mean_in_degree`` by construction
        (sum of in-degrees = sum of out-degrees = |E|); we plot one
        ``mean degree`` panel and drop the other.

    That leaves six informative features. Each subplot has its own
    linear y-axis sized to the local range so the cross-pair pattern is
    visible without log compression.
    """
    pair_specs = [
        ("v6 vs v7",                 v6, v7,   "#5b8fb9", "#b94f5b"),
        ("v5 vs v6",                 v5, v6,   "#5b8fb9", "#b94f5b"),
        ("v6 vs charset_normalizer", v6, csn,  "#5b8fb9", "#b94f5b"),
    ]
    # Compute topology dicts once per distinct worktree (v6 appears in
    # all three pairs; recomputing it three times is wasteful but
    # harmless — we still cache to make the code obvious).
    topo_cache: dict[pathlib.Path, dict[str, float]] = {}

    def topo(path: pathlib.Path) -> dict[str, float]:
        if path not in topo_cache:
            topo_cache[path] = es._graph_topology(es._build_call_graph(path))
        return topo_cache[path]

    pair_topo = [
        (label, topo(a), topo(b), ca, cb)
        for (label, a, b, ca, cb) in pair_specs
    ]

    # Six informative features (see docstring for the two we drop).
    feat_keys = [
        "nodes", "edges", "density",
        "mean_in_degree", "max_in_degree", "max_out_degree",
    ]
    feat_pretty = {
        "nodes":          "nodes",
        "edges":          "edges",
        "density":        "density",
        "mean_in_degree": "mean degree",
        "max_in_degree":  "max in-degree",
        "max_out_degree": "max out-degree",
    }

    fig, axes = plt.subplots(2, 3, figsize=(9.5, 5.6))
    n_pairs = len(pair_topo)
    x = list(range(n_pairs))
    w = 0.36

    for ax, key in zip(axes.flat, feat_keys):
        a_vals = [pt[1][key] for pt in pair_topo]
        b_vals = [pt[2][key] for pt in pair_topo]

        # Two bars per pair (side A, side B), grouped by pair on the x-axis.
        a_color = pair_topo[0][3]
        b_color = pair_topo[0][4]
        ax.bar([i - w / 2 for i in x], a_vals, width=w,
               color=a_color, edgecolor="0.2", linewidth=0.4,
               label="side A")
        ax.bar([i + w / 2 for i in x], b_vals, width=w,
               color=b_color, edgecolor="0.2", linewidth=0.4,
               label="side B")

        # Value labels above each bar. Density uses 4 decimals so the
        # narrow band (0.0040–0.0052) stays legible; everything else
        # uses 2 decimals or integer.
        def fmt(v: float) -> str:
            if key == "density":
                return f"{v:.4f}"
            if v < 10:
                return f"{v:.2f}"
            return f"{int(v)}"

        # Set y-limit with headroom for value labels (15% of range).
        all_vals = a_vals + b_vals
        ymax = max(all_vals)
        ymin = 0.0
        ax.set_ylim(ymin, ymax * 1.18 if ymax > 0 else 1.0)

        for i, (a, b) in enumerate(zip(a_vals, b_vals)):
            ax.text(i - w / 2, a, fmt(a),
                    ha="center", va="bottom", fontsize=6.5)
            ax.text(i + w / 2, b, fmt(b),
                    ha="center", va="bottom", fontsize=6.5)

        ax.set_xticks(x)
        ax.set_xticklabels([pt[0] for pt in pair_topo],
                           rotation=15, ha="right", fontsize=7.5)
        ax.set_title(feat_pretty[key], fontsize=9)
        ax.tick_params(axis="y", labelsize=7)
        ax.grid(axis="y", linestyle=":", linewidth=0.4, color="0.7")
        ax.set_axisbelow(True)

    # Single legend at figure top — bar colour encodes side A / side B
    # per pair (the pair label on each x-tick disambiguates *which* A/B).
    handles = [
        plt.Rectangle((0, 0), 1, 1, fc=pair_topo[0][3], ec="0.2", lw=0.4),
        plt.Rectangle((0, 0), 1, 1, fc=pair_topo[0][4], ec="0.2", lw=0.4),
    ]
    fig.legend(handles, ["side A (left bar)", "side B (right bar)"],
               loc="upper center", ncol=2, fontsize=8,
               bbox_to_anchor=(0.5, 0.99), frameon=False)

    fig.suptitle("C06a call-graph topology features across v2 calibration pairs",
                 fontsize=10, y=0.94)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.91))
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
    parser.add_argument("--v5-root", required=True,
                        help="chardet 5.0.0 worktree (for fig2 v5/v6 pair)")
    parser.add_argument("--v6-root", required=True)
    parser.add_argument("--v7-root", required=True)
    parser.add_argument("--csn-root", required=True,
                        help="charset_normalizer 3.4.7 worktree (for fig2)")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = pathlib.Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    v5 = pathlib.Path(args.v5_root).resolve()
    v6 = pathlib.Path(args.v6_root).resolve()
    v7 = pathlib.Path(args.v7_root).resolve()
    csn = pathlib.Path(args.csn_root).resolve()

    fig1_dag(out_dir / "fig1_implementation_dag.pdf")
    fig2_topology(v5, v6, v7, csn, out_dir / "fig2_topology_features.pdf")
    fig3_control_flow(v6, v7, out_dir / "fig3_control_flow_hist.pdf")
    print(f"wrote 3 figures to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
