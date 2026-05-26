"""Hash de arquivos (SHA-256) para manifesto de ingestao e checksums de runs."""
from __future__ import annotations

import hashlib
from pathlib import Path

TAMANHO_BLOCO = 64 * 1024


def sha256_arquivo(caminho: Path, tamanho_bloco: int = TAMANHO_BLOCO) -> str:
    """Calcula SHA-256 em streaming (memoria constante)."""
    h = hashlib.sha256()
    with Path(caminho).open("rb") as f:
        while bloco := f.read(tamanho_bloco):
            h.update(bloco)
    return h.hexdigest()


def sha256_bytes(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()
