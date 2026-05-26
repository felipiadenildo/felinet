# Revisão Fase 1.1 — Reordenação narrativa e ajustes da Etapa 1

> **Documento de revisão.** Esta nota consolida as **decisões de organização** da Etapa 1 (fundamentação) após a revisão do Felipi em 13/maio/2026. Os arquivos `A1.1` a `A1.6` **mantêm seu conteúdo de pesquisa** (repositório de evidências e citações). Esta nota define **como esse conteúdo será apresentado na monografia** — ordem narrativa, profundidade, placeholders das contribuições pessoais do autor, e o que será **enxugado** no `.tex` final.

---

## 1. Fluxo narrativo aprovado (funil de afunilamento)

A apresentação na monografia segue o **funil clássico de introduções acadêmicas**, indo do problema social ao recorte técnico:

```
┌────────────────────────────────────────────────────────────────┐
│  1. PROBLEMA — animais abandonados, colônias urbanas          │
│         ↓                                                       │
│  2. MÉTODO — CED/TNR como paradigma de manejo ético           │
│         ↓                                                       │
│  3. PERSPECTIVAS — internacional, nacional, AEX/Gatosdoc2     │
│         ↓                                                       │
│  4. IMPORTÂNCIA — bem-estar, zoonoses, fauna                  │
│         ↓                                                       │
│  5. LIMITAÇÕES — gargalos operacionais do CED                 │
│         ↓                                                       │
│  6. TECNOLOGIA SEM IA — câmeras como aliada (curto)           │
│         ↓                                                       │
│  7. TECNOLOGIA COM IA — VC como ferramenta de escala          │
│         ↓                                                       │
│  8. DATASETS E MÉTRICAS — base operacional para o projeto     │
└────────────────────────────────────────────────────────────────┘
                            ↓
            ENTRADA NA ETAPA 2 (PROBLEMA E PROPOSTA)
```

---

## 2. Mapeamento ordem de arquivos → ordem narrativa

A numeração dos arquivos `A1.x` **não corresponde** à ordem em que o conteúdo aparece na monografia. Os arquivos foram criados em ordem de produção; a monografia reorganiza:

| Posição na monografia | Arquivo fonte | Tema |
|---|---|---|
| **§ 1** | A1.1 (seções 1-2) | Problema + definição CED |
| **§ 2** | A1.1 (seções 3-6) | Internacional + nacional + USP |
| **§ 3** | **[INSERIR — texto pessoal do Felipi]** | AEX/Gatosdoc2 (Felipi escreve) |
| **§ 4** | A1.5 | Importância: bem-estar + zoonoses + fauna |
| **§ 5** | A1.2 | Evidências e críticas (limitações do CED) |
| **§ 6** | A1.3 (condensado) | Tecnologia sem IA — câmeras |
| **§ 7** | A1.4 | Tecnologia com IA — visão computacional |
| **§ 8** | A1.6 | Datasets e métricas (operacional) |

---

## 3. Lacunas — partes que o Felipi vai escrever

### [PLACEHOLDER-AEX] — Parágrafo sobre AEX Gatosdoc2

**Onde entra:** § 3 da monografia, **logo após** o panorama nacional de CED no Brasil e **antes** da seção de importância (bem-estar/zoonoses/fauna).

**Função narrativa:** apresentar o **caso específico do projeto de extensão da USP São Carlos** como o **estudo de caso do TCC**, conectando o universal (Itália, EUA, marcos brasileiros) ao particular (Campus 2 — ICMC/IFSC).

**Sugestão de conteúdo (Felipi preenche com palavras próprias):**

- O que é o AEX Gatosdoc2 (programa de extensão, ano de início, vinculação à USP)
- Quem coordena (orientadora AEX)
- Estrutura do grupo (voluntários, parcerias com ONGs como ASA, Embrapa)
- Atividades realizadas (esterilizações, alimentação, vacinação, adoções)
- Números atuais aproximados (já incluídos como placeholder: ~50 gatos, ~10 pontos)
- Lacunas observadas no manejo atual (justifica o TCC: ausência de monitoramento sistemático)
- Como este TCC se insere no programa

