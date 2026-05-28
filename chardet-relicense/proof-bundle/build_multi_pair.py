#!/usr/bin/env python3
"""build_multi_pair.py — assemble the multi-pair calibration table.

Reads `results/<pair>/witness.tsv` for each calibration pair (v6_v7,
v5_v6, v6_charset_norm) and emits:

  1. <figures/scripts>/multi_pair_comparison.tex  — LaTeX longtable source
  2. <figures/scripts>/validation_report.v2_patch.json — JSON patch under
     independent.calibration.pair.{pair}.{signal}.

Pure stdlib; no external deps beyond what the harness already requires.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent  # chardet-relicense/proof-bundle/.. -> repo root
PAIRS = ("v6_v7", "v5_v6", "v6_charset_norm")
PAIR_LABEL = {
    "v6_v7": "chardet 6 vs 7 (v1 headline)",
    "v5_v6": "chardet 5 vs 6 (calibration: same-project rewrite)",
    "v6_charset_norm": "chardet 6 vs charset-normalizer 3.4.7 (calibration: independent same-domain)",
}
PAIR_SHORT = {
    "v6_v7": "v6\\,vs\\,v7",
    "v5_v6": "v5\\,vs\\,v6",
    "v6_charset_norm": "v6\\,vs\\,c\\_n",
}

RESULTS_DIR = HERE / "results"
FIG_SCRIPTS = HERE.parent / "manuscript" / "figures" / "scripts"


def _parse_witness(pair: str) -> dict:
    """Return a dict keyed by contract code (AUX1, C06a, ...) with parsed fields."""
    tsv = RESULTS_DIR / pair / "witness.tsv"
    rows: dict[str, dict] = {}
    for line in tsv.read_text().splitlines():
        if not line or line.startswith("#") or line.startswith("signal\t"):
            continue
        fields = line.split("\t")
        if len(fields) < 6:
            continue
        signal, contract, expected, actual, verdict, evidence = fields[:6]
        rows[contract] = {
            "signal": signal,
            "expected": expected,
            "actual": actual,
            "verdict": verdict,
            "evidence": evidence,
        }
    return rows


def _extract_number(actual: str, key: str) -> float | None:
    m = re.search(rf"{re.escape(key)}=([0-9.eE+-]+)", actual)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _extract_int(actual: str, key: str) -> int | None:
    v = _extract_number(actual, key)
    return None if v is None else int(v)


def _summarise_pair(pair: str) -> dict:
    rows = _parse_witness(pair)
    aux1 = rows.get("AUX1", {})
    c06a = rows.get("C06a", {})
    c06b = rows.get("C06b", {})
    c06c = rows.get("C06c", {})
    c06d = rows.get("C06d", {})
    c06e = rows.get("C06e", {})

    aux1_matches = None
    m = re.search(r"(\d+) matches across", aux1.get("actual", ""))
    if m:
        aux1_matches = int(m.group(1))

    return {
        "aux1": {
            "matches": aux1_matches,
            "actual": aux1.get("actual"),
            "verdict": aux1.get("verdict"),
        },
        "c06a": {
            "similarity": _extract_number(c06a.get("actual", ""), "similarity"),
            "nodes_a": _extract_int(c06a.get("actual", ""), "v6_nodes"),
            "nodes_b": _extract_int(c06a.get("actual", ""), "v7_nodes"),
            "edges_a": _extract_int(c06a.get("actual", ""), "v6_edges"),
            "edges_b": _extract_int(c06a.get("actual", ""), "v7_edges"),
            "actual": c06a.get("actual"),
            "evidence": c06a.get("evidence"),
        },
        "c06b": {
            "jaccard": _extract_number(c06b.get("actual", ""), "jaccard"),
            "shared": _extract_int(c06b.get("actual", ""), "shared"),
            "a_only": _extract_int(c06b.get("actual", ""), "v6_only"),
            "b_only": _extract_int(c06b.get("actual", ""), "v7_only"),
            "evidence": c06b.get("evidence"),
        },
        "c06c": {
            "cosine": _extract_number(c06c.get("actual", ""), "cosine"),
            "total_a": _extract_int(c06c.get("actual", ""), "v6_total"),
            "total_b": _extract_int(c06c.get("actual", ""), "v7_total"),
            "evidence": c06c.get("evidence"),
        },
        "c06d": {
            "shared": _extract_int(c06d.get("actual", ""), "shared"),
            "strict": _extract_int(c06d.get("actual", ""), "strict"),
            "renamed_args": _extract_int(c06d.get("actual", ""), "renamed_args"),
            "diverged": _extract_int(c06d.get("actual", ""), "diverged"),
            "evidence": c06d.get("evidence"),
        },
        "c06e": {
            "exact_rate": _extract_number(c06e.get("actual", ""), "exact_match_rate"),
            "bucket_rate": _extract_number(c06e.get("actual", ""), "bucket_match_rate"),
            "n_inputs": _extract_int(c06e.get("actual", ""), "n_inputs"),
            "verdict": c06e.get("verdict"),
        },
    }


def _read_manifest(pair: str) -> dict:
    return json.loads((RESULTS_DIR / pair / "manifest.json").read_text())


def _emit_latex(summaries: dict[str, dict], manifests: dict[str, dict]) -> str:
    """Generate the longtable source for the multi-pair comparison."""
    # Render numbers with reasonable precision; '—' for missing.
    def fmt(v, digits=3):
        if v is None:
            return "---"
        if isinstance(v, float):
            return f"{v:.{digits}f}"
        return str(v)

    s = summaries
    lines = []
    lines.append("% Generated by chardet-relicense/proof-bundle/build_multi_pair.py")
    lines.append("% DO NOT EDIT BY HAND; re-run detect.sh per pair + this script.")
    lines.append("\\begin{table}[t]")
    lines.append("\\centering")
    lines.append("\\caption{Multi-pair calibration of the v1 chardet-relicensing harness. "
                 "Each column is the same six signals run against a different pair. "
                 "The v1 paper reported only the leftmost column; the other two columns "
                 "answer the reviewer's external-validity question (R17). "
                 "Resolved commit SHAs: chardet 5.0.0=21bc6be (tag object; peeled commit fbb2ec6 via 5.0.0\\^{}\\{\\}), "
                 "6.0.0=8a4636b, 7.0.0=4b89d62; charset-normalizer 3.4.7=0f07891.}")
    lines.append("\\label{tab:multi-pair-calibration}")
    lines.append("\\small")
    lines.append("\\begin{tabular}{lrrr}")
    lines.append("\\toprule")
    lines.append("Signal & " + " & ".join(PAIR_SHORT[p] for p in PAIRS) + " \\\\")
    lines.append("\\midrule")

    # AUX1 — literal carryover (matches count)
    lines.append("AUX1: literal whitespace-norm SHA-256 matches & "
                 + " & ".join(fmt(s[p]["aux1"]["matches"]) for p in PAIRS) + " \\\\")
    # C06a — call graph similarity
    lines.append("C06a: call-graph topology similarity (0--1) & "
                 + " & ".join(fmt(s[p]["c06a"]["similarity"]) for p in PAIRS) + " \\\\")
    # C06b — import edge Jaccard
    lines.append("C06b: 3rd-party import-edge Jaccard (0--1) & "
                 + " & ".join(fmt(s[p]["c06b"]["jaccard"]) for p in PAIRS) + " \\\\")
    # C06c — control flow cosine
    lines.append("C06c: control-flow histogram cosine (0--1) & "
                 + " & ".join(fmt(s[p]["c06c"]["cosine"]) for p in PAIRS) + " \\\\")
    # C06d — public-API shared
    lines.append("C06d: \\texttt{\\_\\_all\\_\\_} shared symbols & "
                 + " & ".join(fmt(s[p]["c06d"]["shared"]) for p in PAIRS) + " \\\\")
    lines.append("\\quad of which strict-signature equal & "
                 + " & ".join(fmt(s[p]["c06d"]["strict"]) for p in PAIRS) + " \\\\")
    lines.append("\\quad of which diverged & "
                 + " & ".join(fmt(s[p]["c06d"]["diverged"]) for p in PAIRS) + " \\\\")
    # C06e — behavioural fingerprint
    lines.append("C06e: behavioural exact-match rate over 1000 fuzz inputs & "
                 + " & ".join(fmt(s[p]["c06e"]["exact_rate"]) for p in PAIRS) + " \\\\")
    lines.append("C06e: behavioural bucket-match rate over 1000 fuzz inputs & "
                 + " & ".join(fmt(s[p]["c06e"]["bucket_rate"]) for p in PAIRS) + " \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")
    return "\n".join(lines) + "\n"


def _emit_json_patch(summaries: dict[str, dict], manifests: dict[str, dict]) -> dict:
    return {
        "independent": {
            "calibration": {
                "harness_invocation": "chardet-relicense/proof-bundle/detect.sh <pair_name>",
                "pairs_defined_in": "chardet-relicense/proof-bundle/detect.sh case statement",
                "pair": {
                    pair: {
                        "manifest": manifests[pair],
                        "signals": summaries[pair],
                    }
                    for pair in PAIRS
                },
                "interpretation_summary": (
                    "If v6/v7 (the v1 headline) shows similarity in line with or BELOW the "
                    "calibration pairs (v5/v6 conventional rewrite; v6/charset-normalizer "
                    "independent same-domain detector), then the v1 'notably high' framing "
                    "does not survive. See per-signal values: C06a is 0.881 for v6/v7, "
                    "0.930 for v5/v6, 0.922 for v6/charset-normalizer — v6/v7 is the LOWEST "
                    "of the three. C06c is 0.984/0.995/0.999 in the same order — again "
                    "v6/v7 is the lowest. C06e is the dramatic outlier in the OPPOSITE "
                    "direction: v5/v6 (a conventional release-to-release evolution) "
                    "preserves behaviour at 0.968 exact-match; v6/v7 (AI rewrite) collapses "
                    "to 0.000; v6/charset-normalizer (independent codebases) is also 0.000. "
                    "Net: the v1 paper's structural-similarity numbers are domain baselines, "
                    "not evidence of derivation. The signal that actually separates "
                    "'evolutionary rewrite' from 'replacement' is C06e, and it goes the "
                    "OPPOSITE way to the v1 narrative."
                ),
            }
        }
    }


def main() -> int:
    summaries = {p: _summarise_pair(p) for p in PAIRS}
    manifests = {p: _read_manifest(p) for p in PAIRS}

    FIG_SCRIPTS.mkdir(parents=True, exist_ok=True)
    tex_path = FIG_SCRIPTS / "multi_pair_comparison.tex"
    tex_path.write_text(_emit_latex(summaries, manifests))
    print(f"wrote {tex_path}")

    json_path = FIG_SCRIPTS / "validation_report.v2_patch.json"
    json_path.write_text(json.dumps(_emit_json_patch(summaries, manifests), indent=2) + "\n")
    print(f"wrote {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
