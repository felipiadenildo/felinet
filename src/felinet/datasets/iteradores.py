"""Iteradores de imagens por tipo de layout de dataset.

Cada layout (``flat``, ``por_classe``, ``por_identidade``, ``cocotraps``,
``aninhado_livre``) tem uma função iteradora própria. O despachante
``iterador_para_layout`` seleciona a função pelo nome do layout.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

EXTENSOES_IMG = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


def iterar_flat(raiz: Path) -> Iterator[Path]:
    """Imagens diretamente na pasta raiz."""
    for p in sorted(raiz.iterdir()):
        if p.is_file() and p.suffix.lower() in EXTENSOES_IMG:
            yield p


def iterar_por_classe(raiz: Path) -> Iterator[Path]:
    """``raiz/<classe>/*.jpg`` — itera todas as imagens, ignora a classe."""
    for classe_dir in sorted(raiz.iterdir()):
        if not classe_dir.is_dir():
            continue
        for p in sorted(classe_dir.iterdir()):
            if p.is_file() and p.suffix.lower() in EXTENSOES_IMG:
                yield p


def iterar_por_identidade(raiz: Path) -> Iterator[tuple[Path, str]]:
    """``raiz/<id>/*.jpg`` — gera tuplas ``(caminho, identidade)``."""
    for id_dir in sorted(raiz.iterdir()):
        if not id_dir.is_dir():
            continue
        for p in sorted(id_dir.iterdir()):
            if p.is_file() and p.suffix.lower() in EXTENSOES_IMG:
                yield p, id_dir.name


def iterar_aninhado_livre(raiz: Path) -> Iterator[Path]:
    """``rglob`` recursivo, fallback para estruturas desconhecidas."""
    for p in sorted(raiz.rglob("*")):
        if p.is_file() and p.suffix.lower() in EXTENSOES_IMG:
            yield p


def iterador_para_layout(layout: str, raiz: Path) -> Iterator[Path]:
    """Despacha para o iterador correto.

    Re-ID (``por_identidade``) usa o iterador específico em outro local
    porque devolve tuplas ``(path, id)``. Aqui só passam por (Path).
    """
    mapping = {
        "flat": iterar_flat,
        "por_classe": iterar_por_classe,
        "aninhado_livre": iterar_aninhado_livre,
        "cocotraps": iterar_aninhado_livre,
    }
    if layout not in mapping:
        raise ValueError(f"layout desconhecido: {layout}")
    return mapping[layout](raiz)