**Extensão sugerida:** 2-4 parágrafos (~400-600 palavras no `.tex`).

### [PLACEHOLDER-HARDWARE-NOTEBOOK] — Especificações do notebook de processamento

**Onde entra:** A2.0 (Requisitos), B1 (Contexto operacional) e B4 (Arquitetura).

**Conteúdo a inserir (Felipi):**
- Modelo do notebook
- CPU (geração, núcleos, threads)
- RAM (GB, tipo)
- GPU (modelo, VRAM, suporte CUDA — se houver)
- Armazenamento (SSD GB, HDD GB)
- Sistema operacional (Linux Mint, versão)

**Atual:** os documentos têm referência genérica a "PC i7, opcional GPU dedicada simples". Será **substituído** pelo placeholder `[ESPEC_HARDWARE_NOTEBOOK]` em todos os documentos.

### [PLACEHOLDER-MAPA-PONTOS] — Mapa do Campus 2 com pontos de alimentação

**Onde entra:** B1 (Contexto operacional) e capítulo de Materiais e Métodos da monografia.

**O que o Felipi precisa fazer:**
1. **Levantamento em campo** — visitar cada ponto de alimentação atual
2. **Coordenadas GPS** — usar app de GPS (recomendo OSMAnd, GPS Test ou similar) em formato WGS84 graus decimais (ex.: -22.0087, -47.8909)
3. **Foto de cada ponto** — três fotos: frente, entorno, vegetação imediata
4. **Ficha por ponto** — preencher modelo (será criado na Fase 4 do plano)
5. **Mapa final** — duas opções:
   - **QGIS** (recomendado, código aberto) → exportar como PNG de alta resolução
   - **Google My Maps** → captura de tela ou exportação como imagem
6. **Inserir no LaTeX** — placeholder `\includegraphics[width=\linewidth]{img/cap3_metodo/mapa_pontos.pdf}`

### [PLACEHOLDER-CONTAGEM-CONFIRMADA] — Contagem final de pontos e gatos

**Estimativa atual no projeto:** 10 pontos, 50 gatos.

**Será confirmada/ajustada após:**
- Visita de campo
- Conversa com a orientadora AEX e voluntários do Gatosdoc2
- Consulta a registros de esterilização e ear-tipping existentes

**Marcação nos documentos:** `[10 pontos estimados — confirmar em campo]` e `[~50 gatos estimados — confirmar via censo Gatosdoc2]`.

---

## 4. O que será enxugado na monografia (vs. mantido nos `.md`)

Os arquivos `.md` são **repositório de pesquisa** (~150 KB de fundamentação). A monografia **não precisa absorver tudo** — segundo sua diretriz "Etapas 1, 4, 5 = grounding curto; Etapas 2 e 3 = profundidade alta".

### Recomendações de condensação para o `.tex` da Etapa 1:

| Arquivo | Tamanho atual | Páginas estimadas no `.tex` | Estratégia |
|---|---|---|---|
| A1.1 | 27 KB | **6-8 páginas** | Manter tabelas legais (importante para defesa). Reduzir variantes TNR/TNVR/RTF para parágrafo conciso. |
| A1.2 | 23 KB | **4-5 páginas** | Manter tabelas de evidências e críticas. Reduzir descrição metodológica de cada estudo. |
| A1.5 | 16 KB | **3-4 páginas** | Manter — já é curto. |
| A1.3 | 25 KB | **2-3 páginas** ⬅️ encurtar! | **Conforme diretriz do Felipi:** manter só 3-4 exemplos icônicos de camera trapping (Snapshot Serengeti, Wildlife Insights, projetos brasileiros) + protocolos de campo. Mover detalhes de hardware para B4 (já está lá). |
| A1.4 | 40 KB | **6-8 páginas** | Manter densidade — esta é a transição para a Etapa 2/3. Cortar repetições com A1.6. |
| A1.6 | 23 KB | **4-5 páginas** | Manter formato de fichas. Mover modelos descartados para apêndice. |
| **TOTAL Etapa 1 no `.tex`** | — | **~25-33 páginas** | Compatível com TCC ICMC (130-180 pgs totais). |

