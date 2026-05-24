# B2 — Pipeline conceitual de visão computacional (Parte 3)

> **Continuidade**: a Parte 1 cobriu o pipeline geral (E0–E4) + aquisição (E0) + detecção (E1) + **workflow detalhado do voluntário com cartão SD**. A Parte 2 cobriu classificação (E2) + re-identificação (E3, núcleo) + pré-processamento (E2.6). Esta **Parte 3** fecha o B2 com:
>
> - **B2.7** — Estágio **E4 (Persistência e indexação)**: schema relacional aderente ao padrão **Camtrap-DP**, índice vetorial para a galeria de re-ID, backup e exportação.
> - **B2.8** — **Métricas ponta-a-ponta**: orçamento de latência por estágio, KPIs operacionais, fronteira de qualidade × custo.
> - **B2.9** — **Plano de testes no notebook do Pesquisador** (**[PLACEHOLDER-HARDWARE-NOTEBOOK]**): estratégia de profiling, cenários de stress, failover.
>
> **Reafirmação do princípio pipeline-agnóstico**: E4, métricas e plano de testes são **idênticos** independentemente do perfil de ponto (OFF-SD, NET, AC, AC+NET). A única adaptação operacional vem em B2.8.1 (filosofia em lote, não tempo real — consequência direta do caso primário OFF-SD).

---

## B2.7 — Estágio E4: persistência e indexação

### B2.7.1 — O que precisa ser persistido

O sistema produz, ao longo de toda a operação, sete famílias distintas de dados que precisam ser armazenadas de forma diferenciada:

1. **Mídias brutas** (imagens JPEG, opcionalmente vídeos curtos) — arquivos binários, grandes, gravados majoritariamente uma vez e lidos sob demanda.
2. **Metadados de captura** (timestamp, ponto, modalidade RGB/IR, EXIF) — pequenos, estruturados, indexáveis.
3. **Detecções de E1** (bounding-boxes, scores de confiança, classe genérica "animal/pessoa/veículo") — médias, relacionais, vinculadas à mídia.
4. **Classificações de E2** (espécie, score, modelo usado, versão) — médias, vinculadas a detecções.
5. **Embeddings de E3** (vetores de 512–2.048 dimensões + metadados de qualidade) — densos, otimizados para busca por similaridade, **não** indexáveis por SQL convencional.
6. **Identidades** (catálogo de gatos, nomes, histórico, fotos canônicas) — pequena, mas crítica para o domínio.
7. **Eventos de presença** (agregação de detecções em "sequências" com `cat_id` resolvido e contagem) — médias, alvo principal das análises ecológicas do projeto.

