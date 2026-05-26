# Justificativa de uso de datasets

A monografia menciona um grande numero de datasets candidatos durante a
revisao bibliografica (Capitulos 1 e 2). Esta nota explicita **quais
foram efetivamente usados** na validacao do pipeline e **por que os
demais foram descartados**.

## Resumo executivo

| Categoria               | Datasets usados              | Datasets descartados                                              |
|-------------------------|------------------------------|-------------------------------------------------------------------|
| Camera-trap (Fases II/III) | **LILA-BC** (subset ENA24)     | iNaturalist 2021; NACTI; Wildlife Insights; Snapshot Serengeti completo |
| Re-ID felinos (Fase IV)    | **PetFace** (categoria `cat`)  | Cat Dataset (Zhang); Animal-Pose; OpenCats                          |
| Operacional Campus 2       | **proprio** (em coleta)        | --                                                                  |

A tabela completa, com codigo de motivo, esta em
`artifacts/tabelas/datasets_avaliados.csv` (consumida pelo Capitulo 4).

## Datasets usados

### LILA-BC (subset ENA24)
- **Uso**: validacao das Fases II (deteccao) e III (classificacao).
- **Por que**: contem armadilhas reais com **gatos domesticos e fauna
  nao-alvo** (capivaras, guaxinins, raposas) -- exercita o decisor.
- **Versao**: ENA24, ~8000 imagens, 22 especies. Acesso publico via
  https://lila.science/datasets/ena24detection.
- **Subset efetivo**: ate 200 imagens em `dev` (placeholder) +
  ate o conjunto completo em `prod`.

### PetFace (subset `cat`)
- **Uso**: avaliacao METODOLOGICA da Fase IV.
- **Por que**: **unico dataset publico de gatos com ID rotulado** em
  multiplas vistas; permite calcular Top-K, CMC e AUC formais.
- **Versao**: PetFace v1.0, categoria `cat`, com particao
  train/query/gallery oficial.
- **Subset**: variamos N entre 50, 200 e 500 IDs para estudar
  comportamento com escala.

## Datasets descartados (com motivo)

### iNaturalist 2021
- **Tamanho**: 2.7 M imagens, 10k+ especies.
- **Motivo do descarte**: foco em biodiversidade ampla (insetos, plantas,
  aves); a fracao com *Felis catus* eh minima e nao representa armadilha
  fotografica. **Excessivo para o orcamento computacional do TCC.**

### NACTI (North American Camera Trap Images)
- **Tamanho**: ~3.7 M imagens.
- **Motivo do descarte**: fauna **norte-americana**, com baixa sobreposicao
  com Campus 2 (Brasil). Ja eh **parcialmente coberto pelo treino do
  MegaDetector**.

### Wildlife Insights
- **Acesso**: API restrita; download manual via colaboracao institucional.
- **Motivo do descarte**: o **SpeciesNet (Google) deriva justamente dele**;
  usar como benchmark seria circular.

### Cat Dataset (Zhang et al.)
- **Tamanho**: 9000 imagens; 9 pontos-chave por gato.
- **Motivo do descarte**: imagens **posadas** (gatos em ambiente
  controlado, frontais). Nao reflete a distribuicao visual de armadilha
  fotografica.

### Animal-Pose / OpenCats
- **Foco**: landmarks (pose estimation), nao identidade.
- **Motivo**: fora do escopo da Fase IV (Re-ID por embedding).

### Snapshot Serengeti completo
- **Tamanho**: ~7 M imagens.
- **Motivo do descarte**: fauna africana; usado apenas como referencia
  metodologica (artigos do consorcio). O subset ENA24 ja cobre o
  caso-de-uso.

## Tabela `datasets_avaliados.csv`

A tabela CSV em `artifacts/tabelas/datasets_avaliados.csv` traz todos os
datasets desta nota mais o veredito (USADO / DESCARTADO) e o codigo de
motivo. Eh consumida diretamente pelo Capitulo 4 da monografia via
`\input{...datasets_avaliados.tex}` (gerada por
`felinet tabelas datasets-avaliados`).
