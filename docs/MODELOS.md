# Modelos, dados e licenças (model card)

Resumo do que o felinet usa, em que versão e sob qual licença. **[V]** = verificado na fonte em 2026-10-15;
**[N]** = não verificado (confirmar antes de redistribuir ou de uso comercial).

## Modelos

| Fase | Modelo | Versão usada na monografia | Licença | Uso |
|---|---|---|---|---|
| II | MegaDetector v6 (PytorchWildlife) | `MDV6-yolov10-c` (registrado nos runs) | variantes Ultralytics: AGPL-3.0 [N]; há variantes MIT/Apache do MDv6 [N] | detecção genérica (animal, pessoa, veículo) |
| III | SpeciesNet (Google) | v4.0.2a, pacote `speciesnet` 5.0.3 | código Apache-2.0 [V]; pesos (Kaggle) [N] | classificação de espécie; filtro geográfico opcional (`pais`) |
| IV | MegaDescriptor-T-224 (BVRA) | `hf-hub:BVRA/MegaDescriptor-T-224` | **CC BY-NC 4.0** [V]: uso não comercial | embeddings de re-ID (768-D) |
| complementar | YOLOv8n (Ultralytics, COCO) | `yolov8n.pt`, classe `cat` | AGPL-3.0 [N] | Experimentos de Cascatas Multifonte e de Sensibilidade |
| complementar | CLIP ViT-B/32 (OpenAI, via open_clip 3.3.0) | `ViT-B-32`, `pretrained="openai"` | MIT [N] | classificação zero-shot no Experimento de Cascatas Multifonte |

Consequência: o código do felinet é MIT, mas **o uso dos pesos** segue as licenças acima. Em especial, o
MegaDescriptor não pode ser usado comercialmente e os componentes AGPL impõem condições a quem distribuir um serviço
derivado. Para o projeto de extensão (uso acadêmico e sem fins lucrativos) não há impedimento.

## Limiares e decisões
- Fase II: confiança mínima 0,2 (justificada pelo Experimento de Sensibilidade ao Limiar).
- Fase III: aceita como *F. catus* se o top-1 for "domestic cat" com probabilidade ≥ 0,5 e entropia do top-5 ≤ 1,5;
  senão, validação humana (baixa confiança ou distribuição dispersa) ou outra espécie. Opcional: filtro geográfico
  `pais="BRA"`, com rótulos genéricos que incluem o gato ("cat family") indo à validação humana.
- Fase IV (operação): limiar 0,65 e margem 0,05 são valores de partida. O Cap. 5 da monografia mostra que precisam
  ser calibrados por tamanho de catálogo, com dados da colônia.

## Limitações conhecidas
- Avaliação só em datasets públicos; nenhum dado do Campus 2 (Cap. 6 da monografia).
- Quadros noturnos de infravermelho degradam detecção e classificação (o único felídeo silvestre aceito como gato no
  Felidae foi um puma em quadro noturno).
- Open-set com catálogo pequeno: TPR a FPR fixo cai com o tamanho do catálogo.
- Sem filtro geográfico, o SpeciesNet confunde espécies brasileiras com parentes de outros continentes
  (ex.: gambá-de-orelha-branca → gambá-da-virgínia), sem efeito na aceitação de gatos (`docs/exemplos/fauna_campus2/`).

## Dados
Ver `docs/DATASETS.md`. As composições efetivas das fontes complementares (`felidae_wild` com 71 imagens únicas e 20
de outros táxons; `inat_br_cats` da Costa Rica; `cats_vs_dogs` com 100 gatos e 100 cães) estão no changelog da monografia.
