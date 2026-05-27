bash pro    #!/usr/bin/env bash
# promover_para_main.sh -- promove refactor/v23-release-candidate para main
# no novo remote (felinet).
#
# Rodar a partir da raiz do repo (~/Desktop/tcc/tcc_gatos_campus2_v22):
#   bash promover_para_main.sh
#
# O que faz:
#   1. Confirma branch atual e ultimo commit
#   2. Atualiza remote origin para https://github.com/felipiadenildo/felinet.git
#   3. Faz git fetch do novo remote
#   4. Cria/atualiza main local
#   5. Merge --no-ff da refactor na main (preserva historico bifurcado)
#   6. Push da main para o novo remote
#   7. Push da refactor (preserva a branch como historico)
#   8. Sugere proximos passos
#
# Pre-requisitos:
#   - Repo 'felinet' ja existe no GitHub (vazio ou nao)
#   - checkpoint_v23.sh ja rodou (commit feito na refactor)
#   - working tree limpa

set -u

BRANCH_FEATURE="refactor/v23-release-candidate"
REMOTE_URL_NOVO="https://github.com/felipiadenildo/felinet.git"
BRANCH_ALVO="main"

ROOT="$(pwd)"
BRANCH_ATUAL="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"

echo "=========================================="
echo "  PROMOCAO PARA MAIN -- novo remote felinet"
echo "  repo: ${ROOT}"
echo "  branch atual: ${BRANCH_ATUAL}"
echo "=========================================="
echo ""

# ---------------------------------------------------------------------------
# Sanity 1: working tree limpa
# ---------------------------------------------------------------------------
if [[ -n "$(git status --porcelain)" ]]; then
    echo "[erro] working tree NAO esta limpa:"
    git status -s
    echo ""
    echo "Rode o checkpoint_v23.sh ANTES de promover, ou faca commit manual."
    exit 1
fi
echo "[ok] working tree limpa"

# ---------------------------------------------------------------------------
# Sanity 2: estou na refactor com commits
# ---------------------------------------------------------------------------
if [[ "${BRANCH_ATUAL}" != "${BRANCH_FEATURE}" ]]; then
    echo "[aviso] voce nao esta em ${BRANCH_FEATURE}, esta em ${BRANCH_ATUAL}"
    read -r -p "Trocar para ${BRANCH_FEATURE} agora? [S/n] " RESP
    if [[ "${RESP,,}" != "n" ]]; then
        git checkout "${BRANCH_FEATURE}" || { echo "[erro] checkout falhou"; exit 1; }
    else
        echo "[cancelado]"
        exit 1
    fi
fi

echo ""
echo "[1/7] estado da refactor:"
git log --oneline -5
echo ""

# ---------------------------------------------------------------------------
# Migra remote
# ---------------------------------------------------------------------------
echo "[2/7] remotes atuais:"
git remote -v
echo ""
REMOTE_URL_ATUAL="$(git remote get-url origin 2>/dev/null || echo '')"
if [[ "${REMOTE_URL_ATUAL}" != "${REMOTE_URL_NOVO}" ]]; then
    echo "Mudando origin -> ${REMOTE_URL_NOVO}"
    read -r -p "Confirmar? [S/n] " CONF_REMOTE
    if [[ "${CONF_REMOTE,,}" != "n" ]]; then
        # Preserva o remote antigo como 'old' para nao perder referencia
        if [[ -n "${REMOTE_URL_ATUAL}" ]]; then
            git remote rename origin old 2>/dev/null || true
            echo "  [info] remote antigo preservado como 'old'"
        fi
        git remote add origin "${REMOTE_URL_NOVO}"
        echo "  [ok] origin -> ${REMOTE_URL_NOVO}"
    else
        echo "[cancelado: manter remote atual]"
    fi
else
    echo "  [ok] origin ja aponta para ${REMOTE_URL_NOVO}"
fi
echo ""

# ---------------------------------------------------------------------------
# Fetch do novo remote
# ---------------------------------------------------------------------------
echo "[3/7] git fetch origin"
git fetch origin 2>&1 | head -10 || {
    echo "[aviso] fetch falhou. Possivelmente o repo 'felinet' esta vazio no GitHub"
    echo "        (o que e' OK -- primeiro push criara as branches remotas)."
}
echo ""

# ---------------------------------------------------------------------------
# Cria/atualiza main local
# ---------------------------------------------------------------------------
echo "[4/7] preparando branch main local"
if git show-ref --verify --quiet refs/heads/main; then
    echo "  branch main ja existe localmente"
    git checkout main
    # Se ha origin/main, fast-forward; se nao, fica como esta
    if git show-ref --verify --quiet refs/remotes/origin/main; then
        echo "  fazendo fast-forward para origin/main..."
        git merge --ff-only origin/main 2>/dev/null || {
            echo "  [aviso] main local diverge de origin/main. Continuando assim."
        }
    fi
