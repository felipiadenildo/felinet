"""Subcomandos: felinet tabelas ...

Gera tabelas CSV + .tex (booktabs) para inclusao na monografia. Le metricas
dos runs metodologicos latest (closed e openset) e agrega em uma unica
linha por N. Saida em ``artifacts/tabelas/<modo>/<fonte>/``.
"""
from __future__ import annotations

import json
from pathlib import Path

import typer

from felinet.config import carregar_perfil, fonte_default, raiz_projeto
from felinet.logging_setup import obter_logger
from felinet.runs import resolver_latest
from felinet.utils.tex import csv_para_booktabs

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.tabelas")


def _pasta_artifacts(cfg, modo: str, fonte: str) -> Path:
    raiz = raiz_projeto() / (cfg.extras.get("artifacts_tabelas_raiz") or "artifacts/tabelas")
    return raiz / modo / fonte


def _ler_metricas_closed(raiz_runs: Path, fonte: str, perfil_nome: str, n: int) -> dict | None:
    alvo = resolver_latest(
        modo="metodologico", fonte=fonte, perfil=perfil_nome,
        protocolo=f"n{n:04d}", raiz_runs=raiz_runs,
    )
    if alvo is None:
        return None
    arq = alvo / "metricas.json"
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None


def _ler_metricas_openset(raiz_runs: Path, fonte: str, perfil_nome: str, n: int) -> dict | None:
    alvo = resolver_latest(
        modo="metodologico", fonte=fonte, perfil=perfil_nome,
        protocolo=f"openset_n{n:04d}", raiz_runs=raiz_runs,
    )
    if alvo is None:
        return None
    arq = alvo / "metricas.json"
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None


@app.command("reid-resumo")
def reid_resumo(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    ns: str = typer.Option("50,200,500", "--ns"),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Tabela resumo Re-ID closed-set variando N (lendo runs latest)."""
    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "metodologico")
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    valores_n = [int(s) for s in ns.split(",")]

    linhas = [["N", "Top-1", "Top-5", "Top-10", "n_query", "n_galeria"]]
    for n in valores_n:
        payload = _ler_metricas_closed(raiz_runs, fonte_efetiva, cfg.nome, n)
        if payload is None:
            LOG.warning(f"N={n}: avaliacao ausente em runs/")
            continue
        rel = payload["relatorio"]
        cmc = rel.get("cmc", [])
        top5 = rel.get("top_5", cmc[4] if len(cmc) >= 5 else 0)
        top10 = rel.get("top_10", cmc[9] if len(cmc) >= 10 else 0)
        linhas.append([
            str(n),
            f"{rel['top_1']:.3f}",
            f"{top5:.3f}",
            f"{top10:.3f}",
            str(payload["n_query"]),
            str(payload["n_galeria"]),
        ])

    pasta = _pasta_artifacts(cfg, "metodologico", fonte_efetiva)
    saida_csv = saida or (pasta / "reid_resumo.csv")
    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    saida_csv.write_text("\n".join(",".join(c) for c in linhas), encoding="utf-8")

    saida_tex = saida_csv.with_suffix(".tex")
    csv_para_booktabs(
        saida_csv, saida_tex,
        legenda=f"Avaliacao Re-ID closed-set sobre {fonte_efetiva} para diferentes N.",
        rotulo=f"tab:reid-resumo-{fonte_efetiva}",
    )
    typer.echo(f"OK: {saida_csv} + {saida_tex}")


@app.command("openset-resumo")
def openset_resumo(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    ns: str = typer.Option("50,200,500", "--ns"),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Tabela resumo open-set (AUC + TAR@FAR) variando N."""
    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "metodologico")
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    valores_n = [int(s) for s in ns.split(",")]

    linhas = [["N", "AUC (media +/- std)", "TAR@FAR=1%", "n_seeds"]]
    for n in valores_n:
        payload = _ler_metricas_openset(raiz_runs, fonte_efetiva, cfg.nome, n)
        if payload is None:
            LOG.warning(f"N={n}: openset ausente em runs/")
            continue
        tar = payload["por_seed"][0]["relatorio"].get("tar_at_far_01", 0.0)
        linhas.append([
            str(n),
            f"{payload['auc_media']:.3f} +/- {payload['auc_desvio']:.3f}",
            f"{tar:.3f}",
            str(len(payload["seeds"])),
        ])

    pasta = _pasta_artifacts(cfg, "metodologico", fonte_efetiva)
    saida_csv = saida or (pasta / "openset_resumo.csv")
    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    saida_csv.write_text("\n".join(",".join(c) for c in linhas), encoding="utf-8")
    saida_tex = saida_csv.with_suffix(".tex")
    csv_para_booktabs(
        saida_csv, saida_tex,
        legenda=f"Avaliacao Re-ID open-set sobre {fonte_efetiva} (media de seeds).",
        rotulo=f"tab:openset-resumo-{fonte_efetiva}",
    )
    typer.echo(f"OK: {saida_csv} + {saida_tex}")


@app.command("datasets-avaliados")
def datasets_avaliados(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
) -> None:
    """Regera a tabela 'datasets avaliados vs descartados' (.tex)."""
    cfg = carregar_perfil(perfil)
    raiz = raiz_projeto() / (cfg.extras.get("artifacts_tabelas_raiz") or "artifacts/tabelas")
    fonte = raiz / "datasets_avaliados.csv"
    if not fonte.exists():
        LOG.error(f"CSV-fonte ausente: {fonte}")
        raise typer.Exit(code=1)
    saida_tex = fonte.with_suffix(".tex")
    csv_para_booktabs(
        fonte, saida_tex,
        legenda="Datasets avaliados durante o desenvolvimento e veredito de uso.",
        rotulo="tab:datasets-avaliados",
    )
    typer.echo(f"OK: {saida_tex}")
