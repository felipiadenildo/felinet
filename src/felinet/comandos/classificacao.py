"""Subcomandos: felinet classificacao ..."""

from __future__ import annotations

from pathlib import Path

import typer

from felinet.config import carregar_perfil, fonte_default, raiz_projeto
from felinet.logging_setup import obter_logger
from felinet.runs import criar_run, finalizar_run, resolver_latest

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.classificacao")


def _resolver_deteccoes_latest(cfg, fonte_efetiva: str) -> Path | None:
    raiz_runs = Path(cfg.extras.get("raiz_runs") or "runs")
    if not raiz_runs.is_absolute():
        raiz_runs = raiz_projeto() / raiz_runs
    latest = resolver_latest(
        modo="operacional",
        fonte=fonte_efetiva,
        perfil=cfg.nome,
        raiz_runs=raiz_runs,
    )
    if latest is None:
        return None
    arq = latest / "deteccoes.json"
    return arq if arq.exists() else None


@app.command("executar")
def executar(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    deteccoes: Path | None = typer.Option(
        None,
        "--deteccoes",
        help="JSON com deteccoes (default: deteccoes.json do run latest).",
    ),
    tag: str = typer.Option(None, "--tag", "-t"),
    saida: Path | None = typer.Option(
        None, "--saida", help="Override de saida (modo legado, sem run em runs/)."
    ),
) -> None:
    """Roda SpeciesNet sobre cada bbox 'animal' das deteccoes da Fase II.

    Mapeia o processo P4 do DFD. Saida default:
    ``runs/operacional/<fonte>/<perfil>/_/<gitsha>[__tag]/classificacoes.json``.
    """
    from felinet.pipeline.fase2_deteccao.schema import (
        ResultadoDeteccao,
    )
    from felinet.pipeline.fase2_deteccao.schema import (
        carregar_resultados_json as carregar_deteccoes,
    )
    from felinet.pipeline.fase3_classificacao.decisor import ConfigDecisor
    from felinet.pipeline.fase3_classificacao.schema import salvar_resultados_json
    from felinet.pipeline.fase3_classificacao.speciesnet import (
        ClassificadorSpeciesNet,
        CropEntrada,
    )

    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "operacional")

    if deteccoes is None:
        deteccoes = _resolver_deteccoes_latest(cfg, fonte_efetiva)
        if deteccoes is None:
            LOG.error(
                f"deteccoes.json nao encontrado para fonte={fonte_efetiva} perfil={cfg.nome}."
                " Rode 'felinet deteccao executar --fonte ...' antes."
            )
            raise typer.Exit(code=1)

    if not deteccoes.exists():
        LOG.error(f"Deteccoes nao encontradas: {deteccoes}")
        raise typer.Exit(code=1)

    resultados: list[ResultadoDeteccao] = carregar_deteccoes(deteccoes)
    classificador = ClassificadorSpeciesNet(config_decisor=ConfigDecisor())

    classificacoes = []
    for r in resultados:
        for i, det in enumerate(r.deteccoes):
            if det.categoria != "animal":
                continue
            entrada = CropEntrada(
                media_path=Path(r.media_path),
                bbox=det.bbox,
                indice=i,
            )
            classificacoes.append(classificador.classificar(entrada))

    if saida is not None:
        saida.parent.mkdir(parents=True, exist_ok=True)
        salvar_resultados_json(classificacoes, saida)
        typer.echo(f"OK: {len(classificacoes)} classificacoes -> {saida}")
        return

    extras = {
        "comando": "classificacao executar",
        "deteccoes_entrada": str(deteccoes),
        "n_classificacoes": len(classificacoes),
    }
    run = criar_run(
        perfil=cfg,
        modo="operacional",
        fonte=fonte_efetiva,
        tag=tag,
        extras=extras,
    )
    arquivo_saida = run.raiz / "classificacoes.json"
    try:
        salvar_resultados_json(classificacoes, arquivo_saida)
        n_felis = sum(1 for c in classificacoes if getattr(c, "status", "") == "felis_catus")
        finalizar_run(
            run,
            metricas_resumo={
                "n_classificacoes": len(classificacoes),
                "n_felis_catus": n_felis,
            },
            sucesso=True,
        )
        typer.echo(f"OK: {len(classificacoes)} classificacoes -> {arquivo_saida}")
    except Exception as exc:
        finalizar_run(run, sucesso=False, mensagem=str(exc))
        raise


@app.command("recortar")
def recortar(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    saida: Path | None = typer.Option(
        None, "--saida", help="Override de pasta de crops (modo legado)."
    ),
) -> None:
    """Persiste crops de bboxes classificadas como felis_catus.

    Le ``classificacoes.json`` e ``deteccoes.json`` do run operacional latest
    e grava arquivos PNG em ``<run>/crops_felis_catus/`` (ou em ``--saida``).
    """
    from felinet.pipeline.fase2_deteccao.schema import (
        carregar_resultados_json as carregar_deteccoes,
    )
    from felinet.pipeline.fase3_classificacao.crops import persistir_crops_felis_catus
    from felinet.pipeline.fase3_classificacao.schema import (
        carregar_resultados_json as carregar_classificacoes,
    )

    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "operacional")

    raiz_runs = Path(cfg.extras.get("raiz_runs") or "runs")
    if not raiz_runs.is_absolute():
        raiz_runs = raiz_projeto() / raiz_runs
    latest = resolver_latest(
        modo="operacional", fonte=fonte_efetiva, perfil=cfg.nome, raiz_runs=raiz_runs
    )
    if latest is None:
        LOG.error(f"Run operacional latest nao encontrado para fonte={fonte_efetiva}.")
        raise typer.Exit(code=1)

    arquivo_clf = latest / "classificacoes.json"
    arquivo_det = latest / "deteccoes.json"
    if not arquivo_clf.exists() or not arquivo_det.exists():
        LOG.error(
            f"Esperado classificacoes.json e deteccoes.json no run {latest}, mas faltam."
            " Re-rode classificacao executar (e/ou deteccao executar) com mesma --tag."
        )
        raise typer.Exit(code=1)

    pasta_saida = saida or (latest / "crops_felis_catus")
    classificacoes = carregar_classificacoes(arquivo_clf)
    resultados_det = carregar_deteccoes(arquivo_det)
    deteccoes_por_imagem = {
        str(r.media_path): [d.bbox for d in r.deteccoes] for r in resultados_det
    }

    crops = persistir_crops_felis_catus(
        classificacoes,
        deteccoes_por_imagem,
        pasta_saida,
    )
    typer.echo(f"OK: {len(crops)} crops persistidos -> {pasta_saida}")
