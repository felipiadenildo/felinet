#!/usr/bin/env bash
# coletar_dados_monografia.sh -- empacota tudo que preciso para diagnostico
# do resumo.html e redacao do Cap. 4 da monografia.
#
# Rodar da raiz do repo:
#   bash coletar_dados_monografia.sh
#
# Gera: dados_monografia.zip (pequeno, ~MB) com:
#   - todas as tabelas CSV/TeX
#   - todas as figuras PNG/PDF
#   - metricas.json de TODOS os runs Re-ID
#   - manifest.json de TODOS os runs operacionais
#   - resumo.html das 2 fontes operacionais
#   - amostra de CSVs internos dos runs (motivos, deteccoes, classificacoes,
#     reidentification) -- so as primeiras 50 linhas para nao explodir o ZIP
#   - registro de ambiente
#   - inventario do que foi coletado

set -u

ROOT="$(pwd)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
SAIDA="dados_monografia_${TS}"
ALVO="${ROOT}/${SAIDA}"

if [[ ! -d artifacts || ! -d runs ]]; then
    echo "[erro] precisa rodar a partir da raiz do repo (faltam artifacts/ ou runs/)."
    exit 1
fi

echo "=========================================="
echo "  COLETOR DE DADOS DA MONOGRAFIA"
echo "  saida: ${SAIDA}/"
echo "=========================================="
echo ""

rm -rf "${ALVO}"
mkdir -p "${ALVO}"

# ---------------------------------------------------------------------------
# 1. Artefatos finais (tabelas + figuras)
# ---------------------------------------------------------------------------
echo "[1/6] copiando artifacts/ (tabelas + figuras)..."
cp -r artifacts "${ALVO}/artifacts"
echo "  $(find "${ALVO}/artifacts" -type f | wc -l) arquivos"

# ---------------------------------------------------------------------------
# 2. Metricas Re-ID (todos os runs metodologicos)
# ---------------------------------------------------------------------------
echo ""
echo "[2/6] coletando metricas.json dos runs Re-ID..."
mkdir -p "${ALVO}/runs_metodologico"
n_metricas=0
while IFS= read -r arq; do
    rel="${arq#runs/metodologico/}"
    destino="${ALVO}/runs_metodologico/${rel}"
    mkdir -p "$(dirname "${destino}")"
    cp "${arq}" "${destino}"
    n_metricas=$((n_metricas + 1))
done < <(find runs/metodologico -name 'metricas.json' 2>/dev/null)
echo "  ${n_metricas} arquivos metricas.json"

# Tambem o manifest.json de cada run metodologico
while IFS= read -r arq; do
    rel="${arq#runs/metodologico/}"
    destino="${ALVO}/runs_metodologico/${rel}"
    mkdir -p "$(dirname "${destino}")"
    cp "${arq}" "${destino}"
done < <(find runs/metodologico -name 'manifest.json' 2>/dev/null)

