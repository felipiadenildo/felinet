# `tests/` -- testes do `felinet`

Suite pytest. Por padrao, **testes que dependem de GPU/modelos pesados
estao marcados com `@pytest.mark.smoke`** e sao pulados.

## Rodar

```bash
pytest                       # rapido, sem GPU
pytest -m "smoke"            # apenas testes de GPU
pytest -m "smoke or not smoke"  # tudo
```

## Estrutura

- `conftest.py` -- fixtures compartilhadas (imagens sinteticas, EXIF).
- `test_e0_*.py` -- Fase I (ingestao, EXIF, manifesto, camtrap).
- `test_e1_*.py` -- Fase II (MegaDetector smoke, schema, visualizacao).
- `test_fase3_*.py` -- Fase III (decisor, schema).
- `test_fase4_*.py` -- Fase IV (avaliacao closed-set, open-set, schema).
- `test_datasets_lila.py` -- adapter LILA-BC.
- `test_pipeline_orquestrador.py` -- smoke do orquestrador (cascata).

## Cobertura

77 testes verdes no commit `fa45751` (mai/2026). Para gerar relatorio
de cobertura:

```bash
pytest --cov=felinet --cov-report=html
```
