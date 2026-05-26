# Análise estrutural da Etapa 2 — diagnóstico e proposta de reorganização

> Este documento é **metodológico**, não conteúdo do TCC. Ele serve para:
> (a) diagnosticar a divisão atual em 3 blocos (Hardware → Software → Plano);
> (b) confrontá-la com modelos consagrados de TCC e papers análogos;
> (c) propor uma estrutura final mais defensável como engenharia.

---

## 1. Diagnóstico da divisão atual

### 1.1 O que a divisão "Hardware → Software → Plano" faz bem

- **Separa preocupações**: hardware, software e operação em camadas distintas, o que é didático.
- **É legível por gestores**: alinhada com a forma como o orientador e a banca esperam o relato (tipicamente "primeiro o quê, depois o como").
- **Permite ler em paralelo**: cada bloco é razoavelmente autocontido.

### 1.2 Onde ela é frágil para um TCC de engenharia

1. **Decisões aparecem antes do espaço de problema estar fechado.** A divisão começa em hardware, mas hardware é uma **resposta** a um conjunto de restrições (de ambiente, de software, de operação), não um ponto de partida. Apresentar 3 cenários (A/B/C) de hardware sem antes formalizar **o espaço de decisão** dá aparência de catálogo de produtos, não de raciocínio de engenharia.
2. **Não separa pesquisa de decisão.** TCCs de engenharia bem estruturados separam claramente *(i) o estudo do problema e do estado da arte*, *(ii) a análise comparativa e os trade-offs*, *(iii) a decisão e a especificação resultante*, *(iv) o plano de validação*. A nossa estrutura mistura (i) e (iii) dentro do mesmo bloco. ([USC — TCC Eng. Comp.](https://pt.slideshare.net/slideshow/orientaes-tcc-eng-comp/48382664); [TCC Solutions Group, 2026](https://tccsolutionsgroup.com.br/como-fazer-tcc-de-informatica/))
3. **O software, que é o **foco** declarado do TCC, vem **depois** do hardware.** Isso inverte a hierarquia argumentativa: o software é o que justifica a maior parte das escolhas de hardware (precisa de detalhe ótico para re-ID, latência específica, etc.). Apresentar hardware primeiro força argumentos a aparecer em duplicata ("explico aqui e justifico lá").
4. **Falta um eixo explícito de trade-offs.** Surveys recentes na área de monitoramento de fauna por edge AI tratam o problema explicitamente como otimização do **tríade acurácia × eficiência × escalabilidade** ([Martinský et al., 2025](https://ieeexplore.ieee.org/document/11280086/)) ou matriz de decisão multi-critério ([Gonzalez-Guevara et al., 2026](https://ieeexplore.ieee.org/document/11435889/)). A nossa estrutura não tem esse eixo como entidade do documento.
5. **Não considera explicitamente cenários adversos.** Sua observação sobre **ausência de Wi-Fi e tomada** é exatamente o tipo de restrição que precisa ser parte do espaço de problema, não um item adicionado de hardware. Isso muda a hierarquia: precisamos modelar o ambiente operacional **antes** de comparar hardware.
6. **O foco em "máximo com mínimo de recursos"** que você mencionou não tem lugar para ser elaborado na estrutura atual — fica diluído entre os 3 cenários. Em TCC de engenharia, esse princípio precisa virar um **critério de decisão explícito e rastreável**.

### 1.3 Resumo do diagnóstico

A divisão atual é **funcional mas não é argumentativa**. Ela descreve componentes, não justifica decisões. Para um TCC defensável como engenharia, o documento precisa ter uma cadeia "**problema → restrições → estado da arte → critérios → análise → decisão → validação**" visível.

---

## 2. O que TCCs e papers análogos fazem

### 2.1 Modelos formais consagrados (TCC de engenharia)

- **Modelo USC / orientações brasileiras** ([USC](https://pt.slideshare.net/slideshow/orientaes-tcc-eng-comp/48382664); [TCC Solutions](https://tccsolutionsgroup.com.br/como-fazer-tcc-de-informatica/)): introdução → fundamentação teórica → metodologia → desenvolvimento (arquitetura, modelagem, implementação) → testes/validação → conclusão. **Crucial**: a arquitetura e a modelagem ficam *após* a metodologia, e a metodologia define os critérios de decisão.
- **Modelo V (V-Model) da engenharia de sistemas** ([Mo et al. — Project-based V-Model](https://ira.lib.polyu.edu.hk/bitstream/10397/104588/1/Mo_Project-based_Learning_Systems.pdf); [SciTePress — V-Model MBSE](https://www.scitepress.org/Papers/2024/126397/126397.pdf); [arXiv 2308.05381 — V-Model para ML](https://arxiv.org/abs/2308.05381)): requisitos → arquitetura funcional → arquitetura lógica → arquitetura física → implementação → verificação → validação. **Crucial**: requisitos viram critérios e cada critério tem teste de verificação correspondente.
- **IMRAD adaptado para projetos práticos** ([LinkedIn — IMRAD, 2025](https://www.linkedin.com/posts/peter-munene-9ab033b8_)): Introduction → Methods → Results → And → Discussion. Em projetos de engenharia, "Methods" se desdobra em arquitetura + design space exploration; "Results" é caracterização do sistema proposto.

### 2.2 Papers análogos de monitoramento por visão computacional

- **Gonzalez-Guevara et al. (2026)** — *Platform Selection, Sensor Trade-Offs, and Architecture Performance: A Decision Framework for Operational Wildlife Monitoring* ([IEEE Access](https://ieeexplore.ieee.org/document/11435889/)): a estrutura é **revisão sistemática → trade-offs por eixo (plataforma, sensor, arquitetura) → matriz de decisão quantitativa**. É exatamente o tipo de raciocínio que falta na nossa estrutura.
- **Rahman et al. (2025)** — *A Scalable Framework for Deploying AI-Powered Wildlife Monitoring in Resource-Limited Field Environments* ([IEEE Access](https://ieeexplore.ieee.org/document/11124843/)): estrutura **problema (campo, energia, conectividade) → modelos (YOLOv8m, YOLOv10m) → plataformas (Jetson Orin Nano, RPi 5) → análise custo-desempenho-energia → recomendação ("Jetson Orin Nano @ 8W / 40 FPS é o ótimo")**. Trade-off explícito.
- **Martinský et al. (2025)** — *Lightweight DL Models for Wildlife Monitoring in IoT and Edge Applications: A Survey* ([IEEE](https://ieeexplore.ieee.org/document/11280086/)): trabalha o **trade-off triádico acurácia–eficiência–escalabilidade**. Conclusão chave: "no single model fully addresses the triad; **hybrid architectures** are the practical path".
- **Construction monitoring** ([Li et al., 2023](https://ieeexplore.ieee.org/document/10261599/)): explicita **cloud-edge collaborative computing architecture** como decisão central, antes de descer para hardware.
- **PelagiCam / WiseEye / PICT / HelioCase** (já catalogados na Etapa 1 e no Bloco H): todos publicam pelo padrão **(a) requisitos de campo → (b) limitações de soluções comerciais → (c) projeto open-source proposto → (d) validação em campo → (e) limitações**. Hardware aparece como **artefato resultante**, não como ponto de partida.

### 2.3 Padrão emergente

Todos esses trabalhos compartilham três traços:

1. **Problema operacional vem antes de tudo** — campo, energia, conectividade, restrições humanas são modelados como espaço de decisão.
2. **Trade-offs são entidade explícita** — há uma seção dedicada a comparar dimensões conflitantes (acurácia × custo × consumo × autonomia).
3. **Decisão de arquitetura é resposta argumentada à matriz de trade-off**, não escolha estética de componentes.

---

## 3. Proposta de reorganização da Etapa 2

Em vez de **Hardware → Software → Plano**, proponho a sequência **Contexto Operacional → Pipeline Conceitual → Trade-offs → Arquitetura de Referência → Plano de Validação**. São 5 blocos (B1–B5) que substituem a divisão antiga, mantendo A2.0 (Requisitos) como fundação.

### 3.1 Visão geral da estrutura proposta

| # | Bloco | O que entrega | Função argumentativa | Profundidade |
|---|---|---|---|---|
| **A2.0** | Requisitos do sistema | RF, RNF, RP | Fundação (pronto) | já feito |
| **B1** | Contexto operacional e modelo de ambiente | Caracterização dos 10 pontos como matriz de cenários (com/sem energia, com/sem rede, etc.) → "perfis de ponto". | Define o espaço de problema. Mostra **explicitamente** que nem todo ponto tem Wi-Fi ou tomada. | **médio** — sustenta tudo o resto |
| **B2** | Pipeline conceitual de visão computacional | Define o pipeline lógico (aquisição → detecção → classificação → re-ID → persistência) **sem fixar onde cada estágio roda**. | É a **arquitetura funcional** do sistema — independente de hardware. Apresenta os modelos candidatos (MegaDetector, YOLO, DeepFaune, MiewID, etc.) com profundidade. | **alta — foco do TCC** |
| **B3** | Análise de trade-offs (espaço de design) | Tabela de trade-offs **eixo × cenário × critério**: acurácia, latência, custo, energia, conectividade necessária, escalabilidade, qualidade óptica para re-ID. Cada modelo de software e cada classe de hardware é avaliada nas mesmas dimensões. | É o **coração da engenharia do TCC** — onde se vê o raciocínio comparativo. Aqui aparece o **princípio "máximo com mínimo"** como critério explícito (custo/benefício marginal). | **alta** |
| **B4** | Arquitetura de referência e camada física | Define a **decisão**: arquitetura proposta (em geral híbrida e adaptativa por ponto), com **perfis de nó** (não cenários A/B/C, mas perfis adaptados aos perfis de ponto de B1). Inclui a câmera modelo conceitual e o orçamento por perfil. | É a **arquitetura física/lógica resultante** — resposta argumentada a B1 + B2 + B3. Aqui o hardware aparece **como consequência**, não como ponto de partida. | **média-alta** |
| **B5** | Plano de validação e implementação | (a) Plano de testes do Felipi no PC com dados próprios e datasets públicos (validação dos modelos); (b) plano de piloto físico (instalação faseada, rotação amostral, governança de dados, privacidade); (c) cronograma e itens marcados como trabalho futuro do implementador. | É a **ponte para Etapa 3** e a defesa do TCC. Mostra como cada requisito de A2.0 será testado. | **média** |
| **B6** | Texto consolidado | Edição final, integração de notas, ABNT. | Deixar para o fim. | — |

### 3.2 Como cada bloco endereça suas preocupações

| Sua preocupação | Onde é tratada |
|---|---|
| "Discutir progressivamente, embasando software e plano" | A sequência B1 → B2 → B3 → B4 → B5 é progressiva por construção: cada bloco usa as conclusões do anterior. |
| "Máximo com mínimo de recursos" | Vira **critério explícito** em B3 (eficiência marginal: ganho de desempenho por R\$ adicional) e **regra de decisão** em B4 (escolher o perfil mais barato que satisfaça os RF/RNF de A2.0). |
| "Cenários sem Wi-Fi e sem tomada" | Vira **dimensão fundamental do modelo de ambiente** em B1 (matriz 2x2: energia × conectividade), com perfis de nó adaptados em B4. Não é "um cenário extra", é parte da estrutura. |
| "Extrair comparações e análises a partir das pesquisas" | É a **função explícita** de B3 (trade-offs) e parte de B2 (comparação de modelos). |
| "Melhores práticas de TCC e engenharia" | Estrutura alinhada ao Modelo V (requisitos→arquitetura funcional→lógica→física→validação) e ao IMRAD aplicado a projetos de engenharia. |

### 3.3 Mapeamento do que já foi produzido para a nova estrutura

| Já produzido | Reaproveitamento na nova estrutura |
|---|---|
| A2.0 — Requisitos (pronto) | Permanece como fundação. Sem mudança. |
| BlocoH_Hardware.md — 3 cenários + câmera modelo (acabei de entregar) | **Não é descartado.** Material vai para B4 (Arquitetura de referência) e parte (custos) para B3 (trade-offs), reorganizados sob a nova lógica argumentativa: os 3 cenários viram **perfis de nó respondendo a perfis de ponto**, e a câmera modelo continua na seção de hardware física. |
| Tabelas de produtos e preços (Tapo, Intelbras, RPi 5, etc.) | Aproveitadas em B3 e B4. |
| Glossário (RTSP, ONVIF, PoE, PIR, LiFePO4, etc.) | Mantido. |
| Fontes e lacunas | Mantidas, expandidas com B1 e B3. |

---

## 4. Como cada bloco será produzido (regras de profundidade)

- **B1** (curto, ~3-5 páginas equivalentes): inventário e taxonomia. Tabela dos perfis de ponto. Sem aprofundamento bibliográfico, só o necessário para fixar o espaço.
- **B2** (longo, ~10-15 páginas equivalentes): **é o miolo técnico do TCC**. Detalha modelos, justifica escolhas com Akbar 2025, Norouzzadeh 2018, MegaDetector, DeepFaune, PetFace, WildlifeReID-10k. Inclui plano de testes do Felipi no PC i7.
- **B3** (médio, ~5-7 páginas equivalentes): tabelas comparativas, matriz de decisão, princípios de design (open-set vs closed-set, edge vs cloud, etc.).
- **B4** (médio, ~5-7 páginas equivalentes): a decisão resultante. Aqui o conteúdo do Bloco H já produzido encontra seu lugar argumentativo correto, reorganizado.
- **B5** (médio, ~5 páginas equivalentes): plano de validação amarrado a A2.0.

---

## 5. Riscos e mitigação da nova estrutura

| Risco | Mitigação |
|---|---|
| Estrutura ficar abstrata demais e perder o leitor | B1 começa com inventário concreto dos 10 pontos do campus. B4 termina com perfis de nó concretos e orçamento. |
| Re-trabalho do Bloco H já produzido | Bloco H não é descartado — é **reorganizado**. O material (3 cenários, câmera modelo, preços) é reaproveitado em B3 e B4 sob a nova lógica. |
| Confusão entre arquitetura lógica (B2) e física (B4) | Convenção explícita: B2 fala de **estágios e modelos** independentes de onde rodam; B4 fala de **onde cada estágio roda** e quais componentes implementam. |
| Falta de dados reais sobre os 10 pontos | B1 começa como **template** (matriz de cenários) que o Felipi preenche com observação de campo. O documento explicita quais células dependem de input do Felipi. |

---

## 6. Conclusão e pergunta de decisão

A estrutura proposta (B1–B5 + B6) é mais **defensável como engenharia** que a divisão Hardware→Software→Plano porque:

1. Apresenta o **problema operacional antes da solução**.
2. Faz o software ser o **eixo central argumentativo**, com hardware como resposta.
3. Trata **trade-offs como entidade explícita**, alinhada com os papers de referência da área (Gonzalez-Guevara 2026; Rahman 2025; Martinský 2025).
4. Acomoda explicitamente cenários sem energia e sem rede como dimensão estrutural, não exceção.
5. Operacionaliza o princípio "máximo com mínimo" como critério rastreável.

**O Bloco H que acabei de entregar não é descartado** — é reorganizado: vira material de suporte para B4 e parcialmente B3, sob a lógica argumentativa correta.

### Decisão pedida

Você aprova a nova estrutura B1→B5 (com A2.0 como fundação)? Se sim, sigo nesta ordem:

1. **Atualizo o plano** (`_plano_etapa2.md`) e a lista de tarefas para a nova estrutura.
2. **Escrevo B1 — Contexto operacional e modelo de ambiente** (curto), incluindo a matriz energia × conectividade dos perfis de ponto e uma lista do que o Felipi precisa observar nos 10 pontos.
3. Depois B2 (pipeline e modelos — o miolo), B3 (trade-offs), B4 (arquitetura de referência reaproveitando o Bloco H já produzido) e B5 (plano de validação).

Se preferir um meio-termo (por exemplo: manter Hardware/Software/Plano mas inserir explicitamente um pré-bloco "contexto operacional" e uma seção interna de "trade-offs" no bloco software), também é viável e posso reorganizar nesse sentido.

## Fontes consultadas para esta análise

- Gonzalez-Guevara L. A., Celeita D., Cárdenas A., Montoya-Torres J. R. (2026). *Platform Selection, Sensor Trade-Offs, and Architecture Performance: A Decision Framework for Operational Wildlife Monitoring*. **IEEE Access**. [doi:10.1109/ACCESS.2026.3674725](https://ieeexplore.ieee.org/document/11435889/).
- Rahman M. A. et al. (2025). *A Scalable Framework for Deploying AI-Powered Wildlife Monitoring in Resource-Limited Field Environments*. **IEEE Access**. [doi:10.1109/ACCESS.2025.3598927](https://ieeexplore.ieee.org/document/11124843/).
- Martinský M., Papán J., Tatarka S. (2025). *Lightweight Deep Learning Models for Wildlife Monitoring in IoT and Edge Applications: A Survey*. **ICETA 2025**. [doi:10.1109/ICETA67772.2025.11280086](https://ieeexplore.ieee.org/document/11280086/).
- Li D., Tian H., Lang H., Niu Z., Zhao Q., Wen L. (2023). *Design of Computer Vision-Based Construction Progress Monitoring System*. **IHMSC 2023**. [doi:10.1109/IHMSC58761.2023.00035](https://ieeexplore.ieee.org/document/10261599/).
- Universidade de São Carlos — *Orientações TCC Engenharia de Computação*. [SlideShare](https://pt.slideshare.net/slideshow/orientaes-tcc-eng-comp/48382664).
- TCC Solutions Group (2026). *Como Fazer TCC de Informática*. [tccsolutionsgroup.com.br](https://tccsolutionsgroup.com.br/como-fazer-tcc-de-informatica/).
- Mo S. et al. *Project-based Learning of Systems Engineering V Model*. [Polytechnic University Hong Kong](https://ira.lib.polyu.edu.hk/bitstream/10397/104588/1/Mo_Project-based_Learning_Systems.pdf).
- *An Exploratory Study of V-Model in Building ML-Enabled Systems* (2023). [arXiv:2308.05381](https://arxiv.org/abs/2308.05381).
- SciTePress (2024). *On Some Artificial Intelligence Methods in the V-Model of MBSE*. [scitepress.org](https://www.scitepress.org/Papers/2024/126397/126397.pdf).
