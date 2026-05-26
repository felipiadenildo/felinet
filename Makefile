# ============================================================
# Makefile -- felinet
# Wrapper do CLI 'felinet' com atalhos para CI, debug e
# geracao de artefatos da monografia. Use `make help`.
# ============================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

# --------- Variaveis configuraveis pela linha de comando ----
PERFIL    ?= prod
FONTE     ?= petface
N         ?= 50
NS        ?= 50,200,500
SEEDS     ?= 42,1337,2024
SUBSET    ?= 100

# Cores (para output legivel)
C_RESET := \033[0m
C_OK    := \033[1;32m
C_WARN  := \033[1;33m
C_ERR   := \033[1;31m
C_INFO  := \033[1;36m

.PHONY: help \
        instalar instalar-prod sync-deps \
        qualidade lint lint-fix format format-check tipos \
        testes testes-v testes-cov testes-smoke testes-falhas \
        validar doctor debug-config debug-runs debug-fontes debug-imports \
        organizar-layout \
        pipeline-dev pipeline cascata-dev \
        reid-extrair reid-closed reid-openset reid-todos reid-um \
        figuras figuras-todas tabelas tabelas-todas artefatos \
        listar-runs limpar-runs limpar-dev limpar-cache limpar-tudo \
        diff-paths git-status pre-commit \
        smoke smoke-petface smoke-fluxo \
        ci

# ============================================================
# AJUDA
# ============================================================
help:
	@printf "$(C_INFO)felinet -- alvos do Makefile$(C_RESET)\n\n"
	@printf "$(C_OK)Variaveis (override: make alvo VAR=valor)$(C_RESET)\n"
	@printf "  PERFIL=$(PERFIL)   FONTE=$(FONTE)   N=$(N)\n"
	@printf "  NS=$(NS)   SEEDS=$(SEEDS)   SUBSET=$(SUBSET)\n\n"
	@printf "$(C_OK)Setup$(C_RESET)\n"
	@printf "  instalar             uv pip install -e '.[dev]'\n"
	@printf "  instalar-prod        uv pip install -e .   (sem dev tools)\n"
	@printf "  sync-deps            uv sync\n"
	@printf "  organizar-layout     scripts/organizar_layout.py (idempotente)\n\n"
	@printf "$(C_OK)Qualidade$(C_RESET)\n"
	@printf "  qualidade            lint + tipos + testes\n"
	@printf "  lint                 ruff check src/ tests/ scripts/\n"
	@printf "  lint-fix             ruff check --fix (aplica auto-fixes)\n"
	@printf "  format               ruff format src/ tests/ scripts/\n"
	@printf "  format-check         ruff format --check  (CI)\n"
	@printf "  tipos                mypy src/ (se mypy estiver instalado)\n\n"
	@printf "$(C_OK)Testes$(C_RESET)\n"
	@printf "  testes               pytest -q\n"
	@printf "  testes-v             pytest -v\n"
	@printf "  testes-cov           pytest --cov=felinet --cov-report=term-missing\n"
	@printf "  testes-smoke         pytest com marker smoke\n"
	@printf "  testes-falhas        pytest --lf -v  (so re-roda os que falharam)\n\n"
	@printf "$(C_OK)Debug / Sanity$(C_RESET)\n"
	@printf "  validar              felinet dev validar-ambiente\n"
	@printf "  doctor               diagnostico completo (env+dados+CUDA+symlinks)\n"
	@printf "  debug-config         imprime perfis carregados e fontes ativas\n"
	@printf "  debug-runs           lista todos os runs/metadados existentes\n"
	@printf "  debug-fontes         confere existencia/conteudo dos symlinks\n"
	@printf "  debug-imports        verifica se todos comandos do CLI carregam\n\n"
	@printf "$(C_OK)Pipeline operacional$(C_RESET)\n"
	@printf "  pipeline-dev         cascata dev (subset, sem GPU)\n"
	@printf "  pipeline             cascata em FONTE=... (PERFIL=prod default)\n\n"
	@printf "$(C_OK)Pipeline metodologico (Re-ID)$(C_RESET)\n"
	@printf "  reid-um              roda closed + open para um N (use N=50)\n"
	@printf "  reid-todos           closed+open para N=$(NS) em FONTE=$(FONTE)\n"
	@printf "  reid-extrair         so extrair-embeddings\n"
	@printf "  reid-closed          so avaliar-closed\n"
	@printf "  reid-openset         so avaliar-openset\n\n"
	@printf "$(C_OK)Artefatos da monografia$(C_RESET)\n"
	@printf "  tabelas              tabelas reid-resumo + openset-resumo (FONTE atual)\n"
	@printf "  tabelas-todas        regera todas as tabelas (incl. datasets-avaliados)\n"
	@printf "  figuras              CMC + matriz para N=$(N)\n"
	@printf "  figuras-todas        figuras para todos os Ns ($(NS))\n"
	@printf "  artefatos            tabelas + figuras (faz tudo)\n\n"
	@printf "$(C_OK)Manutencao$(C_RESET)\n"
	@printf "  listar-runs          lista runs existentes\n"
	@printf "  limpar-runs          apaga runs/ (preserva manifests)\n"
	@printf "  limpar-dev           limpa saidas da cascata dev\n"
	@printf "  limpar-cache         remove __pycache__/ .ruff_cache/ etc.\n"
	@printf "  limpar-tudo          limpar-runs + limpar-dev + limpar-cache\n\n"
	@printf "$(C_OK)Git / Workflow$(C_RESET)\n"
	@printf "  diff-paths           git diff configs/paths.yaml\n"
	@printf "  git-status           status + branch + tag mais recente\n"
	@printf "  pre-commit           lint-fix + format + testes  (rodar antes de commit)\n\n"
	@printf "$(C_OK)Smoke tests end-to-end$(C_RESET)\n"
	@printf "  smoke-petface        fluxo completo Re-ID em PetFace com N=$(N)\n"
	@printf "  smoke-fluxo          extrair -> closed -> open -> tabelas -> figuras\n\n"
	@printf "$(C_OK)CI$(C_RESET)\n"
	@printf "  ci                   pipeline completo de CI (format-check + lint + testes)\n"

# ============================================================
# SETUP
# ============================================================
instalar:
	uv pip install -e ".[dev]"

instalar-prod:
	uv pip install -e .

sync-deps:
	uv sync

organizar-layout:
	python scripts/organizar_layout.py

# ============================================================
# QUALIDADE
# ============================================================
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
	@if command -v mypy >/dev/null 2>&1; then \
	  mypy src/felinet/ || true; \
	else \
	  printf "$(C_WARN)mypy nao instalado; instale com: uv pip install mypy$(C_RESET)\n"; \
	fi

# ============================================================
# TESTES
# ============================================================
testes:
	pytest -q

testes-v:
	pytest -v

testes-cov:
	pytest --cov=felinet --cov-report=term-missing

testes-smoke:
	pytest -q -m "smoke"

testes-falhas:
	pytest --lf -v

# ============================================================
# DEBUG / SANITY
# ============================================================
validar:
	felinet dev validar-ambiente

doctor:
	@printf "$(C_INFO)=== 1. Versao do Python e ambiente ===$(C_RESET)\n"
	@which python && python --version
	@printf "\n$(C_INFO)=== 2. CUDA / GPU ===$(C_RESET)\n"
	@python -c "import torch; print(f'torch={torch.__version__}'); print(f'cuda={torch.cuda.is_available()}'); print(f'device={torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"cpu\"}')" 2>&1 || true
	@printf "\n$(C_INFO)=== 3. CLI carrega? ===$(C_RESET)\n"
	@felinet --version 2>&1 || printf "$(C_ERR)CLI nao instalado$(C_RESET)\n"
	@printf "\n$(C_INFO)=== 4. Symlinks de fontes ===$(C_RESET)\n"
	@for d in data/raw/reid/petface data/raw/reid/petface_mini data/raw/camera_trap/kaggle_cats data/raw/camera_trap/lila_ena24 data/raw/camera_trap/campus2_2025; do \
	  if [ -L "$$d" ] && [ ! -e "$$d" ]; then \
	    printf "  $(C_ERR)BROKEN$(C_RESET) %-44s -> %s (alvo nao existe)\n" "$$d" "$$(readlink $$d)"; \
	  elif [ -e "$$d" ]; then \
	    printf "  $(C_OK)OK$(C_RESET)     %-44s -> %s\n" "$$d" "$$(readlink -f $$d 2>/dev/null || echo '(dir local)')"; \
	  else \
	    printf "  $(C_WARN)--$(C_RESET)     %-44s (ausente)\n" "$$d"; \
	  fi; \
	done
	@printf "\n$(C_INFO)=== 5. Layout runs/ ===$(C_RESET)\n"
	@ls -la runs/ 2>/dev/null | head -5 || printf "$(C_WARN)runs/ ausente -- rode: make organizar-layout$(C_RESET)\n"
	@printf "\n$(C_INFO)=== 6. Ambiente validado ===$(C_RESET)\n"
	@felinet dev validar-ambiente 2>&1 || true

debug-config:
	@printf "$(C_INFO)=== Perfis em configs/paths.yaml ===$(C_RESET)\n"
	@python -c "from felinet.config import carregar_perfil; \
	  cfg = carregar_perfil('prod'); \
	  print(f'perfil: {cfg.nome}'); \
	  print(f'extras (resumo):'); \
	  [print(f'  {k} = {v}') for k,v in cfg.extras.items() if not isinstance(v, dict)]; \
	  print(f'fontes:'); \
	  [print(f'  {k}: {v}') for k,v in (cfg.extras.get('fontes') or {}).items()]"

debug-runs:
	@if [ -d runs ]; then \
	  printf "$(C_INFO)=== runs/ existentes ===$(C_RESET)\n"; \
	  find runs -name manifest.json | head -30 | while read f; do \
	    printf "  $(C_OK)%s$(C_RESET)\n" "$$(dirname $$f)"; \
	  done; \
	  printf "\n$(C_INFO)=== Symlinks latest/ ===$(C_RESET)\n"; \
	  find runs/latest -maxdepth 4 -type l 2>/dev/null | head -20; \
	else \
	  printf "$(C_WARN)runs/ nao existe$(C_RESET)\n"; \
	fi

debug-fontes:
	@printf "$(C_INFO)=== Inspecionando fontes ===$(C_RESET)\n"
	@for d in data/raw/reid/petface data/raw/reid/petface_mini; do \
	  printf "\n$(C_OK)>>> %s$(C_RESET)\n" "$$d"; \
	  if [ -e "$$d" ]; then \
	    ls -la "$$d" 2>&1 | head -5; \
	    printf "  Procurando reidentification.csv...\n"; \
	    find -L "$$d" -name reidentification.csv 2>/dev/null | head -3; \
	    printf "  Estrutura ate 2 niveis:\n"; \
	    find -L "$$d" -maxdepth 2 -type d 2>/dev/null | head -8; \
	  else \
	    printf "  $(C_WARN)ausente$(C_RESET)\n"; \
	  fi; \
	done
	@for d in data/raw/camera_trap/kaggle_cats data/raw/camera_trap/lila_ena24 data/raw/camera_trap/campus2_2025; do \
	  printf "\n$(C_OK)>>> %s$(C_RESET)\n" "$$d"; \
	  if [ -e "$$d" ]; then \
	    ls -la "$$d" 2>&1 | head -3; \
	    printf "  Total de imagens (jpg/png): "; \
	    find -L "$$d" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) 2>/dev/null | wc -l; \
	  else \
	    printf "  $(C_WARN)ausente$(C_RESET)\n"; \
	  fi; \
	done

debug-imports:
	@printf "$(C_INFO)=== Importando todos os modulos CLI ===$(C_RESET)\n"
	@python -c "from felinet.comandos import ingestao, deteccao, classificacao, reid, figuras, tabelas, pipeline, dev; print('OK -- todos os comandos importam')"
	@python -c "from felinet.runs import criar_run, finalizar_run, resolver_latest; print('OK -- felinet.runs')"
	@python -c "from felinet.config import carregar_perfil, resolver_fonte, fonte_default; print('OK -- felinet.config')"

# ============================================================
# PIPELINE OPERACIONAL
# ============================================================
pipeline-dev cascata-dev:
	felinet pipeline executar --perfil dev

pipeline:
	felinet pipeline executar --perfil $(PERFIL) --fonte $(FONTE)

# ============================================================
# PIPELINE METODOLOGICO (Re-ID)
# ============================================================
reid-extrair:
	felinet reid extrair-embeddings --perfil $(PERFIL) --fonte $(FONTE) --n $(N)

reid-closed:
	felinet reid avaliar-closed --perfil $(PERFIL) --fonte $(FONTE) --n $(N)

reid-openset:
	felinet reid avaliar-openset --perfil $(PERFIL) --fonte $(FONTE) --n $(N) --seeds $(SEEDS)

reid-um: reid-extrair reid-closed reid-openset
	@printf "$(C_OK)>>> Re-ID concluido para N=$(N) sobre $(FONTE)$(C_RESET)\n"

reid-todos:
	@IFS=',' read -ra ARR <<< "$(NS)"; \
	for n in "$${ARR[@]}"; do \
	  printf "$(C_INFO)>>> N=$$n$(C_RESET)\n"; \
	  felinet reid extrair-embeddings --perfil $(PERFIL) --fonte $(FONTE) --n $$n || exit 1; \
	  felinet reid avaliar-closed     --perfil $(PERFIL) --fonte $(FONTE) --n $$n || exit 1; \
	  felinet reid avaliar-openset    --perfil $(PERFIL) --fonte $(FONTE) --n $$n --seeds $(SEEDS) || exit 1; \
	done
	@printf "$(C_OK)>>> Re-ID completo para Ns=$(NS) sobre $(FONTE)$(C_RESET)\n"

# ============================================================
# ARTEFATOS
# ============================================================
figuras:
	felinet figuras reid-cmc --perfil $(PERFIL) --fonte $(FONTE) --n $(N)
	felinet figuras matriz-similaridade --perfil $(PERFIL) --fonte $(FONTE) --n $(N)

figuras-todas:
	@IFS=',' read -ra ARR <<< "$(NS)"; \
	for n in "$${ARR[@]}"; do \
	  felinet figuras reid-cmc --perfil $(PERFIL) --fonte $(FONTE) --n $$n || true; \
	done
	felinet figuras matriz-similaridade --perfil $(PERFIL) --fonte $(FONTE) --n 50 || true

tabelas:
	felinet tabelas reid-resumo --perfil $(PERFIL) --fonte $(FONTE) --ns $(NS)
	felinet tabelas openset-resumo --perfil $(PERFIL) --fonte $(FONTE) --ns $(NS)

tabelas-todas: tabelas
	felinet tabelas datasets-avaliados --perfil $(PERFIL) || true

artefatos: tabelas figuras-todas
	@printf "$(C_OK)>>> Artefatos gerados em artifacts/$(C_RESET)\n"

# ============================================================
# MANUTENCAO
# ============================================================
listar-runs:
	felinet pipeline listar --perfil $(PERFIL) || true
	@printf "\n"
	felinet reid listar --perfil $(PERFIL) || true

limpar-runs:
	@read -p "Apagar TUDO em runs/? [s/N] " ans; \
	if [ "$$ans" = "s" ]; then rm -rf runs/operacional runs/metodologico runs/latest; mkdir -p runs; printf "$(C_OK)runs/ limpos$(C_RESET)\n"; fi

limpar-dev:
	felinet dev limpar-saidas-dev --confirmar 2>&1 || true

limpar-cache:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache .pytest_cache .mypy_cache htmlcov .coverage 2>/dev/null || true
	@printf "$(C_OK)caches removidos$(C_RESET)\n"

limpar-tudo: limpar-cache limpar-dev limpar-runs

# ============================================================
# GIT / WORKFLOW
# ============================================================
diff-paths:
	git diff configs/paths.yaml

git-status:
	@printf "$(C_INFO)Branch:$(C_RESET) "
	@git rev-parse --abbrev-ref HEAD
	@printf "$(C_INFO)Ultimo commit:$(C_RESET) "
	@git log -1 --oneline
	@printf "$(C_INFO)Tag mais recente:$(C_RESET) "
	@git describe --tags --abbrev=0 2>/dev/null || echo "(nenhuma)"
	@printf "\n"
	@git status --short

pre-commit: lint-fix format testes
	@printf "$(C_OK)>>> pronto para commit$(C_RESET)\n"

# ============================================================
# SMOKE TESTS
# ============================================================
smoke-petface:
	@printf "$(C_INFO)>>> Smoke PetFace N=$(N)$(C_RESET)\n"
	$(MAKE) reid-um FONTE=petface N=$(N) PERFIL=$(PERFIL)
	$(MAKE) tabelas FONTE=petface NS=$(N) PERFIL=$(PERFIL)
	$(MAKE) figuras FONTE=petface N=$(N) PERFIL=$(PERFIL)
	@printf "$(C_OK)>>> Smoke PetFace concluido$(C_RESET)\n"

smoke-fluxo: smoke-petface
	$(MAKE) listar-runs

smoke: doctor debug-imports testes
	@printf "$(C_OK)>>> Smoke ok$(C_RESET)\n"

# ============================================================
# CI
# ============================================================
ci: format-check lint testes
	@printf "$(C_OK)>>> CI passou$(C_RESET)\n"

# ============================================================
# Figuras avançadas Re-ID (Bloco 2)
# ============================================================

figura-cmc-comp:  ## CMC sobreposta para múltiplos N
	$(FELINET) figuras cmc-comparativo --perfil $(PERFIL) --fonte $(FONTE) --ns $(NS)

figura-dist:  ## Histograma intra vs inter para um N
	$(FELINET) figuras dist-intra-inter --perfil $(PERFIL) --fonte $(FONTE) --n $(N)

figura-roc:  ## ROC open-set com banda entre seeds
	$(FELINET) figuras roc-openset --perfil $(PERFIL) --fonte $(FONTE) --n $(N)

figuras-avancadas: figura-cmc-comp figura-dist figura-roc  ## Gera todas as figuras Bloco 2