"""E0 — Ingestão: extração de metadados EXIF.

Foca nos campos críticos para armadilhas fotográficas: timestamp de
captura, marca/modelo do equipamento e dimensões da imagem.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS

# Formato padrão EXIF (sem timezone): "2026:05:24 14:30:00"
FORMATO_EXIF_DATETIME = "%Y:%m:%d %H:%M:%S"


@dataclass(frozen=True)
class MetadadosImagem:
    """Metadados essenciais extraídos de uma imagem."""

    caminho: Path
    largura: int
    altura: int
    timestamp: datetime | None
    fabricante: str | None
    modelo: str | None


def _ler_exif_bruto(caminho: Path) -> dict[str, object]:
    """Retorna o dicionário EXIF da imagem com chaves legíveis.

    Retorna dicionário vazio se a imagem não tiver EXIF ou não puder ser lida.
    """
    try:
        with Image.open(caminho) as img:
            bruto = img.getexif()
    except Exception:
        return {}
    if not bruto:
        return {}
    return {TAGS.get(tag_id, str(tag_id)): valor for tag_id, valor in bruto.items()}


def _parse_datetime(valor: object) -> datetime | None:
    """Converte string EXIF de data/hora para datetime, retornando None se inválido."""
    if not isinstance(valor, str):
        return None
    try:
        return datetime.strptime(valor.strip(), FORMATO_EXIF_DATETIME)
    except ValueError:
        return None


def extrair_metadados(caminho: Path | str) -> MetadadosImagem:
    """Extrai metadados essenciais de uma imagem.

    Campos ausentes ou inválidos retornam None (timestamp/fabricante/modelo).
    Largura e altura são sempre lidas via Pillow, mesmo sem EXIF.
    """
    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    with Image.open(caminho) as img:
        largura, altura = img.size

    exif = _ler_exif_bruto(caminho)
    timestamp = _parse_datetime(exif.get("DateTimeOriginal") or exif.get("DateTime"))
    fabricante = exif.get("Make")
    modelo = exif.get("Model")

    return MetadadosImagem(
        caminho=caminho,
        largura=largura,
        altura=altura,
        timestamp=timestamp,
        fabricante=str(fabricante).strip() if isinstance(fabricante, str) else None,
        modelo=str(modelo).strip() if isinstance(modelo, str) else None,
    )
