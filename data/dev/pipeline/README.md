# `data/dev/pipeline/` -- cascata dev

Estrutura numerada que reflete a ordem temporal de geracao dos
artefatos:

```
01_brutas/                         <- entrada (humano)
02_manifesto/                      <- Fase I
   rejeitadas_sem_exif/
   rejeitadas_corrompidas/
03_deteccoes/                      <- Fase II
   rejeitadas_sem_deteccao/
04_classificacoes/                 <- Fase III
   rejeitadas_nao_felis_catus/
   rejeitadas_baixa_confianca/
05_crops_felis_catus/              <- bridge III -> IV
06_anotacao_identidade.json        <- humano (simulado em dev)
07_embeddings.npz                  <- Fase IV
08_avaliacao_pipeline.json         <- Fase IV (avaliacao)
```

Ver `docs/arquitetura/fluxo_cascata.md` para o mapeamento de cada
imagem com seu caminho na cascata.
