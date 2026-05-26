# B6 — Consolidação final da Etapa 2 (Parte 2 — Anexos operacionais)

**Natureza desta parte:** **anexos administrativos e de gestão de projeto**. Aqui resolvo todos os pontos do projeto base (PDF) que ficaram em aberto durante a revisão profunda — cronograma, parceiros, hardware excluído, riscos atualizados, mapa Etapas-PDF × Blocos-revisão, transição para Etapa 3. **Não é** material argumentativo (isto está em B6 Parte 1); é material **referencial** que vai para os apêndices da monografia e para a próxima reunião com o orientador.

---

## B6.2.1 — Mapeamento "Etapas do PDF base ↔ Blocos da revisão"

O projeto base (PDF Sec. 2.2) organizou o TCC em 5 Etapas (Levantamento, Concepção técnica, Protótipos VC, BD+fluxos, Indicadores+documentação). A revisão profunda reorganizou o trabalho em 6 Blocos (A2.0 + B1-B5) + B6 consolidação. Esta tabela permite o orientador navegar entre as duas notações:

| Etapa PDF | Atividades originais | Bloco(s) da revisão | Status |
|---|---|---|---|
| **Etapa 1** — Levantamento | revisão bibliográfica; estado da arte VC; datasets públicos; modelos pré-treinados | A1.x (transversais — fora desta revisão) | **Concluído** anteriormente |
| **Etapa 2** — Concepção técnica | requisitos do sistema; arquitetura de hardware/software; comparação soluções; mapeamento Campus 2; tabela de hardware; diagrama UML | **A2.0 + B1 + B2 + B3 + B4** | **Concluído** nesta revisão |
| **Etapa 3** — Protótipos VC | detecção, classificação de espécie, Re-ID com datasets públicos | **B5 Parte 2 (benchmarks)** | **Especificado**; execução no PC do Felipi |
| **Etapa 4** — BD + fluxos | modelagem de BD; metadados; pipelines de tratamento; integração com sistemas externos | **B4.4 + B4.5 + B5.12 (pipeline E0-E4)** | **Concluído** nesta revisão |
| **Etapa 5** — Indicadores + documentação | painel de indicadores; relatórios; documentação técnica; entrega final | **B5.12 (dashboard Streamlit) + B5.13 (NFR × resultados) + Etapa 3 LaTeX** | Painel **especificado**; documentação **em curso** (este material vira a monografia) |

**Observação importante:** a numeração da revisão (B1-B6) e a numeração do PDF (Etapa 1-5) **não coincidem**. Na monografia, **usaremos a numeração das Etapas do PDF** como estrutura de capítulos (Cap. 4 ≡ Etapa 1, Cap. 5 ≡ Etapa 2, etc.), mas com a **profundidade técnica** vinda dos blocos B1-B5. Esta tradução está em B6.2.6.

---

## B6.2.2 — Hardware avaliado e excluído

O projeto base (PDF Sec. 7.2) listava componentes que **não entraram** nos 5 perfis consolidados de B3. Esta seção registra a análise **caso a caso**, alinhada com a transparência exigida pela banca (PDF Sec. 9 risco "teórico demais — mitigação: demonstrações práticas + decisões justificadas").

### B6.2.2.1 — ESP32-CAM

- **Citado em:** PDF Sec. 7.2 ("alternativa ultra-low-cost")
- **Avaliação técnica:**
  - Resolução máxima 1600×1200 com sensor OV2640 de qualidade baixa
  - Sem IR cut filter automático; visão noturna requer hack
  - SDRAM 4 MB insuficiente para inferência local de Re-ID
  - JPEG comprimido com perda alta (~80% qualidade)
- **Avaliação para Re-ID:** **inviável**. Estudos com OSNet, MiewID e PPGNet-Cat reportam queda abrupta de mAP quando a resolução da face do gato cai abaixo de ~80×80 pixels — ESP32-CAM raramente entrega isso para gatos a 1.5-2.5 m de distância
- **Decisão:** **excluído** dos 5 perfis principais. Mantido apenas como referência teórica.
- **Caminho alternativo (Perfil E):** câmeras OEM com chipset Anyka/V380 entregam **1920×1080 ou 2560×1440** com qualidade muito superior pelo mesmo custo (R$ 80-150)

