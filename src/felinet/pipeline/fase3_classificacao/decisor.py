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


# Rótulos de nível taxonômico acima de espécie que incluem o gato doméstico (o filtro geográfico
# do SpeciesNet produz esses rótulos ao subir na taxonomia).
ROTULOS_ANCESTRAIS_FELIS = {
    "cat family",
    "felidae",
    "felidae family",
    "carnivorous mammal",
    "carnivora",
    "mammal",
    "mammalia",
    "animal",
}


@dataclass(frozen=True)
class ConfigDecisor:
    """Parâmetros da política de decisão."""

    limiar_confianca: float = 0.50
    """Confiança mínima da top-1 para aceitar um veredito direto."""

    limiar_entropia: float = 1.50
    """Entropia máxima da distribuição top-K para considerar 'concentrada'.
    Acima disso (distribuição espalhada) vai para validação humana."""

    ancestrais_para_validacao: bool = False
    """Se verdadeiro, top-1 em nível acima de espécie que inclui o gato doméstico (ex.: "cat
    family") vai para validação humana em vez de ser descartado. Desligado nos experimentos da
    monografia; recomendado com o filtro geográfico."""


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

    # Rótulo genérico que pode ser um gato doméstico: não descartar sem revisão
    if (
        config.ancestrais_para_validacao
        and top1.especie.strip().lower() in ROTULOS_ANCESTRAIS_FELIS
    ):
        return STATUS_VALIDACAO_HUMANA

    # Confiança alta — desempate por classe
    if _eh_felis_catus(top1.especie):
        return STATUS_FELIS_CATUS
    return STATUS_OUTRA_ESPECIE
