# Glossário — termos para virar nota de rodapé na monografia

> Termos de **biologia, medicina veterinária e controle animal** que aparecem ao longo do texto mas não são o foco do TCC. Cada entrada já está em formato de nota de rodapé, com fonte. Quando o termo aparecer pela primeira vez na monografia, esta nota é inserida.

---

### Da parte A1.1

**Gato de vida livre / feral / comunitário.** Gato de vida livre (*free-roaming cat*) é termo guarda-chuva que abrange: (a) **gato feral** — nascido e criado sem socialização humana significativa, comportamento esquivo, geralmente não adoptável; (b) **gato comunitário** — vive em vida livre mas é cuidado coletivamente por uma comunidade; (c) **gato semi-domiciliado** — possui tutor mas tem livre acesso à rua. A colônia da USP São Carlos é majoritariamente comunitária. Refs.: Boone (2015); CRMV-AL (2022).

**Vacuum effect (efeito de vácuo).** Fenômeno ecológico segundo o qual a remoção de animais de um território com recursos disponíveis é seguida pela rápida reocupação por novos indivíduos vindos de áreas adjacentes, restaurando a densidade populacional anterior em poucos meses. Principal razão da ineficácia da eutanásia em massa como estratégia de controle. Refs.: Boone (2015); Alley Cat Allies.

**Ear-tipping.** Corte cirúrgico reto de cerca de 1 cm da ponta da orelha esquerda do felino, executado durante a esterilização sob anestesia geral, como marca permanente, indolor e visível à distância indicando que o animal foi castrado e participa de um programa CED. No Brasil, foi formalmente desenquadrado de cirurgia mutilante pela Resolução CFMV nº 1.595/2024. Refs.: ASPCA *Feral Cat Sterilization Guidelines*; CRMV-SP (2024); Resolução CFMV nº 1.595/2024.

**Fauna sinantrópica.** Conjunto de espécies silvestres que se adaptaram a viver em ambientes modificados pelo ser humano, frequentemente em estreita associação com habitação e atividades humanas — ratos (*Rattus norvegicus*, *R. rattus*), pombos (*Columba livia*), gambás (*Didelphis* spp.), guaxinins (*Procyon cancrivorus* no Brasil), tatus, algumas espécies de morcego. Distingue-se da fauna silvestre nativa não-sinantrópica, que pode aparecer em borda urbana mas não depende da presença humana. Em pontos de alimentação de gatos, há atração documentada dessas espécies, com implicações epidemiológicas (leptospirose, hantaviroses, raiva, *Toxoplasma*) e ecológicas. Refs.: Wildlife Society (2011/2018); American Bird Conservancy; discussão em A1.5.

**Esporotricose felina.** Micose subcutânea causada por fungos do complexo *Sporothrix*, especialmente *S. brasiliensis*, com transmissão zoonótica do gato para o humano. O Brasil é epicentro mundial do surto desde os anos 1990 (origem no Rio de Janeiro), hoje endêmico em vários estados. Em colônias em área endêmica, o protocolo CED é estendido para TND-RTM, incluindo diagnóstico e tratamento. Refs.: Ferreira et al. (2026); Boletim de Vigilância Sanitária do Rio (2023); CRMV-PR.

### Da parte A1.3

**Camera trap / armadilha fotográfica.** Câmera com sensor de movimento (PIR, *passive infrared*) instalada de forma fixa para registrar fauna sem presença humana. Equipamentos modernos disparam em até 0,2 s, têm flash IR invisível (840–940 nm) para registros noturnos sem incomodar o animal, e armazenam em cartão SD ou transmitem por celular/Wi-Fi. Diferente do *time-lapse* (intervalo fixo) e da *trail camera* genérica. Refs.: Bruce et al. (2025); Cove et al. (2022).

**Modelos de ocupação (*occupancy models*).** Família de modelos hierárquicos que separam o **processo ecológico** ("o ponto está ocupado pela espécie?") da **observação** ("a câmera detectou?"). Permitem estimar ocupação *Ψ* corrigida por probabilidade de detecção *p* < 1, evitando o erro de classificar como "ausente" um ponto onde a espécie estava mas não foi detectada. Referência didática: MacKenzie et al., *Occupancy Estimation and Modeling*, Academic Press, 2017.

