# Fluxo da cascata operacional (dev)

A cascata processa 5 imagens em `01_brutas/` e -- por construcao --
**cada imagem sai por um caminho diferente**, exercitando todas as
ramificacoes do orquestrador.

## Diagrama (textual)

```
                              ┌──── 01_lila_sem_exif.jpg
                              │     [REJEITADA Fase I]
                              │     -> 02_manifesto/rejeitadas_sem_exif/
                              │
data/dev/pipeline/01_brutas/  ┼──── 02_lila_paisagem_vazia.jpg
        (5 imagens)           │     [aprovada Fase I, REJEITADA Fase II]
                              │     -> 03_deteccoes/rejeitadas_sem_deteccao/
                              │
                              ┼──── 03_lila_capivara.jpg
                              │     [aprovada I, II; REJEITADA Fase III -> outra_especie]
                              │     -> 04_classificacoes/rejeitadas_nao_felis_catus/
                              │
                              ┼──── 04_lila_borrada_baixa_confianca.jpg
                              │     [aprovada I, II; REJEITADA Fase III -> validacao_humana]
                              │     -> 04_classificacoes/rejeitadas_baixa_confianca/
                              │
                              └──── 05_lila_gato_aprovado.jpg
                                    [aprovada I, II, III -> avanca para Fase IV]
                                    -> 05_crops_felis_catus/IMG_0005#bbox0.png
                                    -> 07_embeddings.npz
                                    -> 08_avaliacao_pipeline.json
```

## Numeracao das pastas

A ordenacao numerica das subpastas em `data/dev/pipeline/` reflete a ordem
temporal de geracao dos artefatos:

| Numero | Pasta                                 | Gerado por                          |
|--------|---------------------------------------|-------------------------------------|
| 01     | `01_brutas/`                          | (humano: imagens placeholder)       |
| 02     | `02_manifesto/`                       | `felinet ingestao executar`         |
| 03     | `03_deteccoes/`                       | `felinet deteccao executar`         |
| 04     | `04_classificacoes/`                  | `felinet classificacao executar`    |
| 05     | `05_crops_felis_catus/`               | `felinet classificacao recortar`    |
| 06     | `06_anotacao_identidade.json`         | (humano: P5; pre-preenchido em dev) |
| 07     | `07_embeddings.npz`                   | (parte da cascata Fase IV)          |
| 08     | `08_avaliacao_pipeline.json`          | (parte da cascata Fase IV)          |

## Pastas de rejeicao (vazias por default)

Para fins de **demonstracao visual**, o ZIP inicial cria as pastas de
rejeicao vazias. Ao rodar `felinet pipeline executar --perfil dev`, elas
recebem arquivos-marcador (`.motivo.txt`) indicando por que cada imagem
foi descartada naquela fase. As imagens originais nao sao duplicadas --
o marcador contem apenas o caminho original e o motivo.

## Comando unico para rodar tudo

```bash
felinet pipeline executar --perfil dev
```

Equivalente a executar manualmente, em sequencia:

```bash
felinet ingestao executar       --perfil dev
felinet deteccao executar       --perfil dev
felinet classificacao executar  --perfil dev
felinet classificacao recortar  --perfil dev
```

mais a extracao de embeddings (P6) e avaliacao Re-ID (P7) sobre os crops
aprovados.
