# felinet — monitoramento de gatos ferais por visão computacional

Sistema do TCC de Felipi Soares Sousa (USP São Carlos). Pipeline em cascata
de quatro fases para detectar, classificar e re-identificar gatos ferais a
partir de armadilhas fotográficas instaladas no Campus 2 da USP em
São Carlos.

## Instalação rápida

```bash
git clone https://github.com/felipiadenildo/tcc-gatos-campus2
cd tcc-gatos-campus2
make instalar     # uv pip install -e '.[dev]'
make pre-commit-install   # opcional: hooks ruff + pytest
```

## Primeiros passos

A configuração de datasets é feita uma única vez por máquina. O arquivo
``configs/datasets_locais.yaml`` é versionado apenas como exemplo; cada
usuário copia o template e ajusta os caminhos do próprio disco.

```bash
cp configs/datasets_locais.example.yaml configs/datasets_locais.yaml
# editar configs/datasets_locais.yaml com seus caminhos
felinet datasets linkar           # cria symlinks em data/raw/
felinet datasets listar           # confirma status de cada fonte
felinet easyrun                   # wizard interativo
```

## Validar pipeline didaticamente (~10 min)

```bash
felinet dev demo --fonte kaggle_cats --n 50
# inspecionar runs/operacional/kaggle_cats/dev/_/latest/dev_visualizacao/
```

A galeria visual produzida pelo modo ``--dev`` agrupa as imagens
aceitas/rejeitadas na ingestão, as bbox sobrepostas após a detecção e os
crops classificados como Felis catus ou outras espécies. É a forma mais
rápida de validar visualmente se o pipeline está funcionando após mudanças
de modelo, limiar ou fonte.

## Estrutura

```
src/felinet/         pacote principal (CLI, fases, datasets, runs)
configs/             YAMLs versionados (paths.yaml, modelos.yaml, ...)
docs/                documentação técnica (arquitetura, debugging, ...)
data/                fontes locais (data/raw/*) e amostras dev
runs/                saídas rastreáveis de cada execução
artifacts/           figuras e tabelas geradas para a monografia
tests/               suíte pytest (~150 testes)
tex/                 manuscrito LaTeX (intocado pelo código)
```

## Documentação

A documentação técnica fica em ``docs/``. Os arquivos centrais são:

- ``docs/ARQUITETURA.md`` — visão técnica do pipeline e dos conceitos de
  perfil, modo, fonte, protocolo, run e latest.
- ``docs/DEBUGGING.md`` — onde olhar logs, como inspecionar manifests e
  como rastrear uma imagem específica através das fases.
- ``docs/REPRODUCAO_MONOGRAFIA.md`` — sequência exata de comandos para
  gerar cada artefato citado na monografia.
- ``docs/DATASETS.md`` — datasets suportados, como obter e como adicionar
  um novo.
- ``docs/governanca/MIGRACAO_v22_para_v23.md`` — registro de todas as
  mudanças entre versões.

## Comandos principais

```bash
felinet --help
felinet easyrun                                    # wizard interativo
felinet datasets {linkar,listar}                   # gestão de datasets locais
felinet pipeline executar --fonte X --max-amostras N [--dev]
felinet reid {avaliar-closed,avaliar-openset}
felinet tabelas {comparativo-fontes,fontes-resumo,...}
felinet figuras {comparativo-fontes,reid-cmc,...}
felinet dev demo                                   # demo curta com galeria
```

## Hardware testado

NVIDIA MX250 com 2 GB de VRAM, CUDA 12.1. Modos sem GPU funcionam para a
geração de tabelas, figuras e a configuração de datasets; as fases de
detecção, classificação e Re-ID dependem dos pesos de
MegaDetector v6 (PytorchWildlife), SpeciesNet e MegaDescriptor.

## Licença

MIT.
