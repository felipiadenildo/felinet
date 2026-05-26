"""Subcomandos: felinet figuras ...

Gera figuras 300 DPI para inclusao na monografia (artifacts/figuras/).
"""
from __future__ import annotations

import json
from pathlib import Path

import typer

from felinet.config import carregar_perfil
from felinet.logging_setup import obter_logger

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.figuras")


@app.command("reid-cmc")
def reid_cmc(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    n: int = typer.Option(200, "--n"),
    saida: Path | None = typer.Option(None, "--saida"),
) -> None:
    """Gera curva CMC (Top-K vs K) a partir de ``avaliacao_reid_petface_*``."""
    import matplotlib.pyplot as plt
    import numpy as np

    cfg = carregar_perfil(perfil)
    arquivo = cfg.processed / f"avaliacao_reid_petface_n{n:04d}_latest.json"
    if not arquivo.exists():
        # tenta latest geral
        arquivo = cfg.processed / "avaliacao_reid_petface_latest.json"
    if not arquivo.exists():
        LOG.error(f"Avaliacao Re-ID nao encontrada para n={n}.")
        raise typer.Exit(code=1)

    payload = json.loads(arquivo.read_text(encoding="utf-8"))
    cmc = payload["relatorio"]["cmc"]
    ks = np.arange(1, len(cmc) + 1)
    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    ax.plot(ks, np.asarray(cmc) * 100, marker="o", linewidth=1.5)
    ax.set_xlabel("Rank K")
    ax.set_ylabel("Acerto cumulativo (%)")
    ax.set_title(f"Curva CMC - PetFace cat (N={n})")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    fig.tight_layout()

    saida_arq = saida or (cfg.artifacts_figuras / f"reid_cmc_n{n:04d}.png")
    saida_arq.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida_arq, dpi=300, bbox_inches="tight")
    plt.close(fig)
    typer.echo(f"OK: {saida_arq}")


@app.command("matriz-similaridade")
def matriz_similaridade(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    n: int = typer.Option(50, "--n"),
    saida: Path | None = typer.Option(None, "--saida"),
) -> None:
    """Heatmap de similaridade cosseno (query x galeria) para um subset."""
    import matplotlib.pyplot as plt
    import numpy as np

    cfg = carregar_perfil(perfil)
    arquivo_emb = cfg.interim / f"embeddings_petface_n{n:04d}.npz"
    if not arquivo_emb.exists():
        LOG.error(f"Cache nao encontrado: {arquivo_emb}")
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
    ax.set_title(f"Similaridade cosseno - PetFace (N={n})")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()

    saida_arq = saida or (cfg.artifacts_figuras / f"reid_matriz_sim_n{n:04d}.png")
    saida_arq.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida_arq, dpi=300, bbox_inches="tight")
    plt.close(fig)
    typer.echo(f"OK: {saida_arq}")
