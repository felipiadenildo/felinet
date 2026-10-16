# Sumário detalhado da monografia — Fase 3

**Documento**: TCC — Estudo e Concepção de um Sistema de Monitoramento por Visão Computacional para Colônia de Gatos no Campus 2 USP São Carlos
**Autor**: Felipi Adenildo Soares Sousa
**Orientador**: Prof. Dr. Matheus Machado dos Santos
**Defesa prevista**: Setembro/2026
**Data deste documento**: 14 de maio de 2026
**Estágio**: Draft para revisão com orientador

---

## 1. Justificativa da estrutura escolhida

A estrutura adotada combina três referências consolidadas:

- **ABNT NBR 14724:2024** — define elementos pré, textuais e pós-textuais; o trabalho deve ter introdução, desenvolvimento (livre estruturação em capítulos) e conclusão ([ABNT NBR 14724](https://tpp-uff.com.br/wp-content/uploads/2025/02/ABNT_NBR_14724_2024-1.pdf))
- **Modelo IMRaD-D adaptado** — comum em TCCs de Engenharia de Computação brasileiros (Introdução, Fundamentação, Projeto, Implementação, Resultados/Discussão, Conclusão)
- **Padrão de TCCs de sistemas de visão computacional** observado em repositórios da UFAM, UFES, UnB e Harvard SEAS, que dividem **Projeto (requisitos+arquitetura)** e **Implementação (pipeline+experimentos)** em capítulos separados quando o sistema é complexo ([Harvard SEAS Engineering Thesis Guide](https://seas.harvard.edu/media/79531/download))

**Escolha**: **7 capítulos textuais** + apêndices, alinhado com a divisão lógica dos blocos B1–B6 já revisados, mas com Bloco B6 desmembrado em síntese (Cap 7) e anexos operacionais (Apêndices).

A organização inspira-se no padrão USPSC sem ainda adotar a classe (será migrado quando o draft estabilizar).

---

## 2. Mapeamento Bloco → Capítulo

| Bloco/MD origem | Capítulo de destino | Status no draft |
|---|---|---|
| (Introdução nova, sintetizada de A1.5 + B1) | **Cap 1 — Introdução** | escrita nova |
| A1.1, A1.2, A1.5, A1.6 (literatura) | **Cap 2 — Fundamentação Teórica** | migração + costura |
| A1.3, A1.4, A2.0 (camera-trapping + CV + requisitos) | **Cap 3 — Trabalhos Correlatos e Requisitos** | migração + costura |
| B1, B3 (contexto + trade-offs) | **Cap 4 — Projeto do Sistema** | migração + costura |
| B4, BlocoH (arquitetura + hardware) | **Cap 5 — Arquitetura e Especificação Técnica** | migração + costura |
| B2 partes 1-3 (pipeline E0-E4) | **Cap 6 — Pipeline de Visão Computacional** | migração direta |
| B5 partes 1-3 (validação + piloto) | **Cap 7 — Metodologia de Validação e Plano de Experimentação** | migração + costura |
| B6 parte 1 (síntese) | **Cap 8 — Considerações Finais** | costura + escrita nova |
| B6 parte 2 (anexos operacionais) | **Apêndices A–E** | migração direta |

**Total**: 8 capítulos textuais (1 introdução + 6 desenvolvimento + 1 conclusão) — alinhado à NBR 14724 e prática consolidada.

---

## 3. Sumário detalhado com seções

### Elementos pré-textuais

| Elemento | Páginas est. | Status |
|---|---|---|
| Capa | 1 | template |
| Folha de rosto | 1 | template |
| Folha de aprovação | 1 | placeholder pós-defesa |
| Ficha catalográfica | 1 | solicitar à Biblioteca ICMC |
| Dedicatória | 1 | pendente (Felipi escreve) |
| Agradecimentos | 1–2 | pendente (Felipi escreve) |
| Epígrafe | 1 | pendente (Felipi escolhe) |
| Resumo (pt) + palavras-chave | 1 | escrita pós-draft |
| Abstract (en) + keywords | 1 | escrita pós-draft |
| Lista de figuras | 1–2 | gerada automaticamente |
| Lista de tabelas | 1 | gerada automaticamente |
| Lista de quadros | 1 | gerada automaticamente |
| Lista de abreviaturas e siglas | 2 | extrair de `glossario_notas_rodape.md` |
| Lista de símbolos | 1 | mAP, IoU, F1, etc. |
| Sumário | 2 | gerado automaticamente |

**Total pré-textuais**: ~18 páginas

---

### Cap 1 — Introdução (8–12 páginas)

**Origem**: síntese nova baseada em A1.5 (conservação, zoonoses, bem-estar) + B1.1-B1.3 (contexto operacional)

- 1.1 Contextualização: colônias urbanas de gatos no Brasil e em campi universitários
- 1.2 O caso do Campus 2 da USP São Carlos e a parceria com a AEX Gatosdoc2
- 1.3 Problemática: lacunas em monitoramento individualizado e suporte ao CED/TNR
- 1.4 Motivação tecnológica: visão computacional como apoio operacional
- 1.5 Objetivos
  - 1.5.1 Objetivo geral
  - 1.5.2 Objetivos específicos
- 1.6 Justificativa e contribuições esperadas
- 1.7 Delimitação do escopo
- 1.8 Organização do trabalho

**Figuras estimadas**: 2 (1 mapa Campus 2 placeholder; 1 esquema da problemática)
**Tabelas**: 1 (objetivos específicos vs. capítulos)

---

### Cap 2 — Fundamentação Teórica (18–25 páginas)

**Origem**: A1.1 (CED/TNR), A1.2 (evidências e críticas), A1.5 (conservação/zoonoses/bem-estar), partes de A1.6 (datasets)

- 2.1 Manejo populacional de gatos em ambientes urbanos
  - 2.1.1 Histórico do conceito Captura-Esterilização-Devolução (CED/TNR)
  - 2.1.2 CED no Brasil e marco regulatório
  - 2.1.3 Estudos longitudinais e métricas populacionais
- 2.2 Evidências e críticas ao CED/TNR
  - 2.2.1 Evidências de eficácia (Levy 2014, Spehar & Wolf)
  - 2.2.2 Críticas e contraposições (Longcore, Loss)
  - 2.2.3 Posições de organizações brasileiras
- 2.3 Conservação, zoonoses e bem-estar animal
  - 2.3.1 Impacto sobre fauna nativa
  - 2.3.2 Zoonoses relevantes (toxoplasmose, esporotricose, raiva)
  - 2.3.3 Bem-estar animal de colônias monitoradas
- 2.4 Síntese: o papel do monitoramento individualizado

**Figuras**: 3 (linha do tempo CED; mapa zoonoses; pirâmide de evidência)
**Tabelas**: 2 (estudos longitudinais; síntese de zoonoses)
**Quadros**: 1 (posições institucionais)

---

### Cap 3 — Trabalhos Correlatos e Requisitos (15–20 páginas)

**Origem**: A1.3 (camera-trapping), A1.4 (visão computacional para fauna/felinos), A1.6 (catálogo de datasets), A2.0 (requisitos)

- 3.1 Camera-trapping para fauna
  - 3.1.1 Protocolos consolidados (Lifeplan, Saving Nature, NTCA-Tiger, GBIF)
  - 3.1.2 Padrão Camtrap-DP de dados
  - 3.1.3 Adaptações para gatos urbanos
- 3.2 Visão computacional aplicada a fauna e felinos
  - 3.2.1 Detecção: MegaDetector e variantes
  - 3.2.2 Re-identificação: MiewID, MegaDescriptor
  - 3.2.3 Trabalhos específicos com gatos domésticos
- 3.3 Datasets e modelos públicos relevantes
  - 3.3.1 Datasets de fauna e felinos
  - 3.3.2 Modelos pré-treinados e licenças
- 3.4 Requisitos do sistema
  - 3.4.1 Atores e contexto operacional
  - 3.4.2 Requisitos funcionais (RF-01 a RF-14)
  - 3.4.3 Requisitos não funcionais (RNF-A a RNF-E)
  - 3.4.4 Restrições e premissas (RP-01 a RP-15)
  - 3.4.5 Perguntas de validação (Q-01 a Q-08, Q-INF-CE)

**Figuras**: 3 (taxonomia de pipelines; comparativo modelos; diagrama de atores)
**Tabelas**: 4 (datasets; modelos; RF; RNF)
**Quadros**: 2 (RP; Q-validação)

---

### Cap 4 — Projeto do Sistema (15–20 páginas)

**Origem**: B1 (contexto operacional), B3 partes 1-2 (trade-offs)

- 4.1 Contexto operacional do Campus 2
  - 4.1.1 Caracterização dos pontos de alimentação (≈10 estimados)
  - 4.1.2 População da colônia (≈50 gatos estimados) e fauna sinantrópica
  - 4.1.3 Perfis funcionais de instalação (OFF-SD, NET, AC, AC+NET)
- 4.2 Espaço de design e trade-offs
  - 4.2.1 Aquisição de imagens: câmeras com PIR vs. IPCAMs
  - 4.2.2 Detecção: modelos densos vs. modelos esparsos
  - 4.2.3 Re-identificação: locus por ponto vs. global do campus
  - 4.2.4 Mapeamento e visualização operacional
- 4.3 Decisões de projeto consolidadas
- 4.4 Riscos e mitigações de projeto

**Figuras**: 4 (mapa placeholder; perfis funcionais; trade-off detecção; locus vs. global)
**Tabelas**: 2 (perfis; trade-offs)
**Quadros**: 1 (decisões)

---

### Cap 5 — Arquitetura e Especificação Técnica (12–18 páginas)

**Origem**: B4 partes 1-2 (camadas + ER Chen + DFD + stack), BlocoH (hardware)

- 5.1 Visão de camadas
- 5.2 Diagrama de fluxo de dados (DFD)
- 5.3 Modelo de dados (ER em notação Chen)
- 5.4 Stack tecnológico
  - 5.4.1 Captura (câmeras, gateways)
  - 5.4.2 Processamento (pipeline server)
  - 5.4.3 Armazenamento (BD + objeto)
  - 5.4.4 Apresentação (dashboard operacional)
- 5.5 Especificação de hardware
  - 5.5.1 Câmeras com PIR (perfis OFF-SD, AC, AC+NET)
  - 5.5.2 IPCAMs sem PIR (cenário alternativo)
  - 5.5.3 Servidor de processamento (placeholder notebook)
  - 5.5.4 Armazenamento e nuvem institucional
- 5.6 Segurança e LGPD
- 5.7 Manutenibilidade e roadmap evolutivo

**Figuras**: 6 (camadas; DFD; ER Chen; stack; topologia; foto-kit placeholder)
**Tabelas**: 3 (entidades; estimativas hardware; volume de dados)

---

### Cap 6 — Pipeline de Visão Computacional (20–28 páginas)

**Origem**: B2 partes 1-3 (E0-E4 + métricas + testes)

- 6.1 Visão geral do pipeline e princípio pipeline-agnóstico (RF-13)
- 6.2 Etapa E0 — Ingestão
  - 6.2.1 Sub-rotina online (perfis NET/AC+NET)
  - 6.2.2 Sub-rotina offline com cartão SD (perfis OFF-SD/AC) — workflow voluntário
  - 6.2.3 Frequência de coleta adaptativa
- 6.3 Etapa E1 — Filtragem com MegaDetector
- 6.4 Etapa E2 — Pré-processamento e curadoria
  - 6.4.1 Validação de metadados
  - 6.4.2 Recortes e normalização
  - 6.4.3 Deduplicação temporal
- 6.5 Etapa E3 — Detecção fina e classificação
  - 6.5.1 Detecção de gatos (RF-14: PIR opcional)
  - 6.5.2 Detecção secundária (fauna sinantrópica)
- 6.6 Etapa E4 — Re-identificação individual
  - 6.6.1 Embeddings (MiewID, MegaDescriptor)
  - 6.6.2 Banco de embeddings (locus-aware)
  - 6.6.3 Resolução humana com ranking
- 6.7 Métricas e protocolo de avaliação
  - 6.7.1 Métricas de detecção (mAP, F1)
  - 6.7.2 Métricas de re-id (Rank-1, Rank-5, mAP@K)
  - 6.7.3 Equivalência de desempenho entre perfis (RNF-D05)
- 6.8 Plano de testes do pipeline

**Figuras**: 8 (pipeline geral; sub-rotinas E0; fluxograma E1-E4; exemplos de saída; matriz de confusão; curvas mAP)
**Tabelas**: 5 (etapas; configurações; métricas alvo; perfis vs. métricas)

---

### Cap 7 — Metodologia de Validação e Plano de Experimentação (12–18 páginas)

**Origem**: B5 partes 1-3 (setup repo, datasets, protocolo, wrappers, scripts, métricas, gráficos, piloto, reprodutibilidade)

- 7.1 Setup do ambiente de desenvolvimento
  - 7.1.1 Repositório e padronização
  - 7.1.2 Datasets de teste e treino
  - 7.1.3 Protocolo de divisão (treino/validação/teste)
- 7.2 Wrappers e scripts
  - 7.2.1 Wrappers de modelos (MegaDetector, MiewID)
  - 7.2.2 Scripts de avaliação reprodutíveis
- 7.3 Métricas e gráficos
- 7.4 Piloto operacional no Campus 2
  - 7.4.1 Seleção de pontos para piloto
  - 7.4.2 Cronograma de calibração (2–4 semanas)
  - 7.4.3 Fase de operação regular
  - 7.4.4 Manutenção sob demanda
- 7.5 Reprodutibilidade e versionamento
- 7.6 Limitações reconhecidas e tratamento de pendências

**Figuras**: 4 (cronograma piloto; estrutura repo; exemplo gráfico métricas; fluxo de reprodutibilidade)
**Tabelas**: 3 (datasets; wrappers; cronograma)

---

### Cap 8 — Considerações Finais (5–8 páginas)

**Origem**: B6 parte 1 (síntese técnica) + escrita nova

- 8.1 Síntese das contribuições
- 8.2 Atendimento aos objetivos e requisitos
- 8.3 Limitações do trabalho
- 8.4 Trabalhos futuros
  - 8.4.1 Evolução técnica (locus global, detecção de fauna)
  - 8.4.2 Evolução operacional (escala, novos campi)
- 8.5 Considerações éticas e de bem-estar
- 8.6 Encerramento

**Figuras**: 1 (roadmap evolutivo)
**Tabelas**: 1 (matriz objetivos × atendimento)

---

### Elementos pós-textuais

- **Referências bibliográficas** (8–12 páginas, ~80–120 entradas)
- **Apêndice A — Glossário** (de `glossario_notas_rodape.md`, 3–5 pág.)
- **Apêndice B — Atores e perfis operacionais detalhados** (de B6.2, 2 pág.)
- **Apêndice C — Manual do Voluntário-AEX (workflow SD)** (de B6.2, 4–6 pág.)
- **Apêndice D — Manual do Pesquisador (uso do pipeline)** (de B6.2, 4–6 pág.)
- **Apêndice E — Manual do Mantenedor-TI** (de B6.2, 3–4 pág.)
- **Apêndice F — Lista de TODOs do draft** (`\listoftodos`, 1–2 pág.)
- **Anexo A — Autorizações (placeholder)** (1 pág.)
- **Anexo B — Datasheets de hardware (placeholder)** (1–2 pág.)

**Total pós-textuais**: ~30 páginas

---

## 4. Totalizadores

| Bloco | Páginas estimadas |
|---|---|
| Pré-textuais | ~18 |
| Cap 1 — Introdução | 8–12 |
| Cap 2 — Fundamentação | 18–25 |
| Cap 3 — Correlatos + Requisitos | 15–20 |
| Cap 4 — Projeto | 15–20 |
| Cap 5 — Arquitetura | 12–18 |
| Cap 6 — Pipeline CV | 20–28 |
| Cap 7 — Validação + Piloto | 12–18 |
| Cap 8 — Considerações Finais | 5–8 |
| Pós-textuais | ~30 |
| **TOTAL** | **155–197 páginas** |

Mediana esperada: **~175 páginas**, consistente com TCCs de Engenharia de Computação ICMC que envolvem sistema de software + análise (faixa típica 80–200 páginas).

---

## 5. Inventário consolidado de figuras, tabelas e quadros

| Categoria | Quantidade |
|---|---|
| **Figuras** | 31 |
| **Tabelas** | 21 |
| **Quadros** | 4 |

Listas detalhadas geradas automaticamente pelo LaTeX (`\listoffigures`, `\listoftables`, `\listofquadro`).

---

## 6. Plano de execução do draft (Fase 5)

A geração será incremental, capítulo a capítulo, com **checkpoint entre cada capítulo** para você revisar:

1. Recriar `02_latex/` limpa (próxima ação)
2. Cap 1 — Introdução (escrita nova)
3. Cap 2 — Fundamentação (migrar A1.1, A1.2, A1.5 + costura)
4. Cap 3 — Correlatos + Requisitos (migrar A1.3, A1.4, A1.6, A2.0)
5. Cap 4 — Projeto (migrar B1, B3)
6. Cap 5 — Arquitetura (migrar B4, BlocoH)
7. Cap 6 — Pipeline (migrar B2 partes 1-3)
8. Cap 7 — Validação (migrar B5 partes 1-3)
9. Cap 8 — Considerações Finais (B6.1 + síntese nova)
10. Apêndices A-F (B6.2 + glossário + TODOs)
11. Compilação final e revisão de pendências (`\listoftodos`)