---

## 5. Padronização de nomenclatura e siglas (na monografia)

Vou consolidar em `glossario_notas_rodape.md` a lista oficial. Regras gerais:

- **Primeira ocorrência:** termo por extenso + sigla entre parênteses. Ex.: "Visão Computacional (VC)".
- **Demais ocorrências:** apenas sigla.
- **Lista de abreviaturas:** gerada automaticamente pelo LaTeX (pacote USPSC já provê).
- **Atores:** sempre **papéis genéricos** ("Pesquisador", "Voluntário", "Administrador", "Cuidador") — nunca nomes próprios.
- **Lugares:** "Campus 2 da USP São Carlos" (primeira ocorrência) → "Campus 2" (demais).
- **Nomes próprios:** apenas em (i) autoria, (ii) agradecimentos, (iii) citações bibliográficas.

### Siglas-chave do TCC (lista preliminar — consolidada em glossário)

| Sigla | Significado | Primeira ocorrência (capítulo provável) |
|---|---|---|
| AEX | Atividade de Extensão | Cap. 1 (Introdução) |
| CED | Captura, Esterilização e Devolução | Cap. 1 |
| TNR | *Trap–Neuter–Return* (CED em inglês) | Cap. 1 |
| TNVR | *Trap–Neuter–Vaccinate–Return* | Cap. 2 (Revisão) |
| RTF | *Return-to-Field* | Cap. 2 |
| VC | Visão Computacional | Cap. 2 |
| IA | Inteligência Artificial | Cap. 1 |
| ICMC | Instituto de Ciências Matemáticas e de Computação | Cap. 1 |
| USP | Universidade de São Paulo | Cap. 1 |
| Re-ID | Re-identificação individual | Cap. 2 |
| YOLO | *You Only Look Once* (família de detectores) | Cap. 4 (Pipeline) |
| mAP | *mean Average Precision* | Cap. 4 |
| BAKS/BAUS | *Balanced Accuracy Known/Unknown Subjects* | Cap. 4 |
| PIR | *Passive Infrared* (sensor) | Cap. 3 (Materiais) |
| VMD | *Video Motion Detection* | Cap. 3 |
| RTSP | *Real-Time Streaming Protocol* | Cap. 3 |
| RF/NFR | Requisito Funcional / Requisito Não-Funcional | Cap. 3 |
| ER | Entidade–Relacionamento (Chen) | Cap. 5 (Arquitetura) |
| DFD | Diagrama de Fluxo de Dados | Cap. 5 |
| GBIF | *Global Biodiversity Information Facility* | Cap. 6 (Dados) |
| Camtrap-DP | *Camera Trap Data Package* (padrão GBIF) | Cap. 6 |

---

## 6. Próximos passos da Fase 1

Com este documento de revisão aprovado, sigo para:

1. **Fase 1.2 — B1** (próximo): perfis de ponto renomeados, fauna silvestre, comedouros, mapa
2. **Fase 1.3 — B2:** pipeline-agnóstico, workflow cartão SD
3. **Fase 1.4 — A2.0:** placeholders de hardware e contagens
4. **Fase 1.5 — Glossário:** auditoria de nomes próprios

Os arquivos `A1.x` da Etapa 1 **não serão reescritos** — eles servem como repositório de pesquisa. A **condensação para o `.tex`** acontece na Fase 5 (draft LaTeX), guiada por este documento.

---

## 7. Notas para revisão pelo Felipi

- ✅ A ordem narrativa (funil) está coerente com sua descrição?
- ✅ Os 4 placeholders (AEX, hardware, mapa, contagens) cobrem todas as suas contribuições pessoais à Etapa 1?
- ✅ Tem alguma sigla a acrescentar/remover da lista?
- ✅ A estratégia de "manter tudo no `.md`, condensar para o `.tex`" funciona?

---

**Citações desta nota:**
- Diretrizes ABNT NBR 14724 (apresentação de trabalhos acadêmicos) — referenciado via [Pacote USPSC 3.2](http://biblioteca.puspsc.usp.br/index.php/pacote-uspsc-modelo-para-teses-e-dissertacoes-em-latex/)