else
    if git show-ref --verify --quiet refs/remotes/origin/main; then
        echo "  criando main local rastreando origin/main"
        git checkout -b main origin/main
    else
        # Repo novo (felinet vazio): cria main a partir da refactor
        echo "  origin nao tem main ainda. Criando main local a partir de ${BRANCH_FEATURE}"
        git checkout -b main "${BRANCH_FEATURE}"
        # Como ja foi criada a partir de refactor, o merge a seguir sera no-op.
        # Pulamos para o push.
        echo ""
        echo "[5/7] (pulando merge -- main criada direto da refactor)"
        echo ""
        echo "[6/7] push main -> origin"
        git push -u origin main
        echo ""
        echo "[7/7] push da branch ${BRANCH_FEATURE} (preservar historico)"
        git push -u origin "${BRANCH_FEATURE}"
        echo ""
        echo "=========================================="
        echo "  PROMOCAO CONCLUIDA (repo novo)"
        echo "=========================================="
        git log --oneline -5
        exit 0
    fi
fi
echo ""

# ---------------------------------------------------------------------------
# Merge --no-ff da refactor na main
# ---------------------------------------------------------------------------
echo "[5/7] merge ${BRANCH_FEATURE} -> main (com --no-ff)"
echo ""

# Mostra o que sera mergeado
echo "Commits que serao incorporados na main:"
git log --oneline "main..${BRANCH_FEATURE}" | head -20
N_COMMITS=$(git log --oneline "main..${BRANCH_FEATURE}" | wc -l)
echo ""
echo "  total: ${N_COMMITS} commits"
echo ""

if [[ "${N_COMMITS}" -eq 0 ]]; then
    echo "[aviso] main ja esta atualizada (nada a mergear)."
    echo ""
else
    read -r -p "Confirmar merge --no-ff? [S/n] " CONF_MERGE
    if [[ "${CONF_MERGE,,}" == "n" ]]; then
        echo "[cancelado]"
        exit 0
    fi

    MSG_MERGE="merge ${BRANCH_FEATURE} into main

Inclui:
- v23 refactor/release-candidate completo
- Correcoes dos 3 bugs do smoke (latest_por_fase, RelatorioCascata aliases, preparar-petface-mini sintetico)
- Smoke test v5 com paths corretos
- Experimento definitivo concluido: pipeline N=300 (kaggle_cats+felidae), Re-ID N=50/100/200 em PetFace real
- 184/184 testes verdes"

    git merge --no-ff "${BRANCH_FEATURE}" -m "${MSG_MERGE}"
    if [[ $? -ne 0 ]]; then
        echo "[erro] merge falhou. Resolva conflitos manualmente e rode:"
        echo "  git merge --continue   (apos resolver)"
        echo "  git merge --abort      (para desistir)"
        exit 1
    fi
    echo ""
    echo "[ok] merge concluido"
fi
echo ""

# ---------------------------------------------------------------------------
# Push main + refactor para o novo remote
# ---------------------------------------------------------------------------
echo "[6/7] push main -> origin"
read -r -p "Confirmar push da main? [S/n] " CONF_PUSH_MAIN
if [[ "${CONF_PUSH_MAIN,,}" != "n" ]]; then
    git push -u origin main
else
    echo "[push da main pulado]"
fi
echo ""

echo "[7/7] push ${BRANCH_FEATURE} -> origin"
read -r -p "Manter a branch ${BRANCH_FEATURE} no remote? [S/n] " CONF_PUSH_REF
if [[ "${CONF_PUSH_REF,,}" != "n" ]]; then
    git push -u origin "${BRANCH_FEATURE}"
else
    echo "[push da refactor pulado]"
fi

# ---------------------------------------------------------------------------
# Resumo final
# ---------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "  PROMOCAO PARA MAIN CONCLUIDA"
echo "=========================================="
echo ""
echo "Estado final:"
echo "  branch ativa: $(git rev-parse --abbrev-ref HEAD)"
echo "  remote: $(git remote get-url origin)"
echo ""
echo "Ultimos commits da main:"
git log --oneline main -5 2>/dev/null
echo ""
echo "Branches locais:"
git branch -v
echo ""
echo "Sugestoes (opcional):"
echo "  - apos confirmar que main esta certa, deletar a refactor LOCAL:"
echo "      git branch -d ${BRANCH_FEATURE}"
echo "  - deletar a refactor REMOTA (apos verificar no GitHub):"
echo "      git push origin --delete ${BRANCH_FEATURE}"
echo "  - tag de release na main:"
echo "      git tag -a v0.3.0 -m 'release v23-experimento-definitivo' && git push origin v0.3.0"
