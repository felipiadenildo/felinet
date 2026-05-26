# Notas — pontos de alimentação e perguntas inferenciais futuras

Registro de observações do orientando (11/maio/2026) que **não são foco do TCC** mas
devem aparecer brevemente nas seções apropriadas e ser endereçadas no plano de
trabalhos futuros.

---

## 1. Perguntas inferenciais que o sistema deve ajudar a responder

Lista de perguntas pertinentes a serem formuladas no final da Etapa 2 e usadas
como **ancoradouro das métricas e dos relatórios** do sistema. Não são hipóteses
do TCC (que ficam restritas a métricas técnicas), mas **questões operacionais e
de manejo** que o sistema, ao funcionar, deve subsidiar.

### 1.1 Realocação e disposição espacial dos pontos

- **Q-INF-01.** Pontos mais isolados (vegetação, áreas remotas do campus) atraem
  mais ou menos gatos do que pontos próximos a prédios e fluxo humano?
- **Q-INF-02.** Existe um raio ótimo entre pontos de alimentação para reduzir
  sobreposição de uso e disputas territoriais sem dispersar a colônia?
- **Q-INF-03.** A consolidação de N pontos em M < N pontos (com M ideal a
  determinar) mantém a cobertura da colônia ou cria gatos órfãos de ponto?
- **Q-INF-04.** Quais pontos são "primários" (frequentados por muitos indivíduos)
  e quais são "satélites" (poucos indivíduos exclusivos)?

### 1.2 Impacto da atividade humana

- **Q-INF-05.** Maior movimentação de pessoas (período letivo vs. férias,
  diurno vs. noturno, eventos) reduz a frequência de uso pelos gatos? Ou apenas
  desloca para horários de menor fluxo?
- **Q-INF-06.** Há correlação entre proximidade a salas de aula / restaurantes /
  laboratórios e o número de indivíduos distintos detectados?
- **Q-INF-07.** A presença de voluntários durante a alimentação altera o padrão
  de aparição dos gatos (atraso, antecipação, ausência)?

### 1.3 Dinâmica da colônia

- **Q-INF-08.** Qual o tamanho real da colônia? Os ~50 indivíduos estimados se
  confirmam após contagem por re-identificação?
- **Q-INF-09.** Há indivíduos transitórios (aparecem por dias e somem) vs.
  residentes (aparecem sistematicamente)? Em que proporção?
- **Q-INF-10.** A cobertura da castração CED é completa? Há indivíduos não
  ear-tipped sendo detectados? Aparecem filhotes?
- **Q-INF-11.** Existe sobreposição de uso entre pontos? Um mesmo indivíduo
  visita quantos pontos por noite/semana?

### 1.4 Bem-estar e saúde da colônia

- **Q-INF-12.** Há sinais visíveis de doença (mancar, perda de pelo, ferimentos)
  detectáveis pelas imagens? Frequência por indivíduo?
- **Q-INF-13.** A condição corporal (escore visual) varia entre pontos? Algum
  ponto apresenta indivíduos sistematicamente em pior estado?
- **Q-INF-14.** Há padrões sazonais (calor, frio, chuva) na frequência de
  aparição e número de indivíduos ativos?

### 1.5 Interações inter-específicas

- **Q-INF-15.** Outros animais (cães, gambás, opossuns brasileiros, capivaras,
  aves) competem pelos pontos? Em que frequência?
- **Q-INF-16.** Há predação observada (sobre aves, pequenos mamíferos) registrada
  nos pontos? Relevante para a discussão Lei 14.064/2020 e justificativa do CED.

### 1.6 Planejamento e tomada de decisão

- **Q-INF-17.** Quais pontos justificam manter, quais justificam remover, quais
  justificam criar novos? Critério baseado em dados.
- **Q-INF-18.** Onde alocar recursos limitados (câmeras, voluntários, ração) com
  máximo retorno por indivíduo coberto?
- **Q-INF-19.** Como o sistema pode subsidiar relatórios trimestrais/anuais para
  a Prefeitura do Campus e o Decreto 12.439/2025?

> Estas perguntas serão **listadas em B6 (consolidação da Etapa 2) e detalhadas
> em B5 (plano de validação)**, conectando cada uma a uma métrica observável
> pelo pipeline (B2) e a um item da ficha de campo.

---

## 2. Pontos de alimentação ideais — referencial breve

### 2.1 Situação atual

Hoje os pontos do Campus 2 são compostos por:

- **Casinhas de material reciclado** (madeira, caixotes, embalagens) feitas por
  voluntários.
- **Potes de plástico** no solo para ração seca e água.
- Sem padronização entre pontos, sem identificação formal, sem registro
  estruturado de quem é mantenedor.

