# `01_brutas/` — Entrada da cascata dev

Esta pasta contem **5 imagens-placeholder** que representam os cinco caminhos
possiveis pela cascata I -> II -> III -> IV do pipeline operacional. Cada
imagem foi escolhida para exercitar um caminho diferente, incluindo as quatro
rejeicoes possiveis:

| Imagem                                  | Caminho esperado | Fase de rejeicao | Pasta de destino                                       |
|-----------------------------------------|------------------|------------------|--------------------------------------------------------|
| `01_lila_sem_exif.jpg`                  | rejeitada        | I (Ingestao)     | `02_manifesto/rejeitadas_sem_exif/`                    |
| `02_lila_paisagem_vazia.jpg`            | rejeitada        | II (Deteccao)    | `03_deteccoes/rejeitadas_sem_deteccao/`                |
| `03_lila_capivara.jpg`                  | rejeitada        | III (Decisor)    | `04_classificacoes/rejeitadas_nao_felis_catus/`        |
| `04_lila_borrada_baixa_confianca.jpg`   | rejeitada        | III (Decisor)    | `04_classificacoes/rejeitadas_baixa_confianca/`        |
| `05_lila_gato_aprovado.jpg`             | aprovada         | --               | avanca para IV; crop em `05_crops_felis_catus/`        |

## Como substituir por imagens reais do LILA-BC

Os arquivos atuais sao **placeholders sinteticos** com EXIF minimo. Para uma
demonstracao mais realista (recomendado para a banca), troque cada imagem por
uma amostra real do LILA-BC mantendo os nomes:

```bash
# Exemplo: ENA24 contem caes/gatos/capivaras reais
# https://lila.science/datasets/ena24detection
wget -O 03_lila_capivara.jpg "<url-de-uma-capivara-ENA24>"
wget -O 05_lila_gato_aprovado.jpg "<url-de-um-gato-ENA24>"
```

Subconjuntos sugeridos do LILA-BC:
- **ENA24**: fauna leste-EUA; tem gatos e capivaras em armadilhas.
- **Caltech Camera Traps**: 243k imagens; mamiferos californianos.
- **Snapshot Serengeti**: cenas com vegetacao densa (testa Fase II vazia).
- **Idaho Camera Traps**: noturno; uteis para borradas (Fase III).

Apos substituir, rode `felinet pipeline executar --perfil dev` e os
descartes devem aparecer nas pastas `rejeitadas_*/` correspondentes.

## Justificativa pedagogica

A escolha de **exatamente 5 imagens** -- uma por caminho -- segue o principio
da **cobertura por caminho** de testes E2E: o conjunto minimo que executa
todos os branches do orquestrador. Veja `docs/arquitetura/fluxo_cascata.md`
para o diagrama completo.
