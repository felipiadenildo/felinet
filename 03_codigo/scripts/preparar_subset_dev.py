"""Prepara o subset de desenvolvimento a partir de imagens locais.

Em vez de baixar imagens da internet, este script valida o conteudo do
diretorio ``04_dados/raw/lila_bc_dev/`` (povoado manualmente pelo usuario
com amostras de datasets publicos como LILA BC, iNaturalist ou Wikimedia
Commons) e gera um manifesto reprodutivel.

O manifesto contem, para cada imagem encontrada, o nome do arquivo, o
tamanho em bytes, as dimensoes em pixels e o hash SHA-256 do conteudo
binario, permitindo verificar a integridade do subset entre execucoes.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

EXTENSOES_VALIDAS = {".jpg", ".jpeg", ".png"}
DIRETORIO_PADRAO = Path("04_dados/raw/lila_bc_dev")
ARQUIVO_MANIFESTO = "manifesto.json"


def calcular_hash_sha256(caminho: Path, tamanho_bloco: int = 65536) -> str:
    """Retorna o hash SHA-256 hexadecimal do arquivo informado."""
    hasher = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(tamanho_bloco), b""):
            hasher.update(bloco)
    return hasher.hexdigest()


def coletar_imagens(diretorio: Path) -> list[Path]:
    """Lista, em ordem alfabetica, as imagens validas do diretorio."""
    if not diretorio.exists():
        return []
    return sorted(
        caminho
        for caminho in diretorio.iterdir()
        if caminho.is_file() and caminho.suffix.lower() in EXTENSOES_VALIDAS
    )


def descrever_imagem(caminho: Path) -> dict:
    """Extrai metadados basicos de uma imagem."""
    with Image.open(caminho) as imagem:
        largura, altura = imagem.size
        formato = imagem.format
    return {
        "arquivo": caminho.name,
        "formato": formato,
        "largura": largura,
        "altura": altura,
        "bytes": caminho.stat().st_size,
        "sha256": calcular_hash_sha256(caminho),
    }


def imprimir_instrucoes(diretorio: Path) -> None:
    """Imprime instrucoes de povoamento manual quando o diretorio esta vazio."""
    diretorio.mkdir(parents=True, exist_ok=True)
    mensagem = (
        f"Diretorio vazio: {diretorio}\n"
        "\n"
        "Povoe manualmente com 5 a 10 imagens (.jpg/.jpeg/.png) de fontes\n"
        "publicas, sugestao de composicao para exercitar todos os ramos do\n"
        "decisor da Fase III:\n"
        "  - 3 imagens de Felis catus (gato domestico/feral)\n"
        "  - 2 imagens de outras especies (raposa, guaxinim, gamba)\n"
        "  - 1 imagem com humano\n"
        "  - 1 imagem vazia (paisagem sem animal)\n"
        "\n"
        "Fontes sugeridas:\n"
        "  - LILA BC (lila.science/datasets/caltech-camera-traps)\n"
        "  - iNaturalist (inaturalist.org/taxa/118552-Felis-catus)\n"
        "  - Pexels, Unsplash, Wikimedia Commons\n"
        "\n"
        "Apos copiar as imagens, execute novamente este script."
    )
    print(mensagem)


def preparar_subset_dev(diretorio: Path = DIRETORIO_PADRAO) -> int:
    """Valida o subset e grava o manifesto. Retorna codigo de saida."""
    imagens = coletar_imagens(diretorio)
    if not imagens:
        imprimir_instrucoes(diretorio)
        return 1

    registros = [descrever_imagem(caminho) for caminho in imagens]
    manifesto = {
        "diretorio": str(diretorio),
        "total": len(registros),
        "imagens": registros,
    }
    caminho_manifesto = diretorio / ARQUIVO_MANIFESTO
    caminho_manifesto.write_text(
        json.dumps(manifesto, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Subset preparado: {len(registros)} imagem(ns) em {diretorio}")
    for registro in registros:
        print(
            f"  - {registro['arquivo']:<40s} "
            f"{registro['largura']}x{registro['altura']}  "
            f"{registro['bytes']:>8d} B  "
            f"{registro['sha256'][:12]}"
        )
    print(f"Manifesto gravado em: {caminho_manifesto}")
    return 0


if __name__ == "__main__":
    sys.exit(preparar_subset_dev())