### 2.2 Limitações conhecidas dos arranjos atuais

- Potes de plástico no chão contaminam por chuva, fezes, formigas; ração úmida
  estraga rápido.
- Casinhas de reciclagem sem ventilação ou drenagem podem reter umidade
  (problema em clima Cwa de São Carlos).
- Falta de plataforma elevada dificulta a postura para câmeras (gato fica em
  ângulo desfavorável no chão).
- Sem identificação, qualquer pessoa pode interferir (mover, retirar, alimentar
  com outros itens).
- Sem QR code ou contato, voluntários novos não sabem o protocolo do ponto.

### 2.3 Referências para um ponto bem desenhado

Boas práticas documentadas para colônias gerenciadas em campus, condomínios e
áreas urbanas:

- **Alley Cat Allies — "Feline Frenzy: Feeding Station Best Practices"** —
  estação coberta, elevada, com identificação e cronograma fixo:
  https://www.alleycat.org/resources/feeding-feral-and-stray-cats/
- **Best Friends Animal Society — Community Cat Programs** — orientações sobre
  abrigo e alimentação em colônia:
  https://bestfriends.org/resources/community-cat-program-handbook
- **Neighborhood Cats — TNR Handbook (2nd ed.)** — capítulo sobre feeding
  stations padronizadas, com fotos de modelos em PVC, madeira tratada, e
  abrigos com isolamento térmico.
- **ANDA / Instituto Caramelo (BR)** — orientações em português adaptadas ao
  clima brasileiro:
  https://institutocaramelo.org/
- **USP CEUA / CCD** — normas internas eventuais para alimentação animal em
  campus (a investigar; lacuna).

### 2.4 Características de um ponto ideal (síntese)

Para discutir brevemente em **B1.6 (ficha) e B5 (plano de implementação)** como
recomendação de continuidade:

| Característica | Razão |
|---|---|
| **Plataforma elevada** (20-40 cm) | Mantém ração seca, dificulta acesso de cães e roedores, melhora ângulo para câmeras |
| **Cobertura** contra chuva | Clima Cwa de São Carlos tem verão chuvoso |
| **Dois compartimentos**: alimentação + abrigo | Separa função; abrigo isolado térmica/acusticamente |
| **Material durável** (PVC, madeira tratada, metal galvanizado) | Vida útil > 2 anos, manutenção mínima |
| **Comedouros e bebedouros laváveis** (inox ou cerâmica) | Higiene; plástico envelhece e libera microplásticos |
| **Identificação visível**: placa com nome do projeto, contato e QR code | Evita interferência de transeuntes, orienta voluntários novos |
| **Posicionamento**: borda de área verde, fora de fluxo intenso, com fundo neutro | Conforto dos gatos + facilidade para visão computacional |
| **Distância mínima entre pontos**: a determinar empiricamente | Reduz sobreposição e disputas |

### 2.5 Integração com o sistema de câmeras

Um ponto bem desenhado facilita a instalação da câmera:

- **Plataforma fixa** permite poste/haste de câmera ancorado na mesma estrutura.
- **Fundo neutro** (parede da cobertura) melhora segmentação e detecção.
- **Iluminação previsível**: cobertura permite estimar onde haverá sombra e onde
  o IR refletirá melhor.
- **Acesso para manutenção**: troca de bateria/SD card no mesmo local da
  reposição de ração.

> Esta discussão entra em **B1.6 (ficha de levantamento)** como item a coletar
> sobre o estado atual de cada ponto, e em **B5 (plano de implementação)** como
> recomendação para a parceria com a AEX Gatosdoc2 — não como atividade do TCC,
> mas como contribuição associada que melhora a coleta de dados.

---

## 3. Identificação dos pontos — placas, QR code e materiais

### 3.1 Por que identificar

Três razões interligadas:

1. **Evitar interferência da pesquisa**: pessoas que veem câmera sem contexto
   podem retirar, mover, vandalizar ou questionar formalmente.
2. **Engajar voluntários**: novos cuidadores precisam saber quem mantém o ponto,
   qual o cronograma, o que fazer em caso de animal ferido.
3. **Conformidade ética e legal**: monitoramento com câmeras em espaço público
   universitário deve declarar finalidade (LGPD para imagens incidentais de
   pessoas; transparência institucional).

### 3.2 Itens recomendados em cada ponto

- **Placa de identificação principal** (PVC ou metal, 20×30 cm) com:
  - Nome do projeto (AEX Gatosdoc2 + nome do TCC).
  - Logo USP + ICMC.
  - Texto curto: "Ponto de alimentação monitorado para pesquisa de manejo ético
    de colônia. Por favor, não retire, não alimente com outros itens, não
    interfira com a câmera."
  - **QR code** apontando para página com:
    - Descrição da pesquisa.
    - Cronograma do ponto.
    - Contato dos voluntários e do pesquisador.
    - Formulário para reportar problema.
