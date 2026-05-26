"""Fase III — Classificação: esquema neutro de saída.

Define a estrutura que a Fase IV consome, isolando o resto do pipeline
da API específica do SpeciesNet.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

# Status do veredito por crop, conforme política de decisão da §3.4
STATUS_FELIS_CATUS = "felis_catus"         # vai para Fase IV
STATUS_OUTRA_ESPECIE = "outra_especie"     # vai para base de fauna não-alvo
STATUS_VALIDACAO_HUMANA = "validacao_humana"  # vai para fila humana

STATUS_VALIDOS = {STATUS_FELIS_CATUS, STATUS_OUTRA_ESPECIE, STATUS_VALIDACAO_HUMANA}


@dataclass(frozen=True)
class PrediccaoEspecie:
    """Uma predição (espécie, probabilidade) do classificador."""

    especie: str
    probabilidade: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.probabilidade <= 1.0:
            raise ValueError(f"Probabilidade fora de [0, 1]: {self.probabilidade}")


@dataclass(frozen=True)
class ResultadoClassificacao:
    """Resultado da Fase III para um único crop."""

    media_path: str
    bbox_indice: int            # índice da bbox dentro do ResultadoDeteccao
    top_k: list[PrediccaoEspecie]
    status: str                 # veredito da política de decisão
    modelo: str                 # ex.: "SpeciesNet"
    tempo_ms: float

    def __post_init__(self) -> None:
        if self.status not in STATUS_VALIDOS:
            raise ValueError(f"Status inválido: {self.status}")

    @property
    def top1(self) -> PrediccaoEspecie:
        return self.top_k[0]

    def to_dict(self) -> dict:
        return {
            "media_path": self.media_path,
            "bbox_indice": self.bbox_indice,
            "status": self.status,
            "modelo": self.modelo,
            "tempo_ms": self.tempo_ms,
            "top_k": [asdict(p) for p in self.top_k],
        }


def salvar_resultados_json(
    resultados: list[ResultadoClassificacao],
    arquivo_saida: Path | str,
) -> None:
    """Serializa uma lista de resultados em JSON."""
    arquivo_saida = Path(arquivo_saida)
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
    payload = {"resultados": [r.to_dict() for r in resultados]}
    arquivo_saida.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def carregar_resultados_json(arquivo: Path | str) -> list[ResultadoClassificacao]:
    """Le um JSON de classificacoes serializado por ``salvar_resultados_json``."""
    arquivo = Path(arquivo)
    raw = json.loads(arquivo.read_text(encoding="utf-8"))
    resultados: list[ResultadoClassificacao] = []
    for r in raw.get("resultados", []):
        top_k = [PrediccaoEspecie(**p) for p in r.get("top_k", [])]
        resultados.append(ResultadoClassificacao(
            media_path=r["media_path"],
            bbox_indice=int(r["bbox_indice"]),
            top_k=top_k,
            status=r["status"],
            modelo=r["modelo"],
            tempo_ms=float(r["tempo_ms"]),
        ))
    return resultados
