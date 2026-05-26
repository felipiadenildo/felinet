# felinet

Sistema de monitoramento por visao computacional da colonia de gatos do
Campus 2 da USP Sao Carlos. Pipeline em cascata de quatro fases:
ingestao, deteccao (MegaDetector), classificacao (SpeciesNet) e
re-identificacao (MegaDescriptor).

Codigo do TCC de Felipi Adenildo Soares Sousa, Engenharia de Computacao
ICMC/USP, defesa prevista para setembro de 2026.

## Modos de operacao

| Modo            | Comando                                            | Quando usar                         |
|-----------------|----------------------------------------------------|-------------------------------------|
| **Operacional** | `felinet pipeline executar --perfil dev`           | Demonstrar cascata I -> II -> III -> IV |
| **Metodologico**| `felinet reid avaliar-closed --perfil prod --n 200`| Gerar metricas para a monografia    |

## Setup rapido (dev)

```bash
uv pip install -e ".[dev]"           # instala pacote + ferramentas
make validar                         # sanity-check do ambiente
make pipeline-dev                    # cascata sobre 5 imagens placeholder
```

## Estrutura

```
felinet/
├── src/felinet/         # pacote Python (CLI + modulos por fase)
├── configs/             # paths.yaml, modelos.yaml, pipeline.yaml
├── data/
│   ├── dev/             # subset minimo versionado (cascata + petface_mini)
│   ├── raw/             # symlinks para datasets externos (gitignored)
│   ├── interim/         # intermediarios prod (gitignored)
│   ├── processed/       # JSONs finais (versionados)
│   └── schemas/         # JSON Schema dos artefatos
├── artifacts/           # figuras + tabelas gerados (vao para o LaTeX)
├── modelos/             # pesos pre-treinados (gitignored)
├── tex/                 # fontes LaTeX da monografia
├── docs/                # arquitetura, escopo, runbooks, governanca
├── anexos/              # autorizacoes, datasheets, protocolos
├── tests/               # pytest (sem GPU por default)
├── Makefile             # atalhos para tarefas comuns
└── pyproject.toml
```

## Documentacao

Comece por:

1. [`docs/arquitetura/padrao_src_layout.md`](docs/arquitetura/padrao_src_layout.md)
   -- visao geral do codigo.
2. [`docs/arquitetura/mapeamento_dfd_pipeline.md`](docs/arquitetura/mapeamento_dfd_pipeline.md)
   -- correspondencia DFD da monografia com modulos Python.
3. [`docs/arquitetura/fluxo_cascata.md`](docs/arquitetura/fluxo_cascata.md)
   -- como a cascata dev exercita todos os caminhos de rejeicao.
4. [`docs/escopo/nao_implementado.md`](docs/escopo/nao_implementado.md)
   -- o que esta fora do TCC (P5 humano, P8 blur, fine-tuning, etc.).
5. [`docs/datasets/justificativa_uso.md`](docs/datasets/justificativa_uso.md)
   -- por que apenas LILA-BC e PetFace foram usados.

## Comandos disponiveis

```
felinet ingestao executar         Fase I: manifesto + EXIF
felinet deteccao executar         Fase II: MegaDetector
felinet classificacao executar    Fase III: SpeciesNet + Decisor
felinet classificacao recortar    Fase III: crops felis_catus
felinet reid extrair-embeddings   Fase IV: embeddings PetFace
felinet reid avaliar-closed       Avaliacao closed-set (Top-K + CMC)
felinet reid avaliar-openset      Avaliacao open-set (AUC + thresholds)
felinet pipeline executar         Cascata I -> II -> III -> IV
felinet pipeline resumir          Status dos artefatos
felinet figuras reid-cmc          Curva CMC 300 DPI
felinet figuras matriz-similaridade  Heatmap query x galeria
felinet tabelas reid-resumo       Resumo closed-set CSV + .tex
felinet tabelas openset-resumo    Resumo open-set CSV + .tex
felinet tabelas datasets-avaliados   Tabela datasets do Capitulo 4
felinet dev preparar-petface-mini    Cria subset PetFace dev
felinet dev validar-ambiente         Diagnostico de ambiente
felinet dev limpar-saidas-dev        Reseta cascata dev
```

Cada subcomando aceita `--help`.

## Citacao

Se este codigo for util para outros trabalhos, cite a monografia
correspondente (referencia completa em `tex/main.tex`).

## Licenca

MIT.
