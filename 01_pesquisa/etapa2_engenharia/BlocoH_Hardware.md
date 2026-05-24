# Etapa 2 — Bloco H: Hardware (embasamento conceitual)

> **Escopo deste bloco**: este bloco é deliberadamente **breve e conceitual**. Ele estabelece *três cenários* de hardware (baixo custo, médio, ideal) para sustentar as escolhas de software (Bloco S) e o plano de implementação (Bloco P). Não há aprofundamento em projeto eletrônico, dimensionamento solar fino ou layout de PCB — esses itens são citados e marcados como **trabalho futuro do implementador**, em coerência com a diretriz do TCC de não fazer instalação física real.
>
> **Referência cruzada**: as escolhas justificam-se contra os requisitos consolidados em [A2.0 — Requisitos do sistema](./A2.0_requisitos_sistema.md), em especial **RNF-08** (custo ≤ R$ 2.500/nó no teto), **RNF-09** (custo total do piloto ≤ R$ 15.000), **RNF-12** (autonomia ≥ 7 dias quando off-grid), **RNF-14** (visão noturna IR), **RNF-15** (proteção IP66) e **RP-08** (interoperabilidade RTSP/ONVIF).

## 1. Premissas que condicionam todo o hardware

Antes de comparar componentes, três premissas operacionais derivadas das diretrizes do projeto:

