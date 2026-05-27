"""Subcomandos: felinet pipeline ...

Modo OPERACIONAL (cascata I -> II -> III -> IV) sobre uma FONTE de dados.

A fonte e identificada por slug registrado em ``configs/paths.yaml`` ->
``fontes:``. Exemplos: ``kaggle_cats``, ``lila_ena24``, ``campus2_2025``,
``dev_placeholders``. Cada execucao cria um diretorio rastreavel em
``runs/operacional/<fonte>/<perfil>/_/<gitsha>[__<tag>]/``.

Ver docs/arquitetura/layout_runs.md.
"""

from __future__ import annotations

import json

import typer

from felinet.config import carregar_perfil, fonte_default, resolver_fonte
from felinet.logging_setup import obter_logger
from felinet.runs import criar_run, finalizar_run, listar_runs

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.pipeline")


@app.command("executar")
def executar(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
    fonte: str = typer.Option(
        None,
        "--fonte",
        "-f",
        help="Slug da fonte (configs/paths.yaml -> fontes:). Default do perfil se omitido.",
    ),
    tag: str = typer.Option(
        None,
        "--tag",
        "-t",
        help="Sufixo opcional para distinguir runs com mesmo git_sha.",
    ),
    confianca_deteccao: float = typer.Option(
        0.20,
        "--confianca-deteccao",
        help="Threshold do MegaDetector (default 0.20).",
    ),
    anotacao: str = typer.Option(
        None,
        "--anotacao",
        help="Caminho opcional para arquivo de anotacao de identidade (dev).",
    ),
    max_amostras: int = typer.Option(
        0,
        "--max-amostras",
        help="Limite de imagens amostradas da fonte (0 = todas). Amostragem determinística.",
    ),
    seed_amostragem: int = typer.Option(
        42,
        "--seed-amostragem",
        help="Seed para amostragem determinística quando --max-amostras > 0.",
    ),
    dev_visual: bool = typer.Option(
        False,
        "--dev",
        help="Modo dev: gera galeria visual de descartes/bbox/crops em "
        "runs/.../dev_visualizacao/.",
    ),
) -> None:
    """Roda a cascata completa I -> II -> III -> IV sobre a fonte selecionada.

    Saidas vao para ``runs/operacional/<fonte>/<perfil>/_/<gitsha>[__<tag>]/``.
    """
    from pathlib import Path

    from felinet.pipeline.orquestrador import executar_cascata

    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "operacional")
    pasta_brutas = resolver_fonte(cfg, fonte_efetiva)

    LOG.info(f"Cascata: perfil={perfil}, fonte={fonte_efetiva}, brutas={pasta_brutas}")

    extras = {
        "comando": "pipeline executar",
        "confianca_deteccao": confianca_deteccao,
        "anotacao_origem": str(anotacao) if anotacao else None,
        "max_amostras": max_amostras,
        "seed_amostragem": seed_amostragem,
        "dev_visual": dev_visual,
    }
    run = criar_run(
        perfil=cfg,
        modo="operacional",
        fonte=fonte_efetiva,
        tag=tag,
        extras=extras,
    )
    LOG.info(f"Run criado: {run.raiz}")

    anotacao_path = Path(anotacao) if anotacao else None
    try:
        relatorio = executar_cascata(
            pasta_brutas=pasta_brutas,
            run=run,
            confianca_min_deteccao=confianca_deteccao,
            anotacao_identidade_origem=anotacao_path,
            max_amostras=max_amostras,
            seed_amostragem=seed_amostragem,
            dev_visual=dev_visual,
        )
    except Exception as exc:  # noqa: BLE001
        finalizar_run(run, sucesso=False, mensagem=str(exc))
        raise

    finalizar_run(
        run,
        sucesso=relatorio.sucesso,
        mensagem=relatorio.mensagem,
        metricas_resumo=relatorio.como_dicionario(),
    )

    saida = {
        "run_path": str(run.raiz),
        "manifest": str(run.manifest_path),
        **relatorio.como_dicionario(),
    }
    typer.echo(json.dumps(saida, indent=2, ensure_ascii=False))
    if not relatorio.sucesso:
        raise typer.Exit(code=1)


@app.command("listar")
def listar(
    perfil: str = typer.Option(None, "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
) -> None:
    """Lista runs operacionais existentes em ``runs/``."""
    from felinet.config import raiz_projeto

    cfg = carregar_perfil(perfil) if perfil else None
    raiz_runs = raiz_projeto() / ((cfg.extras.get("raiz_runs") if cfg else None) or "runs")
    registros = listar_runs(
        raiz_runs,
        modo="operacional",
        fonte=fonte,
        perfil=cfg.nome if cfg else None,
    )
    if not registros:
        typer.echo("(nenhum run operacional encontrado)")
        return
    for r in registros:
        m = r.manifest
        sucesso = "OK" if m.get("sucesso") else ("--" if m.get("sucesso") is None else "X")
        resumo = m.get("metricas_resumo") or {}
        emb = resumo.get("n_embeddings", "?")
        typer.echo(
            f"[{sucesso}] {m.get('data_inicio', '?')} "
            f"{m.get('fonte', '?'):20s} {m.get('perfil', '?'):5s} "
            f"git={m.get('git_sha', '?')} emb={emb} -> {r.raiz}"
        )


@app.command("resumir")
def resumir(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
) -> None:
    """Imprime resumo do run latest (operacional) para a fonte selecionada."""
    from felinet.config import raiz_projeto
    from felinet.runs import resolver_latest

    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "operacional")
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    alvo = resolver_latest(
        modo="operacional",
        fonte=fonte_efetiva,
        perfil=cfg.nome,
        raiz_runs=raiz_runs,
    )
    if alvo is None:
        typer.echo(f"(nenhum run latest para operacional/{fonte_efetiva}/{cfg.nome})")
        return
    typer.echo(f"latest -> {alvo}")
    checagens = [
        ("manifesto", alvo / "02_manifesto" / "manifesto.csv"),
        ("deteccoes", alvo / "03_deteccoes" / "deteccoes.json"),
        ("classificacoes", alvo / "04_classificacoes" / "classificacoes.json"),
        ("crops", alvo / "05_crops_felis_catus"),
        ("anotacao_identidade", alvo / "06_anotacao_identidade.json"),
        ("embeddings", alvo / "07_embeddings.npz"),
        ("avaliacao_pipeline", alvo / "08_avaliacao_pipeline.json"),
    ]
    for nome, caminho in checagens:
        marca = "OK" if caminho.exists() else "--"
        typer.echo(f"[{marca}] {nome:24s} {caminho.relative_to(alvo)}")
