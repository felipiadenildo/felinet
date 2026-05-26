# Changelog — Revisão v2 (Fases 1.1 a 1.5)

> **Documento de consolidação.** Data: 14/maio/2026.
> Consolida todas as mudanças aplicadas aos documentos da Etapa 1 e da Etapa 2 (Bloco B1, B2, A2.0) durante as Fases 1.1 a 1.5 da revisão sequencial conduzida com o Pesquisador.
> Função: **rastro auditável** para a defesa, para a banca e para o orientador. Cada mudança aponta para a diretriz que a originou, o arquivo afetado e o estado anterior/posterior.

---

## 1. Princípios consolidados nesta revisão

A revisão v2 cristaliza **sete princípios** que ficam vinculantes para o restante do TCC:

1. **Nomenclatura funcional para atores.** Sem nomes próprios em conteúdo técnico da monografia. Pessoas e organizações específicas ficam no front-matter. Departamentos e setores institucionais (STI, Prefeitura do Campus, CEUA, AEX-Gatosdoc2 como projeto) permanecem.
2. **Perfis operacionais com siglas práticas.** Substituídas as letras gregas (`P-α/β/γ/δ`) por **OFF-SD / NET / AC / AC+NET**. Mnemônica direta: cada perfil indica disponibilidade de energia AC e Wi-Fi.
3. **OFF-SD como caso primário do Campus 2.** Sem AC, sem Wi-Fi, troca manual de cartão SD por Voluntário-AEX. Os demais perfis são variantes.
4. **Pipeline-agnóstico ao perfil.** O núcleo E1–E4 produz resultados equivalentes em qualquer perfil; variação fica encapsulada em E0 (ingestão) + duas sub-rotinas de E2.6 (PrePro). Critério mensurável: `|ΔmAP@0,5| ≤ 0,05` entre subconjuntos.
5. **PIR-opcional / VMD fallback.** O cenário ideal usa PIR, mas o sistema deve operar com IP cams baratas que podem não ter PIR. Fallback explícito para motion-detection software.
6. **Frequência adaptativa de coleta.** Visitas a pontos OFF-SD em 3 fases empíricas (Calibração → Operação Regular → Manutenção sob demanda). A frequência real depende de **bateria + SD + experiência do Voluntário-AEX no ponto**. Literatura usada apenas como ponto de partida.
7. **Placeholders explícitos para insumos do Pesquisador.** Toda informação que depende de coleta/decisão do autor é marcada com `[PLACEHOLDER-*]` ou `[~estimativa]`, nunca chutada.

---

## 2. Mudanças por fase

### Fase 1.1 — Narrativa da Etapa 1 (concluída em sessão anterior)

**Diretriz:** "funil problema → AEX → tecnologia → IA, encurtar tecnologia sem IA"

**Arquivos:** `etapa1/_revisao_fase1_etapa1.md` (criado), notas de ordenação aplicadas a A1.1–A1.6.

**Resumo:** Definida ordem narrativa do capítulo de fundamentação (A1.1 problema → A1.5 conservação/bem-estar → A1.3 camera trapping → A1.4 visão computacional → A1.6 datasets). Encurtamento de A1.3 (apenas 3–4 exemplos icônicos). Lacunas para Felipi escrever marcadas em A1.1 §3 (AEX/Gatosdoc2 em primeira pessoa).

---

### Fase 1.2 — B1 Contexto operacional (concluída em sessão anterior)

**Diretrizes consolidadas:**
- Perfil OFF-SD como caso primário (sem AC, sem Wi-Fi)
- Fauna silvestre + sinantrópica (Cerrado UFSCar adjacente)
- Atores com nomes funcionais
- Mapa do Campus 2 como placeholder
- Comedouros anti-pragas

**Arquivo:** `etapa2/B1_contexto_operacional.md` (54 KB, v2)

