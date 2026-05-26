"""Testes para avaliação open-set Re-ID (Etapa 7.1)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from felinet.pipeline.fase4_reid.avaliacao import (  # noqa: E402
    ResultadoOpenSet,
    avaliar_open_set,
    particionar_ids_open_set,
)


def _gerar_embeddings_separaveis(
    n_ids: int = 10,
    n_imgs_por_id: int = 5,
    dim: int = 64,
    rng_seed: int = 0,
) -> tuple[np.ndarray, list[str]]:
    """Gera embeddings sinteticos linearmente separaveis por ID (L2-norm).

    Cada ID tem um vetor-prototipo aleatorio; imagens do mesmo ID = prototipo + ruido pequeno.
    """
    rng = np.random.default_rng(rng_seed)
    prototipos = rng.standard_normal((n_ids, dim))
    prototipos /= np.linalg.norm(prototipos, axis=1, keepdims=True)

    embeddings = []
    ids = []
    for i in range(n_ids):
        ruido = rng.standard_normal((n_imgs_por_id, dim)) * 0.01
        emb = prototipos[i] + ruido
        emb /= np.linalg.norm(emb, axis=1, keepdims=True)
        embeddings.append(emb)
        ids.extend([f"id_{i:03d}"] * n_imgs_por_id)
    return np.vstack(embeddings), ids


def test_particionar_ids_open_set_reprodutivel():
    ids = [f"id_{i}" for i in range(100)]
    cat1, novos1 = particionar_ids_open_set(ids, frac_novos=0.30, random_state=42)
    cat2, novos2 = particionar_ids_open_set(ids, frac_novos=0.30, random_state=42)
    assert cat1 == cat2
    assert novos1 == novos2
    assert len(novos1) == 30
    assert len(cat1) == 70
    assert cat1.isdisjoint(novos1)


def test_particionar_ids_seeds_diferentes_dao_resultados_diferentes():
    ids = [f"id_{i}" for i in range(100)]
    _, novos_a = particionar_ids_open_set(ids, frac_novos=0.30, random_state=1)
    _, novos_b = particionar_ids_open_set(ids, frac_novos=0.30, random_state=2)
    assert novos_a != novos_b


def test_avaliar_open_set_separacao_perfeita_auc_um():
    """Quando conhecidos e novos sao linearmente separaveis, AUC deve ser ~1.0."""
    emb, ids = _gerar_embeddings_separaveis(n_ids=20, n_imgs_por_id=5, rng_seed=42)
    ids_unicos = list(set(ids))
    ids_catalogo, ids_novos = particionar_ids_open_set(ids_unicos, frac_novos=0.30, random_state=42)

    # Galeria = 4 primeiras imagens dos IDs do catalogo; queries = 5a imagem de TODOS
    emb = np.asarray(emb)
    ids_arr = np.asarray(ids)

    mask_galeria = np.array(
        [(ids_arr[i] in ids_catalogo) and (i % 5 != 4) for i in range(len(ids_arr))]
    )
    mask_query = np.array([i % 5 == 4 for i in range(len(ids_arr))])

    emb_g = emb[mask_galeria]
    ids_g = ids_arr[mask_galeria].tolist()
    emb_q = emb[mask_query]
    ids_q = ids_arr[mask_query].tolist()

    resultado = avaliar_open_set(emb_q, emb_g, ids_q, ids_g, ids_novos)

    assert isinstance(resultado, ResultadoOpenSet)
    assert resultado.auc_roc > 0.95
    assert resultado.tpr_at_fpr_05 > 0.90
    assert resultado.rank1_open_set > 0.90


def test_avaliar_open_set_curva_roc_monotonica():
    emb, ids = _gerar_embeddings_separaveis(n_ids=10, n_imgs_por_id=5, rng_seed=7)
    ids_unicos = list(set(ids))
    _, ids_novos = particionar_ids_open_set(ids_unicos, frac_novos=0.30, random_state=42)

    ids_arr = np.asarray(ids)
    mask_galeria = np.array(
        [(ids_arr[i] not in ids_novos) and (i % 5 != 4) for i in range(len(ids_arr))]
    )
    mask_query = np.array([i % 5 == 4 for i in range(len(ids_arr))])

    resultado = avaliar_open_set(
        emb[mask_query],
        emb[mask_galeria],
        ids_arr[mask_query].tolist(),
        ids_arr[mask_galeria].tolist(),
        ids_novos,
    )

    fpr = np.asarray(resultado.fpr_curve)
    tpr = np.asarray(resultado.tpr_curve)
    assert np.all(np.diff(fpr) >= -1e-9)  # FPR nao-decrescente
    assert np.all(np.diff(tpr) >= -1e-9)  # TPR nao-decrescente
    assert fpr[0] == pytest.approx(0.0)
    assert tpr[0] == pytest.approx(0.0)


def test_avaliar_open_set_contadores_consistentes():
    emb, ids = _gerar_embeddings_separaveis(n_ids=10, n_imgs_por_id=5, rng_seed=3)
    ids_unicos = list(set(ids))
    ids_catalogo, ids_novos = particionar_ids_open_set(ids_unicos, frac_novos=0.30, random_state=42)

    ids_arr = np.asarray(ids)
    mask_galeria = np.array(
        [(ids_arr[i] in ids_catalogo) and (i % 5 != 4) for i in range(len(ids_arr))]
    )
    mask_query = np.array([i % 5 == 4 for i in range(len(ids_arr))])

    resultado = avaliar_open_set(
        emb[mask_query],
        emb[mask_galeria],
        ids_arr[mask_query].tolist(),
        ids_arr[mask_galeria].tolist(),
        ids_novos,
    )

    assert resultado.n_queries_total == int(mask_query.sum())
    assert resultado.n_queries_conhecidas + resultado.n_queries_novas == resultado.n_queries_total
    assert resultado.n_ids_novos == len(ids_novos)
    assert 0.0 <= resultado.tpr_at_fpr_01 <= 1.0
    assert 0.0 <= resultado.tpr_at_fpr_05 <= 1.0
    assert 0.0 <= resultado.auc_roc <= 1.0
    assert resultado.tpr_at_fpr_05 >= resultado.tpr_at_fpr_01  # FPR maior => TPR >=


def test_avaliar_open_set_aleatorio_auc_proximo_meio():
    """Embeddings aleatorios (sem estrutura) => AUC ~ 0.5."""
    rng = np.random.default_rng(123)
    n_ids = 50
    n_imgs = 5
    dim = 32
    emb = rng.standard_normal((n_ids * n_imgs, dim))
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    ids = [f"id_{i:03d}" for i in range(n_ids) for _ in range(n_imgs)]

    _, ids_novos = particionar_ids_open_set(list(set(ids)), frac_novos=0.50, random_state=42)

    ids_arr = np.asarray(ids)
    mask_galeria = np.array(
        [(ids_arr[i] not in ids_novos) and (i % n_imgs != n_imgs - 1) for i in range(len(ids_arr))]
    )
    mask_query = np.array([i % n_imgs == n_imgs - 1 for i in range(len(ids_arr))])

    resultado = avaliar_open_set(
        emb[mask_query],
        emb[mask_galeria],
        ids_arr[mask_query].tolist(),
        ids_arr[mask_galeria].tolist(),
        ids_novos,
    )

    # AUC nao precisa ser exatamente 0.5, mas longe de 1.0 e longe de 0.0
    assert 0.30 <= resultado.auc_roc <= 0.70


def test_calcular_eer_separacao_perfeita():
    """Separacao perfeita => EER proximo de 0."""
    from felinet.pipeline.fase4_reid.avaliacao import calcular_eer

    # Scores conhecidos altos, novos baixos => ROC ideal
    scores_conhecidos = np.array([0.9, 0.85, 0.92, 0.88])
    scores_novos = np.array([0.1, 0.2, 0.15, 0.12])

    from felinet.pipeline.fase4_reid.avaliacao import _curva_roc

    fpr, tpr, thr = _curva_roc(scores_conhecidos, scores_novos)
    eer, tau = calcular_eer(fpr, tpr, thr)
    assert eer < 0.05
    assert 0.1 <= tau <= 0.9


def test_calcular_eer_aleatorio_proximo_meio():
    """Scores aleatorios => EER proximo de 0.5."""
    from felinet.pipeline.fase4_reid.avaliacao import _curva_roc, calcular_eer

    rng = np.random.default_rng(42)
    scores_conhecidos = rng.uniform(0, 1, 200)
    scores_novos = rng.uniform(0, 1, 200)

    fpr, tpr, thr = _curva_roc(scores_conhecidos, scores_novos)
    eer, _ = calcular_eer(fpr, tpr, thr)
    assert 0.40 <= eer <= 0.60


def test_avaliar_open_set_inclui_eer():
    """Smoke test: resultado tem campo EER preenchido."""
    emb, ids = _gerar_embeddings_separaveis(n_ids=10, n_imgs_por_id=5, rng_seed=1)
    ids_unicos = list(set(ids))
    ids_catalogo, ids_novos = particionar_ids_open_set(ids_unicos, frac_novos=0.50, random_state=42)

    ids_arr = np.asarray(ids)
    mask_galeria = np.array(
        [(ids_arr[i] in ids_catalogo) and (i % 5 != 4) for i in range(len(ids_arr))]
    )
    mask_query = np.array([i % 5 == 4 for i in range(len(ids_arr))])

    resultado = avaliar_open_set(
        emb[mask_query],
        emb[mask_galeria],
        ids_arr[mask_query].tolist(),
        ids_arr[mask_galeria].tolist(),
        ids_novos,
    )

    assert 0.0 <= resultado.eer <= 1.0
    assert resultado.tau_eer != 0.0
