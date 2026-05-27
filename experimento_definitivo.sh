#!/usr/bin/env bash
# experimento_definitivo.sh -- gera todos os dados do experimento final
# para a monografia. Rodar a partir da raiz do repo:
#
#   bash experimento_definitivo.sh 2>&1 | tee LOG_experimento.txt
#
# Esperado: 30-50min na MX250. Cada bloco e' idempotente (se algo der
# errado no meio, pode re-rodar do ponto que parou comentando os
# anteriores). NAO usa set -e: queremos ver todos os passos no LOG mesmo
# se um falhar; o smoke_test no final valida o resultado completo.

set -u
trap 'echo "[$(date +%H:%M:%S)] interrompido (sinal)"; exit 130' INT TERM

PERFIL_OP="dev"      # operacional: kaggle_cats, felidae -- com galeria visual
PERFIL_REID="prod"   # re-id: PetFace real (no perfil prod aponta para petface)
N_PIPE=300           # imagens por fonte na cascata
N_LIST=(50 100 200)  # multiplos N para Re-ID (permite cmc-comparativo)
N_PRINCIPAL=200      # N usado nas figuras "principais" (cmc, matriz_sim, etc.)
FONTES_OP=("kaggle_cats" "felidae")
SEED=42

CARIMBO() { echo "[$(date +%H:%M:%S)] $*"; }
SEPARADOR() { echo ""; echo "============================================================"; echo "  $*"; echo "============================================================"; }

# ---------------------------------------------------------------------------
# 0. Sanity + link do PetFace real (uma vez)
# ---------------------------------------------------------------------------
SEPARADOR "0. SANITY E LINK DO PETFACE"

if [[ ! -L data/raw/reid/petface && ! -d data/raw/reid/petface ]]; then
    CARIMBO "linkando PetFace real -> data/raw/reid/petface"
    mkdir -p data/raw/reid
    ln -snf /media/felipi/ssd/dados_tcc/PetFace data/raw/reid/petface
fi

CARIMBO "validando ambiente"
felinet dev validar-ambiente

CARIMBO "registrando ambiente (para apendice da monografia)"
python scripts/registrar_ambiente.py || CARIMBO "  (aviso) registrar_ambiente falhou - seguindo"

# ---------------------------------------------------------------------------
# 1. Pipeline operacional -- cascata completa nas 2 fontes
# ---------------------------------------------------------------------------
SEPARADOR "1. PIPELINE OPERACIONAL (N=${N_PIPE} por fonte, modo --dev)"

for FONTE in "${FONTES_OP[@]}"; do
    CARIMBO "pipeline: ${FONTE}"
    felinet pipeline executar \
        --perfil "${PERFIL_OP}" \
        --fonte "${FONTE}" \
        --max-amostras "${N_PIPE}" \
        --seed-amostragem "${SEED}" \
        --dev \
        --tag "monografia_n${N_PIPE}"
done

# ---------------------------------------------------------------------------
# 2. Re-ID -- extracao de embeddings em multiplos N (PetFace real)
# ---------------------------------------------------------------------------
SEPARADOR "2. RE-ID EMBEDDINGS (Ns: ${N_LIST[*]}, PetFace real)"

for N in "${N_LIST[@]}"; do
    CARIMBO "extrair-embeddings: N=${N}"
    felinet reid extrair-embeddings \
        --perfil "${PERFIL_REID}" \
        --fonte petface \
        --n "${N}"
done

# ---------------------------------------------------------------------------
# 3. Re-ID -- avaliacoes closed-set + open-set
# ---------------------------------------------------------------------------
SEPARADOR "3. AVALIACOES RE-ID (closed + openset, Ns: ${N_LIST[*]})"

for N in "${N_LIST[@]}"; do
    CARIMBO "avaliar-closed: N=${N}"
    felinet reid avaliar-closed \
        --perfil "${PERFIL_REID}" --fonte petface --n "${N}"

    CARIMBO "avaliar-openset: N=${N}"
    felinet reid avaliar-openset \
        --perfil "${PERFIL_REID}" --fonte petface --n "${N}"
