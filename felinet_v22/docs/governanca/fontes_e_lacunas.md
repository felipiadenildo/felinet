# Fontes complementares e lacunas de busca

> Arquivo vivo. Cada parte da revisão (A1.1, A1.2, …) acrescenta aqui as **lacunas** que a busca automatizada não cobriu bem e os **roteiros de pesquisa manual** que o Felipi e a Bárbara devem executar para fechar a referência. Marcar cada item como `[ ]` pendente, `[x]` resolvido, ou `[~]` parcialmente resolvido.

## Etapa 2 — Bloco H (Hardware)

- [ ] **Cotação real de câmeras IP outdoor IP66 no Brasil** (Intelbras iM7 S, WCAM bullet PoE, Hikvision/Dahua compatíveis ONVIF).
  - **Onde buscar:** lojas Intelbras, distribuidores Hikvision/Dahua, MercadoLivre, Kabum, Magazine Luiza, Amazon BR.
  - **Termos:** `câmera IP outdoor IP66 PoE ONVIF`, `Intelbras iM7 S`, `WCAM bullet 2K`.
  - **Por quê:** ancorar os números do Cenário B na realidade de compra (mar/2026).

- [ ] **Preço atualizado de Raspberry Pi 5 (8 GB) e módulo HQ Camera no Brasil em 2026.**
  - O preço oficial subiu (US$ 80 → US$ 125 em MSRP, conforme Notebookcheck).
  - **Onde buscar:** RoboCore, FilipeFlop, Curto Circuito, Mercado Livre BR.
  - **Termos:** `Raspberry Pi 5 8GB Brasil preço 2026`, `Raspberry Pi HQ Camera Brasil`.
  - **Por quê:** atualizar custos do Cenário B2/C antes da consolidação.

- [ ] **Disponibilidade de Jetson Orin Nano no Brasil.**
  - **Onde buscar:** Arrow, Mouser BR, Newark BR, importadores diretos NVIDIA.
  - **Termos:** `Jetson Orin Nano Super Brasil`, `NVIDIA edge AI distribuidor Brasil`.
  - **Por quê:** validar se C3 (Jetson) é factível no piloto ou apenas referência conceitual.

- [ ] **Painéis solares e LiFePO4 — preços e fornecedores brasileiros** (apenas se for desenvolver o Cenário C off-grid).
  - **Onde buscar:** Aldo Solar, Minha Casa Solar, Lithium-on, Ultracell Brasil.
  - **Termos:** `painel solar 30W mono`, `LiFePO4 12V 20Ah Brasil`, `controlador MPPT 10A`.
  - **Status atual:** marcado como "trabalho futuro do implementador" no Bloco H, mas pode ser refinado se for parte do escopo final.

- [ ] **Política de uso de espectro de Wi-Fi do campus USP São Carlos.**
  - É possível pôr câmeras na rede USPnet? Há rede de IoT separada? Quem aprova?
  - **Onde buscar:** Superintendência de TI (STI) da USP, Seção de Informática do ICMC.
  - **Por quê:** o Cenário A depende disso. Sem rede do campus, cai para 4G (custo maior).

- [ ] **Restrições da Prefeitura do Campus para instalação de equipamentos fixos.**
  - Vale-pena descobrir antes do Bloco P.
  - **Onde buscar:** Prefeitura do Campus USP São Carlos (PUSP-SC), seção de obras/manutenção.
  - **Por quê:** condiciona a viabilidade de qualquer cenário físico.

---

## A1.1 — Fundamentos do CED/TNR

