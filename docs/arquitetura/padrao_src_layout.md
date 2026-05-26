# Padrao `src/` layout

## Por que `src/felinet/` em vez de `felinet/` na raiz?

O *src layout* eh a recomendacao oficial da PyPA (Python Packaging Authority)
para projetos publicaveis. Suas vantagens principais sao:

1. **Forca o uso do pacote instalado.** Se o codigo de teste consegue importar
   `felinet` apenas porque o cwd eh a raiz do repo (sem `pip install -e .`),
   bugs de empacotamento ficam mascarados. O `src/` separa **codigo-fonte**
   de **pacote instalavel** e elimina essa armadilha.
2. **Imports relativos limpos.** Dentro de `src/felinet/`, todos os imports
   sao `from felinet.X import Y` -- nunca `sys.path.insert(...)` ou
   `from .X import Y` ad-hoc.
3. **Compatibilidade com `pip`, `uv`, `hatch`, `setuptools`.** Todas as
   ferramentas modernas tratam `src/<pacote>` como o padrao default.

## Mapeamento implementado

```
src/felinet/
├── __init__.py          # versao do pacote
├── __main__.py          # python -m felinet
├── cli.py               # typer app (entry point: 'felinet')
├── config.py            # carregar_perfil() le configs/paths.yaml
├── logging_setup.py     # configurar_logging()
├── comandos/            # subcomandos do CLI (1 por dominio)
│   ├── ingestao.py
│   ├── deteccao.py
│   ├── classificacao.py
│   ├── reid.py
│   ├── pipeline.py      # orquestrador (cascata)
│   ├── figuras.py
│   ├── tabelas.py
│   └── dev.py
├── pipeline/            # logica de negocio (uma pasta por fase)
│   ├── fase1_ingestao/
│   ├── fase2_deteccao/
│   ├── fase3_classificacao/
│   ├── fase4_reid/
│   └── orquestrador.py  # encadeia I -> II -> III -> IV
├── datasets/            # adapters de dataset (PetFace, LILA-BC)
├── persistencia/        # esqueleto de SGBD (P9 do DFD)
└── utils/
    ├── io.py, hash.py, tex.py
```

## Como rodar codigo do repo

Apos `uv pip install -e ".[dev]"`, o entry point `felinet` fica
disponivel no PATH. Equivalencias:

```bash
# Forma 1 (recomendada): script instalado
felinet pipeline executar --perfil dev

# Forma 2: modulo via python
python -m felinet pipeline executar --perfil dev

# Forma 3 (para debug): direto do src/
python src/felinet/cli.py pipeline executar --perfil dev
```

## Renomeacao `tcc_gatos` -> `felinet`

Versoes anteriores deste projeto usavam o nome `tcc_gatos`. A justificativa
da renomeacao esta em [`decisao_renomeacao_felinet.md`](decisao_renomeacao_felinet.md).
