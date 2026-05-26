#!/usr/bin/env bash
# ============================================================
# reorganizar.sh
# ============================================================
# Reorganiza o repositorio tcc_gatos_campus2_v22 para a nova
# estrutura felinet, **preservando a historia git** via 'git mv'.
#
# USO:
#   cd ~/Desktop/tcc/tcc_gatos_campus2_v22
#   bash reorganizar.sh
#
# Apos rodar:
#   git status            # revisar
#   git commit -m "refactor: migra estrutura para src/ layout (felinet)"
#
# Este script NAO sobrescreve arquivos LaTeX -- o usuario controla
# os ajustes em .tex manualmente.
# ============================================================

set -euo pipefail

if [ ! -d ".git" ]; then
    echo "[!!] Execute este script da raiz do repositorio git." >&2
    exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "[!!] Working tree nao esta limpa. Commit ou stash antes." >&2
    git status --short
    exit 1
fi

echo "==> 1) Renomeando 03_codigo/ para src/felinet/ ..."
# As pastas internas mudam de nome (datasets/, pipeline/, persistencia/
# viram subpacotes de felinet/).
mkdir -p src
git mv 03_codigo src/_legado_03_codigo  # passo intermediario
mkdir -p src/felinet
git mv src/_legado_03_codigo/datasets       src/felinet/datasets
git mv src/_legado_03_codigo/pipeline       src/felinet/pipeline
git mv src/_legado_03_codigo/persistencia   src/felinet/persistencia
# Remove restos (configs antigas, scripts, notebooks)
git rm -rf src/_legado_03_codigo

echo "==> 2) Tests para a raiz ..."
# Se houver tests dentro de 03_codigo/ na arvore, ja foram removidos acima.
# Agora copiamos os ajustados (vindos do ZIP felinet) para o lugar correto.
# (Pressupoe que o usuario aplicou o ZIP por cima; veja _INSTRUCOES_MIGRACAO.md)

echo "==> 3) Renomeando 02_latex/ para tex/ ..."
git mv 02_latex tex || echo "(02_latex ja era tex/)"

echo "==> 4) Renomeando 04_dados/ para data/ ..."
if [ -d "04_dados" ]; then
    git mv 04_dados data
fi

echo "==> 5) Renomeando 05_figuras/ para artifacts/figuras/ ..."
mkdir -p artifacts
if [ -d "05_figuras" ]; then
    git mv 05_figuras artifacts/figuras
fi

echo "==> 6) Renomeando 08_modelos/ para modelos/ ..."
if [ -d "08_modelos" ]; then
    git mv 08_modelos modelos
fi

echo "==> 7) Migrando docs ..."
mkdir -p docs
[ -d "00_governanca" ] && git mv 00_governanca docs/governanca
[ -d "01_pesquisa" ]   && git mv 01_pesquisa   docs/pesquisa
[ -d "06_manuais" ]    && git mv 06_manuais    docs/manuais

echo "==> 8) Renomeando 07_anexos/ -> anexos/ ..."
[ -d "07_anexos" ] && git mv 07_anexos anexos

echo "==> 9) Renomeando 09_artefatos_entrega/ -> entrega/ ..."
[ -d "09_artefatos_entrega" ] && git mv 09_artefatos_entrega entrega

echo ""
echo "==> Migracao git mv concluida."
echo ""
echo "Proximos passos:"
echo "  1. Aplique os arquivos novos do ZIP felinet por cima (sobrescreve nada da estrutura git mv)."
echo "  2. git status   # revise"
echo "  3. uv pip install -e \".[dev]\""
echo "  4. pytest -q"
echo "  5. git add -A && git commit -m 'refactor: src/ layout (tcc_gatos -> felinet)'"