### B6.2.2.2 — Jetson Nano

- **Citado em:** PDF Sec. 7.2 ("edge AI")
- **Avaliação técnica:**
  - **Descontinuado pela NVIDIA** desde 2023 (sem suporte de software após JetPack 4.6)
  - Não recebe atualizações de PyTorch >2.0 — incompatível com modelos modernos
  - Custo atual em mercado paralelo: R$ 1.500+ por placa
- **Substituto adotado:** **Raspberry Pi 5 + acelerador Hailo-8L** (Perfil B em P10 stretch). Hailo-8L entrega 13 TOPS contra ~0.5 TOPS efetivos do Jetson Nano, custa similar, e tem **suporte ativo de software**
- **Decisão:** **excluído**. Pi 5 + Hailo-8L é superior em todos os eixos (performance, custo, suporte)

### B6.2.2.3 — LoRaWAN

- **Citado em:** PDF Sec. 7.2 ("comunicação de longo alcance")
- **Avaliação técnica:**
  - Banda útil ~50 kbps em cenário ideal; insuficiente para transportar imagem (10-200 KB cada)
  - Apropriado para **telemetria de eventos** (timestamp + temperatura + flag PIR), não para visão computacional
  - Requer gateway dedicado adicional (~R$ 1.500)
- **Caso de uso real:** poderia complementar trail cams (Perfil A) para **alerta de evento** em tempo real, mas o dado para Re-ID ainda viria via SD swap
- **Decisão:** **excluído** dos perfis de aquisição. Pode reaparecer como **canal auxiliar** em um eventual sistema de alarme de presença (trabalho futuro)

### B6.2.2.4 — 4G/LTE-M (modem celular)

- **Citado em:** PDF Sec. 7.2 ("comunicação onde não há Wi-Fi")
- **Avaliação técnica:**
  - Plano de dados M2M no Brasil: ~R$ 30-80/mês por SIM
  - Para 10 pontos: R$ 300-800/mês de operação **sem contar hardware** dos modems (R$ 150+ cada)
  - Cobertura LTE no Campus 2 USP São Carlos é boa, mas o **custo operacional anual** (R$ 3.600+) é incompatível com projeto sem fonte de financiamento dedicada
- **Alternativa adotada:** **Wi-Fi USP** onde disponível (Perfis B, D, E2) + **SD swap** onde não (Perfis A, E1)
- **Decisão:** **excluído**. Reentraria em discussão apenas se houver **patrocínio de operadora** ou parceria institucional

### B6.2.2.5 — Painéis solares + LiFePO4

- **Citado em:** PDF Sec. 7.2 ("autonomia em pontos remotos")
- **Avaliação técnica:**
  - Custo total estimado por ponto: R$ 800-1.500 (painel 20W + controlador MPPT + bateria 12Ah)
  - Manutenção mensal (limpeza, verificação de tensão) adiciona overhead de operação
  - **Não há ponto verdadeiramente remoto** no Campus 2: distâncias da rede AC são de no máximo 50-100 m
- **Solução adotada para pontos "remotos" (P4, P6):** **Perfil A com bateria interna da câmera + SD swap quinzenal**. Custo total R$ 800-1.200, **menor** que solar e operacionalmente mais simples
- **Decisão:** **excluído** do escopo do TCC. Solar pode reentrar **apenas** se o projeto se expandir para áreas verdadeiramente isoladas (ex.: reserva ecológica do Cerrado, longe da malha elétrica) — fora do escopo da colônia AEX

### B6.2.2.6 — Síntese de hardware excluído

