"""Testes do gerador de manifesto."""

from __future__ import annotations

import csv
from pathlib import Path

from felinet.pipeline.fase1_ingestao.manifesto import COLUNAS_MANIFESTO, gerar_manifesto


class TestGerarManifesto:
    def test_csv_tem_uma_linha_por_imagem(
        self, pasta_midias_sintetica: Path, tmp_path: Path
    ) -> None:
        saida = tmp_path / "manifesto.csv"
        entradas = gerar_manifesto(pasta_midias_sintetica, saida)
        assert len(entradas) == 3
        assert saida.exists()

        with saida.open(encoding="utf-8") as f:
            linhas = list(csv.DictReader(f))
        assert len(linhas) == 3
        assert set(linhas[0].keys()) == set(COLUNAS_MANIFESTO)

    def test_caminhos_sao_relativos(self, pasta_midias_sintetica: Path, tmp_path: Path) -> None:
        saida = tmp_path / "manifesto.csv"
        entradas = gerar_manifesto(pasta_midias_sintetica, saida)
        for e in entradas:
            assert not Path(e.caminho_relativo).is_absolute()

    def test_hash_e_estavel(self, pasta_midias_sintetica: Path, tmp_path: Path) -> None:
        saida1 = tmp_path / "m1.csv"
        saida2 = tmp_path / "m2.csv"
        e1 = gerar_manifesto(pasta_midias_sintetica, saida1)
        e2 = gerar_manifesto(pasta_midias_sintetica, saida2)
        assert [e.sha256 for e in e1] == [e.sha256 for e in e2]
