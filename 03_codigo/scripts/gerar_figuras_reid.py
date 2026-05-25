"""Gera figuras 300dpi da avaliacao Re-ID para a monografia.

Usa o symlink ``avaliacao_reid_petface_latest.json`` para descobrir
qual run e o mais recente e localizar o cache de embeddings correspondente.

Saidas em 05_figuras/reid/ (com sufixo do N):
    cmc_curve_n{N:04d}.png
    matriz_similaridade_n{N:04d}.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ARQUIVO_AVALIACAO = Path("04_dados/processed/avaliacao_reid_petface_latest.json")
DIRETORIO_EMBEDDINGS = Path("04_dados/interim")
DIRETORIO_FIGURAS = Path("05_figuras/reid")


def gerar_cmc(cmc: list[float], saida: Path, titulo_extra: str) -> None:
    ks = np.arange(1, len(cmc) + 1)
    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    ax.plot(ks, np.asarray(cmc) * 100, marker="o", linewidth=1.5)
    ax.set_xlabel("Rank K")
    ax.set_ylabel("Acuracia Top-K (%)")
    ax.set_title(f"Curva CMC -- MegaDescriptor-T-224 / PetFace cat {titulo_extra}")
    ax.set_xticks(ks)
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(saida, dpi=300, bbox_inches="tight")
    plt.close(fig)


def gerar_heatmap(
    arquivo_embeddings: Path,
    saida: Path,
    titulo_extra: str,
    max_amostras: int = 50,
) -> None:
    npz = np.load(arquivo_embeddings)
    emb_q = npz["queries"]
    emb_g = npz["galerias"]

    nq = min(max_amostras, emb_q.shape[0])
    ng = min(max_amostras * 5, emb_g.shape[0])

    sim = emb_q[:nq] @ emb_g[:ng].T

    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    im = ax.imshow(sim, aspect="auto", cmap="viridis", vmin=-0.2, vmax=1.0)
    ax.set_xlabel(f"Galeria (n={ng})")
    ax.set_ylabel(f"Queries (n={nq})")
    ax.set_title(f"Matriz de similaridade cosseno {titulo_extra}")
    fig.colorbar(im, ax=ax, label="cosseno")
    fig.tight_layout()
    fig.savefig(saida, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    if not ARQUIVO_AVALIACAO.exists():
        print(
            f"ERRO: {ARQUIVO_AVALIACAO} nao existe. "
            f"Rode `make avaliar-reid` antes.",
            file=sys.stderr,
        )
        return 1

    with ARQUIVO_AVALIACAO.open(encoding="utf-8") as f:
        meta = json.load(f)
    n = meta["max_individuos"]
    arquivo_emb = DIRETORIO_EMBEDDINGS / f"embeddings_petface_n{n:04d}.npz"
    if not arquivo_emb.exists():
        print(
            f"ERRO: cache de embeddings nao encontrado: {arquivo_emb}",
            file=sys.stderr,
        )
        return 1

    DIRETORIO_FIGURAS.mkdir(parents=True, exist_ok=True)
    titulo_extra = f"(N={n})"

    print(f"[1/2] Gerando curva CMC (N={n})")
    cmc_path = DIRETORIO_FIGURAS / f"cmc_curve_n{n:04d}.png"
    gerar_cmc(meta["cmc"], cmc_path, titulo_extra)
    print(f"  salvo: {cmc_path}")

    print(f"[2/2] Gerando heatmap matriz similaridade (N={n})")
    heatmap_path = DIRETORIO_FIGURAS / f"matriz_similaridade_n{n:04d}.png"
    gerar_heatmap(arquivo_emb, heatmap_path, titulo_extra)
    print(f"  salvo: {heatmap_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
