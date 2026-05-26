# `modelos/` -- pesos pre-treinados

Esta pasta esta no `.gitignore` (modelos pesam centenas de MB cada).

Cada subpasta contem um modelo:

- `megadetector/MDV6-yolov9-c.pt` (~250 MB)
- `speciesnet/<versao>/` (~400 MB)
- `megadescriptor/` (cache do HuggingFace; ~110 MB)

Para baixar, ver `docs/runbooks/baixar_modelos.md`.

## Estrategia zero-shot

O `felinet` **nao treina nenhum modelo**. Todos os pesos sao versoes
oficiais pre-treinadas, conforme decisao arquitetural da §2.5 da
monografia (baixo custo computacional para o operador final). A
justificativa esta em `docs/escopo/nao_implementado.md` (item 5).
