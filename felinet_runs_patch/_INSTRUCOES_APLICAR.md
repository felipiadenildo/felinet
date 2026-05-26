# Patch: layout runs/ + multifonte

## O que muda

- Novo helper `src/felinet/runs.py` (gerencia runs com manifest + latest).
- `configs/paths.yaml` ganha secao `fontes:` e `raiz_runs:`.
- Comandos `pipeline`, `reid`, `figuras`, `tabelas` aceitam `--fonte/--tag/--protocolo`.
- Orquestrador agora grava dentro de um `RunDir` (nao mais nas pastas fixas do perfil).
- Novo `scripts/organizar_layout.py` cria a arvore `runs/`, `data/raw/`, etc.
- Novo doc `docs/arquitetura/layout_runs.md`.
- Novo `tests/test_runs.py` (12 testes); `tests/test_pipeline_orquestrador.py` atualizado.

Os caminhos legados em `paths.yaml` (`saida_manifesto`, etc.) foram mantidos
para nao quebrar codigo que dependia deles, mas o novo fluxo grava em `runs/`.

## Como aplicar

A partir da raiz do repo (`~/Desktop/tcc/tcc_gatos_campus2_v22`), com working
tree limpo:

```bash
# 1) Backup do estado atual
git checkout -b refactor/layout-runs
git tag -a pre-layout-runs -m "Estado antes do layout runs/"

# 2) Extrair o patch sobre o repo (sobrescreve os arquivos listados acima)
cd ~/Desktop/tcc/tcc_gatos_campus2_v22
unzip -o /caminho/para/felinet_runs_patch.zip

# 3) Inspecionar diff
git status
git diff src/felinet/runs.py        # arquivo novo
git diff configs/paths.yaml         # cresceu (fontes:, raiz_runs:)
git diff src/felinet/comandos/      # comandos refatorados

# 4) Criar layout fisico
python scripts/organizar_layout.py            # cria runs/, data/raw/, etc.
# (idempotente -- pode rodar com --dry-run antes para inspecionar)

# 5) Rodar testes
pytest -q
# Esperado: 90 testes verdes (77 antigos + 13 novos)

# 6) Commit
git add -A
git status
git commit -m "feat: layout runs/ multifonte com manifest e latest

- src/felinet/runs.py: gerenciamento de runs (criar, finalizar, latest)
- configs/paths.yaml: secao 'fontes:' + 'raiz_runs:'
- comandos pipeline/reid/figuras/tabelas aceitam --fonte/--tag/--protocolo
- orquestrador grava em RunDir (manifest.json com tupla rastreavel)
- scripts/organizar_layout.py: cria arvore runs/ + data/raw/
- docs/arquitetura/layout_runs.md: documentacao completa
- testes: test_runs.py (13 testes) + test_pipeline_orquestrador.py atualizado

Refs: docs/arquitetura/layout_runs.md"
```

## Smoke test depois do commit

```bash
# Cascata operacional sobre placeholders dev (perfil dev, sem GPU pesada)
felinet pipeline executar --perfil dev
# -> grava em runs/operacional/dev_placeholders/dev/_/<gitsha>/

# Listar runs operacionais
felinet pipeline listar

# Resumir o latest
felinet pipeline resumir --perfil dev
```

## Quando ativar Kaggle (proximo passo)

```bash
# 1) Configurar credenciais Kaggle (~/.kaggle/kaggle.json)
mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json
uv pip install kagglehub

# 2) Baixar e linkar
KAGGLE_PATH=$(python -c "import kagglehub; print(kagglehub.dataset_download('samuelayman/cat-dataset'))")
echo "Dataset baixado em: $KAGGLE_PATH"
ln -s "$KAGGLE_PATH" data/raw/camera_trap/kaggle_cats

# 3) Rodar
felinet pipeline executar --perfil dev --fonte kaggle_cats
# -> grava em runs/operacional/kaggle_cats/dev/_/<gitsha>/
```

## Quando ativar PetFace

```bash
# Symlink para o PetFace ja baixado em algum lugar
ln -s ~/datasets/petface data/raw/reid/petface

# Extrair embeddings + avaliar
felinet reid extrair-embeddings --perfil prod --fonte petface --n 50
felinet reid avaliar-closed --perfil prod --fonte petface --n 50
felinet reid avaliar-openset --perfil prod --fonte petface --n 50

# Gerar tabela para a monografia
felinet tabelas reid-resumo --perfil prod --fonte petface --ns 50,200,500
# -> artifacts/tabelas/metodologico/petface/reid_resumo.{csv,tex}
```
