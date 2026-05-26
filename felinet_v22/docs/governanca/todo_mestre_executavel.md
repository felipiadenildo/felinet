# TODO mestre executável — Fase 4

**Documento**: lista consolidada e priorizada de TODAS as pendências do TCC, organizadas por categoria, com responsável, dependências e prazo sugerido até a defesa em **Setembro/2026**.

**Data deste documento**: 14 de maio de 2026 (≈ 16 semanas para a defesa)

**Como usar**: marque com `[x]` cada item ao concluir. O Apêndice F do draft (`\listoftodos`) reflete automaticamente os `\todo{}` espalhados pelo LaTeX — esta lista é a versão de planejamento, mais completa.

---

## Legenda

- **P0** = bloqueador da defesa (sem isso o trabalho não tem mínimo viável)
- **P1** = importante (qualidade do draft + apresentação)
- **P2** = desejável (refina; pode ficar para versão estendida)
- **Resp.**: F = Felipi, O = Orientador, B = Bárbara (revisora), V = Voluntários AEX, M = Mantenedor-TI, E = Equipe veterinária parceira, I = Institucional (Prefeitura/ICMC/STI)

---

## 1. Redações pessoais (P0, Resp. F)

| ID | Tarefa | Prazo |
|---|---|---|
| 1.1 | Escrever dedicatória (`pre-textuais/dedicatoria.tex`) | Ago/2026 |
| 1.2 | Escrever agradecimentos (`pre-textuais/agradecimentos.tex`) | Ago/2026 |
| 1.3 | Escolher epígrafe (`pre-textuais/epigrafe.tex`) | Ago/2026 |
| 1.4 | Revisar resumo PT e abstract EN com orientador | Ago/2026 |

## 2. Dados de campo (P0, Resp. F + V + B)

| ID | Tarefa | Prazo | Dep. |
|---|---|---|---|
| 2.1 | Contagem real dos pontos de alimentação (estimado: 10) | Jun/2026 | — |
| 2.2 | Contagem real / estimativa atualizada de gatos (estimado: 50) | Jun/2026 | — |
| 2.3 | Caracterização de cada ponto: AC sim/não, Wi-Fi sim/não → distribuição entre perfis OFF-SD/NET/AC/AC+NET | Jun/2026 | 2.1 |
| 2.4 | Mapa do Campus 2 com pontos georreferenciados (substituir `[[PLACEHOLDER-MAPA-CAMPUS2]]`) | Jun/2026 | 2.1 |
| 2.5 | Inventário de fauna sinantrópica observada nos comedouros (saguis, quatis, outros) | Jun-Jul/2026 | — |
| 2.6 | Fotos dos comedouros atuais (`[[PLACEHOLDER-FOTOS-KIT]]`) | Jun/2026 | — |

## 3. Autorizações institucionais (P0, Resp. F + I)

| ID | Tarefa | Prazo | Dep. |
|---|---|---|---|
| 3.1 | Autorização da Prefeitura do Campus USP de São Carlos | Jun/2026 | — |
| 3.2 | Anuência da Diretoria do ICMC | Jun/2026 | 3.1 |
| 3.3 | Termo de cooperação com AEX Gatosdoc2 | Jun/2026 | — |
| 3.4 | Consulta à CEUA (se aplicável ao monitoramento não-invasivo) | Jun/2026 | — |
| 3.5 | Parecer LGPD (Encarregado de Dados USP) | Jul/2026 | — |
| 3.6 | Acordo com STI para hospedagem/nuvem institucional | Jul/2026 | 3.2 |

## 4. Hardware e infraestrutura (P1, Resp. F + M)

| ID | Tarefa | Prazo | Dep. |
|---|---|---|---|
| 4.1 | Escolha de modelos de câmera-armadilha (com PIR) e IPCAM (sem PIR) | Jun/2026 | 2.3 |
| 4.2 | Especificação de pilhas/baterias para câmeras PIR | Jun/2026 | 4.1 |
| 4.3 | Especificação de cartões microSD (capacidade × volume estimado) | Jun/2026 | 4.1 |
| 4.4 | Definir servidor de processamento (substituir `[[PLACEHOLDER-HARDWARE-NOTEBOOK]]`) — notebook do pesquisador ou máquina institucional | Jul/2026 | 3.6 |
| 4.5 | Configurar nuvem institucional / Google Drive USP (`[[PLACEHOLDER-NUVEM-INSTITUCIONAL]]`) | Jul/2026 | 3.6 |
| 4.6 | Definir caixa anti-umidade para transporte de SD | Jun/2026 | 4.3 |
| 4.7 | Anexar datasheets (Anexo B) | Ago/2026 | 4.1-4.3 |

