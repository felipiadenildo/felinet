# B5 — Plano de validação e implementação (Parte 1)

**Bloco:** B5 — Plano de validação e implementação (Etapa 2 — fechamento técnico)
**Parte 1 cobre:** B5.1 (setup do PC + ambiente Python), B5.2 (estrutura do repositório), B5.3 (datasets — download, licenças, organização), B5.4 (protocolo experimental geral)
**Próximas partes:** Parte 2 (métricas, scripts de E1/E2/E3, tabelas e gráficos); Parte 3 (piloto offline + análise + reprodutibilidade)
**Natureza desta seção:** **manual operacional**. Cada subseção contém comandos copiáveis (bash/Python) que o Felipi roda no PC dele. Tudo aqui será adaptado para a monografia (capítulo "Metodologia experimental").

---

## B5.0 — Visão geral da fase de validação

O objetivo de B5 é **transformar as decisões arquiteturais de B1-B4 em evidência empírica**. A pergunta central é: **os modelos escolhidos (YOLO11 + MegaDetector → SpeciesNet → MiewID/MegaDescriptor/PPGNet-Cat) atingem as métricas de sucesso definidas em A2.0** para os datasets disponíveis e para o cenário da colônia AEX Gatosdoc2?

Em síntese, B5 entrega três blocos de evidência:

1. **Benchmarks reproduzíveis** sobre datasets públicos: tabelas e gráficos comparativos por estágio (E1, E2, E3).
2. **Piloto offline em laboratório**: vídeos representativos simulando os 5 perfis (A, B, D, E1, E2), rodados no PC i7 do Felipi, demonstrando que a pipeline completa funciona fim-a-fim.
3. **Análise de viabilidade**: confronto entre os números medidos e os requisitos não-funcionais de A2.0 (latência batch noturna 8h, mAP/Rank-1 mínimos, BAKS/BAUS ≥ 0.80).

**Nota importante de escopo (alinhada com Felipi 12/05/2026):** B5 **não exige instalação física de câmeras no campus**. Toda a validação é feita com dados públicos + vídeos representativos rodados localmente. Isto é consistente com o projeto base (PDF Sec. 3.2: "sem captura física no TCC, anonimização LGPD").

---

## B5.1 — Preparação do PC e ambiente Python

### B5.1.1 — Inventário de hardware do PC do Felipi

Recapitulando B4.3 (dimensionamento) — confirme/anote estas características do seu PC antes de prosseguir:

```bash
# Cole no terminal do PC e anote os valores
# (Linux / WSL2 / Mac com adaptações)
echo "=== CPU ==="
lscpu | grep -E "Model name|Socket|Core|Thread|MHz"

echo "=== RAM ==="
free -h

echo "=== Storage ==="
df -h /

echo "=== GPU (se houver) ==="
lspci | grep -E "VGA|3D"
# Se houver NVIDIA:
nvidia-smi 2>/dev/null || echo "Sem NVIDIA GPU"

echo "=== Sistema ==="
uname -a
cat /etc/os-release 2>/dev/null | head -2
```

**Esperado no PC do Felipi (mínimo para B5):**
- CPU: Intel i7 (8 cores / 16 threads, qualquer geração ≥ 8ª)
- RAM: ≥ 16 GB
- Storage: ≥ 500 GB livre (datasets + modelos + resultados)
- iGPU Intel ou GPU dedicada simples (opcional, acelera E1/E2)

**Anote estes valores em** `docs/hardware_setup.md` **no repositório** — vão direto para a monografia (capítulo "Recursos materiais").

### B5.1.2 — Instalação do ambiente Python

Sigo a recomendação de B4.6 — Python 3.11+, gerenciado por `uv` (mais rápido que pip) ou `poetry`. Apresento `uv` por ser o padrão moderno e mais rápido.

**Passo 1 — Instalar `uv`:**

```bash
# Linux / Mac / WSL2
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reiniciar shell para ativar
source ~/.bashrc   # ou ~/.zshrc

# Verificar
uv --version
```

**Passo 2 — Criar a pasta-raiz do projeto:**

```bash
# Crie a pasta-raiz onde TODO o trabalho prático vai morar
mkdir -p ~/tcc_gatosdoc2
cd ~/tcc_gatosdoc2

# Inicializar projeto Python
uv init --python 3.11
```

