# Plano da Etapa 2 — Concepção arquitetural (estrutura B1→B5)

## Diretrizes herdadas

- **Foco do TCC**: engenharia / computação. Profundidade alta no pipeline de visão computacional (B2), trade-offs explícitos (B3), e arquitetura física justificada (B4).
- **Foco temático**: monitoramento de **gatos comunitários** com câmera + visão computacional, no Campus 2 / USP São Carlos (~10 pontos, ~50 gatos, parceria AEX Gatosdoc2).
- **Princípio operacional declarado**: "máximo com mínimo de recursos" — vira critério explícito em B3 e regra de decisão em B4.
- **Cenários adversos como dimensão estrutural** (não exceção): pontos sem Wi-Fi e/ou sem tomada são parte do espaço de problema desde B1.
- **Não fazer**: instalação física real, manejo animal, desenvolvimento de FGS (rebaixada a bônus futuro), divergir para outras espécies ou áreas da veterinária.
- **Estilo**: Markdown agora, LaTeX só ao final. Citação inline + lista no fim de cada bloco. Notas de rodapé `[^N]:` para termos técnicos. Tabelas, diagramas (Mermaid/ASCII), imagens, gráficos quando agregarem.
- **Partes off-objective** (projeto eletrônico, dimensionamento solar fino, LoRaWAN profundo) → citadas conceitualmente e marcadas como **"trabalho futuro do implementador"**.

## Modelo argumentativo adotado

Estrutura alinhada ao **Modelo V de engenharia de sistemas** e ao padrão de papers análogos da área (Gonzalez-Guevara 2026, Rahman 2025, Martinský 2025):

```
Requisitos (A2.0)
    ↓
Contexto e ambiente (B1)
    ↓
Arquitetura funcional / pipeline lógico (B2) ←─── foco profundo do TCC
    ↓
Análise de trade-offs / espaço de design (B3)
    ↓
Arquitetura física de referência (B4)
    ↓
Plano de validação e implementação (B5)
```

Cada bloco usa as conclusões do anterior. A defesa do TCC apresenta a cadeia "problema → restrições → modelos → critérios → análise → decisão → validação" de forma rastreável.

## Estrutura da Etapa 2

| Bloco | Tema | Profundidade | Entregáveis principais |
|---|---|---|---|
| **A2.0** | Requisitos do sistema | foundation | 12 RF, 38 RNF, 14 RP. **Pronto.** |
| **B1** | **Contexto operacional e modelo de ambiente** | **médio** | (1) Caracterização do Campus 2 e dos 10 pontos do Gatosdoc2; (2) **matriz energia × conectividade** com 4 perfis de ponto (P-α, P-β, P-γ, P-δ); (3) restrições humanas, institucionais e ambientais; (4) ficha de levantamento de campo para o Felipi preencher in loco. |
| **B2** | **Pipeline conceitual de visão computacional** | **alta — foco do TCC** | (1) Diagrama do pipeline lógico em 5 estágios (Aquisição → Detecção → Classificação → Re-ID → Persistência); (2) **Detecção** — MegaDetector v6, YOLO v8/v11, DeepFaune com comparativo; (3) **Classificação de espécie** felis-catus vs. outros; (4) **Re-identificação individual** — Akbar 2025 (body parts MiewID), PetFace cats, WildlifeReID-10k, estratégia open-set; (5) Pré-processamento, augmentação, filtros temporais; (6) Persistência de embeddings e gestão da base de identidades; (7) Métricas e protocolo de avaliação amarrados a A2.0. Inclui plano de testes do Felipi no PC i7. |
| **B3** | **Análise de trade-offs (espaço de design)** | **alta** | (1) Eixos de trade-off: acurácia, latência, custo, energia, conectividade exigida, escalabilidade, qualidade óptica para re-ID; (2) Tabela comparativa modelo × eixo; (3) Tabela comparativa classe de hardware × eixo; (4) **Critério explícito "máximo com mínimo"** — Pareto e eficiência marginal; (5) Decisão "borda vs. servidor" por estágio; (6) Análise de cenário pessimista (sem energia, sem rede). |
| **B4** | **Arquitetura de referência e camada física** | **média-alta** | (1) Decisão arquitetural híbrida-adaptativa; (2) **Perfis de nó** N-A (mínimo viável), N-B (campus padrão), N-C (autônomo off-grid), N-D (referência ideal) — cada um respondendo a um perfil de ponto de B1; (3) Câmera modelo do projeto (reaproveitada do Bloco H entregue); (4) Pipeline edge-to-cloud físico; (5) Orçamento por perfil e total do piloto. |
| **B5** | **Plano de validação e implementação** | **média** | (1) **Plano de validação por requisito** (cada RF/RNF de A2.0 → método de teste → critério de aceite); (2) Plano de testes do Felipi no PC com datasets públicos; (3) Plano de piloto físico faseado e rotação amostral; (4) Governança de dados, privacidade humana, integração com Gatosdoc2; (5) Cronograma conceitual e itens marcados como "implementação futura". |
| **B6** | Consolidação final | — | Edição integrada da Etapa 2, formatação ABNT no fim. |

