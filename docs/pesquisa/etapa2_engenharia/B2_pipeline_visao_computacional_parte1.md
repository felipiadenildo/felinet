# Etapa 2 — B2 (Parte 1/3): Pipeline conceitual de visão computacional

> **Recorte desta entrega (B2.1 + B2.2 + B2.3).** Esta parte cobre o **pipeline geral** (B2.1), o estágio de **aquisição** (B2.2) e o estágio de **detecção genérica de animal** (B2.3). As partes 2/3 (classificação de espécie, re-identificação, pré-processamento) e 3/3 (persistência, métricas, plano de testes) virão nas próximas iterações.
>
> **Princípio do bloco B2 — pipeline-agnóstico em relação ao hardware de captura.** B2 define **o quê** o sistema computa e **com quais modelos**, sem ainda decidir **onde** cada estágio roda (borda × servidor × híbrido). A consequência prática é fundamental: **o core de processamento (E1–E4) é idêntico em todos os perfis de ponto** (OFF-SD, NET, AC, AC+NET — ver B1). A diferença entre uma câmera trail dedicada com PIR e uma IPCAM barata sem PIR fica **encapsulada inteiramente no estágio E0 (ingestão)** e em duas sub-rotinas de E2.6 (pré-processamento). Isso é projeto deliberado, não acidente, e é o que permite escalar o sistema com hardware heterogêneo.
>
> **Revisão 14/maio/2026.** Esta versão substitui a nomenclatura grega de perfis (P-α/β/γ/δ) pela nomenclatura funcional definitiva do B1 v2 — **OFF-SD** (caso primário no Campus 2), **NET**, **AC**, **AC+NET**. Trata o **OFF-SD com IPCAM barata + cartão SD + troca por voluntário** como caso central, e o trail-camera-com-PIR como caso de referência de qualidade.

---

## B2.1 Pipeline conceitual de cinco estágios

### B2.1.1 Visão geral

