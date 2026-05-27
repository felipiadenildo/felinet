"""Testes mínimos do wizard easyrun (mock subprocess)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


def test_modulo_importa() -> None:
    from felinet.comandos import easyrun  # noqa: F401

    assert hasattr(easyrun, "app")
    assert hasattr(easyrun, "_despachar")


def test_despachar_linkar_chama_subprocess() -> None:
    from felinet.comandos import easyrun

    with patch("felinet.comandos.easyrun.subprocess.run") as run:
        easyrun._despachar("Linkar datasets (criar symlinks)")
    assert run.called
    args = run.call_args[0][0]
    assert "datasets" in args
    assert "linkar" in args


def test_despachar_listar_chama_subprocess() -> None:
    from felinet.comandos import easyrun

    with patch("felinet.comandos.easyrun.subprocess.run") as run:
        easyrun._despachar("Listar status dos datasets")
    assert run.called


def test_wizard_pipeline_filtra_por_fase1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ao montar o menu de fonte, só entram datasets com fase 1 aplicável."""
    from felinet.comandos import easyrun
    from felinet.datasets.registro import DatasetLocal

    datasets = {
        "kaggle_cats": DatasetLocal(
            nome="kaggle_cats",
            tipo="camera_trap_brutas",
            layout="flat",
            caminho=tmp_path,
            fases_aplicaveis=[1, 2, 3],
        ),
        "petface": DatasetLocal(
            nome="petface",
            tipo="reid_crops_rotulados",
            layout="por_identidade",
            caminho=tmp_path,
            fases_aplicaveis=[4],
        ),
    }
    monkeypatch.setattr(
        easyrun, "carregar_datasets_locais", lambda *a, **kw: datasets
    )

    capturado: list[list[str]] = []

    class FakePergunta:
        def __init__(self, retorno):
            self.retorno = retorno

        def ask(self):
            return self.retorno

    def fake_select(_msg, choices=None, **_kw):
        capturado.append(list(choices))
        return FakePergunta(choices[0] if choices else None)

    monkeypatch.setattr(easyrun.questionary, "select", fake_select)
    monkeypatch.setattr(
        easyrun.questionary,
        "text",
        lambda *a, **kw: FakePergunta("10"),
    )
    monkeypatch.setattr(
        easyrun.questionary,
        "confirm",
        lambda *a, **kw: FakePergunta(False),
    )

    easyrun._wizard_pipeline()
    # primeira chamada de select recebe a lista de fontes válidas
    assert capturado, "select não foi chamado"
    fontes = capturado[0]
    assert "kaggle_cats" in fontes
    assert "petface" not in fontes
