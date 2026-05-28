#!/usr/bin/env python3
"""gen_fig5_walker_arch.py — render the language-neutral AST-walker
architecture diagram (fig5_walker_architecture.pdf).

The figure visualises the seam introduced in v2 Phase 1b (R15 response):
the six structural-similarity signals (C06a, C06a', C06b, C06c, C06d,
C06f) now route every AST traversal through an `ASTWalker` Protocol.
The Python concrete instance `PythonASTWalker` is shown alongside two
hypothetical un-implemented siblings (`TreeSitterRustWalker`,
`GoASTWalker`) so a reader sees exactly what would need to be built to
add a new language. Each instance is annotated with the language-native
AST construct it would use to satisfy each protocol method.

Matplotlib-only; no LaTeX dependency.
"""

from __future__ import annotations

import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


HERE = pathlib.Path(__file__).resolve().parent
OUT_PDF = HERE.parent / "fig5_walker_architecture.pdf"


# ----- layout helpers ------------------------------------------------------


def _box(ax, x, y, w, h, *, fc, ec="black", lw=1.2, ls="-", alpha=1.0,
          zorder=2):
    rect = mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=lw, edgecolor=ec, facecolor=fc, linestyle=ls,
        alpha=alpha, zorder=zorder,
    )
    ax.add_patch(rect)


def _text(ax, x, y, s, *, fontsize=8.5, weight="normal", ha="center",
           va="center", color="black", zorder=3):
    ax.text(x, y, s, fontsize=fontsize, fontweight=weight, ha=ha, va=va,
            color=color, zorder=zorder)


def _arrow(ax, x0, y0, x1, y1, *, color="black", lw=0.9, style="-|>",
            ls="-"):
    ax.annotate(
        "", xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                        linestyle=ls, mutation_scale=10),
        zorder=4,
    )


# ----- main draw -----------------------------------------------------------


