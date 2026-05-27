#!/usr/bin/env bash
# =============================================================
# instalar_figuras_cap5.sh
# -------------------------------------------------------------
# Copia as figuras geradas pelo pipeline (artifacts/figuras/...)
# para o diretorio que o LaTeX consome (tex/figuras/cap5/).
#
# Premissa: \graphicspath{{figuras/}{USPSC-img/}} no preambulo,
# entao basta colocar PNG em tex/figuras/cap5/ e referenciar como
# \includegraphics{cap5/<arquivo>.png}.
#
# Estrutura esperada (executar a partir da raiz do projeto):
#   tcc_gatos_campus2_v22/
#     artifacts/figuras/metodologico/petface/...   (origem)
#     tex/figuras/cap5/                            (destino)
#     instalar_figuras_cap5.sh                     (este arquivo)
#
# Uso:
#   ./instalar_figuras_cap5.sh             # executa
#   ./instalar_figuras_cap5.sh --dry-run   # so mostra
#   ./instalar_figuras_cap5.sh --force     # sobrescreve mesmo iguais
#   ./instalar_figuras_cap5.sh -h          # ajuda
#
# Flags opcionais:
#   --proj-root <path>   raiz do projeto (default: cwd)
# =============================================================
set -euo pipefail

# ------- defaults -------
PROJ_ROOT="$(pwd)"
DRY_RUN=0
FORCE=0

# ------- parse args -------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --proj-root) PROJ_ROOT="$2"; shift 2 ;;
    --dry-run)   DRY_RUN=1; shift ;;
    --force)     FORCE=1; shift ;;
    -h|--help)
      sed -n '1,30p' "$0" | sed -n '/^#/p' | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "[ERRO] flag desconhecida: $1" >&2; exit 2 ;;
  esac
done

# ------- helpers -------
log()   { printf "[%s] %s\n" "$(date +%H:%M:%S)" "$*"; }
fatal() { printf "[ERRO] %s\n" "$*" >&2; exit 1; }

ARTIFACTS_ROOT="${PROJ_ROOT}/artifacts/figuras"
TEX_FIG_ROOT="${PROJ_ROOT}/tex/elementos/figuras"
DEST_DIR="${TEX_FIG_ROOT}/cap5"

# Tabela: origem (relativa a artifacts/figuras) | destino (nome em cap5/)
# Renomeacao codifica o N para evitar colisao entre n0050, n0100, n0200.
read -r -d '' MAPEAMENTO <<'EOF' || true
metodologico/petface/reid_cmc_comparativo.png|reid_cmc_comparativo.png
metodologico/petface/n0050/reid_cmc.png|reid_cmc_n0050.png
metodologico/petface/n0100/reid_cmc.png|reid_cmc_n0100.png
metodologico/petface/n0200/reid_cmc.png|reid_cmc_n0200.png
metodologico/petface/n0050/reid_matriz_sim.png|reid_matriz_sim_n0050.png
metodologico/petface/n0100/reid_matriz_sim.png|reid_matriz_sim_n0100.png
metodologico/petface/n0200/reid_matriz_sim.png|reid_matriz_sim_n0200.png
metodologico/petface/n0050/reid_dist_intra_inter.png|reid_dist_intra_inter_n0050.png
metodologico/petface/n0100/reid_dist_intra_inter.png|reid_dist_intra_inter_n0100.png
metodologico/petface/n0200/reid_dist_intra_inter.png|reid_dist_intra_inter_n0200.png
metodologico/petface/openset_n0050/reid_roc_openset.png|reid_roc_openset_n0050.png
metodologico/petface/openset_n0100/reid_roc_openset.png|reid_roc_openset_n0100.png
metodologico/petface/openset_n0200/reid_roc_openset.png|reid_roc_openset_n0200.png
EOF

# Figura extra que NAO esta em artifacts/ (gerada manualmente).
# Espera-se que voce baixe comparativo_fontes_v8.png e coloque em
# qualquer um dos caminhos abaixo (script aceita o primeiro encontrado).
EXTRA_CANDIDATOS=(
  "${PROJ_ROOT}/comparativo_fontes_v8.png"
  "${PROJ_ROOT}/Downloads/comparativo_fontes_v8.png"
  "${HOME}/Downloads/comparativo_fontes_v8.png"
  "${PROJ_ROOT}/tex/figuras/cap5/comparativo_fontes_v8.png"
)

