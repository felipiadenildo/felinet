"""Testes dos patches v23-smoke-fix.

Cobre os 3 bugs corrigidos:

1. ``_latest_por_fase`` em ``tabelas.py`` deve aceitar runs com
   ``extras.comando == "pipeline executar"`` como satisfazendo as 3 fases
   (ingestao/deteccao/classificacao). Antes, exigia match exato por fase.

2. ``RelatorioCascata.como_dicionario()`` em ``pipeline/orquestrador.py``
   deve expor aliases ``n_entradas``, ``n_animais_detectados``, ``n_imagens``,
   ``n_classificacoes`` e ``n_felis_catus`` esperados por
   ``figuras comparativo-fontes``.

3. ``dev preparar-petface-mini`` deve gerar um subset sintetico via PIL
   quando ``--origem`` for omitido, criando a estrutura oficial
   ``data/dev/reid_mini/{split/cat/reidentification.csv, images/cat/<id_pad>/*.png}``.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from felinet.comandos.dev import app as dev_app
from felinet.comandos.tabelas import _latest_por_fase
from felinet.pipeline.orquestrador import RelatorioCascata

# ---------------------------------------------------------------------------
# Bug 1: _latest_por_fase aceita "pipeline executar"
# ---------------------------------------------------------------------------


def _escrever_manifest(
    raiz: Path,
    *,
    fonte: str,
    perfil: str,
    comando: str,
    data_inicio: str = "2025-01-01T00:00:00+00:00",
) -> Path:
    raiz.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": "test01",
        "modo": "operacional",
        "fonte": fonte,
        "perfil": perfil,
        "protocolo": None,
        "tag": None,
        "git_sha": "abc1234",
        "git_branch": "main",
        "git_dirty": False,
        "data_inicio": data_inicio,
        "data_fim": data_inicio,
        "duracao_s": 1.0,
        "sucesso": True,
        "mensagem": "",
        "extras": {"comando": comando},
        "metricas_resumo": {},
    }
    arq = raiz / "manifest.json"
    arq.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return arq


def test_latest_por_fase_aceita_pipeline_executar_como_qualquer_fase(
    tmp_path: Path,
) -> None:
    """Um unico run de 'pipeline executar' deve satisfazer as 3 fases."""
    base = tmp_path / "runs" / "operacional"
    _escrever_manifest(
        base / "kaggle_cats" / "dev" / "_" / "abc1234",
        fonte="kaggle_cats",
        perfil="dev",
        comando="pipeline executar",
    )

    for fase in ("ingestao", "deteccao", "classificacao"):
        manifest = _latest_por_fase(
            tmp_path / "runs",
            fonte="kaggle_cats",
            perfil_nome="dev",
            prefixo_comando=fase,
        )
        assert manifest is not None, f"fase={fase} nao encontrou o run unificado"
        assert manifest["extras"]["comando"] == "pipeline executar"


def test_latest_por_fase_ainda_aceita_comandos_individuais(tmp_path: Path) -> None:
    """Backward compat: runs antigos com comandos por fase continuam validos."""
    base = tmp_path / "runs" / "operacional"
    _escrever_manifest(
        base / "felidae" / "dev" / "_" / "old1__ing",
        fonte="felidae",
        perfil="dev",
        comando="ingestao executar",
        data_inicio="2025-01-01T00:00:00+00:00",
    )
    _escrever_manifest(
        base / "felidae" / "dev" / "_" / "old2__det",
        fonte="felidae",
        perfil="dev",
        comando="deteccao executar",
        data_inicio="2025-01-02T00:00:00+00:00",
    )

    man_ing = _latest_por_fase(
        tmp_path / "runs",
        fonte="felidae",
        perfil_nome="dev",
        prefixo_comando="ingestao",
    )
    man_det = _latest_por_fase(
        tmp_path / "runs",
        fonte="felidae",
        perfil_nome="dev",
        prefixo_comando="deteccao",
    )
    assert man_ing is not None and man_ing["extras"]["comando"].startswith("ingestao")
    assert man_det is not None and man_det["extras"]["comando"].startswith("deteccao")


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

    # aliases obrigatorios para o bloco 7
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
def cfg_dev_apontando_para_tmp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
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
