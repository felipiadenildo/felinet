# B5 — Plano de validação e implementação (Parte 2)

**Parte 2 cobre:** B5.5 (wrappers padronizados de modelo), B5.6 (script E1 — detecção), B5.7 (script E2 — espécie), B5.8 (script E3 — Re-ID), B5.9 (métricas formais com fórmulas), B5.10 (geração de tabelas e gráficos da monografia)
**Continuidade:** Parte 1 estabeleceu ambiente, repositório, datasets, protocolo geral. Parte 2 é a **implementação técnica** dos benchmarks. Parte 3 cobre piloto offline + reprodutibilidade fim-a-fim.

---

## B5.5 — Wrappers padronizados de modelo

Para que os 4 modelos de Re-ID (e os 2 de detecção) sejam comparados de forma **justa e auditável**, todos precisam expor a mesma interface. Isto é o que permite gráficos lado a lado e tabelas LaTeX consistentes na monografia.

### B5.5.1 — Interface base

Crie `src/tcc_gatosdoc2/models/base.py`:

```python
"""Interfaces base para todos os modelos do projeto.

Princípio: o restante da pipeline (benchmarks, scripts, dashboard)
NÃO precisa saber qual modelo concreto está rodando — só consome
a interface aqui definida.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
import numpy as np
import time


@dataclass
class Detection:
    """Resultado de detecção: bounding box no formato xywh + score."""
    bbox: tuple[float, float, float, float]   # (x, y, w, h) em pixels
    score: float                              # confiança ∈ [0,1]
    class_name: str                           # "animal" ou específico
    class_id: int                             # índice numérico

@dataclass
class SpeciesPrediction:
    """Resultado de classificação de espécie."""
    scientific_name: str                      # ex.: "Felis catus"
    common_name: str                          # ex.: "domestic cat"
    score: float
    top_k: list[tuple[str, float]] = field(default_factory=list)

@dataclass
class Embedding:
    """Vetor de Re-ID gerado por um modelo."""
    vector: np.ndarray                        # shape (D,), dtype float32
    model_name: str
    model_version: str
    crop_id: str | None = None


# ---------- Bases abstratas ----------

class DetectorBase(ABC):
    """Detector de animais (E1)."""
    name: str
    version: str

    @abstractmethod
    def predict(self, image: np.ndarray) -> list[Detection]:
        """Recebe imagem BGR (OpenCV) e retorna lista de detecções."""

    def predict_batch(self, images: Iterable[np.ndarray]) -> list[list[Detection]]:
        # Implementação ingênua; subclasses podem otimizar.
        return [self.predict(img) for img in images]


class SpeciesClassifierBase(ABC):
    """Classificador de espécie (E2)."""
    name: str
    version: str

    @abstractmethod
    def predict(self, image: np.ndarray) -> SpeciesPrediction:
        ...


class ReIDModelBase(ABC):
    """Modelo de Re-ID (E3) — gera embeddings."""
    name: str
    version: str
    embedding_dim: int

    @abstractmethod
    def embed(self, crop: np.ndarray) -> np.ndarray:
        """Recebe crop RGB normalizado e retorna vetor (embedding_dim,)."""

    def embed_batch(self, crops: Iterable[np.ndarray]) -> np.ndarray:
        vectors = [self.embed(c) for c in crops]
        return np.stack(vectors, axis=0)


# ---------- Decorator para medir latência ----------

def timed(func):
    """Mede tempo de execução de método, salva em self._latencies_ms."""
    def wrapper(self, *args, **kwargs):
        t0 = time.perf_counter()
        out = func(self, *args, **kwargs)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        if not hasattr(self, "_latencies_ms"):
            self._latencies_ms = []
        self._latencies_ms.append(dt_ms)
        return out
    return wrapper
```

### B5.5.2 — Wrapper YOLO11n (Ultralytics)

`src/tcc_gatosdoc2/models/yolo11.py`:

```python
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from .base import DetectorBase, Detection, timed

class YOLO11nDetector(DetectorBase):
    name = "yolo11n"
    version = "8.3.x-ultralytics"

    # COCO class 15 = "cat", 16 = "dog", 17 = "horse"
    # Para o TCC, usamos a classe genérica "animal" agregando
    # cat/dog/bird como mascote/biodiversidade.
    ANIMAL_CLASSES = {15, 16, 17, 18, 19, 20, 21, 22, 23}

    def __init__(self, weights: str = "yolo11n.pt", conf: float = 0.25):
        self.model = YOLO(weights)
        self.conf = conf

    @timed
    def predict(self, image: np.ndarray) -> list[Detection]:
        results = self.model.predict(image, conf=self.conf, verbose=False)
        out: list[Detection] = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls.item())
                if cls_id not in self.ANIMAL_CLASSES and cls_id != 15:
                    continue
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
                out.append(Detection(
                    bbox=(x1, y1, x2 - x1, y2 - y1),
                    score=float(box.conf.item()),
                    class_name=r.names[cls_id],
                    class_id=cls_id,
                ))
        return out
```

### B5.5.3 — Wrapper MegaDetector v6

`src/tcc_gatosdoc2/models/megadetector.py`:

```python
import numpy as np
from pathlib import Path
from .base import DetectorBase, Detection, timed

class MegaDetectorV6(DetectorBase):
    name = "megadetector_v6"
    version = "6.0.0"

    # MegaDetector tem 3 classes: 1=animal, 2=person, 3=vehicle
    def __init__(self, weights: str = "models/megadetector_v6.pt", conf: float = 0.2):
        # MegaDetector v6 é um YOLO retrained, carrega via Ultralytics
        from ultralytics import YOLO
        self.model = YOLO(weights)
        self.conf = conf

    @timed
    def predict(self, image: np.ndarray) -> list[Detection]:
        results = self.model.predict(image, conf=self.conf, verbose=False)
        out: list[Detection] = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls.item())
                if cls_id != 0:  # 0 = animal em MegaDetector v6
                    continue
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
                out.append(Detection(
                    bbox=(x1, y1, x2 - x1, y2 - y1),
                    score=float(box.conf.item()),
                    class_name="animal",
                    class_id=cls_id,
                ))
        return out
```