# ---------------------------------------------------------------------------
# 3. Runs operacionais -- manifest + resumo.html + amostras dos CSVs
# ---------------------------------------------------------------------------
echo ""
echo "[3/6] coletando runs operacionais (kaggle_cats + felidae)..."
mkdir -p "${ALVO}/runs_operacional"
n_op=0
for FONTE in kaggle_cats felidae; do
    # acha o run mais recente da fonte (perfil dev)
    BASE_RUN=$(find "runs/operacional/${FONTE}/dev/_" -maxdepth 1 -mindepth 1 -type d 2>/dev/null \
               | sort | tail -1)
    if [[ -z "${BASE_RUN}" ]]; then
        echo "  [aviso] sem run para ${FONTE}"
        continue
    fi
    REL="${BASE_RUN#runs/operacional/}"
    DEST="${ALVO}/runs_operacional/${REL}"
    mkdir -p "${DEST}"

    # manifest completo
    [[ -f "${BASE_RUN}/manifest.json" ]] && cp "${BASE_RUN}/manifest.json" "${DEST}/"

    # resumo.html da galeria dev
    if [[ -f "${BASE_RUN}/dev_visualizacao/resumo.html" ]]; then
        mkdir -p "${DEST}/dev_visualizacao"
        cp "${BASE_RUN}/dev_visualizacao/resumo.html" "${DEST}/dev_visualizacao/"
        # tambem listamos arquivos da galeria (sem copiar imagens, so o inventario)
        find "${BASE_RUN}/dev_visualizacao" -type f | sed "s|${BASE_RUN}/||" \
            > "${DEST}/dev_visualizacao/_inventario.txt"
    fi

    # amostras dos CSVs (head 50 linhas + tail 5 + contagem total)
    for CSV in 01_ingestao/motivos.csv \
               02_manifesto/manifesto.csv \
               02_deteccao/deteccoes.csv \
               03_classificacao/classificacoes.csv \
               03_deteccoes/deteccoes.csv \
               04_classificacoes/classificacoes.csv; do
        SRC="${BASE_RUN}/${CSV}"
        if [[ -f "${SRC}" ]]; then
            DEST_CSV="${DEST}/${CSV}.amostra"
            mkdir -p "$(dirname "${DEST_CSV}")"
            {
                echo "# arquivo original: ${SRC}"
                echo "# total de linhas: $(wc -l < "${SRC}")"
                echo "# === PRIMEIRAS 50 LINHAS ==="
                head -n 50 "${SRC}"
                echo "# === ULTIMAS 5 LINHAS ==="
                tail -n 5 "${SRC}"
            } > "${DEST_CSV}"
        fi
    done

    # listagem completa de arquivos do run (estrutura)
    find "${BASE_RUN}" -maxdepth 3 -type f | sed "s|${BASE_RUN}/||" | sort \
        > "${DEST}/_estrutura_run.txt"

    n_op=$((n_op + 1))
done
echo "  ${n_op} runs operacionais coletados"

# ---------------------------------------------------------------------------
# 4. Registro de ambiente
# ---------------------------------------------------------------------------
echo ""
echo "[4/6] copiando registro de ambiente..."
if [[ -d runs/_ambiente ]]; then
    mkdir -p "${ALVO}/runs_ambiente"
    cp -r runs/_ambiente/* "${ALVO}/runs_ambiente/" 2>/dev/null
    n_amb=$(ls -1 "${ALVO}/runs_ambiente" 2>/dev/null | wc -l)
    echo "  ${n_amb} arquivos de ambiente"
fi

# ---------------------------------------------------------------------------
# 5. Logs/relatorios soltos na raiz
# ---------------------------------------------------------------------------
echo ""
echo "[5/6] copiando logs e relatorios soltos..."
for f in RELATORIO_SMOKE.md LOG_experimento.txt; do
    if [[ -f "${f}" ]]; then
        cp "${f}" "${ALVO}/"
        echo "  + ${f}"
    fi
done

# ---------------------------------------------------------------------------
# 6. Inventario final + ZIP
# ---------------------------------------------------------------------------
echo ""
echo "[6/6] gerando inventario e empacotando..."

{
    echo "Inventario do pacote dados_monografia (${TS})"
    echo "=============================================="
    echo ""
    echo "Repo: ${ROOT}"
    echo "Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
    echo "Commit: $(git rev-parse --short HEAD 2>/dev/null || echo '?')"
    echo ""
    echo "## Estrutura"
    echo ""
    (cd "${ALVO}" && find . -maxdepth 4 -type d | sort)
    echo ""
    echo "## Arquivos coletados"
    echo ""
    (cd "${ALVO}" && find . -type f | sort)
    echo ""
    echo "## Tamanhos"
    du -sh "${ALVO}"/* 2>/dev/null
} > "${ALVO}/_INVENTARIO.txt"

cd "${ROOT}"
ZIP_PATH="${ROOT}/dados_monografia.zip"
rm -f "${ZIP_PATH}"
zip -r "${ZIP_PATH}" "${SAIDA}/" -q

TAM=$(du -h "${ZIP_PATH}" | awk '{print $1}')

echo ""
echo "=========================================="
echo "  COLETOR CONCLUIDO"
echo "=========================================="
echo ""
echo "  ZIP: ${ZIP_PATH} (${TAM})"
echo "  Pasta: ${ALVO}/"
echo ""
echo "Conteudo resumido:"
unzip -l "${ZIP_PATH}" | tail -20
echo ""
echo "Envie o ZIP no proximo turno do chat."
