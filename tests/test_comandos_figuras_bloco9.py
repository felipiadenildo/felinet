"""Testes para felinet figuras matriz-confusao-fontes (Bloco 9, esqueleto)."""

from __future__ import annotations

from typer.testing import CliRunner

from felinet.comandos.figuras import app as figuras_app

runner = CliRunner()


def test_matriz_confusao_fontes_executa_sem_crashar() -> None:
    """O esqueleto deve sair com codigo 0 e imprimir mensagem de aviso."""
    res = runner.invoke(figuras_app, ["matriz-confusao-fontes", "--perfil", "prod"])
    assert res.exit_code == 0, res.output
    assert "esqueleto" in res.output.lower() or "matriz-confusao-fontes" in res.output


def test_matriz_confusao_fontes_help() -> None:
    res = runner.invoke(figuras_app, ["matriz-confusao-fontes", "--help"])
    assert res.exit_code == 0
    assert "matriz" in res.output.lower()