- **Etiqueta na câmera** (5×8 cm) com:
  - "Câmera para pesquisa científica — Projeto Gatosdoc2 / TCC USP".
  - QR code curto.
  - Contato emergencial.
- **Ficha individual do ponto** (impressa em PVC ou laminada, A5) afixada
  internamente na casinha/abrigo:
  - ID do ponto (P-α-01 etc.).
  - Voluntário responsável.
  - Última manutenção.
  - Observações livres.

### 3.3 Exemplos consolidados

- **Modelo de placa de feeding station** — Alley Cat Allies tem template em PDF:
  https://www.alleycat.org/community-cat-care/
- **QR code para projeto científico em campo** — boas práticas da iNaturalist e
  Movebank usam QR para colaboradores casuais:
  https://www.inaturalist.org/
- **Sinalização de monitoramento em pesquisa com câmera** — modelo seguido em
  estudos de fauna em parques urbanos (ver Cove 2022 metodologia,
  cf. supplementary).

### 3.4 Considerações de LGPD

Câmeras em espaço público de campus podem capturar incidentalmente pessoas.
Mesmo que o foco seja fauna, é recomendado:

- Declarar finalidade publicamente (placa + QR).
- Armar pipeline para descartar/anonimizar bounding boxes não-felinos.
- Definir guardião dos dados e prazo de retenção.

> **Item a incorporar em B5** como parte do plano de implementação ética e em
> A2.0 como RNF (não-funcional) de privacidade.

---

## 3.5 Câmeras IP sem PIR (decisão transversal, 12/maio/2026)

**Observação do orientando**: embora o cenário ideal escolhido em B2 Parte 1 seja
câmeras com **PIR + confirmador software** (estilo WiseEye), o projeto deve **levar
em consideração** que parte do hardware disponível ou doado pode ser composto por
**IP cameras genéricas** (modelos de segurança residencial, Wi-Fi, sem PIR
dedicado, geralmente streaming contínuo RTSP a 15–25 FPS).

**Por que isso importa para o projeto**:

1. **Restrição realista de hardware**. A AEX Gatosdoc2 e a USP não têm orçamento
   garantido para 10 trail cameras de alto trigger speed. É plausível que parte
   dos pontos use câmeras herdadas (sobras de projetos, doações, equipamentos
   de segurança realocados) que **não possuem PIR**.
2. **Trade-off técnico relevante para um TCC de engenharia**. Operar sem PIR
   muda o pipeline em vários pontos:
   - **E0 (Aquisição)** passa a depender exclusivamente de **motion-detection
     em software** (frame differencing, MOG2, ou inferência leve a cada N
     frames). Sem PIR físico, **não há sleep mode profundo** — a câmera
     processa frames continuamente, consumindo mais energia e CPU.
   - **B3 (Trade-offs)** deve mapear isto como um **eixo de design**: PIR-first
     vs. software-first vs. híbrido.
   - **B4 (Arquitetura)** deve prever que pontos com IP camera precisam de
     **mais energia disponível** (classe α/β na matriz P) e **mais computação
     local** (Raspberry Pi 4/5 ou mini-PC ao pé da câmera).
3. **Custo de armazenamento e banda**. IP camera streaming gera bem mais dados
   brutos do que trail camera (que só dispara em eventos). Política de
   retenção precisa ser diferente — provavelmente "buffer circular de 24h em
   disco local, persistir apenas frames com detecção positiva no banco".

**Como será tratado no projeto** (decisão a registrar em B3 e B4):

- **Aquisição é um **eixo de design**, não uma escolha única**. Pelo menos
  dois perfis serão dimensionados explicitamente:
  - **Perfil A — Trail camera com PIR** (cenário ideal de B2 Parte 1):
    melhor para pontos sem energia e sem Wi-Fi (classes γ/δ na matriz P).
  - **Perfil B — IP camera sem PIR + edge compute local** (Raspberry Pi):
    melhor para pontos com energia e Wi-Fi (classes α/β), reaproveita
    hardware existente, permite quadro contínuo e potencialmente vídeo.
- O **pipeline lógico (E1–E4)** permanece **idêntico** nos dois perfis. Muda
  apenas o **front-end (E0)** e a primeira camada física.
- A **avaliação experimental em B5** incluirá **um ponto de cada perfil** para
  comparação direta de qualidade de captura, taxa de eventos perdidos e
  consumo energético.

**Implicação para a monografia (engenharia de computação)**: tratar o
problema como **espaço de configuração** — não como solução única — é um
elemento característico de projeto de engenharia. O TCC ganha rigor ao
mostrar **duas configurações funcionais** com critérios objetivos para
escolher entre elas, em vez de apenas uma recomendação categórica.

