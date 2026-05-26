# Layout de runs/

## Motivacao

O sistema felinet possui duas dimensoes ortogonais que multiplicam as
combinacoes possiveis de execucao:

- **Modos**: operacional (cascata I a IV sobre camera-trap) e metodologico
  (Re-ID isolado sobre dataset com identidade rotulada).
- **Fontes**: para cada modo, multiplas fontes de dados podem ser usadas
  (Campus 2, LILA-BC ENA24, Kaggle cat-dataset no operacional; PetFace,
  futuros datasets no metodologico).

Acrescentando perfil (dev/prod), protocolo metodologico (N=50/200/500,
closed/openset) e versao de codigo (git sha), o numero de combinacoes
cresce rapidamente. Sem um esquema padronizado, e impossivel rastrear
qual conjunto de parametros gerou cada tabela da monografia.

## Decisao

Adota-se um esquema hibrido inspirado em duas referencias maduras:

- **Caminho determinado pelos parametros** (estilo Snakemake): dadas as
  cinco dimensoes (modo, fonte, perfil, protocolo, gitsha), o diretorio
  de saida e calculado, nao escolhido pelo usuario. Isso elimina a
  necessidade de inventar nomes ("teste_3", "final_v2") e garante que
  re-executar a mesma combinacao sobrescreve o mesmo diretorio.
- **Manifesto JSON por execucao** (estilo MLflow): cada diretorio recebe
  um `manifest.json` com a tupla rastreavel completa (git branch e dirty
  status, ambiente Python, GPU disponivel, hora de inicio e fim,
  parametros do comando, metricas resumo). E o registro que conecta um
  resultado citado na monografia ao codigo exato que o gerou.

## Esquema

```
runs/<modo>/<fonte>/<perfil>/<protocolo|_>/<gitsha>[__<tag>]/
```

- **modo**: `operacional` | `metodologico`
- **fonte**: slug registrado em `configs/paths.yaml` -> `fontes:` (ex.:
  `campus2_2025`, `lila_ena24`, `kaggle_cats`, `petface`).
- **perfil**: `dev` | `prod`
- **protocolo**: aplicavel apenas no modo metodologico
  (`n0050`, `n0200`, `n0500`, `openset_n0050`, ...). No modo operacional
  o lugar e preenchido pelo placeholder `_`.
- **gitsha**: primeiros 7 caracteres do HEAD ou `nogit`.
- **tag**: sufixo opcional (`--tag thr020`, `--tag sem_blur`) para
  distinguir runs com mesmo gitsha que variam apenas em parametros.

### Exemplos concretos

```
runs/operacional/kaggle_cats/dev/_/fa45751/
runs/operacional/campus2_2025/prod/_/a3f9c2e__thr025/
runs/metodologico/petface/prod/n0200/fa45751/
runs/metodologico/petface/prod/openset_n0200/fa45751/
runs/metodologico/petface_mini/dev/n0010/nogit/
```

### Symlinks latest/

Para navegacao humana, mantem-se um symlink por combinacao
`(modo, fonte, perfil[, protocolo])` em `runs/latest/`:

```
runs/latest/operacional__kaggle_cats__dev          -> ../operacional/kaggle_cats/dev/_/fa45751
runs/latest/metodologico__petface__prod__n0200     -> ../metodologico/petface/prod/n0200/fa45751
runs/latest/metodologico__petface__prod__openset_n0200 -> ...
```

Esses symlinks sao atualizados automaticamente por `felinet.runs.criar_run`
e consumidos pelos comandos `felinet figuras` e `felinet tabelas`.

## Estrutura interna de um run

### Operacional (modo cascata)

```
<run>/
├── manifest.json
├── 02_manifesto/manifesto.csv
├── 03_deteccoes/deteccoes.json
├── 04_classificacoes/classificacoes.json
├── 05_crops_felis_catus/*.png
├── 06_anotacao_identidade.json     # opcional (dev) ou produzido por humano (prod)
├── 07_embeddings.npz
├── 08_avaliacao_pipeline.json
└── logs/
```

