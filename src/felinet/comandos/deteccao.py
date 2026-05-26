"""Subcomandos: felinet deteccao ..."""

from __future__ import annotations

from pathlib import Path

import typer

from felinet.config import carregar_perfil, fonte_default, resolver_fonte
from felinet.logging_setup import obter_logger
from felinet.runs import criar_run, finalizar_run, resolver_latest

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.deteccao")


@app.command("executar")
def executar(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    confianca: float = typer.Option(0.20, "--confianca", help="Threshold do MegaDetector."),
    tag: str = typer.Option(None, "--tag", "-t"),
    saida: Path | None = typer.Option(
        None, "--saida", help="Override de saida (modo legado, sem run em runs/)."
    ),
) -> None:
    """Roda MegaDetector v6 sobre as imagens cruas da fonte.

    Mapeia o processo P3 do DFD. Saida default:
    ``runs/operacional/<fonte>/<perfil>/_/<gitsha>[__tag]/deteccoes.json``.
    """
    from felinet.pipeline.fase2_deteccao.megadetector import DetectorMegaDetectorV6
    from felinet.pipeline.fase2_deteccao.schema import salvar_resultados_json

    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "operacional")
    raiz_fonte = resolver_fonte(cfg, fonte_efetiva)

    extensoes = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    imagens = sorted(p for p in raiz_fonte.rglob("*") if p.suffix.lower() in extensoes)

    detector = DetectorMegaDetectorV6()
    resultados = []
    for img in imagens:
        LOG.info(f"detectando: {img.name}")
        resultados.append(detector.detectar(img, limite_confianca=confianca))

    if saida is not None:
        salvar_resultados_json(resultados, saida)
        typer.echo(f"OK: {len(resultados)} imagens processadas -> {saida}")
        return

    extras = {
        "comando": "deteccao executar",
        "fonte_raiz": str(raiz_fonte),
        "confianca": confianca,
        "n_imagens": len(imagens),
    }
    run = criar_run(
        perfil=cfg,
        modo="operacional",
        fonte=fonte_efetiva,
        tag=tag,
        extras=extras,
    )
    saida_efetiva = run.raiz / "deteccoes.json"
    LOG.info(f"Run: {run.raiz} -> {saida_efetiva}")
    try:
        salvar_resultados_json(resultados, saida_efetiva)
        n_animais = sum(1 for r in resultados for d in r.deteccoes if d.categoria == "animal")
        finalizar_run(
            run,
            metricas_resumo={
                "n_imagens": len(resultados),
                "n_animais_detectados": n_animais,
                "confianca": confianca,
            },
            sucesso=True,
        )
        typer.echo(f"OK: {len(resultados)} imagens processadas -> {saida_efetiva}")
    except Exception as exc:
        finalizar_run(run, sucesso=False, mensagem=str(exc))
        raise


@app.command("visualizar")
def visualizar(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    entrada: Path | None = typer.Option(
        None, "--entrada", help="JSON de deteccoes (default: latest run de deteccao)."
    ),
    saida: Path | None = typer.Option(None, "--saida", help="Pasta para imagens anotadas."),
) -> None:
    """Desenha bboxes do JSON de deteccoes sobre as imagens originais."""
    from felinet.pipeline.fase2_deteccao.visualizar import visualizar as _visualizar

    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "operacional")

    if entrada is None:
        raiz_runs = Path(cfg.extras.get("raiz_runs") or "runs")
        if not raiz_runs.is_absolute():
            from felinet.config import raiz_projeto

            raiz_runs = raiz_projeto() / raiz_runs
        latest = resolver_latest(
            modo="operacional",
            fonte=fonte_efetiva,
            perfil=cfg.nome,
            raiz_runs=raiz_runs,
        )
        if latest is None or not (latest / "deteccoes.json").exists():
            LOG.error(
                f"Nenhum run operacional encontrado para fonte={fonte_efetiva} perfil={cfg.nome}."
                " Rode 'felinet deteccao executar' antes."
            )
            raise typer.Exit(code=1)
        entrada = latest / "deteccoes.json"

    pasta_saida = saida or (cfg.artifacts_figuras / "exemplos" / fonte_efetiva)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    codigo = _visualizar(entrada, pasta_saida)
    raise typer.Exit(code=codigo)
