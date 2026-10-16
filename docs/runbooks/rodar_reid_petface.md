# Runbook: avaliacao Re-ID sobre PetFace (modo metodologico)

Esta eh a execucao que **gera os numeros reportados na monografia**
(Capitulo 4 e 5). Roda sobre o subset `cat` do PetFace; **requer GPU**
para tempo razoavel.

## Pre-requisitos

- PetFace em `data/raw/petface/` (via symlink -- ver
  `conectar_ssd_symlinks.md`).
- MegaDescriptor T-224 baixado em `modelos/megadescriptor/`.
- GPU com >=2 GB VRAM (testado em NVIDIA MX250).

## Execucao completa (N = 50, 200, 500)

```bash
# 1) Extrai embeddings cacheados (uma vez por N)
felinet reid extrair-embeddings --perfil prod --n 50
felinet reid extrair-embeddings --perfil prod --n 200
felinet reid extrair-embeddings --perfil prod --n 500

# 2) Avalia closed-set (Top-K + CMC)
felinet reid avaliar-closed --perfil prod --n 50
felinet reid avaliar-closed --perfil prod --n 200
felinet reid avaliar-closed --perfil prod --n 500

# 3) Avalia open-set (AUC + thresholds) com 3 seeds
felinet reid avaliar-openset --perfil prod --n 50
felinet reid avaliar-openset --perfil prod --n 200
felinet reid avaliar-openset --perfil prod --n 500
```

Equivalente via Makefile:

```bash
make reid-todos
```

## Resultados de referencia (commit `fa45751`, mai/2026)

| N    | Top-1 (closed) | AUC media +/- std (open-set, 3 seeds) |
|------|----------------|---------------------------------------|
| 50   | 0.720          | 0.694 +/- 0.021                       |
| 200  | 0.590          | 0.611 +/- (variavel)                  |
| 500  | 0.516          | 0.607                                 |

Numeros publicados em `data/processed/avaliacao_reid_petface_n*_latest.json`
e `data/processed/avaliacao_openset_petface_n*_latest.json`.

## Gerar figuras e tabelas da monografia

```bash
felinet monografia gerar     # tabelas closed/open-set, CMC, ROC e as figuras do Apêndice E
```

Os arquivos vão para `monografia-felinet/elementos/gerados/` (ver `docs/REPRODUCAO_MONOGRAFIA.md`).