A decisão arquitetural fundamental é **separar mídias (arquivos no sistema de arquivos) de metadados (banco relacional) e de embeddings (índice vetorial)**. Tentar guardar tudo em um único repositório (e.g., todos os JPEGs como BLOBs em SQLite) é antipattern padrão da literatura de camera-trap ([GBIF Best Practices Guide](https://docs.gbif.org/camera-trap-guide/)).

### B2.7.2 — Aderência ao padrão Camtrap-DP

Em 2024, [Bubnicki et al. (Remote Sensing in Ecology and Conservation 10(3):283–295)](https://www.fs.usda.gov/rm/pubs_journals/2023/rmrs_2023_bubnicki_j001.pdf) consolidaram o **Camtrap DP (Camera Trap Data Package)**, padrão aberto desenvolvido sob a umbrella da **Biodiversity Information Standards (TDWG)** e endossado pelo **GBIF**. É o **único padrão consensual** da comunidade global de camera-trapping, adotado por Wildlife Insights, Agouti e TRAPPER ([camtrap-dp.tdwg.org](https://camtrap-dp.tdwg.org)).

O Camtrap DP estrutura dados em **três tabelas CSV obrigatórias** + metadados em JSON:

| Tabela | Conteúdo | Mapeia para no TCC |
|---|---|---|
| `deployments.csv` | Cada implantação de câmera (local + período de operação) | Ponto Pn no Campus 2 × janela temporal (entre manutenções) |
| `media.csv` | Cada arquivo de mídia gerado | Cada imagem JPEG capturada pelo evento de trigger |
| `observations.csv` | Cada observação biológica (espécie ou indivíduo) | Cada detecção+classificação+re-ID consolidada de um evento |
| `datapackage.json` | Metadados do estudo (autoria, licença, projeto) | Cabeçalho com Pesquisador autor, Revisora, Orientador, AEX Gatosdoc2, USP, licença CC-BY (a confirmar com orientador) |

**Decisão arquitetural**: o banco interno do TCC **espelhará a estrutura Camtrap-DP** (mesmas três tabelas como núcleo) e estenderá com tabelas adicionais necessárias (identidades, embeddings, eventos). Isso permite **exportar para Camtrap-DP em um único `pg_dump` / COPY** ao final do piloto, viabilizando publicação no GBIF ou agregadores brasileiros (SiBBr) **sem retrabalho**.

### B2.7.3 — Escolha do SGBD: SQLite vs. PostgreSQL

A literatura ([dev.to comparação 2025](https://dev.to/lovestaco/postgresql-vs-sqlite-dive-into-two-very-different-databases-5a90); [Hacker News discussão 2022](https://news.ycombinator.com/item?id=32676455)) é clara sobre o trade-off:

| Critério | SQLite | PostgreSQL |
|---|---|---|
| Setup | Zero-config; arquivo único | Servidor; configuração e tuning |
| Concorrência de escrita | **Single-writer** (com WAL ajuda em leitura) | MVCC; múltiplos writers reais |
| Tamanho típico | Até centenas de GB ainda eficiente | TB+ sem perda |
| Backup | Cópia de arquivo | `pg_dump`, replicação, WAL shipping |
| GIS / dados espaciais | SpatiaLite (extensão) | **PostGIS** (referência da indústria) |
| Dependência operacional | Nenhuma (embedded) | Processo daemon |
| Adequação para o piloto (notebook do Pesquisador, `[~50 gatos]`, `[~10 pontos]`, `[PLACEHOLDER-VOLUME-REAL]` ~5–20 mil imagens/mês) | **Excelente** | Overkill |
| Adequação se o sistema escalar (mais pontos, múltiplos usuários remotos) | Insuficiente | **Necessário** |

**Decisão dupla, em camadas**:

- **Fase piloto (2026)**: **SQLite** com WAL ativado. Razões: zero-config para o Pesquisador rodar no próprio notebook (**[PLACEHOLDER-HARDWARE-NOTEBOOK]**); backup é cópia do arquivo `.db`; CLI `sqlite3` simples; sem dependência de serviço externo; literatura indica que SQLite é "blazing fast" para read-heavy local ([dev.to 2025](https://dev.to/lovestaco/postgresql-vs-sqlite-dive-into-two-very-different-databases-5a90)).
- **Caminho de evolução documentado em B3 e B4**: migração para **PostgreSQL + PostGIS** caso o sistema cresça (mais pesquisadores, múltiplos campi, dashboards web concorrentes). A escolha por **TRAPPER (Django + PostgreSQL + PostGIS + RabbitMQ + Celery)** é o cenário de evolução natural ([trapper-project no GitLab](https://gitlab.com/trapper-project/trapper)).

Schema SQL idêntico em ambos (pequenas adaptações de tipo) permite a migração futura ser executada com `pg_loader` ou similar.

### B2.7.4 — Schema relacional proposto (conceitual)

Apresentação em pseudo-DDL para clareza; a notação Chen completa será produzida no relatório formal.

```
-- 1. ESPELHO DO CAMTRAP-DP

CREATE TABLE deployments (
    deployment_id    TEXT PRIMARY KEY,        -- e.g. "P03_2026-03-15"
    location_name    TEXT NOT NULL,           -- "P03 - próximo ICMC bloco 6"
    latitude         REAL NOT NULL,
    longitude        REAL NOT NULL,
    deployment_start TIMESTAMP NOT NULL,
    deployment_end   TIMESTAMP,
    setup_by         TEXT,                    -- ator: Pesquisador / Voluntário-AEX
    camera_id        TEXT,                    -- série/modelo da câmera
    camera_height_m  REAL,
    camera_angle_deg INTEGER,
    -- perfil funcional do ponto (B1 v2)
    point_profile    TEXT,                    -- 'OFF-SD' | 'NET' | 'AC' | 'AC+NET'
    has_pir          INTEGER,                 -- 0/1: hardware do ponto possui PIR físico
    notes            TEXT
);

CREATE TABLE media (
    media_id         TEXT PRIMARY KEY,        -- UUID
    deployment_id    TEXT NOT NULL REFERENCES deployments,
    file_path        TEXT NOT NULL,           -- caminho relativo no FS
    file_mediatype   TEXT NOT NULL,           -- image/jpeg, image/png
    capture_timestamp TIMESTAMP NOT NULL,
    modality         TEXT NOT NULL,           -- 'rgb' | 'ir'
    width_px         INTEGER,
    height_px        INTEGER,
    event_id         TEXT,                    -- agrupa frames de um burst
    exif_json        TEXT                     -- dump JSON do EXIF
);
CREATE INDEX idx_media_event ON media(event_id);
CREATE INDEX idx_media_deploy_ts ON media(deployment_id, capture_timestamp);

CREATE TABLE observations (
    observation_id   TEXT PRIMARY KEY,
    media_id         TEXT REFERENCES media,
    event_id         TEXT,                    -- redundante mas útil para queries
    deployment_id    TEXT NOT NULL,
    observation_type TEXT NOT NULL,           -- 'animal' | 'human' | 'blank' | 'vehicle'
    -- detecção (E1)
    bbox_x           REAL,
    bbox_y           REAL,
    bbox_w           REAL,
    bbox_h           REAL,
    detector_name    TEXT,                    -- 'MegaDetector_v6'
    detector_version TEXT,
    detector_score   REAL,
    -- classificação (E2)
    scientific_name  TEXT,                    -- 'Felis catus'
    classifier_name  TEXT,                    -- 'SpeciesNet'
    classifier_version TEXT,
    classifier_score REAL,
    -- re-id (E3)
    cat_id           TEXT REFERENCES cats,    -- NULL se não foi para re-ID
    reid_model_name  TEXT,                    -- 'MiewID_multispecies_v2'
    reid_score       REAL,                    -- similaridade do match
    reid_status      TEXT,                    -- 'auto_match' | 'human_review' | 'new_individual' | 'rejected'
    -- auditoria
    reviewed_by      TEXT,
    reviewed_at      TIMESTAMP,
    reviewer_decision TEXT
);
CREATE INDEX idx_obs_cat ON observations(cat_id);
CREATE INDEX idx_obs_event ON observations(event_id);

-- 2. EXTENSÕES ESPECÍFICAS DO TCC

CREATE TABLE cats (
    cat_id           TEXT PRIMARY KEY,        -- e.g. "GATO_007"
    nome             TEXT,                    -- nome de campo (atribuído pela AEX)
    sexo_aparente    TEXT,                    -- 'M' | 'F' | 'desconhecido'
    cor_dominante    TEXT,
    primeira_aparicao TIMESTAMP,
    ultima_aparicao  TIMESTAMP,
    status           TEXT,                    -- 'ativo' | 'adotado' | 'obito' | 'desaparecido'
    foto_canonica_media_id TEXT REFERENCES media,
    notas            TEXT
);

CREATE TABLE embeddings (
    embedding_id     TEXT PRIMARY KEY,
    cat_id           TEXT REFERENCES cats,    -- NULL se ainda não atribuído
    observation_id   TEXT REFERENCES observations,
    model_name       TEXT NOT NULL,           -- 'MiewID_multispecies'
    model_version    TEXT NOT NULL,
    embedding_dim    INTEGER NOT NULL,        -- 512 ou 2048
    embedding_blob   BLOB NOT NULL,           -- float32 packed
    quality_score    REAL,                    -- [0,1] derivado em B2.6
    modality         TEXT,                    -- 'rgb' | 'ir'
    captured_at      TIMESTAMP
);
CREATE INDEX idx_emb_cat ON embeddings(cat_id);

CREATE TABLE presence_events (
    event_id         TEXT PRIMARY KEY,        -- UUID
    deployment_id    TEXT NOT NULL,
    cat_id           TEXT REFERENCES cats,    -- pode ser NULL (gato não identificado)
    event_start      TIMESTAMP NOT NULL,
    event_end        TIMESTAMP NOT NULL,
    n_frames         INTEGER,
    n_observations   INTEGER,
    aggregate_method TEXT,                    -- 'majority_vote' | 'best_score'
    confidence       REAL,
    notes            TEXT
);
CREATE INDEX idx_pe_cat_time ON presence_events(cat_id, event_start);
CREATE INDEX idx_pe_deploy_time ON presence_events(deployment_id, event_start);
```

**Notas sobre o schema**:
- As três tabelas Camtrap-DP (`deployments`, `media`, `observations`) contêm todos os campos obrigatórios do padrão. Exportar para CSV via `SELECT` direto produz arquivos válidos.
- `presence_events` é a **vista materializada** que o TCC usará para analisar atividade por gato e por ponto. É o que vai virar gráficos (histograma de presença por dia/hora, mapa de calor por ponto, curva de descoberta de novos indivíduos).
- `embeddings` armazena os vetores em BLOB (eficiente em SQLite). A **busca por similaridade**, no entanto, **não é feita via SQL** — é feita via índice vetorial em memória (próxima sub-seção).
- O `event_id` aparece em três tabelas (`media`, `observations`, `presence_events`) para queries diretas sem joins.

### B2.7.5 — Índice vetorial para a galeria de re-ID

Buscar o vizinho mais próximo de um embedding contra **N** vetores na galeria é o gargalo da etapa E3. Há três famílias de soluções:

**Tabela B2.7-1 — Bibliotecas de busca vetorial**

| Biblioteca | Algoritmo | Pontos fortes | Pontos fracos | Adequação ao TCC |
|---|---|---|---|---|
| **Brute-force NumPy** | Cosine similarity exata | Trivial; 100% recall; zero deps | O(N) por consulta | **Suficiente** para N ≤ 1.000 vetores; provavelmente o ponto inicial |
| **hnswlib** | HNSW (graph-based) | **CPU-friendly**, baixa latência, alta acurácia, indexação incremental ([Vectroid 2025](https://vectroid.com/resources/hnsw-vs-faiss-comprehensive-comparison)) | Maior uso de RAM; índice tem que caber em memória ([Zilliz 2024](https://zilliz.com/blog/faiss-vs-hnswlib-choosing-the-right-tool-for-vector-search)) | **Recomendado** para o piloto. RAM disponível no notebook do Pesquisador (`[PLACEHOLDER-HARDWARE-NOTEBOOK]`, faixa esperada 8–16 GB) não é restrição e o índice de ~10.000 embeddings × 512 dims × 4 bytes ≈ 20 MB é trivial |
| **FAISS** | Múltiplos: Flat, IVF, PQ, HNSW | Otimizado para GPU; bilhões de vetores; várias estratégias ([Vectroid 2025](https://vectroid.com/resources/hnsw-vs-faiss-comprehensive-comparison); [Milvus AI quick ref 2026](https://milvus.io/ai-quick-reference/what-is-the-role-of-faiss-hnsw-and-scann-in-ai-databases)) | Mais complexo; curva de aprendizado; "billion-scale" é overkill | **Backup** se o sistema crescer muito |

**Decisão**: usar **`hnswlib`** como índice de produção, com **fallback brute-force NumPy** documentado e testado para os primeiros meses do piloto (quando a galeria tem < 1.000 vetores e cosine exata é tão rápida que HNSW só agrega complexidade). A migração entre os dois é transparente (interface única no código).

**Parâmetros HNSW recomendados** (baseados em [Marqo 2025: Understanding Recall in HNSW](https://www.marqo.ai/blog/understanding-recall-in-hnsw-search)):
- `M = 16` (conectividade)
- `efConstruction = 200` (qualidade do grafo)
- `efSearch = 100` (qualidade da busca; aumentar para 200–500 se recall ficar abaixo de 0,98 em validação)

**Persistência do índice**: serializar em disco (`hnswlib.Index.save_index`) a cada N novos embeddings (e.g., a cada 50), com checkpoint atômico. Rebuild completo a partir da tabela `embeddings` em caso de corrupção.

### B2.7.6 — Diagrama lógico das três camadas

```
   ┌──────────────────────────────────────────────────────────────┐
   │  CAMADA 1 — FILESYSTEM (mídias brutas)                       │
   │    /data/captures/<deployment_id>/<YYYY-MM>/<media_id>.jpg   │
   │    Backup: rsync semanal para HD externo                     │
   └──────────────────────────────────────────────────────────────┘
                              ↑ file_path
   ┌──────────────────────────────────────────────────────────────┐
   │  CAMADA 2 — SQLITE (metadados, Camtrap-DP compatível)        │
   │    deployments • media • observations                        │
   │    cats • embeddings (BLOB) • presence_events                │
   │    Backup: cópia de capture_trap.db diária                   │
   └──────────────────────────────────────────────────────────────┘
                              ↑ embedding_id
   ┌──────────────────────────────────────────────────────────────┐
   │  CAMADA 3 — HNSWLIB (índice vetorial em memória)             │
   │    Grafo HNSW de embeddings de re-ID                         │
   │    Map: hnsw_internal_id ↔ embedding_id (SQLite)             │
   │    Persistência: capture_trap.hnsw em disco                  │
   └──────────────────────────────────────────────────────────────┘
```

### B2.7.7 — Backup, exportação e retenção

**Backup local (essencial)**:
- Filesystem das mídias: `rsync` incremental para HD externo do Pesquisador ou para `[PLACEHOLDER-NUVEM-INSTITUCIONAL]` (frequência atrelada ao ciclo de ingestão de cartões SD — B2.2.11).
- Banco SQLite: cópia diária do arquivo `capture_trap.db` (a CLI sqlite3 já fornece `.backup`); rotação de 7 dias.
- Índice HNSW: cópia junto com o `.db`.

**Backup remoto (recomendado)**:
- Espelho seletivo (banco + amostras de fotos) em **[PLACEHOLDER-NUVEM-INSTITUCIONAL]** (Google Drive USP, OneDrive USP do Orientador, ou nuvem da própria AEX — a definir).
- Critério de seleção: todas as `cats` + `embeddings` + 1 foto canônica por gato + presence_events. Total estimado em alguns GB.

**Exportação Camtrap-DP** ao final do piloto:
- Script Python que lê o SQLite e emite `datapackage.json` + 3 CSVs conforme spec [camtrap-dp.tdwg.org](https://camtrap-dp.tdwg.org).
- Pacote pronto para envio ao GBIF via IPT v3+ ([discourse GBIF 2025](https://discourse.gbif.org/t/publishing-camtrap-dp-with-the-iptv3/5758)) ou ao SiBBr.

**Retenção e LGPD**:
- Imagens contendo humanos: **descarte em até 30 dias após classificação**; manter apenas log textual (timestamp + ponto + "human" sem imagem).
- Imagens de gatos: retenção indefinida (interesse de pesquisa).
- Após defesa do TCC: avaliar com Orientador e Coordenação-AEX a publicação do dataset como recurso aberto (atendendo à recomendação FAIR de Camtrap-DP).

> **Q-INF-E4-1**: É preferível, para a AEX Gatosdoc2, manter o dataset privado (uso interno) ou abrir publicamente em GBIF/SiBBr ao fim do piloto? Trade-off: visibilidade científica × possibilidade de mau uso (e.g., terceiros localizando colônias para retirada de animais). — pergunta a discutir com Orientador e Coordenação-AEX.

---

## B2.8 — Métricas ponta-a-ponta e orçamento de latência

### B2.8.1 — Filosofia: pipeline assíncrono em lotes, não tempo real

O TCC **não** é um sistema de tempo real: nenhuma decisão depende de detectar e re-identificar o gato dentro de segundos. Esta característica decorre diretamente do **caso primário OFF-SD** descrito em B1 v2 e detalhado em B2.2.10: o ciclo natural é

1. **Câmeras** captam imagens 24/7, gravando localmente em SD.
2. **Voluntário-AEX** coleta cartões SD em frequência adaptativa (semanal a quinzenal conforme calibração por ponto — ver B2.2.11). Pontos com Wi-Fi (NET / AC+NET) podem sincronizar com mais frequência, mas o pipeline não depende disso.
3. **Pipeline processa em lote** no notebook do Pesquisador (**[PLACEHOLDER-HARDWARE-NOTEBOOK]**), idealmente durante a noite ou em janela ociosa.
4. **Resultados** ficam disponíveis para análise no dia seguinte.

Isso muda a métrica-chave: **não é latência por imagem, é throughput por noite (8h)**. Cabe processar uma semana inteira de dados em uma janela noturna? Vamos estimar.

### B2.8.2 — Volume de dados esperado

Estimativa de imagens/semana com base em B1 v2 (estimativas a confirmar em campo):
- **[~10 pontos ativos estimados]**.
- ~3–10 eventos/dia/ponto (ordem de grandeza, varia com ponto e estação).
- ~5 frames por evento (burst típico).
- → ~21–70 eventos/dia × 5 frames × [~10 pontos] = **750 a 2.500 frames/semana**.
- Em surtos (ponto novo, época de cio, época de alimentação aumentada): possível pico de **5.000 frames/semana**.

Tamanho: a 1080p JPEG médio ~ 400 KB → ~300 MB a 2 GB/semana, tolerável para qualquer disco.

> **[PLACEHOLDER-VOLUME-REAL]** — após as primeiras 4 semanas de calibração, atualizar esta tabela com média e desvio-padrão reais de frames/semana por ponto.

### B2.8.3 — Orçamento de latência por estágio

Valores estimados a partir da literatura para um Intel i7 padrão (8–12 cores, 16 GB RAM, **sem GPU dedicada** no cenário mais conservador). Estágios são pipelinados, então o total é \( \max \) dos individuais (não soma).

**Tabela B2.8-1 — Latência estimada por estágio em CPU i7 (sem GPU)**

| Estágio | Modelo | Latência por frame (CPU) | Throughput (frames/h) | Throughput (frames/8h) | Fonte/justificativa |
|---|---|---|---|---|---|
| **E0** | Aquisição (já feita pela câmera) | — | — | — | offline |
| **E1** | MegaDetector v6 (CPU, FP32) | ~150–300 ms | ~12.000–24.000 | ~96.000–192.000 | ordens de grandeza extrapoladas de [MegaDetector benchmarks GitHub 2023–2025](https://github.com/agentmorris/MegaDetector/blob/main/megadetector.md) (GPU faz 17 img/s = 60 ms; CPU é ~3–5× mais lento) |
| **E1 (alt.)** | YOLO11n em CPU | ~56 ms ([Ultralytics docs 2025](https://docs.ultralytics.com/compare/yolo26-vs-yolo11/)) | ~64.000 | ~512.000 | medição oficial Ultralytics |
| **E2** | SpeciesNet (EfficientNetV2-M, CPU) | ~120 ms | ~30.000 | **30.000 (publicado pelo Google)** | [Google blog 2025](https://research.google/blog/where-wild-things-roam-identifying-wildlife-with-speciesnet/) afirma "~30.000 imagens/dia em laptop standard" |
| **E3** | MiewID multispecies (CPU, FP32) | ~80–150 ms | ~25.000–45.000 | ~200.000–360.000 | Swin-B com 109M params em CPU é gargalo; estimativa baseada em [HuggingFace BVRA/MegaDescriptor-B-224](https://huggingface.co/BVRA/MegaDescriptor-B-224) |
| **E3 busca HNSW** | hnswlib `efSearch=100` | < 1 ms para galeria de 10.000 vetores 512-D | > 3.600.000 | irrelevante (não é gargalo) | [hnswlib benchmarks](https://github.com/erikbern/ann-benchmarks) |
| **E4** | Inserção SQLite + atualização HNSW | < 5 ms | > 700.000 | irrelevante | testes locais SQLite WAL |

**Conclusão crítica**: o gargalo do pipeline em CPU é **E2 (SpeciesNet)** com ~30.000 imagens em 8h. O volume esperado de **2.500–5.000 frames/semana** está **uma ordem de grandeza abaixo do limite** — processar uma semana leva ~40 a 90 minutos no pior caso. **A operação em CPU é viável para o piloto sem GPU dedicada**, mesmo no caso primário OFF-SD onde toda uma semana de dados chega de uma vez.

**Com GPU dedicada simples** (e.g., GTX 1650 / RTX 3050, ~5 TFLOPS FP32):
- E1, E2, E3 ganham 5–15×. Pipeline despacha **>100.000 imagens em 8h**.
- Não é necessário para o piloto, mas reduz a janela de processamento de horas para minutos, libera o PC para outras atividades, e abre caminho para fine-tuning local de MiewID.

### B2.8.4 — KPIs operacionais

A Tabela B2.8-2 lista métricas que o sistema reportará automaticamente, semanal e mensalmente.

**Tabela B2.8-2 — KPIs do sistema**

| Categoria | KPI | Meta | Fonte de verdade |
|---|---|---|---|
| **Cobertura** | Uptime por ponto | ≥ 90% das horas previstas | `deployments` × tempo de operação efetiva |
| | Eventos capturados por ponto/semana | Calibrar; espera-se 20–70 (ponto de partida, confirmar com dados reais) | `presence_events` |
| **Operação de campo** | Cartões trocados sem incidente | ≥ 95% das visitas | Log do procedimento B2.2.10.3 |
| | Clock-drift detectado | < 10% dos cartões | `media.clock_status` |
| **Qualidade E1** | Falsos positivos por semana | < 10% das detecções | Auditoria amostral |
| | Falsos negativos (gato não detectado) | < 5% (mais difícil de medir) | Auditoria humana de subconjuntos |
| **Qualidade E2** | Precision Felis catus | ≥ 0,95 | Conjunto anotado |
| **Qualidade E3** | Rank-1 em validação | ≥ 0,85 | Splits temporais |
| | mAP em validação | ≥ 0,75 | Splits temporais |
| | BAKS / BAUS (média harmônica) | ≥ 0,80 | Splits temporais com indivíduos hold-out |
| **Ecologia** | Curva de descoberta de novos indivíduos | Saturação visível até semana 12 | `cats.primeira_aparicao` |
| | Estimativa de tamanho da colônia (Lincoln-Petersen ou similar) | Documentar IC 95% | `presence_events` |
| **Engenharia** | Tempo de processamento/semana de dados | < 4h em GPU; < 90 min/semana em CPU | Profiling automático |
| | Backup completo bem-sucedido | 100% das semanas | Log de backup |

### B2.8.5 — Fronteira qualidade × custo

A fronteira Pareto do sistema, considerando hardware e software, será explorada em **B3 (trade-offs)**. Aqui registramos os pontos extremos:

- **Ponto mínimo viável (B-)**: MegaDetector + SpeciesNet + MiewID multispecies todos rodando em **CPU**, brute-force NumPy para galeria, SQLite local. Custo: zero infra adicional. Qualidade: meta-mínima de Rank-1 ≥ 0,75.
- **Ponto médio (B0)**: idem + **GPU dedicada simples** (GTX 1650 / RTX 3050). Custo: ~R$ 800–1.500 (placa) ou aluguel em cloud. Qualidade: meta de Rank-1 ≥ 0,85.
- **Ponto premium (B+)**: idem + fine-tuning local sobre PetFace + body-part approach do PPGNet-Cat + dashboard web em PostgreSQL + PostGIS. Qualidade: aproximar-se de Akbar 2025 (Rank-1 ≥ 0,90), com custo de tempo de desenvolvimento adicional.

O TCC, conforme cronograma, mira **B0 como meta de validação** e **B-** como **garantia mínima de entregabilidade**.

---

## B2.9 — Plano de testes no notebook do Pesquisador

### B2.9.1 — Hardware-alvo

> **[PLACEHOLDER-HARDWARE-NOTEBOOK]** — especificações exatas (CPU, RAM, GPU, disco, SO) do notebook do Pesquisador a serem registradas em `BlocoH_Hardware.md` após confirmação. As estimativas abaixo são **classes-alvo** com as quais o pipeline foi dimensionado:

- **CPU**: classe Intel Core i7 ou AMD Ryzen 7 (8–12 cores lógicos típicos de geração recente). [PLACEHOLDER-CPU]
- **RAM**: mínimo 16 GB; idealmente 32 GB. [PLACEHOLDER-RAM]
- **Disco**: SSD NVMe ≥ 256 GB para sistema + HD externo para arquivamento de mídias. [PLACEHOLDER-DISCO]
- **GPU**: cenário **A** sem GPU dedicada (iGPU Intel UHD/Iris ou AMD Radeon Vega apenas); cenário **B** com GPU dedicada simples (GTX 1650, RTX 3050 ou similar). Cenário B é **opcional**. [PLACEHOLDER-GPU]
- **SO**: Linux Mint (decisão prática do Pesquisador, conforme alinhamento_projeto_base).
- **Conectividade**: Wi-Fi/Ethernet USP padrão (irrelevante para processamento; relevante apenas para sincronização opcional e ingestão de dados de pontos NET/AC+NET).

### B2.9.2 — Estratégia de profiling

Três fases:

**Fase 1 — Smoke test (semana 1)**:
- Rodar **cada estágio isoladamente** em 100 imagens de dataset público (e.g., subset do WildlifeReID-10k ou camera-trap do AddaxAI demo).
- Medir: tempo médio, tempo p95, uso de RAM, uso de CPU.
- Critério de sucesso: pipeline roda em CPU sem crash; latências dentro do esperado pela Tabela B2.8-1.

**Fase 2 — Stress test (semana 2)**:
- Rodar pipeline completo em **1.000 imagens** simuladas (mix de gatos, vazios, humanos, outras espécies).
- Medir: throughput sustentado, comportamento térmico do laptop, vazamentos de RAM, integridade do SQLite após inserção em massa.
- Cenários de falha simulados: arquivo JPEG corrompido, EXIF ausente, frame com 0 detecções, frame com 50+ detecções (cenário improvável mas vale testar).

**Fase 3 — Operação real (mês 1+)**:
- Pipeline rodando em modo agendado (cron no Linux Mint) toda madrugada ou sob demanda após ingestão de cartões.
- Logging estruturado (JSONL) com tempo de cada estágio e contagem de erros.
- Dashboard local simples (notebook Jupyter recarregável) com KPIs B2.8-2.

### B2.9.3 — Cenários de stress específicos

| Cenário | Descrição | Comportamento esperado |
|---|---|---|
| **Surto de gatos** | 100 eventos em uma única madrugada num único ponto (improvável mas plausível em ponto novo) | Pipeline processa serialmente; aviso se demora total > 8h |
| **Cartão SD corrompido** | Apenas alguns JPEGs ilegíveis | Skip individual + log; pipeline continua |
| **Gato muito parecido com outro** | Embeddings com similaridade ambígua | Roteamento para fila de revisão humana; nenhum auto-assignment |
| **Novo indivíduo "burst"** | Vários novos gatos simultaneamente (ex.: nova ninhada) | Sistema gera múltiplos `cat_id` placeholder, voluntário renomeia |
| **Mudança de iluminação súbita** | Ponto P5 ganhou iluminação artificial recém-instalada → cores mudaram | Detecção de drift no embedding (similaridade média cai); flag para revisão de galeria |
| **GPU travada / driver crash** | Cenário B | Fallback automático para CPU + alerta no log |
| **SQLite locked** | Dois processos tentando escrever simultaneamente | WAL deve impedir; em último caso, fila de retry |

### B2.9.4 — Failover e robustez

Princípios:
1. **Idempotência**: re-rodar o pipeline na mesma imagem produz o mesmo `media_id` e não cria registros duplicados.
2. **Atomicidade**: cada evento é processado em transação; falha no meio reverte parcialmente.
3. **Resumibilidade**: pipeline mantém checkpoint `processed_media.txt`; retomada após crash não reprocessa.
4. **Auditabilidade**: cada `observation` tem `detector_name + version`, `classifier_name + version`, `reid_model_name + version`. Mudança de modelo gera nova observação, não sobrescreve.

### B2.9.5 — Plano de testes em quatro semanas

| Semana | Atividade | Entregável |
|---|---|---|
| **W1** | Smoke test individual de E1, E2, E3 em dataset público | Notebook com tempos e gráficos |
| **W2** | Stress test integrado em 1.000 imagens | Relatório de profiling + SQLite com dados realistas |
| **W3** | Primeira semana de captura real do Campus 2 + processamento | Primeiro `presence_events` real + auditoria humana de amostra |
| **W4** | Comparação MegaDetector v6 vs. YOLO11n e MiewID vs. MegaDescriptor no mesmo dataset | Tabela comparativa para inclusão em B3 (trade-offs) |

O detalhamento operacional (instalação, scripts, comandos exatos) é responsabilidade de **B5 (plano de validação e implementação)**, que herdará desta seção apenas os requisitos.

### B2.9.6 — Riscos de hardware e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Notebook do Pesquisador defeituoso ou indisponível por dias | Baixa | Alto | Backup do banco em nuvem (**[PLACEHOLDER-NUVEM-INSTITUCIONAL]**); outro PC (Orientador, laboratório ICMC) pode executar com mesmo código |
| Disco lota | Média | Médio | Monitor de espaço em disco; rotação de imagens antigas para HD externo |
| RAM insuficiente durante pico (modelo grande + galeria + inferência) | Baixa | Médio | Batch size = 1 em CPU; documentar requirement mínimo 16 GB |
| Driver de GPU desatualizado em cenário B | Média | Baixo | Fallback automático para CPU; uso de Docker para isolar ambiente |
| Atualização involuntária de modelo | Baixa | Alto | Pin de versão de modelo no `requirements.txt`; hash SHA-256 de cada modelo registrado em metadados |
| **Cartão SD corrompido ou perdido** | Média | Alto | Checksum SHA-256 na ingestão (B2.2.10.5); rodízio com cartão reserva no campo; **caderneta paralela** do Voluntário-AEX como evidência textual da janela perdida |
| **Voluntário-AEX indisponível para coleta na semana esperada** | Média | Médio | Pareamento com Voluntário reserva; em último caso, o Pesquisador faz a coleta; janela ampliada não quebra o sistema, só atrasa análises |

---

## Encerramento do B2

O B2 está completo em três partes:

- **Parte 1**: pipeline geral E0–E4 + aquisição (E0) + detecção (E1).
- **Parte 2**: classificação (E2) + re-identificação (E3, núcleo) + pré-processamento (E2.6).
- **Parte 3** (esta): persistência (E4) com Camtrap-DP + métricas + plano de testes.

**Decisões consolidadas ao longo de B2**:
1. Pipeline em 5 estágios + bloco transversal.
2. Aquisição com PIR + confirmador software (WiseEye-style), 1080p, 15 FPS, IR mono.
3. **MegaDetector v6** primário + **YOLO11n** alternativa leve para E1.
4. **SpeciesNet** + verificação binária local para E2.
5. **MiewID multispecies + MegaDescriptor baseline + PPGNet-Cat como referência** para E3; open-set obrigatório; meta Rank-1 ≥ 0,85, mAP ≥ 0,75.
6. **SQLite + Camtrap-DP schema + hnswlib** para E4; PostgreSQL como caminho de evolução.
7. Operação em **CPU é viável** para o piloto; GPU dedicada simples é otimização desejável.

**Próximo entregável**: **B3 — Análise de trade-offs (espaço de design)**. B3 explora a fronteira (energia × conectividade × custo × qualidade), retoma os perfis funcionais **OFF-SD / NET / AC / AC+NET** do B1 v2 e mapeia configurações arquiteturais alternativas para cada classe. É a seção que justificará, após o levantamento de campo do Pesquisador, por que cada um dos [~10 pontos estimados] receberá um perfil específico — com **OFF-SD como caso dominante esperado**.

---

## Fontes citadas nesta parte

### Persistência e padrões abertos
- **Bubnicki J. W. et al. (2024)** — *Camtrap DP: an open standard for the FAIR exchange and archiving of camera trap data*. **Remote Sensing in Ecology and Conservation** 10(3):283–295. [PDF USDA Forest Service](https://www.fs.usda.gov/rm/pubs_journals/2023/rmrs_2023_bubnicki_j001.pdf); [preprint ecoevorxiv](https://ecoevorxiv.org/repository/view/5593/); [specification camtrap-dp.tdwg.org](https://camtrap-dp.tdwg.org); [metadata spec](https://camtrap-dp.tdwg.org/metadata/).
- **GBIF (2024)** — *Best Practices for Managing and Publishing Camera Trap Data*. [docs.gbif.org/camera-trap-guide](https://docs.gbif.org/camera-trap-guide/); [Publishing Camtrap DP with IPTv3+](https://discourse.gbif.org/t/publishing-camtrap-dp-with-the-iptv3/5758).
- **camtrapdp R package (CRAN, 2026)** — [cran.r-project.org/web/packages/camtrapdp](https://cran.r-project.org/web/packages/camtrapdp/camtrapdp.pdf).
- **TRAPPER project (2025)** — *Open-source camera-trap management platform (Django + PostgreSQL + PostGIS + Celery)*. [GitLab](https://gitlab.com/trapper-project/trapper); [docs](https://trapper-project.readthedocs.io/en/latest/overview.html); **Bubnicki et al. (2025)** — *Trapper Citizen Science*: [ecoevorxiv 9876](https://ecoevorxiv.org/repository/view/9876/).
- **Wildlife Insights** — [wildlifeinsights.org](https://www.wildlifeinsights.org/home); [Standards](https://wildlifeinsights.org/standards); **Camelot Project**: [camelotproject.org](https://camelotproject.org).
- **dev.to (2025)** — *PostgreSQL vs SQLite*. [dev.to comparação](https://dev.to/lovestaco/postgresql-vs-sqlite-dive-into-two-very-different-databases-5a90).
- **Hacker News (2022)** — *SQLite vs Postgres for a local database*. [news.ycombinator.com](https://news.ycombinator.com/item?id=32676455).

### Índice vetorial (busca por similaridade)
- **Vectroid (2025)** — *HNSW vs FAISS: A Comprehensive Comparison*. [vectroid.com](https://vectroid.com/resources/hnsw-vs-faiss-comprehensive-comparison).
- **Zilliz (2024)** — *Faiss vs HNSWlib on Vector Search*. [zilliz.com blog](https://zilliz.com/blog/faiss-vs-hnswlib-choosing-the-right-tool-for-vector-search).
- **Marqo (2025)** — *Understanding Recall in HNSW Search*. [marqo.ai blog](https://www.marqo.ai/blog/understanding-recall-in-hnsw-search).
- **Milvus AI Quick Reference (2026)** — *Role of FAISS, HNSW, and ScaNN in AI Databases*. [milvus.io](https://milvus.io/ai-quick-reference/what-is-the-role-of-faiss-hnsw-and-scann-in-ai-databases).
- **Erik Bernhardsson — ann-benchmarks** — benchmarks oficiais ANN. [github.com/erikbern/ann-benchmarks](https://github.com/erikbern/ann-benchmarks).

### Latência e throughput
- **agentmorris/MegaDetector** — *Inference timing results MDv5*. [github.com/agentmorris/MegaDetector](https://github.com/agentmorris/MegaDetector/blob/main/megadetector.md) (RTX 4090: 17,6 img/s; RTX 3090: 11,4 img/s; Quadro P2000: 2,1 img/s; M3 MBP: 4,6 img/s).
- **Ultralytics docs (2025)** — *YOLO26 vs YOLO11: CPU inference benchmarks*. [docs.ultralytics.com](https://docs.ultralytics.com/compare/yolo26-vs-yolo11/) (YOLO11n: 56,1 ms CPU; YOLO26n: 38,9 ms).
- **Google Research / SpeciesNet (2025)** — *Where the wild things roam*. [research.google blog](https://research.google/blog/where-wild-things-roam-identifying-wildlife-with-speciesnet/) (~30K imagens/dia laptop padrão; ~250K/dia em GPU leve).
- **MLCommons MLPerf Inference v6.0 (abr 2026)** — [mlcommons.org](https://mlcommons.org/2026/04/mlperf-inference-v6-0-results/).
- **HuggingFace BVRA/MegaDescriptor-B-224** — [huggingface.co/BVRA/MegaDescriptor-B-224](https://huggingface.co/BVRA/MegaDescriptor-B-224) (Swin-B 109,1M params).
