"""Subcomandos: felinet ingestao ..."""
from __future__ import annotations

from pathlib import Path

import typer

from felinet.config import carregar_perfil
from felinet.logging_setup import obter_logger

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.ingestao")


@app.command("manifesto")
def manifesto(
    perfil: str = typer.Option("dev", "--perfil", "-p", help="Perfil de paths."),
    saida: Path | None = typer.Option(None, "--saida", help="Override do arquivo de saida."),
) -> None:
    """Gera manifesto CSV (SHA256 + EXIF + dimensoes) das imagens cruas.

    Mapeia o processo P2 do DFD. Saida default em
    ``<saida_manifesto>/manifesto.csv`` do perfil ativo.
    """
    from felinet.pipeline.fase1_ingestao.manifesto import gerar_manifesto

    cfg = carregar_perfil(perfil)
    saida_efetiva = saida or (cfg.saida_manifesto / "manifesto.csv")
    LOG.info(f"Gerando manifesto: {cfg.raw_camera_trap} -> {saida_efetiva}")
    entradas = gerar_manifesto(cfg.raw_camera_trap, saida_efetiva)
    typer.echo(f"OK: {len(entradas)} entradas gravadas em {saida_efetiva}")
