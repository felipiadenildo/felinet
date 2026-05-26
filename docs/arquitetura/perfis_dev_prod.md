# Perfis `dev` e `prod`

O `felinet` separa **dois modos de operacao** via perfis, definidos em
`configs/paths.yaml` e selecionados pelo flag `--perfil` (ou pela variavel
`FELINET_PERFIL`).

## Perfil `dev`

- **Proposito**: smoke test, demonstracao para a banca, CI.
- **Tempo de execucao**: < 1 minuto, sem GPU.
- **Tamanho em disco**: ~20 MB (cabe no repositorio).
- **Brutas**: 5 imagens-placeholder em `data/dev/pipeline/01_brutas/`.
  Cada imagem foi escolhida para exercitar um caminho diferente da cascata
  (uma por rejeicao + uma aprovada). Ver
  [`fluxo_cascata.md`](fluxo_cascata.md).
- **PetFace mini**: subset de 5 IDs x 3 imagens em `data/dev/petface_mini/`.
- **Saidas**: todas em `data/dev/pipeline/0[2-8]_*` (versionadas no repo).

## Perfil `prod`

- **Proposito**: execucao oficial -- gera os numeros que vao para a
  monografia.
- **Datasets**: lidos via symlinks em `data/raw/{lila_bc,petface,campus2}`
  apontando para o SSD externo. Ver
  [`runbooks/conectar_ssd_symlinks.md`](../runbooks/conectar_ssd_symlinks.md).
- **Saidas intermediarias**: `data/interim/` (no `.gitignore`).
- **Saidas finais**: `data/processed/` (versionadas; arquivos JSON pequenos).

## Modos de execucao

Independentemente do perfil, o pipeline pode rodar em dois modos distintos:

### Modo operacional (cascata)
```
felinet pipeline executar --perfil dev
```
Encadeia I -> II -> III -> IV sobre `raw_camera_trap`. Em `dev`, demonstra
visualmente os caminhos de rejeicao; em `prod`, processaria o feed real
de Campus 2.

### Modo metodologico (Fase IV isolada sobre PetFace)
```
felinet reid extrair-embeddings --perfil prod --n 500
felinet reid avaliar-closed     --perfil prod --n 500
felinet reid avaliar-openset    --perfil prod --n 500
```
Avalia apenas a Fase IV de forma isolada, usando o PetFace cat como
benchmark com ground-truth. **Estes sao os numeros reportados nas tabelas
da monografia.**

## Por que dois modos?

A monografia exige duas garantias:

1. **Que o pipeline integrado funciona** (modo operacional).
2. **Que o componente mais critico -- Re-ID -- tem desempenho mensuravel
   contra um benchmark publico** (modo metodologico).

Esses dois objetivos requerem datasets diferentes: a cascata operacional
precisa de imagens de armadilha (sem ID rotulado), enquanto a avaliacao
Re-ID precisa de imagens com identidade ground-truth. Por isso o sistema
mantem duas entradas paralelas (`raw_camera_trap` e `raw_petface`).