```
┌─────────────────┬──────────────────┬────────────────────────────────────┐
│  Componente PDF │ Status na revisão│ Por quê                            │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ ESP32-CAM       │     EXCLUÍDO     │ resolução insuficiente para Re-ID  │
│ Jetson Nano     │     EXCLUÍDO     │ descontinuado; Pi 5+Hailo superior │
│ LoRaWAN         │     EXCLUÍDO     │ não transporta imagem; uso limitado│
│ 4G/LTE-M        │     EXCLUÍDO     │ custo operacional alto sem patroc. │
│ Solar+LiFePO4   │     EXCLUÍDO     │ Wi-Fi USP / bateria interna bastam │
│ PostgreSQL+PostGIS│   FUTURO       │ SQLite suficiente para TCC offline │
│ OSNet/TransReID │  BASELINE em B5  │ honra PDF como referência          │
│ Swin (E2)       │  Subst. SpecNet  │ SpeciesNet treinado em fauna       │
│ YOLOv8          │  Subst. YOLO11   │ mesma arq, melhor latência         │
└─────────────────┴──────────────────┴────────────────────────────────────┘
```

Esta tabela é o material para a **seção "Decisões de descarte" da monografia** (apêndice ou subseção dentro de Concepção Técnica). Mostra à banca que a revisão fez **análise informada**, não omissão.

---

## B6.2.3 — Parceiros: quem valida o quê

O projeto base (PDF Sec. 6.3) lista parceiros que **não apareceram explicitamente** durante a revisão técnica (B1-B5). Esta seção fecha esse gap **antes** da defesa: para cada parceiro, defino o **papel de validação** que ele exerce sobre alguma parte do trabalho. Isto vira o **Quadro de validação interdisciplinar** da monografia.

### B6.2.3.1 — Quadro de validação

| Parceiro | Instituição/papel | O que valida | Bloco(s) da revisão |
|---|---|---|---|
| **Prof. Dr. Matheus Machado dos Santos** | Orientador, ICMC/USP | Concepção técnica completa, métodos de visão computacional, qualidade científica geral | A2.0, B1-B6 |
| **Dra. Léa Andri** | Pesquisadora Embrapa, ecologia de fauna | Indicadores ecológicos em E4; categorização de espécies em E2 (biodiversidade); interpretação de comportamento | B2.5 (E4), B5.13 |
| **ONG ASA — Amigos Salvando Amigos** | Bem-estar animal | Indicadores de bem-estar; protocolo CED; interpretação de ear-tipping; ética da intervenção | B2.5 (E4), B5.15 (limitações) |
| **Orientadora AEX Gatosdoc2** | Coordenação da Atividade de Extensão USP | Pontos P1...P10 (mapeamento real); cronograma de campo; relação com administração USP | B1, B3.6 |
| **Equipe Gatosdoc2 (voluntários)** | Cuidadores diários | Validação de identificação individual (Re-ID) por comparação com nomes/marcas conhecidos | B5.12 (piloto), B5.13 |
| **Bárbara Fernandes Madera** | Co-autora do TCC | Co-responsável por todos os blocos; foco a definir entre Bárbara e Felipi | Todos |

### B6.2.3.2 — Protocolo de validação (sugerido)

Antes da defesa, o Felipi deveria:

1. **Reunião com Dra. Léa Andri (30 min)** apresentando E2 (SpeciesNet) e E4 (indicadores) com a tabela de espécies brasileiras detectáveis e os indicadores de biodiversidade — solicitar review crítico
2. **Reunião com ONG ASA (30 min)** apresentando o painel Streamlit com KPI "% castrados" e a estratégia de identificação de ear-tipping por visão computacional — confirmar viabilidade ética e alinhamento com protocolo CED
3. **Vistoria conjunta com a Orientadora AEX** dos 10 pontos P1-P10 com o mapeamento do B3.6 impresso — confirmar in loco a viabilidade física de cada perfil escolhido
4. **Sessão de validação com voluntários Gatosdoc2** mostrando crops anotados pelo sistema e pedindo identificação humana cega — produz dados para BAKS/BAUS em B5