## Reaproveitamento do Bloco H já produzido

O `BlocoH_Hardware.md` entregue na rodada anterior **não é descartado**. Ele é redistribuído:

| Conteúdo do Bloco H | Destino na estrutura B1→B5 |
|---|---|
| Premissas P1-P3 (densidade, rotação, perfil de uso) | B1 (entram como axiomas operacionais) |
| Tabela dos 3 cenários (A/B/C) | B3 (insumo para trade-offs) + B4 (vira **perfis de nó** N-A/N-B/N-C/N-D) |
| Câmera modelo do projeto | B4 (mantida íntegra como artefato aberto) |
| Comparativo síntese contra A2.0 | B4 (síntese final) |
| Síntese de processamento/armazenamento/conectividade/energia | B3 (dimensões de trade-off) + B4 (decisão) |
| Itens off-objective | B4 e B5 |
| Custos por cenário | B3 (eficiência marginal) + B4 (orçamento) |

## Ordem de execução

1. ✅ A2.0 — Requisitos
2. ✅ Análise estrutural + decisão pela estrutura B1→B5
3. ⏳ **B1 — Contexto operacional** (próximo)
4. ⏳ B2 — Pipeline de visão computacional
5. ⏳ B3 — Trade-offs
6. ⏳ B4 — Arquitetura física
7. ⏳ B5 — Plano de validação
8. ⏳ B6 — Consolidação

## Testes do Felipi nesta etapa

Etapa 2 ainda é majoritariamente conceitual, mas com **testes preparatórios** que sustentam B2 e B3:

- **(a) MegaDetector v6 e YOLO v8/v11 no PC i7** com imagens-amostra do Gatosdoc2 e/ou de datasets públicos (CCT, iWildCam, Snapshot Serengeti subset). Mede mAP em felis-catus, FPS e uso de memória. Alimenta B2 e B3.
- **(b) Captura RTSP de uma IP-CAM barata** (Tapo C100 ou similar emprestada) no PC, com `ffmpeg` ou `OpenCV`. Valida o caminho de aquisição do perfil de nó N-A. Alimenta B4.
- **(c) Levantamento de campo dos 10 pontos** preenchendo a **ficha de B1** (energia disponível, sinal Wi-Fi USPnet, sinal 4G, fluxo de gatos, restrições físicas). Alimenta B1, B4 e B5.

Testes mais pesados (fine-tuning, re-ID com dataset real, benchmarks completos) ficam para a Etapa 3.

## Estilo visual

Cada bloco contém:
- Pelo menos **1 diagrama** (Mermaid quando possível para ficar versionável; ASCII como fallback).
- **Tabelas comparativas** sempre que houver decisão envolvida.
- **Boxes destacados** para requisitos cruzados (referência a RF-XX, RNF-XX, RP-XX de A2.0).
- **Notas de rodapé `[^X]:`** para termos técnicos novos (alimentam o glossário transversal).
- **Lista de fontes ao final** de cada bloco.
