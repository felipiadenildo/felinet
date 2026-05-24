"""Testes do estágio E0 — Ingestão."""

from __future__ import annotations

from pathlib import Path

import pytest
from pipeline.E0_ingestao.validar import (
    eh_imagem,
    eh_video,
    listar_midias,
    sha256_arquivo,
)


class TestSha256:
    def test_hash_de_arquivo_conhecido(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "teste.txt"
        arquivo.write_bytes(b"abc")
        # SHA-256 de "abc" é constante e conhecido
        esperado = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        assert sha256_arquivo(arquivo) == esperado

    def test_arquivo_inexistente_levanta(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            sha256_arquivo(tmp_path / "nao_existe.jpg")

    def test_aceita_string_e_path(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "x.bin"
        arquivo.write_bytes(b"hello")
        assert sha256_arquivo(str(arquivo)) == sha256_arquivo(arquivo)


class TestExtensoes:
    @pytest.mark.parametrize("nome", ["foto.jpg", "foto.JPG", "x.png", "y.tiff"])
    def test_eh_imagem_verdadeiro(self, nome: str) -> None:
        assert eh_imagem(nome) is True

    @pytest.mark.parametrize("nome", ["video.mp4", "x.MOV", "y.avi"])
    def test_eh_video_verdadeiro(self, nome: str) -> None:
        assert eh_video(nome) is True

    def test_extensao_desconhecida(self) -> None:
        assert eh_imagem("readme.md") is False
        assert eh_video("readme.md") is False


class TestListarMidias:
    def test_encontra_apenas_midias(self, pasta_midias_sintetica: Path) -> None:
        encontradas = listar_midias(pasta_midias_sintetica)
        assert len(encontradas) == 3
        assert all(eh_imagem(p) for p in encontradas)

    def test_resultado_ordenado(self, pasta_midias_sintetica: Path) -> None:
        encontradas = listar_midias(pasta_midias_sintetica)
        nomes = [p.name for p in encontradas]
        assert nomes == sorted(nomes)

    def test_pasta_inexistente_levanta(self, tmp_path: Path) -> None:
        with pytest.raises(NotADirectoryError):
            listar_midias(tmp_path / "nao_existe")
