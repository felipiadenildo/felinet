# B6 — Consolidação final da Etapa 2 (Parte 1 — Síntese técnica)

**Natureza desta parte:** **Síntese científica de fechamento da Etapa 2**. Não é apêndice administrativo (este vai para B6 Parte 2). Aqui rastreio a coerência entre A2.0 → B1 → B2 → B3 → B4 → B5 e formulo o **argumento técnico central** que sustenta o sistema. Esta parte vira diretamente o capítulo "Síntese da concepção" (ou "Conclusão da Parte II") da monografia.

**Objetivo argumentativo:** mostrar que (a) há **rastreabilidade total** entre requisitos e decisões, (b) cada decisão de design foi **informada pela literatura**, (c) o sistema é **viável** no hardware do Felipi e (d) há **evidência empírica planejada** (B5) para validar as escolhas.

---

## B6.1.1 — A tese técnica em uma sentença

> **O sistema proposto é uma pipeline de visão computacional em 5 estágios (E0–E4) sobre uma arquitetura de 4 camadas (C1–C4), instanciável em 5 perfis de aquisição (A, B, D, E1, E2) distribuídos em 2 categorias de trigger (PIR hardware e VMD software), persistindo em schema Camtrap-DP estendido, e validável de forma reproduzível em CPU comum (i7), atendendo aos requisitos funcionais e não-funcionais elicitados em A2.0 sem necessidade de instalação física durante o TCC.**

Esta sentença sintetiza o que cada bloco entregou e como eles se encadeiam. As próximas subseções desempacotam cada parte do enunciado.

---

## B6.1.2 — Rastreabilidade A2.0 → B1 → B2 → B3 → B4 → B5

A imagem mental que a banca deve formar é a de uma **cascata de decisões justificadas**. Apresento abaixo a cadeia explícita.

### Etapa A2.0 → B1: do **problema** ao **contexto operacional**

A2.0 elicitou 10 requisitos não-funcionais (NFR-001 a NFR-010) e os requisitos funcionais agrupados em RF-Detecção, RF-Espécie, RF-Reidentificação, RF-Indicadores. B1 contextualizou esses requisitos no **cenário concreto**: aproximadamente 50 gatos da colônia AEX Gatosdoc2, 10 pontos no Campus 2 USP São Carlos, sem captura física no TCC, anonimização LGPD por construção (PDF Sec. 3.2). O **modelo de ambiente** de B1 (luz natural variável, infraestrutura elétrica heterogênea, Wi-Fi USP disponível em alguns pontos) é o que **restringe** o espaço de soluções de B3.

### B1 → B2: do **contexto** ao **pipeline lógico**

Dado o contexto de B1 — múltiplos pontos, dados heterogêneos, processamento centralizado — B2 propôs um **pipeline de 5 estágios** (E0 ingestão, E1 detecção, E2 espécie, E3 reidentificação, E4 indicadores), com E2.6 pré-processamento como estágio transversal. **Decisão central:** este pipeline lógico é **invariante aos perfis de aquisição**; o que muda entre perfis é apenas **como** E0 recebe os dados (SD swap vs. RTSP vs. cloud sync), não **o quê** acontece em E1–E4. Esta separação **pipeline lógico × perfil físico** é o que viabiliza a expansão futura sem reescrever a lógica de processamento.

### B2 → B3: do **pipeline** ao **espaço de design**

Com o pipeline fixado, B3 explorou **como cada estágio pode ser instanciado**. Duas dimensões ortogonais foram analisadas:

1. **Eixo de aquisição** (origem dos dados): 2 categorias × 5 perfis (A, B, C opcional, D, E1-E4), com Categoria I usando trigger PIR hardware e Categoria II usando VMD software.
2. **Eixo de detecção/Re-ID**: cascata YOLO11n → MegaDetector v6 em E1; SpeciesNet em E2; MiewID-msv3 primário + MegaDescriptor baseline + PPGNet-Cat referência + OSNet baseline herdado em E3.

B3 não escolheu **um único caminho**; deixou **espaço de design explícito** porque a colônia tem 10 pontos com características heterogêneas. O mapeamento P1...P10 → Perfil foi feito por característica de ponto (acesso AC, distância, criticidade do ponto), não por preferência arbitrária.

### B3 → B4: do **espaço de design** à **arquitetura concreta**

B4 materializou as decisões de B3 em **4 camadas físicas** (C1 Física → C2 Lógica → C3 Dados → C4 Apresentação), com:

