"""Subcomandos: felinet tabelas ...

Gera tabelas CSV + .tex (booktabs) para inclusao na monografia
(artifacts/tabelas/).
"""
from __future__ import annotations

import json
from pathlib import Path

import typer

from felinet.config import carregar_perfil
from felinet.logging_setup import obter_logger
from felinet.utils.tex import csv_para_booktabs

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.tabelas")


@app.command("reid-resumo")
def reid_resumo(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    ns: str = typer.Option("50,200,500", "--ns", help="Lista de N para incluir."),
    saida: Path | None = typer.Option(None, "--saida"),
) -> None:
    """Tabela resumo da avaliacao Re-ID (closed-set) variando N."""
    cfg = carregar_perfil(perfil)
    valores_n = [int(s) for s in ns.split(",")]

    linhas = [["N", "Top-1", "Top-5", "Top-10", "n_query", "n_galeria"]]
    for n in valores_n:
        latest = cfg.processed / f"avaliacao_reid_petface_n{n:04d}_latest.json"
        if not latest.exists():
            LOG.warning(f"N={n}: avaliacao ausente ({latest.name})")
            continue
        payload = json.loads(latest.read_text(encoding="utf-8"))
        rel = payload["relatorio"]
        linhas.append([
            str(n),
            f"{rel['top_1']:.3f}",
            f"{rel.get('top_5', rel['cmc'][4] if len(rel['cmc']) >= 5 else 0):.3f}",
            f"{rel.get('top_10', rel['cmc'][9] if len(rel['cmc']) >= 10 else 0):.3f}",
            str(payload["n_query"]),
            str(payload["n_galeria"]),
        ])

    saida_csv = saida or (cfg.artifacts_tabelas / "reid_resumo.csv")
    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    saida_csv.write_text(
        "\n".join(",".join(c) for c in linhas), encoding="utf-8",
    )

    saida_tex = saida_csv.with_suffix(".tex")
    csv_para_booktabs(
        saida_csv, saida_tex,
        legenda="Avaliacao Re-ID closed-set sobre PetFace cat para diferentes N.",
        rotulo="tab:reid-resumo",
    )
    typer.echo(f"OK: {saida_csv} + {saida_tex}")


@app.command("openset-resumo")
def openset_resumo(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    ns: str = typer.Option("50,200,500", "--ns"),
    saida: Path | None = typer.Option(None, "--saida"),
) -> None:
    """Tabela resumo open-set (AUC + thresholds) variando N."""
    cfg = carregar_perfil(perfil)
    valores_n = [int(s) for s in ns.split(",")]

    linhas = [["N", "AUC (media +/- std)", "TAR@FAR=1%", "n_seeds"]]
    for n in valores_n:
        arq = cfg.processed / f"avaliacao_openset_petface_n{n:04d}_latest.json"
        if not arq.exists():
            LOG.warning(f"N={n}: openset ausente")
            continue
        payload = json.loads(arq.read_text(encoding="utf-8"))
        tar = payload["por_seed"][0]["relatorio"].get("tar_at_far_01", 0.0)
        linhas.append([
            str(n),
            f"{payload['auc_media']:.3f} +/- {payload['auc_desvio']:.3f}",
            f"{tar:.3f}",
            str(len(payload["seeds"])),
        ])

    saida_csv = saida or (cfg.artifacts_tabelas / "openset_resumo.csv")
    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    saida_csv.write_text(
        "\n".join(",".join(c) for c in linhas), encoding="utf-8",
    )
    saida_tex = saida_csv.with_suffix(".tex")
    csv_para_booktabs(
        saida_csv, saida_tex,
        legenda="Avaliacao Re-ID open-set sobre PetFace cat (media de 3 seeds).",
        rotulo="tab:openset-resumo",
    )
    typer.echo(f"OK: {saida_csv} + {saida_tex}")


@app.command("datasets-avaliados")
def datasets_avaliados(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
) -> None:
    """Regera a tabela 'datasets avaliados vs descartados'.

    Conteudo curado em ``docs/datasets/justificativa_uso.md`` --
    este comando gera a versao .tex consumida pelo Capitulo 4.
    """
    cfg = carregar_perfil(perfil)
    fonte = cfg.artifacts_tabelas / "datasets_avaliados.csv"
    if not fonte.exists():
        LOG.error(f"CSV-fonte ausente: {fonte}")
        LOG.error("Gere/edite manualmente em artifacts/tabelas/datasets_avaliados.csv.")
        raise typer.Exit(code=1)
    saida_tex = fonte.with_suffix(".tex")
    csv_para_booktabs(
        fonte, saida_tex,
        legenda="Datasets avaliados durante o desenvolvimento e veredito de uso.",
        rotulo="tab:datasets-avaliados",
    )
    typer.echo(f"OK: {saida_tex}")