### Da parte A1.4

**Re-identificação animal (animal re-ID).** Tarefa de visão computacional que, dada uma imagem de consulta, decide se o indivíduo nela retratado coincide com algum indivíduo de uma galeria de gabaritos (*closed-set*) ou rejeita a consulta como sendo de um indivíduo novo (*open-set*). Implementa o equivalente digital do *capture–recapture* sem nova captura física. Refs.: Schneider, Taylor & Kremer (2022); Adam et al. (2024, WildlifeReID-10k).

**Embedding / espaço de representação.** Vetor de dimensão fixa (tipicamente 128 a 2048) produzido por uma rede neural profunda como assinatura compacta de uma imagem. A distância (euclidiana ou cosseno) entre dois *embeddings* aproxima a similaridade visual entre imagens. Toda re-ID moderna se reduz a aprender um espaço de *embeddings* discriminativo. Refs.: Schroff et al. (2015, FaceNet); Berger-Wolf et al. (2017).

**Triplet loss / contrastive loss.** Funções de custo usadas para treinar redes siamesas. A *contrastive loss* aproxima pares de mesma classe e afasta pares de classes distintas; a *triplet loss* trabalha com tripletas (âncora, positivo, negativo) forçando a âncora a ficar mais próxima do positivo do que do negativo por uma margem. Padrão em re-ID animal *few-shot*. Refs.: Schroff et al. (2015); Porto et al. (2024).

**Open-set vs. closed-set re-identification.** Em *closed-set*, presume-se que toda consulta corresponde a um indivíduo já cadastrado na galeria — métrica típica é Rank-1. Em *open-set*, o sistema também precisa **rejeitar** consultas que não correspondem a ninguém, isto é, identificar indivíduos novos — situação real do TCC, em que novos gatos podem ser abandonados na colônia a qualquer momento. Métricas adicionais incluem AUC e taxa de falsa aceitação. Ref.: Adam et al. (2024).

**Top-k accuracy / Rank-k / mAP / CMC.** Métricas-padrão de re-ID. *Rank-k* é a probabilidade de o indivíduo correto estar entre os k mais similares retornados; a curva *Cumulative Match Characteristic* (CMC) é Rank-k em função de k. *mean Average Precision* (mAP) é a média da precisão média sobre todas as consultas e é a métrica preferida em benchmarks formais. Ref.: Adam et al. (2024); Xiao et al. (2025).

**Transfer learning / fine-tuning.** Estratégia em que pesos de uma rede pré-treinada em conjunto grande (ImageNet, MegaDetector) são reaproveitados em uma tarefa nova, ajustando apenas as últimas camadas (*fine-tuning*) com um conjunto local pequeno. Padrão de engenharia em CV de fauna desde Norouzzadeh et al. (2018) e Mulero-Pázmány et al. (2025).

**CatFACS (*Cat Facial Action Coding System*).** Adaptação para gatos do *Facial Action Coding System* (FACS) de Ekman, descrevendo unidades de ação musculares-faciais. É a base etológica que justifica os 48 marcos faciais usados em CatFLW e em modelos de avaliação automatizada de dor (FGS). Ref.: Caeiro, Waller & Burrows (2017).

**Feline Grimace Scale (FGS).** Escala clínica validada para avaliação de dor aguda em gatos a partir de cinco unidades de ação facial. A versão computacional automatizada por CNN + XGBoost atinge 95% de acurácia (Steagall et al., 2023). No TCC entra como módulo opcional para sinalizar gatos em sofrimento agudo, não como mecanismo de identificação.

**Facial landmarks (marcos faciais).** Pontos anatômicos pré-definidos sobre o rosto (olhos, focinho, base das orelhas, contorno labial) usados para alinhamento, normalização e extração de descritores geométricos. Em gatos, o esquema-padrão de 48 marcos foi proposto por Martvel et al. em CatFLW (2023). Permite morfometria geométrica e análise de expressões.

### Da parte A1.5

