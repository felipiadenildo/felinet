# Diretrizes do projeto (regras transversais)

## Foco e escopo (atualizado em 11/maio/2026)

- **O foco é o monitoramento de colônias de gatos por tecnologia (câmera + visão computacional + IA).** Toda a fundamentação deve servir esse objetivo.
- **Dados, casos e referências servem para extrair métricas e parâmetros que justifiquem o projeto e pautem seus benefícios.** Não como revisão acadêmica autônoma.
- **Evitar divergir** em monitoramento de outras espécies, áreas específicas da veterinária, conservação genérica. Manter apenas o essencial para justificar o projeto.
- **Datasets:** só serão usados de fato os que validem **monitoramento de gatos**. Os demais (fauna selvagem, fauna sinantrópica norte-americana) ficam apenas no plano conceitual / inspiração metodológica.
- **Discutir hardware** (câmeras, sensores, computação local) como parte essencial da fundamentação.
- **Etapas 1, 4 e 5 = grounding curto.** **Etapas 2 e 3 = profundidade alta**, com testes e desenvolvimento no PC pessoal do Felipi.

## Processo

- **Não escrever B1 (consolidação Etapa 1) agora.** Escrita da monografia só ao final, após revisão de todas as etapas.
- **Texto final** será montado em LaTeX seguindo ABNT.
- **Cada etapa**: Fase A (evidências, análise, decisões) com revisão por blocos antes de prosseguir.
- **Cada bloco**: entregue, revisado, ajustado, aprovado → próximo bloco.

## Estrutura aprovada para B1 (será escrito ao final)

1. **Contexto e justificativa do manejo de gatos comunitários** — consolida A1.1, A1.2 e A1.5 (esta última encaixada como sub-bloco)
2. **Monitoramento de colônias por imagem — do gargalo manual à IA** — A1.3 → A1.4 com transição natural
3. **Datasets, modelos, ferramentas e hardware** — A1.6 redigido como narrativa, ampliado com hardware
4. **Síntese e lacuna que o TCC ocupa** — objetivo e importância do TCC

## Reorganização das referências da Etapa 1

- **Manter no centro**: trabalhos com aplicação direta a gatos (Akbar 2025, Cove 2022, Martvel/CatFLW, PetFace, FGS Steagall, McHugh 2025, Gonçalves & Machado 2025, do Val 2024).
- **Manter como inspiração metodológica enxuta**: MegaDetector, DeepFaune, ATRW, Snapshot Serengeti, NACTI — citados como prova de conceito do método, não como objeto de estudo.
- **Reduzir/encaixar como nota**: temas veterinários extensos (esporotricose detalhada, toxoplasmose, raiva), trabalhos sobre tigres, etc.

## Parâmetros operacionais confirmados (11/maio/2026)

- **Hardware de desenvolvimento**: laptops/PCs médios (CPU i7, com ou sem GPU dedicada simples). Treino e avaliação dimensionados para este perfil.
- **Pontos de alimentação**: **10 pontos ativos** no Campus 2 hoje, com intenção futura de redução.
- **Tamanho estimado da colônia**: **~50 gatos** (observação).
- **Acervo do Gatosdoc2**: existe, **simples, inconsistente, sem padrão**. Vale como apoio qualitativo, não como dataset estruturado.
- **FGS (Feline Grimace Scale)**: **rebaixado para bônus opcional futuro** — citar como item de continuidade para quem implementar, não desenvolver no TCC.
- **Restrições da Prefeitura do Campus**: sem informação no momento; trabalhar como se autorizações sejam obtidas futuramente.
- **Foco do TCC**: avaliação de modelos + plano de implementação. **Não é projeto de hardware**. Hardware entra como embasamento, sem aprofundamento excessivo.

## Reorganização da Etapa 2 (definida 11/maio/2026)

A Etapa 2 será reestruturada em **três blocos principais**, mais concisos:

1. **Hardware** — embasamento curto: cenário baixo custo (IP-CAM simples + componentes baratos), cenário médio, cenário ideal. Três cenários comparados, sem aprofundamento.
2. **Software** — discussão de uso, comparação de modelos/ferramentas, racional de escolha. **É aqui que mora o foco de engenharia do projeto.**
3. **Plano de implementação** — sintetiza tudo: implementação física dos 10 pontos (atuais + ideal + rotação), uso dos dados, fluxo operacional.

Detalhes muito específicos que fogem do objetivo são **citados a nível conceitual** indicando que ficam para quem for implementar.

## Estilo

- Markdown agora, LaTeX só no fim.
- Citação inline + lista no fim de cada parte.
- BibTeX apenas no fechamento.
- Notas de rodapé acumuladas em `_transversais/glossario_notas_rodape.md`.
- Sem itálico via `*texto*` — usar **negrito** ou destaque por contexto.
