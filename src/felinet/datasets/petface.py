"""Carregamento do dataset PetFace (categoria cat) para Re-ID.

Protocolo oficial PetFace:
    - O CSV reidentification.csv lista 1 imagem (query) por individuo.
    - As demais imagens em images/cat/<id_pad>/ formam a galeria daquele individuo.
    - Avaliacao Top-K: para cada query, ranqueia toda a galeria global
      (de todos individuos amostrados) e verifica se o ID correto aparece nos K
      primeiros resultados.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

DIRETORIO_PADRAO = Path("04_dados/raw/petface")


@dataclass(frozen=True)
class RegistroPetFace:
    """Um individuo do PetFace com sua query e galeria."""

    id_individuo: int
    query: Path
    galeria: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not self.galeria:
            raise ValueError(f"Individuo {self.id_individuo} sem imagens de galeria")


def subset_esta_pronto(diretorio: Path = DIRETORIO_PADRAO) -> bool:
    """Verifica se a estrutura minima do PetFace esta presente."""
    csv_path = diretorio / "split" / "cat" / "reidentification.csv"
    img_dir = diretorio / "images" / "cat"
    return csv_path.exists() and img_dir.exists() and any(img_dir.iterdir())


def carregar_reidentification(
    diretorio: Path = DIRETORIO_PADRAO,
    max_individuos: int | None = None,
) -> list[RegistroPetFace]:
    """Le reidentification.csv e monta query+galeria por individuo.

    Args:
        diretorio: Raiz do dataset PetFace.
        max_individuos: Se informado, limita aos N primeiros individuos
            distintos com galeria nao vazia.

    Returns:
        Lista de RegistroPetFace na ordem do CSV. Individuos cuja pasta
        tem apenas a imagem-query (galeria vazia) sao silenciosamente pulados.
    """
    csv_path = diretorio / "split" / "cat" / "reidentification.csv"
    img_dir = diretorio / "images" / "cat"
    registros: list[RegistroPetFace] = []

    with csv_path.open(encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            filename = linha["filename"].strip()
            label = int(linha["label"])

            # filename vem como "cat/000000/05.png" -- caminho relativo a raiz
            query_path = diretorio / "split" / "cat" / ".." / ".." / "images" / filename
            query_path = (
                query_path.resolve() if query_path.exists() else (diretorio / "images" / filename)
            )

            id_pad = f"{label:06d}"
            pasta_individuo = img_dir / id_pad
            if not pasta_individuo.is_dir():
                continue

            todas_imgs = sorted(
                p
                for p in pasta_individuo.iterdir()
                if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
            )
            galeria = tuple(p for p in todas_imgs if p.name != query_path.name)
            if not galeria:
                continue

            registros.append(
                RegistroPetFace(
                    id_individuo=label,
                    query=query_path,
                    galeria=galeria,
                )
            )

            if max_individuos is not None and len(registros) >= max_individuos:
                break

    return registros


def agrupar_por_individuo(
    registros: list[RegistroPetFace],
) -> dict[int, RegistroPetFace]:
    """Indexa registros por id_individuo (cada ID aparece uma vez)."""
    return {r.id_individuo: r for r in registros}