## 5. Código a desenvolver (P1, Resp. F)

| ID | Tarefa | Prazo | Dep. |
|---|---|---|---|
| 5.1 | Script de ingestão de SD (`03_codigo/scripts/ingestao.py` — substituir `[[PLACEHOLDER-SCRIPT-INGESTAO]]`) | Jul/2026 | 4.1 |
| 5.2 | Wrapper de MegaDetector (E1) | Jul/2026 | — |
| 5.3 | Pipeline E2 (curadoria, dedup temporal) | Jul/2026 | 5.2 |
| 5.4 | Wrapper de detecção fina (E3) | Jul/2026 | 5.2 |
| 5.5 | Wrapper de MiewID + MegaDescriptor (E4) | Jul/2026 | 5.2 |
| 5.6 | Pipeline integrador `run_all.py` | Jul/2026 | 5.2-5.5 |
| 5.7 | Scripts de métricas (mAP, F1, Rank-K) | Jul/2026 | 5.6 |
| 5.8 | Notebook de exploração / sanity check (`03_codigo/notebooks/`) | Jul/2026 | 5.7 |
| 5.9 | Testes unitários básicos | Ago/2026 | 5.6 |
| 5.10 | Setup DVC + MLflow | Jul/2026 | — |
| 5.11 | Dashboard operacional básico (Streamlit ou similar) | Ago/2026 | 5.7 |

## 6. Execuções a rodar (P0, Resp. F)

| ID | Tarefa | Prazo | Dep. | TODO no draft |
|---|---|---|---|---|
| 6.1 | Benchmark de MegaDetector em dataset público (LILA / Snapshot Serengeti) | Jul/2026 | 5.2 | Cap 7 |
| 6.2 | Benchmark de MiewID + MegaDescriptor em dataset de felinos | Jul/2026 | 5.5 | Cap 7 |
| 6.3 | Calibração inicial (semanas 1-4 do piloto): observar bateria, SD, frequência ideal | Ago/2026 | 4.1, 3.1 | Cap 7 |
| 6.4 | Operação regular (semana 5+): coletar volume real | Set/2026 | 6.3 | Cap 7 |
| 6.5 | Substituir `[[PLACEHOLDER-CALIBRACAO]]` e `[[PLACEHOLDER-VOLUME-REAL]]` por dados reais | Set/2026 | 6.3, 6.4 | Cap 6, 7 |
| 6.6 | Comparativo de equivalência entre perfis (RNF-D05): mAP similar entre OFF-SD, NET, AC, AC+NET | Ago-Set/2026 | 6.1-6.4 | Cap 6 |

## 7. Figuras a gerar (P1, Resp. F)

Total estimado no sumário: ~31 figuras. Lista resumida das placeholder-críticas:

| ID | Figura | Capítulo | Ferramenta sugerida | Prazo |
|---|---|---|---|---|
| 7.1 | Mapa Campus 2 com pontos | Cap 1, 4 | QGIS ou Google Earth | Jun/2026 |
| 7.2 | Esquema da problemática (funil problema → AEX → CV) | Cap 1 | draw.io / TikZ | Jun/2026 |
| 7.3 | Linha do tempo CED no Brasil | Cap 2 | TikZ ou Inkscape | Jul/2026 |
| 7.4 | Diagrama de atores | Cap 3 | draw.io | Jul/2026 |
| 7.5 | Perfis funcionais OFF-SD/NET/AC/AC+NET | Cap 4 | TikZ | Jul/2026 |
| 7.6 | Diagrama de camadas (captura/proc/storage/UI) | Cap 5 | TikZ | Jul/2026 |
| 7.7 | DFD (Diagrama Fluxo de Dados) | Cap 5 | draw.io | Jul/2026 |
| 7.8 | **ER em notação Chen** | Cap 5 | draw.io ou TikZ-er2 | Jul/2026 |
| 7.9 | Fluxograma do pipeline E0-E4 | Cap 6 | TikZ | Jul/2026 |
| 7.10 | Sub-rotinas de E0 (online vs offline-SD) | Cap 6 | TikZ | Jul/2026 |
| 7.11 | Curvas mAP/F1 (após execução do benchmark) | Cap 6, 7 | Matplotlib | Ago/2026 |
| 7.12 | Matriz de confusão de re-id | Cap 6, 7 | Matplotlib | Ago/2026 |
| 7.13 | Cronograma do piloto | Cap 7 | Gantt (TikZ ou plantuml) | Jul/2026 |
| 7.14 | Roadmap evolutivo | Cap 8 | TikZ | Ago/2026 |

