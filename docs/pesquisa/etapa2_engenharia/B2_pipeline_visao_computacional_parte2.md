# B2 — Pipeline conceitual de visão computacional (Parte 2)

> **Continuidade**: esta parte cobre os estágios **E2 (classificação de espécie)**, **E3 (re-identificação individual — núcleo técnico do TCC)** e o bloco transversal **E2.6 (pré-processamento, augmentation e filtros temporais)**. A Parte 1 estabeleceu o pipeline (E0–E4), detalhou aquisição (E0) e detecção (E1) e fixou a hipótese de trabalho de **MegaDetector v6 como detector primário com YOLO11n como alternativa leve**.
>
> **Lembrete metodológico**: o foco desta seção é **engenharia de software e visão computacional**. Discussões sobre saúde animal ou manejo aparecem apenas como contexto justificador, conforme diretriz do orientador.
>
> **Princípio pipeline-agnóstico (reafirmado da Parte 1).** Os estágios E2, E3 e o pré-processamento E2.6 **não sabem qual perfil de ponto** (OFF-SD, NET, AC, AC+NET) originou o quadro — recebem crops normalizados pelo pipeline de ingestão. A única diferenciação que persiste é a **modalidade** (RGB diurno vs. IR noturno mono), tratada em B2.6.5.

---

## B2.4 — Estágio E2: classificação de espécie

### B2.4.1 — Por que classificar espécie em um sistema "de gatos"?

