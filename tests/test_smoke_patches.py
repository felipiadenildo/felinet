"""Testes dos patches v23-smoke-fix.

1. ``RelatorioCascata.como_dicionario()`` em ``pipeline/orquestrador.py``
   deve expor aliases ``n_entradas``, ``n_animais_detectados``, ``n_imagens``,
   ``n_classificacoes`` e ``n_felis_catus`` (contrato do manifesto dos runs).

2. ``dev preparar-petface-mini`` deve gerar um subset sintetico via PIL
   quando ``--origem`` for omitido, criando a estrutura oficial
   ``data/dev/reid_mini/{split/cat/reidentification.csv, images/cat/<id_pad>/*.png}``.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from typer.testing import CliRunner

from felinet.comandos.dev import app as dev_app
from felinet.pipeline.orquestrador import RelatorioCascata

# ---------------------------------------------------------------------------
# Bug 2: RelatorioCascata expoe aliases
# ---------------------------------------------------------------------------


def test_relatorio_cascata_expoe_aliases_esperados_por_comparativo_fontes() -> None:
    """O dict deve conter os 5 aliases consumidos por figuras/comparativo-fontes."""
    rel = RelatorioCascata(
        n_brutas=30,
        n_manifesto=30,
        n_deteccoes_animal=42,
        n_classificacoes_felis_catus=25,
        n_crops_gerados=25,
        n_embeddings=25,
        sucesso=True,
        n_imagens_com_animal=27,
        n_classificacoes_total=42,
    )
    d = rel.como_dicionario()

    # aliases obrigatorios para a figura comparativo-fontes
    assert d["n_entradas"] == 30
    assert d["n_animais_detectados"] == 42
    assert d["n_imagens"] == 27
    assert d["n_classificacoes"] == 42
    assert d["n_felis_catus"] == 25


def test_relatorio_cascata_n_imagens_faz_fallback_para_n_manifesto() -> None:
    """Quando n_imagens_com_animal eh 0, o alias 'n_imagens' usa n_manifesto."""
    rel = RelatorioCascata(
        n_brutas=15,
        n_manifesto=15,
        n_deteccoes_animal=0,
        n_classificacoes_felis_catus=0,
        n_crops_gerados=0,
        n_embeddings=0,
        sucesso=True,
        n_imagens_com_animal=0,
        n_classificacoes_total=0,
    )
    d = rel.como_dicionario()
    assert d["n_imagens"] == 15


# ---------------------------------------------------------------------------
# Bug 3: preparar-petface-mini sintetico (sem --origem)
# ---------------------------------------------------------------------------


@pytest.fixture
def cfg_dev_apontando_para_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Faz carregar_perfil('dev') retornar um Perfil com raw_petface=tmp_path/reid_mini."""
    from felinet import config as cfg_mod

    destino = tmp_path / "reid_mini"
    original = cfg_mod.carregar_perfil

    def fake_carregar_perfil(nome: str):
        perfil = original(nome)
        # substitui raw_petface por um caminho gravavel no tmp
        try:
            object.__setattr__(perfil, "raw_petface", destino)
        except Exception:
            perfil.raw_petface = destino  # type: ignore[attr-defined]
        return perfil

    monkeypatch.setattr(cfg_mod, "carregar_perfil", fake_carregar_perfil)
    # tambem precisa patchar a importacao usada em comandos.dev
    from felinet.comandos import dev as dev_mod

    monkeypatch.setattr(dev_mod, "carregar_perfil", fake_carregar_perfil)
    return destino


def test_preparar_petface_mini_sintetico_cria_estrutura_oficial(
    cfg_dev_apontando_para_tmp: Path,
) -> None:
    """Sem --origem, gera estrutura PetFace-like com PNGs sinteticos via PIL."""
    runner = CliRunner()
    result = runner.invoke(
        dev_app,
        ["preparar-petface-mini", "--individuos", "3", "--imagens-por-id", "2"],
    )
    assert result.exit_code == 0, result.output
    assert "sintetico" in result.output

    destino = cfg_dev_apontando_para_tmp
    # CSV oficial
    csv_path = destino / "split" / "cat" / "reidentification.csv"
    assert csv_path.exists(), f"CSV nao gerado em {csv_path}"
    linhas = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    assert len(linhas) == 3
    assert {"filename", "label"} <= set(linhas[0].keys())

    # Imagens em images/cat/<id_pad>/
    img_root = destino / "images" / "cat"
    pastas = sorted(p for p in img_root.iterdir() if p.is_dir())
    assert len(pastas) == 3
    for pasta in pastas:
        pngs = sorted(pasta.glob("*.png"))
        assert len(pngs) == 2, f"{pasta} deveria ter 2 imagens, achou {len(pngs)}"
