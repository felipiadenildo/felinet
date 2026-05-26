# `data/` -- dados

Organizacao segundo o padrao **Cookiecutter Data Science**:

| Pasta       | Versionado? | Conteudo                                                 |
|-------------|-------------|----------------------------------------------------------|
| `dev/`      | Sim         | Subset minimo (5 imgs cascata + 5 IDs PetFace mini)      |
| `raw/`      | **Nao**     | Symlinks para datasets externos (LILA-BC, PetFace, Campus 2) |
| `interim/`  | **Nao**     | Embeddings cacheados, JSONs intermediarios da execucao prod |
| `processed/`| Sim         | JSONs finais (avaliacao_reid_*, avaliacao_openset_*)     |
| `external/` | **Nao**     | Datasets de terceiros nao processados (raros)            |
| `schemas/`  | Sim         | JSON Schema dos artefatos                                |

## Princıpios

- **`dev/` cabe no repo**: < 20 MB. Permite rodar smoke test sem SSD.
- **`raw/` eh symlink**: nunca copiamos datasets pesados para o repo.
  Ver `docs/runbooks/conectar_ssd_symlinks.md`.
- **`processed/` eh versionado**: contem JSONs pequenos com os numeros
  reportados na monografia (reproducibilidade).
