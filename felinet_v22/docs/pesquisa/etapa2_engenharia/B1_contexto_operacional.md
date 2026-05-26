# Etapa 2 — B1: Contexto operacional e modelo de ambiente

> **Versão 2 — 13/maio/2026.** Revisão completa do B1 incorporando as observações do Felipi (Fase 1.2):
> - Perfil **OFF-SD** (câmera + cartão SD, sem energia AC nem Wi-Fi) reposicionado como **caso primário** do TCC;
> - Fauna silvestre do Campus 2 caracterizada com referência à proximidade ao Cerrado UFSCar;
> - Nomenclatura de perfis substituída por **códigos funcionais** (não-gregos);
> - Subseção sobre **comedouros anti-pragas** com referências internacionais e nacionais;
> - Instruções operacionais para criação do mapa de pontos (placeholder);
> - Substituição de nomes próprios por **papéis genéricos** em atores;
> - Especificações de hardware do notebook substituídas por **placeholder** `[ESPEC_HARDWARE_NOTEBOOK]`;
> - Estimativas de **10 pontos** e **50 gatos** explicitamente marcadas como pendentes de confirmação de campo.

> **Função argumentativa.** B1 fecha o **espaço de problema** antes de qualquer decisão técnica. Aqui modelamos o ambiente do Campus 2 da USP São Carlos, os pontos de alimentação mantidos pela AEX Gatosdoc2 e o comportamento esperado dos gatos comunitários — convertendo tudo em **dimensões de decisão** que serão usadas por B2 (pipeline), B3 (trade-offs) e B4 (arquitetura física).

> **Princípio orientador.** *"Máximo com mínimo de recursos."* Aqui ele se materializa em uma escolha estratégica: o sistema é projetado primeiro para o **pior caso de infraestrutura** (sem tomada, sem Wi-Fi, voluntário troca cartão SD periodicamente) — e os perfis com mais infraestrutura são tratados como **evoluções opcionais**, não como cenário-base.

> **Referência cruzada.** Requisitos de operação RP-01 a RP-14 e ambientais RNF-12 a RNF-16 de [A2.0](./A2.0_requisitos_sistema.md) ancoram este bloco.

---

## 1. O campus e a colônia

### 1.1 Localização e dimensão física