- [ ] **Programas municipais brasileiros de CED com documentação técnica.**
  - **Onde buscar:** sites oficiais das prefeituras de São Paulo (Prefeitura/COSAP), Curitiba, Florianópolis, Rio de Janeiro, Belo Horizonte, Porto Alegre; Centros de Controle de Zoonoses (CCZ) e Unidades de Vigilância de Zoonoses (UVZ).
  - **Termos sugeridos (Google):**
    - `"captura esterilização devolução" site:prefeitura.sp.gov.br`
    - `"manejo populacional ético gatos" relatório filetype:pdf`
    - `"CCZ" "gatos comunitários" relatório anual`
    - `"programa municipal" "gatos comunitários" filetype:pdf`
  - **Bases:** Google Scholar, Catálogo de Teses e Dissertações da CAPES (https://catalogodeteses.capes.gov.br/), SciELO Brasil.
  - **Por quê:** dar contraste com a literatura internacional e mostrar a maturidade prática do Brasil.

- [ ] **Regulamentação infralegal pós-Decreto Federal nº 12.439/2025.**
  - O Art. 10 do Decreto previa edição de normas complementares em até 90 dias após 22/04/2025.
  - **Onde buscar:** [DOU](https://www.in.gov.br/), portal MMA (https://www.gov.br/mma/), CFMV (https://www.cfmv.gov.br/).
  - **Termos:** `"Programa Nacional de Manejo Populacional Ético" portaria`, `"Cadastro Nacional de Animais Domésticos"`.
  - **Por quê:** garantir que o TCC esteja alinhado à normativa mais recente.

- [ ] **Regulamentação interna USP / São Carlos.**
  - Resoluções da Reitoria da USP sobre presença de animais nos campi.
  - Atos da Prefeitura do Campus de São Carlos (PUSP-SC) sobre fauna doméstica.
  - Política da CEUA do ICMC e/ou da EESC.
  - Estatuto e planos de trabalho públicos do AEX Gatosdoc2.
  - **Termos:** `"USP São Carlos" "gatos" portaria`, `"Gatosdoc2"`, `CEUA ICMC USP`, `"prefeitura do campus" São Carlos animais`.
  - **Por quê:** sustentar o tópico "Aspectos burocráticos e autorizações" do PDF do projeto.

- [ ] **Manuais operacionais Alley Cat Allies / HSUS / Humane World versão atual.**
  - Confirmar versão mais recente dos manuais e baixar PDF original (a referência citada na A1.1 é o handbook ASPCA).
  - **Onde:** https://www.alleycat.org/resources/, https://www.humanesociety.org/resources, https://www.aspcapro.org.

---

## A1.2 — Evidências de eficácia e críticas ao CED/TNR

- [ ] **Estudos brasileiros longitudinais (>3 anos) de CED.** A bibliografia internacional acumula casos de 11–28 anos; no Brasil, os estudos mais robustos são de 18 meses (UnB) e 1 ano (UESC). Buscar:
  - Catálogo de Teses CAPES (https://catalogodeteses.capes.gov.br/): `"captura esterilização devolução" longitudinal`
  - Repositórios institucionais USP/UFMG/UFPR/UFRGS para teses defendidas em PPG de Medicina Veterinária Preventiva.
- [ ] **Casos brasileiros de campus.** Procurar relatos do programa Bicho-USP, dos *gatinhos da Politécnica*, da UFSCar (vizinha à USP São Carlos), UFRGS, UFV. Termos: `gatos campus universidade Brasil` em Google Scholar e SciELO.
- [ ] **Posicionamento de SBMV, ABRAVET, CRMV-SP sobre CED.** Útil para mostrar consenso institucional brasileiro. Buscar boletins e pareceres recentes (2023–2026).
- [ ] **Custo-efetividade no Brasil.** A literatura internacional traz custo em USD/cat; não há estimativa pública nacional consolidada. Buscar relatórios COSAP-SP e CCZ-RJ; relatórios da Petlove Foundation/IPS Brasil.
- [ ] **Posição da SBMV (Sociedade Brasileira de Medicina Veterinária) e da Associação Brasileira de Bem-Estar Animal** sobre CED, complementando o consenso nacional além do CFMV.

---

## A1.3 — Monitoramento por câmeras (camera trapping)

- [ ] **Casos brasileiros de camera trapping em fauna urbana e periurbana.** Buscar estudos do CENAP/ICMBio, do Programa BioINFO, teses dos PPGs em Ecologia da USP-RP, USP-São Carlos, UNESP. Termos: `camera trap urbano gatos Brasil`, `armadilha fotográfica fauna urbana`, `*Felis catus* armadilha fotográfica`. Bases: SciELO, BDTD, CAPES.
- [ ] **Programas brasileiros de ciência cidadã com câmeras.** Verificar iNaturalist Brasil, SiBBr, WikiAves e iniciativas do Instituto Ekos.
- [ ] **Padrões de metadados Camtrap DP / Wildlife Insights API** — aprofundar para a Etapa 4. URLs: https://tdwg.github.io/camtrap-dp/, https://api.wildlifeinsights.org/.
- [ ] **Câmeras de baixo custo já testadas em campus universitário no Brasil.** Termos: `câmera IP fauna campus universitário`, `monitoramento gatos câmera USP`. Insumo direto para a Etapa 2.
- [ ] **Estudos de altura/ângulo específicos para gatos.** A literatura disponível é centrada em mamíferos silvestres; pouco há especificamente para *Felis catus* em contexto urbano. Buscar testes empíricos ou dissertações.
- [ ] **Esporotricose felina + monitoramento ambiental.** Cruzar [Geovana et al. (2025, medRxiv)](http://medrxiv.org/lookup/doi/10.1101/2025.09.25.25336677) e Ferreira et al. (2026) com camera trapping.


---

## A1.4 — Visão computacional aplicada a fauna e felinos

- [ ] **L1.4-A — HelloStreetCat e iniciativas comunitárias correlatas.** Sem publicação revisada na busca automatizada. Procurar manualmente em [hellostreetcat.com](https://www.hellostreetcat.com/), GitHub (`hellostreetcat`, `street cat re-id`), YouTube (canais de transmissão ao vivo), ResearchGate. Verificar se a Universidade Nacional de Taiwan ou universidades japonesas publicaram sobre esse tipo de transmissão.
- [ ] **L1.4-B — Re-ID de gatos comunitários no Brasil.** Buscar em [BDTD](https://bdtd.ibict.br/), [Catálogo CAPES](https://catalogodeteses.capes.gov.br/), SciELO Brasil. Termos: `"reidentificação" gato comunitário`, `"identificação individual" "Felis catus" deep learning`, `"visão computacional" "gato comunitário"`, `"camera trap" "Felis catus" Brasil`. Verificar grupos de CV em USP-São Carlos (ICMC, IFSC), UFMG, Unicamp, UFSCar, UnB, PUC-Rio.
- [ ] **L1.4-C — Datasets brasileiros de gatos.** Lapix/UFSC, NILC-USP, CIN-UFPE, anais BRACIS 2020–2025. Confirmar licença. Insumo direto para A1.6.
- [ ] **L1.4-D — Aplicações de MegaDetector / DeepFaune em fauna brasileira.** Cruzar com Bruce et al. (2025) e estudos do CENAP/ICMBio. Bases: SciELO, *Biota Neotropica*, *Journal of Tropical Ecology*, [SBMz](https://www.sbmz.org/).
- [ ] **L1.4-E — CatFACS validado em gatos comunitários (não só pets).** Termos: `CatFACS feral`, `feline grimace scale shelter cat`. Importa para definir limites do módulo opcional de bem-estar.
- [ ] **L1.4-F — Licenciamento dos pesos pré-treinados.** Antes da Etapa 3, ler `LICENSE` de: MegaDetector v6, DeepFaune, SpeciesNet, CatFLW, PetFace, WildlifeReID-10k. Confirmar compatibilidade com TCC + abertura no GitHub.
- [ ] **L1.4-G — Frameworks leves para inferência em CPU/edge.** Comparar **YOLOv8n / YOLOv11n** + **ONNX Runtime** + **OpenVINO** + **TensorRT**. Felipi mede FPS no PC pessoal e reporta na Etapa 3.

### Roteiro de busca manual (strings prontas)

```
"feral cat" OR "community cat" OR "stray cat" "deep learning" "re-identification" 2023..2026
"individual identification" "Felis catus" CNN OR "neural network"
"camera trap" "deep learning" Brazil OR Brasil "Felis catus" OR feline
"MegaDetector" Brasil OR Brazil OR neotropical
"CatFLW" OR "CatFACS" OR "Feline Grimace Scale" computational
"open-set" "animal re-identification" OR "open-world re-identification"
"visão computacional" gatos comunitários OR comunitário Brasil
```

---

## A1.5 — Conservação, zoonoses e bem-estar

- [ ] **L1.5-A — Posição oficial CRMV-SP / CFMV sobre esporotricose e protocolo TND-RTM** (2024–2026). Buscar em [cfmv.gov.br](https://www.cfmv.gov.br/) e CRMV-SP. Cruzar com Resoluções CFMV nº 1.595 e 1.596/2024 (já em A1.1).
- [ ] **L1.5-B — Seroprevalência de toxoplasmose em São Carlos / região**, se houver. SciELO, BDTD (USP-São Carlos, UFSCar), relatórios da Secretaria de Saúde de São Carlos.
- [ ] **L1.5-C — Predação por gatos em cerrado e mata atlântica continental** (continuação de Gonçalves & Machado 2025). Bases: SciELO, *Biota Neotropica*, *Mastozoología Neotropical*, *Journal of Tropical Ecology*. Termos: `Felis catus predação cerrado`, `gato doméstico fauna nativa Brasil mata atlântica`.
- [ ] **L1.5-D — Levantamento de fauna nativa do campus USP São Carlos.** Relatórios da PUSP-SC, dissertações dos PPGs em Ecologia da USP-RP / USP-São Carlos / UFSCar. **Insumo direto para a Etapa 5.**
- [ ] **L1.5-E — Cat Stress Score por imagem.** Aplicação predominante hoje é presencial em abrigo. Buscar trabalhos que tenham operacionalizado o CSS por câmera/vídeo. Termos: `cat stress score remote camera`, `feline behavior automated assessment shelter`. Insumo opcional para a Etapa 3.

---

## A1.6 — Catálogo crítico de datasets, modelos e projetos-base

- [ ] **L1.6-A — Datasets brasileiros de gatos comunitários ou ferais.** Sem retorno na busca automatizada. Verificar [Lapix/UFSC](https://lapix.ufsc.br/), NILC-USP, CIN-UFPE, BRACIS proceedings 2020–2025. Contatar grupo da **Prof. Sandra Avila (Unicamp)**. Conferir SiBBr.
- [ ] **L1.6-B — Confirmação formal da licença de cada item baixado.** Ler `LICENSE` de MegaDetector v6, DeepFaune, SpeciesNet, CatFLW, PetFace, WildlifeReID-10k, Oxford-IIIT, NACTI, Caltech Camera Traps. Documentar em planilha.
- [ ] **L1.6-C — Versão atual do PyTorch-Wildlife em 2026.** Verificar [microsoft.github.io/CameraTraps/](https://microsoft.github.io/CameraTraps/) e se há MegaDetector novo entre v6 e o momento da implementação.
- [ ] **L1.6-D — AnimalCLEF 2026 (calendário CVPR).** Decidir se submeter o sistema do TCC à competição. Datas em [Kaggle](https://www.kaggle.com/competitions/animal-clef-2026).
- [ ] **L1.6-E — Acervo fotográfico do AEX Gatosdoc2 das colônias da USP São Carlos.** Verificar se já existe e se pode ser usado como dado primário. **Insumo crítico para a Etapa 2.**
- [ ] **L1.6-F — Direitos sobre as imagens da colônia.** Confirmar com Prefeitura do Campus / CEUA / AEX Gatosdoc2 se imagens podem ser publicadas em dataset aberto ao fim do TCC.

---

## Etapa 2 — B1 (Contexto operacional)

- [ ] **LB1-A — Distribuição real dos 10 pontos na matriz energia × conectividade.** A ser fechada pela ficha de campo v2 (B1 §5). Insumo direto de B4.
- [ ] **LB1-B — Política da STI USP** para conectar câmeras à USPnet (autenticação, VLAN, restrições). Verificar com Seção Técnica de Informática do ICMC/EESC.
- [ ] **LB1-C — Política da PUSP-SC** para instalação de equipamentos fixos no Campus 2. Contato com Prefeitura do Campus.
- [ ] **LB1-D — Cobertura 4G no Campus 2 por operadora.** Crítico para perfis P-β e P-δ. A ser medido em campo pela ficha §3.
- [ ] **LB1-E — Acervo Gatosdoc2 — protocolo de uso.** Confirmar com a equipe da AEX (cruza com L1.6-E).
- [ ] **LB1-F — Padrão escrito de feeding station da AEX Gatosdoc2.** Não existe; oportunidade de contribuição como subproduto do TCC (cf. §4.5).
- [ ] **LB1-G — Política institucional USP de sinalização LGPD** para câmeras de pesquisa em campus. Buscar com Procuradoria Geral USP e Comissão de Ética da Pesquisa do ICMC/EESC.
- [ ] **LB1-H — Modelos de placa, etiqueta e QR code** que possam ser usados. Templates da Alley Cat Allies e iNaturalist como base.
- [ ] **LB1-I — Estudos de caso de programas TNR/CED com sinalização padronizada em campus universitário.** Buscar em campi nos EUA (NCSU, UC Davis), Reino Unido e Austrália.