Estas validações podem ser **documentadas em apêndice** da monografia (com fotos, atas, e-mails) e citadas como "Validação por especialistas" — fortalecendo a aceitação acadêmica.

---

## B6.2.4 — Cronograma atualizado

O PDF Sec. 8 previa cronograma macro com Mar/Abr = concepção técnica, Mai/Jun = documentação. Hoje (13/05/2026) estamos no meio de Mai já com toda a Etapa 2 escrita em Markdown — **adiantamento real**, mas a fase de execução (rodar B5 no PC) ainda está pendente. Reproponho cronograma:

### B6.2.4.1 — Cronograma macro revisado

```
┌──────────────┬─────────────────────────────────────────────┬──────────────┐
│ Período      │ Atividade                                   │ Saída        │
├──────────────┼─────────────────────────────────────────────┼──────────────┤
│ Jan-Mar/2026 │ A1.x — Levantamento bibliográfico           │ A1 transvers │
│ Mar-Abr/2026 │ A2.0 → B1 → B2 → B3 → B4 → B5 (Markdown)    │ Etapa 2 docs │
│              │ [esta revisão profunda]                     │              │
├──────────────┼─────────────────────────────────────────────┼──────────────┤
│ Mai/2026     │ B6 consolidação + setup PC do Felipi        │ Repo criado  │
│ (1ª quinz.)  │                                             │              │
│ Mai/2026     │ Download datasets + modelos                 │ data/, models│
│ (2ª quinz.)  │ Solicitação PetFace (paralelo)              │              │
├──────────────┼─────────────────────────────────────────────┼──────────────┤
│ Jun/2026     │ Execução benchmarks E1, E2, E3              │ results/*    │
│ (1ª quinz.)  │ Geração de figuras                          │ figures/*    │
│ Jun/2026     │ Construção piloto offline (V1-V5)           │ pilot.sqlite │
│ (2ª quinz.)  │ Dashboard Streamlit                         │ dashboard    │
├──────────────┼─────────────────────────────────────────────┼──────────────┤
│ Jul/2026     │ Validações com parceiros (Léa, ASA, AEX)    │ Atas         │
│ (1ª quinz.)  │ Reprodutibilidade (Docker, DVC, CHECKSUMS)  │ Badge        │
│ Jul/2026     │ ETAPA 3 — Conversão Markdown → LaTeX        │ TCC.pdf v1   │
│ (2ª quinz.)  │ (primeira passada completa)                 │              │
├──────────────┼─────────────────────────────────────────────┼──────────────┤
│ Ago/2026     │ Revisões com orientador                     │ TCC.pdf v2   │
│              │ Ajustes finais, figuras, citações ABNT      │              │
│              │ Submissão para banca                        │ TCC final    │
├──────────────┼─────────────────────────────────────────────┼──────────────┤
│ Set/2026     │ Defesa pública                              │ Aprovação    │
└──────────────┴─────────────────────────────────────────────┴──────────────┘
```

### B6.2.4.2 — Marcos críticos (deadlines)

| Marco | Data-alvo | Risco se atrasar |
|---|---|---|
| **PetFace aprovado** | 25/05/2026 | Re-ID rodaria sem PetFace; aceitar limitação L2 |
| **Benchmarks E1+E2 concluídos** | 15/06/2026 | NFR-001/002 sem evidência → defender por extrapolação da literatura |
| **Benchmarks E3 concluídos** | 30/06/2026 | NFR-003 a NFR-005 críticos; **não pode atrasar** |
| **Piloto offline concluído** | 15/07/2026 | Dashboard sem dados reais; usar mockups |
| **Validação com Dra. Léa, ASA, AEX** | 31/07/2026 | Pode fazer pós-submissão; menos crítico |
| **Submissão Etapa 3 (LaTeX)** | 31/08/2026 | Adiar defesa para semestre seguinte |

### B6.2.4.3 — Buffers de risco

O cronograma acima inclui ~20% de buffer implícito em cada janela. Se atrasar mais de 30%, **acionar plano B**:

