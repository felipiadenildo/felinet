"""Roda o MDv6 sobre todas as imagens do subset dev e salva o JSON."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datasets.lila_bc import listar_subset_dev, subset_esta_pronto  # noqa: E402
from pipeline.fase2_deteccao.megadetector import DetectorMegaDetectorV6  # noqa: E402
from pipeline.fase2_deteccao.schema import salvar_resultados_json  # noqa: E402

DIRETORIO_SUBSET = Path("04_dados/raw/lila_bc_dev")
ARQUIVO_SAIDA = Path("04_dados/interim/deteccoes_subset_dev.json")


def detectar_subset() -> int:
    if not subset_esta_pronto(DIRETORIO_SUBSET):
        print(f"Subset vazio em {DIRETORIO_SUBSET}.")
        return 1

    imagens = listar_subset_dev(DIRETORIO_SUBSET)
    print(f"Detectando {len(imagens)} imagem(ns) com MDv6...")
    detector = DetectorMegaDetectorV6()
    resultados = [detector.detectar(p) for p in imagens]

    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    salvar_resultados_json(resultados, ARQUIVO_SAIDA)
    print(f"\nGravado em: {ARQUIVO_SAIDA}")
    for r in resultados:
        n_animal = sum(1 for d in r.deteccoes if d.categoria == "animal")
        print(f"  {Path(r.media_path).name:<32s} deteccoes={len(r.deteccoes)} animal={n_animal}")
    return 0


if __name__ == "__main__":
    sys.exit(detectar_subset())
