"""Fase II — Detecção: anonimização de pessoas e filtros de caixas (Seção 3.3 da monografia).

* desfoque gaussiano forte das caixas da classe ``person``, aplicado antes de qualquer gravação
  de imagem (LGPD, Lei nº 13.709/2018); as coordenadas continuam como metadado;
* limiar de confiança por modo de captura (diurno ou noturno em infravermelho próximo);
* tamanho mínimo e máximo de caixa, em fração da área do quadro.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageFilter

from .schema import Deteccao


def _caixa_em_pixels(d: Deteccao, largura: int, altura: int) -> tuple[int, int, int, int]:
    b = d.bbox
    x0, y0 = max(0, int(b.x * largura)), max(0, int(b.y * altura))
    x1, y1 = (
        min(largura, int(round((b.x + b.w) * largura))),
        min(altura, int(round((b.y + b.h) * altura))),
    )
    return x0, y0, x1, y1


def anonimizar_pessoas(
    img: Image.Image, deteccoes: Iterable[Deteccao], fator_raio: float = 0.15
) -> Image.Image:
    """Cópia da imagem com as caixas ``person`` desfocadas (raio proporcional ao tamanho da caixa)."""
    saida = img.copy()
    for d in deteccoes:
        if d.categoria != "person":
            continue
        x0, y0, x1, y1 = _caixa_em_pixels(d, *saida.size)
        if x1 <= x0 or y1 <= y0:
            continue
        raio = max(6.0, fator_raio * max(x1 - x0, y1 - y0))
        regiao = saida.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(raio))
        saida.paste(regiao, (x0, y0))
    return saida


def eh_noturno_infravermelho(img: Image.Image, saturacao_max: float = 0.06) -> bool:
    """Quadro de iluminação NIR: praticamente sem cor (saturação média baixa no HSV)."""
    hsv = np.asarray(img.convert("RGB").convert("HSV"), dtype=np.float32)
    return float(hsv[:, :, 1].mean()) / 255.0 < saturacao_max


@dataclass(frozen=True)
class ConfigFiltroDeteccao:
    limiar_dia: float = 0.2
    limiar_noite: float = 0.2  # mesmo valor por padrão; calibrar com dados noturnos do Campus 2
    area_min: float = 0.0  # fração da área do quadro
    area_max: float = 1.0


def filtrar_deteccoes(
    deteccoes: Iterable[Deteccao], noturno: bool, cfg: ConfigFiltroDeteccao = ConfigFiltroDeteccao()
) -> list[Deteccao]:
    """Caixas ``animal`` acima do limiar do modo de captura e dentro da faixa de tamanho.

    Pessoas e veículos passam sem filtro: são metadado de diagnóstico e entrada da anonimização.
    """
    limiar = cfg.limiar_noite if noturno else cfg.limiar_dia
    saida = []
    for d in deteccoes:
        if d.categoria != "animal":
            saida.append(d)
            continue
        area = d.bbox.w * d.bbox.h
        if d.confianca >= limiar and cfg.area_min <= area <= cfg.area_max:
            saida.append(d)
    return saida
