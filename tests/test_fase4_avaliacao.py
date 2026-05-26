"""Testes sinteticos para avaliacao Re-ID (protocolo queries x galeria)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from felinet.pipeline.fase4_reid.avaliacao import (  # noqa: E402
    ResultadoAvaliacao,
    avaliar_top_k,
    matriz_similaridade_cosseno,
)


def _l2(x: np.ndarray) -> np.ndarray:
    return x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-12)


def test_matriz_similaridade_self_diagonal_eh_um() -> None:
    """Quando queries == galeria, a diagonal e 1 (vetores L2-norm)."""
    embs = _l2(np.random.randn(4, 8).astype(np.float32))
    matriz = matriz_similaridade_cosseno(embs, embs)
    assert matriz.shape == (4, 4)
    np.testing.assert_allclose(np.diag(matriz), np.ones(4), atol=1e-5)


def test_matriz_similaridade_self_eh_simetrica() -> None:
    """Quando queries == galeria, M = M.T."""
    embs = _l2(np.random.randn(5, 16).astype(np.float32))
    matriz = matriz_similaridade_cosseno(embs, embs)
    np.testing.assert_allclose(matriz, matriz.T, atol=1e-5)


def test_top1_perfeito_em_clusters_separados() -> None:
    """3 individuos com clusters ortogonais -> Top-1 = 100%."""
    # Query e galeria do mesmo individuo sao vetores identicos
    queries = _l2(
        np.array(
            [
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1],
            ],
            dtype=np.float32,
        )
    )
    galeria = _l2(
        np.array(
            [
                [1, 0, 0],
                [1, 0, 0],
                [0, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [0, 0, 1],
            ],
            dtype=np.float32,
        )
    )
    ids_q = [0, 1, 2]
    ids_g = [0, 0, 1, 1, 2, 2]

    sim = matriz_similaridade_cosseno(queries, galeria)
    resultado = avaliar_top_k(sim, ids_q, ids_g, k_max=3)

    assert isinstance(resultado, ResultadoAvaliacao)
    assert resultado.top_k[1] == pytest.approx(1.0)
    assert resultado.n_queries == 3
    assert resultado.n_galeria == 6


def test_curva_cmc_monotona_nao_decrescente() -> None:
    """CMC[k] >= CMC[k-1] sempre."""
    rng = np.random.default_rng(42)
    queries = _l2(rng.standard_normal((5, 16)).astype(np.float32))
    galeria = _l2(rng.standard_normal((20, 16)).astype(np.float32))
    ids_q = [0, 1, 2, 3, 4]
    ids_g = [i // 4 for i in range(20)]  # 5 IDs, 4 imgs cada

    sim = matriz_similaridade_cosseno(queries, galeria)
    resultado = avaliar_top_k(sim, ids_q, ids_g, k_max=10)

    cmc = resultado.cmc
    for i in range(1, len(cmc)):
        assert cmc[i] >= cmc[i - 1], f"CMC nao-monotona em k={i + 1}"


def test_top_k_dentro_de_zero_um() -> None:
    """Acuracias Top-K estao sempre em [0, 1]."""
    rng = np.random.default_rng(7)
    queries = _l2(rng.standard_normal((10, 32)).astype(np.float32))
    galeria = _l2(rng.standard_normal((40, 32)).astype(np.float32))
    ids_q = list(range(10))
    ids_g = [i // 4 for i in range(40)]

    sim = matriz_similaridade_cosseno(queries, galeria)
    resultado = avaliar_top_k(sim, ids_q, ids_g, k_max=10)

    for acc in resultado.top_k.values():
        assert 0.0 <= acc <= 1.0
    for acc in resultado.cmc:
        assert 0.0 <= acc <= 1.0


def test_tamanho_inconsistente_levanta_erro() -> None:
    """ids_query/ids_galeria com tamanho diferente das matrizes leva a ValueError."""
    sim = np.eye(3, 5, dtype=np.float32)
    with pytest.raises(ValueError):
        avaliar_top_k(sim, ids_query=[0, 1], ids_galeria=[0, 1, 2, 3, 4])
    with pytest.raises(ValueError):
        avaliar_top_k(sim, ids_query=[0, 1, 2], ids_galeria=[0, 1])


def test_dimensoes_incompativeis_levanta_erro() -> None:
    """matriz_similaridade rejeita queries D vs galeria D' diferentes."""
    queries = _l2(np.random.randn(2, 8).astype(np.float32))
    galeria = _l2(np.random.randn(3, 16).astype(np.float32))
    with pytest.raises(ValueError):
        matriz_similaridade_cosseno(queries, galeria)
