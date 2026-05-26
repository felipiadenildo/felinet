"""Subcomandos: felinet figuras ...

Gera figuras 300 DPI para inclusao na monografia. Le dados do run latest
identificado por (modo, fonte, perfil, protocolo) em ``runs/latest/`` e
escreve PNG/PDF em ``artifacts/figuras/<modo>/<fonte>/<protocolo>/``.

Para forcar uma figura a partir de um run especifico (nao o latest),
use ``--run <caminho>``.
"""
from __future__ import annotations

import json
from pathlib import Path

import typer

from felinet.config import carregar_perfil, fonte_default, raiz_projeto
from felinet.logging_setup import obter_logger
from felinet.runs import resolver_latest

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.figuras")


def _resolver_run_metodologico(
    *,
    cfg, fonte: str | None, n: int, openset: bool, run: Path | None,
) -> tuple[Path, str, str]:
    """Retorna (caminho_run, fonte, protocolo)."""
    fonte_efetiva = fonte or fonte_default(cfg, "metodologico")
    protocolo = f"openset_n{n:04d}" if openset else f"n{n:04d}"
    if run:
        return Path(run), fonte_efetiva, protocolo
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    alvo = resolver_latest(
        modo="metodologico", fonte=fonte_efetiva, perfil=cfg.nome,
        protocolo=protocolo, raiz_runs=raiz_runs,
    )
    if alvo is None:
        raise typer.BadParameter(
            f"Nenhum run latest para metodologico/{fonte_efetiva}/{cfg.nome}/{protocolo}."
        )
    return alvo, fonte_efetiva, protocolo


def _pasta_artifacts(cfg, modo: str, fonte: str, protocolo: str | None = None) -> Path:
    raiz = raiz_projeto() / (cfg.extras.get("artifacts_figuras_raiz") or "artifacts/figuras")
    partes = [modo, fonte]
    if protocolo:
        partes.append(protocolo)
    return raiz.joinpath(*partes)


@app.command("reid-cmc")
def reid_cmc(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    n: int = typer.Option(200, "--n"),
    run: Path = typer.Option(None, "--run", help="Caminho explicito de um run."),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Curva CMC (Top-K vs K) a partir do run metodologico latest."""
    import matplotlib.pyplot as plt
    import numpy as np

    cfg = carregar_perfil(perfil)
    raiz_run, fonte_efetiva, protocolo = _resolver_run_metodologico(
        cfg=cfg, fonte=fonte, n=n, openset=False, run=run,
    )
    arquivo = raiz_run / "metricas.json"
    if not arquivo.exists():
        LOG.error(f"metricas.json ausente em {raiz_run}")
        raise typer.Exit(code=1)

    payload = json.loads(arquivo.read_text(encoding="utf-8"))
    cmc = payload["relatorio"]["cmc"]
    ks = np.arange(1, len(cmc) + 1)
    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    ax.plot(ks, np.asarray(cmc) * 100, marker="o", linewidth=1.5)
    ax.set_xlabel("Rank K")
    ax.set_ylabel("Acerto cumulativo (%)")
    ax.set_title(f"Curva CMC - {fonte_efetiva} (N={n})")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    fig.tight_layout()

    pasta = _pasta_artifacts(cfg, "metodologico", fonte_efetiva, protocolo)
    saida_arq = saida or (pasta / "reid_cmc.png")
    saida_arq.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida_arq, dpi=300, bbox_inches="tight")
    plt.close(fig)
    typer.echo(f"OK: {saida_arq}")


@app.command("matriz-similaridade")
def matriz_similaridade(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    n: int = typer.Option(50, "--n"),
    run: Path = typer.Option(None, "--run"),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Heatmap de similaridade cosseno (query x galeria) do run latest."""
    import matplotlib.pyplot as plt
    import numpy as np

    cfg = carregar_perfil(perfil)
    raiz_run, fonte_efetiva, protocolo = _resolver_run_metodologico(
        cfg=cfg, fonte=fonte, n=n, openset=False, run=run,
    )
    arquivo_emb = raiz_run / "07_embeddings.npz"
    if not arquivo_emb.exists():
        arquivo_emb = raiz_run / "embeddings.npz"
    if not arquivo_emb.exists():
        LOG.error(f"embeddings.npz ausente em {raiz_run}")
        raise typer.Exit(code=1)

    dados = np.load(arquivo_emb, allow_pickle=True)
    vetores, splits = dados["vetores"], dados["splits"]
    q = vetores[splits == "query"]
    g = vetores[splits == "gallery"]
    sim = q @ g.T

    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    im = ax.imshow(sim, cmap="viridis", aspect="auto")
    ax.set_xlabel("Galeria (i)")
    ax.set_ylabel("Query (j)")
    ax.set_title(f"Similaridade cosseno - {fonte_efetiva} (N={n})")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()

    pasta = _pasta_artifacts(cfg, "metodologico", fonte_efetiva, protocolo)
    saida_arq = saida or (pasta / "reid_matriz_sim.png")
    saida_arq.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida_arq, dpi=300, bbox_inches="tight")
    plt.close(fig)
    typer.echo(f"OK: {saida_arq}")
