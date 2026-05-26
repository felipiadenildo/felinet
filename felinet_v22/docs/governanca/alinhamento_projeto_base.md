# Alinhamento Revisão vs. Projeto Base do TCC

**Documento de origem:** `projeto_tcc.pdf` (23 páginas, rascunho aprovado)
**Data da análise:** 12/05/2026
**Propósito:** Mapear convergências e divergências entre o projeto base institucional e a revisão profunda em curso (Etapas 2 e 3) para garantir coerência.

---

## 1. Convergências (revisão está alinhada)

| Item do PDF | Onde aparece na revisão | Status |
|---|---|---|
| Sec. 2.2.2(e) "Arquitetura conceitual de hardware e software" | B4 inteira | OK |
| Sec. 3.1 "Análise comparativa entre soluções comerciais e hardware embarcado" | B3 (5 perfis × 2 categorias) | OK |
| Sec. 3.1 "aquisição → pré-proc → armazenamento → comunicação → análise centralizada" | Pipeline E0→E4 (B2) | OK |
| Sec. 2.2.3(f-h) "datasets públicos + reidentificação + modelagem BD + metadados" | B2, B3, B4.4 (próximo) | OK |
| Sec. 3.1 "detecção (YOLO), classificação de espécie, reidentificação" | B2 (YOLO11+MegaDetector → SpeciesNet → MiewID) | OK |
| Sec. 3.2 "anonimização LGPD, sem captura física no TCC" | B1 + diretrizes transversais | OK |
| Sec. 7.5 "Indicadores: visitação, taxa castração, biodiversidade, atípicos" | E4 (B2 Parte 3) | OK |

## 2. Divergências e desvios que valem registrar

### 2.1 Banco de dados: PostgreSQL no PDF vs. SQLite na revisão

- **PDF (7.4):** "Banco relacional **PostgreSQL/MySQL** para eventos de detecção"
- **Revisão atual:** SQLite como primário + PostgreSQL+PostGIS como evolução
- **Justificativa da revisão:** TCC offline, sem instalação física, processamento single-machine no PC do Felipi → SQLite é mais reprodutível e portável; PostgreSQL fica como roadmap.
- **Ação:** Em B4.4 explicitar essa decisão e marcar PostgreSQL como caminho de evolução previsto no projeto base.

### 2.2 Modelos: PDF menciona OSNet/TransReID/Swin; revisão usa MiewID/MegaDescriptor/PPGNet-Cat

- **PDF (7.3):** "Reidentificação individual: OSNet, TransReID, Deep Metric Learning"; "Swin Transformers" nos riscos
- **Revisão:** MiewID-msv3 (primário), MegaDescriptor (baseline), PPGNet-Cat (referência cat-specific)
- **Justificativa:** A literatura específica de fauna (Bubnicki/Wildlife Insights/Akbar 2025) é mais aderente ao problema do que Re-ID genérico de pessoas (OSNet/TransReID).
- **Ação:** Em B4.6 (stack) manter MiewID/MegaDesc/PPGNet, mas registrar nota: "OSNet e TransReID, citados no projeto base, foram avaliados e descartados como primários por serem otimizados para Re-ID de pessoas; permanecem como baseline secundário se MiewID falhar em poses oclusivas."
- Em B5 (testes empíricos): rodar OSNet como **baseline de comparação** para honrar o projeto base.

### 2.3 Hardware: PDF lista ESP32-CAM, Jetson Nano, LoRaWAN, 4G/LTE-M, solar; revisão consolidou em 5 perfis

- **PDF (7.2):** ESP32 / Pi Zero 2W / Jetson Nano; SD/eMMC/NVMe; WiFi/LoRaWAN/4G; solar + LiFePO4
- **Revisão (B3):** Perfis A (trail), B (IP+Pi), C (PIR+Pi opcional), D (consumer com PIR), E (OEM genérica) — não inclui ESP32-CAM, Jetson Nano, LoRaWAN, 4G como perfis principais
- **Justificativa:** B3 priorizou perfis viáveis para o cenário real (~10 pontos, AC disponível em parte deles, Wi-Fi USP, sem comunicação celular contratada). ESP32-CAM tem qualidade de imagem insuficiente para Re-ID de gato individual. Jetson Nano foi descontinuado pela NVIDIA. LoRaWAN não transporta vídeo.
- **Ação:** Em B4.2 (já escrito) está bem; em B4.6 ou em B6 incluir nota explícita: "Hardware listado no projeto base (ESP32-CAM, Jetson Nano, LoRaWAN, 4G/LTE-M, painéis solares) foi avaliado durante a revisão e excluído dos perfis principais pelas razões X, Y, Z; permanece registrado como espaço de design rejeitado em B3 (Apêndice ou nota)."
- **Eventualmente adicionar mini-apêndice em B6**: "Hardware avaliado e excluído", para que a banca veja que houve análise mas não foi adotado.

### 2.4 Cronograma: PDF aloca Mar/Abr para "Concepção técnica" (= Etapa 2)