**Mudanças principais:**
- Reescrita da §perfis usando OFF-SD/NET/AC/AC+NET com OFF-SD em destaque
- Caracterização da fauna do Campus 2 com referência ao Cerrado UFSCar (45 mamíferos, 200+ aves)
- Substituição de "cuidadores do AEX Gatosdoc2" por **Voluntário-AEX** como ator funcional
- Inclusão de Q-INF sobre comedouros anti-pragas com referência Alley Cat Allies
- Mapa do Campus 2 referenciado como `[PLACEHOLDER-MAPA-CAMPUS2]` (a confirmar com Pesquisador)

---

### Fase 1.3 — B2 Pipeline de visão computacional (3 partes)

**Diretrizes consolidadas:**
- Pipeline-agnóstico ao perfil (explícito no header das 3 partes)
- Workflow detalhado do voluntário com cartão SD
- Frequência de coleta dependente de experiência empírica do Voluntário-AEX

**Arquivos:**
- `etapa2/B2_pipeline_visao_computacional_parte1.md` (~580 linhas, v2)
- `etapa2/B2_pipeline_visao_computacional_parte2.md` (~360 linhas, v2)
- `etapa2/B2_pipeline_visao_computacional_parte3.md` (~470 linhas, v2)

**Total de edições aplicadas: 33** (7 + 11 + 15)

**Mudanças principais:**

| # | Mudança | Onde |
|---|---|---|
| 1 | Header reescrito: princípio pipeline-agnóstico + perfis funcionais | Parte 1 (§B2.0), Parte 2 (§B2.4), Parte 3 (§B2.7) |
| 2 | Modos operacionais reescritos com OFF-SD primário | Parte 1 §B2.2.1 |
| 3 | Comparativo de triggers atualizado com PIR-opcional | Parte 1 §B2.2.5 |
| 4 | B2.2.6 substituiu "PIR único" por **decisão híbrida por perfil** (PIR preferido / VMD fallback) | Parte 1 §B2.2.6 |
| 5 | Novo diagrama frontend de aquisição (4 perfis convergindo no mesmo E1) | Parte 1 §B2.2.7 |
| 6 | **NOVA §B2.2.10 — Workflow do Voluntário-AEX para troca de SD** (6 sub-subseções: atores, kit, procedimento 15 passos, nomenclatura, checklist ingestão, rodízio de cartões) | Parte 1 |
| 7 | **NOVA §B2.2.11 — Frequência adaptativa de coleta** (3 fases: Calibração / Operação Regular / Manutenção sob demanda; literatura Lifeplan + Saving Nature + NTCA Tiger Phase III como ponto de partida apenas) | Parte 1 |
| 8 | Síntese da Parte 1 atualizada + fontes ampliadas | Parte 1 §B2.fim |
| 9 | Fauna do Campus 2 caracterizada com Cerrado/sinantrópica/silvestre | Parte 2 §B2.4.2 |
| 10 | Q-INF-CE-2 sobre saguis/quatis em comedouros | Parte 2 §B2.4.4 |
| 11 | `[PLACEHOLDER-HARDWARE-NOTEBOOK]` em todas as menções a hardware do Pesquisador | Partes 2 e 3 |
| 12 | Nota de saturação para `[~50 gatos]` em re-ID | Parte 2 §B2.5.11 |
| 13 | Schema operacional com `point_profile` (enum) + `has_pir` (boolean) em vez de classes gregas | Parte 3 §B2.7.2 |
| 14 | `[PLACEHOLDER-NUVEM-INSTITUCIONAL]` em referências a armazenamento institucional | Parte 3 §B2.7.7 |
| 15 | KPIs de operação de campo (cartões trocados/mês, clock-drift, taxa de SHA-256 ok) | Parte 3 §B2.8.4 |
| 16 | Risco "SD corrompido" e "Voluntário-AEX indisponível" (fallback Pesquisador) | Parte 3 §B2.10 |

---

### Fase 1.4 — A2.0 Requisitos do sistema

