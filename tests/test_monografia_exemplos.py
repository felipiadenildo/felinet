"""Enquadramento comum das grades de exemplos e realce dos recortes escuros."""

from __future__ import annotations

import pytest
from PIL import Image

from felinet.monografia.exemplos import enquadrar, realcar


def _caixa(x: float, y: float, w: float, h: float, confianca: float = 0.9) -> dict:
    return {"categoria": "animal", "confianca": confianca, "bbox": {"x": x, "y": y, "w": w, "h": h}}


def test_enquadrar_retrato_vira_4x3_centrado_na_caixa() -> None:
    img = Image.new("RGB", (300, 400))
    recorte, caixas = enquadrar(img, [_caixa(0.25, 0.70, 0.5, 0.2)])
    assert recorte.size == (300, 225)
    # caixa de y 280..360 px; recorte de y 175..400 px -> caixa inteira e renormalizada
    b = caixas[0]["bbox"]
    assert b["y"] == pytest.approx((280 - 175) / 225)
    assert b["h"] == pytest.approx(80 / 225)
    assert b["x"] == pytest.approx(0.25) and b["w"] == pytest.approx(0.5)


def test_enquadrar_prioriza_a_caixa_mais_confiante_quando_nao_cabem_juntas() -> None:
    img = Image.new("RGB", (300, 400))
    caixas = [_caixa(0.1, 0.9, 0.2, 0.05, 0.9), _caixa(0.1, 0.02, 0.2, 0.05, 0.3)]
    _, saida = enquadrar(img, caixas)
    assert [c["confianca"] for c in saida] == [0.9]  # a outra fica fora do recorte 4:3


def test_realcar_so_recortes_escuros() -> None:
    escuro = Image.new("RGB", (8, 8), (10, 10, 10))
    escuro.putpixel((0, 0), (40, 40, 40))
    claro = Image.new("RGB", (8, 8), (150, 150, 150))
    _, realcou = realcar(escuro)
    assert realcou
    assert realcar(claro) == (claro, False)