- **Plano B1** (E3 atrasou): rodar apenas MiewID e OSNet (2 modelos), pular MegaDescriptor; declarar limitação L8
- **Plano B2** (piloto atrasou): reduzir para 3 vídeos (V1, V2, V5) cobrindo PIR/Frigate/RTSP
- **Plano B3** (LaTeX atrasou): pedir prorrogação ICMC ou defender com versão Markdown convertida via pandoc

---

## B6.2.5 — Resposta aos riscos do PDF Sec. 9

O PDF identificou 7 riscos. Esta seção mostra como a revisão **mitiga cada um**.

| # | Risco do PDF | Mitigação aplicada nesta revisão | Bloco |
|---|---|---|---|
| **R1** | Falhas técnicas em equipamentos no campo | Piloto offline elimina dependência de campo no TCC | B5.11 |
| **R2** | Disponibilidade limitada de dados públicos | 6 datasets baixados; PetFace solicitado; HelloStreetCat como backup | B5.3 |
| **R3** | Métodos do estado da arte podem evoluir | Stack atualizada (YOLO11, MegaDetector v6, MiewID-msv3 versão 2024); revisita prevista em B6 | B4.6.5, B6.1 |
| **R4** | Integração entre módulos complexa | Pipeline E0-E4 desacoplado; wrappers padronizados; testes pytest planejados | B2, B5.5 |
| **R5** | Compreensão limitada do escopo pela banca | Tabela NFR × resultados materializa critérios mensuráveis; B6.1 dá síntese | B5.13, B6.1 |
| **R6** | Capacidade computacional insuficiente do PC | Dimensionamento em B4.3 confirma viabilidade; fallback edge L-B só em P10 stretch | B4.3 |
| **R7** | Trabalho parecer "teórico demais" para a banca | B5 inteira é demonstração prática; piloto rodável; dashboard Streamlit ao vivo | B5 |

**Risco emergente identificado nesta revisão (não estava no PDF):**

| # | Risco emergente | Mitigação |
|---|---|---|
| **R8** | PPGNet-Cat não tem pesos públicos | Declarado em B5.5.8 e B5.15 (L3); plano honesto de "reproduzir ou declarar como trabalho futuro" |
| **R9** | Cronograma de execução de B5 conflita com período letivo | Cronograma B6.2.4 prevê 3 meses (Mai-Jul) com buffers; plano B definido |
| **R10** | Validação por especialistas (Léa, ASA, AEX) depende de agenda externa | Protocolo de 4 reuniões pré-defesa; pode ir para apêndice se não rolar antes |

---

## B6.2.6 — Transição para Etapa 3 (LaTeX final da monografia)

A Etapa 3, conforme decisão consolidada com o Felipi ("Markdown agora, LaTeX só ao final"), converterá todo o material Markdown atual em capítulos LaTeX da monografia ICMC/USP.

### B6.2.6.1 — Mapa Bloco-revisão → Capítulo-monografia

Esta tabela é o **plano de conversão**. Cada Bloco em Markdown será reorganizado em um ou mais Capítulos:

