"""Executa o pipeline Fase II + Fase III sobre o subset dev.

Para cada imagem em ``04_dados/raw/lila_bc_dev/``:
  1. Roda MegaDetector v6 e obtem as deteccoes;
  2. Gera crops apenas das deteccoes da categoria 'animal';
  3. Classifica cada crop com SpeciesNet;
  4. A politica do decisor (``decidir_status``) ja foi aplicada
     internamente pelo ``ClassificadorSpeciesNet``, ficando registrada
     em ``ResultadoClassificacao.status``.

Saida consolidada em ``04_dados/interim/classificacoes_amostras.json``,
com uma entrada por imagem contendo a lista de classificacoes (uma por
crop animal).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datasets.lila_bc import listar_subset_dev, subset_esta_pronto
from pipeline.fase2_deteccao.megadetector import DetectorMegaDetectorV6
from pipeline.fase3_classificacao.speciesnet import (
    ClassificadorSpeciesNet,
    crops_de_deteccao,
)

DIRETORIO_SUBSET = Path("04_dados/raw/lila_bc_dev")
ARQUIVO_SAIDA = Path("04_dados/interim/classificacoes_amostras.json")


def _resumo_classificacao(arquivo: str, indice: int, total: int, classificacao) -> str:
    """Monta uma linha curta de log para uma classificacao individual."""
    topo = classificacao.top1
    return (
        f"  [{indice:02d}/{total:02d}] {arquivo:<32s} "
        f"crop#{classificacao.bbox_indice} -> {classificacao.status:<18s} "
        f"| {topo.especie} ({topo.probabilidade:.3f}) "
        f"[{classificacao.tempo_ms:.0f} ms]"
    )


def classificar_subset() -> int:
    """Roda o pipeline Fase II + Fase III no subset e grava JSON."""
    if not subset_esta_pronto(DIRETORIO_SUBSET):
        print(
            f"Subset vazio em {DIRETORIO_SUBSET}. "
            "Execute primeiro: python 03_codigo/scripts/preparar_subset_dev.py"
        )
        return 1

    imagens = listar_subset_dev(DIRETORIO_SUBSET)
    total = len(imagens)
    print(f"Processando {total} imagem(ns): MegaDetector v6 + SpeciesNet")

    print("Inicializando MegaDetector v6...")
    detector = DetectorMegaDetectorV6()

    print("Inicializando SpeciesNet (primeira execucao baixa pesos)...")
    classificador = ClassificadorSpeciesNet()

    registros: list[dict] = []
    for indice, caminho in enumerate(imagens, start=1):
        print(f"[{indice:02d}/{total:02d}] {caminho.name}")
        resultado_deteccao = detector.detectar(caminho)
        crops = crops_de_deteccao(resultado_deteccao)
        print(
            f"  deteccoes={len(resultado_deteccao.deteccoes)} "
            f"crops_animal={len(crops)}"
        )

        classificacoes = [classificador.classificar(crop) for crop in crops]
        for classificacao in classificacoes:
            print(_resumo_classificacao(caminho.name, indice, total, classificacao))

        registros.append(
            {
                "arquivo": caminho.name,
                "media_path": str(caminho),
                "largura": resultado_deteccao.largura,
                "altura": resultado_deteccao.altura,
                "n_deteccoes": len(resultado_deteccao.deteccoes),
                "n_crops_animal": len(crops),
                "classificacoes": [asdict(c) for c in classificacoes],
            }
        )

    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_SAIDA.write_text(
        json.dumps(
            {"total_imagens": total, "imagens": registros},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\nResultados gravados em: {ARQUIVO_SAIDA}")

    # Resumo final por status
    contagem: dict[str, int] = {}
    for registro in registros:
        for classificacao in registro["classificacoes"]:
            status = classificacao["status"]
            contagem[status] = contagem.get(status, 0) + 1
    if contagem:
        print("Resumo por status:")
        for status, n in sorted(contagem.items()):
            print(f"  {status:<20s} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(classificar_subset())
