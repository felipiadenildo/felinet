# B4 — Arquitetura de referência (Parte 1)

> **Posição na Etapa 2.** B1 modelou o contexto operacional (10 pontos, matriz P-α/β/γ/δ). B2 detalhou o pipeline lógico de visão computacional (E0–E4 + E2.6 transversal). B3 fez a análise de trade-offs e fechou o espaço de design com mapeamento ponto-a-ponto P1…P10 e cinco perfis na fronteira de Pareto. **B4 materializa essas decisões em uma arquitetura concreta**: camadas físicas, lógicas e de dados, diagramas-tipo por perfil de aquisição, dimensionamento do hardware central, schema de banco com diagrama ER, fluxo de dados E0→E4, e stack canônico de software.
>
> **Princípio condutor.** A arquitetura é organizada em **camadas independentes** (física, lógica, dados, apresentação) seguindo modelo de referência clássico de arquitetura de software ([Bass, Clements & Kazman 2021](https://www.pearson.com/store/p/software-architecture-in-practice/P200000005869)). Camadas comunicam-se por contratos bem definidos (formato de dados, APIs internas) — qualquer perfil de aquisição (A/B/C/D/E) ou variante de modelo (MiewID/MegaDescriptor/PPGNet) substitui um componente sem alterar as demais camadas. Esse desacoplamento é o que viabiliza o piloto comparativo de B5 e a evolução pós-TCC.
>
> **Estrutura desta entrega.** Parte 1 cobre **B4.1** (visão geral em camadas), **B4.2** (cinco diagramas físicos-tipo, um por perfil A/B/D/E1/E2) e **B4.3** (dimensionamento do servidor central — PC do Felipi). Parte 2 cobrirá **B4.4** (schema Camtrap-DP estendido + diagrama ER Chen), **B4.5** (diagrama de fluxo de dados E0→E4) e **B4.6** (stack canônico de software).

---

## B4.1 — Visão geral em camadas

### B4.1.1 — As quatro camadas do sistema

O sistema é organizado em quatro camadas com responsabilidades disjuntas. Essa separação é deliberada — qualquer mudança em uma camada (e.g., troca de modelo de re-ID, adição de um novo perfil de aquisição) afeta apenas essa camada.

**Tabela B4.1-1 — Camadas do sistema**

| Camada | Responsabilidade | Implementação | Onde roda |
|---|---|---|---|
| **C1 — Física (Edge)** | Sensoriamento, gravação, transferência de dados brutos | Câmeras dos 5 perfis + opcional Raspberry Pi local | Em campo (10 pontos do Campus 2) |
| **C2 — Lógica (Processamento)** | Pipeline E0–E4: ingestão, detecção, classificação, re-ID, pré-processamento | Python + PyTorch + OpenCV + ffmpeg | PC central do Felipi (batch noturno + ingestão diurna) |
| **C3 — Dados (Persistência)** | Armazenamento estruturado de eventos, mídia, embeddings, metadados de campo | SQLite + schema Camtrap-DP estendido + hnswlib | PC central |
| **C4 — Apresentação (Interface humana)** | Revisão de eventos, correção de re-ID, exportação para AEX | Interface Streamlit ou Flask local + dashboards | PC central, acessível pelo Felipi e pela AEX |

### B4.1.2 — Diagrama macro de camadas

```
┌─────────────────────────────────────────────────────────────────────┐
│                  C4 — APRESENTAÇÃO (PC central)                     │
│   Streamlit dashboard │ Revisão humana │ Exportação CSV/Camtrap-DP  │
└──────────────────┬──────────────────────────────┬───────────────────┘
                   │ leitura SQL                  │ escrita correções
                   ▼                              ▲
┌─────────────────────────────────────────────────────────────────────┐
│                  C3 — DADOS (PC central — SQLite)                   │
│  Tabelas Camtrap-DP estendidas │ Embeddings hnswlib │ Mídia em disco│
│  (deployments, media, observations, individuals, embeddings, …)     │
└──────────────────▲──────────────────────────────▲───────────────────┘
                   │ insere eventos               │ atualiza catálogo
                   │                              │
┌─────────────────────────────────────────────────────────────────────┐
│                  C2 — LÓGICA (PC central — Python)                  │
│   ┌────────┐  ┌────────┐  ┌─────────┐  ┌────────┐  ┌────────┐       │
│   │  E0    │→ │  E1    │→ │  E2.6   │→ │  E2    │→ │  E3    │       │
│   │ingest. │  │detect. │  │preproc. │  │class.  │  │re-ID   │       │
│   └────────┘  └────────┘  └─────────┘  └────────┘  └────────┘       │
│   MDv6 │ YOLO11n cascata │ SpeciesNet │ MiewID-msv3                  │
└──────────────────▲──────────────────────────────────────────────────┘
                   │ frames + metadados (JPEG burst, MP4 curto, RTSP pull)
                   │
┌─────────────────────────────────────────────────────────────────────┐
│              C1 — FÍSICA (Edge, 10 pontos do Campus 2)              │
│                                                                     │
│  Perfil A    Perfil B    Perfil C    Perfil D    Perfil E           │
│  trail+PIR   IP+Pi edge  Híbrido     consumer    OEM genérica       │
│  (P4, P6)    (P1, P10)   —           (P2, P5)    (P3, P7, P9)       │
│                                                                     │
│  Transferência: T-SD │ T-WiFi-sync │ T-RTSP │ T-USB-pulldown        │
└─────────────────────────────────────────────────────────────────────┘
```

### B4.1.3 — Contratos entre camadas

A separação só funciona se os contratos forem explícitos. B4.1.3 lista o que **cada camada entrega à seguinte** e como.

**Contrato C1 → C2 (Edge → Lógica).** Para qualquer perfil, C1 entrega **arquivos de mídia + metadado mínimo**:

| Item | Formato | Origem |
|---|---|---|
| Mídia | JPEG burst (A, C) │ MP4 curto (D, E1, E3) │ stream RTSP (B, E2, E4) | Câmera ou Pi local |
| Timestamp do evento | EXIF (A/B/C) │ nome de arquivo (D) │ filesystem (E) | Câmera ou Pi |
| `deployment_id` | String fixa por ponto (e.g., `usp_p3_2026`) | Ficha de campo |
| `acquisition_profile` | Enum {A, B, C, D, E1, E2, E3, E4} | Configuração de C2 |
| `transfer_mode` | Enum {T-SD, T-RTSP, T-WiFi-sync, T-USB-pulldown} | Configuração de C2 |

**Contrato C2 → C3 (Lógica → Dados).** C2 entrega **registros estruturados** para C3 inserir:

| Item | Tabela alvo | Conteúdo essencial |
|---|---|---|
| Evento de detecção | `observations` | `event_id`, `media_id`, `bbox`, `confidence`, `species`, `behavior_label?` |
| Mídia processada | `media` | `media_id`, `deployment_id`, `capture_timestamp`, `file_path`, `acquisition_profile` |
| Crop de re-ID | `crops` | `crop_id`, `observation_id`, `file_path`, `embedding_id` |
| Embedding | `embeddings` | `embedding_id`, `vector`, `model_name`, `model_version` |
| Indivíduo | `individuals` | `individual_id`, `display_name`, `first_seen`, `last_seen` |
| Match indivíduo↔crop | `individual_crops` | `individual_id`, `crop_id`, `match_confidence`, `assignment_method` |

**Contrato C3 → C4 (Dados → Apresentação).** C4 lê via SQL e expõe ao humano:

- **View "Eventos para revisar"**: observações com confidence baixa ou indivíduo ambíguo.
- **View "Indivíduos com poucas evidências"**: indivíduos com <5 crops associados (risco de erro).
- **View "Estatísticas semanais"**: contagem por ponto, perfil, espécie, indivíduo.

**Contrato C4 → C3 (correção humana).** Quando o humano corrige um match de re-ID, C4 escreve em `individual_crops` com `assignment_method = "human_review"` e `match_confidence = 1.0`, mantendo histórico do match automático original em `match_history` (auditoria).

### B4.1.4 — Princípio de invariância do pipeline lógico

Reafirmando decisão consolidada de B2 e B3: **a camada C2 (lógica) é a mesma para qualquer perfil de aquisição da camada C1**. O que muda entre perfis é apenas o **adaptador de ingestão E0** (sub-modos JPEG, MP4, RTSP) e a **calibração de E2.6** (com ou sem VMD calibrado). E1, E2, E3 são idênticos.

Esse princípio é o que viabiliza:
- **Piloto comparativo** entre perfis (mesmo pipeline, comparação justa).
- **Evolução pós-TCC** sem retrabalho (substituir um perfil A por D não afeta E1–E4).
- **Tolerância a falhas** (se um ponto falha, os outros 9 seguem operando porque cada um é independente).

---

## B4.2 — Diagramas físicos por perfil

Esta seção detalha **cinco diagramas-tipo** correspondentes aos perfis ativos no piloto: A, B, D, E1, E2. O Perfil C (híbrido PIR+Pi) é uma combinação de A+B e não recebe diagrama próprio para evitar duplicação.

### B4.2.1 — Diagrama-tipo Perfil A (Trail wildlife com PIR)

**Aplicação:** P4 (borda florestal nordeste), P6 (ponto remoto extremo).

```
                       ┌─────────────────────────────────┐
                       │  TRAIL CAMERA (Bushnell/Browning│
                       │  /WiseEye DIY)                  │
                       │                                 │
   Evento físico    →  │  ┌─────┐    ┌────────┐          │
   (gato passa)        │  │ PIR │ ─→ │ Câmera │          │
                       │  │     │    │ + IR LED│         │
                       │  └─────┘    └────┬────┘         │
                       │                  │              │
                       │                  ▼              │
                       │              ┌────────┐         │
                       │              │microSD │         │
                       │              │32–128GB│         │
                       │              └────────┘         │
                       │                                 │
                       │  Bateria 4× C ou pack 12V       │
                       │  Painel solar pequeno opcional  │
                       └──────────────┬──────────────────┘
                                      │
                                      │ Troca mensal do SD
                                      ▼
                            ┌──────────────────┐
                            │ Voluntário AEX   │
                            │ leva SD ao lab   │
                            └────────┬─────────┘
                                     │
                                     ▼  T-SD (mensal)
                            ┌──────────────────┐
                            │  PC central      │
                            │  Ingestão E0     │
                            └──────────────────┘
```

**Componentes físicos:**
- Câmera trail comercial (R$ 400–1.500) ou DIY WiseEye (R$ 200–400).
- microSD 64–128 GB (~R$ 50–100).
- Baterias internas (4–8× C ou D, ou pack 12V LiFePO4).
- Opcional: painel solar 6 W (~R$ 80–150) + controlador de carga.
- Gabinete IP65/IP66 (geralmente nativo nas trail cameras comerciais).

**Características operacionais:**
- Trigger por PIR (latência 0,3–2,5 s; WiseEye 0,44 s).
- Output: JPEG burst (3–10 frames) + opcional vídeo curto.
- Consumo: <2 Wh/dia em operação típica.
- Autonomia: meses sem manutenção energética.

### B4.2.2 — Diagrama-tipo Perfil B (IP camera + Raspberry Pi edge)

**Aplicação:** P1 (comedouro principal), P10 (stretch goal com Hailo).

```
                  ┌──────────────────────────────────────────┐
                  │                  GABINETE VEDADO IP65    │
                  │  ┌──────────────┐    ┌─────────────────┐ │
                  │  │ IP camera    │RTSP│ Raspberry Pi 5  │ │
                  │  │ (Intelbras/  │═══▶│ 4 GB RAM        │ │
                  │  │  Hikvision/  │    │ + SSD USB 256GB │ │
                  │  │  Dahua)      │    │ + opcional      │ │
                  │  │ 1080p H.264  │    │   Hailo-8L      │ │
                  │  │ ONVIF/RTSP   │    │   (Pi AI Kit)   │ │
                  │  └──────┬───────┘    └─────────┬───────┘ │
                  │         │ PoE ou 5V/12V       │         │
                  └─────────┼─────────────────────┼─────────┘
                            │                     │
                            ▼                     │ Wi-Fi do campus
                  ┌────────────────┐              │
                  │ Tomada AC 110V │              │
                  │ + nobreak      │              │
                  │ pequeno opc.   │              │
                  └────────────────┘              ▼
                                          ┌──────────────┐
                                          │ Roteador     │
                                          │ campus USP   │
                                          └──────┬───────┘
                                                 │
                                                 ▼  T-WiFi-sync diária
                                          ┌──────────────┐
                                          │ PC central   │
                                          │ Ingestão E0  │
                                          └──────────────┘
```

**Componentes físicos:**
- IP camera ONVIF/RTSP doada (R$ 0) ou comprada (R$ 150–600).
- Raspberry Pi 5 4 GB (R$ 600–800).
- SSD USB 256 GB ou microSD industrial 128 GB (R$ 100–200).
- Acelerador opcional Hailo-8L (R$ 500–800) **ou** Coral USB TPU (R$ 400).
- Gabinete IP65 com ventilação passiva.
- Cabo PoE injetor + switch ou alimentação 12V/5V separada.

**Stack de software no Pi:**
- Raspberry Pi OS 64-bit (Debian Bookworm).
- Frigate NVR (Docker) **ou** pipeline custom Python + OpenCV.
- YOLO11n via Ultralytics CLI ou PyTorch.
- `rsync` cron diário para sincronização com PC central.

**Características operacionais:**
- Streaming RTSP contínuo 24/7.
- VMD calibrado no Pi (MOG2 com background slow learning rate).
- Cascata YOLO11n local → MDv6 no PC central.
- Consumo: ~5–10 W contínuos (câmera + Pi).
- Buffer 24 h em SSD local.

### B4.2.3 — Diagrama-tipo Perfil D (IP cam consumer com PIR + SD)

**Aplicação:** P2 (comedouro secundário), P5 (variante com solar).

```
                       ┌─────────────────────────────────┐
                       │  IP CAMERA CONSUMER             │
                       │  (Tapo C400 / Reolink Argus /   │
                       │   eufy SoloCam)                 │
                       │                                 │
   Evento físico    →  │  ┌─────┐    ┌────────┐          │
   (gato passa)        │  │ PIR │ ─→ │ Câmera │          │
                       │  │6 lvl│    │ + IR   │          │
                       │  └─────┘    └────┬────┘         │
                       │                  │              │
                       │                  ▼              │
                       │              ┌────────┐         │
                       │              │microSD │         │
                       │              │ 64GB+  │         │
                       │              └────────┘         │
                       │                                 │
                       │  Bateria interna 5–10 Ah        │
                       │  + opcional painel solar 6W     │
                       │  (D3 com solar)                 │
                       │  IP65 nativo                    │
                       └──────────────┬──────────────────┘
                                      │
                                      │ Troca quinzenal/mensal
                                      ▼  T-SD
                            ┌──────────────────┐
                            │ Voluntário AEX   │
                            │ leva SD ao lab   │
                            └────────┬─────────┘
                                     ▼
                            ┌──────────────────┐
                            │  PC central      │
                            │  Ingestão E0     │
                            │  + ffmpeg frame  │
                            │    extractor     │
                            └──────────────────┘
```

**Componentes físicos:**
- Câmera consumer (R$ 200–500).
- microSD 64–256 GB (~R$ 50–100).
- Bateria interna do produto (5.000–10.000 mAh).
- Opcional: painel solar 6 W oficial do fabricante ou genérico USB (R$ 80–150).
- Gabinete IP65 nativo do produto.

**Configuração inicial obrigatória:**
1. Setup via app oficial em Wi-Fi temporário (Felipi).
2. **Teste de operação offline por 7 dias** (B5.2): cortar Wi-Fi, verificar gravação contínua em SD sem reconexão.
3. **Captura de tráfego com tcpdump** durante setup para identificar servidores chineses ("phone home") — registrar em apêndice de B5.

**Características operacionais:**
- Trigger PIR ~1–2 s.
- Output: MP4 H.264 curto (10–60 s configurável).
- Consumo: equivalente ao Perfil A (~mW em sleep).
- Autonomia: 120–180 dias por carga (≥4 meses sem manutenção).

### B4.2.4 — Diagrama-tipo Perfil E1 (IP cam genérica OEM, SD swap, sem Wi-Fi)

**Aplicação:** P3 (abrigo coberto noturno), P9 (comparação experimental).

```
                       ┌─────────────────────────────────┐
                       │  IP CAMERA GENÉRICA OEM         │
                       │  (Anyka AK3918EV300L /          │
                       │   V380 / ICSEE / similar)       │
                       │                                 │
   Streaming contínuo  │  ┌────────┐     ┌────────┐      │
   (sem PIR físico)    │  │ Sensor │ ──→ │ SoC    │      │
                       │  │ 1080p  │     │ ARM    │      │
                       │  └────────┘     │ + VMD  │      │
                       │                 │ firmware│     │
                       │                 └───┬────┘      │
                       │                     ▼           │
                       │                ┌────────┐       │
                       │                │microSD │       │
                       │                │64–256GB│       │
                       │                │ FAT32  │       │
                       │                └────────┘       │
                       │                                 │
                       │  Alimentação AC 5V/12V          │
                       │  via fonte original             │
                       │  Wi-Fi DESABILITADO             │
                       │  (validar em B5)                │
                       │  IP65 (verificar produto)       │
                       └──────────────┬──────────────────┘
                                      │
                                      ▼  Tomada AC 110V
                            ┌──────────────────┐
                            │ Tomada do        │
                            │ Campus 2         │
                            └──────────────────┘
                                      
                                      ┃ Troca quinzenal do SD
                                      ▼  T-SD
                            ┌──────────────────┐
                            │ Voluntário AEX   │
                            │ leva SD ao lab   │
                            └────────┬─────────┘
                                     ▼
                            ┌──────────────────┐
                            │  PC central      │
                            │  Ingestão E0     │
                            │  + ffmpeg frame  │
                            │    extractor     │
                            └──────────────────┘
```

**Componentes físicos:**
- Câmera OEM genérica (R$ 50–150).
- Fonte AC 5V/12V (geralmente incluída).
- microSD 64–256 GB (~R$ 50–100).
- Gabinete IP65 (verificar produto; muitas não são vedadas — adicionar caixa externa).

**Configuração inicial obrigatória (B5.2):**
1. Conectar à rede Wi-Fi temporária para configuração via app proprietário (V380, ICSEE).
2. **Habilitar gravação contínua local em SD** com retenção FIFO.
3. **Configurar NTP server local** (se firmware suportar) ou desabilitar overlay de timestamp (usar nome de arquivo).
4. **Desabilitar todas as funções de nuvem**.
5. **Validar acesso RTSP** com VLC: `rtsp://admin:senha@IP:554/live/ch0` deve responder.
6. **Desconectar do Wi-Fi**: confirmar que câmera continua gravando em SD sem reconexão.
7. **Drift de relógio**: comparar timestamp gravado vs. real após 7 dias; documentar deriva.

**Características operacionais:**
- VMD em software (firmware OEM) — qualidade variável.
- Output: clipes MP4 H.264 disparados por VMD.
- Consumo: ~1,5–3 W contínuos (SoC sempre ativo).
- Inviabiliza bateria/solar; só funciona com AC.

### B4.2.5 — Diagrama-tipo Perfil E2 (IP cam genérica OEM, RTSP pull com Wi-Fi)

**Aplicação:** P7 (próximo estacionamento ICMC com Wi-Fi do campus).

```
                  ┌──────────────────────────────────────────┐
                  │                  GABINETE EXTERNO IP65   │
                  │  ┌──────────────┐                        │
                  │  │ IP camera    │ RTSP contínuo          │
                  │  │ OEM genérica │ /live/ch0 (HD)         │
                  │  │ (Anyka/V380) │                        │
                  │  │ 1080p H.264  │                        │
                  │  │ ONVIF/RTSP   │                        │
                  │  └──────┬───────┘                        │
                  │         │ 5V/12V AC                      │
                  └─────────┼────────────────────────────────┘
                            │
                            │ Wi-Fi do campus (VLAN isolada)
                            ▼
                  ┌────────────────┐
                  │ Roteador campus│
                  │ USP + VLAN     │
                  │ "camera-iso"   │
                  │ (sem internet) │
                  └───────┬────────┘
                          │ RTSP via LAN/Wi-Fi
                          ▼
                  ┌──────────────────────────────────┐
                  │  PC central — ffmpeg RTSP puller │
                  │  cron: a cada 10 min,            │
                  │  ffmpeg -i rtsp://… -t 600 …     │
                  │  → arquivo segmentado MP4        │
                  └──────────────┬───────────────────┘
                                 ▼
                  ┌──────────────────────────────────┐
                  │  Ingestão E0 + frame extractor   │
                  │  + VMD secundário no PC          │
                  │  (filtrar FP do firmware)        │
                  └──────────────────────────────────┘
```

**Componentes físicos:**
- Câmera OEM genérica (R$ 50–150).
- Fonte AC 5V/12V.
- Gabinete IP65 externo (R$ 30–80).
- **Sem microSD obrigatório** (gravação no PC central, não na câmera) — pode adicionar SD como redundância de fallback.

**Configuração de rede crítica:**
- **VLAN isolada `camera-iso`** sem saída para internet (mitiga "phone home").
- **DHCP fixo** para garantir IP estável da câmera.
- **Firewall regra**: PC central pode acessar câmera; câmera não acessa nada (incluindo internet).
- **NTP server local** apontado para PC central (sincroniza timestamp).

**Stack de software no PC central (específico para E2):**
- Cron job a cada 10 min: `ffmpeg -rtsp_transport tcp -i rtsp://user:pass@cam_ip/live/ch0 -t 600 -c copy /data/p7/raw/$(date +%s).mp4`.
- Ou: pipeline contínuo via `go2rtc` ou `Frigate` rodando no PC central.

**Características operacionais:**
- Streaming contínuo via RTSP — sem perda por trigger lento.
- VMD do firmware da câmera é descartado; **VMD do PC central** (OpenCV MOG2) substitui — qualidade superior.
- Banda: ~1–5 Mbps por câmera.
- Risco: corte de Wi-Fi do campus → buffer SD funciona como fallback se configurado.

### B4.2.6 — Resumo comparativo dos diagramas físicos

**Tabela B4.2-1 — Síntese dos cinco diagramas-tipo**

| Perfil | Componente principal | Compute local | Energia | Transferência | Custo total típico |
|---|---|---|---|---|---|
| **A** | Trail wildlife | Nenhum | Bateria/solar | T-SD mensal | R$ 250–1.600 |
| **B** | IP cam + Pi 5 | Pi 5 (+ Hailo) | AC contínuo | T-WiFi-sync diária | R$ 750–2.400 |
| **D** | Consumer + PIR + SD | Nenhum | Bateria/solar | T-SD quinzenal | R$ 300–650 |
| **E1** | OEM genérica + SD | Nenhum | AC contínuo | T-SD quinzenal | R$ 100–250 |
| **E2** | OEM genérica + RTSP | PC central | AC contínuo | T-RTSP contínuo | R$ 80–230 |

---

## B4.3 — Dimensionamento do servidor central (PC do Felipi)

### B4.3.1 — Carga de trabalho consolidada

O PC central recebe e processa dados de **todos os 10 pontos**. A carga consolidada é:

**Tabela B4.3-1 — Carga de trabalho diária estimada**

| Origem | Volume diário típico | Pico semanal |
|---|---|---|
| **Ingestão T-SD (5 pontos: P2, P3, P4, P5, P6, P9)** | 0 diário; lote quinzenal/mensal | ~5–20 GB raw por evento de coleta |
| **Ingestão T-RTSP contínua (P7)** | 1 câmera × 1.5 Mbps × 86.400 s = ~16 GB/dia raw H.264 | 110 GB/sem |
| **Ingestão T-WiFi-sync (P1, P10)** | ~500 MB/dia por ponto (já filtrado pelo Pi) | 7 GB/sem |
| **Pipeline E1 (MDv6) batch noturno** | 5.000 frames/sem (estimativa B2.8) × 200 ms CPU = ~17 min total | Cabe em janela de 4 h |
| **Pipeline E2 (SpeciesNet) batch noturno** | 5.000 frames × ~500 ms CPU = ~42 min | Cabe |
| **Pipeline E3 (MiewID) batch noturno** | ~500 crops confirmados × 300 ms = ~2,5 min | Trivial |
| **Indexação hnswlib** | ~500 embeddings/sem × <10 ms = ~5 s | Trivial |

**Janela operacional alvo:** processamento completo de uma semana inteira de dados em **uma noite de 8 h** (e.g., 22 h → 06 h). Folga >5× verificada em B2.8.

### B4.3.2 — Dimensionamento de CPU

**Requisitos por subsistema concorrente:**

| Subsistema | Threads CPU em pico | Justificativa |
|---|---|---|
| **ffmpeg RTSP pull P7** | 1–2 threads contínuos | Decodificação H.264 (com aceleração de hardware se i7 tiver iGPU) |
| **Backup local (rsync)** | <1 thread | I/O bound |
| **Pipeline batch noturno (E1+E2+E3)** | **All cores** durante 1–2 h | MDv6 + SpeciesNet + MiewID em paralelo onde possível |
| **Streamlit dashboard** | <1 thread médio | Web app leve |
| **SQLite queries** | <1 thread | In-memory cache + WAL |

**Especificação recomendada:** Intel i7 (8ª–13ª geração) com **iGPU UHD ou Iris Xe** habilitada (para `h264_qsv` ou `vaapi` acelerar ffmpeg). **Mínimo 4 cores físicos / 8 threads**. **8 cores / 16 threads recomendado** para folga em batch noturno e ingestão concorrente.

**Verificação:** o hardware do Felipi (i7) atende sem necessidade de GPU dedicada. **GPU NVIDIA dedicada (mesmo simples como RTX 3050)** reduziria o tempo de batch em ~3–5× mas **não é requisito** — é stretch goal.

### B4.3.3 — Dimensionamento de RAM

**Requisitos:**

| Subsistema | RAM em pico |
|---|---|
| **OS (Ubuntu 22.04/24.04 ou Windows)** | 1–2 GB |
| **MDv6 modelo carregado em RAM** | ~800 MB |
| **SpeciesNet modelo carregado** | ~600 MB |
| **MiewID-msv3 carregado** | ~300 MB |
| **ffmpeg buffers RTSP** | ~200 MB por stream |
| **SQLite WAL + page cache** | ~500 MB |
| **Streamlit + Python interpreter** | ~500 MB |
| **Buffer livre para batch + frames in-flight** | ~2 GB |

**Total estimado:** ~6 GB em pico de batch noturno.

**Especificação recomendada:** **mínimo 16 GB RAM**; **32 GB recomendado** para folga e possível execução paralela de modelos (em vez de sequencial). A documentação do Frigate ([recommended hardware](https://docs.frigate.video/frigate/planning_setup/)) aponta 16 GB como **mínimo seguro** quando há enrichments — nosso caso tem três modelos rodando em batch, então 16 GB é o piso.

### B4.3.4 — Dimensionamento de armazenamento

**Cálculo de volume mensal:**

| Origem | Volume mensal estimado |
|---|---|
| P1 (Perfil B, filtrado pelo Pi) | ~15 GB/mês |
| P2 (Perfil D, eventos PIR) | ~5 GB/mês |
| P3 (Perfil E1, gravação VMD) | ~30 GB/mês (FP altos sem calibração) |
| P4 (Perfil A, trail) | ~3 GB/mês |
| P5 (Perfil D3, trail+solar) | ~3 GB/mês |
| P6 (Perfil A, remoto) | ~2 GB/mês |
| P7 (Perfil E2, RTSP contínuo raw) | ~500 GB/mês raw → ~50 GB pós-filtragem |
| P8 (Perfil B ou D) | ~10 GB/mês |
| P9 (Perfil E1 ou D) | ~15 GB/mês |
| P10 (Perfil B + Hailo) | ~10 GB/mês |
| **Total raw bruto** | ~640 GB/mês (dominado por P7 RTSP) |
| **Total pós-filtragem (eventos com gato)** | ~140 GB/mês |
| **Banco SQLite + embeddings + metadata** | <2 GB/mês |

**Política de retenção** (consolidação de B2 Parte 3):
- **Raw bruto** (vídeos completos, frames descartados): retenção 30 dias em disco, depois descarte.
- **Eventos com gato (mídia confirmada)** e crops associados: **retenção indefinida** (são o produto científico).
- **Embeddings**: indefinida.
- **Banco de dados**: indefinida + backup semanal.

**Especificação recomendada:**
- **HD 4 TB interno ou USB 3.0** (~R$ 600–900) para storage primário.
- **SSD 500 GB NVMe ou SATA** (~R$ 250–400) para banco SQLite + cache + OS.
- **Backup**: HD externo 2 TB rotativo (~R$ 400) com `rsync` ou `restic` semanal.

### B4.3.5 — Dimensionamento de rede

**Largura de banda do PC central:**

| Origem | Banda contínua |
|---|---|
| RTSP pull P7 | ~1,5 Mbps |
| RTSP pull P10 (se for usar) | ~1,5 Mbps |
| `rsync` diário dos Pis (P1, P10) | Pico de ~50 Mbps por 5–10 min/dia |
| Acesso humano (Streamlit) | Trivial |

**Especificação:** Wi-Fi do campus (802.11ac) ou cabo Ethernet 100 Mbps são suficientes. Sem requisitos especiais.

### B4.3.6 — Configuração de referência consolidada

**Tabela B4.3-2 — Hardware central recomendado**

| Componente | Mínimo | Recomendado | Stretch |
|---|---|---|---|
| **CPU** | Intel i7 4 cores 8 threads + iGPU | Intel i7 8 cores 16 threads + Iris Xe | i9 + RTX 3050/4060 |
| **RAM** | 16 GB DDR4 | 32 GB DDR4 | 64 GB |
| **Armazenamento primário** | HD 2 TB | HD 4 TB + SSD 500 GB NVMe | NAS 8 TB RAID 1 |
| **Armazenamento backup** | HD 1 TB externo | HD 2 TB externo + cron rsync | NAS secundário |
| **Rede** | Ethernet 100 Mbps | Ethernet Gigabit | — |
| **OS** | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS | — |
| **GPU dedicada** | Nenhuma (CPU é OK) | Nenhuma | RTX 3050 (~R$ 1.500 caso doação) |

**Custo total do hardware central** (cenário recomendado, comprado do zero): ~R$ 4.500–6.000. **Cenário do Felipi**: PC existente i7 (≥16 GB, com upgrade de armazenamento opcional ~R$ 600–900 para HD 4 TB) atende perfeitamente.

### B4.3.7 — Considerações de operação

1. **Energia**: PC central conectado a **nobreak pequeno** (~R$ 300–500) para evitar perda de batch noturno em pico de chuva.
2. **Refrigeração**: i7 com cooler stock é suficiente; ambiente do escritório do Felipi com ar-condicionado ou ventilação adequada.
3. **Monitoramento**: log de uso de CPU/RAM em cron diário com `sar` ou `prometheus_node_exporter` (stretch).
4. **Updates**: política conservadora — `unattended-upgrades` apenas para segurança; updates de PyTorch/CUDA apenas em janela manual.

---

## Encerramento da Parte 1 de B4

Esta Parte 1:
- estruturou o sistema em **quatro camadas** (C1 física / C2 lógica / C3 dados / C4 apresentação) com diagrama macro e contratos explícitos entre camadas (B4.1);
- entregou **cinco diagramas físicos-tipo** detalhados, um por perfil de aquisição ativo no piloto (A, B, D, E1, E2), com componentes, configuração inicial obrigatória e características operacionais (B4.2);
- dimensionou o **servidor central** (PC do Felipi) em CPU, RAM, armazenamento e rede, com cenários mínimo/recomendado/stretch e custo estimado — confirmando que o hardware existente do Felipi atende sem necessidade de GPU dedicada (B4.3).

**Próxima entrega (B4 Parte 2)**:
- **B4.4** — Schema Camtrap-DP estendido + diagrama ER em notação Chen.
- **B4.5** — Diagrama de fluxo de dados E0→E4 com origens por perfil (DFD).
- **B4.6** — Stack canônico de software (Python, OpenCV, PyTorch, SQLite, hnswlib, ffmpeg, libs Camtrap-DP).

---

## Fontes citadas nesta parte

### Arquitetura de software
- **Bass L., Clements P., Kazman R. (2021)** — *Software Architecture in Practice*, 4ª ed., Addison-Wesley. [Pearson](https://www.pearson.com/store/p/software-architecture-in-practice/P200000005869).

### Hardware central e Frigate
- **Frigate NVR — Recommended hardware**. [docs.frigate.video/frigate/hardware](https://docs.frigate.video/frigate/hardware/).
- **Frigate NVR — Planning a new installation**. [docs.frigate.video/frigate/planning_setup](https://docs.frigate.video/frigate/planning_setup/).
- **r/frigate_nvr (2025)** — *For 8 cameras, what are suggested CPUs/RAM*. [reddit.com/r/frigate_nvr](https://www.reddit.com/r/frigate_nvr/comments/1izezbl/for_8_cameras_what_are_suggested_cpusram/).
- **AlexxIT/go2rtc (2025)** — *Using ffmpeg filter_complex to split output*. [github.com/AlexxIT/go2rtc/issues/1546](https://github.com/AlexxIT/go2rtc/issues/1546).

### Raspberry Pi 5 (Perfil B)
- **Raspberry Pi forum (2024)** — *Pi 5: increase of power consumption from 2.2W to 2.7W*. [forums.raspberrypi.com](https://forums.raspberrypi.com/viewtopic.php?t=364931).
- **r/homelab (2025)** — *Raspberry Pi 5 8 GB power consumption*. [reddit.com/r/homelab](https://www.reddit.com/r/homelab/comments/1hzlc1o/my_raspberry_pi_5_8_gb_power_consumption/).

### ffmpeg RTSP (Perfil E2)
- **Reddit r/ffmpeg (2024)** — *High CPU utilization with FFMPEG during video stream*. [reddit.com/r/ffmpeg](https://www.reddit.com/r/ffmpeg/comments/1bzu02f/high_cpu_utilization_with_ffmpeg_during_video/).
- **Stack Overflow (2020)** — *ffmpeg RTSP streams to RGB24 using GPU*. [stackoverflow.com](https://stackoverflow.com/questions/59999453/ffmpeg-rtsp-streams-to-rgb24-using-gpu).
