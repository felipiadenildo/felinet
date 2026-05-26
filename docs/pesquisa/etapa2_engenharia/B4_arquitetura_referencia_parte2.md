# B4 — Arquitetura de referência e camada física (Parte 2)

**Bloco:** B4 — Arquitetura de referência (continuação da Parte 1)
**Conteúdo desta parte:** B4.4 (schema de dados + ER Chen), B4.5 (DFD E0→E4), B4.6 (stack canônico de software), B4.7 (notas sobre alimentadores como local físico de montagem)
**Continuidade:** Parte 1 cobriu B4.1 (4 camadas C1-C4), B4.2 (5 diagramas físicos-tipo), B4.3 (dimensionamento PC). Parte 2 fecha o bloco de arquitetura. Próximo: B5 — validação empírica.

---

## B4.4 — Modelagem de dados e diagrama ER (Chen)

### B4.4.1 — Por que Camtrap-DP como base

A modelagem de dados deste sistema parte do **Camera Trap Data Package (Camtrap-DP) versão 1.0.1**, padrão TDWG (Biodiversity Information Standards) endossado por Agouti, eMammal, TRAPPER, Wildlife Insights e GBIF [(Bubnicki et al., 2024)](https://camtrap-dp.tdwg.org/). Esta escolha tem três justificativas operacionais:

1. **Interoperabilidade institucional** — Dados publicados em Camtrap-DP podem ser convertidos para Darwin Core e ingeridos pela infraestrutura GBIF, abrindo caminho para publicação dos achados da colônia em bases científicas reconhecidas, alinhado com o objetivo "g) avaliar viabilidade de modelos para detecção e reidentificação" e com a Sec. 3.1 do projeto base ("modelagem de banco de dados relacional para eventos de detecção, metadados temporais/espaciais e resultados de análise").
2. **Reaproveitamento de software** — Bibliotecas como `camtrapdp` (R) e `camtraptor` (R) leem o formato nativamente. Em Python, o pacote `frictionless` valida o schema via JSON. Não precisamos definir um esquema do zero.
3. **Extensibilidade controlada** — Camtrap-DP define um mecanismo formal de extensão: novos `Resources` podem ser declarados em `datapackage.json` sem perder conformidade com o padrão. É exatamente o que precisamos para acomodar Re-ID (crops, embeddings, match_history) e o multi-perfil de aquisição (Perfis A, B, D, E1, E2 de B3).

**Decisão de SGBD para esta revisão:** **SQLite 3** como motor primário, escolhido por três motivos: (a) o TCC opera offline e single-machine (PC do Felipi, ver B4.3); (b) o arquivo `.sqlite` é portável, versionável e diretamente reprodutível pela banca; (c) o ecossistema Python tem suporte nativo (`sqlite3`) sem dependências externas. **PostgreSQL+PostGIS permanece previsto como evolução** quando o sistema entrar em produção compartilhada (multi-usuário, indexação espacial avançada, processamento distribuído) — coerente com o projeto base [(PDF Sec. 7.4)](#) que menciona "Banco relacional PostgreSQL/MySQL para eventos de detecção".

### B4.4.2 — Núcleo Camtrap-DP (3 tabelas obrigatórias)

As três tabelas obrigatórias do padrão são preservadas integralmente. Listo abaixo só os campos relevantes ao projeto; o schema completo segue a especificação [(Camtrap-DP 1.0.1 / Data)](https://camtrap-dp.tdwg.org/data/).

**Tabela `deployments`** — Cada deployment é uma instalação de câmera num ponto P por um período. Para os 10 pontos, terei tipicamente 1 deployment por ponto (substituído quando a câmera é trocada, SD é trocado em E1, ou bateria expira em A/D).

| Campo Camtrap-DP | Tipo | Uso neste projeto |
|---|---|---|
| `deploymentID` * | string | UUID gerado no momento da instalação |
| `locationID` | string | `"P1".."P10"` (mapeamento de B3.6) |
| `locationName` | string | Ex.: "Comedouro principal AEX" |
| `latitude` *, `longitude` * | number | WGS84 (planejamento, sem instalar no TCC) |
| `deploymentStart` *, `deploymentEnd` * | datetime | ISO 8601 com timezone |
| `cameraID` | string | Serial number da câmera física |
| `cameraModel` | string | Ex.: `"TP-Link-Tapo C400"`, `"Generic-Anyka AK3918EV300L"` |
| `cameraHeight` | number | Altura da câmera (metros) — diretamente relevante ao bloco B4.7 |
| `cameraTilt`, `cameraHeading` | integer | Ângulo vertical e azimute |
| `detectionDistance` | number | Distância máxima de detecção confiável (metros) |
| `featureType` | string | Aqui usamos `"feeding station"` (vocabulário Camtrap) |

**Tabela `media`** — Cada arquivo de imagem (ou vídeo) gerado em campo. Volume estimado em B4.3 (≈140 GB/mês pós-filtragem E0). Campos:

| Campo | Tipo | Uso |
|---|---|---|
| `mediaID` * | string | UUID |
| `deploymentID` * | FK → deployments | |
| `captureMethod` | string | `"motionDetection"` (PIR ou VMD) ou `"timeLapse"` |
| `timestamp` * | datetime | Momento do disparo |
| `filePath` * | string | Caminho relativo no HD 4 TB |
| `fileMediatype` * | string | `"image/jpeg"` ou `"video/mp4"` |
| `exifData` | JSON | Metadados originais da câmera |

**Tabela `observations`** — Cada inferência da pipeline (E1, E2, E3 ou anotação humana) gera uma observação. É aqui que conecta-se a saída dos modelos:

| Campo | Tipo | Uso |
|---|---|---|
| `observationID` * | string | UUID |
| `deploymentID` * | FK → deployments | |
| `mediaID` | FK → media | Quando `observationLevel = "media"` |
| `eventID` | string | Sequência (rajada) — opcional |
| `observationLevel` * | string | `"media"` ou `"event"` |
| `observationType` * | string | `"animal"`, `"human"`, `"blank"`, `"unknown"`, `"vehicle"` |
| `scientificName` | string | `"Felis catus"` (saída do E2 SpeciesNet) |
| `count` | integer | Número de indivíduos no quadro |
| `individualID` | string | FK → individuals (extensão); resultado do E3 |
| `bboxX, bboxY, bboxWidth, bboxHeight` | number | Bounding box do E1 |
| `classificationMethod` | string | `"machine"`, `"human"`, `"machine+human"` |
| `classifiedBy` | string | Identificador do modelo, ex.: `"yolo11n-v1.2.0"` |
| `classificationProbability` | number | Confiança ∈ [0,1] |

### B4.4.3 — Extensões do projeto (Resources adicionais)

Para suportar Re-ID e multi-perfil de aquisição, declaro 4 tabelas adicionais via mecanismo de Resources do Camtrap-DP. Estas extensões são especificadas em `datapackage.json` mas tecnicamente vivem no mesmo arquivo SQLite.

**Tabela `individuals`** — Já é uma extensão prevista pelo Camtrap-DP [(Rowcliffe et al., 2024, Fig. 1)](https://ecoevorxiv.org/repository/object/5593/download/10949/) "as a separate table for animals that can be identified at the individual level using physical features".

| Campo | Tipo | Uso |
|---|---|---|
| `individualID` * | string PK | UUID do indivíduo (ex.: `"cat-0042"`) |
| `scientificName` * | string | `"Felis catus"` |
| `nickname` | string | Apelido AEX (ex.: `"Mingau"`, `"Listrado"`) |
| `lifeStage` | string | `"adult"`, `"juvenile"`, `"unknown"` |
| `sex` | string | `"male"`, `"female"`, `"unknown"` |
| `earTipped` | boolean | **Atributo de manejo crítico** — castração via CED |
| `earTipSide` | string | `"left"`, `"right"`, `"none"` |
| `markings` | string | Padrão de pelagem (texto livre) |
| `firstSeen`, `lastSeen` | datetime | Datas de primeira e última detecção |
| `status` | string | `"active"`, `"adopted"`, `"deceased"`, `"transferred"` |

**Tabela `crops`** — Recortes (bounding boxes) usados para Re-ID. Separar `media` de `crops` é essencial porque uma única imagem pode conter múltiplos gatos, e cada recorte vira input independente para MiewID/MegaDescriptor.

| Campo | Tipo | Uso |
|---|---|---|
| `cropID` * | string PK | UUID |
| `mediaID` * | FK → media | |
| `observationID` * | FK → observations | |
| `bboxX, bboxY, bboxWidth, bboxHeight` * | number | Coordenadas do recorte |
| `cropPath` | string | Caminho do JPG recortado (cache) |
| `quality` | number ∈ [0,1] | Score de qualidade (pose, foco, iluminação) |

**Tabela `embeddings`** — Vetores de Re-ID gerados pelos modelos (MiewID-msv3 primário, MegaDescriptor baseline, PPGNet-Cat referência cat-specific, OSNet baseline secundário herdado do projeto base). Cada crop pode ter múltiplos embeddings (um por modelo) para permitir comparação direta em B5.

| Campo | Tipo | Uso |
|---|---|---|
| `embeddingID` * | string PK | UUID |
| `cropID` * | FK → crops | |
| `model` * | string | `"miewid-msv3"`, `"megadescriptor"`, `"ppgnet-cat"`, `"osnet"` |
| `modelVersion` * | string | Tag/hash da versão (rastreabilidade) |
| `vector` * | blob (binary) | Float32 serializado, dim 512 ou 768 conforme modelo |
| `computedAt` * | datetime | Timestamp da inferência |

**Tabela `match_history`** — Histórico de matches Re-ID. Cada match associa um `cropID` a um `individualID` (ou propõe um novo indivíduo) com a similaridade calculada. Esta tabela é o coração da auditabilidade — permite recalcular indicadores se um modelo for substituído.

| Campo | Tipo | Uso |
|---|---|---|
| `matchID` * | string PK | UUID |
| `cropID` * | FK → crops | |
| `individualID` | FK → individuals (nullable se novo) | |
| `model` * | string | Idem `embeddings.model` |
| `similarity` * | number ∈ [-1,1] | Cosine similarity |
| `decision` * | string | `"matched"`, `"new_individual"`, `"rejected"`, `"pending_review"` |
| `decidedBy` * | string | `"automatic"` ou identificador humano |
| `decidedAt` * | datetime | |

**Tabela auxiliar `acquisition_profile_log`** — Necessária por causa do multi-perfil de aquisição definido em B3 (Categoria I PIR vs. Categoria II VMD). Permite saber a posteriori qual modo de transferência foi usado para cada `media`, o que afeta interpretação dos resultados (ex.: latência em E1 com SD swap é dias; em E2 RTSP é minutos).

| Campo | Tipo | Uso |
|---|---|---|
| `deploymentID` * | FK → deployments | |
| `acquisitionProfile` * | string | `"A"`, `"B"`, `"D"`, `"E1"`, `"E2"` |
| `triggerSource` * | string | `"PIR-hardware"` ou `"VMD-software"` |
| `transferMode` * | string | `"sd-swap"`, `"wifi-rtsp"`, `"wifi-cloud-sync"`, `"ethernet-edge"` |
| `transferLatency` | string | Estimativa qualitativa: `"minutes"`, `"hours"`, `"days"`, `"weeks"` |
| `edgeNodeID` | string | UUID do Pi 5 quando Perfil B; null em A/D/E1/E2 |

### B4.4.4 — Diagrama ER em notação Chen

A notação Chen é a que o Felipi domina (background do user-profile). Uso aqui retângulos para entidades, losangos para relacionamentos, elipses para atributos quando relevantes, e cardinalidades `(min,max)` nas linhas.

```
                          DIAGRAMA ER — Notação Chen
                  ┌────────────────────────────────────────┐
                  │   Sistema de Monitoramento de Colônia  │
                  │       (Camtrap-DP + Extensões)         │
                  └────────────────────────────────────────┘

                       ┌────────────────────┐
                       │   DEPLOYMENTS      │
                       │ ────────────────── │
                       │ PK deploymentID    │
                       │    locationID      │
                       │    latitude        │
                       │    longitude       │
                       │    cameraModel     │
                       │    deploymentStart │
                       │    deploymentEnd   │
                       └─────────┬──────────┘
                                 │ (1,1)
                                 │
                          ◇──────┴──────◇
                         ╱  TEM_PERFIL   ╲
                         ◇───────┬───────◇
                                 │ (1,1)
                                 ▼
                  ┌──────────────────────────┐
                  │ ACQUISITION_PROFILE_LOG  │
                  │ ──────────────────────── │
                  │    acquisitionProfile    │
                  │    triggerSource         │
                  │    transferMode          │
                  │    transferLatency       │
                  └──────────────────────────┘

                       ┌────────────────────┐
                       │   DEPLOYMENTS      │ ◇──────────◇
                       └─────────┬──────────┘ ╲ REGISTRA ╱
                                 │ (1,1)       ◇───┬────◇
                                 │                 │ (0,N)
                                 │                 ▼
                                 │     ┌────────────────────┐
                                 │     │      MEDIA         │
                                 │     │ ────────────────── │
                                 │     │ PK mediaID         │
                                 │     │ FK deploymentID    │
                                 │     │    timestamp       │
                                 │     │    filePath        │
                                 │     │    captureMethod   │
                                 │     └─────────┬──────────┘
                                 │               │ (1,1)
                                 │               │
                                 │        ◇──────┴──────◇
                                 │       ╱   GERA       ╲
                                 │       ◇──────┬───────◇
                                 │              │ (0,N)
                                 │              ▼
                                 │  ┌────────────────────────┐
                                 │  │     OBSERVATIONS       │
                                 └──┤ ──────────────────────  │
                                    │ PK observationID       │
                                    │ FK deploymentID        │
                                    │ FK mediaID             │
                                    │ FK individualID  (opt) │
                                    │    observationType     │
                                    │    scientificName      │
                                    │    bboxX, bboxY        │
                                    │    bboxWidth, bboxHeight│
                                    │    classifiedBy        │
                                    │    classificationProb  │
                                    └─────────┬──────────────┘
                                              │ (1,1)
                                              │
                                       ◇──────┴──────◇
                                      ╱  ORIGINA     ╲
                                      ◇──────┬───────◇
                                             │ (0,N)
                                             ▼
                                  ┌────────────────────┐
                                  │       CROPS        │
                                  │ ────────────────── │
                                  │ PK cropID          │
                                  │ FK observationID   │
                                  │ FK mediaID         │
                                  │    cropPath        │
                                  │    quality         │
                                  └─────────┬──────────┘
                                            │ (1,1)
                                            │
                                     ◇──────┴──────◇
                                    ╱  PRODUZ      ╲
                                    ◇──────┬───────◇
                                           │ (0,N)
                                           ▼
                                ┌──────────────────────┐
                                │     EMBEDDINGS       │
                                │ ──────────────────── │
                                │ PK embeddingID       │
                                │ FK cropID            │
                                │    model             │
                                │    modelVersion      │
                                │    vector (blob)     │
                                │    computedAt        │
                                └──────────┬───────────┘
                                           │ (1,N)
                                           │
                                    ◇──────┴──────◇
                                   ╱  RESULTA EM  ╲
                                   ◇──────┬───────◇
                                          │ (0,N)
                                          ▼
                               ┌────────────────────────┐
                               │   MATCH_HISTORY        │
                               │ ────────────────────── │
                               │ PK matchID             │
                               │ FK cropID              │
                               │ FK individualID (opt)  │
                               │    model               │
                               │    similarity          │
                               │    decision            │
                               └──────────┬─────────────┘
                                          │ (0,N)
                                          │
                                   ◇──────┴──────◇
                                  ╱  IDENTIFICA  ╲
                                  ◇──────┬───────◇
                                         │ (0,1)
                                         ▼
                              ┌────────────────────────┐
                              │     INDIVIDUALS        │
                              │ ────────────────────── │
                              │ PK individualID        │
                              │    nickname            │
                              │    earTipped           │
                              │    earTipSide          │
                              │    markings            │
                              │    sex, lifeStage      │
                              │    status              │
                              └────────────────────────┘
```

**Leitura do ER:**

- Um `deployment` tem exatamente **um** perfil de aquisição (Categoria I/PIR ou II/VMD, identificado em B3) e gera **N** mídias.
- Cada `media` gera **N** observações (uma imagem pode conter múltiplos gatos detectados).
- Cada observação que classifica um animal (`observationType = "animal"`) gera **um** crop (bounding box recortado).
- Cada crop produz **N** embeddings — um por modelo de Re-ID. Isso permite comparação direta de MiewID, MegaDescriptor, PPGNet-Cat e OSNet sobre o **mesmo crop**, garantindo experimento controlado em B5.
- Cada embedding gera **N** entradas em `match_history` (uma por tentativa de match contra o índice atual de indivíduos).
- Cada match aponta para **0 ou 1** indivíduo (zero = decisão `"rejected"` ou `"new_individual"` pendente).

**Restrições críticas:**

- `observations.individualID` é FK opcional para `individuals` — só é preenchida quando há decisão confirmada em `match_history`. Isso preserva consistência: a observação existe antes do Re-ID rodar.
- `embeddings.vector` é armazenado como BLOB binário em SQLite (4 bytes × dim). Em paralelo, **um índice HNSW** [(`hnswlib`)](https://github.com/nmslib/hnswlib) é construído em memória sobre os mesmos vetores para busca aproximada de vizinhos em O(log N), evitando varredura linear quando o banco crescer.

### B4.4.5 — Estratégia de migração SQLite → PostgreSQL+PostGIS

A revisão usa SQLite, mas o schema está desenhado para migração direta:

| Item | SQLite agora | PostgreSQL+PostGIS depois |
|---|---|---|
| Tipos | `TEXT`, `INTEGER`, `REAL`, `BLOB` | `VARCHAR`, `INTEGER`, `DOUBLE PRECISION`, `BYTEA` |
| Coordenadas | `latitude REAL, longitude REAL` | `geom GEOGRAPHY(POINT, 4326)` (PostGIS) |
| Busca espacial | Filtro Python sobre lat/lon | `ST_DWithin`, índice GiST |
| Busca vetorial | `hnswlib` em memória + reload | extensão `pgvector` com índice HNSW nativo |
| Concorrência | Single-writer (SQLite) | Multi-writer (Pg) |

O script de migração será gerado em B5 como parte do código reprodutível do TCC.

---

## B4.5 — Fluxo de dados E0→E4 (DFD)

O Diagrama de Fluxo de Dados (DFD) mostra como dados se movem do mundo físico (Categoria I/PIR ou II/VMD) até os indicadores finais, atravessando as 5 etapas da pipeline (E0 ingestão, E1 detecção, E2 espécie, E3 Re-ID, E4 indicadores) já especificadas em B2.

### B4.5.1 — DFD nível 0 (contexto)

```
            ┌─────────────────────────────────────────────────────────┐
            │                  AMBIENTE FÍSICO                        │
            │       (10 pontos P1-P10 do Campus 2 USP São Carlos)     │
            └────────────┬──────────────────────────┬─────────────────┘
                         │                          │
              [imagens]  │                          │  [eventos físicos:
              [vídeos]   │                          │   gato passa,
              [eventos   │                          │   PIR dispara,
               PIR/VMD]  │                          │   VMD detecta]
                         ▼                          │
                ┌──────────────────────┐            │
                │      P0              │            │
                │  SISTEMA DE          │◀───────────┘
                │  MONITORAMENTO       │
                │  (este TCC)          │
                └─────────┬────────────┘
                          │
              [dashboard]│ [indicadores: visitação,
              [relatórios]│  ear-tipping %, biodiversidade,
                          │  alertas bem-estar]
                          ▼
                ┌──────────────────────┐
                │  USUÁRIOS            │
                │  (AEX Gatosdoc2,     │
                │   orientadores,      │
                │   ONG ASA,           │
                │   Dra. Léa/Embrapa)  │
                └──────────────────────┘
```

### B4.5.2 — DFD nível 1 (decomposição em E0-E4)

```
   ┌────────────────────────────────────────────────────────────────────┐
   │                          DFD Nível 1                               │
   │             Pipeline E0→E4 com origens por perfil                  │
   └────────────────────────────────────────────────────────────────────┘

  ┌─────────────┐    ┌─────────────┐   ┌──────────────┐  ┌─────────────┐
  │  Perfil A   │    │  Perfil B   │   │  Perfil D    │  │ Perfil E1   │
  │ (trail PIR) │    │ (IP+Pi)     │   │ (Tapo/Reolink│  │ (OEM + SD)  │
  │ SD swap     │    │ ONVIF/RTSP  │   │  PIR consumer│  │ AC, no Wi-Fi│
  │ quinzenal   │    │ contínuo    │   │  + bateria)  │  │ swap mensal │
  └──────┬──────┘    └──────┬──────┘   └──────┬───────┘  └──────┬──────┘
         │                  │                  │                 │
         │  [JPGs SD]       │ [stream RTSP]    │ [JPGs/cloud]    │ [JPGs SD]
         │                  │                  │                 │
         └──────────────────┼──────────────────┴─────────────────┤
                            │                                    │
                            │     ┌─────────────┐                │
                            │     │ Perfil E2   │                │
                            │     │ (OEM RTSP)  │                │
                            │     │ ffmpeg pull │                │
                            │     └──────┬──────┘                │
                            │            │                       │
                            │  [stream]  │                       │
                            ▼            ▼                       ▼
                  ┌─────────────────────────────────────────────────┐
                  │                  E0 — INGESTÃO                  │
                  │  ──────────────────────────────────────────────  │
                  │  - Importa de SD (cópia incremental)            │
                  │  - Lê stream RTSP (ffmpeg keyframes)            │
                  │  - Sync de cloud (Tapo Care, opcional)          │
                  │  - Normaliza: deduplica, EXIF, timestamp, UUID  │
                  │  - Aplica VMD (Perfis B/E1/E2) ou usa flag PIR  │
                  │    (Perfis A/D) para descartar mídia "blank"    │
                  └────────────────────┬────────────────────────────┘
                                       │
                                       │ [media + EXIF + observation_type
                                       │  preliminar: "candidate animal"]
                                       │
                                       ▼
                  ┌─────────────────────────────────────────────────┐
                  │              E1 — DETECÇÃO                      │
                  │  ──────────────────────────────────────────────  │
                  │  Cascata:                                       │
                  │  (a) YOLO11n (~56 ms CPU) → triagem             │
                  │  (b) MegaDetector v6 → refinamento (caso        │
                  │      YOLO falhe ou confiança < threshold)       │
                  │  Saída: bounding boxes + confiança              │
                  └────────────────────┬────────────────────────────┘
                                       │
                                       │ [observations com bbox + classifiedBy]
                                       │
                                       ├──────► [observation_type ≠ "animal"]
                                       │        → arquivada com tag, sai do fluxo
                                       │
                                       ▼ [observation_type = "animal"]
                  ┌─────────────────────────────────────────────────┐
                  │           E2 — CLASSIFICAÇÃO DE ESPÉCIE         │
                  │  ──────────────────────────────────────────────  │
                  │  SpeciesNet (Google, 2.498 categorias)          │
                  │  Saída: scientificName + classificationProbab.  │
                  └────────────────────┬────────────────────────────┘
                                       │
                                       │ [observations atualizadas com taxon]
                                       │
                                       ├──────► [scientificName ≠ "Felis catus"]
                                       │        → registrada (biodiversidade),
                                       │           sai do fluxo Re-ID
                                       │
                                       ▼ [scientificName = "Felis catus"]
                  ┌─────────────────────────────────────────────────┐
                  │           E2.6 — PRÉ-PROCESSAMENTO              │
                  │  ──────────────────────────────────────────────  │
                  │  - Recorte crop a partir da bbox                │
                  │  - Score de qualidade (pose, foco, iluminação)  │
                  │  - Filtro: descarta crops com quality < 0.3     │
                  └────────────────────┬────────────────────────────┘
                                       │
                                       │ [crops válidos]
                                       │
                                       ▼
                  ┌─────────────────────────────────────────────────┐
                  │      E3 — REIDENTIFICAÇÃO INDIVIDUAL            │
                  │  ──────────────────────────────────────────────  │
                  │  (a) Inferência de embedding (MiewID-msv3)      │
                  │      [+ baselines em B5: MegaDescriptor,        │
                  │       PPGNet-Cat, OSNet]                        │
                  │  (b) Busca HNSW no índice de indivíduos         │
                  │  (c) Decisão:                                   │
                  │      - similarity > θ_match → MATCH             │
                  │      - similarity < θ_reject → NEW_INDIVIDUAL   │
                  │      - entre os dois → PENDING_REVIEW           │
                  └────────────────────┬────────────────────────────┘
                                       │
                                       │ [match_history + individualID
                                       │  populado em observations]
                                       │
                                       ▼
                  ┌─────────────────────────────────────────────────┐
                  │      E4 — INDICADORES E DASHBOARD               │
                  │  ──────────────────────────────────────────────  │
                  │  Agregações por janela temporal/espacial:       │
                  │  - Frequência de visitação por ponto/horário    │
                  │  - % castrados (earTipped=true) sobre N         │
                  │  - Indivíduos ativos vs. desaparecidos          │
                  │  - Biodiversidade (outras espécies em E2)       │
                  │  - Alertas: ausência > N dias, peso anômalo     │
                  └────────────────────┬────────────────────────────┘
                                       │
                                       │ [dashboard Streamlit]
                                       │ [exports CSV/JSON]
                                       │ [relatórios PDF]
                                       │
                                       ▼
                                ┌──────────────┐
                                │  USUÁRIOS    │
                                └──────────────┘
```

### B4.5.3 — Pontos de armazenamento intermediário (data stores no DFD)

O DFD acima mostra fluxo; mas em cada transição entre estágios há **gravação persistente** no SQLite. Sumário dos stores:

| Após estágio | Tabela(s) gravada(s) | Volume típico/mês |
|---|---|---|
| E0 | `deployments`, `acquisition_profile_log`, `media` | ~50.000 linhas em `media` |
| E1 | `observations` (com bbox) | ~30.000 linhas (≈60% das mídias têm animal) |
| E2 | `observations` (atualiza taxon) | mesmas linhas, update |
| E2.6 | `crops` | ~50.000 crops (cada `Felis catus` pode ter 1-3 crops) |
| E3 | `embeddings`, `match_history`, `observations.individualID` | 4 modelos × 50k = 200k embeddings (B5 só) |
| E4 | Views/materialized views agregadas | leitura |

**Justificativa da gravação granular:** permite **reproduzibilidade científica** (qualquer estágio pode ser reexecutado sem refazer os anteriores) e **auditoria** (se um modelo de Re-ID for trocado, basta limpar `embeddings` e `match_history` daquele `model` e reprocessar).

---

## B4.6 — Stack canônico de software

### B4.6.1 — Linguagem e runtime

- **Python 3.11+** como linguagem primária — domínio total do user-profile, ecossistema mais maduro para visão computacional. Versão mínima 3.11 por suporte a `match` statements (úteis no dispatcher de perfis) e melhor desempenho do interpretador.
- **Ambiente isolado:** `uv` ou `poetry` para lock-file reproduzível. `requirements.txt` exportado no repositório como fallback.

### B4.6.2 — Stack por camada

**Camada C1 (Edge — só quando Perfil B com Pi 5):**

| Componente | Software | Versão alvo | Função |
|---|---|---|---|
| OS Pi 5 | Raspberry Pi OS 64-bit (Bookworm) | 12+ | base |
| Captura RTSP | Frigate NVR ou script `ffmpeg` | Frigate 0.14+ | leitura ONVIF, detecção VMD com motion-vectors H.264 |
| Inferência opcional | YOLO11n via ONNX Runtime ou Hailo SDK | ORT 1.18+ / Hailo 4.x | só no P10 stretch |
| Sync | `rsync` agendado ou Frigate snapshot upload | — | empurra para C2 |

**Camada C2 (Lógica — PC central, núcleo do TCC):**

| Componente | Software | Versão alvo | Função |
|---|---|---|---|
| Visão computacional | **OpenCV** | 4.10+ | leitura/decodificação, augmentations |
| Deep learning | **PyTorch** | 2.4+ | inferência E1, E2, E3 |
| Detecção (E1) | **Ultralytics YOLO11** | 8.3+ (yolo11n) | primária |
| Detecção (E1) | **MegaDetector v6** | v6 (HF Hub) | refinamento |
| Espécie (E2) | **SpeciesNet** (Google) | 2024 release | classificação 2.498 taxa |
| Re-ID primário (E3) | **MiewID-msv3** | WildMe 2024 | embeddings cat-agnostic |
| Re-ID baseline (E3) | **MegaDescriptor-L-384** | HuggingFace | comparação multi-espécie |
| Re-ID referência (E3) | **PPGNet-Cat** [(Akbar et al., 2025)](https://link.springer.com/article/10.1007/s42979-024-03397-w) | implementação do paper | cat-specific (mAP 0.86) |
| Re-ID baseline secundário (E3) | **OSNet** (TorchReID) | 1.4+ | herdado do projeto base (PDF Sec. 7.3) — comparação contra estado da arte de Re-ID genérico |
| Decodificação vídeo | **ffmpeg** + **PyAV** | ffmpeg 6+ | extração de keyframes RTSP (Perfil E2) |
| Aceleração | **ONNX Runtime** (CPU + iGPU) | 1.18+ | inferência otimizada no i7 do Felipi |
| Vetor index | **hnswlib** | 0.8+ | busca aproximada k-NN em embeddings |
| Versionamento de experimentos | **Weights & Biases** (free tier) ou **MLflow** | — | rastreamento de runs em B5 |

**Camada C3 (Dados):**

| Componente | Software | Versão alvo | Função |
|---|---|---|---|
| SGBD | **SQLite** | 3.45+ | core persistence |
| Conformidade Camtrap-DP | **frictionless-py** | 5.17+ | validação do `datapackage.json` |
| Conversão Darwin Core (opcional) | **camtrapdp** (R via `rpy2`) ou exporter próprio | — | publicação futura GBIF |
| Indexação espacial | (futuro) **PostGIS** | 3.4+ | quando migrar |
| ORM (opcional, leve) | **SQLAlchemy 2** + Alembic | 2.0+ | migrations |

**Camada C4 (Apresentação):**

| Componente | Software | Versão alvo | Função |
|---|---|---|---|
| Dashboard | **Streamlit** | 1.38+ | UI rápida, alinhada com Sec. 7.5 do projeto base ("Dashboard Streamlit") |
| Gráficos | **Plotly** + **Altair** | Plotly 5.20+ | visualizações interativas |
| Mapas | **Folium** (Leaflet wrapper) | 0.16+ | localizações P1-P10 |
| Export PDF de relatórios | **WeasyPrint** ou **ReportLab** | — | indicadores impressos |

### B4.6.3 — Ferramentas de desenvolvimento e reprodutibilidade

| Categoria | Ferramenta | Justificativa (alinhamento com PDF Sec. 6.2) |
|---|---|---|
| Versionamento código | **Git + GitHub** | requisito explícito do projeto base |
| Versionamento dados | **DVC** (Data Version Control) | citado no PDF; essencial dado o volume de mídia |
| Anotação opcional | **CVAT** ou **Label Studio** | citados no PDF; usaremos para ajustes manuais em B5 |
| Testes | **pytest** + **pytest-cov** | qualidade de software |
| Linting/format | **ruff** + **black** | padrão Python moderno |
| CI/CD | **GitHub Actions** | execução de testes a cada commit |
| Notebooks | **Jupyter Lab** ou **VSCode notebooks** | exploração e relatórios reproduzíveis em B5 |
| Containerização (opcional) | **Docker** + `docker-compose` | empacotamento para entrega final |

### B4.6.4 — Pacotes Python — `requirements.txt` resumido

```text
# Core
python>=3.11

# Vision & ML
torch>=2.4
torchvision>=0.19
ultralytics>=8.3        # YOLO11
opencv-python>=4.10
onnxruntime>=1.18
av>=12.0                # PyAV para RTSP
ffmpeg-python>=0.2

# Re-ID
torchreid>=1.4          # OSNet baseline
huggingface_hub>=0.24   # MiewID, MegaDescriptor pull
hnswlib>=0.8

# Camtrap-DP
frictionless>=5.17

# Storage
sqlalchemy>=2.0
alembic>=1.13

# UI/Reports
streamlit>=1.38
plotly>=5.20
folium>=0.16
weasyprint>=62

# Experimentos
mlflow>=2.15            # ou wandb>=0.17
dvc>=3.55

# Dev
pytest>=8.3
ruff>=0.6
black>=24.8
```

### B4.6.5 — Nota sobre modelos do projeto base vs. revisão

O projeto base [(PDF Sec. 7.3)](#) menciona explicitamente "OSNet, TransReID, Deep Metric Learning" como modelos de Re-ID e "YOLOv8, Swin Transformers" como detectores. Decisões de evolução tomadas nesta revisão:

| Modelo do PDF | Status na revisão | Justificativa |
|---|---|---|
| **YOLOv8** | Atualizado para **YOLO11** | YOLO11n tem mesma arquitetura geral, melhor desempenho/latência (Ultralytics, 2024) |
| **OSNet** | Mantido como **baseline secundário em B5** | Re-ID otimizado para pessoas; usado para comparação numérica |
| **TransReID** | Avaliado, **não rodado** em B5 inicial | Custo computacional inviável em CPU para volume previsto; opcional como stretch |
| **Swin Transformers (E2)** | Substituído por **SpeciesNet** | SpeciesNet cobre 2.498 categorias com modelo treinado especificamente em fauna; Swin genérico exigiria fine-tuning extensivo |
| **Faster R-CNN, DETR** (PDF) | Não rodados | Cobertura redundante com YOLO11 + MegaDetector; descartados por economia de tempo |

Esta racionalização será detalhada em B5 (validação) e revisitada em B6 (consolidação), seguindo a recomendação do próprio PDF Sec. 9 ("definir métricas rigorosas... realizar experimentos comparativos e discutir realisticamente limitações").

---

## B4.7 — Notas sobre alimentadores como local físico de montagem

O projeto base lista, na Sec. 2.2.2(c) e 7.2, "projetar alimentadores inteligentes que integrem alimentação segura, monitoramento visual e proteção contra outras espécies". Como o foco da revisão é processamento de visão computacional (instrução explícita do Felipi), não detalho o design mecânico completo do alimentador, mas registro aqui os requisitos **mínimos** que o alimentador deve atender enquanto **estrutura de montagem da câmera** — alinhamento entre B4 (câmera) e o alimentador inteligente como projeto futuro.

### B4.7.1 — Função estrutural do alimentador

O alimentador inteligente é o **local físico** onde a câmera dos Perfis A, B, D, E1 ou E2 é instalada. Ele cumpre 4 funções para a visão computacional:

1. **Anchor geométrico** — define a posição (altura, ângulo, distância à zona de alimentação) que torna a imagem aproveitável para detecção e Re-ID.
2. **Atrator comportamental** — concentra os gatos em uma zona de ~1 m² previsível, maximizando a probabilidade de capturar a face e o flanco (cruciais para MiewID e PPGNet-Cat).
3. **Iluminação controlada** — superfície clara (cor mate) na bandeja de alimentação melhora o contraste do gato contra o fundo, especialmente à noite com IR.
4. **Proteção da câmera** — abrigo contra chuva e sol direto, alinhamento com `cameraHeight` e `cameraHeading` do Camtrap-DP estável ao longo do deployment.

### B4.7.2 — Requisitos mínimos para o módulo câmera-no-alimentador

| Parâmetro | Faixa recomendada | Razão computacional |
|---|---|---|
| Altura da câmera (`cameraHeight`) | 1.2 – 1.8 m | Captura face e flanco; evita oclusão por bandeja |
| Ângulo de inclinação (`cameraTilt`) | -20° a -30° (apontada para baixo) | Maximiza tempo do gato no quadro |
| Distância câmera ↔ bandeja | 1.5 – 2.5 m | Equilibra resolução (≥ 100 px na cabeça do gato) e profundidade de campo |
| Resolução mínima | 1280×720 (HD) | Limite inferior para Re-ID confiável (Akbar 2025) |
| FPS mínimo | 5 fps (gravação) / 15 fps (stream) | Captura múltiplas poses |
| IR cut-filter automático | Sim | Operação 24/7; noturna é crítica para gatos |
| Ângulo de campo (FoV) | 90°-110° horizontal | Cobre toda a zona de alimentação |
| Proteção IP | IP65+ | Resistência a chuva |

Estes valores serão referenciados em `deployments.cameraHeight`, `cameraTilt`, `cameraHeading` e `detectionDistance` quando o sistema entrar em campo (fase pós-TCC).

### B4.7.3 — Proteção contra outras espécies (alinhamento com PDF Sec. 2.2.2(c))

O design mecânico do alimentador (fora do escopo deste TCC) deve considerar exclusão de capivaras, gambás e cães. Isto é citado aqui para registrar a **interface entre módulos**:

- **Sensor de presença adicional** (RFID na coleira pós-castração ou peso na plataforma) pode acionar dispensação seletiva — independente da câmera.
- **A câmera registra** todas as visitas, independentemente da dispensação; isto alimenta o indicador de biodiversidade em E4 (espécies não-alvo).

**Conclusão de B4.7:** este bloco fecha o gap entre o projeto base (que lista alimentadores como entregável) e a revisão (focada em processamento), garantindo que a estrutura de dados (`deployments.cameraHeight`, `featureType="feeding station"`) e o pipeline (E2 detecta outras espécies como sinal positivo, não erro) já estão preparados para receber o alimentador físico quando ele for projetado em fase futura.

---

## Resumo executivo da Parte 2

| Bloco | Entregável | Linhas/elementos |
|---|---|---|
| **B4.4** | Schema Camtrap-DP 1.0.1 + 4 extensões + 1 tabela auxiliar + diagrama ER em notação Chen | 8 entidades, 7 relacionamentos |
| **B4.5** | DFD nível 0 + DFD nível 1 com origens por perfil | 2 diagramas, 5 estágios E0-E4 mapeados |
| **B4.6** | Stack canônico Python 3.11+ com 30+ pacotes especificados | 4 camadas × N componentes |
| **B4.7** | Interface câmera ↔ alimentador inteligente | Tabela de 8 parâmetros físicos |

**Próximo:** **B5 — Plano de validação e implementação**. Cobrirá: experimentos com datasets públicos (Oxford-IIIT, CatFLW, PetFace, Cat Individual Images, HelloStreetCat), métricas reprodutíveis, scripts Python, gráficos comparativos de MiewID vs. MegaDescriptor vs. PPGNet-Cat vs. OSNet, plano de piloto offline em laboratório com vídeos representativos.

---

## Fontes citadas nesta parte

- [Camtrap-DP 1.0.1 — Especificação Data (TDWG)](https://camtrap-dp.tdwg.org/data/)
- [Camtrap-DP 1.0.1 — Especificação Metadata (TDWG)](https://camtrap-dp.tdwg.org/metadata/)
- [Camtrap-DP Releases — GitHub TDWG](https://github.com/tdwg/camtrap-dp/releases)
- [Rowcliffe et al., Camtrap DP: open standard for FAIR exchange of camera trap data](https://ecoevorxiv.org/repository/object/5593/download/10949/)
- [camtrapdp R package — CRAN/INBO](https://inbo.github.io/camtrapdp/)
- [Best Practices for Managing and Publishing Camera Trap Data — GBIF](https://docs.gbif.org/camera-trap-guide/)
- [Akbar et al., 2025 — PPGNet-Cat para Re-ID felino (mAP 0.86)](https://link.springer.com/article/10.1007/s42979-024-03397-w)
- [hnswlib — busca aproximada k-NN](https://github.com/nmslib/hnswlib)
- Projeto base do TCC — `projeto_tcc.pdf` (23 páginas, rascunho aprovado 2026)
