"""Subcomandos: felinet ingestao ..."""

from __future__ import annotations

from pathlib import Path

import typer

from felinet.config import carregar_perfil, fonte_default, resolver_fonte
from felinet.logging_setup import obter_logger
from felinet.runs import criar_run, finalizar_run

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.ingestao")


@app.command("manifesto")
def manifesto(
    perfil: str = typer.Option("dev", "--perfil", "-p", help="Perfil de paths."),
    fonte: str = typer.Option(
        None,
        "--fonte",
        "-f",
        help="Fonte registrada em paths.yaml (default: fonte_default_operacional do perfil).",
    ),
    tag: str = typer.Option(None, "--tag", "-t"),
    saida: Path | None = typer.Option(
        None, "--saida", help="Override do arquivo de saida (modo legado)."
    ),
) -> None:
    """Gera manifesto CSV (SHA256 + EXIF + dimensoes) das imagens cruas.

    Mapeia o processo P2 do DFD. Saida default:
    ``runs/operacional/<fonte>/<perfil>/_/<gitsha>[__tag]/manifesto.csv``.
    Quando ``--saida`` e passado, escreve no caminho explicito (modo legado,
    sem registrar run em ``runs/``).
    """
    from felinet.pipeline.fase1_ingestao.manifesto import gerar_manifesto

    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "operacional")
    raiz_fonte = resolver_fonte(cfg, fonte_efetiva)

    if saida is not None:
        LOG.info(f"[modo legado] {raiz_fonte} -> {saida}")
        entradas = gerar_manifesto(raiz_fonte, saida)
        typer.echo(f"OK: {len(entradas)} entradas gravadas em {saida}")
        return

    extras = {"comando": "ingestao manifesto", "fonte_raiz": str(raiz_fonte)}
    run = criar_run(
        perfil=cfg,
        modo="operacional",
        fonte=fonte_efetiva,
        tag=tag,
        extras=extras,
    )
    saida_efetiva = run.raiz / "manifesto.csv"
    LOG.info(f"Run: {run.raiz}")
    LOG.info(f"Gerando manifesto: {raiz_fonte} -> {saida_efetiva}")

    try:
        entradas = gerar_manifesto(raiz_fonte, saida_efetiva)
        finalizar_run(
            run,
            metricas_resumo={"n_entradas": len(entradas)},
            sucesso=True,
        )
        typer.echo(f"OK: {len(entradas)} entradas -> {saida_efetiva}")
    except Exception as exc:
        finalizar_run(run, sucesso=False, mensagem=str(exc))
        raise
