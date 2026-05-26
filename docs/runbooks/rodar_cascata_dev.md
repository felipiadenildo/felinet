# Runbook: cascata dev em < 1 minuto

Execucao end-to-end com as 5 imagens-placeholder, **sem GPU**.

## Pre-requisitos

- `uv pip install -e ".[dev]"` (instala o pacote em modo editavel).
- Modelos baixados em `modelos/` (ver `docs/runbooks/baixar_modelos.md`).

## Rodar

```bash
felinet pipeline executar --perfil dev
```

Saida esperada (JSON):

```json
{
  "n_brutas": 5,
  "n_manifesto": 4,
  "n_deteccoes_animal": 2,
  "n_classificacoes_felis_catus": 1,
  "n_crops_gerados": 1,
  "n_embeddings": 1,
  "sucesso": true
}
```

> Os numeros exatos podem variar conforme as **imagens placeholder** atuais
> (que sao retangulos coloridos sem conteudo real). Para uma demonstracao
> mais realista, substitua os arquivos em `01_brutas/` por imagens
> reais do LILA-BC -- veja o README dessa pasta.

## Inspecionar artefatos

```bash
felinet pipeline resumir --perfil dev
```

Mostra quais arquivos existem em cada estagio da cascata.

## Limpar e refazer

```bash
felinet dev limpar-saidas-dev --confirmar
felinet pipeline executar --perfil dev
```
