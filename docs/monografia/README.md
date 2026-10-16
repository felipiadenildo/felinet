# Monografia: versão defendida e versão revisada

O FELINET foi desenvolvido como Trabalho de Conclusão de Curso (Engenharia de Computação, ICMC/EESC-USP). O texto
LaTeX fica num repositório privado; aqui ficam os PDFs, que são públicos.

| Arquivo | O que é |
|---|---|
| `monografia_defendida_2026-07.pdf` | versão defendida e depositada (julho de 2026, 80 p.). Não muda. |
| `monografia_revisada_2026-10.pdf` | versão revisitada e revisada pelo autor após a defesa (outubro de 2026, 78 p.), com nota na capa e na folha de rosto |
| `diferencas_defendida_x_revisada.pdf` | as duas versões comparadas com o latexdiff: em vermelho e riscado, o que saiu; em azul, o que entrou. Os "??" estão só no texto riscado, que cita rótulos que não existem mais. |

| | Versão defendida | Versão revisada |
|---|---|---|
| Repositório da monografia (privado) | branch `main`, commit `c6305f6` | branch `revisao/pos-defesa` |
| FELINET | branch `main` | branch `melhorias/v0.4` |

O sha256 do PDF defendido é `05d92805dde21e08d8e4362333a035e89504db8ad3e24ff3ec40b2a379d33f70`, o mesmo do `main.pdf` do
commit `c6305f6`. O registro arquivo a arquivo das mudanças está em `docs/CHANGELOG_REVISAO.md`, no repositório da monografia.

## O que não mudou

A revisão não altera o trabalho em seus fundamentos:

- **Problema, objetivo geral e objetivos específicos**: o texto dos objetivos é o mesmo. Só saíram os códigos "O1" a
  "O5", e o objetivo de modelos e bases separa os modelos (MegaDetector, SpeciesNet, MegaDescriptor) dos *datasets*.
- **Arquitetura**: a tipologia única de câmera IP adaptada, *offline-first*, com bateria e cartão; o *pipeline* de
  quatro fases com validação humana.
- **Protocolo**: as mesmas bases, os mesmos modelos pré-treinados, sem ajuste fino, e a mesma divisão entre
  *closed-set* e *open-set*.
- **Resultados**: todos os números das tabelas são iguais, porque vêm dos mesmos runs da execução final. Por exemplo,
  a taxa animal de 61,3% e 97,3%, a aceitação de 83,4% e 0,3%, o Top-1 de 0,720, 0,610 e 0,590, e a AUC-ROC de 0,647,
  0,655 e 0,610.
- **Conclusões**: a cascata das Fases II e III é viável e polarizada. A re-ID serve como ranqueamento assistido, e o
  *open-set* é o limite principal. As cinco limitações e as quatro frentes de trabalho futuro continuam as mesmas.

## O que mudou no conteúdo (correções de fato)

Cada correção foi conferida nos runs, nas imagens reconstruídas pelo SHA-256 ou na fonte do *dataset*.

| Na versão defendida | Na versão revisada | Evidência |
|---|---|---|
| MegaDetector v5 | MegaDetector v6 (MDV6-yolov10-c) | o modelo registrado em todas as detecções dos runs |
| *kaggle_cats* = `tongpython/cat-and-dog` | `samuelayman/cat-dataset` (Apache 2.0) | o layout dos arquivos do run |
| Felidae com "panteras, leopardos, leões e linces" | Felidae Conservation Fund (LILA BC): armadilhas fotográficas na Baía de São Francisco, com lince-pardo, puma, coiote e outros | manifestos e EXIF das 300 imagens |
| a única aceitação no Felidae seria "um felídeo pequeno de pelagem clara" | um puma visto de costas, à noite | imagem reconstruída e conferida |
| a Fase III combinaria SpeciesNet e CLIP | SpeciesNet na cascata principal; CLIP avaliado à parte, com o YOLOv8n | código e runs dos experimentos |
| a Fase III seria binária | três destinos: aceita, validação humana ou outra espécie | código da Fase III |
| WildlifeReID-10k como "validação cruzada" e "mAP para detecção" | removidos, porque não foram executados nem medidos | runs |
| *inat_br_cats* descrito como brasileiro | observações da Costa Rica (`place_id=6924`) | consulta registrada |
| a taxa do YOLOv8n contaria "animal" | conta caixas da classe *cat* do COCO (`classes=[15]`) | código do experimento |
| projeção UMAP "do CatIndividualImages" | a figura publicada era do Oxford-IIIT Pet agrupado por raça, e foi refeita com o CatIndividualImages | manifesto do experimento (calculado em CPU) |
| gráfico de eixo duplo com o número de caixas | proporções por fase, numa escala só | runs |
| *Leopardus tigrinus*, *Leopardus pardalis* | *Leopardus guttulus*, *Puma concolor* | taxonomia atual; amostra do Felidae |

## O que mudou na forma

- **Texto**: capítulos 40% mais curtos, de 18,7 mil para 11,3 mil palavras, sem perder dado. Cada assunto é tratado num
  lugar só. O Capítulo 4 tem uma tabela única de bases e medidas, e a síntese do Capítulo 6 responde a cada objetivo.
  Os códigos O1 a O5 e E1, E2… saíram do texto.
- **Figuras e tabelas**: todas as que vêm de dados são geradas por `felinet monografia gerar`, que registra a origem
  de cada arquivo. Na versão defendida eram imagens coladas.
- **Conteúdo novo**:
  - amostras das duas fontes (Cap. 4);
  - exemplos da cascata em fauna do Campus 2, a partir de fotos do iNaturalist (Cap. 3);
  - exemplos de re-ID com acerto e erro (Cap. 5);
  - tabela-síntese da viabilidade por fase (Cap. 5);
  - Apêndice E, com resultados complementares;
  - Apêndice F, com a origem de cada figura e tabela.
- **Listas**: na lista de siglas ficam só as siglas usadas no texto. Saíram os nomes próprios, como MegaDetector e
  PetFace, e entraram CPU, COCO, CLAHE, IoU, ViT e outras. A lista de símbolos traz $N$, $k$, $\mu\pm\sigma$ e @.

## Como a versão revisada é gerada

Ver `docs/REPRODUCAO_MONOGRAFIA.md`: `felinet monografia gerar` escreve as figuras e tabelas na monografia, e
`felinet monografia verificar` confere se o texto e os dados batem. No PDF, o Apêndice F traz o mesmo mapa.

## Licenças das imagens

A versão revisada mostra fotografias de terceiros. As do iNaturalist têm autor e licença na fonte da figura; as do
*kaggle_cats* (Apache 2.0) e do Felidae (CDLA-Permissive) também. A projeção UMAP não mostra fotos. As 12 do PetFace,
em "Exemplos de re-ID", são reproduzidas com autorização dos autores do *dataset*, que é de uso acadêmico e cuja
redistribuição exige permissão. A autorização cobre a monografia, não o *dataset*. Ver
`docs/runbooks/gerar_monografia_ambiente_original.md`.
