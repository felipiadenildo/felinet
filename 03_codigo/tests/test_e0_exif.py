"""Testes do módulo de extração de EXIF."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from pipeline.fase1_ingestao.exif import extrair_metadados


class TestExtrairMetadados:
    def test_imagem_com_exif_completo(self, pasta_midias_sintetica: Path) -> None:
        primeira = sorted(pasta_midias_sintetica.glob("*.jpg"))[0]
        meta = extrair_metadados(primeira)
        assert meta.largura == 64
        assert meta.altura == 48
        assert meta.timestamp == datetime(2026, 5, 24, 14, 0, 0)
        assert meta.fabricante == "TestCam"
        assert meta.modelo == "MD-001"

    def test_imagem_sem_exif_retorna_none_em_metadados_opcionais(
        self, imagem_sem_exif: Path
    ) -> None:
        meta = extrair_metadados(imagem_sem_exif)
        assert meta.largura == 16
        assert meta.altura == 16
        assert meta.timestamp is None
        assert meta.fabricante is None
        assert meta.modelo is None

    def test_arquivo_inexistente_levanta(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            extrair_metadados(tmp_path / "fantasma.jpg")