**Diretrizes consolidadas:**
- Placeholder hardware notebook
- 10 pontos / 50 gatos como estimativas a confirmar
- Perfis funcionais onde houver "cenários"
- Auditoria de atores para genéricos

**Arquivo:** `etapa2/A2.0_requisitos_sistema.md`

**Total de edições aplicadas: 8**

**Mudanças principais:**

| # | Antes (v1) | Depois (v2) |
|---|---|---|
| 1 | Atores: "Cuidadores Gatosdoc2 / ASA / aluno do TCC" | **Voluntário-AEX, equipe veterinária parceira, Pesquisador, Mantenedor-TI, Gestores do campus** com nota explícita sobre nomenclatura funcional |
| 2 | RF-02: classifica gato/cão/fauna sinantrópica/outros | Inclui agora **fauna silvestre Cerrado/mata nativa** (sagui, quati, ave nativa) |
| 3 | (não havia) | **NOVO RF-13** — Pipeline-agnóstico ao perfil (E1–E4 equivalentes em OFF-SD/NET/AC/AC+NET) |
| 4 | (não havia) | **NOVO RF-14** — Suporte a IP cams baratas sem PIR (fallback motion-detection software) |
| 5 | (não havia) | **NOVO RNF-D05** — Equivalência funcional entre perfis (`\|ΔmAP@0,5\| ≤ 0,05`) |
| 6 | RNF-E01: "≥ 7 dias com 100 disparos/dia" como meta fixa | "**≥ 7 dias como piso conservador**; frequência real é **adaptativa** — B2.2.11 (Calibração → Operação → Manutenção, dependente de bateria + SD + experiência do Voluntário-AEX)" |
| 7 | RNF-U02: "Tempo de coleta semanal de dados ≤ 15 min/ponto" | "**Tempo de troca de cartão SD por visita (perfil OFF-SD)** ≤ 15 min/ponto. **Frequência não é fixa em semanal** — é adaptativa (RNF-E01, B2.2.11)" |
| 8 | RP-08: "calendário fev–jul 2026" | "**Defesa setembro/2026**" (correção) |
| 9 | RP-09: "PC pessoal do Felipi com GPU dedicada (a confirmar)" | "Notebook do Pesquisador — `[PLACEHOLDER-HARDWARE-NOTEBOOK]` + `[PLACEHOLDER-NUVEM-INSTITUCIONAL]`" |
| 10 | (não havia) | **NOVA RP-15** — Escala estimada `~50 gatos` / `~10 pontos` marcada explicitamente como estimativa operacional a confirmar |
| 11 | RP-05: "decisões finais são da ONG ASA – Amigos Salvando Amigos" | "Decisões finais são da equipe veterinária parceira (organização específica registrada no front-matter)" |
| 12 | RP-06: "input do Felipi em 11/maio/2026" | "Consolidado com o Pesquisador na Fase 1" |
| 13 | RNF-P03: "Acesso restrito ao aluno do TCC e ao orientador" | "Acesso restrito ao **Pesquisador** e ao **orientador**" |
| 14 | RNF-C03: "aquisição futura pelo Gatosdoc2/ASA" | "Aquisição futura pelo AEX-Gatosdoc2 e parceiros" |
| 15 | Questões abertas (§7) com 6 itens genéricos | 8 questões (Q-01 a Q-08) cada uma vinculada a um placeholder ativo; nova Q-04 sobre distribuição de perfis OFF-SD/NET/AC entre os pontos; nova Q-08 sobre capacidade padrão de SD/bateria do AEX |

---

### Fase 1.5 — Glossário e auditoria de nomes próprios

**Diretriz adicional:** "nomes de departamentos e setores podem permanecer, como STI e outros"

