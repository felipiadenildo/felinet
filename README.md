# felinet — feral cat monitoring by computer vision

[English](#english) · [Português](#português)

## English

Bachelor's thesis system by Felipi Soares Sousa (University of São Paulo, São Carlos). A four-stage cascade pipeline that detects, classifies and re-identifies feral cats from camera traps installed on USP's Campus 2 in São Carlos.

### Quick install

```bash
git clone https://github.com/felipiadenildo/felinet
cd felinet
make instalar     # uv pip install -e '.[dev]'
make pre-commit-install   # optional: ruff + pytest hooks
```

### Getting started

Dataset setup happens once per machine. `configs/datasets_locais.yaml` is versioned only as a template; each user copies it and points the paths at their own disk.

```bash
cp configs/datasets_locais.example.yaml configs/datasets_locais.yaml
# edit configs/datasets_locais.yaml with your paths
felinet datasets linkar           # creates symlinks in data/raw/
felinet datasets listar           # confirms each source's status
felinet easyrun                   # interactive wizard
```

### Validate the pipeline visually (~10 min)

```bash
felinet dev demo --fonte kaggle_cats --n 50
# inspect runs/operacional/kaggle_cats/dev/_/latest/dev_visualizacao/
```

The gallery produced by `--dev` mode groups accepted/rejected images from ingestion, the bounding boxes overlaid after detection, and the crops classified as *Felis catus* or other species. It's the fastest way to check visually whether the pipeline still works after changing a model, threshold or source.

### Structure

```
src/felinet/         main package (CLI, stages, datasets, runs)
configs/             versioned YAMLs (paths.yaml, modelos.yaml, ...)
docs/                technical documentation (architecture, debugging, ...)
data/                local sources (data/raw/*) and dev samples
runs/                traceable output of each execution
artifacts/           figures and tables generated for the thesis
tests/               pytest suite (~150 tests)
```

The thesis's LaTeX manuscript is versioned separately, in the
[`monografia-tcc-felinet`](https://github.com/felipiadenildo/monografia-tcc-felinet)
repository (private). This repository holds only the pipeline code.

### Documentation

Technical docs live in `docs/`. The core files:

- `docs/ARQUITETURA.md` — technical view of the pipeline and the concepts of profile, mode, source, protocol, run and latest.
- `docs/DEBUGGING.md` — where to look at logs, how to inspect manifests, how to trace a specific image through the stages.
- `docs/REPRODUCAO_MONOGRAFIA.md` — the exact command sequence to regenerate every artifact cited in the thesis.
- `docs/DATASETS.md` — supported datasets, how to obtain them, how to add a new one.
- `docs/governanca/MIGRACAO_v22_para_v23.md` — a record of every change between versions.

### Main commands

```bash
felinet --help
felinet easyrun                                    # interactive wizard
felinet datasets {linkar,listar}                    # local dataset management
felinet pipeline executar --fonte X --max-amostras N [--dev]
felinet reid {avaliar-closed,avaliar-openset}
felinet tabelas {comparativo-fontes,fontes-resumo,...}
felinet figuras {comparativo-fontes,reid-cmc,...}
felinet dev demo                                    # short demo with gallery
```

### Tested hardware

NVIDIA MX250 with 2 GB VRAM, CUDA 12.1. GPU-free modes work for table generation, figures and dataset setup; the detection, classification and Re-ID stages depend on weights from MegaDetector v6 (PytorchWildlife), SpeciesNet and MegaDescriptor.

### License

MIT.

---

## Português

Sistema do TCC de Felipi Soares Sousa (USP São Carlos). Pipeline em cascata de quatro fases para detectar, classificar e re-identificar gatos ferais a partir de armadilhas fotográficas instaladas no Campus 2 da USP em São Carlos.

### Instalação rápida

```bash
git clone https://github.com/felipiadenildo/felinet
cd felinet
make instalar     # uv pip install -e '.[dev]'
make pre-commit-install   # opcional: hooks ruff + pytest
```

### Primeiros passos

A configuração de datasets é feita uma única vez por máquina. O arquivo `configs/datasets_locais.yaml` é versionado apenas como exemplo; cada usuário copia o template e ajusta os caminhos do próprio disco.

```bash
cp configs/datasets_locais.example.yaml configs/datasets_locais.yaml
# editar configs/datasets_locais.yaml com seus caminhos
felinet datasets linkar           # cria symlinks em data/raw/
felinet datasets listar           # confirma status de cada fonte
felinet easyrun                   # wizard interativo
```

### Validar pipeline visualmente (~10 min)

```bash
felinet dev demo --fonte kaggle_cats --n 50
# inspecionar runs/operacional/kaggle_cats/dev/_/latest/dev_visualizacao/
```

A galeria produzida pelo modo `--dev` agrupa as imagens aceitas ou rejeitadas na ingestão, as bounding boxes sobrepostas depois da detecção, e os crops classificados como *Felis catus* ou outras espécies. É a forma mais rápida de checar visualmente se o pipeline continua funcionando depois de trocar modelo, limiar ou fonte.

### Estrutura

```
src/felinet/         pacote principal (CLI, fases, datasets, runs)
configs/             YAMLs versionados (paths.yaml, modelos.yaml, ...)
docs/                documentação técnica (arquitetura, debugging, ...)
data/                fontes locais (data/raw/*) e amostras dev
runs/                saídas rastreáveis de cada execução
artifacts/           figuras e tabelas geradas para a monografia
tests/               suíte pytest (~150 testes)
```

O manuscrito LaTeX da monografia é versionado à parte, no repositório
[`monografia-tcc-felinet`](https://github.com/felipiadenildo/monografia-tcc-felinet)
(privado). Este repositório contém apenas o código do pipeline.

### Documentação

A documentação técnica fica em `docs/`. Os arquivos centrais:

- `docs/ARQUITETURA.md` — visão técnica do pipeline e dos conceitos de perfil, modo, fonte, protocolo, run e latest.
- `docs/DEBUGGING.md` — onde olhar logs, como inspecionar manifests e como rastrear uma imagem específica através das fases.
- `docs/REPRODUCAO_MONOGRAFIA.md` — sequência exata de comandos para gerar cada artefato citado na monografia.
- `docs/DATASETS.md` — datasets suportados, como obter e como adicionar um novo.
- `docs/governanca/MIGRACAO_v22_para_v23.md` — registro de todas as mudanças entre versões.

### Comandos principais

```bash
felinet --help
felinet easyrun                                    # wizard interativo
felinet datasets {linkar,listar}                    # gestão de datasets locais
felinet pipeline executar --fonte X --max-amostras N [--dev]
felinet reid {avaliar-closed,avaliar-openset}
felinet tabelas {comparativo-fontes,fontes-resumo,...}
felinet figuras {comparativo-fontes,reid-cmc,...}
felinet dev demo                                    # demo curta com galeria
```

### Hardware testado

NVIDIA MX250 com 2 GB de VRAM, CUDA 12.1. Modos sem GPU funcionam para geração de tabelas, figuras e configuração de datasets; as fases de detecção, classificação e Re-ID dependem dos pesos de MegaDetector v6 (PytorchWildlife), SpeciesNet e MegaDescriptor.

### Licença

MIT.
