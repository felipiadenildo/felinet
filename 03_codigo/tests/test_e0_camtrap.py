"""Testes do conversor Camtrap-DP simplificado."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pipeline.fase1_ingestao.camtrap import (
    Deployment,
    imagens_para_media,
    salvar_camtrap_json,
)
from pipeline.fase1_ingestao.validar import listar_midias


def _deployment_dummy() -> Deployment:
    return Deployment(
        deployment_id="dep-P01-2026-05",
        location_id="P01",
        location_name="Ponto 01 — Bosque",
        deployment_start=datetime(2026, 5, 24, 0, 0, 0),
        deployment_end=datetime(2026, 5, 31, 23, 59, 59),
        camera_model="MD-001",
    )


class TestImagensParaMedia:
    def test_um_registro_por_imagem(self, pasta_midias_sintetica: Path) -> None:
        dep = _deployment_dummy()
        imagens = listar_midias(pasta_midias_sintetica)
        media = imagens_para_media(imagens, dep)
        assert len(media) == 3

    def test_media_id_deterministico(self, pasta_midias_sintetica: Path) -> None:
        dep = _deployment_dummy()
        imagens = listar_midias(pasta_midias_sintetica)
        m1 = imagens_para_media(imagens, dep)
        m2 = imagens_para_media(imagens, dep)
        assert [r.media_id for r in m1] == [r.media_id for r in m2]

    def test_mediatype_correto(self, pasta_midias_sintetica: Path) -> None:
        dep = _deployment_dummy()
        imagens = listar_midias(pasta_midias_sintetica)
        media = imagens_para_media(imagens, dep)
        assert all(r.file_mediatype == "image/jpeg" for r in media)


class TestSalvarCamtrapJson:
    def test_json_contem_deployment_e_media(
        self, pasta_midias_sintetica: Path, tmp_path: Path
    ) -> None:
        dep = _deployment_dummy()
        imagens = listar_midias(pasta_midias_sintetica)
        media = imagens_para_media(imagens, dep)

        saida = tmp_path / "camtrap.json"
        salvar_camtrap_json(dep, media, saida)

        payload = json.loads(saida.read_text())
        assert payload["profile"].startswith("camtrap-dp-simplified")
        assert len(payload["deployments"]) == 1
        assert len(payload["media"]) == 3
        assert payload["deployments"][0]["location_id"] == "P01"