## 8. Fontes bibliográficas a confirmar (P1, Resp. F + B)

| ID | Tarefa | Prazo |
|---|---|---|
| 8.1 | Confirmar entries placeholder em `bib/references.bib`: `EvansLgpd`, `RealTimeMonitoring` | Jul/2026 |
| 8.2 | Adicionar referências brasileiras específicas (Lei 13.426/2017, resoluções CFMV) com URLs verificadas | Jul/2026 |
| 8.3 | Auditar todas as citações `\cite{}` do draft contra `references.bib` (não pode haver chave inexistente) | Ago/2026 |
| 8.4 | Verificar fechamento de fontes que estão em `01_pesquisa/_buscas_brutas/` mas ainda não foram convertidas em BibTeX | Jul/2026 |

## 9. Revisões com revisora Bárbara (P1, Resp. F + B)

| ID | Tarefa | Prazo |
|---|---|---|
| 9.1 | 1ª revisão completa do draft (após estabilização — Jun/2026) | Jun/2026 |
| 9.2 | 2ª revisão após preenchimento de dados de campo | Ago/2026 |
| 9.3 | Revisão final (português, ortografia, fluidez) | Set/2026 |

## 10. Reuniões com orientador (P0, Resp. F + O)

| ID | Tarefa | Prazo |
|---|---|---|
| 10.1 | Apresentar este draft ao Prof. Matheus | Mai-Jun/2026 |
| 10.2 | Validar escopo do piloto após autorizações | Jul/2026 |
| 10.3 | Revisão pré-defesa | Set/2026 |
| 10.4 | Banca: definir membros e agendar | Jul-Ago/2026 |

## 11. Trâmites finais ICMC (P0, Resp. F + I)

| ID | Tarefa | Prazo |
|---|---|---|
| 11.1 | Solicitar ficha catalográfica à Biblioteca ICMC | Ago/2026 |
| 11.2 | Submeter trabalho ao TCC-ICMC v2.1 (sistema USP) | Ago/2026 |
| 11.3 | Inscrição da banca no sistema | Ago/2026 |
| 11.4 | Imprimir cópias (se exigido) | Set/2026 |
| 11.5 | Folha de aprovação assinada (após defesa) | Set/2026 |
| 11.6 | Versão final corrigida no repositório institucional | Out/2026 |

---

## Cronograma macro

```
Mai/2026  ─── DRAFT ENTREGUE AO ORIENTADOR (este momento) ───
Jun/2026  ─── Dados de campo + autorizações + 1ª revisão B
Jul/2026  ─── Código pronto + benchmarks + figuras
Ago/2026  ─── Piloto fase calibração + 2ª revisão B + ficha cat.
Set/2026  ─── Piloto operação regular + DEFESA + revisão final
Out/2026  ─── Versão final no repositório
```

## Riscos do cronograma

1. **Autorização da Prefeitura/CEUA atrasada** → pode empurrar o piloto. **Mitigação**: iniciar tramitação imediatamente, em paralelo com escrita.
2. **Hardware demora a chegar** → se câmeras forem importadas. **Mitigação**: priorizar modelos com fornecedor nacional.
3. **Disponibilidade dos voluntários** → variável. **Mitigação**: protocolo claro no Apêndice C, treinamento curto.
4. **Resultados do benchmark insuficientes** → modelos não generalizam para gatos urbanos do Campus 2. **Mitigação**: o draft já trata isso como pergunta de validação (Q-04, Q-05); resultado negativo também é resultado válido para o TCC.
