"""Testes para felinet figuras comparativo-fontes (Bloco 7)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from felinet.comandos.figuras import app as figuras_app

runner = CliRunner()


def _criar_run_operacional(
    raiz_runs: Path, fonte: str, perfil: str, comando: str, metricas: dict
) -> Path:
    """Cria estrutura de run que listar_runs reconhece (com manifest.json)."""
    pasta = raiz_runs / "operacional" / fonte / perfil / "_" / f"sha__{comando}"
    pasta.mkdir(parents=True, exist_ok=True)
    manifest = {
        "modo": "operacional",
        "fonte": fonte,
        "perfil": perfil,
        "protocolo": "_",
        "data_inicio": f"2026-01-01T00:00:0{hash(comando) % 10}",
        "extras": {"comando": comando},
        "metricas_resumo": metricas,
        "sucesso": True,
    }
    (pasta / "manifest.json").write_text(json.dumps(manifest))
    latest = raiz_runs / "operacional" / fonte / perfil / "_" / "latest"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    latest.symlink_to(pasta.name)
    return pasta


def _instalar_perfil_fake(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fontes: list[str]
) -> None:
    raiz_runs = tmp_path / "runs"
    artifacts = tmp_path / "artifacts" / "figuras"
    fontes_dict = {f: f"data/raw/camera_trap/{f}" for f in fontes}

    class PerfilFake:
        nome = "prod"
        raiz_runs = tmp_path / "runs"
        artifacts_figuras_raiz = artifacts
        extras = {
            "fontes": fontes_dict,
            "raiz_runs": "runs",
            "artifacts_figuras_raiz": str(artifacts),
        }

    monkeypatch.setattr(
        "felinet.comandos.figuras.carregar_perfil", lambda *a, **kw: PerfilFake()
    )
    monkeypatch.setattr("felinet.comandos.figuras.raiz_projeto", lambda: tmp_path)
    return raiz_runs, artifacts


def test_comparativo_fontes_gera_png(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raiz_runs, artifacts = _instalar_perfil_fake(
        monkeypatch, tmp_path, ["kaggle_cats", "felidae"]
    )
    for fonte in ["kaggle_cats", "felidae"]:
        _criar_run_operacional(
            raiz_runs, fonte, "prod", "ingestao", {"n_entradas": 1000}
        )
        _criar_run_operacional(
            raiz_runs,
            fonte,
            "prod",
            "deteccao",
            {"n_imagens": 1000, "n_animais_detectados": 800},
        )
        _criar_run_operacional(
            raiz_runs,
            fonte,
            "prod",
            "classificacao",
            {"n_classificacoes": 800, "n_felis_catus": 600},
        )

    res = runner.invoke(figuras_app, ["comparativo-fontes", "--perfil", "prod"])
    assert res.exit_code == 0, res.output
    saida = artifacts / "operacional" / "_global" / "comparativo_fontes.png"
    assert saida.exists()
    assert saida.stat().st_size > 1000


def test_comparativo_fontes_aceita_subconjunto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raiz_runs, artifacts = _instalar_perfil_fake(
        monkeypatch, tmp_path, ["kaggle_cats", "felidae"]
    )
    _criar_run_operacional(
        raiz_runs, "kaggle_cats", "prod", "ingestao", {"n_entradas": 100}
    )
    _criar_run_operacional(
        raiz_runs,
        "kaggle_cats",
        "prod",
        "deteccao",
        {"n_imagens": 100, "n_animais_detectados": 80},
    )
    _criar_run_operacional(
        raiz_runs,
        "kaggle_cats",
        "prod",
        "classificacao",
        {"n_classificacoes": 80, "n_felis_catus": 70},
    )
    res = runner.invoke(
        figuras_app,
        ["comparativo-fontes", "--perfil", "prod", "--fontes", "kaggle_cats"],
    )
    assert res.exit_code == 0, res.output


def test_comparativo_fontes_sem_dados_avisa(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _instalar_perfil_fake(monkeypatch, tmp_path, ["kaggle_cats"])
    res = runner.invoke(figuras_app, ["comparativo-fontes", "--perfil", "prod"])
    # Nenhum run criado: deve sair com codigo != 0 e nao crashar.
    assert res.exit_code != 0
