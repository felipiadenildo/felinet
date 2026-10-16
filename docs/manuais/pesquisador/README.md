# Manual do pesquisador

Para quem vai reproduzir, avaliar ou estender o felinet.

## Instalar
```bash
make instalar                          # núcleo + dev (sem GPU): CLI, tabelas, figuras, testes
uv pip install -e '.[modelos]'         # inferência: MegaDetector v6, SpeciesNet, MegaDescriptor
uv pip install -e '.[complementares]'  # YOLOv8n + CLIP + UMAP (experimentos complementares)
uv pip install -e '.[video]'           # Fase I com vídeo e CLAHE (OpenCV)
```
O ambiente exato da monografia está em `requirements/ambiente-original.txt`.

## Reproduzir a monografia
- Figuras e tabelas: `felinet monografia listar`, `gerar` e `verificar` (mapa em `docs/REPRODUCAO_MONOGRAFIA.md`;
  os runs da execução final estão no pacote `academic__felinet__runs.tar`).
- Roteiro completo, inclusive o que exige os datasets originais: `docs/runbooks/gerar_monografia_ambiente_original.md`.

## Experimentos
| Comando | O que faz |
|---|---|
| `felinet pipeline executar [--triagem]` | cascata operacional Fases I–III numa fonte; `--triagem` liga a Fase I completa (vídeo → quadros, descarte de escuros/duplicados, normalização) |
| `felinet reid avaliar-closed / avaliar-openset` | re-ID em PetFace (tabelas closed-set e open-set do Cap. 5) |
| `felinet experimentos cascatas-multifonte` | YOLOv8n + CLIP em várias fontes (Apêndice E); deduplica as imagens |
| `felinet experimentos sensibilidade-limiar` | varredura do limiar do detector (Apêndice E) |
| `felinet experimentos visualizacao-exploratoria` | UMAP dos embeddings de um catálogo por identidade (Apêndice E) |
| `felinet exemplos cascata` | Fases II e III em qualquer pasta de imagens; `--pais BRA` liga o filtro geográfico |

## Estender
- Nova fonte: `docs/DATASETS.md`. Os resultados ficam em `runs/<modo>/<fonte>/...` (`docs/arquitetura/layout_runs.md`).
- Nova figura ou tabela da monografia: uma função em `src/felinet/monografia/graficos.py` (ou `exemplos.py`,
  `tabelas.py`) que recebe os dados e devolve a figura ou o texto LaTeX, e uma entrada em `ELEMENTOS`
  (`src/felinet/monografia/elementos.py`) com o rótulo do LaTeX, o arquivo e os requisitos. Na monografia, use
  `\gerado{...}` ou `\input{elementos/gerados/...}`; `felinet monografia verificar` confere a ligação. O estilo único
  (fonte, cores, vírgula decimal) vem de `monografia/estilo.py`.
- Antes de publicar resultados: licenças e limitações em `docs/MODELOS.md`.
