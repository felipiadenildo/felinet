"""Funções de avaliação Re-ID (closed-set e open-set)."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

# ============================================================
# CLOSED-SET (Etapa 6)
# ============================================================


@dataclass
class ResultadoAvaliacao:
    """Resultado de avaliação Re-ID closed-set.

    Attributes:
        n_queries: Número de queries avaliadas.
        n_galeria: Número de imagens na galeria.
        n_ids: Número de IDs únicos.
        top_k: Dicionário {k: acuracia} para k em 1..k_max.
        cmc: Curva CMC (lista de acertos acumulados normalizados).
    """

    n_queries: int
    n_galeria: int
    n_ids: int
    top_k: dict[int, float]
    cmc: list[float] = field(default_factory=list)

    def como_dicionario(self) -> dict:
        return {
            "n_queries": self.n_queries,
            "n_galeria": self.n_galeria,
            "n_ids": self.n_ids,
            "top_k": {str(k): v for k, v in self.top_k.items()},
            "cmc": self.cmc,
        }


def matriz_similaridade_cosseno(
    embeddings_query: np.ndarray,
    embeddings_galeria: np.ndarray,
) -> np.ndarray:
    """Calcula matriz de similaridade cosseno (assume embeddings L2-norm).

    Args:
        embeddings_query: (Nq, D).
        embeddings_galeria: (Ng, D).

    Returns:
        Matriz (Nq, Ng) com produto interno.
    """
    return embeddings_query @ embeddings_galeria.T


def avaliar_top_k(
    similaridade: np.ndarray,
    ids_query: Sequence[str],
    ids_galeria: Sequence[str],
    k_max: int = 10,
) -> ResultadoAvaliacao:
    """Avalia Top-K e curva CMC closed-set.

    Args:
        similaridade: (Nq, Ng).
        ids_query: IDs verdadeiros das queries.
        ids_galeria: IDs da galeria.
        k_max: K máximo da curva CMC.

    Raises:
        ValueError: Se dimensões de ids_query/ids_galeria não baterem com similaridade.

    Returns:
        ResultadoAvaliacao.
    """
    ids_query = np.asarray(ids_query)
    ids_galeria = np.asarray(ids_galeria)

    if similaridade.ndim != 2:
        raise ValueError(
            f"similaridade deve ser 2D (Nq, Ng); recebido shape={similaridade.shape}"
        )
    n_queries_mat, n_galeria_mat = similaridade.shape
    if len(ids_query) != n_queries_mat:
        raise ValueError(
            f"len(ids_query)={len(ids_query)} != n_queries da matriz={n_queries_mat}"
        )
    if len(ids_galeria) != n_galeria_mat:
        raise ValueError(
            f"len(ids_galeria)={len(ids_galeria)} != n_galeria da matriz={n_galeria_mat}"
        )
    if k_max < 1:
        raise ValueError(f"k_max deve ser >= 1; recebido {k_max}")

    n_queries = len(ids_query)
    k_efetivo = min(k_max, n_galeria_mat)

    # Ordena galeria por similaridade decrescente por query
    ordem = np.argsort(-similaridade, axis=1)
    ids_galeria_ord = ids_galeria[ordem]  # (Nq, Ng)

    # Compara top-K com ID verdadeiro
    acertos = ids_galeria_ord[:, :k_efetivo] == ids_query[:, None]
    acerto_acumulado = np.cumsum(acertos, axis=1) > 0
    cmc = acerto_acumulado.mean(axis=0)

    top_k = {k + 1: float(cmc[k]) for k in range(k_efetivo)}
    ids_unicos = set(ids_query.tolist()) | set(ids_galeria.tolist())

    return ResultadoAvaliacao(
        n_queries=int(n_queries),
        n_galeria=int(n_galeria_mat),
        n_ids=len(ids_unicos),
        top_k=top_k,
        cmc=cmc.tolist(),
    )


# ============================================================
# OPEN-SET (Etapa 7.1)
# ============================================================


@dataclass
class ResultadoOpenSet:
    """Resultado de avaliação open-set Re-ID."""

    n_queries_total: int
    n_queries_conhecidas: int
    n_queries_novas: int
    n_ids_catalogo: int
    n_ids_novos: int
    tpr_at_fpr_01: float
    tpr_at_fpr_05: float
    rank1_open_set: float
    auc_roc: float
    eer: float
    tau_fpr_01: float
    tau_fpr_05: float
    tau_eer: float
    fpr_curve: list[float] = field(default_factory=list)
    tpr_curve: list[float] = field(default_factory=list)

    def como_dicionario(self) -> dict:
        return {
            "n_queries_total": self.n_queries_total,
            "n_queries_conhecidas": self.n_queries_conhecidas,
            "n_queries_novas": self.n_queries_novas,
            "n_ids_catalogo": self.n_ids_catalogo,
            "n_ids_novos": self.n_ids_novos,
            "tpr_at_fpr_01": self.tpr_at_fpr_01,
            "tpr_at_fpr_05": self.tpr_at_fpr_05,
            "rank1_open_set": self.rank1_open_set,
            "auc_roc": self.auc_roc,
            "eer": self.eer,
            "tau_fpr_01": self.tau_fpr_01,
            "tau_fpr_05": self.tau_fpr_05,
            "tau_eer": self.tau_eer,
            "fpr_curve": self.fpr_curve,
            "tpr_curve": self.tpr_curve,
        }


def particionar_ids_open_set(
    ids_unicos: Sequence[str],
    frac_novos: float = 0.30,
    random_state: int = 42,
) -> tuple[set[str], set[str]]:
    """Divide IDs em catálogo (conhecidos) e novos (removidos do catálogo)."""
    rng = np.random.default_rng(random_state)
    ids_arr = np.array(sorted(set(ids_unicos)))
    rng.shuffle(ids_arr)
    n_novos = int(round(len(ids_arr) * frac_novos))
    ids_novos = set(ids_arr[:n_novos].tolist())
    ids_catalogo = set(ids_arr[n_novos:].tolist())
    return ids_catalogo, ids_novos


def _curva_roc(
    scores_conhecidos: np.ndarray, scores_novos: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calcula curva ROC sem sklearn."""
    todos = np.concatenate([scores_conhecidos, scores_novos])
    rotulos = np.concatenate(
        [np.ones(len(scores_conhecidos)), np.zeros(len(scores_novos))]
    )
    ordem = np.argsort(-todos)
    rotulos_ord = rotulos[ordem]
    scores_ord = todos[ordem]

    tp_cum = np.cumsum(rotulos_ord)
    fp_cum = np.cumsum(1 - rotulos_ord)
    n_pos = len(scores_conhecidos)
    n_neg = len(scores_novos)

    tpr = tp_cum / max(n_pos, 1)
    fpr = fp_cum / max(n_neg, 1)

    tpr = np.concatenate([[0.0], tpr])
    fpr = np.concatenate([[0.0], fpr])
    thresholds = np.concatenate([[scores_ord[0] + 1e-6], scores_ord])
    return fpr, tpr, thresholds


