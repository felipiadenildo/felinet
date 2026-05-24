"""Fixtures compartilhadas entre testes."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def pasta_midias_sintetica(tmp_path: Path) -> Path:
    """Cria uma pasta temporária com 3 imagens PNG sintéticas e 1 arquivo lixo.

    Útil para testes de ingestão sem depender de fotos reais.
    """
    pasta = tmp_path / "cartao_sd"
    pasta.mkdir()

    # 3 imagens minúsculas com cores distintas
    for i, cor in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
        img = Image.new("RGB", (32, 32), color=cor)
        img.save(pasta / f"IMG_{i:04d}.jpg", "JPEG")

    # 1 arquivo que NÃO é mídia (pra testar filtro)
    (pasta / "log.txt").write_text("dummy")

    return pasta
