"""Renderiza as bboxes do JSON de detecções em imagens anotadas.

Lê 04_dados/interim/deteccoes_amostras.json e salva imagens
em 05_figuras/deteccoes_dev/ (uma por mídia processada).

Uso:
    python 03_codigo/scripts/visualizar_deteccoes.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "03_codigo"))

from pipeline.E1_deteccao.schema import (  # noqa: E402
    BoundingBox,
    Deteccao,
    ResultadoDeteccao,
)
from pipeline.E1_deteccao.visualizar import desenhar_deteccoes  # noqa: E402


def _carregar_resultados(arquivo: Path) -> list[ResultadoDeteccao]:
    """Reconstrói os objetos ResultadoDeteccao a partir do JSON."""
    payload = json.loads(arquivo.read_text())
    resultados = []
    for r in payload["resultados"]:
        deteccoes = [
            Deteccao(
                categoria=d["categoria"],
                confianca=d["confianca"],
                bbox=BoundingBox(**d["bbox"]),
            )
            for d in r["deteccoes"]
        ]
        resultados.append(
            ResultadoDeteccao(
                media_path=r["media_path"],
                largura=r["largura"],
                altura=r["altura"],
                deteccoes=deteccoes,
                modelo=r["modelo"],
                tempo_ms=r["tempo_ms"],
            )
        )
    return resultados


def main() -> int:
    arquivo_json = RAIZ / "04_dados" / "interim" / "deteccoes_amostras.json"
    destino = RAIZ / "05_figuras" / "deteccoes_dev"

    if not arquivo_json.is_file():
        print(f"JSON não encontrado: {arquivo_json}")
        print("Rode antes: python 03_codigo/scripts/detectar_amostras.py")
        return 1

    resultados = _carregar_resultados(arquivo_json)
    destino.mkdir(parents=True, exist_ok=True)

    for r in resultados:
        nome = Path(r.media_path).stem + "_anotada.jpg"
        saida = destino / nome
        desenhar_deteccoes(r, saida)
        marca = "✓" if r.deteccoes else "—"
        print(f"  {marca} {nome}: {len(r.deteccoes)} bboxes")

    print(f"\nImagens anotadas em: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