# ------- sanity -------
log "PROJ_ROOT      = ${PROJ_ROOT}"
log "ARTIFACTS_ROOT = ${ARTIFACTS_ROOT}"
log "DEST_DIR       = ${DEST_DIR}"
[[ -d "${PROJ_ROOT}" ]]      || fatal "PROJ_ROOT nao existe: ${PROJ_ROOT}"
[[ -d "${ARTIFACTS_ROOT}" ]] || fatal "artifacts/figuras/ nao existe. Rode o pipeline primeiro."
[[ -d "${TEX_FIG_ROOT}" ]]   || fatal "tex/figuras/ nao existe. Confirme estrutura do projeto."

if (( DRY_RUN == 0 )); then
  mkdir -p "${DEST_DIR}"
fi

# ------- copia mapeamento -------
total=0; copiados=0; pulados=0; faltando=0
while IFS='|' read -r origem destino; do
  [[ -z "${origem// }" || "${origem:0:1}" == "#" ]] && continue
  total=$((total+1))

  ORIG="${ARTIFACTS_ROOT}/${origem}"
  DEST="${DEST_DIR}/${destino}"

  if [[ ! -f "${ORIG}" ]]; then
    log "  [FALTA]   ${origem}"
    faltando=$((faltando+1))
    continue
  fi

  if [[ -f "${DEST}" && ${FORCE} -eq 0 ]] && cmp -s "${ORIG}" "${DEST}"; then
    log "  [SKIP]    ${destino}  (igual)"
    pulados=$((pulados+1))
    continue
  fi

  if (( DRY_RUN )); then
    log "  [DRY]     ${origem}  ->  cap5/${destino}"
  else
    install -m 0644 "${ORIG}" "${DEST}"
    log "  [COPY]    cap5/${destino}  ($(stat -c%s "${DEST}") bytes)"
  fi
  copiados=$((copiados+1))
done <<< "${MAPEAMENTO}"

# ------- figura extra (comparativo_fontes_v8) -------
total=$((total+1))
EXTRA_ORIG=""
for c in "${EXTRA_CANDIDATOS[@]}"; do
  [[ -f "$c" ]] && { EXTRA_ORIG="$c"; break; }
done

EXTRA_DEST="${DEST_DIR}/comparativo_fontes_v8.png"
if [[ -z "${EXTRA_ORIG}" ]]; then
  log "  [FALTA]   comparativo_fontes_v8.png  (procurei em: ${EXTRA_CANDIDATOS[*]})"
  log "             baixe do chat e coloque em ${PROJ_ROOT}/ ou ~/Downloads/"
  faltando=$((faltando+1))
elif [[ -f "${EXTRA_DEST}" && ${FORCE} -eq 0 ]] && cmp -s "${EXTRA_ORIG}" "${EXTRA_DEST}"; then
  log "  [SKIP]    cap5/comparativo_fontes_v8.png  (igual)"
  pulados=$((pulados+1))
else
  if (( DRY_RUN )); then
    log "  [DRY]     ${EXTRA_ORIG}  ->  cap5/comparativo_fontes_v8.png"
  else
    install -m 0644 "${EXTRA_ORIG}" "${EXTRA_DEST}"
    log "  [COPY]    cap5/comparativo_fontes_v8.png  ($(stat -c%s "${EXTRA_DEST}") bytes)"
  fi
  copiados=$((copiados+1))
fi

# ------- resumo -------
echo
log "Resumo:"
log "  total declarado : ${total}"
log "  copiados        : ${copiados}"
log "  pulados (igual) : ${pulados}"
log "  faltando        : ${faltando}"

if (( faltando > 0 )); then
  echo
  log "Algumas origens nao foram encontradas. Re-rode o pipeline e/ou"
  log "baixe a figura extra do chat."
  exit 1
fi

if (( DRY_RUN )); then
  echo
  log "Modo dry-run. Para aplicar, rode novamente sem --dry-run."
fi

log "OK."