**Arquivos afetados:**
- `_transversais/glossario_notas_rodape.md` (nova seção §Atores e perfis operacionais v2)
- `etapa1/A1.4_visao_computacional_fauna_felinos.md` (2 correções)
- `etapa2/B2_pipeline_visao_computacional_parte1.md` (7 correções)
- `etapa2/B2_pipeline_visao_computacional_parte2.md` (1 correção)
- `etapa2/B2_pipeline_visao_computacional_parte3.md` (3 correções)
- `etapa2/A2.0_requisitos_sistema.md` (4 correções já contadas na Fase 1.4)

**Total de edições aplicadas: 13 correções + 1 nova seção do glossário (8 entradas)**

**Auditoria executada:** `grep` em 13 documentos de monografia para padrão `\b(Felipi|Bárbara|Madera|ASA|Amigos Salvando|aluno do TCC|PC pessoal|PC do Felipi|notebook do Felipi|laptop do Felipi)\b`. Identificadas 15 ocorrências em conteúdo técnico; todas corrigidas. Preservadas referências em metadocumentos (`_transversais/*`, cabeçalhos de changelog).

**Novas entradas no glossário (seção §Atores e perfis operacionais v2):**

1. Voluntário-AEX, Pesquisador, Mantenedor-TI (papéis funcionais)
2. Perfis OFF-SD / NET / AC / AC+NET
3. Pipeline-agnóstico ao perfil operacional
4. Frequência adaptativa de coleta
5. Cerrado-UFSCar (fauna do Campus 2)
6. PIR-opcional / VMD fallback
7. Placeholders ativos (inventário)

---

## 3. Novos identificadores criados nesta revisão

| ID | Tipo | Onde | O que é |
|---|---|---|---|
| **RF-13** | Requisito funcional | A2.0 §3 | Sistema pipeline-agnóstico ao perfil |
| **RF-14** | Requisito funcional | A2.0 §3 | Suporte a IP cams baratas sem PIR (fallback VMD) |
| **RNF-D05** | Requisito não-funcional (Desempenho) | A2.0 §4.2 | Equivalência funcional entre perfis (`\|ΔmAP@0,5\| ≤ 0,05`) |
| **RP-15** | Restrição do projeto | A2.0 §5.3 | Escala estimada `~50 gatos` / `~10 pontos` (estimativas a confirmar) |
| **B2.2.10** | Seção nova | B2 Parte 1 | Workflow do Voluntário-AEX para troca de SD (15 passos) |
| **B2.2.11** | Seção nova | B2 Parte 1 | Frequência adaptativa de coleta (3 fases empíricas) |
| **Q-INF-CE-2** | Pergunta inferencial | B2 Parte 2 | Comportamento de saguis/quatis em comedouros |

---

## 4. Inventário de placeholders ativos

> Marcadores que dependem de coleta/decisão do Pesquisador, não de pesquisa adicional. Substituir ao longo das próximas fases.

| Placeholder | Conteúdo esperado | Onde aparece |
|---|---|---|
| `[PLACEHOLDER-HARDWARE-NOTEBOOK]` | CPU, RAM, GPU, VRAM, storage, SO do notebook do Pesquisador | A1.4, A2.0 (RP-09, §7 Q-01), B2 Partes 1/2/3 |
| `[PLACEHOLDER-NUVEM-INSTITUCIONAL]` | Google Drive USP via e-mail @usp.br, OneDrive USP, repositório AEX, ou combinação | A2.0 (§2.1, RP-09, §7 Q-02), B2 Parte 3 |
| `[PLACEHOLDER-MAPA-CAMPUS2]` | Planta/mapa do Campus 2 com pontos de alimentação marcados | B1 §6 |
| `[PLACEHOLDER-FOTOS-KIT]` | Fotos do kit de campo do Voluntário-AEX | B2 Parte 1 §B2.2.10.2 |
| `[PLACEHOLDER-SCRIPT-INGESTAO]` | Script Python de ingestão de cartão SD com SHA-256 + clock-drift | B2 Parte 1 §B2.2.10.5 |
| `[PLACEHOLDER-CALIBRACAO]` | Relatório da Fase Calibração (semanas 1–4) | B2 Parte 1 §B2.2.11 |
| `[PLACEHOLDER-VOLUME-REAL]` | Volume real de imagens/mês após Calibração | B2 Parte 3 §B2.7.1 |
| `[~50 gatos]` | Tamanho real da colônia (estimativa operacional) | A2.0 (RP-15, §7 Q-03), B2 Parte 3 |
| `[~10 pontos]` | Número real de pontos de alimentação (estimativa operacional) | A2.0 (RP-15, §7 Q-03), B1, B2 Parte 1 |

