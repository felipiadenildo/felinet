# B3 — Análise de trade-offs e espaço de design (Parte 2)

> **Posição na Etapa 2.** Esta é a continuação direta de **B3 Parte 1**. A Parte 1 cobriu o método (B3.1), o front-end de aquisição (B3.2 — duas categorias × cinco perfis A/B/C/D/E na fronteira de Pareto) e o detector genérico (B3.3 — cascata YOLO11n → MegaDetector v6). Esta Parte 2 cobre:
>
> - **B3.4** — Modelo de re-identificação (eixo E-3): MiewID-msv3 × MegaDescriptor × PPGNet-Cat × PetFace fine-tune.
> - **B3.5** — Locus de computação (E-4) cruzado com persistência (E-5) e transferência (E-6).
> - **B3.6** — **Mapeamento ponto-a-ponto P1…P10**: tabela operacional consolidando perfil de aquisição + modelos + locus + frequência de coleta para cada um dos 10 pontos. É o input direto para **B4 (Arquitetura de referência)**.
>
> **Lembrete sobre escopo.** B3 mapeia trade-offs com base em **literatura, benchmarks publicados e especificações de fabricantes** — os números aqui são estimativas e referências bibliográficas, não medições próprias. A **execução experimental** (rodar modelos sobre datasets, gerar gráficos comparativos, calcular Rank-1 real, fazer piloto de campo entre perfis) acontece em **B5 (Plano de validação e implementação)**. Veja B5.1 para o protocolo de avaliação offline em datasets e B5.2 para o protocolo de piloto em campo.

---

## B3.4 — Eixo E-3: Modelo de re-identificação

### B3.4.1 — O problema específico de E-3 no nosso contexto

Recapitulando B2 Parte 2: E-3 é o estágio mais crítico do pipeline e o que mais sofre com o cenário "gato doméstico/feral em colônia urbana fechada". O problema técnico é:

> Dado um *crop* de gato vindo de E-1/E-2, atribuir a esse crop um **identificador individual** consistente — seja a um indivíduo já conhecido na base, seja a um novo indivíduo se ainda não foi visto.

Três restrições do nosso cenário tornam o problema **mais difícil** que o caso médio da literatura wildlife:

