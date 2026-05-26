"""Testes para felinet figuras matriz-confusao-fontes (Bloco 9)."""

from __future__ import annotations

from typer.testing import CliRunner

from felinet.comandos.figuras import app as figuras_app

runner = CliRunner()


def test_matriz_confusao_fontes_sem_dados_avisa() -> None:
    """Sem runs de classificação, deve sair com código 0 e listar avisos."""
    res = runner.invoke(figuras_app, ["matriz-confusao-fontes", "--perfil", "prod"])
    assert res.exit_code == 0, res.output
    assert (
        "nenhuma fonte" in res.output.lower()
        or "sem run" in res.output.lower()
        or "matriz" in res.output.lower()
    )


def test_matriz_confusao_fontes_help() -> None:
    res = runner.invoke(figuras_app, ["matriz-confusao-fontes", "--help"])
    assert res.exit_code == 0
    assert "matriz" in res.output.lower()
