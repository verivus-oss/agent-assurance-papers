#!/usr/bin/env bash
# reproduce.sh — the container entrypoint (DESIGN.md §10). Reproduces the whole
# Stateful I/O proof and compiles the paper inside the image. Pinning is partial:
# go/node/rust are sha256-pinned and the base is digest-pinned, but the
# zypper-provided tools (gcc, gawk, python3, java, TeX) are NOT — see the
# Containerfile header. Exits 0 only if every witness (the load-bearing contract,
# the graceful-vs-kill control, the AWK boundary, the differential-agreement
# channel, the C04 in-flight timing guard, and the re-pointed Java reproducer),
# every validator, and the PDF build succeed. main.pdf and this log are copied to
# /out (bind-mount it to collect them on the host).
set -u
REPO=/work/agent-assurance-papers
B="$REPO/non-trivial-proof/proof-bundle"
M="$REPO/non-trivial-proof/manuscript"
V=/work/agent-assurance/validators
OUT="${OUT_DIR:-/out}"
mkdir -p "$OUT" 2>/dev/null || true

echo "############ TOOLCHAINS ############"
echo "  (go/node/rust pinned by version+sha256; gcc/python/java/gawk/TeX are"
echo "   unpinned, from the digest-pinned base's LIVE zypper repos — versions"
echo "   below are a snapshot of this build, not a guarantee)"
go version
printf 'node %s\n' "$(node --version)"
python3 --version
cc --version | head -1
rustc --version
java -version 2>&1 | head -1
gawk --version | head -1

echo; echo "############ WITNESSES ############"
cd "$B" || exit 2
./run_service_contract.sh;    rc_contract=$?
echo; ./detect_graceful_shutdown.sh; rc_graceful=$?
echo; ./detect_awk_boundary.sh;      rc_awk=$?
echo; python3 differential_echo.py;  rc_diff=$?
echo; python3 detect_inflight_window.py; rc_inflight=$?
echo; ./detect_java_reuseaddr.sh;    rc_java=$?

echo; echo "############ VALIDATORS (--check-paths-exist --repo-root) ############"
cd "$REPO" || exit 2
vfail=0
run_v() { if python3 "$@" >/tmp/v.out 2>&1; then echo "  PASS  $2"; else echo "  FAIL  $2"; tail -4 /tmp/v.out | sed 's/^/        /'; vfail=1; fi; }
run_v "$V/validate_implementation_dag.py" non-trivial-proof/proof-bundle/implementation_dag.toml --repo-root . --check-paths-exist
run_v "$V/validate_traceability.py"       non-trivial-proof/proof-bundle/traceability.toml       --repo-root . --check-paths-exist
for f in contract_declaration review_readiness evidence_matrix; do
  run_v "$V/validate_review_readiness.py" "non-trivial-proof/proof-bundle/$f.toml" --repo-root . --check-paths-exist
done

echo; echo "############ PAPER (pdflatex -> bibtex -> pdflatex x2) ############"
cd "$M" || exit 2
rm -f main.aux main.bbl main.blg main.out main.log main.pdf
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/tmp/tex1.log 2>&1
bibtex main                                               >/tmp/bib.log  2>&1
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/tmp/tex2.log 2>&1
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/tmp/tex3.log 2>&1
pdfrc=1
if [ -f main.pdf ]; then
  pages=$(grep -oE 'Output written on main\.pdf \([0-9]+ page' /tmp/tex3.log | grep -oE '[0-9]+' | head -1)
  echo "  main.pdf built: $(wc -c < main.pdf) bytes, ${pages:-?} pages"
  cp main.pdf "$OUT/main.pdf" 2>/dev/null && echo "  copied to $OUT/main.pdf"
  pdfrc=0
else
  echo "  PDF BUILD FAILED — tail of last pass:"; tail -25 /tmp/tex3.log | sed 's/^/    /'
fi

echo; echo "############ SUMMARY ############"
echo "  witnesses : contract=$rc_contract graceful=$rc_graceful awk=$rc_awk diff=$rc_diff inflight=$rc_inflight java=$rc_java"
echo "  validators: $([ "$vfail" = 0 ] && echo 'all pass' || echo 'FAIL')"
echo "  paper     : $([ "$pdfrc" = 0 ] && echo 'main.pdf built' || echo 'FAIL')"
if [ "$rc_contract" = 0 ] && [ "$rc_graceful" = 0 ] && [ "$rc_awk" = 0 ] && \
   [ "$rc_diff" = 0 ] && [ "$rc_inflight" = 0 ] && [ "$rc_java" = 0 ] && [ "$vfail" = 0 ] && [ "$pdfrc" = 0 ]; then
  echo "  REPRODUCE: OK"; exit 0
else
  echo "  REPRODUCE: FAIL"; exit 1
fi
