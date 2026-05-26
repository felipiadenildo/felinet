# =============================================================================
#  Makefile -- compilação modular do TCC v2 (abntex2)
#  Build em /build, mantendo a árvore de subdiretórios espelhada
# =============================================================================
MAIN      := main
BUILD_DIR := build
LATEX     := pdflatex
BIBTEX    := bibtex
LATEXOPTS := -interaction=nonstopmode -file-line-error -halt-on-error \
             -output-directory=$(BUILD_DIR)

# Subdiretórios criados em build/ para acompanhar \include{caminho/arquivo}
SUBDIRS := \
  $(BUILD_DIR)/pre-textuais \
  $(BUILD_DIR)/capitulos \
  $(BUILD_DIR)/capitulos/cap2_hardware \
  $(BUILD_DIR)/capitulos/cap3_pipeline \
  $(BUILD_DIR)/pos-textuais \
  $(BUILD_DIR)/pos-textuais/apendices \
  $(BUILD_DIR)/pos-textuais/anexos

.PHONY: all pdf clean distclean view

all: pdf

pdf: _build_dirs
	$(LATEX) $(LATEXOPTS) $(MAIN).tex
	cd $(BUILD_DIR) && BIBINPUTS=..:$$BIBINPUTS BSTINPUTS=..:$$BSTINPUTS $(BIBTEX) $(MAIN) || true
	$(LATEX) $(LATEXOPTS) $(MAIN).tex
	$(LATEX) $(LATEXOPTS) $(MAIN).tex
	@cp $(BUILD_DIR)/$(MAIN).pdf $(MAIN).pdf
	@echo ""
	@echo "==> PDF gerado: $(MAIN).pdf"

_build_dirs:
	@mkdir -p $(SUBDIRS)

clean:
	@rm -rf $(BUILD_DIR)

distclean: clean
	@rm -f $(MAIN).pdf

view: pdf
	@xdg-open $(MAIN).pdf >/dev/null 2>&1 || true
