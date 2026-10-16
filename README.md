# felinet — feral cat monitoring by computer vision

[English](#english) · [Português](#português)

## English

Bachelor's thesis system by Felipi Soares Sousa (University of São Paulo, São Carlos). A four-stage cascade pipeline that detects, classifies and re-identifies feral cats from camera traps installed on USP's Campus 2 in São Carlos.

### Quick install

```bash
git clone https://github.com/felipiadenildo/felinet
cd felinet
make instalar     # core + dev tools: CLI, tables, figures, tests (no GPU, ~250 MB)
uv pip install -e '.[modelos]'   # adds the inference stack (torch, MegaDetector v6, SpeciesNet, MegaDescriptor)
```

The exact environment that produced the thesis results (Python 3.12, PyTorch 2.5.1 + CUDA 12.1, NVIDIA MX250)
is pinned in `requirements/ambiente-original.txt`.

### Thesis figures and tables

Every figure and table the thesis draws from data is written by felinet into the thesis repository
(`../monografia-felinet/elementos/gerados/`), as vector PDF or LaTeX, together with a `MANIFESTO.json` (sha256 of
each file, the input files it read, and the felinet commit) and a `LEIAME.md` map (LaTeX label → file → function).
The registry is `src/felinet/monografia/elementos.py`; default paths are in `configs/monografia.yaml`.

```bash
felinet monografia listar      # what the thesis uses and what this machine can generate
make monografia                # felinet monografia gerar + verificar
```

`verificar` fails if the LaTeX, the registry, the generated files and the manifest disagree, or if a table no longer
matches the runs. Details: `docs/REPRODUCAO_MONOGRAFIA.md`.

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
tests/               pytest suite (~210 tests)
```

The thesis's LaTeX manuscript is versioned separately, in the
[`monografia-engenharia-de-computacao-felinet`](https://github.com/felipiadenildo/monografia-engenharia-de-computacao-felinet)
repository (private). This repository holds only the pipeline code.

### Documentation

Technical docs live in `docs/`. The core files:

- `docs/ARQUITETURA.md` — technical view of the pipeline and the concepts of profile, mode, source, protocol, run and latest.
- `docs/DEBUGGING.md` — where to look at logs, how to inspect manifests, how to trace a specific image through the stages.
- `docs/REPRODUCAO_MONOGRAFIA.md` — where each thesis figure and table comes from, and how to regenerate it.
- `docs/DATASETS.md` — supported datasets, how to obtain them, how to add a new one.
- `docs/MODELOS.md` — models, versions, thresholds, licenses and known limitations (model card).
- `docs/runbooks/gerar_monografia_ambiente_original.md` — regenerate the thesis figures in the original environment.
- `docs/manuais/` — guides for researchers, AEX volunteers and IT maintainers.
- `docs/monografia/` — the thesis PDFs: the defended version (July 2026), the version revised by the author (October 2026) and a diff between them, with a summary of what changed.
- `docs/historico/` — planning records from the thesis period (old step numbering).

### Main commands

```bash
felinet --help
felinet easyrun                                    # interactive wizard
felinet datasets {linkar,listar}                    # local dataset management
felinet pipeline executar --fonte X --max-amostras N [--dev] [--triagem]
felinet reid {avaliar-closed,avaliar-openset}
felinet monografia {listar,gerar,verificar}        # thesis figures and tables
felinet experimentos {cascatas-multifonte,sensibilidade-limiar,visualizacao-exploratoria}
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
make instalar     # núcleo + ferramentas de desenvolvimento: CLI, tabelas, figuras, testes (sem GPU, ~250 MB)
uv pip install -e '.[modelos]'   # acrescenta a inferência (torch, MegaDetector v6, SpeciesNet, MegaDescriptor)
```

O ambiente exato em que os resultados da monografia foram gerados (Python 3.12, PyTorch 2.5.1 + CUDA 12.1,
NVIDIA MX250) está fixado em `requirements/ambiente-original.txt`.

### Figuras e tabelas da monografia

Toda figura e tabela que a monografia tira de dados é escrita pelo felinet no repositório da monografia
(`../monografia-felinet/elementos/gerados/`), em PDF vetorial ou LaTeX, com um `MANIFESTO.json` (sha256 de cada
arquivo, os arquivos de entrada lidos e o commit do felinet) e um mapa `LEIAME.md` (rótulo do LaTeX → arquivo →
função). O registro é `src/felinet/monografia/elementos.py`; os caminhos padrão ficam em `configs/monografia.yaml`.

```bash
felinet monografia listar      # o que a monografia usa e o que esta máquina consegue gerar
make monografia                # felinet monografia gerar + verificar
```

O `verificar` falha se o LaTeX, o registro, os arquivos gerados e o manifesto não baterem, ou se uma tabela não
conferir mais com os runs. Detalhes: `docs/REPRODUCAO_MONOGRAFIA.md`.

Os PDFs da monografia, nas versões defendida (julho de 2026) e revisada pelo autor (outubro de 2026), e a comparação
entre elas ficam em `docs/monografia/`.

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
tests/               suíte pytest (~210 testes)
```

O manuscrito LaTeX da monografia é versionado à parte, no repositório
[`monografia-engenharia-de-computacao-felinet`](https://github.com/felipiadenildo/monografia-engenharia-de-computacao-felinet)
(privado). Este repositório contém apenas o código do pipeline.

### Documentação

A documentação técnica fica em `docs/`. Os arquivos centrais:

- `docs/ARQUITETURA.md` — visão técnica do pipeline e dos conceitos de perfil, modo, fonte, protocolo, run e latest.
- `docs/DEBUGGING.md` — onde olhar logs, como inspecionar manifests e como rastrear uma imagem específica através das fases.
- `docs/REPRODUCAO_MONOGRAFIA.md` — de onde sai cada figura e tabela da monografia e como gerar de novo.
- `docs/DATASETS.md` — datasets suportados, como obter e como adicionar um novo.
- `docs/MODELOS.md` — modelos, versões, limiares, licenças e limitações conhecidas (model card).
- `docs/runbooks/gerar_monografia_ambiente_original.md` — gerar as figuras da monografia no ambiente original.
- `docs/manuais/` — guias para pesquisador, voluntário da AEX e mantenedor de TI.
- `docs/historico/` — registros de planejamento do período do TCC (numeração antiga de etapas).

### Comandos principais

```bash
felinet --help
felinet easyrun                                    # wizard interativo
felinet datasets {linkar,listar}                    # gestão de datasets locais
felinet pipeline executar --fonte X --max-amostras N [--dev] [--triagem]
felinet reid {avaliar-closed,avaliar-openset}
felinet monografia {listar,gerar,verificar}        # figuras e tabelas da monografia
felinet experimentos {cascatas-multifonte,sensibilidade-limiar,visualizacao-exploratoria}
felinet dev demo                                    # demo curta com galeria
```

### Hardware testado

NVIDIA MX250 com 2 GB de VRAM, CUDA 12.1. Modos sem GPU funcionam para geração de tabelas, figuras e configuração de datasets; as fases de detecção, classificação e Re-ID dependem dos pesos de MegaDetector v6 (PytorchWildlife), SpeciesNet e MegaDescriptor.

### Licença

MIT.
