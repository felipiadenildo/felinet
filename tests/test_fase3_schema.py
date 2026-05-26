"""Testes do esquema da Fase III."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from felinet.pipeline.fase3_classificacao.schema import (
    STATUS_FELIS_CATUS,
    PrediccaoEspecie,
    ResultadoClassificacao,
    salvar_resultados_json,
)


class TestPrediccaoEspecie:
    def test_construcao_valida(self) -> None:
        p = PrediccaoEspecie(especie="Felis catus", probabilidade=0.85)
        assert p.probabilidade == 0.85

    def test_probabilidade_fora_levanta(self) -> None:
        with pytest.raises(ValueError):
            PrediccaoEspecie(especie="x", probabilidade=1.5)


class TestResultadoClassificacao:
    def test_top1_e_primeiro_da_lista(self) -> None:
        r = ResultadoClassificacao(
            media_path="x.jpg",
            bbox_indice=0,
            top_k=[
                PrediccaoEspecie("Felis catus", 0.9),
                PrediccaoEspecie("Lynx rufus", 0.08),
            ],
            status=STATUS_FELIS_CATUS,
            modelo="SpeciesNet",
            tempo_ms=12.0,
        )
        assert r.top1.especie == "Felis catus"

    def test_status_invalido_levanta(self) -> None:
        with pytest.raises(ValueError):
            ResultadoClassificacao(
                media_path="x.jpg",
                bbox_indice=0,
                top_k=[PrediccaoEspecie("x", 0.9)],
                status="status_inexistente",
                modelo="SpeciesNet",
                tempo_ms=0.0,
            )

    def test_serializacao_round_trip(self, tmp_path: Path) -> None:
        r = ResultadoClassificacao(
            media_path="x.jpg",
            bbox_indice=2,
            top_k=[PrediccaoEspecie("Felis catus", 0.95)],
            status=STATUS_FELIS_CATUS,
            modelo="SpeciesNet",
            tempo_ms=12.0,
        )
        saida = tmp_path / "out.json"
        salvar_resultados_json([r], saida)
        carregado = json.loads(saida.read_text())
        assert carregado["resultados"][0]["status"] == STATUS_FELIS_CATUS
        assert carregado["resultados"][0]["bbox_indice"] == 2