**Passo 3 — Instalar dependências mínimas para B5 (subset do `requirements.txt` de B4.6.4):**

```bash
# Núcleo de visão e ML
uv add "torch>=2.4" "torchvision>=0.19" "opencv-python>=4.10"
uv add "ultralytics>=8.3" "onnxruntime>=1.18"
uv add "huggingface_hub>=0.24" "transformers>=4.44"
uv add "hnswlib>=0.8" "scikit-learn>=1.5" "scipy>=1.14"

# Re-ID baselines
uv add "torchreid>=1.4"   # OSNet
uv add "timm>=1.0"        # MegaDescriptor depende disso

# Dados
uv add "pandas>=2.2" "numpy>=1.26" "pillow>=10.4" "pyarrow>=17"
uv add "sqlalchemy>=2.0" "alembic>=1.13"
uv add "frictionless>=5.17"   # Camtrap-DP

# Experimentos / reprodutibilidade
uv add "mlflow>=2.15" "dvc>=3.55" "tqdm>=4.66"
uv add --dev "jupyterlab>=4.2" "ipywidgets>=8.1"
uv add --dev "pytest>=8.3" "ruff>=0.6" "black>=24.8"

# Visualização (para gráficos da monografia)
uv add "matplotlib>=3.9" "seaborn>=0.13" "plotly>=5.20"

# UI (será usado em B5 Parte 3 quando montarmos demo)
uv add "streamlit>=1.38" "folium>=0.16"
```

**Passo 4 — Verificar instalação:**

```bash
uv run python -c "
import torch, torchvision, cv2, ultralytics, hnswlib, sklearn
print('Torch:', torch.__version__, '| CUDA:', torch.cuda.is_available())
print('OpenCV:', cv2.__version__)
print('YOLO Ultralytics:', ultralytics.__version__)
print('hnswlib OK')
print('OK — ambiente pronto')
"
```

Saída esperada (sem GPU dedicada):

```
Torch: 2.4.1+cpu | CUDA: False
OpenCV: 4.10.0
YOLO Ultralytics: 8.3.x
hnswlib OK
OK — ambiente pronto
```

Se você tiver GPU NVIDIA, instale `torch` com CUDA:

```bash
# Substitua a versão de torch por uma com CUDA
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### B5.1.3 — Instalação de FFmpeg e ferramentas de sistema

```bash
# Linux (Ubuntu/Debian/WSL)
sudo apt update
sudo apt install -y ffmpeg git git-lfs make jq

# Mac
brew install ffmpeg git git-lfs make jq

# Verificar
ffmpeg -version | head -1
git lfs --version
```

`git-lfs` é necessário porque alguns modelos (MegaDescriptor) vêm via Hugging Face Hub que usa LFS.

### B5.1.4 — Configurar credenciais externas

Você vai precisar de duas contas para baixar modelos e datasets:

**Hugging Face (modelos + datasets):**

```bash
# Cadastre-se em https://huggingface.co/join
# Crie um token em https://huggingface.co/settings/tokens (read access)
uv run huggingface-cli login
# Cole o token quando pedir
```

**Kaggle (datasets):**

```bash
# Cadastre-se em https://www.kaggle.com
# Vá em "Account" → "Create New API Token"
# Baixe kaggle.json e mova para ~/.kaggle/
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

