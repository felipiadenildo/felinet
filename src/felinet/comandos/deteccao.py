"""Subcomandos: felinet deteccao ..."""

from __future__ import annotations

from pathlib import Path

import typer

from felinet.config import carregar_perfil
from felinet.logging_setup import obter_logger

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.deteccao")


@app.command("executar")
def executar(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
    confianca: float = typer.Option(0.20, "--confianca", help="Threshold do MegaDetector."),
    saida: Path | None = typer.Option(None, "--saida"),
) -> None:
    """Roda MegaDetector v6 sobre as imagens cruas do perfil ativo.

    Mapeia o processo P3 do DFD. Saida default:
    ``<saida_deteccoes>/deteccoes.json``.
    """
    from felinet.pipeline.fase2_deteccao.megadetector import DetectorMegaDetectorV6
    from felinet.pipeline.fase2_deteccao.schema import salvar_resultados_json

    cfg = carregar_perfil(perfil)
    saida_efetiva = saida or (cfg.saida_deteccoes / "deteccoes.json")
    detector = DetectorMegaDetectorV6()

    extensoes = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    imagens = sorted(p for p in cfg.raw_camera_trap.rglob("*") if p.suffix.lower() in extensoes)

    resultados = []
    for img in imagens:
        LOG.info(f"detectando: {img.name}")
        resultados.append(detector.detectar(img, limite_confianca=confianca))

    salvar_resultados_json(resultados, saida_efetiva)
    typer.echo(f"OK: {len(resultados)} imagens processadas -> {saida_efetiva}")


@app.command("visualizar")
def visualizar(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
    entrada: Path | None = typer.Option(None, "--entrada", help="JSON de deteccoes."),
    saida: Path | None = typer.Option(None, "--saida", help="Pasta para imagens anotadas."),
) -> None:
    """Desenha bboxes do JSON de deteccoes sobre as imagens originais."""
    from felinet.pipeline.fase2_deteccao.visualizar import visualizar as _visualizar

    cfg = carregar_perfil(perfil)
    arquivo_entrada = entrada or (cfg.saida_deteccoes / "deteccoes.json")
    pasta_saida = saida or (cfg.artifacts_figuras / "exemplos")
    pasta_saida.mkdir(parents=True, exist_ok=True)
    codigo = _visualizar(arquivo_entrada, pasta_saida)
    raise typer.Exit(code=codigo)