1. **Open-set obrigatório.** A população da colônia muda: novos gatos entram (filhotes, abandonos, dispersão de outras colônias) e antigos saem (adoção, óbito, dispersão). O modelo não pode assumir conjunto fechado — precisa decidir "este é o gato X" **ou** "este é alguém novo". Métricas BAKS/BAUS de [Cermak et al. 2024 (WACV)](https://openaccess.thecvf.com/content/WACV2024/papers/Cermak_WildlifeDatasets_An_Open-Source_Toolkit_for_Animal_Re-Identification_WACV_2024_paper.pdf) endereçam exatamente isso.

2. **Pose variável e oclusão constante.** Gato comendo, gato passando, gato sentado, gato em postura defensiva, gato com cauda erguida em direção à câmera. Modelos baseados em face (PetFace) lidam mal com isso; modelos baseados em corpo (MiewID, MegaDescriptor) lidam melhor mas exigem visibilidade do corpo.

3. **Poucos indivíduos, muitas imagens por indivíduo (eventualmente).** Cerca de **50 gatos**, mas potencialmente **centenas de eventos por gato/mês** se o ponto de alimentação for frequente. Isso favorece abordagens que aprendem **representação** (embedding) sobre abordagens que classificam (softmax sobre N classes fixas) — porque a representação generaliza para novos indivíduos.

### B3.4.2 — Candidatos e seu posicionamento

**Tabela B3.4-1 — Candidatos a re-ID (E-3)**

| Modelo | Arquitetura | Treino | Foco em gato? | Open-set nativo? | Tamanho do modelo | Disponibilidade |
|---|---|---|---|---|---|---|
| **MiewID-msv3** | EfficientNetV2-L + sub-center ArcFace, embedding 512-d, imagens 440×440 | 49 espécies / 37k indivíduos / 225k imagens; treinado para **identificação multispecies** ([Otarashvili et al. 2024, arXiv:2412.05602](https://arxiv.org/abs/2412.05602)) | Não específico, mas treino inclui felinos | **Sim** — embedding-based; novo indivíduo é só uma nova entrada na DB | 51,1 M params; 24,4 GMACs | HF [conservationxlabs/miewid-msv3](https://huggingface.co/conservationxlabs/miewid-msv3) |
| **MegaDescriptor-L** | Swin-L/p4-w12-384, embedding via ArcFace | 29 datasets wildlife combinados; foundation model wildlife ([Cermak et al. 2024 WACV](https://openaccess.thecvf.com/content/WACV2024/papers/Cermak_WildlifeDatasets_An_Open-Source_Toolkit_for_Animal_Re-Identification_WACV_2024_paper.pdf); [arXiv:2311.09118](https://arxiv.org/abs/2311.09118)) | Não específico | **Sim** — embedding-based | ~200 M params | HF; toolkit [wildlife-tools](https://github.com/WildlifeDatasets/wildlife-tools) |
| **PPGNet-Cat** | PPGNet (part-pose guided) adaptada de re-ID de tigres Amur para gatos ferais; ResNet50 backbone | Dataset privado do paper + Victoria National Parks (público) | **Sim** (treinado em gatos ferais) | Parcial (precisa adaptar threshold) | ~25 M params (ResNet50) | GitHub [victorcaquilpan/PPGNet-Cat](https://github.com/victorcaquilpan/PPGNet-Cat); paper [Akbar 2025, arXiv:2507.11575](https://arxiv.org/abs/2507.11575). **mAP 0,86; Rank-1 0,95; Rank-5 0,975** sobre 10 indivíduos não vistos |
| **PetFace (joint-trained)** | ArcFace + multi-family training | PetFace: **257.484 indivíduos**, 13 famílias animais (inclui gato), 319 categorias de raça ([Inoue et al. 2024 ECCV Oral](https://arxiv.org/abs/2407.13555); [project page](https://dahlian00.github.io/PetFacePage/)) | **Sim** (categoria cat com fine-grained labels) | **Sim** — verification para unseen | Variável (ArcFace + backbone) | GitHub [mapooon/PetFace](https://github.com/mapooon/PetFace) |
| **Baseline body-parts (Akbar 2025)** | 4× ResNet50 paralelos (corpo, perna traseira, perna dianteira, cauda) → concat → FC | 10 gatos ferais com câmera trap | **Sim** (gato feral, camera-trap) | Classificação fechada (10 classes) | 4×25 M = ~100 M params | Paper [Akbar 2025, ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1574954125002675) |

### B3.4.3 — Análise comparativa por dimensão

**Dimensão 1 — Generalização para novos indivíduos (open-set)**

| Modelo | Comportamento esperado |
|---|---|
| **MiewID-msv3** | **Melhor** — treino multispecies com 37k indivíduos diferentes força embedding genérico. Otarashvili et al. reportam ganho de **19,2 % em Rank-1 média** sobre MegaDescriptor em espécies não-vistas ([arXiv:2412.05602](https://arxiv.org/abs/2412.05602)). |
| **MegaDescriptor-L** | Boa, foundation model com 29 datasets. Baseline natural de comparação. |
| **PPGNet-Cat** | **Specific-purpose**: treinado só em gato. Mais alta acurácia *intra-distribuição* (mAP 0,86 em gatos ferais), mas extrapolação para novos gatos do nosso conjunto é incerta sem fine-tune com nossos dados. |
| **PetFace** | Open-set por construção (verification task). Backbone treinado em **257k indivíduos** ajuda na generalização. |
| **Body-parts (Akbar)** | **Fechada** — desenhada para 10 indivíduos pré-rotulados. Não generaliza sem retreino. Inviável para open-set. |

**Dimensão 2 — Qualidade reportada em conjuntos de teste**

A literatura reporta números **em datasets diferentes**, então comparação direta é arriscada. Síntese honesta do que está disponível:
- **PPGNet-Cat** em 10 gatos ferais não-vistos: **mAP 0,86 / Rank-1 0,95** ([Akbar 2025](https://arxiv.org/abs/2507.11575)).
- **MegaDescriptor-L** em 29 datasets wildlife: SOTA consistente, supera CLIP e DINOv2 em todos os 29 ([Cermak 2024](https://openaccess.thecvf.com/content/WACV2024/papers/Cermak_WildlifeDatasets_An_Open-Source_Toolkit_for_Animal_Re-Identification_WACV_2024_paper.pdf)).
- **MiewID-msv3** em espécies não-vistas: top-1 médio **+19,2 %** sobre MegaDescriptor ([Otarashvili 2024](https://arxiv.org/abs/2412.05602)).
- **PetFace** em verificação cat unseen: melhor separação positivo/negativo que MegaDescriptor e CLIP no plot de similaridade (sem número Rank-1 direto comparável).

**Comparação real só será possível em B5.1** — rodando os quatro modelos sobre o mesmo conjunto (provavelmente PetFace-cat + nosso dataset piloto USP) com split temporal idêntico. Os números acima são apenas balizadores.

**Dimensão 3 — Custo computacional e viabilidade de inferência**

| Modelo | Latência por imagem (CPU/GPU leve) | Memória | Aderência ao PC do Felipi (i7 sem GPU dedicada) |
|---|---|---|---|
| **MiewID-msv3** | ~200–400 ms CPU; ~30–60 ms RTX 3050 | ~200 MB para o modelo; embedding 512-d (~2 KB/imagem) | **Viável em batch noturno** — extração de embedding de 5k imagens leva ~30–60 min em CPU |
| **MegaDescriptor-L (Swin-L)** | ~400–800 ms CPU; ~60–100 ms GPU | ~800 MB; embedding 1024–1536-d | **Pesado** mas viável para batch noturno; tempo total em PC sem GPU é cerca de 2× MiewID |
| **PPGNet-Cat (ResNet50 + part guidance)** | ~150–300 ms CPU; ~25–50 ms GPU | ~100 MB | **Mais leve** — bom candidato se PPGNet sobrar como winner final |
| **PetFace fine-tune** | Depende do backbone; com ArcFace + ResNet50 ~100–200 ms CPU | ~100 MB | **Leve** |
| **Body-parts (4× ResNet50)** | ~600 ms CPU (4× ResNet50 sequencial) | ~400 MB | Pesado relativo ao ganho |

**Dimensão 4 — Esforço de implementação e curva de aprendizado**

| Modelo | Esforço |
|---|---|
| **MiewID-msv3** | Baixo — modelo no HuggingFace, exemplo de uso completo, integra com `wildlife-tools` |
| **MegaDescriptor-L** | Baixo — mesma stack `wildlife-tools` |
| **PPGNet-Cat** | **Médio–alto** — exige anotação de keypoints (cabeça, ombros, ancas, cauda) no nosso dataset; pipeline de extração de body-parts não é plug-and-play |
| **PetFace fine-tune** | Médio — exige preparar dataset cat-specific no formato do repo; fine-tune leva horas em GPU; sem GPU é problemático |
| **Body-parts (Akbar)** | Alto — paper descreve abordagem mas requer reimplementação completa |

### B3.4.4 — Análise de Pareto e decisão consolidada

**Tabela B3.4-2 — Re-ID na fronteira de Pareto**

| Modelo | Qualidade | Generalização open-set | Latência | Esforço | Veredito |
|---|---|---|---|---|---|
| **MiewID-msv3** | **Alta** (multispecies SOTA recente) | **Excelente** | Boa | **Baixo** | **Primário recomendado** |
| **MegaDescriptor-L** | Alta (foundation reference) | Boa | Média | Baixo | **Baseline obrigatório** para comparação |
| **PPGNet-Cat** | Alta intra-distribuição | Incerta | Boa | Médio–alto | **Referência cat-specific** (validar com fine-tune nosso dataset) |
| **PetFace fine-tune** | Alta (cat-specific após FT) | Boa | Boa | Médio | **Exploração se PPGNet falhar** |
| **Body-parts (Akbar)** | Alta intra-distribuição | **Inviável open-set** | Pesada | Alto | **Dominado** — descartado |

**Recomendação para o TCC:**
- **E-3 primário**: **MiewID-msv3** — pelo argumento de generalização multispecies recente (2024), boa latência em CPU, esforço de integração baixo, e por já ter sido apontado em B2 Parte 2 como primário do pipeline lógico. **Mantém-se.**
- **E-3 baseline de comparação**: **MegaDescriptor-L** — para reportar dois números no relatório final e demonstrar análise comparativa.
- **E-3 referência cat-specific**: **PPGNet-Cat** — reproduzir o número de Akbar 2025 no nosso dataset (com fine-tune) como benchmark superior alcançável; se nosso piloto entregar **mAP < 0,75** com MiewID, fazer fine-tune do PPGNet para tentar bater meta.
- **Descartados**: Body-parts Akbar (não generaliza open-set), PetFace original sem fine-tune (treino majoritariamente em raças puras de pet; gatos ferais USP têm distribuição visual diferente).

**Meta operacional do TCC** (reafirmando B2 Parte 3): **mAP ≥ 0,75 e Rank-1 ≥ 0,85 sobre split temporal**, com BAKS/BAUS média harmônica ≥ 0,80.

### B3.4.5 — Eixo ortogonal: face approach vs. body approach

Discussão herdada de B2 Parte 2 que B3 reafirma como **decisão consolidada**:

- **Face approach** (PetFace original, FaceNet-style): exige rosto frontal, falha em câmera-trap com pose arbitrária. **Descartado como pipeline primário.**
- **Body approach** (MiewID, MegaDescriptor): aceita qualquer pose com corpo visível. **Escolhido.**
- **Body-part approach** (PPGNet-Cat, Akbar): usa partes específicas (cabeça, perna, cauda). **Promissor mas com custo de anotação.**

### B3.4.6 — Implicações da escolha sobre o pipeline lógico

A decisão "MiewID primário + MegaDescriptor baseline + PPGNet referência" não muda E-1 nem E-2, mas afeta E-2.6 (pré-processamento de re-ID):

1. **Resize 440×440** (input nativo do MiewID-msv3) precisa ser aplicado no E-2.6, com letterbox para preservar aspect ratio.
2. **Embedding cache** em SQLite + hnswlib (decisão de B2 Parte 3) precisa armazenar **três embeddings por crop** durante o piloto comparativo (um por modelo). Após escolha consolidada em B6, apenas o vencedor é mantido na operação contínua.
3. **Thresholding open-set**: cada modelo tem seu threshold próprio (calibrar em validação). MiewID típico: cosine similarity > 0,55. MegaDescriptor: > 0,50. Detalhes em B5.

---

## B3.5 — Eixos E-4, E-5, E-6: Locus de computação, persistência, transferência

### B3.5.1 — Por que tratar os três eixos juntos

Os três eixos têm acoplamento forte: **onde** processo determina **onde** persisto e como **transfiro** os resultados. Tratar separadamente leva a configurações fisicamente impossíveis (e.g., "processo edge, persisto central, sem rede"). Aqui agrupamos os três para preservar consistência.

### B3.5.2 — Eixo E-4: Locus de computação

**Variantes:**

- **L-A — Centralizada total**: toda inferência roda no PC do Felipi (i7, opcionalmente com GPU dedicada simples). Pontos de campo só capturam e transferem raw data (imagens, vídeos, RTSP streams).
- **L-B — Edge total**: cada ponto roda pipeline completo localmente (Raspberry Pi 4/5 + opcional acelerador Hailo-8L ou Coral TPU). Apenas resultados estruturados (detecções, embeddings) são transferidos.
- **L-C — Híbrida**: ponto roda filtragem leve (motion + YOLO11n ou MegaDetector-Compact); PC central roda detecção pesada (MDv6) + classificação (SpeciesNet) + re-ID (MiewID).

**Tabela B3.5-1 — Comparação L-A vs. L-B vs. L-C**

| Dimensão | L-A Centralizada | L-B Edge total | L-C Híbrida |
|---|---|---|---|
| **Custo inicial** | Baixo nos pontos (só câmera/sensor); alto centralizado (PC com GPU se quiser velocidade) | Alto por ponto (Pi + acelerador); baixo centralizado | Médio nos pontos; médio centralizado |
| **Latência E2E** | Alta — depende de janela de transferência | Baixa — inferência local | Média |
| **Banda exigida** | **Alta** — transferir imagens/vídeos brutos | **Mínima** — só metadados estruturados | Média — só frames pós-filtragem |
| **Tolerância a falhas de rede** | Baixa — sem rede, dados se acumulam no SD do ponto | **Alta** — pode operar offline indefinidamente | Média |
| **Manutenção** | Pontos simples; PC central exige cuidados | Pontos complexos (mais peças); cada ponto é um sistema | Pontos médios; PC central é o sistema "rico" |
| **Aderência ao TCC (i7 sem GPU dedicada)** | **Excelente** — usa exatamente o hardware disponível | Inviável sem orçamento de Pi+acelerador por ponto | Boa — Pi por ponto é razoável |
| **Escalabilidade** | Limitada pelo PC central (10 pontos × 5k frames/sem = 50k frames/sem; viável segundo B2.8) | Linear nos pontos | Linear nos pontos |

**Análise.** Para o nosso cenário (10 pontos, ~50 gatos, PC i7 do Felipi, sem orçamento garantido para 10× Pi+acelerador), **L-A Centralizada é a configuração natural**. L-C Híbrida só faz sentido em pontos onde o Perfil B/E2 já tem Pi rodando — nesses casos, é "L-C de graça" (já está lá; usar). L-B Edge total requer compra de 10 Pi 5 + 10 aceleradores Hailo-8L = ~R$ 12–15k apenas em compute; fora do orçamento.

**Decisão consolidada para o TCC:**
- **Padrão = L-A Centralizada**. Todos os pontos enviam dados brutos (imagens, vídeos, embeddings parciais quando há Pi) ao PC central; o PC roda pipeline noturno completo.
- **Exceção pontual = L-C Híbrida** nos pontos que usem Perfil B (IP cam + Pi com Frigate) ou Perfil C (PIR + Pi). Nesses pontos, o Pi pode rodar YOLO11n como pré-filtragem para reduzir banda.
- **L-B Edge total**: stretch goal de pesquisa, demonstrado em **um único ponto α** se houver hardware doado (Pi 5 + Hailo-8L); resultado vira figura de B6.

### B3.5.3 — Eixo E-5: Persistência e indexação

Recapitulando decisão de B2 Parte 3: **SQLite + schema Camtrap-DP + hnswlib vetorial** como padrão; **PostgreSQL + PostGIS** como evolução natural. Aqui consolidamos por que **PostgreSQL não é hoje** — não dominância, mas timing.

**Tabela B3.5-2 — Trade-off SQLite vs. PostgreSQL**

| Aspecto | SQLite local | PostgreSQL central |
|---|---|---|
| **Setup** | Zero — biblioteca embarcada Python (`sqlite3` stdlib) | Médio — servidor, usuários, ACLs, backup |
| **Concorrência write** | Limitada (1 writer por vez) | Multi-writer com MVCC |
| **Tamanho viável** | ~100 GB confortável; >1 TB começa a sofrer | TB sem problema |
| **Backup** | Cópia do arquivo `.db` | `pg_dump`; estratégia replicação |
| **PostGIS / GIS queries** | Não nativo (extensão SpatiaLite) | Nativo, padrão indústria |
| **Aderência ao volume do TCC** | **Excelente** — volume total estimado em 12 meses é <50 GB | Excessivo para piloto; subutilizado |
| **Migração futura** | Schema Camtrap-DP é portátil — migração SQLite→PostgreSQL é direta com `pgloader` ou script Python | — |

**Decisão:** **SQLite + Camtrap-DP** no piloto e na operação contínua do TCC. **Migração documentada** para PostgreSQL como item da seção "Trabalhos futuros" do B6.

**Indexação vetorial:** **hnswlib** local no SQLite, com fallback para força bruta se a base for pequena. Para volume estimado (≤50 gatos × ~200 embeddings = 10k vetores), força bruta com `numpy` é trivial. hnswlib só ganha relevância acima de ~50k vetores.

### B3.5.4 — Eixo E-6: Modo de transferência de dados

Este eixo varia **por ponto** dependendo do perfil de aquisição. Consolida:

**Tabela B3.5-3 — Modos de transferência viáveis**

| Modo | Mecanismo | Latência | Banda | Quando usar |
|---|---|---|---|---|
| **T-SD** | Troca física do cartão microSD | Semanal–mensal | Ilimitada (offline) | Perfis A, C, D, E1, E3 (gravação local) |
| **T-RTSP** | Pull de stream RTSP via `ffmpeg` para PC central | Tempo real | Alta (~1–5 Mbps por câmera) | Perfis B, E2 (Wi-Fi disponível) |
| **T-WiFi-sync** | Pi local sincroniza burst de eventos via `rsync` periódico | Diária | Média (só eventos pós-filtragem) | Perfis B, C com Pi local |
| **T-LoRa-meta** | Apenas metadados/alertas via LoRa (heartbeat, contador de eventos) | Tempo real | Mínima | Telemetria de saúde; **não para imagens** |
| **T-4G-cellular** | Modem 4G no ponto | Tempo real | Alta (custo de dados) | **Descartado para piloto** — custo recorrente alto |
| **T-USB-pulldown** | Voluntário leva pendrive/HD ao ponto e copia local | Quinzenal | Ilimitada | Pontos extremos; fallback |

**Recomendação por perfil:**
- **Perfil A (trail wildlife)**: T-SD (troca semanal–mensal).
- **Perfil B (IP cam + Pi edge)**: T-WiFi-sync (rsync diário) **ou** T-RTSP pull contínuo.
- **Perfil C (híbrido)**: T-WiFi-sync (Pi local consolida e envia).
- **Perfil D (consumer + SD)**: T-SD (troca quinzenal).
- **Perfil E1 (genérica + SD)**: T-SD (troca quinzenal–mensal).
- **Perfil E2 (genérica + RTSP)**: T-RTSP pull.

**LoRa como telemetria complementar:** em pontos δ (remotos, sem rede), **um único módulo LoRa por ponto** pode enviar heartbeat (bateria, contagem de eventos da última hora) ao PC central via gateway LoRa em ponto α. Custo: ~R$ 50–100 por nó LoRa + R$ 200 gateway. **Stretch goal de robustez**, não decisão crítica do piloto.

---

## B3.6 — Mapeamento ponto-a-ponto P1…P10

### B3.6.1 — Premissas do mapeamento

Esta tabela é a **consolidação operacional** de todas as decisões de B3. Para cada um dos 10 pontos de monitoramento do Campus 2, define-se:

- **Classe P (α/β/γ/δ)** herdada da matriz energia × conectividade de B1.
- **Perfil de aquisição** (A/B/C/D/E com sub-variante quando aplicável) escolhido conforme B3.2.
- **Detector E-1** (cascata YOLO11n→MDv6 é padrão; eventuais variações).
- **Re-ID E-3** (MiewID primário em todos; baselines comparativos rodam em B5).
- **Locus de computação** (L-A/L-B/L-C conforme B3.5.2).
- **Modo de transferência** (T-SD/T-RTSP/T-WiFi-sync conforme B3.5.4).
- **Frequência de manutenção em campo** (troca de SD, recarga, vistoria).
- **Justificativa específica** da escolha do perfil para aquele ponto.

> **Importante.** Os 10 pontos abaixo são definidos com base no levantamento preliminar de B1 (mapa preliminar do Campus 2 com a AEX). O **mapeamento exato** dependerá do levantamento de campo final em B5 — esta tabela é a **configuração de referência** a ser refinada na vistoria inicial.

### B3.6.2 — Configuração de referência

**Tabela B3.6-1 — Mapeamento ponto-a-ponto (proposta de referência)**

| Ponto | Local (preliminar) | Classe P | Perfil | Detector | Re-ID | Locus | Transferência | Manutenção | Justificativa |
|---|---|---|---|---|---|---|---|---|---|
| **P1** | Comedouro principal próximo prédio AEX | α | **B** (IP cam + Pi com Frigate) | YOLO11n no Pi → MDv6 no PC | MiewID central | L-C híbrido | T-WiFi-sync diária | Vistoria mensal | Ponto de alto tráfego, AC + Wi-Fi garantidos; vale investir em qualidade de captura contínua |
| **P2** | Comedouro secundário corredor entre prédios | α | **D** (Tapo C400 ou Reolink Argus) | MDv6 batch noturno | MiewID central | L-A | T-SD quinzenal | Quinzenal (troca SD) | Custo baixo, simplicidade, próximo a transeuntes (vandalismo moderado) |
| **P3** | Abrigo coberto noturno | β | **E1** (genérica + SD swap) | MDv6 batch | MiewID central | L-A | T-SD quinzenal | Quinzenal | Sem Wi-Fi confiável; AC disponível; cenário "barato" canônico para validar Perfil E |
| **P4** | Borda florestal nordeste do Campus 2 | γ | **A** (trail wildlife com PIR) | MDv6 batch | MiewID central | L-A | T-SD mensal | Mensal | Sem AC, com painel solar pequeno; PIR otimiza energia |
| **P5** | Borda florestal sul (proximidade mata Cerrado) | γ | **D3** (Tapo + painel solar) | MDv6 batch | MiewID central | L-A | T-SD mensal | Mensal | Alternativa de baixo custo ao Perfil A; comparação direta com P4 |
| **P6** | Ponto remoto extremo nordeste | δ | **A** (trail wildlife com PIR e bateria longa) | MDv6 batch | MiewID central | L-A | T-SD mensal | Mensal | Sem AC nem rede; só trail é viável |
| **P7** | Próximo estacionamento ICMC (alto fluxo humano) | α | **E2** (genérica + RTSP pull) | YOLO11n no PC central (pré-filtragem ffmpeg) → MDv6 | MiewID central | L-A | T-RTSP contínuo | Vistoria mensal | Wi-Fi do campus disponível; cenário "baratíssimo + rede" |
| **P8** | Pátio interno biblioteca (movimento diurno) | α | **D** ou **B** (decisão em B5) | YOLO11n + MDv6 | MiewID central | L-A ou L-C | T-SD ou T-WiFi-sync | Quinzenal | Ponto de comparação experimental B vs. D no piloto |
| **P9** | Estacionamento secundário (luz noturna parcial) | β | **E1** ou **D** | MDv6 batch | MiewID central | L-A | T-SD quinzenal | Quinzenal | Comparação E1 vs. D no piloto (Q-INF-PT-5/6) |
| **P10** | Ponto α experimental — pipeline edge completo | α | **B + Hailo-8L** (stretch goal) | YOLO11n → YOLOv8s+Hailo edge → MDv6 fallback PC | **Embedding edge no Pi 5 + Hailo** | **L-B** | T-WiFi-sync (apenas metadata) | Mensal | **Demonstração de pipeline edge completo** se hardware doado for obtido; resultado em B6 |

### B3.6.3 — Distribuição de perfis no piloto

**Resumo da configuração de referência:**
- Perfil A — 2 pontos (P4, P6) — trail wildlife clássica.
- Perfil B — 2 pontos (P1, P10) — IP cam + Pi edge; P10 é stretch com Hailo.
- Perfil D — 2 pontos (P2, P5) — consumer com PIR; P5 é variante solar.
- Perfil E — 3 pontos (P3, P7, P9) — genérica/OEM; P3 é E1 SD, P7 é E2 RTSP, P9 é comparação.
- **Ponto P8 fica como variável experimental** (B vs. D) para validar Q-INF-PT-1.

**Implicações:**
- **5 perfis distintos rodando em paralelo** — atende ao princípio de comparação experimental (B3.2.9, Q-INF-PT-1 a PT-6).
- **Categoria I (PIR hardware)** cobre P2, P4, P5, P6, P8 (parcial), P10 (parcial) — 5–6 pontos.
- **Categoria II (VMD software)** cobre P1, P3, P7, P9, P10 (parcial) — 5 pontos.
- Distribuição balanceada para análise estatística mesmo com **n=10**.

### B3.6.4 — Comparação experimental embutida no design

A escolha deliberada de **operar múltiplos perfis simultaneamente nos 10 pontos** é o que permite responder as perguntas inferenciais Q-INF-PT-* registradas em B3.2.9:

| Pergunta | Pontos relevantes para responder |
|---|---|
| **Q-INF-PT-1** — Qual frota captura mais eventos? | P8 (B vs. D direto), P1 vs. P2 (mesma classe α, perfis distintos) |
| **Q-INF-PT-2** — Tempo de revisão humana? | Todos — log de minutos por semana por perfil |
| **Q-INF-PT-3** — TCO 12 meses? | Cálculo retrospectivo cobrindo todos os pontos |
| **Q-INF-PT-4** — Perfil D entrega qualidade suficiente? | P2, P5, P8 — comparar Rank-1 de re-ID em crops de D vs. crops de A/B |
| **Q-INF-PT-5** — Perfil E entrega qualidade aceitável? | P3, P7, P9 — comparar Rank-1 de re-ID em crops de E vs. crops de A/B/D |
| **Q-INF-PT-6** — Calibração VMD do Perfil E? | P3, P9 — comparar FP/hora antes e depois de tuning |

Em **B5**, definimos o protocolo experimental detalhado e os critérios de aceitação por pergunta.

### B3.6.5 — Caminho para B4 (Arquitetura de referência)

A tabela B3.6-1 alimenta diretamente B4 nos seguintes aspectos:
1. **Diagrama físico do sistema**: 10 pontos com perfis distintos exigem diagramas representativos por perfil (não 10 diagramas; 5 diagramas-tipo).
2. **Topologia de rede**: pontos com T-WiFi-sync ou T-RTSP precisam de mapa de cobertura Wi-Fi do Campus 2 (atividade de B5).
3. **Servidor central**: PC do Felipi precisa rodar concorrentemente **ingestão T-RTSP de 2–3 streams** + **ingestão batch noturno de SD/USB** + **inferência MDv6 + MiewID** + **interface humana de revisão**. Esse dimensionamento é tema de B4.3.
4. **Banco de dados**: schema Camtrap-DP estendido com colunas `acquisition_profile`, `transfer_mode`, `pi_local_uuid` para rastreabilidade da configuração por evento. Detalhe em B4.4.

---

## Encerramento da Parte 2 de B3

Esta Parte 2:
- analisou o eixo **E-3 Re-ID** (B3.4) e consolidou **MiewID-msv3 como primário**, **MegaDescriptor-L como baseline**, **PPGNet-Cat como referência cat-specific de comparação**, com PetFace e Body-parts descartados como primários;
- analisou conjuntamente **E-4 locus**, **E-5 persistência** e **E-6 transferência** (B3.5), fixando **L-A Centralizada como padrão** (com L-C híbrida onde o hardware Pi já estiver presente) e **SQLite+Camtrap-DP local** como persistência canônica;
- entregou em **B3.6** o **mapeamento ponto-a-ponto P1…P10** com perfil, detector, re-ID, locus, transferência e justificativa por ponto.

Com B3 Parte 1 + Parte 2 completos, o **espaço de design está formalmente analisado**. Os trade-offs estão quantificados, as decisões registradas com justificativa, e o sistema está pronto para ganhar forma arquitetural concreta em **B4** e protocolo experimental em **B5**.

**Próxima entrega (B4 — Arquitetura de referência)**:
- B4.1 — Visão geral em camadas (física, lógica, dados, apresentação).
- B4.2 — Diagramas-tipo por perfil (A, B, D, E1, E2) — 5 diagramas físicos.
- B4.3 — Dimensionamento do servidor central (PC do Felipi).
- B4.4 — Schema de banco Camtrap-DP estendido + diagrama ER.
- B4.5 — Diagrama de fluxo de dados E0→E4 com origens por perfil.
- B4.6 — Stack de software canônico (Python, SQLite, hnswlib, ffmpeg, Frigate opcional).

---

## Fontes citadas nesta parte

### Re-ID multispecies e wildlife
- **Otarashvili L. et al. (2024)** — *Multispecies Animal Re-ID Using a Large Community-Curated Dataset*. arXiv:2412.05602. [arxiv.org/abs/2412.05602](https://arxiv.org/abs/2412.05602).
- **Cermak V. et al. (2024)** — *WildlifeDatasets: An Open-Source Toolkit for Animal Re-Identification*. WACV 2024. [openaccess.thecvf.com](https://openaccess.thecvf.com/content/WACV2024/papers/Cermak_WildlifeDatasets_An_Open-Source_Toolkit_for_Animal_Re-Identification_WACV_2024_paper.pdf); arXiv: [2311.09118](https://arxiv.org/abs/2311.09118).
- **conservationxlabs/miewid-msv3** — *MiewID feature extractor*. HuggingFace. [huggingface.co/conservationxlabs/miewid-msv3](https://huggingface.co/conservationxlabs/miewid-msv3).
- **WildlifeDatasets/wildlife-tools** — Toolkit no GitHub. [github.com/WildlifeDatasets/wildlife-tools](https://github.com/WildlifeDatasets/wildlife-tools); [datasets recomendados](https://wildlifedatasets.github.io/wildlife-datasets/recommended/).
- **Cermak V. et al. (2024)** — *WildlifeReID-10k: Wildlife re-identification dataset with 10k individual animals*. arXiv:2406.09211. [arxiv.org/abs/2406.09211](https://arxiv.org/abs/2406.09211).

### Re-ID gato-específico
- **Akbar R. R. S. (2025)** — *Body-part-based individual feral cat identification from camera trap images using deep learning*. ScienceDirect. [sciencedirect.com](https://www.sciencedirect.com/science/article/pii/S1574954125002675); arXiv: [2507.11575](https://arxiv.org/abs/2507.11575).
- **PPGNet-Cat repository** — *Re-ID model for feral cats based on PPGNet*. [github.com/victorcaquilpan/PPGNet-Cat](https://github.com/victorcaquilpan/PPGNet-Cat).
- **Inoue R. et al. (2024)** — *PetFace: A Large-Scale Dataset and Benchmark for Animal Identification*. ECCV 2024 Oral. arXiv:2407.13555. [arxiv.org/abs/2407.13555](https://arxiv.org/abs/2407.13555); project: [dahlian00.github.io/PetFacePage](https://dahlian00.github.io/PetFacePage/); code: [github.com/mapooon/PetFace](https://github.com/mapooon/PetFace).

### Edge computing e locus
- **Lekhadia S. et al. (2025)** — *An Edge Computing Approach for Real-Time Wildlife Detection and Alert System using YOLOv8 on Raspberry Pi 5*. IJERT 14(8). [ijert.org](https://www.ijert.org/an-edge-computing-approach-for-real-time-wildlife-detection-and-alert-system-using-yolov8-on-raspberry-pi-5).
- **Future of Edge AI in biodiversity monitoring (2024)** — arXiv pre-print discutindo MDv6-compact (22M params, recall 73%→85%) para edge. [arxiv.org/html/2602.13496v1](https://arxiv.org/html/2602.13496v1).

### Persistência e padrões de dados
- **Bubnicki J. W. et al. (2024)** — *Camtrap DP: an open standard for the FAIR exchange of camera trap data*. **Methods in Ecology and Evolution** (já citado em B2 Parte 3). [tdwg.org/standards/camtrap-dp](https://tdwg.github.io/camtrap-dp/).
- **hnswlib** — biblioteca de aproximação de vizinhos. [github.com/nmslib/hnswlib](https://github.com/nmslib/hnswlib).