**Cinco Domínios do Bem-Estar Animal.** Modelo internacional consolidado para avaliação de bem-estar, formalizado por Mellor & Beausoleil e atualizado em 2020 com a inclusão explícita das interações humano–animal. Os domínios são: (1) **Nutrição**, (2) **Ambiente Físico**, (3) **Saúde**, (4) **Comportamento** e (5) **Estado Mental**. Substituiu progressivamente o antigo modelo das Cinco Liberdades. É base de diretrizes da OIE/WOAH e do CFMV. Ref.: Mellor et al. (2020, *Animals* 10:1870).

**Cat Stress Score (CSS).** Escala de 1 a 7 para avaliação clínica de estresse em gatos a partir de postura, comportamento, vocalização e atividade, proposta por Kessler & Turner (1997). É instrumento de campo padrão em abrigos e canis. Em colônias livres, sua aplicação por imagem ainda é incipiente, e é referencial para um eventual módulo opcional de bem-estar do TCC.

**One Health (Saúde Única).** Abordagem integrada que reconhece a interdependência entre saúde humana, animal e ambiental. Sustenta a justificativa epidemiológica do CED: o controle populacional e sanitário dos gatos comunitários protege simultaneamente os próprios animais, a saúde pública e a fauna nativa. Ref.: WHO/FAO/WOAH One Health Joint Plan of Action (2022–2026).

**Hospedeiro definitivo / hospedeiro intermediário.** No ciclo de vida do *Toxoplasma gondii*, o **hospedeiro definitivo** (gato e demais felídeos) abriga a forma sexuada do parásita e elimina oocistos no ambiente; **hospedeiros intermediários** (humanos, aves, demais mamíferos) abrigam apenas as formas assexuadas. Distinguir os dois papéis é essencial para entender o risco zoonótico real do gato e os pontos de quebra do ciclo. Refs.: Higa et al. (2010); Lopes-Mori et al. (2013).

*A nota sobre **esporotricose felina** está na seção A1.1; aqui ela é amplificada com referências 2024–2025 (Bastos & de Farias 2025; Colombo et al. 2024; Santiago et al. 2025).*

### Da Etapa 2 — Bloco H (Hardware)

**RTSP — Real Time Streaming Protocol.** Padrão IETF (RFC 2326/7826) para controle de streams de vídeo em rede IP. Suportado nativamente por praticamente todas as câmeras IP comerciais — incluindo modelos populares no Brasil como TP-Link Tapo, Intelbras Mibo e WEG WCAM — e por bibliotecas open-source como `ffmpeg`, `OpenCV` e GStreamer. É a interface de integração preferida deste projeto (vide RP-08 em A2.0).