done

# ---------------------------------------------------------------------------
# 4. Tabelas (todas)
# ---------------------------------------------------------------------------
SEPARADOR "4. TABELAS"

for SUB in reid-resumo openset-resumo fontes-resumo comparativo-fontes \
           datasets-avaliados run-inventory; do
    CARIMBO "tabelas ${SUB}"
    felinet tabelas "${SUB}" --perfil "${PERFIL_OP}"
done

# ---------------------------------------------------------------------------
# 5. Figuras operacionais (Blocos 7 e 9)
# ---------------------------------------------------------------------------
SEPARADOR "5. FIGURAS OPERACIONAIS"

CARIMBO "figuras comparativo-fontes"
felinet figuras comparativo-fontes \
    --perfil "${PERFIL_OP}" --fontes "$(IFS=, ; echo "${FONTES_OP[*]}")"

CARIMBO "figuras matriz-confusao-fontes"
felinet figuras matriz-confusao-fontes --perfil "${PERFIL_OP}" \
    || CARIMBO "  (aviso) matriz-confusao-fontes pode nao gerar se classe_origem nao popular"

# ---------------------------------------------------------------------------
# 6. Figuras Re-ID -- principais usam N=${N_PRINCIPAL}
# ---------------------------------------------------------------------------
SEPARADOR "6. FIGURAS RE-ID (N_principal=${N_PRINCIPAL})"

for SUB in reid-cmc matriz-similaridade dist-intra-inter roc-openset; do
    CARIMBO "figuras ${SUB}"
    felinet figuras "${SUB}" \
        --perfil "${PERFIL_REID}" --fonte petface --n "${N_PRINCIPAL}"
done

CARIMBO "figuras galeria-erros (opcional)"
felinet figuras galeria-erros \
    --perfil "${PERFIL_REID}" --fonte petface --n "${N_PRINCIPAL}" \
    || CARIMBO "  (aviso) galeria-erros nao gera se modelo acertou tudo"

CARIMBO "figuras cmc-comparativo (Ns=${N_LIST[*]})"
felinet figuras cmc-comparativo \
    --perfil "${PERFIL_REID}" --fonte petface \
    --ns "$(IFS=, ; echo "${N_LIST[*]}")"

# ---------------------------------------------------------------------------
# 7. Resumo HTML das galerias visuais
# ---------------------------------------------------------------------------
SEPARADOR "7. RESUMO HTML POR FONTE"

for FONTE in "${FONTES_OP[@]}"; do
    CARIMBO "dev gerar-resumo-html: ${FONTE}"
    felinet dev gerar-resumo-html --fonte "${FONTE}" --perfil "${PERFIL_OP}"
done

# ---------------------------------------------------------------------------
# 8. Inventario final
# ---------------------------------------------------------------------------
SEPARADOR "8. INVENTARIO FINAL"

CARIMBO "tabelas geradas:"
find artifacts/tabelas -type f \( -name '*.csv' -o -name '*.tex' \) \
    | sort | sed 's/^/  /'

echo ""
CARIMBO "figuras geradas:"
find artifacts/figuras -type f \( -name '*.png' -o -name '*.pdf' \) \
    | sort | sed 's/^/  /'

echo ""
CARIMBO "runs criados:"
find runs -maxdepth 5 -name 'manifest.json' \
    | sort | sed 's/^/  /'

echo ""
CARIMBO "ambiente registrado:"
ls -la runs/_ambiente/ 2>/dev/null || echo "  (vazio)"

echo ""
SEPARADOR "EXPERIMENTO DEFINITIVO CONCLUIDO"
echo ""
echo "Proximos passos sugeridos:"
echo "  1) Abrir o resumo.html de cada fonte no navegador"
echo "  2) Inspecionar artifacts/tabelas/ e artifacts/figuras/"
echo "  3) Rodar 'python scripts/smoke_test.py' para validacao final"
echo "  4) Iniciar redacao do Cap. 4 da monografia"