### Metodologico (Re-ID isolado)

```
<run>/
├── manifest.json
├── splits.json                     # quantidade de queries/galeria
├── embeddings.npz                  # ou 07_embeddings.npz (mesmo conteudo)
├── matriz_similaridade.npz         # opcional
├── metricas.json                   # Top-K, CMC, AUC, TAR@FAR
└── logs/
```

## manifest.json

Cada run grava um manifesto com a tupla rastreavel:

```json
{
  "run_id": "a1b2c3",
  "modo": "metodologico",
  "fonte": "petface",
  "perfil": "prod",
  "protocolo": "n0200",
  "tag": null,
  "git_sha": "fa45751",
  "git_branch": "refactor/felinet-src-layout",
  "git_dirty": false,
  "data_inicio": "2026-05-26T02:42:13-03:00",
  "data_fim": "2026-05-26T02:48:01-03:00",
  "duracao_s": 348,
  "sucesso": true,
  "fonte_path_real": "/home/felipi/datasets/petface",
  "configs": {
    "paths": "configs/paths.yaml",
    "modelos": "configs/modelos.yaml",
    "pipeline": "configs/pipeline.yaml"
  },
  "ambiente": {
    "python": "3.12.3",
    "torch": "2.5.1+cu121",
    "cuda": true,
    "gpu": "NVIDIA GeForce MX250",
    "hostname": "felipi-pc",
    "platform": "Linux-..."
  },
  "extras": {
    "comando": "reid extrair-embeddings",
    "n": 200
  },
  "metricas_resumo": {
    "n_embeddings": 1200,
    "n_query": 600,
    "n_galeria": 600
  }
}
```

## Versionamento

- `runs/` e gitignored: pixels e embeddings nao entram no repositorio.
- Apenas o `manifest.json` e citavel; quando um resultado precisa ser
  preservado para a monografia, a tabela ou figura derivada e gravada
  em `artifacts/tabelas/...` ou `artifacts/figuras/...` (versionados).
- O `manifest.json` carrega o git_sha que permite reconstruir o codigo
  exato. Se o usuario quiser preservar o run completo, deve copia-lo
  manualmente para fora do `runs/` (ex.: para um SSD de arquivo morto).

## Como a monografia consome runs/

O fluxo de geracao de tabelas e figuras nunca cita `runs/` diretamente
no texto. O fluxo e:

1. `felinet reid extrair-embeddings --fonte petface --n 200`
   cria `runs/metodologico/petface/prod/n0200/<sha>/`.
2. `felinet reid avaliar-closed --fonte petface --n 200` consome o run
   anterior e grava `metricas.json` no mesmo (ou novo) run.
3. `felinet tabelas reid-resumo --fonte petface --ns 50,200,500` le os
   tres runs latest e escreve
   `artifacts/tabelas/metodologico/petface/reid_resumo.{csv,tex}`.
4. O `.tex` da monografia faz
   `\input{artifacts/tabelas/metodologico/petface/reid_resumo.tex}`.

A versionalizacao do `.tex` em `artifacts/` documenta o estado dos
numeros; o `manifest.json` linkado por gitsha permite reproduzir.

## Adicionando uma nova fonte

1. Criar symlink ou copia em `data/raw/<categoria>/<slug>/`.
2. Registrar em `configs/paths.yaml` -> `fontes:` com o mesmo slug.
3. Opcional: definir como `fonte_default_<modo>` em um perfil.
4. Rodar `felinet pipeline executar --fonte <slug>` ou
   `felinet reid extrair-embeddings --fonte <slug>`.

## Adicionando um novo protocolo metodologico

Cada protocolo e identificado por slug `<familia>_n<NNNN>` ou apenas
`n<NNNN>`. Para criar um protocolo novo, basta passar `--tag` para
diferenciar variacoes (ex.: `--tag triplet_loss`) ou estender o codigo
do comando para mapear novas combinacoes a slugs proprios.
