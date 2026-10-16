# ============================================================
# Makefile -- felinet
# ============================================================
#   make monografia      gera as figuras e tabelas na monografia e confere (configs/monografia.yaml)
#   make execucao-final  refaz os runs da execução final (GPU; horas)
#   make qualidade       lint + testes
# ============================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

PERFIL ?= prod
FONTE  ?= petface
N      ?= 50
NS     ?= 50,100,200
SEEDS  ?= 42,7,123
PYTHON := python

C_OK := \033[1;32m
C_INFO := \033[1;36m
C_RESET := \033[0m

.PHONY: help instalar qualidade lint lint-fix format format-check testes testes-cov ci \
        doctor monografia monografia-listar execucao-final pipeline reid-um reid-todos \
        smoke ambiente limpar

help:
	@printf "$(C_INFO)felinet -- alvos$(C_RESET)\n\n"
	@printf "$(C_OK)Monografia$(C_RESET)\n"
	@printf "  monografia          felinet monografia gerar + verificar (caminhos em configs/monografia.yaml)\n"
	@printf "  monografia-listar   o que a monografia usa e o que falta nesta máquina\n"
	@printf "  execucao-final      refaz os runs da execução final (GPU)\n\n"
	@printf "$(C_OK)Desenvolvimento$(C_RESET)\n"
	@printf "  instalar            uv pip install -e '.[dev]'\n"
	@printf "  qualidade           lint + testes (antes de commit)\n"
	@printf "  lint / lint-fix / format / format-check / testes / testes-cov / ci\n"
	@printf "  doctor              diagnóstico (Python, GPU, symlinks dos datasets)\n"
	@printf "  smoke               smoke test ponta a ponta (cria runs com tag smoke_n30)\n\n"
	@printf "$(C_OK)Execuções pontuais$(C_RESET)  (PERFIL=$(PERFIL) FONTE=$(FONTE) N=$(N) NS=$(NS) SEEDS=$(SEEDS))\n"
	@printf "  pipeline / reid-um / reid-todos\n"

# ============================================================
# MONOGRAFIA
# ============================================================
monografia:
	felinet monografia gerar
	felinet monografia verificar

monografia-listar:
	felinet monografia listar

# Os comandos que produziram os runs usados na monografia (ver docs/REPRODUCAO_MONOGRAFIA.md).
execucao-final:
	felinet pipeline executar --perfil dev --fonte kaggle_cats --tag monografia_n300 --max-amostras 300 --seed-amostragem 42 --dev
	felinet pipeline executar --perfil dev --fonte felidae --tag monografia_n300 --max-amostras 300 --seed-amostragem 42 --dev
	$(MAKE) --no-print-directory reid-todos PERFIL=prod FONTE=petface NS=50,100,200 SEEDS=42,7,123

# ============================================================
# SETUP / QUALIDADE
# ============================================================
instalar:
	uv pip install -e ".[dev]"

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

testes:
	pytest -q

testes-cov:
	pytest --cov=felinet --cov-report=term-missing

ci: format-check lint testes
	@printf "$(C_OK)>>> CI passou$(C_RESET)\n"

doctor:
	@printf "$(C_INFO)=== Python ===$(C_RESET)\n"
	@which $(PYTHON) && $(PYTHON) --version
	@printf "\n$(C_INFO)=== CUDA / GPU ===$(C_RESET)\n"
	@$(PYTHON) -c "import torch; print(f'torch={torch.__version__} cuda={torch.cuda.is_available()}')" 2>&1 || true
	@printf "\n$(C_INFO)=== CLI ===$(C_RESET)\n"
	@felinet --version 2>&1 || printf "CLI nao instalado\n"
	@printf "\n$(C_INFO)=== Symlinks ===$(C_RESET)\n"
	@for d in data/raw/reid/petface data/raw/camera_trap/kaggle_cats data/raw/camera_trap/felidae; do \
	  if [ -L "$$d" ] && [ -e "$$d" ]; then printf "  OK     %s\n" "$$d"; \
	  elif [ -L "$$d" ]; then printf "  BROKEN %s\n" "$$d"; \
	  else printf "  --     %s (ausente)\n" "$$d"; fi; done
	@printf "\n$(C_INFO)=== validar-ambiente ===$(C_RESET)\n"
	@felinet dev validar-ambiente 2>&1 || true

# ============================================================
# EXECUÇÕES PONTUAIS
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

smoke: ambiente
	@$(PYTHON) scripts/smoke_test.py

ambiente:
	@$(PYTHON) scripts/registrar_ambiente.py

limpar:
	@find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".ruff_cache" -o -name ".mypy_cache" -o -name "*.egg-info" \) -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name ".coverage" \) -delete 2>/dev/null || true
	@rm -rf build/ dist/ htmlcov/ coverage.xml
	@printf "$(C_OK)[limpar] caches removidos$(C_RESET)\n"
