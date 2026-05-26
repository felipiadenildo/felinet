# 03_codigo/tests/test_e1_visualizar.py
"""Teste do renderizador de bboxes."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from felinet.pipeline.fase2_deteccao.schema import (
    BoundingBox,
    Deteccao,
    ResultadoDeteccao,
)
from felinet.pipeline.fase2_deteccao.visualizar import desenhar_deteccoes


def test_gera_arquivo_com_dimensoes_da_imagem_original(
    pasta_midias_sintetica: Path, tmp_path: Path
) -> None:
    imagem = sorted(pasta_midias_sintetica.glob("*.jpg"))[0]
    resultado = ResultadoDeteccao(
        media_path=str(imagem),
        largura=64,
        altura=48,
        deteccoes=[
            Deteccao(
                categoria="animal",
                confianca=0.91,
                bbox=BoundingBox(0.1, 0.1, 0.3, 0.3),
            )
        ],
        modelo="MDv6 (test)",
        tempo_ms=10.0,
    )
    saida = tmp_path / "anotada.jpg"
    desenhar_deteccoes(resultado, saida)
    assert saida.is_file()
    with Image.open(saida) as img:
        assert img.size == (64, 48)


def test_imagem_sem_deteccoes_gera_arquivo_sem_anotacoes(
    pasta_midias_sintetica: Path, tmp_path: Path
) -> None:
    imagem = sorted(pasta_midias_sintetica.glob("*.jpg"))[0]
    resultado = ResultadoDeteccao(
        media_path=str(imagem),
        largura=64,
        altura=48,
        deteccoes=[],
        modelo="MDv6 (test)",
        tempo_ms=10.0,
    )
    saida = tmp_path / "anotada.jpg"
    desenhar_deteccoes(resultado, saida)
    assert saida.is_file()
