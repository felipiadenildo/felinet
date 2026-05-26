# ============================================================
# Makefile -- felinet
# ============================================================
# Wrapper fino do CLI 'felinet'. Cada alvo eh equivalente a um
# comando do typer; o Makefile existe apenas para atalhos comuns
# (CI, demonstracao, geracao de artefatos da monografia).
# ============================================================

.PHONY: help instalar qualidade testes testes-smoke pipeline-dev \
        cascata-dev figuras tabelas reid-todos limpar-dev validar

help:
	@echo "felinet -- alvos do Makefile:"
	@echo "  instalar       Instala o pacote em modo editavel (uv pip install -e '.[dev]')"
	@echo "  qualidade      Roda ruff + pytest"
	@echo "  testes         Apenas pytest (sem smoke/GPU)"
	@echo "  testes-smoke   Inclui testes que requerem GPU/modelos pesados"
	@echo "  validar        Sanity check do ambiente (felinet dev validar-ambiente)"
	@echo "  pipeline-dev   Cascata operacional sobre as 5 imagens de 01_brutas/"
	@echo "  cascata-dev    Alias de pipeline-dev"
	@echo "  figuras        Regera figuras da Fase IV (artifacts/figuras/)"
	@echo "  tabelas        Regera tabelas da Fase IV (artifacts/tabelas/)"
	@echo "  reid-todos     Roda avaliacao Re-ID closed+open para N=50,200,500"
	@echo "  limpar-dev     Apaga artefatos da cascata dev (preserva 01_brutas/)"

instalar:
	uv pip install -e ".[dev]"

qualidade:
	ruff check src/ tests/
	pytest -q

testes:
	pytest -q

testes-smoke:
	pytest -q -m "smoke or not smoke"

validar:
	felinet dev validar-ambiente

pipeline-dev cascata-dev:
	felinet pipeline executar --perfil dev

figuras:
	felinet figuras reid-cmc --perfil prod --n 200
	felinet figuras reid-cmc --perfil prod --n 500
	felinet figuras matriz-similaridade --perfil prod --n 50

tabelas:
	felinet tabelas reid-resumo --perfil prod
	felinet tabelas openset-resumo --perfil prod
	felinet tabelas datasets-avaliados

reid-todos:
	for n in 50 200 500; do \
	  felinet reid extrair-embeddings --perfil prod --n $$n ; \
	  felinet reid avaliar-closed     --perfil prod --n $$n ; \
	  felinet reid avaliar-openset    --perfil prod --n $$n ; \
	done

limpar-dev:
	felinet dev limpar-saidas-dev --confirmar
