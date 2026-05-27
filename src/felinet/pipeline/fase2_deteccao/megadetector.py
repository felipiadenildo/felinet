"""E1 — Detecção: wrapper do MegaDetector v6.

Carregamento sob demanda (lazy) para manter testes rápidos.
A primeira chamada baixa os pesos automaticamente (~50 MB)
em ~/.cache/torch/hub/ ou similar.
"""

from __future__ import annotations

# --- Workaround: evita import de torchaudio (que exige libcudart.so.13
#     ausente no host) e bioacústica do PytorchWildlife, não usados aqui.
#     Cada stub recebe __spec__ válido para que importlib.util.find_spec
#     (usado por transformers.is_torchaudio_available) não quebre.
import importlib.machinery as _machinery
import sys as _sys
import types as _types


def _instalar_stub(nome: str) -> None:
    if nome in _sys.modules:
        return
    mod = _types.ModuleType(nome)
    mod.__spec__ = _machinery.ModuleSpec(nome, loader=None)
    mod.__path__ = []  # marca como pacote (permite submódulos)
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
# --- fim workaround ---

import time
from pathlib import Path
from typing import Any

from PIL import Image

from .schema import (
    CATEGORIA_ANIMAL,
    CATEGORIA_PESSOA,
    CATEGORIA_VEICULO,
    BoundingBox,
    Deteccao,
    ResultadoDeteccao,
)

# Mapeamento das categorias numéricas do MegaDetector → strings canônicas
_MAPA_CATEGORIAS = {
    1: CATEGORIA_ANIMAL,
    2: CATEGORIA_PESSOA,
    3: CATEGORIA_VEICULO,
}

VERSAO_MDV6 = "MDV6-yolov10-c"
NOME_MODELO = f"MDv6 ({VERSAO_MDV6})"


class DetectorMegaDetectorV6:
    """Wrapper preguiçoso em torno do MegaDetector v6 da PytorchWildlife."""

    def __init__(self, dispositivo: str = "auto") -> None:
        """
        Parameters
        ----------
        dispositivo : str
            "auto" (escolhe CUDA se disponível), "cuda" ou "cpu".
        """
        self.dispositivo = self._resolver_dispositivo(dispositivo)
        self._modelo: Any = None  # carregado sob demanda

    @staticmethod
    def _resolver_dispositivo(dispositivo: str) -> str:
        if dispositivo == "auto":
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        return dispositivo

    def _carregar(self) -> Any:
        """Carrega o modelo na primeira chamada (lazy init).

        Importa o submódulo `detection` diretamente para evitar carregar
        `PytorchWildlife.data.bioacoustics`, que exige torchaudio com
        runtime CUDA específico e não é usado pelo pipeline visual.
        """
        if self._modelo is not None:
            return self._modelo
        # Import direto do submódulo de detecção (pula bioacoustics)
        from PytorchWildlife.models.detection import (
            MegaDetectorV6,  # type: ignore[attr-defined]
        )

        self._modelo = MegaDetectorV6(
            device=self.dispositivo,
            pretrained=True,
            version=VERSAO_MDV6,
        )
        return self._modelo

    def detectar(
        self,
        caminho_imagem: Path | str,
        limite_confianca: float = 0.50,
    ) -> ResultadoDeteccao:
        """Executa detecção em uma única imagem.

        Parameters
        ----------
        caminho_imagem : Path
            Caminho para a imagem.
        limite_confianca : float
            Detecções com confiança abaixo desse valor são descartadas.

        Returns
        -------
        ResultadoDeteccao
        """
        caminho_imagem = Path(caminho_imagem)
        if not caminho_imagem.is_file():
            raise FileNotFoundError(caminho_imagem)

        with Image.open(caminho_imagem) as img:
            largura, altura = img.size

        modelo = self._carregar()

        t0 = time.perf_counter()
        # API PytorchWildlife MDv6: single_image_detection retorna dict
        # com chaves 'detections' (xyxy abs), 'labels' (lista de int).
        resultado_bruto = modelo.single_image_detection(str(caminho_imagem))
        tempo_ms = (time.perf_counter() - t0) * 1000

        deteccoes = self._converter(resultado_bruto, largura, altura, limite_confianca)

        return ResultadoDeteccao(
            media_path=str(caminho_imagem),
            largura=largura,
            altura=altura,
            deteccoes=deteccoes,
            modelo=NOME_MODELO,
            tempo_ms=tempo_ms,
        )

    @staticmethod
    def _converter(
        resultado_bruto: Any,
        largura: int,
        altura: int,
        limite_confianca: float,
    ) -> list[Deteccao]:
        """Converte saída do MDv6 para nosso esquema neutro.

        O formato exato pode variar entre versões da PytorchWildlife;
        esta função aceita as duas variantes mais comuns.
        """
        deteccoes_dict = resultado_bruto.get("detections") or resultado_bruto
        # supervision.Detections compatível: tem .xyxy, .confidence, .class_id
        xyxy = getattr(deteccoes_dict, "xyxy", None)
        if xyxy is None:
            return []

        confiancas = getattr(deteccoes_dict, "confidence", [])
        classes = getattr(deteccoes_dict, "class_id", [])

        deteccoes: list[Deteccao] = []
        for i, box in enumerate(xyxy):
            conf = float(confiancas[i]) if i < len(confiancas) else 0.0
            if conf < limite_confianca:
                continue
            cls_id = int(classes[i]) if i < len(classes) else 1
            # MDv6 reporta classe 0-indexada (animal=0); ajustamos para 1-indexado
            categoria = _MAPA_CATEGORIAS.get(cls_id + 1, CATEGORIA_ANIMAL)

            x1, y1, x2, y2 = (float(v) for v in box)
            bbox = BoundingBox(
                x=max(0.0, min(1.0, x1 / largura)),
                y=max(0.0, min(1.0, y1 / altura)),
                w=max(0.0, min(1.0, (x2 - x1) / largura)),
                h=max(0.0, min(1.0, (y2 - y1) / altura)),
            )
            deteccoes.append(Deteccao(categoria=categoria, confianca=conf, bbox=bbox))
        return deteccoes