À primeira vista, classificar espécie em um projeto cujo alvo é *Felis catus* parece redundante. Não é. O Campus 2 da USP São Carlos não é um ambiente controlado: tem **mata nativa própria e proximidade com fragmentos de Cerrado**, e por isso atrai **fauna sinantrópica e silvestre**. Conforme caracterizado em B1 v2, nos pontos de alimentação circulam cães errantes, gambás (*Didelphis albiventris*), saguis (*Callithrix penicillata* ou *C. jacchus*), quatis (*Nasua nasua*), aves de médio porte (saíras, sabiás, anus), roedores e — especialmente em pontos próximos a edifícios — **humanos** (Voluntários-AEX reabastecendo comida/água, Pesquisadores, alunos, funcionários). A própria literatura de camera-trapping é unânime ao apontar que **a fração de "falsos animais" em fototrampolins de área aberta é alta**: o MegaDetector reduz tempo de revisão em 50–99,9% justamente porque o problema dominante é separar movimento relevante de movimento irrelevante, antes de qualquer pergunta biológica ([Beery, Morris & Yang 2019](https://arxiv.org/abs/1907.06772); [AI4G ML survey](https://agentmorris.github.io/camera-trap-ml-survey/)).

O estágio **E2** cumpre, portanto, três funções distintas:

1. **Filtragem positiva** — confirmar que a detecção do estágio E1 é de fato um *gato doméstico* antes de despachar o recorte para o estágio E3 (re-identificação). Isso evita poluir as galerias de embeddings com cães, gambás, saguis, quatis ou aves erroneamente cropados como "animal".
2. **Inventário secundário de fauna não-alvo (subproduto)** — produzir uma estatística automática das **demais espécies** que visitam os pontos. Esse dado tem valor para a AEX Gatosdoc2 (entender quem mais consome a ração, justificar comedouros anti-pragas — ver B1) e para ecologia urbana, sem custo adicional: o pipeline já está rodando.
3. **Auditoria e descarte de privacidade** — humanos detectados em E1 devem ser **excluídos do fluxo de re-ID e marcados para descarte** conforme a discussão de ética em B1. A classificação humano/animal/vazio é a primeira barreira anti-LGPD.

### B2.4.2 — Candidatos a modelo de classificação

A literatura recente (2023–2025) consolidou três famílias de classificadores de espécie para camera-trap. A escolha é menos sobre acurácia bruta (todos os modelos modernos passam de 90% em condições favoráveis) e mais sobre **fit operacional** com o pipeline já decidido em E1.

**Tabela B2.4-1 — Candidatos a classificador de espécie em E2**

| Modelo | Backbone | Cobertura taxonômica | Acurácia reportada | Throughput | Adequação ao TCC |
|---|---|---|---|---|---|
| **SpeciesNet (Google)** | EfficientNetV2-M | **2.498 categorias**, treino em **65M imagens** | 99,4% encontrar animal; 83% nível espécie; **94,5% das predições de espécie corretas** | ~30K imagens/dia em laptop padrão; ~250K/dia em GPU leve | **Alta** — cobre *Felis catus* nativamente, integrado a AddaxAI e Wildlife Insights ([Google Research blog](https://research.google/blog/where-wild-things-roam-identifying-wildlife-with-speciesnet/), [Google blog corporativo](https://blog.google/company-news/outreach-and-initiatives/sustainability/speciesnet-open-source-ai-wildlife/)) |
| **DeepFaune classifier v1.3** | ViT-B baseado | 26 táxons europeus | **97% acurácia macro** em validação interna | ~5–10 imagens/s em CPU; >50/s em GPU leve | **Média** — focado em fauna europeia; categoria "domestic cat" presente, mas treinada com viés rural ([Rigoudy et al. 2023](https://www.biorxiv.org/content/10.1101/2022.03.15.484324v3.full-text)) |
| **Transfer learning customizado** (ResNet-50 ou EfficientNet-B0 sobre crops do E1) | Treinado em dataset local (gatos × cães × humanos × vazio) | 4–6 classes específicas do Campus 2 | 90% com **1.000 imagens/categoria** ([Tabak et al. workflow R, 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11638126/)) | <5 ms/imagem em CPU em modelos pequenos | **Média-alta** — máximo controle, mas custo de anotação alto |
| **Two-stage MegaDetectorV5 → classificador** | Yi-Yolo/EfficientNet | 24 mamíferos | **F1 = 96,2%** em estudo italiano ([PMC 12064792, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12064792/)) | Variável | **Alta como paradigma** — confirma a viabilidade de detector + classificador empilhados |

### B2.4.3 — Estratégia adotada conceitualmente

O TCC propõe uma **abordagem em dois níveis**, executada em ordem:

**Nível A — classificador genérico pronto (SpeciesNet)**:
- Recorte vindo de E1 é passado pelo SpeciesNet
- Saída esperada para o caso de uso: rótulo `Felis catus` com confiança \( p \ge \tau_{\text{spp}} \)
- Threshold \( \tau_{\text{spp}} \) inicial conservador: **0,7** (calibrado durante validação)
- Justificativa: SpeciesNet já contém *Felis catus* no vocabulário de 2.498 classes, foi treinado em 65M de imagens de camera-trap globais (incluindo gatos domésticos e ferais) e está disponível open-source via Wildlife Insights/AddaxAI ([SpeciesNet code release](https://github.com/google/cameratrapai)).

**Nível B — verificação binária leve** (opcional, ativada se SpeciesNet tiver baixa confiança):
- Pequeno classificador binário **gato × não-gato** treinado em dataset local (~500–1.000 crops anotados pelo Pesquisador e por Voluntários-AEX colaboradores)
- Função: desempate em casos ambíguos do Nível A, especialmente quando há perda de cor (gato preto sob IR → "tigre branco"; ver alerta documentado em [Reddit r/Feral_Cats 2025](https://www.reddit.com/r/Feral_Cats/comments/1o191pt/can_a_security_camera_make_a_black_cat_look_white/))
- Custo: tempo de anotação ~10–15h colaborativos, sem necessidade de GPU para treino (poucas centenas de imagens em backbone congelado)

### B2.4.4 — Tratamento de classes "outras"

A política de roteamento após E2 é:

1. **`Felis catus`** com \( p \ge \tau_{\text{spp}} \) → segue para **E3 (re-ID)**.
2. **`Felis catus`** com \( p < \tau_{\text{spp}} \) → vai para **fila de revisão humana** (Pesquisador e Voluntários-AEX revisores no AddaxAI); não entra na re-ID até confirmação.
3. **`Homo sapiens`** ou pessoa detectada → **descarte imediato do recorte** com retenção apenas do log de "evento humano às HH:MM no ponto Pn" (sem imagem); cumpre LGPD e ainda permite estimar tráfego humano para análise das Q-INF do Bloco B1.
4. **Outras espécies** (cão, gambá, sagui, quati, ave, roedor) → registro em tabela de "fauna acompanhante" com timestamp, ponto e bbox; descartar imagem se houver presença humana coincidente; manter se for apenas animal não-alvo.
5. **`Blank`/baixa confiança em tudo** → descartar; usar para auditoria de taxa de falsos do detector E1.

### B2.4.5 — Filtragem temporal e *active ensemble*

Camera-traps disparam em **sequências**: um único evento de movimento gera 3–10 frames próximos. [Mononen et al. 2025](https://www.mrazova.net/l/an-active-ensemble-classifier-for-detecting-animal-sequences-from-global-camera-trap-data/) propõem um **classificador ativo em ensemble** para sequências, em que a decisão final é agregada sobre todos os frames de um burst antes de ser ditada como rótulo final. Para o TCC, isso significa:

- Operar E2 em nível de **sequência** (não frame): se 7 dos 10 frames recebem rótulo `Felis catus`, o evento é gato; se 4 são gato, 3 são vazios e 3 são gambá, há ambiguidade e o evento vai para revisão humana.
- Esse agregador também resolve parcialmente o problema de gato preto sob IR (alguns frames com cor preservada vencem o voto).

### B2.4.6 — Métricas e plano de avaliação de E2

Para o TCC, E2 será avaliado em duas etapas:

1. **Avaliação retrospectiva** em um sub-conjunto anotado manualmente (~500 sequências de teste do piloto) com SpeciesNet plug-and-play, calculando precision/recall por classe e matriz de confusão. Meta: precision \( \ge 0,95 \) para `Felis catus`.
2. **Avaliação prospectiva contínua** durante o piloto: amostragem aleatória de 5% dos eventos para auditoria humana, calculando concordância (Cohen's κ) entre SpeciesNet e voluntário.

> **Q-INF-CE-1**: O SpeciesNet treinado em fauna global terá viés contra gatos domésticos brasileiros (subnutridos, com pelagem distinta de gatos europeus/americanos)? — pergunta aberta a responder no piloto.
>
> **Q-INF-CE-2**: SpeciesNet reconhece bem **saguis e quatis** (fauna neotropical do Cerrado próximo ao Campus 2)? Verificar matriz de confusão no dataset de calibração; se não, considerar fine-tune leve sobre [WildlifeReID-10k](https://arxiv.org/abs/2406.09211) ou adicionar essas classes ao classificador binário do Nível B.

---

## B2.5 — Estágio E3: re-identificação individual (núcleo do TCC)

Este é o estágio **mais profundo do trabalho** e ocupa a maior parte do esforço de engenharia. A re-identificação (re-ID) é o problema de, dado um recorte de gato anônimo, decidir **qual indivíduo da colônia ele é** — ou se é um novo indivíduo ainda não catalogado. É um problema de *matching* e busca, não de classificação fechada, e por isso requer uma abordagem fundamentalmente diferente de E1 e E2.

### B2.5.1 — Formulação do problema

**Definição operacional**: dado um recorte \( x \) de um gato vindo de E2, queremos:

1. Computar um **embedding** (vetor de características) \( \phi(x) \in \mathbb{R}^d \), tipicamente \( d = 512 \) ou \( 2.048 \).
2. Comparar \( \phi(x) \) com uma **galeria** \( \mathcal{G} = \{(\phi(g_i), \text{id}_i)\}_{i=1}^N \) de embeddings já catalogados.
3. Retornar:
   - **Identidade conhecida** \( \text{id}_k \) se a similaridade do *match* mais próximo exceder um limiar \( \tau_{\text{reid}} \).
   - **"Indivíduo novo"** caso contrário — abrir nova entrada na galeria.

**Por que não é classificação clássica?** Em classificação fechada, o número de classes é fixo e conhecido a priori. Aqui:
- O número de gatos pode crescer (chegada de novos animais, presença ocasional de gatos de fora da colônia).
- O número de gatos pode encolher (óbito, adoção, dispersão).
- Indivíduos catalogados podem mudar de aparência (ferida cicatrizando, perda de peso, condição da pelagem em diferentes estações).

Essa formulação se chama **re-ID em mundo aberto** (*open-set re-ID*), e é o cenário-padrão em re-ID de fauna selvagem. Toda decisão arquitetural de B2.5 deriva dessa restrição.

### B2.5.2 — Closed-set vs. open-set: por que open-set é obrigatório

| Cenário | Closed-set | Open-set |
|---|---|---|
| Conjunto de identidades | Fixo, conhecido a priori | Variável; pode ter "desconhecido" |
| Saída do modelo | Distribuição de probabilidade sobre N classes (softmax) | Similaridade contínua sobre galeria + threshold de rejeição |
| Funções de perda no treino | Cross-entropy | **Triplet loss**, **ArcFace**, **CosFace** (perdas métricas) |
| Cenário típico | Reconhecimento facial em base fechada (funcionários de uma empresa) | Reconhecimento facial em grande escala (busca de pessoa em base aberta), **biometria de fauna selvagem** |
| Aplicabilidade ao TCC | **Não aplicável** — não conhecemos o conjunto exato de gatos a priori | **Aplicável** — é o que faremos |

A diferença prática é enorme: em closed-set, errar é "atribuir o gato A à classe B". Em open-set, errar inclui também **atribuir um gato novo a um indivíduo conhecido** (falso match) ou **falhar em reconhecer um indivíduo conhecido** (falso "novo"). As métricas serão diferentes (próxima sub-seção).

### B2.5.3 — Métricas de avaliação em re-ID open-set

A literatura de re-ID animal converge em três métricas-chave, todas adotadas no AnimalCLEF 2025 ([AnimalCLEF 2025 overview](https://ceur-ws.org/Vol-4038/paper_231.pdf); [imageclef.org/AnimalCLEF2025](https://www.imageclef.org/AnimalCLEF2025)):

- **Rank-1 / Top-k accuracy**: probabilidade de que o *match* correto esteja entre os k vizinhos mais próximos. Rank-1 = 0,90 significa que em 90% dos casos o gato certo é o mais parecido na galeria.
- **mAP (mean Average Precision)**: precisão média ao recuperar todas as imagens do mesmo indivíduo da galeria. Robusta a múltiplas imagens por gato.
- **BAKS / BAUS**:
  - **BAKS** (Balanced Accuracy on Known Samples) — acurácia em recuperar a identidade correta quando a consulta é de fato um gato já catalogado.
  - **BAUS** (Balanced Accuracy on Unknown Samples) — acurácia em **rejeitar corretamente** uma consulta de gato novo ainda não catalogado, classificando-o como "novo".
  - Métricas complementares: um modelo pode ter BAKS alto e BAUS baixo (memoriza tudo, nunca rejeita) ou vice-versa.

Para o TCC, a métrica composite recomendada será a **média harmônica de BAKS e BAUS**, pois penaliza desbalanceamento — exatamente o que queremos em uma colônia onde **novos gatos podem chegar a qualquer momento**.

### B2.5.4 — Foundation models de re-ID animal (estado da arte 2024–2025)

A virada metodológica que torna este TCC viável aconteceu em 2023–2024: emergiram **foundation models** de re-ID animal, pré-treinados em dezenas de milhares de indivíduos de dezenas de espécies, que podem ser usados **sem fine-tuning** (zero-shot) ou com fine-tuning leve para um caso novo. Tabela comparativa:

**Tabela B2.5-1 — Foundation models de re-ID animal**

| Modelo | Backbone | Treino | Tamanho do treino | Acurácia reportada | Disponibilidade | Status para o TCC |
|---|---|---|---|---|---|---|
| **MiewID multispecies (Wild Me, dez 2024)** | EfficientNetV2 + ArcFace head | 59 datasets, **49 espécies**, **37.138 indivíduos**, **225.374 anotações** | 225K anotações | **+12,5% Top-1 vs. single-species**; superou MegaDescriptor na maioria das tarefas ([Wild Me et al. 2024, arXiv:2412.05602](https://arxiv.org/html/2412.05602v1)) | Open-source via [Wildbook MiewID docs](https://wildbook.docs.wildme.org/introduction/image-analysis-pipeline.html); HuggingFace | **Recomendação primária** |
| **MegaDescriptor-B-224** | **Swin-B Transformer**, 109,1M params, input 224×224 | WildlifeDatasets toolkit, 31 espécies | 31 datasets | Baseline ampla; superado pelo MiewID multispecies | [HuggingFace BVRA/MegaDescriptor-B-224](https://huggingface.co/BVRA/MegaDescriptor-B-224); paper [Čermák et al. WACV 2024](https://ieeexplore.ieee.org/document/10483925/) | **Baseline secundário** (comparação obrigatória) |
| **DINOv2 (Meta)** | ViT-S/B/L self-supervised | LVD-142M (142M imagens gerais) | Imagens web não-rotuladas | Backbone genérico; competitivo no AnimalCLEF 2025 quando combinado com MegaDescriptor head ([DS@GT AnimalCLEF 2025, arXiv:2509.12353](https://arxiv.org/abs/2509.12353)) | Open-source Meta AI | **Baseline experimental** opcional |
| **PetFace-trained models** | ResNet-50, ViT | **PetFace dataset**: 257.484 indivíduos, **13 famílias animais**, 319 raças (inclui gatos domésticos) | 257K indivíduos | Modelos baseline disponibilizados pelos autores; foco em *pets* | [Shinoda et al. 2024, arXiv:2407.13555](https://arxiv.org/abs/2407.13555); [PetFace project page](https://dahlian00.github.io/PetFacePage/) | **Fine-tuning candidato** — único grande dataset com gatos domésticos |

### B2.5.5 — Trabalho específico em gatos: PPGNet-Cat

O trabalho mais próximo do escopo do TCC é o de [Akbar & Rees Fleming 2025](https://arxiv.org/abs/2507.11575), publicado no *Journal of Imaging* 11(8):274 sob o título "*MiewID body parts approach for feral cat re-identification*". É o primeiro paper a aplicar **explicitamente uma estratégia MiewID com body parts a gatos ferais**:

- **Arquitetura**: adapta o **PPGNet** (Part-Pose Guided Network), originalmente desenvolvido para re-ID de tigres do Amur, ao caso de gatos ferais. Modelo:
  - Detector de partes do corpo (cabeça, tronco, padrão lateral, cauda) acoplado.
  - Branches específicos por parte, com agregação de embeddings ponderada por confiança da parte.
  - Loss: **ArcFace** (additive angular margin) no head final.
- **Dataset**: gatos ferais de colônias geridas (manejadas, similares ao caso do Campus 2 USP).
- **Resultados**:
  - **mAP = 0,86**
  - **Rank-1 accuracy = 0,95**
  - Robustez a variação de pose e iluminação.
- **Implicação direta para o TCC**: serve como **âncora metodológica e benchmark**. A meta de qualidade do sistema em condições de validação será *aproximar-se de mAP ≥ 0,75 / Rank-1 ≥ 0,85* — abaixo de Akbar 2025 porque o dataset deles é melhor curado, mas no mesmo regime.

### B2.5.6 — Estratégia de re-ID adotada para o TCC

A decisão arquitetural, considerando o budget de hardware (**[PLACEHOLDER-HARDWARE-NOTEBOOK]** — notebook do Pesquisador, especificações exatas a confirmar; classe i7 ou Ryzen 7, opcionalmente com GPU dedicada simples) e cronograma (um semestre piloto):

**Decisão A — modelo primário**: **MiewID multispecies (Wild Me, dez 2024)**, usado em modo **zero-shot** inicialmente, com **fine-tuning leve** sobre dataset local (~500 imagens anotadas por indivíduo conhecido). Justificativa: é o estado da arte em foundation model multi-espécie, supera MegaDescriptor, e a equipe Wild Me disponibiliza o pipeline completo via Wildbook ([documentação Wildbook MiewID](https://wildbook.docs.wildme.org/introduction/image-analysis-pipeline.html)).

**Decisão B — baseline obrigatório**: **MegaDescriptor-B-224** rodando em paralelo no mesmo conjunto de teste. Permite reportar comparação numérica e validar a escolha de MiewID no contexto específico de gatos brasileiros — caso MegaDescriptor seja superior em *Felis catus* (improvável mas possível, pois o treino do MegaDescriptor inclui mais espécies de carnívoros pequenos), trocamos.

**Decisão C — exploração condicional**: caso o cronograma permita após validar A e B, fazer um experimento com **fine-tuning sobre PetFace** ou **adaptação de PPGNet-Cat** com body parts. Esses experimentos são **stretch goals** explicitamente listados em B5 (plano de validação).

**Decisão D — não-decisão deliberada**: o TCC **não treinará um modelo do zero**. A literatura é unânime em apontar que treinar re-ID animal do zero requer milhares de indivíduos rotulados por espécie ([Adam et al. 2024 WildlifeReID-10k, arXiv:2406.09211](https://arxiv.org/abs/2406.09211)), o que não é compatível com os recursos disponíveis. O TCC se posiciona como **estudo de aplicação e adaptação**, não de criação de modelo novo.

### B2.5.7 — Galeria, busca e thresholds

A galeria de embeddings será mantida em estrutura física simples (E4, próxima parte do B2):

- Tabela SQL `cats(id, nome, sexo_aparente, observações, primeira_aparicao, ultima_aparicao)`.
- Tabela `embeddings(id_emb, cat_id, vetor BLOB ou índice externo, qualidade_score, data_captura, ponto, evento_id)`.
- Para busca rápida, uso de **FAISS** ou **HNSW** em índice in-memory, recarregado do disco a cada inicialização.

A política de matching:

1. Embedding da consulta \( \phi(x) \) computado por MiewID.
2. Busca de **k-nearest neighbors** (k=5) na galeria por similaridade cosseno.
3. **Decisão**:
   - Se \( \text{sim}_1 \ge \tau_{\text{reid}}^{\text{hi}} \) (limiar superior, conservador) → match único confiante → atribui id.
   - Se \( \tau_{\text{reid}}^{\text{lo}} \le \text{sim}_1 < \tau_{\text{reid}}^{\text{hi}} \) → **fila de revisão humana**, voluntário decide.
   - Se \( \text{sim}_1 < \tau_{\text{reid}}^{\text{lo}} \) → candidato a **novo indivíduo**; fila de "novos" para batismo.
4. Limiares iniciais (a calibrar empiricamente): \( \tau_{\text{reid}}^{\text{hi}} = 0,75 \), \( \tau_{\text{reid}}^{\text{lo}} = 0,55 \).

### B2.5.8 — Múltiplas imagens por indivíduo (galeria multi-shot)

Cada gato terá **múltiplos embeddings na galeria** (5–15 por indivíduo idealmente). Justificativa:

- Variação de pose (gato comendo, dormindo, andando, olhando para câmera).
- Variação de iluminação (dia colorido, noite IR monocromática).
- Variação de ponto (mesma identidade em ângulos diferentes).

O *matching* opera **por consulta contra todas as imagens da galeria**, retornando a **maior similaridade entre embeddings da consulta e qualquer embedding de cada indivíduo** — pattern padrão em re-ID multi-shot.

### B2.5.9 — Estratégia ativa e curva de aprendizado da galeria

Camera-trapping tem um padrão característico: nas **primeiras semanas**, quase todos os eventos geram "novos indivíduos"; após 4–8 semanas, a curva de novos saturando indica que o catálogo está aproximadamente completo (típico de estudo de captura-recaptura — *capture-recapture* é a base estatística clássica de estimar populações em fauna). Esse comportamento é uma **assinatura biológica útil**: divergir do padrão esperado é sinal de algo errado (modelo está falhando em re-conhecer indivíduos antigos, gerando "falsos novos").

> **Nota — saturação esperada para [~50 gatos estimados] no Campus 2.** Com estimativa preliminar de **~50 indivíduos** na colônia atendida pela AEX Gatosdoc2 (a confirmar em levantamento de campo), a curva de descoberta deve saturar entre as semanas 8 e 12 do piloto. Se após 16 semanas o sistema continuar "descobrindo" indivíduos novos a taxa significativa, isso é sinal forte de problema em E3 (falsos novos) e não de uma população maior. Esta heurística fica registrada como critério de auditoria automática em B5.

[Sani, Khurana & Anand 2025](https://arxiv.org/abs/2511.06658) (*Active Learning for Animal Re-Identification with Ambiguity-Aware Sampling*) mostraram que **amostragem ativa** (priorizar para anotação humana exatamente os recortes onde o modelo está em dúvida) consegue **+10,49 ponto% mAP** sobre baseline com **apenas 0,033% das anotações totais**. O TCC adotará essa estratégia: a "fila de revisão humana" (B2.5.7) é, em essência, uma fila de active learning, e suas decisões alimentam o fine-tuning subsequente.

### B2.5.10 — Cenários de erro e mitigações

| Erro | Causa provável | Mitigação |
|---|---|---|
| Falso match (atribuir gato novo a antigo) | Gatos muito parecidos (irmãos, mesma pelagem tricolor); galeria pobre | Limiar `τ_hi` conservador; revisão humana em zona de dúvida; aumentar amostras por indivíduo |
| Falso "novo" (não reconhecer gato antigo) | Mudança visível (ferida, perda de peso, troca de pelagem); pose extrema | Múltiplos embeddings por indivíduo; reconhecer assinaturas de qualidade do recorte e descartar abaixo de threshold |
| Confusão sob IR (gato preto → "branco") | Câmera distorce cor sob IR (alerta documentado em [Reddit r/Feral_Cats 2025](https://www.reddit.com/r/Feral_Cats/comments/1o191pt/can_a_security_camera_make_a_black_cat_look_white/)) | Treinar/avaliar com mix de imagens RGB e IR; embeddings IR-aware; ou usar gates separados por modalidade |
| Drift temporal | Gato envelhece, muda pelagem ao longo de meses | Re-cadastrar embeddings a cada 3 meses; atualizar galeria com imagens recentes |
| Detector de body parts falha | Imagem oclusa, pose extrema | Fallback para embedding holístico (sem body parts) |

> **Q-INF-CE-2**: Em uma colônia de ~50 gatos com alto grau de mestiçagem (sem padrões raciais marcantes), o desempenho de re-ID baseado em pelagem se degrada relativamente a colônias de gatos com pelagem altamente distintiva (e.g., tigres do Amur, baleias com fluke únicos)? — pergunta empírica a quantificar no piloto.

### B2.5.11 — Decisão metodológica: rosto vs. corpo

PetFace ([Shinoda et al. 2024](https://arxiv.org/abs/2407.13555)) re-identifica gatos por **face**. PPGNet-Cat ([Akbar & Rees Fleming 2025](https://arxiv.org/abs/2507.11575)) usa **body parts incluindo o flanco lateral**. Qual abordagem para o TCC?

- **Camera-trap de Campus 2** captura gatos em **deslocamento lateral** majoritariamente (eles passam pelo ponto, comem, saem). A face **frontal** é capturada em fração minoritária dos frames (gato olhando para câmera).
- **Conclusão**: usar **body-part approach** (à la MiewID multispecies + PPGNet-Cat), não face-only. Face entra como **branch auxiliar** quando detectada, mas não como obrigatório.

Esta escolha tem consequência direta na fase E0 (aquisição): a câmera deve ser **posicionada lateralmente ao corredor de movimento**, não voltada para a face, e a altura deve ser tal que o flanco do gato esteja inteiramente no FOV. Esta restrição **vale igualmente para qualquer perfil de hardware** (trail camera dedicada ou IPCAM barata) e fica registrada como diretriz operacional em B1 v2 e será detalhada em B4 (arquitetura de referência).

### B2.5.12 — Plano de implementação prática

Na seção B5 (plano de validação) detalharemos passos. Resumo para fechar B2.5:

1. **Mês 1**: instalar MiewID e MegaDescriptor no notebook do Pesquisador (**[PLACEHOLDER-HARDWARE-NOTEBOOK]**); rodar zero-shot em dataset de 100 crops anotados; medir Rank-1 e mAP.
2. **Mês 2**: anotar 500 crops adicionais; fine-tuning leve do MiewID; re-avaliar.
3. **Mês 3**: deploy contínuo no piloto com galeria viva; medir drift e false-novo-rate semanalmente.
4. **Mês 4**: análise estatística final; comparação com baseline; relato.

---

## B2.6 — Pré-processamento, augmentation e filtros temporais (transversal)

Este bloco é **transversal** a E1, E2 e E3 porque todos os estágios precisam de imagens pré-processadas e de estratégias de robustez. Tratamos os três tópicos juntos para evitar repetição.

### B2.6.1 — Pré-processamento padrão

A pipeline de pré-processamento, aplicada a todo crop antes de entrar em E2 ou E3:

1. **Recorte** (já feito por E1 a partir da bounding box).
2. **Padding quadrado** com margem de 10% para preservar contexto ao redor do gato.
3. **Resize** para o tamanho de input do modelo:
   - SpeciesNet: 480×480.
   - MiewID / MegaDescriptor: 224×224 ou 384×384 dependendo da variante.
4. **Normalização**:
   - Para modelos pré-treinados em ImageNet: média `[0.485, 0.456, 0.406]`, desvio `[0.229, 0.224, 0.225]`.
   - Para MiewID: usar média/desvio do treino multispecies se disponível na docstring do modelo; senão, fallback ImageNet.
5. **Conversão de modalidade**:
   - Imagem RGB diurna: passa direto.
   - Imagem IR monocromática: replicar canal único em três canais antes da normalização ImageNet.
6. **Filtragem de qualidade**: descarte de crops com menos de 64×64 px ou com bounding-box predita pelo detector com confiança \( < 0,5 \).

### B2.6.2 — Data augmentation para fine-tuning

Para qualquer fine-tuning (E2 binário, E3 MiewID), augmentation seguirá receita padrão de re-ID animal, conforme [Čermák et al. 2024](https://ieeexplore.ieee.org/document/10483925/):

| Transformação | Probabilidade | Parâmetros |
|---|---|---|
| Horizontal flip | 0,5 | — |
| Rotação | 0,5 | ±15° |
| Color jitter | 0,5 | brilho/contraste/saturação ±0,2; *hue* ±0,05 |
| Random crop com resize | 0,3 | escala 0,8–1,0 |
| Random erasing | 0,3 | área 0,02–0,1, simula oclusões |
| **Não usar** vertical flip | — | Gatos não viram de cabeça para baixo no chão; flip vertical seria fora-de-distribuição |

Para imagens IR, dois cuidados adicionais:
- Limitar color jitter a brightness/contrast (não há cor real significativa).
- Augmentation específica para variação de exposição IR (gamma random).

### B2.6.3 — Filtros temporais ao nível de sequência

Como mencionado em B2.4.5, camera-trap opera em **bursts**. Filtros temporais aplicados:

- **Agregação por evento**: definir "evento" como uma sequência de frames com gap \( \le 30 \) s entre disparos. Todo o evento recebe uma decisão única em E2 e em E3.
- **Voto majoritário em E2**: rótulo do evento = moda dos rótulos por frame.
- **Embedding agregado em E3**: média (ou max-pooling) dos embeddings de cada frame do evento — abordagem padrão em re-ID multi-shot e adotada em [Adam et al. 2024](https://arxiv.org/abs/2406.09211).
- **Cooldown anti-duplicata**: se um mesmo `cat_id` for re-identificado no mesmo ponto dentro de uma janela de 5 minutos, contar como **um único** evento de presença (não dois). Janela calibrável.

### B2.6.4 — Drift temporal e *StreamTrap*

O recente benchmark **StreamTrap** ([Saurabh et al. 2026, arXiv:2603.20509](https://arxiv.org/html/2603.20509v1)) explicita um problema que afetará o TCC: **mudança temporal na distribuição de classes**. Em camera-trap, ao longo dos meses:
- Gatos individuais podem desaparecer ou aparecer.
- Frequência relativa por ponto pode mudar (sazonalidade, mudança de comportamento alimentar humano).
- Iluminação e vegetação mudam (estações).

StreamTrap propõe **avaliar modelos em ordem cronológica** (não shuffle aleatório), o que evidencia degradação ao longo do tempo. Adotaremos essa prática em B5 (plano de validação): split de treino/validação **temporal** (treino = primeiras semanas; validação = últimas semanas), não aleatório. Resultados que parecem altos em split aleatório frequentemente caem 5–15 pontos% em split temporal.

### B2.6.5 — Política de cor sob IR

Recapitulando a discussão de B2.5.10: imagens IR podem distorcer pelagem. Política operacional:

- Anotar a modalidade (RGB vs. IR) como atributo do embedding na galeria.
- Em **busca**, se a consulta é IR, dar peso ligeiramente maior aos embeddings IR da galeria (e vice-versa).
- Em casos de **drift bimodal extremo** (ex.: gato preto identificado por dia como preto e por noite como branco), tratar como dois "registros visuais" do mesmo `cat_id` na galeria — registro de identidade vinculado mas embeddings separados por modalidade.

### B2.6.6 — Resumo: o que sai de B2.6 para o sistema

| Saída | Forma | Usado por |
|---|---|---|
| `crop_padronizado.jpg` | 224×224 ou 384×384, normalizado | E2, E3 |
| `event_id` | Identificador único de burst (ponto+timestamp+gap) | E2, E3, E4 |
| `embedding[ev_id, frame_id]` | Vetor \( d \)-dimensional | E3, E4 |
| `embedding[ev_id]` (agregado) | Vetor agregado por evento | E3 (matching final) |
| `modalidade` | `rgb` ou `ir` | E3 (busca diferenciada) |
| `qualidade_score` | float ∈ [0,1] derivado de bbox confidence + tamanho + nitidez | E3 (filtragem de galeria), E4 (auditoria) |

---

## Encerramento da Parte 2

A Parte 2 fechou os **três estágios mais técnicos** do pipeline:

- **E2 (Classificação de espécie)** — SpeciesNet primário, verificação binária local opcional, agregação por sequência (Mononen 2025).
- **E3 (Re-identificação individual — núcleo do TCC)** — MiewID multispecies primário, MegaDescriptor baseline, PPGNet-Cat como referência ancorando metas (mAP ≥ 0,75 / Rank-1 ≥ 0,85). Galeria multi-shot, thresholds duplos com fila de revisão humana, active learning.
- **E2.6 (Pré-processamento e filtros temporais)** — Pipeline padrão, augmentation calibrada, split temporal obrigatório (StreamTrap), tratamento de modalidade RGB vs. IR.

Decisões críticas registradas:
1. Re-ID é **open-set obrigatoriamente** — métrica composite é média harmônica de BAKS/BAUS.
2. Body-part approach > face approach para o cenário de câmera lateral em ponto de alimentação.
3. Não treinar do zero; usar foundation models e fine-tuning leve.
4. Split temporal (não aleatório) no plano de validação.

**Próximo entregável (B2 Parte 3)**: estágio **E4 (Persistência e indexação)**, **métricas consolidadas do pipeline ponta-a-ponta**, e o **plano de testes específico no notebook do Pesquisador** (`[PLACEHOLDER-HARDWARE-NOTEBOOK]`) — orçamento de latência por estágio, profiling esperado, cenários de failover.

---

## Fontes citadas nesta parte

### Classificação de espécie (E2)
- **Google Research / Wildlife Insights — SpeciesNet (2025)**. *Where the wild things roam: identifying wildlife with SpeciesNet*. [research.google blog](https://research.google/blog/where-wild-things-roam-identifying-wildlife-with-speciesnet/); [Google corporate blog](https://blog.google/company-news/outreach-and-initiatives/sustainability/speciesnet-open-source-ai-wildlife/); [github.com/google/cameratrapai](https://github.com/google/cameratrapai).
- **Rigoudy N. et al. (2023)** — *The DeepFaune initiative: a collaborative effort towards camera-trap image classification*. [bioRxiv](https://www.biorxiv.org/content/10.1101/2022.03.15.484324v3.full-text).
- **Tabak M. et al. (2024)** — *Ecologist-friendly workflow for camera-trap species classification using R*. [PMC 11638126](https://pmc.ncbi.nlm.nih.gov/articles/PMC11638126/).
- **PMC 12064792 (2025)** — *Two-stage deep learning classification of mammals using MegaDetectorV5 transfer learning*. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12064792/).
- **Mononen J. et al. (2025)** — *An active ensemble classifier for detecting animal sequences from global camera-trap data*. [mrazova.net](https://www.mrazova.net/l/an-active-ensemble-classifier-for-detecting-animal-sequences-from-global-camera-trap-data/).

### Re-identificação individual (E3) — **núcleo do TCC**
- **Wild Me et al. (dez 2024)** — *MiewID multispecies: a multi-species animal re-identification model*. [arXiv:2412.05602](https://arxiv.org/html/2412.05602v1); documentação técnica em [Wildbook docs](https://wildbook.docs.wildme.org/introduction/image-analysis-pipeline.html).
- **Čermák V., Picek L., Adam L., Papafitsoros K. (2023/2024)** — *WildlifeDatasets: An open-source toolkit for animal re-identification* (introduz **MegaDescriptor**). [IEEE WACV 2024](https://ieeexplore.ieee.org/document/10483925/); modelo em [HuggingFace BVRA/MegaDescriptor-B-224](https://huggingface.co/BVRA/MegaDescriptor-B-224).
- **Akbar S., Rees Fleming H. (2025)** — *MiewID body parts approach for feral cat re-identification (PPGNet-Cat)*. [J. Imaging 11(8):274 — arXiv:2507.11575](https://arxiv.org/abs/2507.11575).
- **Shinoda R. et al. (2024)** — *PetFace: A Large-Scale Dataset and Benchmark for Animal Identification*. [arXiv:2407.13555](https://arxiv.org/abs/2407.13555); [project page](https://dahlian00.github.io/PetFacePage/).
- **Adam L. et al. (2024)** — *WildlifeReID-10k: Wildlife re-identification dataset with 10k individual animals across 33 species*. [arXiv:2406.09211](https://arxiv.org/abs/2406.09211); [CVPRW 2025 paper](https://openaccess.thecvf.com/content/CVPR2025W/FGVC/papers/Adam_WildlifeReID-10k_Wildlife_re-identification_dataset_with_10k_individual_animals_CVPRW_2025_paper.pdf).
- **AnimalCLEF 2025 organizers** — *Overview of AnimalCLEF 2025: Multi-species open-set animal re-identification*. [CEUR-WS](https://ceur-ws.org/Vol-4038/paper_231.pdf); task site [imageclef.org/AnimalCLEF2025](https://www.imageclef.org/AnimalCLEF2025).
- **DS@GT team (2025)** — *DINOv2 vs. MegaDescriptor at AnimalCLEF 2025*. [arXiv:2509.12353](https://arxiv.org/abs/2509.12353).
- **Sani D., Khurana M., Anand S. (2025)** — *Active Learning for Animal Re-Identification with Ambiguity-Aware Sampling*. [arXiv:2511.06658](https://arxiv.org/abs/2511.06658).

### Pré-processamento, augmentation e filtros temporais
- **Saurabh et al. (2026)** — *StreamTrap: A streaming benchmark for temporal class distribution shift in camera-traps*. [arXiv:2603.20509](https://arxiv.org/html/2603.20509v1).
- **GBIF Camera-Trap Best Practices Guide** — [docs.gbif.org/camera-trap-guide](https://docs.gbif.org/camera-trap-guide/).
- **Reddit r/Feral_Cats (2025)** — discussão prática sobre câmera de segurança distorcendo cor de gato preto sob IR. [reddit.com/r/Feral_Cats](https://www.reddit.com/r/Feral_Cats/comments/1o191pt/can_a_security_camera_make_a_black_cat_look_white/).