- **5 diagramas físicos-tipo** (um por perfil) em ASCII reproduzível
- **Dimensionamento explícito** do PC central (i7, 16-32 GB RAM, HD 4 TB + SSD 500 GB)
- **Schema de dados** Camtrap-DP 1.0.1 + 4 extensões (`individuals`, `crops`, `embeddings`, `match_history`) + 1 auxiliar (`acquisition_profile_log`) modelado em **ER notação Chen**
- **DFD nível 0 e 1** mostrando como os 5 perfis convergem em E0 e fluem por E1-E4
- **Stack canônico** Python 3.11+/PyTorch/OpenCV/SQLite/Streamlit
- **Notas sobre alimentadores** como local físico de montagem (B4.7) — atende PDF Sec. 2.2.2(c)

### B4 → B5: da **arquitetura** à **validação empírica**

B5 transformou a arquitetura em **manual operacional executável** no PC do Felipi:

- **Setup** + **estrutura canônica** do repositório (`tcc_gatosdoc2/`)
- **6 datasets públicos** baixáveis via scripts unificados
- **6 wrappers** padronizados (interface comum `DetectorBase`, `SpeciesClassifierBase`, `ReIDModelBase`)
- **3 scripts de benchmark** (`run_benchmark_e1/e2/e3.py`) com métricas formais (mAP, Rank-K, BAKS/BAUS)
- **Piloto offline** com 5 vídeos representativos (V1-V5) cobrindo os 5 perfis sem instalação física
- **Dashboard Streamlit** consumindo `pilot.sqlite`
- **Reprodutibilidade total** (Docker, DVC remote, CHECKSUMS, badge)
- **Confronto NFR × resultados** auto-gerado

### Resumo gráfico da cascata

```
   ┌────────────────────────────────────────────────────────────┐
   │  A2.0  Requisitos do sistema (NFR-001..010, RF-*)          │
   └─────────────────────────────┬──────────────────────────────┘
                                 │ contextualiza
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │  B1    Contexto operacional: 50 gatos / 10 pontos /        │
   │        Campus 2 USP / sem captura física / LGPD            │
   └─────────────────────────────┬──────────────────────────────┘
                                 │ define pipeline
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │  B2    Pipeline lógico E0→E1→E2→E3→E4 + E2.6 PrePro        │
   │        (invariante ao perfil físico)                       │
   └─────────────────────────────┬──────────────────────────────┘
                                 │ explora espaço de design
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │  B3    2 categorias × 5 perfis + cascata detecção +        │
   │        Re-ID multi-modelo + mapeamento P1...P10            │
   └─────────────────────────────┬──────────────────────────────┘
                                 │ instancia arquitetura
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │  B4    4 camadas C1..C4 + 5 diagramas físicos +            │
   │        Camtrap-DP + ER Chen + DFD + stack canônico +       │
   │        B4.7 alimentadores como mount físico                │
   └─────────────────────────────┬──────────────────────────────┘
                                 │ valida empiricamente
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │  B5    Setup + repo + 6 datasets + 6 wrappers +            │
   │        benchmarks E1/E2/E3 + piloto V1..V5 +               │
   │        dashboard + NFR × resultados + Docker/DVC           │
   └─────────────────────────────┬──────────────────────────────┘
                                 │ conclui
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │  B6    Síntese técnica (esta parte) + anexos               │
   │        operacionais (Parte 2)                              │
   └────────────────────────────────────────────────────────────┘
```

---

## B6.1.3 — Decisões consolidadas (carryover canônico)

Esta tabela é o **dicionário canônico** das decisões do projeto. Toda referência futura na monografia, em apresentações e na Etapa 3 deve usar exatamente esses termos.

### Pipeline

| Estágio | Modelo primário | Baseline / alternativa | Métrica-alvo (A2.0) |
|---|---|---|---|
| **E0** Ingestão | módulos por perfil (SD reader, RTSP puller, cloud sync) | — | latência depende do perfil |
| **E1** Detecção | **YOLO11n** (Ultralytics) | **MegaDetector v6** em cascata | mAP@0.5 ≥ 0.80 |
| **E2** Espécie | **SpeciesNet** (Google, 2.498 categorias) | — | recall `Felis catus` ≥ 0.95 |
| **E2.6** Pré-proc | crop a partir de bbox + score de qualidade | landmarks de CatFLW para enriquecimento | quality threshold = 0.3 |
| **E3** Re-ID | **MiewID-msv3** (WildMe) | **MegaDescriptor** baseline; **PPGNet-Cat** referência cat-specific; **OSNet** baseline herdado do PDF | Rank-1 ≥ 0.85, mAP ≥ 0.75, BAKS/BAUS ≥ 0.80 |
| **E4** Indicadores | SQLite + Camtrap-DP queries | + hnswlib em memória para busca k-NN | janela batch ≤ 8 h |

