"""Avaliacao Top-K para Re-ID no protocolo PetFace.

Protocolo:
    - Conjunto de queries: 1 imagem por individuo.
    - Conjunto de galeria: as demais imagens dos mesmos individuos
      (multi-imagens por ID, todas concatenadas em uma galeria global).
    - Para cada query, ranquear toda a galeria por similaridade de cosseno
      e verificar se o ID correto aparece nos K primeiros resultados.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ResultadoAvaliacao:
    """Resultado agregado de uma avaliacao Top-K."""

    top_k: dict[int, float]  # {k: acuracia}
    cmc: list[float]  # CMC[k-1] = acuracia top-k para k=1..K_max
    n_queries: int
    n_galeria: int
    dim_embedding: int


def matriz_similaridade_cosseno(
    queries: np.ndarray,
    galeria: np.ndarray,
) -> np.ndarray:
    """Calcula matriz de similaridade de cosseno entre queries e galeria.

    Assume embeddings L2-normalizados (entao cosseno = produto interno).

    Args:
        queries: (Nq, D) matriz de embeddings das queries.
        galeria: (Ng, D) matriz de embeddings da galeria.

    Returns:
        (Nq, Ng) matriz de similaridades em [-1, 1].
    """
    if queries.ndim != 2 or galeria.ndim != 2:
        raise ValueError("queries e galeria devem ser matrizes 2D")
    if queries.shape[1] != galeria.shape[1]:
        raise ValueError(
            f"dimensoes incompativeis: queries D={queries.shape[1]} "
            f"vs galeria D={galeria.shape[1]}"
        )
    return queries @ galeria.T


def avaliar_top_k(
    similaridades: np.ndarray,
    ids_query: list[int],
    ids_galeria: list[int],
    k_max: int = 10,
) -> ResultadoAvaliacao:
    """Calcula Top-K accuracy e curva CMC.

    Top-K: para cada query, ordena a galeria por similaridade decrescente;
    a query e considerada acerto se o ID correto aparece entre os top-K.

    Args:
        similaridades: (Nq, Ng) matriz de similaridade.
        ids_query: lista de Nq IDs (paralela a linhas de similaridades).
        ids_galeria: lista de Ng IDs (paralela a colunas de similaridades).
        k_max: maior K a calcular (default 10).

    Returns:
        ResultadoAvaliacao com top_k {1..k_max} e curva CMC.
    """
    nq, ng = similaridades.shape
    if len(ids_query) != nq:
        raise ValueError(
            f"len(ids_query)={len(ids_query)} != linhas={nq}"
        )
    if len(ids_galeria) != ng:
        raise ValueError(
            f"len(ids_galeria)={len(ids_galeria)} != colunas={ng}"
        )
    k_efetivo = min(k_max, ng)

    # Para cada query, indices da galeria ordenados por similaridade decrescente
    ordem = np.argsort(-similaridades, axis=1)  # (Nq, Ng)
    ids_galeria_arr = np.asarray(ids_galeria)

    acertos_por_k = np.zeros(k_efetivo, dtype=np.int64)
    for i, id_q in enumerate(ids_query):
        ranking = ids_galeria_arr[ordem[i, :k_efetivo]]
        # primeira posicao onde o ID correto aparece (ou -1)
        match = np.where(ranking == id_q)[0]
        if match.size > 0:
            primeira_pos = match[0]
            # acerto em todos os K >= primeira_pos+1
            acertos_por_k[primeira_pos:] += 1

    acc_por_k = acertos_por_k / nq
    return ResultadoAvaliacao(
        top_k={k: float(acc_por_k[k - 1]) for k in (1, 5, 10) if k <= k_efetivo},
        cmc=[float(x) for x in acc_por_k],
        n_queries=nq,
        n_galeria=ng,
        dim_embedding=0,  # preenchido pelo chamador
    )