def build_figure() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8.5, 9.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 11.5)
    ax.set_axis_off()

    # ---------- Top: ASTWalker Protocol ---------------------------------

    _box(ax, 1.5, 9.7, 7.0, 1.5,
          fc="#E8EAF6", ec="#3949AB", lw=1.6, zorder=2)
    _text(ax, 5.0, 11.0, "ASTWalker  (Protocol)", fontsize=11.5,
           weight="bold", color="#1A237E")
    _text(ax, 5.0, 10.55,
           "language-neutral seam: every signal traverses the AST only "
           "through these methods",
           fontsize=8.2, color="#283593")
    methods = [
        "iter_call_edges()", "iter_control_flow_nodes()",
        "iter_public_api()", "iter_imports()",
        "iter_class_methods()", "iter_function_signatures()",
    ]
    # Print in two rows of three
    for i, m in enumerate(methods):
        col = i % 3
        row = i // 3
        _text(ax, 2.5 + col * 2.5, 10.18 - row * 0.27, m,
               fontsize=7.6, color="#1A237E")

    # ---------- Three concrete-instance columns -------------------------

    cols = [
        # (x, y, w, h, fc, ec, title, status, notes)
        (0.3, 5.7, 3.0, 3.6, "#E8F5E9", "#2E7D32",
         "PythonASTWalker",
         "REFERENCE INSTANCE  (implemented, this paper)",
         [
            "iter_call_edges        ast.Call inside",
            "                        FunctionDef bodies",
            "iter_control_flow_nodes  ast.If / For / While /",
            "                        Try / With / Match",
            "iter_public_api        names in __all__,",
            "                        resolved via",
            "                        ImportFrom",
            "iter_imports           ast.Import +",
            "                        ImportFrom",
            "iter_class_methods     ast.FunctionDef in",
            "                        ast.ClassDef body",
            "iter_function_sigs     ast.arguments tuple",
         ]),
        (3.5, 5.7, 3.0, 3.6, "#FFF8E1", "#F9A825",
         "TreeSitterRustWalker",
         "HYPOTHETICAL  (not implemented)",
         [
            "iter_call_edges        syn::ExprCall under",
            "                        syn::ItemFn",
            "iter_control_flow_nodes  syn::ExprIf /",
            "                        ExprWhile / ForLoop",
            "                        / ExprMatch / ExprTry",
            "iter_public_api        pub fn / pub struct",
            "                        in lib.rs, +",
            "                        pub use re-exports",
            "iter_imports           use items + extern",
            "                        crate decls",
            "iter_class_methods     methods inside impl",
            "                        blocks (self recvr)",
            "iter_function_sigs     syn::Signature",
         ]),
        (6.7, 5.7, 3.0, 3.6, "#FFEBEE", "#C62828",
         "GoASTWalker",
         "HYPOTHETICAL  (not implemented)",
         [
            "iter_call_edges        ast.CallExpr inside",
            "                        ast.FuncDecl",
            "iter_control_flow_nodes  IfStmt / ForStmt /",
            "                        SwitchStmt /",
            "                        TypeSwitchStmt /",
            "                        ReturnStmt /",
            "                        RangeStmt",
            "iter_public_api        capitalised idents",
            "                        in pkg .go files",
            "iter_imports           import declarations",
            "iter_class_methods     methods with named",
            "                        receivers (no class)",
            "iter_function_sigs     ast.FuncType",
         ]),
    ]
    for x, y, w, h, fc, ec, title, status, notes in cols:
        _box(ax, x, y, w, h, fc=fc, ec=ec, lw=1.4, zorder=2)
        _text(ax, x + w / 2, y + h - 0.22, title,
               fontsize=10, weight="bold", color=ec)
        _text(ax, x + w / 2, y + h - 0.45, status,
               fontsize=7.4, color=ec)
        for i, line in enumerate(notes):
            _text(ax, x + 0.1, y + h - 0.78 - i * 0.22, line,
                   fontsize=6.6, ha="left",
                   color="#212121", weight="normal")

    # Arrows: Protocol -> each walker
    for x, y, w, _h, _fc, ec, *_ in cols:
        _arrow(ax, x + w / 2, 9.7, x + w / 2, y + 3.55,
                color=ec, lw=1.2, ls="-")

    # ---------- Bottom: Signal Extractors -------------------------------

    _box(ax, 1.0, 1.3, 8.0, 3.6,
          fc="#F3E5F5", ec="#6A1B9A", lw=1.4, zorder=2)
    _text(ax, 5.0, 4.62, "Signal extractors  (extract_signals.py)",
           fontsize=11, weight="bold", color="#4A148C")
    _text(ax, 5.0, 4.32,
           "call walker.iter_*() only — no signal touches ast.* or any "
           "language-specific parser API",
           fontsize=8.0, color="#6A1B9A")

    signals = [
        ("C06a  call_graph_topology",
         "iter_call_edges -> build call graph -> 8-feature reldiff"),
        ("C06a' call_graph_wl_kernel",
         "iter_call_edges -> Weisfeiler-Lehman kernel (k=4)"),
        ("C06b  import_edge_set",
         "iter_imports / audit_imports -> R1-R5 -> Jaccard"),
        ("C06c  control_flow_histogram",
         "iter_control_flow_nodes -> sum, normalise, cosine"),
        ("C06d  public_api_signature_equivalence",
         "iter_public_api + iter_class_methods -> per-method verdict"),
        ("C06f  per_function_ast_shape",
         "iter_function_signatures + iter_call_edges -> match & dist"),
    ]
    for i, (nm, desc) in enumerate(signals):
        col = i % 2
        row = i // 2
        ox = 1.25 + col * 4.0
        oy = 4.0 - row * 0.65
        _text(ax, ox, oy, nm, fontsize=8.5, ha="left", weight="bold",
               color="#4A148C")
        _text(ax, ox + 0.07, oy - 0.27, desc, fontsize=7.4, ha="left",
               color="#311B92")

    # Arrows: each walker -> signal box
    for x, _y, w, _h, _fc, ec, *_ in cols:
        _arrow(ax, x + w / 2, 5.7, x + w / 2, 4.9,
                color=ec, lw=1.2, ls="-")

    # ---------- Caption -------------------------------------------------

    _text(ax, 5.0, 0.6,
           "Figure 5. The language-neutral AST-walker seam introduced "
           "in v2 Phase 1b.\n"
           "Python is the reference instance; Rust and Go instances are "
           "stubs documenting the equivalent constructs.",
           fontsize=8.6, color="#212121")

    plt.tight_layout()
    return fig


def main() -> None:
    fig = build_figure()
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, format="pdf", bbox_inches="tight")
    print(f"wrote: {OUT_PDF}")


if __name__ == "__main__":
    main()
