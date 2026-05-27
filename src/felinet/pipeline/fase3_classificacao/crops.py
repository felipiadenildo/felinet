"""Recorte e persistencia de crops felis_catus aprovados pelo decisor.

Apos a Fase III filtrar bboxes em ``felis_catus``, os crops sao gravados em
disco para servirem de entrada concreta da Fase IV (Re-ID). Em dev, a pasta
``data/dev/pipeline/05_crops_felis_catus/`` materializa essa ponte.

Cada crop e nomeado deterministicamente como
``<basename_imagem>__bbox<indice>.png`` para permitir rastreabilidade direta
ate o arquivo original e o indice da bbox no JSON da Fase II.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..fase2_deteccao.schema import BoundingBox
from .schema import STATUS_FELIS_CATUS, ResultadoClassificacao
from .speciesnet import cortar_crop


@dataclass(frozen=True)
class CropPersistido:
    """Registro de um crop felis_catus gravado em disco."""

    media_path_original: str
    bbox_indice: int
    caminho_crop: Path
    largura: int
    altura: int


def _nome_arquivo_crop(media_path: Path, bbox_indice: int) -> str:
    return f"{media_path.stem}__bbox{bbox_indice:02d}.png"


def persistir_crops_felis_catus(
    classificacoes: list[ResultadoClassificacao],
    deteccoes_por_imagem: dict[str, list[BoundingBox]],
    pasta_saida: Path,
) -> list[CropPersistido]:
    """Grava em disco apenas os crops com status ``felis_catus``.

    Args:
        classificacoes: Saidas da Fase III (uma por bbox classificada).
        deteccoes_por_imagem: Mapa ``media_path -> lista de bboxes`` da Fase II.
            Necessario porque ``ResultadoClassificacao`` so guarda o indice da bbox.
        pasta_saida: Diretorio onde gravar os PNGs (criado se nao existir).

    Returns:
        Lista de ``CropPersistido``, na ordem em que foram gravados.
    """
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    persistidos: list[CropPersistido] = []
    for classificacao in classificacoes:
        if classificacao.status != STATUS_FELIS_CATUS:
            continue
        media_path = Path(classificacao.media_path)
        bboxes = deteccoes_por_imagem.get(str(media_path), [])
        if not bboxes or classificacao.bbox_indice >= len(bboxes):
            continue
        bbox = bboxes[classificacao.bbox_indice]
        crop = cortar_crop(media_path, bbox)
        nome = _nome_arquivo_crop(media_path, classificacao.bbox_indice)
        caminho = pasta_saida / nome
        crop.save(caminho, format="PNG")
        persistidos.append(
            CropPersistido(
                media_path_original=str(media_path),
                bbox_indice=classificacao.bbox_indice,
                caminho_crop=caminho,
                largura=crop.width,
                altura=crop.height,
            )
        )
    return persistidos


def mover_rejeitados(
    media_paths: list[Path],
    pasta_rejeitos: Path,
    motivo: str,
) -> None:
    """Copia (NAO move) imagens rejeitadas para uma pasta de demonstracao.

    Em dev essa pasta materializa as decisoes do pipeline para discussao na
    monografia. NAO usa ``shutil.move`` para preservar o original em
    ``01_brutas/`` -- as rejeicoes sao replicadas, nao deslocadas.

    Cada imagem copiada vem com um arquivo-irmao ``.motivo.txt`` explicando
    a razao da rejeicao.
    """
    import shutil

    pasta_rejeitos = Path(pasta_rejeitos)
    pasta_rejeitos.mkdir(parents=True, exist_ok=True)
    for caminho in media_paths:
        if not Path(caminho).exists():
            continue
        destino = pasta_rejeitos / Path(caminho).name
        shutil.copy2(caminho, destino)
        (destino.with_suffix(destino.suffix + ".motivo.txt")).write_text(
            motivo + "\n", encoding="utf-8"
        )