O TCC adota como sítio de estudo a **Área 2 do Campus USP São Carlos**, no bairro Santa Angelina, com endereço institucional Av. João Dagnone 1100 (Portaria Norte) ([Prefeitura do Campus USP São Carlos — Localização](https://prefeitura.sc.usp.br/localizacao/); [Guia de Calouros](https://saocarlos.usp.br/guia-calouros/)). A Área 2 é descrita pela própria USP como **"relativamente mais recente e, por isso, menos densa"** que a Área 1, com institutos, biblioteca central, restaurante universitário e moradia estudantil ([USP São Carlos — Guia de Calouros, 2025](https://saocarlos.usp.br/guia-calouros/)).

Esta característica é estruturante para o projeto: campus menos denso significa **mais áreas verdes, mata nativa preservada, bordas com terrenos baldios e maior heterogeneidade de coberturas** — exatamente o tipo de paisagem em que colônias de gatos comunitários se estabelecem e em que **fauna silvestre coexiste com fauna sinantrópica** ([Johansson & DeGregorio, 2023](https://academic.oup.com/jue/article/doi/10.1093/jue/juad003/7161106); [Gehrt et al., 2013](https://dx.plos.org/10.1371/journal.pone.0075718)).

> **Insumo de campo necessário.** A planta interna da Área 2 está disponível em [prefeitura.sc.usp.br/mapas-e-aplicativos](https://prefeitura.sc.usp.br/mapas-e-aplicativos/). A **localização geográfica dos pontos atuais** precisa ser levantada em campo pelo autor — instruções operacionais consolidadas em **§ 5 (Mapa dos pontos)**.

### 1.2 A colônia: estimativa inicial

Parâmetros operacionais iniciais, **a confirmar em campo**:

- **População-alvo:** **`[~50 gatos]`** — estimativa do AEX Gatosdoc2; **não é censo formal**. Será refinada via fichas de campo (§ 6) e via re-identificação automática quando o piloto entrar em operação.
- **Pontos de alimentação ativos:** **`[~10 pontos]`** — número operacional informado pelos voluntários; **a confirmar via levantamento em campo**.
- **Intenção declarada pela AEX:** reduzir o número de pontos ao longo do tempo (concentração da alimentação para facilitar manejo).

> **Placeholder.** Os valores entre `[colchetes]` permanecem até que o autor conclua o levantamento de campo. Toda referência a "50 gatos" e "10 pontos" neste e em outros documentos é **estimativa de trabalho**, não dado confirmado.

Esses valores têm implicação direta no dimensionamento de software (B2) e hardware (B4):

| Variável | Estimativa | Implicação |
|---|---|---|
| Indivíduos esperados | ~50 (a confirmar) | Re-ID **closed-set** é viável (galeria pequena); *open-set rejection* precisa lidar com chegada de novos. |
| Pontos ativos | ~10 (a confirmar) | Sistema multi-câmera com **rotação amostral** provável (menos câmeras que pontos). |
| Gatos por ponto (média) | ~5 | A literatura mostra **agregação forte** ([Horn et al., 2011](https://wildlife.onlinelibrary.wiley.com/doi/10.1002/jwmg.145); [Zhang et al., 2022](https://www.mdpi.com/2076-2615/12/9/1141)) — alguns pontos terão muito mais, outros quase nenhum. |

### 1.3 Acervo Gatosdoc2

O Gatosdoc2 possui um acervo de fotos, mas **inconsistente, sem padrão e de qualidade irregular**. Implicações:

- **Não é dataset de treino confiável** — não usaremos para *fine-tuning*.
- **Pode servir como dataset de validação qualitativa** — sanity-check de detecção e classificação de espécie.
- **É documentação histórica útil** — para identificar indivíduos já catalogados e cruzar com a base de identidades futura.

> **Lacuna metodológica.** Ver `fontes_e_lacunas.md` § B1 — protocolo de uso ético e técnico desse acervo precisa ser fechado com a AEX Gatosdoc2 antes da Etapa 3.

---

## 2. Comportamento dos gatos como restrição de projeto

O comportamento espaço-temporal de gatos de vida livre define quando e onde o sistema precisa capturar imagens — e, portanto, quanto de armazenamento, energia e processamento alocar.

### 2.1 Padrão temporal de atividade — bimodal crepuscular

A literatura é convergente: gatos de vida livre têm **atividade bimodal**, com dois picos crepusculares.

| Estudo | Sítio | Picos de atividade observados |
|---|---|---|
| [Zhang et al., 2022](https://www.mdpi.com/2076-2615/12/9/1141) | Campus universitário, China | **06:00–10:00** e **17:00–21:00** (média 19.864 passos/dia). |
| [Cove et al., 2022](https://doi.org/10.1002/ece3.8771) | Washington DC, EUA (camera-trap) | Maior detecção em crepúsculo e noite. |
| [Johansson & DeGregorio, 2023](https://academic.oup.com/jue/article/doi/10.1093/jue/juad003/7161106) | Áreas residenciais, Arkansas | Mais diurnos em áreas urbanas centrais; mais noturnos com predadores presentes. |
| [Zacharia et al., 2026](https://www.mdpi.com/2076-2615/16/7/1101) | Mediterrâneo (Chipre) | Pico no fim da tarde. |

**Consequências para o projeto:**

- **RNF-14 (visão noturna IR) é obrigatória** — boa parte das passagens ocorrerá entre 17h e madrugada.
- Aquisição não precisa ser 24/7 contínua: **gravação disparada por evento** (movimento ou PIR) capta a maior parte da informação útil com fração do volume de dados ([Klemens et al., 2021](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.13607)).
- Janelas de pico coincidem com **disponibilidade humana** dos voluntários (horários típicos de alimentação) — alinha a aquisição com a operação de campo, sinergia importante para B5.

### 2.2 Padrão espacial — uso concentrado perto da fonte de alimento

Gatos comunitários têm **home range pequeno quando há recurso alimentar estável**, gastando a maior parte do tempo a dezenas de metros do ponto de alimentação ([López-Jara et al., 2021](https://linkinghub.elsevier.com/retrieve/pii/S253006442100016X); [Zhang et al., 2022](https://www.mdpi.com/2076-2615/12/9/1141)).

| Estudo | Home range médio (95% KDE) |
|---|---|
| [Horn et al., 2011](https://wildlife.onlinelibrary.wiley.com/doi/10.1002/jwmg.145) | Variável; mais amplo em machos não-castrados |
| [Zhang et al., 2022](https://www.mdpi.com/2076-2615/12/9/1141) | Machos 6,68–12,60 ha; fêmeas 5,02–7,73 ha (campus) |
| [Zacharia et al., 2026](https://www.mdpi.com/2076-2615/16/7/1101) | 36.088 m² (~3,6 ha) — Chipre |
| [López-Jara et al., 2021](https://linkinghub.elsevier.com/retrieve/pii/S253006442100016X) | 1–47 ha; atividade em ~100 m da casa, max 2,5 km |

**Consequências para o projeto:**

- A maioria dos gatos provavelmente circula entre **2–4 pontos vizinhos**, com forte concentração em um ponto principal. Isto implica:
  - **Cross-camera re-ID** (o mesmo indivíduo aparece em múltiplos pontos);
  - **Modelagem de quem-é-onde** permite estimar contagens corrigidas (sem dupla contagem);
  - **Rotação amostral** (poucas câmeras cobrindo pontos diferentes ao longo do tempo) é defensável estatisticamente porque a sub-amostragem de pontos vizinhos ainda captura o mesmo conjunto de indivíduos.

### 2.3 Fauna do Campus 2 — silvestre e sinantrópica

> **Decisão de projeto (revisão 13/maio/2026).** O Campus 2 da USP São Carlos preserva **mata nativa** e está em **proximidade ecológica ao Cerrado UFSCar** (campus vizinho, mesmo município, mesmo bioma de transição Cerrado–Mata Atlântica). Isto significa que o sistema **precisa distinguir gato de fauna silvestre não-alvo** com robustez maior do que se o campus fosse exclusivamente urbano.

**Fauna esperada — classes funcionais:**

**(a) Fauna sinantrópica** — espécies adaptadas a viver junto ao humano em ambiente urbano:
- Cães errantes
- Pombos (*Columba livia*), pardais (*Passer domesticus*), bem-te-vis (*Pitangus sulphuratus*)
- Roedores: ratos (*Rattus norvegicus*, *Rattus rattus*), camundongos (*Mus musculus*)
- Gambás-de-orelha-branca (*Didelphis albiventris*) — frequentes em fragmentos urbanos do Cerrado ([Cerrado UFSCar — Belezas do Campus](https://sites.google.com/view/expo-sgas-ufscar/exposi%C3%A7%C3%B5es/belezas-do-campus))

**(b) Fauna silvestre** — espécies do bioma Cerrado / Mata Atlântica em transição, registradas no fragmento contíguo da UFSCar ([Cerrado UFSCar](https://sites.google.com/view/expo-sgas-ufscar/exposi%C3%A7%C3%B5es/belezas-do-campus), com **45 espécies de mamíferos** e **+200 espécies de aves** documentadas):
- Sagui-de-tufos-pretos (*Callithrix penicillata*)
- Quati (*Nasua nasua*) — grupos de até 15 indivíduos
- Tatu-galinha (*Dasypus novemcinctus*)
- Tamanduá-mirim (*Tamandua tetradactyla*)
- Veado-catingueiro (*Mazama gouazoubira*)
- Cotia (*Dasyprocta* spp.)
- Carcará (*Caracara plancus*)
- Lobo-guará (*Chrysocyon brachyurus*) — registrado no Cerrado UFSCar; presença no Campus 2 USP **improvável mas possível** em borda noturna
- Onça-parda (*Puma concolor*) — registrada no Cerrado UFSCar; presença no Campus 2 USP **muito improvável**

> **Nota.** A lista do Cerrado UFSCar é o **teto** da diversidade esperada. A maioria das espécies silvestres listadas tem **baixa probabilidade** de aparecer em pontos de alimentação na área **urbanizada** do Campus 2 USP. As **mais prováveis** de comparecer são: gambás, saguis, quatis, aves de médio porte. Capivaras (*Hydrochoerus hydrochaeris*) também são frequentes em campi USP — registradas em campus análogo ([USP "Luiz de Queiroz", Piracicaba](https://www.revistaea.org/artigo.php?idartigo=5675)).

**Consequências para o projeto (atualizações no pipeline B2):**

- **RF-02 (detecção de animal) e RF-03 (classificação de espécie)** ganham peso operacional. Não basta detectar "movimento" ou "animal" — é necessário **classificação multi-classe** capaz de distinguir pelo menos: **gato doméstico × cão × gambá × sagui × quati × ave × roedor × humano**.
- O modelo de classificação escolhido (**SpeciesNet**, ver B2 Parte 2) já cobre fauna brasileira; isto valida sua escolha como E2 do pipeline.
- A **interferência de fauna não-alvo nos pontos de alimentação** justifica a recomendação de **comedouros anti-pragas** (ver § 3 desta nota), embora isto seja recomendação para a AEX, não escopo do TCC.

---

## 3. Pontos de alimentação: estado atual e recomendações

> **Escopo desta seção.** O TCC trabalha com **os pontos atuais como dados de entrada** — não modifica a infraestrutura existente. Esta seção documenta **(i)** as limitações dos arranjos atuais; **(ii)** o que a literatura prática recomenda para pontos de alimentação de colônias; **(iii)** uma proposta de **padrão mínimo** como subproduto do TCC para a AEX Gatosdoc2 — sem desviar do escopo principal.

### 3.1 Limitações dos arranjos atuais

Hoje os pontos do Campus 2 são compostos por **casinhas de material reciclado e potes de plástico no solo**, sem padronização entre pontos e sem identificação formal. Esse arranjo limita o monitoramento por imagem por três razões:

1. **Ângulo desfavorável** — gato no chão produz poucos pontos de vista úteis e gera oclusão por embalagens;
2. **Fundo visual heterogêneo** — dificulta segmentação e re-identificação;
3. **Ausência de identificação formal** — cria risco de interferência de terceiros e desconhecimento por voluntários novos.

### 3.2 Características de um ponto bem-desenhado (literatura consolidada)

A literatura prática internacional consolidou um padrão razoavelmente consensual para pontos de alimentação de colônias gerenciadas:

**Organizações de referência (internacionais):**
- **[Alley Cat Allies](https://www.alleycat.org/resources/feeding-station-options-gallery/) — *Feeding Station Options Gallery***: comparativo de oito modelos com vantagens/desvantagens detalhadas. Princípios: cobertura, plataforma elevada, drenagem, escoamento angular.
- **[Alley Cat Allies — Build a Feeding Station](https://www.alleycat.org/resources/build-a-feral-cat-feeding-station/)**: manual DIY com tina plástica de 30 galões elevada por 2x4s. Regra operacional: **remover ração não-consumida em 30 minutos** para evitar atrair pragas.
- **[Neighborhood Cats (NYC) — TNR Handbook](https://www.neighborhoodcats.org/how-to-tnr/colony-care/feeding-and-watering)**: alimentação programada (não livre-acesso), retirada de resto após 30–60 minutos, frequência de visitação dos voluntários.
- **[Best Friends Animal Society](https://bestfriends.org/resources/community-cat-program-handbook) — *Community Cat Program Handbook***: padrão de manejo de colônias gerenciadas, incluindo design de estações.

**Modelos brasileiros:** o uso de TNR/CED é regulamentado pela [Resolução CFMV 1.595/2024](https://crmvsp.gov.br/nova-resolucao-do-cfmv-redefine-identificacao-de-felinos-castrados/) e pela [Resolução CFMV 1.596/2024](https://ses.sp.bvs.br/wp-content/uploads/2024/04/U_RS-CFMV-1.596_260324.pdf), mas o **padrão físico de pontos de alimentação não está normatizado** no Brasil. Projetos universitários como o **PROCAES/UFRJ** e iniciativas locais em SP e RS usam adaptações do padrão Alley Cat Allies (tina elevada, comedouro coberto).

### 3.3 Características que servem ao bem-estar e ao monitoramento

| Característica | Razão de manejo | Ganho para monitoramento (imagem) |
|---|---|---|
| **Plataforma elevada (20–40 cm)** | Reduz acesso de ratos e cães; mantém ração seca em chuva | Ângulo frontal/lateral favorável para câmera; menos oclusão |
| **Cobertura contra chuva** | Clima Cwa de São Carlos (verão chuvoso) | Iluminação previsível; sombras estáveis; melhor desempenho IR à noite |
| **Fundo neutro** (parede da cobertura) | — | Segmentação e detecção mais simples |
| **Material durável** (PVC, madeira tratada, metal galvanizado) | Vida útil > 2 anos | Possibilita fixação de hastes/câmeras na própria estrutura |
| **Comedouros laváveis** (inox, cerâmica) | Higiene; evita microplásticos | Refletância previsível na imagem |
| **Posicionamento na borda de verde**, fora de fluxo intenso | Conforto dos gatos | Menos pessoas no quadro → menos falsos positivos não-felinos |
| **Alimentação programada** (não livre-acesso) | Reduz atração de pragas; evita desperdício | Permite **janela temporal previsível** de atividade |

### 3.4 Estratégias anti-pragas (pragas = ratos, pombos, fauna silvestre não-alvo)

A literatura internacional e fóruns especializados convergem em quatro estratégias:

1. **Elevação física** (60–90 cm sobre piso liso/metálico) — impede ratos de escalar ([reddit r/homestead](https://www.reddit.com/r/homestead/comments/1o4pnmx/rodent_proof_cat_feeder/); [Alley Cat Allies](https://www.alleycat.org/resources/feeding-station-options-gallery/)).
2. **Cobertura com entrada lateral estreita** — admite gato, exclui aves de médio porte (pombos, urubus) e cães.
3. **Alimentação programada com retirada após 30 minutos** — remove o atrator antes da chegada de noturnos (gambás, ratos).
4. **Comedouros seletivos** com RFID/microchip — alimentadores como **SureFeed Microchip Pet Feeder** ([Kittyclysm review, 2019](https://kittyclysm.com/outdoor-cat-feeding-stations/)) liberam ração apenas para gatos cadastrados. **Custo alto** (~R$ 800–1.200 por unidade), inviável em escala de 10 pontos.

> **Recomendação para a AEX Gatosdoc2 (subproduto do TCC, não escopo central).** Padronizar os pontos com **plataforma elevada + cobertura + alimentação programada** já elimina ~80% dos problemas de fauna não-alvo, a custo baixo (R$ 100–200 por ponto em material). A discussão técnica detalhada e o cronograma de implantação são tratados em B5 como **continuidade do projeto**.

---

## 4. Modelo do ambiente — matriz de perfis de ponto

Esta é a **contribuição central de B1**: classificar cada ponto segundo duas dimensões binárias que determinam diretamente o desenho do nó de aquisição:

- **Energia disponível** — há tomada AC acessível em até ~10 m? (Sim / Não)
- **Conectividade Wi-Fi** — o ponto está dentro de área de cobertura usável da rede USPnet ou de Wi-Fi de algum prédio? (Sim / Não)

### 4.1 Matriz de perfis — nomenclatura funcional

> **Decisão de projeto (revisão 13/maio/2026).** Adotou-se nomenclatura **funcional** (não-grega, não-alfabética) para os perfis, baseada nas características operacionais do ponto. Padrão similar ao usado em redes de camera trapping internacionais ([Wildlife Insights — Network Design](https://www.wildlifeinsights.org/)).

```
                      Conectividade Wi-Fi
                  ┌─────────────────┬─────────────────┐
                  │       SIM       │       NÃO       │
       ┌──────────┼─────────────────┼─────────────────┤
       │          │      AC+NET     │       AC        │
   SIM │  Energia │  (com energia   │  (com energia,  │
       │   AC     │   e rede)       │   sem rede)     │
       ├──────────┼─────────────────┼─────────────────┤
       │          │      NET        │     OFF-SD      │  ◄── CASO PRIMÁRIO
   NÃO │  Energia │  (sem energia,  │  (sem energia,  │
       │   AC     │   com rede)     │   sem rede)     │
       └──────────┴─────────────────┴─────────────────┘
```

| Código | Energia AC | Conectividade | Cenário típico no Campus 2 | Estratégia operacional |
|---|---|---|---|---|
| **OFF-SD** ⭐ | Não | Não | Borda de mata, terreno baldio anexo, áreas verdes afastadas | **Câmera autônoma + cartão SD + voluntário troca cartão periodicamente.** Caso primário do TCC. |
| **NET** | Não | Sim (USPnet/prédio) | Praça arborizada sob cobertura Wi-Fi externa | Energia por bateria + solar; transmissão por Wi-Fi |
| **AC** | Sim (tomada ≤10 m) | Não | Garagem, depósito com tomada, mas fora de cobertura Wi-Fi | Câmera AC com armazenamento local; sincronização periódica |
| **AC+NET** | Sim | Sim | Próximo a entrada/parede de prédio (Engenharia, biblioteca, RU) | Câmera IP + processamento centralizado em servidor |

⭐ **OFF-SD é o caso primário do TCC.** Os demais são **evoluções opcionais** quando há infraestrutura disponível.

### 4.2 Razões para OFF-SD ser o caso primário

> **Decisão técnica revisada (13/maio/2026).** Embora cenários online com PIR + Wi-Fi sejam tecnicamente superiores em latência e cobertura temporal, a realidade do Campus 2 favorece o caso **OFF-SD** como caso-base do projeto. Justificativas:

1. **Realidade do Campus 2.** A maior parte dos pontos de alimentação está em áreas com mata, distante de prédios com tomada acessível e rede confiável. Forçar todos os pontos a serem "online" obrigaria a infraestrutura de extensão elétrica e/ou repetidores Wi-Fi inviáveis no curto prazo.

2. **Custo de entrada baixo.** Câmeras IP baratas (~R$ 150–300) com cartão SD operam em modo *motion-trigger* sem dependência de rede ou alimentação contínua. Várias funcionam com bateria interna recarregável, autonomia de dias a semanas.

3. **Pipeline desacoplado do modelo físico.** Como o pipeline (B2) processa **arquivos de mídia** (vídeo ou imagem) independentemente de origem, o caso OFF-SD não impõe restrição técnica ao sistema de processamento — apenas adiciona uma etapa de **importação manual** via cartão SD/pen-drive.

4. **Argumento metodológico forte.** Provar que o sistema funciona no **pior caso de infraestrutura** demonstra robustez. Os cenários NET, AC, AC+NET passam a ser **otimizações** quando houver recurso, não pré-requisitos.

5. **Convergência com camera trapping clássico.** O modelo OFF-SD é exatamente o protocolo padrão de wildlife camera trapping há 30 anos ([Lifeplan Camera Trapping Protocol, 2023](https://www.protocols.io/view/lifeplan-camera-trapping-protocol-c5uky6uw.pdf); [Saving Nature — Camera Trapping Protocol, 2024](https://savingnature.com/camera-trapping-protocol/)). A literatura recomenda **visita semanal a quinzenal** para troca de SD e baterias em pesquisa de fauna, com frequência mensal a trimestral para câmeras remotas — a **frequência exata para o Campus 2 dependerá de testes-piloto** (capacidade de cartão SD utilizado, taxa de eventos por ponto, autonomia de bateria).

### 4.3 Visualização do espaço de problema

```
       Complexidade de instalação
           ▲
           │
  AC+NET ──┤                              ●  (mais simples)
           │
       AC ──┤                    ●
           │
      NET ──┤          ●
           │
   OFF-SD ──┤  ●  ⭐  (mais autônomo — caso primário do TCC)
           │
           └──────────────────────────────────────────►
                Disponibilidade de infraestrutura
```

**Princípio "máximo com mínimo" aplicado:** *o sistema precisa de quatro respostas, não uma só.* OFF-SD é a **resposta padrão**; AC+NET é a resposta otimizada quando há infraestrutura.

### 4.4 Distribuição esperada dos pontos pela matriz

Sem o levantamento de campo (ver § 6), só é possível estimar. **Hipótese a ser validada/refutada pelo autor:**

| Perfil | Estimativa | Justificativa hipotética |
|---|---|---|
| **OFF-SD** ⭐ | **5–7** pontos | Áreas com mata, terreno baldio, bordas — maioria dos pontos de alimentação atuais |
| **NET** | 1–2 pontos | Praças arborizadas com cobertura Wi-Fi externa de prédios próximos |
| **AC** | 1–2 pontos | Áreas administrativas com tomada mas sem Wi-Fi confiável |
| **AC+NET** | 1–2 pontos | Próximos a entradas de prédios |
| **Total** | **~10** | Estimativa pendente de confirmação em campo |

> **Tarefa do autor (ficha de campo § 6):** confirmar/ajustar essa distribuição visitando cada ponto. **`[PLACEHOLDER]`** — preencher após levantamento.

---

## 5. Mapa dos pontos — instruções operacionais

> **Tarefa do autor.** O mapa do Campus 2 com a localização dos pontos é elemento gráfico obrigatório da monografia (Cap. 3 — Materiais e Métodos). Esta seção fornece o **passo a passo operacional** para produzi-lo.

### 5.1 Coleta de coordenadas em campo

**Equipamento mínimo:**
- Smartphone com GPS (Android ou iOS) — não precisa ser de alta precisão; precisão de 5–10 m basta para escala de campus
- App de coordenadas:
  - **Android:** [GPS Test](https://play.google.com/store/apps/details?id=com.chartcross.gpstest) (free) ou [OSMAnd](https://osmand.net/) (offline maps)
  - **iOS:** [GPS Status](https://apps.apple.com/app/gps-status-coordinates/id1106321027) ou [Maps.me](https://maps.me/)
  - **Web (sem app):** [Google Maps](https://www.google.com/maps) — clicar com botão direito no ponto → "What's here?" mostra coordenadas

**Formato:** **WGS84 graus decimais** (ex.: `-22.0087, -47.8909`).

**Procedimento por ponto:**
1. Posicionar-se na **estrutura central** do ponto de alimentação (comedouro principal).
2. Aguardar **30–60 segundos** com o GPS aberto para estabilização (especialmente sob copa densa).
3. Anotar: **latitude, longitude, altitude, precisão estimada (m)**.
4. Tirar **3 fotos** do ponto:
   - **Frente** — visão geral do ponto;
   - **Entorno** — paisagem ao redor (~10 m de raio);
   - **Vegetação imediata** — cobertura do céu, copa, abrigo natural.
5. Preencher **ficha de campo** (§ 6).

### 5.2 Produção do mapa final

**Opção A — QGIS (recomendado para a monografia):**

[QGIS](https://qgis.org/) é o software de SIG (Sistema de Informações Geográficas) open-source padrão acadêmico. Vantagens: profissional, exporta PDF/PNG de alta resolução, permite sobrepor camadas (limite do campus, edificações, áreas verdes).

Passos básicos:
1. Instalar QGIS (`sudo apt install qgis` no Linux Mint).
2. Criar projeto novo em CRS **WGS84 (EPSG:4326)**.
3. Adicionar camada **OpenStreetMap** (Plugin → Quick Map Services → OSM Standard).
4. Criar camada vetorial **Pontos** (Camada → Criar Camada → Camada *Shapefile*).
5. Adicionar cada ponto com coordenadas anotadas.
6. Categorizar pontos por perfil (OFF-SD / NET / AC / AC+NET) — cores diferentes.
7. Adicionar **escala**, **rosa-dos-ventos**, **título** e **legenda**.
8. Exportar como **PDF** (Project → Import/Export → Export Map to PDF) — para inserir no LaTeX com `\includegraphics`.

**Opção B — Google My Maps (mais simples, qualidade menor):**

Para um mapa mais rápido sem rigor de SIG: [mymaps.google.com](https://www.google.com/maps/d/).
1. Criar mapa novo.
2. Adicionar cada ponto via clique ou coordenadas.
3. Personalizar ícones por categoria.
4. **Limitação:** exportação como imagem é por captura de tela (qualidade média).

### 5.3 Inserção na monografia

Espaço reservado no LaTeX (Cap. 3 — Materiais e Métodos):

```latex
\begin{figure}[H]
  \centering
  \includegraphics[width=0.85\linewidth]{img/cap3_metodo/mapa_pontos_campus2.pdf}
  \caption{Localização dos pontos de alimentação da AEX Gatosdoc2 no Campus 2
           da USP São Carlos. Pontos categorizados por perfil de infraestrutura
           (OFF-SD, NET, AC, AC+NET). [PLACEHOLDER — figura a inserir após
           levantamento de campo.]}
  \label{fig:mapa-pontos-campus2}
\end{figure}
```

> **`[PLACEHOLDER-MAPA-PONTOS]`** — o autor preenche após o levantamento de campo.

### 5.4 Outras figuras gráficas a produzir (lista de placeholders)

| ID | Figura | Quando produzir | Ferramenta sugerida |
|---|---|---|---|
| `[FIG-MAPA-PONTOS]` | Mapa do Campus 2 com pontos categorizados | Após levantamento de campo | QGIS ou Google My Maps |
| `[FIG-FOTOS-PONTOS]` | Painel com 3 fotos por ponto (× 10 pontos) | Durante levantamento de campo | Smartphone + ImageMagick para montagem |
| `[FIG-COMEDOURO-ATUAL]` | Foto exemplar do estado atual de um ponto | Durante levantamento | Smartphone |
| `[FIG-COMEDOURO-PROPOSTO]` | Desenho/foto do padrão proposto (subproduto) | Cap. 7 (Recomendações) | Inkscape ou foto de modelo similar |
| `[FIG-DIAGRAMA-CAMPUS]` | Esquema simplificado do campus com áreas | Cap. 3 | Inkscape ou PowerPoint (depois exportar PDF) |
| `[FIG-HARDWARE-NOTEBOOK]` | Foto do notebook usado no processamento | Após especificação do hardware | Smartphone |

---

## 6. Ficha de levantamento de campo (entregável)

Esta ficha estrutura a coleta de dados que **o autor e os voluntários da AEX Gatosdoc2 precisam realizar**. Uma ficha por ponto. Os dados alimentam B4 (atribuição de perfis de nó), B5 (plano de piloto) e B6 (análises inferenciais).

### 6.1 Objetivos da ficha (três níveis)

A ficha tem **três funções simultâneas**:

1. **Engenharia** — dados físicos (energia, conectividade, fixação, microclima) para escolha do perfil de nó.
2. **Manejo** — estado atual do ponto (estrutura, higiene, ração, mantenedores) para recomendações e pano de fundo das análises.
3. **Inferencial** — observações dos voluntários sobre uso pelos gatos, contexto humano, dinâmica esperada — servindo como **ground truth qualitativo**.

### 6.2 Estrutura da ficha

```
═══════════════════════════════════════════════════════
  FICHA DE LEVANTAMENTO — PONTO P-XX
  Versão 2 — 13/maio/2026
═══════════════════════════════════════════════════════

[1] IDENTIFICAÇÃO E LOCALIZAÇÃO
    • Código interno: P-01 / ... / P-10
    • Apelido AEX Gatosdoc2: ___________________________
    • Mantenedor(es) atual(is): ____________________
    • Data de criação do ponto (aproximada): ______
    • Coordenadas (lat, lon, altitude): ____________
    • Precisão GPS (m): ____________
    • Referência textual ("atrás do bloco X, lateral leste"): _______
    • Fotos: frente, entorno, vegetação (3 fotos)
    • Croqui mão-livre do entorno: anexar

[2] ENERGIA
    • Tomada AC em até 10 m?            ( ) Sim ( ) Não
    • Distância à tomada mais próxima:  ____ m
    • Tomada acessível 24h?             ( ) Sim ( ) Não ( ) Apenas horário comercial
    • Quadro elétrico visível?          ( ) Sim ( ) Não   Onde? ____________
    • Área recebe sol direto > 4 h/dia? ( ) Sim ( ) Não  (relevante para solar)
    • Tipo de fixação possível:         ( ) Parede ( ) Poste ( ) Árvore ( ) Cobertura ( ) Outro: ____
    • Altura recomendada de instalação (m): ____
    • Iluminação noturna pública?       ( ) Sim ( ) Não  Tipo: ____________

[3] CONECTIVIDADE
    • Sinal Wi-Fi USPnet:    RSSI ____ dBm   SSID visível? ( ) Sim ( ) Não
    • Outras redes Wi-Fi visíveis: ___________________________________
    • Sinal 4G — Vivo: ___ barras  TIM: ___  Claro: ___  Oi: ___
    • Speedtest 4G (Mbps, melhor operadora): down ____ up ____ ping ____ ms
    • Visada ótica para janela de prédio mais próximo? ( ) Sim ( ) Não  Distância: ____ m
    • Cabo Ethernet viável?             ( ) Sim ( ) Não  Comprimento estimado: ____ m

[4] AMBIENTE FÍSICO E MICROCLIMA
    • Cobertura do céu:                 ( ) Aberta ( ) Parcial ( ) Sob copa densa
    • Insolação direta:                 ( ) Manhã ( ) Tarde ( ) Pouca ( ) Nenhuma
    • Exposição a chuva direta:         ( ) Total ( ) Parcial ( ) Protegida
    • Risco de alagamento/escorrimento? ( ) Sim ( ) Não
    • Vegetação próxima (espécie, densidade): _________________
    • Fundo visual no enquadramento da câmera: ( ) Neutro ( ) Poluído ( ) Movimento (folhas)

[5] ESTRUTURA FÍSICA DO PONTO
    • Tipo de estrutura:                ( ) Casinha reciclada ( ) Pote no chão ( ) Plataforma improvisada ( ) Outra: ____
    • Material predominante:            _____________________
    • Cobertura contra chuva?           ( ) Sim ( ) Não ( ) Parcial
    • Plataforma elevada?               ( ) Sim ( ) Não    Altura: ___ cm
    • Comedouros: quantos? ____   Material: _________  Estado: ( ) Bom ( ) Regular ( ) Ruim
    • Bebedouros: quantos? ____   Estado: ____________
    • Abrigo separado da alimentação?   ( ) Sim ( ) Não
    • Limpeza percebida no momento:     ( ) Limpo ( ) Aceitável ( ) Sujo
    • Foto da estrutura: anexar

[6] LOGÍSTICA DE MANEJO
    • Frequência de reposição de ração: ____ vezes/dia ou ____ vezes/semana
    • Horários habituais de reposição:  __________________________
    • Número e identificação dos voluntários responsáveis: ______
    • Hora de chegada/saída dos voluntários: ______________________
    • Tipo de ração usada:              _____________________
    • Origem da ração (doação/compra/USP): _________________
    • Medicação oferecida nesse ponto?  ( ) Sim ( ) Não  Qual? ____
    • Acesso ao ponto em caso de chuva forte? ( ) Fácil ( ) Difícil ( ) Impossível

[7] USO PELOS GATOS (observação dos voluntários)
    • Número de gatos vistos:  média ____  máximo ____  mínimo ____
    • Indivíduos reconhecidos individualmente: ____ (descrever brevemente)
    • Horários típicos de aparição:     __________________________
    • Ear-tipped vs. não ear-tipped:    ____ / ____
    • Filhotes vistos no último mês?    ( ) Sim ( ) Não    Quantos? ____
    • Sinais visíveis de doença/ferimento? ( ) Sim ( ) Não  Descrever: ____
    • Resposta à presença humana:       ( ) Aproximam ( ) Toleram ( ) Fogem
    • OUTRAS ESPÉCIES VISTAS NO PONTO:
       ( ) Cães  ( ) Pombos  ( ) Outras aves  ( ) Gambás  ( ) Saguis
       ( ) Quatis  ( ) Capivaras  ( ) Tatus  ( ) Roedores  ( ) Outros: ____
    • Frequência das outras espécies:   ( ) Diária ( ) Semanal ( ) Eventual

[8] CONTEXTO HUMANO E INSTITUCIONAL
    • Fluxo de pessoas em horário letivo:   ( ) Alto ( ) Médio ( ) Baixo
    • Fluxo em horário noturno:             ( ) Alto ( ) Médio ( ) Baixo
    • Fluxo durante férias:                 ( ) Alto ( ) Médio ( ) Baixo ( ) Nulo
    • Prédios próximos (uso predominante):  _________________
    • Distância ao prédio mais próximo:     ____ m
    • Frequentadores não-voluntários que alimentam? ( ) Sim ( ) Não ( ) Desconhecido
    • Histórico de reclamações de funcionários/alunos? ( ) Sim ( ) Não
    • Risco de vandalismo (subjetivo):      ( ) Alto ( ) Médio ( ) Baixo
    • Câmera de segurança USP no entorno?   ( ) Sim ( ) Não  Quantas? ____

[9] IDENTIFICAÇÃO DO PONTO (estado atual)
    • Há placa identificando o projeto?    ( ) Sim ( ) Não
    • Há QR code/contato visível?          ( ) Sim ( ) Não
    • Há alguma comunicação ao público?    ( ) Sim ( ) Não  Descrever: ____
    • Aviso de câmera futura será necessário? ( ) Sim ( ) Não (LGPD)

[10] AVALIAÇÃO TÉCNICA PARA CÂMERAS (preencher in loco)
    • Ponto de fixação ideal identificado? ( ) Sim ( ) Não   Onde? ______
    • Alcance esperado da câmera no ângulo principal: ____ m
    • Área útil de detecção (estimada):    ____ m²
    • Risco de superexposição solar?       ( ) Sim ( ) Não
    • Risco de backlight (sol contra a câmera)? ( ) Sim ( ) Não
    • Tem como esconder cabos?             ( ) Sim ( ) Não ( ) Parcial
    • Acesso para troca de SD/bateria:     ( ) Fácil ( ) Difícil
    • Necessita de poda/limpeza para boa visada? ( ) Sim ( ) Não

[11] CLASSIFICAÇÃO DERIVADA (preencher após coleta)
    • Energia AC disponível?               ( ) Sim ( ) Não
    • Wi-Fi usável? (RSSI > -75 dBm)       ( ) Sim ( ) Não
    • 4G usável?                           ( ) Sim ( ) Não
    • PERFIL ATRIBUÍDO:                    ( ) OFF-SD ( ) NET ( ) AC ( ) AC+NET
    • Prioridade no piloto:                ( ) Alta ( ) Média ( ) Baixa
    • Observações livres do pesquisador:   ______________________
═══════════════════════════════════════════════════════
```

### 6.3 Instrumentação mínima

- Aplicativo de medição de Wi-Fi (Android: WiFiAnalyzer) — RSSI em dBm.
- App de teste de 4G (Speedtest, OpenSignal) — testar duas operadoras pelo menos.
- App de GPS com altitude (Google Maps, GPS Test).
- Trena ou estimação visual para distâncias.
- Smartphone com câmera para fotos de contexto.
- Caderno + caneta (mais confiável que app em ambiente externo úmido).
- Bússola (ou app) para orientação solar.
- Termo-higrômetro de bolso (opcional, para microclima).

### 6.4 Output esperado

Dois entregáveis derivados:

1. **Tabela consolidada** de 10 linhas com colunas PERFIL e prioridade preenchidas — insumo de B4.
2. **Mapa anotado** do Campus 2 (§ 5) — insumo de B5 e B6.

### 6.5 Perguntas inferenciais ancoradas na ficha

Cada bloco mapeia para **perguntas inferenciais** que o sistema, em operação, deve ajudar a responder. Consolidadas em B6.

| ID | Pergunta | Bloco-fonte | Dado produzido pelo sistema |
|---|---|---|---|
| Q-INF-01 | Pontos isolados atraem mais ou menos gatos do que pontos próximos a prédios? | [4], [8] | Contagem por re-ID por ponto |
| Q-INF-02 | Existe raio ótimo entre pontos para reduzir disputas? | [1] | Sobreposição de indivíduos |
| Q-INF-03 | Consolidar N pontos em M < N pontos manteria a cobertura? | [1] + [7] | Simulação de remoção |
| Q-INF-04 | Quais pontos são "primários" e quais são "satélites"? | [7] | Distribuição de indivíduos |
| Q-INF-05 | Maior movimentação de pessoas reduz uso ou apenas desloca horários? | [8] | Histograma temporal |
| Q-INF-06 | Há correlação entre tipo de prédio e indivíduos? | [8] + [1] | Re-ID cruzada com tipologia |
| Q-INF-07 | Presença de voluntários altera padrão de aparição? | [6] | Antes/depois da alimentação |
| Q-INF-08 | Qual o tamanho real da colônia? | [7] | Re-ID, *capture–recapture* |
| Q-INF-09 | Há indivíduos transitórios vs. residentes? | [7] | Série temporal por ID |
| Q-INF-10 | A cobertura de castração é completa? | [7] | Detecção de *ear-tip* |
| Q-INF-11 | Sobreposição de uso entre pontos? | [1] + [7] | Re-ID *cross-camera* |
| Q-INF-12 | Há sinais visíveis de doença/ferimento? | [7] | Inspeção assistida |
| Q-INF-13 | Condição corporal varia entre pontos? | [5] + [7] | Escore visual assistido |
| Q-INF-14 | Há padrões sazonais? | [4] | Série temporal longa |
| Q-INF-15 | Outras espécies competem pelos pontos? | [7] | Classificação multi-classe |
| Q-INF-16 | Há predação registrada? | [7] | Eventos co-temporais |
| Q-INF-17 | Quais pontos justificam manter, remover ou criar? | todos | Síntese B6 |
| Q-INF-18 | Onde alocar recursos limitados com máximo retorno? | [6] + [7] | Análise de cobertura |
| Q-INF-19 | Como subsidiar relatórios trimestrais ao [Decreto 12.439/2025](https://www.planalto.gov.br/ccivil_03/_Ato2023-2026/2025/Decreto/D12439.htm)? | todos | Template de relatório |

> **Como esta lista entra no TCC.** Ela é introduzida em B1 (justificativa de coleta), retomada em B5 (plano de validação) e consolidada em **B6 como entregável analítico**. O **TCC não responde** as 19 perguntas (muitas exigem meses), mas **define** quais são respondíveis e **demonstra** o método em 2–3 delas no piloto.

---

## 7. Restrições humanas, institucionais e legais

### 7.1 Marco legal vigente

| Norma | Conteúdo relevante | Implicação |
|---|---|---|
| **Lei 13.426/2017** | Política nacional de controle populacional de cães e gatos (CED) | Sustenta legalidade do trabalho da AEX Gatosdoc2 |
| **Decreto 12.439/2025** ([Planalto](https://www.planalto.gov.br/ccivil_03/_Ato2023-2026/2025/Decreto/D12439.htm)) | Programa Nacional de Manejo Populacional Ético; microchipagem, registro, vacinação, castração | Cria diretriz nacional alinhada ao manejo ético. Identificação digital ganha base legal |
| **Resolução CFMV 1.595/2024 e 1.596/2024** | Diretrizes para CED e *ear-tipping* | Define padrão técnico das ações da AEX |
| **LGPD (Lei 13.709/2018)** | Lei Geral de Proteção de Dados Pessoais | **Privacidade de pessoas filmadas** acidentalmente. RNF-17 (anonimização) |
| **Regulamento USP / PUSP-SC** | Sem informação consolidada | Lacuna — ver § 8 |

### 7.2 Atores e suas responsabilidades

> **Decisão de projeto (revisão 13/maio/2026).** Atores apresentados como **papéis genéricos**, sem nomes próprios. Os autores do TCC, advisor e coordenadora AEX aparecem apenas em capa, agradecimentos e bibliografia.

```
┌──────────────────────────────────────────────────────┐
│ Atores envolvidos no sistema                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Autor(es) ── concepção do TCC e implementação       │
│       │                                              │
│       ▼                                              │
│  Orientador ── validação técnica e acadêmica         │
│       │                                              │
│       ▼                                              │
│  Coordenação AEX Gatosdoc2 ── parceria operacional;  │
│       │                       acervo histórico       │
│       ▼                                              │
│  Voluntários alimentadores ── rotina nos pontos;     │
│       │                       observações de campo   │
│       ▼                                              │
│  CEUA ICMC/USP ── ética em pesquisa, se Etapa 3      │
│       │           gerar dados primários              │
│       ▼                                              │
│  PUSP-SC + STI USP ── autorização para instalação    │
│                       física e uso de rede           │
│                                                      │
│  Pesquisador externo (referência metodológica) ──    │
│      consulta sobre padrões de camera trapping       │
└──────────────────────────────────────────────────────┘
```

### 7.3 Restrições ambientais físicas (clima de São Carlos)

São Carlos tem clima **Cwa** (subtropical de altitude), com **estação chuvosa de outubro a março** e estação seca de abril a setembro. Temperatura média anual ~21 °C.

| Variável climática | Implicação para o hardware |
|---|---|
| Chuva intensa concentrada | **IP66 obrigatório** para nós outdoor (RNF-15) |
| Sol forte em meses secos | Risco térmico; preferência por **caixas claras e ventilação passiva**. **LiFePO4** sobre íon-lítio NMC em cenários solares (mais estável termicamente) |
| Variação noite/dia ~10 °C | Tolerável para SBCs comerciais (RPi opera 0 a +50 °C) |
| Insolação anual (São Carlos) | ~5,2 kWh/m²/dia ([CRESESB/SunData](http://www.cresesb.cepel.br/)) — dimensionamento solar dos perfis NET/OFF-SD com bateria recarregada por painel pequeno |

### 7.4 Restrições humanas operacionais

- **Acesso noturno aos pontos.** Picos de gatos ocorrem na madrugada — voluntários **não estão presentes**. O sistema opera **autônomo** nesses períodos. Reforça a aquisição por *motion-detection* com armazenamento local.
- **Manutenção e rotação.** Rotação de câmeras (poucas câmeras, vários pontos) **acrescenta tempo de voluntariado**. Sistema deve ser **simples de instalar/desinstalar** (montagem rápida, sem ferramentas exóticas).
- **Vandalismo e furto.** Campus universitário sofre furtos esporádicos. Câmeras visíveis em pontos externos devem ter **fixação anti-furto** e, idealmente, valor de mercado baixo. Isto reforça o caso OFF-SD com câmera IP barata (R$ 150–300) em vez de equipamento caro.

---

## 8. Hipóteses e lacunas

### 8.1 Hipóteses operacionais adotadas

| ID | Hipótese | Justificativa | Risco se falsa |
|---|---|---|---|
| H1 | Os ~10 pontos cobrem a maior parte do *home range* dos ~50 gatos | Pontos de alimentação são atratores fortes ([Horn 2011](https://wildlife.onlinelibrary.wiley.com/doi/10.1002/jwmg.145)) | Indivíduos não detectados não entram na base — subestimativa populacional |
| H2 | Atividade dos gatos é majoritariamente crepuscular e noturna | Convergente em [Cove 2022](https://doi.org/10.1002/ece3.8771), [Zhang 2022](https://www.mdpi.com/2076-2615/12/9/1141), [Zacharia 2026](https://www.mdpi.com/2076-2615/16/7/1101) | Pouca consequência (captura disparada por evento funciona em qualquer horário) |
| H3 | A maior parte dos pontos será **OFF-SD** | Campus 2 com mata, pontos afastados de prédios | Se falsa, mais pontos terão infraestrutura — **simplifica** o projeto, não complica |
| H4 | A USP autorizará instalação de equipamentos discretos para pesquisa | Há parceria com AEX e tradição de pesquisa | Se falsa, todo o piloto físico fica em risco — TCC vira **conceitual puro**, mas mantém valor metodológico |
| H5 | Fauna silvestre (sagui, quati, gambá) frequentará os pontos com baixa-média frequência | Proximidade ao Cerrado UFSCar; literatura local | Se mais frequente: oportunidade adicional (Q-INF-15, Q-INF-16); se menos frequente: simplifica o pipeline E2 |

### 8.2 Lacunas a fechar

(Replicadas em `fontes_e_lacunas.md`)

- [ ] **Distribuição real dos ~10 pontos na matriz de perfis** — ficha de campo § 6
- [ ] **Política da STI USP** para conectar câmeras à USPnet
- [ ] **Política da PUSP-SC** para instalação de equipamentos fixos
- [ ] **Cobertura 4G** no Campus 2 por operadora (importante para AC e OFF-SD com módulo 4G opcional)
- [ ] **Acervo Gatosdoc2** — protocolo de uso (qualitativo)
- [ ] **Padrão escrito de feeding station** da AEX — não existe; oportunidade de subproduto
- [ ] **Política institucional USP de sinalização LGPD** para câmeras de pesquisa em campus
- [ ] **Especificações finais do notebook de processamento** — `[PLACEHOLDER-HARDWARE-NOTEBOOK]`

---

## 9. Síntese de B1 e ponte para B2

B1 entregou:

1. **Caracterização do sítio:** Campus 2 USP São Carlos, mata nativa, proximidade ao Cerrado UFSCar (~45 mamíferos, ~200 aves catalogados), parceria AEX Gatosdoc2.
2. **Estimativas iniciais:** **`[~50 gatos]`** e **`[~10 pontos]`** — ambos a confirmar em campo.
3. **Restrições comportamentais:** atividade bimodal crepuscular, *home range* pequeno e agregado, *cross-camera re-ID* necessária, classificação multi-classe de espécie (gato × cão × sagui × quati × gambá × aves × roedores × humano) obrigatória.
4. **Modelo de ambiente:** matriz energia × conectividade com **4 perfis funcionais** — **OFF-SD (caso primário)**, NET, AC, AC+NET. OFF-SD é a base; demais são otimizações com infraestrutura disponível.
5. **Recomendações operacionais para a AEX (subproduto, não escopo central):** estações de alimentação elevadas, cobertas, com alimentação programada e retirada em 30 min — referenciadas em [Alley Cat Allies](https://www.alleycat.org/resources/feeding-station-options-gallery/), [Neighborhood Cats](https://www.neighborhoodcats.org/), [Best Friends](https://bestfriends.org/).
6. **Ficha de campo v2** (11 blocos) e **instruções operacionais para o mapa** (§ 5) — entregas pendentes do autor.
7. **19 perguntas inferenciais** ancoradas nos blocos da ficha — base do relatório analítico B6.
8. **Restrições legais, institucionais, ambientais e humanas** — marco regulatório federal recente (Decreto 12.439/2025) alinha o projeto a uma política pública.
9. **Hipóteses operacionais H1–H5** e **lacunas explícitas** para fechamento ao longo do projeto.

**Próximo passo (B2):** definir o **pipeline conceitual de visão computacional** (Aquisição → Detecção → Classificação → Re-ID → Persistência) e os modelos candidatos, **independentemente** de onde rodam e de qual perfil de ponto está sendo servido. O acoplamento com os perfis ocorre apenas em B4.

---

## 10. Placeholders ativos neste bloco

| Tag | Descrição | Quem completa | Quando |
|---|---|---|---|
| `[~50 gatos]` | População estimada — confirmar | Autor + voluntários AEX | Após levantamento |
| `[~10 pontos]` | Pontos ativos — confirmar | Autor + voluntários AEX | Após levantamento |
| `[PLACEHOLDER-MAPA-PONTOS]` | Mapa SIG do Campus 2 | Autor | Após GPS dos pontos |
| `[PLACEHOLDER-HARDWARE-NOTEBOOK]` | Specs do notebook usado no processamento | Autor | Imediato |
| `[PLACEHOLDER-AEX]` | Parágrafo sobre a AEX Gatosdoc2 (na Etapa 1) | Autor | Antes do draft LaTeX |
| `[FIG-FOTOS-PONTOS]` | Painel de fotos dos 10 pontos | Autor | Durante levantamento |
| `[FIG-COMEDOURO-ATUAL]` | Foto exemplar de estrutura atual | Autor | Durante levantamento |
| `[FIG-DIAGRAMA-CAMPUS]` | Esquema do campus com áreas | Autor | Cap. 3 |

---

## Fontes citadas neste bloco

### Sobre o campus e marco institucional

- **Prefeitura do Campus USP São Carlos** — [Mapas e Aplicativos](https://prefeitura.sc.usp.br/mapas-e-aplicativos/); [Localização](https://prefeitura.sc.usp.br/localizacao/).
- **EESC USP — Endereços e Mapas** — [eesc.usp.br](https://eesc.usp.br/institucional/enderecos-mapas.php).
- **USP São Carlos — Guia de Calouros** — [saocarlos.usp.br](https://saocarlos.usp.br/guia-calouros/).
- **Decreto 12.439/2025** — Programa Nacional de Manejo Populacional Ético. [Planalto](https://www.planalto.gov.br/ccivil_03/_Ato2023-2026/2025/Decreto/D12439.htm).
- **Lei 13.426/2017** (já em A1.1).
- **Resoluções CFMV 1.595/2024 e 1.596/2024** (já em A1.1).

### Fauna do Campus 2 e proximidade ao Cerrado UFSCar

- **UFSCar — Cerrado: Belezas do Campus** ([sites.google.com/view/expo-sgas-ufscar](https://sites.google.com/view/expo-sgas-ufscar/exposi%C3%A7%C3%B5es/belezas-do-campus)) — **45 espécies de mamíferos e +200 de aves** catalogadas no fragmento contíguo ao Campus USP.
- **Coexistência com Fauna no Campus USP Luiz de Queiroz** (Piracicaba) ([revistaea.org, 2026](https://www.revistaea.org/artigo.php?idartigo=5675)) — caso análogo para gestão de fauna em campi USP.

### Comportamento de gatos comunitários

- **Horn J. A. et al. (2011)** — *Home Range, Habitat Use, and Activity Patterns of Free-Roaming Domestic Cats*. **J. Wildlife Management**. [doi:10.1002/jwmg.145](https://wildlife.onlinelibrary.wiley.com/doi/10.1002/jwmg.145).
- **Zhang Z. et al. (2022)** — *Home Range and Activity Patterns of Free-Ranging Cats: A Case Study from a Chinese University Campus*. **Animals 12(9):1141**. [doi:10.3390/ani12091141](https://www.mdpi.com/2076-2615/12/9/1141).
- **Johansson E., DeGregorio B. (2023)** — *Effects of landscape cover and yard features on feral and free-roaming cat distribution*. **Journal of Urban Ecology**. [doi:10.1093/jue/juad003](https://academic.oup.com/jue/article/doi/10.1093/jue/juad003/7161106).
- **Zacharia M. et al. (2026)** — *Living Wild in a Mediterranean Island*. **Animals 16(7):1101**. [doi:10.3390/ani16071101](https://www.mdpi.com/2076-2615/16/7/1101).
- **Gehrt S. et al. (2013)** — *Population Ecology of Free-Roaming Cats and Interference Competition by Coyotes in Urban Parks*. **PLOS ONE**. [doi:10.1371/journal.pone.0075718](https://dx.plos.org/10.1371/journal.pone.0075718).
- **López-Jara M. J. et al. (2021)** — *Free-roaming domestic cats near conservation areas in Chile*. **Perspectives in Ecology and Conservation**. [doi:10.1016/j.pecon.2021.02.001](https://linkinghub.elsevier.com/retrieve/pii/S253006442100016X).

### Camera trapping — protocolos de campo

- **Lifeplan Camera Trapping Protocol v.3** (2023) — [protocols.io](https://www.protocols.io/view/lifeplan-camera-trapping-protocol-c5uky6uw.pdf) — **frequência semanal** de visita a câmeras em pesquisa de fauna.
- **Saving Nature — Camera Trapping Protocol** (2024) — [savingnature.com](https://savingnature.com/camera-trapping-protocol/) — **mensal para câmeras acessíveis; trimestral para remotas**.
- **NTCA — Projeto Tigre Fase III Camera Trapping Protocol** (Índia) — [ntca.gov.in](https://ntca.gov.in/assets/uploads/Reports/AITM/Phase_III_CT%20Manual.pdf) — visita condicionada a risco de furto.
- **GBIF — Best Practices for Managing and Publishing Camera Trap Data** — [docs.gbif.org](https://docs.gbif.org/camera-trap-guide/) — padrão de organização de imagens em sequências.
- **Klemens J. A. et al. (2021)** — *A motion-detection based camera trap*. **Methods in Ecology and Evolution**. [doi:10.1111/2041-210X.13607](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.13607).

### Pontos de alimentação para colônias

- **Alley Cat Allies — Feeding Station Options Gallery** ([alleycat.org](https://www.alleycat.org/resources/feeding-station-options-gallery/)) — comparativo de 8 modelos.
- **Alley Cat Allies — Build a Feeding Station** ([alleycat.org](https://www.alleycat.org/resources/build-a-feral-cat-feeding-station/)) — manual DIY com tina elevada.
- **Neighborhood Cats — Feeding and Watering** ([neighborhoodcats.org](https://www.neighborhoodcats.org/how-to-tnr/colony-care/feeding-and-watering)) — manual TNR (2ª ed.).
- **Best Friends Animal Society — Community Cat Program Handbook** ([bestfriends.org](https://bestfriends.org/resources/community-cat-program-handbook)) — manejo de colônias gerenciadas.
- **Kittyclysm — Outdoor Cat Feeding Stations** (2019) ([kittyclysm.com](https://kittyclysm.com/outdoor-cat-feeding-stations/)) — revisão de alimentadores seletivos (SureFeed) e abrigos.
- **iNaturalist** ([inaturalist.org](https://www.inaturalist.org/)) — uso de QR para engajamento em pesquisa de campo.

### Climatologia regional (São Carlos)

- **CRESESB / CEPEL — Atlas Solarimétrico Brasileiro** ([SunData](http://www.cresesb.cepel.br/)) — insolação média em São Carlos.

### LGPD

- **Lei 13.709/2018 — LGPD** ([planalto.gov.br](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)).
