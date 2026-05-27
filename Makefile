# ============================================================
# Makefile -- felinet
# ============================================================
# Comando canonico para reproduzir a monografia inteira:
#
#     make monografia              # incremental (so o que falta)
#     make monografia FORCE=1      # forca regerar TUDO
#     make monografia VERBOSE=2    # log detalhado (DEBUG)
#
# Para tarefas pontuais, ver `make help`.
# ============================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

# --------- Variaveis configuraveis ------------------------------
PERFIL ?= prod
FONTE  ?= petface
N      ?= 50
NS     ?= 50,100,200
SEEDS  ?= 42,1337,2024

# Flags para `make monografia`:
#   FORCE=1         regenera tudo (ignora incremental)
#   DRY=1           so mostra o plano
#   REGENERAR=...   apaga artefatos de grupos (csv ou 'all')
#                    ex: REGENERAR=tabelas,figuras_globais
#   COM_SMOKE=1     roda smoke antes (default: NAO)
FORCE       ?=
DRY         ?=
REGENERAR   ?=
COM_SMOKE   ?=

PYTHON := python
ORQ    := scripts/orquestrar_monografia.py

# Cores
C_OK := \033[1;32m
C_WARN := \033[1;33m
C_ERR := \033[1;31m
C_INFO := \033[1;36m
C_RESET := \033[0m

.PHONY: help \
        instalar sync-deps pre-commit-install \
        qualidade lint lint-fix format format-check tipos testes testes-cov \
        doctor debug-runs debug-imports \
        pipeline reid-um reid-todos figuras tabelas \
        monografia monografia-tabelas monografia-figuras monografia-status \
        limpar limpar-tudo limpar-runs-sem-tag \
        smoke ambiente organizar \
        ci git-status

# ============================================================
# AJUDA
# ============================================================
help:
	@printf "$(C_INFO)felinet -- alvos principais$(C_RESET)\n\n"
	@printf "$(C_OK)>>> MONOGRAFIA (alvo canonico)$(C_RESET)\n"
	@printf "  make monografia                          # incremental (so o que falta)\n"
	@printf "  make monografia FORCE=1                  # regera TUDO\n"
	@printf "  make monografia REGENERAR=tabelas        # apaga e regera tabelas\n"
	@printf "  make monografia REGENERAR=all            # apaga e regera tudo dirigido por items\n"
	@printf "  make monografia DRY=1                    # mostra plano sem executar\n"
	@printf "  make monografia COM_SMOKE=1              # roda smoke antes (default: NAO)\n"
	@printf "  make monografia-tabelas           # so as tabelas\n"
	@printf "  make monografia-figuras           # so as figuras\n"
	@printf "  make monografia-status            # mostra o que esta pronto/falta\n\n"
	@printf "$(C_OK)Setup$(C_RESET)\n"
	@printf "  instalar              uv pip install -e '.[dev]'\n"
	@printf "  sync-deps             uv sync\n"
	@printf "  pre-commit-install    instala hooks de pre-commit\n\n"
	@printf "$(C_OK)Qualidade$(C_RESET)\n"
	@printf "  qualidade             lint + testes  (use antes de commit)\n"
	@printf "  lint / lint-fix       ruff check [--fix]\n"
	@printf "  format / format-check ruff format [--check]\n"
	@printf "  tipos                 mypy src/  (se instalado)\n"
	@printf "  testes / testes-cov   pytest [com coverage]\n\n"
	@printf "$(C_OK)Debug$(C_RESET)\n"
	@printf "  doctor                diagnostico completo (env, GPU, symlinks)\n"
	@printf "  debug-runs            lista runs/ existentes\n"
	@printf "  debug-imports         confere se todo o CLI carrega\n\n"
	@printf "$(C_OK)Tarefas pontuais (override: VAR=valor)$(C_RESET)\n"
	@printf "  pipeline              executa pipeline operacional em uma fonte\n"
	@printf "  reid-um               extrai + closed + openset em um N\n"
	@printf "  reid-todos            mesmo para NS=$(NS)\n"
	@printf "  figuras / tabelas     gera artefatos pontuais\n\n"
	@printf "$(C_OK)Manutencao$(C_RESET)\n"
	@printf "  limpar                caches e build artifacts\n"
	@printf "  limpar-runs-sem-tag   apaga runs operacionais SEM tag (preserva monografia_n300)\n"
	@printf "  limpar-tudo           limpar + runs + dados dev + artifacts (CUIDADO)\n"
	@printf "  smoke                 smoke test (cria runs com tag=smoke_n30)\n"
	@printf "  ambiente              registra especs (uma vez por dia)\n"
	@printf "  organizar             scripts/organizar_repo.py\n\n"
	@printf "$(C_OK)Variaveis (defaults atuais)$(C_RESET)\n"
	@printf "  PERFIL=$(PERFIL)  FONTE=$(FONTE)  N=$(N)  NS=$(NS)  SEEDS=$(SEEDS)\n"

# ============================================================
# MONOGRAFIA (alvo principal)
# ============================================================
# Constroi a flag-list para o orquestrador a partir das variaveis FORCE/VERBOSE/SKIP_SMOKE.
# Usa $(if ...) do GNU make para condicionais sem complicacao.
ORQ_FLAGS := \
  $(if $(filter 1,$(FORCE)),--force,) \
  $(if $(filter 1,$(COM_SMOKE)),--com-smoke,) \
  $(if $(filter 1,$(DRY)),--dry-run,) \
  $(if $(REGENERAR),--regenerar $(REGENERAR),)

monografia:
	@printf "$(C_INFO)══════════════════════════════════════════$(C_RESET)\n"
	@printf "$(C_INFO)  felinet monografia$(C_RESET)\n"
	@printf "$(C_INFO)══════════════════════════════════════════$(C_RESET)\n"
	@printf "  FORCE=$(FORCE)  DRY=$(DRY)  REGENERAR=$(REGENERAR)  COM_SMOKE=$(COM_SMOKE)\n"
	@printf "  flags: $(ORQ_FLAGS)\n\n"
	@mkdir -p logs/monografia
	@ts=$$(date +%Y%m%dT%H%M%S); log=logs/monografia/orq_$$ts.log; \
	  printf "  log -> $$log\n\n"; \
	  set -o pipefail; $(PYTHON) $(ORQ) $(ORQ_FLAGS) 2>&1 | tee $$log

monografia-tabelas:
	$(PYTHON) $(ORQ) --so-tabelas $(if $(filter 1,$(FORCE)),--force,)

monografia-figuras:
	$(PYTHON) $(ORQ) --so-figuras $(if $(filter 1,$(FORCE)),--force,)

monografia-status:
	@printf "$(C_INFO)Artefatos esperados:$(C_RESET)\n"
	@$(PYTHON) -c "import json; d=json.load(open('scripts/monografia.json')); \
	  faltam=[]; ok=[]; \
	  from pathlib import Path; \
	  alvos=[]; \
	  [alvos.extend(it.get('artefatos', [])) for grp in d['etapas'].values() if isinstance(grp, dict) and 'items' in grp for it in grp['items']]; \
	  [ok.append(a) if Path(a).exists() else faltam.append(a) for a in alvos]; \
	  print(f'  OK    : {len(ok)}'); print(f'  faltam: {len(faltam)}'); \
	  [print(f'    - {a}') for a in faltam[:10]]; \
	  print(f'    ... e mais {len(faltam)-10}') if len(faltam) > 10 else None"

# ============================================================
# SETUP / QUALIDADE / TESTES
# ============================================================
instalar:
	uv pip install -e ".[dev]"

sync-deps:
	uv sync

pre-commit-install:
	pre-commit install --hook-type pre-commit --hook-type pre-push

qualidade: lint testes
	@printf "$(C_OK)>>> qualidade OK$(C_RESET)\n"

lint:
	ruff check src/ tests/ scripts/

lint-fix:
	ruff check --fix src/ tests/ scripts/

format:
	ruff format src/ tests/ scripts/

format-check:
	ruff format --check src/ tests/ scripts/

tipos:
	@command -v mypy >/dev/null 2>&1 && mypy src/felinet/ || printf "$(C_WARN)mypy nao instalado$(C_RESET)\n"

testes:
	pytest -q

testes-cov:
	pytest --cov=felinet --cov-report=term-missing

ci: format-check lint testes
	@printf "$(C_OK)>>> CI passou$(C_RESET)\n"

pre-commit: lint-fix format testes
	@printf "$(C_OK)>>> pronto para commit$(C_RESET)\n"

# ============================================================
# DEBUG
# ============================================================
doctor:
	@printf "$(C_INFO)=== Python ===$(C_RESET)\n"
	@which $(PYTHON) && $(PYTHON) --version
	@printf "\n$(C_INFO)=== CUDA / GPU ===$(C_RESET)\n"
	@$(PYTHON) -c "import torch; print(f'torch={torch.__version__} cuda={torch.cuda.is_available()}')" 2>&1 || true
	@printf "\n$(C_INFO)=== CLI ===$(C_RESET)\n"
	@felinet --version 2>&1 || printf "$(C_ERR)CLI nao instalado$(C_RESET)\n"
	@printf "\n$(C_INFO)=== Symlinks ===$(C_RESET)\n"
	@for d in data/raw/reid/petface data/raw/camera_trap/kaggle_cats data/raw/camera_trap/felidae; do \
	  if [ -L "$$d" ] && [ -e "$$d" ]; then printf "  $(C_OK)OK$(C_RESET)     %s\n" "$$d"; \
	  elif [ -L "$$d" ]; then printf "  $(C_ERR)BROKEN$(C_RESET) %s\n" "$$d"; \
	  else printf "  $(C_WARN)--$(C_RESET)     %s (ausente)\n" "$$d"; fi; done
	@printf "\n$(C_INFO)=== validar-ambiente ===$(C_RESET)\n"
	@felinet dev validar-ambiente 2>&1 || true

debug-runs:
	@find runs -name manifest.json 2>/dev/null | head -20 | while read f; do \
	  tag=$$($(PYTHON) -c "import json; d=json.load(open('$$f')); print(d.get('tag') or '-')"); \
	  printf "  tag=%-20s %s\n" "$$tag" "$$(dirname $$f)"; done

debug-imports:
	@$(PYTHON) -c "from felinet.comandos import ingestao, deteccao, classificacao, reid, figuras, tabelas, pipeline, dev; print('OK')"

# ============================================================
# TAREFAS PONTUAIS
# ============================================================
pipeline:
	felinet pipeline executar --perfil $(PERFIL) --fonte $(FONTE)

reid-um:
	felinet reid extrair-embeddings --perfil $(PERFIL) --fonte $(FONTE) --n $(N)
	felinet reid avaliar-closed     --perfil $(PERFIL) --fonte $(FONTE) --n $(N)
	felinet reid avaliar-openset    --perfil $(PERFIL) --fonte $(FONTE) --n $(N) --seeds $(SEEDS)

reid-todos:
	@IFS=',' read -ra ARR <<< "$(NS)"; \
	for n in "$${ARR[@]}"; do \
	  $(MAKE) --no-print-directory reid-um N=$$n PERFIL=$(PERFIL) FONTE=$(FONTE) SEEDS=$(SEEDS) || exit 1; \
	done

figuras:
	felinet figuras reid-cmc            --perfil $(PERFIL) --fonte $(FONTE) --n $(N)
	felinet figuras matriz-similaridade --perfil $(PERFIL) --fonte $(FONTE) --n $(N)

tabelas:
	felinet tabelas reid-resumo    --perfil $(PERFIL) --fonte $(FONTE) --ns $(NS)
	felinet tabelas openset-resumo --perfil $(PERFIL) --fonte $(FONTE) --ns $(NS)

# ============================================================
# MANUTENCAO
# ============================================================
limpar:
	@find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".ruff_cache" -o -name ".mypy_cache" -o -name "*.egg-info" \) -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name ".coverage" \) -delete 2>/dev/null || true
	@rm -rf build/ dist/ htmlcov/ coverage.xml tex/build/
	@printf "$(C_OK)[limpar] caches removidos$(C_RESET)\n"

limpar-runs-sem-tag:
	@printf "$(C_INFO)Procurando runs operacionais SEM tag...$(C_RESET)\n"
	@total=0; while IFS= read -r m; do \
	  tag=$$($(PYTHON) -c "import json; d=json.load(open('$$m')); print(d.get('tag') or '')"); \
	  if [ -z "$$tag" ]; then \
	    d=$$(dirname "$$m"); printf "  - %s\n" "$$d"; rm -rf "$$d"; total=$$((total+1)); \
	  fi; \
	done < <(find runs/operacional -name manifest.json 2>/dev/null); \
	printf "$(C_OK)[limpar-runs-sem-tag] %d run(s) removidos$(C_RESET)\n" $$total

limpar-tudo: limpar
	@read -p "Apagar TUDO (runs/, artifacts/, data/dev/pipeline/)? [s/N] " ans; \
	if [ "$$ans" = "s" ]; then \
	  rm -rf runs/ artifacts/ data/dev/pipeline/02_manifesto/ data/dev/pipeline/03_deteccoes/ data/dev/pipeline/04_classificacoes/ data/dev/pipeline/05_crops_felis_catus/; \
	  find data -name "*_latest.json" -delete 2>/dev/null || true; \
	  printf "$(C_OK)[limpar-tudo] ok$(C_RESET)\n"; \
	fi

smoke: ambiente
	@$(PYTHON) scripts/smoke_test.py

ambiente:
	@$(PYTHON) scripts/registrar_ambiente.py

organizar:
	@$(PYTHON) scripts/organizar_repo.py

git-status:
	@printf "$(C_INFO)Branch:$(C_RESET) "; git rev-parse --abbrev-ref HEAD
	@printf "$(C_INFO)Ultimo commit:$(C_RESET) "; git log -1 --oneline
	@printf "$(C_INFO)Tag:$(C_RESET) "; git describe --tags --abbrev=0 2>/dev/null || echo "(nenhuma)"
	@git status --short