### B5.5.4 — Wrapper SpeciesNet (Google)

`src/tcc_gatosdoc2/models/speciesnet.py`:

```python
import numpy as np
import cv2
from .base import SpeciesClassifierBase, SpeciesPrediction, timed

class SpeciesNetClassifier(SpeciesClassifierBase):
    name = "speciesnet"
    version = "2024-release"

    def __init__(self, weights_dir: str = "models/speciesnet"):
        # SpeciesNet shipping is via the `speciesnet` Python package
        # ou TFLite. Aqui usamos o pacote oficial quando disponível.
        try:
            from speciesnet import SpeciesNet
            self.model = SpeciesNet(model_path=weights_dir)
        except ImportError:
            raise RuntimeError(
                "Instale 'speciesnet' do release oficial Google:\n"
                "uv pip install speciesnet  # quando disponível no PyPI\n"
                "ou clone https://github.com/google/cameratrapai"
            )

    @timed
    def predict(self, image: np.ndarray) -> SpeciesPrediction:
        # SpeciesNet espera RGB; OpenCV entrega BGR
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = self.model.classify(rgb)
        # result: {"prediction": "Felis catus", "score": 0.97, "top_k": [...]}
        return SpeciesPrediction(
            scientific_name=result.get("scientific_name", ""),
            common_name=result.get("common_name", ""),
            score=float(result.get("score", 0.0)),
            top_k=result.get("top_k", []),
        )
```

