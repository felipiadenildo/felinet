# Makefile — TCC Gatos Campus 2 v22
#
# Alvos principais:
#   make help              Lista alvos disponiveis
#   make qualidade         Roda lint + testes
#   make amostras          Pipeline completo nas 3 imagens de amostras_dev/
#   make subset-dev        Pipeline completo no subset lila_bc_dev/
#   make limpar            Remove artefatos gerados (interim, figuras)
#
# Variaveis opcionais:
#   PY=python  -> interprete (use uv run python se preferir)

SHELL := /bin/bash
PY ?= python

DIR_CODIGO := 03_codigo
DIR_SCRIPTS := $(DIR_CODIGO)/scripts
DIR_INTERIM := 04_dados/interim
DIR_FIGURAS := 05_figuras

.PHONY: help qualidade amostras subset-dev preparar-subset detectar-subset visualizar-subset classificar-subset limpar

help:
	@echo "Alvos disponiveis:"
	@echo "  make qualidade         Lint (ruff) + testes (pytest)"
	@echo "  make amostras          Pipeline nas 3 imagens de amostras_dev/"
	@echo "  make subset-dev        Pipeline no subset lila_bc_dev/ (8 imagens)"
	@echo "  make preparar-subset   So valida o subset e gera manifesto"
	@echo "  make detectar-subset   So roda MDv6 sobre o subset"
	@echo "  make visualizar-subset So gera bboxes anotadas do subset"
	@echo "  make classificar-subset So roda SpeciesNet no subset"
	@echo "  make limpar            Remove artefatos gerados"

qualidade:
	ruff check $(DIR_CODIGO)/
	pytest -q

# ------------------------------------------------------------
# Amostras dev (3 imagens originais de gato — Etapa 4)
# ------------------------------------------------------------

amostras:
	$(PY) $(DIR_SCRIPTS)/baixar_amostras.py
	$(PY) $(DIR_SCRIPTS)/detectar_amostras.py
	$(PY) $(DIR_SCRIPTS)/visualizar_deteccoes.py

# ------------------------------------------------------------
# Subset dev (lila_bc_dev — Etapa 5)
# ------------------------------------------------------------

preparar-subset:
	$(PY) $(DIR_SCRIPTS)/preparar_subset_dev.py

detectar-subset: preparar-subset
	$(PY) $(DIR_SCRIPTS)/detectar_subset_dev.py

visualizar-subset: detectar-subset
	$(PY) $(DIR_SCRIPTS)/visualizar_deteccoes.py \
	    --entrada-json $(DIR_INTERIM)/deteccoes_subset_dev.json \
	    --saida $(DIR_FIGURAS)/subset_dev

classificar-subset: detectar-subset
	$(PY) $(DIR_SCRIPTS)/classificar_amostras.py

subset-dev: visualizar-subset classificar-subset
	@echo ""
	@echo "Pipeline completo concluido. Artefatos:"
	@echo "  - $(DIR_INTERIM)/deteccoes_subset_dev.json"
	@echo "  - $(DIR_INTERIM)/classificacoes_amostras.json"
	@echo "  - $(DIR_FIGURAS)/subset_dev/*.jpg"

# ------------------------------------------------------------
# Limpeza
# ------------------------------------------------------------

limpar:
	rm -f $(DIR_INTERIM)/deteccoes_*.json
	rm -f $(DIR_INTERIM)/classificacoes_*.json
	rm -rf $(DIR_FIGURAS)/deteccoes_dev
	rm -rf $(DIR_FIGURAS)/subset_dev
	@echo "Artefatos removidos."