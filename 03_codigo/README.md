# 03 — Código

Implementação computacional do pipeline de visão computacional. Tudo aqui roda no **notebook do Pesquisador** (`[PLACEHOLDER-HARDWARE-NOTEBOOK]`).

## Setup

```bash
# 1. Instalar uv (se ainda não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Sincronizar dependências (a partir da raiz do projeto)
cd ..   # volta para a raiz
uv sync

# 3. Ativar o ambiente
source .venv/bin/activate

# 4. Verificar
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `pipeline/E0_ingestao/` | Leitura de cartão SD, validação SHA-256, clock-drift, conversão para Camtrap-DP |
| `pipeline/E1_deteccao/` | MegaDetector v6-compact, YOLO11n (contraprova) |
| `pipeline/E2_classificacao/` | SpeciesNet + classificador local (gato vs. não-gato, fauna sinantrópica/silvestre) |
| `pipeline/E2_6_preprocessamento/` | Crops, normalização, augmentation, filtros |
| `pipeline/E3_reid/` | MiewID multispecies, MegaDescriptor (baseline), PPGNet-Cat (referência) |
| `pipeline/E4_persistencia/` | SQLite (Camtrap-DP schema), hnswlib (índice de embeddings) |
| `notebooks/` | Jupyter para exploração, ablação e geração de gráficos (saídas em `05_figuras/`) |
| `scripts/` | CLIs (ingestao_cartao.py, treinar_reid.py, export_relatorio.py) |
| `tests/` | pytest |
| `configs/` | YAMLs de configuração por experimento (rastreado em MLflow) |

## Convenções

- Python 3.11+, type hints em todas as funções públicas.
- Lint: `ruff check .` | Format: `ruff format .`
- Type-check opcional: `mypy 03_codigo/`
- Testes: `pytest`
- Cada experimento tem um `configs/exp_NNN_descricao.yaml` e fica rastreado no MLflow.