O sistema de monitoramento por imagem é organizado como um **pipeline em cascata** de cinco estágios independentes, cada um produzindo uma saída estruturada que serve de entrada para o próximo. Esta organização é o padrão consolidado pela literatura de camera-trapping desde [Beery, Morris & Yang (2019) — *Efficient Pipeline for Camera Trap Image Review*](https://arxiv.org/abs/1907.06772) e replicado por [DeepFaune (Rigoudy et al. 2023)](https://www.biorxiv.org/content/10.1101/2022.03.15.484324v3.full-text), [Pytorch-Wildlife / MegaDetector v6 (Microsoft 2024)](https://microsoft.github.io/CameraTraps/), [SpeciesNet / Wildlife Insights (Google 2024)](https://addaxdatascience.com/addaxai/) e [AddaxAI (Addax Data Science 2024)](https://addaxdatascience.com/addaxai/).

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE CONCEITUAL                                │
└────────────────────────────────────────────────────────────────────────────┘

  [E0]            [E1]              [E2]              [E3]            [E4]
 AQUISIÇÃO  ──►  DETECÇÃO    ──►  CLASSIFICAÇÃO ──►  RE-IDENTI-  ──►  PERSIS-
 (E2.2)         (E2.3)           DE ESPÉCIE          FICAÇÃO          TÊNCIA
                                  (E2.4)             (E2.5)           (E2.7)
   │              │                  │                  │               │
   ▼              ▼                  ▼                  ▼               ▼
 quadros     bounding-boxes     bbox + rótulo      bbox + ID         eventos +
 (RGB ou      "animal"           "felis catus"      "Gato-α-#012"     embeddings
  IR)         + score            + score            + score           + meta
                                                                    + base


              ◄────────────── PRÉ-PROCESSAMENTO (E2.6) ─────────────►
                   crop, normalização, augmentation, filtros
                   temporais — aplicado entre E1, E2, E3
```

> **Convenção de nomes.** Cada estágio recebe um identificador **E0–E4** que será reutilizado em B3, B4 e B5 para mapear as decisões de implementação.

### B2.1.2 O que cada estágio recebe e produz

| Estágio | Entrada | Saída | Função |
|---|---|---|---|
| **E0 — Aquisição** | Cena física | Quadros RGB ou IR (PNG/JPEG/H.264) com metadados (timestamp, ID do ponto, modo) | Capturar imagem **somente quando há evento de interesse**, minimizando volume de dados e consumo. |
| **E1 — Detecção** | Quadro | Lista de bounding-boxes com classe genérica (animal/humano/veículo) + score | **Filtrar imagens vazias** e localizar onde está o animal — etapa que viabiliza tudo o que vem depois. |
| **E2 — Classificação de espécie** | Crop do bounding-box | Rótulo de espécie (ex.: *Felis catus*) + score | **Aceitar só gatos**; descartar fauna não-alvo. |
| **E3 — Re-identificação** | Crop classificado como gato | ID do indivíduo (conhecido) ou marcador "desconhecido" + score | **Atribuir identidade individual** (núcleo do TCC). |
| **E4 — Persistência** | ID + crop + metadados | Linha em base de eventos; embedding na galeria | **Memória do sistema**: catálogo de indivíduos, eventos por ponto, série temporal por ID. |
| **PrePro (E2.6)** | qualquer estágio | mesmo formato pós-tratado | Cross-cutting: crop, normalização, augmentation, filtros temporais. |

### B2.1.3 Princípios de projeto adotados

1. **Cascata com filtros agressivos no início.** A grande maioria dos quadros é vazia ou contém apenas fundo. Cada estágio descarta o que não interessa para reduzir custo dos estágios subsequentes. Estudo de [Mansfield (BNL 2025)](https://www.bnl.gov/esd/wildlife/files/research/pdf/2025-mansfield-paper.pdf) mostra que detector genérico reduz ~82% das imagens vazias mantendo 99,2% das imagens com animal. Em [AnimalDetect (2024)](https://www.animaldetect.com/blog/megadetector-review-pros-cons-use-cases), MegaDetector v5 atinge precisão 0,96 e recall 0,73.
2. **Modelos genéricos antes de modelos específicos.** Detectores treinados em milhões de imagens de fauna variada generalizam melhor que modelos treinados em dataset pequeno do projeto. A classificação de espécie só vem depois (princípio do Beery 2019).
3. **Cada estágio é desacoplável.** Cada modelo pode ser trocado sem afetar os demais, desde que a interface seja respeitada. Isso permite, no plano de validação (B5), benchmarkar candidatos por estágio.
4. **Open-set por padrão em re-ID.** Como novos indivíduos aparecerão sempre que filhotes nascerem ou novos gatos chegarem à colônia, o estágio E3 precisa **declarar "desconhecido"** quando não houver match suficiente, em vez de forçar uma classificação. Este é o regime adotado pelo benchmark [AnimalCLEF 2025](https://www.imageclef.org/AnimalCLEF2025) e por [Sani, Khurana & Anand (2025)](https://arxiv.org/abs/2511.06658).
5. **Embeddings, não rótulos rígidos.** A saída de E3 é um vetor (embedding) comparado contra uma galeria, não uma classe fixa. Isso permite (a) acrescentar IDs novos sem retreino; (b) calcular similaridade explícita; (c) suportar consultas humanas ("quem é esse gato?") com top-k.
6. **Independência do hardware na conceituação.** B2 fala apenas de modelos e fluxos. A pergunta "isso roda em Raspberry Pi 5?" é deliberadamente adiada para B3.

### B2.1.4 Fluxos de dados — três modos operacionais

O mesmo pipeline conceitual atende **três modos** que serão escolhidos por ponto em B4 com base nos perfis funcionais do B1 (**OFF-SD / NET / AC / AC+NET**).

```
MODO 1 — OFFLINE COM TROCA DE MÍDIA (caso primário Campus 2)
  Câmera (PIR ou VMD firmware) → grava em cartão SD →
   voluntário coleta o cartão periodicamente →
   PC do pesquisador ingere o conteúdo → [E1..E4] em lote
  Usa: pontos OFF-SD — sem AC, sem Wi-Fi. É o caso operacional dominante
        no Campus 2. Pipeline processa em batch, não em tempo real.

MODO 2 — TUDO NO SERVIDOR / DESKTOP (via rede)
  Câmera com Wi-Fi → upload contínuo (RTSP ou push) → PC/servidor →
   [E1..E4] no servidor
  Usa: pontos NET ou AC+NET com Wi-Fi institucional disponível.

MODO 3 — HÍBRIDO COM BORDA LEVE
  Câmera + SBC local (Raspberry Pi) → borda faz [E1] (descarta vazios) →
   upload só de crops com animal → servidor faz [E2..E4]
  Usa: pontos AC+NET com necessidade de reduzir banda. Cenário ideal
        mas raro no Campus 2; documentado como evolução futura.
```

Cada modo é uma **decisão arquitetural**, não um requisito conceitual. Nos três modos o **core E1–E4 é o mesmo código**; muda apenas o **frontend de ingestão (E0)** e o gatilho da execução (job em lote pós-coleta vs. consumidor de stream).

### B2.1.5 Métricas amarradas a cada estágio

| Estágio | Métrica primária | Métrica secundária | Origem da meta |
|---|---|---|---|
| **E0** Aquisição | Recall de evento (eventos capturados / eventos reais) | Falso-positivo de trigger | A2.0 RF-01, RF-02 |
| **E1** Detecção | mAP@0,5 para classe "animal" | Latência por quadro | A2.0 RF-03 (≥ 0,90) |
| **E2** Classificação espécie | F1 para *Felis catus* | Precisão para fauna não-alvo | A2.0 RF-04 (≥ 0,90) |
| **E3** Re-ID | mAP open-set; Rank-1 closed-set | Curva de descoberta de IDs novos | A2.0 RF-05 (open-set ≥ 0,70; closed-set Rank-1 ≥ 0,80) |
| **E4** Persistência | Integridade de eventos; consistência temporal | Tempo de query top-k | A2.0 RNF-06 |

> **Estas métricas são todas observáveis no notebook do Pesquisador** (`[PLACEHOLDER-HARDWARE-NOTEBOOK]`) durante a Etapa 3 com datasets públicos. A meta numérica vem de A2.0.

---

## B2.2 Estágio E0 — Aquisição

### B2.2.1 O problema

Aquisição é **decisão de quando capturar**, não apenas como. Capturar 24/7 a 30 FPS em [~10 pontos estimados] durante 30 dias gera ordem de 78 TB de vídeo bruto — inviável. Capturar uma foto a cada 5 minutos perde os eventos rápidos. O bom projeto de aquisição **otimiza a curva recall-versus-volume**, conceito consolidado em [Glover-Kapfer, Soto-Navarro & Wearn (2019)](https://doi.org/10.1002/rse2.106) e em [Klemens et al. (2021)](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.13607).

> **Restrição de projeto reafirmada (B1 v2).** O sistema **não pode assumir PIR**. Embora o cenário ideal de qualidade de trigger seja câmeras com PIR físico, o caso primário do Campus 2 (perfil OFF-SD) usa **IPCAM baratas que podem ou não ter PIR interno** — muitas usam apenas VMD (motion-detection do firmware) ou time-lapse. O projeto **leva em consideração ambos os mecanismos** como cidadãos de primeira classe; a discussão a seguir compara as famílias para subsidiar a decisão por perfil, e a §B2.2.6 fecha a recomendação.

A literatura de camera-trapping reconhece **três famílias de trigger**:

```
                ┌──────────────────────────────────────────────────┐
                │             FAMÍLIAS DE TRIGGER                  │
                └──────────────────────────────────────────────────┘

        PIR físico                Software (visão)            Time-lapse
        ──────────                ────────────────            ──────────
   Sensor passivo IR        Frame-difference / motion       Captura periódica
   detecta calor + movim.   sobre o stream de vídeo         (1 foto/min/etc.)

   ✔ Latência ~0.1-0.5 s    ✔ Sem hardware extra            ✔ Captura animais
   ✔ Consumo mínimo         ✔ Programável                     "frios" (répteis)
   ✔ Sem CPU para detectar  ✗ Câmera sempre ligada          ✔ Captura cenários
                              (consumo alto)                   estáticos
   ✗ Falsos por vegetação   ✗ Falsos por iluminação/        ✗ Volume alto
     aquecida e veículos      sombras                         de imagens vazias
   ✗ Não dispara em vidro   ✔ Pode ser refinado por ML
```

### B2.2.2 Trigger PIR — base de referência

O PIR é o trigger **padrão histórico** das trail cameras comerciais e da pesquisa em wildlife. Funciona detectando variação de radiação infravermelha emitida por corpos com temperatura distinta do fundo. Características conhecidas:

- **Latência (trigger speed)**: 0,1 s a 2 s dependendo da câmara. [TrailCamPro (2022)](https://www.trailcampro.com/pages/trail-camera-tests) registra que as melhores câmeras comerciais ficam abaixo de 0,5 s; modelos mais antigos chegam a 1+ s.
- **WiseEye (Klemens et al. 2021)** atinge **0,44 s** (DP 0,2 s) com Raspberry Pi + PIR vs. **2,5 s** (DP 0,4 s) de uma Bushnell comercial — relevante porque, em ambiente externo com animais rápidos, 1 s de latência significa perda do quadro.
- **Falsos positivos**: vegetação aquecida pelo sol e movida pelo vento; passagem de veículos quentes; aves grandes. Mitigação: sensor de confirmação ou análise de pixel imediata, como em WiseEye.
- **Consumo**: ordem de centenas de µA quando ocioso; a câmera pode ficar em sleep até o trigger.

### B2.2.3 Trigger por software (motion-detection)

Motion-detection por software roda sobre o stream da câmera (sempre ligada) e dispara captura/gravação quando há diferença significativa entre quadros. Implementações conhecidas:

- **pikrellcam / motion** (Linux clássico) em [raspberrytrap (Lanf 2017)](https://github.com/roblanf/raspberrytrap) — frame-difference, threshold ajustável, baixo overhead em ARM.
- **OpenCV background subtraction** (MOG2, KNN) — mais robusto a iluminação variável.
- **Detector leve embutido** (YOLO-nano, MobileNet-SSD) — sem PIR; o próprio detector decide se há animal. Latência da ordem de 100–300 ms em CPU moderna.

Vantagens: sem hardware extra; programável; pode ser ajustado por ponto. Desvantagens: câmera sempre ligada (consumo maior); falsos por sombras, chuva e mudança de luz.

### B2.2.4 Time-lapse — fallback

Captura periódica (1 foto a cada N segundos/minutos) é usada por padrão para animais ectotérmicos ou cenários em que o PIR não dispara (vidro, distância). [Bø et al. (2024) — Authorea](https://www.authorea.com/users/624924/articles/647057-motion-detection-or-time-lapse-a-comparison-of-camera-trap-triggers-in-the-monitoring-of-elusive-ground-dwelling-birds) compara time-lapse vs. PIR e mostra que para aves elusivas o time-lapse tende a coletar **mais dados** com **mesma contagem populacional**. Para o nosso caso (gatos), o PIR já é suficiente; time-lapse fica como modo de calibração.

### B2.2.5 Comparativo dos triggers — síntese aplicada ao projeto

| Critério | PIR | Motion-detection software (VMD) | Time-lapse |
|---|---|---|---|
| Latência típica | 0,1–0,5 s | 0,1–0,3 s (sempre ligado) | depende do intervalo |
| Hardware extra | Sim (sensor PIR) | Não | Não |
| Consumo médio | **Muito baixo** (sleep + spike) | Alto (sempre ligado) | Médio |
| Falsos positivos | Vegetação, veículos, vento | Iluminação variável, sombras, chuva | Praticamente todos negativos |
| Volume de imagens | **Baixo** | Médio | **Alto** |
| Adequado a OFF-SD (sem AC, sem Wi-Fi, captura local em SD) | **Sim** (trail camera dedicada com bateria + PIR) ou **Sim** (IPCAM com PIR interno + bateria) | Possível em IPCAM AC com VMD no firmware, mas inadequado em OFF-SD por consumo | Possível mas inflaciona volume e encurta autonomia |
| Adequado a NET (Wi-Fi, sem AC) | Sim | Sim (CPU local da câmera) | Sim |
| Adequado a AC / AC+NET | Sim | **Sim — VMD pode rodar em servidor sobre RTSP** | Sim |
| Compatível com gatos | Sim (homeotermos) | Sim | Sim |
| Recomendado quando: | autonomia crítica e qualidade de trigger é prioridade | hardware é IPCAM barata sem PIR ou se há servidor recebendo stream | calibração, cenário estático ou animais ectotérmicos |

### B2.2.6 Decisão conceitual por perfil de ponto

A decisão é **híbrida e dependente do perfil** (B1 v2), não única. O sistema **não força um único trigger**; aceita os disponíveis em cada hardware e padroniza o que vem depois:

| Perfil de ponto (B1) | Trigger primário recomendado | Trigger de confirmação | Mecanismo de coleta dos dados |
|---|---|---|---|
| **OFF-SD** ⭐ caso primário | **PIR interno da IPCAM** (se disponível) — fallback: **VMD do firmware** | Nenhum (energia limitada por bateria) | **Voluntário troca cartão SD periodicamente** — workflow detalhado em B2.2.10 |
| **NET** | PIR ou VMD da câmera | Opcional: VMD em servidor sobre RTSP | Push do firmware ou pull RTSP via Wi-Fi |
| **AC** | PIR ou VMD do firmware | VMD em servidor (já que há energia para rodar a câmera 24/7) | Pull periódico do SD via técnico, ou export via Wi-Fi local |
| **AC+NET** | PIR + **VMD em servidor como confirmador** (estilo WiseEye) | A própria detecção de E1 funciona como segundo filtro | Stream contínuo (RTSP) ou push de eventos |

**Princípio**: aceitar o gatilho que o hardware do ponto oferece e **descarregar a inteligência de filtragem para o servidor/PC** via E1 (MegaDetector). O resultado é que **mesmo uma IPCAM barata com VMD ruidoso** entrega dados utilizáveis após E1 descartar os vazios. A arquitetura de **confirmatory sensing** de [WiseEye (Klemens et al. 2021)](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.13607) inspira a estratégia, mas adaptada: o "confirmador" não precisa ser hardware — pode ser o próprio E1 rodando em batch.

> **Nota — pareto de hardware**. O espaço de hardware do projeto (formalizado em B3) inclui trail cameras dedicadas com PIR (qualidade máxima de trigger), IPCAMs consumer com PIR e bateria (Tapo C400 / Reolink Argus), IPCAMs baratas OEM com VMD do firmware (Anyka, V380, ICSEE — faixa R$ 50–150), e Raspberry Pi + câmera USB com VMD/detector leve embarcado. **Todos compartilham o mesmo pipeline E1–E4** (princípio pipeline-agnóstico, RF-13); o mapeamento ponto-a-ponto será finalizado em B3 após o Pesquisador confirmar os `[~10 pontos]` em campo.

```
                FRONTEND DE AQUISIÇÃO POR PERFIL (E0)
                — varia por hardware, mas converge na mesma saída —

   OFF-SD  ──►  IPCAM bateria + SD    ┐
                (PIR interno ou VMD)  │
                                       │
   NET     ──►  IPCAM Wi-Fi           │
                (push / RTSP)         │      ┌───────────────────┐
                                       ├─────►│  SAÍDA NORMALIZADA │
   AC      ──►  IPCAM AC + SD/Wi-Fi   │      │  JPEG / MP4 +     │──► E1
                                       │      │  metadados        │
   AC+NET  ──►  RTSP contínuo + VMD   │      │  (ponto, ts,       │
                no servidor (WiseEye) │      │   modalidade,      │
                                       ┘      │   fonte de trigger)│
                                              └───────────────────┘

              ─────────────────────────────────────────────
              A partir daqui, E1–E4 não sabem qual perfil
              de hardware originou o quadro.
```

### B2.2.7 Parâmetros de aquisição — recomendações

| Parâmetro | Recomendação | Justificativa |
|---|---|---|
| Modo padrão | Vídeo curto 5–10 s + foto a cada disparo | Vídeo dá contexto temporal para re-ID; foto serve à classificação. |
| Frame-rate de captura | **15 FPS** vídeo; 1 foto/0,5 s | Suficiente para gatos (velocidade até ~5 m/s); economiza armazenamento. 15 FPS é o padrão wildlife (Bushnell, Reconyx, WiseEye). |
| Resolução | **1080p** mínimo (1920×1080); 4K se possível em perfis com AC | Re-ID precisa de detalhes de pelagem; 720p é insuficiente. |
| Modo noturno | IR ativo (LED IR) com filtro IR-cut comutável | Atividade dos gatos é majoritariamente noturna (B1 §2.1); imagem monocromática IR limita re-ID baseada em cor mas mantém padrões de listras/pontas. |
| Janela de captura | 24h com motion-trigger | Não restringir a janela porque pico é crepuscular e noturno. |
| Buffer pré-trigger | 1–2 s (quando suportado) | Captura o animal entrando no quadro, não só depois. |
| Cooldown entre eventos | 5–10 s | Evita centenas de imagens redundantes do mesmo evento. |
| Timestamp embarcado | NTP-sincronizado | Necessário para sincronizar eventos entre câmeras (cross-camera re-ID). |
| Metadados por captura | ID do ponto, timestamp, trigger source, temperatura, lux estimado | Insumo para B6. |

### B2.2.8 Particularidades do IR para re-ID de gatos

Atividade noturna implica imagem **monocromática** com iluminação IR. Isso tem três consequências importantes para os estágios subsequentes:

1. **Cor da pelagem perdida.** Re-ID baseado em cor (preto vs. tigrado vs. siamês) deixa de funcionar à noite. Modelos de re-ID precisam treinar com IR para aprender padrões estruturais (listras, manchas, formato).
2. **Olhos brilhantes (eye-shine).** Reflexão do tapetum lucidum sobre o LED IR pode saturar a região dos olhos — afeta detecção facial. Atenuação via expor mais para o corpo ou IR de baixa intensidade.
3. **Falsa cor (security cam).** Algumas câmeras comerciais (modelos Tapo) tentam reconstruir cor à noite via algoritmo de "color night vision" — frequentemente produzem cor errada (preto vira branco, marrom vira cinza), como reportado por usuários em [r/Feral_Cats (2025)](https://www.reddit.com/r/Feral_Cats/comments/1o191pt/can_a_security_camera_make_a_black_cat_look_white/). **Desligar** essa função e usar **IR mono nativo**.

Em B2.5 (re-ID) discutiremos como o uso de [Akbar, Rees & Fleming (2025) — MiewID body parts](https://doi.org/10.3390/jimaging11080274) é especialmente adequado porque foca em **partes do corpo** (que sobrevivem ao IR) em vez de cor global.

### B2.2.9 Critérios mínimos para o estágio E0 (resumo)

- Trigger aceitável: **PIR físico, VMD do firmware ou VMD em servidor** — o que o hardware do ponto oferecer.
- Vídeo curto + foto, 15 FPS, 1080p, IR noturno mono.
- Buffer pré-trigger e cooldown configuráveis quando o firmware permitir.
- Metadados ricos (ID do ponto, NTP timestamp ou timestamp da câmera, trigger source).
- Saída padronizada (JPEG/PNG + H.264 / MP4) com **nomenclatura estruturada** (§B2.2.10).
- **Ingestão tolerante a falhas**: arquivos corrompidos, EXIF ausente ou clock fora de sincronismo não quebram o pipeline; geram log e seguem.

### B2.2.10 Workflow do voluntário com cartão SD (caso primário OFF-SD)

No perfil OFF-SD — o caso operacional dominante no Campus 2 (ver B1) — a "sincronização" do sistema **é o voluntário**. Não há Wi-Fi, não há servidor remoto consumindo stream: o **fluxo físico de cartões SD entre o ponto de campo e o PC do pesquisador** é o que torna o sistema possível. Este sub-bloco padroniza o procedimento para que o pipeline subsequente (E1–E4) receba dados íntegros e identificáveis.

#### B2.2.10.1 Atores envolvidos

- **Voluntário-AEX** — pessoa autorizada pela AEX Gatosdoc2 que executa a coleta no campo. Pode ser o mesmo que reabastece os comedouros ou um voluntário específico do projeto.
- **Pesquisador** — responsável por receber os cartões e executar a ingestão no notebook (`[PLACEHOLDER-HARDWARE-NOTEBOOK]`). Papel funcional; pessoa específica fica registrada no front-matter da monografia.
- **Mantenedor-TI** (opcional) — backup do pesquisador; pode receber e processar quando o pesquisador está indisponível.

#### B2.2.10.2 Kit de campo do voluntário

Cada voluntário deve receber, antes da primeira coleta, um kit padronizado:

| Item | Quantidade | Finalidade |
|---|---|---|
| Cartões SD reserva | **2 por câmera** (rodízio) | Trocar o cartão cheio sem deixar o ponto offline |
| Saquinhos antiestáticos / case rígido | 1 por cartão em trânsito | Proteger contra umidade e ESD |
| Etiquetas adesivas pré-impressas | 20–30 | Identificar cartões no momento da retirada |
| Caderneta de campo simples (papel) | 1 | Registro manual paralelo (número do ponto, data/hora, observações) |
| Pano seco / lápis | 1 | Limpar contatos e marcar etiquetas |
| Smartphone com app de notas + câmera | (pessoal do voluntário) | Foto do ponto, hora automática, GPS opcional |

> **[PLACEHOLDER-FOTOS-KIT]** — quando o kit físico estiver montado, fotografar e incluir no anexo.

#### B2.2.10.3 Procedimento de troca de cartão (passo a passo)

```
  Antes de sair de casa
  ────────────────────────────────────────
  [1] Confira: 2 cartões SD vazios formatados (FAT32/exFAT) e etiquetados
      como "RESERVA Pn" para cada ponto previsto naquele dia.
  [2] Pegue caderneta + etiquetas adicionais.
  [3] Confira hora do celular (vai servir como referência de timestamp).

  No ponto Pn
  ────────────────────────────────────────
  [4] Antes de mexer na câmera: anote na caderneta
        ponto: Pn
        data/hora (do celular): YYYY-MM-DD HH:MM
        condições: chuva? sol? sombra? câmera tombada?
  [5] Tire 1 foto do ponto com o celular (geolocalizada de preferência).
  [6] Desligue a câmera ou aguarde ela entrar em sleep.
  [7] Abra o compartimento; retire o cartão cheio.
  [8] **Etiquete imediatamente** o cartão que saiu:
        Pn_YYYY-MM-DD_v01   (v01 = voluntário 01; ou as iniciais do voluntário)
  [9] Coloque o cartão etiquetado no saquinho/case e guarde em local seguro.
 [10] Insira o cartão RESERVA correspondente.
 [11] Ligue a câmera; aguarde 1 ciclo de boot e teste o trigger (passe a mão
      em frente — confirme que a luz/LED responde, se a câmera tiver indicador).
 [12] Verifique nível de bateria se visível no LED ou display.
 [13] Repita para os próximos pontos.

  Ao final do dia
  ────────────────────────────────────────
 [14] Entregue os cartões etiquetados ao Pesquisador ou ao
      Mantenedor-TI. Se a entrega for em outro dia, mantenha em
      ambiente seco, longe de magnetos e altas temperaturas.
 [15] Compartilhe foto da caderneta (ou as fotos do celular) por
      mensagem para registro paralelo.
```

#### B2.2.10.4 Nomenclatura de cartões e arquivos

A nomenclatura segue **trail-camera best practice** (GBIF Camera Trap Guide; Camtrap-DP) e cobre os dois níveis:

- **Etiqueta do cartão** (escrita à mão ou impressa):
  `Pn_YYYY-MM-DD_vNN`
  - `Pn` = ponto (P1…P10 [estimativa])
  - `YYYY-MM-DD` = data da **retirada** do cartão (não da instalação)
  - `vNN` = código do voluntário

- **Pasta criada no PC após ingestão**:
  `raw/<Pn>/<YYYY-MM>/<Pn_YYYY-MM-DD_vNN>/`
  Dentro dela, os arquivos originais são preservados tal como vieram do firmware da câmera (nomes do tipo `IMG_0001.JPG`, `MOV_0017.MP4`).

- **`media_id` interno** atribuído pelo pipeline na ingestão (E0 → E1):
  UUID v4, registrado no banco com referência ao caminho relativo. O nome original do firmware **não** é chave estável — câmeras reciclam nomes ao formatar.

#### B2.2.10.5 Checklist de integridade na ingestão (no PC do pesquisador)

Quando o pesquisador insere o cartão no PC, um script de ingestão (a ser implementado em B5) executa:

1. **Listar arquivos** do cartão (JPG, MP4, AVI dependendo do firmware).
2. **Copiar** para `raw/<Pn>/<YYYY-MM>/<Pn_YYYY-MM-DD_vNN>/` — nunca mover, sempre copiar.
3. **Verificar checksum SHA-256** de cada arquivo no destino contra o original (detecta corrupção de cartão).
4. **Ler EXIF / metadados**: timestamp, modelo da câmera, dimensões. Logar arquivos com EXIF ausente.
5. **Detectar clock-drift** comparando o `DateTimeOriginal` do EXIF com a data anotada pelo voluntário (caderneta) e o `mtime` do filesystem. Se houver desvio > 24h, marcar todos os arquivos do batch com `clock_status = 'drift_detected'` para correção manual posterior.
6. **Inserir registros em `media`** (tabela Camtrap-DP — ver B2.7) com `deployment_id` derivado do nome da pasta e `media_id` UUID novo.
7. **Mover o cartão original para "prontos para formatar"** somente após conferência bem-sucedida.

> **[PLACEHOLDER-SCRIPT-INGESTAO]** — o script Python que automatiza B2.2.10.5 será implementado em B5. Por enquanto, fica a especificação.

#### B2.2.10.6 Política de rodízio de cartões

- Mínimo: **2 cartões por ponto** (um em campo, um reserva).
- Reformatar o cartão **somente depois** de a ingestão no PC ter sido concluída **e** backup feito (ver B2.7.7).
- Vida útil esperada de SD industrial: 3–5 anos; SD consumer: 1–2 anos sob ciclo intenso. **Numerar os cartões** (`SD-01`, `SD-02`…) e registrar em planilha quando entram e quando são aposentados.
- **Velocidade mínima** recomendada: classe U3 / V30 para gravação de vídeo 1080p sem perda de quadros.

### B2.2.11 Frequência de coleta — função empírica

A frequência ideal de coleta dos cartões **não pode ser ditada por referência bibliográfica isolada**. Ela emerge da interseção de três variáveis que só serão conhecidas após testes em campo:

1. **Autonomia da bateria do ponto** — quantos dias a câmera roda em modo PIR/VMD com a bateria escolhida (LiFePO4 12 V, ou bateria interna da IPCAM, ou banco USB). Depende de:
   - Capacidade da bateria.
   - Temperatura ambiente (Campus 2: 10–38°C ao longo do ano).
   - Frequência real de disparos (ponto com muito movimento drena mais).
2. **Capacidade do cartão SD vs. taxa de gravação** — quantos dias o cartão aguenta antes de encher. Depende de:
   - Tamanho do cartão (32 GB, 64 GB, 128 GB …).
   - Resolução e taxa de quadros configuradas no firmware.
   - Volume de eventos efetivos no ponto.
3. **Experiência operacional dos voluntários** — logo nas primeiras semanas não se sabe ainda qual desses dois é o gargalo. A janela inicial precisa ser **conservadora** (visita mais frequente) até medir os dois acima nos pontos reais.

**Estratégia adotada — frequência adaptativa em três fases**:

| Fase | Janela | Frequência inicial recomendada | Ajuste |
|---|---|---|---|
| **Calibração** | Primeiras 2–4 semanas | **Visita semanal** a todos os pontos | Medir autonomia real da bateria e % de preenchimento do SD ao chegar |
| **Operação regular** | Da semana 5 em diante | **Ajustada por ponto** conforme o limitante (bateria ou SD) observado, sempre com **margem de 30%** | Pontos com alta atividade podem voltar a semanal; pontos calmos podem ir para quinzenal |
| **Manutenção reforce-as-needed** | Em paralelo | Visita extraordinária sempre que algum sinal externo indicar problema (câmera caída, ataque, fauna anormal) | Sob demanda |

**Referências bibliográficas como ponto de partida**, não como prescrição:

- [Lifeplan Camera Trapping Protocol (2023)](https://www.protocols.io/view/lifeplan-camera-trapping-protocol-c5uky6uw.pdf) — propõe **visita semanal** padrão.
- [Saving Nature — Camera Trapping Protocol](https://savingnature.com/camera-trapping-protocol/) — sugere **mensal para pontos acessíveis, trimestral para remotos**.
- [NTCA Tiger Phase III](https://ntca.gov.in/assets/uploads/Reports/AITM/Phase_III_CT%20Manual.pdf) — protocolo de tigres usa janelas mais longas (limitação de logística), validável quando SD e bateria são dimensionados para isso.

Para o Campus 2, a literatura serve apenas para fundamentar **"semanal como ponto de partida"**. O regime definitivo será fixado pela experiência do **Voluntário-AEX** e do **Pesquisador** após as primeiras semanas de calibração, com os dois limitantes (bateria, SD) medidos no campo.

> **[PLACEHOLDER-CALIBRACAO]** — após a fase de calibração, registrar nesta seção a frequência operacional final por ponto, junto com a métrica que a justifica ("P3: bateria seca em 9 dias, SD enche em 12 dias → visita a cada 6 dias").

---

## B2.3 Estágio E1 — Detecção genérica de animal

### B2.3.1 Por que detecção antes de classificação

Detector genérico (animal/humano/veículo) **filtra** os ~80% de quadros vazios e **localiza** o animal no quadro — duas funções que evitam que o classificador de espécie e o re-ID precisem processar o quadro inteiro. Este padrão é consagrado por [Beery et al. (2019)](https://beerys.github.io/assets/papers/EfficientPipeline.pdf) e replicado por todos os pipelines modernos (DeepFaune, AddaxAI, Pytorch-Wildlife, Wildlife Insights).

### B2.3.2 Modelos candidatos

Três famílias de detectores são candidatas para o E1:

1. **MegaDetector v6** (Microsoft / Pytorch-Wildlife, 2024) — detector dedicado wildlife.
2. **DeepFaune detector** (Rigoudy et al. 2023) — detector dedicado wildlife (europeu).
3. **YOLO v8 / v11 / v12** (Ultralytics) — detector genérico, customizado para wildlife em vários estudos.

Há outros (Faster R-CNN, EfficientDet, RT-DETR), mas a comunidade de camera-trapping consolidou-se em torno desses três. Os demais entram apenas em estudos comparativos pontuais.

### B2.3.3 MegaDetector v6 — visão geral

MegaDetector é um **modelo open-source mantido pela Microsoft AI for Good Lab** treinado em **milhões de imagens** de camera-traps de "ecossistemas diversos no mundo todo" ([GitHub Microsoft/CameraTraps](https://github.com/microsoft/CameraTraps/releases)). Classes: **animal, person, vehicle**. Não identifica espécie.

A versão **v6**, lançada em abril 2024 e refinada ao longo de 2024–2025, traz mudanças críticas em relação à v5:

| Característica | MegaDetector v5 | MegaDetector v6-compact |
|---|---|---|
| Backbone | YOLOv5 | **YOLOv9-compact** |
| Tamanho (parâmetros) | ~7M | **~1,2M (1/6 do v5)** |
| Recall em animais (validação Microsoft) | baseline | **+12% sobre v5** |
| Velocidade (relato Microsoft) | baseline | **~5× mais rápido que v5** |
| Devices alvo | GPU / CPU | **CPU, dispositivos baixo orçamento** |
| Licença | MIT | MIT |
| Distribuição | via Pytorch-Wildlife | via Pytorch-Wildlife |

Fonte: [Releases · microsoft/Biodiversity (2025)](https://github.com/microsoft/CameraTraps/releases).

Variantes da v6 (rolling release): MDv6-c (compact, prioriza velocidade), MDv6-x (extra, prioriza acurácia). Para o nosso caso, MDv6-c é o candidato natural para borda; MDv6-x para servidor de revisão.

**Acurácia em terreno:** [Brookhaven National Laboratory (Mansfield 2025)](https://www.bnl.gov/esd/wildlife/files/research/pdf/2025-mansfield-paper.pdf) reporta 93,7% de imagens corretamente rotuladas (TP + TN) numa base de 11.862 imagens reais de camera-trap, consistente com a literatura existente para MegaDetector ([animaldetect.com (2024)](https://www.animaldetect.com/blog/megadetector-review-pros-cons-use-cases)) registra precisão 0,96 e recall 0,73 para MD v5).

### B2.3.4 DeepFaune detector — visão geral

DeepFaune é uma **iniciativa franco-europeia colaborativa** ([Rigoudy et al. 2023, bioRxiv](https://www.biorxiv.org/content/10.1101/2022.03.15.484324v3.full-text)) que entrega um pipeline completo de detecção + classificação treinado em fauna europeia. O detector dedicado:

- **Velocidade**: ~0,3 s por imagem (mencionada pelos autores).
- **Desempenho próximo ao MegaDetector v5** em detecção, mas muito mais rápido (segundo os próprios autores).
- **Pacote desktop**: roda offline em notebook sem GPU dedicada, com interface gráfica simples — vantagem para ecólogos sem time de ML.
- Existe uma versão **DeepFaune New England (DFNE, 2025)** com classificador de 24 táxons norte-americanos, 97% accuracy ([PMC (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12617260/)) — irrelevante para nossas espécies mas útil como referência metodológica.

### B2.3.5 YOLO v8 / v11 / v12 — visão geral

YOLO (You Only Look Once) é a **família de detectores de propósito geral** mais usada em produção. Não é específica para wildlife, mas tem dois pontos a favor:

1. Pode ser **fine-tuned** com pouco dado em qualquer dataset.
2. Tem **versões nano/small** otimizadas para borda (Raspberry Pi, Jetson Nano).

Estudo recente [Wang et al. (2025) — *YOLO11-APS: Lightweight Model for Protected Wildlife Detection*](https://pmc.ncbi.nlm.nih.gov/articles/PMC12694077/) reporta para YOLO11-base em wildlife:

| Métrica | YOLO11-base | YOLO11-APS (fine-tuned wildlife) |
|---|---|---|
| Precisão | 88,9% | **92,7%** |
| Recall | 80,7% | **87,0%** |
| mAP@0,5 | 88,1% | **92,6%** |
| mAP@0,5:0,95 | 58,5% | **62,2%** |

A baseline (YOLO11 sem customização) já entrega mAP@0,5 de 88,1% em wildlife — abaixo da meta de 0,90 do A2.0 (RF-03), mas próxima.

### B2.3.6 Comparativo dos detectores — tabela aplicada

| Critério | **MegaDetector v6-c** | **DeepFaune detector** | **YOLOv11-base** |
|---|---|---|---|
| Família | YOLOv9 customizado | YOLO customizado | YOLOv11 |
| Classes nativas | animal / humano / veículo | animal / humano | configurável (genérico) |
| Treinado em | milhões de imagens camera-trap mundial | dataset europeu | COCO + transfer |
| mAP em wildlife (referência) | recall +12% sobre MDv5; precisão >0,90 em literatura | "near MDv5" | 88,1% baseline; 92,6% fine-tuned |
| Velocidade em CPU | **~5× mais rápido que MDv5** | ~0,3 s/img | depende da versão; nano < 100 ms |
| Tamanho | ~1,2M parâmetros | médio | nano: ~2,6M; small: ~9M; medium: ~25M |
| Licença | MIT | open-source (não-comercial detalhes em GitHub) | AGPL-3.0 (Ultralytics) ou Enterprise |
| Maturidade na comunidade wildlife | **alta** (referência) | **alta** (Europa) | crescente |
| Fácil de fine-tunar | sim (Pytorch-Wildlife) | parcial | **sim** (muito documentado) |
| Roda em Raspberry Pi 5 | sim (compact) | sim (Python desktop) | sim (nano/small) |
| Suporte oficial brasileiro / lusófono | não específico | não | não |
| Aplicabilidade a *Felis catus* | **boa** (treinado com gatos entre outras) | parcial (fauna europeia tem gato) | **boa** se fine-tune |

> **Observação sobre licença.** A licença AGPL do YOLOv11 (Ultralytics) implica que **qualquer uso em produto distribuído** requer abertura do código. Para um TCC acadêmico, sem distribuição comercial, isso é compatível. Vale registrar para que o sistema, se evoluir para spin-off, considere a licença Enterprise.

### B2.3.7 Decisão conceitual para o E1

A escolha conceitual para o estágio E1 segue três critérios:

1. **Robustez out-of-the-box**: o sistema precisa funcionar imediatamente nos pontos do Campus 2, sem dataset rotulado nosso.
2. **Custo computacional**: o modelo precisa rodar em borda viável (~Raspberry Pi 5) e em laptop comum.
3. **Compatibilidade com Pytorch-Wildlife**: porque os estágios E2 e E3 também tendem a usar esse pipeline (cf. SpeciesNet integration).

**Recomendação conceitual**: **MegaDetector v6-compact** como detector primário em todos os perfis de nó (princípio pipeline-agnóstico), com **YOLOv11-small fine-tuned** como contraprova durante a Etapa 3 (avaliação no notebook do Pesquisador — `[PLACEHOLDER-HARDWARE-NOTEBOOK]`).

```
                  Estratégia adotada para E1
                  ─────────────────────────────

   Padrão de produção  ──► MegaDetector v6-compact
                            • out-of-the-box
                            • leve, rápido
                            • mantém ecossistema Pytorch-Wildlife

   Contraprova         ──► YOLOv11-small fine-tuned
                            • benchmark em dataset gato-específico
                            • avalia se vale o custo de treino próprio

   Backup leve         ──► DeepFaune detector standalone
                            • offline, desktop simples
                            • cenário em que o usuário só tem PC e quer GUI
```

### B2.3.8 Threshold de confiança e estratégia de erros

Detector retorna **score [0,1]**. A escolha do threshold é trade-off entre falsos positivos e falsos negativos:

| Threshold | Comportamento | Quando usar |
|---|---|---|
| **Baixo** (0,1–0,2) | Mais detecções, mais falsos positivos | Coleta exploratória, revisão humana |
| **Médio** (0,3–0,5) | Equilibrado | Pipeline de produção típico |
| **Alto** (0,6–0,8) | Conservador, perde animais | Quando o pipeline a jusante é caro |

Recomendação padrão MegaDetector (Microsoft): **threshold 0,2** para detectar com confiança baixa e deixar a triagem para os estágios seguintes. Esta é a convenção que adotamos como ponto de partida. Será calibrado em B5 (validação).

### B2.3.9 Falhas conhecidas do detector e mitigações

Conforme [Mansfield (BNL 2025)](https://www.bnl.gov/esd/wildlife/files/research/pdf/2025-mansfield-paper.pdf), MegaDetector é afetado por:

| Falha | Tipo | Mitigação no projeto |
|---|---|---|
| Vegetação densa estruturada | falso negativo | Posicionar câmera com fundo neutro (cf. B1 §4.5) |
| Objetos inanimados móveis (folhas, embalagens ao vento) | falso positivo | Confirmação multi-modal (PIR + frame-diff) |
| Animais parcialmente ocluídos | falso negativo | Múltiplos quadros do mesmo evento (vídeo curto) |
| Animais pequenos a distância | falso negativo | Posicionamento próximo à estação de alimentação (B1 §4.5 — câmera elevada e centrada) |
| Aves / roedores pequenos | falso negativo | Reduzir threshold em pontos com fauna pequena (registro em fonte_e_lacunas) |

---

## B2.4–B2.9 — O que vem nas próximas iterações

| Sub-bloco | Entrega | Status |
|---|---|---|
| **B2.4** | Classificação de espécie (E2): SpeciesNet, DeepFaune classifier, modelos custom para *Felis catus*; estratégia de transfer learning. | Parte 2 |
| **B2.5** | **Re-identificação (E3) — núcleo do TCC**: MegaDescriptor, MiewID body parts (Akbar 2025), PetFace, WildlifeReID-10k, ArcFace loss, open-set thresholding, capture–recapture. | Parte 2 |
| **B2.6** | Pré-processamento, augmentation e filtros temporais (cross-cutting). | Parte 2 |
| **B2.7** | Persistência (E4): base de eventos, galeria de embeddings, schema, sincronização. | Parte 3 |
| **B2.8** | Protocolo de métricas amarrado a A2.0 (datasets, métricas por estágio, threshold, baselines). | Parte 3 |
| **B2.9** | Plano de testes no notebook do Pesquisador (`[PLACEHOLDER-HARDWARE-NOTEBOOK]`): quais modelos, quais datasets, quais experimentos, timeline. | Parte 3 |

---

## Síntese de B2 — Parte 1

Esta parte fechou:

1. **Pipeline conceitual de 5 estágios** (E0–E4) com interfaces explícitas e princípios de projeto. **Core E1–E4 é pipeline-agnóstico** ao hardware de captura; a diferença entre perfis (OFF-SD, NET, AC, AC+NET) fica encapsulada em E0.
2. **Estágio E0 (Aquisição)** com decisão híbrida por perfil (PIR físico, VMD do firmware ou VMD em servidor, conforme o hardware do ponto oferecer), parâmetros (15 FPS, 1080p, IR mono), workflow detalhado do **voluntário com cartão SD** (caso primário OFF-SD), e estratégia de **frequência de coleta adaptativa** — calibração empírica baseada em autonomia de bateria + capacidade de SD + experiência operacional dos voluntários.
3. **Estágio E1 (Detecção)** com comparativo **MegaDetector v6 × DeepFaune × YOLOv11** e recomendação de **MegaDetector v6-compact** como padrão, **YOLOv11-small** como contraprova, **DeepFaune** como backup desktop.

**Próximo entregável (B2 Parte 2)**: classificação de espécie + re-identificação + pré-processamento. A re-identificação é o **coração técnico do TCC** e receberá tratamento muito mais detalhado (open-set, ArcFace, MiewID body parts, datasets, estratégia de avaliação no PC do pesquisador).

---

## Fontes citadas nesta parte

### Pipeline geral e ferramentas
- **Beery S., Morris D., Yang S. (2019)**. *Efficient Pipeline for Camera Trap Image Review*. [arXiv:1907.06772](https://arxiv.org/abs/1907.06772); [PDF Beery](https://beerys.github.io/assets/papers/EfficientPipeline.pdf).
- **Microsoft AI for Good Lab — Pytorch-Wildlife / MegaDetector v6** (2024–2025). [microsoft.github.io/CameraTraps](https://microsoft.github.io/CameraTraps/); [Releases · microsoft/Biodiversity](https://github.com/microsoft/CameraTraps/releases); [agentmorris/MegaDetector](https://github.com/agentmorris/MegaDetector).
- **AddaxAI / Addax Data Science (2024)** — [addaxdatascience.com](https://addaxdatascience.com/addaxai/); **AI4G survey**: [agentmorris.github.io/camera-trap-ml-survey](https://agentmorris.github.io/camera-trap-ml-survey/).
- **Wildlife Insights / SpeciesNet (Google)** — descrito em AddaxAI; classificador EfficientNetV2-M com >2000 rótulos.

### Detectores
- **Rigoudy N. et al. (2023)** — *The DeepFaune initiative: a collaborative effort towards camera-trap image classification*. [bioRxiv](https://www.biorxiv.org/content/10.1101/2022.03.15.484324v3.full-text).
- **Brouillette M. et al. (2025)** — *DeepFaune New England: A Species Classification Model*. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12617260/).
- **Wang Y. et al. (2025)** — *YOLO11-APS: An Improved Lightweight Model for Protected Wildlife Detection*. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12694077/).
- **Mansfield T. (2025)** — *AddaxAI evaluation at Brookhaven National Laboratory*. [BNL ESD](https://www.bnl.gov/esd/wildlife/files/research/pdf/2025-mansfield-paper.pdf).
- **AnimalDetect (2024)** — *MegaDetector Review 2025: Real-World Use Cases*. [animaldetect.com](https://www.animaldetect.com/blog/megadetector-review-pros-cons-use-cases).
- **Ultralytics (2025)** — *How to train Ultralytics YOLO models to detect animals*. [ultralytics.com](https://www.ultralytics.com/blog/how-to-train-ultralytics-yolo-models-to-detect-animals-in-the-wild).

### Aquisição e triggers
- **Klemens J. A. et al. (2021)** — *A motion-detection based camera trap for small nocturnal mammals (WiseEye)*. [Methods in Ecology and Evolution](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.13607); [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5226779/).
- **WildCare UK** — *Guide to Common Trail Camera Features*. [wildcare.co.uk](https://www.wildcare.co.uk/blog/a-guide-to-common-trail-camera-features/).
- **TrailCamPro (2022)** — *Trail Camera Tests: Detection Range, Field of View*. [trailcampro.com](https://www.trailcampro.com/pages/trail-camera-tests).
- **Bø et al. (2024)** — *Motion detection or time lapse? Camera trap triggers for elusive ground-dwelling birds*. [Authorea](https://www.authorea.com/users/624924/articles/647057-motion-detection-or-time-lapse-a-comparison-of-camera-trap-triggers-in-the-monitoring-of-elusive-ground-dwelling-birds).
- **Lanfear R. (2017)** — *Raspberry Pi motion-capture camera trap*. [github.com/roblanf/raspberrytrap](https://github.com/roblanf/raspberrytrap).
- **Reddit r/Feral_Cats (2025)** — discussão sobre security camera distorcendo cor de gatos pretos: [reddit.com/r/Feral_Cats](https://www.reddit.com/r/Feral_Cats/comments/1o191pt/can_a_security_camera_make_a_black_cat_look_white/).

### Protocolos de campo e frequência de coleta
- **Lifeplan Camera Trapping Protocol (2023)** — [protocols.io](https://www.protocols.io/view/lifeplan-camera-trapping-protocol-c5uky6uw.pdf). Recomenda visita semanal.
- **Saving Nature — Camera Trapping Protocol** — [savingnature.com](https://savingnature.com/camera-trapping-protocol/). Recomenda visita mensal a trimestral conforme acessibilidade.
- **NTCA (National Tiger Conservation Authority, Índia) — Tiger Phase III Camera Trap Manual** — [ntca.gov.in](https://ntca.gov.in/assets/uploads/Reports/AITM/Phase_III_CT%20Manual.pdf).
- **GBIF — Camera Trap Guide** — [docs.gbif.org/camera-trap-guide](https://docs.gbif.org/camera-trap-guide/). Padrões de nomenclatura e organização de arquivos.

### Re-identificação (já citadas, retomadas em B2.5)
- **Čermák V., Picek L., Adam L., Papafitsoros K. (2023)** — *WildlifeDatasets: An open-source toolkit for animal re-identification* (introduz **MegaDescriptor**). [IEEE WACV 2024](https://ieeexplore.ieee.org/document/10483925/).
- **AnimalCLEF 2025** — [imageclef.org/AnimalCLEF2025](https://www.imageclef.org/AnimalCLEF2025); paper de baseline em [CEUR-WS](https://ceur-ws.org/Vol-4038/paper_245.pdf).
- **Akbar S., Rees Fleming H. (2025)** — *MiewID body parts approach for feral cat re-identification*. [J. Imaging 11(8):274](https://doi.org/10.3390/jimaging11080274). (Citado em A1.6 e retomada em B2.5.)
- **Sani D., Khurana M., Anand S. (2025)** — *Active Learning for Animal Re-Identification with Ambiguity-Aware Sampling*. [arXiv:2511.06658](https://arxiv.org/abs/2511.06658).