def _auc_trapezio(fpr: np.ndarray, tpr: np.ndarray) -> float:
    return float(np.trapz(tpr, fpr))


def _tpr_em_fpr_alvo(
    fpr: np.ndarray, tpr: np.ndarray, thresholds: np.ndarray, fpr_alvo: float
) -> tuple[float, float]:
    """Retorna (TPR, τ) no maior τ cuja FPR <= fpr_alvo."""
    validos = fpr <= fpr_alvo
    if not validos.any():
        return 0.0, float(thresholds[0])
    indices_validos = np.where(validos)[0]
    melhor = indices_validos[np.argmax(tpr[indices_validos])]
    return float(tpr[melhor]), float(thresholds[melhor])


def avaliar_open_set(
    embeddings_query: np.ndarray,
    embeddings_galeria: np.ndarray,
    ids_query: Sequence[str],
    ids_galeria: Sequence[str],
    ids_novos: set[str],
) -> ResultadoOpenSet:
    """Avalia Re-ID open-set.

    Args:
        embeddings_query: (Nq, D) L2-norm.
        embeddings_galeria: (Ng, D) L2-norm — JÁ FILTRADA para excluir ids_novos.
        ids_query: IDs verdadeiros das queries (Nq).
        ids_galeria: IDs da galeria filtrada (Ng).
        ids_novos: Conjunto de IDs removidos do catálogo.
    """
    ids_query = np.asarray(ids_query)
    ids_galeria = np.asarray(ids_galeria)

    sim = embeddings_query @ embeddings_galeria.T  # (Nq, Ng)

    idx_top1 = np.argmax(sim, axis=1)
    sim_max = sim[np.arange(len(sim)), idx_top1]
    id_top1_predito = ids_galeria[idx_top1]

    mask_novas = np.array([qid in ids_novos for qid in ids_query])
    mask_conhecidas = ~mask_novas

    scores_conhecidos = sim_max[mask_conhecidas]
    scores_novos_q = sim_max[mask_novas]

    fpr, tpr, thresholds = _curva_roc(scores_conhecidos, scores_novos_q)
    auc = _auc_trapezio(fpr, tpr)

    tpr_01, tau_01 = _tpr_em_fpr_alvo(fpr, tpr, thresholds, 0.01)
    tpr_05, tau_05 = _tpr_em_fpr_alvo(fpr, tpr, thresholds, 0.05)
    eer, tau_eer = calcular_eer(fpr, tpr, thresholds)

    acerto_id = (id_top1_predito == ids_query) & mask_conhecidas
    acerto_aceito = acerto_id & (sim_max >= tau_01)
    rank1_open = float(acerto_aceito.sum() / max(mask_conhecidas.sum(), 1))

    ids_catalogo = set(ids_galeria.tolist())

    return ResultadoOpenSet(
        n_queries_total=int(len(ids_query)),
        n_queries_conhecidas=int(mask_conhecidas.sum()),
        n_queries_novas=int(mask_novas.sum()),
        n_ids_catalogo=len(ids_catalogo),
        n_ids_novos=len(ids_novos),
        tpr_at_fpr_01=tpr_01,
        tpr_at_fpr_05=tpr_05,
        rank1_open_set=rank1_open,
        auc_roc=auc,
        eer=eer,
        tau_fpr_01=tau_01,
        tau_fpr_05=tau_05,
        tau_eer=tau_eer,
        fpr_curve=fpr.tolist(),
        tpr_curve=tpr.tolist(),
    )

def calcular_eer(
    fpr: np.ndarray,
    tpr: np.ndarray,
    thresholds: np.ndarray,
) -> tuple[float, float]:
    """Calcula Equal Error Rate (EER) e threshold correspondente.

    EER e o ponto onde FPR == FNR (= 1 - TPR), metrica classica
    de literatura biometrica.

    Args:
        fpr: Curva FPR (ordenada nao-decrescente).
        tpr: Curva TPR (ordenada nao-decrescente).
        thresholds: Thresholds correspondentes a cada (FPR, TPR).

    Returns:
        (eer, tau_eer): EER em [0,1] e threshold no ponto.
    """
    fpr = np.asarray(fpr)
    tpr = np.asarray(tpr)
    thresholds = np.asarray(thresholds)
    fnr = 1.0 - tpr

    # Encontra o indice onde |FPR - FNR| e minimo
    diff = np.abs(fpr - fnr)
    idx = int(np.argmin(diff))

    # EER e a media de FPR e FNR no ponto (sao quase iguais ali)
    eer = float((fpr[idx] + fnr[idx]) / 2.0)
    tau_eer = float(thresholds[idx])
    return eer, tau_eer
