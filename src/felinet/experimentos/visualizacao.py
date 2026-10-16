"""Projeção de Visualização Exploratória (Fig. 16 da monografia).

Embeddings MegaDescriptor-T-224 de um catálogo de identidades (CatIndividualImages: uma
subpasta por indivíduo) projetados em 2D com UMAP. Ao contrário do protótipo ``felinet_mono``,
não há substituto silencioso: sem catálogo, o comando falha. O protótipo caía no Oxford-IIIT Pet
agrupado por raça quando o download do CatIndividualImages falhava.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from pathlib import Path

import numpy as np

EXTENSOES = {".jpg", ".jpeg", ".png"}


def selecionar_catalogo(
    pasta: Path,
    n_identidades: int = 20,
    min_por_id: int = 3,
    max_por_id: int = 8,
    semente: int = 42,
) -> list[tuple[str, Path]]:
    """Sorteia ``n_identidades`` (semente fixa) entre as que têm ao menos ``min_por_id`` imagens."""
    elegiveis = []
    for d in sorted(p for p in Path(pasta).iterdir() if p.is_dir()):
        imagens = sorted(q for q in d.iterdir() if q.suffix.lower() in EXTENSOES)
        if len(imagens) >= min_por_id:
            elegiveis.append((d.name, imagens[:max_por_id]))
    if not elegiveis:
        raise FileNotFoundError(f"nenhuma identidade com {min_por_id}+ imagens em {pasta}")
    escolhidas = random.Random(semente).sample(elegiveis, min(n_identidades, len(elegiveis)))
    return [(ident, img) for ident, imgs in sorted(escolhidas) for img in imgs]


def projetar_umap(
    vetores: np.ndarray, semente: int = 42, vizinhos: int = 15, dist_min: float = 0.1
) -> np.ndarray:
    import umap

    redutor = umap.UMAP(
        n_neighbors=min(vizinhos, len(vetores) - 1),
        min_dist=dist_min,
        metric="cosine",
        random_state=semente,
    )
    return redutor.fit_transform(vetores)


def visualizacao_exploratoria(
    itens: list[tuple[str, Path]],
    extrair: Callable[[Path], np.ndarray],
    projetar: Callable[[np.ndarray], np.ndarray] = projetar_umap,
) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Devolve ``(vetores, coordenadas 2D, linhas da tabela de projeção)``."""
    vetores = np.stack([extrair(caminho) for _, caminho in itens]).astype(np.float32)
    coords = projetar(vetores)
    linhas = [
        {"identity": ident, "file": caminho.name, "x": float(x), "y": float(y)}
        for (ident, caminho), (x, y) in zip(itens, coords, strict=True)
    ]
    return vetores, coords, linhas
