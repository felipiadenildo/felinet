# =============================================================================
# Makefile do TCC — compilação isolada em build/
# =============================================================================
# Uso:
#   make            # compila build/main.pdf (pdflatex + bibtex + 2x pdflatex)
#   make view       # compila + abre o PDF
#   make clean      # remove build/ e .aux espalhados pelas subpastas
#   make rebuild    # clean + all
#   make todos      # regenera Apêndice F (lista de \todoex)
#   make validate   # roda validador Python
#
# Requer: TeXLive (pdflatex, bibtex), Python 3
# =============================================================================

MAIN      := main
BUILD_DIR := build

# Flags do pdflatex
PDFLATEX_FLAGS := -synctex=1 -interaction=nonstopmode -file-line-error \
                  -shell-escape -output-directory=$(BUILD_DIR)

# Subpastas com \include — precisam existir DENTRO de build/ para o pdflatex
# conseguir gravar os .aux de cada arquivo incluído.
INCLUDE_DIRS := \
	capitulos \
	capitulos/cap5_arquitetura \
	capitulos/cap6_pipeline \
	capitulos/cap7_validacao \
	pre-textuais \
	pos-textuais

BUILD_SUBDIRS := $(addprefix $(BUILD_DIR)/,$(INCLUDE_DIRS))

.PHONY: all view clean rebuild todos validate _build_dirs

# -----------------------------------------------------------------------------
# Compilação padrão (saída em build/main.pdf)
# Sequência: pdflatex → bibtex → pdflatex → pdflatex
# -----------------------------------------------------------------------------
all: _build_dirs
	pdflatex $(PDFLATEX_FLAGS) $(MAIN).tex
	cd $(BUILD_DIR) && bibtex $(MAIN)
	pdflatex $(PDFLATEX_FLAGS) $(MAIN).tex
	pdflatex $(PDFLATEX_FLAGS) $(MAIN).tex
	@echo ""
	@echo "==> PDF gerado: $(BUILD_DIR)/$(MAIN).pdf"

view: all
	@xdg-open $(BUILD_DIR)/$(MAIN).pdf >/dev/null 2>&1 &

# Cria a árvore de subpastas em build/
_build_dirs:
	@mkdir -p $(BUILD_SUBDIRS)

# -----------------------------------------------------------------------------
# Limpeza
# -----------------------------------------------------------------------------
# Remove:
#   - a pasta build/ inteira
#   - .aux/.log/etc. que ficaram na raiz de compilações antigas
#   - .aux que ficaram espalhados em capitulos/, pre-textuais/, pos-textuais/
#     (vestígios de quando se compilava sem -output-directory)
clean:
	rm -rf $(BUILD_DIR)
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).log $(MAIN).out \
	      $(MAIN).toc $(MAIN).lof $(MAIN).lot $(MAIN).loa $(MAIN).lol \
	      $(MAIN).synctex.gz $(MAIN).fls $(MAIN).fdb_latexmk $(MAIN).run.xml \
	      $(MAIN).pdf
	find capitulos pre-textuais pos-textuais -type f \
	     \( -name '*.aux' -o -name '*.log' -o -name '*.out' \) \
	     -delete 2>/dev/null || true
	@echo "Limpeza completa."

rebuild: clean all

# -----------------------------------------------------------------------------
# Utilitários do projeto
# -----------------------------------------------------------------------------
todos:
	@python3 ../03_codigo/scripts/extrair_todos.py

validate:
	@python3 ../03_codigo/scripts/validar_latex.py
