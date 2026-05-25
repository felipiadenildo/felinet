"""E0 — Ingestão: geração de manifesto CSV de mídias.

O manifesto é o registro auditável de tudo que entrou no pipeline:
caminho relativo, hash SHA-256, timestamp, dimensões e equipamento.
Salvo em CSV para inspeção humana e versionamento via DVC.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from .exif import extrair_metadados
from .validar import listar_midias, sha256_arquivo

COLUNAS_MANIFESTO = [
    "caminho_relativo",
    "sha256",
    "largura",
    "altura",
    "timestamp",
    "fabricante",
    "modelo",
]


@dataclass(frozen=True)
class EntradaManifesto:
    """Uma linha do manifesto de ingestão."""

    caminho_relativo: str
    sha256: str
    largura: int
    altura: int
    timestamp: str  # ISO 8601 ou string vazia
    fabricante: str
    modelo: str


def _formatar_timestamp(ts: datetime | None) -> str:
    return ts.isoformat() if ts else ""


def gerar_entrada(caminho: Path, raiz: Path) -> EntradaManifesto:
    """Cria uma entrada de manifesto para uma única imagem."""
    meta = extrair_metadados(caminho)
    return EntradaManifesto(
        caminho_relativo=str(caminho.relative_to(raiz)),
        sha256=sha256_arquivo(caminho),
        largura=meta.largura,
        altura=meta.altura,
        timestamp=_formatar_timestamp(meta.timestamp),
        fabricante=meta.fabricante or "",
        modelo=meta.modelo or "",
    )


def gerar_manifesto(
    pasta_origem: Path | str,
    arquivo_saida: Path | str,
) -> list[EntradaManifesto]:
    """Percorre uma pasta de mídias e grava o manifesto em CSV.

    Apenas imagens são processadas — vídeos ficam fora desta versão.

    Returns
    -------
    list[EntradaManifesto]
        Entradas geradas, na mesma ordem do CSV.
    """
    pasta_origem = Path(pasta_origem)
    arquivo_saida = Path(arquivo_saida)
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    midias = [
        m
        for m in listar_midias(pasta_origem)
        if m.suffix.lower() in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    ]
    entradas = [gerar_entrada(m, pasta_origem) for m in midias]

    with arquivo_saida.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_MANIFESTO)
        writer.writeheader()
        for entrada in entradas:
            writer.writerow(asdict(entrada))

    return entradas
