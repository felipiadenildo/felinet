"""Ponto de entrada do CLI felinet.

Uso:
    felinet --help
    felinet --version
    felinet pipeline executar --perfil dev
    felinet reid avaliar-closed --n 200
    felinet figuras reid-cmc --n 200
    felinet dev preparar-petface-mini

Subcomandos sao definidos em ``felinet.comandos.*`` e registrados aqui.
"""

from __future__ import annotations

import typer

from felinet import __version__
from felinet.comandos import (
    classificacao,
    datasets,
    deteccao,
    dev,
    easyrun,
    figuras,
    ingestao,
    reid,
    tabelas,
)
from felinet.comandos import (
    pipeline as pipeline_cmd,
)
from felinet.logging_setup import configurar_logging

app = typer.Typer(
    name="felinet",
    help="Sistema de monitoramento por visao computacional de gatos do Campus 2.",
    no_args_is_help=True,
    add_completion=False,
)

app.add_typer(ingestao.app, name="ingestao", help="Fase I: ingestao + manifesto + EXIF.")
app.add_typer(deteccao.app, name="deteccao", help="Fase II: deteccao com MegaDetector.")
app.add_typer(
    classificacao.app, name="classificacao", help="Fase III: classificacao SpeciesNet + decisor."
)
app.add_typer(reid.app, name="reid", help="Fase IV: Re-ID MegaDescriptor (PetFace + cascata).")
app.add_typer(figuras.app, name="figuras", help="Gera figuras (PNG/PDF) para a monografia.")
app.add_typer(tabelas.app, name="tabelas", help="Gera tabelas (CSV + booktabs .tex).")
app.add_typer(pipeline_cmd.app, name="pipeline", help="Orquestrador da cascata I->II->III->IV.")
app.add_typer(dev.app, name="dev", help="Utilitarios de desenvolvimento (cascata dev, validacao).")
app.add_typer(datasets.app, name="datasets", help="Download e preparo de datasets externos.")
app.add_typer(
    easyrun.app,
    name="easyrun",
    help="Wizard interativo. RECOMENDADO para começar.",
)


def _versao_callback(valor: bool) -> None:
    if valor:
        typer.echo(f"felinet {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    versao: bool = typer.Option(  # noqa: FBT001
        False,
        "--version",
        "-v",
        callback=_versao_callback,
        is_eager=True,
        help="Mostra a versao e sai.",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="Nivel de log: DEBUG, INFO, WARNING, ERROR.",
    ),
) -> None:
    """felinet -- CLI principal."""
    configurar_logging(nivel=log_level)


if __name__ == "__main__":
    app()
