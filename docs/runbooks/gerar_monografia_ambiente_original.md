# Runbook: gerar e conferir a monografia

Todas as figuras e tabelas da monografia foram geradas no servidor (2026-10-15), sem GPU, a partir dos runs da
execução final; o notebook do ambiente original (Python 3.12, NVIDIA MX250, CUDA 12.1) passou a ser **conferência
final opcional**. Nada é treinado. Os runs da monografia continuam sendo os da MX250; só a projeção UMAP do
Apêndice E foi calculada no servidor, em CPU (registrado no `manifest.json` do experimento e no texto).

## 1. Repositórios lado a lado
O felinet procura a monografia em `../monografia-felinet` (`configs/monografia.yaml`):
```
<pasta>/
├── felinet/               branch melhorias/v0.4
└── monografia-felinet/    branch revisao/pos-defesa
```
```bash
cd felinet
uv venv --python 3.12 && . .venv/bin/activate
uv pip install -r requirements/ambiente-original.txt --index-strategy unsafe-best-match \
    --extra-index-url https://download.pytorch.org/whl/cu121      # ou: uv pip install -e '.[dev]' (sem modelos)
uv pip install -e . --no-deps
felinet monografia listar        # o que a monografia usa e o que esta máquina consegue gerar
```

## 2. Dados
| Requisito | Onde está | Observação |
|---|---|---|
| runs da execução final | `runs/` (pacote de runs; inclui `complementar/visualizacao_exploratoria/`) | aponte `runs:` em `configs/monografia.yaml` se estiver em outro lugar |
| imagens dos runs (`kaggle_cats`, Felidae) | caminhos gravados nos runs, no notebook original | fora dele: `felinet datasets reconstruir-run` + `substituir` |
| 36 fotos do iNaturalist | `data/exemplos/fauna_campus2` | `python scripts/baixar_exemplos_inat.py data/exemplos/fauna_campus2 docs/exemplos/fauna_campus2/registro.json` |
| imagens do PetFace (576, N=100) | `/media/felipi/ssd/dados_tcc/PetFace/images` no notebook | no servidor: extraídas de `images/cat.tar.gz` do Drive, em fluxo, só as da lista (ver abaixo) |
| CatIndividualImages | Kaggle `timost1234/cat-individuals` (CC BY 4.0, ~10,5 GB) | só para refazer o UMAP |

PetFace sem gravar o pacote inteiro (47 GB): o `cat.tar.gz` é lido em fluxo e só as imagens citadas no campo
`caminhos` dos embeddings do run são gravadas (a leitura para quando todas aparecem):
```bash
rclone cat gdrive:images/cat.tar.gz --drive-root-folder-id <pasta do PetFace> \
  | felinet datasets extrair-petface --embeddings runs/metodologico/petface/prod/n0100/<sha>/embeddings.npz \
      --destino <quarentena>/images
# e em configs/monografia.yaml -> substituir, os dois prefixos do PetFace -> <quarentena>/images
```

## 3. Gerar e conferir
```bash
felinet monografia gerar                  # escreve em ../monografia-felinet/elementos/gerados/
felinet monografia verificar --runs runs  # tem de terminar em "OK"
cd ../monografia-felinet && make pdf
```
Conferência: o PDF não tem nenhum quadro "Pendente" nem texto vermelho (OBS), e as figuras regeradas no notebook
devem ser iguais às do servidor (o `MANIFESTO.json` guarda o sha256 de cada uma; uma diferença só de metadados de
fonte é esperada entre versões do matplotlib).

## Refazer a projeção UMAP
```bash
uv pip install "open-clip-torch==3.3.0" "umap-learn>=0.5"      # extra [complementares]
python -c "import kagglehub; print(kagglehub.dataset_download('timost1234/cat-individuals'))"
felinet experimentos visualizacao-exploratoria --catalogo <pasta com uma subpasta por gato> --runs runs
felinet monografia gerar --so apendice_e/reid_umap.pdf
```
O `manifest.json` do experimento registra o dispositivo e a máquina (`ambiente`). Se for refeito na MX250, atualize
a frase do Apêndice E que diz onde os *embeddings* foram calculados.

## Refazer os experimentos complementares (opcional)
Não é necessário: a decisão D6 manteve a linha do `felidae_wild` como publicada, com a ressalva no texto. O porte
para o felinet foi validado (`cats_vs_dogs` e `inat_br_cats` reproduzem a tabela).
```bash
D=/CAMINHO/felinet_mono/data
felinet experimentos cascatas-multifonte --runs runs --pesos-yolo /CAMINHO/felinet_mono/yolov8n.pt \
  --fonte cats_vs_dogs=$D/cats_vs_dogs --fonte felidae_wild=$D/felidae_wild --fonte inat_br_cats=$D/inat_br_cats
felinet monografia gerar && felinet monografia verificar --runs runs
```

## Licenças das imagens publicadas
- PetFace: "for research purposes only"; o README do dataset proíbe redistribuir "in whole or in part" sem
  permissão escrita. O autor obteve dos autores do PetFace autorização para usar e publicar na monografia as 12 imagens
  da figura de exemplos de re-ID (2026-10). A autorização cobre a monografia (e seus PDFs em `docs/monografia/`), não a
  redistribuição do *dataset*: as imagens extraídas continuam fora do git.
- CatIndividualImages: CC BY 4.0 (a figura UMAP não mostra imagens).
- iNaturalist: créditos e licença por foto na fonte da figura (gerados de `registro.json`).
