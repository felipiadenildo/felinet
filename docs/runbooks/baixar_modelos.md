# Runbook: baixar modelos pre-treinados

O `felinet` usa **tres modelos pre-treinados** que precisam estar em
`modelos/`. Nenhum deles eh treinado neste TCC (estrategia zero-shot).

## 1. MegaDetector v6

```bash
mkdir -p modelos/megadetector
cd modelos/megadetector
wget https://zenodo.org/records/15376499/files/MDV6-yolov9-c.pt
```

Tamanho: ~250 MB.

## 2. SpeciesNet v4.0.2a

```bash
mkdir -p modelos/speciesnet
# Via kaggle CLI (recomendado):
kaggle models instances versions download google/speciesnet/tensorflow2/v4.0.2a \
  -p modelos/speciesnet
```

Alternativa: o pacote `speciesnet` (em `pyproject.toml`) faz lazy-download
automatico na primeira execucao se o cache estiver vazio.

Tamanho: ~400 MB.

## 3. MegaDescriptor T-224

Baixado automaticamente do Hugging Face na primeira execucao:

```python
from transformers import AutoModel
AutoModel.from_pretrained("BVRA/MegaDescriptor-T-224")
```

Cache: `~/.cache/huggingface/hub/`. Tamanho: ~110 MB.

## Validar

```bash
felinet dev validar-ambiente
```
