# 04 — Dados

Pasta gerenciada por **DVC** (não commitar conteúdo no Git, apenas os `.dvc`).

## Estrutura (padrão Cookiecutter Data Science)

| Pasta | Conteúdo | Versionamento |
|---|---|---|
| `raw/` | Dados originais imutáveis. Nunca modificar. | DVC |
| `interim/` | Transformações intermediárias (output de E0/E1). | DVC |
| `processed/` | Pronto para modelagem e relatório (output de E2.6/E3). | DVC |
| `external/` | Datasets de terceiros (PetFace, CatFLW, WildlifeReID-10k, MegaDetector pesos). | DVC |
| `schemas/` | Camtrap-DP, JSON Schemas, DDL SQLite (versionados no Git). | Git |

## Setup DVC

```bash
# A partir da raiz do projeto:
dvc init
dvc remote add -d storage <url-do-remote>   # ex.: Google Drive USP, S3, MinIO
```

## Política

- Nenhum binário > 100 MB no Git. Tudo grande passa por DVC.
- Datasets de terceiros têm `external/<nome>/SOURCE.md` documentando origem, licença e versão.
- `raw/` é imutável: jamais sobrescrever; criar novo subdiretório se precisar refazer.
