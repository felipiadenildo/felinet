"""Utilitarios para acesso ao subset de desenvolvimento do LILA BC.

O subset de desenvolvimento e povoado manualmente pelo usuario com
imagens de fontes publicas (LILA BC, iNaturalist, Wikimedia Commons,
Pexels, Unsplash). Este modulo nao realiza download: oferece apenas
funcoes para listar e descrever as imagens presentes no diretorio
local, bem como consultar o manifesto gerado por
``scripts/preparar_subset_dev.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

EXTENSOES_VALIDAS = {".jpg", ".jpeg", ".png"}
DIRETORIO_PADRAO = Path("04_dados/raw/lila_bc_dev")
ARQUIVO_MANIFESTO = "manifesto.json"


def listar_subset_dev(diretorio: Path = DIRETORIO_PADRAO) -> list[Path]:
    """Lista, em ordem alfabetica, as imagens validas do subset.

    Args:
        diretorio: Caminho da pasta com as imagens.

    Returns:
        Lista de caminhos para arquivos de imagem (.jpg, .jpeg, .png).
        Lista vazia se o diretorio nao existir ou nao contiver imagens.
    """
    if not diretorio.exists():
        return []
    return sorted(
        caminho
        for caminho in diretorio.iterdir()
        if caminho.is_file() and caminho.suffix.lower() in EXTENSOES_VALIDAS
    )


def carregar_manifesto(diretorio: Path = DIRETORIO_PADRAO) -> dict | None:
    """Carrega o manifesto.json do subset, se existir.

    Args:
        diretorio: Caminho da pasta com o manifesto.

    Returns:
        Dicionario com o conteudo do manifesto ou ``None`` se ausente.
    """
    caminho = diretorio / ARQUIVO_MANIFESTO
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))


def subset_esta_pronto(diretorio: Path = DIRETORIO_PADRAO) -> bool:
    """Indica se o subset contem pelo menos uma imagem valida."""
    return len(listar_subset_dev(diretorio)) > 0
