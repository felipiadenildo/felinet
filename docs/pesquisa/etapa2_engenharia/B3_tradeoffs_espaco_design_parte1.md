# B3 — Análise de trade-offs e espaço de design (Parte 1)

> **Posição na Etapa 2.** Os requisitos foram estabelecidos em A2.0. O contexto operacional do Campus 2 (10 pontos, matriz P-α/β/γ/δ de energia × conectividade) foi modelado em B1. O pipeline de visão computacional (E0–E4) foi detalhado em B2 (três partes). **B3 transforma essas decisões em um espaço de design explícito**: enumera eixos de configuração, quantifica os trade-offs e mapeia configurações arquiteturais que serão materializadas em B4 (arquitetura de referência) e validadas em B5 (plano de implementação).
>
> **Enquadramento de engenharia de computação.** Esta seção é deliberadamente escrita como análise de engenharia, não como recomendação categórica. Um projeto de engenharia de computação se caracteriza por (1) tratar a solução como **espaço de configuração** e não solução única, (2) **quantificar trade-offs** com métricas reproduzíveis, (3) explicitar **critérios objetivos** para escolher entre alternativas, e (4) registrar as decisões com suas justificativas. B3 segue essa rubrica.
>
> **Estrutura desta entrega**: Parte 1 cobre **B3.1** (eixos de design), **B3.2** (front-end de aquisição organizado em **duas categorias × cinco perfis** A/B/C/D/E na fronteira de Pareto) e **B3.3** (modelos de detecção: MegaDetector v6 × YOLO11n × alternativas). A Parte 2 cobrirá **B3.4** (re-ID), **B3.5** (locus de computação, persistência, transferência) e **B3.6** (mapeamento ponto-a-ponto P1…P10).

---

## B3.1 — Eixos de design e método de análise

### B3.1.1 — Por que tratar o problema como espaço de design

A literatura de camera-trap automatizado é vasta, mas a maior parte dos trabalhos individuais escolhe **uma** configuração e a defende. Esse padrão não serve a um TCC de engenharia de computação porque oculta a fronteira de decisão: o leitor recebe a recomendação sem entender quais variáveis a movem. Aqui adotamos o caminho oposto. Cada decisão técnica do sistema é enumerada como um **eixo** com variantes; cada variante é avaliada em **dimensões mensuráveis** (custo, qualidade, esforço, robustez); o cruzamento dos eixos define o **espaço de design** sobre o qual recomendamos pontos específicos.

