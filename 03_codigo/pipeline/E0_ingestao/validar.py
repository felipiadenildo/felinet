"""E0 — Ingestão: utilitários de validação de arquivos.

Funções básicas para verificar integridade e identificar arquivos
de mídia provenientes de cartões SD de armadilhas fotográficas.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_SIZE = 65_536  # 64 KiB — bom equilíbrio I/O vs. memória
EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
EXTENSOES_VIDEO = {".mp4", ".avi", ".mov", ".mkv"}


def sha256_arquivo(caminho: Path | str) -> str:
    """Calcula o hash SHA-256 de um arquivo, lendo em blocos.

    Parameters
    ----------
    caminho : Path | str
        Caminho para o arquivo.

    Returns
    -------
    str
        Hash SHA-256 em hexadecimal (64 caracteres).

    Raises
    ------
    FileNotFoundError
        Se o arquivo não existir.
    """
    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    sha = hashlib.sha256()
    with caminho.open("rb") as f:
        while bloco := f.read(CHUNK_SIZE):
            sha.update(bloco)
    return sha.hexdigest()


def eh_imagem(caminho: Path | str) -> bool:
    """Retorna True se a extensão do arquivo é de imagem suportada."""
    return Path(caminho).suffix.lower() in EXTENSOES_IMAGEM


def eh_video(caminho: Path | str) -> bool:
    """Retorna True se a extensão do arquivo é de vídeo suportada."""
    return Path(caminho).suffix.lower() in EXTENSOES_VIDEO


def listar_midias(pasta: Path | str) -> list[Path]:
    """Lista recursivamente todos os arquivos de imagem ou vídeo em uma pasta.

    Resultado ordenado alfabeticamente para reprodutibilidade.
    """
    pasta = Path(pasta)
    if not pasta.is_dir():
        raise NotADirectoryError(f"Não é diretório: {pasta}")

    midias = [p for p in pasta.rglob("*") if p.is_file() and (eh_imagem(p) or eh_video(p))]
    return sorted(midias)
