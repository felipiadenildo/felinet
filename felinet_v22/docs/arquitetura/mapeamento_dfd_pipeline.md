# Mapeamento DFD -> codigo

A monografia apresenta, no Capitulo 3, um **Diagrama de Fluxo de Dados (DFD)**
do pipeline. Esta tabela aponta, para cada processo do DFD, o modulo Python
que o implementa e o artefato que ele grava em disco.

| ID    | Processo do DFD                  | Modulo `felinet.*`                                    | Artefato gerado                            | Implementado? |
|-------|----------------------------------|-------------------------------------------------------|--------------------------------------------|---------------|
| P1    | Aquisicao de midias              | --- (externo: armadilha + cartao SD)                  | `data/raw/campus2/`                        | Externo       |
| P2    | Ingestao + extracao EXIF         | `pipeline.fase1_ingestao.manifesto`                   | `02_manifesto/manifesto.csv`               | Sim           |
| P3    | Deteccao de animal               | `pipeline.fase2_deteccao.megadetector`                | `03_deteccoes/deteccoes.json`              | Sim           |
| P4    | Classificacao de especie         | `pipeline.fase3_classificacao.speciesnet`             | (intermediario, dentro do decisor)         | Sim           |
| P4.1  | Decisor (politica de aceitacao)  | `pipeline.fase3_classificacao.decisor`                | `04_classificacoes/classificacoes.json`    | Sim           |
| P4.2  | Recorte de crops aprovados       | `pipeline.fase3_classificacao.crops`                  | `05_crops_felis_catus/*.png`               | Sim           |
| P5    | Anotacao humana de identidade    | --- (interface humana)                                | `06_anotacao_identidade.json`              | **Nao**       |
| P6    | Embedding (MegaDescriptor)       | `pipeline.fase4_reid.megadescriptor`                  | `07_embeddings.npz`                        | Sim           |
| P7    | Matching / avaliacao Re-ID       | `pipeline.fase4_reid.avaliacao`                       | `08_avaliacao_pipeline.json`               | Sim           |
| P8    | **Anonimizacao (blur de pessoa)**| ---                                                   | ---                                        | **Nao**       |
| P9    | Persistencia em SGBD             | `persistencia/` (esqueleto)                           | (banco)                                    | Esqueleto     |

## Processos NAO implementados

- **P5 (Interface de anotacao humana)**: o pipeline aceita um JSON
  pre-preenchido em `06_anotacao_identidade.json` como simulacao. A
  interface real (web ou nativa) esta fora do escopo do TCC -- ver
  [`docs/escopo/nao_implementado.md`](../escopo/nao_implementado.md).

- **P8 (Blur de pessoa)**: a monografia preve P8 como medida de privacidade
  para imagens onde pessoas aparecem em segundo plano. **Nao foi
  implementado neste TCC.** Justificativa: a base LILA-BC eh ja anonimizada
  pelas instituicoes provedoras (sem rostos identificaveis), e a coleta de
  Campus 2 ainda nao gerou imagens com pessoas. P8 sera implementado em
  trabalhos futuros usando MegaDetector para detectar `category == "person"`
  e aplicar blur Gaussiano sobre cada bbox.

- **P9 (SGBD)**: o esqueleto `persistencia/` ja contem o schema SQLAlchemy
  alinhado com Camtrap-DP, mas a integracao continua entre cascata e banco
  esta postergada.

## Como ler este mapeamento ao acompanhar o codigo

1. Abra `Capitulo 3 -- Arquitetura` da monografia e localize o DFD.
2. Para cada processo Px, ache a linha correspondente acima.
3. O modulo Python listado contem a implementacao -- a docstring no topo
   de cada modulo reproduz o ID `Px` do DFD para facilitar rastreabilidade.
4. Para reproduzir o artefato, use `felinet pipeline executar --perfil dev`
   ou um dos comandos individuais por fase.
