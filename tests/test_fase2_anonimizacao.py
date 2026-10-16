"""Fase II: anonimização de pessoas (LGPD), modo noturno e filtro de caixas."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from felinet.pipeline.fase2_deteccao.anonimizacao import (
    ConfigFiltroDeteccao,
    anonimizar_pessoas,
    eh_noturno_infravermelho,
    filtrar_deteccoes,
)
from felinet.pipeline.fase2_deteccao.schema import BoundingBox, Deteccao
from felinet.pipeline.fase3_classificacao.crops import persistir_crops_felis_catus
from felinet.pipeline.fase3_classificacao.schema import ResultadoClassificacao


def _xadrez(tamanho: int = 64) -> Image.Image:
    i, j = np.indices((tamanho, tamanho))
    arr = (((i // 4 + j // 4) % 2) * 255).astype(np.uint8)
    return Image.fromarray(np.stack([arr] * 3, axis=-1))


def _variacao(img: Image.Image, caixa: tuple[int, int, int, int]) -> float:
    return float(np.asarray(img.crop(caixa).convert("L"), dtype=np.float32).std())


PESSOA = Deteccao("person", 0.9, BoundingBox(0.0, 0.0, 0.5, 0.5))
ANIMAL = Deteccao("animal", 0.8, BoundingBox(0.5, 0.5, 0.5, 0.5))


def test_desfoca_so_a_caixa_da_pessoa() -> None:
    img = _xadrez()
    saida = anonimizar_pessoas(img, [PESSOA, ANIMAL])
    assert _variacao(saida, (0, 0, 32, 32)) < 0.2 * _variacao(img, (0, 0, 32, 32))
    assert np.array_equal(
        np.asarray(saida.crop((32, 32, 64, 64))), np.asarray(img.crop((32, 32, 64, 64)))
    )


def test_noturno_infravermelho() -> None:
    assert eh_noturno_infravermelho(Image.new("RGB", (8, 8), (90, 90, 92)))
    assert not eh_noturno_infravermelho(Image.new("RGB", (8, 8), (180, 90, 40)))


def test_filtro_por_modo_e_area() -> None:
    fraca = Deteccao("animal", 0.3, BoundingBox(0.1, 0.1, 0.05, 0.05))
    cfg = ConfigFiltroDeteccao(limiar_dia=0.2, limiar_noite=0.4, area_min=0.01)
    assert filtrar_deteccoes([fraca, ANIMAL, PESSOA], noturno=False, cfg=cfg) == [ANIMAL, PESSOA]
    cfg_area = ConfigFiltroDeteccao(area_min=0.0)
    assert fraca in filtrar_deteccoes([fraca], noturno=False, cfg=cfg_area)
    assert fraca not in filtrar_deteccoes(
        [fraca], noturno=True, cfg=ConfigFiltroDeteccao(limiar_noite=0.4)
    )


def test_recorte_gravado_nao_contem_pessoa_nitida(tmp_path: Path) -> None:
    origem = tmp_path / "quadro.png"
    _xadrez().save(origem)
    # caixa do animal cobre o quadro inteiro, inclusive a região da pessoa
    caixa_animal = BoundingBox(0.0, 0.0, 1.0, 1.0)
    clf = ResultadoClassificacao(
        media_path=str(origem),
        bbox_indice=0,
        top_k=[],
        status="felis_catus",
        modelo="x",
        tempo_ms=0.0,
    )
    (gravado,) = persistir_crops_felis_catus(
        [clf],
        {str(origem): [caixa_animal]},
        tmp_path / "crops",
        pessoas_por_imagem={str(origem): [PESSOA]},
    )
    recorte = Image.open(gravado.caminho_crop)
    assert _variacao(recorte, (0, 0, 32, 32)) < 0.2 * _variacao(_xadrez(), (0, 0, 32, 32))
