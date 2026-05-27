# Makefile -- builds the chardet-relicense paper PDF.
#
# Single manuscript: main.tex (Werner-voice canonical).
# (A separate default-scientific-voice variant lived at
# chardet-relicense/manuscript/main_werner.tex through 2026-05-25; it was deleted in
# consolidation with main.tex per author directive that only the
# Werner-voice version ships.)
#
# Requires: pdflatex, bibtex (any stock TeX Live install).
# Targets:
#   make           (== make all == make main.pdf)
#   make figures   -- regenerate figures from harness data
#   make validate  -- re-derive every numeric headline with scipy/numpy
#   make clean     -- remove LaTeX build artefacts
#   make distclean -- also remove the PDF and the figures

LATEX     = pdflatex
BIBTEX    = bibtex
LATEXOPTS = -interaction=nonstopmode -halt-on-error

PYTHON      = python3
FIGURES_DIR = figures
FIGURES = \
  $(FIGURES_DIR)/fig1_implementation_dag.pdf \
  $(FIGURES_DIR)/fig2_topology_features.pdf \
  $(FIGURES_DIR)/fig3_control_flow_hist.pdf

.PHONY: all figures validate clean distclean help

all: main.pdf

# Three pdflatex + bibtex passes is the standard ritual for resolving
# citations and cross-references.
main.pdf: main.tex references.bib $(FIGURES)
	$(LATEX) $(LATEXOPTS) main.tex
	$(BIBTEX) main
	$(LATEX) $(LATEXOPTS) main.tex
	$(LATEX) $(LATEXOPTS) main.tex

figures:
	bash $(FIGURES_DIR)/scripts/gen_figures.sh

# Independently re-derive every numeric headline using scipy + numpy +
# networkx primitives, and write chardet-relicense/manuscript/figures/scripts/validation_report.json.
validate:
	$(PYTHON) $(FIGURES_DIR)/scripts/validate_numbers.py

$(FIGURES_DIR)/fig1_implementation_dag.pdf \
$(FIGURES_DIR)/fig2_topology_features.pdf \
$(FIGURES_DIR)/fig3_control_flow_hist.pdf: $(FIGURES_DIR)/scripts/gen_figures.py
	bash $(FIGURES_DIR)/scripts/gen_figures.sh

clean:
	rm -f main.aux main.bbl main.blg main.log main.out \
	      main.toc main.fls main.fdb_latexmk main.synctex.gz

distclean: clean
	rm -f main.pdf $(FIGURES)

help:
	@echo "Targets:"
	@echo "  make           -- build main.pdf"
	@echo "  make figures   -- regenerate figures from harness data"
	@echo "  make validate  -- run validate_numbers.py and emit JSON report"
	@echo "  make clean     -- remove LaTeX build artefacts"
	@echo "  make distclean -- also remove the PDF and the figures"
