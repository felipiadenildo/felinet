"""Wrapper MegaDescriptor-T-224 (Swin-Tiny treinado em fauna).

Recebe um ``CropEntrada`` (gerado pela Fase II) e devolve um ``Embedding``
no schema neutro da Fase IV. Modelo carregado via timm a partir do
Hugging Face Hub (``hf-hub:BVRA/MegaDescriptor-T-224``).

Pesos: ~204 MB, 27.5M parametros, embedding de dimensao 768.
"""

from __future__ import annotations

import time
from typing import Any

import torch
from torchvision import transforms

from ..fase2_deteccao.schema import BoundingBox
from ..fase3_classificacao.speciesnet import CropEntrada, cortar_crop
from .schema import Embedding

NOME_MODELO = "MegaDescriptor-T-224"
NOME_HF = "hf-hub:BVRA/MegaDescriptor-T-224"
TAMANHO_ENTRADA = 224

# Normalizacao ImageNet — padrao para Swin pre-treinados em fauna
MEDIA_NORMALIZACAO = [0.485, 0.456, 0.406]
DESVIO_NORMALIZACAO = [0.229, 0.224, 0.225]


class ExtratorMegaDescriptor:
    """Wrapper preguicoso do MegaDescriptor-T-224."""

    def __init__(self, dispositivo: str = "auto") -> None:
        self.dispositivo = self._resolver_dispositivo(dispositivo)
        self._modelo: Any = None
        self._transformacao = self._criar_transformacao()

    @staticmethod
    def _resolver_dispositivo(dispositivo: str) -> str:
        if dispositivo == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return dispositivo

    @staticmethod
    def _criar_transformacao() -> transforms.Compose:
        return transforms.Compose(
            [
                transforms.Resize((TAMANHO_ENTRADA, TAMANHO_ENTRADA)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=MEDIA_NORMALIZACAO,
                    std=DESVIO_NORMALIZACAO,
                ),
            ]
        )

    def _carregar(self) -> Any:
        if self._modelo is not None:
            return self._modelo
        import timm

        modelo = timm.create_model(NOME_HF, pretrained=True)
        modelo = modelo.eval().to(self.dispositivo)
        self._modelo = modelo
        return self._modelo

    def extrair(self, crop_entrada: CropEntrada) -> Embedding:
        """Extrai embedding L2-normalizado de um unico crop."""
        modelo = self._carregar()
        crop_img = cortar_crop(crop_entrada.media_path, crop_entrada.bbox)

        t0 = time.perf_counter()
        tensor = self._transformacao(crop_img).unsqueeze(0).to(self.dispositivo)
        with torch.no_grad():
            saida = modelo(tensor)
        # L2-normalizar embedding (recomendado para similaridade cosseno)
        saida = torch.nn.functional.normalize(saida, p=2, dim=1)
        vetor = saida.squeeze(0).cpu().tolist()
        tempo_ms = (time.perf_counter() - t0) * 1000

        return Embedding(
            media_path=str(crop_entrada.media_path),
            bbox_indice=crop_entrada.indice,
            vetor=vetor,
            modelo=NOME_MODELO,
            tempo_ms=tempo_ms,
        )

    def extrair_de_pil(
        self,
        media_path: str,
        bbox_indice: int,
        crop_img: Any,
    ) -> Embedding:
        """Variante: recebe a imagem PIL ja cortada (evita reler do disco).

        Util quando se extrai varios embeddings da mesma fonte sem precisar
        passar por ``BoundingBox`` (ex.: avaliacao em PetFace).
        """
        modelo = self._carregar()
        t0 = time.perf_counter()
        tensor = self._transformacao(crop_img).unsqueeze(0).to(self.dispositivo)
        with torch.no_grad():
            saida = modelo(tensor)
        saida = torch.nn.functional.normalize(saida, p=2, dim=1)
        vetor = saida.squeeze(0).cpu().tolist()
        tempo_ms = (time.perf_counter() - t0) * 1000

        return Embedding(
            media_path=media_path,
            bbox_indice=bbox_indice,
            vetor=vetor,
            modelo=NOME_MODELO,
            tempo_ms=tempo_ms,
        )


__all__ = ["BoundingBox", "ExtratorMegaDescriptor", "NOME_MODELO"]