Essa abordagem é canônica em engenharia de sistemas e tem nome próprio: **análise de espaço de design** (*design space exploration*), formalizada em hardware/software co-design ([Kang & Schaumont 2008](https://dl.acm.org/doi/10.1145/1377972.1377991)) e em arquitetura de software ([Bass et al., *Software Architecture in Practice*, 4ª ed., 2021](https://www.pearson.com/store/p/software-architecture-in-practice/P200000005869)). Para o nosso caso, ela é especialmente útil porque a colônia do Campus 2 não é homogênea: os 10 pontos diferem em energia, conectividade, fluxo humano e risco de vandalismo (matriz P do B1). Uma única configuração para todos os pontos seria sub-ótima por construção.

### B3.1.2 — Os seis eixos de design do sistema

O sistema admite seis decisões independentes que, combinadas, definem uma configuração concreta. Cada decisão é abordada como eixo separado para preservar a independência analítica.

**Tabela B3.1-1 — Eixos de design**

| # | Eixo | Variantes principais | Onde é tratado |
|---|---|---|---|
| **E-1** | Front-end de aquisição (E0) | **Categoria I (PIR hardware):** Perfis A, C, D · **Categoria II (VMD software / streaming):** Perfis B, E | B3.2 (esta parte) |
| **E-2** | Modelo de detecção genérica (E1) | MegaDetector v6 · YOLO11n · YOLO11s · alternativas | B3.3 (esta parte) |
| **E-3** | Modelo de re-identificação (E3) | MiewID multispecies · MegaDescriptor · PPGNet-Cat · PetFace fine-tune | B3.4 (Parte 2) |
| **E-4** | Locus de computação | Edge total · Centralizado total · Híbrido (filtragem edge + análise central) | B3.5 (Parte 2) |
| **E-5** | Persistência e indexação | SQLite + hnswlib local · PostgreSQL + PostGIS · cloud-managed | B3.5 (Parte 2) |
| **E-6** | Modo de transferência de dados | SD card offline · Wi-Fi periódico · LoRa telemetria · 4G/5G · pull RTSP | B3.5 (Parte 2) |

### B3.1.3 — Dimensões de avaliação

Cada variante de cada eixo é avaliada em cinco dimensões consistentes ao longo de B3:

1. **Custo** (R$): aquisição inicial de hardware e custo recorrente de operação (energia, banda, serviços).
2. **Qualidade**: métricas técnicas relevantes ao eixo (Rank-1, mAP, recall de detecção, FPS, latência, taxa de falsos positivos).
3. **Esforço de implementação**: medido em pessoa-semanas para o TCC (referencial: Felipi e Bárbara, com auxílio do orientador).
4. **Robustez operacional**: tolerância a falhas, complexidade de manutenção em campo, dependência de infraestrutura externa.
5. **Aderência ao contexto Campus 2**: adequação aos pontos reais conforme matriz P de B1 (energia, conectividade, vandalismo, fluxo humano).

Quando relevante, registramos também **consumo energético** e **footprint de armazenamento** como métricas auxiliares.

### B3.1.4 — Critério de seleção: dominância de Pareto

Em cada eixo, identificamos variantes **dominadas** (piores que outra em todas as dimensões) e variantes **na fronteira de Pareto** (não dominadas — cada uma vence em pelo menos uma dimensão). A recomendação final do TCC escolhe pontos na fronteira de Pareto justificando o trade-off escolhido em função do contexto operacional. Variantes dominadas são descartadas com justificativa explícita.

### B3.1.5 — Resumo das decisões prévias que B3 herda

Antes de mergulhar nos eixos, vale recapitular as decisões já estabelecidas e que B3 trata como **invariantes** (não estão em questão aqui):

- **Pipeline lógico em 5 estágios** (E0–E4) com bloco transversal E2.6 — fixado em B2 Parte 1.
- **Pipeline lógico (E1–E4) é invariante ao perfil de aquisição** — princípio de B2 que B3 confirma ao tratar E-1 como eixo independente.
- **Classificador de espécie** (E2) — **SpeciesNet** primário, com verificação binária local opcional, fixado em B2 Parte 2.
- **Métricas-alvo** (Rank-1 ≥ 0,85, mAP ≥ 0,75, BAKS/BAUS ≥ 0,80) — fixadas em B2 Parte 3.
- **Padrão de dados** (Camtrap-DP) — fixado em B2 Parte 3.

---

## B3.2 — Eixo E-1: Front-end de aquisição

### B3.2.1 — Por que este é o eixo mais importante

A aquisição condiciona tudo o que vem depois. O detector mais sofisticado do mundo é inútil se o front-end perde o evento. O modelo de re-ID mais acurado falha se a câmera entrega imagens de pose ruim ou modalidade incompatível com o treino. E mais: o front-end é a única camada que **toca o mundo físico** — sua escolha define consumo de energia, custo de cabeamento, exposição a vandalismo, e portanto define o que é fisicamente instalável em cada um dos 10 pontos do Campus 2.

### B3.2.2 — Eixo de decisão fundamental: PIR hardware vs. VMD software

Antes de enumerar perfis, é preciso explicitar o **eixo de decisão raiz** que organiza todo o E-1: **como o sistema decide que algo merece ser gravado**. Há duas famílias:

**Categoria I — Trigger por PIR (Passive Infrared) hardware.** Um sensor piroelétrico físico detecta variação de calor no campo de visão. Câmera permanece em deep-sleep (consumo <10 mW). Ao detectar evento, acorda, captura, volta a dormir. **Vantagens**: consumo energético baixíssimo, viabiliza bateria interna de longa duração, latência determinística de hardware. **Desvantagens**: pode falhar para alvos de baixo contraste térmico (gato pequeno em dia quente); hardware fixo; falsos negativos invisíveis (o evento simplesmente não é gravado).

**Categoria II — Trigger por VMD (Video Motion Detection) software.** A câmera permanece em streaming contínuo (ou em loop quase-contínuo); um software analisa frames consecutivos buscando variação pixel-a-pixel acima de um limiar (algoritmos típicos: MOG2, frame-difference, KNN). Quando detecta movimento, sinaliza para gravação. **Vantagens**: ajustável em software (zonas, sensibilidade, máscaras de exclusão); detecta alvos invisíveis ao PIR (e.g., contraste térmico fraco); permite re-análise posterior do raw stream. **Desvantagens**: consumo energético uma ou duas ordens de magnitude maior (CPU sempre ativa decodificando e analisando); falsos positivos altos sem calibração cuidadosa (vegetação ao vento, sombras, mudança de iluminação); inviabiliza operação por bateria sem painel solar grande.

Essa distinção define **quais perfis são fisicamente instaláveis em quais pontos**. Em pontos sem AC (P-γ/δ), apenas Categoria I é viável. Em pontos com AC (P-α/β), ambas as categorias são opções legítimas com trade-offs distintos.

### B3.2.3 — Categoria I, Perfil A: Trail camera wildlife com PIR

**Descrição.** Câmera comercial dedicada (Bushnell, Reconyx, Browning, ou alternativa nacional) integrando: sensor de imagem (1080p), LEDs IR para visão noturna, **PIR físico calibrado para fauna**, slot para SD card, alimentação por baterias AA/D ou pack 12 V, opcionalmente módulo cellular ou Wi-Fi. Existe variante DIY consolidada (WiseEye em Raspberry Pi Zero + PIR + módulo de câmera) descrita em [Klemens et al. 2021](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.13607).

**Funcionamento.** PIR detecta variação térmica → câmera acorda do *deep sleep* → captura burst de 3–10 frames + opcional vídeo curto → grava em SD card → volta a dormir. Operação totalmente autônoma, sem cabos exceto para troca de baterias e leitura periódica do SD.

**Avaliação:**

| Dimensão | Valor |
|---|---|
| **Custo inicial** | R$ 300–1.500 por câmera comercial nacional; ~R$ 2.000–4.000 para Bushnell/Reconyx; ~R$ 200–400 para *clone* DIY estilo WiseEye |
| **Custo recorrente** | Pilhas (~R$ 50/mês com pack alcalino; quase zero com bateria LiFePO4 + painel solar pequeno) |
| **Qualidade** | Trigger 0,3–2,5 s dependendo do modelo (DIY WiseEye reporta 0,44 s); resolução 1080p padrão; visão noturna IR boa em até 5–15 m |
| **Esforço** | Baixo — comercial é plug-and-play; DIY exige montagem mas a literatura entrega blueprint completo |
| **Robustez** | Alta — IP65/IP66 nativos; sem cabos elétricos externos |
| **Aderência ao Campus 2** | **Excelente em pontos δ e γ**; **suficiente em α/β** mas subutiliza recursos disponíveis |
| **Consumo energético** | 5–50 mW em sleep; 200–800 mW durante captura; geralmente <2 Wh/dia |
| **Riscos** | Roubo/vandalismo; falso negativo do PIR para gatos pequenos ou de mesma temperatura do fundo |

### B3.2.4 — Categoria I, Perfil C: Híbrido (câmera com PIR + edge compute local)

**Descrição.** Mantém a câmera com PIR (estilo Perfil A), mas adiciona um **Raspberry Pi adjacente** para processamento local de classificação e re-ID em pontos onde isso é desejável. Câmera dorme entre eventos; PIR dispara captura; imagens são transferidas via USB/SD para o Pi local, que executa o pipeline parcial (E1, E2, opcionalmente E3) antes de sincronizar com o PC central.

**Avaliação resumida.** Reúne benefícios do Perfil A (autonomia energética da câmera) com benefícios do edge compute (redução de banda, processamento local). O custo é maior (câmera + Pi + bateria/painel solar para o Pi) e o esforço de integração é o mais alto desta categoria. **Aderência**: faz sentido em pontos α/β com AC para o Pi mantendo a câmera com PIR; ou em γ/δ com painel solar dedicado ao Pi (possível mas custoso).

### B3.2.5 — Categoria I, Perfil D: IP camera consumer battery-powered (PIR interno, offline, SD)

**Descrição.** Câmera de segurança residencial **battery-powered com PIR interno e slot SD**, configurada para operar **sem Wi-Fi após setup inicial**. Exemplos: [Tapo C400 (TP-Link)](https://www.tp-link.com/us/home-networking/cloud-camera/tapo-c400/), [Reolink Argus PT Ultra / Argus Eco](https://reolink.com/product/argus-pt-ultra/), eufy SoloCam. Preço no Brasil: **R$ 200–500**. Especificações típicas: 1080p–4K, PIR integrado, slot microSD até 256–512 GB, IP65, bateria embutida 5.000–10.000 mAh, opcional painel solar pequeno. Autonomia reportada: **120–180 dias** em modo PIR-triggered ([Reolink battery table](https://support.reolink.com/articles/900000421243-How-Long-Does-the-Battery-Last-for-Battery-powered-Cameras/)).

**Funcionamento.** PIR detecta movimento → câmera acorda → grava clipe curto (10–60 s) em microSD → volta a dormir. **Sem comunicação com servidor durante operação**.

**Avaliação:**

| Dimensão | Valor |
|---|---|
| **Custo inicial** | **R$ 200–500/câmera**. microSD 64 GB: ~R$ 50. Painel solar opcional: ~R$ 80–150 |
| **Custo recorrente** | Quase zero — recarga a cada 3–6 meses, zero com solar |
| **Qualidade** | Trigger PIR ~1–2 s (mais lento que A wildlife dedicada); 1080p–4K; clipe de vídeo curto (não burst JPEG) |
| **Esforço** | **Muito baixo** — plug-and-play; setup em ~10 min via app |
| **Robustez** | Média–alta — IP65 nativo; risco de **trava de firmware exigindo nuvem** (validar com teste offline) |
| **Aderência ao Campus 2** | **Boa em todas as classes P-α/β/γ/δ** |
| **Riscos** | Plataforma fechada (Wyze já exigiu reauth periódico, [forum 2024](https://forums.wyze.com/t/sd-card-recording-while-offline/309334)); EXIF/timestamp consumer-grade; descontinuação do produto |

**Subvariantes do Perfil D**:
- **D1** — Battery interna fixa (Tapo C400, Reolink Argus Eco). Recarga via USB-C.
- **D2** — Bateria removível (Reolink Argus 4 Pro). Elimina downtime.
- **D3** — D1/D2 + painel solar 6 W (~R$ 80–150). Operação indefinida.
- **D4** — Nacionais (Intelbras, Multilaser). Suporte PT-BR; testar firmware offline antes.

### B3.2.6 — Categoria II, Perfil B: IP camera ONVIF/RTSP + edge compute (Raspberry Pi)

**Descrição.** Câmera de rede (Intelbras, Hikvision, Dahua, ou qualquer câmera ONVIF/RTSP) **sem PIR físico**, em streaming contínuo via RTSP, conectada a um **Raspberry Pi 4/5** próximo. O Pi roda VMD em software, faz inferência E1 leve localmente, e só persiste frames com detecção positiva. Pipeline inspirado em [Frigate NVR](https://frigate.video) ([repositório](https://github.com/blakeblackshear/frigate)) e tutorial Raspberry Pi para fauna ([XDA Developers 2025](https://www.xda-developers.com/i-made-a-wildlife-camera-with-a-raspberry-pi/)).

**Funcionamento.** Câmera transmite RTSP H.264 24/7 a 15–25 FPS em 1080p → Pi mantém buffer circular em RAM/disco (~24 h) → executa VMD (MOG2/frame-diff em OpenCV) → quando detecta movimento, executa **MegaDetector v6 ou YOLO11n** localmente → se confirma animal, persiste burst + envia para PC central; senão, descarta.

**Avaliação:**

| Dimensão | Valor |
|---|---|
| **Custo inicial** | IP cam doada: R$ 0; comprada R$ 150–600. Raspberry Pi 5 4 GB: R$ 600–800. SD/SSD: R$ 100–200. Acelerador opcional Coral USB ou Hailo-8L: R$ 400–800. **Total: R$ 250–2.400** |
| **Custo recorrente** | Energia AC contínua ~5–10 W → ~4–7 kWh/mês → R$ 4–10/mês |
| **Qualidade** | Streaming 24/7 ⇒ **zero perda por trigger lento**. 1080p ou 4K. VMD com ajuste fino possível |
| **Esforço** | Médio — configuração de RTSP, montagem do Pi, software (Frigate ou custom), testes de VMD. ~2–4 pessoa-semanas |
| **Robustez** | Média — depende de AC contínuo; cabos adicionais expõem a vandalismo |
| **Aderência ao Campus 2** | **Excelente em α**; **boa em β** com Pi armazenando local; **ruim em γ/δ** |
| **Consumo energético** | 5–10 W contínuos = ~120–240 Wh/dia. **30–100× maior** que Categoria I |
| **Riscos** | Roubo do conjunto; corte de cabo; falha de Wi-Fi; falsos positivos altos sem calibração |

### B3.2.7 — Categoria II, Perfil E: IP camera genérica/OEM (VMD software, SD/RTSP, baixo custo)

**Descrição.** Câmeras IP **genéricas de mercado de massa** baseadas em SoCs OEM (Anyka, Goke, Hisilicon, Ingenic, XiongMai), comercializadas em varejo brasileiro e marketplaces internacionais (AliExpress, Banggood). **Sem PIR físico** — detecção exclusiva via VMD em software embutida no firmware da câmera. Vendidas como câmeras de segurança residencial de baixo custo, frequentemente sob marcas brancas ou pequenas (V380, ICSEE, iCSee, IPCAM P2P) com qualidade variável. Preço típico no Brasil: **R$ 50–150**, ou seja, **a opção mais barata por unidade** do espaço de design.

**Exemplo técnico representativo** (caso real, dump de campo): câmera baseada em **SoC Anyka AK3918EV300L**, ARM926EJ-S @ 888 MHz, 64 MiB DRAM DDR2, Linux 4.4 + Buildroot, Wi-Fi Atbm603x, sensor 1080p, sem PIR físico, VMD via software com algoritmo "AI Humanoid" embutido, RTSP exposto em `/live/ch0` (HD) e `/live/ch1` (SD) na porta 554, gravação local em microSD via FAT32 em `/mnt/sdcard`, processo principal `GW_APP` ([especificações do chip — Unifore 2020](https://www.unifore.net/ip-video-surveillance/anyka-ak3918ev300-1080p-ip-camera-solution.html); padrão de URLs RTSP de câmeras chinesas catalogado em [iSpyConnect](https://www.ispyconnect.com/pt/camera/china)). O dump técnico completo desta câmera está documentado em **Apêndice B3.A** ao final desta parte, como referência para implementação.

**Funcionamento.** VMD no firmware da câmera analisa frames continuamente → quando detecta variação acima do limiar, dispara gravação local em SD (clipe MP4 H.264) **ou** mantém streaming RTSP contínuo disponível na LAN. Coleta dos dados: depende da sub-variante.

**Avaliação:**

| Dimensão | Valor |
|---|---|
| **Custo inicial** | **R$ 50–150/câmera** (mais baixo do espaço). microSD 64 GB: ~R$ 50. Painel solar (se sub-variante com bateria): R$ 80–150 |
| **Custo recorrente** | Próximo de zero em E1 (AC + SD swap); ~R$ 4–10/mês em E2 (AC + RTSP pull); alto em E3/E4 (bateria não dura) |
| **Qualidade** | VMD ajustável mas com falsos positivos altos sem calibração (vegetação, sombras); resolução 1080p; **sem PIR para confirmar evento térmico** |
| **Esforço** | Baixo–médio — depende da sub-variante; setup via app proprietário (V380, ICSEE) ou direto via RTSP |
| **Robustez** | **Variável e dependente de firmware** — modelos OEM podem ter bugs, exigir reboot periódico, ter falhas de NTP |
| **Aderência ao Campus 2** | **Boa em α/β** (todas sub-variantes); **inviável em γ/δ** com bateria (E3/E4); E1/E2 inviáveis em γ/δ por falta de AC |
| **Consumo energético** | **Alto** — VMD contínuo mantém SoC ativo (~1,5–3 W contínuos); incompatível com bateria pequena |
| **Customização** | **Alta no nível de protocolo** (RTSP/ONVIF expostos) mas **baixa no firmware** (closed-source). Existe rota de custom firmware via **OpenIPC** ([openipc.org](https://openipc.org); cobre Anyka, HiSilicon, GrainMedia, XiongMai) para usuários avançados — não recomendada para o piloto do TCC |
| **Riscos** | (1) Firmware fechado e descontinuado sem aviso; (2) bugs de NTP / drift de relógio inviabilizam timestamp confiável; (3) "phone home" para servidor da fabricante (mitigação: VLAN isolada); (4) qualidade óptica variável; (5) sem padronização EXIF |

**Subvariantes do Perfil E** (apresentadas em pé de igualdade — escolha por ponto será feita em B3.6):

| Sub | Wi-Fi | Bateria | Ingestão | Aderência prática |
|---|---|---|---|---|
| **E1** | Não | Não (AC) | SD swap presencial (semanal/quinzenal) | **Viável e simples**. Cenário "barato e offline" canônico. Boa para α/β remotos do roteador, sem rede |
| **E2** | Sim | Não (AC) | Pull RTSP via PC/Pi remoto (`ffmpeg -i rtsp://...`) | **Viável**. Reaproveita rede Wi-Fi do campus quando disponível. Mais flexível operacionalmente |
| **E3** | Não | Sim | SD swap + recarga periódica de powerbank | **Pouco viável** — VMD contínuo descarrega powerbank em 1–3 dias sem painel solar grande |
| **E4** | Sim | Sim | RTSP pull intermitente + recarga | **Pior cenário** — Wi-Fi + VMD esgotam bateria rapidamente; só faz sentido com painel solar e raramente vale a complexidade |

**Pontos fortes:**
- **Menor custo por unidade** do espaço de design (R$ 50–150).
- **Disponibilidade no varejo brasileiro** (mercado de câmeras de segurança residencial é grande).
- **Padrões abertos** RTSP/ONVIF na maioria dos modelos permitem ingestão direta sem app proprietário.
- **Sub-variante E1 é a configuração mais simples** do espaço inteiro: câmera ligada na tomada, gravando em SD, voluntário troca o cartão no caminho.

**Pontos fracos:**
- **Sem PIR → consumo alto** → opções com bateria (E3/E4) são marginais.
- **Qualidade de VMD do firmware OEM** geralmente é fraca (limiar global, sem zonas) — falsos positivos elevados.
- **Timestamp não confiável** sem configuração explícita de NTP (e firmware OEM pode não suportar).
- **Risco de lock-in de app proprietário** se o RTSP não estiver exposto ou estiver atrás de autenticação não documentada.
- **Sem padronização EXIF** — metadados precisam ser inferidos do nome do arquivo ou overlay do vídeo.

### B3.2.8 — Análise de Pareto (eixo E-1)

**Tabela B3.2-1 — Cinco perfis na fronteira de Pareto**

| Perfil | Categoria | Trigger | Custo inicial | Custo recorrente | Qualidade trigger | Esforço | Aderência α/β | Aderência γ/δ |
|---|---|---|---|---|---|---|---|---|
| **A — Trail+PIR wildlife** | I (PIR HW) | PIR físico calibrado fauna | Médio (R$ 400–2.000) | Quase zero | **Alta** (0,3–0,8 s) | Baixo | OK | **Ótima** |
| **B — IP cam + Pi edge** | II (VMD SW) | VMD calibrado no Pi | Médio (R$ 250–2.400) | Médio (R$ 4–10/mês) | Excelente (24/7, sem perda) | Médio | **Ótima** | Inviável |
| **C — Híbrido PIR+Pi** | I (PIR HW) | PIR + edge | Alto | Médio | Excelente | Alto | Boa | Marginal |
| **D — IP cam consumer + SD** | I (PIR HW) | PIR interno consumer | Baixo (R$ 200–500) | Quase zero | Média (1–2 s) | **Muito baixo** | Boa | **Boa** |
| **E — IP cam genérica + SD/RTSP** | II (VMD SW) | VMD firmware OEM | **Baixíssimo (R$ 50–150)** | Baixo (E1/E2) | Média–baixa (FP altos) | Baixo (E1); médio (E2) | Boa (E1/E2) | Inviável (E3/E4 marginais) |

**Variantes dominadas (descartadas):**
- IP camera ONVIF **sem** edge compute, com envio direto de stream para PC central via Wi-Fi: dominada por B (mesmo custo de banda, sem o ganho de filtragem local).
- Trail camera com módulo **cellular pago** (4G/5G): dominada por A simples para o orçamento atual; retomar como evolução futura.
- Perfil E sub-variante E4 (Wi-Fi + bateria): dominada por E2 (sem bateria, mesma rede) ou por D3 (com PIR + solar) — descartada para o piloto.

**Recomendação por classe de ponto (preliminar — refinada em B3.6)**:
- **P-α (AC + Wi-Fi)**: B (qualidade máxima se há doação de hardware) **ou** E2 (custo mínimo) **ou** D (simplicidade).
- **P-β (AC sem Wi-Fi)**: B (com armazenamento local + sync periódica) **ou** E1 (SD swap) **ou** D.
- **P-γ (sem AC, com Wi-Fi distante)**: A **ou** D3 (consumer + solar).
- **P-δ (sem AC, sem rede)**: A **ou** D (PIR consumer com bateria de longa duração).

**Justificativa de manter cinco perfis na fronteira**: cada um vence em pelo menos uma dimensão. **A** vence em qualidade de trigger e robustez em pontos remotos; **B** vence em qualidade de stream e flexibilidade computacional; **C** vence em pipeline completo com autonomia; **D** vence em simplicidade e equilíbrio custo/qualidade; **E1** vence em **custo absoluto mínimo**. Nenhum é dominado, todos são legítimos.

### B3.2.9 — Implicação metodológica: piloto comparativo entre perfis

A decisão de operar com **múltiplos perfis simultaneamente** abre uma oportunidade rara para o TCC: **comparação experimental direta** entre perfis no mesmo cenário ambiental. Em B5 será detalhado o protocolo, mas a hipótese é registrar:

- **Q-INF-PT-1**: Em um ponto α servido por dois ou três perfis simultaneamente (e.g., trail wildlife A + IP cam consumer D + IP camera com Pi B + IP genérica E), qual frota captura **mais eventos de gato**? Qual tem **mais falsos positivos**? Qual produz crops com **melhor qualidade média para re-ID**?
- **Q-INF-PT-2**: Tempo de revisão humana semanal por perfil (proxy de utilidade operacional).
- **Q-INF-PT-3**: **TCO de 12 meses** — hardware, energia, mão de obra de manutenção, perda por defeito (decisão prática para a AEX continuar pós-TCC).
- **Q-INF-PT-4**: O Perfil D entrega **qualidade suficiente para re-ID** apesar do trigger mais lento?
- **Q-INF-PT-5**: O Perfil E (mais barato) entrega **qualidade aceitável apesar dos falsos positivos do VMD OEM**? Ou o custo de revisão humana inviabiliza?
- **Q-INF-PT-6**: A **calibração de VMD** no Perfil E (zonas de exclusão, limiar) consegue reduzir falsos positivos a um nível operacional aceitável?

Essa comparação experimental é um **diferencial técnico** do TCC — a maior parte dos trabalhos compara apenas modelos ou apenas hardware, raramente o front-end completo em paralelo. Ela responde à questão de engenharia central: **qual configuração é melhor para este caso de uso, considerando orçamento e cronograma reais?**

### B3.2.10 — Implicações dos Perfis D e E sobre o pipeline lógico

A inclusão dos Perfis D e E impõe ajustes pontuais no pipeline já definido em B2:

1. **E0 (Aquisição) ganha três sub-modos de ingestão**:
   - **(a) JPEG burst** (Perfis A e C — formato wildlife clássico).
   - **(b) MP4 curto** (Perfil D, Perfil E1/E3 com gravação SD). Inserir **frame extractor** à frente: `ffmpeg -i input.mp4 -vf fps=2 -q:v 2 -an frame_%04d.jpg` produz 1 frame a cada 0,5 s.
   - **(c) RTSP pull** (Perfil B e Perfil E2/E4). Pipeline: `ffmpeg -rtsp_transport tcp -i rtsp://user:pass@cam_ip/live/ch0 -vf "select='gt(scene,0.05)'" -vsync vfr keyframe_%04d.jpg` extrai keyframes em mudança de cena, ou faz dump direto do stream em segmentos de N minutos.

2. **E2.6 (Pré-processamento) ganha calibração específica por perfil**:
   - Perfis B e E exigem **calibração de VMD** (ajuste de limiar, zonas de exclusão para vegetação) — etapa de tuning de 1–2 semanas por ponto.
   - Perfis A, C, D não exigem calibração de VMD (PIR já filtra).

3. **E4 (Persistência) ganha política de timestamp por perfil**:
   - **Perfis A, B, C**: timestamp EXIF confiável (sistemas dedicados); fallback NTP no PC central.
   - **Perfil D**: timestamp do nome de arquivo (`YYYYMMDD_HHMMSS.mp4`) ou overlay no vídeo (OCR opcional como último recurso).
   - **Perfil E**: timestamp **menos confiável** — verificar drift do RTC da câmera; se falhar, usar timestamp do filesystem (data de modificação no SD) com aviso de ±1 minuto. **Para Perfil E2, configurar NTP server local** (Pi ou PC) e apontar a câmera para ele se o firmware permitir.

4. **B5 (Plano de implementação) ganha rotinas de teste por perfil**:
   - **Perfil D**: teste de operação offline por 7 dias antes de compra em escala.
   - **Perfil E**: teste de **(a) RTSP exposto** (ferramenta: `vlc rtsp://...`), **(b) drift de relógio** em 7 dias, **(c) qualidade de VMD do firmware** (taxa de FP por hora em condição típica), **(d) phone-home** (capturar tráfego com `tcpdump` em VLAN isolada).
   - **Para ambos D e E**: registrar firmware version, MAC, e parâmetros calibrados em `deployment.json` por ponto.

5. **B4 (Arquitetura de referência) ganha módulo de ingestão multi-perfil**: um worker Python por sub-modo (JPEG, MP4, RTSP) que normaliza para o formato canônico de E0 antes de despachar para E1.

Esses ajustes são pequenos e **confirmam o princípio de B2 de que o pipeline lógico (E1–E4) é invariante** aos perfis de aquisição — toda a variabilidade fica contida em E0 + E2.6.

---

## B3.3 — Eixo E-2: Modelo de detecção genérica (E1)

### B3.3.1 — O problema específico de E1

Recapitulando B2 Parte 1: E1 é o detector genérico de **animal/pessoa/veículo** que opera sobre cada frame válido vindo de E0 e retorna **bounding boxes**. As escolhas técnicas relevantes são:

- **Acurácia em fauna pequena e em condições de camera-trap** (não em ImageNet).
- **Throughput em CPU** (cenário sem GPU dedicada é o piloto mínimo, conforme B2.8).
- **Tamanho do modelo** (impacta deploy no Raspberry Pi do Perfil B).
- **Facilidade de uso** (interface CLI, integração Python, atualizações de versão).

Observação adicional importante após inclusão dos Perfis D e E: o detector E1 também atua como **filtro de falsos positivos do VMD** nos perfis Categoria II. No Perfil E especificamente, onde o VMD do firmware é fraco, E1 carrega a responsabilidade de descartar disparos espúrios (folha, sombra, mudança de luz). Isso favorece detectores treinados em camera-trap (MegaDetector) sobre detectores genéricos COCO (YOLO11n stock).

### B3.3.2 — Candidatos

**Tabela B3.3-1 — Candidatos a detector E1**

| Modelo | Backbone / arquitetura | Treino | Latência CPU | Latência GPU leve | Tamanho | Adequação |
|---|---|---|---|---|---|---|
| **MegaDetector v6 (MDv6-Extra)** | YOLOv9 fine-tunado | Treino contínuo sobre dados de camera-trap globais ([HuggingFace MDv6c-Extra](https://huggingface.co/MIT-AI4Healthcare/MDv6c-Extra)); ver [release notes](https://github.com/microsoft/CameraTraps/blob/main/megadetector.md#megadetector-v6) | ~150–300 ms (FP32) | ~60–100 ms (RTX 3050) | ~100–200 MB | **Padrão de fato** em camera-trap; referência |
| **MegaDetector v5a / v5b** | YOLOv5 | Dataset histórico (50k+ imagens curadas) | ~200–400 ms CPU | ~60–90 ms GPU | ~140 MB | Versão anterior, ainda muito usada; benchmark publicado: RTX 4090 17,6 img/s; M3 MBP 4,6 img/s ([agentmorris/MegaDetector](https://github.com/agentmorris/MegaDetector/blob/main/megadetector.md)) |
| **YOLO11n (Ultralytics, 2024–2025)** | YOLOv11 nano | COCO + fine-tune opcional | **56,1 ms CPU** ([Ultralytics docs](https://docs.ultralytics.com/compare/yolo26-vs-yolo11/)) | ~10–15 ms | ~6 MB | **Mais leve** — viável no Pi 5 sem acelerador |
| **YOLO11s (small)** | YOLOv11 small | COCO + fine-tune opcional | ~120 ms | ~20 ms | ~22 MB | Intermediário |
| **YOLOv8s + Hailo-8L** | YOLOv8s em AI Kit | COCO | — | **~13 FPS = 76 ms** no Pi 5 + Hailo ([benchmark Reddit](https://www.reddit.com/r/raspberry_pi/comments/1e5zycb/yolov8s_fps_benchmark_and_performance_comparison/)) | ~22 MB + acelerador | Opção edge acelerada |
| **EfficientDet-D0 / D1** | EfficientNet + BiFPN | COCO | ~250–400 ms CPU | ~30–60 ms | ~16–25 MB | Bom equilíbrio; menos popular em wildlife |
| **DETR / Deformable DETR** | Transformer end-to-end | COCO | >1 s CPU | ~100 ms GPU | ~150 MB | SOTA em precisão mas pesado para Pi |

### B3.3.3 — Análise de trade-offs (eixo E-2)

A escolha do detector tem três pontos relevantes na fronteira de Pareto:

**Ponto 1 — MegaDetector v6 (qualidade máxima)**
- **Justificativa**: treino específico em camera-trap reduz falsos positivos clássicos (vegetação, sombras) que YOLO11n genérico produz. Crítico para **filtragem do output do Perfil E** (VMD OEM ruidoso).
- **Custo**: ~150–300 ms CPU é tolerável para batch noturno.
- **Quando usar**: PC central do Felipi.

**Ponto 2 — YOLO11n (custo computacional mínimo)**
- **Justificativa**: 56 ms CPU permite rodar **no Raspberry Pi do Perfil B** sem acelerador, viabilizando edge compute em hardware modesto.
- **Custo**: acurácia menor; mais falsos positivos a filtrar depois.
- **Quando usar**: motion-confirmation no Pi do Perfil B; cascata leve antes do MegaDetector.

**Ponto 3 — YOLOv8s + Hailo-8L (edge acelerado)**
- **Justificativa**: acelerador Hailo-8L entrega ~13 FPS de YOLOv8s no Pi 5.
- **Custo**: hardware adicional R$ 500–800; complexidade.
- **Quando usar**: pontos α com AC garantida e desejo de pipeline completo edge.

### B3.3.4 — Estratégia em cascata

Dado que os pontos 1 e 2 têm trade-offs complementares, a recomendação é uma **cascata em dois níveis**:

1. **Nível 1 (rápido, no Pi do Perfil B ou pré-pass no PC central)**: **YOLO11n** como confirmação de movimento. Frames com detecção positiva (`animal`, `person`, `vehicle` com score > 0,3) seguem.
2. **Nível 2 (preciso, no PC central)**: **MegaDetector v6** em todos os frames aprovados pelo Nível 1. Suas decisões são a verdade do pipeline.

Essa cascata reduz a carga em ~uma ordem de grandeza, melhora a latência efetiva e mantém o MegaDetector como referência.

### B3.3.5 — Métrica composta para escolha

Para fins do relatório técnico, propomos uma métrica composite ponderada:

\[
\text{Score}_{\text{det}} = 0{,}4 \cdot \text{precision}_{\text{animal}} + 0{,}3 \cdot \text{recall}_{\text{animal}} + 0{,}2 \cdot \frac{1}{\text{latency}_{\text{normalized}}} + 0{,}1 \cdot \text{deploy\_simplicity}
\]

com `latency_normalized = latency_modelo / latency_MDv6` e `deploy_simplicity` ∈ [0,1] subjetivo. Em B5, esse score será calculado empiricamente sobre o conjunto de teste do piloto.

### B3.3.6 — Decisão consolidada

- **Detector primário no PC central**: **MegaDetector v6**.
- **Detector secundário (filtragem rápida)**: **YOLO11n** no Pi do Perfil B ou pré-pass no PC.
- **Detector experimental (stretch goal)**: **YOLOv8s + Hailo-8L** em um ponto α.

Descartado: **DETR e variantes** — overkill para o budget e sem ganho comprovado em camera-trap.

---

## Apêndice B3.A — Dump técnico de câmera Anyka (exemplo Perfil E)

Esta seção registra o dump técnico completo de uma câmera IP de baixo custo baseada em SoC Anyka, obtido em análise de campo. Serve como **referência de implementação** para quem for adquirir o mesmo hardware ou similar (V300/V330) para o piloto. Mantida em apêndice para não congestionar o texto principal.

### Sistema operacional
| Item | Valor |
|---|---|
| Kernel Linux | 4.4.282 |
| Arquitetura | ARM926EJ-S (ARMv5TEJ) |
| Buildroot | 2018.02.7 |
| Bootloader | U-Boot 2019.10.0-V4.0.18 |
| Shell | BusyBox v1.22.1 |

### Hardware principal
| Item | Valor |
|---|---|
| SoC | Anyka AK3918EV300L |
| Frequência CPU | 888 MHz |
| RAM | 64 MiB DDR2 @ 444 MHz |
| Flash | 8 MiB (XM25QH64C) |
| Sensor de imagem | H63 / SC1346 (1080p / 2 MP) |
| Módulo Wi-Fi | Atbm603x / 6012bx |

### Rede e protocolos
| Item | Valor |
|---|---|
| UART | ttySAK0 @ 115200 bps |
| Portas abertas | 554 (RTSP), 5000 (UPnP), 50000 (proprietário Gwell/Jortan) |
| Streams RTSP | `/live/ch0` (HD), `/live/ch1` (SD), `/onvif1` |

### Sensores e detecção
| Item | Valor |
|---|---|
| PIR | **Não presente** (`pirSen: 0`) |
| Detecção de movimento | VMD por software |
| Detecção humana | Algoritmo "AI Humanoid" embutido (`humanDetectEn: 2`) |
| Armazenamento externo | Slot microSD (vfat/FAT32) em `/mnt/sdcard` |

### Processos e estrutura de arquivos
| Item | Valor |
|---|---|
| Processo principal | `GW_APP` (áudio + vídeo + rede) |
| Configurações | `/etc/config/ipc_setting.ini` |
| Binários e scripts | `/ipc/` |
| Driver de captura | `/dev/video0` |

### Observações de engenharia
- **Validação inicial recomendada**: confirmar acesso RTSP em `rtsp://admin:senha@IP:554/live/ch0` com VLC antes de qualquer integração.
- **Customização avançada (opcional, não para piloto TCC)**: comunidade [OpenIPC](https://openipc.org) suporta SoCs Anyka — viabiliza firmware aberto com Majestic streamer, removendo lock-in. Custo: complexidade alta de flashing via UART (3,3 V — atenção, 5 V queima o SoC). Repositório de referência para AK3918: [MuhammedKalkan/Anyka-Camera-Firmware](https://github.com/MuhammedKalkan/Anyka-Camera-Firmware), [JayGoldberg/anyka-cams](https://github.com/JayGoldberg/anyka-cams).
- **Risco operacional**: firmware OEM pode tentar conexão a servidores chineses ("phone home"). Mitigação: isolar câmera em VLAN sem saída para internet; monitorar com `tcpdump` durante 24 h antes de instalação definitiva.

---

## Encerramento da Parte 1 de B3

Esta Parte 1:
- enumerou o **método** (B3.1) com seis eixos de design e critério de Pareto;
- estruturou o **front-end de aquisição** (B3.2) em **duas categorias** (PIR hardware vs. VMD software) **× cinco perfis** (A, B, C, D, E) na fronteira de Pareto, com Perfil E mapeando explicitamente o cenário **"câmera IP genérica + SD/RTSP"** em quatro sub-variantes (E1–E4) apresentadas em pé de igualdade;
- documentou implicações sobre o **pipeline lógico** (frame extractor para MP4, RTSP pull para streams, calibração de VMD, política de timestamp por perfil);
- fixou a estratégia de **detecção** (B3.3) como cascata **YOLO11n → MegaDetector v6**, com observação de que MegaDetector é especialmente importante para filtrar o output ruidoso do Perfil E;
- registrou em **Apêndice B3.A** o dump técnico de uma câmera Anyka real como referência de implementação.

**Próxima entrega (B3 Parte 2)**: análise de trade-offs em re-ID (E-3) com MiewID × MegaDescriptor × PPGNet-Cat × PetFace; eixo de locus de computação (E-4) cruzado com persistência (E-5) e transferência (E-6); finalmente o **mapeamento ponto-a-ponto P1…P10** consolidando todas as decisões — incluindo a escolha de **qual perfil A/B/C/D/E (e qual sub-variante de E) é canônico para cada ponto**.

---

## Fontes citadas nesta parte

### Método e fundamentação de engenharia
- **Kang E. & Schaumont P. (2008)** — *Domain-specific multiprocessor design for embedded video processing*. Proc. DATE. [dl.acm.org/doi/10.1145/1377972.1377991](https://dl.acm.org/doi/10.1145/1377972.1377991).
- **Bass L., Clements P., Kazman R. (2021)** — *Software Architecture in Practice*, 4ª ed., Addison-Wesley. [Pearson](https://www.pearson.com/store/p/software-architecture-in-practice/P200000005869).

### Front-end de aquisição — Categoria I (PIR)
- **Klemens J. C. et al. (2021)** — *WiseEye: A Raspberry Pi-based, low-cost camera trap with a customizable motion-detection trigger*. **Methods in Ecology and Evolution** 12(8):1456–1466. [BES journal](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.13607).
- **Glover-Kapfer P., Soto-Navarro C. A., Wearn O. R. (2019)** — *Camera-trapping version 3.0*. **Remote Sensing in Ecology and Conservation** 5(3):209–223. [DOI](https://doi.org/10.1002/rse2.106).
- **PMC 10945077 (2024)** — *A portable Raspberry Pi-based camera set-up to record behaviour of small terrestrial animals*. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10945077/).
- **TP-Link Tapo C400** — produto e especificações. [tp-link.com](https://www.tp-link.com/us/home-networking/cloud-camera/tapo-c400/).
- **Reolink Argus PT Ultra** — produto. [reolink.com](https://reolink.com/product/argus-pt-ultra/); tabela de bateria: [support.reolink.com](https://support.reolink.com/articles/900000421243-How-Long-Does-the-Battery-Last-for-Battery-powered-Cameras/).
- **Wyze community forum (2024)** — *SD card recording while offline*. [forums.wyze.com](https://forums.wyze.com/t/sd-card-recording-while-offline/309334).

### Front-end de aquisição — Categoria II (VMD)
- **Frigate NVR** — *Realtime Object Detection for IP Cameras*. [frigate.video](https://frigate.video); [docs.frigate.video](https://docs.frigate.video); [github.com/blakeblackshear/frigate](https://github.com/blakeblackshear/frigate).
- **XDA Developers (2025)** — *How I made my own wildlife camera with a Raspberry Pi*. [xda-developers.com](https://www.xda-developers.com/i-made-a-wildlife-camera-with-a-raspberry-pi/).
- **r/computervision (2025)** — *How to better suppress tree motion but keep animal motion (MOG2 tuning)*. [reddit.com/r/computervision](https://www.reddit.com/r/computervision/comments/1p4hmpn/how_to_better_suppress_treemotion_but_keep_animal_motion/).

### Câmeras IP genéricas / SoCs OEM (referência para Perfil E)
- **Unifore (2020)** — *Anyka AK3918EV300 1080p IP Camera Solution*. [unifore.net](https://www.unifore.net/ip-video-surveillance/anyka-ak3918ev300-1080p-ip-camera-solution.html).
- **JayGoldberg/anyka-cams (GitHub, 2021)** — *Investigation of Anyka 3918E cameras (OUCAM P1/P2)*. [github.com/JayGoldberg/anyka-cams](https://github.com/JayGoldberg/anyka-cams).
- **MuhammedKalkan/Anyka-Camera-Firmware (GitHub, 2024)** — Firmware aberto para câmeras Anyka. [github.com/MuhammedKalkan/Anyka-Camera-Firmware](https://github.com/MuhammedKalkan/Anyka-Camera-Firmware).
- **VGerris/Anyka_ak3918_hacking_journey (GitHub, 2024)** — Notas de engenharia reversa de câmera AK3918. [github.com/VGerris/Anyka_ak3918_hacking_journey](https://github.com/VGerris/Anyka_ak3918_hacking_journey).
- **OpenIPC project** — Firmware aberto multi-SoC (suporta Anyka, HiSilicon, Goke, XiongMai). [openipc.org](https://openipc.org); [openipc.github.io](https://openipc.github.io).
- **iSpyConnect** — *Catálogo de URLs RTSP para câmeras IP chinesas*. [ispyconnect.com/pt/camera/china](https://www.ispyconnect.com/pt/camera/china).
- **ipcamtalk (2022)** — *How to get stream from a chinese model AK3918E V300*. [ipcamtalk.com](https://ipcamtalk.com/threads/how-to-get-stream-from-a-chinese-model-ak3918e-v300.62319/).
- **Home Assistant community (2021)** — *Add ICSEE camera to HA (RTSP)*. [community.home-assistant.io](https://community.home-assistant.io/t/add-icsee-camera-to-ha-rtsp/290852).
- **reddit r/hardwarehacking (2024)** — *Cheap chinese IP cam, help with programming to activate RTSP*. [reddit.com/r/hardwarehacking](https://www.reddit.com/r/hardwarehacking/comments/1bex821/cheap_chinese_ip_cam_help_with_programming_to/).

### Detecção (E1)
- **agentmorris/MegaDetector (2023–2025)** — Inference benchmarks. [github.com/agentmorris/MegaDetector](https://github.com/agentmorris/MegaDetector/blob/main/megadetector.md).
- **MIT-AI4Healthcare / MDv6c-Extra** — HuggingFace release. [huggingface.co](https://huggingface.co/MIT-AI4Healthcare/MDv6c-Extra).
- **microsoft/CameraTraps** — MegaDetector v6 release notes. [github.com/microsoft/CameraTraps](https://github.com/microsoft/CameraTraps/blob/main/megadetector.md).
- **Ultralytics (2025)** — YOLO26 vs. YOLO11 benchmarks. [docs.ultralytics.com](https://docs.ultralytics.com/compare/yolo26-vs-yolo11/).
- **r/raspberry_pi (2024)** — *YOLOv8s FPS Benchmark on Raspberry Pi 5 + AI Kit (Hailo-8L)*. [reddit.com/r/raspberry_pi](https://www.reddit.com/r/raspberry_pi/comments/1e5zycb/yolov8s_fps_benchmark_and_performance_comparison/).
- **Ultralytics (2024)** — *Coral Edge TPU on Raspberry Pi with YOLO*. [docs.ultralytics.com](https://docs.ultralytics.com/guides/coral-edge-tpu-on-raspberry-pi/).
- **Coral (Google)** — *Edge TPU products and benchmarks*. [coral.ai/products](https://www.coral.ai/products/).