**ONVIF — Open Network Video Interface Forum.** Padrão da indústria de vigilância para descoberta, configuração e controle de câmeras IP em rede. Cumprir ONVIF é equivalente, em câmeras comerciais, a expor RTSP + um conjunto padronizado de chamadas de descoberta. Permite trocar de fabricante sem reescrever o pipeline. Ref.: [onvif.org](https://www.onvif.org/).

**PoE — Power over Ethernet.** Norma IEEE 802.3af/at/bt que permite transmitir energia elétrica (até 30 W em 802.3at, até 90 W em 802.3bt) pelo mesmo cabo Cat-5e/6 que carrega dados Ethernet. Simplifica drasticamente a instalação de câmeras outdoor — basta um switch PoE no rack central e um cabo até a câmera, sem tomada elétrica adicional.

**PIR — Passive Infrared sensor.** Sensor que detecta variação de radiação infravermelha (calor corporal) na cena. É o gatilho padrão de câmeras de armadilha (trail cameras) e do projeto WiseEye e PICT. Em ambiente urbano, sofre com falsos positivos (vento em vegetação aquecida, passagem de veículos), o que motiva a confirmação multi-modal (PIR + análise de pixel, vide WiseEye).

**SBC — Single Board Computer.** Computador completo em uma única placa, com CPU, RAM, armazenamento e interfaces I/O integrados. Exemplos: Raspberry Pi 4/5, Raspberry Pi Zero 2W, NVIDIA Jetson Nano/Orin Nano, Rock Pi. Categoria-padrão para nós de borda em IoT e armadilhas fotográficas modernas.

**LiFePO4 — Lithium Iron Phosphate.** Química de bateria de íon-lítio com cátodo de fosfato de ferro-lítio. Em comparação com íon-lítio convencional (NMC/LCO): maior número de ciclos de carga (≥ 2.000 vs. 500-800), maior estabilidade térmica (segurança em ambiente exposto ao sol), tensão nominal 3,2 V por célula (vs. 3,7 V), densidade energética menor. É o padrão de fato em soluções solar off-grid para aplicações de longa duração (HelioCase, Bennett et al. 2024).

**MPPT — Maximum Power Point Tracking.** Algoritmo embarcado em controladores de carga solar que ajusta a tensão/corrente extraída do painel fotovoltaico para operar continuamente no ponto de máxima potência da curva I-V, maximizando o rendimento em condições variáveis de irradiação. Diferencia-se do controlador PWM (mais barato e menos eficiente).

**IP66 / IP67 (classificação IP).** Norma IEC 60529 de classificação de proteção de invólucros. O primeiro dígito (6) indica proteção total contra entrada de poeira; o segundo (6 = jatos d'água potentes; 7 = imersão temporária até 1 m). IP66 é o piso aceitável para câmera outdoor em São Carlos, onde ocorrem chuvas torrenciais sazonais.

**Trail camera (câmera de armadilha comercial).** Categoria comercial de câmera robusta, alimentada por pilhas AA ou bateria recarregável, com disparo PIR e gravação em cartão SD. Mercado dominado por Bushnell, Browning, Reconyx, Stealth Cam. Otimizada para uso fechado: o pipeline computacional não roda dentro dela; serve apenas para captura. No nosso projeto, é o componente do Cenário C2.

### Siglas

**TNR / TNVR / RTF / SNR / TND-RTM / CED.** *Trap–Neuter–Return* (TNR) é a sigla histórica em inglês; *Trap–Neuter–Vaccinate–Return* (TNVR) acrescenta vacinação obrigatória; *Return-to-Field* (RTF, também SNR) é a variante baseada em abrigo; *Trap, Neuter, Diagnose, Return, Treatment, Monitor* (TND-RTM) é a variante brasileira proposta por Ferreira et al. (2026) para áreas endêmicas. **Captura, Esterilização e Devolução (CED)** é a denominação consagrada no Brasil pelo CFMV e pela Lei nº 13.426/2017. Para fins desta monografia, **CED é usado como termo principal** e os demais como variantes. Refs.: Spehar & Wolf (2021); Ferreira et al. (2026); CRMV-AL (2022).


### Da Etapa 2 — Atores e perfis operacionais (revisão v2)

> Convenção adotada nos blocos B1, B2 e A2.0 v2: **nomes funcionais (não-próprios)** para atores e **siglas práticas (não-gregas)** para perfis. Pessoas e entidades específicas ficam restritas ao front-matter da monografia e aos documentos de contexto operacional. Nomes de **departamentos e setores** (STI, Prefeitura do Campus, CEUA, equipe veterinária parceira) permanecem por serem referências institucionais funcionais, não pessoais.

**Voluntário-AEX.** Papel operacional de campo no projeto AEX-Gatosdoc2. Pessoa autorizada que alimenta a colônia, observa os animais, executa a troca de cartões SD nos pontos OFF-SD (B2.2.10), registra ocorrências em caderneta + fotos de celular, e fornece o insumo empírico para calibração adaptativa da frequência de coleta (B2.2.11). Pode coincidir com quem reabastece os comedouros.

**Pesquisador.** Papel técnico-científico do TCC. Executa ingestão, treina e avalia modelos, valida resultados, mantém o repositório e a documentação. Em caso de indisponibilidade de Voluntário-AEX, assume a troca de cartões como fallback. Pessoa específica registrada no front-matter da monografia.

**Mantenedor-TI.** Papel de infraestrutura. Cuida do armazenamento institucional, backups, controle de acesso, integridade da base. Na fase TCC pode coincidir com o Pesquisador; em operação de longo prazo seria a STI do campus ou equipe equivalente.

**Perfis operacionais de ponto (OFF-SD / NET / AC / AC+NET).** Classificação funcional dos pontos de monitoramento segundo a disponibilidade de **energia AC** e **conectividade Wi-Fi**. Substitui a antiga notação por letras gregas (P-α/β/γ/δ) por nomes mnemônicos. **OFF-SD** — sem AC, sem Wi-Fi, dados em cartão SD (caso primário esperado no Campus 2); **NET** — sem AC, com Wi-Fi; **AC** — com AC, sem Wi-Fi; **AC+NET** — com AC e Wi-Fi (cenário ideal, raro). O schema de dados usa `point_profile` (enum) + `has_pir` (boolean) como atributos do ponto. Ver A2.0 §3 (RF-13, RF-14).

**Pipeline-agnóstico (ao perfil operacional).** Princípio arquitetural: o núcleo E1–E4 do pipeline (detecção, classificação, re-ID, persistência) produz resultados equivalentes em qualquer perfil operacional. A variação entre perfis fica **encapsulada em E0** (ingestão: leitura de cartão SD vs. stream RTSP vs. transferência agendada) e em **duas sub-rotinas de E2.6** (pré-processamento). Garante que o resultado científico não seja enviesado pelo perfil do ponto (RNF-D05: |ΔmAP@0,5| ≤ 0,05 entre perfis). Ver B2 v2 §B2.2 e §B2.5.

**Frequência adaptativa de coleta.** Estratégia de visita a pontos OFF-SD em três fases definidas empiricamente (B2.2.11): (i) **Calibração** (semanas 1–4) — visita semanal para medir consumo real de bateria e taxa de gravação por ponto; (ii) **Operação Regular** (semana 5+) — frequência ajustada por ponto com margem de segurança de 30% sobre o pior caso observado; (iii) **Manutenção sob demanda** — visitas apenas quando alarmes (bateria <20%, SD >80%, sensor offline >48h). A frequência real depende da **capacidade da bateria**, da **capacidade do cartão SD** e da **experiência empírica do Voluntário-AEX no ponto específico**. Literatura (Lifeplan, Saving Nature, NTCA Tiger Phase III) usada apenas como ponto de partida.

**Cerrado-UFSCar (fauna do Campus 2).** Referência ao mosaico de mata nativa e fragmentos de Cerrado próximos ao Campus 2 da USP, com referência direta ao inventário da UFSCar (45 espécies de mamíferos, 200+ de aves). Justifica a necessidade do pipeline distinguir **fauna sinantrópica** (gambá, rato, pombo) de **fauna silvestre nativa** (sagui, quati, ave nativa) e não apenas "gato vs. não-gato". Fonte: Expo SGAS-UFSCar.

**PIR-opcional / VMD (Video Motion Detection) como fallback.** O cenário ideal usa **sensor PIR** (passive infrared) como trigger, mas o projeto contempla explícitamente **câmeras IP baratas sem PIR** como caso real do Campus 2. Nesses casos, o trigger passa a ser **VMD software** — detecção de movimento por análise de píxel feita pelo firmware da câmera ou pelo servidor de ingestão. Em ambos os casos o filtro definitivo de eventos vazios é o E1 (MegaDetector) operando em batch. Ver A2.0 RF-14 e B2.2.6.

**Placeholders ativos da revisão v2.** Marcadores `[PLACEHOLDER-*]` no texto indicam informação dependente de coleta/decisão do Pesquisador, não de pesquisa adicional. Ativos: `[PLACEHOLDER-HARDWARE-NOTEBOOK]` (specs do notebook), `[PLACEHOLDER-NUVEM-INSTITUCIONAL]` (Google Drive USP / OneDrive / AEX), `[PLACEHOLDER-FOTOS-KIT]` (fotos do kit de campo), `[PLACEHOLDER-SCRIPT-INGESTAO]` (script Python de ingestão), `[PLACEHOLDER-CALIBRACAO]` (relatório da Fase Calibração), `[PLACEHOLDER-VOLUME-REAL]` (volume real de imagens/mês), `[~50 gatos]`, `[~10 pontos]` (estimativas operacionais a confirmar na A2.1). Documentados em A2.0 §7.

### Da Etapa 2 — B1 (Contexto operacional)

**Feeding station (estação de alimentação).** Estrutura física padronizada, normalmente coberta e elevada, usada por programas de manejo de colônias gerenciadas para oferecer ração e água em condições higiênicas, com vida útil de anos. Difere do pote no chão pela durabilidade, segregação alimentação×abrigo e por permitir identificação institucional. Referências: Alley Cat Allies, Neighborhood Cats (TNR Handbook 2ª ed.), Best Friends Animal Society.

**LGPD — Lei Geral de Proteção de Dados (Lei nº 13.709/2018).** Marco brasileiro de proteção de dados pessoais. Para o projeto, é relevante porque câmeras instaladas em espaço público de campus capturam pessoas incidentalmente. A LGPD exige declaração de finalidade, base legal (no caso, legítimo interesse de pesquisa científica), guardião dos dados e prazo de retenção. Operacionalmente, traduz-se em placa de aviso, contato responsável e protocolo para descarte/anonimização de pessoas detectadas.

**Pergunta inferencial (Q-INF).** Pergunta operacional sobre manejo, comportamento ou planejamento que o sistema, uma vez em operação, deve ajudar a responder com base nos dados coletados. Diferencia-se de hipótese de pesquisa porque (a) não exige rejeição estatística no escopo do TCC; (b) define o roteiro do relatório periódico do sistema; (c) é mapeada a um bloco da ficha de levantamento como linha de base.

**Capture–recapture (em re-ID).** Família de métodos estatísticos populacionais originalmente desenvolvidos para fauna selvagem (Lincoln-Petersen, Jolly-Seber). No projeto, tem análogo computacional: cada re-identificação de um indivíduo em um novo evento equivale a uma "recaptura" sem trapping físico. Permite estimar tamanho da colônia a partir da curva de descoberta de novos indivíduos ao longo do tempo.

**RSSI — Received Signal Strength Indicator.** Indicador de potência do sinal recebido em redes sem fio (Wi-Fi, celular), expresso em dBm. Para Wi-Fi: ≥ -50 dBm = excelente, -50 a -67 dBm = bom, -67 a -75 dBm = usável, < -75 dBm = instável/inutilizável. Critério adotado na ficha §5 para decidir se Wi-Fi é viável no ponto.

### Da Etapa 2 — B2 Parte 1 (Pipeline E0–E1)

**Bounding-box (bbox).** Caixa retangular delimitando a posição de um objeto detectado em uma imagem, representada como (x, y, largura, altura) em píxeis ou coordenadas normalizadas [0,1]. É a saída-padrão de detectores como MegaDetector, YOLO e DeepFaune.

**Open-set vs. closed-set (em re-identificação).** Em **closed-set**, todos os indivíduos a serem identificados estão presentes na galeria de treinamento — o modelo apenas escolhe entre N classes conhecidas. Em **open-set**, o modelo precisa decidir entre (a) atribuir a um indivíduo conhecido ou (b) declarar "indivíduo novo/desconhecido". O regime open-set é o que vale para colônia real, onde sempre surgem indivíduos novos. Métricas adequadas: mAP open-set, ROC AUC, BAKS (Balanced Accuracy on Known Samples) e BAUS (Balanced Accuracy on Unknown Samples), conforme AnimalCLEF 2024–2025.

**Embedding (vetor de identidade).** Representação numérica densa, tipicamente um vetor de 128 a 2048 dimensões, produzido pela penúltima camada de um modelo de re-ID treinado com perdas de aprendizado métrico (triplet loss, ArcFace). Dois embeddings próximos no espaço (alta similaridade cossenoidal) indicam o mesmo indivíduo. Substitui o rótulo rígido em sistemas que precisam acrescentar IDs novos sem retreino.

**ArcFace loss.** Função de perda para aprendizado métrico que adiciona uma margem angular entre classes no espaço de embeddings normalizado. Resultado: classes mais separadas e mais compactas. É o estado-da-arte para re-ID humano e foi adotada por MegaDescriptor, MiewID e congêneres em re-ID animal.

**mAP — mean Average Precision.** Métrica padrão para detecção e re-ID. Em detecção, mAP@0,5 mede a precisão média quando se considera correta uma detecção cuja IoU com o ground-truth é ≥ 0,5. Em re-ID, mAP mede a qualidade da ordenação top-k das galerias para cada consulta.

**Confirmatory sensing (sensoriamento confirmatório).** Estratégia em armadilhas fotográficas que combina dois ou mais sensores independentes (ex.: PIR físico + análise de pixel software) para validar um evento antes de gravar. Reduz falsos positivos com baixo custo computacional. Proposta original em WiseEye (Klemens et al. 2021).

**Trigger speed (latência de disparo).** Tempo entre a detecção do evento (PIR ou software) e a captura efetiva da imagem. As melhores trail cameras comerciais ficam abaixo de 0,5 s; algumas básicas chegam a 1–2 s. Em animais rápidos, latência alta significa perder o quadro ou capturar apenas parte do corpo.

### Da Etapa 2 — B2 Parte 2 (Pipeline E2–E3 + Pré-processamento)

**Foundation model (em re-ID animal).** Modelo de larga escala pré-treinado em milhares a dezenas de milhares de indivíduos de muitas espécies, projetado para gerar embeddings úteis em zero-shot ou com fine-tuning leve. Análogo a foundation models de NLP (GPT, BERT) mas para biometria animal. Exemplos: MiewID multispecies (Wild Me 2024), MegaDescriptor (Čermák 2024).

**Transfer learning (em visão computacional).** Estratégia de treinar um modelo pré-treinado em domínio fonte (ImageNet, camera-trap global) reutilizando-o em domínio alvo menor (gatos do Campus 2) com fine-tuning leve. Reduz drasticamente a necessidade de dados rotulados — tipicamente 90% de acurácia com 1.000 imagens/categoria contra dezenas de milhares no treino do zero.

**Zero-shot inference.** Aplicar um modelo pré-treinado a um caso novo **sem nenhum fine-tuning**. Útil como linha de base e teste de viabilidade rápida; performance abaixo do fine-tuning específico, mas requer zero anotação local.

**BAKS — Balanced Accuracy on Known Samples.** Métrica de re-ID open-set: probabilidade de atribuir corretamente a identidade a uma consulta que **é** de fato de indivíduo já catalogado. Análogo ao recall em indivíduos conhecidos. Padrão no AnimalCLEF 2025.

**BAUS — Balanced Accuracy on Unknown Samples.** Métrica de re-ID open-set: probabilidade de **rejeitar corretamente** uma consulta de indivíduo novo (classificá-la como "desconhecido" e não tentar atribuir a um conhecido). Análogo à especificidade. Padrão no AnimalCLEF 2025. A média harmônica de BAKS e BAUS é a métrica composite adotada como meta no TCC.

**Rank-1 / Top-k accuracy.** Probabilidade de que o *match* correto esteja entre os k vizinhos mais próximos na galeria. Rank-1 = 0,95 significa que em 95% das consultas o indivíduo certo é o mais parecido.

**Swin Transformer.** Arquitetura de transformer hierárquica baseada em janelas deslizantes, alternativa eficiente ao ViT puro para visão computacional. Backbone do MegaDescriptor-B-224 (109,1M parâmetros).

**Triplet loss.** Função de perda para aprendizado métrico que opera sobre triplas (âncora, positivo, negativo): minimiza distância entre âncora e positivo, maximiza distância entre âncora e negativo, com margem fixa. Precursor histórico do ArcFace; ainda usado quando há restrições de memória ou batch pequeno.

**Active learning.** Estratégia de treino em que o algoritmo **escolhe** quais amostras enviar para anotação humana, priorizando casos de maior incerteza ou ambiguidade. Sani et al. 2025 mostraram +10,49% mAP em re-ID animal com apenas 0,033% das anotações em comparação ao baseline.

**Galeria multi-shot.** Em re-ID, manter **múltiplas imagens** por indivíduo na base de busca (em vez de apenas uma imagem de referência). Robusto a variações de pose, iluminação e modalidade (RGB vs. IR). Padrão em re-ID animal moderno.

**Body-part approach (vs. face approach).** Em re-ID animal, estratégia de gerar embeddings ponderados por **partes do corpo** detectadas separadamente (cabeça, tronco, padrão lateral, cauda) em vez de tratar a imagem inteira como bloco único. Vence o face approach em câmeras laterais a corredores de movimento (cenário do Campus 2). Adotado por PPGNet-Cat (Akbar 2025) e MiewID multispecies.

**Split temporal (em avaliação de modelos).** Divisão de treino/teste em ordem cronológica (treino = início, teste = fim do período) em vez de aleatória. Evidencia drift temporal — performance em split temporal tipicamente cai 5–15 pontos% relativos ao split aleatório, mas é mais realista. Adotado em StreamTrap (Saurabh 2026) e em B5 do TCC.

**Cooldown anti-duplicata.** Janela temporal (ex.: 5 minutos) durante a qual a re-identificação do mesmo indivíduo no mesmo ponto é contada como **um único evento de presença**. Evita inflar estatísticas quando um gato fica comendo por vários minutos disparando múltiplas detecções consecutivas.

### Da Etapa 2 — B2 Parte 3 (Persistência e plano de testes)

**Camtrap-DP (Camera Trap Data Package).** Padrão aberto desenvolvido sob a umbrella da **Biodiversity Information Standards (TDWG)** e adotado pelo **GBIF** para troca, harmonização e arquivamento de dados de armadilhas fotográficas. Estrutura dados em três tabelas CSV (deployments, media, observations) + metadados em datapackage.json. O TCC adotará essa estrutura para o banco interno, garantindo exportação sem retrabalho. Referência: Bubnicki et al. 2024, *Remote Sensing in Ecology and Conservation* 10(3):283–295.

**FAIR (princípios).** Findable, Accessible, Interoperable, Reusable. Conjunto de princípios para gestão e publicação de dados científicos formalizado em Wilkinson et al. 2016. Camtrap-DP é a implementação FAIR para camera-trap.

**SQLite WAL (Write-Ahead Logging).** Modo de journaling do SQLite que permite múltiplos leitores concorrentes com um único escritor, melhorando significativamente performance em workloads read-heavy. Recomendado para o caso de uso do TCC.

**HNSW (Hierarchical Navigable Small World).** Algoritmo de busca aproximada de vizinhos mais próximos baseado em grafo hierárquico com camadas multi-escala. CPU-friendly, latency-low, indexação incremental. Hiperparâmetros chave: M (conectividade), efConstruction (qualidade do grafo no build), efSearch (qualidade da busca em runtime). Implementação de referência: **hnswlib** (header-only C++ com bindings Python).

**FAISS (Facebook AI Similarity Search).** Toolkit de busca por similaridade da Meta AI, suporta brute-force exato (Flat), invertido (IVF), quantização de produto (PQ) e HNSW. Otimizado para GPU e datasets bilhionários. Para o piloto do TCC é overkill; mantido como backup.

**Brute-force NN (Nearest Neighbor).** Busca exata de vizinhos mais próximos por comparação linear (cosine similarity ou L2) contra todos os vetores da galeria. O(N) por consulta. Trivial em NumPy. Suficiente até ~1.000–5.000 vetores em CPU — ponto de partida natural do TCC.

**Throughput vs. latência.** Throughput = imagens processadas por unidade de tempo (img/h ou img/dia). Latência = tempo para processar uma única imagem. O TCC opera em modo **batch noturno**, então a métrica-chave é throughput sustentado; latência individual é secundária.

**Idempotência (em pipelines de processamento).** Propriedade de uma operação tal que execuções repetidas produzem o mesmo resultado da primeira execução. Garante que re-rodar o pipeline na mesma imagem não cria duplicatas no banco. Implementada via UUIDs determinísticos (hash do arquivo) e UPSERT em SQL.

**Capture-recapture (Lincoln-Petersen).** Família de métodos estatísticos para estimar tamanho de população a partir de capturas e recapturas independentes. Em camera-trap com re-ID automática, cada nova detecção de um indivíduo já catalogado é uma "recaptura" sem trapping físico, permitindo estimar N total da colônia com IC 95%. Saturação da curva de descoberta de novos indivíduos ao longo das semanas é a assinatura biológica de que o catálogo está aproximadamente completo.
