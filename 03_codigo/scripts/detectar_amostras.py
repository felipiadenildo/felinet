"""Roda o MegaDetector v6 nas imagens em 04_dados/raw/amostras_dev/
e salva os resultados em 04_dados/interim/deteccoes_amostras.json.

Uso:
    python 03_codigo/scripts/detectar_amostras.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Permite importar `pipeline.*` quando rodado direto
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "03_codigo"))

from pipeline.E0_ingestao.validar import listar_midias  # noqa: E402
from pipeline.E1_deteccao.megadetector import DetectorMegaDetectorV6  # noqa: E402
from pipeline.E1_deteccao.schema import salvar_resultados_json  # noqa: E402


def main() -> int:
    pasta_imagens = RAIZ / "04_dados" / "raw" / "amostras_dev"
    arquivo_saida = RAIZ / "04_dados" / "interim" / "deteccoes_amostras.json"

    if not pasta_imagens.is_dir() or not any(pasta_imagens.iterdir()):
        print(f"Sem imagens em {pasta_imagens}.")
        print("Rode antes: python 03_codigo/scripts/baixar_amostras.py")
        return 1

    imagens = listar_midias(pasta_imagens)
    print(f"Imagens encontradas: {len(imagens)}")

    print("Inicializando MegaDetector v6 (primeira execução baixa pesos)...")
    detector = DetectorMegaDetectorV6(dispositivo="auto")
    print(f"Dispositivo: {detector.dispositivo}")

    resultados = []
    for img in imagens:
        r = detector.detectar(img, limite_confianca=0.20)
        animais = sum(1 for d in r.deteccoes if d.categoria == "animal")
        print(
            f"  {img.name}: {len(r.deteccoes)} detecções "
            f"({animais} animal) — {r.tempo_ms:.0f} ms"
        )
        resultados.append(r)

    salvar_resultados_json(resultados, arquivo_saida)
    print(f"\nResultados salvos em: {arquivo_saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