> Item a propagar:
> - **B2 Parte 1** (E0) ganha breve nota de continuidade indicando que B3 trata
>   todos os perfis.
> - **B3** introduz formalmente o eixo "PIR-first vs. software-first".
> - **B4** dimensiona os perfis com diagramas físicos distintos.
> - **B5** inclui ponto de cada perfil no piloto comparativo.
> - **B6** consolida lições aprendidas sobre quando cada perfil é preferível.

---

## 3.6 Câmeras IP genéricas OEM como Perfil E (decisão transversal, 12/maio/2026)

**Observação do orientando**: além das IP cameras ONVIF mais robustas, há categoria distinta a mapear — câmeras IP **genéricas/OEM de baixíssimo custo** (R$ 50–150) baseadas em SoCs como **Anyka AK3918EV300L**, vendidas em varejo brasileiro e internacional sob marcas brancas (V380, ICSEE, IPCAM P2P). Características: **sem PIR**, **VMD via software no firmware**, **RTSP exposto** em `/live/ch0`, gravação local em microSD, podem operar com ou sem Wi-Fi, e em casos limitados com bateria.

**Mapeamento aprovado** (12/maio): incluídas como **Perfil E** em B3.2, com quatro sub-variantes em pé de igualdade:
- **E1** — AC + sem Wi-Fi + SD swap presencial (cenário "barato e simples" canônico).
- **E2** — AC + Wi-Fi + RTSP pull via Pi/PC remoto.
- **E3** — Bateria + SD (viável apenas com painel solar grande).
- **E4** — Wi-Fi + bateria (pior cenário energético; descartado para piloto).

**Justificativa de engenharia**:
- **Custo absoluto mínimo** do espaço de design.
- **Disponibilidade no varejo brasileiro** (mercado de segurança residencial é grande).
- **Padrões abertos** (RTSP/ONVIF) permitem ingestão direta sem app proprietário.
- **Diferenciação analítica** entre PIR hardware (Categoria I) e VMD software (Categoria II) fortalece o framing de engenharia de computação.

**Riscos mapeados**:
- Firmware OEM fechado e potencialmente descontinuado.
- VMD do firmware geralmente fraca (FP altos sem calibração de zonas).
- Drift de relógio sem NTP configurado.
- Risco de "phone home" para servidores chineses (mitigar com VLAN isolada).
- Customização avançada via OpenIPC disponível mas não recomendada para piloto TCC.

**Documentação de referência**: o dump técnico completo de uma câmera Anyka real (kernel Linux 4.4.282, ARM926EJ-S @ 888 MHz, 64 MiB DRAM, sensor H63/SC1346, processo GW_APP, paths RTSP) está registrado em **Apêndice B3.A** de B3 Parte 1. Serve como referência para implementação e para quem comprar hardware similar.

---

## 4. Estado de incorporação no projeto

| Item desta nota | Onde será incorporado | Quando |
|---|---|---|
| Q-INF-01 a Q-INF-19 (perguntas inferenciais) | **B5 (plano de validação)** seção dedicada; **B6 (consolidação)** como roteiro de relatório | Quando escrevermos B5/B6 |
| Ficha de campo expandida | **B1.6** — atualização agora | Já nesta iteração |
| Ponto de alimentação ideal — discussão breve | **B1.6** subseção + nota em **B5** | Atualização B1 agora; aprofundar em B5 |
| Identificação dos pontos (placa/QR/etiqueta) | **B5 (plano de implementação)** + **A2.0 RNF de privacidade** | B5; nota agora em B1 |
| LGPD para imagens incidentais | **A2.0 RNF** (já existe) + **B5** detalhamento | B5 |
| IP camera ONVIF sem PIR como Perfil B | **B2 Parte 1** nota; **B3.2** formal; **B4** arquitetura; **B5** piloto | Concluído em B3 Parte 1 |
| IP cam consumer com PIR + SD como Perfil D | **B3.2** formal (4 sub-variantes D1–D4); **B4**; **B5** teste offline | Concluído em B3 Parte 1 |
| **IP cam genérica OEM (Anyka et al.) como Perfil E** | **B2 Parte 1** nota atualizada; **B3.2** formal (sub-variantes E1–E4); **Apêndice B3.A** dump técnico; **B3.6** mapeamento ponto; **B4**; **B5** teste de RTSP/drift/phone-home | **B3 Parte 1 concluído (12/maio)**; B3.6, B4, B5 próximos |

---

*Última atualização: 12/maio/2026 — incorporação de Perfil E (IP cam genérica OEM) após aprovação do orientando.*