### Aquisição

| Categoria | Perfil | Trigger | Hardware-tipo | Modo de transferência | Pontos atribuídos |
|---|---|---|---|---|---|
| **I — PIR hardware** | **A** | PIR built-in | Bushnell/Reconyx/WiseEye DIY | SD swap | P4, P6 |
| | **D** | PIR built-in | Tapo C400 / Reolink Argus | Wi-Fi cloud sync | P2, P5, P8 |
| | **C** (opcional) | PIR + edge | PIR sensor + Pi 5 | Wi-Fi | (stretch) |
| **II — VMD software** | **B** | VMD (Frigate / motion-vectors H.264) | IP cam ONVIF + Pi 5 | Wi-Fi RTSP edge | P1, P10 |
| | **E1** | VMD no PC central | OEM genérica (Anyka/V380) AC | SD swap | P3, P9 |
| | **E2** | VMD no PC central | OEM genérica AC | RTSP pull | P7 |

### Arquitetura física e lógica

| Camada | Componente | Tecnologia |
|---|---|---|
| **C1 Física** | 10 pontos × 5 perfis | hardware definido em B3.5 |
| **C2 Lógica** | PC central i7 + Python | PyTorch 2.4+, ONNX Runtime, hnswlib |
| **C3 Dados** | SQLite + extensões | Camtrap-DP 1.0.1 + 4 Resources adicionais + ER Chen |
| **C4 Apresentação** | dashboard local | Streamlit + Plotly + Folium |

### Locus de computação

| Locus | Onde | Quando |
|---|---|---|
| **L-A Centralizado** | PC i7 | Padrão para A, D, E1, E2 |
| **L-C Híbrido** | Pi 5 (Frigate) + PC i7 | Perfil B em P1 |
| **L-B Edge total** | Pi 5 + Hailo-8L | Apenas P10 (stretch) |

---

## B6.1.4 — Por que estas escolhas, em uma página

A banca pode pedir resumidamente: "**por que MiewID e não OSNet?**", "**por que SQLite e não PostgreSQL?**", "**por que YOLO11n e não YOLOv8?**". A tabela abaixo é o **vade mecum** das justificativas — todas já desenvolvidas em B2/B3/B4/B5, aqui condensadas.

| Escolha | Alternativa rejeitada | Razão principal |
|---|---|---|
| **MiewID-msv3** como Re-ID primário | OSNet, TransReID | MiewID é **animal-agnostic** treinado em fauna; OSNet/TransReID são **pessoa-otimizados**. Mantemos OSNet como baseline para comparação numérica em B5 (honra o PDF Sec. 7.3) |
| **PPGNet-Cat** como referência cat-specific | apenas MiewID | PPGNet-Cat (Akbar 2025) é o estado da arte cat-specific (mAP 0.86 / Rank-1 0.95) — se a reprodução for viável, posiciona o trabalho na fronteira; se não, registramos como trabalho futuro |
| **SpeciesNet** em E2 | Swin Transformers genérico (PDF) | SpeciesNet vem **pré-treinado em 2.498 espécies de fauna** com curadoria Google; Swin genérico exigiria fine-tune extensivo sem ganho garantido |
| **YOLO11n + MegaDetector em cascata** em E1 | YOLOv8 puro (PDF) ou MegaDetector puro | YOLO11n é **mais rápido** que YOLOv8 com mesma arquitetura; cascata com MegaDetector dá robustez em cenário noturno/oclusão sem custo de latência média |
| **SQLite** como SGBD | PostgreSQL/MySQL (PDF) | TCC é **single-machine offline**; SQLite é portável, reprodutível e sem instalação; PostgreSQL+PostGIS planejado para evolução pós-TCC |
| **Camtrap-DP 1.0.1** como schema base | esquema próprio | Padrão TDWG endossado por GBIF, Wildlife Insights, eMammal, TRAPPER, Agouti — **interoperável** com publicação científica; extensível via Resources |
| **5 perfis em 2 categorias** | 1 perfil canônico (decisão original do Felipi) | Cenário real tem 10 pontos heterogêneos; perfil único cobriria mal os extremos (trail wildlife isolado vs. câmera AC contínua) |
| **hnswlib** para busca vetorial | varredura linear | Em ~500 gatos × 4 modelos × ~100 embeddings cada = 200k vetores; varredura linear inviável para queries do dashboard em tempo real |
| **Streamlit** para dashboard | Django/Flask | Streamlit é **alinhado ao PDF Sec. 7.5** e tem time-to-value imediato; defesa do TCC pode rodá-lo localmente sem deploy |
| **Piloto offline** (sem instalação física) | piloto em campo no Campus 2 | PDF Sec. 3.2 já estabeleceu "sem captura física"; piloto offline preserva controle sobre verdade-de-base e elimina riscos do PDF Sec. 9 (autorizações, vandalismo, clima) |
| **Python 3.11+** com **uv** | conda + Python 3.10 | uv é mais rápido e o lock-file é reproduzível em qualquer máquina; 3.11+ desbloqueia `match` statements úteis no dispatcher de perfis |