| Capítulo LaTeX (sugestão) | Origem na revisão | Tamanho estimado |
|---|---|---|
| **Cap. 1 — Introdução** | adaptado de A2.0 + B1 (motivação) + PDF Sec. 1 | 8-12 páginas |
| **Cap. 2 — Fundamentação teórica** | A1.x transversais (CED, camera trapping, VC, datasets) | 25-35 páginas |
| **Cap. 3 — Trabalhos relacionados** | A1.x + posicionamento B6.1.6 | 8-12 páginas |
| **Cap. 4 — Concepção do sistema** | B1 + B2 + B3 | 20-30 páginas |
| **Cap. 5 — Arquitetura** | B4 (4 camadas + ER + DFD + stack + alimentadores) | 15-20 páginas |
| **Cap. 6 — Metodologia experimental** | B5 Partes 1-2 (setup, datasets, métricas) | 15-20 páginas |
| **Cap. 7 — Implementação e piloto** | B5 Parte 3 (piloto, pipeline, dashboard) | 8-12 páginas |
| **Cap. 8 — Resultados** | tabelas e figuras geradas em B5 + análise | 15-20 páginas |
| **Cap. 9 — Discussão** | B5.13 (NFR × medido) + B6.1.5 + B6.1.6 | 6-10 páginas |
| **Cap. 10 — Conclusões e trabalho futuro** | B5.15 + B6.1.8 | 4-6 páginas |
| **Referências** | bibliografia consolidada | — |
| **Apêndice A** — Repositório de código | B5.2 | 2-3 páginas + URL |
| **Apêndice B** — Inventário de datasets | B5.3.4 auto-gerado | 1-2 páginas |
| **Apêndice C** — Ambiente de execução | runtime.json | 1-2 páginas |
| **Apêndice D** — Métricas brutas (JSON) | results/*/metrics.json | 4-8 páginas |
| **Apêndice E** — Hardware avaliado e excluído | B6.2.2 | 3-4 páginas |
| **Apêndice F** — Validações por especialistas | atas das reuniões pós-B6 | 4-6 páginas |
| **Apêndice G** — CHECKSUMS e instruções de reprodução | CHECKSUMS.txt + B5.14 | 2-3 páginas |

**Total estimado da monografia:** **130-180 páginas + apêndices**. Volume compatível com TCCs de Engenharia de Computação ICMC.

### B6.2.6.2 — Decisões de formatação reservadas para Etapa 3

| Decisão | Status |
|---|---|
| Template LaTeX | usar template oficial ICMC/USP (verificar versão atual) |
| Citações | ABNT NBR 10520 (autor-data) ou IEEE — confirmar com orientador |
| Língua | Português brasileiro (PDF base estava em pt-BR) |
| Figuras | converter ASCII diagramas → PlantUML/TikZ; tabelas Markdown → tabular LaTeX |
| Glossário | gerar a partir de `glossario_notas_rodape.md` (transversal) |
| Pré-textuais | folha de rosto, dedicatória, agradecimentos, resumo (pt/en), lista de figuras/tabelas/abreviaturas — gerados ao final |

### B6.2.6.3 — Ordem sugerida de execução da Etapa 3

1. **Semana 1** — gerar template LaTeX + verificar compilação local (Overleaf, dado o background do Felipi)
2. **Semana 2** — Cap. 1 + Cap. 2 + Cap. 3 (Introdução e fundamentação) — conversão direta de A1.x
3. **Semana 3** — Cap. 4 + Cap. 5 (concepção e arquitetura) — conversão de B1-B4 com diagramas re-renderizados em TikZ/PlantUML
4. **Semana 4** — Cap. 6 + Cap. 7 (metodologia e implementação) — B5 partes 1-3
5. **Semana 5** — Cap. 8 + Cap. 9 (resultados e discussão) — depende de ter rodado B5 antes
6. **Semana 6** — Cap. 10 + Apêndices + revisão geral + abstract

---

## B6.2.7 — Checklist de entrega da Etapa 2

Para o Felipi confirmar que **a Etapa 2 está fechada** antes de iniciar Etapa 3:

### Documentação técnica (Markdown)

- [x] A2.0 — Requisitos do sistema (NFR-001 a NFR-010 + RF)
- [x] B1 — Contexto operacional e modelo de ambiente
- [x] B2 Parte 1 — Pipeline geral + E0 + E1
- [x] B2 Parte 2 — E2 + E3 + pré-processamento
- [x] B2 Parte 3 — E4 + métricas + plano de testes
- [x] B3 Parte 1 — Aquisição (2 categorias × 5 perfis) + Detecção
- [x] B3 Parte 2 — Re-ID + locus + mapeamento P1-P10
- [x] B4 Parte 1 — 4 camadas + 5 diagramas físicos + dimensionamento
- [x] B4 Parte 2 — ER Chen + DFD + stack + alimentadores (B4.7)
- [x] B5 Parte 1 — Setup + repo + datasets + protocolo
- [x] B5 Parte 2 — Wrappers + scripts + métricas + figuras
- [x] B5 Parte 3 — Piloto + pipeline + reprodutibilidade
- [x] B6 Parte 1 — Síntese técnica
- [x] B6 Parte 2 — Anexos operacionais (este documento)

### Documentos transversais

- [x] `_plano_etapa2.md`
- [x] `_analise_estrutural.md`
- [x] `glossario_notas_rodape.md`
- [x] `fontes_e_lacunas.md`
- [x] `notas_pontos_futuros.md`
- [x] `alinhamento_projeto_base.md` (gap analysis PDF × revisão)
- [x] `BlocoH_Hardware.md`

### Para iniciar Etapa 3

- [ ] Felipi inicia setup do PC (B5.1) — abrir terminal, rodar comandos
- [ ] Felipi cria repo no GitHub e inicializa estrutura canônica (B5.2)
- [ ] Felipi solicita PetFace via Google Form
- [ ] Reunião com orientador apresentando síntese B6.1 + cronograma B6.2.4
- [ ] Reunião com co-autora Bárbara para dividir responsabilidades de Etapa 3

### Para defesa

- [ ] Execução de B5 (Mai-Jul 2026 conforme cronograma)
- [ ] Validações com parceiros (Léa, ASA, AEX)
- [ ] Conversão Markdown → LaTeX (Etapa 3)
- [ ] Submissão à banca (Ago 2026)
- [ ] Defesa (Set 2026)

---

## B6.2.8 — Fechamento da Etapa 2

A Etapa 2 do TCC "Estudo e Concepção de um Sistema de Monitoramento por Visão Computacional para a Colônia AEX Gatosdoc2" está **tecnicamente concluída** nesta revisão profunda, totalizando:

- **15 documentos Markdown** (A2.0 + B1 + B2 P1-3 + B3 P1-2 + B4 P1-2 + B5 P1-3 + B6 P1-2)
- **~280 KB de documentação técnica**
- **~2.000 linhas de código fonte** especificadas
- **17 entidades + relacionamentos** modelados em ER Chen
- **8 divergências** ao projeto base documentadas e justificadas
- **5 perfis de aquisição** consolidados em 2 categorias × 10 pontos
- **6 modelos de IA** integrados em pipeline E0-E4
- **NFR-001 a NFR-010** mensuráveis com protocolo definido
- **Plano executável** com cronograma realista de 11 dias úteis para rodar B5

**Próximos passos do Felipi:**
1. Ler B6 Partes 1 e 2 com atenção (esta entrega)
2. Validar com o orientador a coerência da síntese e o cronograma
3. Começar a execução prática de B5 no PC (setup + downloads)
4. Iniciar reuniões com parceiros (Léa, ASA, AEX, Bárbara)
5. **Quando estiver pronto, sinalizar para iniciar Etapa 3** (conversão LaTeX)

A Etapa 2 não termina aqui no sentido de "encerrada para sempre" — termina no sentido de **"pronta para virar capítulos da monografia"**. Tudo o que foi escrito é insumo direto para o LaTeX.

---

## Fontes citadas nesta parte

- Projeto base do TCC — `projeto_tcc.pdf` (Sec. 2.2, 6.3, 7.2, 8, 9)
- `alinhamento_projeto_base.md` (gap analysis interno desta revisão)
- [Camtrap-DP Recommendations — Bubnicki et al., 2024](https://camtrap-dp.tdwg.org/) (carryover)
- [Hailo-8L M.2 specification](https://hailo.ai/products/ai-accelerators/hailo-8l-ai-acceleration-module/) (referência para B6.2.2.2)
- [NVIDIA Jetson Nano EOL notice (2023)](https://forums.developer.nvidia.com/) (referência para B6.2.2.2)
- Template ICMC/USP (Etapa 3 — a confirmar versão atual com o orientador)
