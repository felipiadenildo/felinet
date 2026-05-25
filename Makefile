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
	@echo "  make extrair-embeddings So roda MegaDescriptor no subset"
		@echo "  validar-petface   - valida estrutura do PetFace"
	@echo "  avaliar-reid      - avalia Re-ID (use N=200, default N=50)"
	@echo "  figuras-reid      - gera CMC + heatmap da ultima rodada"
	@echo "  resumo-reid       - tabela comparativa de todas as rodadas"
	@echo "  reid-completo     - avaliar-reid + figuras-reid"
	@echo "  reid-suite        - roda N=50, 200, 500 + figuras + resumo"
	@echo "  limpar-reid       - limpa JSONs e figuras de Re-ID"
	@echo "  limpar-reid-tudo  - limpa tambem cache de embeddings"

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

extrair-embeddings: classificar-subset
	$(PY) $(DIR_SCRIPTS)/extrair_embeddings.py

subset-dev: visualizar-subset classificar-subset extrair-embeddings
	@echo ""
	@echo "Pipeline completo concluido. Artefatos:"
	@echo "  - $(DIR_INTERIM)/deteccoes_subset_dev.json"
	@echo "  - $(DIR_INTERIM)/classificacoes_amostras.json"
	@echo "  - $(DIR_FIGURAS)/subset_dev/*.jpg"

# ------------------------------------------------------------
# Avaliacao Re-ID em PetFace (Etapa 6)
# ------------------------------------------------------------

# N pode ser passado pela linha de comando: make avaliar-reid N=200
N ?= 50

validar-petface:
	uv run python 03_codigo/scripts/validar_petface.py

avaliar-reid:
	uv run python 03_codigo/scripts/avaliar_reid_petface.py --max-individuos $(N)

figuras-reid:
	uv run python 03_codigo/scripts/gerar_figuras_reid.py

resumo-reid:
	uv run python 03_codigo/scripts/resumir_reid.py

# Rodada unica: avalia com N especificado + figuras correspondentes
reid-completo: avaliar-reid figuras-reid

# Suite completa: 50, 200, 500 sequencialmente + figuras de cada + resumo
reid-suite:
	$(MAKE) avaliar-reid N=50
	$(MAKE) figuras-reid
	$(MAKE) avaliar-reid N=200
	$(MAKE) figuras-reid
	$(MAKE) avaliar-reid N=500
	$(MAKE) figuras-reid
	$(MAKE) resumo-reid

# Limpa apenas saidas de Re-ID (preserva cache de embeddings)
limpar-reid:
	rm -f 04_dados/processed/avaliacao_reid_petface_*.json
	rm -f 05_figuras/reid/cmc_curve_n*.png
	rm -f 05_figuras/reid/matriz_similaridade_n*.png

# Limpa tudo de Re-ID incluindo cache pesado de embeddings
limpar-reid-tudo: limpar-reid
	rm -f 04_dados/interim/embeddings_petface_n*.npz

# ------------------------------------------------------------
# Limpeza
# ------------------------------------------------------------

limpar:
	rm -f $(DIR_INTERIM)/deteccoes_*.json
	rm -f $(DIR_INTERIM)/classificacoes_*.json
	rm -rf $(DIR_FIGURAS)/deteccoes_dev
	rm -rf $(DIR_FIGURAS)/subset_dev
	rm -f $(DIR_INTERIM)/embeddings_*.json
	rm -f 04_dados/processed/avaliacao_reid_*.json
	rm -f 04_dados/interim/embeddings_petface.npz
	rm -rf 05_figuras/reid
	@echo "Artefatos removidos."