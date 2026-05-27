"""Testes para felinet datasets {linkar, listar}."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from felinet.comandos.datasets import app as datasets_app

runner = CliRunner()


def _setup_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """Monta uma raiz_projeto fake e um dataset físico para linkar."""
    raiz = tmp_path / "repo"
    (raiz / "configs").mkdir(parents=True)
    fonte_disco = tmp_path / "ssd" / "kaggle_cats"
    fonte_disco.mkdir(parents=True)
    (fonte_disco / "a.jpg").write_bytes(b"\x00")
    (raiz / "configs" / "datasets_locais.yaml").write_text(
        "datasets:\n"
        "  kaggle_cats:\n"
        "    tipo: camera_trap_brutas\n"
        "    layout: flat\n"
        f"    caminho: {fonte_disco}\n"
        "    fases_aplicaveis: [1, 2, 3]\n"
    )
    monkeypatch.setattr("felinet.comandos.datasets.__name__", "felinet.comandos.datasets")
    monkeypatch.setattr("felinet.config.raiz_projeto", lambda: raiz)
    return raiz, fonte_disco


def test_listar_sem_arquivo_da_mensagem_amigavel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raiz = tmp_path / "repo"
    (raiz / "configs").mkdir(parents=True)
    monkeypatch.setattr("felinet.config.raiz_projeto", lambda: raiz)
    res = runner.invoke(datasets_app, ["listar"])
    assert res.exit_code == 0
    assert "Configure seus datasets" in res.output


def test_listar_com_yaml_mostra_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup_repo(tmp_path, monkeypatch)
    res = runner.invoke(datasets_app, ["listar"])
    assert res.exit_code == 0
    assert "kaggle_cats" in res.output
    assert "camera_trap_brutas" in res.output


def test_linkar_cria_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raiz, fonte_disco = _setup_repo(tmp_path, monkeypatch)
    res = runner.invoke(datasets_app, ["linkar", "--nome", "kaggle_cats"])
    assert res.exit_code == 0, res.output
    link = raiz / "data" / "raw" / "camera_trap" / "kaggle_cats"
    assert link.is_symlink()
    assert link.resolve() == fonte_disco.resolve()


def test_linkar_apenas_planejar_nao_cria(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raiz, _ = _setup_repo(tmp_path, monkeypatch)
    res = runner.invoke(
        datasets_app,
        ["linkar", "--nome", "kaggle_cats", "--apenas-planejar"],
    )
    assert res.exit_code == 0
    link = raiz / "data" / "raw" / "camera_trap" / "kaggle_cats"
    assert not link.exists()


def test_linkar_nome_inexistente_da_erro(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup_repo(tmp_path, monkeypatch)
    res = runner.invoke(datasets_app, ["linkar", "--nome", "nao_existe"])
    assert res.exit_code != 0
