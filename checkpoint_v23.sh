#!/usr/bin/env bash
# checkpoint_v23.sh -- commit + push do estado pos-experimento definitivo.
#
# Roda da raiz do repo (~/Desktop/tcc/tcc_gatos_campus2_v22):
#   bash checkpoint_v23.sh
#
# O que faz:
#   1. Mostra git status para voce ver o que sera commitado
#   2. Pergunta confirmacao antes de adicionar
#   3. Faz git add do que NAO esta no .gitignore (codigo, scripts, docs, configs)
#   4. Mostra git diff --cached resumido
#   5. Pergunta confirmacao para commit
#   6. Commita com mensagem padrao + estatisticas
#   7. Pergunta se quer fazer push (e para qual remote)
#
# NAO commita: artifacts/, runs/, data/, *.zip, RELATORIO_SMOKE.md (saida do smoke),
# LOG_experimento.txt, BACKUP_v23_smoke_fix_*/ -- esses devem ficar no .gitignore.

set -u

ROOT="$(pwd)"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'desconhecida')"

echo "=========================================="
echo "  CHECKPOINT v23 -- pos experimento definitivo"
echo "  repo: ${ROOT}"
echo "  branch atual: ${BRANCH}"
echo "=========================================="
echo ""

# ---------------------------------------------------------------------------
# 1. Estado atual
# ---------------------------------------------------------------------------
echo "[1/6] git status"
echo ""
git status -s | head -60
TOTAL_ALTERADOS=$(git status -s | wc -l)
echo ""
echo "  total de arquivos alterados/novos: ${TOTAL_ALTERADOS}"
echo ""

if [[ "${TOTAL_ALTERADOS}" -eq 0 ]]; then
    echo "[ok] working tree limpa. Nada para commitar."
    echo ""
    echo "Ultimo commit:"
    git log -1 --format='  %h %s (%cr)'
    exit 0
fi

# ---------------------------------------------------------------------------
# 2. Sanidade: verificar que NADA do .gitignore foi forcado
# ---------------------------------------------------------------------------
echo "[2/6] checando se artifacts/, runs/, data/ estao ignorados..."
PRESENTE_QUE_NAO_DEVIA=""
for dir in artifacts runs data BACKUP_v23_smoke_fix; do
    if git status -s | grep -qE "^\?\? ${dir}/|^A. ${dir}/|^M. ${dir}/"; then
        PRESENTE_QUE_NAO_DEVIA="${PRESENTE_QUE_NAO_DEVIA} ${dir}/"
    fi
done
if [[ -n "${PRESENTE_QUE_NAO_DEVIA}" ]]; then
    echo "  [AVISO] estes paths apareceram no status:${PRESENTE_QUE_NAO_DEVIA}"
    echo "  eles deveriam estar no .gitignore. Verifique antes de continuar."
    echo "  (se for proposital, pode seguir; vou ignorar via :^pathspec abaixo)"
    echo ""
fi

read -r -p "Prosseguir para git add? [s/N] " RESPOSTA
if [[ "${RESPOSTA,,}" != "s" && "${RESPOSTA,,}" != "sim" ]]; then
    echo "[cancelado]"
    exit 0
fi

# ---------------------------------------------------------------------------
# 3. git add seletivo (codigo, scripts, docs, configs; NAO artifacts/runs/data)
# ---------------------------------------------------------------------------
echo ""
echo "[3/6] git add (excluindo artifacts/, runs/, data/, BACKUP_*, *.zip, RELATORIO_SMOKE.md, LOG_experimento.txt)"

# Pathspecs negativos protegem mesmo se .gitignore nao cobrir
git add . \
    ':!artifacts/' \
    ':!runs/' \
    ':!data/' \
    ':!BACKUP_v23_smoke_fix_*' \
    ':!*.zip' \
    ':!RELATORIO_SMOKE.md' \
    ':!LOG_experimento.txt' \
    ':!dados_monografia.zip'

# ---------------------------------------------------------------------------
# 4. Mostrar o que vai no commit
# ---------------------------------------------------------------------------
echo ""
echo "[4/6] arquivos staged para commit:"
git diff --cached --stat | tail -40

# ---------------------------------------------------------------------------
# 5. Confirmar e commitar
# ---------------------------------------------------------------------------
echo ""
MSG_PADRAO="checkpoint v23: experimento definitivo concluido (smoke 25/25 OK)

- 3 bugs do v23-smoke corrigidos (latest_por_fase, RelatorioCascata aliases, preparar-petface-mini sintetico)
- dev gerar-resumo-html usando resolver_latest
- smoke_test v5 com globs corretos das figuras Re-ID (prefixo reid_, 3 subpastas)
- experimento_definitivo.sh: pipeline N=300 (kaggle_cats+felidae) + Re-ID N=50,100,200 em PetFace real
- 5 testes novos em test_smoke_patches.py (179 -> 184 verde)
- compat: runs antigos com comandos individuais por fase continuam validos"

echo "[5/6] mensagem de commit padrao:"
echo "----"
echo "${MSG_PADRAO}"
echo "----"
echo ""
read -r -p "Usar essa mensagem? [S/n/editar] " RESP_MSG
case "${RESP_MSG,,}" in
    n|nao)
        echo "[cancelado] use 'git commit' manualmente."
        exit 0
        ;;
    e|editar|edit)
        TMPFILE="$(mktemp /tmp/commit_msg_XXXXXX.txt)"
        echo "${MSG_PADRAO}" > "${TMPFILE}"
        ${EDITOR:-nano} "${TMPFILE}"
        git commit -F "${TMPFILE}"
        rm -f "${TMPFILE}"
        ;;
    *)
        git commit -m "${MSG_PADRAO}"
        ;;
esac

if [[ $? -ne 0 ]]; then
    echo "[erro] git commit falhou."
    exit 1
fi

echo ""
git log -1 --format='[ok] commit criado: %h %s'

# ---------------------------------------------------------------------------
# 6. Push opcional
# ---------------------------------------------------------------------------
echo ""
echo "[6/6] push para origin?"
REMOTES=$(git remote -v 2>/dev/null | grep '(push)' | awk '{print $1}' | sort -u)
echo "  remotes disponiveis:"
git remote -v | sed 's/^/    /'
echo ""
read -r -p "Fazer push? [s/N] " PUSH_RESP
if [[ "${PUSH_RESP,,}" == "s" || "${PUSH_RESP,,}" == "sim" ]]; then
    REMOTE_DEFAULT=$(echo "${REMOTES}" | head -1)
    read -r -p "Remote (default: ${REMOTE_DEFAULT}): " REMOTE_ESCOLHIDO
    REMOTE_ESCOLHIDO="${REMOTE_ESCOLHIDO:-${REMOTE_DEFAULT}}"
    echo "[push] git push ${REMOTE_ESCOLHIDO} ${BRANCH}"
    git push "${REMOTE_ESCOLHIDO}" "${BRANCH}"
else
    echo "[push pulado] rode manualmente quando quiser: git push origin ${BRANCH}"
fi

echo ""
echo "=========================================="
echo "  CHECKPOINT CONCLUIDO"
echo "=========================================="
echo ""
echo "Proximo passo: bash coletar_dados_monografia.sh"