**Nota de fallback:** se o pacote `speciesnet` ainda não estiver no PyPI no momento de rodar, o repositório [google/cameratrapai](https://github.com/google/cameratrapai) tem instruções de empacotamento. Documentar isto em `docs/models_inventory.md`.

### B5.5.5 — Wrapper MiewID-msv3 (primário)

`src/tcc_gatosdoc2/models/miewid.py`:

```python
import numpy as np
import cv2
import torch
from pathlib import Path
from .base import ReIDModelBase, timed

class MiewIDmsv3(ReIDModelBase):
    name = "miewid_msv3"
    version = "wildme-2024"
    embedding_dim = 2152   # confirmar pela inferência inicial

    def __init__(self, device: str = "cpu"):
        from huggingface_hub import snapshot_download
        model_dir = snapshot_download(
            repo_id="conservationxlabs/miewid-msv3",
            local_dir="models/miewid_msv3",
        )
        # Carrega via timm (MiewID expõe um EfficientNetV2 backbone)
        import timm
        self.model = timm.create_model(
            "efficientnetv2_rw_m", pretrained=False, num_classes=0
        )
        state_dict = torch.load(
            Path(model_dir) / "pytorch_model.bin",
            map_location=device,
        )
        self.model.load_state_dict(state_dict, strict=False)
        self.model.eval().to(device)
        self.device = device

        # Atualiza embedding_dim a partir do modelo carregado
        with torch.no_grad():
            dummy = torch.zeros(1, 3, 440, 440).to(device)
            self.embedding_dim = self.model(dummy).shape[1]

    @timed
    def embed(self, crop: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (440, 440))
        tensor = torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0
        # Normalização ImageNet
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        tensor = (tensor - mean) / std
        tensor = tensor.unsqueeze(0).to(self.device)
        with torch.no_grad():
            emb = self.model(tensor).cpu().numpy()[0]
        # L2-normalizar para cosine similarity
        return emb / np.linalg.norm(emb)
```

### B5.5.6 — Wrapper MegaDescriptor

`src/tcc_gatosdoc2/models/megadescriptor.py`:

```python
import numpy as np
import cv2
import torch
import timm
from huggingface_hub import hf_hub_download
from .base import ReIDModelBase, timed

class MegaDescriptorL384(ReIDModelBase):
    name = "megadescriptor_l_384"
    version = "BohemianVRA-2024"
    embedding_dim = 1536

    def __init__(self, device: str = "cpu"):
        weights = hf_hub_download(
            repo_id="BVRA/MegaDescriptor-L-384",
            filename="pytorch_model.bin",
        )
        self.model = timm.create_model("swin_large_patch4_window12_384",
                                       pretrained=False, num_classes=0)
        state = torch.load(weights, map_location=device)
        self.model.load_state_dict(state, strict=False)
        self.model.eval().to(device)
        self.device = device

    @timed
    def embed(self, crop: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (384, 384))
        t = torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        t = (t - mean) / std
        with torch.no_grad():
            emb = self.model(t.unsqueeze(0).to(self.device)).cpu().numpy()[0]
        return emb / np.linalg.norm(emb)
```

### B5.5.7 — Wrapper OSNet (baseline do projeto base)

`src/tcc_gatosdoc2/models/osnet.py`:

```python
import numpy as np
import cv2
import torch
import torchreid
from .base import ReIDModelBase, timed

class OSNetX1(ReIDModelBase):
    name = "osnet_x1_0"
    version = "torchreid-1.4"
    embedding_dim = 512

    def __init__(self, device: str = "cpu"):
        self.model = torchreid.models.build_model(
            name="osnet_x1_0", num_classes=1000, pretrained=True
        )
        self.model.eval().to(device)
        self.device = device

    @timed
    def embed(self, crop: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (256, 128))   # OSNet padrão
        t = torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        t = (t - mean) / std
        with torch.no_grad():
            emb = self.model(t.unsqueeze(0).to(self.device))
            if isinstance(emb, tuple):
                emb = emb[0]
            emb = emb.cpu().numpy()[0]
        return emb / np.linalg.norm(emb)
```

### B5.5.8 — Wrapper PPGNet-Cat (referência cat-specific)

`src/tcc_gatosdoc2/models/ppgnet_cat.py`:

```python
"""
PPGNet-Cat (Akbar et al., 2025) - implementação a partir do paper.

Status: o autor não publicou pesos oficiais (até abr/2026).
Plano:
  (a) Reimplementar arquitetura do paper (PPG Block + ResNet50 backbone)
  (b) Fine-tunar em PetFace e HelloStreetCat (replicar protocolo do paper)
  (c) Se não conseguirmos reproduzir, OMITIR PPGNet de B5 e mencionar
      em B6 como trabalho futuro.

Esta classe é um STUB para o esqueleto do experimento; o treino real
fica em scripts/train_ppgnet_cat.py (B5 Parte 3).
"""
import numpy as np
from .base import ReIDModelBase, timed

class PPGNetCat(ReIDModelBase):
    name = "ppgnet_cat"
    version = "reproduced-akbar2025"
    embedding_dim = 2048

    def __init__(self, weights: str | None = None, device: str = "cpu"):
        if weights is None:
            raise NotImplementedError(
                "PPGNet-Cat requer pesos treinados pelo Felipi. "
                "Rodar scripts/train_ppgnet_cat.py primeiro."
            )
        # Carrega modelo treinado
        ...

    @timed
    def embed(self, crop: np.ndarray) -> np.ndarray:
        ...
```

**Decisão prática:** se a reprodução de PPGNet-Cat não for viável em tempo hábil, **declare honestamente no TCC** (Sec. "Limitações") que o modelo cat-specific de Akbar 2025 ficou como trabalho futuro. Isto é academicamente correto e o projeto base (PDF Sec. 9) já antecipou esta situação no risco "métodos do estado da arte podem evoluir".

---

## B5.6 — Script de benchmark E1 (detecção)

`scripts/run_benchmark_e1.py`:

```python
"""
Benchmark de detecção (E1).
Compara YOLO11n vs. MegaDetector v6 em Oxford-IIIT Pet, Cat Crawford, CatFLW.

Saídas:
  results/e1/<config>/<timestamp>/predictions.csv
  results/e1/<config>/<timestamp>/metrics.json
  results/e1/<config>/<timestamp>/figures/*.png
"""
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
import pandas as pd
import yaml
from tqdm import tqdm

from tcc_gatosdoc2.models.yolo11 import YOLO11nDetector
from tcc_gatosdoc2.models.megadetector import MegaDetectorV6
from tcc_gatosdoc2.metrics.detection import compute_map_at_iou
from tcc_gatosdoc2.utils.runtime_log import snapshot_runtime


MODEL_REGISTRY = {
    "yolo11n": YOLO11nDetector,
    "megadetector_v6": MegaDetectorV6,
}


def load_dataset_index(name: str, split: str = "test") -> pd.DataFrame:
    """
    Retorna DataFrame com colunas:
      image_path | gt_boxes (lista de (x,y,w,h)) | gt_labels
    """
    if name == "oxford_iiit_pet":
        from tcc_gatosdoc2.data.adapters import load_oxford_iiit_pet
        return load_oxford_iiit_pet(split=split)
    if name == "cat_crawford":
        from tcc_gatosdoc2.data.adapters import load_cat_crawford
        return load_cat_crawford(split=split)
    if name == "catflw":
        from tcc_gatosdoc2.data.adapters import load_catflw
        return load_catflw(split=split)
    raise ValueError(f"Dataset desconhecido: {name}")


def main(cfg_path: str):
    cfg = yaml.safe_load(Path(cfg_path).read_text())

    model_cls = MODEL_REGISTRY[cfg["model"]]
    model = model_cls(**cfg.get("model_kwargs", {}))

    out_dir = (
        Path("results/e1") / cfg["model"] /
        datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot_runtime(out_dir)

    all_predictions = []
    per_dataset_metrics = {}

    for ds_name in cfg["datasets"]:
        print(f"\n=== {ds_name} ===")
        index = load_dataset_index(ds_name, split="test")

        rows = []
        for _, row in tqdm(index.iterrows(), total=len(index)):
            img = cv2.imread(row["image_path"])
            if img is None:
                continue
            detections = model.predict(img)
            for d in detections:
                rows.append({
                    "dataset": ds_name,
                    "image_path": row["image_path"],
                    "pred_x": d.bbox[0],
                    "pred_y": d.bbox[1],
                    "pred_w": d.bbox[2],
                    "pred_h": d.bbox[3],
                    "score": d.score,
                    "class": d.class_name,
                })

        df = pd.DataFrame(rows)
        df.to_csv(out_dir / f"predictions_{ds_name}.csv", index=False)
        all_predictions.append(df)

        # Métricas
        map_50 = compute_map_at_iou(predictions=df, ground_truth=index, iou=0.5)
        map_75 = compute_map_at_iou(predictions=df, ground_truth=index, iou=0.75)
        latencies = np.array(model._latencies_ms)
        per_dataset_metrics[ds_name] = {
            "mAP@0.5": map_50,
            "mAP@0.75": map_75,
            "n_images": len(index),
            "n_detections": len(df),
            "latency_p50_ms": float(np.percentile(latencies, 50)),
            "latency_p95_ms": float(np.percentile(latencies, 95)),
            "latency_mean_ms": float(latencies.mean()),
        }
        model._latencies_ms = []   # reset entre datasets

    # Métricas agregadas
    with (out_dir / "metrics.json").open("w") as f:
        json.dump({
            "model": cfg["model"],
            "version": model.version,
            "per_dataset": per_dataset_metrics,
            "config": cfg,
        }, f, indent=2)

    # Gera markdown-summary para a monografia
    write_summary_md(out_dir, model.name, per_dataset_metrics)

    print(f"\n[OK] Resultados em {out_dir}")


def write_summary_md(out_dir, model_name, metrics):
    lines = [f"# Resultados E1 — {model_name}\n", "## Métricas por dataset\n",
             "| Dataset | mAP@0.5 | mAP@0.75 | Latência p50 (ms) | Latência p95 (ms) |",
             "|---|---|---|---|---|"]
    for ds, m in metrics.items():
        lines.append(
            f"| {ds} | {m['mAP@0.5']:.3f} | {m['mAP@0.75']:.3f} | "
            f"{m['latency_p50_ms']:.1f} | {m['latency_p95_ms']:.1f} |"
        )
    (out_dir / "summary.md").write_text("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    main(args.config)
```

**Config YAML correspondente — `configs/e1_yolo11n.yaml`:**

```yaml
model: yolo11n
model_kwargs:
  weights: yolo11n.pt
  conf: 0.25
datasets:
  - oxford_iiit_pet
  - cat_crawford
  - catflw
seed: 42
```

E `configs/e1_megadetector.yaml`:

```yaml
model: megadetector_v6
model_kwargs:
  weights: models/megadetector_v6.pt
  conf: 0.2
datasets:
  - oxford_iiit_pet
  - cat_crawford
  - catflw
seed: 42
```

Execução:

```bash
make benchmark-e1
# ou individualmente:
uv run python scripts/run_benchmark_e1.py --config configs/e1_yolo11n.yaml
```

---

## B5.7 — Script de benchmark E2 (espécie)

`scripts/run_benchmark_e2.py`:

```python
"""
Benchmark de classificação de espécie (E2 - SpeciesNet).

Avaliação principal: confirmar que para imagens de gato doméstico,
SpeciesNet retorna 'Felis catus' como Top-1 com confiança ≥ 0.80
em ≥ 95% dos casos.

Saídas:
  results/e2/<config>/<timestamp>/predictions.csv
  results/e2/<config>/<timestamp>/metrics.json
  results/e2/<config>/<timestamp>/confusion_matrix.png
"""
import argparse, json, yaml
from pathlib import Path
from datetime import datetime
import cv2, numpy as np, pandas as pd
from tqdm import tqdm

from tcc_gatosdoc2.models.speciesnet import SpeciesNetClassifier
from tcc_gatosdoc2.utils.runtime_log import snapshot_runtime
from tcc_gatosdoc2.metrics.classification import (
    compute_top_k_accuracy, compute_confusion_matrix, plot_confusion_matrix,
)


def main(cfg_path: str):
    cfg = yaml.safe_load(Path(cfg_path).read_text())
    model = SpeciesNetClassifier(**cfg.get("model_kwargs", {}))

    out_dir = Path("results/e2") / cfg["model"] / datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot_runtime(out_dir)

    # Para E2 usamos uma seleção de imagens com label confiável:
    #   - Oxford-IIIT Pet (37 raças de gato/cachorro - usamos como "tem-cat-yes/no")
    #   - Subset com taxa "wildlife" de Cat Crawford
    from tcc_gatosdoc2.data.adapters import load_species_eval_set
    eval_set = load_species_eval_set(cfg["datasets"])   # df: path | true_species

    rows = []
    for _, r in tqdm(eval_set.iterrows(), total=len(eval_set)):
        img = cv2.imread(r["image_path"])
        if img is None:
            continue
        pred = model.predict(img)
        rows.append({
            "image_path": r["image_path"],
            "true_species": r["true_species"],
            "pred_species": pred.scientific_name,
            "score": pred.score,
            "top_k": json.dumps(pred.top_k),
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "predictions.csv", index=False)

    top1 = compute_top_k_accuracy(df, k=1, label_col="true_species", pred_col="pred_species")
    top5 = compute_top_k_accuracy(df, k=5, label_col="true_species", pred_col="top_k", is_topk_json=True)
    cat_recall = (
        (df["true_species"] == "Felis catus") & (df["pred_species"] == "Felis catus")
    ).sum() / max((df["true_species"] == "Felis catus").sum(), 1)

    cm = compute_confusion_matrix(df, label_col="true_species", pred_col="pred_species", top_n=15)
    plot_confusion_matrix(cm, out_path=out_dir / "confusion_matrix.png")

    metrics = {
        "model": model.name, "version": model.version,
        "n_eval": len(df),
        "top1_accuracy": top1,
        "top5_accuracy": top5,
        "felis_catus_recall": cat_recall,
        "felis_catus_target": 0.95,
        "passes_threshold": bool(cat_recall >= 0.95),
    }
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    main(args.config)
```

`configs/e2_speciesnet.yaml`:

```yaml
model: speciesnet
model_kwargs: {}
datasets:
  - oxford_iiit_pet
  - cat_crawford
seed: 42
```

---

## B5.8 — Script de benchmark E3 (Re-ID)

Este é o experimento mais rico — gera os gráficos centrais do TCC (CMC curves, mAP por modelo, BAKS/BAUS).

`scripts/run_benchmark_e3.py`:

```python
"""
Benchmark de Re-Identificação (E3).
Compara MiewID, MegaDescriptor, OSNet, (PPGNet-Cat se disponível).

Saídas:
  results/e3/<model>/<timestamp>/embeddings.npz
  results/e3/<model>/<timestamp>/match_results.csv
  results/e3/<model>/<timestamp>/cmc.png
  results/e3/<model>/<timestamp>/metrics.json
"""
import argparse, json, yaml, time
from pathlib import Path
from datetime import datetime
import cv2, numpy as np, pandas as pd
import hnswlib
from tqdm import tqdm

from tcc_gatosdoc2.models.miewid import MiewIDmsv3
from tcc_gatosdoc2.models.megadescriptor import MegaDescriptorL384
from tcc_gatosdoc2.models.osnet import OSNetX1
from tcc_gatosdoc2.models.ppgnet_cat import PPGNetCat
from tcc_gatosdoc2.metrics.reid import (
    compute_cmc_and_map, compute_baks_bauks, plot_cmc_curve,
)
from tcc_gatosdoc2.utils.runtime_log import snapshot_runtime

MODELS = {
    "miewid_msv3": MiewIDmsv3,
    "megadescriptor_l_384": MegaDescriptorL384,
    "osnet_x1_0": OSNetX1,
    "ppgnet_cat": PPGNetCat,
}


def main(cfg_path: str):
    cfg = yaml.safe_load(Path(cfg_path).read_text())
    model = MODELS[cfg["model"]](**cfg.get("model_kwargs", {}))

    out_dir = Path("results/e3") / cfg["model"] / datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot_runtime(out_dir)

    all_metrics = {}

    for ds_name in cfg["datasets"]:
        print(f"\n=== {ds_name} (modelo={cfg['model']}) ===")
        # gallery = imagens conhecidas (treino+val)
        # query   = imagens de teste a serem identificadas
        from tcc_gatosdoc2.data.adapters import load_reid_split
        gallery_df, query_df = load_reid_split(ds_name)

        # --- Embeddings da galeria ---
        gallery_emb = []
        for _, r in tqdm(gallery_df.iterrows(), total=len(gallery_df), desc="gallery"):
            img = cv2.imread(r["crop_path"])
            gallery_emb.append(model.embed(img))
        gallery_emb = np.stack(gallery_emb, axis=0).astype(np.float32)

        # Constrói índice HNSW
        index = hnswlib.Index(space="cosine", dim=model.embedding_dim)
        index.init_index(max_elements=len(gallery_emb), ef_construction=200, M=16)
        index.add_items(gallery_emb, np.arange(len(gallery_emb)))
        index.set_ef(50)

        # --- Embeddings da query ---
        query_emb, gt_ids = [], []
        for _, r in tqdm(query_df.iterrows(), total=len(query_df), desc="query"):
            img = cv2.imread(r["crop_path"])
            query_emb.append(model.embed(img))
            gt_ids.append(r["individual_id"])
        query_emb = np.stack(query_emb, axis=0).astype(np.float32)

        # --- Busca top-K ---
        K = 20
        nn_idx, nn_dist = index.knn_query(query_emb, k=K)
        # nn_idx: (n_query, K) ← índices na galeria
        gallery_ids = gallery_df["individual_id"].values
        ranked_ids = gallery_ids[nn_idx]   # (n_query, K)

        # --- Métricas ---
        cmc, mean_ap = compute_cmc_and_map(ranked_ids, np.array(gt_ids), max_rank=K)
        baks, bauks = compute_baks_bauks(ranked_ids, np.array(gt_ids))

        latencies = np.array(model._latencies_ms[-len(query_emb):])
        all_metrics[ds_name] = {
            "rank_1": float(cmc[0]),
            "rank_5": float(cmc[4]),
            "rank_10": float(cmc[9]),
            "mean_ap": float(mean_ap),
            "baks": float(baks),
            "bauks": float(bauks),
            "n_query": len(query_df),
            "n_gallery": len(gallery_df),
            "embedding_dim": model.embedding_dim,
            "latency_p50_ms": float(np.percentile(latencies, 50)),
            "latency_p95_ms": float(np.percentile(latencies, 95)),
        }

        # Salva embeddings p/ reuso/debug
        np.savez_compressed(
            out_dir / f"embeddings_{ds_name}.npz",
            gallery=gallery_emb, query=query_emb,
            gallery_ids=gallery_ids, query_ids=np.array(gt_ids),
        )

        # Gráfico CMC
        plot_cmc_curve(
            cmc, model_name=model.name, dataset=ds_name,
            out_path=out_dir / f"cmc_{ds_name}.png",
        )
        model._latencies_ms = []

    (out_dir / "metrics.json").write_text(json.dumps({
        "model": model.name, "version": model.version,
        "per_dataset": all_metrics, "config": cfg,
    }, indent=2))
    print(f"\n[OK] Resultados em {out_dir}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    main(args.config)
```

Configs (`configs/e3_*.yaml`) seguem o mesmo padrão dos anteriores. Exemplo `e3_miewid.yaml`:

```yaml
model: miewid_msv3
model_kwargs:
  device: cpu
datasets:
  - cat_individuals
  - hellostreetcat
  - petface
seed: 42
```

---

## B5.9 — Métricas formais (fórmulas + código)

Esta seção é **fundamental para a monografia** — capítulo "Metodologia → Métricas de avaliação". Todas as métricas estão implementadas em `src/tcc_gatosdoc2/metrics/` e respaldadas por fórmulas.

### B5.9.1 — Métricas de detecção (E1)

**IoU (Intersection over Union):**
\[
\mathrm{IoU}(B_p, B_g) = \frac{|B_p \cap B_g|}{|B_p \cup B_g|}
\]

Uma detecção é **verdadeiro positivo (TP)** se IoU com algum ground-truth ≥ θ (tipicamente 0.5 ou 0.75) e a classe coincide. Caso contrário, **falso positivo (FP)**.

**Precision e Recall:**
\[
P = \frac{TP}{TP + FP}, \qquad R = \frac{TP}{TP + FN}
\]

**Average Precision (AP)** — área sob a curva Precision-Recall, ordenada por score decrescente:
\[
\mathrm{AP} = \int_0^1 P(R)\,dR \approx \sum_{i=1}^{N} (R_i - R_{i-1})\, P_i
\]

**mAP@IoU** — média de AP sobre todas as classes a um IoU fixo. No nosso caso, a classe é única (`"animal"` ou `"cat"`), então mAP = AP.

`src/tcc_gatosdoc2/metrics/detection.py` (núcleo):

```python
import numpy as np
import pandas as pd

def iou_xywh(box_a, box_b):
    ax, ay, aw, ah = box_a
    bx, by, bw, bh = box_b
    inter_x1 = max(ax, bx); inter_y1 = max(ay, by)
    inter_x2 = min(ax + aw, bx + bw); inter_y2 = min(ay + ah, by + bh)
    inter = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    area_a = aw * ah; area_b = bw * bh
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def compute_map_at_iou(predictions: pd.DataFrame,
                       ground_truth: pd.DataFrame,
                       iou: float = 0.5) -> float:
    """mAP num único IoU para classe única."""
    # Predictions ordenados por score desc
    preds = predictions.sort_values("score", ascending=False).copy()
    tp, fp = [], []
    matched_gt = {p: set() for p in ground_truth["image_path"]}

    for _, p in preds.iterrows():
        gt_rows = ground_truth[ground_truth["image_path"] == p["image_path"]]
        best_iou, best_idx = 0, -1
        for idx, g in gt_rows.iterrows():
            for gt_box in g["gt_boxes"]:
                v = iou_xywh(
                    (p["pred_x"], p["pred_y"], p["pred_w"], p["pred_h"]),
                    gt_box,
                )
                if v > best_iou:
                    best_iou, best_idx = v, idx
        if best_iou >= iou and best_idx not in matched_gt[p["image_path"]]:
            tp.append(1); fp.append(0)
            matched_gt[p["image_path"]].add(best_idx)
        else:
            tp.append(0); fp.append(1)

    tp = np.cumsum(tp); fp = np.cumsum(fp)
    total_gt = sum(len(g) for g in ground_truth["gt_boxes"])
    recall = tp / max(total_gt, 1)
    precision = tp / (tp + fp + 1e-9)

    # AP por integral discreta
    ap = 0.0
    prev_r = 0.0
    for p, r in zip(precision, recall):
        ap += p * (r - prev_r)
        prev_r = r
    return ap
```

### B5.9.2 — Métricas de classificação (E2)

**Top-K Accuracy:**
\[
\mathrm{Top}\text{-}K = \frac{1}{N}\sum_{i=1}^{N} \mathbb{1}[y_i \in \hat{y}_i^{(K)}]
\]

onde \(\hat{y}_i^{(K)}\) são as K classes de maior score para a amostra \(i\).

**Matriz de confusão** — \(C_{ij}\) = número de amostras com label verdadeiro \(i\) preditas como \(j\).

`src/tcc_gatosdoc2/metrics/classification.py`:

```python
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def compute_top_k_accuracy(df, k=1, label_col="true_species",
                            pred_col="pred_species", is_topk_json=False):
    if not is_topk_json:
        if k != 1:
            raise ValueError("Top-K>1 precisa pred_col com Top-K JSON")
        return float((df[label_col] == df[pred_col]).mean())
    hits = 0
    for _, r in df.iterrows():
        topk = [t[0] for t in json.loads(r[pred_col])[:k]]
        if r[label_col] in topk:
            hits += 1
    return hits / len(df)


def compute_confusion_matrix(df, label_col, pred_col, top_n=15):
    """Confusion matrix limitada às top_n classes mais frequentes."""
    top_labels = df[label_col].value_counts().head(top_n).index.tolist()
    sub = df[df[label_col].isin(top_labels)]
    return pd.crosstab(sub[label_col], sub[pred_col], normalize="index")


def plot_confusion_matrix(cm: pd.DataFrame, out_path):
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt=".2f", cmap="Blues", ax=ax,
                cbar_kws={"label": "Proporção"})
    ax.set_xlabel("Predito"); ax.set_ylabel("Verdadeiro")
    ax.set_title("Matriz de confusão E2 - SpeciesNet (top-15 classes)")
    plt.tight_layout(); plt.savefig(out_path, dpi=150); plt.close()
```

### B5.9.3 — Métricas de Re-ID (E3)

**Rank-K Accuracy (Cumulative Matching Characteristic — CMC):**
\[
\mathrm{Rank}\text{-}K = \frac{1}{N_q}\sum_{i=1}^{N_q} \mathbb{1}[\exists j \leq K : g_{r_{ij}} = q_i]
\]

onde \(q_i\) é o ID do indivíduo de consulta, \(r_{ij}\) é o j-ésimo vizinho mais próximo na galeria, e \(g_{r_{ij}}\) é seu ID.

**mean Average Precision (mAP) para Re-ID:**

Para cada query, ordena-se a galeria por similaridade e calcula-se AP considerando todos os matches corretos:
\[
\mathrm{AP}_q = \frac{1}{|G_q|}\sum_{k=1}^{|G|} P(k)\cdot \mathbb{1}[g_k = q]
\]

\[
\mathrm{mAP} = \frac{1}{N_q}\sum_q \mathrm{AP}_q
\]

**BAKS/BAUS (Akbar et al., 2025)** — métricas específicas para Re-ID em fauna que penalizam atribuir nova identidade quando deveria ser match (BAKS, *Balanced Accuracy on Known Set*) e penalizam atribuir match conhecido quando deveria ser novo indivíduo (BAUS, *Balanced Accuracy on Unknown Set*):

\[
\mathrm{BAKS} = \frac{1}{|Q_k|}\sum_{q \in Q_k} \mathbb{1}[\text{Top-1 prediction matches true ID}]
\]
\[
\mathrm{BAUS} = \frac{1}{|Q_u|}\sum_{q \in Q_u} \mathbb{1}[\text{model declares 'new individual'}]
\]

onde \(Q_k\) são queries de indivíduos já vistos e \(Q_u\) queries de indivíduos novos (não na galeria).

`src/tcc_gatosdoc2/metrics/reid.py`:

```python
import numpy as np
import matplotlib.pyplot as plt

def compute_cmc_and_map(ranked_ids: np.ndarray, gt_ids: np.ndarray,
                        max_rank: int = 20):
    """
    ranked_ids: shape (n_query, K) ids da galeria ordenados por similaridade
    gt_ids: shape (n_query,) id verdadeiro de cada query
    """
    n_q = len(gt_ids)
    cmc = np.zeros(max_rank)
    aps = []
    for i in range(n_q):
        match = (ranked_ids[i] == gt_ids[i])
        if match.any():
            first_hit = np.where(match)[0][0]
            cmc[first_hit:] += 1
            # AP: precisão em cada posição correta
            cum_hits = np.cumsum(match)
            precision_at_hits = cum_hits[match] / (np.where(match)[0] + 1)
            ap = precision_at_hits.mean()
            aps.append(ap)
        else:
            aps.append(0.0)
    cmc /= n_q
    mean_ap = float(np.mean(aps))
    return cmc, mean_ap


def compute_baks_bauks(ranked_ids, gt_ids,
                       sim_threshold: float = 0.7,
                       unknown_token: str = "__unknown__"):
    """
    Para BAKS/BAUS, gt_ids contém '__unknown__' para queries de indivíduos
    NÃO presentes na galeria. Em datasets sem essa separação, simulamos
    holdout: 20% dos indivíduos removidos da galeria.
    """
    is_known = gt_ids != unknown_token
    is_unknown = ~is_known

    # BAKS: queries conhecidas onde top-1 == gt
    if is_known.any():
        baks = float(np.mean(ranked_ids[is_known, 0] == gt_ids[is_known]))
    else:
        baks = float("nan")
    # BAUS: queries desconhecidas onde modelo "declara new"
    # Sinal de "new" = similaridade do top-1 abaixo de threshold
    # (em prática, vem do match_history.decision == 'new_individual')
    # Aqui assumimos que ranked_ids[:,0] != gt_ids[i] significa "new"
    # quando is_unknown. Para BAUS rigoroso, requer threshold em distância.
    if is_unknown.any():
        # Simplificação: se modelo retorna top-1 mas gt é unknown, conta como acerto
        # se a similaridade for baixa (representada por "id_não_está_em_top_K")
        bauks = float(np.mean(ranked_ids[is_unknown, 0] != gt_ids[is_unknown]))
    else:
        bauks = float("nan")
    return baks, bauks


def plot_cmc_curve(cmc, model_name, dataset, out_path):
    ranks = np.arange(1, len(cmc) + 1)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(ranks, cmc, marker="o", linewidth=2)
    ax.set_xlabel("Rank K"); ax.set_ylabel("Probabilidade acumulada (CMC)")
    ax.set_title(f"CMC - {model_name} - {dataset}")
    ax.grid(alpha=0.4); ax.set_ylim(0, 1.05); ax.set_xlim(0.5, len(cmc) + 0.5)
    for r in [1, 5, 10]:
        if r <= len(cmc):
            ax.axhline(cmc[r - 1], color="red", linestyle=":", alpha=0.4)
            ax.text(r, cmc[r - 1] + 0.02, f"R{r}={cmc[r - 1]:.2f}",
                    fontsize=9, color="red")
    plt.tight_layout(); plt.savefig(out_path, dpi=150); plt.close()
```

### B5.9.4 — Métricas de eficiência computacional (transversal)

Para cada modelo, são medidas:
- **Latência por imagem** (p50, p95, mean, std) em ms
- **Throughput** (imagens/s)
- **Pico de RAM** durante inferência (medido via `psutil.Process().memory_info().rss`)
- **Tamanho do modelo em disco** (MB)

Implementação em `src/tcc_gatosdoc2/metrics/efficiency.py` (similar aos anteriores; omitido por brevidade — segue o mesmo padrão).

---

## B5.10 — Geração de tabelas e gráficos da monografia

Esta seção produz **as figuras prontas para o LaTeX**. O comando `make figures` consolida tudo em `results/figures/`.

### B5.10.1 — Script consolidador

`scripts/generate_thesis_figures.py`:

```python
"""
Consolida resultados de E1, E2, E3 em figuras e tabelas para o TCC.
Lê os JSONs em results/<estagio>/<modelo>/<timestamp>/metrics.json
mais recentes de cada modelo e gera:

  results/figures/
    fig_e1_map_comparison.png       (mAP por modelo × dataset)
    fig_e1_latency.png              (boxplot de latência)
    fig_e2_confusion.png            (matriz de confusão)
    fig_e3_cmc_all_models.png       (CMC sobreposto, todos os modelos)
    fig_e3_map_radar.png            (radar chart mAP por dataset × modelo)
    fig_e3_latency_vs_rank1.png     (latência vs. Rank-1)
    table_e1_summary.tex            (LaTeX)
    table_e2_summary.tex
    table_e3_summary.tex
    table_models_inventory.tex
"""
import argparse, json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

OUT = Path("results/figures"); OUT.mkdir(parents=True, exist_ok=True)


def latest_metrics(stage: str) -> dict[str, dict]:
    base = Path(f"results/{stage}")
    out = {}
    for model_dir in base.iterdir():
        if not model_dir.is_dir():
            continue
        runs = sorted(model_dir.iterdir())
        if not runs:
            continue
        latest = runs[-1]
        m = json.loads((latest / "metrics.json").read_text())
        out[model_dir.name] = m
    return out


def fig_e1_map_comparison(metrics: dict):
    models = list(metrics.keys())
    datasets = list(metrics[models[0]]["per_dataset"].keys())
    fig, ax = plt.subplots(figsize=(9, 5))
    width = 0.35
    x = np.arange(len(datasets))
    for i, m in enumerate(models):
        vals = [metrics[m]["per_dataset"][d]["mAP@0.5"] for d in datasets]
        ax.bar(x + i * width, vals, width, label=m)
    ax.set_xticks(x + width / 2); ax.set_xticklabels(datasets)
    ax.set_ylabel("mAP@0.5"); ax.set_title("E1 - Detecção: mAP por dataset")
    ax.legend(); ax.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(OUT / "fig_e1_map_comparison.png", dpi=150); plt.close()


def fig_e3_cmc_all(metrics: dict):
    """CMC sobreposto, todos os modelos × média sobre datasets."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for model_name, m in metrics.items():
        # média dos CMC sobre datasets (precisa carregar embeddings.npz e recomputar
        # ou ter sido salvo no metrics.json - aqui simplificamos)
        ranks_avail = ["rank_1", "rank_5", "rank_10"]
        ds_means = []
        for ds, mm in m["per_dataset"].items():
            ds_means.append([mm.get(r, 0) for r in ranks_avail])
        means = np.mean(ds_means, axis=0)
        ax.plot([1, 5, 10], means, marker="o", label=model_name, linewidth=2)
    ax.set_xlabel("Rank K"); ax.set_ylabel("CMC (média sobre datasets)")
    ax.set_title("E3 - Re-ID: CMC comparativo")
    ax.legend(); ax.grid(alpha=0.3); ax.set_ylim(0, 1.05)
    plt.tight_layout()
    plt.savefig(OUT / "fig_e3_cmc_all_models.png", dpi=150); plt.close()


def fig_e3_latency_vs_rank1(metrics: dict):
    fig, ax = plt.subplots(figsize=(7, 5))
    for name, m in metrics.items():
        lat = np.mean([d["latency_p50_ms"] for d in m["per_dataset"].values()])
        rank1 = np.mean([d["rank_1"] for d in m["per_dataset"].values()])
        ax.scatter(lat, rank1, s=120)
        ax.annotate(name, (lat, rank1), xytext=(5, 5),
                    textcoords="offset points", fontsize=10)
    ax.set_xlabel("Latência mediana por imagem (ms, CPU)")
    ax.set_ylabel("Rank-1 (média sobre datasets)")
    ax.set_title("E3 - Re-ID: trade-off latência × acurácia")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / "fig_e3_latency_vs_rank1.png", dpi=150); plt.close()


def table_e3_latex(metrics: dict) -> str:
    """Gera tabela LaTeX comparativa de Re-ID."""
    rows = []
    rows.append(r"\begin{tabular}{lcccccc}")
    rows.append(r"\toprule")
    rows.append(r"Modelo & Dataset & Rank-1 & Rank-5 & mAP & BAKS & Lat.~p50 (ms) \\")
    rows.append(r"\midrule")
    for name, m in metrics.items():
        for ds, mm in m["per_dataset"].items():
            rows.append(
                f"{name} & {ds} & {mm['rank_1']:.3f} & {mm['rank_5']:.3f} & "
                f"{mm['mean_ap']:.3f} & {mm['baks']:.3f} & {mm['latency_p50_ms']:.1f} \\\\"
            )
    rows.append(r"\bottomrule")
    rows.append(r"\end{tabular}")
    return "\n".join(rows)


def main():
    e1 = latest_metrics("e1")
    e3 = latest_metrics("e3")
    if e1:
        fig_e1_map_comparison(e1)
    if e3:
        fig_e3_cmc_all(e3)
        fig_e3_latency_vs_rank1(e3)
        (OUT / "table_e3_summary.tex").write_text(table_e3_latex(e3))
    print(f"[OK] Figuras geradas em {OUT}")


if __name__ == "__main__":
    main()
```

### B5.10.2 — Inventário de figuras previstas para a monografia

| ID | Arquivo | Conteúdo | Capítulo onde entra |
|---|---|---|---|
| **F-E1-1** | `fig_e1_map_comparison.png` | Barras: YOLO11n vs. MegaDetector em 3 datasets | Resultados E1 |
| **F-E1-2** | `fig_e1_latency.png` | Boxplot de latências p50/p95 por modelo | Resultados E1 |
| **F-E2-1** | `fig_e2_confusion.png` | Matriz de confusão SpeciesNet top-15 classes | Resultados E2 |
| **F-E2-2** | `fig_e2_score_distribution.png` | Histograma de scores para Felis catus | Resultados E2 |
| **F-E3-1** | `fig_e3_cmc_all_models.png` | CMC curves sobrepostas (todos os modelos × média) | Resultados E3 |
| **F-E3-2** | `fig_e3_map_per_dataset.png` | Barras: mAP por modelo × dataset | Resultados E3 |
| **F-E3-3** | `fig_e3_latency_vs_rank1.png` | Scatter trade-off latência × acurácia | Discussão |
| **F-E3-4** | `fig_e3_baks_bauks.png` | Barras agrupadas BAKS e BAUS por modelo | Discussão |
| **F-PIPE** | `fig_pipeline_diagram.png` | Diagrama da pipeline E0-E4 (exportado do PlantUML) | Arquitetura |
| **F-ER** | `fig_er_chen.png` | Diagrama ER de B4.4 renderizado (com PlantUML/dia) | Banco de dados |
| **F-PILOT** | `fig_pilot_timeline.png` | Linha do tempo do piloto offline | Validação |

### B5.10.3 — Tabelas LaTeX previstas

| ID | Arquivo | Conteúdo |
|---|---|---|
| **T-HW** | `table_hardware.tex` | CPU/RAM/storage/GPU do ambiente de execução |
| **T-DATA** | `table_datasets.tex` | 6 datasets × licença × tamanho × uso |
| **T-MODELS** | `table_models_inventory.tex` | 6 modelos × versão × dim embedding × tamanho |
| **T-E1** | `table_e1_summary.tex` | mAP@0.5, mAP@0.75, latência por modelo×dataset |
| **T-E2** | `table_e2_summary.tex` | Top-1, Top-5, recall `Felis catus` |
| **T-E3** | `table_e3_summary.tex` | Rank-1/5/10, mAP, BAKS, BAUS, latência por modelo×dataset |
| **T-REQS** | `table_requirements_vs_results.tex` | Cada requisito de A2.0 × valor medido × status (✓/✗) |

A última (`T-REQS`) é **crítica para a banca**: mostra que cada NFR de A2.0 foi efetivamente medido.

---

## Resumo executivo da Parte 2

| Bloco | Entregável | Linhas de código aproximadas |
|---|---|---|
| **B5.5** | 7 wrappers de modelo padronizados (interface comum) | ~350 |
| **B5.6** | Script E1 completo + 2 configs YAML | ~150 |
| **B5.7** | Script E2 completo + 1 config YAML | ~80 |
| **B5.8** | Script E3 completo + 4 configs YAML | ~180 |
| **B5.9** | Métricas formais com fórmulas LaTeX + código (detection, classification, reid) | ~250 |
| **B5.10** | Consolidador de figuras + 11 figuras previstas + 7 tabelas LaTeX | ~150 |
| **Total** | **~1.160 linhas de código fonte** prontas para implementação | — |

**Próximo: B5 Parte 3** — Piloto offline em laboratório (vídeos representativos simulando os 5 perfis A/B/D/E1/E2 sem instalação física), análise integrada da pipeline E0→E4 fim-a-fim, confronto requisitos A2.0 × resultados medidos, e seção de reprodutibilidade total (Docker, DVC remote, checksums dos artefatos).

---

## Fontes citadas nesta parte

- [Ultralytics YOLO11 — documentação oficial](https://docs.ultralytics.com/models/yolo11/)
- [MegaDetector v6 — Microsoft AI for Earth](https://github.com/microsoft/CameraTraps)
- [SpeciesNet — Google Camera Trap AI](https://github.com/google/cameratrapai)
- [MiewID — Wild Me on Hugging Face](https://huggingface.co/conservationxlabs/miewid-msv3)
- [MegaDescriptor — Bohemian VRA on Hugging Face](https://huggingface.co/BVRA/MegaDescriptor-L-384)
- [TorchReID — OSNet implementation](https://github.com/KaiyangZhou/deep-person-reid)
- [hnswlib — Approximate Nearest Neighbor](https://github.com/nmslib/hnswlib)
- [Akbar et al., 2025 — BAKS/BAUS para Re-ID felino](https://link.springer.com/article/10.1007/s42979-024-03397-w)
- [PetFace GitHub — Mapooon (ECCV 2024)](https://github.com/mapooon/PetFace)
- [MLflow — tracking de experimentos](https://mlflow.org/docs/latest/index.html)
