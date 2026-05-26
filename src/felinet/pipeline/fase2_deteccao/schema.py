"""E1 — Detecção: esquema neutro de saída.

Define a estrutura de dados que o pipeline consome após a detecção,
isolando o resto do sistema da API específica do MegaDetector.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

# Classes do MegaDetector (categorias canônicas)
CATEGORIA_ANIMAL = "animal"
CATEGORIA_PESSOA = "person"
CATEGORIA_VEICULO = "vehicle"
CATEGORIAS_VALIDAS = {CATEGORIA_ANIMAL, CATEGORIA_PESSOA, CATEGORIA_VEICULO}


@dataclass(frozen=True)
class BoundingBox:
    """Caixa delimitadora normalizada (coordenadas em [0, 1])."""

    x: float
    y: float
    w: float
    h: float

    def __post_init__(self) -> None:
        for nome, v in [("x", self.x), ("y", self.y), ("w", self.w), ("h", self.h)]:
            if not 0.0 <= v <= 1.0:
                raise ValueError(f"BoundingBox.{nome}={v} fora de [0, 1]")


@dataclass(frozen=True)
class Deteccao:
    """Uma detecção: categoria + confiança + bbox."""

    categoria: str
    confianca: float
    bbox: BoundingBox

    def __post_init__(self) -> None:
        if self.categoria not in CATEGORIAS_VALIDAS:
            raise ValueError(f"Categoria inválida: {self.categoria}")
        if not 0.0 <= self.confianca <= 1.0:
            raise ValueError(f"Confiança fora de [0, 1]: {self.confianca}")


@dataclass(frozen=True)
class ResultadoDeteccao:
    """Resultado da detecção para uma única imagem."""

    media_path: str
    largura: int
    altura: int
    deteccoes: list[Deteccao]
    modelo: str  # ex.: "MDv6-compact"
    tempo_ms: float

    def to_dict(self) -> dict:
        return {
            "media_path": self.media_path,
            "largura": self.largura,
            "altura": self.altura,
            "modelo": self.modelo,
            "tempo_ms": self.tempo_ms,
            "deteccoes": [
                {
                    "categoria": d.categoria,
                    "confianca": d.confianca,
                    "bbox": asdict(d.bbox),
                }
                for d in self.deteccoes
            ],
        }


def salvar_resultados_json(
    resultados: list[ResultadoDeteccao],
    arquivo_saida: Path | str,
) -> None:
    """Serializa uma lista de resultados em JSON."""
    arquivo_saida = Path(arquivo_saida)
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
    payload = {"resultados": [r.to_dict() for r in resultados]}
    arquivo_saida.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
