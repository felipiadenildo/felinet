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
    "classe_origem",
]


@dataclass(frozen=True)
class EntradaManifesto:
    """Uma linha do manifesto de ingestão.

    ``classe_origem`` é o nome da subpasta imediata sob a raiz do dataset
    quando o layout é ``por_classe`` (e.g. ``bobcat``, ``puma``,
    ``domestic_cat`` no Felidae). Vazio quando o layout não usa subpastas
    como rótulo. Permite cruzar predições do classificador com rótulo
    proxy (ver ``felinet.metricas.confusao_especie``).
    """

    caminho_relativo: str
    sha256: str
    largura: int
    altura: int
    timestamp: str  # ISO 8601 ou string vazia
    fabricante: str
    modelo: str
    classe_origem: str = ""


def _formatar_timestamp(ts: datetime | None) -> str:
    return ts.isoformat() if ts else ""


def _inferir_classe_origem(caminho: Path, raiz: Path, layout: str = "") -> str:
    """Inferir a ``classe_origem`` a partir do caminho relativo.

    Em layout ``por_classe`` (e.g. felidae), a primeira componente do
    caminho relativo é a classe (e.g. ``bobcat/IMG_001.jpg`` → ``bobcat``).
    Em outros layouts (``flat``, ``aninhado_livre``), retorna string vazia.
    """
    if layout != "por_classe":
        return ""
    try:
        partes = caminho.relative_to(raiz).parts
    except ValueError:
        return ""
    return partes[0] if len(partes) >= 2 else ""


def gerar_entrada(caminho: Path, raiz: Path, layout: str = "") -> EntradaManifesto:
    """Cria uma entrada de manifesto para uma única imagem.

    Quando ``layout=='por_classe'``, ``classe_origem`` é inferida do nome
    da subpasta imediata sob ``raiz``.
    """
    meta = extrair_metadados(caminho)
    return EntradaManifesto(
        caminho_relativo=str(caminho.relative_to(raiz)),
        sha256=sha256_arquivo(caminho),
        largura=meta.largura,
        altura=meta.altura,
        timestamp=_formatar_timestamp(meta.timestamp),
        fabricante=meta.fabricante or "",
        modelo=meta.modelo or "",
        classe_origem=_inferir_classe_origem(caminho, raiz, layout),
    )


def gerar_manifesto(
    pasta_origem: Path | str,
    arquivo_saida: Path | str,
    midias: list[Path] | None = None,
    layout: str = "",
) -> list[EntradaManifesto]:
    """Percorre uma pasta de mídias e grava o manifesto em CSV.

    Apenas imagens são processadas — vídeos ficam fora desta versão.

    Quando ``midias`` é fornecida, usa a lista pré-amostrada (preservando
    ordem) em vez de varrer ``pasta_origem``. Caminho útil para amostragem
    determinística no orquestrador.

    Quando ``layout=='por_classe'``, a coluna ``classe_origem`` é populada
    com o nome da subpasta imediata de cada imagem (e.g. ``bobcat``,
    ``puma``). Em outros layouts a coluna fica vazia. Compatível com
    manifestos antigos: leitores que ignorarem a coluna não quebram.

    Returns
    -------
    list[EntradaManifesto]
        Entradas geradas, na mesma ordem do CSV.
    """
    pasta_origem = Path(pasta_origem)
    arquivo_saida = Path(arquivo_saida)
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    if midias is None:
        midias = [
            m
            for m in listar_midias(pasta_origem)
            if m.suffix.lower() in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
        ]
    entradas = [gerar_entrada(m, pasta_origem, layout) for m in midias]

    with arquivo_saida.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_MANIFESTO)
        writer.writeheader()
        for entrada in entradas:
            writer.writerow(asdict(entrada))

    return entradas
