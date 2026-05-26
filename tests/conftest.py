"""Fixtures compartilhadas entre testes."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import piexif
import pytest
from PIL import Image


def _imagem_com_exif(
    caminho: Path,
    cor: tuple[int, int, int],
    timestamp: datetime,
    make: str = "TestCam",
    model: str = "MD-001",
) -> None:
    """Cria uma imagem JPEG com EXIF mínimo de armadilha fotográfica."""
    img = Image.new("RGB", (64, 48), color=cor)
    ts_str = timestamp.strftime("%Y:%m:%d %H:%M:%S").encode()
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: make.encode(),
            piexif.ImageIFD.Model: model.encode(),
            piexif.ImageIFD.DateTime: ts_str,
        },
        "Exif": {piexif.ExifIFD.DateTimeOriginal: ts_str},
    }
    img.save(caminho, "JPEG", exif=piexif.dump(exif_dict))


@pytest.fixture
def pasta_midias_sintetica(tmp_path: Path) -> Path:
    """Pasta com 3 imagens JPEG com EXIF + 1 arquivo não-mídia."""
    pasta = tmp_path / "cartao_sd"
    pasta.mkdir()

    base = datetime(2026, 5, 24, 14, 0, 0)
    cores = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    for i, cor in enumerate(cores):
        _imagem_com_exif(
            pasta / f"IMG_{i:04d}.jpg",
            cor,
            base + timedelta(minutes=i * 5),
        )

    (pasta / "log.txt").write_text("dummy")
    return pasta


@pytest.fixture
def imagem_sem_exif(tmp_path: Path) -> Path:
    """Uma imagem PNG simples, sem nenhum metadado EXIF."""
    caminho = tmp_path / "sem_exif.png"
    Image.new("RGB", (16, 16), color=(128, 128, 128)).save(caminho)
    return caminho
