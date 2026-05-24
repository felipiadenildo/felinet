"""Testes do esquema neutro de detecção."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pipeline.E1_deteccao.schema import (
    BoundingBox,
    Deteccao,
    ResultadoDeteccao,
    salvar_resultados_json,
)


class TestBoundingBox:
    def test_construcao_valida(self) -> None:
        b = BoundingBox(x=0.1, y=0.2, w=0.3, h=0.4)
        assert b.x == 0.1

    @pytest.mark.parametrize(
        "x,y,w,h",
        [
            (-0.1, 0.0, 0.5, 0.5),
            (0.0, 1.1, 0.5, 0.5),
            (0.0, 0.0, 1.5, 0.5),
            (0.0, 0.0, 0.5, -0.01),
        ],
    )
    def test_valor_fora_de_intervalo_levanta(
        self, x: float, y: float, w: float, h: float
    ) -> None:
        with pytest.raises(ValueError):
            BoundingBox(x=x, y=y, w=w, h=h)


class TestDeteccao:
    def test_construcao_valida(self) -> None:
        d = Deteccao(
            categoria="animal",
            confianca=0.85,
            bbox=BoundingBox(0.1, 0.1, 0.2, 0.2),
        )
        assert d.confianca == 0.85

    def test_categoria_invalida_levanta(self) -> None:
        with pytest.raises(ValueError):
            Deteccao(
                categoria="gato",  # não é categoria canônica do MD
                confianca=0.9,
                bbox=BoundingBox(0.0, 0.0, 0.1, 0.1),
            )

    def test_confianca_fora_levanta(self) -> None:
        with pytest.raises(ValueError):
            Deteccao(
                categoria="animal",
                confianca=1.5,
                bbox=BoundingBox(0.0, 0.0, 0.1, 0.1),
            )


class TestSerializacao:
    def test_resultado_serializa_e_recupera(self, tmp_path: Path) -> None:
        r = ResultadoDeteccao(
            media_path="x.jpg",
            largura=100,
            altura=80,
            deteccoes=[
                Deteccao(
                    "animal", 0.91, BoundingBox(0.1, 0.2, 0.3, 0.4)
                )
            ],
            modelo="MDv6 (MDV6-yolov10-c)",
            tempo_ms=42.0,
        )
        saida = tmp_path / "det.json"
        salvar_resultados_json([r], saida)
        carregado = json.loads(saida.read_text())
        assert len(carregado["resultados"]) == 1
        assert carregado["resultados"][0]["deteccoes"][0]["categoria"] == "animal"
