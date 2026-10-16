"""Wrapper SpeciesNet (pacote oficial Google/Kaggle).

Recebe um ``CropEntrada`` (gerado a partir das deteccoes da Fase II) e
devolve um ``ResultadoClassificacao`` no schema neutro da Fase III. A
politica de decisao (``decidir_status``) e aplicada internamente.

Stubs do torchaudio sao instalados antes do primeiro import de
``speciesnet`` para evitar erros de ``libcudart.so.13`` em ambientes
onde o torchaudio foi instalado mas a libcuda nao esta disponivel.
"""

from __future__ import annotations

import importlib.machinery as _machinery
import sys as _sys
import time
import types as _types
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _instalar_stub(nome: str) -> None:
    if nome in _sys.modules:
        return
    mod = _types.ModuleType(nome)
    mod.__spec__ = _machinery.ModuleSpec(nome, loader=None)
    mod.__path__ = []
    _sys.modules[nome] = mod


for _stub_name in (
    "torchaudio",
    "torchaudio._extension",
    "soundfile",
    "PytorchWildlife.data.bioacoustics",
    "PytorchWildlife.data.bioacoustics.bioacoustics_spectrograms",
    "PytorchWildlife.data.bioacoustics.bioacoustics_annotations",
):
    _instalar_stub(_stub_name)


from PIL import Image  # noqa: E402

from ..fase2_deteccao.schema import BoundingBox, ResultadoDeteccao  # noqa: E402
from .decisor import ConfigDecisor, decidir_status  # noqa: E402
from .schema import PrediccaoEspecie, ResultadoClassificacao  # noqa: E402

NOME_MODELO = "SpeciesNet (Google v4.0.2a)"


@dataclass(frozen=True)
class CropEntrada:
    """Um crop a classificar: imagem original + bbox + indice."""

    media_path: Path
    bbox: BoundingBox
    indice: int


def cortar_crop(media_path: Path | str, bbox: BoundingBox) -> Image.Image:
    """Extrai o recorte normalizado da bbox sobre a imagem original."""
    return cortar_de_imagem(Image.open(media_path).convert("RGB"), bbox)


def cortar_de_imagem(img: Image.Image, bbox: BoundingBox) -> Image.Image:
    """Recorte da bbox (coordenadas normalizadas) sobre uma imagem já carregada."""
    largura, altura = img.size
    x1 = int(bbox.x * largura)
    y1 = int(bbox.y * altura)
    x2 = int((bbox.x + bbox.w) * largura)
    y2 = int((bbox.y + bbox.h) * altura)
    return img.crop((x1, y1, x2, y2))


def crops_de_deteccao(resultado: ResultadoDeteccao) -> list[CropEntrada]:
    """Converte um ResultadoDeteccao em lista de crops para classificar.

    Apenas deteccoes da categoria 'animal' geram crops — a Fase III
    nao classifica pessoas ou veiculos.
    """
    return [
        CropEntrada(
            media_path=Path(resultado.media_path),
            bbox=d.bbox,
            indice=i,
        )
        for i, d in enumerate(resultado.deteccoes)
        if d.categoria == "animal"
    ]


def _extrair_especie(label_completo: str) -> str:
    """Devolve a ultima parte do label hierarquico do SpeciesNet.

    Labels seguem o formato ``uuid;classe;ordem;familia;genero;especie;nome_comum``.
    Para sentinelas (``blank``, ``vehicle``, ``animal``, ``human``) a ultima
    parte ja e o proprio rotulo.
    """
    return label_completo.split(";")[-1].strip().lower()