- **PDF (Sec. 8):** Mar/Abr = mapeamento Campus 2 + alimentadores + tabela hardware + diagrama UML
- **Hoje (12/05/2026):** estamos em Mai/Jun = "Documentação final" no cronograma do PDF
- **Implicação:** A revisão profunda das Etapas 2 e 3 está acontecendo na janela que o PDF reservava à documentação. Isso é coerente com o pedido do Felipi de revisar Etapa 2 com profundidade alta, mas o cronograma original precisa ser ajustado em B6 ou no front-matter do TCC final.

### 2.5 Etapas 3, 4, 5 do PDF estão "achatadas" para B5+B6 na revisão

- **PDF:** Etapa 3 = protótipos VC, Etapa 4 = BD + fluxos, Etapa 5 = indicadores + documentação
- **Revisão:** Etapa 2 (B1-B6) é a única detalhada em profundidade; Etapas 3-5 ficam como grounding curto (instrução do Felipi)
- **Decisão consolidada com o Felipi:** B5 da Etapa 2 absorve testes empíricos + scripts + gráficos comparativos (o que o PDF chamaria de Etapa 3 + Etapa 4)
- **Ação:** Em B6 incluir um "mapa de equivalência": Etapas PDF → Blocos da revisão.

### 2.6 Alimentadores inteligentes (Sec. 2.2.2(c), 3.1, 7.2)

- **PDF:** "Projetar alimentadores inteligentes que integrem alimentação segura, monitoramento visual e proteção contra outras espécies"
- **Revisão:** Praticamente ausente. Os perfis B3 tratam de câmeras, mas alimentadores como objeto físico de design não foram detalhados.
- **Implicação:** Pode ser percebido como lacuna pela banca. Há duas saídas:
  - **(a) Incluir mini-bloco em B4** (B4.7 "Notas sobre alimentadores inteligentes"): descrever conceitualmente que o alimentador é o local físico onde a câmera é montada, com requisitos de geometria (altura, ângulo, proteção contra chuva e contra outras espécies via design da bandeja), mas que o detalhamento do mobiliário fica para fase futura.
  - **(b) Registrar formalmente como fora do escopo desta revisão** e citar no PDF base que cobriu o tema.
- **Recomendação:** opção (a) — adicionar mini-bloco curto (~80 linhas) em B4 Parte 2 ou Parte 3.

### 2.7 Parceiros do projeto (Sec. 6.3)

- **PDF:** Dra. Léa Andri (Embrapa), ONG ASA – Amigos Salvando Amigos, Orientadora AEX Gatosdoc2, equipe Gatosdoc2
- **Revisão:** Em B1 só menciona AEX Gatosdoc2 nominalmente. Dra. Léa, ONG ASA e Orientadora AEX não aparecem.
- **Ação:** Em B6 (consolidação) incluir mapeamento "quem valida o quê" — por exemplo: Dra. Léa valida ecologia de fauna em E4; ONG ASA valida indicadores de bem-estar; Orientadora AEX valida pontos P1...P10.

### 2.8 Risco "teórico demais" (Sec. 9, último risco)

- **PDF:** risco identificado de o trabalho "parecer teórico demais para a banca"
- **Mitigação prevista no PDF:** "incluir demonstrações práticas dos modelos desenvolvidos"
- **Aderência da revisão:** B5 (validação) atende isso ao executar testes empíricos com datasets + gráficos comparativos. Manter ênfase forte em B5 e B6.

## 3. Datasets do PDF vs. revisão

| Dataset (PDF Sec. 7.1) | Aparece na revisão? | Onde |
|---|---|---|
| Oxford-IIIT Pet | A1.6 catálogo + B5 previsto | OK |
| CatFLW (landmarks faciais) | A1.6 catálogo | OK |
| PetFace | A1.6 catálogo | OK |
| Cat Individual Images | A1.6 catálogo + Re-ID Akbar 2025 | OK |
| HelloStreetCat Individuals | A1.6 catálogo | OK |
| Cat Dataset Crawford | A1.6 catálogo | OK |

Catálogo está coerente. B5 vai executar testes sobre estes.

## 4. Resumo das ações concretas a tomar

1. **B4 Parte 2 (próxima):** adicionar mini-bloco B4.7 "Notas sobre alimentadores inteligentes" (~80 linhas) — opção (a) acima.
2. **B4.4 (ER + schema):** declarar PostgreSQL como evolução prevista do SQLite, citando o PDF.
3. **B4.6 (stack):** registrar nota explícita sobre OSNet/TransReID/Swin como baseline alternativo a MiewID.
4. **B5 (validação):** incluir OSNet como baseline secundário nos experimentos de Re-ID para honrar o projeto base.
5. **B6 (consolidação):** incluir três mapeamentos:
   - "Etapas do projeto base ↔ Blocos B1-B6 da revisão"
   - "Hardware listado e excluído" (ESP32-CAM, Jetson Nano, LoRaWAN, 4G/LTE-M, painéis solares)
   - "Quem valida o quê" (Léa, ONG ASA, AEX, orientador)
6. **Cronograma:** B6 inclui versão atualizada do cronograma macro do PDF, com a nova distribuição de Etapas.

---

**Conclusão da análise:** A revisão é **consistente** com o projeto base em termos de objetivos e escopo. As divergências são todas justificáveis tecnicamente e devem ser registradas explicitamente nos blocos finais (B4.4, B4.6, B5, B6) para que a banca e o orientador vejam que houve **decisão informada**, não omissão.
