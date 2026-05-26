"""Fase IV — Re-identificacao: esquema neutro de saida.

Define a estrutura de embeddings produzida pelo extrator (MegaDescriptor),
isolando o resto do pipeline da arquitetura especifica do modelo.

A Fase IV opera apenas sobre crops cuja Fase III emitiu o status
``felis_catus`` — demais status nao chegam a esta fase.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Embedding:
    """Vetor de caracteristicas extraido de um crop felis_catus."""

    media_path: str
    bbox_indice: int
    vetor: list[float]
    modelo: str
    tempo_ms: float

    def __post_init__(self) -> None:
        if not self.vetor:
            raise ValueError("Embedding com vetor vazio")
        if not isinstance(self.vetor, list):
            raise TypeError("Embedding.vetor deve ser list[float]")

    @property
    def dimensao(self) -> int:
        return len(self.vetor)


def salvar_embeddings_json(embeddings: list[Embedding], caminho: Path) -> None:
    """Serializa lista de Embedding para JSON UTF-8 com newline final."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "total": len(embeddings),
        "dimensao": embeddings[0].dimensao if embeddings else 0,
        "embeddings": [asdict(e) for e in embeddings],
    }
    caminho.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def carregar_embeddings_json(caminho: Path) -> list[Embedding]:
    """Le arquivo JSON e reconstroi lista de Embedding."""
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return [Embedding(**registro) for registro in dados.get("embeddings", [])]