uv add kaggle
uv run kaggle --version
```

---

## B5.2 — Estrutura canônica do repositório

A estrutura abaixo é o que entra no GitHub e será citada na monografia como **Apêndice A — Repositório de código e dados**. Padrão "Cookiecutter Data Science" adaptado.

### B5.2.1 — Layout de pastas

```
tcc_gatosdoc2/
├── README.md                       # apresentação do projeto (vai virar resumo da monografia)
├── pyproject.toml                  # gerenciado por uv
├── uv.lock                         # lock-file de dependências
├── .gitignore
├── .python-version                 # "3.11"
├── Makefile                        # comandos macro: make download, make train, etc.
│
├── configs/                        # YAMLs versionados de cada experimento
│   ├── e1_yolo11n.yaml
│   ├── e1_megadetector.yaml
│   ├── e2_speciesnet.yaml
│   ├── e3_miewid.yaml
│   ├── e3_megadescriptor.yaml
│   ├── e3_osnet.yaml
│   ├── e3_ppgnet_cat.yaml          # quando implementarmos
│   └── pipeline_full.yaml
│
├── data/                           # gerenciado por DVC, NÃO entra no git
│   ├── raw/                        # datasets baixados sem modificar
│   │   ├── oxford_iiit_pet/
│   │   ├── catflw/
│   │   ├── petface/                # só após aprovação do Google Form
│   │   ├── cat_individuals/
│   │   ├── hellostreetcat/
│   │   └── cat_dataset_crawford/
│   ├── interim/                    # após filtros básicos (split, deduplicação)
│   ├── processed/                  # crops normalizados, splits train/val/test
│   └── pilot_videos/               # vídeos representativos para B5 Parte 3
│
├── models/                         # pesos baixados, gerenciados por DVC
│   ├── yolo11n.pt
│   ├── megadetector_v6.pt
│   ├── speciesnet.tflite
│   ├── miewid_msv3/
│   ├── megadescriptor_l_384/
│   └── osnet_x1_0/
│
├── src/tcc_gatosdoc2/              # código fonte importável
│   ├── __init__.py
│   ├── data/                       # download e preparação
│   │   ├── download.py
│   │   ├── preprocess.py
│   │   └── splits.py
│   ├── pipeline/                   # estágios E0-E4
│   │   ├── e0_ingestion.py
│   │   ├── e1_detection.py
│   │   ├── e2_species.py
│   │   ├── e3_reid.py
│   │   └── e4_indicators.py
│   ├── models/                     # wrappers padronizados
│   │   ├── base.py
│   │   ├── yolo11.py
│   │   ├── megadetector.py
│   │   ├── speciesnet.py
│   │   ├── miewid.py
│   │   ├── megadescriptor.py
│   │   ├── ppgnet_cat.py
│   │   └── osnet.py
│   ├── db/                         # schema Camtrap-DP + extensões (B4.4)
│   │   ├── schema.sql
│   │   ├── migrations/
│   │   └── camtrap_dp_export.py
│   ├── metrics/                    # cálculo de mAP, Rank-K, BAKS/BAUS
│   │   ├── detection.py
│   │   ├── classification.py
│   │   └── reid.py
│   └── viz/                        # geração de gráficos para a monografia
│       ├── benchmarks.py
│       ├── confusion.py
│       └── cmc_curves.py
│
├── scripts/                        # entrypoints CLI
│   ├── download_datasets.py
│   ├── download_models.py
│   ├── run_benchmark_e1.py
│   ├── run_benchmark_e2.py
│   ├── run_benchmark_e3.py
│   ├── run_pilot.py
│   └── generate_thesis_figures.py  # gera todos os gráficos do TCC
│
├── notebooks/                      # análises exploratórias e relatórios
│   ├── 01_data_exploration.ipynb
│   ├── 02_e1_detection_results.ipynb
│   ├── 03_e2_species_results.ipynb
│   ├── 04_e3_reid_results.ipynb
│   └── 05_pilot_analysis.ipynb
│
├── results/                        # outputs versionados (CSV, JSON, PNG)
│   ├── e1/
│   ├── e2/
│   ├── e3/
│   ├── pilot/
│   └── figures/                    # PNGs prontos para a monografia
│
├── tests/                          # pytest
│   ├── test_pipeline.py
│   └── test_metrics.py
│
└── docs/                           # documentação técnica
    ├── hardware_setup.md           # output do B5.1.1
    ├── datasets_inventory.md
    ├── models_inventory.md
    └── reproducibility.md
```

### B5.2.2 — Comandos `make` para automação

Criar `Makefile` na raiz:

```makefile
.PHONY: install download-datasets download-models benchmark-e1 benchmark-e2 benchmark-e3 pilot figures clean

install:
	uv sync

download-datasets:
	uv run python scripts/download_datasets.py --all

download-models:
	uv run python scripts/download_models.py --all

benchmark-e1:
	uv run python scripts/run_benchmark_e1.py --config configs/e1_yolo11n.yaml
	uv run python scripts/run_benchmark_e1.py --config configs/e1_megadetector.yaml

benchmark-e2:
	uv run python scripts/run_benchmark_e2.py --config configs/e2_speciesnet.yaml

