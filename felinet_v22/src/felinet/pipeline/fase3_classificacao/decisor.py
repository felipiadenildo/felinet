"""Fase III — Decisor de espécie.

Política conservadora descrita em §3.4 da monografia:
- Confiança alta em Felis catus  → segue para Fase IV
- Confiança alta em outra espécie → fauna não-alvo
- Confiança baixa ou ambígua     → fila de validação humana
"""
from __future__ import annotations

from dataclasses import dataclass
from math import log

from .schema import (
    STATUS_FELIS_CATUS,
    STATUS_OUTRA_ESPECIE,
    STATUS_VALIDACAO_HUMANA,
    PrediccaoEspecie,
)

# Rótulo canônico de gato doméstico — varia entre modelos.
# Aceitamos sinônimos comuns para robustez.
ROTULOS_FELIS_CATUS = {
    "felis catus",
    "felis_catus",
    "domestic cat",
    "cat",
}


@dataclass(frozen=True)
class ConfigDecisor:
    """Parâmetros da política de decisão."""

    limiar_confianca: float = 0.50
    """Confiança mínima da top-1 para aceitar um veredito direto."""

    limiar_entropia: float = 1.50
    """Entropia máxima da distribuição top-K para considerar 'concentrada'.
    Acima disso (distribuição espalhada) vai para validação humana."""


def _eh_felis_catus(rotulo: str) -> bool:
    return rotulo.strip().lower() in ROTULOS_FELIS_CATUS


def _entropia(probs: list[float]) -> float:
    """Entropia de Shannon (base e). Maior = distribuição mais incerta."""
    return -sum(p * log(p) for p in probs if p > 0)


def decidir_status(
    top_k: list[PrediccaoEspecie],
    config: ConfigDecisor | None = None,
) -> str:
    """Aplica a política de decisão sobre as top-K predições do classificador.

    Retorna um dos valores de STATUS_VALIDOS do schema.
    """
    if not top_k:
        return STATUS_VALIDACAO_HUMANA

    config = config or ConfigDecisor()
    top1 = top_k[0]

    # Distribuição muito incerta → fila humana
    entropia = _entropia([p.probabilidade for p in top_k])
    if entropia > config.limiar_entropia:
        return STATUS_VALIDACAO_HUMANA

    # Confiança baixa → fila humana
    if top1.probabilidade < config.limiar_confianca:
        return STATUS_VALIDACAO_HUMANA

    # Confiança alta — desempate por classe
    if _eh_felis_catus(top1.especie):
        return STATUS_FELIS_CATUS
    return STATUS_OUTRA_ESPECIE
