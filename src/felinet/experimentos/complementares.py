"""Experimentos complementares do Cap. 5 da monografia.

* **Experimento de Cascatas Multifonte** (Tab. 9): detector + classificador leves em quatro fontes.
* **Experimento de Sensibilidade ao Limiar do Detector** (Tab. 10).

Portados do protótipo ``felinet_mono`` (usado na monografia), com a mesma lógica:

* detector: YOLOv8n do COCO restrito à classe ``cat`` (id 15), limiar 0,2;
* classificador: CLIP ViT-B/32 *zero-shot* sobre a **imagem inteira**, com quatro prompts; a imagem
  é "gato" quando o prompt de gato tem a maior similaridade; uma classificação por imagem com detecção;
* sensibilidade: detecções extraídas uma vez com limiar 0,05 e depois filtradas por limiar.

Diferença deliberada: as imagens de cada fonte são deduplicadas por SHA-256. O protótipo repetiu o
cache do ``felidae_wild`` (71 imagens únicas contadas como 200).
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Protocol

EXTENSOES = {".jpg", ".jpeg", ".png"}
COCO_GATO = 15
PROMPTS = (
    "a photo of a cat",
    "a photo of a dog",
    "a photo of a wild animal",
    "a photo without any animal",
)
ROTULOS = ("cat", "dog", "wild_animal", "no_animal")
LIMIARES_PADRAO = (0.1, 0.2, 0.3, 0.5, 0.7)


class Detector(Protocol):
    def detectar(self, caminho: Path, conf: float) -> list[float]: ...


class Classificador(Protocol):
    def classificar(self, caminho: Path) -> str: ...


def imagens_da_fonte(pasta: Path) -> tuple[list[Path], int]:
    """Imagens da pasta (recursivo, em ordem de nome), sem repetições de conteúdo.

    Devolve ``(imagens únicas, quantidade de duplicatas descartadas)``.
    """
    vistos: set[str] = set()
    unicas: list[Path] = []
    duplicatas = 0
    for p in sorted(q for q in Path(pasta).rglob("*") if q.suffix.lower() in EXTENSOES):
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if h in vistos:
            duplicatas += 1
            continue
        vistos.add(h)
        unicas.append(p)
    return unicas, duplicatas


def cascatas_multifonte(
    fontes: dict[str, list[Path]],
    detector: Detector,
    classificador: Classificador,
    conf: float = 0.2,
    relogio: Callable[[], float] = time.perf_counter,
) -> list[dict]:
    """Uma linha por fonte, com as colunas da Tab. 9 (mesmos nomes do protótipo)."""
    linhas = []
    for nome, imagens in fontes.items():
        n_caixas = n_com_animal = n_gato = 0
        confiancas: list[float] = []
        inicio = relogio()
        for caminho in imagens:
            scores = detector.detectar(caminho, conf)
            if not scores:
                continue
            n_com_animal += 1
            n_caixas += len(scores)
            confiancas.extend(scores)
            if classificador.classificar(caminho) == "cat":
                n_gato += 1
        n = len(imagens)
        linhas.append(
            {
                "source": nome,
                "n_images": n,
                "n_detection_boxes": n_caixas,
                "n_images_with_animal": n_com_animal,
                "rate_animal": n_com_animal / max(n, 1),
                "n_classified_cat": n_gato,
                "rate_cat": n_gato / max(n_com_animal, 1),
                "mean_det_score": sum(confiancas) / len(confiancas) if confiancas else 0.0,
                "elapsed_s": relogio() - inicio,
            }
        )
    return linhas


def sensibilidade_limiar(
    fonte: str,
    imagens: list[Path],
    detector: Detector,
    limiares: Iterable[float] = LIMIARES_PADRAO,
    conf_base: float = 0.05,
) -> list[dict]:
    """Uma linha por limiar, com as colunas da Tab. 10 (detecção apenas, sem classificação)."""
    deteccoes = [
        (i, s) for i, caminho in enumerate(imagens) for s in detector.detectar(caminho, conf_base)
    ]
    n = len(imagens)
    linhas = []
    for t in limiares:
        acima = [(i, s) for i, s in deteccoes if s >= t]
        com_animal = {i for i, _ in acima}
        linhas.append(
            {
                "source": fonte,
                "threshold": t,
                "n_boxes": len(acima),
                "n_images_with_animal": len(com_animal),
                "rate_animal": len(com_animal) / max(n, 1),
                "mean_score": sum(s for _, s in acima) / len(acima) if acima else 0.0,
            }
        )
    return linhas


# ----------------------------------------------------------------------------
# Modelos reais (extra [complementares]); carregados só quando usados
# ----------------------------------------------------------------------------


def _dispositivo(dispositivo: str) -> str:
    if dispositivo != "auto":
        return dispositivo
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


class DetectorGatoYolo:
    """YOLOv8n do COCO restrito à classe ``cat``; devolve a confiança de cada caixa."""

    def __init__(self, pesos: str | Path = "yolov8n.pt", dispositivo: str = "auto") -> None:
        from ultralytics import YOLO

        self.dispositivo = _dispositivo(dispositivo)
        self.modelo = YOLO(str(pesos))

    def detectar(self, caminho: Path, conf: float) -> list[float]:
        resultado = self.modelo.predict(
            str(caminho), conf=conf, classes=[COCO_GATO], device=self.dispositivo, verbose=False
        )
        if not resultado or resultado[0].boxes is None:
            return []
        return [float(s) for s in resultado[0].boxes.conf.cpu().numpy()]


class ClassificadorGatoClip:
    """CLIP ViT-B/32 (OpenAI) zero-shot sobre a imagem inteira; devolve o rótulo de maior similaridade."""

    def __init__(self, dispositivo: str = "auto") -> None:
        import open_clip
        import torch

        self.torch = torch
        self.dispositivo = _dispositivo(dispositivo)
        self.modelo, _, self.preprocessar = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="openai"
        )
        self.modelo = self.modelo.to(self.dispositivo).eval()
        tokens = open_clip.get_tokenizer("ViT-B-32")(list(PROMPTS)).to(self.dispositivo)
        with torch.no_grad():
            texto = self.modelo.encode_text(tokens)
        self.texto = texto / texto.norm(dim=-1, keepdim=True)

    def classificar(self, caminho: Path) -> str:
        from PIL import Image

        try:
            imagem = Image.open(caminho).convert("RGB")
        except OSError:
            return "unknown"
        with self.torch.no_grad():
            x = self.preprocessar(imagem).unsqueeze(0).to(self.dispositivo)
            v = self.modelo.encode_image(x)
            v = v / v.norm(dim=-1, keepdim=True)
            similaridades = (v @ self.texto.T).squeeze(0)
        return ROTULOS[int(similaridades.argmax())]