benchmark-e3:
	uv run python scripts/run_benchmark_e3.py --config configs/e3_miewid.yaml
	uv run python scripts/run_benchmark_e3.py --config configs/e3_megadescriptor.yaml
	uv run python scripts/run_benchmark_e3.py --config configs/e3_osnet.yaml

pilot:
	uv run python scripts/run_pilot.py --videos data/pilot_videos --output results/pilot

figures:
	uv run python scripts/generate_thesis_figures.py --out results/figures

all: download-datasets download-models benchmark-e1 benchmark-e2 benchmark-e3 pilot figures

clean:
	rm -rf results/*/cache/
```

Uso esperado depois de tudo configurado:

```bash
make install            # ambiente
make download-datasets  # ~ 2-4 h (depende da internet)
make download-models    # ~ 30 min
make benchmark-e1       # ~ 2-4 h no i7
make benchmark-e2       # ~ 1-2 h
make benchmark-e3       # ~ 4-8 h (4 modelos)
make pilot              # ~ 1-2 h
make figures            # ~ 5 min — gera PNGs prontos para o LaTeX
```

### B5.2.3 — Inicializar o repositório

```bash
cd ~/tcc_gatosdoc2

# Git
git init
git lfs install

# DVC (para data/ e models/ — não cabem no git)
uv run dvc init
echo "data/" >> .gitignore
echo "models/" >> .gitignore
echo "results/" >> .gitignore
echo ".env" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".mlflow/" >> .gitignore

# Primeiro commit
git add .
git commit -m "Inicialização do repositório TCC Gatosdoc2"

# Criar repo no GitHub e empurrar
# (depois de criar em github.com/<seu_usuario>/tcc_gatosdoc2)
git remote add origin git@github.com:<seu_usuario>/tcc_gatosdoc2.git
git branch -M main
git push -u origin main
```

---

## B5.3 — Datasets: download, licenças, organização

Os 6 datasets do projeto base (PDF Sec. 7.1) foram catalogados em A1.6. Aqui detalho o **procedimento operacional** para cada um — comando, licença, organização das pastas, e como cada um será usado nos estágios E1, E2, E3.

### B5.3.1 — Tabela-síntese

| Dataset | Tamanho | Fonte | Licença | Estágio onde será usado | Acesso |
|---|---|---|---|---|---|
| **Oxford-IIIT Pet** | 7.349 imagens | Univ. Oxford | CC BY-SA 4.0 | E1 (detecção de gato) | Direto |
| **CatFLW** | 2.079 imagens + 48 landmarks | Hadar Shrem-Tov et al. | CC BY 4.0 | E2.6 (qualidade de pose) | Kaggle/GitHub |
| **PetFace (subset cat)** | ~14.000 imagens, 5.000+ IDs | Mapooon (ECCV 2024) | Pesquisa, via Google Form | E3 (Re-ID) | Google Form |
| **Cat Individual Images** | ~10.000 imagens, ~500 IDs | timost1234 (Kaggle) | CC0 | E3 (Re-ID) | Kaggle |
| **HelloStreetCat Individuals** | ~6.000 imagens, ~50 IDs | Akbar 2025 release | Pesquisa | E3 (Re-ID, "in-the-wild") | Hugging Face |
| **Cat Dataset (Crawford)** | 9.993 imagens, landmarks | Crawford (2018, Kaggle) | CC0 | E1 (detecção, complementar) | Kaggle |

### B5.3.2 — Script unificado de download

Crie `scripts/download_datasets.py` com este conteúdo:

```python
"""Download incremental dos 6 datasets do TCC.

Uso:
    uv run python scripts/download_datasets.py --dataset oxford_iiit_pet
    uv run python scripts/download_datasets.py --all
"""
import argparse
from pathlib import Path
import subprocess
import sys

DATA_ROOT = Path("data/raw")


def download_oxford_iiit_pet() -> None:
    target = DATA_ROOT / "oxford_iiit_pet"
    target.mkdir(parents=True, exist_ok=True)
    # via torchvision API — já cacheia local
    cmd = [
        "python", "-c",
        f"from torchvision.datasets import OxfordIIITPet; "
        f"OxfordIIITPet(root='{target}', download=True, split='trainval'); "
        f"OxfordIIITPet(root='{target}', download=True, split='test')"
    ]
    subprocess.run(cmd, check=True)
    print(f"[OK] Oxford-IIIT Pet baixado em {target}")


def download_catflw() -> None:
    target = DATA_ROOT / "catflw"
    target.mkdir(parents=True, exist_ok=True)
    # Kaggle CLI (configurado em B5.1.4)
    subprocess.run(
        ["kaggle", "datasets", "download",
         "-d", "george7777/catflw-cat-facial-landmarks-in-the-wild",
         "-p", str(target), "--unzip"],
        check=True,
    )
    print(f"[OK] CatFLW baixado em {target}")


def download_cat_individuals() -> None:
    target = DATA_ROOT / "cat_individuals"
    target.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["kaggle", "datasets", "download",
         "-d", "timost1234/cat-individuals",
         "-p", str(target), "--unzip"],
        check=True,
    )
    print(f"[OK] Cat Individual Images baixado em {target}")


def download_cat_crawford() -> None:
    target = DATA_ROOT / "cat_dataset_crawford"
    target.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["kaggle", "datasets", "download",
         "-d", "crawford/cat-dataset",
         "-p", str(target), "--unzip"],
        check=True,
    )
    print(f"[OK] Cat Dataset (Crawford) baixado em {target}")


def download_hellostreetcat() -> None:
    target = DATA_ROOT / "hellostreetcat"
    target.mkdir(parents=True, exist_ok=True)
    # Via Hugging Face Hub
    from huggingface_hub import snapshot_download
    snapshot_download(
        repo_id="rkakbar/HelloStreetCat",  # confirmar slug oficial no release de Akbar 2025
        repo_type="dataset",
        local_dir=str(target),
        local_dir_use_symlinks=False,
    )
    print(f"[OK] HelloStreetCat baixado em {target}")


def download_petface() -> None:
    """PetFace exige Google Form. Esta função apenas valida que a pasta exista."""
    target = DATA_ROOT / "petface"
    if not target.exists() or not any(target.iterdir()):
        print(
            "[ATENÇÃO] PetFace precisa ser solicitado em:\n"
            "  https://dahlian00.github.io/PetFacePage/\n"
            "Preencha o Google Form e aguarde aprovação por e-mail.\n"
            f"Quando receber o link, baixe e descompacte em: {target}\n"
            "Estrutura esperada:\n"
            "  data/raw/petface/images/cat/000000/00.png\n"
            "  data/raw/petface/split/cat/{train,val,test}.csv\n"
            "  data/raw/petface/annotations/cat.csv"
        )
        return
    print(f"[OK] PetFace encontrado em {target}")


REGISTRY = {
    "oxford_iiit_pet": download_oxford_iiit_pet,
    "catflw": download_catflw,
    "cat_individuals": download_cat_individuals,
    "cat_crawford": download_cat_crawford,
    "hellostreetcat": download_hellostreetcat,
    "petface": download_petface,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=list(REGISTRY.keys()))
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all:
        for name, fn in REGISTRY.items():
            print(f"\n=== {name} ===")
            try:
                fn()
            except Exception as e:
                print(f"[ERRO] {name}: {e}", file=sys.stderr)
    elif args.dataset:
        REGISTRY[args.dataset]()
    else:
        parser.error("Use --dataset NOME ou --all")


if __name__ == "__main__":
    main()
```

Execução:

```bash
# Um por um (recomendado na primeira vez para detectar erros)
uv run python scripts/download_datasets.py --dataset oxford_iiit_pet
uv run python scripts/download_datasets.py --dataset catflw
uv run python scripts/download_datasets.py --dataset cat_individuals
uv run python scripts/download_datasets.py --dataset cat_crawford
uv run python scripts/download_datasets.py --dataset hellostreetcat
uv run python scripts/download_datasets.py --dataset petface  # solicitar Form ANTES

# Ou tudo de uma vez (depois de já ter feito 1x)
make download-datasets
```

**Importante para o Felipi:** **solicite o PetFace HOJE** (preencha o Google Form em [dahlian00.github.io/PetFacePage](https://dahlian00.github.io/PetFacePage/)). Aprovação demora dias a uma semana. Enquanto espera, baixe os outros 5.

### B5.3.3 — Versionamento dos datasets com DVC

Depois de baixar, registre no DVC:

```bash
cd ~/tcc_gatosdoc2

# Cada dataset vira um "artifact" rastreado
uv run dvc add data/raw/oxford_iiit_pet
uv run dvc add data/raw/catflw
uv run dvc add data/raw/cat_individuals
uv run dvc add data/raw/cat_dataset_crawford
uv run dvc add data/raw/hellostreetcat

# Commit dos .dvc files (são pequenos, vão pro git)
git add data/raw/*.dvc data/.gitignore
git commit -m "Track raw datasets with DVC"

# (Opcional, recomendado) — remote DVC em Google Drive ou S3
# para backup e compartilhamento com o orientador
uv run dvc remote add -d gdrive_remote gdrive://<folder_id>
uv run dvc push
```

### B5.3.4 — Inventário dos datasets — `docs/datasets_inventory.md`

Após download, gere automaticamente o inventário (este arquivo vira o **Apêndice B** da monografia):

```bash
cat > scripts/inventory_datasets.py << 'PY'
"""Gera docs/datasets_inventory.md com contagens e samples de cada dataset."""
from pathlib import Path
import json

DATASETS = {
    "Oxford-IIIT Pet": "data/raw/oxford_iiit_pet/oxford-iiit-pet",
    "CatFLW": "data/raw/catflw",
    "Cat Individual Images": "data/raw/cat_individuals",
    "Cat Dataset (Crawford)": "data/raw/cat_dataset_crawford",
    "HelloStreetCat": "data/raw/hellostreetcat",
    "PetFace (cat)": "data/raw/petface/images/cat",
}

lines = ["# Inventário de Datasets\n",
         "| Dataset | Diretório | # arquivos | Tamanho (MB) |",
         "|---|---|---|---|"]
for name, path in DATASETS.items():
    p = Path(path)
    if not p.exists():
        lines.append(f"| {name} | {path} | _não baixado_ | — |")
        continue
    files = list(p.rglob("*.*"))
    size_mb = sum(f.stat().st_size for f in files if f.is_file()) / 1e6
    lines.append(f"| {name} | `{path}` | {len(files):,} | {size_mb:,.1f} |")

Path("docs/datasets_inventory.md").write_text("\n".join(lines) + "\n")
print("Gerado: docs/datasets_inventory.md")
PY

uv run python scripts/inventory_datasets.py
cat docs/datasets_inventory.md
```

### B5.3.5 — Splits canônicos (train / val / test)

Para cada dataset, definimos splits **reproduzíveis** (seed fixa, gravados em CSV). Crie `src/tcc_gatosdoc2/data/splits.py` com função genérica:

```python
"""Geração de splits estratificados reproduzíveis."""
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

SEED = 42

def make_split_csv(
    image_paths: list[Path],
    labels: list[str],
    out_dir: Path,
    ratios: tuple[float, float, float] = (0.7, 0.15, 0.15),
) -> None:
    """Gera train.csv, val.csv, test.csv estratificados por label."""
    df = pd.DataFrame({"path": [str(p) for p in image_paths], "label": labels})
    train_val, test = train_test_split(
        df, test_size=ratios[2], stratify=df["label"], random_state=SEED
    )
    train, val = train_test_split(
        train_val,
        test_size=ratios[1] / (ratios[0] + ratios[1]),
        stratify=train_val["label"],
        random_state=SEED,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    train.to_csv(out_dir / "train.csv", index=False)
    val.to_csv(out_dir / "val.csv", index=False)
    test.to_csv(out_dir / "test.csv", index=False)
    print(f"Splits gerados em {out_dir}: train={len(train)} val={len(val)} test={len(test)}")
```

**Nota sobre PetFace:** já vem com `train.csv`, `val.txt`, `test.txt`, `reidentification.csv`, `verification.csv` definidos pelos autores. **Use os splits oficiais**, não regenere — isto garante comparação direta com o paper original.

### B5.3.6 — Mapeamento dataset → estágio (referência para B5 Parte 2)

```
┌──────────────────────────┬──────────┬──────────┬──────────┐
│  Dataset                 │   E1     │   E2     │   E3     │
│                          │ detecção │ espécie  │  Re-ID   │
├──────────────────────────┼──────────┼──────────┼──────────┤
│ Oxford-IIIT Pet          │    ✓     │   ✓ *    │          │
│ CatFLW                   │    ✓     │          │   △ **   │
│ Cat Dataset (Crawford)   │    ✓     │          │          │
│ Cat Individual Images    │          │          │    ✓     │
│ HelloStreetCat           │          │          │    ✓     │
│ PetFace (cat)            │          │          │    ✓     │
└──────────────────────────┴──────────┴──────────┴──────────┘

* Oxford-IIIT tem 37 raças, usado em E2 só para validar classificação fina
  (sub-tarefa do projeto, não core do TCC)
** CatFLW tem landmarks; usado para enriquecer crops do E2.6 (qualidade de pose)
   antes de mandar para E3
```

---

## B5.4 — Protocolo experimental geral

O protocolo abaixo é a **espinha dorsal científica** de B5. Quando virar texto na monografia, esta seção vira "3.X Metodologia de avaliação".

### B5.4.1 — Princípios de reprodutibilidade

Toda execução em B5 segue 5 princípios:

1. **Seeds fixas** — `random_state=42` em todo split, augmentation e shuffle.
2. **Versões pinadas** — `uv.lock` no git; modelos referenciados por hash do Hugging Face ou checksum SHA256.
3. **Configs YAML imutáveis** — cada experimento tem um YAML em `configs/`; ao mudar, criar nova versão (`e3_miewid_v2.yaml`), nunca sobrescrever.
4. **Outputs versionados** — todo output (CSV, PNG, JSON) é gravado em `results/<estágio>/<config_name>/<timestamp>/` e tracked por DVC.
5. **MLflow logging** — métricas, parâmetros e artefatos logados em `mlruns/`; o orientador pode abrir o MLflow UI e auditar.

### B5.4.2 — Hardware fixo durante experimentos

Toda execução B5 deve declarar no log:
- modelo da CPU,
- presença de GPU,
- versão do Python,
- versão de cada pacote-chave,
- carga do sistema (`uptime`, `free -h`).

Este bloco é gravado automaticamente pelo helper:

```python
# src/tcc_gatosdoc2/utils/runtime_log.py
import platform, psutil, torch, sys, subprocess
import json
from pathlib import Path
from datetime import datetime, timezone

def snapshot_runtime(out_dir: Path) -> dict:
    info = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "cpu": platform.processor() or platform.machine(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "mem_total_gb": psutil.virtual_memory().total / 1e9,
        "mem_available_gb": psutil.virtual_memory().available / 1e9,
        "torch_version": torch.__version__,
        "torch_cuda_available": torch.cuda.is_available(),
        "torch_cuda_device": (
            torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        ),
        "uname": platform.uname()._asdict(),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "runtime.json").write_text(json.dumps(info, indent=2))
    return info
```

Chamado no início de cada `run_benchmark_*.py`. Os JSONs viram **Apêndice C — Ambiente de execução** da monografia (com tabela auto-gerada).

### B5.4.3 — Estrutura de cada experimento

Cada experimento (E1, E2, E3) segue o mesmo molde:

```
1. CARREGAMENTO
   ├── Lê config YAML
   ├── Resolve dataset(s) → split de teste
   └── Carrega modelo(s) com versão pinada

2. INFERÊNCIA
   ├── Itera sobre o split de teste com tqdm
   ├── Mede tempo por imagem (latência) e total
   ├── Mede uso de memória de pico
   └── Salva predictions.csv com: image_path | pred | confidence | latency_ms

3. AVALIAÇÃO
   ├── Calcula métricas específicas do estágio
   │   (E1: mAP/Precision/Recall; E2: Top-1/Top-5; E3: Rank-K/mAP/BAKS/BAUS)
   ├── Salva metrics.json
   └── Loga no MLflow

4. VISUALIZAÇÃO
   ├── Gera gráficos do experimento → results/<exp>/figures/
   └── Gera tabela summary.md (vai virar tabela LaTeX)
```

Este molde é implementado em `src/tcc_gatosdoc2/pipeline/_runner.py` e reusado por todos os scripts `run_benchmark_*.py` — detalhes em B5 Parte 2.

### B5.4.4 — O que será comparado, exatamente

| Estágio | Modelos comparados | Datasets de teste | Métrica primária | Decisão derivada |
|---|---|---|---|---|
| **E1 — detecção** | YOLO11n vs. MegaDetector v6 | Oxford-IIIT Pet (split test), Cat Dataset Crawford, CatFLW | mAP@0.5, latência ms/img | Qual modelo lidera, em que regime usar cascata |
| **E2 — espécie** | SpeciesNet (Google) | Oxford-IIIT (sub-tarefa raças), subset com fauna brasileira | Top-1 accuracy para "cat", Top-1 para outras espécies | Confirmação de que SpeciesNet ≥ 0.95 para `Felis catus` |
| **E3 — Re-ID** | MiewID-msv3, MegaDescriptor-L-384, PPGNet-Cat (se implementação disponível), OSNet-x1.0 | Cat Individual Images, HelloStreetCat, PetFace-cat | Rank-1, mAP, BAKS/BAUS (Akbar 2025) | Qual modelo vira **primário** no sistema; quais ficam baseline |

### B5.4.5 — Cronograma realista para rodar B5 no PC do Felipi

Estimativas considerando i7 sem GPU dedicada. Se houver GPU dedicada simples (RTX 3050+), divida tudo por 3-5.

| Atividade | Tempo estimado | Quando |
|---|---|---|
| Setup ambiente (B5.1) | 1 dia | Dia 1 |
| Download de 5 datasets (B5.3) | 4-6 h ativos | Dia 1-2 |
| Solicitar PetFace + esperar aprovação | 1-7 dias | Dia 1 (paralelo) |
| Splits e inventário | 2 h | Dia 2 |
| Bench E1 (2 modelos × 3 datasets) | 6-8 h CPU | Dia 3 |
| Bench E2 (SpeciesNet) | 2-3 h | Dia 4 |
| Bench E3 (4 modelos × 3 datasets) | 12-20 h CPU | Dia 4-6 |
| Piloto offline (vídeos) | 4-6 h | Dia 7 |
| Geração de gráficos para monografia | 1 dia | Dia 8 |
| Revisão e re-runs pontuais | 2-3 dias | Dia 9-11 |
| **TOTAL realista** | **~11 dias úteis** | — |

**Observação importante:** o E3 é o gargalo. Se o Felipi tiver acesso temporário a uma máquina com GPU (laboratório do ICMC), recomendo concentrar o E3 lá.

---

## Resumo executivo da Parte 1

| Bloco | Entregável | Status no fim desta parte |
|---|---|---|
| **B5.1** | Setup do PC + ambiente Python 3.11 + dependências + credenciais HF/Kaggle | Comandos prontos para colar |
| **B5.2** | Estrutura canônica de pastas + `Makefile` + inicialização do repositório | Repo template descrito |
| **B5.3** | Download de 6 datasets + DVC + inventário automático + splits canônicos | Script `download_datasets.py` completo |
| **B5.4** | Protocolo experimental geral + cronograma de 11 dias úteis | Definido |

**Próximo: B5 Parte 2** — implementação detalhada dos benchmarks (E1, E2, E3): wrappers de modelo, scripts `run_benchmark_*.py`, definição formal das métricas (mAP, Rank-K, BAKS/BAUS com fórmulas e código), formato exato das tabelas e gráficos que vão para a monografia.

---

## Fontes citadas nesta parte

- [Camtrap-DP 1.0.1 specification](https://camtrap-dp.tdwg.org/) (carryover de B4.4)
- [PetFace — Mapooon (ECCV 2024)](https://dahlian00.github.io/PetFacePage/)
- [PetFace GitHub repository](https://github.com/mapooon/PetFace)
- [CatFLW — Hugging Face papers](https://huggingface.co/papers/2305.04232)
- [CatFLW GitHub mirror — martvelge](https://github.com/martvelge/CatFLW)
- [Cat Individual Images — Kaggle (timost1234)](https://www.kaggle.com/datasets/timost1234/cat-individuals/data)
- [Cat Dataset Crawford — Kaggle](https://www.kaggle.com/datasets/crawford/cat-dataset)
- [Oxford-IIIT Pet — torchvision](https://pytorch.org/vision/stable/generated/torchvision.datasets.OxfordIIITPet.html)
- [uv — instalador Python da Astral](https://docs.astral.sh/uv/)
- [DVC — Data Version Control](https://dvc.org/doc)
- [Akbar et al., 2025 — PPGNet-Cat](https://link.springer.com/article/10.1007/s42979-024-03397-w) (carryover B4)
- Projeto base do TCC — `projeto_tcc.pdf` (Sec. 3.2, 7.1, 9)