---

## 5. Fontes adicionadas/validadas na revisão v2

> Fontes citadas inline nos documentos atualizados. Todas com URL pública verificada.

**Protocolos de camera trapping** (referência para frequência adaptativa, B2.2.11):
- [Lifeplan Camera Trapping Protocol](https://www.protocols.io/view/lifeplan-camera-trapping-protocol-c5uky6uw.pdf) — visita semanal como base
- [Saving Nature Protocol](https://savingnature.com/camera-trapping-protocol/) — visita mensal-trimestral
- [NTCA Tiger Phase III Manual](https://ntca.gov.in/assets/uploads/Reports/AITM/Phase_III_CT%20Manual.pdf) — protocolo de longo prazo
- [GBIF Camera Trap Guide](https://docs.gbif.org/camera-trap-guide/) — boas práticas operacionais

**Visão computacional** (referência para pipeline):
- [MegaDetector v6](https://microsoft.github.io/CameraTraps/) + [releases](https://github.com/microsoft/CameraTraps/releases)
- [MiewID multispecies](https://arxiv.org/html/2412.05602v1) + [Wildbook docs](https://wildbook.docs.wildme.org/introduction/image-analysis-pipeline.html)
- [MegaDescriptor-B-224](https://huggingface.co/BVRA/MegaDescriptor-B-224)
- [Akbar 2025 PPGNet-Cat](https://doi.org/10.3390/jimaging11080274) — re-ID de gatos ferais por partes do corpo

**Padrão de dados:**
- [Camtrap-DP (TDWG)](https://camtrap-dp.tdwg.org)

**Contexto operacional Campus 2:**
- [Cerrado UFSCar — inventário de fauna](https://sites.google.com/view/expo-sgas-ufscar/exposi%C3%A7%C3%B5es/belezas-do-campus)
- [Alley Cat Allies — Feeding station anti-pragas](https://www.alleycat.org/resources/build-a-feral-cat-feeding-station/)

**Template LaTeX da defesa:**
- [USPSC 3.2 pacote oficial](http://biblioteca.puspsc.usp.br/index.php/pacote-uspsc-modelo-para-teses-e-dissertacoes-em-latex/)
- [Overleaf USPSC 3.2](https://www.overleaf.com/latex/templates/pacote-uspsc-modelos-de-trabalhos-de-academicos-em-latex-versao-3-dot-2-campus-usp-de-sao-carlos/ydqymxwkgcnn)

---

## 6. Documentos compartilhados na revisão v2 (com versionamento)

> Cada `name` preserva histórico de versões na plataforma.

| Asset name | Caminho local | Status |
|---|---|---|
| `_revisao_fase1_etapa1` | `etapa1/_revisao_fase1_etapa1.md` | Compartilhado (Fase 1.1) |
| `B1_contexto_operacional` | `etapa2/B1_contexto_operacional.md` | Compartilhado v2 (Fase 1.2) |
| `B2_parte1_pipeline_E0_E1` | `etapa2/B2_pipeline_visao_computacional_parte1.md` | Compartilhado v2 (Fase 1.3 → atualizado 1.5) |
| `B2_parte2_pipeline_E2_E3_PrePro` | `etapa2/B2_pipeline_visao_computacional_parte2.md` | Compartilhado v2 (Fase 1.3 → atualizado 1.5) |
| `B2_parte3_pipeline_E4_metricas_testes` | `etapa2/B2_pipeline_visao_computacional_parte3.md` | Compartilhado v2 (Fase 1.3 → atualizado 1.5) |
| `A2.0_requisitos_sistema` | `etapa2/A2.0_requisitos_sistema.md` | Compartilhado v2 (Fase 1.4 → atualizado 1.5) |
| `A1.4_visao_computacional` | `etapa1/A1.4_visao_computacional_fauna_felinos.md` | Compartilhado v2 (Fase 1.5) |
| `glossario_notas_rodape` | `_transversais/glossario_notas_rodape.md` | Compartilhado v2 (Fase 1.5) |

---

## 7. Documentos NÃO afetados pela revisão v2 (a revisar nas próximas fases)

> Estes arquivos contêm conteúdo da Etapa 2 que ainda usa convenções antigas (letras gregas, nomes próprios em texto técnico) e/ou não foi tocado. Serão revisados conforme prioridade definida com o Pesquisador.

**Etapa 2 — Blocos B3 a B6** (8 arquivos):
- `etapa2/B3_parte1_tradeoffs_aquisicao_deteccao.md`
- `etapa2/B3_parte2_reid_locus_mapeamento.md`
- `etapa2/B4_parte1_camadas_diagramas_servidor.md`
- `etapa2/B4_parte2_er_chen_dfd_stack.md`
- `etapa2/B5_parte1_setup_repo_datasets_protocolo.md`
- `etapa2/B5_parte2_wrappers_scripts_metricas_graficos.md`
- `etapa2/B5_parte3_piloto_pipeline_reprodutibilidade.md`
- `etapa2/B6_parte1_sintese_tecnica.md`
- `etapa2/B6_parte2_anexos_operacionais.md`

**Etapa 1 — A1.1, A1.2, A1.3, A1.5, A1.6** (5 arquivos):
- Não tocados na revisão v2. Conteúdo de pesquisa preservado; ordem narrativa definida em `_revisao_fase1_etapa1.md`.

**Transversais (revisar quando aplicar mudanças nos blocos restantes):**
- `_transversais/fontes_e_lacunas.md`
- `_transversais/diretrizes_projeto.md`
- `_transversais/alinhamento_projeto_base.md` (contém referências a "Dra. Léa", "ONG ASA", "Orientadora AEX" — preservadas como documento de governança)
- `_transversais/notas_pontos_futuros.md`

---

## 8. Pendências para Fases 2 a 5

| Fase | Objetivo | Status |
|---|---|---|
| **2** | Reorganizar estrutura de pastas do projeto completa (pesquisa + LaTeX + código + dados + figuras) | Pendente |
| **3** | Sumário detalhado da monografia (mapeamento Bloco→Capítulo, estimativa de páginas, lista de figuras/tabelas) | Pendente |
| **4** | TODO mestre executável (fichamento, código, autorizações, medições, fontes, redações pessoais) | Pendente |
| **5** | Draft LaTeX completo (capítulos esqueleto preenchível, migração dos MDs) | Pendente |

---

## 9. Como usar este changelog

- **Antes de qualquer nova mudança em B1, B2, A2.0:** consultar §2 desta nota para entender o estado atual.
- **Ao revisar B3–B6:** aplicar as mesmas convenções da §1 (atores funcionais, perfis OFF-SD/NET/AC, pipeline-agnóstico, placeholders explícitos).
- **Ao montar o LaTeX (Fase 5):** os placeholders da §4 viram macros ou comandos `\todo{...}` no .tex.
- **Para a banca:** §3 (novos identificadores) e §5 (fontes) são o suficiente para auditoria.

---

> Fim do changelog v2 (Fases 1.1 a 1.5).
> Próxima atualização: ao concluir a Fase 2 (reorganização de pastas).