**P1. Densidade-alvo conhecida e infraestrutura disponível.** O Campus 2 da USP São Carlos é uma área urbana com **~50 gatos** distribuídos em **~10 pontos de alimentação** mantidos pelo grupo de extensão AEX Gatosdoc2. A infraestrutura institucional (energia AC, rede Wi-Fi do campus, vigilância) está disponível em vários pontos — diferentemente do cenário clássico de armadilhas fotográficas em reservas remotas ([Cove et al., 2022](https://doi.org/10.1002/ece3.8771); [Meek et al., 2016](https://doi.org/10.1071/AM15014)). Isso permite cenários mistos: parte dos pontos pode ser servida por **câmeras IP cabeadas ou Wi-Fi** com energia AC, e apenas pontos mais isolados exigem nós autônomos.

**P2. Rotação amostral provável.** Como a quantidade de câmeras instaladas inicialmente deve ser **menor que o número de pontos**, o plano operacional (Bloco P) prevê **rotação amostral** — cada câmera cobre um ponto por um período, depois é deslocada. Isso favorece equipamentos **fáceis de remontar e calibrar** e desencoraja instalações permanentes complexas.

**P3. Volume e perfil de uso dos dados.** O sistema é destinado a **detectar gatos, classificar a espécie e tentar re-identificar indivíduos**, não a vigilância contínua de área. Portanto:

- O detector pode operar **disparado por movimento** (PIR ou *motion detection* por software) para reduzir volume.
- A câmera precisa de **boa qualidade de imagem em close-medium** (1-5 m), porque a re-ID precisa de detalhes de pelagem ([Akbar et al., 2025](https://doi.org/10.3390/jimaging11080274)).
- Áudio é dispensável; visão noturna IR é **obrigatória** (gatos têm atividade crepuscular e noturna marcada, conforme [Cove et al., 2022](https://doi.org/10.1002/ece3.8771)).

## 2. Os três cenários de hardware

A tabela abaixo sintetiza os três cenários. As linhas seguintes detalham cada um em parágrafos curtos.

| Item | **Cenário A — Baixo custo** | **Cenário B — Médio** | **Cenário C — Ideal** |
|---|---|---|---|
| **Câmera** | IP-CAM Wi-Fi indoor/semi-outdoor barata (Tapo C100, Mibo iC4) | IP-CAM outdoor IP66 PoE (Intelbras iM7 S, WCAM bullet) **ou** Raspberry Pi + módulo IMX219/v2 em caixa estanque | Raspberry Pi 5 + módulo HQ IMX477 com lente CS-mount em caixa IP66, **ou** trail camera profissional (Bushnell Core S-4K) |
| **Processamento por nó** | Nenhum local — vídeo flui via RTSP para **PC central** (i7 do Felipi) | Borda leve: RPi Zero 2W ou RPi 4 (4 GB) executa detecção simples; servidor central faz re-ID | Borda completa: RPi 5 (8 GB) ou Jetson Orin Nano executa pipeline completo (detect+classif+embedding), servidor só agrega |
| **Armazenamento** | Disco do PC central; câmera com micro-SD opcional | Micro-SD industrial 64 GB no nó + NAS/servidor | SSD M.2 no nó (via HAT) + servidor central com RAID |
| **Conectividade** | Wi-Fi do campus | Wi-Fi do campus ou Ethernet/PoE | Ethernet/PoE em pontos cabeados; 4G/LTE-M ou LoRaWAN¹ em pontos isolados |
| **Energia** | AC de tomada do campus | AC + UPS pequeno (NoBreak 600 VA) | AC com UPS **ou** painel solar 30-50 Wp + LiFePO4 12V/20 Ah para nós off-grid |
| **Visão noturna IR** | Sim (built-in nas Tapo/Mibo) | Sim (built-in) ou módulo IR add-on para RPi | Sim, com leds IR de alta potência ou IR-cut mecânico |
| **Proteção ambiental** | Improvisada (gabinete plástico) | IP66 nativa ou caixa selada com janela óptica | IP66 com radiador passivo, anti-vandalismo, anti-pombo |
| **Custo por ponto (estimado)** | **R$ 250 – R$ 450** | **R$ 700 – R$ 1.500** | **R$ 2.000 – R$ 3.500** |
| **Piloto 5 pontos (estimado)** | **~R$ 2.000** + PC já existente | **~R$ 6.000** | **~R$ 14.000** |

¹ LoRaWAN não transporta vídeo — apenas metadados/eventos. Para câmeras off-grid sem 4G, a alternativa realista é **gravação local + sincronização presencial periódica**, citada conceitualmente em §6.

### 2.1 Cenário A — Baixo custo (IP-CAM Wi-Fi + PC central)

**Filosofia**: minimizar custo de hardware concentrando o processamento em **um único PC** já existente. Cada ponto recebe apenas uma câmera IP residencial barata, que expõe um stream RTSP² para o PC central.

**Exemplos de câmera**: TP-Link Tapo C100 (R$ 175-211 [Magazine Luiza, 2026](https://www.magazineluiza.com.br/busca/camera+full+hd+tapo+c100+tp+link/); [Kalunga, 2026](https://www.kalunga.com.br/prod/camera-de-seguranca-wi-fi-full-hd-tapo-c100-tp-link-cx-1-un/610809)), Intelbras Mibo iC3/iC4 (faixa similar). Resolução Full HD 1080p, IR built-in, ONVIF/RTSP suportado em firmware atualizado ([iSpyConnect — Intelbras Setup Guide](https://www.ispyconnect.com/camera/intelbras); [Intelbras — Tutorial Mibo Cam RTSP](https://backend.intelbras.com/sites/default/files/2021-08/mibo-cam-rtsp.pdf)).

**Vantagens**:

- Custo mínimo por nó.
- Câmeras vendidas em qualquer eletrônica brasileira, garantia formal, suporte do fabricante.
- Felipi pode testar o protocolo RTSP imediatamente no seu i7 — alimenta o Bloco S sem precisar comprar nada.

**Limitações**:

- **Sem IP66 nativo** na maioria dos modelos baratos — exigirá gabinete improvisado para uso outdoor.
- Dependência total da **rede Wi-Fi do campus**; quedas de rede paralisam o ponto.
- Latência e qualidade do stream variam com a banda; em períodos de pico pode haver degradação que prejudica a re-ID.
- Câmeras desse segmento têm **lentes fixas grande-angulares** — bom para vigilância, ruim para captar detalhes de pelagem para re-ID. Mitigação: posicionar a câmera mais perto do ponto de alimentação.

**Atende quais requisitos de A2.0**: RNF-08 (folga grande), RP-08 (RTSP nativo). **Não atende plenamente**: RNF-15 (IP66), RNF-12 (autonomia off-grid — não aplicável neste cenário, exige AC).

² *RTSP — Real Time Streaming Protocol*. Protocolo padrão de streaming de vídeo IP em tempo real. Captura via `ffmpeg`, `OpenCV` ou GStreamer.[^rtsp]

### 2.2 Cenário B — Médio (IP-CAM outdoor PoE ou Raspberry em caixa estanque)

**Filosofia**: equilibrar custo e robustez. Câmeras outdoor de **classificação IP66** alimentadas por PoE ou Wi-Fi com adaptador AC ambiental, com **processamento parcial em borda** para reduzir tráfego.

**Variante B1 — IP-CAM outdoor comercial**: Intelbras iM7 S Full Color IP66 (R$ 389,90 [Intelbras, 2026](https://loja.intelbras.com.br/camera-externa-im7s-full-color/p)), câmeras WEG WCAM bullet 2K PoE (R$ 678,90 [Andra, 2026](https://www.andra.com.br/camera_ip_bullet_2k_2-8mm_ip66_poe_wcam_ip-h042-b71_16994357_weg/p)). Modelos com ONVIF/RTSP. Vantagem: IP66 nativo, instalação outdoor sem improviso, IR de fábrica. Desvantagem: ainda lente fixa, ainda dependente de rede.

**Variante B2 — Raspberry Pi + módulo IMX219/v2 em caixa estanque**: monta-se uma câmera customizada. Esta é a base da subseção §3 ("Câmera modelo do projeto"). Vantagens: **lente trocável**, controle total do firmware, possibilidade de **detecção local com MegaDetector ou YOLO leve** antes de enviar dados. Desvantagens: o preço do Raspberry Pi subiu fortemente em 2026 (RPi 5 8 GB chegou a US$ 125 MSRP, [Notebookcheck, 2026](https://www.notebookcheck.info/Raspberry-Pi-5-agora-custa-ate-US-205-devido-a-crise-de-RAM.1218279.0.html); na RoboCore o RPi 5 8 GB está em torno de **R$ 1.000+** sem acessórios³).

³ Como referência histórica e operacional, há cenários onde o **RPi Zero 2W** (US$ 15-20) substitui o RPi 5 quando o objetivo é apenas capturar e fazer pré-filtragem com motion detection — vide o projeto [Cat Traption](https://discourse.nixos.org/t/cross-build-raspberry-pi-0-2w-using-camera-v2/75066) que usa exatamente essa topologia para trap-neuter-return de gatos, descartando capturas de outras espécies. Para o nosso uso, no entanto, a inferência de classificação felis-catus já exige mais do que o Zero 2W oferece, então B2 assume RPi 4 ou 5.

**Processamento**: Felipi roda detecção e classificação leves no nó (ex.: MobileNet/YOLO-nano) e envia apenas eventos relevantes para o servidor. Re-ID continua no servidor por exigir embeddings mais pesados.

**Atende A2.0**: RNF-08 (dentro do teto), RNF-15 (em B1 nativamente; em B2 com caixa adequada), RP-08 (RTSP nativo em B1; via `rpicam-apps` + GStreamer em B2). **Atende parcialmente**: RNF-12 (UPS pequeno cobre quedas curtas, não autonomia de 7 dias).

### 2.3 Cenário C — Ideal (nó dedicado com câmera HQ + autonomia)

**Filosofia**: maximizar qualidade de imagem, autonomia e capacidade de processamento em borda. É a referência para os pontos mais críticos da colônia (ex.: ponto de maior diversidade de indivíduos).

**Configurações típicas**:

- **C1 — Pi-camera HQ**: Raspberry Pi 5 (8 ou 16 GB) + módulo Raspberry Pi HQ Camera (sensor Sony IMX477 12,3 MP, lente C/CS-mount trocável; [raspberrypi.com](https://www.raspberrypi.com/products/raspberry-pi-high-quality-camera/)) + caixa IP66 com janela óptica + opcional: módulo IR cut e leds IR.
- **C2 — Trail camera profissional**: Bushnell Core S-4K No-Glow (R$ ~4.000 em revendedores nacionais, [Lognature, 2026](https://lognature.com.br/produtos/camera-trap-bushnell-core-s-4k-no-glow-30mp-ate-512gb-119949c/)). Vantagem: produto integrado, à prova de tempo, otimizado para captura disparada por PIR. Desvantagem: **fechada** — não permite executar nosso software de detecção/re-ID em borda; serve apenas como capturadora, com pipeline rodando depois no servidor.
- **C3 — Jetson Orin Nano**: para os 1-2 pontos mais críticos, um Jetson Orin Nano Super (US$ 249 oficial, [NVIDIA](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/)) executa o **pipeline completo edge** com baixíssima latência. Pode ser overkill para este TCC mas serve de teto técnico de referência.

**Energia em C**: pontos ideais combinam **AC + UPS** quando possível; em pontos isolados, **painel solar 30-50 Wp + controlador MPPT + LiFePO4 12V/20 Ah** é o padrão usado em literatura comparável ([Bennett et al., 2024 — HelioCase](https://ieeexplore.ieee.org/document/10753937/); [PICT, Droissart et al., 2021](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.13618); [Reichley — Solar Pi camera, raspberrypi.com](https://www.raspberrypi.com/news/solar-powered-nature-camera/)). O dimensionamento detalhado fica como **trabalho futuro do implementador**.

**Atende A2.0**: todos os requisitos não-funcionais, incluindo RNF-12 (autonomia ≥ 7 dias com a configuração solar) e RNF-15.

## 3. Câmera modelo do projeto (sub-bloco)

Como o TCC não compra equipamento, propõe-se uma **câmera modelo de referência** — uma especificação aberta e construtível que serve de bússola para qualquer implementação futura do plano. Inspira-se em projetos open-source comparáveis e adapta o foco para **gatos comunitários** em vez de pequena fauna silvestre.

### 3.1 Projetos de referência

- **PICT** ([Droissart et al., 2021](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.13618)) — RPi Zero + caixa estanque + powerbank, <100 USD. Demonstra que modularidade e custo baixo são compatíveis.
- **WiseEye** ([Nazir et al., 2017](https://dx.plos.org/10.1371/journal.pone.0169758)) — plataforma RPi com **sensing confirmatório** (PIR + radar + pixel-change) para reduzir falsos positivos. Princípio aproveitável aqui.
- **HelioCase** ([Bennett et al., 2024](https://ieeexplore.ieee.org/document/10753937/)) — RPi solar com LiFePO4 e gravação 24h em SSD externo; demonstra autonomia plena off-grid.
- **pirecorder** ([Jolles, 2020](https://joss.theoj.org/papers/10.21105/joss.02584)) — biblioteca Python para controle uniforme de captura em RPi, citada na ciência aberta. Pode ser reaproveitada no firmware.
- **Camera trap RPi para insetos** ([Lanfear, raspberrytrap GitHub](https://github.com/roblanf/raspberrytrap)) — exemplo prático de construção mecânica simples.

### 3.2 Especificação proposta da câmera modelo (referência conceitual)

| Camada | Componente | Justificativa |
|---|---|---|
| **Sensor** | Raspberry Pi HQ Camera (Sony IMX477, 12,3 MP) **OU** módulo IMX219 v2 (8 MP) para variantes mais baratas | Lente trocável (C/CS-mount no HQ; M12 no v2). Necessário para captar detalhes de pelagem de gatos em distância de alimentação (1-3 m). |
| **Lente** | 6 mm ou 8 mm de comprimento focal (CS-mount, ~R$ 200-400) | Calculado para enquadrar o ponto de alimentação com distância de instalação típica de 2-3 m. Substituível em campo. |
| **Iluminação noturna** | Anel IR 850 nm ou 940 nm (940 nm = no-glow, invisível aos gatos) | Gatos têm atividade crepuscular/noturna marcada ([Cove 2022](https://doi.org/10.1002/ece3.8771)). 940 nm é preferível para não estressar (Steagall et al., 2023 sobre estresse felino; em [Akbar 2025](https://doi.org/10.3390/jimaging11080274) imagens IR funcionam para re-ID corporal). |
| **IR cut mecânico** | Filtro com servo (presente nos módulos HQ "PoV" ou solução DIY) | Cor de dia, NIR de noite. |
| **SBC (compute)** | RPi 5 (8 GB) em B2/C1; RPi 4 (4 GB) como mínimo aceitável | Processa MegaDetector v6 a ~1 FPS em CPU, suficiente para captura disparada por evento (não 24/7 vídeo) — alinhado a RF-04 e ao perfil de uso descrito no Bloco S. |
| **Disparo (trigger)** | (a) **Software** — *motion detection* por subtração de frames (`OpenCV BackgroundSubtractorMOG2`); (b) **Hardware** — sensor PIR HC-SR501 (R$ 10-25) **ou** PIR + microondas redundante (princípio WiseEye) | Reduz volume de armazenamento e energia. Felipi pode testar (a) sem nenhum custo. |
| **Armazenamento local** | Cartão micro-SD industrial 64-128 GB (ou SSD M.2 via HAT em C) | Buffer para quando a rede falhar. |
| **Conectividade** | Wi-Fi (built-in no RPi 5) **ou** Ethernet (preferida quando há infraestrutura) | RTSP server local via `rpicam-vid` + `gst-rtsp-server`, para interoperabilidade com o Bloco S. |
| **Energia** | 5V/3A USB-C (RPi 5) com adaptador AC; UPS HAT opcional; painel solar 30-50 Wp + LiFePO4 12V/20 Ah para off-grid | Modular: a mesma câmera modelo serve cenário B com AC e cenário C com solar. |
| **Gabinete** | Caixa de PVC ou ABS com tampa transparente para a lente, vedação IP66 com gaxeta, prensa-cabos | Inspirado em PICT e raspberrytrap. Pode ser impressa em 3D ou comprada pronta. |

### 3.3 Custo da câmera modelo

Estimativa **conceitual** (preços de varejo brasileiro 2026, sem otimização de compra agrupada):

| Item | Versão econômica | Versão completa |
|---|---|---|
| SBC (RPi 4 4 GB ou RPi 5 8 GB) | R$ 500 (RPi 4) | R$ 1.000-1.300 (RPi 5) |
| Câmera (IMX219 v2 ou IMX477 HQ) | R$ 150 | R$ 450-550 |
| Lente (M12 padrão ou CS-mount 6mm) | (incluso no v2) | R$ 250-400 |
| PIR + anel IR + IR cut | R$ 60-100 | R$ 150-250 |
| micro-SD industrial 64 GB | R$ 80 | R$ 150 (128 GB industrial) |
| Caixa IP66 + gaxetas + prensa-cabos | R$ 80 | R$ 150 |
| Fonte AC ou solar + bateria | R$ 50 (fonte) | R$ 600-900 (solar+LiFePO4) |
| **Total estimado** | **~R$ 920** | **~R$ 2.800-3.400** |

A versão econômica encaixa em **B2**; a completa, em **C1**. A diferença prática para a re-ID está na **lente + sensor HQ**, justificada porque Akbar 2025 demonstrou que partes corporais (cabeça, flanco, dorso) precisam de detalhe suficiente para gerar embeddings distintivos.

## 4. Comparativo síntese contra os requisitos de A2.0

| Requisito chave | Cenário A | Cenário B | Cenário C |
|---|---|---|---|
| RNF-08 — Custo nó ≤ R$ 2.500 | ✅ folgado | ✅ | ✅ no limite |
| RNF-09 — Piloto total ≤ R$ 15.000 | ✅ folgado (~R$ 2.000) | ✅ (~R$ 6.000) | ✅ no limite (~R$ 14.000) |
| RNF-12 — Autonomia ≥ 7 dias off-grid | ❌ N/A (AC) | ⚠ parcial (UPS) | ✅ (solar+LiFePO4) |
| RNF-14 — Visão noturna IR | ✅ built-in | ✅ | ✅ |
| RNF-15 — IP66 | ⚠ improvisado | ✅ | ✅ |
| RP-08 — RTSP/ONVIF nativo | ✅ | ✅ | ✅ (RPi via gst-rtsp-server) |
| Qualidade óptica para re-ID | ⚠ lente fixa angular | ✅ ajustável (B2) | ✅ HQ + lente escolhida |
| Replicabilidade / open-hardware | ⚠ caixa-preta | ⚠ misto | ✅ totalmente |

## 5. Processamento, armazenamento, conectividade e energia — síntese curta

Como o foco é o software (Bloco S), os quatro eixos abaixo são tratados em parágrafos curtos. Detalhamento profundo é **trabalho futuro do implementador**.

**Processamento.** Há um espectro contínuo: (a) sem processamento no nó (Cenário A — tudo no PC central), (b) pré-filtragem leve (Cenário B — RPi 4/5 com motion detection e talvez detecção MobileNet/YOLO-nano), (c) pipeline completo em borda (Cenário C — RPi 5 ou Jetson Orin Nano executando detecção + classificação + extração de embedding). O ponto de equilíbrio para este TCC é provavelmente **(b)**, com PC central executando re-ID em batch — descrito em detalhe no Bloco S.

**Armazenamento.** Em campo, **cartões micro-SD industriais** (Sandisk High Endurance, Samsung PRO Endurance — R$ 80-200 para 64-256 GB) são padrão no segmento de câmeras de vigilância. Para nós críticos, **SSD M.2 via HAT** no RPi 5 é referência (HelioCase usa SSD externo). No servidor central, qualquer disco de PC moderno (1-2 TB) cobre o piloto.

**Conectividade.** Em ordem de preferência operacional para este projeto: **Ethernet/PoE** (quando o ponto está perto de tomada de rede do campus) > **Wi-Fi do campus** (maior parte dos pontos) > **4G/LTE-M** (pontos isolados, com chip pré-pago dedicado) > **LoRaWAN** (apenas para metadados/eventos, não vídeo — possível trabalho futuro, fora do escopo do TCC). O Bloco P endereça a topologia de rede.

**Energia.** Três modos: **AC de tomada** (maioria dos pontos do campus), **AC + UPS** (resistência a quedas curtas), **solar + LiFePO4** (off-grid). O dimensionamento solar segue regras clássicas (consumo médio × dias de autonomia × fator de descarga ≈ 30%) — exemplificadas em [HelioCase](https://ieeexplore.ieee.org/document/10753937/) e [Bennett's solar Pi](https://www.raspberrypi.com/news/solar-powered-nature-camera/). **Cálculo detalhado é trabalho futuro.**

## 6. Limitações conhecidas e itens fora do escopo (citação conceitual)

Para honrar a diretriz "partes muito específicas podem ser citadas a nível conceitual", listo abaixo o que **deliberadamente não aprofundo**:

- **Projeto eletrônico / PCB**: a câmera modelo é descrita por especificação de componentes off-the-shelf, não por esquemático elétrico próprio. → trabalho futuro do implementador.
- **Dimensionamento solar fino**: cita-se a topologia (PV + MPPT + LiFePO4) e ordens de grandeza, não calculo a curva W/h por mês para São Carlos. Referências: literatura comparável + dados da CRESESB/INPE quando for implementar.
- **LoRaWAN end-to-end**: mencionado como opção para transmitir **metadados/eventos** de pontos isolados (não vídeo). Requer gateway no campus e parceria com o LSI-TEC/ICMC. → trabalho futuro.
- **Alimentador inteligente físico** (RFID, comporta motorizada, balança): descrito conceitualmente no Bloco P; engenharia mecatrônica detalhada **fora do escopo do TCC** (FGS rebaixada a bônus opcional).
- **Anti-vandalismo e anti-pombo (mecânica)**: princípios apenas (caixa em altura ≥ 2,5 m, fixação com parafuso de segurança, malha contra pombos no ponto de alimentação). Projeto mecânico fica para implementador.

## 7. Conclusão do Bloco H

Recomenda-se um **piloto misto**: a maioria dos pontos no **Cenário A** (já testável no PC do Felipi durante este TCC, com IP-CAM Tapo C100 ou similar), **1-2 pontos críticos** projetados para o **Cenário B/C** como referência de qualidade, e a **câmera modelo do projeto (§3)** documentada como artefato aberto e reaproveitável.

Essa estratégia:

- mantém o piloto **abaixo de R$ 5.000-6.000** (folga em RNF-09);
- permite que o Bloco S (software) seja **testado já com câmeras IP comuns** via RTSP, sem dependência de hardware especial;
- entrega ao Gatosdoc2 e ao orientador um **caminho de upgrade** claro (do Cenário A para o C) que pode ser percorrido em ondas de financiamento sucessivas.

A escolha final por ponto será refinada no Bloco P, à luz da planta do campus e da rotação amostral.

---

[^rtsp]: **RTSP — Real Time Streaming Protocol**. Padrão IETF (RFC 2326/7826) para controle de streams de vídeo em rede IP. Suportado nativamente por praticamente todas as câmeras IP comerciais — incluindo modelos populares no Brasil como TP-Link Tapo, Intelbras Mibo e WEG WCAM — e por bibliotecas open-source como `ffmpeg`, `OpenCV` e GStreamer. É a interface de integração preferida deste projeto (vide RP-08).

## Fontes citadas neste bloco

### Produtos e preços (Brasil, 2026)

- **TP-Link Tapo C100** — Magazine Luiza, [busca em fev/2026](https://www.magazineluiza.com.br/busca/camera+full+hd+tapo+c100+tp+link/); Kalunga, [oferta R$ 153-166](https://www.kalunga.com.br/prod/camera-de-seguranca-wi-fi-full-hd-tapo-c100-tp-link-cx-1-un/610809).
- **Intelbras iM7 S Full Color IP66** — [loja oficial Intelbras, R$ 389,90](https://loja.intelbras.com.br/camera-externa-im7s-full-color/p).
- **Intelbras Mibo / RTSP** — [tutorial técnico Intelbras (PDF)](https://backend.intelbras.com/sites/default/files/2021-08/mibo-cam-rtsp.pdf); [iSpyConnect — Intelbras Setup Guide](https://www.ispyconnect.com/camera/intelbras).
- **WEG WCAM IP-H042-B71 PoE bullet 2K IP66** — [Andra, R$ 678,90](https://www.andra.com.br/camera_ip_bullet_2k_2-8mm_ip66_poe_wcam_ip-h042-b71_16994357_weg/p).
- **Bushnell Core S-4K No-Glow 30 MP** — [Lognature.com.br](https://lognature.com.br/produtos/camera-trap-bushnell-core-s-4k-no-glow-30mp-ate-512gb-119949c/).
- **Raspberry Pi 5 8 GB** — [RoboCore, importador BR](https://www.robocore.net/placa-raspberry-pi/raspberry-pi-5-8gb); preço oficial atualizado em [Notebookcheck, fev/2026](https://www.notebookcheck.info/Raspberry-Pi-5-agora-custa-ate-US-205-devido-a-crise-de-RAM.1218279.0.html).
- **Raspberry Pi HQ Camera (IMX477)** — [raspberrypi.com/produto](https://www.raspberrypi.com/products/raspberry-pi-high-quality-camera/); [Waveshare ficha técnica](https://www.waveshare.com/raspberry-pi-hq-camera.htm).
- **Jetson Orin Nano Super Developer Kit** — [NVIDIA, US$ 249](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/).
- **ESP32-CAM AI Thinker** — [ficha Ai-Thinker](https://vdoc.ai-thinker.com/en/esp32-cam).

### Projetos open-source de referência

- **PICT** — Droissart V., Azandi L. N., Onguene E. R., Savignac M., Smith T., Deblauwe V. (2021). *PICT: A low-cost, modular, open-source camera trap system to study plant–insect interactions*. **Methods in Ecology and Evolution**. [doi:10.1111/2041-210X.13618](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.13618).
- **WiseEye** — Nazir S., Newey S., Irvine R., Verdicchio F., Davidson P., Fairhurst G., van der Wal R. (2017). *WiseEye: Next Generation Expandable and Programmable Camera Trap Platform for Wildlife Research*. **PLOS ONE**. [doi:10.1371/journal.pone.0169758](https://dx.plos.org/10.1371/journal.pone.0169758).
- **HelioCase** — Bennett K., Vincent R. E., Bennett A., Triantafyllou M. S. (2024). *Deployment of a Solar-Powered Field Camera for Monitoring Living Marine Resources*. **OCEANS 2024**. [doi:10.1109/OCEANS55160.2024.10753937](https://ieeexplore.ieee.org/document/10753937/).
- **pirecorder** — Jolles J. (2020). *pirecorder: Controlled and automated image and video recording with the raspberry pi*. **Journal of Open Source Software**. [doi:10.21105/joss.02584](https://joss.theoj.org/papers/10.21105/joss.02584).
- **raspberrytrap** — Lanfear R. *Raspberry Pi motion-capture camera trap for very small animals*. [GitHub roblanf/raspberrytrap](https://github.com/roblanf/raspberrytrap).
- **Solar Pi nature camera** — *Build a solar-powered nature camera for your garden*. [raspberrypi.com news, 2018](https://www.raspberrypi.com/news/solar-powered-nature-camera/).
- **Cat Traption (TNR cats com RPi Zero 2W)** — discussão técnica em [discourse.nixos.org, fev/2026](https://discourse.nixos.org/t/cross-build-raspberry-pi-0-2w-using-camera-v2/75066).
- **ML-based wildlife camera with ESP32-CAM** — *Pertanika J. Sci. Technol.* 33(4), 2025. [PDF](http://www.pertanika.upm.edu.my/resources/files/Pertanika%20PAPERS/JST%20Vol.%2033%20(4)%20Jul.%202025/05%20JST-5510-2024.pdf).

### Referências cruzadas com a Etapa 1

- **Akbar M. S., Rees N., Fleming P. A. (2025)** — re-ID de gatos ferais por partes corporais. [doi:10.3390/jimaging11080274](https://doi.org/10.3390/jimaging11080274). → justifica exigência de detalhe óptico para re-ID.
- **Cove M. V. et al. (2022)** — atividade de gatos domésticos em camera-traps. [doi:10.1002/ece3.8771](https://doi.org/10.1002/ece3.8771). → justifica IR noturno como obrigatório.
- **Meek P. D. et al. (2016)** — boas práticas em camera-trapping. [doi:10.1071/AM15014](https://doi.org/10.1071/AM15014). → orienta posicionamento e seleção.

### Referência de A2.0

- **A2.0 — Requisitos do sistema**: arquivo local `/etapa2/A2.0_requisitos_sistema.md`. Requisitos RF-04, RNF-08, RNF-09, RNF-12, RNF-14, RNF-15, RP-08 são os principais referenciados aqui.
