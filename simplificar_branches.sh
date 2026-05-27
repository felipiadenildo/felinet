#!/usr/bin/env bash
# simplificar_branches.sh
# Push main (force-with-lease) + tags para origin e remove branches/stashes obsoletos.
# Estratégia decidida nesta sessão:
#   - Divergência: force-with-lease (apaga c7fe5a8 do remote, conteúdo já existe via 0985863)
#   - Stash: clear (todos WIP pre-checkpoint, já incorporados)
#   - Branches: branch -d (todas já mergeadas em main, seguro)

set -euo pipefail

REPO_DIR="${1:-$HOME/Desktop/tcc/tcc_gatos_campus2_v22}"
MAIN_BRANCH="main"
REMOTE="origin"

BRANCHES_LOCAIS=(
  "chore/ruff-format-massa"
  "chore/ruff-lint-config"
  "refactor/felinet-src-layout"
  "refactor/layout-runs"
  "refactor/v23-release-candidate"
)

BRANCHES_REMOTAS=(
  "refactor/felinet-src-layout"
  "refactor/layout-runs"
  "refactor/v23-release-candidate"
)

say()  { printf '\n\033[1;36m▶ %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m✓ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m⚠ %s\033[0m\n' "$*"; }
fail() { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

confirma() {
  read -r -p "$1 [s/N] " resp
  [[ "$resp" =~ ^[sS]$ ]]
}

# ---------- pre-flight ----------
cd "$REPO_DIR" || fail "Repo não encontrado: $REPO_DIR"
say "Repo: $(pwd)"

branch_atual=$(git symbolic-ref --short HEAD)
[[ "$branch_atual" == "$MAIN_BRANCH" ]] || fail "HEAD não está em $MAIN_BRANCH (atual: $branch_atual)."
[[ -z "$(git status --porcelain)" ]] || fail "Working tree não está limpa."

say "git fetch --all --prune --tags"
git fetch --all --prune --tags
ok "fetch OK"

# ---------- 1) Push force-with-lease ----------
say "Push de main (force-with-lease) + tags"
echo "Commits que serão enviados:"
git log --oneline "$REMOTE/$MAIN_BRANCH".."$MAIN_BRANCH" || true
echo ""
echo "Commit que será sobrescrito no remote (já incorporado localmente via outro caminho):"
git log --oneline "$MAIN_BRANCH".."$REMOTE/$MAIN_BRANCH" || true
echo ""
if confirma "Executar 'git push --force-with-lease origin main --follow-tags'?"; then
  git push --force-with-lease "$REMOTE" "$MAIN_BRANCH" --follow-tags
  ok "main + tags enviados (force-with-lease)"
else
  fail "Abortado pelo usuário antes do push."
fi

# ---------- 2) Stash clear ----------
say "Limpando stashes"
if git stash list | grep -q .; then
  git stash list
  if confirma "Executar 'git stash clear' (remove TODOS)?"; then
    git stash clear
    ok "stash limpo"
  else
    warn "stash mantido"
  fi
else
  ok "nenhum stash"
fi

# ---------- 3) Branches locais ----------
say "Deletando branches locais mergeadas"
for br in "${BRANCHES_LOCAIS[@]}"; do
  if ! git show-ref --verify --quiet "refs/heads/$br"; then
    warn "  $br não existe localmente — pulado"
    continue
  fi
  if ! git merge-base --is-ancestor "$br" "$MAIN_BRANCH"; then
    warn "  $br NÃO está mergeada em $MAIN_BRANCH — pulado (não deveria acontecer)"
    continue
  fi
  if confirma "  Deletar local $br?"; then
    git branch -d "$br"
    ok "  deletada: $br"
  else
    warn "  pulada: $br"
  fi
done

# ---------- 4) Branches remotas ----------
say "Deletando branches remotas mergeadas"
for br in "${BRANCHES_REMOTAS[@]}"; do
  if ! git show-ref --verify --quiet "refs/remotes/$REMOTE/$br"; then
    warn "  $REMOTE/$br não existe — pulado"
    continue
  fi
  if confirma "  Deletar remota $REMOTE/$br?"; then
    git push "$REMOTE" --delete "$br"
    ok "  remota deletada: $br"
  else
    warn "  pulada: $br"
  fi
done

# ---------- 5) Limpeza final ----------
say "Limpeza final"
git remote prune "$REMOTE"
ok "prune OK"

say "Estado final:"
echo "--- branches locais ---"; git branch
echo "--- branches remotas ---"; git branch -r
echo "--- tags recentes ---"; git tag --sort=-creatordate | head -5
echo "--- último commit ---"; git log --oneline -1

ok "Cleanup completo."