class ClassificadorSpeciesNet:
    """Wrapper preguicoso do SpeciesNet (pacote oficial Google)."""

    def __init__(
        self,
        dispositivo: str = "auto",
        top_k: int = 5,
        config_decisor: ConfigDecisor | None = None,
        pais: str | None = None,
    ) -> None:
        """``pais`` (ISO 3166-1 alfa-3, ex.: ``"BRA"``) ativa o filtro geográfico oficial do
        SpeciesNet: espécies que não ocorrem no país sobem na taxonomia (família, ordem...).
        Os experimentos da monografia rodaram sem filtro (``pais=None``)."""
        self.dispositivo = self._resolver_dispositivo(dispositivo)
        self.top_k = top_k
        self.config_decisor = config_decisor or ConfigDecisor()
        self.pais = pais
        self._modelo: Any = None
        self._ensemble: Any = None

    @staticmethod
    def _resolver_dispositivo(dispositivo: str) -> str:
        if dispositivo == "auto":
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        return dispositivo

    def _carregar(self) -> Any:
        if self._modelo is not None:
            return self._modelo
        from speciesnet import DEFAULT_MODEL, SpeciesNetClassifier

        self._modelo = SpeciesNetClassifier(
            model_name=DEFAULT_MODEL,
            device=self.dispositivo,
        )
        return self._modelo

    def _converter(self, bruto: dict) -> list[PrediccaoEspecie]:
        """Mapeia o dict bruto do SpeciesNet para a lista top-K do schema."""
        classificacoes = bruto.get("classifications")
        if not classificacoes:
            return []
        classes = classificacoes.get("classes", [])
        scores = classificacoes.get("scores", [])
        if self.pais and classes:
            classes, scores = self._filtro_geografico(classes, scores)
        resultado: list[PrediccaoEspecie] = []
        for label, score in zip(classes[: self.top_k], scores[: self.top_k], strict=False):
            resultado.append(
                PrediccaoEspecie(
                    especie=_extrair_especie(label),
                    probabilidade=float(score),
                )
            )
        return resultado

    def _filtro_geografico(self, classes: list[str], scores: list[float]) -> tuple[list, list]:
        """Aplica o filtro geográfico do SpeciesNet ao top-1 e remove do restante as espécies
        bloqueadas no país (mesmas regras do ``SpeciesNetEnsemble``)."""
        from speciesnet import DEFAULT_MODEL, SpeciesNetEnsemble
        from speciesnet.geofence_utils import (
            geofence_animal_classification,
            should_geofence_animal_classification,
        )

        if self._ensemble is None:
            self._ensemble = SpeciesNetEnsemble(DEFAULT_MODEL, geofence=True)
        mapa = self._ensemble.geofence_map
        rotulo, score, _fonte = geofence_animal_classification(
            labels=list(classes), scores=list(scores), country=self.pais, admin1_region=None,
            taxonomy_map=self._ensemble.taxonomy_map, geofence_map=mapa, enable_geofence=True,
        )  # fmt: skip
        if rotulo == classes[0]:
            return classes, scores
        resto = [
            (c, s)
            for c, s in zip(classes[1:], scores[1:], strict=False)
            if not should_geofence_animal_classification(c, self.pais, None, mapa, True)
        ]
        return [rotulo] + [c for c, _ in resto], [score] + [s for _, s in resto]

    def classificar(self, crop_entrada: CropEntrada) -> ResultadoClassificacao:
        """Classifica um unico crop e aplica a politica de decisao."""
        modelo = self._carregar()
        crop_img = cortar_crop(crop_entrada.media_path, crop_entrada.bbox)

        t0 = time.perf_counter()
        img_pre = modelo.preprocess(crop_img, bboxes=None, resize=True)
        bruto = modelo.predict(str(crop_entrada.media_path), img_pre)
        tempo_ms = (time.perf_counter() - t0) * 1000

        top_k = self._converter(bruto)
        status = decidir_status(top_k, self.config_decisor)

        return ResultadoClassificacao(
            media_path=str(crop_entrada.media_path),
            bbox_indice=crop_entrada.indice,
            top_k=top_k,
            status=status,
            modelo=NOME_MODELO,
            tempo_ms=tempo_ms,
        )