---

## B6.1.5 — Por que o sistema atende A2.0 sem instalação física

Esta é a questão **mais delicada** academicamente. A banca pode questionar: "vocês prometeram um sistema; rodaram em vídeos sintéticos?". A resposta consolidada:

**Argumento de cobertura experimental:**
1. **Datasets públicos** (B5.6-B5.8) cobrem os modelos individuais: YOLO11+MegaDetector validados em Oxford-IIIT/Crawford/CatFLW; SpeciesNet validado contra ground-truth de espécie; MiewID/MegaDescriptor/OSNet validados em PetFace/Cat Individuals/HelloStreetCat. Estes datasets são **superiores em dificuldade** ao cenário da colônia AEX (mais espécies, mais variabilidade, anotação especialista).
2. **Piloto offline** (B5.11) testa a **integração** ponta-a-ponta com 5 vídeos representativos cobrindo Perfis A, B, D, E1 e E2 — exatamente os perfis mapeados a P1-P10 em B3.6.
3. **Confronto NFR × medido** (B5.13) materializa o veredicto.

**Argumento de escopo legítimo:**
O projeto base (PDF Sec. 3.2) **definiu** que o TCC não inclui captura física. Pedir captura física iria além do escopo aprovado e violaria a delimitação documentada.

**Argumento de continuidade:**
A monografia incluirá, em Trabalho Futuro (B5.15.2 horizonte curto prazo), o plano explícito de instalação física no P1 pós-defesa, com a AEX Gatosdoc2 e Dra. Léa Andri/Embrapa como parceiros. O projeto **não morre na defesa**; tem continuidade institucional.

---

## B6.1.6 — Posicionamento na literatura

O TCC se posiciona na **interseção** de quatro linhas:

1. **Camera trapping para fauna** — endorse de Camtrap-DP (TDWG), uso de MegaDetector v6 (Microsoft AI for Earth) e SpeciesNet (Google) representa a fronteira atual de software para wildlife monitoring [Bubnicki et al., 2024](https://camtrap-dp.tdwg.org/).

2. **Re-identificação de animais individuais** — uso de MiewID-msv3 da Wild Me como primário, MegaDescriptor (BVRA) como baseline multi-espécie e PPGNet-Cat (Akbar 2025) como referência cat-specific cobre o **estado da arte 2024-2026** em Re-ID animal.

3. **Manejo CED de colônias urbanas** — o sistema apoia o programa CED de castração na AEX Gatosdoc2 fornecendo indicadores quantitativos (% castrados, ear-tipping verificado por visão computacional, ausência prolongada). Esta linha conecta o TCC com **medicina veterinária e zoonoses urbanas** sem divergir para esses campos.

4. **Engenharia de software para sistemas reprodutíveis** — uso de Camtrap-DP padronizado, DVC, MLflow, Docker, CHECKSUMS, badge "reproducible" alinha o trabalho com FAIR principles e **boas práticas modernas de engenharia de software de pesquisa** (Research Software Engineering).

A contribuição original do TCC, sintetizada em uma frase: **"primeira instância documentada (no nosso levantamento) de pipeline Camtrap-DP + Re-ID multi-modelo + multi-perfil de aquisição aplicada a colônia urbana de gatos em campus universitário brasileiro, com reprodutibilidade completa e integração planejada com programa CED institucional"**. Esta frase pode ir, levemente parafraseada, para o Resumo da monografia.

---

## B6.1.7 — Resultado esperado da Etapa 2 → o que B5 vai mostrar

A Etapa 2 termina **antes** da execução dos benchmarks (que rodam no PC do Felipi quando ele seguir o manual de B5). Por isso, B6.1 fecha com **expectativas baseadas em literatura**, não com números medidos:

| Estágio | Expectativa baseada em literatura | Fonte |
|---|---|---|
| **E1** | YOLO11n: mAP@0.5 ≈ 0.85-0.92 em fauna; MegaDetector v6: ≈ 0.90+ | Ultralytics 2024, [Microsoft CameraTraps](https://github.com/microsoft/CameraTraps) |
| **E2** | SpeciesNet: top-1 ≈ 0.97 para taxa frequentes | [Google cameratrapai](https://github.com/google/cameratrapai) |
| **E3 MiewID** | mAP ≈ 0.70-0.80, Rank-1 ≈ 0.80-0.90 em fauna | [Wild Me MiewID release notes](https://huggingface.co/conservationxlabs/miewid-msv3) |
| **E3 MegaDesc** | mAP ≈ 0.65-0.75 em multi-espécie | [BVRA paper](https://huggingface.co/BVRA/MegaDescriptor-L-384) |
| **E3 PPGNet-Cat** | mAP 0.86, Rank-1 0.95 em cat-specific | [Akbar et al., 2025](https://link.springer.com/article/10.1007/s42979-024-03397-w) |
| **E3 OSNet** | mAP ≈ 0.50-0.65 em fauna (otimizado para pessoa) | TorchReID benchmarks, expectativa abaixo dos cat-specific |

Se a medição em B5 confirmar essas faixas, **NFR-001 a NFR-005 passam** (verde). Se ficar abaixo, B5.15 entra em ação documentando limitação + trabalho futuro. Em ambos os cenários, **o TCC está cientificamente defensável**.

---

## B6.1.8 — Fechamento da síntese técnica

A Etapa 2 entrega:

- **6 blocos de revisão** (A2.0 + B1-B5) totalizando **~250 KB de documentação técnica em Markdown**
- **~2.000 linhas de código fonte** especificadas em B5 (Python 3.11)
- **8 entidades + 7 relacionamentos** modelados em ER Chen sobre Camtrap-DP 1.0.1
- **5 perfis de aquisição** mapeados a 10 pontos do Campus 2
- **6 modelos de IA** integrados (YOLO11, MegaDetector, SpeciesNet, MiewID, MegaDescriptor, OSNet) + 1 stub (PPGNet-Cat)
- **11 figuras** e **7 tabelas LaTeX** automatizadas para a monografia
- **Plano de validação** com NFR-001 a NFR-010 mensuráveis
- **Reprodutibilidade total** via Docker + DVC + CHECKSUMS
- **Cobertura completa** do escopo aprovado pelo projeto base (PDF), com **8 divergências** documentadas e justificadas no documento `alinhamento_projeto_base.md`

Com isso, **a Etapa 2 está tecnicamente fechada**. O que falta é:

1. **B6 Parte 2** — anexos operacionais e gestão de projeto (hardware excluído, parceiros, cronograma atualizado, riscos, transição para Etapa 3)
2. **Etapa 3** — conversão de todo este material Markdown em **LaTeX da monografia final**, seguindo as regras de formatação do ICMC/USP (separada conforme decisão do Felipi: "LaTeX só ao final")

---

## Fontes citadas nesta parte

- [Camtrap-DP 1.0.1 — TDWG](https://camtrap-dp.tdwg.org/) (carryover B4/B5)
- [Bubnicki et al., 2024 — Camtrap DP: an open standard for FAIR exchange of camera trap data](https://ecoevorxiv.org/repository/object/5593/download/10949/)
- [Microsoft CameraTraps — MegaDetector](https://github.com/microsoft/CameraTraps)
- [Google cameratrapai — SpeciesNet](https://github.com/google/cameratrapai)
- [Wild Me — MiewID-msv3 model card](https://huggingface.co/conservationxlabs/miewid-msv3)
- [Bohemian VRA — MegaDescriptor-L-384](https://huggingface.co/BVRA/MegaDescriptor-L-384)
- [Akbar et al., 2025 — PPGNet-Cat e métricas BAKS/BAUS](https://link.springer.com/article/10.1007/s42979-024-03397-w)
- [Wilkinson et al., 2016 — FAIR Principles for scientific data management](https://www.nature.com/articles/sdata201618)
- [Ultralytics YOLO11 documentation](https://docs.ultralytics.com/models/yolo11/)
- Projeto base do TCC — `projeto_tcc.pdf` (Sec. 2.2.2, 3.2, 7.1-7.5, 9)
